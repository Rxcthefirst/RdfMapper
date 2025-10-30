"""Data transformation functions."""

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Dict, Optional

from dateutil import parser as date_parser


# Registry of transform functions
_TRANSFORM_REGISTRY: Dict[str, Callable[[Any], Any]] = {}


def register_transform(name: str) -> Callable:
    """Decorator to register a transform function.
    
    Args:
        name: Name of the transform
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable[[Any], Any]) -> Callable:
        _TRANSFORM_REGISTRY[name] = func
        return func
    return decorator


def get_transform(name: str) -> Optional[Callable[[Any], Any]]:
    """Get a transform function by name.
    
    Args:
        name: Transform name
        
    Returns:
        Transform function or None if not found
    """
    return _TRANSFORM_REGISTRY.get(name)


@register_transform("to_decimal")
def to_decimal(value: Any) -> Decimal:
    """Convert value to decimal.
    
    Args:
        value: Input value
        
    Returns:
        Decimal value
        
    Raises:
        ValueError: If conversion fails
    """
    if pd.isna(value) or value == "":
        raise ValueError("Cannot convert empty value to decimal")
    
    try:
        # Handle string values that might have currency symbols or commas
        if isinstance(value, str):
            # Remove common currency symbols and separators
            cleaned = value.replace("$", "").replace(",", "").replace("€", "").replace("£", "").strip()
            return Decimal(cleaned)
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as e:
        raise ValueError(f"Cannot convert '{value}' to decimal: {e}")


@register_transform("to_integer")
def to_integer(value: Any) -> int:
    """Convert value to integer.
    
    Args:
        value: Input value
        
    Returns:
        Integer value
        
    Raises:
        ValueError: If conversion fails
    """
    if pd.isna(value) or value == "":
        raise ValueError("Cannot convert empty value to integer")
    
    try:
        # Handle floats by truncating
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            # Remove commas and spaces
            cleaned = value.replace(",", "").replace(" ", "").strip()
            return int(float(cleaned))
        return int(value)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Cannot convert '{value}' to integer: {e}")


@register_transform("to_date")
def to_date(value: Any) -> str:
    """Convert value to ISO date string (YYYY-MM-DD).
    
    Args:
        value: Input value (string, datetime, etc.)
        
    Returns:
        ISO date string
        
    Raises:
        ValueError: If parsing fails
    """
    if pd.isna(value) or value == "":
        raise ValueError("Cannot convert empty value to date")
    
    try:
        if isinstance(value, datetime):
            return value.date().isoformat()
        
        # Parse string to datetime
        dt = date_parser.parse(str(value))
        return dt.date().isoformat()
    except (ValueError, TypeError, date_parser.ParserError) as e:
        raise ValueError(f"Cannot convert '{value}' to date: {e}")


@register_transform("to_datetime")
def to_datetime(value: Any) -> str:
    """Convert value to ISO datetime string with timezone.
    
    Args:
        value: Input value
        
    Returns:
        ISO datetime string
        
    Raises:
        ValueError: If parsing fails
    """
    if pd.isna(value) or value == "":
        raise ValueError("Cannot convert empty value to datetime")
    
    try:
        if isinstance(value, datetime):
            dt = value
        else:
            # Parse string to datetime
            dt = date_parser.parse(str(value))
        
        # Ensure timezone awareness
        if dt.tzinfo is None:
            # Assume UTC if no timezone
            dt = dt.replace(tzinfo=timezone.utc)
        
        return dt.isoformat()
    except (ValueError, TypeError, date_parser.ParserError) as e:
        raise ValueError(f"Cannot convert '{value}' to datetime: {e}")


@register_transform("to_boolean")
def to_boolean(value: Any) -> bool:
    """Convert value to boolean.
    
    Args:
        value: Input value
        
    Returns:
        Boolean value
        
    Raises:
        ValueError: If conversion fails
    """
    if pd.isna(value):
        raise ValueError("Cannot convert empty value to boolean")
    
    if isinstance(value, bool):
        return value
    
    if isinstance(value, (int, float)):
        return bool(value)
    
    # String conversion
    str_value = str(value).lower().strip()
    
    if str_value in ["true", "yes", "1", "t", "y"]:
        return True
    elif str_value in ["false", "no", "0", "f", "n"]:
        return False
    else:
        raise ValueError(f"Cannot convert '{value}' to boolean")


@register_transform("uppercase")
def uppercase(value: Any) -> str:
    """Convert string to uppercase.
    
    Args:
        value: Input value
        
    Returns:
        Uppercase string
    """
    if pd.isna(value):
        return ""
    return str(value).upper()


@register_transform("lowercase")
def lowercase(value: Any) -> str:
    """Convert string to lowercase.
    
    Args:
        value: Input value
        
    Returns:
        Lowercase string
    """
    if pd.isna(value):
        return ""
    return str(value).lower()


@register_transform("strip")
def strip(value: Any) -> str:
    """Strip whitespace from string.
    
    Args:
        value: Input value
        
    Returns:
        Stripped string
    """
    if pd.isna(value):
        return ""
    return str(value).strip()


# Import pandas for NaN checking
import pandas as pd


def apply_transform(value: Any, transform_name: str) -> Any:
    """Apply a named transform to a value.
    
    Args:
        value: Value to transform
        transform_name: Name of transform to apply
        
    Returns:
        Transformed value
        
    Raises:
        ValueError: If transform not found or transformation fails
    """
    transform_func = get_transform(transform_name)
    if not transform_func:
        raise ValueError(f"Unknown transform: {transform_name}")
    
    return transform_func(value)
