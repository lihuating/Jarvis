# Jarvis VSCodeTool：构建 / 安装 / 使用说明

本文档面向 `VscodeTool/` 目录下的 VSCode 扩展工程（TypeScript）。

## 前置条件

- **Node.js**: 建议 18+（本仓库环境已验证 22.x 可用）
- **VSCode**: `^1.90.0`
- **Jarvis 后端命令**：
  - 默认使用 `jca`（代码代理）
  - 也支持 `jvs`（通用代理）
  - 要求命令在 VSCode 启动环境的 `PATH` 中可找到，或在插件配置里指定绝对路径

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

在 Chat 顶部：
- 可通过下拉框切换后端：`jca` / `jvs`
- 可选择上下文模式：`no context` / `selection` / `current file` / `pick paths…`

## 配置项（Settings）

在 VSCode 设置中搜索 `Jarvis`：

- **`jarvis.backend`**：`jca` / `jvs`（默认 `jca`）
- **`jarvis.commandPath`**：后端命令绝对路径（例如 `/usr/local/bin/jca`），为空则从 `PATH` 查找
- **`jarvis.nonInteractive`**：是否添加 `-n/--non-interactive`（默认 `true`，推荐保持开启）
- **`jarvis.disableReview`**：仅对 `jca`，是否添加 `--disable-review`（默认 `true`，减少副作用与等待时间）

## 运行机制说明（重要）

插件会在工作区根目录（workspace root）下启动后端进程，命令行形态为：

- `jca -n -T "<prompt>" --disable-review`（默认）
- 或 `jvs -n -T "<prompt>"`

插件会将：
- stdout：作为“assistant”增量输出流式显示
- stderr：作为“system”输出显示

如果你的系统里 `jca/jvs` 需要特定的 Python 3.12 环境，请确保 VSCode 启动时继承到了正确的环境变量（或通过 `jarvis.commandPath` 指向包装脚本）。

## 打包与安装（可选）

**重要：本扩展未发布到 VS Code / Open VSX 应用商店。** 在扩展市场搜索「Jarvis」通常**搜不到**，必须通过下面任一方式安装。

### 1) 先编译（必须）

`package.json` 的入口是 `dist/extension.js`。若仓库里没有 `dist/`，必须先执行：

```bash
cd VscodeTool
npm install
npm run compile
```

没有 `dist/extension.js` 就打出来的 `.vsix` 安装后会**无法激活**或报「找不到 main」。

### 2) 打包 `.vsix`

本仓库已在 `devDependencies` 中声明 `@vscode/vsce`，推荐用项目内版本：

```bash
cd VscodeTool
npm run compile
npx @vscode/vsce package
```

（若已全局安装，也可用 `vsce package`。）

会生成类似 `jarvis-vscode-tool-0.1.1.vsix`。

### 3) 安装 `.vsix`

**图形界面**

- **VS Code**：扩展视图 → 右上角 `⋯` → **Install from VSIX…** → 选择上述 `.vsix`。
- **Cursor**：同样通过命令面板 `Extensions: Install from VSIX...`（或扩展面板中的「从 VSIX 安装」）选择文件。

**命令行（推荐，便于确认报错）**

- VS Code（需 `code` 在 PATH 中）：

```bash
code --install-extension jarvis-vscode-tool-0.1.1.vsix
```

- Cursor（可执行文件名因安装路径而异，常见为 `cursor`）：

```bash
cursor --install-extension jarvis-vscode-tool-0.1.1.vsix
```

安装成功后扩展 id 为 **`jarvis.jarvis-vscode-tool`**，可在已安装扩展列表中搜索 `jarvis` 核对。

### 4) 仍装不上时自检

| 现象 | 处理 |
|------|------|
| 市场搜不到 Jarvis | 正常：未上架，请用 VSIX。 |
| 提示与当前 VS Code 版本不兼容 | 升级 VS Code / Cursor 至 **1.90+**（见 `package.json` → `engines.vscode`）。 |
| 安装后扩展不工作 | 确认 `dist/extension.js` 已打进包；重新 `npm run compile` 后再 `vsce package`。 |
| Chat 无输出 | 见下文「Chat 能打开，但不出结果」：`jca`/`jvs` 与 `PATH` 或 `jarvis.commandPath`。 |

## 常见问题

- **Q: Chat 能打开，但不出结果？**
  - A: 通常是 `jca/jvs` 在 VSCode 环境里找不到或权限不足。请先在 VSCode 集成终端执行 `jca --help` 验证可用；或设置 `jarvis.commandPath`。

- **Q: 后端进程启动后立刻退出？**
  - A: 查看 Chat 中的 system 输出（stderr），常见原因是 Jarvis 配置缺失（API key / config.yaml），或 Python 版本不匹配（Jarvis 需要 Python 3.12）。

- **Q: 我想让“资源管理器选中文件”自动读取文件内容，而不是只传路径。**
  - A: 目前实现传的是路径列表（更轻量、更安全）。如果你希望自动读文件内容，可以继续增强（需做大小阈值与忽略规则）。

