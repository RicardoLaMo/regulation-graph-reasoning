"""
Utility functions for data validation module.
"""

import re
from typing import Optional, Any


def clean_whitespace(text: str) -> str:
    """
    Clean excessive whitespace from text.
    
    Args:
        text: Input text string
        
    Returns:
        Cleaned text with normalized whitespace
    """
    if not isinstance(text, str):
        return str(text) if text is not None else ""
    
    # Replace multiple whitespace with single space
    cleaned = re.sub(r'\s+', ' ', text.strip())
    return cleaned


def is_valid_date_format(date_str: str) -> bool:
    """
    Check if date string is in YYYY-MM-DD format.
    
    Args:
        date_str: Date string to validate
        
    Returns:
        True if valid date format, False otherwise
    """
    if not isinstance(date_str, str):
        return False
    
    # Simple regex for YYYY-MM-DD format
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    return bool(re.match(pattern, date_str))


def safe_get(data: dict, key: str, default: Any = None) -> Any:
    """
    Safely get value from dictionary with fallback.
    
    Args:
        data: Dictionary to search
        key: Key to look for
        default: Default value if key not found
        
    Returns:
        Value from dictionary or default
    """
    if not isinstance(data, dict):
        return default
    
    return data.get(key, default)


def is_empty_or_none(value: Any) -> bool:
    """
    Check if value is None, empty string, or only whitespace.
    
    Args:
        value: Value to check
        
    Returns:
        True if value is considered empty, False otherwise
    """
    if value is None:
        return True
    
    if isinstance(value, str):
        return len(value.strip()) == 0
    
    return False