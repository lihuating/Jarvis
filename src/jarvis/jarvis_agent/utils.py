# -*- coding: utf-8 -*-
"""
工具函数（jarvis_agent.utils）

- join_prompts: 统一的提示拼接策略（仅拼接非空段落，使用双换行）
- is_auto_complete: 统一的自动完成标记检测
- fix_tool_call_with_llm: 使用大模型修复工具调用格式
"""

from enum import Enum
from typing import Any
from typing import Iterable
from typing import Optional
from typing import cast


from jarvis.jarvis_utils.output import PrettyOutput
from jarvis.jarvis_utils.tag import ct
from jarvis.jarvis_utils.tag import ot


def join_prompts(parts: Iterable[str]) -> str:
    """
    将多个提示片段按统一规则拼接：
    - 过滤掉空字符串
    - 使用两个换行分隔
    - 不进行额外 strip，保持调用方原样语义
    """
    try:
        non_empty: list[str] = [p for p in parts if isinstance(p, str) and p]
    except Exception:
        # 防御性处理：若 parts 不可迭代或出现异常，直接返回空字符串
        return ""
    return "\n\n".join(non_empty)


def is_auto_complete(response: str) -> bool:
    """
    检测是否包含自动完成标记。
    当前实现：包含 ot('!!!COMPLETE!!!') 即视为自动完成。
    """
    try:
        return ot("!!!COMPLETE!!!") in response
    except Exception:
        # 防御性处理：即使 ot 出现异常，也不阻塞主流程
        return "!!!COMPLETE!!!" in response


def user_input_indicates_loop_complete(user_input: str) -> bool:
    """
    判断交互模式下用户的非空输入是否表示「结束当前任务、不再继续对话」。

    背景：主循环提示「回车结束；输入文字继续」，但用户常自然输入「符合预期，结束」等，
    若一律当作下一轮 prompt 会再次调用模型，形成无效循环。

    规则：优先识别否定/继续意图；否则匹配明确的结束类短语（中英）。保守策略，避免
    将「好的」「继续」等歧义短句误判为结束。
    """
    s = (user_input or "").strip()
    if not s:
        return False

    negation_markers = (
        "不要结束",
        "别结束",
        "暂不结束",
        "还不能结束",
        "不要完成",
        "别完成",
        "继续任务",
        "还要继续",
        "继续执行",
        "继续评审",
        "继续分析",
    )
    if any(m in s for m in negation_markers):
        return False

    completion_markers_cn = (
        "结束本次任务",
        "结束任务",
        "完成任务",
        "任务结束",
        "到此为止",
        "无需继续",
        "没有新需求",
        "确认结束",
        "可以结束",
        "任务完成",
        "就先这样",
        "不用继续",
        "不需要继续",
    )
    if any(m in s for m in completion_markers_cn):
        return True

    if "符合预期" in s or "符合要求" in s:
        return True

    low = s.lower().strip()
    low_core = low.rstrip(".!！").strip()
    if low_core in {
        "ok",
        "done",
        "q",
        "quit",
        "exit",
        "bye",
        "finished",
        "complete",
        "thats all",
        "that's all",
        "no more",
        "finish",
    }:
        return True

    return False


def normalize_next_action(next_action: Any) -> str:
    """
    规范化下一步动作为字符串:
    - 如果是 Enum, 返回其 value（若为字符串）
    - 如果是 str, 原样返回
    - 其他情况返回空字符串
    """
    try:
        if isinstance(next_action, Enum):
            value = getattr(next_action, "value", None)
            return value if isinstance(value, str) else ""
        if isinstance(next_action, str):
            return next_action
        return ""
    except Exception:
        return ""


def build_fix_prompt(content: str, error_msg: str, tool_usage: str) -> str:
    """构建修复工具调用的提示词

    参数:
        content: 包含错误工具调用的内容
        error_msg: 错误消息
        tool_usage: 工具使用说明

    返回:
        str: 构建好的提示字符串
    """
    return f"""你之前的工具调用格式有误，请根据工具使用说明修复以下内容。

**错误信息：**
{error_msg}

**工具使用说明：**
{tool_usage}

**错误的工具调用内容：**
{content}

请修复上述工具调用内容，确保：
1. 包含完整的 {ot("TOOL_CALL")} 和 {ct("TOOL_CALL")} 标签
2. JSON格式正确，包含 name、arguments、want 三个字段
3. 如果使用多行字符串，直接换行即可

请直接返回修复后的完整工具调用内容，不要添加其他说明文字。"""


def fix_tool_call_with_llm(content: str, agent: Any, error_msg: str) -> Optional[str]:
    """使用大模型修复工具调用格式

    参数:
        content: 包含错误工具调用的内容
        agent: Agent实例，用于调用大模型
        error_msg: 错误消息

    返回:
        Optional[str]: 修复后的内容，如果修复失败则返回None
    """
    try:
        # 获取工具使用说明
        tool_usage = agent.get_tool_usage_prompt()

        # 构建修复提示
        fix_prompt = build_fix_prompt(content, error_msg, tool_usage)

        # 调用大模型修复
        PrettyOutput.auto_print("🤖 尝试使用大模型修复工具调用格式...")
        fixed_content: Any = agent.model.chat_until_success(fix_prompt)

        # 类型检查：确保返回的是字符串
        if fixed_content and isinstance(fixed_content, str):
            PrettyOutput.auto_print("✅ 大模型修复完成")
            # 类型断言：确保返回类型匹配函数签名
            return cast(Optional[str], fixed_content)
        else:
            PrettyOutput.auto_print("❌ 大模型修复失败：返回内容为空")
            return None

    except Exception as e:
        PrettyOutput.auto_print(f"❌ 大模型修复失败：{str(e)}")
        return None


__all__ = [
    "join_prompts",
    "is_auto_complete",
    "user_input_indicates_loop_complete",
    "normalize_next_action",
    "fix_tool_call_with_llm",
]
