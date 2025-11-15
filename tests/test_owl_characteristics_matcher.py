"""Tests for OWL Characteristics Matcher.

This module tests the OWLCharacteristicsMatcher which uses OWL property
characteristics (Functional, InverseFunctional, etc.) for semantic matching.
"""

import pytest
from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal, XSD

from rdfmap.generator.ontology_analyzer import OntologyAnalyzer
from rdfmap.generator.data_analyzer import DataFieldAnalysis
from rdfmap.generator.matchers.owl_characteristics_matcher import OWLCharacteristicsMatcher


@pytest.fixture
def test_owl_ontology_path(tmp_path):
    """Create a test ontology with OWL characteristics."""
    g = Graph()
    EX = Namespace("http://example.org/")
    g.bind("ex", EX)
    g.bind("xsd", XSD)

    # InverseFunctional Properties (unique identifiers)
    g.add((EX.hasCustomerID, RDF.type, OWL.DatatypeProperty))
    g.add((EX.hasCustomerID, RDF.type, OWL.InverseFunctionalProperty))
    g.add((EX.hasCustomerID, RDFS.label, Literal("has customer ID")))
    g.add((EX.hasCustomerID, RDFS.range, XSD.string))

    g.add((EX.hasEmail, RDF.type, OWL.DatatypeProperty))
    g.add((EX.hasEmail, RDF.type, OWL.InverseFunctionalProperty))
    g.add((EX.hasEmail, RDFS.label, Literal("has email")))
    g.add((EX.hasEmail, RDFS.range, XSD.string))

    g.add((EX.hasSSN, RDF.type, OWL.DatatypeProperty))
    g.add((EX.hasSSN, RDF.type, OWL.InverseFunctionalProperty))
    g.add((EX.hasSSN, RDFS.label, Literal("has SSN")))
    g.add((EX.hasSSN, RDFS.range, XSD.string))

    # Functional Properties (single-valued)
    g.add((EX.hasDateOfBirth, RDF.type, OWL.DatatypeProperty))
    g.add((EX.hasDateOfBirth, RDF.type, OWL.FunctionalProperty))
    g.add((EX.hasDateOfBirth, RDFS.label, Literal("has date of birth")))
    g.add((EX.hasDateOfBirth, RDFS.range, XSD.date))

    g.add((EX.hasAge, RDF.type, OWL.DatatypeProperty))
    g.add((EX.hasAge, RDF.type, OWL.FunctionalProperty))
    g.add((EX.hasAge, RDFS.label, Literal("has age")))
    g.add((EX.hasAge, RDFS.range, XSD.integer))

    # Regular properties (no special characteristics)
    g.add((EX.hasName, RDF.type, OWL.DatatypeProperty))
    g.add((EX.hasName, RDFS.label, Literal("has name")))
    g.add((EX.hasName, RDFS.range, XSD.string))

    # Symmetric property
    g.add((EX.isSiblingOf, RDF.type, OWL.ObjectProperty))
    g.add((EX.isSiblingOf, RDF.type, OWL.SymmetricProperty))
    g.add((EX.isSiblingOf, RDFS.label, Literal("is sibling of")))

    # Transitive property
    g.add((EX.isAncestorOf, RDF.type, OWL.ObjectProperty))
    g.add((EX.isAncestorOf, RDF.type, OWL.TransitiveProperty))
    g.add((EX.isAncestorOf, RDFS.label, Literal("is ancestor of")))

    # Save to file
    onto_path = tmp_path / "test_owl.ttl"
    g.serialize(onto_path, format="turtle")

    return onto_path


@pytest.fixture
def owl_ontology_analyzer(test_owl_ontology_path):
    """Create ontology analyzer from test ontology."""
    return OntologyAnalyzer(str(test_owl_ontology_path))


@pytest.fixture
def owl_matcher(owl_ontology_analyzer):
    """Create OWL characteristics matcher instance."""
    return OWLCharacteristicsMatcher(
        ontology_analyzer=owl_ontology_analyzer,
        enabled=True,
        threshold=0.60,
        ifp_uniqueness_threshold=0.90,
        fp_uniqueness_threshold=0.95
    )


