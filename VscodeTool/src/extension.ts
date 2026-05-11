import * as vscode from "vscode";
import { spawn, ChildProcessWithoutNullStreams } from "node:child_process";
import * as path from "node:path";

type Backend = "jca" | "jvs";

type WebviewToExtension =
  | { type: "send"; text: string; contextMode?: "none" | "selection" | "file" | "explorer" }
  | { type: "setBackend"; backend: Backend }
  | { type: "stop" }
  | { type: "newChat" };

type ExtensionToWebview =
  | { type: "appendAssistant"; text: string }
  | { type: "appendSystem"; text: string }
  | { type: "setBackend"; backend: Backend }
  | { type: "setRunning"; running: boolean }
  | { type: "setSessionName"; sessionName: string | null };

class JarvisChatPanel {
  public static current: JarvisChatPanel | undefined;

  private readonly panel: vscode.WebviewPanel;
  private readonly ctx: vscode.ExtensionContext;
  private proc: ChildProcessWithoutNullStreams | null = null;
  private bufferedStdout = "";
  private lastBackend: Backend = "jca";
  private sessionName: string | null = null;  // 会话名称，用于保持上下文

  private constructor(ctx: vscode.ExtensionContext) {
    this.ctx = ctx;
    this.panel = vscode.window.createWebviewPanel(
      "jarvisChat",
      "Jarvis Chat",
      vscode.ViewColumn.Beside,
      { enableScripts: true, retainContextWhenHidden: true }
    );

    this.panel.webview.html = this.renderHtml(this.panel.webview);

    const backend = this.getBackendSetting();
    this.lastBackend = backend;
    this.post({ type: "setBackend", backend });

    this.panel.webview.onDidReceiveMessage((msg: WebviewToExtension) => {
      void this.onMessage(msg);
    });

    this.panel.onDidDispose(() => {
      this.stop();
      JarvisChatPanel.current = undefined;
    });
  }

  public static open(ctx: vscode.ExtensionContext): JarvisChatPanel {
    if (JarvisChatPanel.current) {
      JarvisChatPanel.current.panel.reveal(vscode.ViewColumn.Beside);
      return JarvisChatPanel.current;
    }
    JarvisChatPanel.current = new JarvisChatPanel(ctx);
    return JarvisChatPanel.current;
  }

  public async sendWithContext(text: string, mode: "none" | "selection" | "file" | "explorer") {
    await this.onMessage({ type: "send", text, contextMode: mode });
  }

  private async onMessage(msg: WebviewToExtension) {
    if (msg.type === "setBackend") {
      await vscode.workspace.getConfiguration().update("jarvis.backend", msg.backend, true);
      this.lastBackend = msg.backend;
      this.post({ type: "setBackend", backend: msg.backend });
      return;
    }

    if (msg.type === "stop") {
      this.stop();
      return;
    }

    if (msg.type === "newChat") {
      this.newChat();
      return;
    }

    if (msg.type === "send") {
      const backend = this.getBackendSetting();
      this.lastBackend = backend;
      const prompt = await this.buildPrompt(msg.text, msg.contextMode ?? "none");
      await this.runBackend(backend, prompt);
    }
  }

  private getBackendSetting(): Backend {
    const cfg = vscode.workspace.getConfiguration();
    const v = cfg.get<string>("jarvis.backend", "jca");
    return v === "jvs" ? "jvs" : "jca";
  }

  private getCommandPathSetting(): string {
    return vscode.workspace.getConfiguration().get<string>("jarvis.commandPath", "")?.trim() ?? "";
  }

  private shouldNonInteractive(): boolean {
    return vscode.workspace.getConfiguration().get<boolean>("jarvis.nonInteractive", true) === true;
  }

  private shouldDisableReview(): boolean {
    return vscode.workspace.getConfiguration().get<boolean>("jarvis.disableReview", true) === true;
  }

  private getSessionMode(): "persistent" | "single-use" {
    return vscode.workspace.getConfiguration().get<string>("jarvis.sessionMode", "persistent") as "persistent" | "single-use";
  }

  private newChat() {
    // 重置会话名称，下次运行时会创建新会话
    this.sessionName = null;
    this.post({ type: "setSessionName", sessionName: null });
    this.post({ type: "appendSystem", text: "已新建会话，上下文已清空。" });
  }

