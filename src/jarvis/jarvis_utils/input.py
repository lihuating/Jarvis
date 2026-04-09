"""
输入处理模块
该模块提供了处理Jarvis系统中用户输入的实用工具。
包含：
- 支持历史记录的单行输入
- 增强补全功能的多行输入
- 带有模糊匹配的文件路径补全
- 用于输入控制的自定义键绑定
"""

import base64
import os
import sys

from jarvis.jarvis_utils.output import PrettyOutput

# -*- coding: utf-8 -*-
from typing import Iterable
from typing import List
from typing import Any
from typing import Optional
from typing import Tuple

import wcwidth
from colorama import Fore
from colorama import Style as ColoramaStyle
from fuzzywuzzy import process
from prompt_toolkit import PromptSession
from prompt_toolkit.application import Application
from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.completion import Completer
from prompt_toolkit.completion import Completion
from prompt_toolkit.completion import PathCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.filters import has_focus
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style as PromptStyle

from jarvis.jarvis_utils.clipboard import copy_to_clipboard
from jarvis.jarvis_utils.config import get_data_dir
from jarvis.jarvis_utils.config import get_normal_model_name
from jarvis.jarvis_utils.config import get_replace_map
from jarvis.jarvis_utils.config import get_smart_model_name
from jarvis.jarvis_utils.config import get_conversation_turn_threshold
from jarvis.jarvis_utils.globals import get_message_history
from jarvis.jarvis_utils.globals import get_current_agent
from jarvis.jarvis_utils.tag import ot
from jarvis.jarvis_utils.utils import decode_output

# 在文件顶部导入需要在函数内部使用的模块
# (使用别名避免与内置模块冲突)
import os as _os
import subprocess as _subprocess
import shutil as _shutil

# Git root cache (used for @ completion)
_GIT_ROOT_CACHE: Optional[str] = None
_COMPLETION_ROOT_CACHE: Optional[str] = None
_CACHE_CWD: Optional[str] = None


def _get_completion_root() -> str:
    """获取用于文件补全的项目根目录。

    优先级：
    1) 环境变量 JARVIS_PROJECT_ROOT
    2) 当前 Agent 的 root_dir（如果可用）
    3) git 仓库根目录（git rev-parse --show-toplevel）
    4) 当前工作目录
    """
    global _COMPLETION_ROOT_CACHE
    global _GIT_ROOT_CACHE
    global _CACHE_CWD

    # 当用户在不同工程目录之间切换时，自动失效缓存，避免补全一直指向旧工程
    try:
        cwd = os.getcwd()
    except Exception:
        cwd = None
    if cwd and _CACHE_CWD and cwd != _CACHE_CWD:
        _COMPLETION_ROOT_CACHE = None
        _GIT_ROOT_CACHE = None
    if cwd and _CACHE_CWD != cwd:
        _CACHE_CWD = cwd

    if _COMPLETION_ROOT_CACHE:
        return _COMPLETION_ROOT_CACHE

    try:
        env_root = os.environ.get("JARVIS_PROJECT_ROOT", "").strip()
        if env_root and os.path.isdir(env_root):
            _COMPLETION_ROOT_CACHE = env_root
            return env_root
    except Exception:
        pass

    try:
        agent = get_current_agent()
        root_dir = getattr(agent, "root_dir", None) if agent else None
        if isinstance(root_dir, str) and root_dir and os.path.isdir(root_dir):
            _COMPLETION_ROOT_CACHE = root_dir
            return root_dir
    except Exception:
        pass

    try:
        rr = _subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            stdout=_subprocess.PIPE,
            stderr=_subprocess.PIPE,
            text=True,
        )
        if rr.returncode == 0:
            p = rr.stdout.strip()
            if p and os.path.isdir(p):
                _COMPLETION_ROOT_CACHE = p
                return p
    except Exception:
        pass

    _COMPLETION_ROOT_CACHE = os.getcwd()
    return _COMPLETION_ROOT_CACHE

# Sentinel value to indicate that Ctrl+O was pressed
CTRL_O_SENTINEL = "__CTRL_O_PRESSED__"
# Sentinel value to indicate that Ctrl+X was pressed (exit program)
CTRL_X_SENTINEL = "__CTRL_X_PRESSED__"
# Sentinel prefix to indicate that Ctrl+F (fzf) inserted content should prefill next prompt
FZF_INSERT_SENTINEL_PREFIX = "__FZF_INSERT__::"
# Sentinel to request running fzf outside the prompt and then prefill next prompt
FZF_REQUEST_SENTINEL_PREFIX = "__FZF_REQUEST__::"
# Sentinel to request running fzf outside the prompt for all-files mode (exclude .git)
FZF_REQUEST_ALL_SENTINEL_PREFIX = "__FZF_REQUEST_ALL__::"

# Persistent hint marker for multiline input (shown only once across runs)
_MULTILINE_HINT_MARK_FILE = os.path.join(get_data_dir(), "multiline_enter_hint_shown")

# 内置命令标记列表（用于自动补全和 fzf）
BUILTIN_COMMANDS = [
    ("Summary", "总结"),
    ("Pin", "固定/置顶内容"),
    ("Clear", "清除历史"),
    ("Exit", "退出 Jarvis"),
    ("Commit", "提交代码"),
    ("ToolUsage", "工具使用说明"),
    ("ReloadConfig", "重新加载配置"),
    ("SaveSession", "保存当前会话"),
    ("RestoreSession", "恢复会话"),
    ("ListSessions", "列出所有会话"),
    ("ListRule", "列出所有规则"),
    ("Quiet", "无人值守模式"),
    ("FixToolCall", "修复工具调用"),
    ("SwitchModel", "切换模型组"),
    (
        "Init",
        "在当前目录生成/更新 JVS_MEMORY.md（优先 cheap LLM，失败则 normal；均失败则报错）",
    ),
]


def _display_width(s: str) -> int:
    """计算字符串在终端中的可打印宽度(处理宽字符)。"""
    try:
        w = 0
        for ch in s:
            cw = wcwidth.wcwidth(ch)
            if cw is None or cw < 0:
                # Fallback for unknown width chars (e.g. emoji on some terminals)
                cw = 1
            w += cw
        return w
    except Exception:
        return len(s)


