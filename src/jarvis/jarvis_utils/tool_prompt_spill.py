# -*- coding: utf-8 -*-
"""工具结果写入 session.prompt 前的外置策略（对齐 Claude Code 思路，质量优先）。

- **准确度**：完整工具输出写入单独的 ``*.payload.txt``，文件内**不含**任何 Jarvis
  注入前缀，便于与工具原文逐字对照、用 ``read_code`` 全文引用。
- **元数据**：``*.meta.json`` 记录 agent、阈值、长度、SHA256 等，便于核对读回是否一致。
- **会话内说明**：向模型提供路径、校验和、首尾 + 可选**中部**预览，降低「只看到头尾而漏掉中段」的风险。

环境变量（可选）：
- ``JARVIS_TOOL_PROMPT_MAX_INLINE_CHARS``：超过则外置（默认 120000，质量优先略抬高内联上限）
- ``JARVIS_TOOL_PROMPT_PREVIEW_HEAD_CHARS`` / ``JARVIS_TOOL_PROMPT_PREVIEW_TAIL_CHARS``
- ``JARVIS_TOOL_PROMPT_PREVIEW_MIDDLE_CHARS``：中部预览窗口（默认 8000，0 表示关闭）
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime
from datetime import timezone
from typing import Optional


def _max_inline_chars() -> int:
    raw = os.environ.get("JARVIS_TOOL_PROMPT_MAX_INLINE_CHARS", "120000").strip()
    try:
        n = int(raw)
    except ValueError:
        n = 120_000
    return max(1_000, min(n, 2_000_000))


def _preview_limits() -> tuple[int, int, int]:
    """(head_chars, tail_chars, middle_chars)。"""
    try:
        head = int(os.environ.get("JARVIS_TOOL_PROMPT_PREVIEW_HEAD_CHARS", "24000"))
    except ValueError:
        head = 24_000
    try:
        tail = int(os.environ.get("JARVIS_TOOL_PROMPT_PREVIEW_TAIL_CHARS", "12000"))
    except ValueError:
        tail = 12_000
    try:
        mid = int(os.environ.get("JARVIS_TOOL_PROMPT_PREVIEW_MIDDLE_CHARS", "8000"))
    except ValueError:
        mid = 8_000
    head = max(500, min(head, 500_000))
    tail = max(0, min(tail, 500_000))
    mid = max(0, min(mid, 200_000))
    return head, tail, mid


def _sha256_utf8(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def _middle_slice(text: str, head_n: int, tail_n: int, mid_n: int) -> Optional[str]:
    """若文本足够长，取几何中心附近一段作为中部预览。"""
    if mid_n <= 0:
        return None
    n = len(text)
    if n <= head_n + tail_n + mid_n + 4000:
        return None
    core = n - head_n - tail_n
    center = head_n + core // 2
    half = mid_n // 2
    start = max(head_n, center - half)
    end = min(n - tail_n, start + mid_n)
    if end - start < mid_n // 2:
        return None
    return text[start:end]


def materialize_large_tool_prompt_for_session(
    tool_prompt: str,
    *,
    agent_name: Optional[str] = None,
) -> str:
    """若工具拼接串过长则外置到磁盘，返回应写入 session 的文本。

    参数:
        tool_prompt: 工具执行后拟拼入 session 的完整字符串
        agent_name: 可选，写入元数据便于排查

    返回:
        可直接 join 到 session.prompt 的字符串（可能为原文或外置说明）
    """
    if not isinstance(tool_prompt, str) or not tool_prompt:
        return tool_prompt if isinstance(tool_prompt, str) else ""

    limit = _max_inline_chars()
    if len(tool_prompt) <= limit:
        return tool_prompt

    try:
        from jarvis.jarvis_utils.config import get_data_dir
        from jarvis.jarvis_utils.output import PrettyOutput

        spill_dir = os.path.join(get_data_dir(), "tool_spill")
        os.makedirs(spill_dir, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        uid = uuid.uuid4().hex
        base = f"{stamp}_{uid}"
        payload_path = os.path.join(spill_dir, f"{base}.payload.txt")
        meta_path = os.path.join(spill_dir, f"{base}.meta.json")

        digest = _sha256_utf8(tool_prompt)
        created = datetime.now(timezone.utc).isoformat()

        # 原文单独落盘，便于对照与 read_code 全量读取
        with open(
            payload_path, "w", encoding="utf-8", newline="\n", errors="replace"
        ) as f:
            f.write(tool_prompt)

        meta_obj = {
            "version": 1,
            "kind": "tool_prompt_spill",
            "created_utc": created,
            "agent_name": agent_name or "",
            "original_chars": len(tool_prompt),
            "threshold_chars": limit,
            "sha256_utf8": digest,
            "payload_file": os.path.basename(payload_path),
            "meta_file": os.path.basename(meta_path),
        }
        with open(meta_path, "w", encoding="utf-8", newline="\n") as mf:
            json.dump(meta_obj, mf, ensure_ascii=False, indent=2)

        head_n, tail_n, mid_n = _preview_limits()
        head = tool_prompt[:head_n]
        tail = tool_prompt[-tail_n:] if tail_n > 0 else ""
        middle = _middle_slice(tool_prompt, head_n, tail_n, mid_n)

        PrettyOutput.auto_print(
            f"ℹ️ 工具输出过长（{len(tool_prompt)} 字符 > {limit}），已外置原文: {payload_path}"
        )

        lines = [
            "## 工具输出已外置（质量优先：原文落盘，会话内仅摘要）",
            "",
            "**完整输出**与工具返回**逐字一致**，已写入下列文件（请用 `read_code` 读取该 `.payload.txt` 后再推理；不要用本消息里的预览代替全文验收）：",
            "",
            f"- **payload（原文）**: `{payload_path}`",
            f"- **meta（元数据）**: `{meta_path}`",
            f"- **UTF-8 SHA256（原文）**: `{digest}`",
            f"- **原始长度**: {len(tool_prompt)} 字符",
            f"- **内联上限**: {limit} 字符（`JARVIS_TOOL_PROMPT_MAX_INLINE_CHARS`）",
            "",
            "读完 `read_code` 后，可将关键片段与上述 SHA256 对照，确认未被截断或重复粘贴污染。",
            "",
            "### 预览（首部）",
            "",
            "```text",
            head,
            "```",
            "",
        ]
        if middle is not None:
            lines.extend(
                [
                    "### 预览（中部，几何中心附近）",
                    "",
                    "_用于长日志/大段输出时降低「仅头尾而漏中段」的风险；仍以 payload 全文为准。_",
                    "",
                    "```text",
                    middle,
                    "```",
                    "",
                ]
            )
        if tail_n > 0 and len(tool_prompt) > head_n + tail_n:
            lines.extend(
                [
                    "### 预览（尾部）",
                    "",
                    "```text",
                    tail,
                    "```",
                    "",
                ]
            )
        lines.append(
            "_后续步骤：优先 `read_code` 定位 payload 中的证据行，再写报告或改代码；避免把整份 payload 再次粘贴进对话。_"
        )
        return "\n".join(lines)
    except Exception:
        # 外置失败时不阻塞主流程：退回原文（可能仍会触发后续截断逻辑）
        return tool_prompt
