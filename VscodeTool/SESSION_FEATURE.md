# Jarvis VSCode 插件 - 会话保持功能说明

## 📋 功能概述

**问题**：原实现每次调用都是独立的 `jca -n -T "<prompt>"`，多个问题之间没有上下文关联。

**解决方案**：使用 Jarvis 后端的 `--session-name` 参数，实现多轮对话上下文保持。

---

## ✨ 新增功能

### 1. 持久会话模式（默认）

- ✅ **上下文保持**：第一个问题和第二个问题之间有关联
- ✅ **自动会话管理**：首次对话自动创建会话，后续对话自动恢复
- ✅ **会话名称显示**：在界面顶部显示当前会话名称（蓝色徽章）

### 2. New Chat 按钮

- 🆕 **新建会话**：点击按钮清空上下文，开始新对话
- 🎨 **绿色样式**：易于识别的"New Chat"按钮
- ⚡ **快速重置**：立即重置会话状态

### 3. 会话名称显示

- 🏷️ **蓝色徽章**：在界面顶部显示当前会话名称
- 👁️ **实时可见**：随时了解当前处于哪个会话中
- 🎯 **上下文提示**：看到会话名称就知道是否有历史对话

### 4. 会话模式配置

```json
{
  "jarvis.sessionMode": "persistent"  // 默认：持久会话
}
```

可选值：
- `"persistent"` - 持久会话模式（保持上下文）
- `"single-use"` - 单次会话模式（每次独立）

---

## 🎯 使用示例

### 场景 1：代码分析和优化（多轮对话）

```
用户：[选中一段代码] 分析这段代码的逻辑
AI:   这段代码实现了用户认证功能，包括...

用户：如何优化它的性能？  ← 基于上面的分析
AI:   可以从以下几个方面优化：
      1. 缓存用户信息...
      2. 减少数据库查询...

用户：帮我实现方案 1  ← 继续上面的对话
AI:   好的，已添加缓存层：
      ```python
      @cache(ttl=300)
      def get_user_info(user_id):
          ...
      ```
```

### 场景 2：Bug 修复（多轮对话）

```
用户：src/user/service.py 的登录有问题
AI:   我发现第 45 行的验证逻辑有问题...

用户：具体是什么问题？  ← 询问上面的内容
AI:   在第 45 行，代码没有检查用户是否被禁用...

用户：修复它  ← 基于上下文
AI:   已修复，添加了 is_active 检查...
```

### 场景 3：开始新话题（新建会话）

```
用户：[完成了一个代码审查任务]

用户：[点击 "New Chat" 按钮]
系统：已新建会话，上下文已清空。

用户：现在帮我写一个单元测试  ← 全新的话题
AI:   好的，请问要测试哪个功能？
```

---

## 🔧 技术实现

### 核心代码变更

#### 1. 会话名称管理

```typescript
class JarvisChatPanel {
  private sessionName: string | null = null;  // 会话名称
  
  private async runBackend(backend: Backend, prompt: string) {
    // ...
    
    // 持久会话模式下，使用固定的会话名称
    if (sessionMode === "persistent") {
      if (!this.sessionName) {
        this.sessionName = `vscode-${Date.now()}`;
      }
      args.push("--session-name", this.sessionName);
    }
  }
}
```

#### 2. New Chat 功能

```typescript
private newChat() {
  this.sessionName = null;  // 重置会话名称
  this.post({ type: "setSessionName", sessionName: null });
  this.post({ type: "appendSystem", text: "已新建会话，上下文已清空。" });
}
```

#### 3. 界面更新

- 添加 "New Chat" 按钮（绿色样式）
- 显示会话名称（系统消息中）
- 添加 `jarvis.newChat` 命令

---

## 📊 会话模式对比

| 特性 | persistent（持久） | single-use（单次） |
|------|-------------------|-------------------|
| 上下文保持 | ✅ 是 | ❌ 否 |
| 会话名称 | 固定 | 每次不同 |
| 适用场景 | 多轮对话、复杂任务 | 简单查询、独立问题 |
| 内存占用 | 较高（保持状态） | 较低 |
| 响应速度 | 较快（无需重新加载） | 正常 |

---

## 🚀 安装和配置

### 安装新版本

```bash
cd /media/vdc/code/Jarvis/VscodeTool
code --install-extension jarvis-vscode-tool-0.2.0.vsix
```

### 配置会话模式

#### 方法 1: VSCode 设置界面

1. 打开设置 (`Ctrl+,`)
2. 搜索 `jarvis.sessionMode`
3. 选择 `persistent` 或 `single-use`

#### 方法 2: settings.json

```json
{
  "jarvis.sessionMode": "persistent"
}
```

---

## 📁 会话文件管理

### 会话文件位置

```
~/.jarvis/sessions/
├── vscode-1715424000000.json  ← VSCode 创建的会话
├── vscode-1715424100000.json
└── ...
```

### 会话文件内容

```json
{
  "session_name": "vscode-1715424000000",
  "messages": [
    {"role": "user", "content": "分析这段代码..."},
    {"role": "assistant", "content": "这段代码实现了..."},
    {"role": "user", "content": "如何优化？"},
    {"role": "assistant", "content": "可以从以下几个方面..."}
  ],
  "context": {
    "workspace": "/path/to/project",
    "files": [...]
  }
}
```

### 会话清理

Jarvis 后端会自动管理会话文件：
- ✅ 自动保留最近 10 个会话
- ✅ 自动清理旧会话
- ✅ 手动清理：点击 "New Chat"

---

## 🎨 界面变更

### 顶部工具栏

```
┌─────────────────────────────────────────────────────────┐
│ backend: jca ▼ │ New Chat │ Stop │ ... │ Context ▼    │
└─────────────────────────────────────────────────────────┘
```

