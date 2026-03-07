# Jarvis AI 助手 - 项目分析报告

## 项目概述

**Jarvis** 是一个功能强大的 Python AI 应用开发 SDK，为开发者提供灵活的工具和能力来快速构建专业的 AI 应用。与传统的 workflow 形式 Agent 平台（如 Dify）不同，Jarvis 以 Python SDK 的形式提供，强调可编程性和可扩展性。

### 核心定位
- **AI 应用开发 SDK**：提供强大而灵活的基础组件，帮助开发者快速构建专业的 AI 应用
- **高度可编程**：以纯 Python SDK 形式提供，开发者可以自由组合各种能力
- **工具生态丰富**：内置 30+ 工具（代码分析、文件操作、命令执行等），支持自定义扩展

### 主要技术栈
- **编程语言**：Python 3.12
- **核心依赖**：
  - LLM 集成：OpenAI (1.78.1)、Anthropic (>=0.40.0)
  - 代码分析：tree-sitter 系列支持多种语言（Python、JavaScript、TypeScript、Rust、Go、Java、C/C++、Ruby、PHP、SQL、Markdown、HTML、CSS、Bash 等）
  - 浏览器自动化：Playwright (1.48.0)
  - Web 框架：FastAPI (0.115.12)、Uvicorn (0.33.0)
  - 终端 UI：Rich (14.0.0)、Prompt Toolkit (3.0.50)
  - 其他：requests、pyyaml、tiktoken、pillow、markitdown、jsonnet、ddgr、typer、pathspec、plotext 等

### 项目版本
- **当前版本**：2.0.19
- **许可证**：MIT
- **支持平台**：Linux（主要）、Windows（通过 WSL）、macOS

## 项目结构

```
Jarvis/
├── src/jarvis/                    # 源代码目录
│   ├── jarvis_agent/             # 通用 AI 代理核心
│   ├── jarvis_code_agent/        # 代码专用代理
│   ├── jarvis_browser/           # 浏览器自动化工具
│   ├── jarvis_c2rust/            # C→Rust 迁移套件
│   ├── jarvis_config/            # 配置管理
│   ├── jarvis_git_utils/         # Git 工具集
│   ├── jarvis_git_squash/        # Git 提交历史整理
│   ├── jarvis_jck/               # 工具检查模块
│   ├── jarvis_lsp/               # LSP 服务端
│   ├── jarvis_mcp/               # MCP 客户端
│   ├── jarvis_memory_organizer/  # 记忆管理
│   ├── jarvis_methodology/       # 方法论知识库
│   ├── jarvis_platform/          # LLM 平台抽象层
│   ├── jarvis_platform_manager/  # 平台管理器
│   ├── jarvis_rules_index/       # 规则索引管理
│   ├── jarvis_sec/               # 安全分析套件
│   ├── jarvis_smart_shell/       # 智能Shell
│   ├── jarvis_tools/             # 工具系统
│   ├── jarvis_utils/             # 通用工具
│   ├── jarvis_windows/           # Windows 桌面自动化
│   ├── jarvis_data/              # 数据配置
│   └── scripts/                  # 脚本工具
├── tests/                        # 测试套件
│   ├── jarvis_agent/
│   ├── jarvis_code_agent/
│   ├── jarvis_c2rust/
│   ├── jarvis_config/
│   ├── jarvis_git_utils/
│   ├── jarvis_lsp/
│   ├── jarvis_mcp/
│   ├── jarvis_memory_organizer/
│   ├── jarvis_platform/
│   ├── jarvis_platform_manager/
│   ├── jarvis_sec/
│   ├── jarvis_smart_shell/
│   ├── jarvis_tools/
│   ├── jarvis_utils/
│   ├── performance/              # 性能测试
│   ├── regression/               # 回归测试
│   ├── security/                 # 安全测试
│   └── test_utils/               # 测试工具
├── docs/                         # 文档
│   ├── jarvis_book/             # Jarvis Book 官方文档
│   ├── images/
│   └── ...
├── scripts/                      # 脚本工具
│   ├── install.sh
│   ├── install.ps1
│   ├── run_tests.sh
│   └── ...
├── builtin/                      # 内置资源
│   ├── agent/
│   ├── prompts/
│   └── rules/
├── .jarvis/                      # 配置和数据目录
│   ├── config.yaml               # 主配置文件
│   ├── memory/                   # 记忆存储
│   ├── methodologies/            # 方法论
│   ├── evolution/                # 进化记录
│   └── ...
├── pyproject.toml                # 项目配置（现代）
├── setup.py                      # 项目配置（传统）
├── Dockerfile                    # Docker 镜像
├── docker-compose.yml            # Docker Compose 配置
└── README.md                     # 项目说明
```

