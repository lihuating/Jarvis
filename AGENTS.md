# Jarvis AI 助手 - 项目上下文

## 项目概述

**Jarvis** 是一个强大的 AI 应用开发 SDK，提供灵活的基础组件帮助开发者快速构建专业的 AI 应用。与传统的 workflow 形式 Agent 平台（如 Dify）不同，Jarvis 以 Python SDK 形式提供，强调可编程性和可扩展性。

### 核心特性

- **AI 应用开发 SDK**: 提供 Agent 和 CodeAgent 等精心设计的基础组件
- **高度可编程**: 纯 Python SDK，开发者可自由组合各种能力
- **丰富工具生态**: 内置 30+ 工具（代码分析、文件操作、命令执行等）
- **多模型支持**: 支持 OpenAI、Claude 等多种 LLM 平台
- **专业套件**: 包含安全分析、代码迁移、代码审查等专业工具

### 版本信息

- **当前版本**: 2.0.15
- **Python 版本**: 3.12
- **许可证**: MIT
- **主要语言**: Python

### 技术栈

**核心依赖**:
- requests==2.32.3
- playwright==1.48.0
- openai==1.78.1
- anthropic>=0.40.0
- python-lsp-server>=1.14.0
- tree-sitter 系列（支持多种编程语言）

**开发依赖**:
- pytest, pytest-cov, coverage
- ruff, mypy, bandit
- mkdocs-material (文档构建)

## 项目结构

```
Jarvis/
├── src/jarvis/              # 主要源代码
│   ├── jarvis_agent/        # 通用 AI 代理
│   ├── jarvis_code_agent/   # 代码专用代理
│   ├── jarvis_platform/     # 平台基础类
│   ├── jarvis_tools/        # 工具系统
│   ├── jarvis_git_utils/    # Git 工具
│   ├── jarvis_sec/          # 安全分析
│   ├── jarvis_c2rust/       # C→Rust 迁移
│   ├── jarvis_browser/      # 浏览器自动化
│   ├── jarvis_windows/      # Windows 自动化
│   ├── jarvis_lsp/          # LSP 服务端
│   ├── jarvis_config/       # 配置管理
│   ├── jarvis_memory_organizer/  # 记忆管理
│   ├── jarvis_methodology/  # 方法论知识库
│   └── jarvis_data/         # 数据文件
├── tests/                   # 测试代码
├── builtin/                 # 内置规则和提示
│   ├── agent/              # Agent 相关配置
│   ├── prompts/            # 系统提示词
│   └── rules/              # 规则文件
├── docs/                   # 文档
├── scripts/                # 脚本工具
├── .jarvis/                # 用户配置目录
│   ├── config.yaml         # 主配置文件
│   ├── evolution/          # 进化阶段跟踪
│   └── memory/             # 记忆文件
└── docker-compose.yml      # Docker 部署配置
```

## 核心命令

| 命令 | 快捷方式 | 功能描述 |
|------|----------|----------|
| `jarvis` | `jvs` | 通用 AI 代理 |
| `jarvis-code-agent` | `jca` | 代码专用代理 |
| `jarvis-git-commit` | `jgc` | 自动生成 Git 提交信息 |
| `jarvis-git-squash` | `jgs` | Git 提交历史整理 |
| `jarvis-platform-manager` | `jpm` | LLM 平台管理 |
| `jarvis-tool` | `jt` | 工具管理与调用 |
| `jarvis-memory-organizer` | `jmo` | 记忆管理 |
| `jarvis-sec` | `jsec` | 安全分析套件 |
| `jarvis-c2rust` | `jc2r` | C→Rust 迁移套件 |
| `jarvis-config` | `jcfg` | 配置管理 |
| `jarvis-lsp` | `jlsp` | LSP 服务端 |
| `jarvis-browser` | `jb` | 浏览器自动化 |
| `jarvis-windows` | `jw` | Windows 自动化 |

## 构建和运行

### 安装

**一键安装（推荐）**:
```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/skyfireitdiy/Jarvis/main/scripts/install.sh)"
```

**手动安装**:
```bash
git clone https://github.com/skyfireitdiy/Jarvis.git
cd Jarvis
pip3 install -e .
```

**使用 uv 安装**:
```bash
uv tool install git+https://github.com/skyfireitdiy/Jarvis.git
```

### Docker 部署

```bash
# 拉取镜像
docker pull ghcr.io/skyfireitdiy/jarvis:latest

# 使用 Docker Compose
docker-compose run --rm jarvis

# 直接使用 Docker 命令
docker run -it --rm \
  --user "$(id -u):$(id -g)" \
  -v $(pwd):/workspace \
  -v $HOME/.jarvis:/home/jarvis/.jarvis \
  -w /workspace \
  ghcr.io/skyfireitdiy/jarvis:latest
```

### 测试

```bash
# 运行所有测试
python -m pytest -v

# 运行特定模块测试
python -m pytest tests/jarvis_agent/ -v

# 使用测试脚本
cd scripts
./run_tests.sh
```

### 文档构建

```bash
# 构建文档
./scripts/make_book.sh

# 构建 PDF
./scripts/build_pdf.sh
```

## 配置说明

### 主配置文件

配置文件位置: `~/.jarvis/config.yaml`

**基本配置示例**:
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
      openai_api_key: "your-api-key-here"
      openai_api_base: "https://api.openai.com/v1"

  claude-opus-4:
    platform: claude
    model: claude-opus-4-20250514
    max_input_token_count: 200000
    llm_config:
      anthropic_api_key: "your-api-key-here"
      anthropic_base_url: "https://api.anthropic.com"
