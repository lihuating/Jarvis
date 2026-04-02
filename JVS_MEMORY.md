# JVS_MEMORY.md

该文件由 Jarvis 自动生成，用于加速大工程下的启动与“开始回答”时间。

- 生成时间: 2026-04-02 16:39:20
- 项目根目录: /media/vdc/code/Jarvis
- 规则索引指纹: 1d83d652c8f930d42e313be219072273

---

项目概况:
Git托管目录结构（共1604个文件）:
├── .github/
│   └── workflows/
├── .jarvis/
│   ├── evolution/
│   │   └── decisions/
│   ├── jsec/
│   ├── memory/
│   ├── methodologies/
│   ├── rules/
│   │   ├── deployment/
│   │   ├── development_tools/
│   │   ├── evolution/
│   │   └── tool_config/
│   └── spec/
├── .specstory/
│   └── history/
├── VscodeTool/
│   └── src/
├── builtin/
│   ├── agent/
│   ├── multi_agent/
│   ├── prompts/
│   │   └── code_agent_system/
│   └── rules/
│       ├── agent_personality/
│       ├── architecture_design/
│       ├── code_quality/
│       ├── deployment/
│       ├── development_tools/
│       ├── development_workflow/
│       ├── performance/
│       ├── security/
│       ├── testing/
│       ├── tool_config/
│       └── ui_design/
├── docs/
│   ├── best_practices/
│   ├── compare/
│   ├── images/
│   ├── jarvis_book/
│   ├── superpowers/
│   │   └── plans/
│   └── technical/
│       └── implementation/
├── memory_data/
├── scripts/
├── src/
│   ├── jarvis/
│   │   ├── jarvis_agent/
│   │   │   └── language_extractors/
│   │   ├── jarvis_browser/
│   │   ├── jarvis_c2rust/
│   │   ├── jarvis_code_agent/
│   │   │   └── code_analyzer/
│   │   │       ├── build_validator/
│   │   │       └── languages/
│   │   ├── jarvis_config/
│   │   ├── jarvis_data/
│   │   │   └── tiktoken/
│   │   ├── jarvis_git_squash/
│   │   ├── jarvis_git_utils/
│   │   ├── jarvis_jck/
│   │   ├── jarvis_lsp/
│   │   ├── jarvis_mcp/
│   │   ├── jarvis_memory_organizer/
│   │   ├── jarvis_methodology/
│   │   ├── jarvis_platform/
│   │   ├── jarvis_platform_manager/
│   │   ├── jarvis_sec/
│   │   │   └── checkers/
│   │   ├── jarvis_smart_shell/
│   │   ├── jarvis_tools/
│   │   │   └── cli/
│   │   ├── jarvis_utils/
│   │   ├── jarvis_windows/
│   │   └── scripts/
│   └── jarvis_rust_tools/
│       └── src/
└── tests/
    ├── jarvis_agent/
    ├── jarvis_c2rust/
    ├── jarvis_code_agent/
    ├── jarvis_config/
    ├── jarvis_git_utils/
    ├── jarvis_lsp/
    ├── jarvis_mcp/
    ├── jarvis_memory_organizer/
    ├── jarvis_platform/
    ├── jarvis_platform_manager/
    ├── jarvis_sec/
    ├── jarvis_smart_shell/
    ├── jarvis_tools/
    ├── jarvis_utils/
    ├── performance/
    ├── regression/
    ├── security/
    └── test_utils/

最近提交:
提交 1: 191702c - @@优化 (1个文件)
    - src/jarvis/jarvis_utils/input.py
提交 2: aa2b2cb - 对交互窗口进行优化提交 (15个文件)
    - src/jarvis/jarvis_agent/__init__.py
    - src/jarvis/jarvis_platform/claude.py
    - src/jarvis/jarvis_agent/share_manager.py
    - src/jarvis/jarvis_code_agent/worktree_manager.py
    - src/jarvis/jarvis_c2rust/llm_module_agent_executor.py
    ...
提交 3: fd66f68 - 优化会话后的提示显示 (4个文件)
    - src/jarvis/jarvis_data/config_schema.json
    - src/jarvis/jarvis_agent/__init__.py
    - src/jarvis/jarvis_utils/config.py
    - src/jarvis/jarvis_utils/output.py
提交 4: 9ef3eb8 - feat(llm): 实现智能模型自动选择和性能优化 (8个文件)
    - src/jarvis/jarvis_agent/__init__.py
    - src/jarvis/jarvis_agent/builtin_input_handler.py
    - src/jarvis/jarvis_platform/base.py
    - src/jarvis/jarvis_utils/config.py
    - src/jarvis/jarvis_tools/registry.py
    ...