### 系统消息示例

```
启动后端 (会话：vscode-1715424000000): jca -n --session-name vscode-1715424000000 -T "分析代码"
```

---

## ⚠️ 注意事项

### 1. 会话名称生成

- 格式：`vscode-<timestamp>`
- 示例：`vscode-1715424000000`
- 每个 VSCode 窗口独立会话

### 2. 会话恢复

- 关闭 VSCode 后再打开，会话**不会**自动恢复
- 需要点击 "New Chat" 开始新会话
- 未来版本可能支持会话持久化

### 3. 内存管理

- 持久会话模式会占用更多内存
- 建议定期点击 "New Chat" 清理旧会话
- 大型项目建议使用单次模式

### 4. 后端兼容性

- 需要 Jarvis 后端支持 `--session-name` 参数
- **Jarvis v2.0.19+** 完全支持（2026-03-06 发布）
- **支持范围**：
  - ✅ `jvs` 命令（通用代理）
  - ✅ `jca` 命令（代码代理）
  - ✅ `jarvis-agent-dispatcher` 命令
  - ✅ `jarvis-code-agent-dispatcher` 命令
- 旧版本后端会忽略此参数，导致会话保持不生效

---

## 🔧 后端实现说明

### 后端参数定义

Jarvis 后端在 `jarvis.py` 中添加了 `--session-name` 参数：

```python
# src/jarvis/jarvis_agent/jarvis.py
session_name: Optional[str] = typer.Option(
    None,
    "--session-name",
    help="指定会话名称，用于多轮对话上下文保持（自动启用会话恢复）",
)
```

### 配置同步逻辑

当使用 `--session-name` 参数时，后端会自动：

```python
# 同步到全局配置
if session_name:
    set_config("restore_session", True)  # 自动启用会话恢复
    set_config("session_name", str(session_name))
```

### SessionManager 处理流程

1. **恢复会话**：`session_manager.py` 的 `restore_session()` 方法会：
   - 检查配置中的 `session_name`
   - 调用 `_find_session_by_name()` 查找匹配的会话文件
   - 如果找到，使用 `restore_session_from_file()` 恢复
   - 如果未找到，返回 False 创建新会话

2. **保存会话**：`save_session()` 方法会：
   - 使用 `current_session_name` 作为文件名前缀
   - 保存到 `~/.jarvis/sessions/{session_name}_saved_session_{agent}_{timestamp}.json`
   - 自动清理旧会话（最多保留 10 个）

### 会话文件命名规则

```
格式：{session_name}_saved_session_{agent_name}_{timestamp}.json

示例：
- vscode-1715424000000_saved_session_Jarvis_20260306_120000.json
- vscode-1715424000000_saved_session_CodeAgent_20260306_120500.json
```

### 支持的命令

所有基于 `jarvis.py` CLI 入口的命令都支持会话保持：

| 命令 | 快捷方式 | 支持会话保持 |
|------|---------|------------|
| jarvis | jvs | ✅ |
| jarvis-agent-dispatcher | jvsd | ✅ |
| jarvis-code-agent | jca | ✅ |
| jarvis-code-agent-dispatcher | jcad | ✅ |

---

## 🔍 故障排查

### 问题 1: 上下文不保持

**检查**：
```bash
# 查看是否使用了 --session-name 参数
# 在 Chat 窗口的系统消息中查看
```

**解决**：
1. 确认 `jarvis.sessionMode` 设置为 `"persistent"`
2. 检查系统消息中是否有会话名称
3. 尝试点击 "New Chat" 重新开始

### 问题 2: New Chat 按钮无响应

**检查**：
- 打开开发者工具查看错误

**解决**：
1. 重启 VSCode
2. 重新安装插件
3. 检查控制台错误

### 问题 3: 会话文件过多

**清理**：
```bash
# 手动清理旧会话
rm ~/.jarvis/sessions/vscode-*.json
```

---

## 📝 版本历史

### v0.2.0 (当前版本) - 会话保持

- ✅ 添加持久会话模式
- ✅ 添加 New Chat 按钮
- ✅ 添加会话模式配置
- ✅ 界面顶部显示会话名称（蓝色徽章）
- ✅ 优化上下文管理

### v0.1.0 (初始版本) - 基础功能

- ✅ 基础 Chat 界面
- ✅ 上下文注入
- ✅ 后端切换

---

## 🎯 最佳实践

### 1. 使用持久会话模式的场景

- ✅ 代码审查和修复
- ✅ 功能开发和完善
- ✅ 问题诊断和解决
- ✅ 学习和探索代码

### 2. 使用单次会话模式的场景

- ✅ 简单问题查询
- ✅ 独立的代码片段
- ✅ 快速测试想法
- ✅ 内存受限环境

### 3. 会话管理技巧

- 💡 完成一个大任务后点击 "New Chat"
- 💡 切换项目时点击 "New Chat"
- 💡 遇到奇怪的行为时点击 "New Chat"
- 💡 定期清理旧会话文件

---

## 📚 相关文档

- [INSTALL.md](INSTALL.md) - 安装指南
- [BUILD_SUMMARY.md](BUILD_SUMMARY.md) - 构建说明
- [SESSION_DESIGN.md](SESSION_DESIGN.md) - 设计方案
- [README.md](README.md) - 快速参考

---

## 🎉 总结

通过 `--session-name` 参数，Jarvis VSCode 插件现在支持：

1. ✅ **多轮对话**：问题和回答之间保持上下文
2. ✅ **智能会话管理**：自动创建和恢复会话
3. ✅ **灵活配置**：可选择持久或单次模式
4. ✅ **用户友好**：New Chat 按钮一键重置

这使得插件更适合复杂的代码开发任务，可以进行连续的对话和迭代改进！
