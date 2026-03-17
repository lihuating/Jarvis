# Jarvis Rust Tools

High-performance Rust implementations for Jarvis AI Assistant.

## Features

- Fast file I/O using memory mapping
- Optimized string processing and regex matching
- Efficient token calculation with caching

## Installation

```bash
pip install jarvis-rust-tools
```

## Usage

```python
from jarvis_rust_tools import fast_read_file, calculate_tokens_optimized

# Read file fast
content = fast_read_file("example.py", 1, 100)

# Calculate tokens
token_count = calculate_tokens_optimized(content)
```

## Performance

This module provides 2-10x performance improvements over pure Python implementations for common operations.