提交 5: 4f9d10c - feat(search): zhipu MCP and search_web; cheap LLM for aux tasks (5个文件)
    - src/jarvis/jarvis_agent/__init__.py
    - src/jarvis/jarvis_platform/base.py
    - src/jarvis/jarvis_utils/methodology.py
    - src/jarvis/jarvis_code_agent/code_agent_prompts.py
    - src/jarvis/jarvis_tools/search_web.py
## 来自 AGENTS.md 的项目摘要

## 项目概述

**Jarvis** 是一个功能强大的 Python AI 应用开发 SDK，为开发者提供灵活的工具和能力来快速构建专业的 AI 应用。与传统的 workflow 形式 Agent 平台（如 Dify）不同，Jarvis 以 Python SDK 的形式提供，强调可编程性和可扩展性。

### 核心定位
- **AI 应用开发 SDK**：提供强大而灵活的基础组件，帮助开发者快速构建专业的 AI 应用
- **高度可编程**：以纯 Python SDK 形式提供，开发者可以自由组合各种能力
- **工具生态丰富**：内置 30+ 工具（代码分析、文件操作、命令执行等），支持自定义扩展
- **聚焦代码开发**：专为代码任务优化，提供完整的代码分析、编辑、验证、提交工作流

### 主要技术栈
- **编程语言**：Python 3.12
- **核心依赖**：
  - LLM 集成：OpenAI (1.78.1)、Anthropic (>=0.40.0)
  - 代码分析：tree-sitter 系列支持多种语言（Python、JavaScript、TypeScript、Rust、Go、Java、C/C++、Ruby、PHP、SQL、Markdown、HTML、CSS、Bash 等）
  - 浏览器自动化：Playwright (1.48.0)
  - Web 框架：FastAPI (0.115.12)、Uvicorn (0.33.0)
  - 终端 UI：Rich (14.0.0)、Prompt Toolkit (3.0.50)
  - Windows 自动化：pywinauto (>=0.6.9)
  - 其他：requests、pyyaml、tiktoken、pillow、markitdown、jsonnet、ddgr、typer、pathspec、plotext 等

### 项目版本
- **当前版本**：2.0.19
- **许可证**：MIT
- **支持平台**：Linux（主要）、Windows（通过 WSL 或原生，支持 GUI 自动化）、macOS

## 项目结构

