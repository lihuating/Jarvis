# -*- coding: utf-8 -*-
import os
import re
import subprocess
from typing import Any
from typing import List
from typing import Optional
from typing import Tuple

from jarvis.jarvis_utils.config import get_replace_map
from jarvis.jarvis_utils.output import PrettyOutput
from rich.table import Table
from rich.console import Console

# 模型组切换相关导入
from jarvis.jarvis_platform.registry import PlatformRegistry
from jarvis.jarvis_utils.config import get_llm_group
from jarvis.jarvis_utils.config import set_llm_group
from jarvis.jarvis_utils.config import get_global_config_data
from jarvis.jarvis_utils.embedding import get_context_token_count


# 辅助函数：获取全局配置数据（避免导入时绑定问题）
def _get_global_config() -> Any:
    """获取全局配置数据的辅助函数

    使用函数调用而不是直接导入，避免在 set_global_config_data()
    重新赋值后使用旧引用。
    """
    return get_global_config_data()


def _get_rule_content(rule_name: str) -> str | None:
    """获取规则内容

    参数:
        rule_name: 规则名称

    返回:
        str | None: 规则内容，如果未找到则返回 None
    """
    try:
        import os

        from jarvis.jarvis_agent.rules_manager import RulesManager

        # 使用当前工作目录作为root_dir
        rules_manager = RulesManager(root_dir=os.getcwd())
        rule_content = rules_manager.get_named_rule(rule_name)

        if rule_content:
            # 尝试查找规则文件路径
            rule_file_path = _find_rule_file_path(rules_manager, rule_name)
            if rule_file_path:
                # 在规则内容前添加路径注释
                path_comment = f"<!-- 规则文件路径: {rule_file_path} -->\n"
                return path_comment + rule_content

        return rule_content
    except ImportError:
        return None


def _find_rule_file_path(rules_manager: Any, rule_name: str) -> str | None:
    """查找规则文件的绝对路径

    参数:
        rules_manager: RulesManager 实例
        rule_name: 规则名称

    返回:
        str | None: 规则文件绝对路径，如果未找到则返回 None
    """
    import os

    try:
        # 按优先级查找规则文件
        # 优先级 1: 项目 rules.yaml 文件
        project_rules_yaml = os.path.join(
            rules_manager.root_dir, ".jarvis", "rules.yaml"
        )
        if os.path.exists(project_rules_yaml):
            import yaml

            with open(project_rules_yaml, "r", encoding="utf-8") as f:
                rules = yaml.safe_load(f) or {}
            if rule_name in rules:
                # 从 rules.yaml 读取的规则，文件路径就是 yaml 文件路径
                return os.path.abspath(project_rules_yaml)

        # 优先级 2: 项目 rules 目录
        project_rules_dir = os.path.join(rules_manager.root_dir, ".jarvis", "rules")
        if os.path.exists(project_rules_dir) and os.path.isdir(project_rules_dir):
            rule_file = os.path.join(project_rules_dir, rule_name + ".md")
            if os.path.exists(rule_file):
                return os.path.abspath(rule_file)

        # 优先级 3: 全局 rules.yaml 文件
        from jarvis.jarvis_utils.config import get_data_dir

        global_rules_yaml = os.path.join(get_data_dir(), "rules.yaml")
        if os.path.exists(global_rules_yaml):
            import yaml

            with open(global_rules_yaml, "r", encoding="utf-8") as f:
                rules = yaml.safe_load(f) or {}
            if rule_name in rules:
                return os.path.abspath(global_rules_yaml)

        # 优先级 4: 全局 rules 目录
        global_rules_dir = os.path.join(get_data_dir(), "rules")
        if os.path.exists(global_rules_dir) and os.path.isdir(global_rules_dir):
            rule_file = os.path.join(global_rules_dir, rule_name + ".md")
            if os.path.exists(rule_file):
                return os.path.abspath(rule_file)

        # 优先级 5: 中心规则仓库
        if rules_manager.central_repo_path and os.path.exists(
            rules_manager.central_repo_path
        ):
            central_rules_dir = os.path.join(rules_manager.central_repo_path, "rules")
            if os.path.exists(central_rules_dir) and os.path.isdir(central_rules_dir):
                rule_file = os.path.join(central_rules_dir, rule_name + ".md")
                if os.path.exists(rule_file):
                    return os.path.abspath(rule_file)
            else:
                rule_file = os.path.join(
                    rules_manager.central_repo_path, rule_name + ".md"
                )
                if os.path.exists(rule_file):
                    return os.path.abspath(rule_file)

        # 优先级 6: 内置规则
        from jarvis.jarvis_utils.template_utils import _get_builtin_dir

        builtin_dir = _get_builtin_dir()
        if builtin_dir:
            # 在 builtin/rules 目录中查找
            from pathlib import Path

            builtin_rules_dir = builtin_dir / "rules"
            if builtin_rules_dir.exists() and builtin_rules_dir.is_dir():
                builtin_rule_file: Path = builtin_rules_dir / (rule_name + ".md")
                if builtin_rule_file.exists() and builtin_rule_file.is_file():
                    return str(builtin_rule_file.absolute())

            # 在 builtin/rules/testing 目录中查找
            testing_rules_dir = builtin_rules_dir / "testing"
            if testing_rules_dir.exists() and testing_rules_dir.is_dir():
                builtin_rule_file = testing_rules_dir / (rule_name + ".md")
                if builtin_rule_file.exists() and builtin_rule_file.is_file():
                    return str(builtin_rule_file.absolute())

        return None
    except Exception:
        return None


