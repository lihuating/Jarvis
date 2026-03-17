#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script for Jarvis Rust Tools"""

import sys
import tempfile
import time

try:
    from jarvis_rust_tools import (
        fast_read_file,
        read_file_with_line_numbers,
        detect_file_encoding,
        regex_match_fast,
        extract_json_from_text,
        clean_extra_markers,
        strip_line_endings,
        calculate_tokens_optimized,
        token_count_with_cache,
        clear_token_cache,
        get_cache_stats,
    )
    print("✅ Successfully imported jarvis_rust_tools")
except ImportError as e:
    print(f"❌ Failed to import jarvis_rust_tools: {e}")
    sys.exit(1)


def test_file_operations():
    """Test file operations"""
    print("\n" + "=" * 60)
    print("Testing File Operations")
    print("=" * 60)

    # Create a test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        test_file = f.name
        f.write("def hello():\n")
        f.write("    print('Hello, World!')\n")
        f.write("    return 42\n")
        f.write("\n")
        f.write("def add(a, b):\n")
        f.write("    return a + b\n")

    try:
        # Test fast_read_file
        print("\n1. Testing fast_read_file...")
        content = fast_read_file(test_file, 1, 3)
        print(f"   Read lines 1-3:\n{content}")
        print("   ✅ fast_read_file works")

        # Test read_file_with_line_numbers
        print("\n2. Testing read_file_with_line_numbers...")
        numbered = read_file_with_line_numbers(test_file, 1, 3)
        print(f"   Numbered lines:\n{numbered}")
        print("   ✅ read_file_with_line_numbers works")

        # Test detect_file_encoding
        print("\n3. Testing detect_file_encoding...")
        encoding = detect_file_encoding(test_file)
        print(f"   Detected encoding: {encoding}")
        print("   ✅ detect_file_encoding works")

    finally:
        import os
        os.unlink(test_file)


def test_string_operations():
    """Test string operations"""
    print("\n" + "=" * 60)
    print("Testing String Operations")
    print("=" * 60)

    # Test regex_match_fast
    print("\n1. Testing regex_match_fast...")
    result = regex_match_fast(r"hello", "hello world")
    print(f"   Match 'hello' in 'hello world': {result}")
    assert result == True
    print("   ✅ regex_match_fast works")

    # Test extract_json_from_text
    print("\n2. Testing extract_json_from_text...")
    text = r'prefix {"name": "test", "value": 42} suffix'
    json_str, pos = extract_json_from_text(text, 0)
    print(f"   Extracted JSON: {json_str}")
    print(f"   Position after JSON: {pos}")
    assert json_str is not None
    print("   ✅ extract_json_from_text works")

    # Test clean_extra_markers
    print("\n3. Testing clean_extra_markers...")
    text = "text <|marker|> more text <|end|>"
    cleaned = clean_extra_markers(text)
    print(f"   Original: {text}")
    print(f"   Cleaned: {cleaned}")
    assert "<|marker|>" not in cleaned
    print("   ✅ clean_extra_markers works")

    # Test strip_line_endings
    print("\n4. Testing strip_line_endings...")
    text = "line1\r\nline2\rline3\n"
    stripped = strip_line_endings(text)
    print(f"   Original: {repr(text)}")
    print(f"   Stripped: {repr(stripped)}")
    assert "\r\n" not in stripped
    print("   ✅ strip_line_endings works")


def test_token_operations():
    """Test token operations"""
    print("\n" + "=" * 60)
    print("Testing Token Operations")
    print("=" * 60)

    # Test calculate_tokens_optimized
    print("\n1. Testing calculate_tokens_optimized...")
    text = "Hello, world! This is a test."
    count = calculate_tokens_optimized(text)
    print(f"   Text: {text}")
    print(f"   Token count: {count}")
    assert count > 0
    print("   ✅ calculate_tokens_optimized works")

    # Test token_count_with_cache
    print("\n2. Testing token_count_with_cache...")
    clear_token_cache()
    count1 = token_count_with_cache(text)
    count2 = token_count_with_cache(text)
    print(f"   First call: {count1}")
    print(f"   Second call (cached): {count2}")
    assert count1 == count2
    print("   ✅ token_count_with_cache works")

    # Test get_cache_stats
    print("\n3. Testing get_cache_stats...")
    size, max_size = get_cache_stats()
    print(f"   Cache size: {size}/{max_size}")
    print("   ✅ get_cache_stats works")


def test_performance():
    """Test performance improvement"""
    print("\n" + "=" * 60)
    print("Performance Comparison")
    print("=" * 60)

    # Create a large test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        test_file = f.name
        for i in range(1000):
            f.write(f"def function_{i}():\n")
            f.write(f"    return {i}\n")

    try:
        # Test file reading performance
        print("\n1. File Reading Performance (1000 lines)")
        
        # Rust version
        start = time.time()
        rust_content = fast_read_file(test_file, 1, -1)
        rust_time = time.time() - start
        print(f"   Rust version: {rust_time:.4f}s")

        # Python version for comparison
        start = time.time()
        with open(test_file, 'r') as f:
            python_content = f.read()
        python_time = time.time() - start
        print(f"   Python version: {python_time:.4f}s")

        speedup = python_time / rust_time
        print(f"   Speedup: {speedup:.2f}x")

        # Test token calculation performance
        print("\n2. Token Calculation Performance")
        test_text = python_content
        
        # Rust version
        start = time.time()
        rust_tokens = calculate_tokens_optimized(test_text)
        rust_time = time.time() - start
        print(f"   Rust version: {rust_time:.4f}s ({rust_tokens} tokens)")

        # Simple Python version for comparison
        start = time.time()
        python_tokens = len(test_text.split())
        python_time = time.time() - start
        print(f"   Python version: {python_time:.4f}s ({python_tokens} words)")

        speedup = python_time / rust_time
        print(f"   Speedup: {speedup:.2f}x")

    finally:
        import os
        os.unlink(test_file)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Jarvis Rust Tools - Test Suite")
    print("=" * 60)

    try:
        test_file_operations()
        test_string_operations()
        test_token_operations()
        test_performance()

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