```
Jarvis/
├── src/jarvis/                    # 源代码目录
│   ├── jarvis_agent/             # 通用 AI 代理核心
│   ├── jarvis_code_agent/        # 代码专用代理
│   ├── jarvis_browser/           # 浏览器自动化工具（基于 Playwright）
│   ├── jarvis_c2rust/            # C→Rust 迁移套件
│   ├── jarvis_config/            # 配置管理
│   ├── jarvis_git_utils/         # Git 工具集
│   ├── jarvis_git_squash/        # Git 提交历史整理
│   ├── jarvis_jck/               # 工具检查模块
│   ├── jarvis_lsp/               # LSP 服务端
│   ├── jarvis_mcp/               # MCP 客户端
│   ├── jarvis_memory_organizer/  # 记忆管理
│   ├── jarvis_methodology/       # 方法论知识库
│   ├── jarvis_platform/          # LLM 平台抽象层（OpenAI、Claude）
│   ├── jarvis_platform_manager/  # 平台管理器
│   ├── jarvis_rules_index/       # 规则索引管理
│   ├── jarvis_sec/               # 安全分析套件
│   ├── jarvis_smart_shell/       # 智能Shell
│   ├── jarvis_tools/             # 工具系统
│   ├── jarvis_utils/             # 通用工具
│   ├── jarvis_windows/           # Windows 桌面自动化工具
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
├── docs/                         # 文档（使用 MkDocs 构建）
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
│   ├── sessions/                 # 会话文件
│   └── ...
├── pyproject.toml                # 项目配置（现代）
├── setup.py                      # 项目配置（传统）
├── Dockerfile                    # Docker 镜像
├── docker-compose.yml            # Docker Compose 配置
├── mkdocs.yml                    # MkDocs 文档配置
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
- 支持非交互模式和任务派发模式

**关键类**：
- `Agent`：基础代理类
- `AgentRunLoop`：主运行循环
- `SessionManager`：会话管理（自动保存、自动清理、智能恢复）
- `MemoryManager`：记忆管理（三层架构：短期、项目长期、全局长期）
- `TaskListManager`：任务列表管理
- `RulesManager`：规则管理器（支持自动规则选择）
- `TaskAnalyzer`：任务分析器

**新特性（v2.0.16+）**：
- 会话自动保存和清理
- 会话名称智能生成
- 历史会话智能检测
- Git 一致性检查
- 规则激活反馈
- 自动规则选择
- Agent 性格系统

### 2. CodeAgent（代码专用代理）
**位置**：`src/jarvis/jarvis_code_agent/`

**功能**：
- 继承自 Agent，专为代码任务优化
- 内置代码分析、符号查找、精确编辑、构建验证等专业能力
- 支持 Git 操作（提交、变基、diff 分析）
- 自动进行代码审查和构建验证
- 支持会话自动保存和恢复
- 支持默认规则配置
- 支持连续任务执行

**关键管理器**：
- `BuildValidationManager`：构建验证
- `LintManager`：代码检查
- `DiffManager`：差异分析
- `ImpactManager`：影响分析
- `GitManager`：Git 操作

**新特性（v2.0.16+）**：
- 默认规则配置
- 连续任务支持
- 内置命令优先处理
- 静态检查优化
- 代码格式化工具支持

### 3. 工具系统
**位置**：`src/jarvis/jarvis_tools/`

**内置工具类别**：
- 文件操作：`read_code`、`edit_file`、`write_file`、`list_directory`
- 代码分析：`search_file_content`、`glob`、符号查找、LSP 代码分析
- 命令执行：`run_shell_command`、`execute_script`（支持 Windows PowerShell）
- Git 操作：`git_commit`、`git_squash`
- 记忆管理：`memory`（save/retrieve/clear）
- 方法论：`methodology`（load/apply）
- 浏览器：浏览器自动化命令（41+）
- Windows：Windows 桌面自动化命令（13+）
- PPT：PowerPoint 生成和编辑
- 其他：Markdown 处理、文件编码检测、任务列表管理等

**扩展能力**：
- 支持自定义工具开发
- 工具过滤机制（避免工具过多干扰模型决策）
- 工具按场景智能筛选（超过 30 个工具时自动筛选）
- 工具注册表完整索引

### 4. 平台抽象层
**位置**：`src/jarvis/jarvis_platform/`

**支持的平台**：
- OpenAI
- Anthropic (Claude)

**核心类**：
- `BasePlatform`：平台基类
- `PlatformRegistry`：平台注册表
- 各平台具体实现

**架构简化（v2.0.1+）**：
- 移除了 kimi、tongyi、yuanbao 等平台实现
- 聚焦 OpenAI 和 Claude 平台
- 简化配置和调用链

### 5. 专业套件

#### 安全分析（jsec）
**位置**：`src/jarvis/jarvis_sec/`
- 启发式扫描
- AI 深度验证
- 支持 C/C++ 和 Rust 语言
- 配置驱动设计（v2.0.5+）

#### C→Rust 迁移（jc2r）
**位置**：`src/jarvis/jarvis_c2rust/`
- 渐进式迁移
- 断点续跑
- 智能库替代

#### 浏览器自动化（jb）
**位置**：`src/jarvis/jarvis_browser/`
- 41+ 浏览器命令（v2.0.11+）
- 守护进程模式
- 基于 Playwright
- 支持 Windows 平台（v2.0.12+）

#### Windows 桌面自动化（jw）
**位置**：`src/jarvis/jarvis_windows/`
- 应用启动/连接
- 点击、输入、截图
- 控件树操作
- 13+ 常用命令（v2.0.11+）
- 系统配置管理（主题、电源、代理等）（v2.0.12+）

#### 智能Shell（jss）
**位置**：`src/jarvis/jarvis_smart_shell/`
- 实验性智能 Shell 功能
- 交互式命令执行

#### 规则索引（jri）
**位置**：`src/jarvis/jarvis_rules_index/`
- 规则查询和管理
- 支持内置规则和项目规则
- 规则文件定位（v2.0.17+）

#### LSP 代码分析（jlsp）
**位置**：`src/jarvis/jarvis_lsp/`
- LSP 客户端工具
- 符号查询、定义查找、引用定位
- 代码质量检查和修复建议（v2.0.9+）
- 支持 Windows 平台（v2.0.13+）

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

**命令变更说明（v2.0.1+）**：
- `jck` 命令已迁移为 `jvs --check` 参数
- `jqc` 命令已迁移为 `jvs --quick-config` 参数

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

# 工具检查（替代原 jck 命令）
jvs --check

# 检查特定工具
jvs --check-tool <工具名>
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

# 构建文档（使用 MkDocs）
mkdocs build
mkdocs serve
```
工具概况: edit_file, execute_script, load_rule, memory, meta_agent, methodology, read_code, read_webpage, search_web, task_list_manager, virtual_tty, vsw_mem_collect, zhipu_web_search_prime.resource.get_resource, zhipu_web_search_prime.resource.get_resource_list, zhipu_web_search_prime.tool_call.web_search_prime（共15个）
