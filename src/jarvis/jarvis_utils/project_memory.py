# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple

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
    try:
        from jarvis.jarvis_tools import registry as tool_registry_mod

        cached = getattr(tool_registry_mod, "_tools_cache", {}).get("all_tools")
        if isinstance(cached, dict) and cached:
            names = sorted(cached.keys())
            preview = ", ".join(names[:40])
            extra = (
                f"…（共{len(names)}个）" if len(names) > 40 else f"（共{len(names)}个）"
            )
            return f"- Jarvis 内置/已加载工具预览: {preview}{extra}"
    except Exception:
        pass

    try:
        from jarvis.jarvis_tools.registry import ToolRegistry

        tr = ToolRegistry()
        tools = tr.get_all_tools()
        names = [t.get("name", "") for t in tools if isinstance(t, dict)]
        names = [n for n in names if n]
        preview = ", ".join(sorted(names)[:40])
        extra = f"…（共{len(names)}个）" if len(names) > 40 else f"（共{len(names)}个）"
        return f"- Jarvis 内置/已加载工具预览: {preview}{extra}"
    except Exception:
        return "- Jarvis 工具概况: （获取失败）"


def _read_text_file_safely(path: str, max_chars: int = 200_000) -> str:
    try:
        if not os.path.exists(path):
            return ""
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            s = f.read()
        if len(s) > max_chars:
            return s[:max_chars]
        return s
    except Exception:
        return ""


def _run_git(
    project_root: str, args: List[str], timeout: int = 60
) -> Tuple[int, str]:
    try:
        rr = subprocess.run(
            ["git"] + args,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=timeout,
            errors="replace",
        )
        return rr.returncode, (rr.stdout or "").strip()
    except Exception:
        return -1, ""


# --- JVS_MEMORY：目录全量索引 + cheap LLM 按 15 维生成 ---------------------------------

_SKIP_WALK_DIRS = frozenset(
    {
        ".git",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        "dist",
        "build",
        "target",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        "eggs",
        ".eggs",
        "htmlcov",
        ".gradle",
    }
)

_TEXT_EXTS = frozenset(
    {
        ".md",
        ".txt",
        ".py",
        ".toml",
        ".yaml",
        ".yml",
        ".json",
        ".rs",
        ".go",
        ".c",
        ".h",
        ".cpp",
        ".hpp",
        ".java",
        ".kt",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".css",
        ".html",
        ".sh",
        ".bash",
        ".zsh",
        ".sql",
        ".xml",
        ".ini",
        ".cfg",
        ".rb",
        ".php",
        ".swift",
        ".scala",
        ".clj",
        ".dockerfile",
    }
)

_GOVERNANCE_NAMES = ("AGENTS.md", "CLAUDE.md", "GEMINI.md")

_JVS_REQUIRED_SECTIONS: Tuple[str, ...] = (
    "## 项目概述",
    "## 项目结构",
    "## 核心组件",
    "## 主要命令",
    "## 构建和运行",
    "## 配置说明",
    "## 开发约定",
    "## 核心概念",
    "## 依赖关系",
    "## 新增功能",
    "## 架构演变",
    "## 常见使用场景",
    "## 注意事项",
    "## 参考资源",
    "## 总结",
)


def _list_project_files_with_sizes(root: str) -> List[Tuple[str, int]]:
    root = os.path.abspath(root)
    out: List[Tuple[str, int]] = []
    try:
        for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
            dirnames[:] = [d for d in dirnames if d not in _SKIP_WALK_DIRS]
            for fn in filenames:
                if fn.endswith((".pyc", ".pyo", ".so", ".dll", ".dylib", ".exe")):
                    continue
                fp = os.path.join(dirpath, fn)
                try:
                    st = os.stat(fp)
                    if not os.path.isfile(fp):
                        continue
                    rel = os.path.relpath(fp, root).replace(os.sep, "/")
                    out.append((rel, int(st.st_size)))
                except OSError:
                    continue
    except Exception:
        pass
    return out


def _extension_histogram(paths: List[Tuple[str, int]]) -> str:
    hist: dict[str, int] = {}
    for rel, _ in paths:
        ext = os.path.splitext(rel)[1].lower() or "(无扩展名)"
        hist[ext] = hist.get(ext, 0) + 1
    lines = [f"  - `{k}`: {v}" for k, v in sorted(hist.items(), key=lambda x: (-x[1], x[0]))]
    return "\n".join(lines[:80])


