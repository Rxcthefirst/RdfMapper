"""Tests for transformation functions."""

import pytest
from decimal import Decimal
from datetime import datetime

from rdfmap.transforms.functions import (
    to_decimal,
    to_integer,
    to_date,
    to_datetime,
    to_boolean,
    uppercase,
    lowercase,
    strip,
    apply_transform,
)


class TestToDecimal:
    """Tests for to_decimal transform."""
    
    def test_decimal_from_string(self):
        assert to_decimal("123.45") == Decimal("123.45")
    
    def test_decimal_from_int(self):
        assert to_decimal(100) == Decimal("100")
    
    def test_decimal_from_float(self):
        assert to_decimal(99.99) == Decimal("99.99")
    
    def test_decimal_with_currency_symbols(self):
        assert to_decimal("$1,234.56") == Decimal("1234.56")
        assert to_decimal("€500.00") == Decimal("500.00")
    
    def test_decimal_empty_value(self):
        with pytest.raises(ValueError):
            to_decimal("")
    
    def test_decimal_invalid_value(self):
        with pytest.raises(ValueError):
            to_decimal("not a number")


class TestToInteger:
    """Tests for to_integer transform."""
    
    def test_integer_from_string(self):
        assert to_integer("42") == 42
    
    def test_integer_from_float(self):
        assert to_integer(42.9) == 42
    
    def test_integer_with_commas(self):
        assert to_integer("1,000") == 1000
    
    def test_integer_empty_value(self):
        with pytest.raises(ValueError):
            to_integer("")
    
    def test_integer_invalid_value(self):
        with pytest.raises(ValueError):
            to_integer("not a number")


class TestToDate:
    """Tests for to_date transform."""
    
    def test_date_from_iso_string(self):
        assert to_date("2023-06-15") == "2023-06-15"
    
    def test_date_from_us_format(self):
        result = to_date("06/15/2023")
        assert result == "2023-06-15"
    
    def test_date_from_datetime(self):
        dt = datetime(2023, 6, 15, 10, 30)
        assert to_date(dt) == "2023-06-15"
    
    def test_date_empty_value(self):
        with pytest.raises(ValueError):
            to_date("")
    
    def test_date_invalid_value(self):
        with pytest.raises(ValueError):
            to_date("not a date")


class TestToDatetime:
    """Tests for to_datetime transform."""
    
    def test_datetime_from_iso_string(self):
        result = to_datetime("2023-06-15T10:30:00Z")
        assert "2023-06-15" in result
        assert "10:30:00" in result
    
    def test_datetime_adds_timezone(self):
        result = to_datetime("2023-06-15 10:30:00")
        # Should add UTC timezone if none present
        assert "+" in result or "Z" in result or result.endswith("+00:00")


class TestToBoolean:
    """Tests for to_boolean transform."""
    
    def test_boolean_from_true_strings(self):
        for val in ["true", "True", "TRUE", "yes", "Yes", "1", "t", "y"]:
            assert to_boolean(val) is True
    
    def test_boolean_from_false_strings(self):
        for val in ["false", "False", "FALSE", "no", "No", "0", "f", "n"]:
            assert to_boolean(val) is False
    
    def test_boolean_from_int(self):
        assert to_boolean(1) is True
        assert to_boolean(0) is False
    
    def test_boolean_invalid_value(self):
        with pytest.raises(ValueError):
            to_boolean("maybe")


class TestStringTransforms:
    """Tests for string transformation functions."""
    
    def test_uppercase(self):
        assert uppercase("hello") == "HELLO"
        assert uppercase("Hello World") == "HELLO WORLD"
    
    def test_lowercase(self):
        assert lowercase("HELLO") == "hello"
        assert lowercase("Hello World") == "hello world"
    
    def test_strip(self):
        assert strip("  hello  ") == "hello"
        assert strip("\thello\n") == "hello"


class TestApplyTransform:
    """Tests for apply_transform function."""
    
    def test_apply_valid_transform(self):
        result = apply_transform("123.45", "to_decimal")
        assert result == Decimal("123.45")
    
    def test_apply_unknown_transform(self):
        with pytest.raises(ValueError, match="Unknown transform"):
            apply_transform("value", "nonexistent_transform")
