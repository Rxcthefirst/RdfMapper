"""Tests for the data type inference matcher."""

import pytest
from rdflib import URIRef, XSD

from src.rdfmap.generator.matchers.datatype_matcher import DataTypeInferenceMatcher
from src.rdfmap.generator.ontology_analyzer import OntologyProperty
from src.rdfmap.generator.data_analyzer import DataFieldAnalysis


def test_integer_type_inference():
    """Test matching based on integer data type."""
    matcher = DataTypeInferenceMatcher()

    # Column with integer values
    column = DataFieldAnalysis("loan_amount", "loan_amount")
    column.sample_values = [250000, 300000, 450000, 125000]
    column.inferred_type = "integer"

    # Properties with different range types
    props = [
        OntologyProperty(
            URIRef("http://ex.org/loanAmount"),
            label="Loan Amount",
            range_type=XSD.integer
        ),
        OntologyProperty(
            URIRef("http://ex.org/loanDescription"),
            label="Loan Description",
            range_type=XSD.string
        )
    ]

    result = matcher.match(column, props)

    assert result is not None
    assert result.property.uri == URIRef("http://ex.org/loanAmount")
    assert result.confidence >= 0.7
    print(f"✅ Integer type match: {result.property.label} (confidence: {result.confidence:.2f})")


def test_decimal_type_inference():
    """Test matching based on decimal data type."""
    matcher = DataTypeInferenceMatcher()

    # Column with decimal values
    column = DataFieldAnalysis("interest_rate", "interest_rate")
    column.sample_values = [0.0525, 0.0375, 0.0425, 0.0675]
    column.inferred_type = "decimal"

    props = [
        OntologyProperty(
            URIRef("http://ex.org/interestRate"),
            label="Interest Rate",
            range_type=XSD.decimal
        ),
        OntologyProperty(
            URIRef("http://ex.org/borrowerName"),
            label="Borrower Name",
            range_type=XSD.string
        )
    ]

    result = matcher.match(column, props)

    assert result is not None
    assert result.property.uri == URIRef("http://ex.org/interestRate")
    print(f"✅ Decimal type match: {result.property.label} (confidence: {result.confidence:.2f})")


def test_string_type_inference():
    """Test matching based on string data type."""
    matcher = DataTypeInferenceMatcher()

    # Column with string values
    column = DataFieldAnalysis("borrower_name", "borrower_name")
    column.sample_values = ["John Smith", "Jane Doe", "Bob Johnson"]
    column.inferred_type = "string"

    props = [
        OntologyProperty(
            URIRef("http://ex.org/borrowerName"),
            label="Borrower Name",
            range_type=XSD.string
        ),
        OntologyProperty(
            URIRef("http://ex.org/loanAmount"),
            label="Loan Amount",
            range_type=XSD.integer
        )
    ]

    result = matcher.match(column, props)

    assert result is not None
    assert result.property.uri == URIRef("http://ex.org/borrowerName")
    print(f"✅ String type match: {result.property.label} (confidence: {result.confidence:.2f})")


def test_date_type_inference():
    """Test matching based on date data type."""
    matcher = DataTypeInferenceMatcher()

    # Column with date values
    column = DataFieldAnalysis("origination_date", "origination_date")
    column.sample_values = ["2023-01-15", "2023-02-20", "2023-03-10"]
    column.inferred_type = "date"

    props = [
        OntologyProperty(
            URIRef("http://ex.org/originationDate"),
            label="Origination Date",
            range_type=XSD.date
        ),
        OntologyProperty(
            URIRef("http://ex.org/loanAmount"),
            label="Loan Amount",
            range_type=XSD.integer
        )
    ]

    result = matcher.match(column, props)

    assert result is not None
    assert result.property.uri == URIRef("http://ex.org/originationDate")
    print(f"✅ Date type match: {result.property.label} (confidence: {result.confidence:.2f})")


def test_type_mismatch_rejected():
    """Test that incompatible types don't match."""
    matcher = DataTypeInferenceMatcher(threshold=0.7)

    # Column with integer values
    column = DataFieldAnalysis("loan_id", "loan_id")
    column.sample_values = [12345, 67890, 11223]
    column.inferred_type = "integer"

    # Only string property available
    props = [
        OntologyProperty(
            URIRef("http://ex.org/description"),
            label="Description",
            range_type=XSD.string
        )
    ]

    result = matcher.match(column, props, None)

    # Should not match or have very low confidence
    if result:
        assert result.confidence < 0.7
    print(f"✅ Type mismatch correctly rejected or low confidence")


def test_numeric_type_compatibility():
    """Test that numeric types are compatible."""
    matcher = DataTypeInferenceMatcher(threshold=0.6)  # Lower threshold for compatibility test

    # Integer column
    column = DataFieldAnalysis("count", "count")
    column.sample_values = [10, 20, 30]
    column.inferred_type = "integer"

    # Decimal property (should be compatible)
    props = [
        OntologyProperty(
            URIRef("http://ex.org/amountValue"),  # Better name match
            label="Amount Value",
            range_type=XSD.decimal
        )
    ]

    result = matcher.match(column, props)

    assert result is not None
    assert result.confidence > 0
    print(f"✅ Numeric compatibility works: integer → decimal (confidence: {result.confidence:.2f})")


def test_property_without_range():
    """Test matching when property has no explicit range type."""
    matcher = DataTypeInferenceMatcher()

    # Column with numeric values
    column = DataFieldAnalysis("price", "price")
    column.sample_values = [100.50, 200.75, 150.25]
    column.inferred_type = "decimal"

    # Property without explicit range but name suggests numeric
    props = [
        OntologyProperty(
            URIRef("http://ex.org/priceAmount"),
            label="Price Amount",
            range_type=None  # No explicit range
        )
    ]

    result = matcher.match(column, props)

    # Should still match based on name inference
    assert result is not None
    print(f"✅ Matches even without explicit range type")


def test_type_inference_from_sample_values():
    """Test type inference when inferred_type is not available."""
    matcher = DataTypeInferenceMatcher()

    # Column without inferred_type but with numeric samples
    column = DataFieldAnalysis("amount", "amount")
    column.sample_values = [100, 200, 300, 400]
    column.inferred_type = None  # Force inference from samples

    # Should still infer integer type
    inferred = matcher._infer_column_type(column)
    assert inferred == "integer"
    print(f"✅ Type inference from sample values works: {inferred}")


if __name__ == "__main__":
    print("Running data type inference matcher tests...\n")
    test_integer_type_inference()
    test_decimal_type_inference()
    test_string_type_inference()
    test_date_type_inference()
    test_type_mismatch_rejected()
    test_numeric_type_compatibility()
    test_property_without_range()
    test_type_inference_from_sample_values()
    print("\n✅ All data type matcher tests passed!")

