# -*- coding: utf-8 -*-
"""SQLite3 兼容层：为未编译 _sqlite3 的 Python 环境提供回退实现。"""

import sys

_SQLITE3_READY = False


def ensure_sqlite3() -> bool:
    """确保 ``sqlite3`` 可导入；缺失时使用 ``pysqlite3-binary`` 注入。"""
    global _SQLITE3_READY
    if _SQLITE3_READY:
        return True

    try:
        import sqlite3  # noqa: F401

        _SQLITE3_READY = True
        return True
    except ModuleNotFoundError:
        pass

    try:
        from pysqlite3 import dbapi2 as sqlite3

        sys.modules["sqlite3"] = sqlite3
        sys.modules["_sqlite3"] = sqlite3
        _SQLITE3_READY = True
        return True
    except ImportError:
        return False
