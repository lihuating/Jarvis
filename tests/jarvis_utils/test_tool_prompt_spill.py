# -*- coding: utf-8 -*-
"""tool_prompt_spill：超长工具输出外置（原文 payload + meta JSON）。"""

from pathlib import Path

import pytest

from jarvis.jarvis_utils.tool_prompt_spill import materialize_large_tool_prompt_for_session


def test_short_prompt_unchanged(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "jarvis.jarvis_utils.config.get_data_dir", lambda: str(tmp_path)
    )
    s = "hello"
    assert materialize_large_tool_prompt_for_session(s, agent_name="A") == s


def test_long_prompt_spilled(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "jarvis.jarvis_utils.config.get_data_dir", lambda: str(tmp_path)
    )
    big = "Z" * 60_000
    out = materialize_large_tool_prompt_for_session(big, agent_name="UnitTest")
    assert "工具输出已外置" in out
    assert ".payload.txt" in out
    assert "SHA256" in out
    spill_dir = tmp_path / "tool_spill"
    assert spill_dir.is_dir()
    payloads = list(spill_dir.glob("*.payload.txt"))
    assert len(payloads) == 1
    assert payloads[0].read_text(encoding="utf-8") == big
    metas = list(spill_dir.glob("*.meta.json"))
    assert len(metas) == 1
