# 更新日志 (Changelog)

## [0.2.0] - 2026-05-11

### ✨ 新增功能

#### 会话保持功能
- ✅ 添加 `--session-name` 参数支持，实现多轮对话上下文保持
- ✅ 支持持久会话模式（persistent）和单次会话模式（single-use）
- ✅ 界面顶部显示会话名称（蓝色徽章），实时可见
- ✅ 添加 "New Chat" 按钮，一键重置会话
- ✅ 自动创建和恢复会话文件
- ✅ jca 和 jvs 两个后端都支持会话保持

#### 配置项
- ✅ 新增 `jarvis.sessionMode` 配置项
  - `persistent`（默认）：持久会话模式，保持上下文
  - `single-use`：单次会话模式，每次独立

### 📝 文档更新

- ✅ 新增 `SESSION_FEATURE.md` - 详细功能说明
- ✅ 新增 `SESSION_IMPLEMENTATION_SUMMARY.md` - 实现总结
- ✅ 新增 `SESSION_DESIGN.md` - 设计方案
- ✅ 新增 `SESSION_QUICK_REFERENCE.md` - 快速参考卡片
- ✅ 新增 `BACKWARD_COMPATIBILITY_ANALYSIS.md` - 向后兼容性分析
- ✅ 新增 `SESSION_COMPLETE_SUMMARY.md` - 完整实现总结
- ✅ 更新 `README.md` - 添加会话功能说明
- ✅ 更新 `BUILD_INSTALL_USAGE.md` - 添加会话配置说明

### 🔧 技术改进

- ✅ 修改 `jarvis.py` 添加 `--session-name` 参数
- ✅ 修改 `session_manager.py` 支持自定义会话文件名
- ✅ 修改 `extension.ts` 实现会话管理逻辑
- ✅ 修改 `package.json` 添加会话模式配置
- ✅ 优化界面显示，添加会话名称徽章

### 📊 改进效果

- ✅ 支持多轮对话，问题和回答之间保持上下文
- ✅ 界面友好，会话状态实时可见
- ✅ 灵活配置，满足不同使用场景
- ✅ 自动管理会话文件，最多保留 10 个

---

## [0.1.0] - 2026-04-XX

### ✨ 初始版本

#### 基础功能
- ✅ Chat 窗口（Webview）
- ✅ 支持注入上下文：选区 / 当前文件 / 选取路径（资源管理器）
- ✅ 后端可选 `jca`（默认）或 `jvs`
- ✅ 后端切换功能
- ✅ 上下文模式选择

#### 配置项
- ✅ `jarvis.backend`：`jca` / `jvs`
- ✅ `jarvis.commandPath`：后端命令绝对路径
- ✅ `jarvis.nonInteractive`：是否加 `-n`
- ✅ `jarvis.disableReview`：仅对 `jca`，是否加 `--disable-review`

#### 命令
- ✅ `Jarvis: Open Chat` - 打开 Chat Webview
- ✅ `Jarvis: Send Selection to Chat` - 选区作为上下文
- ✅ `Jarvis: Send Current File to Chat` - 当前文件作为上下文
- ✅ `Jarvis: Send Explorer Selection to Chat` - 选择路径作为上下文
- ✅ `Jarvis: Stop Backend` - 停止后端进程

---

## 版本说明

### 版本号规则

- **主版本号**：重大架构变更或不兼容的更新
- **次版本号**：新增功能或重大改进
- **修订号**：Bug 修复和小改进

### 发布周期

- **主版本**：不定期发布
- **次版本**：每月发布
- **修订版**：每周发布

---

## 升级指南

### 从 0.1.0 升级到 0.2.0

1. **安装新版本**
   ```bash
   code --install-extension jarvis-vscode-tool-0.2.0.vsix
   ```

2. **配置会话模式**（可选）
   ```json
   {
     "jarvis.sessionMode": "persistent"  // 默认值
   }
   ```

3. **使用新功能**
   - 打开 Chat 窗口，自动启用会话保持
   - 查看界面顶部的会话名称显示
   - 点击 "New Chat" 按钮开始新对话

4. **查看文档**
   - 阅读 `SESSION_FEATURE.md` 了解详细功能
   - 阅读 `SESSION_QUICK_REFERENCE.md` 快速上手

---

## 已知问题

### v0.2.0

- 无已知问题

### v0.1.0

- ❌ 多轮对话没有上下文关联（已在 v0.2.0 中修复）

---

## 计划中的功能

### v0.3.0（计划中）

- [ ] 会话列表查看和选择
- [ ] 会话导出/导入功能
- [ ] 会话搜索功能
- [ ] 会话标签/分类

### v0.4.0（未来）

- [ ] 会话共享/协作
- [ ] 会话快照功能
- [ ] 会话过期策略

---

## 贡献者

- Jarvis AI Assistant

---

## 许可证

MIT License
