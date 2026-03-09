# -*- coding: utf-8 -*-
"""
输出格式化模块
该模块为Jarvis系统提供了丰富的文本格式化和显示工具。
包含：
- 用于分类不同输出类型的OutputType枚举
- 用于格式化和显示样式化输出的PrettyOutput类
- 多种编程语言的语法高亮支持
- 结构化输出的面板显示
"""

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
import re
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from datetime import datetime

from pygments.lexers import guess_lexer
from pygments.util import ClassNotFound
from rich.style import Style as RichStyle
from rich.syntax import Syntax
from rich.text import Text

from jarvis.jarvis_utils.config import get_pretty_output
from jarvis.jarvis_utils.config import is_print_error_traceback
from jarvis.jarvis_utils.globals import console
from jarvis.jarvis_utils.globals import get_agent
from jarvis.jarvis_utils.globals import get_agent_list
from jarvis.jarvis_utils import globals as jarvis_globals
from jarvis.jarvis_utils.globals import TRUNCATED_HISTORY_MAX_SIZE


# Rich支持的标准颜色列表
RICH_STANDARD_COLORS = {
    "black",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "white",
    "bright_black",
    "bright_red",
    "bright_green",
    "bright_yellow",
    "bright_blue",
    "bright_magenta",
    "bright_cyan",
    "bright_white",
    "dark_red",
    "dark_green",
    "dark_yellow",
    "dark_blue",
    "dark_magenta",
    "dark_cyan",
    "grey0",
    "grey100",
    "grey50",
    "grey70",
    "grey30",
}


def _safe_color_get(color_name: str, fallback: str = "white") -> str:
    """
    安全的颜色获取函数，提供颜色验证和回退机制。

    参数：
        color_name: 期望的颜色名称
        fallback: 回退颜色名称（默认为白色）

    返回：
        有效的颜色名称，如果原颜色无效则返回回退颜色
    """
    if color_name in RICH_STANDARD_COLORS:
        return color_name

    # 尝试一些常见的颜色别名映射
    color_alias_map = {
        "dark_olive_green": "green",
        "orange3": "bright_yellow",
        "sea_green3": "green",
        "dark_sea_green": "green",
        "grey58": "grey50",
    }

    return color_alias_map.get(color_name, fallback)


class OutputType(Enum):
    """
    输出类型枚举，用于分类和样式化不同类型的消息。

    属性：
        SYSTEM: AI助手消息
        CODE: 代码相关输出
        RESULT: 工具执行结果
        ERROR: 错误信息
        INFO: 系统提示
        PLANNING: 任务规划
        PROGRESS: 执行进度
        SUCCESS: 成功信息
        WARNING: 警告信息
        DEBUG: 调试信息
        USER: 用户输入
        TOOL: 工具调用
        START: 任务开始
        TARGET: 目标任务
        STOP: 任务停止
        RETRY: 重试操作
        ROLLBACK: 回滚操作
        DIRECTORY: 目录相关
        STATISTICS: 统计信息
    """

    SYSTEM = "SYSTEM"
    CODE = "CODE"
    RESULT = "RESULT"
    ERROR = "ERROR"
    INFO = "INFO"
    PLANNING = "PLANNING"
    PROGRESS = "PROGRESS"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    DEBUG = "DEBUG"
    USER = "USER"
    TOOL = "TOOL"
    START = "START"
    TARGET = "TARGET"
    STOP = "STOP"
    RETRY = "RETRY"
    ROLLBACK = "ROLLBACK"
    DIRECTORY = "DIRECTORY"
    STATISTICS = "STATISTICS"
    CHEAP_MODEL = "CHEAP_MODEL"
    NORMAL_MODEL = "NORMAL_MODEL"
    SMART_MODEL = "SMART_MODEL"


# 输出类型图标映射（统一的图标定义）
OUTPUT_ICONS = {
    OutputType.SYSTEM: "🤖",
    OutputType.CODE: "📝",
    OutputType.RESULT: "✨",
    OutputType.ERROR: "❌",
    OutputType.INFO: "ℹ️",
    OutputType.PLANNING: "📋",
    OutputType.PROGRESS: "⏳",
    OutputType.SUCCESS: "✅",
    OutputType.WARNING: "⚠️",
    OutputType.DEBUG: "🔍",
    OutputType.USER: "👤",
    OutputType.TOOL: "🔧",
    OutputType.START: "🚀",
    OutputType.TARGET: "🎯",
    OutputType.STOP: "🛑",
    OutputType.RETRY: "🔄",
    OutputType.ROLLBACK: "🔙",
    OutputType.DIRECTORY: "📁",
    OutputType.STATISTICS: "📊",
    OutputType.CHEAP_MODEL: "💰",
    OutputType.NORMAL_MODEL: "⭐",
    OutputType.SMART_MODEL: "🧠",
}


# Emoji 到输出类型的反向映射（包含别名）
EMOJI_TO_OUTPUT_TYPE = {
    "🤖": OutputType.SYSTEM,
    "📝": OutputType.CODE,
    "✨": OutputType.RESULT,
    "❌": OutputType.ERROR,
    "ℹ️": OutputType.INFO,
    "📋": OutputType.PLANNING,
    "⏳": OutputType.PROGRESS,
    "✅": OutputType.SUCCESS,
    "⚠️": OutputType.WARNING,
    "🔍": OutputType.DEBUG,
    "👤": OutputType.USER,
    "🔧": OutputType.TOOL,
    "🚀": OutputType.START,
    "🎯": OutputType.TARGET,
    "🛑": OutputType.STOP,
    "🔄": OutputType.RETRY,
    "🔙": OutputType.ROLLBACK,
    "📁": OutputType.DIRECTORY,
    "📂": OutputType.DIRECTORY,  # 别名
    "📊": OutputType.STATISTICS,
    "💰": OutputType.CHEAP_MODEL,
    "⭐": OutputType.NORMAL_MODEL,
    "🧠": OutputType.SMART_MODEL,
}


