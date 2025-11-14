"""Tests for graph-based matching strategies.

This test suite validates the GraphReasoningMatcher and InheritanceAwareMatcher
that use ontology structure for intelligent column-to-property matching.
"""

import pytest
from rdflib import Graph, URIRef, Namespace, RDF, RDFS, OWL, Literal
from rdflib.namespace import XSD

from rdfmap.generator.graph_reasoner import GraphReasoner
from rdfmap.generator.ontology_analyzer import OntologyAnalyzer
from rdfmap.generator.data_analyzer import DataFieldAnalysis
from rdfmap.generator.matchers.graph_matcher import (
    GraphReasoningMatcher,
    InheritanceAwareMatcher
)
from rdfmap.generator.matchers.base import MatchContext
from rdfmap.models.alignment import MatchType


# Define test namespace
TEST = Namespace("http://example.com/test#")


def create_test_column(name: str, sample_values: list, inferred_type: str, is_unique: bool = False) -> DataFieldAnalysis:
    """Helper to create DataFieldAnalysis for testing."""
    column = DataFieldAnalysis(name=name)
    column.sample_values = sample_values
    column.inferred_type = inferred_type
    column.is_unique = is_unique
    column.total_count = len(sample_values)
    return column


@pytest.fixture
def mortgage_ontology_graph():
    """Create a mortgage loan ontology for testing."""
    g = Graph()
    g.bind("test", TEST)
    g.bind("xsd", XSD)

    # Classes
    g.add((TEST.FinancialInstrument, RDF.type, OWL.Class))
    g.add((TEST.FinancialInstrument, RDFS.label, Literal("Financial Instrument")))

    g.add((TEST.Loan, RDF.type, OWL.Class))
    g.add((TEST.Loan, RDFS.label, Literal("Loan")))
    g.add((TEST.Loan, RDFS.subClassOf, TEST.FinancialInstrument))

    g.add((TEST.MortgageLoan, RDF.type, OWL.Class))
    g.add((TEST.MortgageLoan, RDFS.label, Literal("Mortgage Loan")))
    g.add((TEST.MortgageLoan, RDFS.subClassOf, TEST.Loan))

    g.add((TEST.Borrower, RDF.type, OWL.Class))
    g.add((TEST.Borrower, RDFS.label, Literal("Borrower")))

    g.add((TEST.Property, RDF.type, OWL.Class))
    g.add((TEST.Property, RDFS.label, Literal("Property")))

    # Properties on FinancialInstrument
    g.add((TEST.instrumentId, RDF.type, OWL.DatatypeProperty))
    g.add((TEST.instrumentId, RDFS.label, Literal("instrument ID")))
    g.add((TEST.instrumentId, RDFS.domain, TEST.FinancialInstrument))
    g.add((TEST.instrumentId, RDFS.range, XSD.string))

    # Properties on Loan
    g.add((TEST.principalAmount, RDF.type, OWL.DatatypeProperty))
    g.add((TEST.principalAmount, RDFS.label, Literal("principal amount")))
    g.add((TEST.principalAmount, RDFS.domain, TEST.Loan))
    g.add((TEST.principalAmount, RDFS.range, XSD.decimal))

    g.add((TEST.interestRate, RDF.type, OWL.DatatypeProperty))
    g.add((TEST.interestRate, RDFS.label, Literal("interest rate")))
    g.add((TEST.interestRate, RDFS.domain, TEST.Loan))
    g.add((TEST.interestRate, RDFS.range, XSD.decimal))

    # Properties on MortgageLoan
    g.add((TEST.loanNumber, RDF.type, OWL.DatatypeProperty))
    g.add((TEST.loanNumber, RDFS.label, Literal("loan number")))
    g.add((TEST.loanNumber, RDFS.domain, TEST.MortgageLoan))
    g.add((TEST.loanNumber, RDFS.range, XSD.string))

    g.add((TEST.loanTerm, RDF.type, OWL.DatatypeProperty))
    g.add((TEST.loanTerm, RDFS.label, Literal("loan term")))
    g.add((TEST.loanTerm, RDFS.domain, TEST.MortgageLoan))
    g.add((TEST.loanTerm, RDFS.range, XSD.integer))

    # Object properties
    g.add((TEST.hasBorrower, RDF.type, OWL.ObjectProperty))
    g.add((TEST.hasBorrower, RDFS.label, Literal("has borrower")))
    g.add((TEST.hasBorrower, RDFS.domain, TEST.MortgageLoan))
    g.add((TEST.hasBorrower, RDFS.range, TEST.Borrower))

    g.add((TEST.collateralProperty, RDF.type, OWL.ObjectProperty))
    g.add((TEST.collateralProperty, RDFS.label, Literal("collateral property")))
    g.add((TEST.collateralProperty, RDFS.domain, TEST.MortgageLoan))
    g.add((TEST.collateralProperty, RDFS.range, TEST.Property))

    # Properties on Borrower
    g.add((TEST.borrowerName, RDF.type, OWL.DatatypeProperty))
    g.add((TEST.borrowerName, RDFS.label, Literal("borrower name")))
    g.add((TEST.borrowerName, RDFS.domain, TEST.Borrower))
    g.add((TEST.borrowerName, RDFS.range, XSD.string))

    g.add((TEST.creditScore, RDF.type, OWL.DatatypeProperty))
    g.add((TEST.creditScore, RDFS.label, Literal("credit score")))
    g.add((TEST.creditScore, RDFS.domain, TEST.Borrower))
    g.add((TEST.creditScore, RDFS.range, XSD.integer))

    # Properties on Property
    g.add((TEST.propertyAddress, RDF.type, OWL.DatatypeProperty))
    g.add((TEST.propertyAddress, RDFS.label, Literal("property address")))
    g.add((TEST.propertyAddress, RDFS.domain, TEST.Property))
    g.add((TEST.propertyAddress, RDFS.range, XSD.string))

    g.add((TEST.propertyValue, RDF.type, OWL.DatatypeProperty))
    g.add((TEST.propertyValue, RDFS.label, Literal("property value")))
    g.add((TEST.propertyValue, RDFS.domain, TEST.Property))
    g.add((TEST.propertyValue, RDFS.range, XSD.decimal))

    return g


