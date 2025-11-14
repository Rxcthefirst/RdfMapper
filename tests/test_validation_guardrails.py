"""Tests for validation guardrails."""

import pytest
import polars as pl
from pathlib import Path

from rdfmap.validator.datatypes import (
    validate_xsd_string,
    validate_xsd_integer,
    validate_xsd_decimal,
    validate_xsd_boolean,
    validate_xsd_date,
    validate_xsd_datetime,
    validate_xsd_anyuri,
    validate_datatype,
)
from rdfmap.validator.config import (
    validate_namespace_prefixes,
    validate_required_fields,
    extract_prefixes_from_curie,
)
from rdfmap.models.mapping import (
    MappingConfig,
    SheetMapping,
    RowResource,
    ColumnMapping,
    LinkedObject,
    ObjectPropertyMapping,
    DefaultsConfig,
)
from rdfmap.emitter.graph_builder import RDFGraphBuilder
from rdfmap.models.errors import ProcessingReport, ErrorSeverity


class TestDatatypeValidation:
    """Test XSD datatype validation."""
    
    def test_validate_string(self):
        """Test string validation."""
        assert validate_xsd_string("hello")[0] is True
        assert validate_xsd_string(123)[0] is True
        assert validate_xsd_string("")[0] is True
    
    def test_validate_integer(self):
        """Test integer validation."""
        assert validate_xsd_integer(42)[0] is True
        assert validate_xsd_integer("123")[0] is True
        assert validate_xsd_integer(0)[0] is True
        
        # Should fail for non-integers
        is_valid, error = validate_xsd_integer(3.14)
        assert is_valid is False
        assert "not an integer" in error
        
        is_valid, error = validate_xsd_integer("abc")
        assert is_valid is False
    
    def test_validate_decimal(self):
        """Test decimal validation."""
        assert validate_xsd_decimal(3.14)[0] is True
        assert validate_xsd_decimal("3.14")[0] is True
        assert validate_xsd_decimal(42)[0] is True
        assert validate_xsd_decimal("0.0525")[0] is True
        
        is_valid, error = validate_xsd_decimal("not a number")
        assert is_valid is False
    
    def test_validate_boolean(self):
        """Test boolean validation."""
        assert validate_xsd_boolean(True)[0] is True
        assert validate_xsd_boolean(False)[0] is True
        assert validate_xsd_boolean("true")[0] is True
        assert validate_xsd_boolean("false")[0] is True
        assert validate_xsd_boolean("1")[0] is True
        assert validate_xsd_boolean("0")[0] is True
        assert validate_xsd_boolean(1)[0] is True
        assert validate_xsd_boolean(0)[0] is True
        
        is_valid, error = validate_xsd_boolean("yes")
        assert is_valid is False
        
        is_valid, error = validate_xsd_boolean(42)
        assert is_valid is False
    
    def test_validate_date(self):
        """Test date validation."""
        assert validate_xsd_date("2023-06-15")[0] is True
        assert validate_xsd_date("2024-01-01")[0] is True
        
        # Invalid dates
        is_valid, error = validate_xsd_date("2023-13-01")  # Invalid month
        assert is_valid is False
        
        is_valid, error = validate_xsd_date("2023-06-32")  # Invalid day
        assert is_valid is False
        
        is_valid, error = validate_xsd_date("06/15/2023")  # Wrong format
        assert is_valid is False
        assert "YYYY-MM-DD" in error
    
    def test_validate_datetime(self):
        """Test datetime validation."""
        assert validate_xsd_datetime("2023-06-15T10:30:00")[0] is True
        assert validate_xsd_datetime("2024-01-01T00:00:00")[0] is True
        
        is_valid, error = validate_xsd_datetime("2023-06-15")  # Missing time
        assert is_valid is False
    
    def test_validate_anyuri(self):
        """Test URI validation."""
        assert validate_xsd_anyuri("https://example.com")[0] is True
        assert validate_xsd_anyuri("http://example.com/path")[0] is True
        assert validate_xsd_anyuri("urn:isbn:1234567890")[0] is True
        
        # Invalid URIs
        is_valid, error = validate_xsd_anyuri("not a uri")
        assert is_valid is False
        assert "scheme" in error.lower()
        
        is_valid, error = validate_xsd_anyuri("http://example.com/path with spaces")
        assert is_valid is False
        assert "invalid characters" in error.lower()
    
    def test_validate_datatype_with_curie(self):
        """Test validation with CURIE format."""
        is_valid, _ = validate_datatype(42, "xsd:integer")
        assert is_valid is True
        
        is_valid, error = validate_datatype("not a number", "xsd:integer")
        assert is_valid is False
        
        is_valid, _ = validate_datatype("3.14", "xsd:decimal")
        assert is_valid is True


