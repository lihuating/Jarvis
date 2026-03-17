#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的 Rust 优化测试
"""

import sys
import tempfile
import time

def test_rust_imports():
    """测试 Rust 扩展导入"""
    print("=" * 60)
    print("测试 Rust 扩展导入")
    print("=" * 60)
    
    try:
        from jarvis_rust_tools import (
            fast_read_file,
            read_file_with_line_numbers,
            calculate_tokens_optimized,
            token_count_with_cache,
            extract_json_from_text,
            clean_extra_markers,
        )
        print("✅ Rust 扩展导入成功")
        return True
    except ImportError as e:
        print(f"❌ Rust 扩展导入失败: {e}")
        return False


def test_file_operations():
    """测试文件操作"""
    print("\n" + "=" * 60)
    print("测试文件操作")
    print("=" * 60)
    
    from jarvis_rust_tools import fast_read_file, read_file_with_line_numbers
    
    # 创建测试文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        test_file = f.name
        f.write("def hello():\n")
        f.write("    print('Hello, World!')\n")
        f.write("    return 42\n")
        f.write("\n")
        f.write("def add(a, b):\n")
        f.write("    return a + b\n")
    
    try:
        # 测试快速读取
        print("\n1. 测试 fast_read_file:")
        content = fast_read_file(test_file, 1, 3)
        print(f"   读取内容:\n{content}")
        print("   ✅ fast_read_file 成功")
        
        # 测试带行号读取
        print("\n2. 测试 read_file_with_line_numbers:")
        numbered = read_file_with_line_numbers(test_file, 1, 3)
        print(f"   带行号内容:\n{numbered}")
        print("   ✅ read_file_with_line_numbers 成功")
        
        return True
    except Exception as e:
        print(f"❌ 文件操作测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        import os
        os.unlink(test_file)


def test_token_calculation():
    """测试 token 计算"""
    print("\n" + "=" * 60)
    print("测试 Token 计算")
    print("=" * 60)
    
    from jarvis_rust_tools import (
        calculate_tokens_optimized,
        token_count_with_cache,
        clear_token_cache,
        get_cache_stats,
    )
    
    try:
        test_text = "Hello, world! This is a test of the token calculation system."
        
        print("\n1. 测试 calculate_tokens_optimized:")
        start = time.time()
        count = calculate_tokens_optimized(test_text)
        elapsed = time.time() - start
        print(f"   Token 数量: {count}")
        print(f"   计算时间: {elapsed:.6f}s")
        print("   ✅ calculate_tokens_optimized 成功")
        
        print("\n2. 测试 token_count_with_cache:")
        clear_token_cache()
        start = time.time()
        count1 = token_count_with_cache(test_text)
        elapsed1 = time.time() - start
        
        start = time.time()
        count2 = token_count_with_cache(test_text)
        elapsed2 = time.time() - start
        
        print(f"   第一次调用: {count1} tokens, {elapsed1:.6f}s")
        print(f"   第二次调用: {count2} tokens, {elapsed2:.6f}s (缓存)")
        print("   ✅ token_count_with_cache 成功")
        
        print("\n3. 测试 get_cache_stats:")
        size, max_size = get_cache_stats()
        print(f"   缓存大小: {size}/{max_size}")
        print("   ✅ get_cache_stats 成功")
        
        return True
    except Exception as e:
        print(f"❌ Token 计算测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_string_operations():
    """测试字符串操作"""
    print("\n" + "=" * 60)
    print("测试字符串操作")
    print("=" * 60)
    
    from jarvis_rust_tools import extract_json_from_text, clean_extra_markers
    
    try:
        # 测试 JSON 提取
        print("\n1. 测试 extract_json_from_text:")
        text = r'prefix {"name": "test", "value": 42} suffix'
        json_str, pos = extract_json_from_text(text, 0)
        print(f"   原始文本: {text}")
        print(f"   提取的 JSON: {json_str}")
        print(f"   位置: {pos}")
        if json_str:
            print("   ✅ extract_json_from_text 成功")
        else:
            print("   ❌ extract_json_from_text 失败")
            return False
        
        # 测试标记清理
        print("\n2. 测试 clean_extra_markers:")
        text = "text <|marker|> more text <|end|>"
        cleaned = clean_extra_markers(text)
        print(f"   原始文本: {text}")
        print(f"   清理后: {cleaned}")
        if "<|marker|>" not in cleaned:
            print("   ✅ clean_extra_markers 成功")
        else:
            print("   ❌ clean_extra_markers 失败")
            return False
        
        return True
    except Exception as e:
        print(f"❌ 字符串操作测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_performance():
    """性能测试"""
    print("\n" + "=" * 60)
    print("性能测试")
    print("=" * 60)
    
    from jarvis_rust_tools import fast_read_file, calculate_tokens_optimized
    
    # 创建大文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        test_file = f.name
        for i in range(1000):
            f.write(f"def function_{i}():\n")
            f.write(f"    # This is a comment with some text\n")
            f.write(f"    return {i}\n")
    
    try:
        print(f"\n测试文件: {test_file} (1000 行)")
        
        # 测试文件读取性能
        print("\n1. 文件读取性能:")
        start = time.time()
        content = fast_read_file(test_file, 1, -1)
        read_time = time.time() - start
        print(f"   读取时间: {read_time:.4f}s")
        print(f"   读取行数: {content.count(chr(10)) + 1}")
        print("   ✅ 文件读取成功")
        
        # 测试 token 计算性能
        print("\n2. Token 计算性能:")
        start = time.time()
        tokens = calculate_tokens_optimized(content)
        calc_time = time.time() - start
        print(f"   计算时间: {calc_time:.4f}s")
        print(f"   Token 数量: {tokens}")
        print("   ✅ Token 计算成功")
        
        # 性能指标
        lines_per_sec = 1000 / read_time
        tokens_per_sec = tokens / calc_time
        
        print(f"\n性能指标:")
        print(f"   文件读取: {lines_per_sec:.0f} 行/秒")
        print(f"   Token 计算: {tokens_per_sec:.0f} tokens/秒")
        
        return True
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        import os
        os.unlink(test_file)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Jarvis Rust 优化 - 简单测试套件")
    print("=" * 60)
    
    results = []
    
    results.append(("Rust 扩展导入", test_rust_imports()))
    results.append(("文件操作", test_file_operations()))
    results.append(("Token 计算", test_token_calculation()))
    results.append(("字符串操作", test_string_operations()))
    results.append(("性能测试", test_performance()))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:20s}: {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过！Rust 优化工作正常！")
    else:
        print("❌ 部分测试失败")
    print("=" * 60)
    
    sys.exit(0 if all_passed else 1)
