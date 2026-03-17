#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Rust 优化与 Jarvis 的集成
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, '/media/vdc/code/Jarvis/src')

def test_rust_wrapper():
    """测试 Rust wrapper 模块"""
    print("=" * 60)
    print("测试 Rust Wrapper 模块")
    print("=" * 60)
    
    try:
        from jarvis.jarvis_utils.rust_wrapper import (
            get_performance_info,
            is_rust_available,
        )
        
        info = get_performance_info()
        print(f"\n性能信息:")
        print(f"  Rust 可用: {info['rust_available']}")
        print(f"  Rust 启用: {info['rust_enabled']}")
        print(f"  缓存大小: {info['cache_size']}/{info['cache_max_size']}")
        
        if is_rust_available():
            print("\n✅ Rust 优化已启用并正常工作")
        else:
            print("\n⚠️ Rust 优化未启用，将使用 Python 回退实现")
        
        return True
    except Exception as e:
        print(f"\n❌ Rust wrapper 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_read_code_tool():
    """测试 ReadCodeTool 的 Rust 优化"""
    print("\n" + "=" * 60)
    print("测试 ReadCodeTool Rust 优化")
    print("=" * 60)
    
    try:
        from jarvis.jarvis_tools.read_code import ReadCodeTool, _USE_RUST
        
        print(f"\nRust 优化状态: {'启用' if _USE_RUST else '禁用'}")
        
        # 测试读取当前文件
        tool = ReadCodeTool()
        result = tool.execute({
            "files": [{
                "path": "/media/vdc/code/Jarvis/test_rust_integration.py",
                "start_line": 1,
                "end_line": 20
            }],
            "agent": None
        })
        
        if result["success"]:
            print(f"\n✅ ReadCodeTool 测试成功")
            print(f"   读取行数: {result['stdout'].count(chr(10)) + 1}")
            return True
        else:
            print(f"\n❌ ReadCodeTool 测试失败: {result['stderr']}")
            return False
    except Exception as e:
        print(f"\n❌ ReadCodeTool 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tool_registry():
    """测试 ToolRegistry 的 Rust 优化"""
    print("\n" + "=" * 60)
    print("测试 ToolRegistry Rust 优化")
    print("=" * 60)
    
    try:
        from jarvis.jarvis_tools.registry import ToolRegistry, _USE_RUST
        
        print(f"\nRust 优化状态: {'启用' if _USE_RUST else '禁用'}")
        
        # 测试 JSON 提取
        test_text = 'prefix {"name": "test", "value": 42} suffix'
        json_str, pos = ToolRegistry._extract_json_from_text(test_text, 0)
        
        if json_str:
            print(f"\n✅ JSON 提取测试成功")
            print(f"   提取的 JSON: {json_str}")
        else:
            print(f"\n❌ JSON 提取测试失败")
            return False
        
        # 测试标记清理
        test_text = "text <|marker|> more text <|end|>"
        cleaned = ToolRegistry._clean_extra_markers(test_text)
        
        if "<|marker|>" not in cleaned:
            print(f"\n✅ 标记清理测试成功")
            print(f"   清理后: {cleaned}")
        else:
            print(f"\n❌ 标记清理测试失败")
            return False
        
        return True
    except Exception as e:
        print(f"\n❌ ToolRegistry 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_performance_comparison():
    """性能对比测试"""
    print("\n" + "=" * 60)
    print("性能对比测试")
    print("=" * 60)
    
    import tempfile
    import time
    
    # 创建测试文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        test_file = f.name
        for i in range(500):
            f.write(f"def function_{i}():\n")
            f.write(f"    # This is a comment with some text\n")
            f.write(f"    return {i}\n")
    
    try:
        from jarvis.jarvis_tools.read_code import ReadCodeTool
        from jarvis.jarvis_utils.rust_wrapper import is_rust_available
        
        tool = ReadCodeTool()
        
        print(f"\n测试文件: {test_file}")
        print(f"Rust 可用: {is_rust_available()}")
        
        # 测试读取性能
        print("\n文件读取性能测试:")
        start = time.time()
        result = tool.execute({
            "files": [{
                "path": test_file,
                "start_line": 1,
                "end_line": -1
            }],
            "agent": None
        })
        read_time = time.time() - start
        
        if result["success"]:
            print(f"  读取时间: {read_time:.4f}s")
            print(f"  读取行数: {result['stdout'].count(chr(10)) + 1}")
            print(f"  ✅ 文件读取成功")
        else:
            print(f"  ❌ 文件读取失败: {result['stderr']}")
        
        # 测试 token 计算性能
        print("\nToken 计算性能测试:")
        content = result.get("stdout", "")
        
        from jarvis.jarvis_utils.rust_wrapper import (
            calculate_tokens_optimized,
            get_cache_stats
        )
        
        # 清空缓存
        from jarvis.jarvis_utils.rust_wrapper import clear_token_cache
        clear_token_cache()
        
        start = time.time()
        tokens = calculate_tokens_optimized(content)
        calc_time = time.time() - start
        
        cache_size, max_size = get_cache_stats()
        
        print(f"  计算时间: {calc_time:.4f}s")
        print(f"  Token 数量: {tokens}")
        print(f"  缓存大小: {cache_size}/{max_size}")
        print(f"  ✅ Token 计算成功")
        
        return True
    except Exception as e:
        print(f"\n❌ 性能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        os.unlink(test_file)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Jarvis Rust 优化集成测试")
    print("=" * 60)
    
    results = []
    
    results.append(("Rust Wrapper", test_rust_wrapper()))
    results.append(("ReadCodeTool", test_read_code_tool()))
    results.append(("ToolRegistry", test_tool_registry()))
    results.append(("性能对比", test_performance_comparison()))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:20s}: {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过！Rust 优化集成成功！")
    else:
        print("❌ 部分测试失败，请检查错误信息")
    print("=" * 60)
    
    sys.exit(0 if all_passed else 1)