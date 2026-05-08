# -*- coding: utf-8 -*-
"""流式输出期间检测 ESC（与 Ctrl+C 区分，用于合并追问后重新提交）。"""

from __future__ import annotations

import os
import sys
import threading
import time
from typing import Optional
from typing import Tuple


def _drain_after_esc_byte(fd: int) -> bool:
    """已读入首字节 ESC (0x1b)。若后续为 CSI/SS3 等则丢弃并返回 False；若为「裸 ESC」返回 True。"""
    import select

    deadline = time.monotonic() + 0.05
    r, _, _ = select.select([fd], [], [], 0.05)
    if fd not in r:
        return True
    try:
        b2 = os.read(fd, 1)
    except OSError:
        return True
    if not b2:
        return True
    if b2 == b"[":
        while time.monotonic() < deadline + 0.2:
            r2, _, _ = select.select([fd], [], [], 0.05)
            if fd not in r2:
                break
            try:
                c = os.read(fd, 1)
            except OSError:
                break
            if not c:
                break
            if 0x40 <= c[0] <= 0x7E:
                break
        return False
    if b2 == b"O":
        r2, _, _ = select.select([fd], [], [], 0.05)
        if fd in r2:
            try:
                os.read(fd, 1)
            except OSError:
                pass
        return False
    try:
        os.write(1, b2)
    except OSError:
        pass
    return False


def _esc_worker_unix(fd: int, stop: threading.Event, esc_hit: threading.Event) -> None:
    import select

    while not stop.is_set():
        try:
            r, _, _ = select.select([fd], [], [], 0.08)
        except (ValueError, TypeError, OSError):
            return
        if stop.is_set():
            return
        if fd not in r:
            continue
        try:
            b = os.read(fd, 1)
        except OSError:
            return
        if not b:
            continue
        if b == b"\x1b":
            if _drain_after_esc_byte(fd):
                esc_hit.set()
                return
        else:
            try:
                os.write(1, b)
            except OSError:
                pass


def _esc_worker_win(stop: threading.Event, esc_hit: threading.Event) -> None:
    import msvcrt

    while not stop.wait(0.06):
        try:
            while msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch == "\x1b":
                    esc_hit.set()
                    return
                if ch in ("\x00", "\xe0"):
                    if msvcrt.kbhit():
                        try:
                            msvcrt.getwch()
                        except OSError:
                            pass
        except (OSError, AttributeError):
            return


def install_stdio_cbreak_for_esc_poll() -> Optional[Tuple[int, object]]:
    """在 Unix 上将 stdin 设为 cbreak，便于单字节读取 ESC。Windows 返回 None。"""
    if os.name == "nt":
        return None
    if not sys.stdin.isatty():
        return None
    try:
        import termios  # type: ignore[import-not-found]
        import tty  # type: ignore[import-not-found]
    except ImportError:
        return None
    fd = sys.stdin.fileno()
    try:
        old = termios.tcgetattr(fd)
        tty.setcbreak(fd)
        return (fd, old)
    except Exception:
        return None


def restore_stdio_attrs(tty_state: Optional[Tuple[int, object]]) -> None:
    if not tty_state:
        return
    fd, old = tty_state
    try:
        import termios  # type: ignore[import-not-found]

        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    except Exception:
        pass


def spawn_esc_poll_thread(
    stop: threading.Event,
    esc_hit: threading.Event,
    tty_state: Optional[Tuple[int, object]],
) -> threading.Thread:
    """启动后台轮询：Windows 用 msvcrt；Unix 依赖 install_stdio_cbreak_for_esc_poll 已生效。"""

    def _run() -> None:
        if os.name == "nt":
            _esc_worker_win(stop, esc_hit)
            return
        if tty_state:
            fd = tty_state[0]
            _esc_worker_unix(fd, stop, esc_hit)

    t = threading.Thread(target=_run, daemon=True, name="jarvis-stream-esc")
    t.start()
    return t
