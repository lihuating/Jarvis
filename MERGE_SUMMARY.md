# Jarvis 合并记录 (Jarvis_sky v3.1.10 → Jarvis)

合并日期: 2026-06-09

## 已执行策略摘要

| 分区 | 策略 |
|------|------|
| Part A (sky 独有) | 除 A1-6 外全部 `sky` 引入 |
| Part B (Jarvis 独有) | 全部保留 |
| Part C | agent/others=jarvis；code_agent/c2rust=sky+回灌；tools/platform/mcp/utils=merge |
| Part D | pyproject/setup/manifest=merge；Dockerfile/mkdocs=jarvis |

## 新增模块

- `jarvis_web_gateway/`, `jarvis_gateway/`, `jarvis_service/` (+ Vue frontend)
- `jarvis_rules_index/`, `skill_discovery/`, 新工具与符号表等

## 保留的 Jarvis 定制

- `code_agent_delivery.py`, `search_file_content.py`, `tool_prompt_spill.py`
- `project_memory.py`, `llm_metrics.py`, `rich_box.py`, `rust_wrapper.py`
- `jarvis_rust_tools/`, `VscodeTool/`, JCA 治理文档

## 安装

```bash
cd /mnt/d/code_pub/Jarvis
pip install -e .
# Web 前端（首次）
cd src/jarvis/jarvis_service/frontend && npm install && npm run build
```

## 新命令

- `jwg serve` — Web Gateway
- `jservice run` — 统一服务（Gateway + 前端）
- `jri show` — 规则索引

## 已知环境依赖

- Web 栈需要: `websockets`, `httpx`, `aiohttp`, `psutil`, `jieba`
- `symbol_dependency` / SQLite 符号表需要 Python `_sqlite3` 模块