def _calc_prompt_rows(prev_text: str) -> int:
    """
    估算上一个提示占用了多少终端行数。
    考虑提示前缀和跨终端列的软换行。
    """
    try:
        cols = os.get_terminal_size().columns
    except Exception:
        cols = 80
    
    # 获取模型名称以计算正确的提示符宽度
    def _get_model_name_hint() -> str:
        try:
            current_agent = get_current_agent()
            if current_agent and hasattr(current_agent, "model"):
                model = current_agent.model
                if model and getattr(model, "model_name", None):
                    # 提示头只显示模型名，避免显示 `|normal`/`|smart` 档位后缀
                    return f"[{model.model_name}]"
        except Exception:
            pass
        return ""
    
    model_hint = _get_model_name_hint()
    prefix = f"👤{model_hint} > "
    prefix_w = _display_width(prefix)

    lines = prev_text.splitlines()
    if not lines:
        lines = [""]
    # If the text ends with a newline, there is a visible empty line at the end.
    if prev_text.endswith("\n"):
        lines.append("")
    total_rows = 0
    for i, line in enumerate(lines):
        lw = _display_width(line)
        if i == 0:
            width = prefix_w + lw
        else:
            width = lw
        rows = max(1, (width + cols - 1) // cols)
        total_rows += rows
    return max(1, total_rows)


def _get_git_files() -> List[str]:
    """获取Git仓库中的文件列表。"""
    files = []
    try:
        global _GIT_ROOT_CACHE
        # 与补全根目录保持一致：切换目录时缓存会在 _get_completion_root 中被失效
        if _GIT_ROOT_CACHE is None:
            rr = _subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                stdout=_subprocess.PIPE,
                stderr=_subprocess.PIPE,
                text=True,
            )
            _GIT_ROOT_CACHE = rr.stdout.strip() if rr.returncode == 0 else ""
        # 首选补全根目录下的 git 根（更符合用户“项目文件”预期）
        completion_root = _get_completion_root()
        git_root = _GIT_ROOT_CACHE or completion_root
        r = _subprocess.run(
            ["git", "ls-files"],
            stdout=_subprocess.PIPE,
            stderr=_subprocess.PIPE,
            text=False,
            cwd=git_root,
        )
        if r.returncode == 0:
            files = [
                line for line in decode_output(r.stdout).splitlines() if line.strip()
            ]
    except Exception:
        files = []
    return files


def _get_all_files(exclude_git: bool = False) -> List[str]:
    """获取所有文件列表。

    Args:
        exclude_git: 是否排除.git目录
    """
    files = []
    try:
        import os as _os
        global _GIT_ROOT_CACHE
        base_dir = _get_completion_root()

        for root, dirs, fnames in _os.walk(base_dir, followlinks=False):
            if exclude_git:
                # Exclude .git directories
                dirs[:] = [d for d in dirs if d != ".git"]
            for name in fnames:
                files.append(_os.path.relpath(_os.path.join(root, name), base_dir))
            if len(files) > 10000:
                break
    except Exception:
        files = []
    return files


def _get_files_for_fzf(use_git: bool = True) -> List[str]:
    """为FZF获取文件列表。

    Args:
        use_git: 是否优先使用git文件列表（失败则fallback到os.walk）
    """
    if use_git:
        files = _get_git_files()
        if files:
            return files
    return _get_all_files(exclude_git=True)


def _parse_fzf_payload(
    user_input: str, prefix: str
) -> Tuple[Optional[int], Optional[str]]:
    """解析FZF请求payload。

    Args:
        user_input: 用户输入，包含FZF前缀和payload
        prefix: FZF前缀（如FZF_REQUEST_SENTINEL_PREFIX）

    Returns:
        (cursor, text) 元组，解析失败时返回 (None, None)
    """
    try:
        payload = user_input[len(prefix) :]
        sep_index = payload.find(":")
        cursor = int(payload[:sep_index])
        text = base64.b64decode(payload[sep_index + 1 :].encode("ascii")).decode(
            "utf-8"
        )
        return cursor, text
    except Exception:
        return None, None


def _run_fzf_for_selection(files: List[str], prompt_text: str) -> Optional[str]:
    """运行FZF获取用户选择。

    Args:
        files: 文件列表
        prompt_text: FZF提示文本

    Returns:
        选中的文件路径，取消或错误时返回None
    """
    if _shutil.which("fzf") is None:
        PrettyOutput.auto_print("⚠️ 未检测到 fzf，无法打开文件选择器。")
        return None

    if not files:
        PrettyOutput.auto_print("ℹ️ 未找到可选择的文件。")
        return None

    # _get_fzf_completion_items会自动添加完整的BUILTIN_COMMANDS
    # 因此这里传入空列表，避免重复
    specials: List[str] = []
    items = _get_fzf_completion_items(specials, files)
    proc = _subprocess.run(
        [
            "fzf",
            "--prompt",
            prompt_text,
            "--height",
            "40%",
            "--border",
        ],
        input="\n".join(items),
        stdout=_subprocess.PIPE,
        stderr=_subprocess.PIPE,
        text=True,
    )
    sel = proc.stdout.strip()
    return sel if sel else None


def _insert_file_path(
    text: str, cursor: int, path: str, symbol: str
) -> Tuple[str, int]:
    """插入文件路径到文本中。

    Args:
        text: 原始文本
        cursor: 光标位置
        path: 要插入的文件路径
        symbol: 触发符号（'@' 或 '#'）

    Returns:
        (new_text, new_cursor) 元组
    """
    text_before = text[:cursor]
    last_symbol = text_before.rfind(symbol)
    if last_symbol != -1 and " " not in text_before[last_symbol + 1 :]:
        # Replace @... or #... segment
        inserted = f"'{path}'"
        new_text = text[:last_symbol] + inserted + text[cursor:]
        new_cursor = last_symbol + len(inserted)
    else:
        # Plain insert
        inserted = f"'{path}'"
        new_text = text[:cursor] + inserted + text[cursor:]
        new_cursor = cursor + len(inserted)
    return new_text, new_cursor


def _clear_previous_prompt(text: str) -> None:
    """清除上一条输入行。

    Args:
        text: 上一次的输入文本
    """
    try:
        rows_total = _calc_prompt_rows(text)
        for _ in range(rows_total):
            sys.stdout.write("\x1b[1A")  # 光标上移一行
            sys.stdout.write("\x1b[2K\r")  # 清除整行
        sys.stdout.flush()
    except Exception:
        pass


def _multiline_hint_already_shown() -> bool:
    """检查是否已显示过多行输入提示(持久化存储)。"""
    try:
        return os.path.exists(_MULTILINE_HINT_MARK_FILE)
    except Exception:
        return False


def _mark_multiline_hint_shown() -> None:
    """持久化存储多行输入提示已显示的状态。"""
    try:
        os.makedirs(os.path.dirname(_MULTILINE_HINT_MARK_FILE), exist_ok=True)
        with open(_MULTILINE_HINT_MARK_FILE, "w", encoding="utf-8") as f:
            f.write("1")
    except Exception:
        # Non-critical persistence failure; ignore to avoid breaking input flow
        pass


def get_single_line_input(tip: str, default: str = "") -> str:
    """
    获取支持历史记录的单行输入。
    """
    # 获取当前模型名称用于提示符
    def _get_model_name_hint() -> str:
        try:
            current_agent = get_current_agent()
            if current_agent and hasattr(current_agent, "model"):
                model = current_agent.model
                if model and getattr(model, "model_name", None):
                    # 提示头只显示模型名，避免显示 `|normal`/`|smart` 档位后缀
                    return f"[{model.model_name}]"
        except Exception:
            pass
        return ""
    
    model_hint = _get_model_name_hint()
    
    session: PromptSession[Any] = PromptSession(history=None)
    style = PromptStyle.from_dict(
        {"prompt": "ansicyan", "bottom-toolbar": "fg:#888888"}
    )
    prompt = FormattedText([("class:prompt", f"👤{model_hint} > {tip}")])
    return str(session.prompt(prompt, default=default, style=style))


