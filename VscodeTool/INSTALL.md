# Jarvis VSCode 插件安装指南

本文档提供 Jarvis VSCode 插件的详细安装说明。

## 构建产物

- **插件文件**: `jarvis-vscode-tool-0.2.0.vsix` (约 14KB)
- **位置**: `VscodeTool/` 目录

## 前置要求

1. **VSCode 版本**: ≥ 1.90.0
2. **Node.js 版本**: ≥ 18.0.0
3. **Jarvis 后端**: 需要安装 Jarvis Python 包（提供 `jca` 或 `jvs` 命令）

### 安装 Jarvis 后端

```bash
# 方法 1: 使用 pip
pip install -e .

# 方法 2: 使用 uv
uv tool install git+https://github.com/skyfireitdiy/Jarvis.git

# 方法 3: 使用 Docker
docker pull ghcr.io/skyfireitdiy/jarvis:latest
```

## 离线安装方法

### 方法 1: VSCode 图形界面安装

1. 打开 VSCode
2. 按 `Ctrl+Shift+X` 打开扩展面板
3. 点击右上角的 `...` 菜单
4. 选择 **"从 VSIX 安装..."** (Install from VSIX...)
5. 浏览并选择 `jarvis-vscode-tool-0.2.0.vsix` 文件
6. 点击安装，等待完成
7. 重启 VSCode

### 方法 2: 命令行安装

```bash
# 使用 code 命令安装
code --install-extension jarvis-vscode-tool-0.2.0.vsix

# 或者指定完整路径
code --install-extension /media/vdc/code/Jarvis/VscodeTool/jarvis-vscode-tool-0.2.0.vsix
```

### 方法 3: 手动解压安装（高级）

```bash
# 1. 解压 .vsix 文件（实际上是一个 zip 文件）
unzip jarvis-vscode-tool-0.2.0.vsix -d jarvis-extension

# 2. 将 extension 目录复制到 VSCode 扩展目录
cp -r jarvis-extension/extension ~/.vscode/extensions/jarvis-vscode-tool-0.2.0

# 3. 重启 VSCode
```

## 安装验证

安装成功后，在 VSCode 中：

1. 打开命令面板 (`Ctrl+Shift+P`)
2. 输入 `Jarvis`
3. 应该能看到以下命令：
   - `Jarvis: Open Chat` - 打开 Chat 窗口
   - `Jarvis: Send Selection to Chat` - 发送选区到 Chat
   - `Jarvis: Send Current File to Chat` - 发送当前文件到 Chat
   - `Jarvis: Send Explorer Selection to Chat` - 发送资源管理器选择到 Chat
   - `Jarvis: Stop Backend` - 停止后端进程

4. 在左侧活动栏应该能看到 Jarvis 图标（绿色/蓝色渐变圆形，中间有白色"J"字母）

## 配置说明

安装完成后，需要配置插件以连接到 Jarvis 后端：

### 基本配置

打开 VSCode 设置 (`Ctrl+,`)，搜索 `Jarvis`，配置以下选项：

1. **jarvis.backend**: 选择后端命令
   - `jca` (默认) - 代码专用代理
   - `jvs` - 通用代理

2. **jarvis.commandPath**: (可选) Jarvis 命令的绝对路径
   - 如果 `jca`/`jvs` 在 PATH 中可找到，留空即可
   - 否则填写完整路径，如 `/usr/local/bin/jca`

3. **jarvis.nonInteractive**: 是否使用非交互模式
   - 默认：`true` (推荐)

4. **jarvis.disableReview**: (仅对 jca) 是否禁用审查步骤
   - 默认：`true` (减少等待时间)

### 配置文件位置

配置会保存在以下位置：

- **Linux**: `~/.config/Code/User/settings.json`
- **Windows**: `%APPDATA%\Code\User\settings.json`
- **macOS**: `~/Library/Application Support/Code/User/settings.json`

示例配置：

```json
{
  "jarvis.backend": "jca",
  "jarvis.commandPath": "",
  "jarvis.nonInteractive": true,
  "jarvis.disableReview": true
}
```

## 使用方法

### 打开 Chat 窗口

1. 点击左侧活动栏的 Jarvis 图标
2. 或使用命令面板：`Ctrl+Shift+P` → `Jarvis: Open Chat`

### 发送代码上下文

#### 发送选区

1. 在编辑器中选择代码
2. 按 `Ctrl+Shift+P` → `Jarvis: Send Selection to Chat`
3. 在 Chat 窗口输入问题或指令

#### 发送整个文件

1. 打开要分析的文件
2. 按 `Ctrl+Shift+P` → `Jarvis: Send Current File to Chat`
3. 在 Chat 窗口输入问题或指令

#### 发送资源管理器中的文件/目录

1. 在资源管理器中右键点击文件或目录
2. 选择 `Jarvis: Send Explorer Selection to Chat`
3. 在 Chat 窗口输入问题或指令