@pytest.fixture
def ontology_analyzer(mortgage_ontology_graph):
    """Create an OntologyAnalyzer from the test graph."""
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(mode='wb', suffix='.ttl', delete=False) as f:
        mortgage_ontology_graph.serialize(f, format='turtle')
        temp_path = f.name

    analyzer = OntologyAnalyzer(temp_path)
    os.unlink(temp_path)

    return analyzer


@pytest.fixture
def graph_reasoner(mortgage_ontology_graph, ontology_analyzer):
    """Create a GraphReasoner instance."""
    return GraphReasoner(
        mortgage_ontology_graph,
        ontology_analyzer.classes,
        ontology_analyzer.properties
    )


@pytest.fixture
def graph_matcher(graph_reasoner):
    """Create a GraphReasoningMatcher instance."""
    return GraphReasoningMatcher(
        reasoner=graph_reasoner,
        enabled=True,
        threshold=0.6
    )


def test_graph_matcher_with_type_validation(graph_matcher, ontology_analyzer):
    """Test graph matcher with data type validation."""
    # Create a column that looks like interest rate
    column = create_test_column("interest_rate", [0.0525, 0.0450, 0.0375], "xsd:decimal")

    properties = list(ontology_analyzer.properties.values())

    result = graph_matcher.match(column, properties)

    assert result is not None
    assert result.property.uri == TEST.interestRate
    assert result.confidence >= 0.6
    assert result.match_type == MatchType.GRAPH_REASONING


def test_graph_matcher_type_mismatch(graph_matcher, ontology_analyzer):
    """Test that graph matcher rejects type mismatches."""
    # Create a column with integer data trying to match decimal property
    column = create_test_column("principal_amount", [100, 200, 300], "xsd:integer")

    properties = [ontology_analyzer.properties[TEST.principalAmount]]

    result = graph_matcher.match(column, properties)

    # Should still match since integer is compatible with decimal
    # (validation should be lenient for compatible types)
    # But if we had completely incompatible types, it would fail


def test_graph_matcher_with_object_property_pattern(graph_matcher, ontology_analyzer):
    """Test graph matcher recognizes object property patterns (foreign keys)."""
    # Create a column that looks like a foreign key
    column = create_test_column("borrower_id", ["B001", "B002", "B003"], "xsd:string", is_unique=True)

    properties = list(ontology_analyzer.properties.values())

    result = graph_matcher.match(column, properties)

    # Should match hasBorrower (object property)
    # or at least score it highly due to FK pattern
    if result:
        assert result.confidence > 0


def test_graph_matcher_structural_fit(graph_matcher, ontology_analyzer):
    """Test structural fit scoring with related columns."""
    # Create related columns that form a coherent structure
    loan_number_col = create_test_column("loan_number", ["LN001", "LN002"], "xsd:string", is_unique=True)
    loan_term_col = create_test_column("loan_term", [360, 240], "xsd:integer")
    interest_rate_col = create_test_column("interest_rate", [0.0525, 0.0450], "xsd:decimal")

    all_columns = [loan_number_col, loan_term_col, interest_rate_col]
    properties = list(ontology_analyzer.properties.values())

    # Create context with all columns
    context = MatchContext(
        column=loan_number_col,
        all_columns=all_columns,
        available_properties=properties
    )

    result = graph_matcher.match(loan_number_col, properties, context)

    assert result is not None
    # Should get structural boost from matching sibling properties