  private async buildPrompt(userText: string, mode: "none" | "selection" | "file" | "explorer") {
    const root = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? "";
    const activeEditor = vscode.window.activeTextEditor;

    let contextBlock = "";
    if (mode === "selection" && activeEditor) {
      const sel = activeEditor.selection;
      const selected = activeEditor.document.getText(sel);
      const filePath = activeEditor.document.uri.fsPath;
      if (selected.trim()) {
        contextBlock = [
          "<context>",
          `workspace_root: ${root}`,
          `active_file: ${path.relative(root || path.dirname(filePath), filePath)}`,
          "selected_text:",
          selected,
          "</context>",
        ].join("\n");
      }
    } else if (mode === "file" && activeEditor) {
      const filePath = activeEditor.document.uri.fsPath;
      const full = activeEditor.document.getText();
      contextBlock = [
        "<context>",
        `workspace_root: ${root}`,
        `active_file: ${path.relative(root || path.dirname(filePath), filePath)}`,
        "file_content:",
        full,
        "</context>",
      ].join("\n");
    } else if (mode === "explorer") {
      const picked = await vscode.window.showOpenDialog({
        canSelectFiles: true,
        canSelectFolders: true,
        canSelectMany: true,
        defaultUri: root ? vscode.Uri.file(root) : undefined,
        openLabel: "Use as context",
      });
      if (picked?.length) {
        const rels = picked.map((u) => (root ? path.relative(root, u.fsPath) : u.fsPath));
        contextBlock = [
          "<context>",
          `workspace_root: ${root}`,
          "selected_paths:",
          ...rels.map((p) => `- ${p}`),
          "</context>",
        ].join("\n");
      }
    }

    return contextBlock ? `${contextBlock}\n\n${userText}` : userText;
  }

  private async runBackend(backend: Backend, prompt: string) {
    if (!prompt.trim()) return;

    if (this.proc) {
      this.post({ type: "appendSystem", text: "已有任务在运行，已先停止旧任务。" });
      this.stop();
    }

    const commandPath = this.getCommandPathSetting();
    const cmd = commandPath || backend;
    const args: string[] = [];

    // 以非交互模式执行（避免 VSCode 内等待输入）
    if (this.shouldNonInteractive()) args.push("-n");
    
    // 会话管理：使用持久会话模式
    const sessionMode = this.getSessionMode();
    if (sessionMode === "persistent") {
      // 如果是持久会话模式，使用固定的会话名称
      if (!this.sessionName) {
        // 生成会话名称：vscode-<timestamp>
        this.sessionName = `vscode-${Date.now()}`;
        this.post({ type: "setSessionName", sessionName: this.sessionName });
      }
      args.push("--session-name", this.sessionName);
    }
    
    args.push("-T", prompt);

    if (backend === "jca" && this.shouldDisableReview()) {
      args.push("--disable-review");
    }

    const cwd = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? process.cwd();

    this.post({ type: "setRunning", running: true });
    const sessionInfo = this.sessionName ? ` (会话：${this.sessionName})` : "";
    this.post({ type: "appendSystem", text: `启动后端${sessionInfo}: ${cmd} ${args.join(" ")}` });

    try {
      this.proc = spawn(cmd, args, { cwd });
    } catch (e) {
      this.proc = null;
      this.post({ type: "appendSystem", text: `启动失败：${String(e)}` });
      this.post({ type: "setRunning", running: false });
      return;
    }

    this.bufferedStdout = "";

    this.proc.stdout.on("data", (chunk: Buffer) => {
      const s = chunk.toString("utf-8");
      this.bufferedStdout += s;
      this.post({ type: "appendAssistant", text: s });
    });

    this.proc.stderr.on("data", (chunk: Buffer) => {
      const s = chunk.toString("utf-8");
      this.post({ type: "appendSystem", text: s });
    });

    this.proc.on("close", (code) => {
      this.post({ type: "appendSystem", text: `进程退出：code=${code ?? "null"}` });
      this.post({ type: "setRunning", running: false });
      this.proc = null;
    });
  }

  private stop() {
    if (!this.proc) return;
    try {
      this.proc.kill("SIGTERM");
    } catch {
      // ignore
    }
    this.proc = null;
    this.post({ type: "setRunning", running: false });
  }

  private post(msg: ExtensionToWebview) {
    void this.panel.webview.postMessage(msg);
  }