_BTW_SYSTEM_PROMPT = (
    "你是 Jarvis 的旁路问答助手。用户正在主会话中执行另一项核心任务，此处仅顺带提出一个独立问题（BTW）。\n"
    "约束：\n"
    "- 你没有主会话的对话历史；请只根据用户本条消息作答，不要臆测上文或主任务内容。\n"
    "- 不要延续、修改或依赖主任务中的代码/计划；仅回答本条问题。\n"
    "- 若必须依赖主会话才有的信息，请简短说明并建议回到主流程补充背景。\n"
    "- 回答简洁、直接。"
)

_BTW_CODE_AGENT_TASK_PREFIX = (
    "[BTW 旁路任务] 与主会话的对话历史无关，仅处理本条说明或操作需求；"
    "若属于概念/命令解释可直接作答；需要查仓库或跑命令时再使用工具。\n\n"
)


def _normalize_btw_question(text: str) -> str:
    """去掉补全用的前导 @ 及空白，避免 `\\@'<BTW>'` 形式残留 @。"""
    s = (text or "").strip()
    s = re.sub(r"^@+\s*", "", s).strip()
    return s


def _run_btw_isolated_chat(user_question: str) -> None:
    """使用临时 LLM 实例回答 BTW（jvs 或 CodeAgent 失败回退），不把问答写入主 agent 的模型上下文。

    说明：stream_chat_with_panel 使用 transient Live，结束后面板会被清屏，因此必须在流结束后
    再 print_markdown 固化可见输出。
    """
    import time

    from jarvis.jarvis_utils.embedding import get_context_token_count
    from jarvis.jarvis_utils.globals import get_interrupt

    reg = PlatformRegistry.get_global_platform_registry()
    plat = reg.create_platform(platform_type="normal", silent=True)
    if plat is None:
        plat = reg.create_platform(platform_type="cheap", silent=True)
    if plat is None:
        PrettyOutput.auto_print("⚠️ BTW：无法创建临时模型实例，请检查 LLM 配置。")
        return

    plat.agent = None
    plat.set_system_prompt(_BTW_SYSTEM_PROMPT)
    plat.set_suppress_output(False)
    start = time.time()
    msg = user_question.strip()
    if not msg:
        PrettyOutput.auto_print("（BTW 内容为空，已跳过）")
        return

    def _noop_append(_u: str, _r: str) -> None:
        return

    out = ""
    try:
        out, _dur = PrettyOutput.stream_chat_with_panel(
            chat_iterator=plat.chat(msg),
            title="BTW",
            status_message="💬 BTW（独立问答，不写入主会话上下文）· 思考中...",
            get_used_token_count=plat.get_used_token_count,
            get_conversation_turn=plat.get_conversation_turn,
            get_platform_max_input_token_count=plat._get_platform_max_input_token_count,
            get_context_token_count=get_context_token_count,
            append_session_history=_noop_append,
            start_time=start,
            message=msg,
            max_output=0,
            check_interrupt=get_interrupt,
            panel_lock=plat._panel_lock,
        )
    except Exception as e:
        PrettyOutput.auto_print(f"⚠️ BTW 失败: {e}")
        return

    out = (out or "").strip()
    if out:
        PrettyOutput.print_markdown(
            out,
            title="💬 BTW 回复（未写入主会话上下文）",
            border_style="dim",
            highlight_headings=True,
        )


def _run_btw_child_code_agent(parent_agent: Any, side_q: str) -> None:
    """在独立 CodeAgent 子实例中跑完 jca 流程（工具、run_loop 输出方式），不合并回父 agent 模型历史。"""
    from jarvis.jarvis_code_agent.code_agent import CodeAgent

    use_tools: List[str] = []
    try:
        parent_registry = parent_agent.get_tool_registry()
        if parent_registry:
            for t in parent_registry.get_all_tools():
                if isinstance(t, dict) and t.get("name"):
                    use_tools.append(str(t["name"]))
    except Exception:
        pass

    forbidden_tools = frozenset({"sub_agent", "sub_code_agent"})
    append_tools = None
    try:
        base_tools = frozenset({"execute_script", "read_code", "edit_file"})
        if use_tools:
            extras = [
                t for t in use_tools if t not in base_tools and t not in forbidden_tools
            ]
            append_tools = ",".join(extras) if extras else None
    except Exception:
        append_tools = None

    tool_group = getattr(parent_agent, "tool_group", None)
    rule_names = None
    try:
        loaded = getattr(parent_agent, "loaded_rule_names", None)
        if loaded:
            rule_names = ",".join(loaded)
    except Exception:
        rule_names = None

    try:
        code_agent = CodeAgent(
            name="BTW",
            need_summary=False,
            append_tools=append_tools,
            tool_group=tool_group,
            non_interactive=True,
            rule_names=rule_names,
            disable_review=True,
            use_methodology=False,
            use_analysis=False,
        )
        # 标记为旁路任务：run_loop 内自动收尾，不占用主会话上下文，也不弹出「回车结束」等待
        code_agent.btw_side_task = True
    except SystemExit as se:
        raise RuntimeError(
            f"初始化 BTW 子 CodeAgent 失败（可能未配置 git 或非 git 目录）: {se}"
        ) from se

    try:
        if use_tools:
            filtered = [t for t in use_tools if t not in forbidden_tools]
            if filtered:
                code_agent.set_use_tools(filtered)
    except Exception:
        pass

    task = _BTW_CODE_AGENT_TASK_PREFIX + side_q
    code_agent.run(task, "", "")


