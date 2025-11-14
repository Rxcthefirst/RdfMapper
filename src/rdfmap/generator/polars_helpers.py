"""Polars-compatible helper functions for data analysis."""

import re
from typing import Optional
import polars as pl


def _infer_polars_type(column: pl.Series) -> str:
    """Infer the Polars data type."""
    dtype = column.dtype

    if dtype in [pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64]:
        return 'integer'
    elif dtype in [pl.Float32, pl.Float64]:
        return 'float'
    elif dtype == pl.Boolean:
        return 'boolean'
    elif dtype in [pl.Date, pl.Datetime]:
        return 'datetime'
    else:
        return 'string'


def _suggest_xsd_datatype_polars(column: pl.Series) -> str:
    """Suggest appropriate XSD datatype for Polars column."""
    sample_values = column.drop_nulls().head(20).to_list()

    if len(sample_values) == 0:
        return "xsd:string"

    # Check for specific patterns first
    for value in sample_values:
        str_val = str(value)

        # Date patterns
        if re.match(r'^\d{4}-\d{2}-\d{2}$', str_val):
            return "xsd:date"
        elif re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', str_val):
            return "xsd:dateTime"

    # Infer from Polars dtype
    dtype = column.dtype

    if dtype in [pl.Int8, pl.Int16, pl.Int32, pl.Int64]:
        return "xsd:integer"
    elif dtype in [pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64]:
        return "xsd:nonNegativeInteger"
    elif dtype in [pl.Float32, pl.Float64]:
        return "xsd:decimal"
    elif dtype == pl.Boolean:
        return "xsd:boolean"
    elif dtype in [pl.Date]:
        return "xsd:date"
    elif dtype in [pl.Datetime]:
        return "xsd:dateTime"
    else:
        return "xsd:string"


def _is_likely_identifier_polars(col_name: str, column: pl.Series) -> bool:
    """Check if column is likely an identifier using Polars."""
    # Name-based heuristics
    name_lower = col_name.lower()
    if any(keyword in name_lower for keyword in ['id', 'key', 'uuid', 'guid', 'number']):
        return True

    # Value-based heuristics
    non_null = column.drop_nulls()
    if len(non_null) == 0:
        return False

    # Check uniqueness
    if non_null.n_unique() == len(non_null):
        return True

    return False


def _detect_pattern_polars(column: pl.Series) -> Optional[str]:
    """Detect common patterns in Polars column values."""
    sample_values = [str(v) for v in column.drop_nulls().head(20).to_list()]

    if not sample_values:
        return None

    # Common patterns
    patterns = {
        r'^\d{3}-\d{2}-\d{4}$': 'SSN',
        r'^\d{10}$': 'Phone (10 digit)',
        r'^\(\d{3}\) \d{3}-\d{4}$': 'Phone (formatted)',
        r'^[A-Z]{2}\d{4}$': 'State code + number',
        r'^\d{5}(-\d{4})?$': 'ZIP code',
        r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$': 'Email',
    }

    for pattern, description in patterns.items():
        if all(re.match(pattern, val) for val in sample_values):
            return description

    return None
