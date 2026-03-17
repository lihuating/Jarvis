//! Jarvis Rust Tools - Performance Optimization Modules
//!
//! This library provides high-performance Rust implementations for common operations
//! in Jarvis, including file I/O, string processing, and token calculation.

use lazy_static::lazy_static;
use memmap2::Mmap;
use pyo3::prelude::*;
use regex::Regex;
use std::collections::HashMap;
use std::fs::File;
use std::sync::Mutex;

// ============================================================================
// File Operations
// ============================================================================

/// Fast file reading using memory mapping
#[pyfunction]
pub fn fast_read_file(filepath: &str, start_line: usize, end_line: i64) -> PyResult<String> {
    let file = File::open(filepath)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(format!("Failed to open file: {}", e)))?;

    let mmap = unsafe { Mmap::map(&file) }
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(format!("Failed to map file: {}", e)))?;

    let content = std::str::from_utf8(&mmap)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyUnicodeDecodeError, _>(format!("Failed to decode file: {}", e)))?;

    let lines: Vec<&str> = content.lines().collect();
    let total_lines = lines.len();

    let end_line = if end_line == -1 {
        total_lines
    } else {
        end_line as usize
    };

    if start_line < 1 || start_line > total_lines {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            format!("Invalid start_line: {} (file has {} lines)", start_line, total_lines)
        ));
    }

    if end_line < start_line || end_line > total_lines {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            format!("Invalid end_line: {} (file has {} lines)", end_line, total_lines)
        ));
    }

    let selected_lines: Vec<&str> = lines
        .iter()
        .skip(start_line - 1)
        .take(end_line - start_line + 1)
        .cloned()
        .collect();

    Ok(selected_lines.join("\n"))
}

/// Read file with line numbers added
#[pyfunction]
pub fn read_file_with_line_numbers(filepath: &str, start_line: usize, end_line: i64) -> PyResult<String> {
    let file = File::open(filepath)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(format!("Failed to open file: {}", e)))?;

    let mmap = unsafe { Mmap::map(&file) }
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(format!("Failed to map file: {}", e)))?;

    let content = std::str::from_utf8(&mmap)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyUnicodeDecodeError, _>(format!("Failed to decode file: {}", e)))?;

    let lines: Vec<&str> = content.lines().collect();
    let total_lines = lines.len();

    let end_line = if end_line == -1 {
        total_lines
    } else {
        end_line as usize
    };

    if start_line < 1 || start_line > total_lines {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            format!("Invalid start_line: {} (file has {} lines)", start_line, total_lines)
        ));
    }

    if end_line < start_line || end_line > total_lines {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            format!("Invalid end_line: {} (file has {} lines)", end_line, total_lines)
        ));
    }

    let mut result = String::new();
    for (i, line) in lines
        .iter()
        .skip(start_line - 1)
        .take(end_line - start_line + 1)
        .enumerate()
    {
        result.push_str(&format!("{:4}:{}\n", start_line + i, line));
    }

    Ok(result)
}

/// Detect file encoding (simplified version)
#[pyfunction]
pub fn detect_file_encoding(filepath: &str) -> PyResult<String> {
    let file = File::open(filepath)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(format!("Failed to open file: {}", e)))?;

    let mmap = unsafe { Mmap::map(&file) }
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(format!("Failed to map file: {}", e)))?;

    // Simple heuristic: check for UTF-8 BOM or valid UTF-8
    if mmap.len() >= 3 && &mmap[0..3] == &[0xEF, 0xBB, 0xBF] {
        return Ok("utf-8-sig".to_string());
    }

    // Try to decode as UTF-8
    if std::str::from_utf8(&mmap).is_ok() {
        return Ok("utf-8".to_string());
    }

    // Default to latin-1 (which never fails)
    Ok("latin-1".to_string())
}

// ============================================================================
// String Operations
// ============================================================================

lazy_static! {
    static ref TOOL_CALL_OPEN_PATTERN: Regex = Regex::new(r"(?i)<\|TOOL_CALL\|>").unwrap();
    static ref TOOL_CALL_CLOSE_PATTERN: Regex = Regex::new(r"(?i)<\|/TOOL_CALL\|>").unwrap();
    static ref EXTRA_MARKERS_PATTERN: Regex = Regex::new(r"<\|.*?\|>").unwrap();
}

/// Fast regex matching
#[pyfunction]
pub fn regex_match_fast(pattern: &str, text: &str) -> PyResult<bool> {
    let re = Regex::new(pattern)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Invalid regex pattern: {}", e)))?;
    Ok(re.is_match(text))
}