## 核心组件

### 1. Agent（通用 AI 代理）
**位置**：`src/jarvis/jarvis_agent/`

**功能**：
- 提供完整的任务执行能力
- 支持工具调用、记忆管理、任务规划等核心功能
- 通过 system_prompt 定义行为，可快速定制专用 Agent
- 内置 ARCHER 工作流（Analyze → Rule → Collect → Hypothesize → Execute → Review）

**关键类**：
- `Agent`：基础代理类
- `SessionManager`：会话管理
- `MemoryManager`：记忆管理（三层架构：短期、项目长期、全局长期）
- `TaskListManager`：任务列表管理
- `RulesManager`：规则管理器
- `TaskAnalyzer`：任务分析器

### 2. CodeAgent（代码专用代理）
**位置**：`src/jarvis/jarvis_code_agent/`

**功能**：
- 继承自 Agent，专为代码任务优化
- 内置代码分析、符号查找、精确编辑、构建验证等专业能力
- 支持 Git 操作（提交、变基、diff 分析）
- 自动进行代码审查和构建验证
- 支持会话自动保存和恢复
- 支持默认规则配置

**关键管理器**：
- `BuildValidationManager`：构建验证
- `LintManager`：代码检查
- `DiffManager`：差异分析
- `ImpactManager`：影响分析
- `GitManager`：Git 操作

### 3. 工具系统
**位置**：`src/jarvis/jarvis_tools/`

**内置工具类别**：
- 文件操作：`read_code`、`edit_file`、`write_file`、`list_directory`
- 代码分析：`search_file_content`、`glob`、符号查找、LSP 代码分析
- 命令执行：`run_shell_command`、`execute_script`
- Git 操作：`git_commit`、`git_squash`
- 记忆管理：`memory`（save/retrieve/clear）
- 方法论：`methodology`（load/apply）
- 浏览器：浏览器自动化命令（35+）
- Windows：Windows 桌面自动化命令（13+）
- 其他：PPT 生成、Markdown 处理、文件编码检测等

**扩展能力**：
- 支持自定义工具开发
- 工具过滤机制（避免工具过多干扰模型决策）
- 工具按场景智能筛选

### 4. 平台抽象层
**位置**：`src/jarvis/jarvis_platform/`

**支持的平台**：
- OpenAI
- Anthropic (Claude)
- 可扩展自定义平台

**核心类**：
- `BasePlatform`：平台基类
- `PlatformRegistry`：平台注册表
- 各平台具体实现

### 5. 专业套件

#### 安全分析（jsec）
**位置**：`src/jarvis/jarvis_sec/`
- 启发式扫描
- AI 深度验证
- 支持 C/C++ 和 Rust 语言
- 配置驱动设计

#### C→Rust 迁移（jc2r）
**位置**：`src/jarvis/jarvis_c2rust/`
- 渐进式迁移
- 断点续跑
- 智能库替代

#### 浏览器自动化（jb）
**位置**：`src/jarvis/jarvis_browser/`
- 35+ 浏览器命令
- 守护进程模式
- 基于 Playwright
- 支持 Windows 平台

#### Windows 桌面自动化（jw）
**位置**：`src/jarvis/jarvis_windows/`
- 应用启动/连接
- 点击、输入、截图
- 控件树操作
- 13+ 常用命令

#### 智能Shell（jss）
**位置**：`src/jarvis/jarvis_smart_shell/`
- 实验性智能 Shell 功能
- 交互式命令执行

#### 规则索引（jri）
**位置**：`src/jarvis/jarvis_rules_index/`
- 规则查询和管理
- 支持内置规则和项目规则
- 规则文件定位

#### MCP 客户端
**位置**：`src/jarvis/jarvis_mcp/`
- MCP 协议客户端
- 支持与 MCP 服务器通信

## 主要命令