### 上下文模式选择

在 Chat 窗口顶部，可以选择上下文模式：

- **no context**: 不发送任何上下文
- **selection**: 发送编辑器选区
- **current file**: 发送当前文件全文
- **pick paths…**: 选择文件/目录路径

### 切换后端

在 Chat 窗口顶部，可以通过下拉框切换后端：

- **jca (default)**: 代码专用代理，适合代码生成、修改、审查
- **jvs**: 通用代理，适合一般性问题

## 故障排查

### 问题 1: Chat 窗口能打开，但没有响应

**可能原因**:

- Jarvis 后端未安装
- 后端命令不在 PATH 中
- Python 环境配置问题

**解决方案**:

1. 在终端运行 `jca --help` 或 `jvs --help` 验证命令可用
2. 在 VSCode 集成终端运行 `which jca` 查看命令路径
3. 在设置中配置 `jarvis.commandPath` 为完整路径

### 问题 2: 后端进程启动后立即退出

**可能原因**:

- Jarvis 配置文件缺失 (`~/.jarvis/config.yaml`)
- API Key 未配置
- Python 版本不匹配（需要 Python 3.12）

**解决方案**:

1. 运行 `jvs --quick-config` 快速配置
2. 检查 `~/.jarvis/config.yaml` 是否存在
3. 确认 Python 版本：`python --version`

### 问题 3: 看不到 Jarvis 图标或命令

**可能原因**:

- 插件未正确安装
- VSCode 版本过低

**解决方案**:

1. 检查 VSCode 版本：`Help` → `About` (应 ≥ 1.90.0)
2. 重新安装插件
3. 查看扩展输出：`Help` → `Toggle Developer Tools` → `Console`

### 问题 4: 输出显示乱码或颜色异常

**解决方案**:

1. 确保终端编码为 UTF-8
2. 在设置中添加：

   ```json
   "terminal.integrated.env.linux": {
     "LANG": "zh_CN.UTF-8"
   }
   ```

## 卸载

### 方法 1: VSCode 图形界面

1. 打开扩展面板 (`Ctrl+Shift+X`)
2. 搜索 `Jarvis`
3. 点击卸载按钮

### 方法 2: 命令行

```bash
code --uninstall-extension skyfireitdiy.jarvis-vscode-tool
```

### 方法 3: 手动删除

```bash
# Linux
rm -rf ~/.vscode/extensions/jarvis-vscode-tool-*

# Windows
rmdir /s /q "%USERPROFILE%\.vscode\extensions\jarvis-vscode-tool-*"

# macOS
rm -rf ~/.vscode/extensions/jarvis-vscode-tool-*
```

## 更新

### 手动更新

1. 下载最新版本的 `.vsix` 文件
2. 按照安装步骤重新安装
3. VSCode 会自动替换旧版本

### 自动更新

目前不支持自动更新，需要手动下载安装新版本。

## 技术细节

### 插件结构

```text
jarvis-vscode-tool-0.2.0.vsix
├── [Content_Types].xml
├── extension.vsixmanifest
└── extension/
    ├── package.json           # 插件清单
    ├── LICENSE.txt            # 许可证
    ├── readme.md              # 说明文档
    ├── dist/
    │   └── extension.js       # 编译后的代码
    └── media/
        ├── jarvis-128.png          # 插件图标
        └── jarvis-activitybar.png  # 活动栏图标
```

### 运行机制

1. 插件在 VSCode 工作区根目录启动后端进程
2. 命令行格式：
   - `jca -n -T "<prompt>" --disable-review` (默认)
   - `jvs -n -T "<prompt>"`
3. 输出处理：
   - stdout → assistant 消息（白色）
   - stderr → system 消息（灰色）

### 环境变量

插件会继承 VSCode 的环境变量。如果 Jarvis 需要特定的 Python 环境，请确保：

1. 在启动 VSCode 前激活虚拟环境
2. 或在 `.bashrc`/`.zshrc` 中配置 PATH
3. 或使用 `jarvis.commandPath` 指定包装脚本

## 支持与反馈

- **GitHub Issues**: <https://github.com/skyfireitdiy/Jarvis/issues>
- **Gitee Issues**: <https://gitee.com/skyfireitdiy/Jarvis/issues>
- **文档**: <https://skyfireitdiy.github.io/Jarvis/>

## 版本历史

### v0.2.0 (当前版本)

- ✅ 支持 jca/jvs 后端切换
- ✅ 支持多种上下文注入模式
- ✅ 侧边栏 Chat 界面
- ✅ 资源管理器右键菜单集成
- ✅ 配置管理
- ✅ 进程管理（启动/停止）

### v0.1.0 (初始版本)

- 基础 Chat 功能
- 简单的上下文支持

## 许可证

MIT License - 详见 LICENSE 文件
