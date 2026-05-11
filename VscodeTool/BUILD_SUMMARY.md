# Jarvis VSCode 插件构建总结

## 构建成功！✅

Jarvis VSCode 插件已成功构建，生成了可用于离线安装的 `.vsix` 文件。

## 构建产物

### 主要文件

- **jarvis-vscode-tool-0.2.0.vsix** (14KB) - VSCode 插件安装包
  - 位置：`/media/vdc/code/Jarvis/VscodeTool/`
  - 用途：离线安装到 VSCode

### 支持文件

- **INSTALL.md** - 详细安装指南
- **BUILD_INSTALL_USAGE.md** - 构建和使用说明
- **README.md** - 快速参考
- **build.sh** - 自动化构建脚本

## 安装方法

### 方法 1: 命令行安装（推荐）

```bash
cd /media/vdc/code/Jarvis/VscodeTool
code --install-extension jarvis-vscode-tool-0.2.0.vsix
```

### 方法 2: VSCode 图形界面

1. 打开 VSCode
2. 按 `Ctrl+Shift+X` 打开扩展面板
3. 点击右上角 `...` 菜单
4. 选择 **"从 VSIX 安装..."**
5. 选择 `jarvis-vscode-tool-0.2.0.vsix` 文件
6. 点击安装

### 方法 3: 使用构建脚本

```bash
cd /media/vdc/code/Jarvis/VscodeTool
./build.sh
```

## 插件功能

✅ **侧边栏 Chat 面板** - 与 Jarvis AI 实时交互  
✅ **上下文注入** - 支持选区/当前文件/资源管理器路径  
✅ **后端切换** - 支持 jca（代码代理）和 jvs（通用代理）  
✅ **命令执行** - 自动调用 Jarvis 后端命令  
✅ **配置管理** - 灵活的插件配置选项  
✅ **进程管理** - 启动/停止后端进程  

## 配置要求

### 系统要求

- **VSCode**: ≥ 1.90.0
- **Node.js**: ≥ 18.0.0
- **Jarvis 后端**: 需要安装 Jarvis Python 包

### Jarvis 后端安装

```bash
# 在项目根目录
pip install -e .

# 或使用 uv
uv tool install git+https://github.com/skyfireitdiy/Jarvis.git
```

### 插件配置

在 VSCode 设置中搜索 `Jarvis`，配置以下选项：

- `jarvis.backend`: `jca` (默认) 或 `jvs`
- `jarvis.commandPath`: 可选，Jarvis 命令的绝对路径
- `jarvis.nonInteractive`: `true` (推荐)
- `jarvis.disableReview`: `true` (推荐)

## 使用示例

### 打开 Chat

```text
Ctrl+Shift+P → Jarvis: Open Chat
```

### 发送代码选区

1. 在编辑器中选择代码
2. `Ctrl+Shift+P` → `Jarvis: Send Selection to Chat`
3. 在 Chat 窗口输入问题

### 发送整个文件

1. 打开要分析的文件
2. `Ctrl+Shift+P` → `Jarvis: Send Current File to Chat`
3. 在 Chat 窗口输入问题

## 构建细节

### 使用的工具

- **esbuild**: 0.25.12 - TypeScript 编译
- **@vscode/vsce**: 2.24.0 - VSIX 打包
- **sharp**: 图像生成（用于创建图标）
- **typescript**: 5.5.0 - TypeScript 编译器

### 构建步骤

1. 安装依赖：`npm install`
2. 编译代码：`npm run build`
3. 打包 VSIX: `vsce package`

### 生成的图标

- `media/jarvis-128.png` (128x128) - 插件图标
- `media/jarvis-activitybar.png` (24x24) - 活动栏图标

图标设计：绿色到蓝色渐变圆形，中间白色 "J" 字母

### VSIX 内容

```text
jarvis-vscode-tool-0.2.0.vsix
├── [Content_Types].xml
├── extension.vsixmanifest
└── extension/
    ├── LICENSE.txt (1.04 KB)
    ├── package.json (3.68 KB)
    ├── readme.md
    ├── dist/
    │   └── extension.js (13.02 KB)
    └── media/
        ├── jarvis-128.png (3.74 KB)
        └── jarvis-activitybar.png (0.65 KB)
```

## 验证安装

安装成功后，在 VSCode 中：

1. ✅ 左侧活动栏出现 Jarvis 图标（绿色/蓝色渐变圆形）
2. ✅ 命令面板显示 Jarvis 相关命令
3. ✅ 可以打开 Chat 窗口
4. ✅ 可以发送代码上下文
5. ✅ 后端命令正常执行

## 故障排查

### 常见问题

**问题**: 找不到 `jca` 或 `jvs` 命令  
**解决**: 在设置中配置 `jarvis.commandPath` 为完整路径

**问题**: Chat 窗口无响应  
**解决**: 检查 Jarvis 配置 (`~/.jarvis/config.yaml`) 和 API Key

**问题**: 图标不显示  
**解决**: 重启 VSCode，或重新安装插件

详细故障排查请参考 `INSTALL.md`。

## 重新构建

如果需要重新构建（例如修改了代码）：

```bash
cd /media/vdc/code/Jarvis/VscodeTool

# 清理旧文件
rm -f *.vsix

# 重新构建
./build.sh

# 或手动执行
npm install
npm run build
vsce package --no-yarn
```

## 分发给其他人

将以下文件分发给需要安装的用户：

1. `jarvis-vscode-tool-0.2.0.vsix` - 插件安装包
2. `INSTALL.md` - 安装指南

用户只需运行：

```bash
code --install-extension jarvis-vscode-tool-0.2.0.vsix
```

## 版本信息

- **插件版本**: 0.2.0
- **构建日期**: 2026-05-11
- **发布者**: skyfireitdiy
- **许可证**: MIT

## 下一步

### 可选增强

1. **添加更多图标尺寸** - 适配不同 DPI 屏幕
2. **本地化** - 支持多语言界面
3. **自动更新** - 集成 VSCode 扩展市场
4. **测试套件** - 添加单元测试和集成测试
5. **性能优化** - 优化大文件处理

### 发布到市场

如果希望发布到 VSCode 扩展市场：

```bash
# 登录到 Visual Studio Marketplace
vsce login skyfireitdiy

# 发布
vsce publish
```

注意：发布前需要申请发布者 ID 和配置认证。

## 相关资源

- **项目主页**: <https://github.com/skyfireitdiy/Jarvis>
- **在线文档**: <https://skyfireitdiy.github.io/Jarvis/>
- **问题反馈**: <https://github.com/skyfireitdiy/Jarvis/issues>

---

**构建完成时间**: 2026-05-11  
**构建状态**: ✅ 成功  
**插件状态**: ✅ 可用于离线安装