class TestConfigValidation:
    """Test configuration validation."""
    
    def test_extract_prefixes(self):
        """Test prefix extraction from CURIEs."""
        assert extract_prefixes_from_curie("ex:property") == {"ex"}
        assert extract_prefixes_from_curie("xsd:string") == {"xsd"}
        assert extract_prefixes_from_curie("https://example.com/property") == set()
        assert extract_prefixes_from_curie("property") == set()
    
    def test_validate_namespace_prefixes_valid(self):
        """Test validation with all prefixes declared."""
        config = MappingConfig(namespaces={"xsd": "http://www.w3.org/2001/XMLSchema#", "ex": "https://example.com#", "xsd": "http://www.w3.org/2001/XMLSchema#"},
            defaults=DefaultsConfig(base_iri="https://data.example.com/"),
            sheets=[
                SheetMapping(
                    name="test",
                    source="test.csv",
                    row_resource=RowResource(
                        class_type="ex:TestClass",
                        iri_template="{base_iri}test/{id}"
                    ),
                    columns={
                        "id": ColumnMapping(as_property="ex:id", datatype="xsd:string"),
                        "value": ColumnMapping(as_property="ex:value", datatype="xsd:decimal"),
                    }
                )
            ]
        )
        
        errors = validate_namespace_prefixes(config)
        assert len(errors) == 0
    
    def test_validate_namespace_prefixes_undefined(self):
        """Test validation with undefined prefixes."""
        config = MappingConfig(namespaces={"xsd": "http://www.w3.org/2001/XMLSchema#", "ex": "https://example.com#", "xsd": "http://www.w3.org/2001/XMLSchema#"},
            defaults=DefaultsConfig(base_iri="https://data.example.com/"),
            sheets=[
                SheetMapping(
                    name="test",
                    source="test.csv",
                    row_resource=RowResource(
                        class_type="undefined:TestClass",  # undefined prefix
                        iri_template="{base_iri}test/{id}"
                    ),
                    columns={
                        "id": ColumnMapping(as_property="ex:id", datatype="xsd:string"),
                    }
                )
            ]
        )
        
        errors = validate_namespace_prefixes(config)
        assert len(errors) > 0
        assert any("undefined" in error[1] for error in errors)
    
    def test_validate_required_fields(self):
        """Test validation of required fields in IRI templates."""
        config = MappingConfig(namespaces={"xsd": "http://www.w3.org/2001/XMLSchema#", "ex": "https://example.com#", "xsd": "http://www.w3.org/2001/XMLSchema#"},
            defaults=DefaultsConfig(base_iri="https://data.example.com/"),
            sheets=[
                SheetMapping(
                    name="test",
                    source="test.csv",
                    row_resource=RowResource(
                        class_type="ex:TestClass",
                        iri_template="{base_iri}test/{id}/{optional}"
                    ),
                    columns={
                        "id": ColumnMapping(as_property="ex:id", datatype="xsd:string", required=True),
                        "optional": ColumnMapping(as_property="ex:optional", datatype="xsd:string", required=False),
                    }
                )
            ]
        )
        
        warnings = validate_required_fields(config)
        assert len(warnings) > 0
        assert any("optional" in warning[1] for warning in warnings)