def _run_btw_dispatch(agent: Any, side_q: str) -> None:
    """jca：走独立 CodeAgent 全流程；失败或非代码代理：走临时模型轻量问答。"""
    side_q = _normalize_btw_question(side_q)
    if not side_q:
        PrettyOutput.auto_print("（BTW 内容为空，已跳过）")
        return
    if hasattr(agent, "git_manager"):
        try:
            _run_btw_child_code_agent(agent, side_q)
        except Exception as e:
            PrettyOutput.auto_print(f"⚠️ BTW（CodeAgent 子会话）不可用：{e}")
            _run_btw_isolated_chat(side_q)
    else:
        _run_btw_isolated_chat(side_q)


def builtin_input_handler(user_input: str, agent_: Any) -> Tuple[str, bool]:
    """
    处理内置的特殊输入标记，并追加相应的提示词

    参数：
        user_input: 用户输入
        agent: 代理对象

    返回：
        Tuple[str, bool]: 处理后的输入和是否需要进一步处理
    """
    from jarvis.jarvis_agent import Agent

    agent: Agent = agent_
    # 以 ! 开头：将后续输入直接作为 shell 命令执行
    stripped = user_input.strip()
    if stripped.startswith("!"):
        cmd = stripped[1:].strip()
        # 去掉 JARVIS-NOCONFIRM 等注释，得到实际命令
        if " # " in cmd:
            cmd = cmd.split(" # ")[0].strip()
        if cmd:
            # Ctrl+T 等会启动交互式 shell（如 env terminal=1 bash），需连接终端才能正常使用
            is_interactive_shell = (
                "terminal" in cmd  # Ctrl+T 启动的子 shell（含 terminal=1 或 terminal='1'）
                or cmd.strip().rstrip("&").strip() in ("bash", "zsh", "fish", "sh")
            )
            try:
                if is_interactive_shell:
                    result = subprocess.run(
                        cmd,
                        shell=True,
                        stdin=None,
                        stdout=None,
                        stderr=None,
                        cwd=os.getcwd(),
                    )
                    if result.returncode != 0:
                        PrettyOutput.auto_print(f"[退出码 {result.returncode}]")
                else:
                    result = subprocess.run(
                        cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=300,
                        cwd=os.getcwd(),
                    )
                    if result.stdout:
                        PrettyOutput.auto_print(result.stdout)
                    if result.stderr:
                        PrettyOutput.auto_print(result.stderr)
                    if result.returncode != 0 and not result.stderr and not result.stdout:
                        PrettyOutput.auto_print(f"[退出码 {result.returncode}]")
            except subprocess.TimeoutExpired:
                PrettyOutput.auto_print("⚠️ 命令执行超时（300秒）")
            except Exception as e:
                PrettyOutput.auto_print(f"⚠️ 执行命令失败: {e}")
            return "", True
        return "", True
    # 查找特殊标记
    special_tags = re.findall(r"'<([^>]+)>'", user_input)

    if not special_tags:
        return user_input, False

    # 获取替换映射表
    replace_map = get_replace_map()
    processed_tag = set()
    add_on_prompt = ""
    modified_input = user_input

    # 优先处理Pin标记
    if "Pin" in special_tags:
        pin_marker = "'<Pin>'"
        pin_index = modified_input.find(pin_marker)

        if pin_index != -1:
            # 分割为Pin标记前和Pin标记后的内容
            before_pin = modified_input[:pin_index]
            after_pin = modified_input[pin_index + len(pin_marker) :]

            # 将Pin标记之后的内容追加到pin_content
            after_pin_stripped = after_pin.strip()
            if after_pin_stripped:
                if agent.pin_content:
                    agent.pin_content += "\n" + after_pin_stripped
                else:
                    agent.pin_content = after_pin_stripped
                PrettyOutput.auto_print(f"📌 已固定内容: {after_pin_stripped[:50]}...")

            # 移除Pin标记，保留前后内容
            modified_input = before_pin + after_pin

    # 处理其他标记
    for tag in special_tags:
        # 优先处理会立即返回的特殊标记（不包含Pin）
        if tag == "Summary":
            # 直接使用全量总结
            summary = agent._summarize_and_clear_history(trigger_reason="用户指令触发")
            memory_tags_prompt = agent.memory_manager.prepare_memory_tags_prompt()
            prompt = ""
            if summary:
                # 将摘要和记忆标签设置为新会话的初始提示
                prompt = summary + "\n" + memory_tags_prompt
            else:
                # 即使没有摘要，也确保设置记忆标签作为新会话的初始提示
                prompt = memory_tags_prompt
            return prompt, True
        elif tag == "Exit":
            # 退出 Jarvis（在 jvs/jca 均可用）
            PrettyOutput.auto_print("🛑 用户请求退出程序...")
            raise SystemExit(0)
        elif tag == "Clear":
            agent.clear_history()
            return "", True
        elif tag == "BTW":
            from jarvis.jarvis_utils.input import get_multiline_input

            q_inline = modified_input.replace("'<BTW>'", "").strip()
            if q_inline:
                side_q = q_inline
            else:
                side_q = get_multiline_input(
                    "💬 BTW（不占主会话）：输入独立问题（空行提交，Ctrl+C 取消）",
                    print_on_empty=True,
                ).strip()
            if side_q:
                _run_btw_dispatch(agent, side_q)
            else:
                PrettyOutput.auto_print("（已取消 BTW）")
            return "", True
        elif tag == "ToolUsage":
            agent.set_addon_prompt(agent.get_tool_usage_prompt())
            continue
        elif tag == "JarvisHelp":
            # Jarvis 使用答疑：本轮强制优先从本仓库源码/文档检索答案（一次性 addon_prompt）
            from jarvis.jarvis_utils.input import get_multiline_input

            q_inline = modified_input.replace("'<JarvisHelp>'", "").strip()
            if q_inline:
                q = q_inline
            else:
                q = get_multiline_input(
                    "📚 JarvisHelp：请输入关于 Jarvis 的使用问题（空行取消，Ctrl+C 取消）",
                    print_on_empty=True,
                ).strip()
            if not q:
                PrettyOutput.auto_print("（已取消 JarvisHelp）")
                return "", True

            agent.set_addon_prompt(
                "\n".join(
                    [
                        "你正在回答“Jarvis 的使用问题”。",
                        "要求：在给出结论前，必须优先从当前仓库中查找依据（源码/文档/README/CLI 帮助等），再作答。",
                        "建议优先检索的路径：`src/jarvis/`、`docs/`、`builtin/`。",
                        "回答时请给出关键依据的位置（文件路径 + 关键函数/命令名；必要时引用关键片段）。",
                        "如果仓库中找不到直接答案：说明你查找了哪些关键词/路径，并给出最接近的可行替代方案或需要补充的信息。",
                    ]
                )
            )
            modified_input = q
            continue
        elif tag == "AddDir":
            # Claude Code 风格 add-dir：扩大当前会话可访问目录范围（支持会话/项目持久化）
            from jarvis.jarvis_utils.input import get_multiline_input
            from jarvis.jarvis_utils.input import get_single_line_input
            from jarvis.jarvis_utils.input import reset_completion_caches
            from jarvis.jarvis_utils.config import set_config

            raw_inline = modified_input.replace("'<AddDir>'", "").strip()
            if raw_inline:
                raw_path = raw_inline
            else:
                raw_path = (
                    get_multiline_input(
                        "📁 AddDir：请输入要加入访问范围的目录路径（空行取消，Ctrl+C 取消）",
                        print_on_empty=True,
                    ).strip()
                )
            if not raw_path:
                PrettyOutput.auto_print("（已取消 AddDir）")
                return "", True

            try:
                p = os.path.expanduser(os.path.expandvars(raw_path.strip()))
                abs_dir = os.path.abspath(p)
            except Exception:
                PrettyOutput.auto_print("⚠️ 目录路径解析失败。")
                return "", True

            if not os.path.isdir(abs_dir):
                PrettyOutput.auto_print(f"⚠️ 目录不存在或不可访问: {abs_dir}")
                return "", True

            # 使用“同一交互界面”的单行输入选择，避免切换到独立的全屏选择窗口
            choice = ""
            for _ in range(3):
                choice = (
                    get_single_line_input(
                        "AddDir 生效范围：输入 1=仅本次会话(session)，2=当前目录永久(project) > ",
                        default="1",
                    )
                    .strip()
                )
                if choice in ("1", "2"):
                    break
            if choice not in ("1", "2"):
                PrettyOutput.auto_print("⚠️ 无效选择，已取消 AddDir。")
                return "", True

            # 1) 本次会话：写入 env（立即生效）
            def _add_to_session_env(dir_path: str) -> None:
                cur = os.environ.get("JARVIS_ADDITIONAL_DIRS", "").strip()
                parts = [p for p in cur.split(":") if p.strip()] if cur else []
                if dir_path not in parts:
                    parts.append(dir_path)
                os.environ["JARVIS_ADDITIONAL_DIRS"] = ":".join(parts)
                reset_completion_caches()

            # 2) 当前目录永久：写入 .jarvis/config.yaml，并同时更新本进程 env + GLOBAL_CONFIG_DATA
            def _add_to_project_config(dir_path: str) -> None:
                try:
                    cfg_dir = os.path.join(os.getcwd(), ".jarvis")
                    os.makedirs(cfg_dir, exist_ok=True)
                    cfg_path = os.path.join(cfg_dir, "config.yaml")
                    data = {}
                    if os.path.exists(cfg_path):
                        try:
                            with open(cfg_path, "r", encoding="utf-8", errors="ignore") as f:
                                data = yaml.safe_load(f) or {}
                        except Exception:
                            data = {}
                    if not isinstance(data, dict):
                        data = {}
                    allowed = data.get("allowed_dirs", [])
                    if isinstance(allowed, str):
                        allowed = [p for p in allowed.split(":") if p.strip()]
                    if not isinstance(allowed, list):
                        allowed = []
                    if dir_path not in allowed:
                        allowed.append(dir_path)
                    data["allowed_dirs"] = allowed
                    with open(cfg_path, "w", encoding="utf-8") as f:
                        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
                    # 更新运行时配置 + env，使当前会话立刻生效
                    try:
                        set_config("allowed_dirs", allowed)
                    except Exception:
                        pass
                except Exception as e:
                    PrettyOutput.auto_print(f"⚠️ 写入项目配置失败: {e}")

            if choice == "1":
                _add_to_session_env(abs_dir)
                PrettyOutput.auto_print(f"✅ 已加入本次会话访问范围: {abs_dir}")
                return "", True

            # project
            _add_to_session_env(abs_dir)
            _add_to_project_config(abs_dir)
            PrettyOutput.auto_print(f"✅ 已加入当前目录永久访问范围: {abs_dir}")
            return "", True
        elif tag == "ReloadConfig":
            from jarvis.jarvis_utils.utils import load_config

            load_config()
            return "", True
        elif tag == "SwitchToJCA":
            # 仅在 Git 仓库内允许切换到 jca，避免误触导致无意义的进程替换
            try:
                res = subprocess.run(
                    ["git", "rev-parse", "--show-toplevel"],
                    capture_output=True,
                    text=False,
                )
                if res.returncode != 0:
                    PrettyOutput.auto_print("⚠️ 当前不在 Git 仓库内，无法切换到 jca。")
                    return "", True
            except Exception:
                PrettyOutput.auto_print("⚠️ 检测 Git 仓库失败，无法切换到 jca。")
                return "", True

            PrettyOutput.auto_print("ℹ️ 正在切换到 'jca'（jarvis-code-agent）...")
            try:
                os.execvp("jarvis-code-agent", ["jarvis-code-agent"])
            except Exception as e:
                PrettyOutput.auto_print(f"❌ 切换到 jca 失败: {e}")
            return "", True
        elif tag == "SwitchToJVS":
            # 切回通用模式（jvs）。使用 --keep-jvs 防止在 Git 仓库内被再次自动切回 jca。
            PrettyOutput.auto_print("ℹ️ 正在切换到 'jvs'（jarvis）...")
            try:
                os.execvp("jarvis", ["jarvis", "--keep-jvs"])
            except Exception as e:
                PrettyOutput.auto_print(f"❌ 切换到 jvs 失败: {e}")
            return "", True
        elif tag == "ListRule":
            # 列出所有规则及其状态
            # 使用 agent 的 rules_manager 实例，而不是创建新实例
            # 这样可以正确获取已加载的规则状态
            rules_manager = agent.rules_manager
            rules_info = rules_manager.get_all_rules_with_status()

            if not rules_info:
                PrettyOutput.auto_print("📋 未找到任何规则")
            else:
                # 使用 rich.Table 创建美观的表格
                console = Console()
                table = Table(
                    title="📋 所有可用规则",
                    show_header=True,
                    header_style="bold magenta",
                    expand=True,
                )

                # 添加列
                table.add_column("规则名称", style="cyan", no_wrap=False)
                table.add_column("内容预览", style="green")
                table.add_column("文件路径", style="yellow", no_wrap=False)
                table.add_column("状态", justify="center")

                # 添加行数据
                for rule_name, preview, is_loaded, file_path in rules_info:
                    # 截断过长的预览（已由 get_rule_preview 限制为100字符）
                    # 这里不再需要二次截断，保持原有预览内容
                    # 截断过长的文件路径
                    if len(file_path) > 37:
                        file_path = file_path[:37] + "..."
                    status = (
                        "✅ [green]已激活[/green]"
                        if is_loaded
                        else "🔴 [dim]未激活[/dim]"
                    )
                    table.add_row(rule_name, preview, file_path, status)

                # 打印表格和统计信息
                console.print(table)
                console.print(f"\n总计: {len(rules_info)} 个规则\n")

            return "", True
        elif tag == "SaveSession":
            # 检查是否允许使用SaveSession命令
            if not getattr(agent, "allow_savesession", False):
                PrettyOutput.auto_print("⚠️ SaveSession 命令仅在 jvs/jca 主程序中可用。")
                return "", True
            if agent.save_session():
                PrettyOutput.auto_print("✅ 会话已成功保存。")
            else:
                PrettyOutput.auto_print("❌ 保存会话失败。")
            return "", True
        elif tag == "RestoreSession":
            # 检查是否允许使用RestoreSession命令
            if not getattr(agent, "allow_savesession", False):
                PrettyOutput.auto_print(
                    "⚠️ RestoreSession 命令仅在 jvs/jca 主程序中可用。"
                )
                return "", True
            if agent.restore_session():
                PrettyOutput.auto_print("✅ 会话已成功恢复。")
            else:
                PrettyOutput.auto_print("❌ 恢复会话失败。")
            return "", True
        elif tag == "ListSessions":
            # 列出所有已保存的会话文件（使用模块顶部 import os，避免与函数内 os 冲突导致 ! 命令报错）
            sessions = agent.session._parse_session_files()

            if not sessions:
                PrettyOutput.auto_print("📋 未找到已保存的会话文件。")
            else:
                PrettyOutput.auto_print(f"📋 找到 {len(sessions)} 个会话文件：")
                for idx, (file_path, timestamp, session_name) in enumerate(sessions, 1):
                    # 获取文件大小
                    try:
                        file_size = os.path.getsize(file_path)
                        size_str = f"({file_size / 1024:.1f} KB)"
                    except OSError:
                        size_str = "(未知大小)"

                    # 格式化时间戳显示
                    if timestamp:
                        # 时间戳格式：YYYYMMDD_HHMMSS
                        try:
                            from datetime import datetime

                            dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            time_str = timestamp
                    else:
                        time_str = "(无时间戳)"

                    PrettyOutput.auto_print(f"  {idx}. {os.path.basename(file_path)}")
                    PrettyOutput.auto_print(f"     时间: {time_str}  大小: {size_str}")
            return "", True
        elif tag == "Quiet":
            agent.set_non_interactive(True)
            PrettyOutput.auto_print("🔇 已切换到无人值守模式（非交互模式）")
            modified_input = modified_input.replace("'<Quiet>'", "")
            continue
        elif tag == "FixToolCall":
            # 处理修复工具调用的命令
            if not agent._last_response_content:
                PrettyOutput.auto_print("⚠️ 没有找到需要修复的工具调用内容")
                return "", True

            PrettyOutput.auto_print("🔧 正在构造修复提示词...")
            error_msg = "用户请求手动修复工具调用"

            # 导入提示词构造函数
            from jarvis.jarvis_agent.utils import build_fix_prompt

            # 获取工具使用说明
            tool_usage = agent.get_tool_usage_prompt()

            # 构造修复提示词
            fix_prompt = build_fix_prompt(
                agent._last_response_content, error_msg, tool_usage
            )

            return fix_prompt, False
        elif tag == "SwitchModel":
            # 处理切换模型组命令（仅在主 agent 中可用）
            if not getattr(agent, "allow_savesession", False):
                PrettyOutput.auto_print("⚠️ SwitchModel 命令仅在 jvs/jca 主程序中可用。")
                return "", True

            if switch_model_group(agent):
                PrettyOutput.auto_print("✅ 模型组切换成功。")
            else:
                PrettyOutput.auto_print("❌ 模型组切换失败或已取消。")
            return "", True
        elif tag == "Commit":
            # 处理代码提交命令（仅在 code agent 中可用）
            if not hasattr(agent, "git_manager"):
                PrettyOutput.auto_print("⚠️ Commit 命令仅在 code agent 中可用。")
                return "", True

            from jarvis.jarvis_utils.git_utils import get_latest_commit_hash

            PrettyOutput.auto_print("📝 正在提交代码...")

            # 获取当前的 end commit
            end_commit = get_latest_commit_hash()

            # 获取提交历史
            commits = agent.git_manager.show_commit_history(
                agent.start_commit, end_commit
            )

            # 调用 handle_commit_confirmation 处理提交确认
            # 使用 agent 中存储的 prefix/suffix，不需要额外的后处理函数
            agent.git_manager.handle_commit_confirmation(
                commits,
                agent.start_commit,
                prefix=agent.prefix,
                suffix=agent.suffix,
                agent=agent,
                post_process_func=lambda files: None,  # 简化实现，不需要后处理
            )

            return "", True

        elif tag == "Init":
            # 在当前 cwd 生成/覆盖 JVS_MEMORY.md：jvs/jca 都支持手动刷新。
            try:
                from jarvis.jarvis_utils.project_memory import (
                    build_jvs_memory,
                    read_jvs_memory,
                    write_jvs_memory,
                )

                project_root = os.path.abspath(os.getcwd())
                content = build_jvs_memory(project_root)
                if write_jvs_memory(project_root, content):
                    PrettyOutput.auto_print(
                        f"✅ 已生成/刷新 JVS_MEMORY.md：{os.path.join(project_root, 'JVS_MEMORY.md')}"
                    )
                    # 立即加载到本会话 addon prompt（下轮优先生效）
                    loaded = read_jvs_memory(project_root)
                    if loaded:
                        cur = agent.session.addon_prompt or ""
                        agent.set_addon_prompt(
                            (cur + "\n\n" + loaded).strip()
                            if cur.strip()
                            else loaded.strip()
                        )
                else:
                    PrettyOutput.auto_print("⚠️ 生成 JVS_MEMORY.md 失败")
            except Exception as e:
                PrettyOutput.auto_print(f"⚠️ Init 执行失败: {e}")
            return "", True

        elif tag == "Pin":
            # Pin标记已在前面处理，跳过
            continue

        # 处理普通替换标记
        if tag in replace_map:
            processed_tag.add(tag)
            if (
                "append" in replace_map[tag]
                and replace_map[tag]["append"]
                and tag not in processed_tag
            ):
                modified_input = modified_input.replace(f"'<{tag}>'", "")
                add_on_prompt += replace_map[tag]["template"] + "\n"
            else:
                modified_input = modified_input.replace(
                    f"'<{tag}>'", replace_map[tag]["template"]
                )
        elif tag.startswith("rule:"):
            # 处理 rule:xxx 格式的规则标记
            if tag not in processed_tag:
                rule_name = tag[5:]  # 去掉 "rule:" 前缀

                # 获取规则内容
                rule_content = _get_rule_content(rule_name)
                processed_tag.add(tag)

                if rule_content:
                    # 激活规则：调用 RulesManager.activate_rule()
                    # 使用 Agent 已有的 rules_manager 实例，而不是创建新的
                    # Agent 一定存在 rules_manager 属性，直接使用
                    rules_manager = agent.rules_manager
                    activated = rules_manager.activate_rule(rule_name)

                    # 将激活的规则添加到 agent.loaded_rule_names
                    if activated:
                        if not hasattr(agent, "loaded_rule_names"):
                            agent.loaded_rule_names = set()
                        agent.loaded_rule_names.add(rule_name)
                        PrettyOutput.auto_print(f"🟢 已激活规则: {rule_name}")

                    separator = "\n" + "=" * 50 + "\n"
                    modified_input = modified_input.replace(
                        f"'<{tag}>'", f"<rule>\n{rule_content}\n</rule>{separator}"
                    )

    # 设置附加提示词并返回处理后的内容
    agent.set_addon_prompt(add_on_prompt)
    return modified_input, False


