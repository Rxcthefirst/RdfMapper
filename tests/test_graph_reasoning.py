"""Tests for graph reasoning engine.

This test suite validates the deep ontology reasoning capabilities,
including class hierarchies, property inheritance, domain/range validation,
and semantic path finding.
"""

import pytest
from rdflib import Graph, URIRef, Namespace, RDF, RDFS, OWL, Literal
from rdflib.namespace import XSD

from rdfmap.generator.graph_reasoner import GraphReasoner, SemanticPath, PropertyContext
from rdfmap.generator.ontology_analyzer import OntologyAnalyzer, OntologyClass, OntologyProperty


# Define test namespace
TEST = Namespace("http://example.com/test#")


@pytest.fixture
def test_ontology_graph():
    """Create a test ontology with class hierarchy and properties."""
    g = Graph()
    g.bind("test", TEST)
    g.bind("xsd", XSD)

    # Define class hierarchy: Thing -> Person -> Employee
    g.add((TEST.Thing, RDF.type, OWL.Class))
    g.add((TEST.Thing, RDFS.label, Literal("Thing")))

    g.add((TEST.Person, RDF.type, OWL.Class))
    g.add((TEST.Person, RDFS.label, Literal("Person")))
    g.add((TEST.Person, RDFS.subClassOf, TEST.Thing))

    g.add((TEST.Employee, RDF.type, OWL.Class))
    g.add((TEST.Employee, RDFS.label, Literal("Employee")))
    g.add((TEST.Employee, RDFS.subClassOf, TEST.Person))

    g.add((TEST.Department, RDF.type, OWL.Class))
    g.add((TEST.Department, RDFS.label, Literal("Department")))

    # Properties on Thing
    g.add((TEST.identifier, RDF.type, OWL.DatatypeProperty))
    g.add((TEST.identifier, RDFS.label, Literal("identifier")))
    g.add((TEST.identifier, RDFS.domain, TEST.Thing))
    g.add((TEST.identifier, RDFS.range, XSD.string))

    # Properties on Person
    g.add((TEST.name, RDF.type, OWL.DatatypeProperty))
    g.add((TEST.name, RDFS.label, Literal("name")))
    g.add((TEST.name, RDFS.domain, TEST.Person))
    g.add((TEST.name, RDFS.range, XSD.string))

    g.add((TEST.age, RDF.type, OWL.DatatypeProperty))
    g.add((TEST.age, RDFS.label, Literal("age")))
    g.add((TEST.age, RDFS.domain, TEST.Person))
    g.add((TEST.age, RDFS.range, XSD.integer))

    # Properties on Employee
    g.add((TEST.employeeId, RDF.type, OWL.DatatypeProperty))
    g.add((TEST.employeeId, RDFS.label, Literal("employee ID")))
    g.add((TEST.employeeId, RDFS.domain, TEST.Employee))
    g.add((TEST.employeeId, RDFS.range, XSD.string))

    g.add((TEST.salary, RDF.type, OWL.DatatypeProperty))
    g.add((TEST.salary, RDFS.label, Literal("salary")))
    g.add((TEST.salary, RDFS.domain, TEST.Employee))
    g.add((TEST.salary, RDFS.range, XSD.decimal))

    # Object property: Employee -> Department
    g.add((TEST.worksIn, RDF.type, OWL.ObjectProperty))
    g.add((TEST.worksIn, RDFS.label, Literal("works in")))
    g.add((TEST.worksIn, RDFS.domain, TEST.Employee))
    g.add((TEST.worksIn, RDFS.range, TEST.Department))

    # Property on Department
    g.add((TEST.departmentName, RDF.type, OWL.DatatypeProperty))
    g.add((TEST.departmentName, RDFS.label, Literal("department name")))
    g.add((TEST.departmentName, RDFS.domain, TEST.Department))
    g.add((TEST.departmentName, RDFS.range, XSD.string))

    # Property hierarchy: hasName -> name
    g.add((TEST.hasName, RDF.type, OWL.DatatypeProperty))
    g.add((TEST.hasName, RDFS.label, Literal("has name")))
    g.add((TEST.hasName, RDFS.domain, TEST.Thing))
    g.add((TEST.hasName, RDFS.range, XSD.string))
    g.add((TEST.name, RDFS.subPropertyOf, TEST.hasName))

    return g