/// Extract JSON from text using bracket matching
#[pyfunction]
pub fn extract_json_from_text(text: &str, start_pos: usize) -> PyResult<(Option<String>, usize)> {
    let mut brace_count = 0;
    let mut in_string = false;
    let mut escape_next = false;
    let mut json_start: Option<usize> = None;
    let mut string_char: Option<char> = None;

    let chars: Vec<char> = text.chars().collect();

    for i in start_pos..chars.len() {
        let char = chars[i];

        if escape_next {
            escape_next = false;
            continue;
        }

        match char {
            '\\' => {
                escape_next = true;
            }
            '"' | '\'' => {
                if !in_string {
                    in_string = true;
                    string_char = Some(char);
                } else if Some(char) == string_char {
                    in_string = false;
                    string_char = None;
                }
            }
            '{' if !in_string => {
                if json_start.is_none() {
                    json_start = Some(i);
                }
                brace_count += 1;
            }
            '}' if !in_string => {
                brace_count -= 1;
                if brace_count == 0 {
                    if let Some(start) = json_start {
                        let json_str = text[start..=i].to_string();
                        return Ok((Some(json_str), i + 1));
                    }
                }
            }
            _ => {}
        }
    }

    Ok((None, text.len()))
}

/// Clean extra markers from text
#[pyfunction]
pub fn clean_extra_markers(text: &str) -> PyResult<String> {
    Ok(EXTRA_MARKERS_PATTERN.replace_all(text, "").to_string())
}

/// Strip line endings from text
#[pyfunction]
pub fn strip_line_endings(text: &str) -> PyResult<String> {
    Ok(text.replace("\r\n", "\n").replace("\r", "\n"))
}

// ============================================================================
// Token Operations
// ============================================================================

const MAX_CACHE_SIZE: usize = 1000;

lazy_static! {
    static ref TOKEN_CACHE: Mutex<HashMap<String, usize>> = Mutex::new(HashMap::new());
}

/// Calculate token count using optimized algorithm
#[pyfunction]
pub fn calculate_tokens_optimized(text: &str) -> PyResult<usize> {
    let mut count = 0;

    // Count words (approximate)
    for word in text.split_whitespace() {
        count += ((word.len() / 4) + 1) as usize;
    }

    // Add punctuation tokens
    count += text.matches(|c: char| c.is_ascii_punctuation()).count();

    // Add newlines and special characters
    count += text.matches(|c: char| c == '\n' || c == '\t').count();

    // Account for code-specific tokens
    count += text.matches(|c: char| c == '{' || c == '}' || c == '(' || c == ')' || c == '[' || c == ']').count();
    count += text.matches(|c: char| c == '=' || c == '+' || c == '-' || c == '*' || c == '/').count();

    Ok(count)
}

/// Calculate token count with caching
#[pyfunction]
pub fn token_count_with_cache(text: &str) -> PyResult<usize> {
    // Calculate hash of the text for caching
    let digest = md5::compute(text.as_bytes());
    let hash = format!("{:x}", digest);

    // Check cache
    {
        let cache = TOKEN_CACHE.lock().unwrap();
        if let Some(&count) = cache.get(&hash) {
            return Ok(count);
        }
    }

    // Calculate and cache
    let count = calculate_tokens_optimized(text)?;

    // Update cache with LRU eviction
    let mut cache = TOKEN_CACHE.lock().unwrap();
    if cache.len() >= MAX_CACHE_SIZE {
        let keys: Vec<String> = cache.keys().take(100).cloned().collect();
        for key in keys {
            cache.remove(&key);
        }
    }
    cache.insert(hash, count);

    Ok(count)
}

/// Clear the token cache
#[pyfunction]
pub fn clear_token_cache() -> PyResult<()> {
    let mut cache = TOKEN_CACHE.lock().unwrap();
    cache.clear();
    Ok(())
}

/// Get cache statistics
#[pyfunction]
pub fn get_cache_stats() -> PyResult<(usize, usize)> {
    let cache = TOKEN_CACHE.lock().unwrap();
    Ok((cache.len(), MAX_CACHE_SIZE))
}

// ============================================================================
// Python Module Definition
// ============================================================================

#[pymodule]
fn jarvis_rust_tools(_py: Python, m: &PyModule) -> PyResult<()> {
    // File operations
    m.add_wrapped(wrap_pyfunction!(fast_read_file))?;
    m.add_wrapped(wrap_pyfunction!(read_file_with_line_numbers))?;
    m.add_wrapped(wrap_pyfunction!(detect_file_encoding))?;

    // String operations
    m.add_wrapped(wrap_pyfunction!(regex_match_fast))?;
    m.add_wrapped(wrap_pyfunction!(extract_json_from_text))?;
    m.add_wrapped(wrap_pyfunction!(clean_extra_markers))?;
    m.add_wrapped(wrap_pyfunction!(strip_line_endings))?;

    // Token operations
    m.add_wrapped(wrap_pyfunction!(calculate_tokens_optimized))?;
    m.add_wrapped(wrap_pyfunction!(token_count_with_cache))?;
    m.add_wrapped(wrap_pyfunction!(clear_token_cache))?;
    m.add_wrapped(wrap_pyfunction!(get_cache_stats))?;

    Ok(())
}