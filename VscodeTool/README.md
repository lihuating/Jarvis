# Jarvis VSCodeTool

本目录是一个 VSCode 扩展（TypeScript），提供：

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

## 构建/安装/使用完整文档

请阅读 `BUILD_INSTALL_USAGE.md`。

## 配置

- `jarvis.backend`: `jca` / `jvs`（默认 `jca`）
- `jarvis.commandPath`: 可选后端命令绝对路径
- `jarvis.nonInteractive`: 是否加 `-n`（默认 true）
- `jarvis.disableReview`: 仅对 `jca`，是否加 `--disable-review`（默认 true）

