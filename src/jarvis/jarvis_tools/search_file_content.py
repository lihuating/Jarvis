# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import shutil
import subprocess
from typing import Any, Dict, List

from jarvis.jarvis_utils.config import get_allowed_dirs


def _get_additional_roots() -> List[str]:
    """默认搜索根目录：当前工作目录 + AddDir 追加目录（env + config）。"""
    roots: List[str] = []

    try:
        roots.append(os.path.abspath(os.getcwd()))
    except Exception:
        pass

    # 会话内追加（AddDir session）：JARVIS_ADDITIONAL_DIRS，使用 ':' 分隔
    try:
        env_val = os.environ.get("JARVIS_ADDITIONAL_DIRS", "").strip()
        if env_val:
            for p in env_val.split(":"):
                p = (p or "").strip()
                if p:
                    roots.append(p)
    except Exception:
        pass

    # 项目/全局配置追加（AddDir project）：allowed_dirs
    try:
        roots.extend(get_allowed_dirs())
    except Exception:
        pass

    # 归一化 + 去重保序 + 仅保留存在目录
    out: List[str] = []
    seen = set()
    for p in roots:
        try:
            ep = os.path.expanduser(os.path.expandvars(str(p)))
            ap = os.path.abspath(ep)
            if ap in seen:
                continue
            if os.path.isdir(ap):
                seen.add(ap)
                out.append(ap)
        except Exception:
            continue
    return out


class SearchFileContentTool:
    name = "search_file_content"
    description = (
        "在文件内容中搜索指定文本/正则（基于 ripgrep）。"
        "默认搜索范围：当前工作目录 + AddDir 追加目录（JARVIS_ADDITIONAL_DIRS / allowed_dirs）。"
        "如需限制范围可显式传 roots。"
    )
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "要搜索的正则/文本（ripgrep 语法，默认按正则）。",
            },
            "literal": {
                "type": "boolean",
                "description": "是否按纯文本匹配（等价 rg -F），默认 false。",
                "default": False,
            },
            "case_insensitive": {
                "type": "boolean",
                "description": "是否忽略大小写（rg -i），默认 false。",
                "default": False,
            },
            "file_glob": {
                "type": "string",
                "description": "文件 glob 过滤（rg --glob），例如 '*.py' 或 '**/*.md'。",
            },
            "roots": {
                "type": "array",
                "items": {"type": "string"},
                "description": "搜索根目录列表。为空/不传则默认使用当前目录 + AddDir 追加目录。",
            },
            "max_results": {
                "type": "number",
                "description": "最大命中行数（rg --max-count），默认 200。",
                "default": 200,
            },
        },
        "required": ["pattern"],
    }

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        pattern = str(args.get("pattern", "")).strip()
        if not pattern:
            return {"success": False, "stdout": "", "stderr": "pattern 不能为空"}

        rg_path = shutil.which("rg")
        if not rg_path:
            return {
                "success": False,
                "stdout": "",
                "stderr": "未找到 ripgrep（rg）。请先安装 rg，或改用 execute_script 调用 grep/rg。",
            }

        literal = bool(args.get("literal", False))
        case_insensitive = bool(args.get("case_insensitive", False))
        file_glob = str(args.get("file_glob", "") or "").strip()
        max_results = int(args.get("max_results", 200) or 200)

        roots_arg = args.get("roots")
        if isinstance(roots_arg, list) and any(str(x).strip() for x in roots_arg):
            roots = [str(x).strip() for x in roots_arg if str(x).strip()]
        else:
            roots = _get_additional_roots()

        # rg 选项：line-number + no-heading 便于后处理
        base_cmd: List[str] = [
            rg_path,
            "--line-number",
            "--no-heading",
            "--hidden",
            "--max-count",
            str(max_results),
        ]
        if literal:
            base_cmd.append("-F")
        if case_insensitive:
            base_cmd.append("-i")
        if file_glob:
            base_cmd.extend(["--glob", file_glob])

        # 兼容：有些额外目录可能包含巨量内容，默认也排除 .git
        base_cmd.extend(["--glob", "!.git/**"])

        outputs: List[str] = []
        errors: List[str] = []
        any_match = False

        for root in roots:
            try:
                cmd = base_cmd + [pattern, root]
                p = subprocess.run(  # nosec B603,B607 - 执行 rg 搜索
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                if p.stdout.strip():
                    any_match = True
                    outputs.append(f"## ROOT: {os.path.abspath(root)}\n{p.stdout.rstrip()}")
                # rg：0=有命中，1=无命中，2=错误
                if p.returncode == 2:
                    err = (p.stderr or "").strip() or "rg 执行失败"
                    errors.append(f"[{os.path.abspath(root)}] {err}")
            except Exception as e:
                errors.append(f"[{os.path.abspath(root)}] {e}")

        stdout = "\n\n".join(outputs) if outputs else ""
        if not any_match:
            stdout = "未找到匹配内容。"

        stderr = "\n".join(errors).strip()
        success = True if not errors else True  # 搜索可部分成功，错误写入 stderr
        return {"success": success, "stdout": stdout, "stderr": stderr}