@pytest.fixture
def ontology_analyzer(test_ontology_graph):
    """Create an OntologyAnalyzer from the test graph."""
    # Save graph to temp file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.ttl', delete=False) as f:
        test_ontology_graph.serialize(f, format='turtle')
        temp_path = f.name

    analyzer = OntologyAnalyzer(temp_path)

    # Cleanup
    import os
    os.unlink(temp_path)

    return analyzer


@pytest.fixture
def graph_reasoner(test_ontology_graph, ontology_analyzer):
    """Create a GraphReasoner instance."""
    return GraphReasoner(
        test_ontology_graph,
        ontology_analyzer.classes,
        ontology_analyzer.properties
    )


def test_get_all_ancestors(graph_reasoner):
    """Test finding all ancestor classes."""
    # Employee should have ancestors: Person, Thing
    ancestors = graph_reasoner.get_all_ancestors(TEST.Employee)

    assert TEST.Person in ancestors
    assert TEST.Thing in ancestors
    assert len(ancestors) == 2

    # Person should have ancestor: Thing
    ancestors = graph_reasoner.get_all_ancestors(TEST.Person)
    assert TEST.Thing in ancestors
    assert len(ancestors) == 1

    # Thing should have no ancestors
    ancestors = graph_reasoner.get_all_ancestors(TEST.Thing)
    assert len(ancestors) == 0


def test_get_all_descendants(graph_reasoner):
    """Test finding all descendant classes."""
    # Thing should have descendants: Person, Employee
    descendants = graph_reasoner.get_all_descendants(TEST.Thing)

    assert TEST.Person in descendants
    assert TEST.Employee in descendants
    assert len(descendants) == 2

    # Person should have descendant: Employee
    descendants = graph_reasoner.get_all_descendants(TEST.Person)
    assert TEST.Employee in descendants
    assert len(descendants) == 1

    # Employee should have no descendants
    descendants = graph_reasoner.get_all_descendants(TEST.Employee)
    assert len(descendants) == 0


def test_get_inherited_properties(graph_reasoner):
    """Test property inheritance from parent classes."""
    # Employee should have:
    # - Own properties: employeeId, salary, worksIn
    # - Inherited from Person: name, age
    # - Inherited from Thing: identifier, hasName

    inherited_props = graph_reasoner.get_inherited_properties(TEST.Employee)
    prop_uris = {p.uri for p in inherited_props}

    # Own properties
    assert TEST.employeeId in prop_uris
    assert TEST.salary in prop_uris
    assert TEST.worksIn in prop_uris

    # Inherited from Person
    assert TEST.name in prop_uris
    assert TEST.age in prop_uris

    # Inherited from Thing
    assert TEST.identifier in prop_uris
    assert TEST.hasName in prop_uris

    # Should have 7 total properties
    assert len(inherited_props) == 7


def test_find_property_by_domain_and_range(graph_reasoner):
    """Test finding properties by domain and range."""
    # Find properties from Employee to decimal
    props = graph_reasoner.find_property_by_domain_and_range(
        TEST.Employee,
        XSD.decimal,
        allow_subclasses=False
    )

    assert len(props) == 1
    assert props[0].uri == TEST.salary

    # Find object properties from Employee to Department
    props = graph_reasoner.find_property_by_domain_and_range(
        TEST.Employee,
        TEST.Department,
        allow_subclasses=False
    )

    assert len(props) == 1
    assert props[0].uri == TEST.worksIn


def test_get_property_context(graph_reasoner):
    """Test getting rich property context."""
    # Get context for 'name' property
    context = graph_reasoner.get_property_context(TEST.name)

    assert context.property.uri == TEST.name

    # Should have parent property: hasName
    parent_uris = {p.uri for p in context.parent_properties}
    assert TEST.hasName in parent_uris

    # Should have sibling property: age (same domain)
    sibling_uris = {p.uri for p in context.sibling_properties}
    assert TEST.age in sibling_uris

    # Should have domain ancestors
    assert TEST.Thing in context.domain_ancestors

    # Should have range info
    assert context.range_info == XSD.string


def test_get_property_context_with_object_property(graph_reasoner):
    """Test property context for Employee properties."""
    context = graph_reasoner.get_property_context(TEST.salary)

    # Sibling properties: employeeId
    sibling_uris = {p.uri for p in context.sibling_properties}
    assert TEST.employeeId in sibling_uris

    # Related via object properties: worksIn -> Department
    related_classes = {cls for _, cls in context.related_via_object_props}
    assert TEST.Department in related_classes


