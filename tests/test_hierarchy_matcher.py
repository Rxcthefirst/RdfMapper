"""Tests for Property Hierarchy Matcher.

This module tests the PropertyHierarchyMatcher which uses rdfs:subPropertyOf
reasoning to match columns to properties with hierarchy awareness.
"""

import pytest
from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal

from rdfmap.generator.ontology_analyzer import OntologyAnalyzer
from rdfmap.generator.data_analyzer import DataFieldAnalysis
from rdfmap.generator.matchers.hierarchy_matcher import PropertyHierarchyMatcher


@pytest.fixture
def test_ontology_path(tmp_path):
    """Create a test ontology with property hierarchy."""
    g = Graph()
    EX = Namespace("http://example.org/")
    g.bind("ex", EX)

    # Define property hierarchy
    # hasIdentifier (root)
    #   ├── hasName (child of hasIdentifier)
    #   │   ├── hasFullName (child of hasName)
    #   │   ├── hasFirstName (child of hasName)
    #   │   └── hasLastName (child of hasName)
    #   └── hasID (child of hasIdentifier)
    #       └── hasCustomerID (child of hasID)

    # Add properties
    g.add((EX.hasIdentifier, RDF.type, OWL.DatatypeProperty))
    g.add((EX.hasIdentifier, RDFS.label, Literal("has identifier")))

    g.add((EX.hasName, RDF.type, OWL.DatatypeProperty))
    g.add((EX.hasName, RDFS.label, Literal("has name")))
    g.add((EX.hasName, RDFS.subPropertyOf, EX.hasIdentifier))

    g.add((EX.hasFullName, RDF.type, OWL.DatatypeProperty))
    g.add((EX.hasFullName, RDFS.label, Literal("has full name")))
    g.add((EX.hasFullName, RDFS.subPropertyOf, EX.hasName))

    g.add((EX.hasFirstName, RDF.type, OWL.DatatypeProperty))
    g.add((EX.hasFirstName, RDFS.label, Literal("has first name")))
    g.add((EX.hasFirstName, RDFS.subPropertyOf, EX.hasName))

    g.add((EX.hasLastName, RDF.type, OWL.DatatypeProperty))
    g.add((EX.hasLastName, RDFS.label, Literal("has last name")))
    g.add((EX.hasLastName, RDFS.subPropertyOf, EX.hasName))

    g.add((EX.hasID, RDF.type, OWL.DatatypeProperty))
    g.add((EX.hasID, RDFS.label, Literal("has ID")))
    g.add((EX.hasID, RDFS.subPropertyOf, EX.hasIdentifier))

    g.add((EX.hasCustomerID, RDF.type, OWL.DatatypeProperty))
    g.add((EX.hasCustomerID, RDFS.label, Literal("has customer ID")))
    g.add((EX.hasCustomerID, RDFS.subPropertyOf, EX.hasID))

    # Save to file
    onto_path = tmp_path / "test_hierarchy.ttl"
    g.serialize(onto_path, format="turtle")

    return onto_path


@pytest.fixture
def ontology_analyzer(test_ontology_path):
    """Create ontology analyzer from test ontology."""
    return OntologyAnalyzer(str(test_ontology_path))


@pytest.fixture
def hierarchy_matcher(ontology_analyzer):
    """Create hierarchy matcher instance."""
    return PropertyHierarchyMatcher(
        ontology_analyzer=ontology_analyzer,
        enabled=True,
        threshold=0.65,
        hierarchy_boost=0.15
    )


