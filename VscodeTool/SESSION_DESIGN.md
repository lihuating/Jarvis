# VSCode 插件会话保持设计方案

## 问题分析

当前实现：每次用户发送消息都是独立的 `jca -n -T "<prompt>"` 调用，没有上下文关联。

目标：实现多轮对话，第一个问题和第二个问题之间有关联性。

---

## 方案 1：使用后端会话恢复（推荐）⭐

### 原理

利用 Jarvis 后端已有的 `restore_session` 功能，通过 `--session-name` 参数指定会话名称，实现上下文保持。

### 实现步骤

#### 1. 修改 extension.ts

在 `JarvisChatPanel` 类中添加会话管理：

```typescript
class JarvisChatPanel {
  private sessionName: string | null = null;  // 会话名称
  
  // 首次运行时创建会话，后续复用
  private async runBackend(backend: Backend, prompt: string) {
    // ... 现有代码 ...
    
    const args: string[] = [];
    args.push("-n");
    
    // 关键：使用固定的会话名称
    if (!this.sessionName) {
      this.sessionName = `vscode-${Date.now()}`;
    }
    args.push("--session-name", this.sessionName);
    
    args.push("-T", prompt);
    
    // ... 其余代码不变 ...
  }
  
  // 新建会话时重置
  public newChat() {
    this.sessionName = null;
    this.post({ type: "appendSystem", text: "已新建会话，上下文已清空" });
  }
}
```

#### 2. 添加"新建会话"按钮

在 Chat 界面顶部添加按钮：

```html
<button class="btn" id="btnNewChat">New Chat</button>
```

```javascript
const btnNewChat = document.getElementById('btnNewChat');
btnNewChat.addEventListener('click', () => {
  vscode.postMessage({ type: 'newChat' });
});
```

### 后端命令示例

```bash
# 第一次调用
jca -n --session-name vscode-1234567890 -T "分析这个函数的逻辑"

# 第二次调用（恢复同一个会话）
jca -n --session-name vscode-1234567890 -T "如何优化它？"

# 第三次调用（继续同一个会话）
jca -n --session-name vscode-1234567890 -T "帮我实现优化"
```

### 配置文件支持

在 `package.json` 中添加配置：

```json
{
  "jarvis.sessionMode": {
    "type": "string",
    "enum": ["persistent", "single-use"],
    "default": "persistent",
    "description": "会话模式：persistent（持久会话）或 single-use（单次会话）"
  }
}
```

---

## 方案 2：使用 tmux 长连接（更复杂但更强大）

### 原理

在 tmux 中启动一个持久的 jca 会话，VSCode 插件通过 tmux 发送命令到该会话。

### 实现步骤

#### 1. 启动持久会话

```typescript
private async startPersistentSession(): Promise<string> {
  const sessionName = `vscode-jarvis-${Date.now()}`;
  
  // 在 tmux 中启动 jca 交互模式
  const cmd = `tmux new-session -d -s ${sessionName} 'jca'`;
  await exec(cmd);
  
  return sessionName;
}
```

#### 2. 发送命令到会话

```typescript
private async sendToSession(sessionName: string, prompt: string): Promise<void> {
  // 通过 tmux send-keys 发送输入
  const cmd = `tmux send-keys -t ${sessionName} '${prompt}' Enter`;
  await exec(cmd);
  
  // 等待并捕获输出（需要更复杂的逻辑）
}
```

### 优点
- ✅ 真正的实时交互
- ✅ 无会话加载开销
- ✅ 可以查看历史输出

### 缺点
- ❌ 实现复杂度高
- ❌ 输出捕获困难
- ❌ 依赖 tmux
- ❌ 错误处理复杂

---

## 方案 3：使用 SDK 直接调用（最优雅但需要后端支持）

### 原理

通过 Python SDK 直接调用 CodeAgent，保持 Agent 实例不销毁。

### 实现方式

需要创建一个 Node.js 桥接服务：

```typescript
// 简化的示例
import { spawn } from 'child_process';

class JarvisBridge {
  private agent: any = null;
  
  async initialize() {
    // 启动 Python 桥接进程
    this.agent = spawn('python', ['-c', `
from jarvis.jarvis_code_agent import CodeAgent
import json
import sys

agent = CodeAgent()
while True:
    line = sys.stdin.readline()
    if not line:
        break
    result = agent.run(line.strip())
    print(json.dumps(result), flush=True)
    sys.stdout.flush()
`], {
      stdio: ['pipe', 'pipe', 'pipe']
    });
  }
  
  async sendPrompt(prompt: string): Promise<string> {
    this.agent.stdin.write(prompt + '\n');
    // 等待响应...
  }
}
```

### 优点
- ✅ 最优雅的架构
- ✅ 无会话加载开销
- ✅ 完整的对象状态保持

### 缺点
- ❌ 需要后端支持 STDIN/STDOUT 协议
- ❌ 需要编写桥接代码
- ❌ 进程管理复杂

---

## 推荐方案：方案 1（会话恢复）

### 理由

1. **改动最小**：只需修改 VSCode 插件，后端无需改动
2. **功能完整**：利用已有的会话恢复机制
3. **稳定可靠**：基于成熟的会话管理功能
4. **易于实现**：代码改动少于 50 行

### 实现清单

- [ ] 在 `JarvisChatPanel` 中添加 `sessionName` 属性
- [ ] 修改 `runBackend` 方法，添加 `--session-name` 参数
- [ ] 在 Chat 界面添加"New Chat"按钮
- [ ] 添加配置项 `jarvis.sessionMode`
- [ ] 测试多轮对话上下文保持

### 预期效果

```
用户：分析 src/user/service.py 的登录逻辑
AI:  [分析结果...]

用户：如何优化它？  ← 基于上面的分析
AI:  [优化建议...]  ← 理解上下文

用户：帮我实现方案 2  ← 继续上面的对话
AI:  [实现代码...]   ← 保持上下文
```

---

## 技术细节

### 会话文件位置

```
~/.jarvis/sessions/
├── vscode-1234567890.json
├── vscode-1234567891.json
└── ...
```

### 会话恢复流程

```
1. 用户发送第一个问题
   ↓
2. 创建会话文件 vscode-xxx.json
   ↓
3. 调用 jca --session-name vscode-xxx
   ↓
4. 用户发送第二个问题
   ↓
5. 恢复会话 vscode-xxx.json
   ↓
6. 调用 jca --session-name vscode-xxx
   ↓
7. 上下文保持！
```

### 会话清理

- 自动清理：Jarvis 后端会自动保留最近 10 个会话
- 手动清理：点击"New Chat"按钮创建新会话
- 会话命名：使用 `vscode-<timestamp>` 格式

---

## 总结

**推荐方案 1**，原因：
- ✅ 改动小（<50 行代码）
- ✅ 无需修改后端
- ✅ 功能完整
- ✅ 稳定可靠
- ✅ 易于维护