| 命令 | 快捷方式 | 功能 |
|------|---------|------|
| `jarvis` | `jvs` | 通用 AI 代理 |
| `jarvis-agent-dispatcher` | `jvsd` | jvs 的便捷封装，支持任务派发 |
| `jarvis-agent` | `ja` | AI 代理基础功能 |
| `jarvis-code-agent` | `jca` | 代码专用代理 |
| `jarvis-code-agent-dispatcher` | `jcad` | jca 的便捷封装，支持任务派发 |
| `jarvis-git-commit` | `jgc` | Git 提交信息生成 |
| `jarvis-git-squash` | `jgs` | Git 提交历史整理 |
| `jarvis-platform-manager` | `jpm` | 平台管理 |
| `jarvis-tool` | `jt` | 工具管理 |
| `jarvis-methodology` | `jm` | 方法论管理 |
| `jarvis-memory-organizer` | `jmo` | 记忆管理 |
| `jarvis-sec` | `jsec` | 安全分析 |
| `jarvis-c2rust` | `jc2r` | C→Rust 迁移 |
| `jarvis-config` | `jcfg` | 配置管理 |
| `jarvis-lsp` | `jlsp` | LSP 服务 |
| `jarvis-browser` | `jb` | 浏览器自动化 |
| `jarvis-windows` | `jw` | Windows 桌面自动化 |
| `jarvis-smart-shell` | `jss` | 智能 Shell |
| `jarvis-rules-index` | `jri` | 规则索引管理 |
| `install-playwright` | - | 安装 Playwright 浏览器驱动 |

## 构建和运行

### 安装

#### 一键安装（推荐）
```bash
# Linux/macOS
bash -c "$(curl -fsSL https://raw.githubusercontent.com/skyfireitdiy/Jarvis/main/scripts/install.sh)"

# Windows PowerShell
iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/skyfireitdiy/Jarvis/main/scripts/install.ps1'))
```

#### 手动安装
```bash
git clone https://github.com/skyfireitdiy/Jarvis.git
cd Jarvis
pip3 install -e .
```

#### 使用 uv 安装
```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装 jarvis
uv tool install git+https://github.com/skyfireitdiy/Jarvis.git
```

#### Docker 安装
```bash
# 拉取镜像
docker pull ghcr.io/skyfireitdiy/jarvis:latest

# 使用 Docker Compose
docker-compose run --rm jarvis

# 直接使用 Docker
docker run -it --rm \
  --user "$(id -u):$(id -g)" \
  -v $(pwd):/workspace \
  -v $HOME/.jarvis:/home/jarvis/.jarvis \
  -w /workspace \
  ghcr.io/skyfireitdiy/jarvis:latest
```

### 运行

#### 基本使用
```bash
# 启动通用代理
jvs

# 启动代码代理
jca

# 非交互模式
jvs -n -T "分析代码结构"

# 快速配置
jvs --quick-config

# 工具检查
jvs --check
```

#### SDK 使用
```python
from jarvis.jarvis_code_agent.code_agent import CodeAgent

agent = CodeAgent()
agent.run('修复 user/service.py 中的登录验证 bug')
```

### 测试

```bash
# 运行所有测试
python -m pytest -v

# 运行特定模块测试
python -m pytest tests/jarvis_agent/
python -m pytest tests/jarvis_code_agent/

# 使用测试脚本
cd scripts
./run_tests.sh

# 运行特定标记的测试
pytest -m unit
pytest -m integration
pytest -m slow
pytest -m security
pytest -m performance
pytest -m regression
```

### 构建

```bash
# 构建 Python 包
python -m build

# 构建 Docker 镜像
docker build -t jarvis:latest .
```

## 配置说明

### 主配置文件
**位置**：`~/.jarvis/config.yaml`

**基本配置结构**：
```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/skyfireitdiy/Jarvis/main/docs/schema/config.schema.json

# 基础配置
llm_group: default

# 模型组配置
llm_groups:
  default:
    normal_llm: gpt-5
    cheap_llm: gpt-3.5-turbo
    smart_llm: gpt-5

# 模型定义
llms:
  gpt-5:
    platform: openai
    model: gpt-5
    max_input_token_count: 128000
    llm_config:
      openai_api_key: "your-api-key"
      openai_api_base: "https://api.openai.com/v1"

  claude-opus-4:
    platform: claude
    model: claude-opus-4-20250514
    max_input_token_count: 200000
    llm_config:
      anthropic_api_key: "your-api-key"
      anthropic_base_url: "https://api.anthropic.com"

# 其他配置
print_error_traceback: true
tool_filter_threshold: 30
execute_tool_confirm: true
auto_resume_session: false
```