def run_truncated_history_viewer() -> None:
    """进入历史隐藏查看界面：展示索引与摘要列表，输入序号并回车查看对应完整内容。

    在 run_in_terminal 中执行，故使用内置 input() 读取序号，避免嵌套 asyncio 事件循环。
    """
    from rich.console import Console
    from rich.table import Table

    history = PrettyOutput.get_truncated_history()
    if not history:
        PrettyOutput.auto_print("ℹ️ 当前无历史隐藏内容")
        return
    console = Console()
    table = Table(
        title="📋 历史隐藏查看",
        show_header=True,
        header_style="bold magenta",
        title_style="bold cyan",
    )
    table.add_column("索引", style="cyan", width=6)
    table.add_column("隐藏摘要", style="yellow")
    for i, (_content, summary) in enumerate(history, 1):
        row_summary = (
            (summary[:80] + "…") if len(summary) > 80 else summary
        )
        table.add_row(str(i), row_summary)
    console.print(table)
    try:
        line = input("请输入序号 (直接回车退出): ").strip()
    except (EOFError, KeyboardInterrupt):
        line = ""
    if not line:
        return
    try:
        idx = int(line.strip())
        if not PrettyOutput.show_truncated_item_by_index(idx):
            PrettyOutput.auto_print("⚠️ 无效序号")
    except ValueError:
        PrettyOutput.auto_print("⚠️ 请输入有效数字")


def get_choice(tip: str, choices: List[str]) -> str:
    """
    提供一个可滚动的选择列表供用户选择。
    """
    if not choices:
        raise ValueError("Choices cannot be empty.")

    try:
        terminal_height = os.get_terminal_size().lines
    except OSError:
        terminal_height = 25  # 如果无法确定终端大小，则使用默认高度

    # 为提示和缓冲区保留行
    max_visible_choices = max(5, terminal_height - 4)

    bindings = KeyBindings()
    selected_index = 0
    start_index = 0

    @bindings.add("up")
    def _(event: KeyPressEvent) -> None:
        nonlocal selected_index, start_index
        selected_index = (selected_index - 1 + len(choices)) % len(choices)
        if selected_index < start_index:
            start_index = selected_index
        elif selected_index == len(choices) - 1:  # 支持从第一项上翻到最后一项时滚动
            start_index = max(0, len(choices) - max_visible_choices)
        event.app.invalidate()

    @bindings.add("down")
    def _(event: KeyPressEvent) -> None:
        nonlocal selected_index, start_index
        selected_index = (selected_index + 1) % len(choices)
        if selected_index >= start_index + max_visible_choices:
            start_index = selected_index - max_visible_choices + 1
        elif selected_index == 0:  # 支持从最后一项下翻到第一项时滚动
            start_index = 0
        event.app.invalidate()

    @bindings.add("enter")
    def _(event: KeyPressEvent) -> None:
        event.app.exit(result=choices[selected_index])

    def get_prompt_tokens() -> FormattedText:
        tokens = [("class:question", f"{tip} (使用上下箭头选择, Enter确认)\n")]

        end_index = min(start_index + max_visible_choices, len(choices))
        visible_choices_slice = choices[start_index:end_index]

        if start_index > 0:
            tokens.append(("class:indicator", "  ... (更多选项在上方) ...\n"))

        for i, choice in enumerate(visible_choices_slice, start=start_index):
            if i == selected_index:
                tokens.append(("class:selected", f"> {choice}\n"))
            else:
                tokens.append(("", f"  {choice}\n"))

        if end_index < len(choices):
            tokens.append(("class:indicator", "  ... (更多选项在下方) ...\n"))

        return FormattedText(tokens)

    style = PromptStyle.from_dict(
        {
            "question": "bold",
            "selected": "bg:#696969 #ffffff",
            "indicator": "fg:gray",
        }
    )

    layout = Layout(
        container=Window(
            content=FormattedTextControl(
                text=get_prompt_tokens,
                focusable=True,
                key_bindings=bindings,
            )
        )
    )

    app: Application[Any] = Application(
        layout=layout,
        key_bindings=bindings,
        style=style,
        mouse_support=True,
        full_screen=True,
    )

    try:
        result = app.run()
        return result if result is not None else ""
    except (KeyboardInterrupt, EOFError):
        return ""


