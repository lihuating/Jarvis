# -*- coding: utf-8 -*-
"""CodeAgent 交付/验证治理：只读脚本判定、验证缓存、交付落盘与短路。

目标：
- 在尽量不影响质量的前提下，减少「只读验证 → 误触发重后处理 → token 膨胀 → 摘要重置 → 再验证」的循环。
- 将「已交付」从自然语言表述升级为可机读、可落盘的结构化标记。
"""

import hashlib
import json
import os
import re
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from jarvis.jarvis_utils.output import PrettyOutput


_JCA_DELIVERY_BLOCK = re.compile(
    r"<JCA_DELIVERY>\s*(\{[\s\S]*?\})\s*</JCA_DELIVERY>",
    re.IGNORECASE,
)


def normalize_task_text(text: str) -> str:
    return " ".join((text or "").split()).strip()


def task_fingerprint(repo_root: str, start_commit: Optional[str], user_input: str) -> str:
    base = f"{repo_root}\n{start_commit or ''}\n{normalize_task_text(user_input)}"
    return hashlib.sha256(base.encode("utf-8", errors="ignore")).hexdigest()


def marker_paths(repo_root: str, fp: str) -> Tuple[Path, Path]:
    base = Path(repo_root) / ".jarvis" / "code_agent" / "deliveries" / fp
    return base.with_suffix(".marker.json"), base.with_suffix(".delivery.json")