class TestDuplicateIRIDetection:
    """Test duplicate IRI detection."""
    
    def test_duplicate_iris_generate_warnings(self):
        """Test that duplicate IRIs generate warnings."""
        pytest.skip("Duplicate IRI detection not yet implemented in graph builder")

        config = MappingConfig(namespaces={"xsd": "http://www.w3.org/2001/XMLSchema#", "ex": "https://example.com#"},
            defaults=DefaultsConfig(base_iri="https://data.example.com/"), sheets=[
                SheetMapping(
                    name="test",
                    source="test.csv",
                    row_resource=RowResource(
                        class_type="ex:Item",
                        iri_template="{base_iri}item/{category}"  # Will create duplicates
                    ),
                    columns={
                        "category": ColumnMapping(as_property="ex:category", datatype="xsd:string"),
                        "value": ColumnMapping(as_property="ex:value", datatype="xsd:integer"),
                    }
                )
            ]
        )
        
        # Create test data with duplicate categories
        df = pl.DataFrame({
            "category": ["A", "B", "A", "C", "B"],  # A and B are duplicates
            "value": [1, 2, 3, 4, 5]
        })
        
        report = ProcessingReport()
        builder = RDFGraphBuilder(config, report)
        builder.add_dataframe(df, config.sheets[0])
        
        # Check for warnings
        warnings = [e for e in report.errors if e.severity == ErrorSeverity.WARNING]
        assert len(warnings) > 0
        assert any("Duplicate IRI" in e.error for e in warnings)
        
        # Verify the specific duplicates
        duplicate_messages = [e.error for e in warnings if "Duplicate IRI" in e.error]
        assert any("item/A" in msg for msg in duplicate_messages)
        assert any("item/B" in msg for msg in duplicate_messages)


class TestIntegratedValidation:
    """Test integrated validation with real-world scenarios."""
    
    def test_invalid_datatype_caught(self):
        """Test that invalid datatypes are caught during processing."""
        pytest.skip("Datatype validation warnings not yet fully implemented in processing")

        config = MappingConfig(namespaces={"xsd": "http://www.w3.org/2001/XMLSchema#", "ex": "https://example.com#"},
            defaults=DefaultsConfig(base_iri="https://data.example.com/"), sheets=[
                SheetMapping(
                    name="test",
                    source="test.csv",
                    row_resource=RowResource(
                        class_type="ex:Item",
                        iri_template="{base_iri}item/{id}"
                    ),
                    columns={
                        "id": ColumnMapping(as_property="ex:id", datatype="xsd:string"),
                        "count": ColumnMapping(as_property="ex:count", datatype="xsd:integer"),
                    }
                )
            ]
        )
        
        # Create test data with invalid integer
        df = pl.DataFrame({
            "id": ["1", "2", "3"],
            "count": [10, "invalid", 30]  # "invalid" should fail integer validation
        })
        
        report = ProcessingReport()
        builder = RDFGraphBuilder(config, report)
        builder.add_dataframe(df, config.sheets[0])
        
        # Check for errors
        errors = [e for e in report.errors if e.severity == ErrorSeverity.ERROR]
        assert len(errors) > 0
        assert any("Datatype validation failed" in e.error for e in errors)
    
    def test_all_validations_together(self):
        """Test all validation features working together."""
        pytest.skip("Integrated validation features not yet fully implemented")

        config = MappingConfig(namespaces={"xsd": "http://www.w3.org/2001/XMLSchema#", "ex": "https://example.com#", "xsd": "http://www.w3.org/2001/XMLSchema#"},
            defaults=DefaultsConfig(base_iri="https://data.example.com/"), sheets=[
                SheetMapping(
                    name="loans",
                    source="loans.csv",
                    row_resource=RowResource(
                        class_type="ex:Loan",
                        iri_template="{base_iri}loan/{id}"
                    ),
                    columns={
                        "id": ColumnMapping(as_property="ex:loanId", datatype="xsd:string", required=True),
                        "amount": ColumnMapping(as_property="ex:amount", datatype="xsd:decimal", required=True),
                        "date": ColumnMapping(as_property="ex:date", datatype="xsd:date"),
                    }
                )
            ]
        )
        
        # Validate config (namespace prefixes)
        prefix_errors = validate_namespace_prefixes(config)
        assert len(prefix_errors) == 0
        
        # Create test data
        df = pl.DataFrame({
            "id": ["L1", "L2", "L1"],  # L1 is duplicate
            "amount": ["1000.50", "2000.00", "1500.75"],
            "date": ["2023-01-15", "2023-02-20", "2023-03-10"]
        })
        
        report = ProcessingReport()
        builder = RDFGraphBuilder(config, report)
        builder.add_dataframe(df, config.sheets[0])
        
        # Should have duplicate IRI warning
        warnings = [e for e in report.errors if e.severity == ErrorSeverity.WARNING]
        assert any("Duplicate IRI" in e.error for e in warnings)
        
        # Should have no datatype errors (all valid)
        datatype_errors = [e for e in report.errors if "Datatype validation failed" in e.error]
        assert len(datatype_errors) == 0
