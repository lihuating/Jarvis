# 常见 Jarvis 知识点解答

本文档记录 Jarvis 使用过程中的常见疑问和解答。

---

## 📚 核心概念

### Q1: Rule、Tools、Memory、Methodologies 有什么区别？

**A:** 这五个概念是 Jarvis 的核心组成部分，各有不同的作用和存储方式：

#### 📊 五大组件对比表

| 组件 | 类型 | 存储内容 | 主要作用 | 是否持久化 |
|------|------|----------|----------|------------|
| **rule** | 索引文件 | 规则/技能的引用和描述 | 注册和定位规则 | ✅ 是 |
| **rules/** | 目录 | Markdown 文档 | 具体的行为规范和指导 | ✅ 是 |
| **tools/** | 目录 | 可执行代码 | 扩展工具能力 | ✅ 是 |
| **memory/** | 目录 | JSON 数据 | 跨会话记忆存储 | ✅ 是 |
| **methodologies/** | 目录 | 方法论模板 | 问题解决流程指导 | ✅ 是 |

#### 🔄 工作流程示例

当用户发起请求时，Jarvis 的执行流程如下：

```
用户请求
  ↓
## 1. 查找 rule (索引)
  根据任务描述在 rule 索引中查找相关规则
  ↓
## 2. 加载 rules/ 中的具体规则
  从内置规则、项目规则或中心规则库加载匹配的规则文件
  ↓
## 3. 调用 tools/ 中的工具执行
  根据规则指导，调用相应的工具执行具体操作
  ↓
## 4. 从 memory/ 获取历史信息
  检索相关的记忆信息，利用历史经验
  ↓
## 5. 使用 methodologies/ 中的方法论
  加载相似任务的成功方法论，指导执行流程
  ↓
## 6. 执行并保存结果到 memory/
  执行任务，并将关键信息保存到记忆系统
```

#### 📝 详细说明

**1. rule（规则索引）**
- **作用**：电话簿，告诉系统有什么规则
- **存储**：索引文件，包含规则的引用和描述
- **特点**：快速定位和匹配规则

**2. rules/（规则目录）**
- **作用**：使用手册，告诉系统怎么做
- **存储**：Markdown 文档，包含具体的行为规范和指导
- **特点**：
  - YAML 头部：描述和触发条件
  - Markdown 内容：具体的规则和步骤
  - 支持自动匹配和加载

**3. tools/（工具目录）**
- **作用**：工具箱，提供实际可用的工具
- **存储**：可执行的 Python 代码
- **特点**：
  - 继承自 `Tool` 基类
  - 支持自定义扩展
  - 按任务智能筛选

**4. memory/（记忆目录）**
- **作用**：大脑，记住的信息
- **存储**：JSON 数据文件
- **特点**：
  - 三层架构：短期、项目长期、全局长期
  - 支持标签化检索
  - 跨会话持久化

**5. methodologies/（方法论目录）**
- **作用**：教程，解决问题的方法
- **存储**：方法论模板（JSON 格式）
- **特点**：
  - 从历史任务中提取成功模式
  - 支持自动匹配和加载
  - 可通过中心化仓库共享

#### 💡 总结

```
• rule    = 电话簿（告诉有什么）
• rules/  = 使用手册（告诉怎么做）
• tools/  = 工具箱（实际可用的工具）
• memory/ = 大脑（记住的信息）
• methodologies/ = 教程（解决问题的方法）
```

这五个组件相互配合，共同构成了 Jarvis 的强大能力！

---

## 🛠️ 工具使用

### Q2: 如何使用工具执行任务？

**A:** Jarvis 支持通过自然语言调用工具，工具调用格式如下：

```
{TOOL_CALL}
{
  "want": "想要从执行结果中获取到的信息",
  "name": "工具名称",
  "arguments": {
    "param1": "值1",
    "param2": "值2"
  }
}
{TOOL_CALL}
```

**示例：**
```jsonnet
{TOOL_CALL}
{
  "want": "查看 src/jarvis/jarvis_agent/ 目录下的文件列表",
  "name": "list_directory",
  "arguments": {
    "path": "/media/vdc/code/Jarvis/src/jarvis/jarvis_agent"
  }
}
{TOOL_CALL}
```

### Q3: 如何一次调用多个工具？

**A:** 支持一次调用多个工具，但有以下限制：

```
{TOOL_CALL}
{"name": "tool1", "arguments": {...}}
{TOOL_CALL}

{TOOL_CALL}
{"name": "tool2", "arguments": {...}}
{TOOL_CALL}
```

**重要限制：**
- 多个工具调用之间必须**没有相互依赖关系**
- 工具 A 的执行结果不能作为工具 B 的输入参数
- 如果工具之间存在依赖关系，必须分多次调用

---

## 📋 任务列表管理

### Q4: 如何使用任务列表进行任务拆解？

**A:** 使用 `task_list_manager` 工具进行任务拆解和管理：

**1. 创建任务列表并添加任务：**
```jsonnet
{TOOL_CALL}
{
  "want": "创建任务列表，包含3个子任务",
  "name": "task_list_manager",
  "arguments": {
    "action": "add_tasks",
    "main_goal": "重新对比 Jarvis 和 Jarvis_sky 目录",
    "background": "需要对比两个目录的代码差异，识别修改并同步文件",
    "tasks_info": [
      {
        "task_name": "对比代码差异",
        "task_desc": "使用 diff 工具对比两个目录的代码文件",
        "expected_output": "1) 差异报告 2) 修改文件列表",
        "agent_type": "main",
        "dependencies": []
      },
      {
        "task_name": "识别修改",
        "task_desc": "分析差异，识别具体的修改内容",
        "expected_output": "修改分析报告",
        "agent_type": "main",
        "dependencies": ["对比代码差异"]
      }
    ]
  }
}
{TOOL_CALL}
```

**2. 执行任务：**
```jsonnet
{TOOL_CALL}
{
  "want": "执行第一个任务",
  "name": "task_list_manager",
  "arguments": {
    "action": "execute_task",
    "task_id": "task-1",
    "additional_info": "使用 diff 命令对比两个目录"
  }
}
{TOOL_CALL}
```

**3. 查看任务状态：**
```jsonnet
{TOOL_CALL}
{
  "want": "查看当前任务列表状态",
  "name": "task_list_manager",
  "arguments": {
    "action": "get_task_list_summary"
  }
}
{TOOL_CALL}
```

### Q5: 任务列表显示格式是怎样的？

**A:** 任务列表会以 Plan 风格显示，例如：

```
📋 任务步骤拆分
  ✔  Plan 更新待办事项列表（2个待处理，1个进行中，1个已完成）
     ·已更新待办事项列表
       ⎿ ✔ 已完成的任务名
         ☐ 待执行的任务名
         ⎿ 🔄 正在进行的任务名
```

**状态说明：**
- ✔ 已完成（completed）
- ☐ 待处理（pending）
- 🔄 进行中（running）
- ❌ 失败（failed）
- ⏭️ 已放弃（abandoned）

---

## 🧠 记忆管理

### Q6: 如何使用记忆功能？

**A:** 使用 `memory` 工具进行记忆管理：

**1. 保存记忆：**
```jsonnet
{TOOL_CALL}
{
  "want": "记住项目使用 Python 3.12",
  "name": "memory",
  "arguments": {
    "action": "save",
    "fact": "项目使用 Python 3.12 版本"
  }
}
{TOOL_CALL}
```

**2. 检索记忆：**
```jsonnet
{TOOL_CALL}
{
  "want": "查找关于 Python 的记忆",
  "name": "memory",
  "arguments": {
    "action": "retrieve",
    "keyword": "Python"
  }
}
{TOOL_CALL}
```

**3. 清除记忆：**
```jsonnet
{TOOL_CALL}
{
  "want": "清除所有短期记忆",
  "name": "memory",
  "arguments": {
    "action": "clear",
    "memory_type": "short_term"
  }
}
{TOOL_CALL}
```

### Q7: 记忆的三层架构是什么？

**A:** Jarvis 提供三层记忆架构：

1. **短期记忆（Short-term）**
   - 当前会话期间的临时记忆
   - FIFO（先进先出）队列
   - 会话结束自动清除

2. **项目长期记忆（Project Long-term）**
   - 项目级别的知识持久化
   - 跨会话共享
   - 用于存储项目特定信息

3. **全局长期记忆（Global Long-term）**
   - 跨项目的全局知识库
   - 个人级别的知识积累
   - 用于存储通用知识和经验

---

## 📖 方法论

### Q8: 如何使用方法论？

**A:** 方法论会根据任务描述自动匹配和加载：

**加载方法论：**
```jsonnet
{TOOL_CALL}
{
  "want": "加载数据库迁移相关方法论",
  "name": "methodology",
  "arguments": {
    "action": "load",
    "task_description": "需要处理数据库迁移任务"
  }
}
{TOOL_CALL}
```

方法论内容会自动添加到系统提示词中，指导 Agent 执行任务。

### Q9: 方法论是如何生成和存储的？

**A:**
- **生成**：从历史任务中自动提取成功模式
- **存储**：以 JSON 格式存储在 `.jarvis/methodologies/` 目录
- **命名**：使用哈希值命名，避免冲突
- **共享**：支持通过中心化 Git 仓库共享方法论

---

## 🎯 规则系统

### Q10: 规则是如何自动选择的？

**A:** 规则系统根据任务描述自动匹配合适的规则：

1. **触发条件**：规则文件中定义的 `description` 包含触发关键词
2. **匹配算法**：使用关键词匹配和语义分析
3. **加载机制**：自动从内置规则、项目规则、中心规则库中加载
4. **激活反馈**：规则激活时会显示规则路径和描述

**示例规则触发：**
- 用户说"代码审查" → 自动加载 `code_review.md` 规则
- 用户说"性能优化" → 自动加载性能相关规则
- 用户说"安全检查" → 自动加载安全相关规则

### Q11: 如何自定义规则？

**A:** 可以在 `.jarvis/rules/` 目录下创建自定义规则文件：

**规则文件格式：**
```yaml
---
description: 当需要进行自定义操作时使用此规则
---

# 自定义规则名称

## 规则内容

### 必须遵守的原则
- 原则1
- 原则2

### 操作步骤
1. 步骤1
2. 步骤2
```

**创建位置：**
- 项目规则：`.jarvis/rules/`（仅当前项目可用）
- 中心规则库：配置的 Git 仓库（所有项目共享）

---

## 🔧 配置管理

### Q12: 如何配置 LLM 模型？

**A:** 有两种方式配置模型：

**方式1：快速配置**
```bash
jvs --quick-config
```

**方式2：手动编辑配置文件**
编辑 `~/.jarvis/config.yaml`：

```yaml
llm_group: default

llm_groups:
  default:
    normal_llm: gpt-5
    cheap_llm: gpt-3.5-turbo
    smart_llm: gpt-5

llms:
  gpt-5:
    platform: openai
    model: gpt-5
    max_input_token_count: 128000
    llm_config:
      openai_api_key: "your-api-key"
      openai_api_base: "https://api.openai.com/v1"
```

### Q13: 支持哪些 LLM 平台？

**A:** Jarvis 支持以下平台：

- **OpenAI**：GPT-4、GPT-3.5 等
- **Anthropic (Claude)**：Claude Opus、Claude Sonnet 等
- **自定义平台**：可通过扩展支持其他平台

---

## 🎨 交互体验

### Q14: 如何使用 Agent 性格系统？

**A:** Jarvis 提供多种 Agent 性格规则，可根据任务类型选择：

**可用性格：**
- 默认性格：平衡型，适合大多数场景
- 严谨型：注重代码质量和规范
- 创意型：鼓励创新和探索
- 简洁型：简洁明了的输出

**使用方式：**
系统会根据任务类型自动推荐合适的性格，也可以在配置中指定。

### Q15: 如何优化交互体验？

**A:** 以下是一些优化建议：

1. **使用快捷命令**：
   - `jvs` - 通用 AI 代理
   - `jca` - 代码专用代理
   - `jgc` - Git 提交
   - `jsec` - 安全分析

2. **启用工具确认**：
   ```yaml
   execute_tool_confirm: true
   ```

3. **调整工具过滤阈值**：
   ```yaml
   tool_filter_threshold: 30
   ```

4. **启用进度显示**：
   长时间操作会自动显示进度提示

---

## 🚀 常见问题

### Q16: 如何处理工具执行超时？

**A:** Jarvis 有以下超时机制：

- **交互模式**：无超时限制
- **非交互模式**：5 分钟超时限制
- **后台任务**：可配置超时时间

**解决方案：**
1. 使用 `--timeout` 参数调整超时时间
2. 将大任务拆分为多个小任务
3. 使用任务列表管理复杂任务

### Q17: 如何处理 Token 限制？

**A:** Jarvis 提供多种 Token 管理机制：

1. **上下文压缩**：自动压缩历史对话
2. **任务列表分离**：支线任务不污染主 Agent 上下文
3. **智能筛选**：根据任务筛选相关工具和规则
4. **动态计算**：基于剩余 Token 动态调整输出长度

**配置选项：**
```yaml
tool_filter_threshold: 30  # 工具过滤阈值
```

### Q18: 如何调试问题？

**A:** 调试技巧：

1. **启用错误追踪**：
   ```yaml
   print_error_traceback: true
   ```

2. **查看详细日志**：
   ```bash
   jvs --verbose
   ```

3. **使用工具检查**：
   ```bash
   jvs --check
   ```

4. **检查配置**：
   ```bash
   jcfg show
   ```

---

## 📦 安装和更新

### Q19: 如何安装 Jarvis？

**A:** 有多种安装方式：

**方式1：一键安装（推荐）**
```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/skyfireitdiy/Jarvis/main/scripts/install.sh)"
```

**方式2：手动安装**
```bash
git clone https://github.com/skyfireitdiy/Jarvis.git
cd Jarvis
pip3 install -e .
```

**方式3：使用 uv**
```bash
uv tool install git+https://github.com/skyfireitdiy/Jarvis.git
```

### Q20: 如何更新 Jarvis？

**A:** Jarvis 支持自动更新：

- **小版本更新**：后台静默自动更新
- **大版本更新**：显示更新提醒，可选择时机
- **手动更新**：
  ```bash
  git pull
  pip3 install -e .
  ```

---

## 🤝 贡献和支持

### Q21: 如何贡献代码？

**A:** 欢迎贡献代码：

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

**开发约定：**
- 使用 Python 3.12
- 遵循 PEP 8 规范
- 使用 ruff 进行代码检查
- 使用 mypy 进行类型检查

### Q22: 如何获取帮助？

**A:** 获取帮助的方式：

1. **查看文档**：
   - [Jarvis Book](docs/jarvis_book/) - 官方文档
   - [README.md](README.md) - 项目说明
   - [AGENTS.md](AGENTS.md) - 项目分析报告

2. **社区支持**：
   - GitHub: https://github.com/skyfireitdiy/Jarvis
   - Gitee: https://gitee.com/skyfireitdiy/Jarvis

3. **命令行帮助**：
   ```bash
   jvs --help
   jvs --check
   ```

---

## 📌 更多资源

- **官方文档**：[docs/jarvis_book/](docs/jarvis_book/)
- **技术文档**：[docs/technical/](docs/technical/)
- **最佳实践**：[docs/best_practices/](docs/best_practices/)
- **发布说明**：[ReleaseNote.md](ReleaseNote.md)

---

*最后更新：2026-03-09*