```

### 配置特性

- **多层配置**: 支持从当前目录逐层向上查找并合并多个 `.jarvis/config.yaml` 配置文件
- **模型组管理**: 通过 `llm_groups` 灵活切换不同场景的模型组合
- **工具筛选**: 可配置 `tool_filter_threshold`（默认 30）控制工具数量
- **错误回溯**: 可通过 `print_error_traceback: true` 启用全局错误回溯

## 开发约定

### 代码风格

- 使用 Python 3.12
- 遵循 PEP 8 规范
- 使用 ruff 进行代码检查
- 使用 mypy 进行类型检查

### 测试规范

- 使用 pytest 作为测试框架
- 测试文件命名: `test_*.py` 或 `*_test.py`
- 测试函数命名: `test_*`
- 支持标记: `slow`, `integration`, `unit`, `smoke`, `security`, `performance`, `regression`

### 提交规范

使用 `jgc` 命令自动生成规范的提交信息，或使用 `jgs` 命令整理提交历史。

### 文档规范

- 使用 Markdown 格式
- 文档位于 `docs/jarvis_book/` 目录
- 使用 MkDocs + Material Theme 构建文档站点

## 关键模块说明

### Agent 系统

**jarvis_agent**: 通用 AI 代理，提供完整的任务执行能力
- 支持工具调用、记忆管理、任务规划
- 通过 system_prompt 定制行为
- 支持内置命令（如 `<ListRule>`, `<Commit>`）

**jarvis_code_agent**: 代码专用代理，继承自 Agent
- 内置代码分析、符号查找、精确编辑能力
- 支持静态检查和自动修复
- 与 Git 深度集成

### 平台系统

**jarvis_platform**: LLM 平台基础类
- 统一的 LLM 调用接口
- 支持流式输出
- 错误处理和重试机制

**jarvis_platform_manager**: 平台管理工具
- 测试不同 LLM 平台
- 管理平台配置

### 工具系统

**jarvis_tools**: 工具注册和调用系统
- 30+ 内置工具
- 支持自定义工具扩展
- 工具版本检测和安装

### 专业套件

**jarvis_sec**: 安全分析套件
- 启发式扫描
- AI 深度验证
- 支持 C/C++ 和 Rust

**jarvis_c2rust**: C→Rust 迁移套件
- 渐进式迁移
- 断点续跑
- 智能库替代

**jarvis_browser**: 浏览器自动化
- 基于 Playwright
- 35+ 操作命令
- 守护进程模式

**jarvis_windows**: Windows 自动化
- 原生应用自动化
- 窗口管理、控件交互
- 截图和控件树获取

### Git 工具

**jarvis_git_utils**: Git 工具集
- `jarvis-git-commit`: 自动生成提交信息
- `jarvis-git-squash`: 提交历史整理

### 记忆系统

三层记忆架构:
1. **短期记忆**: 会话级临时记忆
2. **项目长期记忆**: 项目级持久化记忆
3. **全局长期记忆**: 跨项目共享记忆

### 方法论系统

**jarvis_methodology**: 方法论知识库
- 沉淀成功经验
- 支持本地和中心化共享
- 提升任务执行效率

## 进化阶段

项目当前处于 **阶段1 - 架构自主优化**（66% 完成）

### 已完成功能

- ✅ 架构健康度分析工具（67个测试，92%覆盖率）
- ✅ 自动重构能力（149个测试，≥93%覆盖率）
  - 提取函数、提取类、内联函数、移动方法
  - 接口自动提取
  - 模块自动拆分
  - 依赖注入改造

### 进行中

- 架构演进机制设计
  - 模块热插拔机制
  - 版本化 API 机制
  - 灰度发布机制
  - A/B 测试机制

## 常见任务

### 代码分析

```python
from jarvis.jarvis_code_agent.code_agent import CodeAgent

agent = CodeAgent()
agent.run('分析 user/service.py 的代码质量')
```

### 文档生成

```python
from jarvis import Agent

agent = Agent(
    system_prompt="你是一个专业的文档维护助手。",
    name="DocGenerator"
)
agent.run('分析 README.md，补充用户群体和应用场景信息')
```

### 安全扫描

```bash
jsec config
jsec scan
```

### Git 提交

```bash
jgc
```

## 扩展开发

### 添加自定义工具

在 `~/.jarvis/tools/` 目录下创建新工具实现

### 集成新 LLM 平台

在 `~/.jarvis/platforms/` 目录下添加新的平台适配器

### 定义方法论

通过配置文件集成外部或自定义的命令协议

## 重要提醒

- **系统要求**: 主要支持 Linux 系统，Windows 用户可使用 WSL
- **命令执行风险**: Jarvis 具备执行系统命令的能力，请谨慎使用
- **模型使用风险**: 请遵守各模型平台的服务条款
- **安全增强**: 可在配置文件中启用 `execute_tool_confirm: true` 进行工具执行确认

## 相关资源

- **GitHub**: https://github.com/skyfireitdiy/Jarvis.git
- **Gitee**: https://gitee.com/skyfireitdiy/Jarvis.git
- **文档**: docs/jarvis_book/
- **Docker 镜像**: ghcr.io/skyfireitdiy/jarvis:latest

## 项目记忆

本团队负责以下模块:
- moni, sdr2itran, hotpatch, sym, bbx, comm（oss_itran 目录）
- sche, op 通信，file, voslog, sym, hotpatch（oss_aau 目录）
- sym, hotpatch, comm, init, moni, toil（通用模块）

9200 基站操作信息已保存到记忆系统中，可通过记忆工具查询。

---

**最后更新**: 2026-03-02
**项目版本**: 2.0.15
**维护者**: Jarvis 团队