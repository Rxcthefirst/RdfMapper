"""Tests for the matcher pipeline architecture."""

import pytest
from rdflib import URIRef

from src.rdfmap.generator.matchers import (
    create_default_pipeline,
    create_exact_only_pipeline,
    create_fast_pipeline,
    MatchContext,
    MatchPriority
)
from src.rdfmap.generator.matchers.exact_matchers import ExactPrefLabelMatcher
from src.rdfmap.generator.matchers.semantic_matcher import SemanticSimilarityMatcher
from src.rdfmap.generator.ontology_analyzer import OntologyProperty
from src.rdfmap.generator.data_analyzer import DataFieldAnalysis


def test_exact_pref_label_matcher():
    """Test exact prefLabel matching."""
    matcher = ExactPrefLabelMatcher()

    column = DataFieldAnalysis("customer_id", "customer_id")
    props = [
        OntologyProperty(
            URIRef("http://ex.org/customerId"),
            pref_label="Customer ID"
        ),
        OntologyProperty(
            URIRef("http://ex.org/productCode"),
            pref_label="Product Code"
        )
    ]

    result = matcher.match(column, props)

    assert result is not None
    assert result.property.uri == URIRef("http://ex.org/customerId")
    assert result.confidence == 1.0
    assert result.matcher_name == "ExactPrefLabelMatcher"
    print(f"✅ Exact prefLabel matching: {result}")


def test_matcher_priority():
    """Test that matchers are sorted by priority."""
    pipeline = create_default_pipeline()

    # First matcher should be highest priority
    assert pipeline.matchers[0].priority() == MatchPriority.CRITICAL

    # Check that matchers are in priority order
    priorities = [m.priority() for m in pipeline.matchers]
    assert priorities == sorted(priorities)
    print(f"✅ Matchers sorted by priority: {priorities}")


def test_pipeline_match():
    """Test that pipeline returns first successful match."""
    pipeline = create_default_pipeline(use_semantic=False)

    column = DataFieldAnalysis("loan_number", "loan_number")
    props = [
        OntologyProperty(
            URIRef("http://ex.org/loanNumber"),
            label="Loan Number"
        )
    ]

    result = pipeline.match(column, props)

    assert result is not None
    assert result.property.uri == URIRef("http://ex.org/loanNumber")
    print(f"✅ Pipeline matching: {result}")


def test_pipeline_match_all():
    """Test getting all possible matches."""
    pipeline = create_default_pipeline(use_semantic=False)

    column = DataFieldAnalysis("loan", "loan")
    props = [
        OntologyProperty(
            URIRef("http://ex.org/loanNumber"),
            label="Loan Number"
        ),
        OntologyProperty(
            URIRef("http://ex.org/loanAmount"),
            label="Loan Amount"
        )
    ]

    # Should find multiple partial matches
    results = pipeline.match_all(column, props, top_k=5)

    assert len(results) >= 1  # At least one match
    # Results should be sorted by confidence
    if len(results) > 1:
        assert results[0].confidence >= results[1].confidence
    print(f"✅ Pipeline match_all: Found {len(results)} matches")


def test_exact_only_pipeline():
    """Test pipeline with only exact matchers."""
    pipeline = create_exact_only_pipeline()

    # Should only have exact matchers
    for matcher in pipeline.matchers:
        assert "Exact" in matcher.name()

    print(f"✅ Exact-only pipeline: {len(pipeline.matchers)} exact matchers")


def test_fast_pipeline():
    """Test fast pipeline without semantic matching."""
    pipeline = create_fast_pipeline()

    # Should not have semantic matcher
    matcher_names = [m.name() for m in pipeline.matchers]
    assert "SemanticSimilarityMatcher" not in matcher_names

    print(f"✅ Fast pipeline: {len(pipeline.matchers)} matchers (no semantic)")


def test_pipeline_stats():
    """Test getting pipeline statistics."""
    pipeline = create_default_pipeline()

    stats = pipeline.get_matcher_stats()

    assert "total_matchers" in stats
    assert "enabled_matchers" in stats
    assert "matchers" in stats
    assert len(stats["matchers"]) > 0

    print(f"✅ Pipeline stats: {stats['total_matchers']} total, {stats['enabled_matchers']} enabled")


def test_add_remove_matcher():
    """Test adding and removing matchers dynamically."""
    pipeline = create_exact_only_pipeline()
    initial_count = len(pipeline.matchers)

    # Add a matcher
    new_matcher = ExactPrefLabelMatcher()
    pipeline.add_matcher(new_matcher)
    assert len(pipeline.matchers) == initial_count + 1

    # Remove it
    pipeline.remove_matcher("ExactPrefLabelMatcher")
    # Should have removed at least one
    assert len(pipeline.matchers) <= initial_count

    print(f"✅ Dynamic add/remove matchers works")


def test_match_context():
    """Test that match context is properly created."""
    column = DataFieldAnalysis("test", "test")
    all_columns = [column]
    props = []

    context = MatchContext(
        column=column,
        all_columns=all_columns,
        available_properties=props,
        domain_hints="finance"
    )

    assert context.column == column
    assert context.domain_hints == "finance"
    print(f"✅ MatchContext created successfully")


if __name__ == "__main__":
    print("Running matcher pipeline tests...\n")
    test_exact_pref_label_matcher()
    test_matcher_priority()
    test_pipeline_match()
    test_pipeline_match_all()
    test_exact_only_pipeline()
    test_fast_pipeline()
    test_pipeline_stats()
    test_add_remove_matcher()
    test_match_context()
    print("\n✅ All matcher pipeline tests passed!")

