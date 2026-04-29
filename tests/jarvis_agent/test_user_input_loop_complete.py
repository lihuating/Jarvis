# -*- coding: utf-8 -*-
"""user_input_indicates_loop_complete 行为测试"""

from jarvis.jarvis_agent.utils import user_input_indicates_loop_complete


def test_empty_not_complete_via_helper():
    assert user_input_indicates_loop_complete("") is False
    assert user_input_indicates_loop_complete("   ") is False


def test_completion_phrases():
    assert user_input_indicates_loop_complete("符合预期，结束本次任务") is True
    assert user_input_indicates_loop_complete("符合举起，结束本次任务") is True
    assert user_input_indicates_loop_complete("符合要求，没问题了") is True
    assert user_input_indicates_loop_complete("无需继续") is True
    assert user_input_indicates_loop_complete("done") is True
    assert user_input_indicates_loop_complete("OK") is True
    assert user_input_indicates_loop_complete("that's all") is True
    assert user_input_indicates_loop_complete("ok.") is True


def test_negation_not_complete():
    assert user_input_indicates_loop_complete("不要结束，继续评审") is False
    assert user_input_indicates_loop_complete("别结束任务") is False
    assert user_input_indicates_loop_complete("还要继续分析") is False


def test_ambiguous_not_complete():
    assert user_input_indicates_loop_complete("好的") is False
    assert user_input_indicates_loop_complete("请再检查一下登录流程") is False
