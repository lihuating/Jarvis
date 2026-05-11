# Jarvis VSCodeTool：构建 / 安装 / 使用说明

本文档面向 `VscodeTool/` 目录下的 VSCode 扩展工程（TypeScript）。

## 前置条件

- **Node.js**: 建议 18+（本仓库环境已验证 22.x 可用）
- **VSCode**: `^1.90.0`
- **Jarvis 后端命令**:
  - 默认使用 `jca`（代码代理）
  - 也支持 `jvs`（通用代理）
  - 要求命令在 VSCode 启动环境的 `PATH` 中可找到，或在插件配置里指定绝对路径

## 快速安装（离线）

如果你已经构建了 `.vsix` 文件，可以直接安装：

```bash
# 方法 1: 使用 VSCode 命令
code --install-extension jarvis-vscode-tool-0.2.0.vsix

# 方法 2: 在 VSCode 图形界面
# 1. 按 Ctrl+Shift+X 打开扩展面板
# 2. 点击右上角 "..." 菜单
# 3. 选择 "从 VSIX 安装..."
# 4. 选择 jarvis-vscode-tool-0.2.0.vsix 文件
```

详细安装说明请查看 `INSTALL.md`。

## 构建（开发）

在 VSCode 打开 `VscodeTool/` 目录后，终端执行：

```bash
cd /media/vdc/code/Jarvis/VscodeTool
npm install
npm run compile
```

然后按 `F5` 启动 **Extension Development Host**。

## 使用（开发态）

打开命令面板（`Ctrl+Shift+P`）：

- **`Jarvis: Open Chat`**：打开 Chat Webview
- **`Jarvis: Send Selection to Chat`**：把当前编辑器选区作为上下文发送
- **`Jarvis: Send Current File to Chat`**：把当前文件全文作为上下文发送
- **`Jarvis: Send Explorer Selection to Chat`**：弹出选择器，选择路径/文件作为上下文发送
- **`Jarvis: Stop Backend`**：停止当前后端进程
- **`Jarvis: New Chat`**：新建会话，清空上下文（快捷键：在 Chat 界面点击 "New Chat" 按钮）

在 Chat 顶部：

- 可通过下拉框切换后端：`jca` / `jvs`
- 可选择上下文模式：`no context` / `selection` / `current file` / `pick paths…`
- **会话名称显示**：蓝色徽章显示当前会话名称（仅持久会话模式）
- **New Chat 按钮**：绿色按钮，点击清空上下文

## 配置项（Settings）

在 VSCode 设置中搜索 `Jarvis`：

- **`jarvis.backend`**：`jca` / `jvs`（默认 `jca`）
- **`jarvis.commandPath`**：后端命令绝对路径（例如 `/usr/local/bin/jca`），为空则从 `PATH` 查找
- **`jarvis.nonInteractive`**：是否添加 `-n/--non-interactive`（默认 `true`，推荐保持开启）
- **`jarvis.disableReview`**：仅对 `jca`，是否添加 `--disable-review`（默认 `true`，减少副作用与等待时间）
- **`jarvis.sessionMode`**：`persistent` / `single-use`（默认 `persistent`，多轮对话保持上下文）

### 会话模式说明

- **`persistent`**（默认）：持久会话模式，多轮对话保持上下文，界面顶部显示会话名称
- **`single-use`**：单次会话模式，每次对话独立，不保留上下文

详细会话功能请查看 [会话功能说明](SESSION_FEATURE.md)。

## 运行机制说明（重要）

插件会在工作区根目录（workspace root）下启动后端进程，命令行形态为：

- `jca -n -T "<prompt>" --disable-review`（默认）
- 或 `jvs -n -T "<prompt>"`

插件会将：

- stdout：作为“assistant”增量输出流式显示
- stderr：作为“system”输出显示

如果你的系统里 `jca/jvs` 需要特定的 Python 3.12 环境，请确保 VSCode 启动时继承到了正确的环境变量（或通过 `jarvis.commandPath` 指向包装脚本）。

## 打包与安装（可选）

当前工程未内置 `vsce` 打包依赖。如果你需要生成 `.vsix`：

1) 安装 vsce

```bash
npm i -g @vscode/vsce
```

1) 打包

```bash
cd /media/vdc/code/Jarvis/VscodeTool
npm run compile
vsce package
```

会生成类似 `jarvis-vscode-tool-0.1.0.vsix`。

1) 安装 `.vsix`

- VSCode：Extensions 视图 → 右上角 “...” → **Install from VSIX…**

## 常见问题

- **Q: Chat 能打开，但不出结果？**
  - A: 通常是 `jca/jvs` 在 VSCode 环境里找不到或权限不足。请先在 VSCode 集成终端执行 `jca --help` 验证可用；或设置 `jarvis.commandPath`。

- **Q: 后端进程启动后立刻退出？**
  - A: 查看 Chat 中的 system 输出（stderr），常见原因是 Jarvis 配置缺失（API key / config.yaml），或 Python 版本不匹配（Jarvis 需要 Python 3.12）。

- **Q: 我想让"资源管理器选中文件"自动读取文件内容，而不是只传路径。**
  - A: 目前实现传的是路径列表（更轻量、更安全）。如果你希望自动读文件内容，可以继续增强（需做大小阈值与忽略规则）。

- **Q: 多轮对话没有上下文关联？**
  - A: 检查是否使用了默认的 `persistent` 会话模式。查看界面顶部是否有会话名称显示（蓝色徽章）。如果没有，点击 "New Chat" 按钮后重新提问。

- **Q: 如何开始全新的对话（不保留之前的上下文）？**
  - A: 点击 Chat 界面顶部的 "New Chat" 按钮（绿色），系统会提示"已新建会话，上下文已清空"。

- **Q: 会话文件在哪里？如何清理？**
  - A: 会话文件位于 `~/.jarvis/sessions/` 目录。可以定期清理旧文件，或者让系统自动管理（最多保留 10 个）。