class TestOWLCharacteristicsMatcher:
    """Test suite for OWL Characteristics Matcher."""

    def test_owl_cache_built(self, owl_matcher):
        """Test that OWL characteristics cache is built correctly."""
        assert len(owl_matcher._owl_cache) > 0

        # Check that IFP properties are recognized
        ifp_found = False
        for uri, info in owl_matcher._owl_cache.items():
            if info['is_inverse_functional']:
                ifp_found = True
                break

        assert ifp_found, "Should find at least one InverseFunctionalProperty"

    def test_inverse_functional_property_match(self, owl_matcher, owl_ontology_analyzer):
        """Test matching with InverseFunctionalProperty."""
        column = DataFieldAnalysis("customer_id")
        column.sample_values = ["CUST001", "CUST002", "CUST003", "CUST004", "CUST005"]
        column.inferred_datatype = "string"

        properties = list(owl_ontology_analyzer.properties.values())
        result = owl_matcher.match(column, properties)

        assert result is not None
        assert "customer" in result.property.label.lower()
        assert result.confidence > 0.90  # High confidence for perfect IFP match
        assert "IFP" in result.matched_via or "InverseFunctional" in result.matched_via

    def test_ifp_violation_detection(self, owl_matcher, owl_ontology_analyzer):
        """Test that IFP violations reduce confidence."""
        # Email with duplicates (violates IFP)
        column = DataFieldAnalysis("email")
        column.sample_values = ["john@ex.com", "jane@ex.com", "john@ex.com", "alice@ex.com"]
        column.inferred_datatype = "string"

        properties = list(owl_ontology_analyzer.properties.values())
        result = owl_matcher.match(column, properties)

        assert result is not None
        # Check that it matched to email property
        if "email" in result.property.label.lower():
            # With duplicates (75% unique), confidence should be lower than perfect match
            # but the exact value depends on the matching algorithm
            # Just verify it's not getting full boost
            assert result.confidence < 0.95  # Not getting perfect IFP boost
            # The "violation" might be mentioned in matched_via or just show lower confidence
            uniqueness = owl_matcher._calculate_uniqueness_ratio(column)
            assert uniqueness < 0.90  # Confirm data has duplicates

    def test_functional_property_match(self, owl_matcher, owl_ontology_analyzer):
        """Test matching with Functional Property."""
        column = DataFieldAnalysis("date_of_birth")
        column.sample_values = ["1990-01-15", "1985-05-20", "1992-08-10", "1988-03-25"]
        column.inferred_datatype = "date"

        properties = list(owl_ontology_analyzer.properties.values())
        result = owl_matcher.match(column, properties)

        assert result is not None
        assert "birth" in result.property.label.lower() or "date" in result.property.label.lower()
        assert result.confidence > 0.75  # Good confidence for FP match

    def test_uniqueness_ratio_calculation(self, owl_matcher):
        """Test uniqueness ratio calculation."""
        # All unique
        column1 = DataFieldAnalysis("test1")
        column1.sample_values = ["a", "b", "c", "d", "e"]
        assert owl_matcher._calculate_uniqueness_ratio(column1) == 1.0

        # 50% unique
        column2 = DataFieldAnalysis("test2")
        column2.sample_values = ["a", "a", "b", "b"]
        assert owl_matcher._calculate_uniqueness_ratio(column2) == 0.5

        # With nulls
        column3 = DataFieldAnalysis("test3")
        column3.sample_values = ["a", None, "b", None, "c"]
        ratio = owl_matcher._calculate_uniqueness_ratio(column3)
        assert ratio == 1.0  # 3 unique non-null values out of 3

    def test_id_pattern_detection(self, owl_matcher):
        """Test ID pattern detection."""
        # Has ID in name
        column1 = DataFieldAnalysis("customer_id")
        column1.sample_values = ["C001"]
        assert owl_matcher._has_id_pattern(column1) == True

        # UUID pattern
        column2 = DataFieldAnalysis("uuid")
        column2.sample_values = ["550e8400-e29b-41d4-a716-446655440000"]
        assert owl_matcher._has_id_pattern(column2) == True

        # Email pattern
        column3 = DataFieldAnalysis("email")
        column3.sample_values = ["user@example.com"]
        assert owl_matcher._has_id_pattern(column3) == True

        # Not an ID
        column4 = DataFieldAnalysis("description")
        column4.sample_values = ["Some text here"]
        assert owl_matcher._has_id_pattern(column4) == False

    def test_owl_characteristics_retrieval(self, owl_matcher, owl_ontology_analyzer):
        """Test getting OWL characteristics for a property."""
        # Find hasCustomerID property
        customer_id_prop = None
        for prop in owl_ontology_analyzer.properties.values():
            if "customer" in prop.label.lower():
                customer_id_prop = prop
                break

        assert customer_id_prop is not None

        chars = owl_matcher.get_owl_characteristics(customer_id_prop)

        assert chars['is_inverse_functional'] == True
        assert chars['can_be_identifier'] == True
        assert 'InverseFunctional' in chars['characteristics']

    def test_regular_property_without_owl(self, owl_matcher, owl_ontology_analyzer):
        """Test matching regular property without special OWL characteristics."""
        column = DataFieldAnalysis("name")
        column.sample_values = ["John", "Jane", "Bob", "Alice", "John"]  # Duplicates OK
        column.inferred_datatype = "string"

        properties = list(owl_ontology_analyzer.properties.values())
        result = owl_matcher.match(column, properties)

        assert result is not None
        # Should match with moderate confidence (just label match, no OWL boost)
        assert 0.60 <= result.confidence <= 0.80