class FileCompleter(Completer):
    """
    带有模糊匹配的文件路径自定义补全器。
    """

    def __init__(self) -> None:
        self.path_completer = PathCompleter()
        self.max_suggestions = 30
        self.min_score = 10
        self.replace_map = get_replace_map()
        # Caches for file lists to avoid repeated expensive scans
        self._git_files_cache: Optional[List[str]] = None
        self._all_files_cache: Optional[List[str]] = None
        self._max_walk_files = 10000
        # Cache for rules to avoid repeated loading
        self._rules_cache: Optional[List[Tuple[str, str]]] = None

    def _get_all_rule_completions(self) -> List[str]:
        """获取所有规则补全项的统一接口

        返回:
            List[str]: 格式为"<rule:{rule_name}>"的规则列表
        """
        all_rules = []
        try:
            from jarvis.jarvis_agent.rules_manager import RulesManager

            rules_manager = RulesManager(os.getcwd())
            available_rules = rules_manager.get_all_available_rule_names()

            # 添加内置规则
            if available_rules.get("builtin"):
                for rule_name in available_rules["builtin"]:
                    all_rules.append(f"<rule:{rule_name}>")

            # 添加文件规则
            if available_rules.get("files"):
                for rule_name in available_rules["files"]:
                    all_rules.append(f"<rule:{rule_name}>")

            # 添加YAML规则
            if available_rules.get("yaml"):
                for rule_name in available_rules["yaml"]:
                    all_rules.append(f"<rule:{rule_name}>")
        except ImportError:
            # 如果无法导入，只使用内置规则
            try:
                from jarvis.jarvis_agent.builtin_rules import list_builtin_rules

                for rule_name in list_builtin_rules():
                    all_rules.append(f"<rule:{rule_name}>")
            except ImportError:
                pass
        except Exception:
            # 任何错误都静默处理
            pass

        return all_rules

    def _get_all_rules(self) -> List[Tuple[str, str]]:
        """获取所有可用的规则，包括内置规则、文件规则和YAML规则

        返回:
            List[Tuple[str, str]]: (规则名称, 规则描述) 列表
        """
        if self._rules_cache is not None:
            return self._rules_cache

        all_rules = []

        try:
            # 导入必要的模块
            from jarvis.jarvis_agent.rules_manager import RulesManager

            # 创建RulesManager实例
            rules_manager = RulesManager(os.getcwd())

            # 获取所有可用规则
            available_rules = rules_manager.get_all_available_rule_names()

            # 添加内置规则
            if available_rules.get("builtin"):
                for rule_name in available_rules["builtin"]:
                    all_rules.append((rule_name, f"📚 内置规则: {rule_name}"))

            # 添加文件规则
            if available_rules.get("files"):
                for rule_name in available_rules["files"]:
                    all_rules.append((rule_name, f"📄 文件规则: {rule_name}"))

            # 添加YAML规则
            if available_rules.get("yaml"):
                for rule_name in available_rules["yaml"]:
                    all_rules.append((rule_name, f"📝 YAML规则: {rule_name}"))

        except ImportError:
            # 如果无法导入，只使用内置规则
            try:
                from jarvis.jarvis_agent.builtin_rules import list_builtin_rules

                for rule_name in list_builtin_rules():
                    all_rules.append((rule_name, f"📚 内置规则: {rule_name}"))
            except ImportError:
                pass
        except Exception:
            # 任何错误都静默处理
            pass

        self._rules_cache = all_rules
        return all_rules

    def get_completions(
        self, document: Document, _: CompleteEvent
    ) -> Iterable[Completion]:
        global _GIT_ROOT_CACHE
        text = document.text_before_cursor
        cursor_pos = document.cursor_position

        # Support both '@' (git files) and '#' (all files excluding .git)
        sym_positions = [(i, ch) for i, ch in enumerate(text) if ch in ("@", "#")]
        if not sym_positions:
            return
        current_pos = None
        current_sym = None
        for i, ch in sym_positions:
            if i < cursor_pos:
                current_pos = i
                current_sym = ch
        if current_pos is None:
            return

        text_after = text[current_pos + 1 : cursor_pos]
        if " " in text_after:
            return

        token = text_after.strip()
        replace_length = len(text_after) + 1

        # 交互约定：
        # - 单个 '@'：优先进行文件路径补全（git tracked files）
        # - '@@'：才显示“内置补全菜单”（tags/commands/rules + files）
        double_at_menu = (
            current_sym == "@"
            and current_pos > 0
            and text[current_pos - 1 : current_pos + 1] == "@@"
        )

        all_completions = []
        if double_at_menu or current_sym != "@":
            all_completions.extend(
                [(ot(tag), self._get_description(tag)) for tag in self.replace_map.keys()]
            )
            all_completions.extend([(ot(cmd), desc) for cmd, desc in BUILTIN_COMMANDS])
            # 添加所有规则（包括内置规则、文件规则、YAML规则）到补全列表
            rules = self._get_all_rules()
            for rule_name, rule_desc in rules:
                all_completions.append((f"<rule:{rule_name}>", rule_desc))

        # File path candidates
        try:
            if current_sym == "@":
                if self._git_files_cache is None:
                    if _GIT_ROOT_CACHE is None:
                        rr = _subprocess.run(
                            ["git", "rev-parse", "--show-toplevel"],
                            stdout=_subprocess.PIPE,
                            stderr=_subprocess.PIPE,
                            text=True,
                            cwd=_get_completion_root(),
                        )
                        _GIT_ROOT_CACHE = rr.stdout.strip() if rr.returncode == 0 else ""
                    git_root = _GIT_ROOT_CACHE or _get_completion_root()
                    result = _subprocess.run(
                        ["git", "ls-files"],
                        stdout=_subprocess.PIPE,
                        stderr=_subprocess.PIPE,
                        text=False,
                        cwd=git_root,
                    )
                    if result.returncode == 0:
                        self._git_files_cache = [
                            p
                            for p in decode_output(result.stdout).splitlines()
                            if p.strip()
                        ]
                    else:
                        self._git_files_cache = []
                paths: List[str] = self._git_files_cache or []
                if not paths:
                    paths = _get_all_files(exclude_git=True)
            else:
                if self._all_files_cache is None:
                    files: List[str] = []
                    base_dir = _get_completion_root()
                    for root, dirs, fnames in _os.walk(base_dir, followlinks=False):
                        # Explicitly include hidden directories (starting with .), but exclude .git, __pycache__, .pytest_cache, etc.
                        dirs[:] = [
                            d
                            for d in dirs
                            if d
                            not in {
                                ".git",
                                "__pycache__",
                                ".pytest_cache",
                                ".mypy_cache",
                                ".ruff_cache",
                                "node_modules",
                                "target",
                            }
                        ]
                        for name in fnames:
                            files.append(
                                _os.path.relpath(_os.path.join(root, name), base_dir)
                            )
                            if len(files) > self._max_walk_files:
                                break
                        if len(files) > self._max_walk_files:
                            break
                    self._all_files_cache = files
                paths = self._all_files_cache or []
            all_completions.extend([(path, "File") for path in paths])
        except Exception:
            pass

        if token:
            # Check if token contains only punctuation/special characters
            # This prevents fuzzywuzzy processor from reducing it to empty string
            token_stripped = token.strip()
            if token_stripped and not any(c.isalnum() for c in token_stripped):
                # Token contains only punctuation/special chars, skip fuzzy matching
                # to avoid warning from fuzzywuzzy processor
                for t, desc in all_completions[: self.max_suggestions]:
                    yield Completion(
                        text=f"'{t}'",
                        start_position=-replace_length,
                        display=t,
                        display_meta=desc,
                    )
            else:
                scored_items = process.extract(
                    token,
                    [item[0] for item in all_completions],
                    limit=self.max_suggestions,
                )
                scored_items = [
                    (item[0], item[1])
                    for item in scored_items
                    if item[1] > self.min_score
                ]
                completion_map = {item[0]: item[1] for item in all_completions}
                for t, score in scored_items:
                    display_text = f"{t} ({score}%)" if score < 100 else t
                    yield Completion(
                        text=f"'{t}'",
                        start_position=-replace_length,
                        display=display_text,
                        display_meta=completion_map.get(t, ""),
                    )
        else:
            for t, desc in all_completions[: self.max_suggestions]:
                yield Completion(
                    text=f"'{t}'",
                    start_position=-replace_length,
                    display=t,
                    display_meta=desc,
                )

    def _get_description(self, tag: str) -> str:
        """
        `@@` 菜单里右侧显示的“提示内容”。

        规则：
        - `append=True`：显示 description，并附加工具线索（如模板里可提取到）。
        - `append=False`（Replace）：如果没有任何可用工具/命令线索，则右侧留空（避免出现无意义的 Replace 提示）。
        - 若模板里能提取到工具名（例如 Web 模板里有 `name: search_web`），则用于补充显示。
        """
        entry = self.replace_map.get(tag)
        if not entry:
            return tag

        append = bool(entry.get("append", False))
        desc = entry.get("description") or ""
        template = entry.get("template") or ""

        # 从模板提取显式工具名（内置模板目前主要通过 `name: xxx` 给出）
        tool_names: list[str] = []
        try:
            import re

            # 支持模板里 `name:` 行可能带缩进
            m = re.search(r"(?m)^\\s*name:\\s*([A-Za-z0-9_\\-]+)\\s*$", template)
            if m:
                tool_names.append(m.group(1))
        except Exception:
            pass

        tool_hint = f"工具: {', '.join(tool_names)}" if tool_names else ""

        # 右侧栏“使用说明”优先展示 description；如果还能提取到工具名则一并补充。
        # 行为标记用中文，便于用户理解模板会“追加/替换”。
        mode_hint = "（追加）" if append else "（替换）"
        parts = [p for p in (desc, tool_hint) if p]
        if not parts:
            return ""
        return " ".join(parts) + mode_hint


