# 工程扫描持久化 & 输出渲染优化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在大工程场景下缩短“开始回答”的等待时间，并减少 Rich 流式输出渲染导致的“看起来卡”。

**Architecture:** 引入工程内 `JVS_MEMORY.md` 作为“只扫一次”的持久化索引摘要（可通过 `'<Init>'` 刷新，启动时自动加载）；流式输出侧复用 `Panel` 并将 `wrap` 成本限制在尾部窗口，长文本输出自动降级以减少语法高亮开销。

**Tech Stack:** Python 3.12、Rich、Prompt Toolkit、Git（`git rev-parse` / `git ls-files`）。

---

### Task 1: 工程根目录识别与 `JVS_MEMORY.md` 读写工具

**Files:**
- Create: `src/jarvis/jarvis_utils/project_memory.py`
- Modify: `src/jarvis/jarvis_code_agent/code_agent.py`
- Modify: `src/jarvis/jarvis_agent/__init__.py`

- [ ] **Step 1: 新增 `project_memory.py`**
  - 提供：`get_git_root_fallback(cwd)`、`get_jvs_memory_path(root)`、`read_jvs_memory(root)`、`write_jvs_memory(root, content)`、`build_jvs_memory(root)`。
  - `build_jvs_memory()` 复用 `jarvis_code_agent/utils.py:get_project_overview()`，并附加工具/规则简要统计（避免写入过大）。

- [ ] **Step 2: CodeAgent 启动时自动加载**
  - 在 `CodeAgent.run()` 早期注入：若存在 `JVS_MEMORY.md` 则追加到 addon/system prompt；不存在则生成一次再加载。

- [ ] **Step 3: 通用 Agent 启动时自动加载**
  - 在 `Agent` 初始化或 run loop 开始前注入同样逻辑，确保 `jvs` 也生效。

---

### Task 2: 新增 `'<Init>'` 内置命令（刷新 `JVS_MEMORY.md`）

**Files:**
- Modify: `src/jarvis/jarvis_utils/input.py`
- Modify: `src/jarvis/jarvis_agent/builtin_input_handler.py`

- [ ] **Step 1: 补全菜单增加 `Init`**
  - 在 `BUILTIN_COMMANDS` 中追加 `("Init", "扫描工程并生成/刷新 JVS_MEMORY.md")`。

- [ ] **Step 2: builtin handler 实现 `Init`**
  - 生成/刷新 git 根目录下 `JVS_MEMORY.md`，并提示用户路径。
  - 完成后在当前会话中立即加载（追加到 addon prompt）。

---

### Task 3: 流式输出渲染优化（复用 Panel + 尾部窗口 wrap）

**Files:**
- Modify: `src/jarvis/jarvis_utils/output.py`

- [ ] **Step 1: `stream_chat_with_panel()` 复用 Panel**
  - 初始化一次 `Panel`，后续只更新 `panel.renderable` / `panel.subtitle`，不再每次重建 `Panel(...)`。

- [ ] **Step 2: 将 wrap 成本限制为“尾部窗口”**
  - 新增窗口阈值（环境变量/默认值）：仅对最后 N 字符做 wrap/滚动裁剪，避免随着全文增长越来越慢。

- [ ] **Step 3: 长文本输出降级**
  - 对超长文本（按字符/行阈值）关闭 `Syntax` 高亮，改用 `Text`，减少排版开销。

---

### Task 4: 最小自检

**Files:**
- Modify: (none)

- [ ] **Step 1: 静态检查**
  - `ReadLints` 覆盖修改文件，确保无新增 lint。

- [ ] **Step 2: 基本执行路径检查**
  - 在 Python 3.12 环境下运行 `jvs`/`jca`，执行 `'<Init>'`，确认生成 `JVS_MEMORY.md` 并下次启动自动加载。

