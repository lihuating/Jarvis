"""Rich box 样式工具。

本模块集中定义 Rich Panel 的边框风格，避免在各处散落硬编码。
"""

from rich import box


# 仅保留上/下横线的 Panel 边框：
# - 左右竖线与角落字符都使用空格，减少复制粘贴时的对齐问题
# - 上下边线使用横线，提供清晰的分隔感
HORIZONTAL_RULE_BOX = box.Box(
    # Rich box 需要 8 行，每行 4 个字符（分别对应四个位置）。
    # 这里用空格占位角/分隔符位置，仅保留上下边线的横线。
    " ─  \n"  # top_left, top, top_divider, top_right
    "    \n"  # head_left, head_vertical, head_right, head_horizontal
    " ─  \n"  # mid_left, mid, mid_divider, mid_right（作为底边线使用）
    "    \n"  # row_left, row_vertical, row_right, row_horizontal
    "    \n"  # foot_left, foot_vertical, foot_right, foot_horizontal
    "    \n"  # bottom_left, bottom, bottom_divider, bottom_right
    "    \n"  # body_left, body_vertical, body_right, body_horizontal
    "    \n"  # caption_left, caption_right, caption_divider, caption_horizontal
)