def get_all_rules_formatted() -> List[str]:
    """
    获取所有可用规则的格式化列表，包括内置、文件和YAML规则。

    返回:
        List[str]: 格式化的规则列表，每个规则以"<rule:规则名>"格式返回

    异常处理:
        - 处理RulesManager导入失败的情况
        - 处理内置规则导入失败的情况
        - 在任何错误情况下返回空列表而不是抛出异常
    """
    all_rules = []
    try:
        try:
            from jarvis.jarvis_agent.rules_manager import RulesManager

            rules_manager = RulesManager(os.getcwd())
            available_rules = rules_manager.get_all_available_rule_names()

            # 添加内置规则
            if available_rules.get("builtin"):
                for rule_name in available_rules["builtin"]:
                    all_rules.append(f"<rule:{rule_name}>")

            # 添加文件规则
            if available_rules.get("files"):
                for rule_name in available_rules["files"]:
                    all_rules.append(f"<rule:{rule_name}>")

            # 添加YAML规则
            if available_rules.get("yaml"):
                for rule_name in available_rules["yaml"]:
                    all_rules.append(f"<rule:{rule_name}>")
        except ImportError:
            # 如果无法导入RulesManager，只使用内置规则
            try:
                from jarvis.jarvis_agent.builtin_rules import list_builtin_rules

                for rule_name in list_builtin_rules():
                    all_rules.append(f"<rule:{rule_name}>")
            except ImportError:
                pass
    except Exception:
        # 任何异常都返回空列表
        all_rules = []

    return all_rules


def _get_fzf_completion_items(specials: List[str], files: List[str]) -> List[str]:
    """
    获取fzf补全所需的完整项目列表。

    该函数统一处理fzf补全所需的各类项目，包括特殊符号、内置标签、规则、文件等，
    消除了两处fzf补全代码中的重复逻辑。

    参数:
        specials: 特殊符号列表
        files: 文件列表

    返回:
        List[str]: 合并后的完整项目列表，按特定顺序排列
    """
    items = []

    # 添加特殊符号（过滤空字符串）
    items.extend([s for s in specials if isinstance(s, str) and s.strip()])

    # 添加内置标签
    try:
        from jarvis.jarvis_utils.config import get_replace_map
        from jarvis.jarvis_utils.tag import ot

        replace_map = get_replace_map()
        builtin_tags = [
            ot(tag)
            for tag in replace_map.keys()
            if isinstance(tag, str) and tag.strip()
        ]
        items.extend(builtin_tags)

        # 添加内置命令标记
        builtin_commands = [ot(cmd) for cmd, _ in BUILTIN_COMMANDS]
        items.extend(builtin_commands)
    except Exception:
        # 标签获取失败时跳过
        pass

    # 添加规则
    try:
        builtin_rules = get_all_rules_formatted()
        items.extend(builtin_rules)
    except Exception:
        # 规则获取失败时跳过
        pass

    # 添加文件
    items.extend(files)

    return items


# -+
# 公共判定辅助函数（按当前Agent优先）
# ---------------------
def _get_current_agent_for_input() -> Optional[Any]:
    try:
        import jarvis.jarvis_utils.globals as g

        current_name = g.get_current_agent_name()
        if current_name:
            return g.get_agent(current_name)
    except Exception:
        pass
    return None


def _is_non_interactive_for_current_agent() -> bool:
    try:
        from jarvis.jarvis_utils.config import is_non_interactive

        ag = _get_current_agent_for_input()
        try:
            return (
                bool(getattr(ag, "non_interactive", False))
                if ag
                else bool(is_non_interactive())
            )
        except Exception:
            return bool(is_non_interactive())
    except Exception:
        return False


def _is_auto_complete_for_current_agent() -> bool:
    try:
        ag = _get_current_agent_for_input()
        if ag is not None and hasattr(ag, "auto_complete"):
            try:
                return bool(getattr(ag, "auto_complete", False))
            except Exception:
                pass
        return False
    except Exception:
        return False


def _get_agent_hint() -> str:
    """获取当前Agent的提示信息（可用智能体列表）。"""
    try:
        ag = _get_current_agent_for_input()
        ohs = getattr(ag, "output_handler", [])
        available_agents: List[str] = []
        for oh in ohs or []:
            cfgs = getattr(oh, "agents_config", None)
            if isinstance(cfgs, list):
                for c in cfgs:
                    try:
                        name = c.get("name")
                    except Exception:
                        name = None
                    if isinstance(name, str) and name.strip():
                        available_agents.append(name.strip())
        if available_agents:
            # 去重但保留顺序
            seen = set()
            ordered = []
            for n in available_agents:
                if n not in seen:
                    seen.add(n)
                    ordered.append(n)
            return (
                "\n当前可用智能体: "
                + ", ".join(ordered)
                + f"\n如需将任务交给其他智能体，请使用 {ot('SEND_MESSAGE')} 块。"
            )
    except Exception:
        pass
    return ""


def _get_non_interactive_response(auto_complete: bool) -> str:
    """获取非交互模式下的响应文本。"""
    hint = _get_agent_hint()
    if auto_complete:
        base_msg = (
            "当前是非交互模式，所有的事情你都自我决策，如果无法决策，就完成任务。输出"
            + ot("!!!COMPLETE!!!")
        )
        return base_msg + hint
    else:
        return "当前是非交互模式，所有的事情你都自我决策" + hint


def user_confirm(tip: str, default: bool = True) -> bool:
    """提示用户确认是/否问题（按当前Agent优先判断非交互）"""
    try:
        if _is_non_interactive_for_current_agent():
            return default

        # 获取当前agent名称并添加到提示前缀
        agent_name = ""
        try:
            ag = _get_current_agent_for_input()
            if ag is not None:
                name = getattr(ag, "name", None)
                if name:
                    agent_name = f"[{name}] "
        except Exception:
            pass

        suffix = "[Y/n]" if default else "[y/N]"
        ret = get_single_line_input(f"{agent_name}{tip} {suffix}: ")
        return default if ret == "" else ret.lower() == "y"
    except KeyboardInterrupt:
        return False