def get_platform_type_from_agent(agent: Any) -> str:
    """根据 Agent 类型返回平台类型

    参数:
        agent: Agent 实例

    返回:
        str: 平台类型，'normal' 或 'smart'
    """
    agent_type = getattr(agent, "_agent_type", "normal")
    return "smart" if agent_type == "code_agent" else "normal"


def _llm_ref_key_to_display(llm_key: Any) -> str:
    """将 llm_groups 中的 llms 引用键解析为「API 模型名 (配置键)」，便于与 config.yaml 对照。"""
    if not isinstance(llm_key, str) or not llm_key.strip() or llm_key == "-":
        return "-"
    llms = _get_global_config().get("llms", {})
    if isinstance(llms, dict) and llm_key in llms:
        ent = llms[llm_key]
        if isinstance(ent, dict):
            m = ent.get("model")
            if m and str(m).strip():
                return f"{m} ({llm_key})"
    return llm_key


def list_model_groups() -> Optional[List[Tuple[str, str, str, str]]]:
    """列出所有可用的模型组

    返回:
        Optional[List[Tuple[str, str, str, str]]]: 模型组列表，每个元素为 (group_name, smart_model, normal_model, cheap_model)
    """

    model_groups = _get_global_config().get("llm_groups", {})
    if not isinstance(model_groups, dict) or not model_groups:
        PrettyOutput.auto_print("📋 未找到任何模型组配置")
        return None

    groups = []
    for group_name, group_config in model_groups.items():
        if isinstance(group_config, dict):
            # 获取各平台的模型名称（展示为解析后的 model 字段，便于与 cheap/normal/smart 配置对应）
            smart_model = _llm_ref_key_to_display(group_config.get("smart_llm", "-"))
            normal_model = _llm_ref_key_to_display(group_config.get("normal_llm", "-"))
            cheap_model = _llm_ref_key_to_display(group_config.get("cheap_llm", "-"))
            groups.append((group_name, smart_model, normal_model, cheap_model))

    return groups