def _is_probably_binary_sample(path: str) -> bool:
    try:
        with open(path, "rb") as f:
            chunk = f.read(4096)
        return b"\x00" in chunk
    except OSError:
        return True


def _read_head_lines(path: str, max_lines: int, max_chars: int) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines: List[str] = []
            total = 0
            for _ in range(max_lines):
                line = f.readline()
                if not line:
                    break
                if total + len(line) > max_chars:
                    break
                lines.append(line.rstrip("\n"))
                total += len(line)
        return "\n".join(lines)
    except Exception:
        return ""


def _collect_inventory_quick(project_root: str, max_list: int = 3500) -> str:
    files = _list_project_files_with_sizes(project_root)
    n = len(files)
    lines: List[str] = [
        f"【快速索引】当前目录 `{project_root}` 递归扫描（已跳过常见依赖/构建缓存目录）。",
        f"- 文件总数（近似）: {n}",
        "",
        "【扩展名统计（前 80 项）】",
        _extension_histogram(files),
        "",
        f"【相对路径列表（前 {max_list} 条，按字典序）】",
    ]
    for rel, sz in sorted(files, key=lambda x: x[0])[:max_list]:
        lines.append(f"  - {rel}  ({sz} bytes)")
    if n > max_list:
        lines.append(f"  … 另有 {n - max_list} 个文件未列出")
    return "\n".join(lines)