def test_find_semantic_path(graph_reasoner):
    """Test finding semantic paths through the ontology."""
    # Find path from Employee to departmentName
    # Path should be: Employee -> (worksIn) -> Department -> departmentName

    path = graph_reasoner.find_semantic_path(
        TEST.Employee,
        TEST.departmentName,
        max_hops=3
    )

    assert path is not None
    assert path.start == TEST.Employee
    assert path.end == TEST.Department  # departmentName's domain
    assert path.hops > 0
    assert path.confidence > 0


def test_get_related_properties(graph_reasoner):
    """Test finding related properties."""
    related = graph_reasoner.get_related_properties(TEST.name)

    # Should have sibling: age
    assert "sibling" in related
    sibling_uris = {p.uri for p in related["sibling"]}
    assert TEST.age in sibling_uris

    # Should have parent: hasName
    assert "parent" in related
    parent_uris = {p.uri for p in related["parent"]}
    assert TEST.hasName in parent_uris


def test_validate_property_for_data_type(graph_reasoner, ontology_analyzer):
    """Test data type validation."""
    # Get properties
    age_prop = ontology_analyzer.properties[TEST.age]
    name_prop = ontology_analyzer.properties[TEST.name]

    # age property with integer range should match xsd:integer
    is_valid, confidence = graph_reasoner.validate_property_for_data_type(
        age_prop,
        "xsd:integer"
    )
    assert is_valid
    assert confidence >= 0.8  # Should be high confidence (compatible or exact)

    # name property with string range should match xsd:string
    is_valid, confidence = graph_reasoner.validate_property_for_data_type(
        name_prop,
        "xsd:string"
    )
    assert is_valid
    assert confidence >= 0.8  # Should be high confidence (compatible or exact)

    # age property should NOT match string type
    is_valid, confidence = graph_reasoner.validate_property_for_data_type(
        age_prop,
        "xsd:string"
    )
    # Should still be valid but with low confidence (or invalid)
    assert confidence < 1.0


def test_explain_property_choice(graph_reasoner, ontology_analyzer):
    """Test generating human-readable explanations."""
    # Get property
    salary_prop = ontology_analyzer.properties[TEST.salary]

    explanation = graph_reasoner.explain_property_choice(
        salary_prop,
        context_class=TEST.Employee
    )

    assert "salary" in explanation.lower()
    assert "employee" in explanation.lower() or "domain" in explanation.lower()
    assert "decimal" in explanation.lower() or "datatype" in explanation.lower()


def test_property_context_no_siblings(graph_reasoner):
    """Test property context when there are no sibling properties."""
    # departmentName is the only property for Department class
    context = graph_reasoner.get_property_context(TEST.departmentName)

    assert context.property.uri == TEST.departmentName
    assert len(context.sibling_properties) == 0


def test_inherited_properties_no_duplicates(graph_reasoner):
    """Test that inherited properties don't include duplicates."""
    inherited = graph_reasoner.get_inherited_properties(TEST.Employee)

    # Check for duplicates
    uri_list = [p.uri for p in inherited]
    uri_set = set(uri_list)

    assert len(uri_list) == len(uri_set), "Duplicate properties found"


def test_subproperty_relationships(graph_reasoner):
    """Test subPropertyOf indexing."""
    # name is subPropertyOf hasName
    related = graph_reasoner.get_related_properties(TEST.name, ["parent"])

    assert "parent" in related
    parent_uris = {p.uri for p in related["parent"]}
    assert TEST.hasName in parent_uris

    # hasName should have name as child
    related = graph_reasoner.get_related_properties(TEST.hasName, ["child"])

    assert "child" in related
    child_uris = {p.uri for p in related["child"]}
    assert TEST.name in child_uris


def test_reasoner_with_empty_ontology():
    """Test reasoner behavior with minimal ontology."""
    g = Graph()
    classes = {}
    properties = {}

    reasoner = GraphReasoner(g, classes, properties)

    # Should not crash, just return empty results
    ancestors = reasoner.get_all_ancestors(URIRef("http://example.com/test#Dummy"))
    assert len(ancestors) == 0

    inherited = reasoner.get_inherited_properties(URIRef("http://example.com/test#Dummy"))
    assert len(inherited) == 0

