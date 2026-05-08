# Jarvis VSCodeTool

本目录是一个 VSCode / Cursor 扩展（TypeScript），提供：

- Chat 窗口（Webview）
- 支持注入：选区 / 当前文件 / 选取路径（资源管理器）
- 后端可选 `jca`（默认）或 `jvs`

## 开发与运行

在 VSCode 打开本目录：

1. 安装依赖

```bash
npm install
```

2. 编译

```bash
npm run compile
```

3. 按 `F5` 启动 Extension Development Host

在命令面板运行：
- `Jarvis: Open Chat`

## 安装说明（必读）

**本扩展未上架扩展市场**，在商店里搜索「Jarvis」一般**无法安装**。请任选其一：

1. **从 VSIX 安装**：在仓库 `VscodeTool/` 下执行 `npm install && npm run compile && npx @vscode/vsce package`，再用 VS Code / Cursor 的 **Install from VSIX** 安装生成的 `.vsix`；或用命令行 `code --install-extension xxx.vsix` / `cursor --install-extension xxx.vsix`。
2. **开发模式**：在本目录打开工作区，`npm install && npm run compile` 后按 **F5** 启动 Extension Development Host。

详见 `BUILD_INSTALL_USAGE.md`。

## 构建/安装/使用完整文档

请阅读 `BUILD_INSTALL_USAGE.md`。

## 配置

- `jarvis.backend`: `jca` / `jvs`（默认 `jca`）
- `jarvis.commandPath`: 可选后端命令绝对路径
- `jarvis.nonInteractive`: 是否加 `-n`（默认 true）
- `jarvis.disableReview`: 仅对 `jca`，是否加 `--disable-review`（默认 true）

