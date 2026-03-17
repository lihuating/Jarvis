# -*- coding: utf-8 -*-
"""
Rust 优化功能的包装模块

提供对 Rust 优化函数的访问，带有回退到 Python 实现的功能
"""

import os
from typing import Optional, Tuple, Any

# 尝试导入 Rust 优化模块
_RUST_AVAILABLE = False
try:
    from jarvis_rust_tools import (
        fast_read_file as _rust_fast_read_file,
        read_file_with_line_numbers as _rust_read_file_with_line_numbers,
        detect_file_encoding as _rust_detect_file_encoding,
        regex_match_fast as _rust_regex_match_fast,
        extract_json_from_text as _rust_extract_json_from_text,
        clean_extra_markers as _rust_clean_extra_markers,
        strip_line_endings as _rust_strip_line_endings,
        calculate_tokens_optimized as _rust_calculate_tokens_optimized,
        token_count_with_cache as _rust_token_count_with_cache,
        clear_token_cache as _rust_clear_token_cache,
        get_cache_stats as _rust_get_cache_stats,
    )
    _RUST_AVAILABLE = True
except ImportError:
    _RUST_AVAILABLE = False

# 检查是否强制使用 Python 版本
_USE_RUST = _RUST_AVAILABLE and os.environ.get('JARVIS_USE_RUST', 'true').lower() == 'true'


def is_rust_available() -> bool:
    """检查 Rust 优化是否可用"""
    return _RUST_AVAILABLE and _USE_RUST


def fast_read_file(filepath: str, start_line: int = 1, end_line: int = -1) -> str:
    """
    快速读取文件（使用 Rust 优化或 Python 回退）
    
    Args:
        filepath: 文件路径
        start_line: 起始行号（1-indexed）
        end_line: 结束行号（1-indexed，-1 表示到文件末尾）
    
    Returns:
        文件内容字符串
    """
    if is_rust_available():
        try:
            return _rust_fast_read_file(filepath, start_line, end_line)
        except Exception as e:
            # Rust 版本失败，回退到 Python
            import warnings
            warnings.warn(f"Rust fast_read_file failed, falling back to Python: {e}")
    
    # Python 回退实现
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    total_lines = len(lines)
    if end_line == -1:
        end_line = total_lines
    else:
        end_line = min(end_line, total_lines)
    
    start_line = max(1, start_line)
    end_line = max(start_line, min(end_line, total_lines))
    
    selected_lines = lines[start_line - 1:end_line]
    return ''.join(selected_lines)


def read_file_with_line_numbers(filepath: str, start_line: int = 1, end_line: int = -1) -> str:
    """
    读取文件并添加行号（使用 Rust 优化或 Python 回退）
    
    Args:
        filepath: 文件路径
        start_line: 起始行号（1-indexed）
        end_line: 结束行号（1-indexed，-1 表示到文件末尾）
    
    Returns:
        带行号的文件内容字符串
    """
    if is_rust_available():
        try:
            return _rust_read_file_with_line_numbers(filepath, start_line, end_line)
        except Exception as e:
            import warnings
            warnings.warn(f"Rust read_file_with_line_numbers failed, falling back to Python: {e}")
    
    # Python 回退实现
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    total_lines = len(lines)
    if end_line == -1:
        end_line = total_lines
    else:
        end_line = min(end_line, total_lines)
    
    start_line = max(1, start_line)
    end_line = max(start_line, min(end_line, total_lines))
    
    result = []
    for i, line in enumerate(lines[start_line - 1:end_line], start=start_line):
        result.append(f"{i:4d}:{line.rstrip()}")
    
    return '\n'.join(result)


def extract_json_from_text(text: str, start_pos: int = 0) -> Tuple[Optional[str], int]:
    """
    从文本中提取 JSON（使用 Rust 优化或 Python 回退）
    
    Args:
        text: 包含 JSON 的文本
        start_pos: 开始搜索的位置
    
    Returns:
        (提取的 JSON 字符串, JSON 结束后的位置)
    """
    if is_rust_available():
        try:
            return _rust_extract_json_from_text(text, start_pos)
        except Exception as e:
            import warnings
            warnings.warn(f"Rust extract_json_from_text failed, falling back to Python: {e}")
    
    # Python 回退实现
    import json
    brace_count = 0
    in_string = False
    escape_next = False
    string_char = None
    json_start = None
    
    for i in range(start_pos, len(text)):
        char = text[i]
        
        if escape_next:
            escape_next = False
            continue
        
        if char == '\\':
            escape_next = True
        elif char in ('"', "'"):
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False
                string_char = None
        elif char == '{' and not in_string:
            if json_start is None:
                json_start = i
            brace_count += 1
        elif char == '}' and not in_string:
            brace_count -= 1
            if brace_count == 0 and json_start is not None:
                json_str = text[json_start:i+1]
                try:
                    json.loads(json_str)  # 验证是否为有效 JSON
                    return json_str, i + 1
                except json.JSONDecodeError:
                    pass
    
    return None, len(text)


def clean_extra_markers(text: str) -> str:
    """
    清理文本中的额外标记（使用 Rust 优化或 Python 回退）
    
    Args:
        text: 要清理的文本
    
    Returns:
        清理后的文本
    """
    if is_rust_available():
        try:
            return _rust_clean_extra_markers(text)
        except Exception as e:
            import warnings
            warnings.warn(f"Rust clean_extra_markers failed, falling back to Python: {e}")
    
    # Python 回退实现
    import re
    return re.sub(r'<\|.*?\|>', '', text, flags=re.IGNORECASE)


def calculate_tokens_optimized(text: str) -> int:
    """
    计算 token 数量（使用 Rust 优化或 Python 回退）
    
    Args:
        text: 要计算 token 的文本
    
    Returns:
        token 数量
    """
    if is_rust_available():
        try:
            return _rust_calculate_tokens_optimized(text)
        except Exception as e:
            import warnings
            warnings.warn(f"Rust calculate_tokens_optimized failed, falling back to Python: {e}")
    
    # Python 回退实现
    # 简化的 token 计算算法
    count = 0
    for word in text.split():
        count += (len(word) // 4) + 1
    
    count += sum(1 for c in text if c.isascii() and c in '.,;:!?()[]{}')
    count += text.count('\n') + text.count('\t')
    
    return count


def token_count_with_cache(text: str) -> int:
    """
    计算 token 数量（带缓存）（使用 Rust 优化或 Python 回退）
    
    Args:
        text: 要计算 token 的文本
    
    Returns:
        token 数量
    """
    if is_rust_available():
        try:
            return _rust_token_count_with_cache(text)
        except Exception as e:
            import warnings
            warnings.warn(f"Rust token_count_with_cache failed, falling back to Python: {e}")
    
    # Python 回退实现（无缓存）
    return calculate_tokens_optimized(text)


def clear_token_cache():
    """清空 token 缓存"""
    if is_rust_available():
        try:
            _rust_clear_token_cache()
        except Exception:
            pass


def get_cache_stats() -> Tuple[int, int]:
    """
    获取缓存统计信息
    
    Returns:
        (当前缓存大小, 最大缓存大小)
    """
    if is_rust_available():
        try:
            return _rust_get_cache_stats()
        except Exception:
            pass
    
    return (0, 0)


def get_performance_info() -> dict:
    """
    获取性能优化信息
    
    Returns:
        包含性能信息的字典
    """
    return {
        'rust_available': _RUST_AVAILABLE,
        'rust_enabled': _USE_RUST,
        'cache_size': get_cache_stats()[0],
        'cache_max_size': get_cache_stats()[1],
    }