def _collect_inventory_full(project_root: str) -> str:
    files = _list_project_files_with_sizes(project_root)
    n = len(files)
    lines: List[str] = [
        f"【全量更新索引】目录 `{project_root}` 递归（已跳过 .git/node_modules 等）。",
        f"- 文件总数: {n}",
        "",
        "【扩展名统计】",
        _extension_histogram(files),
        "",
        "【全部相对路径（可能截断）】",
    ]
    max_paths_lines = 9000
    sorted_files = sorted(files, key=lambda x: x[0])
    for i, (rel, sz) in enumerate(sorted_files):
        if i >= max_paths_lines:
            lines.append(f"… 路径列表在第 {max_paths_lines} 条处截断，共 {n} 个文件")
            break
        lines.append(f"  - {rel}  ({sz} bytes)")
    # 代表性文本片段
    text_candidates = [
        (rel, sz)
        for rel, sz in sorted_files
        if os.path.splitext(rel)[1].lower() in _TEXT_EXTS and sz <= 400_000
    ]
    max_samples = 55
    step = max(1, len(text_candidates) // max_samples) if text_candidates else 1
    picked: List[Tuple[str, int]] = []
    for i in range(0, len(text_candidates), step):
        picked.append(text_candidates[i])
        if len(picked) >= max_samples:
            break
    lines.append("")
    lines.append("【代表性文本文件片段（抽检，每文件最多 45 行）】")
    root = os.path.abspath(project_root)
    for rel, sz in picked:
        fp = os.path.join(root, rel.replace("/", os.sep))
        if _is_probably_binary_sample(fp):
            lines.append(f"\n### `{rel}` ({sz} bytes) — 判定为二进制或不可读，跳过内容")
            continue
        snippet = _read_head_lines(fp, 45, 6000)
        lines.append(f"\n### `{rel}` ({sz} bytes)\n```\n{snippet}\n```")
    inv = "\n".join(lines)
    max_inv = 220_000
    if len(inv) > max_inv:
        inv = inv[:max_inv] + "\n\n…【素材因长度已截断】\n"
    return inv


def _read_governance_for_first_init(project_root: str, max_per_file: int = 48_000) -> str:
    parts: List[str] = []
    for name in _GOVERNANCE_NAMES:
        p = os.path.join(project_root, name)
        if not os.path.isfile(p):
            continue
        body = _read_text_file_safely(p, max_per_file)
        if body.strip():
            parts.append(f"### 文件: {name}\n\n{body.strip()}")
    if not parts:
        return ""
    blob = "\n\n---\n\n".join(parts)
    max_total = 100_000
    if len(blob) > max_total:
        blob = blob[:max_total] + "\n\n…（治理文档总长度已截断）\n"
    return blob


def _jvs_llm_single_shot(llm, prompt: str) -> str:
    """对指定平台单次 ``_chat``，恢复消息列表；**不使用** ``chat_until_success``（避免重试刷屏）。"""
    llm.set_suppress_output(True)
    prev_messages: List[Dict[str, str]] = []
    try:
        prev_messages = list(llm.get_messages())
    except Exception:
        prev_messages = []

    response: str = ""
    try:
        response = str(llm._chat(prompt, 0) or "").strip()
    except Exception:
        response = ""
    finally:
        try:
            llm.set_messages(prev_messages)
        except Exception:
            pass

    return response


def _generate_jvs_body_via_llm(prompt: str) -> Tuple[str, str]:
    """优先 cheap，失败再 normal；返回 ``(正文, 'cheap'|'normal')``。

    若两者均不可用、无有效响应或未通过 15 维校验，抛出 ``RuntimeError``。
    """
    from jarvis.jarvis_platform.registry import PlatformRegistry

    reg = PlatformRegistry.get_global_platform_registry()
    errors: List[str] = []

    for tier, getter in (
        ("cheap", reg.get_cheap_platform),
        ("normal", reg.get_normal_platform),
    ):
        try:
            llm = getter()
        except Exception as e:
            errors.append(f"{tier}: 无法创建平台 — {e}")
            continue
        raw = _jvs_llm_single_shot(llm, prompt)
        body = _strip_outer_markdown_fence(raw)
        if _validate_jvs_sections(body):
            return body, tier
        errors.append(f"{tier}: 无有效响应或未通过 15 维章节校验")

    detail = "；".join(errors) if errors else "未知原因"
    raise RuntimeError(
        "Init 生成 JVS_MEMORY.md 失败：cheap 与 normal 模型均未产出合规正文。"
        f"请检查 ~/.jarvis/config.yaml 与网络。详情：{detail}"
    )


def _jvs_llm_prompt(
    first_init: bool, governance_excerpt: str, inventory: str
) -> str:
    sections_list = "\n".join(_JVS_REQUIRED_SECTIONS)
    if first_init:
        mode_desc = (
            "【模式】**首次 Init（快速）**。可结合下方「治理文档摘录」（若存在）与「目录索引」撰写；"
            "治理文档与素材冲突时以素材为准。"
        )
        gov_section = (
            "【治理文档摘录（AGENTS.md / CLAUDE.md / GEMINI.md，可空）】\n"
            + (governance_excerpt.strip() or "（本目录下未找到上述文件或内容为空）")
        )
    else:
        mode_desc = (
            "【模式】**再次 Init（全量更新）**。**不要**依赖或复述旧版 AGENTS/CLAUDE 的成见；"
            "必须**主要依据**下方「全量目录与文件抽检素材」归纳；若某维度素材不足，写「（素材中未体现）」。"
        )
        gov_section = "【治理文档摘录】\n（更新模式：不使用治理文档，本块忽略。）"

    return f"""你是软件工程助理。请**只根据**下面提供的素材撰写 Markdown，**禁止编造**素材中不存在的事实或路径。

{mode_desc}

{gov_section}

【目录与文件素材】
{inventory}

---

**输出要求（必须严格遵守）**：
1. 输出**仅**包含从第一个 `## 项目概述` 开始到 `## 总结` 结束的正文，**不要**输出一级标题 `#`、不要输出代码围栏外的解释性开场白。
2. 必须**按顺序**包含以下 15 个二级标题，**标题文字一字不差**（含空格与标点）：

{sections_list}

3. 每个二级标题下用 Markdown 列表或短段落；单节不宜过长。无依据则写「（素材中未体现）」。
4. 语言：中文为主；专有名词、命令、路径可保留英文原文。
"""


def _validate_jvs_sections(body: str) -> bool:
    if not body or len(body) < 200:
        return False
    for h in _JVS_REQUIRED_SECTIONS:
        inner = h[3:].strip()
        if not re.search(rf"(?m)^##\s*{re.escape(inner)}\s*$", body):
            return False
    return True


def _inject_tools_into_references_section(llm_body: str) -> str:
    tools = _get_tools_overview()
    marker = "## 参考资源"
    if marker not in llm_body:
        return llm_body.rstrip() + "\n\n" + marker + "\n\n" + tools + "\n"
    pos = llm_body.find(marker) + len(marker)
    rest = llm_body[pos:]
    m = re.search(r"(?m)^##\s*总结\s*$", rest)
    if m:
        cut = pos + m.start()
        return llm_body[:cut] + "\n\n" + tools + "\n" + llm_body[cut:].lstrip("\n")
    return llm_body.rstrip() + "\n\n" + tools + "\n"


def _strip_outer_markdown_fence(s: str) -> str:
    t = s.strip()
    if not t.startswith("```"):
        return t
    lines = t.split("\n")
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _jvs_file_header(
    project_root: str,
    rules_fp: str,
    first_init: bool,
    llm_ok: bool,
    llm_tier: Optional[str] = None,
) -> str:
    if llm_ok:
        mode = (
            "首次 Init（快速目录索引 + 可选 AGENTS/CLAUDE/GEMINI）"
            if first_init
            else "再次 Init（全量目录与文件抽检）"
        )
        if llm_tier == "normal":
            src = "正文由 **normal** LLM 生成（cheap 不可用或无合规输出后已切换）。"
        else:
            src = "正文由 **cheap** LLM 依据素材生成。"
    else:
        mode = "程序化摘要（非 Init 主路径）"
        src = "启发式拼装，通常仅供调试或未接 LLM 时使用。"
    return "\n".join(
        [
            "# JVS_MEMORY.md",
            "",
            "> **生成位置**: 当前工作目录下的 `JVS_MEMORY.md`（与执行 Init 时的 `cwd` 一致）。",
            "> **触发方式**: 仅内置命令 **Init**（`'<Init>'`）生成或覆盖；会话启动**不会**自动创建。",
            f"> **本次模式**: {mode}。{src}",
            "",
            f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **目录根**: `{project_root}`",
            f"- **规则索引指纹**: {rules_fp or '(unknown)'}",
            "",
            "---",
            "",
        ]
    )


def _dim_project_overview(project_root: str) -> str:
    lines: List[str] = []
    name = os.path.basename(os.path.normpath(project_root)) or "."
    lines.append(f"- **工程目录名**: `{name}`")
    rc, out = _run_git(project_root, ["remote", "-v"])
    if rc == 0 and out:
        first = out.splitlines()[0].strip()
        if first:
            lines.append(f"- **Git remote（首条）**: `{first}`")
    rc, branch = _run_git(project_root, ["rev-parse", "--abbrev-ref", "HEAD"])
    if rc == 0 and branch:
        lines.append(f"- **当前分支**: `{branch}`")
    try:
        from jarvis.jarvis_utils.utils import get_loc_stats

        loc = get_loc_stats()
        if loc and str(loc).strip():
            lines.append("")
            lines.append("**代码规模（粗略）**:")
            lines.append("")
            lines.append("```")
            lines.append(str(loc).strip())
            lines.append("```")
    except Exception:
        pass
    readme = _read_text_file_safely(os.path.join(project_root, "README.md"), 8000)
    if readme.strip():
        intro_lines: List[str] = []
        for raw in readme.splitlines()[:35]:
            s = raw.strip()
            if not s or s.startswith("#"):
                continue
            if s.startswith("!") or s.startswith("[!["):
                continue
            intro_lines.append(raw.rstrip())
            if len(intro_lines) >= 12:
                break
        if intro_lines:
            lines.append("")
            lines.append("**README 摘录（非标题行，供快速了解用途）**:")
            lines.append("")
            lines.append("> " + "\n> ".join(intro_lines[:12]))
    if len(lines) == 1:
        lines.append(
            "- （未能读取更多元信息：可补充 README、或确保在 Git 仓库根目录执行 Init）"
        )
    return "\n".join(lines)


def _dim_project_structure(project_root: str) -> str:
    try:
        from jarvis.jarvis_code_agent.utils import get_git_tracked_files_info

        info = get_git_tracked_files_info(project_root)
        if info and info.strip():
            return info.strip()
    except Exception:
        pass
    return "（未能获取 Git 跟踪文件列表：请确认当前目录为 Git 仓库根目录。）"


def _dim_core_components(project_root: str) -> str:
    """按 git ls-files 一级目录聚合文件数，推断模块/包分布。"""
    rc, out = _run_git(project_root, ["ls-files"])
    if rc != 0 or not out:
        return "（无 `git ls-files` 结果。）"
    files = [ln.strip() for ln in out.splitlines() if ln.strip()]
    if not files:
        return "（仓库中暂无已跟踪文件。）"
    counts: dict[str, int] = {}
    for f in files:
        top = f.split("/", 1)[0]
        counts[top] = counts.get(top, 0) + 1
    ranked = sorted(counts.items(), key=lambda x: (-x[1], x[0]))[:40]
    body = "\n".join(f"- `{k}/` — {v} 个已跟踪文件" for k, v in ranked)
    if len(counts) > 40:
        body += f"\n- … 另有 {len(counts) - 40} 个顶层项未列出"
    return body


def _parse_ini_like_scripts_pyproject(text: str) -> List[str]:
    """轻量解析 [project.scripts] / [tool.poetry.scripts] 块，不依赖 tomllib。"""
    lines_out: List[str] = []
    in_scripts = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            norm = s.replace(" ", "").lower()
            in_scripts = norm in ("[project.scripts]", "[tool.poetry.scripts]")
            continue
        if in_scripts and "=" in s and not s.startswith("#"):
            key = s.split("=", 1)[0].strip()
            if key and re.match(r"^[A-Za-z0-9_.-]+$", key):
                lines_out.append(f"- `{key}`")
    return lines_out[:30]


def _dim_main_commands(project_root: str) -> str:
    parts: List[str] = []
    pp = os.path.join(project_root, "pyproject.toml")
    if os.path.isfile(pp):
        t = _read_text_file_safely(pp, 120_000)
        scripts = _parse_ini_like_scripts_pyproject(t)
        if scripts:
            parts.append("**pyproject.toml [project.scripts]（节选）**:")
            parts.extend(scripts)
    pkg = os.path.join(project_root, "package.json")
    if os.path.isfile(pkg):
        try:
            with open(pkg, encoding="utf-8", errors="replace") as f:
                data = json.load(f)
            scr = data.get("scripts")
            if isinstance(scr, dict) and scr:
                parts.append("")
                parts.append("**package.json scripts（节选）**:")
                for k in sorted(scr.keys())[:25]:
                    parts.append(f"- `{k}`")
        except Exception:
            pass
    makefile = os.path.join(project_root, "Makefile")
    if os.path.isfile(makefile):
        mf = _read_text_file_safely(makefile, 30_000)
        targets: List[str] = []
        for line in mf.splitlines():
            m = re.match(r"^([A-Za-z0-9_.-]+)\s*:", line)
            if m and not line.startswith(".") and m.group(1) not in (
                "PHONY",
                "SHELL",
            ):
                targets.append(m.group(1))
        uniq = []
        for t in targets:
            if t not in uniq:
                uniq.append(t)
            if len(uniq) >= 20:
                break
        if uniq:
            parts.append("")
            parts.append("**Makefile 目标（节选）**:")
            parts.extend(f"- `{x}`" for x in uniq)
    if not parts:
        return "（未发现 pyproject scripts / package.json scripts / Makefile 目标；可查看 README 或仓库文档。）"
    return "\n".join(parts)


def _dim_build_and_run(project_root: str) -> str:
    markers = [
        ("pyproject.toml", "Python 打包/元数据（PEP 621）"),
        ("setup.py", "传统 setuptools 安装"),
        ("setup.cfg", "setuptools 配置"),
        ("requirements.txt", "pip 依赖列表"),
        ("Pipfile", "pipenv"),
        ("poetry.lock", "Poetry"),
        ("Cargo.toml", "Rust / cargo"),
        ("go.mod", "Go modules"),
        ("pom.xml", "Maven"),
        ("build.gradle", "Gradle"),
        ("Dockerfile", "容器构建"),
        ("docker-compose.yml", "Compose"),
        ("docker-compose.yaml", "Compose"),
        ("Makefile", "Make 构建"),
        ("CMakeLists.txt", "CMake"),
        ("meson.build", "Meson"),
        ("package.json", "Node/npm"),
    ]
    found: List[str] = []
    for fname, desc in markers:
        if os.path.isfile(os.path.join(project_root, fname)):
            found.append(f"- `{fname}` — {desc}")
    if not found:
        return "（根目录未检测到常见构建描述文件。）"
    return "\n".join(found)


def _dim_configuration(project_root: str) -> str:
    names = [
        ".env.example",
        ".env.sample",
        "config.yaml",
        "config.yml",
        "settings.py",
        "pytest.ini",
        "tox.ini",
        "ruff.toml",
        ".ruff.toml",
        "mypy.ini",
        ".flake8",
        "pyrightconfig.json",
        "tsconfig.json",
        "vite.config.ts",
        "next.config.js",
        "mkdocs.yml",
        "application.yml",
        "application.yaml",
    ]
    found: List[str] = []
    for n in names:
        if os.path.isfile(os.path.join(project_root, n)):
            found.append(f"- `{n}`")
    try:
        for entry in sorted(os.listdir(project_root))[:200]:
            if entry.startswith(".jarvis") or entry.startswith(".cursor"):
                p = os.path.join(project_root, entry)
                if os.path.isfile(p) and entry.endswith((".yaml", ".yml", ".json")):
                    found.append(f"- `{entry}`")
    except Exception:
        pass
    if not found:
        return "（未发现常见配置文件名；实际配置可能在子目录。）"
    return "\n".join(found[:45])


def _dim_dev_conventions(project_root: str) -> str:
    items: List[str] = []
    checks = [
        (".pre-commit-config.yaml", "pre-commit"),
        ("ruff.toml", "Ruff"),
        (".ruff.toml", "Ruff"),
        ("pyproject.toml", "可能含 ruff/black/isort 等（见文件内 [tool.*]）"),
        (".editorconfig", "EditorConfig"),
        ("CONTRIBUTING.md", "贡献指南"),
        ("CODE_OF_CONDUCT.md", "行为准则"),
        (".github/workflows", "GitHub Actions（目录）"),
    ]
    for rel, desc in checks:
        p = os.path.join(project_root, rel)
        if os.path.exists(p):
            items.append(f"- `{rel}` — {desc}")
    if not items:
        return "（未发现典型约定文件；以团队文档为准。）"
    return "\n".join(items)


def _dim_core_concepts(project_root: str) -> str:
    """根据依赖文件名/片段猜测技术栈关键词，非读取 AGENTS。"""
    hints: List[str] = []
    blob = ""
    for fn in ("pyproject.toml", "requirements.txt", "package.json"):
        blob += _read_text_file_safely(os.path.join(project_root, fn), 50_000).lower()
    keywords = [
        ("django", "Django Web"),
        ("fastapi", "FastAPI"),
        ("flask", "Flask"),
        ("pytest", "pytest 测试"),
        ("sqlalchemy", "SQLAlchemy"),
        ("pydantic", "Pydantic"),
        ("react", "React"),
        ("vue", "Vue"),
        ("next", "Next.js"),
        ("express", "Express"),
        ("playwright", "Playwright"),
    ]
    for kw, label in keywords:
        if kw in blob:
            hints.append(f"- 依赖/配置中出现 **{label}** 相关线索（`{kw}`）")
    if not hints:
        return (
            "- 本摘要由仓库文件自动推断；具体领域模型、工作流命名等请结合源码与 README。\n"
            "- 若使用 Jarvis Agent，可参考内置 ARCHER（分析→规则→收集→假设→执行→回顾）流程理解任务阶段。"
        )
    return "\n".join(hints[:15])


def _dim_dependencies(project_root: str) -> str:
    lines: List[str] = []
    req = os.path.join(project_root, "requirements.txt")
    if os.path.isfile(req):
        body = _read_text_file_safely(req, 20_000)
        for ln in body.splitlines()[:45]:
            s = ln.strip()
            if s and not s.startswith("#"):
                lines.append(f"- {s}")
        if lines:
            return "**requirements.txt（节选）**:\n\n" + "\n".join(lines)
    pp = os.path.join(project_root, "pyproject.toml")
    if os.path.isfile(pp):
        t = _read_text_file_safely(pp, 120_000)
        m = re.search(
            r"dependencies\s*=\s*\[([\s\S]*?)\]", t, re.IGNORECASE
        )
        if m:
            block = m.group(1)
            deps = re.findall(r"\"([^\"]+)\"|'([^']+)'", block)
            flat = [a or b for a, b in deps][:40]
            if flat:
                return "**pyproject 依赖字符串（节选）**:\n\n" + "\n".join(
                    f"- `{x}`" for x in flat
                )
    pkg = os.path.join(project_root, "package.json")
    if os.path.isfile(pkg):
        try:
            with open(pkg, encoding="utf-8", errors="replace") as f:
                data = json.load(f)
            dep = data.get("dependencies")
            if isinstance(dep, dict):
                keys = sorted(dep.keys())[:40]
                return "**package.json dependencies（节选）**:\n\n" + "\n".join(
                    f"- `{k}`" for k in keys
                )
        except Exception:
            pass
    return "（未发现 requirements.txt / pyproject 依赖表 / package.json dependencies。）"


def _dim_whats_new(project_root: str) -> str:
    for name in (
        "CHANGELOG.md",
        "CHANGES.md",
        "HISTORY.md",
        "NEWS.md",
        "CHANGELOG",
    ):
        p = os.path.join(project_root, name)
        if os.path.isfile(p):
            body = _read_text_file_safely(p, 12_000)
            lines = body.splitlines()[:50]
            return "\n".join(lines)
    rc, out = _run_git(project_root, ["log", "-8", "--oneline", "--no-decorate"])
    if rc == 0 and out:
        return "**最近提交（git log -8 --oneline）**:\n\n" + "\n".join(
            f"- {ln}" for ln in out.splitlines()
        )
    return "（无 CHANGELOG 类文件且无法读取 git log。）"


def _dim_architecture_evolution(project_root: str) -> str:
    rc, out = _run_git(
        project_root,
        ["log", "-15", "--pretty=format:%h %ad %s", "--date=short"],
    )
    if rc == 0 and out:
        return "\n".join(f"- {ln}" for ln in out.splitlines())
    return "（无法读取 git 历史。）"


def _extract_readme_section(readme: str, heading_keywords: Tuple[str, ...]) -> str:
    if not readme.strip():
        return ""
    best_idx = -1
    for kw in heading_keywords:
        try:
            m = re.search(rf"(?mi)^##\s*{re.escape(kw)}\s*$", readme)
        except re.error:
            continue
        if m and (best_idx < 0 or m.start() < best_idx):
            best_idx = m.start()
    if best_idx < 0:
        return ""
    chunk = readme[best_idx:]
    for marker in ("\n## ", "\r\n## "):
        k = chunk.find(marker, 3)
        if k > 0:
            chunk = chunk[:k]
    return chunk.strip()[:6000]


def _dim_common_scenarios(project_root: str) -> str:
    readme = _read_text_file_safely(os.path.join(project_root, "README.md"), 80_000)
    for kws in (
        ("用法", "使用", "快速开始", "Getting Started", "Usage", "Quick start"),
        ("安装", "Install", "Installation"),
    ):
        sec = _extract_readme_section(readme, kws)
        if sec:
            return sec
    return "（README 中未匹配到常见「使用/安装」二级标题；请直接阅读 README.md。）"


def _dim_notes(project_root: str) -> str:
    items: List[str] = []
    if os.path.isfile(os.path.join(project_root, "LICENSE")):
        items.append("- 仓库含 `LICENSE`，使用或分发前请遵守许可证条款。")
    if os.path.isfile(os.path.join(project_root, "SECURITY.md")):
        items.append("- 含 `SECURITY.md`，安全披露请按该文件指引。")
    if os.path.isfile(os.path.join(project_root, ".gitignore")):
        items.append("- 已存在 `.gitignore`；注意勿将密钥、本地大文件提交入库。")
    items.append("- 本文件为机器梳理摘要，**不能**替代安全审计与合规审查。")
    return "\n".join(items)


def _dim_references(project_root: str) -> str:
    lines: List[str] = []
    readme = _read_text_file_safely(os.path.join(project_root, "README.md"), 100_000)
    urls = re.findall(r"https?://[^\s)>\]]+", readme)
    seen = set()
    for u in urls:
        if u not in seen and len(seen) < 25:
            seen.add(u)
            lines.append(f"- {u}")
    if lines:
        body = "**README 中出现的链接（节选）**:\n\n" + "\n".join(lines)
    else:
        body = "- （README 中未解析到 http(s) 链接。）"
    body += "\n\n" + _get_tools_overview()
    return body


def _dim_summary(project_root: str) -> str:
    bullets: List[str] = []
    name = os.path.basename(os.path.normpath(project_root))
    bullets.append(f"- 工程目录: `{name}`")
    rc, out = _run_git(project_root, ["ls-files"])
    nfiles = len([x for x in out.splitlines() if x.strip()]) if rc == 0 else 0
    if nfiles:
        bullets.append(f"- Git 已跟踪文件约 **{nfiles}** 个")
    if os.path.isdir(os.path.join(project_root, "tests")) or os.path.isdir(
        os.path.join(project_root, "test")
    ):
        bullets.append("- 检测到 `tests/` 或 `test/` 目录，可能含自动化测试")
    bullets.append("- 更细粒度说明见上文各维度；**完整信息以源码与官方文档为准**。")
    bullets.append(
        "- 更新本摘要：在 Jarvis 主会话中执行内置命令 **Init**（`'<Init>'`）。"
    )
    return "\n".join(bullets)


def _build_jvs_memory_programmatic(
    project_root: str, rules_fp: str, first_init: bool
) -> str:
    """无 LLM 时的启发式 15 维拼装（Init 主线不再调用，仅保留供调试等场景）。"""
    header = _jvs_file_header(project_root, rules_fp, first_init, llm_ok=False)
    sections = [
        ("## 项目概述", _dim_project_overview(project_root)),
        ("## 项目结构", _dim_project_structure(project_root)),
        ("## 核心组件", _dim_core_components(project_root)),
        ("## 主要命令", _dim_main_commands(project_root)),
        ("## 构建和运行", _dim_build_and_run(project_root)),
        ("## 配置说明", _dim_configuration(project_root)),
        ("## 开发约定", _dim_dev_conventions(project_root)),
        ("## 核心概念", _dim_core_concepts(project_root)),
        ("## 依赖关系", _dim_dependencies(project_root)),
        ("## 新增功能", _dim_whats_new(project_root)),
        ("## 架构演变", _dim_architecture_evolution(project_root)),
        ("## 常见使用场景", _dim_common_scenarios(project_root)),
        ("## 注意事项", _dim_notes(project_root)),
        ("## 参考资源", _dim_references(project_root)),
        ("## 总结", _dim_summary(project_root)),
    ]
    body = "\n\n".join(f"{title}\n\n{content.strip()}" for title, content in sections)
    return (header + body).strip() + "\n"


def build_jvs_memory(project_root: Optional[str] = None) -> str:
    """由 Init 调用：**默认 cheap LLM**，失败则 **normal LLM**；两者均失败则抛出 ``RuntimeError``。

    - **首次**（当前目录尚无 ``JVS_MEMORY.md``）：快速目录索引 + 可选治理文档摘录。
    - **再次**：全量目录与文本抽检素材，不读取治理文档。
    - ``project_root`` 默认当前工作目录（与 Init 的 cwd 一致）。
    """
    project_root = os.path.abspath(project_root or os.getcwd())
    rules_fp = _get_rules_fingerprint(project_root)
    jvs_path = get_jvs_memory_path(project_root)
    first_init = not os.path.isfile(jvs_path)

    if first_init:
        inventory = _collect_inventory_quick(project_root)
        governance = _read_governance_for_first_init(project_root)
    else:
        inventory = _collect_inventory_full(project_root)
        governance = ""

    _max_llm_material = 100_000
    if len(inventory) > _max_llm_material:
        inventory = (
            inventory[:_max_llm_material]
            + "\n\n…【索引素材已截断以适配 LLM 上下文】\n"
        )

    prompt = _jvs_llm_prompt(first_init, governance, inventory)
    body, tier = _generate_jvs_body_via_llm(prompt)
    body = _inject_tools_into_references_section(body)
    header = _jvs_file_header(
        project_root, rules_fp, first_init, llm_ok=True, llm_tier=tier
    )
    return (header + body).strip() + "\n"


def ensure_jvs_memory(project_root: str) -> Tuple[bool, str]:
    """兼容保留：不再自动写入 JVS_MEMORY.md（仅 Init 会生成/更新）。

    返回 (False, path) 表示未写入；调用方应改用 Init + build_jvs_memory + write_jvs_memory。
    """
    return False, get_jvs_memory_path(project_root)