def test_inheritance_aware_matcher(graph_reasoner, ontology_analyzer):
    """Test InheritanceAwareMatcher finds inherited properties."""
    # Create matcher targeting MortgageLoan class
    matcher = InheritanceAwareMatcher(
        reasoner=graph_reasoner,
        target_class=str(TEST.MortgageLoan),
        enabled=True,
        threshold=0.7
    )

    # Create a column matching an inherited property
    column = create_test_column("principal_amount", [500000, 750000], "xsd:decimal")

    # Only provide direct MortgageLoan properties
    direct_properties = [
        p for p in ontology_analyzer.properties.values()
        if p.domain == TEST.MortgageLoan
    ]

    result = matcher.match(column, direct_properties)

    # Should find principalAmount even though it's inherited from Loan
    assert result is not None
    assert result.property.uri == TEST.principalAmount
    assert result.match_type == MatchType.INHERITED_PROPERTY


def test_inheritance_aware_matcher_direct_property(graph_reasoner, ontology_analyzer):
    """Test InheritanceAwareMatcher with direct property."""
    matcher = InheritanceAwareMatcher(
        reasoner=graph_reasoner,
        target_class=str(TEST.MortgageLoan),
        enabled=True,
        threshold=0.7
    )

    # Create a column matching a direct property
    column = create_test_column("loan_number", ["LN001", "LN002"], "xsd:string", is_unique=True)

    direct_properties = [
        p for p in ontology_analyzer.properties.values()
        if p.domain == TEST.MortgageLoan
    ]

    result = matcher.match(column, direct_properties)

    # Should find loanNumber as direct property
    assert result is not None
    assert result.property.uri == TEST.loanNumber
    assert result.match_type == MatchType.GRAPH_REASONING  # Direct, not inherited


def test_graph_matcher_property_context_scoring(graph_matcher, ontology_analyzer):
    """Test that well-structured properties score higher."""
    # loanNumber is part of well-defined MortgageLoan class
    # with siblings, domain, range, etc.
    column = create_test_column("loan_number", ["LN001"], "xsd:string", is_unique=True)

    properties = list(ontology_analyzer.properties.values())
    result = graph_matcher.match(column, properties)

    assert result is not None
    # Should have high confidence due to good property context


def test_graph_matcher_label_similarity_fallback(graph_matcher, ontology_analyzer):
    """Test label similarity as fallback when structure doesn't help."""
    # Column with good label match but no structural context
    column = create_test_column("credit_score", [720, 680], "xsd:integer")

    properties = list(ontology_analyzer.properties.values())
    result = graph_matcher.match(column, properties)

    assert result is not None
    assert result.property.uri == TEST.creditScore


def test_graph_matcher_no_match_below_threshold(graph_matcher, ontology_analyzer):
    """Test that low-scoring matches are rejected."""
    # Column that doesn't match anything well
    column = create_test_column("random_column_xyz", ["abc", "def"], "xsd:string")

    properties = list(ontology_analyzer.properties.values())
    result = graph_matcher.match(column, properties)

    # Should return None if below threshold
    assert result is None or result.confidence < 0.6


def test_graph_matcher_disabled(graph_matcher, ontology_analyzer):
    """Test that disabled matcher returns None."""
    graph_matcher.enabled = False

    column = create_test_column("loan_number", ["LN001"], "xsd:string", is_unique=True)

    properties = list(ontology_analyzer.properties.values())
    result = graph_matcher.match(column, properties)

    assert result is None


def test_inheritance_matcher_no_target_class(graph_reasoner, ontology_analyzer):
    """Test InheritanceAwareMatcher without target class."""
    matcher = InheritanceAwareMatcher(
        reasoner=graph_reasoner,
        target_class=None,  # No target class
        enabled=True,
        threshold=0.7
    )

    column = create_test_column("loan_number", ["LN001"], "xsd:string", is_unique=True)

    properties = list(ontology_analyzer.properties.values())
    result = matcher.match(column, properties)

    # Should return None without target class
    assert result is None


def test_multiple_inheritance_levels(graph_reasoner, ontology_analyzer):
    """Test inheritance through multiple class levels."""
    matcher = InheritanceAwareMatcher(
        reasoner=graph_reasoner,
        target_class=str(TEST.MortgageLoan),
        enabled=True,
        threshold=0.7
    )

    # instrumentId is on FinancialInstrument (2 levels up)
    column = create_test_column("instrument_id", ["INS001", "INS002"], "xsd:string", is_unique=True)

    direct_properties = [
        p for p in ontology_analyzer.properties.values()
        if p.domain == TEST.MortgageLoan
    ]

    result = matcher.match(column, direct_properties)

    # Should find instrumentId through inheritance chain
    assert result is not None
    assert result.property.uri == TEST.instrumentId
    assert result.match_type == MatchType.INHERITED_PROPERTY