### 快速配置
```bash
# 快速配置 LLM 平台
jvs --quick-config
```

## 开发约定

### 代码风格
- 使用 Python 3.12
- 遵循 PEP 8 规范
- 使用 ruff 进行代码检查
- 使用 mypy 进行类型检查

### 测试规范
- 测试文件命名：`test_*.py` 或 `*_test.py`
- 测试类命名：`Test*`
- 测试函数命名：`test_*`
- 测试标记：`unit`、`integration`、`slow`、`security`、`performance`、`regression`、`monitoring`

### 文档规范
- 使用中文编写文档
- Markdown 格式
- API 文档使用 docstring
- 主要文档位于 `docs/jarvis_book/`

### 扩展开发
- 自定义工具：放在 `~/.jarvis/tools/` 目录
- 自定义平台：放在 `~/.jarvis/platforms/` 目录
- 自定义方法论：放在 `~/.jarvis/methodologies/` 目录

## 核心概念

### 1. ARCHER 工作流
- **ANALYZE**：分析意图，明确任务目标
- **RULE**：加载相关规则和最佳实践
- **COLLECT**：收集必要信息（只读）
- **HYPOTHESIZE**：提出方案，制定计划（需用户确认）
- **EXECUTE**：按计划执行操作
- **REVIEW**：反思工作成果

### 2. 三层记忆架构
- **短期记忆**：当前会话期间的临时记忆（FIFO）
- **项目长期记忆**：项目级别的知识持久化
- **全局长期记忆**：跨项目的全局知识库

### 3. 工具系统
- **工具注册表**：统一管理所有可用工具
- **工具过滤**：根据任务自动筛选相关工具
- **工具确认**：可选的工具执行前确认机制
- **工具按场景筛选**：智能筛选与当前任务最相关的工具

### 4. 方法论系统
- 将成功经验沉淀为可复用的方法论
- 支持本地和中心化共享
- 可通过 `methodology` 工具加载和应用

### 5. 规则系统
- **自动规则选择**：根据任务描述自动选择合适的规则
- **规则索引**：支持规则查询和管理
- **规则激活反馈**：规则激活时即时反馈
- **规则状态管理**：区分"加载"和"激活"状态

### 6. 会话管理
- **会话自动保存**：程序退出时自动保存会话状态
- **会话自动清理**：自动清理旧会话文件，最多保留10个
- **会话名称智能生成**：自动根据用户输入生成简洁的会话名称
- **历史会话智能检测**：启动时自动检测与当前commit一致的历史会话
- **Git一致性检查**：恢复会话时自动检查代码版本

### 7. Agent 性格系统
- 支持多种 Agent 性格规则
- 可根据任务类型和个人喜好选择合适的性格
- 提供不同风格的交互体验

## 依赖关系

### 核心依赖
```
jarvis_agent (基础)
├── jarvis_platform (LLM 平台抽象)
├── jarvis_tools (工具系统)
├── jarvis_utils (通用工具)
└── jarvis_memory_organizer (记忆管理)

jarvis_code_agent (代码代理)
├── jarvis_agent (继承)
├── jarvis_git_utils (Git 工具)
├── jarvis_jck (工具检查)
└── jarvis_lsp (LSP 代码分析)

jarvis_sec (安全分析)
├── jarvis_agent
└── 自定义扫描工具

jarvis_c2rust (C→Rust 迁移)
├── jarvis_agent
└── Rust 代码生成工具

jarvis_browser (浏览器自动化)
├── jarvis_agent
└── Playwright 集成

jarvis_windows (Windows 自动化)
├── jarvis_agent
└── pywinauto 集成
```

### 外部依赖
- Python 3.12
- Docker（可选）
- Clang（可选，用于 C/C++ 分析）
- Rust（可选，用于 C→Rust 迁移）
- Playwright（用于浏览器自动化）

## 新增功能（v2.0.16 - v2.0.19）

### v2.0.19（2026-03-06）
- 输入交互优化：统一使用"Ctrl+C 退出"
- 空提交处理优化：要求用户必须输入有效内容
- 进度状态显示增强：为长时间操作添加进度提示
- 测试代码精简：移除冗余的 input 模块测试文件

