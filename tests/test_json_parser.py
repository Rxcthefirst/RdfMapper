"""Tests for JSON Parser with nested object handling.

This module tests the JSONParser's ability to parse nested JSON structures
and expand arrays correctly.
"""

import pytest
import json
from pathlib import Path
import polars as pl

from rdfmap.parsers.data_source import JSONParser


@pytest.fixture
def sample_nested_json(tmp_path):
    """Create a sample nested JSON file for testing."""
    data = [
        {
            "student_id": "S001",
            "name": "John Doe",
            "courses": [
                {"course_code": "CS101", "course_title": "Intro to CS", "grade": "A"},
                {"course_code": "MATH201", "course_title": "Calculus", "grade": "B"}
            ]
        },
        {
            "student_id": "S002",
            "name": "Jane Smith",
            "courses": [
                {"course_code": "CS101", "course_title": "Intro to CS", "grade": "A"},
                {"course_code": "ENG101", "course_title": "English", "grade": "A"}
            ]
        }
    ]

    json_file = tmp_path / "students_nested.json"
    with open(json_file, 'w') as f:
        json.dump(data, f)

    return json_file


@pytest.fixture
def sample_flat_json(tmp_path):
    """Create a sample flat JSON file for testing."""
    data = [
        {"id": 1, "name": "Alice", "age": 30},
        {"id": 2, "name": "Bob", "age": 25},
        {"id": 3, "name": "Charlie", "age": 35}
    ]

    json_file = tmp_path / "people_flat.json"
    with open(json_file, 'w') as f:
        json.dump(data, f)

    return json_file


class TestJSONParser:
    """Test suite for JSON Parser."""

    def test_parser_initialization(self, sample_flat_json):
        """Test that parser initializes correctly."""
        parser = JSONParser(sample_flat_json)
        assert parser is not None
        assert parser.file_path == sample_flat_json

    def test_flat_json_parsing(self, sample_flat_json):
        """Test parsing flat JSON structure."""
        parser = JSONParser(sample_flat_json)

        dfs = list(parser.parse())
        assert len(dfs) == 1

        df = dfs[0]
        assert df.shape[0] == 3  # 3 records
        assert 'id' in df.columns
        assert 'name' in df.columns
        assert 'age' in df.columns

    def test_nested_json_parsing(self, sample_nested_json):
        """Test parsing nested JSON with array expansion."""
        parser = JSONParser(sample_nested_json)

        dfs = list(parser.parse())
        assert len(dfs) == 1

        df = dfs[0]

        # Should have columns for nested fields
        assert 'student_id' in df.columns
        assert 'name' in df.columns

        # Check for nested column names (dot notation)
        nested_cols = [col for col in df.columns if 'courses.' in col]
        assert len(nested_cols) > 0, "Should have nested course columns"

    def test_array_expansion(self, sample_nested_json):
        """Test that arrays are properly expanded."""
        parser = JSONParser(sample_nested_json)

        dfs = list(parser.parse())
        df = dfs[0]

        # Count occurrences of each student ID
        # Each student should appear multiple times (once per course)
        student_counts = df['student_id'].value_counts()

        # Both students have 2 courses, so should appear 2 times each
        # Polars value_counts() returns a DataFrame with 'student_id' and 'count' columns
        s001_count = student_counts.filter(pl.col('student_id') == "S001")['count'][0] if len(student_counts.filter(pl.col('student_id') == "S001")) > 0 else 0
        s002_count = student_counts.filter(pl.col('student_id') == "S002")['count'][0] if len(student_counts.filter(pl.col('student_id') == "S002")) > 0 else 0

        assert s001_count == 2
        assert s002_count == 2

    def test_nested_field_values(self, sample_nested_json):
        """Test that nested field values are correctly extracted."""
        parser = JSONParser(sample_nested_json)

        dfs = list(parser.parse())
        df = dfs[0]

        # Find the course code column (might have different naming)
        course_code_col = None
        for col in df.columns:
            if 'course_code' in col.lower():
                course_code_col = col
                break

        assert course_code_col is not None, "Should have course_code column"

        # Check that we have the expected course codes
        course_codes = set(df[course_code_col].to_list())
        expected_codes = {"CS101", "MATH201", "ENG101"}
        assert course_codes == expected_codes

    def test_empty_json(self, tmp_path):
        """Test parsing empty JSON."""
        empty_json = tmp_path / "empty.json"
        with open(empty_json, 'w') as f:
            json.dump([], f)

        parser = JSONParser(empty_json)
        dfs = list(parser.parse())

        # Should return empty dataframe or no dataframes
        assert len(dfs) == 0 or (len(dfs) == 1 and dfs[0].shape[0] == 0)

    def test_single_object_json(self, tmp_path):
        """Test parsing JSON with single object (not array)."""
        single_json = tmp_path / "single.json"
        data = {"id": 1, "name": "Test"}

        with open(single_json, 'w') as f:
            json.dump(data, f)

        parser = JSONParser(single_json)
        dfs = list(parser.parse())

        assert len(dfs) == 1
        df = dfs[0]
        assert df.shape[0] == 1  # Single record


class TestJSONParserEdgeCases:
    """Test edge cases for JSON Parser."""

    def test_deeply_nested_json(self, tmp_path):
        """Test parsing deeply nested JSON structures."""
        data = [
            {
                "id": 1,
                "details": {
                    "personal": {
                        "name": "John",
                        "age": 30
                    },
                    "contact": {
                        "email": "john@example.com"
                    }
                }
            }
        ]

        json_file = tmp_path / "deep_nested.json"
        with open(json_file, 'w') as f:
            json.dump(data, f)

        parser = JSONParser(json_file)
        dfs = list(parser.parse())

        assert len(dfs) == 1
        df = dfs[0]

        # Check that deeply nested fields are accessible
        nested_cols = [col for col in df.columns if '.' in col]
        assert len(nested_cols) > 0, "Should have nested columns"

    def test_mixed_types_in_array(self, tmp_path):
        """Test handling of mixed types in arrays."""
        data = [
            {"id": 1, "values": [1, 2, 3]},
            {"id": 2, "values": ["a", "b", "c"]}
        ]

        json_file = tmp_path / "mixed_types.json"
        with open(json_file, 'w') as f:
            json.dump(data, f)

        parser = JSONParser(json_file)
        dfs = list(parser.parse())

        # Should handle mixed types gracefully
        assert len(dfs) == 1

    def test_null_values(self, tmp_path):
        """Test handling of null values in JSON."""
        data = [
            {"id": 1, "name": "Alice", "age": 30},
            {"id": 2, "name": None, "age": None},
            {"id": 3, "name": "Charlie", "age": 35}
        ]

        json_file = tmp_path / "with_nulls.json"
        with open(json_file, 'w') as f:
            json.dump(data, f)

        parser = JSONParser(json_file)
        dfs = list(parser.parse())

        assert len(dfs) == 1
        df = dfs[0]
        assert df.shape[0] == 3

        # Check that nulls are handled
        assert df['name'].null_count() > 0


@pytest.mark.integration
class TestJSONParserIntegration:
    """Integration tests with real example files."""

    def test_with_example_file(self):
        """Test with actual example file if it exists."""
        example_file = Path('examples/owl2_rdfxml_demo/data/students_nested.json')

        if not example_file.exists():
            pytest.skip("Example file not found")

        parser = JSONParser(example_file)
        dfs = list(parser.parse())

        assert len(dfs) > 0
        df = dfs[0]
        assert df.shape[0] > 0
        assert 'student_id' in df.columns