class TestPropertyHierarchyMatcher:
    """Test suite for Property Hierarchy Matcher."""

    def test_hierarchy_cache_built(self, hierarchy_matcher):
        """Test that hierarchy cache is built correctly."""
        assert len(hierarchy_matcher._hierarchy_cache) > 0

        # Check that hasIdentifier is recognized as root
        for uri, info in hierarchy_matcher._hierarchy_cache.items():
            if 'hasIdentifier' in uri:
                assert len(info['parents']) == 0  # Root has no parents
                assert len(info['children']) > 0   # Root has children
                assert info['depth'] == 0

    def test_exact_match_with_hierarchy(self, hierarchy_matcher, ontology_analyzer):
        """Test exact match with hierarchy awareness."""
        column = DataFieldAnalysis("full_name")
        column.sample_values = ["John Doe", "Jane Smith", "Bob Johnson"]
        column.inferred_datatype = "string"

        properties = list(ontology_analyzer.properties.values())
        result = hierarchy_matcher.match(column, properties)

        assert result is not None
        assert result.property.label == "has full name"
        assert result.confidence > 0.95
        assert "hierarchy" in result.matched_via.lower()

    def test_general_term_matching(self, hierarchy_matcher, ontology_analyzer):
        """Test matching general term to property."""
        column = DataFieldAnalysis("name")
        column.sample_values = ["John", "Jane", "Bob"]
        column.inferred_datatype = "string"

        properties = list(ontology_analyzer.properties.values())
        result = hierarchy_matcher.match(column, properties)

        assert result is not None
        # Should match to hasName or one of its children
        assert "name" in result.property.label.lower()
        assert result.confidence > 0.70

    def test_specific_id_matching(self, hierarchy_matcher, ontology_analyzer):
        """Test matching specific ID column."""
        column = DataFieldAnalysis("customer_id")
        column.sample_values = ["C001", "C002", "C003"]
        column.inferred_datatype = "string"

        properties = list(ontology_analyzer.properties.values())
        result = hierarchy_matcher.match(column, properties)

        assert result is not None
        assert "customer" in result.property.label.lower()
        assert result.confidence > 0.95

    def test_hierarchy_info_retrieval(self, hierarchy_matcher, ontology_analyzer):
        """Test getting hierarchy information for a property."""
        # Find hasFullName property
        full_name_prop = None
        for prop in ontology_analyzer.properties.values():
            if prop.label == "has full name":
                full_name_prop = prop
                break

        assert full_name_prop is not None

        hierarchy_info = hierarchy_matcher.get_property_hierarchy_info(full_name_prop)

        assert hierarchy_info['depth'] == 2
        assert hierarchy_info['is_leaf'] == True
        assert hierarchy_info['is_root'] == False
        # Check that parents list exists and contains property objects
        assert 'parents' in hierarchy_info
        assert isinstance(hierarchy_info['parents'], list)

    def test_has_prefix_handling(self, hierarchy_matcher, ontology_analyzer):
        """Test that 'has' prefix is properly handled."""
        # Column without 'has' should match property with 'has'
        column = DataFieldAnalysis("first_name")
        column.sample_values = ["John", "Jane"]
        column.inferred_datatype = "string"

        properties = list(ontology_analyzer.properties.values())
        result = hierarchy_matcher.match(column, properties)

        assert result is not None
        assert "first" in result.property.label.lower()

    def test_no_match_below_threshold(self, hierarchy_matcher, ontology_analyzer):
        """Test that no match is returned when confidence is below threshold."""
        column = DataFieldAnalysis("completely_unrelated_column")
        column.sample_values = ["xyz", "abc"]
        column.inferred_datatype = "string"

        properties = list(ontology_analyzer.properties.values())
        result = hierarchy_matcher.match(column, properties)

        # Should not match anything
        assert result is None or result.confidence < hierarchy_matcher.threshold

    def test_confidence_boosting(self, hierarchy_matcher, ontology_analyzer):
        """Test that hierarchy position boosts confidence."""
        # More specific properties should get higher confidence
        column1 = DataFieldAnalysis("full_name")
        column1.sample_values = ["John Doe"]

        column2 = DataFieldAnalysis("name")
        column2.sample_values = ["John"]

        properties = list(ontology_analyzer.properties.values())

        result1 = hierarchy_matcher.match(column1, properties)
        result2 = hierarchy_matcher.match(column2, properties)

        if result1 and result2:
            # More specific match (hasFullName) should have higher specificity
            info1 = hierarchy_matcher._get_hierarchy_info(result1.property)
            info2 = hierarchy_matcher._get_hierarchy_info(result2.property)

            # hasFullName should be more specific than hasName
            if result1.property.label == "has full name":
                assert info1['specificity'] > info2['specificity']


class TestHierarchyCacheBuilding:
    """Test hierarchy cache building functionality."""

    def test_ancestors_calculation(self, hierarchy_matcher, ontology_analyzer):
        """Test that ancestors are calculated correctly."""
        # hasFullName should have hasName and hasIdentifier as ancestors
        for uri, info in hierarchy_matcher._hierarchy_cache.items():
            if 'hasFullName' in uri:
                assert len(info['ancestors']) == 2
                ancestor_strs = [str(a) for a in info['ancestors']]
                assert any('hasName' in a for a in ancestor_strs)
                assert any('hasIdentifier' in a for a in ancestor_strs)

    def test_descendants_calculation(self, hierarchy_matcher, ontology_analyzer):
        """Test that descendants are calculated correctly."""
        # hasName should have hasFullName, hasFirstName, hasLastName as descendants
        for uri, info in hierarchy_matcher._hierarchy_cache.items():
            if 'hasName' in uri and 'Full' not in uri and 'First' not in uri and 'Last' not in uri:
                assert len(info['descendants']) == 3

    def test_depth_calculation(self, hierarchy_matcher):
        """Test that depth is calculated correctly."""
        for uri, info in hierarchy_matcher._hierarchy_cache.items():
            if 'hasIdentifier' in uri and 'Name' not in uri and 'ID' not in uri:
                # Root should have depth 0
                assert info['depth'] == 0
            elif 'hasFullName' in uri:
                # Leaf should have depth 2
                assert info['depth'] == 2


@pytest.mark.integration
class TestHierarchyMatcherIntegration:
    """Integration tests for hierarchy matcher."""

    def test_matcher_in_pipeline(self, ontology_analyzer):
        """Test that matcher works in a pipeline context."""
        from rdfmap.generator.matchers import create_default_pipeline

        pipeline = create_default_pipeline(
            use_hierarchy=True,
            ontology_analyzer=ontology_analyzer,
            use_semantic=False,
            use_datatype=False,
            use_history=False
        )

        column = DataFieldAnalysis("full_name")
        column.sample_values = ["John Doe"]

        properties = list(ontology_analyzer.properties.values())

        # Pipeline should use hierarchy matcher
        result = pipeline.match(column, properties)

        assert result is not None
        assert result.confidence > 0.70

