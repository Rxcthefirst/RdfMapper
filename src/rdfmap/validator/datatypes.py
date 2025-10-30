"""XSD datatype validation."""

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Optional


def validate_xsd_string(value: Any) -> tuple[bool, Optional[str]]:
    """Validate value can be represented as xsd:string."""
    try:
        str(value)
        return True, None
    except Exception as e:
        return False, f"Cannot convert to string: {e}"


def validate_xsd_integer(value: Any) -> tuple[bool, Optional[str]]:
    """Validate value can be represented as xsd:integer."""
    try:
        int_val = int(value)
        # Check if conversion changed the value (e.g., 3.14 -> 3)
        if isinstance(value, float) and value != int_val:
            return False, f"Value {value} is not an integer"
        return True, None
    except (ValueError, TypeError) as e:
        return False, f"Cannot convert to integer: {e}"


def validate_xsd_decimal(value: Any) -> tuple[bool, Optional[str]]:
    """Validate value can be represented as xsd:decimal."""
    try:
        Decimal(str(value))
        return True, None
    except (InvalidOperation, ValueError) as e:
        return False, f"Cannot convert to decimal: {e}"


def validate_xsd_float(value: Any) -> tuple[bool, Optional[str]]:
    """Validate value can be represented as xsd:float."""
    try:
        float(value)
        return True, None
    except (ValueError, TypeError) as e:
        return False, f"Cannot convert to float: {e}"


def validate_xsd_double(value: Any) -> tuple[bool, Optional[str]]:
    """Validate value can be represented as xsd:double."""
    return validate_xsd_float(value)


def validate_xsd_boolean(value: Any) -> tuple[bool, Optional[str]]:
    """Validate value can be represented as xsd:boolean."""
    if isinstance(value, bool):
        return True, None
    
    if isinstance(value, str):
        if value.lower() in ("true", "false", "1", "0"):
            return True, None
    
    if isinstance(value, (int, float)):
        if value in (0, 1):
            return True, None
    
    return False, f"Cannot convert '{value}' to boolean"


def validate_xsd_date(value: Any) -> tuple[bool, Optional[str]]:
    """Validate value can be represented as xsd:date."""
    if isinstance(value, date) and not isinstance(value, datetime):
        return True, None
    
    if isinstance(value, str):
        # Basic ISO 8601 date format validation
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        if re.match(date_pattern, value):
            try:
                # Validate it's a real date
                year, month, day = map(int, value.split('-'))
                date(year, month, day)
                return True, None
            except ValueError as e:
                return False, f"Invalid date: {e}"
        return False, f"Date must be in YYYY-MM-DD format, got '{value}'"
    
    return False, f"Cannot convert type {type(value).__name__} to date"


def validate_xsd_datetime(value: Any) -> tuple[bool, Optional[str]]:
    """Validate value can be represented as xsd:dateTime."""
    if isinstance(value, datetime):
        return True, None
    
    if isinstance(value, str):
        # Basic ISO 8601 datetime format validation
        datetime_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
        if re.match(datetime_pattern, value):
            return True, None
        return False, f"DateTime must be in ISO 8601 format, got '{value}'"
    
    return False, f"Cannot convert type {type(value).__name__} to dateTime"


def validate_xsd_time(value: Any) -> tuple[bool, Optional[str]]:
    """Validate value can be represented as xsd:time."""
    if isinstance(value, str):
        # Basic time format validation HH:MM:SS
        time_pattern = r'^\d{2}:\d{2}:\d{2}$'
        if re.match(time_pattern, value):
            return True, None
        return False, f"Time must be in HH:MM:SS format, got '{value}'"
    
    return False, f"Cannot convert type {type(value).__name__} to time"


def validate_xsd_anyuri(value: Any) -> tuple[bool, Optional[str]]:
    """Validate value can be represented as xsd:anyURI."""
    if not isinstance(value, str):
        return False, "URI must be a string"
    
    # Basic URI validation
    uri_pattern = r'^[a-zA-Z][a-zA-Z0-9+.-]*:'
    if not re.match(uri_pattern, value):
        return False, f"Invalid URI format: '{value}' (must have a scheme)"
    
    # Check for invalid characters
    if any(c in value for c in [' ', '<', '>', '"', '{', '}', '|', '\\', '^', '`']):
        return False, f"URI contains invalid characters: '{value}'"
    
    return True, None


# Mapping of XSD datatype URIs to validation functions
DATATYPE_VALIDATORS = {
    "http://www.w3.org/2001/XMLSchema#string": validate_xsd_string,
    "http://www.w3.org/2001/XMLSchema#integer": validate_xsd_integer,
    "http://www.w3.org/2001/XMLSchema#int": validate_xsd_integer,
    "http://www.w3.org/2001/XMLSchema#long": validate_xsd_integer,
    "http://www.w3.org/2001/XMLSchema#short": validate_xsd_integer,
    "http://www.w3.org/2001/XMLSchema#decimal": validate_xsd_decimal,
    "http://www.w3.org/2001/XMLSchema#float": validate_xsd_float,
    "http://www.w3.org/2001/XMLSchema#double": validate_xsd_double,
    "http://www.w3.org/2001/XMLSchema#boolean": validate_xsd_boolean,
    "http://www.w3.org/2001/XMLSchema#date": validate_xsd_date,
    "http://www.w3.org/2001/XMLSchema#dateTime": validate_xsd_datetime,
    "http://www.w3.org/2001/XMLSchema#time": validate_xsd_time,
    "http://www.w3.org/2001/XMLSchema#anyURI": validate_xsd_anyuri,
}


def validate_datatype(value: Any, datatype: str) -> tuple[bool, Optional[str]]:
    """Validate a value against an XSD datatype.
    
    Args:
        value: Value to validate
        datatype: XSD datatype URI or CURIE (e.g., "xsd:string")
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Handle CURIE format
    if ":" in datatype and not datatype.startswith("http"):
        prefix, local = datatype.split(":", 1)
        if prefix == "xsd":
            datatype = f"http://www.w3.org/2001/XMLSchema#{local}"
    
    validator = DATATYPE_VALIDATORS.get(datatype)
    if validator:
        return validator(value)
    
    # Unknown datatype - allow it (permissive)
    return True, None
