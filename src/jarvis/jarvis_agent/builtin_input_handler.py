# -*- coding: utf-8 -*-
import os
import re
import subprocess
from typing import Any
from typing import List
from typing import Optional
from typing import Tuple

import yaml

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
    from jarvis.jarvis_utils.globals import set_in_chat

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
        # BTW 不经 chat_until_success，须标记 in_chat，避免全局看门狗再开 Live 与流式面板冲突
        set_in_chat(True)
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
        finally:
            set_in_chat(False)
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
                    # 进入交互式 shell 期间会长时间“无 Jarvis 输出”，全局看门狗会误刷“思考中...”
                    # 且 Live 刷新会污染用户的交互终端，因此在该作用域内暂停看门狗。
                    from jarvis.jarvis_utils.output import OutputWatchdogPaused

                    with OutputWatchdogPaused():
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
        elif tag == "ToolList":
            # 执行型：直接列出可用工具（来自当前 agent 的 ToolRegistry）
            try:
                tool_registry = agent.get_tool_registry()
            except Exception:
                tool_registry = None

            if not tool_registry:
                PrettyOutput.auto_print("⚠️ 未找到可用的工具注册表（ToolRegistry）。")
                return "", True

            try:
                tools = tool_registry.get_all_tools()
            except Exception as e:
                PrettyOutput.auto_print(f"⚠️ 获取工具列表失败: {e}")
                return "", True

            PrettyOutput.auto_print(f"📋 共 {len(tools)} 个工具：")
            max_show = 50
            for t in tools[:max_show]:
                name = t.get("name", "")
                desc = t.get("description", "") or ""
                PrettyOutput.auto_print(f"  - {name}: {desc}")
            if len(tools) > max_show:
                PrettyOutput.auto_print(f"  ... 还有 {len(tools) - max_show} 个未显示")

            return "", True

        elif tag == "ToolShow":
            # 执行型：展示指定工具的参数 schema 与描述
            from jarvis.jarvis_utils.input import get_single_line_input

            q_inline = modified_input.replace("'<ToolShow>'", "").strip()
            tool_name = q_inline or get_single_line_input(
                "🔧 ToolShow：请输入工具名（空回车取消） > ", default=""
            ).strip()
            if not tool_name:
                PrettyOutput.auto_print("（已取消 ToolShow）")
                return "", True

            tool_registry = agent.get_tool_registry()
            if not tool_registry:
                PrettyOutput.auto_print("⚠️ 未找到可用的工具注册表（ToolRegistry）。")
                return "", True

            try:
                tool = tool_registry.get_tool(tool_name)
            except Exception:
                tool = None

            if not tool:
                PrettyOutput.auto_print(
                    f"⚠️ 找不到工具 {tool_name}。"
                )
                return "", True

            PrettyOutput.auto_print(f"🧩 工具: {tool_name}")
            PrettyOutput.auto_print(f"  描述: {getattr(tool, 'description', '')}")
            try:
                import json

                PrettyOutput.auto_print(
                    "  参数 schema：\n"
                    + json.dumps(
                        getattr(tool, "parameters", {}),
                        ensure_ascii=False,
                        indent=2,
                    )
                )
            except Exception:
                # schema 展示失败则不阻断
                pass
            return "", True

        elif tag == "ToolRun":
            # 执行型：用户指定工具与参数，直接在当前进程里跑该工具并回显输出
            from jarvis.jarvis_utils.input import get_multiline_input
            from jarvis.jarvis_utils.input import get_single_line_input
            from jarvis.jarvis_utils.input import user_confirm

            from jarvis.jarvis_utils.jsonnet_compat import loads as json_loads

            q_inline = modified_input.replace("'<ToolRun>'", "").strip()
            tool_name = q_inline or get_single_line_input(
                "🔧 ToolRun：请输入工具名（空回车取消） > ", default=""
            ).strip()
            if not tool_name:
                PrettyOutput.auto_print("（已取消 ToolRun）")
                return "", True

            tool_registry = agent.get_tool_registry()
            if not tool_registry:
                PrettyOutput.auto_print("⚠️ 未找到可用的工具注册表（ToolRegistry）。")
                return "", True

            try:
                tool = tool_registry.get_tool(tool_name)
            except Exception:
                tool = None

            if not tool:
                PrettyOutput.auto_print(f"⚠️ 找不到工具 {tool_name}。")
                return "", True

            # 参数输入：空行代表 {}
            raw_args = get_multiline_input(
                "🔧 ToolRun：请输入参数 JSON（空行={}，Ctrl+C取消）",
                print_on_empty=False,
            )
            if not raw_args.strip():
                args = {}
            else:
                try:
                    parsed = json_loads(raw_args)
                    args = parsed if isinstance(parsed, dict) else {}
                except Exception as e:
                    PrettyOutput.auto_print(f"⚠️ 参数 JSON 解析失败: {e}")
                    return "", True

            # 执行前确认（与 tool_executor 的 execute_tool_confirm 语义保持一致）
            if getattr(agent, "execute_tool_confirm", False) and not user_confirm(
                f"需要执行工具 {tool_name} 确认？", True
            ):
                PrettyOutput.auto_print("（已取消工具执行）")
                return "", True

            PrettyOutput.auto_print(f"🔧 正在执行工具: {tool_name}")
            try:
                result = tool_registry.execute_tool(
                    tool_name, args, agent=agent
                )
            except Exception as e:
                PrettyOutput.auto_print(f"❌ 工具执行失败: {e}")
                return "", True

            # 回显结果（尽量按 stdout/stderr 结构）
            if isinstance(result, dict):
                success = result.get("success", None)
                if success is True:
                    PrettyOutput.auto_print("✅ 工具执行成功")
                elif success is False:
                    PrettyOutput.auto_print("❌ 工具执行失败")
                stdout = result.get("stdout", "")
                stderr = result.get("stderr", "")
                if stdout:
                    PrettyOutput.auto_print(stdout)
                if stderr:
                    PrettyOutput.auto_print(stderr)
                PrettyOutput.auto_print(f"📌 返回值字段: {', '.join(result.keys())}")
            else:
                PrettyOutput.auto_print(f"📌 返回值: {result}")

            return "", True
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
        elif tag == "RuleShow":
            # 执行型：显示指定规则的内容（包含文件路径注释）
            from jarvis.jarvis_utils.input import get_single_line_input

            q_inline = modified_input.replace("'<RuleShow>'", "").strip()
            rule_name = q_inline or get_single_line_input(
                "📚 RuleShow：请输入规则名（空回车取消） > ", default=""
            ).strip()
            if not rule_name:
                PrettyOutput.auto_print("（已取消 RuleShow）")
                return "", True

            rule_content = _get_rule_content(rule_name)
            if not rule_content:
                PrettyOutput.auto_print(f"⚠️ 未找到规则: {rule_name}")
                return "", True

            # 防止单条规则过长刷屏：展示前 2000 字符
            max_chars = 2000
            show = rule_content if len(rule_content) <= max_chars else rule_content[:max_chars] + "\n...（内容已截断）"
            PrettyOutput.auto_print(f"🧩 规则内容预览: {rule_name}")
            PrettyOutput.auto_print(show)
            return "", True

        elif tag == "RuleActivate":
            # 执行型：激活指定规则并把激活结果更新到 addon_prompt（用于下一次模型调用）
            from jarvis.jarvis_utils.input import get_single_line_input

            q_inline = modified_input.replace("'<RuleActivate>'", "").strip()
            rule_name = q_inline or get_single_line_input(
                "📚 RuleActivate：请输入规则名（空回车取消） > ", default=""
            ).strip()
            if not rule_name:
                PrettyOutput.auto_print("（已取消 RuleActivate）")
                return "", True

            try:
                activated = agent.rules_manager.activate_rule(rule_name)
            except Exception as e:
                PrettyOutput.auto_print(f"⚠️ 激活规则失败: {e}")
                return "", True

            if not activated:
                PrettyOutput.auto_print(f"⚠️ 未找到或激活失败: {rule_name}")
                return "", True

            active_rules_content = agent.rules_manager.get_active_rules_content()
            if active_rules_content:
                agent.set_addon_prompt(
                    f"<rules>\n{active_rules_content}\n</rules>"
                )
            PrettyOutput.auto_print(f"✅ 已激活规则: {rule_name}")
            return "", True

        elif tag == "RuleDeactivate":
            # 执行型：停用指定规则并更新 addon_prompt
            from jarvis.jarvis_utils.input import get_single_line_input

            q_inline = modified_input.replace("'<RuleDeactivate>'", "").strip()
            rule_name = q_inline or get_single_line_input(
                "📚 RuleDeactivate：请输入规则名（空回车取消） > ", default=""
            ).strip()
            if not rule_name:
                PrettyOutput.auto_print("（已取消 RuleDeactivate）")
                return "", True

            try:
                deactivated = agent.rules_manager.deactivate_rule(rule_name)
            except Exception as e:
                PrettyOutput.auto_print(f"⚠️ 停用规则失败: {e}")
                return "", True

            if not deactivated:
                PrettyOutput.auto_print(f"⚠️ 规则未激活或停用失败: {rule_name}")
                return "", True

            active_rules_content = agent.rules_manager.get_active_rules_content()
            if active_rules_content:
                agent.set_addon_prompt(
                    f"<rules>\n{active_rules_content}\n</rules>"
                )
            else:
                agent.set_addon_prompt("")
            PrettyOutput.auto_print(f"✅ 已停用规则: {rule_name}")
            return "", True

        elif tag == "MethodologyList":
            # 执行型：列出所有可用方法论的 problem_type
            try:
                from jarvis.jarvis_utils.methodology import _load_all_methodologies
            except Exception as e:
                PrettyOutput.auto_print(f"⚠️ 导入方法论列表失败: {e}")
                return "", True

            methodologies = _load_all_methodologies()
            if not methodologies:
                PrettyOutput.auto_print("📚 未找到任何方法论")
                return "", True

            max_show = 60
            PrettyOutput.auto_print(f"📚 共 {len(methodologies)} 个方法论：")
            for i, (problem_type, _) in enumerate(methodologies[:max_show], 1):
                PrettyOutput.auto_print(f"  {i}. {problem_type}")
            if len(methodologies) > max_show:
                PrettyOutput.auto_print(f"  ... 还有 {len(methodologies) - max_show} 个未显示")
            return "", True

        elif tag == "MethodologyShow":
            # 执行型：展示指定方法论（按 problem_type 匹配）
            from jarvis.jarvis_utils.input import get_single_line_input
            import json

            q_inline = modified_input.replace("'<MethodologyShow>'", "").strip()
            problem_type = q_inline or get_single_line_input(
                "🧭 MethodologyShow：请输入 problem_type（空回车取消） > ", default=""
            ).strip()
            if not problem_type:
                PrettyOutput.auto_print("（已取消 MethodologyShow）")
                return "", True

            try:
                from jarvis.jarvis_utils.methodology import _load_all_methodologies
            except Exception as e:
                PrettyOutput.auto_print(f"⚠️ 加载方法论失败: {e}")
                return "", True

            content = ""
            for pt, c in _load_all_methodologies():
                if pt == problem_type:
                    content = c
                    break

            if not content:
                PrettyOutput.auto_print(f"⚠️ 未找到方法论: {problem_type}")
                return "", True

            max_chars = 2000
            show = content if len(content) <= max_chars else content[:max_chars] + "\n...（内容已截断）"
            PrettyOutput.auto_print(f"🧩 方法论内容预览: {problem_type}")
            PrettyOutput.auto_print(show)
            return "", True

        elif tag == "MethodologyUse":
            # 执行型：根据用户输入调用 load_methodology，并把结果写入 addon_prompt
            from jarvis.jarvis_utils.input import get_multiline_input

            q_inline = modified_input.replace("'<MethodologyUse>'", "").strip()
            user_text = q_inline or get_multiline_input(
                "🧭 MethodologyUse：输入需求/问题描述（空行取消，Ctrl+C取消）",
                print_on_empty=True,
            ).strip()
            if not user_text:
                PrettyOutput.auto_print("（已取消 MethodologyUse）")
                return "", True

            try:
                from jarvis.jarvis_utils.methodology import load_methodology
            except Exception as e:
                PrettyOutput.auto_print(f"⚠️ 导入 load_methodology 失败: {e}")
                return "", True

            tool_registry = agent.get_tool_registry()
            if not tool_registry:
                PrettyOutput.auto_print("⚠️ 未找到可用 ToolRegistry，无法加载方法论")
                return "", True

            result = load_methodology(user_text, tool_registry)
            if not result:
                PrettyOutput.auto_print("⚠️ 未加载到相关方法论")
                return "", True

            agent.set_addon_prompt(
                "以下是历史类似问题的执行经验，可参考：\n" + result
            )
            PrettyOutput.auto_print("✅ 方法论已加载到下一次模型调用的上下文")
            return "", True

        elif tag == "MethodologyAdd" or tag == "MethodologyUpdate":
            # 执行型：添加/更新方法论（调用 methodology 工具）
            from jarvis.jarvis_utils.input import get_single_line_input
            from jarvis.jarvis_utils.input import user_confirm

            operation = "add" if tag == "MethodologyAdd" else "update"

            q_inline = modified_input.replace(f"'<{tag}>'", "").strip()
            if q_inline:
                PrettyOutput.auto_print("（提示）请用交互输入方式填写参数；行内额外文本将被忽略。")

            problem_type = get_single_line_input(
                "🧩 请输入 problem_type（空回车取消） > ", default=""
            ).strip()
            if not problem_type:
                PrettyOutput.auto_print(f"（已取消 {tag}）")
                return "", True

            scope = get_single_line_input(
                "🧩 请输入 scope：global/project（空回车默认 global） > ", default="global"
            ).strip().lower()
            if not scope:
                scope = "global"
            if scope not in ("global", "project"):
                PrettyOutput.auto_print("⚠️ scope 必须是 global 或 project")
                return "", True

            content = ""
            if tag == "MethodologyAdd":
                # 自动从当前会话中提取“成功达成目标”的方法论内容（无需人工输入）
                try:
                    from pathlib import Path

                    from jarvis.jarvis_utils.dialogue_recorder import get_global_recorder
                    from jarvis.jarvis_utils.output import status_spinner

                    def _build_session_excerpt(max_records: int = 240) -> str:
                        recorder = get_global_recorder()
                        session_path = recorder.get_session_file_path()
                        sid = Path(session_path).stem
                        records = recorder.read_session(sid) or []
                        records = records[-max_records:]

                        lines = []
                        for r in records:
                            role = str(r.get("role", "") or "").strip() or "unknown"
                            txt = str(r.get("content", "") or "").strip()
                            if not txt:
                                continue
                            # 单条过长会压爆 token：保守截断
                            if len(txt) > 1200:
                                txt = txt[:1200] + "…"
                            lines.append(f"[{role}] {txt}")
                        return "\n".join(lines).strip()

                    excerpt = _build_session_excerpt()
                    if not excerpt:
                        # 兜底：从模型 messages 抽取
                        try:
                            msgs = agent.model.get_messages() or []
                            tail = msgs[-60:]
                            lines = []
                            for m in tail:
                                role = str(m.get("role", "") or "").strip() or "unknown"
                                txt = str(m.get("content", "") or "").strip()
                                if not txt:
                                    continue
                                if len(txt) > 1200:
                                    txt = txt[:1200] + "…"
                                lines.append(f"[{role}] {txt}")
                            excerpt = "\n".join(lines).strip()
                        except Exception:
                            excerpt = ""

                    prompt = "\n".join(
                        [
                            "你是 Jarvis 的“方法论提取器”。",
                            "目标：从下面的会话片段中，自动总结出【可复用】的方法论，用于以后遇到同类问题时复现成功路径。",
                            "",
                            "要求：",
                            "- 只总结“成功达成目标/解决问题”的步骤与关键决策；避免无关闲聊。",
                            "- 输出中文 Markdown，结构固定为：",
                            "  1) ## 问题重述",
                            "  2) ## 解决流程（编号步骤，尽量可执行）",
                            "  3) ## 注意事项（坑点/边界/超时/权限/输出缓冲等）",
                            "  4) ## 示例（可选：给出关键命令/工具调用的示例参数）",
                            "- 不要输出任何敏感信息（token/key/账号密码/IP 可保留网段或打码）。",
                            "- 不要提及“我作为模型/我调用了工具”等元叙事。",
                            "",
                            f"问题类型（problem_type）：{problem_type}",
                            "",
                            "会话片段：",
                            "```",
                            excerpt if excerpt else "（会话片段为空）",
                            "```",
                        ]
                    )

                    with status_spinner("🧠 正在自动总结方法论内容...", spinner="dots"):
                        # 使用当前模型生成（会话内一次性总结）
                        content = agent.model.chat_until_success(prompt, max_output=6000)  # type: ignore[attr-defined]
                    content = (content or "").strip()
                except Exception as e:
                    PrettyOutput.auto_print(f"⚠️ 自动总结方法论失败：{e}")
                    content = ""
            else:
                # MethodologyUpdate 仍保留人工输入（更新场景通常需要明确内容）
                from jarvis.jarvis_utils.input import get_multiline_input

                content = get_multiline_input(
                    f"🧩 请输入方法论内容（{tag}；空行取消，Ctrl+C取消）",
                    print_on_empty=True,
                ).strip()

            if not content:
                PrettyOutput.auto_print(f"（已取消 {tag}）")
                return "", True

            tool_registry = agent.get_tool_registry()
            if not tool_registry:
                PrettyOutput.auto_print("⚠️ 未找到可用 ToolRegistry")
                return "", True

            args = {
                "operation": operation,
                "problem_type": problem_type,
                "content": content,
                "scope": scope,
            }

            if getattr(agent, "execute_tool_confirm", False) and not user_confirm(
                f"需要执行方法论{operation}确认？", True
            ):
                PrettyOutput.auto_print("（已取消方法论写入）")
                return "", True

            result = tool_registry.execute_tool("methodology", args, agent=agent)
            if isinstance(result, dict):
                PrettyOutput.auto_print(
                    f"✅ 方法论{operation}完成"
                    + (f"：{result.get('stdout','')}" if result.get("stdout") else "")
                )
                if result.get("stderr"):
                    PrettyOutput.auto_print(result.get("stderr"))
            else:
                PrettyOutput.auto_print(f"📌 返回值: {result}")
            return "", True

        elif tag == "TaskAnalysis":
            # 执行型：手动触发任务分析（保存记忆、生成方法论等）
            from jarvis.jarvis_utils.input import get_single_line_input
            from jarvis.jarvis_utils.output import OutputWatchdogPaused

            q_inline = modified_input.replace(f"'<{tag}>'", "").strip()
            if q_inline:
                PrettyOutput.auto_print("（提示）请用交互输入方式填写参数；行内额外文本将被忽略。")

            feedback = get_single_line_input(
                "📊 可选：你对本次任务完成是否满意？（直接回车跳过） > ", default=""
            ).strip()
            try:
                # analysis 内部可能会使用 Live/面板输出；外层再包一层 Status(Live) 会冲突。
                # 这里仅暂停“无输出→思考中...”看门狗，避免在分析期间刷屏污染输出。
                PrettyOutput.auto_print("📊 正在执行任务分析（保存记忆/生成方法论）...")
                with OutputWatchdogPaused():
                    agent.analysis(feedback)
                PrettyOutput.auto_print("✅ 任务分析已完成")
            except Exception as e:
                PrettyOutput.auto_print(f"⚠️ 任务分析失败: {e}")
            return "", True

        elif tag == "MethodologyDelete":
            # 执行型：删除方法论（调用 methodology 工具）
            from jarvis.jarvis_utils.input import get_single_line_input
            from jarvis.jarvis_utils.input import user_confirm

            problem_type = get_single_line_input(
                "🧩 请输入要删除的 problem_type（空回车取消） > ", default=""
            ).strip()
            if not problem_type:
                PrettyOutput.auto_print("（已取消 MethodologyDelete）")
                return "", True

            scope = get_single_line_input(
                "🧩 请输入 scope：global/project（空回车默认 global） > ", default="global"
            ).strip().lower()
            if not scope:
                scope = "global"
            if scope not in ("global", "project"):
                PrettyOutput.auto_print("⚠️ scope 必须是 global 或 project")
                return "", True

            tool_registry = agent.get_tool_registry()
            if not tool_registry:
                PrettyOutput.auto_print("⚠️ 未找到可用 ToolRegistry")
                return "", True

            args = {
                "operation": "delete",
                "problem_type": problem_type,
                "scope": scope,
            }

            if getattr(agent, "execute_tool_confirm", False) and not user_confirm(
                "需要执行方法论删除确认？", True
            ):
                PrettyOutput.auto_print("（已取消方法论删除）")
                return "", True

            result = tool_registry.execute_tool("methodology", args, agent=agent)
            if isinstance(result, dict):
                PrettyOutput.auto_print(
                    "✅ 方法论删除完成"
                    + (f"：{result.get('stdout','')}" if result.get("stdout") else "")
                )
                if result.get("stderr"):
                    PrettyOutput.auto_print(result.get("stderr"))
            else:
                PrettyOutput.auto_print(f"📌 返回值: {result}")
            return "", True
        elif tag == "MemoryTags":
            # 执行型：展示所有已出现的记忆标签（从 short/project/global 归集）
            try:
                from jarvis.jarvis_utils.globals import get_all_memory_tags
            except Exception as e:
                PrettyOutput.auto_print(f"⚠️ 获取内存标签失败: {e}")
                return "", True

            # None：不截断唯一标签数（与注入模型的 get_all_memory_tags() 默认 200 区分）
            tags_by_type = get_all_memory_tags(max_tags_per_type=None) or {}
            session_tags: List[str] = []
            if callable(getattr(agent, "get_memory_tags", None)):
                try:
                    session_tags = sorted(set(agent.get_memory_tags() or []))
                except Exception:
                    session_tags = []
            has_persisted = any(
                (tags_by_type.get(k) or []) for k in ("short_term", "project_long_term", "global_long_term")
            )
            if not has_persisted and not session_tags:
                PrettyOutput.auto_print("📭 未找到任何记忆标签")
                return "", True

            type_labels = {
                "short_term": "短期记忆 (short_term)",
                "project_long_term": "项目长期记忆 (project_long_term)",
                "global_long_term": "全局长期记忆 (global_long_term)",
            }
            PrettyOutput.auto_print("🏷️ 记忆标签概览（持久化按类型全量列出；同名字母序）：")
            tags_per_line = 28
            for m_type in ["short_term", "project_long_term", "global_long_term"]:
                t_list = tags_by_type.get(m_type, []) or []
                if not t_list:
                    continue
                label = type_labels.get(m_type, m_type)
                PrettyOutput.auto_print(f"  ▶ {label} — 共 {len(t_list)} 个")
                for i in range(0, len(t_list), tags_per_line):
                    chunk = t_list[i : i + tags_per_line]
                    PrettyOutput.auto_print("    " + ", ".join(chunk))
            if session_tags:
                PrettyOutput.auto_print(
                    f"  ▶ 当前会话已收集标签（Agent.memory_tags，含 memory 工具写入） — 共 {len(session_tags)} 个"
                )
                for i in range(0, len(session_tags), tags_per_line):
                    chunk = session_tags[i : i + tags_per_line]
                    PrettyOutput.auto_print("    " + ", ".join(chunk))
            return "", True

        elif tag == "MemorySave":
            # 执行型：保存一条记忆（调用 memory 工具 action=save）
            from jarvis.jarvis_utils.input import get_single_line_input
            from jarvis.jarvis_utils.input import get_multiline_input
            from jarvis.jarvis_utils.input import user_confirm

            memory_type = get_single_line_input(
                "🧠 MemorySave：memory_type=project_long_term/global_long_term/short_term > ",
                default="short_term",
            ).strip()
            if not memory_type:
                PrettyOutput.auto_print("（已取消 MemorySave）")
                return "", True
            if memory_type not in (
                "project_long_term",
                "global_long_term",
                "short_term",
            ):
                PrettyOutput.auto_print(
                    "⚠️ memory_type 必须是 project_long_term/global_long_term/short_term"
                )
                return "", True

            tags_str = get_single_line_input(
                "🏷️ tags：用逗号分隔（可空，回车跳过） > ", default=""
            ).strip()
            tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []

            content = get_multiline_input(
                "🧠 MemorySave：请输入要保存的内容（空行取消，Ctrl+C取消）",
                print_on_empty=True,
            ).strip()
            if not content:
                PrettyOutput.auto_print("（已取消 MemorySave）")
                return "", True

            # 执行前确认（save 不一定不可逆，但仍建议遵循 execute_tool_confirm）
            if getattr(agent, "execute_tool_confirm", False) and not user_confirm(
                f"需要执行 memory.save（memory_type={memory_type}）确认？", True
            ):
                PrettyOutput.auto_print("（已取消记忆保存）")
                return "", True

            tool_registry = agent.get_tool_registry()
            if not tool_registry:
                PrettyOutput.auto_print("⚠️ 未找到可用的 ToolRegistry")
                return "", True

            args = {
                "action": "save",
                "memories": [
                    {"memory_type": memory_type, "tags": tags, "content": content}
                ],
            }
            result = tool_registry.execute_tool("memory", args, agent=agent)
            if isinstance(result, dict):
                if result.get("success") is True:
                    PrettyOutput.auto_print("✅ 记忆保存成功")
                if result.get("stdout"):
                    PrettyOutput.auto_print(result["stdout"])
                if result.get("stderr"):
                    PrettyOutput.auto_print(result["stderr"])
            else:
                PrettyOutput.auto_print(f"📌 返回值: {result}")
            return "", True

        elif tag == "MemoryRetrieve":
            # 执行型：检索记忆（调用 memory 工具 action=retrieve）
            from jarvis.jarvis_utils.input import get_single_line_input
            from jarvis.jarvis_utils.input import get_multiline_input

            memory_types_str = get_single_line_input(
                "🔎 MemoryRetrieve：memory_types（逗号分隔，可选 all/project_long_term/global_long_term/short_term） > ",
                default="all",
            ).strip()
            if not memory_types_str:
                PrettyOutput.auto_print("（已取消 MemoryRetrieve）")
                return "", True
            memory_types = [t.strip() for t in memory_types_str.split(",") if t.strip()]

            tags_str = get_single_line_input(
                "🏷️ tags 过滤（可空，逗号分隔） > ", default=""
            ).strip()
            tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []

            limit_str = get_single_line_input(
                "📌 limit（返回最大数量） > ", default="5"
            ).strip()
            try:
                limit = int(limit_str) if limit_str else 5
            except Exception:
                limit = 5
            if limit <= 0:
                limit = 5

            smart_str = get_single_line_input(
                "🧠 是否启用 smart_search？y/N > ", default="n"
            ).strip().lower()
            smart_search = smart_str in ("y", "yes", "true", "1")
            query = ""
            if smart_search:
                query = get_multiline_input(
                    "🧠 smart_search=true：请输入语义检索 query（空行取消）",
                    print_on_empty=True,
                ).strip()
                if not query:
                    PrettyOutput.auto_print("（已取消 MemoryRetrieve）")
                    return "", True

            tool_registry = agent.get_tool_registry()
            if not tool_registry:
                PrettyOutput.auto_print("⚠️ 未找到可用的 ToolRegistry")
                return "", True

            args = {
                "action": "retrieve",
                "memory_types": memory_types,
                "tags": tags,
                "limit": limit,
                "smart_search": smart_search,
                "query": query,
            }
            result = tool_registry.execute_tool("memory", args, agent=agent)
            if isinstance(result, dict):
                if result.get("success") is True:
                    PrettyOutput.auto_print("✅ 记忆检索完成")
                if result.get("stdout"):
                    PrettyOutput.auto_print(result["stdout"])
                if result.get("stderr"):
                    PrettyOutput.auto_print(result["stderr"])
            else:
                PrettyOutput.auto_print(f"📌 返回值: {result}")
            return "", True

        elif tag == "MemoryClear":
            # 执行型：清除记忆（调用 memory 工具 action=clear，且必须 confirm=true）
            from jarvis.jarvis_utils.input import get_single_line_input
            from jarvis.jarvis_utils.input import user_confirm

            memory_types_str = get_single_line_input(
                "🧹 MemoryClear：memory_types（逗号分隔，支持 all/xxx，空回车取消） > ",
                default="all",
            ).strip()
            if not memory_types_str:
                PrettyOutput.auto_print("（已取消 MemoryClear）")
                return "", True
            memory_types = [t.strip() for t in memory_types_str.split(",") if t.strip()]

            tags_str = get_single_line_input(
                "🏷️ tags 过滤（可空，逗号分隔） > ", default=""
            ).strip()
            tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []

            ids_str = get_single_line_input(
                "🆔 memory_ids（可空，逗号分隔，若不填将按 tags/memory_types 过滤） > ",
                default="",
            ).strip()
            memory_ids = [t.strip() for t in ids_str.split(",") if t.strip()] if ids_str else []

            # 让用户显式确认不可逆操作
            if not user_confirm("⚠️ 该操作不可恢复，确认清除？", default=False):
                PrettyOutput.auto_print("（已取消 MemoryClear）")
                return "", True

            tool_registry = agent.get_tool_registry()
            if not tool_registry:
                PrettyOutput.auto_print("⚠️ 未找到可用的 ToolRegistry")
                return "", True

            args = {
                "action": "clear",
                "memory_types": memory_types,
                "tags": tags,
                "memory_ids": memory_ids,
                "confirm": True,
            }
            result = tool_registry.execute_tool("memory", args, agent=agent)
            if isinstance(result, dict):
                if result.get("success") is True:
                    PrettyOutput.auto_print("✅ 记忆清除完成")
                if result.get("stdout"):
                    PrettyOutput.auto_print(result["stdout"])
                if result.get("stderr"):
                    PrettyOutput.auto_print(result["stderr"])
            else:
                PrettyOutput.auto_print(f"📌 返回值: {result}")
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
    # 等待用户输入属于"正常静默"，暂停无输出看门狗，避免误触发思考中提示
    try:
        from jarvis.jarvis_utils.output import OutputWatchdogPaused
    except Exception:
        OutputWatchdogPaused = None
    PrettyOutput.auto_print("")
    while True:
        if OutputWatchdogPaused:
            with OutputWatchdogPaused():
                choice = input("请输入模型组编号 (0 取消): ").strip()
        else:
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