def check_context_limit(
    agent: Any, new_model_group: str, platform_type: str = "normal"
) -> Tuple[bool, str]:
    """检查当前对话是否超出新模型的上下文限制

    参数:
        agent: Agent 实例
        new_model_group: 新模型组名称
        platform_type: 平台类型 ('normal' 或 'smart')

    返回:
        Tuple[bool, str]: (是否可以切换, 原因说明)
    """
    model_groups = _get_global_config().get("llm_groups", {})
    if not isinstance(model_groups, dict):
        return False, "模型组配置不存在"

    group_config = model_groups.get(new_model_group)
    if not isinstance(group_config, dict):
        return False, f"模型组 '{new_model_group}' 不存在"

    # 获取当前对话的 token 数
    current_tokens = 0
    if hasattr(agent, "model"):
        # 从 model 获取所有消息并计算 token
        try:
            messages_text = str(agent.model.get_messages())
            current_tokens = get_context_token_count(messages_text)
        except Exception:
            # 如果无法计算，使用粗略估计
            current_tokens = 0

    # 根据平台类型获取对应的 token 限制
    if platform_type == "smart":
        token_limit_key = "smart_max_input_token_count"
    else:
        token_limit_key = "max_input_token_count"

    # 从模型组配置中获取 token 限制
    token_limit = group_config.get(token_limit_key)
    if token_limit is None:
        # 尝试从 llms 引用中获取
        normal_llm = group_config.get("normal_llm")
        if normal_llm:
            llms = _get_global_config().get("llms", {})
            llm_config = llms.get(normal_llm, {})
            token_limit = llm_config.get("max_input_token_count")

    if token_limit is None:
        # 使用默认限制
        token_limit = 128000

    # 检查是否超出限制（留出 10% 的余量）
    if current_tokens > token_limit * 0.9:
        return (
            False,
            f"当前对话 ({current_tokens} tokens) 超出新模型限制 ({token_limit} tokens) 的 90%",
        )

    return (
        True,
        f"当前对话 ({current_tokens} tokens) 在新模型限制 ({token_limit} tokens) 范围内",
    )