def _show_history_and_copy() -> None:
    """
    显示消息历史记录并处理复制到剪贴板。
    此函数使用标准I/O，可在提示会话之外安全调用。
    """

    history = get_message_history()
    if not history:
        PrettyOutput.auto_print("ℹ️ 没有可复制的消息")
        return

    # 为避免 PrettyOutput 在循环中为每行加框，先拼接后统一打印
    lines = []
    lines.append("\n" + "=" * 20 + " 📜 消息历史记录 " + "=" * 20)
    for i, msg in enumerate(history):
        cleaned_msg = msg.replace("\n", r"\n")
        display_msg = (
            (cleaned_msg[:70] + "...") if len(cleaned_msg) > 70 else cleaned_msg
        )
        lines.append(f"  {i + 1}: {display_msg.strip()}")
        lines.append("=" * 58 + "\n")
    PrettyOutput.auto_print("\n".join(lines))

    while True:
        try:
            prompt_text = f"{Fore.CYAN}请输入要复制的条目序号 (或输入c取消, 直接回车选择最后一条): {ColoramaStyle.RESET_ALL}"
            choice_str = input(prompt_text)

            if not choice_str:  # User pressed Enter
                if not history:
                    PrettyOutput.auto_print("ℹ️ 没有历史记录可供选择。")
                    break
                choice = len(history) - 1
            elif choice_str.lower() == "c":
                PrettyOutput.auto_print("ℹ️ 已取消")
                break
            else:
                choice = int(choice_str) - 1

            if 0 <= choice < len(history):
                selected_msg = history[choice]
                copy_to_clipboard(selected_msg)
                PrettyOutput.auto_print(f"✅ 已复制消息: {selected_msg[:70]}...")
                break
            else:
                PrettyOutput.auto_print("⚠️ 无效的序号，请重试。")
        except ValueError:
            PrettyOutput.auto_print("⚠️ 无效的输入，请输入数字。")
        except (KeyboardInterrupt, EOFError):
            PrettyOutput.auto_print("ℹ️ 操作取消")
            break


def try_toggle_agent_normal_smart_tier() -> bool:
    """主会话在 normal 与 smart 之间切换（多行输入栏 F2）。

    cheap 档位会先切到 smart（再按一次可回到 normal）；从 normal 按快捷键进入 smart。
    """
    try:
        ag = get_current_agent()
        if not ag or not getattr(ag, "model", None):
            return False
        m = ag.model
        if not hasattr(m, "set_platform_type"):
            return False
        pt = getattr(m, "platform_type", "normal") or "normal"
        if pt == "smart":
            m.set_platform_type("normal")
            # 这里不要额外向 stdout 打印，避免破坏 prompt_toolkit 的原地刷新区域。
        else:
            m.set_platform_type("smart")
            # 这里不要额外向 stdout 打印，避免破坏 prompt_toolkit 的原地刷新区域。
        return True
    except Exception as e:
        PrettyOutput.auto_print(f"⚠️ 切换 smart/normal 失败: {e}")
        return False


