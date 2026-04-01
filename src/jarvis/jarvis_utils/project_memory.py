# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple

from jarvis.jarvis_utils.output import PrettyOutput


def get_git_root_fallback(cwd: Optional[str] = None) -> str:
    """尽可能稳定地获取当前工程的 git 根目录。

    优先：git rev-parse --show-toplevel；失败则回退到 cwd 或 os.getcwd()。
    """
    base = cwd or os.getcwd()
    try:
        rr = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=base,
        )
        if rr.returncode == 0:
            p = rr.stdout.strip()
            if p and os.path.isdir(p):
                return p
    except Exception:
        pass
    return base


def get_jvs_memory_path(project_root: str) -> str:
    return os.path.join(project_root, "JVS_MEMORY.md")


def read_jvs_memory(project_root: str) -> Optional[str]:
    path = get_jvs_memory_path(project_root)
    try:
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read().strip()
        return content or None
    except Exception:
        return None


def write_jvs_memory(project_root: str, content: str) -> bool:
    path = get_jvs_memory_path(project_root)
    try:
        with open(path, "w", encoding="utf-8", errors="replace") as f:
            f.write(content.rstrip() + "\n")
        return True
    except Exception as e:
        PrettyOutput.auto_print(f"⚠️ 写入 JVS_MEMORY.md 失败: {e}")
        return False


def _get_rules_fingerprint(project_root: str) -> str:
    try:
        from jarvis.jarvis_agent.rules_manager import RulesManager

        rm = RulesManager(project_root)
        return rm._get_rules_index_fingerprint()  # type: ignore[attr-defined]
    except Exception:
        return ""


def _get_tools_overview() -> str:
    # 优先复用 ToolRegistry 的全局缓存，避免为生成 JVS_MEMORY 再次完整加载工具/MCP（否则会重复触发覆盖告警）
    try:
        from jarvis.jarvis_tools import registry as tool_registry_mod

        cached = getattr(tool_registry_mod, "_tools_cache", {}).get("all_tools")
        if isinstance(cached, dict) and cached:
            names = sorted(cached.keys())
            preview = ", ".join(names[:30])
            extra = (
                f"…（共{len(names)}个）" if len(names) > 30 else f"（共{len(names)}个）"
            )
            return (
                f"工具概况: {preview}{extra}" if preview else f"工具概况: （共{len(names)}个）"
            )
    except Exception:
        pass

    try:
        from jarvis.jarvis_tools.registry import ToolRegistry

        tr = ToolRegistry()
        tools = tr.get_all_tools()
        names = [t.get("name", "") for t in tools if isinstance(t, dict)]
        names = [n for n in names if n]
        preview = ", ".join(names[:30])
        extra = f"…（共{len(names)}个）" if len(names) > 30 else f"（共{len(names)}个）"
        return f"工具概况: {preview}{extra}" if preview else f"工具概况: （共{len(names)}个）"
    except Exception:
        return "工具概况: （获取失败）"


def build_jvs_memory(project_root: str) -> str:
    """构建用于快速启动的工程摘要。内容尽量短、稳定、可复用。"""
    try:
        from jarvis.jarvis_code_agent.utils import get_project_overview

        overview = get_project_overview(project_root).strip()
    except Exception:
        overview = ""

    rules_fp = _get_rules_fingerprint(project_root)
    tools_overview = _get_tools_overview()

    header = [
        "# JVS_MEMORY.md",
        "",
        "该文件由 Jarvis 自动生成，用于加速大工程下的启动与“开始回答”时间。",
        "",
        f"- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 项目根目录: {project_root}",
        f"- 规则索引指纹: {rules_fp or '(unknown)'}",
        "",
        "---",
        "",
    ]

    body_parts = []
    if overview:
        body_parts.append(overview)
    body_parts.append(tools_overview)

    return "\n".join(header + body_parts).strip() + "\n"


def ensure_jvs_memory(project_root: str) -> Tuple[bool, str]:
    """确保 JVS_MEMORY.md 存在；若不存在则生成并写入。返回 (是否写入, 文件路径)。"""
    path = get_jvs_memory_path(project_root)
    if os.path.exists(path):
        return False, path
    content = build_jvs_memory(project_root)
    ok = write_jvs_memory(project_root, content)
    return bool(ok), path