@dataclass
class OutputEvent:
    """
    输出事件的通用结构，供不同输出后端（Sink）消费。
    - text: 文本内容
    - output_type: 输出类型
    - timestamp: 是否显示时间戳
    - lang: 语法高亮语言（可选，不提供则自动检测）
    - traceback: 是否显示异常堆栈
    - section: 若为章节标题输出，填入标题文本；否则为None
    - context: 额外上下文（预留给TUI/日志等）
    """

    text: str
    output_type: OutputType
    timestamp: bool = True
    lang: Optional[str] = None
    traceback: bool = False
    section: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class OutputSink(ABC):
    """输出后端抽象接口，不同前端（控制台/TUI/SSE/日志）实现该接口以消费输出事件。"""

    @abstractmethod
    def emit(self, event: OutputEvent) -> None:  # pragma: no cover - 抽象方法
        raise NotImplementedError


class ConsoleOutputSink(OutputSink):
    """
    默认控制台输出实现，保持与原 PrettyOutput 行为一致。
    """

    # 章节样式配置（使用统一的图标）
    _SECTION_STYLES = {
        OutputType.SYSTEM: RichStyle(
            color="cyan", frame=True, meta={"icon": OUTPUT_ICONS[OutputType.SYSTEM]}
        ),
        OutputType.CODE: RichStyle(
            color="green", frame=True, meta={"icon": OUTPUT_ICONS[OutputType.CODE]}
        ),
        OutputType.RESULT: RichStyle(
            color="blue", frame=True, meta={"icon": OUTPUT_ICONS[OutputType.RESULT]}
        ),
        OutputType.ERROR: RichStyle(
            color="bright_red",
            frame=True,
            meta={"icon": OUTPUT_ICONS[OutputType.ERROR]},
            blink=True,
            bold=True,
        ),
        OutputType.INFO: RichStyle(
            color="grey70", frame=True, meta={"icon": OUTPUT_ICONS[OutputType.INFO]}
        ),
        OutputType.PLANNING: RichStyle(
            color="magenta",
            bold=True,
            frame=True,
            meta={"icon": OUTPUT_ICONS[OutputType.PLANNING]},
        ),
        OutputType.PROGRESS: RichStyle(
            color="grey50",
            encircle=True,
            frame=True,
            meta={"icon": OUTPUT_ICONS[OutputType.PROGRESS]},
        ),
        OutputType.SUCCESS: RichStyle(
            color="bright_green",
            bold=True,
            strike=False,
            meta={"icon": OUTPUT_ICONS[OutputType.SUCCESS]},
        ),
        OutputType.WARNING: RichStyle(
            color="bright_yellow",
            bold=True,
            blink=True,
            meta={"icon": OUTPUT_ICONS[OutputType.WARNING]},
        ),
        OutputType.DEBUG: RichStyle(
            color="grey50",
            dim=True,
            conceal=True,
            meta={"icon": OUTPUT_ICONS[OutputType.DEBUG]},
        ),
        OutputType.USER: RichStyle(
            color="bright_green",
            frame=True,
            meta={"icon": OUTPUT_ICONS[OutputType.USER]},
        ),
        OutputType.TOOL: RichStyle(
            color="green", frame=True, meta={"icon": OUTPUT_ICONS[OutputType.TOOL]}
        ),
        OutputType.START: RichStyle(
            color="bright_cyan",
            bold=True,
            frame=True,
            meta={"icon": OUTPUT_ICONS[OutputType.START]},
        ),
        OutputType.TARGET: RichStyle(
            color="bright_magenta",
            bold=True,
            frame=True,
            meta={"icon": OUTPUT_ICONS[OutputType.TARGET]},
        ),
        OutputType.STOP: RichStyle(
            color="bright_red",
            bold=True,
            frame=True,
            meta={"icon": OUTPUT_ICONS[OutputType.STOP]},
        ),
        OutputType.RETRY: RichStyle(
            color="grey70",
            bold=True,
            frame=True,
            meta={"icon": OUTPUT_ICONS[OutputType.RETRY]},
        ),
        OutputType.ROLLBACK: RichStyle(
            color="grey70",
            bold=True,
            frame=True,
            meta={"icon": OUTPUT_ICONS[OutputType.ROLLBACK]},
        ),
        OutputType.DIRECTORY: RichStyle(
            color="cyan", frame=True, meta={"icon": OUTPUT_ICONS[OutputType.DIRECTORY]}
        ),
        OutputType.STATISTICS: RichStyle(
            color="grey58",
            frame=True,
            meta={"icon": OUTPUT_ICONS[OutputType.STATISTICS]},
        ),
        OutputType.CHEAP_MODEL: RichStyle(
            color="grey58",
            frame=True,
            meta={"icon": OUTPUT_ICONS[OutputType.CHEAP_MODEL]},
        ),
        OutputType.NORMAL_MODEL: RichStyle(
            color="bright_blue",
            frame=True,
            meta={"icon": OUTPUT_ICONS[OutputType.NORMAL_MODEL]},
        ),
        OutputType.SMART_MODEL: RichStyle(
            color="bright_magenta",
            bold=True,
            frame=True,
            meta={"icon": OUTPUT_ICONS[OutputType.SMART_MODEL]},
        ),
    }

    # 文字颜色映射
    _TEXT_COLORS = {
        OutputType.SYSTEM: "cyan",
        OutputType.CODE: "green",
        OutputType.RESULT: "grey70",
        OutputType.ERROR: "bright_red",
        OutputType.INFO: "grey70",
        OutputType.PLANNING: "magenta",
        OutputType.PROGRESS: "grey50",
        OutputType.SUCCESS: "bright_green",
        OutputType.WARNING: "bright_yellow",
        OutputType.DEBUG: "grey30",
        OutputType.USER: "bright_green",
        OutputType.TOOL: "green",
        OutputType.START: "bright_cyan",
        OutputType.TARGET: "bright_magenta",
        OutputType.STOP: "bright_red",
        OutputType.RETRY: "grey70",
        OutputType.ROLLBACK: "grey70",
        OutputType.DIRECTORY: "cyan",
        OutputType.STATISTICS: "grey58",
        OutputType.CHEAP_MODEL: "grey58",
        OutputType.NORMAL_MODEL: "bright_blue",
        OutputType.SMART_MODEL: "bright_magenta",
    }

    @staticmethod
    def _highlight_progress_text(
        text: str, output_type: OutputType, text_colors: Dict[OutputType, str]
    ) -> Text:
        """
        检测并高亮文本中的进度信息（如"第 X 轮"或"第 X/Y 轮"）。

        参数：
            text: 要处理的文本
            output_type: 输出类型
            text_colors: 颜色映射字典

        返回：
            Text: 格式化后的文本对象
        """
        progress_pattern = r"第\s*(\d+)(?:/(\d+))?\s*轮"
        if re.search(progress_pattern, text):
            # 包含进度信息，高亮数字
            parts = re.split(progress_pattern, text)
            colored_text = Text()
            for i, part in enumerate(parts):
                if i % 3 == 0:  # 普通文本
                    colored_text.append(
                        part,
                        style=RichStyle(
                            color=_safe_color_get(text_colors[output_type], "white")
                        ),
                    )
                elif i % 3 == 1:  # 第一个数字（当前轮次）
                    colored_text.append(
                        part,
                        style=RichStyle(
                            color=_safe_color_get(text_colors[output_type], "white"),
                            bold=True,
                        ),
                    )
                elif i % 3 == 2 and part:  # 第二个数字（总轮次，如果有）
                    colored_text.append(
                        f"/{part}",
                        style=RichStyle(
                            color=_safe_color_get(text_colors[output_type], "white")
                        ),
                    )
            return colored_text
        else:
            # 普通文本
            return Text(
                text,
                style=RichStyle(
                    color=_safe_color_get(text_colors[output_type], "white")
                ),
            )

    def emit(self, event: OutputEvent) -> None:
        # 章节输出
        if event.section is not None:
            # 使用带背景色和样式的Text替代Panel
            style_obj = self._SECTION_STYLES.get(
                event.output_type, RichStyle(color="white")
            )
            # 所有章节标题都靠左对齐
            text = Text(f"\n{event.section}\n", style=style_obj, justify="left")
            if get_pretty_output():
                console.print(text)
            else:
                console.print(Text(event.section, style=event.output_type.value))
            return

        # 普通内容输出
        lang = (
            event.lang
            if event.lang is not None
            else PrettyOutput._detect_language(event.text, default_lang="markdown")
        )

        content = Syntax(
            event.text,
            lang,
            theme="monokai",
            word_wrap=True,
            # 使用终端默认背景色
        )
        # 直接输出带背景色的内容，不再使用Panel包装
        agent_name = PrettyOutput._format(event.output_type, event.timestamp)
        header_text = Text(
            agent_name,
            style=RichStyle(color="grey58", dim=True),
        )
        if get_pretty_output():
            # 检测是否为多行文本，如果是则使用更好的格式化
            lines = event.text.split("\n")
            is_multiline = len(lines) > 1

            # 检测是否包含列表项（以数字、-、* 开头）
            is_list = any(
                line.strip().startswith(("- ", "* ", "• "))
                or (
                    line.strip()
                    and line.strip()[0].isdigit()
                    and ". " in line.strip()[:5]
                )
                for line in lines
            )

            # 检测是否包含缩进内容（可能是子项或代码块）
            has_indent = any(line.startswith(("   ", "  ", "\t")) for line in lines)

            if is_multiline and (is_list or has_indent):
                # 多行列表或缩进内容：第一行显示header，后续行使用缩进
                combined_text = Text()
                combined_text.append(header_text)
                combined_text.append(" ")

                # 第一行：检测并高亮进度信息；##/### 标题行使用醒目样式
                first_line = lines[0]
                if first_line.strip().startswith(("#", "##", "###")):
                    colored_first_line = Text(
                        first_line, style=RichStyle(bold=True, color="bright_cyan")
                    )
                else:
                    colored_first_line = self._highlight_progress_text(
                        first_line, event.output_type, self._TEXT_COLORS
                    )

                combined_text.append(colored_first_line)
                console.print(combined_text)

                # 后续行使用缩进，保持视觉层次；##/### 标题行加粗+亮青突出显示
                for line in lines[1:]:
                    if line.strip():  # 非空行
                        line_stripped = line.strip()
                        is_heading = line_stripped.startswith(
                            ("#", "##", "###", "####", "#####", "######")
                        )
                        # 检测列表项标记并适当格式化
                        is_list_item = line_stripped.startswith(("- ", "* ", "• ")) or (
                            line_stripped
                            and line_stripped[0].isdigit()
                            and ". " in line_stripped[:5]
                        )

                        # 如果已经是缩进的，保持原样；标题和列表项（1. / - * •）靠左不缩进，其余续行缩进
                        if line.startswith(("   ", "  ", "\t")):
                            display_line = line
                        elif is_heading or is_list_item:
                            display_line = line
                        else:
                            display_line = f"   {line}"

                        if is_heading:
                            indented_line = Text(
                                display_line,
                                style=RichStyle(bold=True, color="bright_cyan"),
                            )
                        else:
                            indented_line = Text(
                                display_line,
                                style=RichStyle(
                                    color=_safe_color_get(
                                        self._TEXT_COLORS[event.output_type], "white"
                                    ),
                                    dim=not is_list_item
                                    and line.startswith(
                                        ("   ", "  ", "\t")
                                    ),  # 已缩进的非列表项稍微变暗
                                ),
                            )
                        console.print(indented_line)
                    else:
                        console.print()  # 空行保持原样
            else:
                # 单行或简单多行：合并header和content；markdown 多行时对 ##/### 标题行突出显示
                combined_text = Text()
                combined_text.append(header_text)
                combined_text.append(" ")

                if lang == "markdown" and "\n" in event.text:
                    # 多行 markdown：首行与 header 同排，后续行逐行输出并高亮 ## 标题
                    lines = event.text.split("\n")
                    first_line = lines[0]
                    if first_line.strip().startswith(("#", "##", "###")):
                        combined_text.append(
                            Text(
                                first_line,
                                style=RichStyle(bold=True, color="bright_cyan"),
                            )
                        )
                    else:
                        colored_first = self._highlight_progress_text(
                            first_line, event.output_type, self._TEXT_COLORS
                        )
                        combined_text.append(colored_first)
                    console.print(combined_text)
                    for line in lines[1:]:
                        if line.strip().startswith(
                            ("#", "##", "###", "####", "#####", "######")
                        ):
                            console.print(
                                Text(
                                    line,
                                    style=RichStyle(bold=True, color="bright_cyan"),
                                )
                            )
                        elif line.strip():
                            colored_line = self._highlight_progress_text(
                                line, event.output_type, self._TEXT_COLORS
                            )
                            console.print(colored_line)
                        else:
                            console.print()
                else:
                    # 单行或非 markdown：沿用原逻辑
                    colored_content = self._highlight_progress_text(
                        event.text, event.output_type, self._TEXT_COLORS
                    )
                    combined_text.append(colored_content)
                    console.print(combined_text)
        else:
            console.print(content)
        if event.traceback or (
            event.output_type == OutputType.ERROR and is_print_error_traceback()
        ):
            try:
                console.print_exception()
            except Exception as e:
                console.print(f"Error: {e}")


