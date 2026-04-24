# Disable Auto JCA Switch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 进入 Git 仓库时默认不再自动切换到 `jca`；用户可通过快捷键/内置命令一键切换到 `jca`。

**Architecture:** 启动阶段的自动切换逻辑保留，但由“默认开启”改为“默认关闭”，仅在显式 CLI 开关或配置开关打开时触发。交互输入层增加内置命令 `SwitchToJCA`，并绑定快捷键（F3）触发；命令执行时通过 `os.execvp` 切换到 `jarvis-code-agent`。

**Tech Stack:** Python, Typer CLI, prompt_toolkit key bindings, Rich（不涉及改动）。

---

### Task 1: Add config flag for auto switch

**Files:**
- Modify: `src/jarvis/jarvis_utils/config.py`

- [ ] **Step 1: Add config getter**

Add a new function:

```python
def is_auto_switch_to_jca_in_git_repo() -> bool:
    return GLOBAL_CONFIG_DATA.get("auto_switch_to_jca_in_git_repo", False) is True
```

- [ ] **Step 2: Run bytecode compile**

Run:
`python3 -m py_compile src/jarvis/jarvis_utils/config.py`

Expected: exit code 0

---

### Task 2: Change startup behavior to default NOT switching

**Files:**
- Modify: `src/jarvis/jarvis_agent/jarvis.py`

- [ ] **Step 1: Add CLI option to enable auto switch**

Add a Typer option:

```python
auto_jca: bool = typer.Option(
    False, "--auto-jca", help="检测到 Git 仓库时自动切换到 jca（默认关闭）"
)
```

- [ ] **Step 2: Gate `try_switch_to_jca_if_git_repo` with (auto_jca or config flag)**

Update `try_switch_to_jca_if_git_repo(..., auto_jca: bool, keep_jvs: bool=False)` so it returns unless:
- `auto_jca` is True OR `is_auto_switch_to_jca_in_git_repo()` is True
- still respects `--keep-jvs`
- still skips non-interactive mode

- [ ] **Step 3: Verify manual run**

Run:
`/home/10186806@zte.intra/.local/bin/jvs -n -T "你好"`

Expected: 不会再打印“正在自动切换到 jca…”并保持在 `jvs` 运行。

---

### Task 3: Add SwitchToJCA builtin command + shortcut

**Files:**
- Modify: `src/jarvis/jarvis_utils/input.py`
- Modify: `src/jarvis/jarvis_agent/builtin_input_handler.py`

- [ ] **Step 1: Register builtin command**

Add to `BUILTIN_COMMANDS`:

```python
("SwitchToJCA", "切换到代码模式（jca）")
```

- [ ] **Step 2: Bind F3 in multiline prompt**

In `_get_multiline_input_internal`, add:

```python
@bindings.add("f3", filter=has_focus(DEFAULT_BUFFER), eager=True)
def _(event):
    event.app.exit(result=ot("SwitchToJCA"))
```

- [ ] **Step 3: Handle builtin tag**

In `builtin_input_handler.py`, add a branch:

```python
elif tag == "SwitchToJCA":
    # exec to jarvis-code-agent (keep cwd)
```

Behavior:
- If not in a git repo, print warning and keep current session.
- If in a git repo, `os.execvp("jarvis-code-agent", ["jarvis-code-agent"])`.

- [ ] **Step 4: Verify interaction**

Manual:
1) `jvs` 进入交互
2) 按 F3

Expected:
切换到 `jca`（进程被替换）。

---

### Task 4: Quick smoke checks

**Files:**
- Modify: none

- [ ] **Step 1: Bytecode compile touched files**

Run:
`python3 -m py_compile src/jarvis/jarvis_agent/jarvis.py src/jarvis/jarvis_utils/input.py src/jarvis/jarvis_agent/builtin_input_handler.py`

Expected: exit code 0