def _get_multiline_input_internal(
    tip: str, preset: Optional[str] = None, preset_cursor: Optional[int] = None
) -> str:
    """
    Internal function to get multiline input using prompt_toolkit.
    Returns a sentinel value if Ctrl+O is pressed.
    """
    # 获取当前模型名称用于提示符
    def _get_model_name_hint() -> str:
        try:
            current_agent = get_current_agent()
            if current_agent and hasattr(current_agent, "model"):
                model = current_agent.model
                if model and getattr(model, "model_name", None):
                    # 提示头只显示模型名，避免显示 `|normal`/`|smart` 档位后缀
                    return f"[{model.model_name}]"
        except Exception:
            pass
        return ""
    
    model_hint = _get_model_name_hint()
    
    bindings = KeyBindings()

    # Show a one-time hint on the first Enter press in this invocation (disabled; using inlay toolbar instead)
    first_enter_hint_shown = True

    @bindings.add("enter")
    def _(event: KeyPressEvent) -> None:
        nonlocal first_enter_hint_shown
        if not first_enter_hint_shown and not _multiline_hint_already_shown():
            first_enter_hint_shown = True

            def _show_notice() -> None:
                PrettyOutput.auto_print(
                    "ℹ️ 提示：当前支持多行输入。输入完成请使用 Ctrl+J 或 Ctrl+D 确认；Enter 仅用于换行。"
                )
                try:
                    input("按回车继续...")
                except Exception:
                    pass
                # Persist the hint so it won't be shown again in future runs
                try:
                    _mark_multiline_hint_shown()
                except Exception:
                    pass

            run_in_terminal(_show_notice)
            return

        if event.current_buffer.complete_state:
            completion = event.current_buffer.complete_state.current_completion
            if completion:
                event.current_buffer.apply_completion(completion)
            else:
                event.current_buffer.insert_text("\n")
        else:
            event.current_buffer.insert_text("\n")

    @bindings.add("c-j", filter=has_focus(DEFAULT_BUFFER))
    def _(event: KeyPressEvent) -> None:
        event.current_buffer.validate_and_handle()

    @bindings.add("c-d", filter=has_focus(DEFAULT_BUFFER))
    def _(event: KeyPressEvent) -> None:
        event.current_buffer.validate_and_handle()

    @bindings.add("c-o", filter=has_focus(DEFAULT_BUFFER))
    def _(event: KeyPressEvent) -> None:
        """Handle Ctrl+O by exiting the prompt and returning the sentinel value."""
        event.app.exit(result=CTRL_O_SENTINEL)

    @bindings.add("c-x", filter=has_focus(DEFAULT_BUFFER))
    def _(event: KeyPressEvent) -> None:
        """Handle Ctrl+X by exiting the prompt and requesting program exit."""
        event.app.exit(result=CTRL_X_SENTINEL)

    @bindings.add("f2", filter=has_focus(DEFAULT_BUFFER))
    def _(event: KeyPressEvent) -> None:
        """F2：主会话 normal ↔ smart（增强档需手动切换）。"""
        try_toggle_agent_normal_smart_tier()
        try:
            event.app.invalidate()
        except Exception:
            pass

    # Ctrl+R：进入历史隐藏查看界面（列表 + 输入序号查看，注意在 bash 中 Ctrl+R 为反向历史搜索）
    @bindings.add("c-r", filter=has_focus(DEFAULT_BUFFER), eager=True)
    def _(event: KeyPressEvent) -> None:
        """Ctrl+R: 进入历史隐藏查看界面，输入序号并回车查看对应完整内容。"""
        run_in_terminal(run_truncated_history_viewer)

    def _gen_shell_cmd() -> str:
        try:
            if _os.name == "nt":
                for name in ("pwsh", "powershell", "cmd"):
                    if name == "cmd" or _shutil.which(name):
                        if name == "cmd":
                            return "!cmd /K set terminal=1"
                        return f"!{name} -NoExit -Command \"$env:terminal='1'\""
            else:
                shell_path = os.environ.get("SHELL", "")
                if shell_path:
                    base = os.path.basename(shell_path)
                    if base:
                        return f"!env terminal=1 {base}"
                for name in ("fish", "zsh", "bash", "sh"):
                    if _shutil.which(name):
                        return f"!env terminal=1 {name}"
                return "!env terminal=1 bash"
        except Exception:
            pass
        return "!env terminal=1 bash"

    @bindings.add("c-t", eager=True)
    def _(event: KeyPressEvent) -> None:
        """Ctrl+T: 打开终端(!SHELL)。"""
        event.app.exit(result=_gen_shell_cmd() + " # JARVIS-NOCONFIRM")

    @bindings.add("@", filter=has_focus(DEFAULT_BUFFER), eager=True)
    def _(event: KeyPressEvent) -> None:
        """
        使用 @ 触发 fzf（当 fzf 存在）；否则仅插入 @ 以启用内置补全
        逻辑：
        - 若检测到系统存在 fzf，则先插入 '@'，随后请求外层运行 fzf 并在返回后进行替换/插入
        - 若不存在 fzf 或发生异常，则直接插入 '@' 并触发补全
        """
        try:
            buf = event.current_buffer
            # 默认行为：插入 '@' 并触发补全（单个 @ 为文件补全；@@ 为内置菜单）
            # 如需沿用旧行为（@ 触发 fzf），可设置 JARVIS_AT_USE_FZF=true
            use_fzf = os.environ.get("JARVIS_AT_USE_FZF", "false").lower() == "true"
            if use_fzf and _shutil.which("fzf") is not None:
                # 先插入 '@'，以便外层根据最后一个 '@' 进行片段替换
                buf.insert_text("@")
                doc = buf.document
                text = doc.text
                cursor = doc.cursor_position
                payload = (
                    f"{cursor}:{base64.b64encode(text.encode('utf-8')).decode('ascii')}"
                )
                event.app.exit(result=FZF_REQUEST_SENTINEL_PREFIX + payload)
                return

            buf.insert_text("@")
            buf.start_completion(select_first=False)
            return
        except Exception:
            try:
                buf = event.current_buffer
                buf.insert_text("@")
                # 即使发生异常，也尝试触发补全
                buf.start_completion(select_first=False)
            except Exception:
                pass

    @bindings.add("#", filter=has_focus(DEFAULT_BUFFER), eager=True)
    def _(event: KeyPressEvent) -> None:
        """
        使用 # 触发 fzf（当 fzf 存在），以“全量文件模式”进行选择（排除 .git）；否则仅插入 # 启用内置补全
        """
        try:
            buf = event.current_buffer
            disable_fzf = os.environ.get("JARVIS_DISABLE_FZF_COMPLETION", "false").lower() == "true"
            if disable_fzf or _shutil.which("fzf") is None:
                buf.insert_text("#")
                # 手动触发补全，以便显示 rule 和其他补全选项
                buf.start_completion(select_first=False)
                return
            # 先插入 '#'
            buf.insert_text("#")
            doc = buf.document
            text = doc.text
            cursor = doc.cursor_position
            payload = (
                f"{cursor}:{base64.b64encode(text.encode('utf-8')).decode('ascii')}"
            )
            event.app.exit(result=FZF_REQUEST_ALL_SENTINEL_PREFIX + payload)
            return
        except Exception:
            try:
                buf = event.current_buffer
                buf.insert_text("#")
                # 即使发生异常，也尝试触发补全
                buf.start_completion(select_first=False)
            except Exception:
                pass

    # 快捷键栏：去除背景色（与终端背景一致），说明文字浅青、快捷键组合白色加粗
    style = PromptStyle.from_dict(
        {
            "prompt": "ansicyan bold",
            "bottom-toolbar": "bg:default noreverse",
            "bottom-toolbar.text": "bg:default noreverse",
            "bt.line": "bg:default fg:#00bcd4 noreverse",
            "bt.tip": "fg:#00bcd4 bold",
            "bt.sep": "fg:#00bcd4",
            "bt.key": "fg:#ffffff bold",
            "bt.label": "fg:#00bcd4",
            "placeholder": "italic fg:#888888",
        }
    )

    def _bottom_toolbar() -> Any:
        try:
            cols = os.get_terminal_size().columns
        except Exception:
            cols = 80
        rule_str = "─" * max(0, cols)

        def _truncate_segments_from_left(
            segments: list[tuple[str, str]], max_width: int
        ) -> list[tuple[str, str]]:
            """按字符宽度限制在终端列数内，超过则从左侧截断（保留右侧信息）。"""
            from wcwidth import wcswidth

            def _text_width(s: str) -> int:
                w = wcswidth(s)
                return w if w >= 0 else len(s)

            def _suffix_by_width(s: str, width: int) -> str:
                """按显示宽度从字符串末尾截取 suffix，确保其 w <= width。"""
                if width <= 0 or not s:
                    return ""
                out_rev: list[str] = []
                used_w = 0
                for ch in reversed(s):
                    ch_w = _text_width(ch)
                    if used_w + ch_w > width:
                        break
                    out_rev.append(ch)
                    used_w += ch_w
                return "".join(reversed(out_rev))

            if max_width <= 0:
                return []
            # 计算总宽度（需要考虑中文全角等“显示宽度”差异）
            total = 0
            for _, t in segments:
                total += _text_width(t)
            if total <= max_width:
                return segments

            kept: list[tuple[str, str]] = []
            used = 0
            for style, text in reversed(segments):
                if not text:
                    continue
                seg_w = _text_width(text)
                if used + seg_w <= max_width:
                    kept.append((style, text))
                    used += seg_w
                    continue

                # 仅保留本段的“右侧 suffix”
                remain = max_width - used
                if remain <= 0:
                    break

                ellipsis = "..."
                ell_w = _text_width(ellipsis)
                if remain <= ell_w:
                    new_text = _suffix_by_width(text, remain)
                else:
                    suffix = _suffix_by_width(text, remain - ell_w)
                    new_text = ellipsis + suffix

                kept.append((style, new_text))
                used = max_width
                break

            return list(reversed(kept))

        # line2：尽量把“轮次/Token”等右侧状态保留在同一行，避免换行导致的 UI 漂移。
        line2_items: list[tuple[str, str]] = [
            ("class:bt.key", "@"),
            ("class:bt.label", " 文件补全 "),
            ("class:bt.sep", " • "),
            ("class:bt.key", "Ctrl+D"),
            ("class:bt.label", " 提交 "),
            ("class:bt.sep", " • "),
            ("class:bt.key", "Ctrl+O"),
            ("class:bt.label", " 复制历史信息 "),
            ("class:bt.sep", " • "),
            ("class:bt.key", "Ctrl+R"),
            ("class:bt.label", " 历史隐藏查看 "),
            ("class:bt.sep", " • "),
            ("class:bt.key", "Ctrl+T"),
            ("class:bt.label", " 终端(!SHELL) "),
            ("class:bt.sep", " • "),
            ("class:bt.key", "F2"),
            ("class:bt.label", " normal↔smart "),
            ("class:bt.sep", " • "),
            ("class:bt.key", "Ctrl+C"),
            ("class:bt.label", " 取消 "),
        ]
        
        # 获取当前轮次和token信息
        try:
            current_agent = get_current_agent()
            if current_agent and hasattr(current_agent, 'model'):
                model = current_agent.model
                if hasattr(model, "platform_type"):
                    pt = getattr(model, "platform_type", "normal") or "normal"
                    # normal 档位不做额外展示，避免界面噪音；smart/cheap 才提示
                    if pt != "normal":
                        line2_items.append(("class:bt.sep", " • "))
                        line2_items.append(("class:bt.key", "当前档"))
                        line2_items.append(("class:bt.label", f": {pt} "))
                if hasattr(model, 'get_conversation_turn'):
                    current_turn = model.get_conversation_turn()
                    threshold = get_conversation_turn_threshold()
                    
                    # 尝试获取token使用信息
                    token_percent = 0.0
                    if hasattr(model, '_get_token_usage_info'):
                        try:
                            token_percent, percent_color, progress_bar = model._get_token_usage_info()
                        except Exception:
                            token_percent = 0.0
                    
                    # 添加右侧的分隔符和状态信息，使用与Ctrl+X相同的样式
                    line2_items.append(("class:bt.sep", " • "))
                    line2_items.append(("class:bt.key", "轮次"))
                    line2_items.append(
                        ("class:bt.label", f": {current_turn}/{threshold} ")
                    )
                    if token_percent > 0:
                        line2_items.append(("class:bt.sep", " • "))
                        line2_items.append(("class:bt.key", "Token"))
                        line2_items.append(("class:bt.label", f": {token_percent:.1f}% "))
        except Exception:
            pass

        line2_items = _truncate_segments_from_left(line2_items, cols)
        # 强制使用固定“2行”布局：第1行横线，第2行状态文本；避免 F2 切换时因宽度变化自动换行。
        toolbar_items = [("class:bt.line", rule_str), ("", "\n"), *line2_items]
        return FormattedText(toolbar_items)

    history_dir = get_data_dir()
    session: PromptSession[Any] = PromptSession(
        history=FileHistory(os.path.join(history_dir, "multiline_input_history")),
        completer=FileCompleter(),
        key_bindings=bindings,
        complete_while_typing=True,
        multiline=True,
        vi_mode=False,
        mouse_support=False,
    )

    # Tip is shown in placeholder; avoid extra print
    prompt = FormattedText([("class:prompt", f"👤{model_hint} > ")])

    def _pre_run() -> None:
        try:
            from prompt_toolkit.application.current import get_app as _ga

            app = _ga()
            buf = app.current_buffer
            if preset is not None and preset_cursor is not None:
                cp = max(0, min(len(buf.text), preset_cursor))
                buf.cursor_position = cp
        except Exception:
            pass

    # 输入框上方横线（两条横线中间是用户输入）
    try:
        cols = os.get_terminal_size().columns
        sys.stdout.write("\033[36m" + "─" * max(0, cols) + "\033[0m\n")
        sys.stdout.flush()
    except Exception:
        pass

    try:
        result = session.prompt(
            prompt,
            style=style,
            pre_run=_pre_run,
            bottom_toolbar=_bottom_toolbar,
            placeholder=FormattedText([("class:placeholder", tip)]),
            default=(preset or ""),
        )
        return str(result).strip() if result else ""
    except (KeyboardInterrupt, EOFError):
        return ""


