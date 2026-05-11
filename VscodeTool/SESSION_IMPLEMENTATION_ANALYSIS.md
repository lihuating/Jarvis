# 会话保持实现分析 - jca vs jvs

## ❓ 问题

> 上述方案是只针对 jca 模式吗，jvs 模式不会被波及吗？

## ✅ 答案

**当前实现对 jca 和 jvs 都应用了会话保持**，但**后端实际上不支持 `--session-name` 参数**！

---

## 🔍 后端参数分析

### jvs 和 jca 的共同点

jvs 和 jca 都使用同一个 CLI 入口：`src/jarvis/jarvis_agent/jarvis.py`

**支持的会话相关参数**：
```python
restore_session: bool = typer.Option(
    False,
    "-r",
    "--restore-session",
    help="从 .jarvis/saved_session.json 恢复会话",
)
```

**注意**：❌ **没有 `--session-name` 参数！**

### 当前 VSCode 插件实现

```typescript
// extension.ts - runBackend 方法
if (sessionMode === "persistent") {
  if (!this.sessionName) {
    this.sessionName = `vscode-${Date.now()}`;
  }
  args.push("--session-name", this.sessionName);  // ← 这个参数后端不支持！
}
```

---

## ⚠️ 问题严重性

### 当前行为

当 VSCode 插件执行：
```bash
jca -n --session-name vscode-1234567890 -T "分析代码"
```

后端会：
1. ✅ 识别 `-n` (non-interactive)
2. ❌ **忽略 `--session-name`** (未定义的参数)
3. ✅ 识别 `-T` (task)

**结果**：会话保持**不会生效**，每次都是独立的调用！

---

## 🎯 正确的实现方案

### 方案 A：使用 `--restore-session` 参数（需要修改后端）

**后端需要添加的功能**：
```python
session_name: Optional[str] = typer.Option(
    None,
    "--session-name",
    help="指定会话名称，用于多轮对话",
)
```

**VSCode 插件调用**：
```bash
# 第一次
jca -n --session-name vscode-1234567890 -T "分析代码"
# 创建会话：vscode-1234567890.json

# 第二次
jca -n --session-name vscode-1234567890 -T "如何优化？"
# 恢复会话：vscode-1234567890.json
```

### 方案 B：使用固定的会话文件（无需修改后端）

利用现有的 `--restore-session` 机制：

```typescript
private sessionFile: string | null = null;

private async runBackend(backend: Backend, prompt: string) {
  // ...
  
  if (sessionMode === "persistent") {
    if (!this.sessionFile) {
      // 第一次运行：创建临时文件作为会话标识
      this.sessionFile = path.join(
        os.homedir(),
        '.jarvis',
        'sessions',
        `vscode-${Date.now()}.json`
      );
    }
    
    // 每次都尝试恢复会话
    args.push("-r", "--restore-session");
    // 需要修改后端支持从指定文件恢复
  }
}
```

**问题**：当前 `--restore-session` 只从固定的 `saved_session.json` 恢复，不支持自定义文件名。

### 方案 C：修改后端支持自动会话管理（推荐）⭐

**后端修改**：
1. 添加 `--session-name` 参数
2. 自动在 `~/.jarvis/sessions/` 目录创建/恢复会话文件
3. 支持 jca 和 jvs 两种模式

**VSCode 插件**：保持当前实现不变

---

## 📊 jca vs jvs 会话需求对比

| 特性 | jca (代码代理) | jvs (通用代理) |
|------|---------------|---------------|
| 多轮对话需求 | ✅ 高（代码审查、修复、优化） | ✅ 中（问题分析、方案讨论） |
| 上下文重要性 | ✅ 非常高（代码状态、git commit） | ✅ 高（问题背景、已收集信息） |
| 会话文件内容 | 代码 diff、git 状态、工具调用 | 对话历史、工具调用 |
| 使用频率 | ✅ 高频连续对话 | ✅ 中频连续对话 |

**结论**：**jca 和 jvs 都需要会话保持功能**

---

## 🔧 正确的实现（需要后端支持）

### 后端修改清单

需要在 `src/jarvis/jarvis_agent/jarvis.py` 添加：

```python
# 添加 session_name 参数
session_name: Optional[str] = typer.Option(
    None,
    "--session-name",
    help="指定会话名称，用于多轮对话上下文保持",
)

# 在 run_cli 函数中使用
if session_name:
    # 设置会话文件路径
    session_file = os.path.join(
        os.path.expanduser("~/.jarvis/sessions"),
        f"{session_name}.json"
    )
    # 自动启用会话恢复
    restore_session = True
    # 保存会话时使用指定名称
    set_config("session_file", session_file)
```

### VSCode 插件实现（当前已正确）

```typescript
// 对 jca 和 jvs 都应用会话保持
const sessionMode = this.getSessionMode();
if (sessionMode === "persistent") {
  if (!this.sessionName) {
    this.sessionName = `vscode-${Date.now()}`;
  }
  args.push("--session-name", this.sessionName);  // ← 需要后端支持
}
```

---

## 🎯 推荐方案

### 短期方案（无需修改后端）

**使用 tmux 长连接**：
- 在 tmux 中启动一个持久的 jca/jvs 会话
- VSCode 插件通过 tmux send-keys 发送输入
- 真正的实时交互，完整的上下文保持

**缺点**：
- 实现复杂
- 输出捕获困难
- 依赖 tmux

### 中期方案（修改后端）⭐

**添加 `--session-name` 参数**：
- 修改 `jarvis.py` 添加参数支持
- 自动管理会话文件
- VSCode 插件无需修改

**优点**：
- 实现简单
- 对 jca 和 jvs 都有效
- 用户无感知

### 长期方案（架构优化）

**SDK 直接调用**：
- 创建 Python 桥接服务
- VSCode 通过 STDIN/STDOUT 与 Agent 通信
- Agent 实例常驻内存

**优点**：
- 最佳性能
- 完整状态保持
- 无会话加载开销

---

## 📝 总结

### 当前状态

| 组件 | 状态 |
|------|------|
| VSCode 插件实现 | ✅ 已实现（对 jca 和 jvs 都应用） |
| 后端参数支持 | ❌ 不支持 `--session-name` |
| 实际效果 | ❌ 会话保持**不生效** |

### 影响范围

- ✅ **jca 和 jvs 都被波及**（插件代码对两者都添加 `--session-name`）
- ❌ **但都无效**（后端忽略未知参数）

### 下一步

**必须修改后端**才能实现会话保持功能！

**推荐修改**：
1. 在 `jarvis.py` 添加 `--session-name` 参数
2. 实现会话文件自动管理
3. 对 jca 和 jvs 都有效

---

## 🔗 相关文件

- `src/jarvis/jarvis_agent/jarvis.py` - 需要修改的主文件
- `src/jarvis/jarvis_agent/session_manager.py` - 会话管理器
- `VscodeTool/src/extension.ts` - VSCode 插件实现（已正确）