def load_marker(marker_path: Path) -> Optional[Dict[str, Any]]:
    try:
        if not marker_path.exists():
            return None
        with open(marker_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def write_marker(
    marker_path: Path,
    *,
    fingerprint: str,
    scenario: str,
    delivered: bool,
    artifact_type: str,
    artifact_refs: List[str],
    evidence: Optional[Dict[str, Any]] = None,
) -> None:
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "fingerprint": fingerprint,
        "scenario": scenario,
        "delivered": bool(delivered),
        "artifact_type": artifact_type,
        "artifact_refs": list(artifact_refs or []),
        "evidence": evidence or {},
    }
    with open(marker_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def write_delivery_artifact(
    delivery_path: Path,
    *,
    fingerprint: str,
    scenario: str,
    delivery_obj: Dict[str, Any],
    last_model_text: str,
) -> None:
    delivery_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "fingerprint": fingerprint,
        "scenario": scenario,
        "delivery": delivery_obj,
        "last_model_text_excerpt": (last_model_text or "")[:20000],
    }
    with open(delivery_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def parse_delivery_block(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    m = _JCA_DELIVERY_BLOCK.search(text)
    if not m:
        return None
    raw = m.group(1).strip()
    try:
        obj = json.loads(raw)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def user_requests_force_rerun(user_input: str) -> bool:
    t = (user_input or "").lower()
    keys = (
        "force",
        "rerun",
        "re-run",
        "重新",
        "再来",
        "重做",
        "重跑",
        "重新分析",
        "重新输出",
    )
    return any(k in (user_input or "") for k in keys) or any(k in t for k in ("rerun", "re-run", "force"))


def _strip_quotes(s: str) -> str:
    s2 = s.strip()
    if len(s2) >= 2 and ((s2[0] == s2[-1] == '"') or (s2[0] == s2[-1] == "'")):
        return s2[1:-1]
    return s2


def _tokenize_powershell(script: str) -> List[str]:
    # 极简分词：按空白切分，保留简单引号包裹 token
    try:
        return shlex.split(script, posix=False)
    except Exception:
        return script.split()


def _bash_tokens_one_line(script: str) -> List[str]:
    # 仅支持「单行」bash 场景（jca 里 rg 查询基本都是单行）
    s = (script or "").strip()
    if not s:
        return []
    if "\n" in s:
        return []
    try:
        return shlex.split(s, posix=True)
    except Exception:
        return s.split()


_SAFE_BASH_PREFIXES: Tuple[str, ...] = (
    "rg",
    "grep",
    "git",
    "sed",
    "awk",
    "head",
    "tail",
    "wc",
    "ls",
    "find",
    "stat",
    "file",
    "cat",
    "less",
    "more",
    "which",
    "whoami",
    "pwd",
    "uname",
)

_SAFE_PS_CMDLETS = (
    "Select-String",
    "Get-Content",
    "Get-ChildItem",
    "Measure-Object",
    "Where-Object",
    "Sort-Object",
    "Select-Object",
    "Format-Table",
    "Format-List",
)


def is_execute_script_read_only(interpreter: str, script_content: str) -> bool:
    """保守判定：仅允许常见只读查询命令；无法判定则返回 False。"""
    it = (interpreter or "").strip().lower()
    sc = script_content or ""

    if it in ("bash", "sh", "zsh"):
        toks = _bash_tokens_one_line(sc)
        if not toks:
            return False
        cmd0 = toks[0].lower().lstrip("./")
        if cmd0 in _SAFE_BASH_PREFIXES:
            # 禁止明显危险子串（保守）
            banned = (
                ">",
                ">>",
                "| bash",
                "|sh",
                "| zsh",
                "curl ",
                "wget ",
                "chmod ",
                "chown ",
                "rm ",
                "mv ",
                "cp ",
                "tee ",
                "python ",
                "python3 ",
                "perl ",
                "ruby ",
                "node ",
                "npm ",
                "yarn ",
                "docker ",
                "kubectl ",
            )
            low = sc.lower()
            if any(b in low for b in banned):
                return False
            return True
        return False

    if it in ("powershell", "pwsh"):
        toks = _tokenize_powershell(sc)
        if not toks:
            return False
        # 允许 Select-String / Get-Content / Get-ChildItem 等只读 cmdlet 开头
        first = toks[0]
        if first in _SAFE_PS_CMDLETS:
            low = sc.lower()
            banned = (
                "set-content",
                "add-content",
                "out-file",
                "new-item",
                "remove-item",
                "move-item",
                "copy-item",
                "start-process",
                "invoke-webrequest",
                "irm ",
                "iwr ",
            )
            if any(b in low for b in banned):
                return False
            return True
        return False

    # python 等解释器默认不视为只读（避免误判）
    return False


def extract_execute_script_calls_from_tool_response(response: Optional[str]) -> List[Tuple[str, str]]:
    """从模型响应中的 TOOL_CALL 块解析 execute_script 的 (interpreter, script_content)。"""
    if not response or not isinstance(response, str):
        return []
    try:
        from jarvis.jarvis_utils.jsonnet_compat import loads as json_loads
        from jarvis.jarvis_utils.tag import ct, ot

        pattern = (
            rf"(?msi){re.escape(ot('TOOL_CALL'))}(.*?)^{re.escape(ct('TOOL_CALL'))}"
        )
        matches = re.findall(pattern, response)
        out: List[Tuple[str, str]] = []
        for block in matches:
            text = block.strip()
            if not text:
                continue
            try:
                obj: Any = json_loads(text)
            except Exception:
                try:
                    obj = json.loads(text)
                except Exception:
                    continue

            payloads: List[Any]
            if isinstance(obj, dict):
                payloads = [obj]
            elif isinstance(obj, list):
                payloads = obj
            else:
                continue

            for item in payloads:
                if not isinstance(item, dict):
                    continue
                if item.get("name") != "execute_script":
                    continue
                args = item.get("arguments")
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except Exception:
                        args = None
                if not isinstance(args, dict):
                    continue
                interpreter = str(args.get("interpreter") or "bash")
                script_content = str(args.get("script_content") or "")
                out.append((interpreter, script_content))
        return out
    except Exception:
        return []


@dataclass(frozen=True)
class VerificationCacheKey:
    fingerprint: str
    diff_hash: str
    interpreter: str
    script_hash: str


class VerificationCache:
    """进程内验证缓存：同一任务指纹 + 同一 diff + 同一脚本内容 → 跳过重复重后处理。"""

    def __init__(self) -> None:
        self._hits: Dict[str, VerificationCacheKey] = {}

    def record_and_should_skip_heavy_postprocess(
        self, fp: str, diff_hash: str, interpreter: str, script_content: str
    ) -> bool:
        """第一次返回 False（允许执行一次），从第二次开始返回 True。"""
        sh = hashlib.sha256((script_content or "").encode("utf-8", errors="ignore")).hexdigest()
        k = VerificationCacheKey(
            fingerprint=fp,
            diff_hash=diff_hash,
            interpreter=interpreter.strip().lower(),
            script_hash=sh,
        )
        ck = f"{k.fingerprint}:{k.diff_hash}:{k.interpreter}:{k.script_hash}"
        if ck in self._hits:
            return True
        self._hits[ck] = k
        return False


def compute_diff_hash_for_cache() -> str:
    """用于缓存键：优先使用 HEAD；空仓库则使用工作区 diff 文本 hash。"""
    try:
        head_ok = (
            subprocess.run(
                ["git", "rev-parse", "--verify", "HEAD"],
                capture_output=True,
                text=False,
                check=False,
            ).returncode
            == 0
        )
    except Exception:
        head_ok = False

    try:
        if head_ok:
            r = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=False,
                check=False,
            )
            h = decode_git_stdout(r.stdout).strip()
            return h or "no-head"
        # 空仓库：用 diff 文本做 hash（可能更贵，但只在无 HEAD 时发生）
        from jarvis.jarvis_utils.git_utils import get_diff

        d = get_diff() or ""
        return hashlib.sha256(d.encode("utf-8", errors="ignore")).hexdigest()
    except Exception:
        return "unknown"


def decode_git_stdout(data: Optional[bytes]) -> str:
    from jarvis.jarvis_utils.utils import decode_output

    return decode_output(data) if data else ""


def maybe_short_circuit_delivered_run(
    *,
    repo_root: str,
    start_commit: Optional[str],
    user_input: str,
    scenario: str,
) -> Optional[str]:
    """若已存在交付标记且用户未强制重跑，则直接短路返回。"""
    fp = task_fingerprint(repo_root, start_commit, user_input)
    marker_path, delivery_path = marker_paths(repo_root, fp)
    marker = load_marker(marker_path)
    if not marker or not marker.get("delivered"):
        return None
    if user_requests_force_rerun(user_input):
        return None

    refs = marker.get("artifact_refs") or []
    refs_txt = "\n".join(f"- {r}" for r in refs) if refs else "- （无额外引用）"
    return (
        "ℹ️ 检测到该任务此前已标记为交付完成（基于任务指纹与起始 commit），为避免摘要压缩后重复执行，本次已短路。\n\n"
        f"- 任务指纹: `{fp}`\n"
        f"- 场景: `{scenario}`\n"
        f"- 交付标记文件: `{marker_path}`\n"
        f"- 交付快照文件: `{delivery_path}`\n\n"
        "**交付引用：**\n"
        f"{refs_txt}\n\n"
        "如需重新完整执行，请在需求中明确包含「重新/重做/重跑/force」等关键词。"
    )
