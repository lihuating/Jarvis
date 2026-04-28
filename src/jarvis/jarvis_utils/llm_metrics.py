# -*- coding: utf-8 -*-
"""轻量 LLM 调用观测（JSONL + 滚动）。

设计目标：
- **默认仅记录慢调用**，避免噪音与磁盘膨胀。
- 写入位置：`~/.jarvis/metrics/`（通过 get_data_dir() 获取）。
- 滚动策略：按大小滚动（默认 10MB），保留最近 N 份历史（默认 5 份）。

注意：这是“运行时观测”，不是对话记录；即使写入失败也不应影响主流程。
"""

import json
import os
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from jarvis.jarvis_utils.config import get_data_dir


@dataclass(frozen=True)
class LlmCallMetrics:
    ts: float
    platform: str
    model: str
    tier: str
    conversation_turn: int
    input_chars: int
    input_tokens: int
    output_tokens: int
    duration_s: float
    first_token_s: float
    tokens_per_second: float
    remaining_tokens: Optional[int] = None
    max_input_tokens: Optional[int] = None


_LOCK = threading.Lock()


def _metrics_dir() -> str:
    return os.path.join(get_data_dir(), "metrics")


def _log_path() -> str:
    return os.path.join(_metrics_dir(), "llm_calls.jsonl")


def _rotate_if_needed(path: str, *, max_bytes: int, keep_files: int) -> None:
    try:
        if not os.path.isfile(path):
            return
        size = os.path.getsize(path)
        if size < max_bytes:
            return

        # 例如：
        # llm_calls.jsonl -> llm_calls.1.jsonl
        # llm_calls.1.jsonl -> llm_calls.2.jsonl ...
        for i in range(keep_files - 1, 0, -1):
            src = f"{path.rsplit('.', 1)[0]}.{i}.jsonl"
            dst = f"{path.rsplit('.', 1)[0]}.{i+1}.jsonl"
            if os.path.isfile(src):
                try:
                    os.replace(src, dst)
                except Exception:
                    pass
        try:
            os.replace(path, f"{path.rsplit('.', 1)[0]}.1.jsonl")
        except Exception:
            # 旋转失败则直接不旋转，避免影响主流程
            return
    except Exception:
        return


def should_log_slow_call(
    *, first_token_s: float, duration_s: float, ttft_threshold_s: float, duration_threshold_s: float
) -> bool:
    return bool(first_token_s >= ttft_threshold_s or duration_s >= duration_threshold_s)


def log_llm_call_metrics(
    metrics: LlmCallMetrics,
    *,
    slow_only: bool = True,
    ttft_threshold_s: float = 3.0,
    duration_threshold_s: float = 10.0,
    rotate_max_mb: int = 10,
    rotate_keep_files: int = 5,
) -> Tuple[bool, str]:
    """写入一条 JSONL 指标记录。失败也返回 (False, reason) 且不抛异常。"""
    try:
        if slow_only and not should_log_slow_call(
            first_token_s=metrics.first_token_s,
            duration_s=metrics.duration_s,
            ttft_threshold_s=ttft_threshold_s,
            duration_threshold_s=duration_threshold_s,
        ):
            return False, "skipped_not_slow"

        d = _metrics_dir()
        os.makedirs(d, exist_ok=True)
        path = _log_path()

        max_bytes = int(max(1, rotate_max_mb)) * 1024 * 1024
        keep_files = max(1, int(rotate_keep_files))

        payload: Dict[str, Any] = {
            "ts": metrics.ts or time.time(),
            "platform": metrics.platform,
            "model": metrics.model,
            "tier": metrics.tier,
            "conversation_turn": metrics.conversation_turn,
            "input_chars": metrics.input_chars,
            "input_tokens": metrics.input_tokens,
            "output_tokens": metrics.output_tokens,
            "duration_s": metrics.duration_s,
            "first_token_s": metrics.first_token_s,
            "tokens_per_second": metrics.tokens_per_second,
            "remaining_tokens": metrics.remaining_tokens,
            "max_input_tokens": metrics.max_input_tokens,
        }

        line = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

        with _LOCK:
            _rotate_if_needed(path, max_bytes=max_bytes, keep_files=keep_files)
            with open(path, "a", encoding="utf-8", newline="\n") as f:
                f.write(line + "\n")
        return True, path
    except Exception as e:
        return False, f"error:{e}"