### v2.0.18（2026-03-05）
- 自动规则选择：根据任务描述自动选择合适的规则
- 会话名称生成状态：添加加载状态提示
- 规则系统智能化：重构规则加载机制，提供更直观的规则信息展示
- 代码精简优化：移除冗余 prompt 索引，统一输出格式接口

### v2.0.17（2026-03-01）
- PPT 生成与编辑：完整的 PowerPoint 演示文稿生成和编辑能力
- 规则索引工具：新增 jarvis-rules-index 命令行工具
- 规则描述格式统一：所有规则文件更新描述信息
- 规则系统扩展：支持多种规则来源（内置规则、项目规则）

### v2.0.16（2026-03-01）
- 规则文件加载优化：跳过没有描述信息的规则文件
- 性能指标可视化：显示首 token 响应时间和生成速度
- 更新机制智能化：后台静默检查更新，小版本自动更新
- 配置流程优化：支持手动输入，增加 API 连通性测试

## 常见使用场景

### 1. 代码修改
```bash
jca '为 user/service.py 添加用户 profile 接口'
```

### 2. 代码审查
```bash
jvs '审查 src/ 目录下的代码质量'
```

### 3. Git 提交
```bash
jgc
```

### 4. 安全分析
```bash
jsec config  # 配置扫描参数
jsec scan    # 执行扫描
```

### 5. C→Rust 迁移
```bash
jc2r migrate /path/to/c/project
```

### 6. 浏览器自动化
```bash
jb '访问 https://example.com 并截图'
```

### 7. Windows 自动化
```bash
jw list-windows  # 列出窗口
jw connect <window>  # 连接窗口
```

### 8. PPT 生成
```bash
jm load ppt_generation
jvs '生成一个项目汇报 PPT'
```

### 9. 规则管理
```bash
jri list  # 列出所有规则
jri show <rule_name>  # 查看规则详情
```

### 10. 记忆管理
```bash
jmo  # 启动记忆管理工具
```

## 注意事项

### 安全性
- 命令执行功能强大，请谨慎使用
- 建议启用 `execute_tool_confirm: true` 进行工具执行确认
- 不要在配置文件中暴露敏感信息

### 性能
- 工具过多时可能影响模型决策，建议使用 `tool_filter_threshold` 进行过滤
- 大型项目建议使用 CodeAgent 的上下文推荐功能
- 非交互模式有 5 分钟超时限制

### 兼容性
- 主要支持 Linux 系统
- Windows 用户建议使用 WSL
- 需要 Python 3.12 环境

### 扩展性
- 支持自定义工具、平台、方法论
- 插件系统灵活，易于集成新功能
- SDK 形式便于嵌入到其他项目中

### 会话管理
- 会话文件保存在 `~/.jarvis/sessions/` 目录
- 自动保留最近 10 个会话
- 恢复会话时会检查 Git 一致性

## 参考资源

### 官方文档
- [Jarvis Book](docs/jarvis_book/) - 完整的官方文档
- [README.md](README.md) - 项目说明
- [ReleaseNote.md](ReleaseNote.md) - 版本发布说明

### 技术文档
- [配置说明](docs/jarvis_config.md)
- [技术文档](docs/technical/)
- [最佳实践](docs/best_practices/)

### 社区资源
- GitHub: https://github.com/skyfireitdiy/Jarvis
- Gitee: https://gitee.com/skyfireitdiy/Jarvis

## 总结

Jarvis 是一个设计精良、功能强大的 AI 应用开发 SDK，具有以下特点：

1. **架构清晰**：模块化设计，职责分离明确
2. **扩展性强**：支持自定义工具、平台、方法论
3. **功能丰富**：内置 30+ 工具，覆盖多种场景
4. **易于使用**：提供命令行工具和 SDK 两种使用方式
5. **文档完善**：详细的官方文档和使用指南
6. **专业套件**：安全分析、代码迁移、浏览器自动化、Windows 自动化等专用工具
7. **记忆系统**：三层记忆架构，支持知识持久化
8. **工作流规范**：ARCHER 工作流确保任务执行质量
9. **会话管理**：自动保存、智能恢复、Git 一致性检查
10. **规则系统**：自动选择、智能筛选、状态管理
11. **性能优化**：进度显示、工具筛选、更新机制
12. **用户体验**：性格系统、交互优化、反馈及时

适合个人开发者、AI 应用探索者以及需要处理各种技术任务的工程师使用。