def perform_switch(
    agent: Any, new_model_group: str, platform_type: str = "normal"
) -> bool:
    """执行模型组切换

    参数:
        agent: Agent 实例
        new_model_group: 新模型组名称
        platform_type: 平台类型 ('normal' 或 'smart')

    返回:
        bool: 是否切换成功
    """
    try:
        # 保存旧模型的消息
        old_messages = agent.model.get_messages()

        # 更新全局配置
        set_llm_group(new_model_group)

        # 重新创建模型
        platform_registry = PlatformRegistry()
        if platform_type == "smart":
            agent.model = platform_registry.get_smart_platform()
        else:
            agent.model = platform_registry.get_normal_platform()

        agent.model.set_suppress_output(False)
        agent.model.agent = agent

        # 将旧消息设置到新模型
        if old_messages:
            agent.model.set_messages(old_messages)

        # 将新模型设置到现有的 session 中
        agent.session.model = agent.model

        return True
    except Exception as e:
        PrettyOutput.auto_print(f"❌ 切换模型组失败: {e}")
        return False


def switch_model_group(agent: Any) -> bool:
    """切换模型组的主函数

    参数:
        agent: Agent 实例

    返回:
        bool: 是否切换成功
    """
    # 获取当前模型组
    current_group = get_llm_group() or "(未设置)"
    PrettyOutput.auto_print(f"📌 当前模型组: {current_group}")

    # 列出所有模型组
    groups = list_model_groups()
    if not groups:
        return False

    # 显示模型组列表
    table = Table(
        title="📋 可用模型组",
        show_header=True,
        header_style="bold magenta",
        expand=True,
    )
    table.add_column("编号", style="cyan", justify="center")
    table.add_column("模型组名称", style="green")
    table.add_column("Smart", style="cyan", justify="center")
    table.add_column("Normal", style="magenta", justify="center")
    table.add_column("Cheap", style="yellow", justify="center")

    for idx, (group_name, smart_model, normal_model, cheap_model) in enumerate(
        groups, 1
    ):
        table.add_row(str(idx), group_name, smart_model, normal_model, cheap_model)

    Console().print(table)

    # 用户选择（循环直到输入有效）
    PrettyOutput.auto_print("")
    while True:
        choice = input("请输入模型组编号 (0 取消): ").strip()

        if choice == "0":
            PrettyOutput.auto_print("🚫 已取消切换")
            return False

        try:
            choice_idx = int(choice) - 1
            if choice_idx < 0 or choice_idx >= len(groups):
                PrettyOutput.auto_print(f"❌ 无效的编号: {choice}，请重新输入")
                continue

            new_group = groups[choice_idx][0]
            break
        except ValueError:
            PrettyOutput.auto_print(f"❌ 无效的输入: {choice}，请输入数字")
            continue

    # 执行切换逻辑
    try:
        # 检查是否与当前模型组相同
        if new_group == current_group:
            PrettyOutput.auto_print("⚠️ 当前已使用该模型组")
            return False

        # 获取平台类型
        platform_type = get_platform_type_from_agent(agent)

        # 检查上下文限制
        can_switch, reason = check_context_limit(agent, new_group, platform_type)
        if not can_switch:
            PrettyOutput.auto_print(f"⚠️ {reason}")
            PrettyOutput.auto_print("🚫 已取消切换")
            return False
        else:
            PrettyOutput.auto_print(f"✅ {reason}")

        # 执行切换
        PrettyOutput.auto_print(f"🔄 正在切换到模型组 '{new_group}'...")
        if perform_switch(agent, new_group, platform_type):
            PrettyOutput.auto_print(f"✅ 已成功切换到模型组 '{new_group}'")
            return True
        else:
            return False
    except Exception as e:
        PrettyOutput.auto_print(f"❌ 切换失败: {e}")
        return False