# 模块级输出分发器（默认注册控制台后端）
_output_sinks: List[OutputSink] = [ConsoleOutputSink()]


def emit_output(event: OutputEvent) -> None:
    """向所有已注册的输出后端广播事件。"""
    for sink in list(_output_sinks):
        try:
            sink.emit(event)
        except Exception as e:
            # 后端故障不影响其他后端
            console.print(f"[输出后端错误] {sink.__class__.__name__}: {e}")


class PrettyOutput:
    """
    使用rich库格式化和显示富文本输出的类。

    提供以下方法：
    - 使用适当的样式格式化不同类型的输出
    - 代码块的语法高亮
    - 结构化内容的面板显示
    - 渐进显示的流式输出
    """

    # 语法高亮的语言映射
    _lang_map = {
        "Python": "python",
        "JavaScript": "javascript",
        "TypeScript": "typescript",
        "Java": "java",
        "C++": "cpp",
        "C#": "csharp",
        "Ruby": "ruby",
        "PHP": "php",
        "Go": "go",
        "Rust": "rust",
        "Bash": "bash",
        "HTML": "html",
        "CSS": "css",
        "SQL": "sql",
        "R": "r",
        "Kotlin": "kotlin",
        "Swift": "swift",
        "Scala": "scala",
        "Perl": "perl",
        "Lua": "lua",
        "YAML": "yaml",
        "JSON": "json",
        "XML": "xml",
        "Markdown": "markdown",
        "Text": "text",
        "Shell": "bash",
        "Dockerfile": "dockerfile",
        "Makefile": "makefile",
        "INI": "ini",
        "TOML": "toml",
    }

    @staticmethod
    def _detect_language(text: str, default_lang: str = "markdown") -> str:
        """
        检测给定文本的编程语言。

        参数：
            text: 要分析的文本
            default_lang: 如果检测失败，默认返回的语言

        返回：
            str: 检测到的语言名称
        """
        try:
            lexer = guess_lexer(text)
            detected_lang = lexer.name
            return PrettyOutput._lang_map.get(detected_lang, default_lang)
        except (ClassNotFound, Exception):
            return default_lang

    @staticmethod
    def _format(output_type: OutputType, timestamp: bool = True) -> str:
        """
        返回带时间戳前缀的Agent名字格式。

        参数：
            output_type: 输出类型（不再使用）
            timestamp: 是否包含时间戳

        返回：
            str: 包含时间戳和Agent名字的字符串
        """
        agent_info = get_agent_list()
        if not agent_info:
            return ""

        # 提取agent名字列表（去掉前面的数量标识）
        match = re.match(r"^\[(\d+)\](.+)$", agent_info)
        if match:
            count = match.group(1)
            agent_names = match.group(2).strip()
            # 为每个agent名字添加对应的emoji（根据其non_interactive状态）
            agent_names_with_emoji = []
            for name in agent_names.split(", "):
                name = name.strip()
                agent = get_agent(name)
                if agent and getattr(agent, "non_interactive", False):
                    emoji = "🔇"  # 非交互模式
                else:
                    emoji = "🔊"  # 交互模式
                agent_names_with_emoji.append(f"{name}{emoji}")
            agent_info = f"[{count}]{', '.join(agent_names_with_emoji)}"

        if timestamp:
            current_time = datetime.now().strftime("%H:%M:%S")
            # 使用更美观的时间戳格式，添加分隔符
            return f"⏰ {current_time} │ {agent_info}"
        else:
            return agent_info

    @staticmethod
    def _print(
        text: str,
        output_type: OutputType,
        timestamp: bool = True,
        lang: Optional[str] = None,
        traceback: bool = False,
    ) -> None:
        """
        使用样式和语法高亮打印格式化输出（已抽象为事件 + Sink 机制）。
        内部接口，不建议直接使用，请使用 auto_print 代替。
        保持对现有调用方的向后兼容，同时为TUI/日志等前端预留扩展点。
        """
        event = OutputEvent(
            text=text,
            output_type=output_type,
            timestamp=timestamp,
            lang=lang,
            traceback=traceback,
        )
        emit_output(event)

    @staticmethod
    def section(title: str, output_type: OutputType = OutputType.INFO) -> None:
        """
        在样式化面板中打印章节标题（通过事件 + Sink 机制分发）。
        """
        event = OutputEvent(
            text="",
            output_type=output_type,
            section=title,
        )
        emit_output(event)

    # Sink管理（为外部注册自定义后端预留）
    @staticmethod
    def add_sink(sink: OutputSink) -> None:
        """注册一个新的输出后端。"""
        _output_sinks.append(sink)

    @staticmethod
    def clear_sinks(keep_default: bool = True) -> None:
        """清空已注册的输出后端；可选择保留默认控制台后端。"""
        if keep_default:
            globals()["_output_sinks"] = [
                s for s in _output_sinks if isinstance(s, ConsoleOutputSink)
            ]
        else:
            _output_sinks.clear()

    @staticmethod
    def get_sinks() -> List[OutputSink]:
        """获取当前已注册的输出后端列表（副本）。"""
        return list(_output_sinks)

    @staticmethod
    def print_gradient_text(
        text: str, start_color: Tuple[int, int, int], end_color: Tuple[int, int, int]
    ) -> None:
        """打印带有渐变色彩的文本。

        Args:
            text: 要打印的文本
            start_color: 起始RGB颜色元组 (r, g, b)
            end_color: 结束RGB颜色元组 (r, g, b)
        """
        lines = text.strip("\n").split("\n")
        total_lines = len(lines)
        colored_lines = []
        for i, line in enumerate(lines):
            # 计算当前行的渐变颜色
            r = int(
                start_color[0] + (end_color[0] - start_color[0]) * i / (total_lines - 1)
            )
            g = int(
                start_color[1] + (end_color[1] - start_color[1]) * i / (total_lines - 1)
            )
            b = int(
                start_color[2] + (end_color[2] - start_color[2]) * i / (total_lines - 1)
            )

            # 使用ANSI转义序列设置颜色
            colored_lines.append(f"\033[38;2;{r};{g};{b}m{line}\033[0m")
        colored_text = Text(
            "\n".join(colored_lines), style=OutputType.TOOL.value, justify="left"
        )
        # 直接输出渐变文本，不再使用Panel包装
        console.print(colored_text)

    @staticmethod
    def auto_print(
        text: str, timestamp: bool = True, lang: Optional[str] = None
    ) -> None:
        """
        自动根据打印信息的前缀emoji判断类型并着色输出。

        支持的emoji前缀映射：
        - ⚠️ -> WARNING (黄色警告)
        - ❌ -> ERROR (红色错误)
        - ✅ -> SUCCESS (绿色成功)
        - ℹ️ -> INFO (青色信息)
        - 📋 -> PLANNING (紫色规划)
        - ⏳ -> PROGRESS (白色进度)
        - 🔍 -> DEBUG (灰色调试)
        - 🤖 -> SYSTEM (青色系统)
        - 📝 -> CODE (绿色代码)
        - ✨ -> RESULT (蓝色结果)
        - 👤 -> USER (绿色用户)
        - 🔧 -> TOOL (绿色工具)

        参数：
            text: 要打印的文本
            timestamp: 是否显示时间戳
            lang: 语言类型（用于语法高亮）
        """
        # 检测emoji前缀（使用统一的emoji映射）
        output_type = OutputType.INFO  # 默认类型
        detected_emoji = None
        for emoji, type_enum in EMOJI_TO_OUTPUT_TYPE.items():
            if text.startswith(emoji):
                output_type = type_enum
                detected_emoji = emoji
                break

        # 优化文本格式：确保emoji和文本之间有适当的间距
        if detected_emoji:
            # 如果emoji后没有空格，添加一个空格
            if len(text) > len(detected_emoji) and text[len(detected_emoji)] != " ":
                text = f"{detected_emoji} {text[len(detected_emoji) :].lstrip()}"

        # 如果打印的内容中有换行，就在要打印的内容开头添加一个换行
        if "\n" in text:
            text = f"\n{text}"

        # 使用现有的print方法进行着色输出
        PrettyOutput._print(
            text=text, output_type=output_type, timestamp=timestamp, lang=lang
        )

    @staticmethod
    def print_task_list_plan_status(summary: Dict[str, Any]) -> None:
        """以 Plan 风格打印待办事项列表，便于用户查看任务拆解与执行进度。

        格式示例：
          ✔  Plan 更新待办事项列表（2个待处理，1个进行中，1个已完成）
             ·已更新待办事项列表
               ⎿ ✔ 已完成的任务名
                 ☐ 待执行的任务名

        参数：
            summary: get_task_list_summary 返回的字典，需包含 pending, running,
                     completed, failed, abandoned, tasks（tasks 中每项含 task_name, status）
        """
        if not summary or "tasks" not in summary:
            return
        pending = summary.get("pending", 0)
        running = summary.get("running", 0)
        completed = summary.get("completed", 0)
        failed = summary.get("failed", 0)
        abandoned = summary.get("abandoned", 0)
        parts = [f"{pending}个待处理", f"{running}个进行中", f"{completed}个已完成"]
        if failed:
            parts.append(f"{failed}个失败")
        if abandoned:
            parts.append(f"{abandoned}个已放弃")
        count_str = "，".join(parts)
        line1 = f"  ✔  Plan 更新待办事项列表（{count_str}）"
        line2 = "     ·已更新待办事项列表"

        def _task_sort_key(t: Dict[str, Any]) -> int:
            tid = t.get("task_id", "")
            try:
                return int(tid.split("-")[1])
            except (IndexError, ValueError):
                return 999999

        tasks = sorted(summary["tasks"], key=_task_sort_key)
        completed_status = "completed"
        lines = [line1, line2]
        for i, t in enumerate(tasks):
            name = (t.get("task_name") or "").strip()
            status = (t.get("status") or "").strip().lower()
            mark = "✔ " if status == completed_status else "☐ "
            # 第一项带树形符 ⎿，后续项仅缩进（与示例格式一致）
            prefix = "       ⎿ " if i == 0 else "         "
            lines.append(f"{prefix}{mark}{name}")

        block = "\n".join(lines)
        PrettyOutput._print(
            text=f"\n{block}",
            output_type=OutputType.PLANNING,
            timestamp=True,
            lang=None,
        )

    @staticmethod
    def print_truncated_with_expand_hint(
        full_content: str,
        title: Optional[str] = None,
        visible_before: int = 12,
        visible_after: int = 30,
        max_lines: int = 60,
        output_type: OutputType = OutputType.RESULT,
        expand_hint: str = "输入 Ctrl+R 查看全部",
        trigger_context: Optional[str] = None,
        purpose: Optional[str] = None,
    ) -> None:
        """对非关键长内容做部分显示，其余隐藏，完整内容可通过 Ctrl+R 查看。

        purpose: 历史列表中显示的摘要（是什么信息、做什么用），便于用户区分。
        """
        lines = full_content.splitlines()
        total = len(lines)
        if total <= max_lines:
            PrettyOutput._print(
                text=full_content, output_type=output_type, timestamp=True, lang=None
            )
            jarvis_globals.last_truncated_full_content = None
            jarvis_globals.last_truncated_title = None
            return
        # 需要折叠显示：写入历史列表（供 Ctrl+R 历史查看）并保留最近一条
        PrettyOutput.push_truncated_to_history(
            full_content,
            title,
            trigger_context=trigger_context,
            purpose=purpose,
        )
        jarvis_globals.last_truncated_full_content = full_content
        jarvis_globals.last_truncated_title = title
        history = getattr(jarvis_globals, "truncated_history", [])
        index = len(history)  # 本条在历史中的序号（1-based 即 index）
        head = visible_before
        tail = visible_after
        if head + tail >= total:
            head = max(1, total - tail)
        hidden_count = total - head - tail
        mid_hint = f"\n... 前 {hidden_count} 行已隐藏 ...（{expand_hint}，对应索引为：{index}）\n"
        partial_lines = lines[:head] + [mid_hint.strip()] + lines[-tail:]
        partial_text = "\n".join(partial_lines)
        PrettyOutput._print(
            text=partial_text, output_type=output_type, timestamp=True, lang=None
        )

    @staticmethod
    def show_last_truncated_full() -> bool:
        """显示上次通过 print_truncated_with_expand_hint 保存的完整内容。

        供 Ctrl+R 快捷键调用。若有内容则用当前控制台输出并返回 True，否则返回 False。
        
        注意：显示后不会清除保存的内容，用户可以多次查看。
        """
        full = getattr(
            jarvis_globals, "last_truncated_full_content", None
        )
        title = getattr(jarvis_globals, "last_truncated_title", None)
        if not full:
            return False
        if title:
            PrettyOutput.auto_print(f"\n📄 完整内容：{title}")
            PrettyOutput.auto_print("─" * 80)
        PrettyOutput._print(
            text=full,
            output_type=OutputType.RESULT,
            timestamp=False,  # 不显示时间戳，避免重复
            lang=None,
        )
        if title:
            PrettyOutput.auto_print("─" * 80)
        # 不清除保存的内容，允许用户多次查看
        return True

    @staticmethod
    def push_truncated_to_history(
        full_content: str,
        title: Optional[str] = None,
        trigger_context: Optional[str] = None,
        purpose: Optional[str] = None,
    ) -> None:
        """将一次折叠的完整内容与摘要加入历史列表，供 Ctrl+R 历史查看界面使用。

        purpose: 隐藏摘要的完整描述（是什么信息、做什么用），优先于 trigger_context/title。
        trigger_context: 触发背景，与 title 组合成摘要（当 purpose 未提供时）。
        """
        if purpose and purpose.strip():
            summary = purpose.strip()
        elif trigger_context and title:
            summary = f"{trigger_context} · {title}"
        elif trigger_context:
            summary = trigger_context
        elif title:
            summary = title
        else:
            summary = ""
        if not summary and full_content:
            first_line = full_content.splitlines()[0].strip() if full_content else ""
            summary = (first_line[:60] + "…") if len(first_line) > 60 else first_line
        history = getattr(jarvis_globals, "truncated_history", None)
        if history is None:
            return
        history.append((full_content, summary or "(无标题)"))
        while len(history) > TRUNCATED_HISTORY_MAX_SIZE:
            history.pop(0)

    @staticmethod
    def get_truncated_history() -> List[Tuple[str, str]]:
        """返回折叠历史列表，每项为 (完整内容, 摘要)。"""
        return getattr(jarvis_globals, "truncated_history", [])

    @staticmethod
    def show_truncated_item_by_index(one_based_index: int) -> bool:
        """根据序号（从 1 开始）显示历史中对应项的完整内容。"""
        history = PrettyOutput.get_truncated_history()
        if one_based_index < 1 or one_based_index > len(history):
            return False
        full_content, summary = history[one_based_index - 1]
        if summary:
            PrettyOutput.auto_print(f"\n📄 完整内容：{summary}")
            PrettyOutput.auto_print("─" * 80)
        PrettyOutput._print(
            text=full_content,
            output_type=OutputType.RESULT,
            timestamp=False,
            lang=None,
        )
        if summary:
            PrettyOutput.auto_print("─" * 80)
        PrettyOutput.auto_print(
            "[dim]（已显示完毕，可继续输入或按 Ctrl+J/Ctrl+D 确认）[/dim]"
        )
        return True

    @staticmethod
    def _normalize_markdown_headings(content: str) -> str:
        """将内容中的标题行规范为 # / ## 格式，便于左对齐与层级显示。

        - 以「数字. 」开头的行（如 1. xxx、2. xxx）规范为二级标题：## 1. xxx
        - 首个非空、非列表、非已有 # 的短行视为一级标题，补 #
        """
        lines = content.splitlines()
        out: List[str] = []
        seen_first_heading = False
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if not stripped:
                out.append(line)
                continue
            if stripped.startswith("#"):
                seen_first_heading = True
                out.append(line)
                continue
            # 以「数字.」开头（可有可无空格）→ 二级标题 ## N. xxx
            if re.match(r"^\d+\.\s*", stripped):
                indent = line[: len(line) - len(stripped)]
                out.append(indent + "## " + stripped)
                continue
            # 首个像标题的短行（无 #、非列表、非数字开头）→ 一级标题 #
            if not seen_first_heading and 3 <= len(stripped) <= 120:
                if not re.match(r"^[\d\-\*\]\>]", stripped):
                    indent = line[: len(line) - len(stripped)]
                    out.append(indent + "# " + stripped)
                    seen_first_heading = True
                    continue
            out.append(line)
        return "\n".join(out)

    @staticmethod
    def print_markdown(
        content: str,
        title: Optional[str] = None,
        border_style: str = "bright_blue",
        theme: str = "monokai",
        highlight_headings: bool = False,
    ) -> None:
        """
        使用Panel显示带markdown语法高亮的内容。

        参数：
            content: 要显示的markdown格式内容
            title: Panel标题（可选）
            border_style: 边框样式（默认"bright_blue"）
            theme: markdown高亮主题（默认"monokai"）
            highlight_headings: 为True时使用Markdown渲染，标题靠左、## 等突出显示（默认False）
        """
        from rich.panel import Panel

        if highlight_headings:
            from rich.align import Align
            from rich.console import Console as RichConsole
            from rich.console import ConsoleOptions
            from rich.console import RenderResult
            from rich.markdown import Markdown
            from rich.markdown import Heading
            from rich.theme import Theme

            # 自定义 Heading：强制所有级别标题左对齐（Rich 默认 h1 居中）
            class _LeftHeading(Heading):
                def __rich_console__(
                    self, console, options: ConsoleOptions
                ) -> RenderResult:
                    text = self.text.copy()
                    text.justify = "left"
                    yield text

            class _LeftMarkdown(Markdown):
                elements = {**Markdown.elements, "heading_open": _LeftHeading}

            # 规范标题格式（数字开头→## N. xxx），便于统一左对齐与层级
            content = PrettyOutput._normalize_markdown_headings(content)
            # 使用自定义 Markdown 渲染，标题全部靠左
            renderable = Align.left(_LeftMarkdown(content))
            heading_theme = Theme(
                {
                    "markdown.h1": "bold bright_cyan",
                    "markdown.h2": "bold bright_cyan",
                    "markdown.h3": "bold bright_cyan",
                    "markdown.h4": "bold cyan",
                    "markdown.h5": "bold cyan",
                    "markdown.h6": "bold cyan",
                }
            )
            panel = Panel(
                renderable,
                title=title,
                border_style=border_style,
                expand=True,
                title_align="left",
            )
            RichConsole(theme=heading_theme).print(panel)
            return
        else:
            renderable = Syntax(content, "markdown", theme=theme, word_wrap=True)

        panel = Panel(
            renderable,
            title=title,
            border_style=border_style,
            expand=True,
            title_align="left",
        )
        console.print(panel)

    @staticmethod
    def show_thinking_until(
        stop_event, interval: float = 0.4, delay_seconds: float = 3.0
    ) -> None:
        """在等待期间显示「思考中」+ 动态点，直到 stop_event 被设置。

        仅当持续 delay_seconds 秒以上无结果时才显示，避免短暂等待时刷屏。
        使用单行文本、无边框，字体不加粗。

        参数:
            stop_event: threading.Event，当阻塞操作完成时调用 set()
            interval: 动态点刷新间隔（秒）
            delay_seconds: 超过该秒数无输出后才显示思考中（默认 3 秒）
        """
        import threading
        import time
        from rich.live import Live
        from rich.text import Text

        if not (hasattr(stop_event, "wait") and hasattr(stop_event, "set")):
            return
        # 先等待 delay_seconds 秒，若期间已完成则直接返回，不显示思考中
        if stop_event.wait(timeout=delay_seconds):
            return
        thinking_dots = 0
        text_content = Text("思考中.", style="bright_cyan")
        with Live(text_content, refresh_per_second=4, transient=True) as live:
            while not stop_event.wait(interval):
                thinking_dots = (thinking_dots + 1) % 4
                dots_str = "." * (thinking_dots + 1)
                text_content = Text(f"思考中{dots_str}", style="bright_cyan")
                live.update(text_content)

    @staticmethod
    def stream_chat_with_panel(
        chat_iterator,
        title: str,
        status_message: str,
        get_used_token_count,
        get_conversation_turn,
        get_platform_max_input_token_count,
        get_context_token_count,
        append_session_history,
        start_time: float,
        message: str,
        max_output: int = 0,
        check_interrupt=None,
        panel_lock=None,
    ) -> Tuple[str, float]:
        """使用面板显示流式聊天输出。

        参数:
            chat_iterator: 聊天迭代器
            title: 面板标题
            status_message: 状态消息
            get_used_token_count: 获取已使用 token 数的函数
            get_conversation_turn: 获取对话轮次的函数
            get_platform_max_input_token_count: 获取平台最大输入 token 数的函数
            get_context_token_count: 获取上下文 token 数的函数
            append_session_history: 添加会话历史的函数
            start_time: 开始时间
            message: 用户消息
            max_output: 最大输出长度
            check_interrupt: 检查中断的函数
            panel_lock: 面板锁

        返回:
            Tuple[str, float]: (响应内容, 耗时)
        """
        import threading
        import time
        from rich.live import Live
        from rich.panel import Panel
        from rich.text import Text
        from rich import box
        from jarvis.jarvis_utils.globals import get_interrupt
        from jarvis.jarvis_utils.config import is_immediate_abort

        # 用于后台线程存放首个 chunk 或 StopIteration
        first_chunk_result = [None]
        stop_iteration_flag = [False]

        def _fetch_first_chunk():
            try:
                chunk = next(chat_iterator)
                first_chunk_result[0] = chunk if chunk else ""
            except StopIteration:
                stop_iteration_flag[0] = True
                first_chunk_result[0] = None

        fetch_thread = threading.Thread(target=_fetch_first_chunk, daemon=True)
        fetch_thread.start()

        # 仅当持续 3 秒以上无首个 chunk 时才显示「思考中」，单行、无边框、不加粗
        thinking_delay = 3.0
        elapsed = 0.0
        check_interval = 0.2
        while elapsed < thinking_delay and fetch_thread.is_alive():
            time.sleep(check_interval)
            elapsed += check_interval
        if fetch_thread.is_alive():
            thinking_dots = 0
            text_content = Text("思考中.", style="bright_cyan")
            with Live(text_content, refresh_per_second=4, transient=True) as live:
                while fetch_thread.is_alive():
                    thinking_dots = (thinking_dots + 1) % 4
                    dots_str = "." * (thinking_dots + 1)
                    text_content = Text(f"思考中{dots_str}", style="bright_cyan")
                    live.update(text_content)
                    time.sleep(0.4)
        fetch_thread.join()

        if stop_iteration_flag[0]:
            append_session_history(message, "")
            return "", time.time() - start_time

        first_chunk = first_chunk_result[0] or ""
        text_content = Text(overflow="fold")
        panel = Panel(
            text_content,
            title=None,
            subtitle=None,
            border_style="cyan",
            box=box.ROUNDED,
            expand=True,
        )

        response = ""
        last_subtitle_update_time = time.time()
        subtitle_update_interval = 1  # subtitle 更新间隔（秒）
        update_count = 0  # 更新计数器

        def _update_panel_subtitle_with_token(
            panel_obj: Panel, response_text: str, is_completed: bool = False
        ):
            """更新面板的 subtitle，显示 token 信息。"""
            try:
                threshold = 100  # 默认阈值
                try:
                    max_input = get_platform_max_input_token_count()
                    current_context = get_context_token_count()
                    threshold = max_input - current_context if max_input else 100
                except Exception:
                    pass

                current_time = time.time()
                duration = current_time - start_time

                try:
                    used_tokens = get_used_token_count()
                    conversation_turn = get_conversation_turn()

                    if is_completed:
                        panel_obj.subtitle = (
                            f"[bold green]✓ {current_time:.0f} | "
                            f"({conversation_turn}/{threshold}) | "
                            f"tokens: {used_tokens} | "
                            f"耗时: {duration:.2f}秒[/bold green]"
                        )
                    else:
                        panel_obj.subtitle = (
                            f"[yellow]{current_time:.0f} | "
                            f"({conversation_turn}/{threshold}) | "
                            f"tokens: {used_tokens} | "
                            f"正在回答... (按 Ctrl+C 中断)[/yellow]"
                        )
                except Exception:
                    # 如果获取 token 信息失败，使用简化版本
                    if is_completed:
                        panel_obj.subtitle = (
                            f"[bold green]✓ {current_time:.0f} | "
                            f"耗时: {duration:.2f}秒[/bold green]"
                        )
                    else:
                        panel_obj.subtitle = (
                            f"[yellow]{current_time:.0f} | "
                            f"正在回答... (按 Ctrl+C 中断)[/yellow]"
                        )
            except Exception:
                # 如果更新 subtitle 失败，使用默认值
                current_time = time.time()
                duration = current_time - start_time
                if is_completed:
                    panel_obj.subtitle = (
                        f"[bold green]✓ 耗时: {duration:.2f}秒[/bold green]"
                    )
                else:
                    panel_obj.subtitle = (
                        f"[yellow]正在回答... (按 Ctrl+C 中断)[/yellow]"
                    )

        with Live(panel, refresh_per_second=4, transient=True) as live:

            def _update_panel_content(content: str, update_subtitle: bool = False):
                nonlocal response, last_subtitle_update_time, update_count, text_content, panel

                # 在锁外进行文本拼接和wrap计算，避免与console内部锁冲突
                # 获取当前文本并添加新内容，创建新的 Text 对象
                # 避免在原 Text 对象上调用 append()，防止与 Live 内部线程并发访问导致不一致
                current_text = text_content.plain
                new_content = current_text + content
                new_text_obj = Text(new_content, overflow="fold", style="bright_white")
                update_count += 1

                # Scrolling Logic - 只在内容超过一定行数时才应用滚动
                max_text_height = console.height - 5
                if max_text_height <= 0:
                    max_text_height = 1

                lines = new_text_obj.wrap(
                    console,
                    console.width - 4 if console.width > 4 else 1,
                )

                # 只在内容超过最大高度时才截取，减少不必要的操作
                final_text = new_text_obj
                if len(lines) > max_text_height:
                    # 创建新的Text对象，避免直接修改plain属性导致内部状态不一致
                    # 这确保了Rich内部spans列表与文本内容保持同步
                    final_text = Text(
                        "\n".join([line.plain for line in lines[-max_text_height:]]),
                        overflow="fold",
                    )

                # 使用锁保护 panel 更新，避免与 Live 内部线程冲突
                if panel_lock:
                    with panel_lock:
                        # 在锁内只更新text_content和panel
                        text_content = final_text

                        # 重建panel对象，确保panel始终引用最新的text_content
                        # 这样无论内容是否超出高度，流式输出都能正常刷新
                        panel = Panel(
                            text_content,
                            title=None,
                            subtitle=None,
                            border_style="cyan",
                            box=box.ROUNDED,
                            expand=True,
                        )

                        # 只在需要时更新 subtitle（减少更新频率，避免重复渲染标题）
                        # 策略：每 10 次内容更新或每 3 秒更新一次 subtitle
                        current_time = time.time()
                        should_update_subtitle = (
                            update_subtitle
                            or update_count % 10 == 0  # 每 10 次更新一次
                            or (current_time - last_subtitle_update_time)
                            >= subtitle_update_interval
                        )

                        if should_update_subtitle:
                            _update_panel_subtitle_with_token(
                                panel, response, is_completed=False
                            )
                            last_subtitle_update_time = current_time

                        # 更新 panel（只更新内容，subtitle 更新频率已降低）
                        # 添加异常处理，防止 rich 内部线程冲突导致的 IndexError
                        try:
                            live.update(panel)
                        except (IndexError, RuntimeError):
                            # 忽略 rich 内部错误，避免影响主流程
                            # 这些错误通常是由于 Live 内部线程与主线程的时序冲突导致的
                            pass
                else:
                    # 如果没有提供 panel_lock，直接更新
                    text_content = final_text
                    panel = Panel(
                        text_content,
                        title=None,
                        subtitle=None,
                        border_style="cyan",
                        box=box.ROUNDED,
                        expand=True,
                    )

                    current_time = time.time()
                    should_update_subtitle = (
                        update_subtitle
                        or update_count % 10 == 0
                        or (current_time - last_subtitle_update_time)
                        >= subtitle_update_interval
                    )

                    if should_update_subtitle:
                        _update_panel_subtitle_with_token(
                            panel, response, is_completed=False
                        )
                        last_subtitle_update_time = current_time

                    try:
                        live.update(panel)
                    except (IndexError, RuntimeError):
                        pass

            # Process first chunk
            response += first_chunk
            if first_chunk:
                _update_panel_content(
                    first_chunk, update_subtitle=True
                )  # 第一次更新时更新 subtitle

            # 缓存机制：降低更新频率，减少界面闪烁
            buffer = ""
            last_update_time = time.time()
            update_interval = 1
            min_buffer_size = 1

            def _flush_buffer():
                nonlocal buffer, last_update_time
                if buffer:
                    _update_panel_content(buffer)
                    buffer = ""
                    last_update_time = time.time()

            # Process rest of the chunks
            for s in chat_iterator:
                if not s:
                    continue
                response += s
                buffer += s

                current_time = time.time()
                should_update = (
                    len(buffer) >= min_buffer_size
                    or (current_time - last_update_time) >= update_interval
                )

                if should_update:
                    _flush_buffer()

                # 检查中断
                try:
                    if is_immediate_abort() and (check_interrupt and check_interrupt()):
                        _flush_buffer()
                        append_session_history(message, response)
                        return response, time.time() - start_time
                except Exception:
                    pass

            _flush_buffer()
            # 在结束前，将面板内容替换为完整响应，确保最后一次渲染的 panel 显示全部内容

        return response, time.time() - start_time