def get_multiline_input(tip: str, print_on_empty: bool = True) -> str:
    """
    获取带有增强补全和确认功能的多行输入。
    此函数处理控制流，允许在不破坏终端状态的情况下处理历史记录复制。

    参数:
        tip: 提示文本，将显示在底部工具栏中
        print_on_empty: 当输入为空字符串时，是否打印“输入已取消”提示。默认打印。
    """
    preset: Optional[str] = None
    preset_cursor: Optional[int] = None
    while True:
        # 基于“当前Agent”精确判断非交互与自动完成，避免多Agent相互干扰
        if _is_non_interactive_for_current_agent():
            return _get_non_interactive_response(_is_auto_complete_for_current_agent())
        user_input = _get_multiline_input_internal(
            tip, preset=preset, preset_cursor=preset_cursor
        )

        if user_input == CTRL_O_SENTINEL:
            _show_history_and_copy()
            tip = "请继续输入（或按Ctrl+J/Ctrl+D确认）:"
            continue
        if user_input == CTRL_X_SENTINEL:
            PrettyOutput.auto_print("🛑 用户请求退出程序...")
            raise SystemExit(0)
        elif isinstance(user_input, str) and user_input.startswith(
            FZF_REQUEST_SENTINEL_PREFIX
        ):
            # Handle fzf request outside the prompt, then prefill new text.
            cursor, text = _parse_fzf_payload(user_input, FZF_REQUEST_SENTINEL_PREFIX)
            if cursor is None or text is None:
                # Malformed payload; just continue without change.
                preset = None
                tip = "FZF 预填失败，继续输入:"
                continue

            # Run fzf to get a file selection synchronously (outside prompt)
            files = _get_files_for_fzf(use_git=True)
            selected_path = _run_fzf_for_selection(files, "Files> ")

            # Compute new text based on selection (or keep original if none)
            if selected_path:
                preset, preset_cursor = _insert_file_path(
                    text, cursor, selected_path, "@"
                )
                tip = "已插入文件，继续编辑或按Ctrl+J/Ctrl+]确认:"
            else:
                # No selection; keep original text and cursor
                preset = text
                preset_cursor = cursor
                tip = "未选择文件或已取消，继续编辑:"
            _clear_previous_prompt(text)
            continue
        elif isinstance(user_input, str) and user_input.startswith(
            FZF_REQUEST_ALL_SENTINEL_PREFIX
        ):
            # Handle fzf request (all-files mode, excluding .git) outside the prompt, then prefill new text.
            cursor, text = _parse_fzf_payload(
                user_input, FZF_REQUEST_ALL_SENTINEL_PREFIX
            )
            if cursor is None or text is None:
                # Malformed payload; just continue without change.
                preset = None
                tip = "FZF 预填失败，继续输入:"
                continue

            # Run fzf to get a file selection synchronously (outside prompt) with all files (exclude .git)
            files = _get_all_files(exclude_git=True)
            selected_path = _run_fzf_for_selection(files, "Files(all)> ")

            # Compute new text based on selection (or keep original if none)
            if selected_path:
                preset, preset_cursor = _insert_file_path(
                    text, cursor, selected_path, "#"
                )
                tip = "已插入文件，继续编辑或按Ctrl+J/Ctrl+D确认:"
            else:
                # No selection; keep original text and cursor
                preset = text
                preset_cursor = cursor
                tip = "未选择文件或已取消，继续编辑:"
            _clear_previous_prompt(text)
            continue
        elif isinstance(user_input, str) and user_input.startswith(
            FZF_INSERT_SENTINEL_PREFIX
        ):
            # 从哨兵载荷中提取新文本，作为下次进入提示的预填内容
            preset = user_input[len(FZF_INSERT_SENTINEL_PREFIX) :]
            preset_cursor = len(preset)

            # 清除上一条输入行（多行安全），避免多清，保守仅按提示行估算
            try:
                rows_total = _calc_prompt_rows(preset)
                for _ in range(rows_total):
                    sys.stdout.write("\x1b[1A")
                    sys.stdout.write("\x1b[2K\r")
                sys.stdout.flush()
            except Exception:
                pass
            tip = "已插入文件，继续编辑或按Ctrl+J/Ctrl+D确认:"
            continue
        else:
            if not user_input and print_on_empty:
                PrettyOutput.auto_print("ℹ️ 输入已取消")
            return user_input