  private renderHtml(webview: vscode.Webview) {
    const nonce = String(Date.now());
    const backend = this.getBackendSetting();
    return `<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${nonce}';" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Jarvis Chat</title>
  <style>
    body { font-family: -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif; padding: 0; margin: 0; }
    .topbar { display: flex; gap: 8px; align-items: center; padding: 8px 10px; border-bottom: 1px solid rgba(127,127,127,0.25); }
    .badge { padding: 2px 8px; border-radius: 999px; background: rgba(127,127,127,0.15); }
    .session-badge { padding: 2px 8px; border-radius: 999px; background: rgba(33,150,243,0.2); color: #2196f3; font-size: 0.85em; }
    .btn { cursor: pointer; padding: 6px 10px; border: 1px solid rgba(127,127,127,0.35); border-radius: 6px; background: rgba(127,127,127,0.10); }
    .btn:disabled { opacity: 0.5; cursor: not-allowed; }
    .btn-new { background: rgba(76,175,80,0.2); border-color: rgba(76,175,80,0.5); }
    .grow { flex: 1; }
    .log { padding: 10px; height: calc(100vh - 120px); overflow: auto; white-space: pre-wrap; }
    .msg-user { color: #0b6; }
    .msg-assistant { color: #ddd; }
    .msg-system { color: #aaa; }
    .composer { display: flex; gap: 8px; padding: 10px; border-top: 1px solid rgba(127,127,127,0.25); }
    textarea { flex: 1; resize: vertical; min-height: 56px; padding: 8px; border-radius: 8px; border: 1px solid rgba(127,127,127,0.35); background: rgba(127,127,127,0.08); color: inherit; }
    select { padding: 6px 8px; border-radius: 6px; border: 1px solid rgba(127,127,127,0.35); background: rgba(127,127,127,0.08); color: inherit; }
  </style>
</head>
<body>
  <div class="topbar">
    <span class="badge" id="backendBadge">backend: ${backend}</span>
    <select id="backendSel" title="Backend">
      <option value="jca" ${backend === "jca" ? "selected" : ""}>jca (default)</option>
      <option value="jvs" ${backend === "jvs" ? "selected" : ""}>jvs</option>
    </select>
    <span id="sessionBadge" class="session-badge" style="display: none;"></span>
    <button class="btn btn-new" id="btnNewChat" title="新建会话（清空上下文）">New Chat</button>
    <button class="btn" id="btnStop" disabled>Stop</button>
    <div class="grow"></div>
    <select id="ctxSel" title="Context mode">
      <option value="none">no context</option>
      <option value="selection">selection</option>
      <option value="file">current file</option>
      <option value="explorer">pick paths…</option>
    </select>
  </div>

  <div class="log" id="log"></div>

  <div class="composer">
    <textarea id="input" placeholder="Ask Jarvis…"></textarea>
    <button class="btn" id="btnSend">Send</button>
  </div>

  <script nonce="${nonce}">
    const vscode = acquireVsCodeApi();
    const log = document.getElementById('log');
    const input = document.getElementById('input');
    const btnSend = document.getElementById('btnSend');
    const btnStop = document.getElementById('btnStop');
    const btnNewChat = document.getElementById('btnNewChat');
    const backendSel = document.getElementById('backendSel');
    const backendBadge = document.getElementById('backendBadge');
    const sessionBadge = document.getElementById('sessionBadge');
    const ctxSel = document.getElementById('ctxSel');

    function appendLine(cls, text) {
      const pre = document.createElement('pre');
      pre.className = cls;
      pre.textContent = text;
      log.appendChild(pre);
      log.scrollTop = log.scrollHeight;
    }

    btnSend.addEventListener('click', () => {
      const text = input.value || '';
      if (!text.trim()) return;
      appendLine('msg-user', '> ' + text);
      input.value = '';
      vscode.postMessage({ type: 'send', text, contextMode: ctxSel.value });
    });

    btnStop.addEventListener('click', () => vscode.postMessage({ type: 'stop' }));
    
    btnNewChat.addEventListener('click', () => vscode.postMessage({ type: 'newChat' }));

    backendSel.addEventListener('change', () => {
      vscode.postMessage({ type: 'setBackend', backend: backendSel.value });
    });

    window.addEventListener('message', (ev) => {
      const msg = ev.data;
      if (msg.type === 'appendAssistant') appendLine('msg-assistant', msg.text);
      if (msg.type === 'appendSystem') appendLine('msg-system', msg.text);
      if (msg.type === 'setBackend') {
        backendSel.value = msg.backend;
        backendBadge.textContent = 'backend: ' + msg.backend;
      }
      if (msg.type === 'setRunning') {
        btnStop.disabled = !msg.running;
        btnSend.disabled = msg.running;
      }
      if (msg.type === 'setSessionName') {
        // 会话名称更新，在界面上显示
        if (msg.sessionName) {
          sessionBadge.textContent = '📝 ' + msg.sessionName;
          sessionBadge.style.display = 'inline-block';
        } else {
          sessionBadge.textContent = '';
          sessionBadge.style.display = 'none';
        }
      }
    });
  </script>
</body>
</html>`;
  }
}

export function activate(context: vscode.ExtensionContext) {
  const openChat = () => JarvisChatPanel.open(context);

  context.subscriptions.push(
    vscode.commands.registerCommand("jarvis.openChat", openChat),
    vscode.commands.registerCommand("jarvis.stopBackend", () => {
      JarvisChatPanel.current?.["stop"]?.();
    }),
    vscode.commands.registerCommand("jarvis.newChat", () => {
      JarvisChatPanel.current?.["newChat"]?.();
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("jarvis.sendSelectionToChat", async () => {
      const panel = openChat();
      await panel.sendWithContext("请基于我选中的代码回答/处理。", "selection");
    }),
    vscode.commands.registerCommand("jarvis.sendCurrentFileToChat", async () => {
      const panel = openChat();
      await panel.sendWithContext("请基于当前文件内容回答/处理。", "file");
    }),
    vscode.commands.registerCommand("jarvis.sendExplorerSelectionToChat", async () => {
      const panel = openChat();
      await panel.sendWithContext("请基于我选择的路径/文件回答/处理。", "explorer");
    })
  );
}

export function deactivate() {
  JarvisChatPanel.current?.["stop"]?.();
}