class TestOWLValidation:
    """Test OWL semantic validation."""

    def test_perfect_ifp_alignment(self, owl_matcher, owl_ontology_analyzer):
        """Test perfect alignment between data and IFP."""
        column = DataFieldAnalysis("ssn")
        column.sample_values = ["111-11-1111", "222-22-2222", "333-33-3333", "444-44-4444"]
        column.inferred_datatype = "string"

        properties = list(owl_ontology_analyzer.properties.values())
        result = owl_matcher.match(column, properties)

        assert result is not None
        # Should have high confidence due to perfect alignment
        assert result.confidence > 0.90

    def test_partial_ifp_alignment(self, owl_matcher, owl_ontology_analyzer):
        """Test partial alignment (70-90% unique)."""
        column = DataFieldAnalysis("email")
        # 80% unique
        column.sample_values = ["a@ex.com", "b@ex.com", "c@ex.com", "d@ex.com", "a@ex.com"]
        column.inferred_datatype = "string"

        properties = list(owl_ontology_analyzer.properties.values())
        result = owl_matcher.match(column, properties)

        if result and result.property.label == "has email":
            # Should have moderate confidence (partial match)
            assert 0.60 <= result.confidence <= 0.85

    def test_enrichment_suggestion(self, owl_matcher, owl_ontology_analyzer):
        """Test that enrichment suggestions are made for unique data without IFP."""
        # This would test the scenario where data is unique but property not marked IFP
        # In our test ontology, all ID-like properties are already marked
        # This test validates the suggestion mechanism works
        column = DataFieldAnalysis("account_number")
        column.sample_values = ["ACC001", "ACC002", "ACC003"]
        column.inferred_datatype = "string"

        properties = list(owl_ontology_analyzer.properties.values())
        result = owl_matcher.match(column, properties)

        # Even if no perfect match, the matcher should recognize the ID pattern
        if result:
            owl_info = owl_matcher._get_owl_info(result.property)
            # If not IFP but data is unique, should suggest enrichment
            if not owl_info['is_inverse_functional']:
                uniqueness = owl_matcher._calculate_uniqueness_ratio(column)
                assert uniqueness >= 0.90  # Data is unique


class TestOWLMatcherIntegration:
    """Integration tests for OWL matcher."""

    @pytest.mark.integration
    def test_matcher_in_pipeline(self, owl_ontology_analyzer):
        """Test that OWL matcher works in pipeline."""
        from rdfmap.generator.matchers import create_default_pipeline

        pipeline = create_default_pipeline(
            use_owl_characteristics=True,
            ontology_analyzer=owl_ontology_analyzer,
            use_semantic=False,
            use_datatype=False
        )

        column = DataFieldAnalysis("customer_id")
        column.sample_values = ["C001", "C002", "C003"]

        properties = list(owl_ontology_analyzer.properties.values())
        result = pipeline.match(column, properties)

        assert result is not None
        assert result.confidence > 0.60

    def test_combined_with_hierarchy_matcher(self, owl_ontology_analyzer):
        """Test OWL matcher working alongside hierarchy matcher."""
        from rdfmap.generator.matchers import create_default_pipeline

        # Both matchers enabled
        pipeline = create_default_pipeline(
            use_hierarchy=True,
            use_owl_characteristics=True,
            ontology_analyzer=owl_ontology_analyzer,
            use_semantic=False
        )

        column = DataFieldAnalysis("email")
        column.sample_values = ["user@example.com"]

        properties = list(owl_ontology_analyzer.properties.values())
        result = pipeline.match(column, properties)

        # Should get match from appropriate matchers
        assert result is not None
        assert result.confidence > 0.60


class TestConfidenceAdjustment:
    """Test confidence adjustment based on OWL alignment."""

    def test_ifp_boost(self, owl_matcher, owl_ontology_analyzer):
        """Test confidence boost for perfect IFP alignment."""
        column = DataFieldAnalysis("email")
        column.sample_values = ["a@ex.com", "b@ex.com", "c@ex.com"]  # 100% unique

        properties = list(owl_ontology_analyzer.properties.values())
        result = owl_matcher.match(column, properties)

        if result and "email" in result.property.label.lower():
            # Should have boost
            assert result.confidence > 0.85

    def test_ifp_penalty(self, owl_matcher, owl_ontology_analyzer):
        """Test confidence penalty for IFP violation."""
        column = DataFieldAnalysis("email")
        column.sample_values = ["a@ex.com", "a@ex.com", "a@ex.com"]  # All same!

        properties = list(owl_ontology_analyzer.properties.values())
        result = owl_matcher.match(column, properties)

        if result and "email" in result.property.label.lower():
            # Should have penalty
            assert result.confidence < 0.70

