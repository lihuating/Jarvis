# jca（CodeAgent）防重复执行治理：A+B+C 组合方案

本文描述 **A（交付落盘/短路）+ B（只读验证缓存）+ C（只读 execute_script 降噪）** 的组合方案在 Jarvis 代码中的落地点、使用方式与行为边界。

## 背景与问题

在长对话/大仓库场景下，jca 可能出现以下“看起来像反复分析与确认”的链路：

- 工具后处理链路较重（diff/影响分析/构建/静态检查等）→ token 增长更快
- 触发 **上下文压缩/摘要重置**
- 摘要后模型为稳妥起见会再次做关键验证（例如 `rg` 定位行号/读取关键文件）

同时，`execute_script` 曾被统一视为“可能修改工作区”的工具，从而**即使只读查询**也可能触发重后处理，进一步放大 token 与摘要触发的概率。

## 设计目标

在尽量保证**质量不下降**（仍能验证、仍能产出可复核证据）的前提下：

- 将“任务已完成/已交付”从自然语言描述升级为 **可机读、可落盘** 的状态
- 将只读验证与真实代码改动区分，**避免无意义的重后处理**
- 在进程内对重复验证做 **可解释的短路**（不依赖模型自觉）

## 方案 A：通用 Delivery Marker + 落盘

### 机制

- 当模型在最终可交付时输出如下结构化块（JSON 必须合法）：

```text
<JCA_DELIVERY>
{
  "delivered": true,
  "artifact_type": "analysis_report",
  "artifact_refs": ["相对路径/关键文件1", "..."],
  "confidence": 0.0,
  "notes": "一句话说明交付物是什么/在哪里"
}
</JCA_DELIVERY>
```

- `CodeAgent` 在 `run()` 结束主对话后解析该块，并写入：

  - `.jarvis/code_agent/deliveries/<task_fingerprint>.marker.json`
  - `.jarvis/code_agent/deliveries/<task_fingerprint>.delivery.json`

- `task_fingerprint` 由 `repo_root + start_commit + 归一化 user_input` 派生，用于跨摘要压缩的弱稳定关联。

- 之后再次进入 `CodeAgent.run()` 时，如检测到已交付且用户**未显式要求重跑**，会短路并提示交付文件位置，避免在摘要后重新跑完整主流程。

### 代码落点

- `src/jarvis/jarvis_code_agent/code_agent_delivery.py`
- `src/jarvis/jarvis_code_agent/code_agent.py`（`run()` 中解析与落盘/短路）

### 强制重跑

用户输入包含类似关键词（**启发式**）时不会短路：例如 `重新/重跑/force/rerun/...`（实现见 `user_requests_force_rerun()`）。

## 方案 B：只读验证缓存（防止重复后处理）

### 机制

- 对“**仅只读 tools + 只读 execute_script**”场景：
  - 第一次仍可能执行后处理（保守策略，避免工具解析失败导致漏检）
  - 从第二次开始，如 `(fingerprint, diff_hash, interpreter, script)` 相同，则直接跳过后续重后处理

### 代码落点

- `src/jarvis/jarvis_code_agent/code_agent_delivery.py`（`VerificationCache`）
- `src/jarvis/jarvis_code_agent/code_agent.py`（`CodeAgent._on_after_tool_call()`）

> 说明：该缓存是**进程内**缓存，进程重启会失效；其目标是降低“同一会话中反复只读验证”带来的噪声与成本。

## 方案 C：将 `execute_script` 的“只读命令”从写命令路径中分离

### 机制

- 为 `execute_script` 提供保守的只读判断（`is_execute_script_read_only`）：
  - 优先支持 `bash/sh` 下单行命令的典型只读模式（`rg/grep/git/...` 等，且禁止明显写操作子串）
  - PowerShell 覆盖常见只读 cmdlet（`Select-String/Get-Content/...` 等）并避免明显写操作 cmdlet
  - 对 `python/perl/...` 等解释器默认 **不** 判为只读（避免误放行）

- `CodeAgent._on_after_tool_call()` 在判定本轮为“全只读 tool 调用”时，跳过完整后处理链路。

### 与质量的关系

- 这不是“为了省 token 而跳过检查”，而是避免把**只读验证**误当成**写操作后的代码变更**来处理。

## 与 `code_analysis` 提示词增强的关系

`builtin/prompts/code_agent_system/code_analysis.md` 已要求：当任务可结束时输出 `<JCA_DELIVERY>` 块。  
这属于 **方案 A 的提示词落地点**，让分析类任务更容易被结构化标记捕获。

> 其他场景可逐步复用同一块协议（不强制所有场景都开启）。

## 非交互模式下的工作区提示（`confirm_add_new_files`）补充

当启用“新增文件检查”并触发清单提示时，**非交互模式**默认只展示清单、不做隐式副作用（如自动批量写入 `.gitignore` 等），相关逻辑见 `src/jarvis/jarvis_utils/git_utils.py` 的 `confirm_add_new_files()`（该行为来自独立的安全策略，不等同于 A/B/C，但与长会话/自动化有关）。

## 排障与回归检查清单

- 如果你希望 jca 在摘要压缩后**稳定停止重复**：
  - 确认最终回答包含 `<JCA_DELIVERY>` 且 `delivered: true`
  - 确认交付引用（`artifact_refs`）能指向可复核的源文件/证据

- 如果你发现只读 `rg` 仍触发重后处理：
  - 检查 `execute_script` 是否是单行 bash，以及命令是否在白名单与不含写操作子串
  - 多工具混合调用中只要存在非只读 tool，整轮仍会走重后处理（符合保守策略）
