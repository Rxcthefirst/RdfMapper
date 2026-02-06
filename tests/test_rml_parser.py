"""Tests for RML parser."""

import pytest
from pathlib import Path
from rdfmap.config.rml_parser import RMLParser, parse_rml


def test_rml_parser_basic():
    """Test basic RML parsing."""
    # Create a simple RML mapping
    rml_content = """
@prefix rr: <http://www.w3.org/ns/r2rml#>.
@prefix rml: <http://semweb.mmlab.be/ns/rml#>.
@prefix ql: <http://semweb.mmlab.be/ns/ql#>.
@prefix schema: <http://schema.org/>.
@prefix ex: <http://example.org/>.

<#PersonMapping>
    a rr:TriplesMap;
    
    rml:logicalSource [
        rml:source "data/people.csv";
        rml:referenceFormulation ql:CSV
    ];
    
    rr:subjectMap [
        rr:template "http://example.org/person/{id}";
        rr:class schema:Person
    ];
    
    rr:predicateObjectMap [
        rr:predicate schema:name;
        rr:objectMap [ rml:reference "name" ]
    ];
    
    rr:predicateObjectMap [
        rr:predicate schema:age;
        rr:objectMap [ 
            rml:reference "age";
            rr:datatype <http://www.w3.org/2001/XMLSchema#integer>
        ]
    ].
"""

    # Write to temp file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as f:
        f.write(rml_content)
        temp_path = Path(f.name)

    try:
        # Parse RML (now returns v3 format)
        parser = RMLParser()
        result = parser.parse(temp_path)

        # Verify v3 structure
        assert 'sources' in result
        assert 'mappings' in result
        assert 'namespaces' in result
        assert 'base_iri' in result

        # Check sources
        assert len(result['sources']) >= 1
        source_name = list(result['sources'].keys())[0]
        source = result['sources'][source_name]
        assert 'people.csv' in source['path']
        assert source['format'] == 'csv'

        # Check mappings
        assert len(result['mappings']) >= 1
        mapping_name = list(result['mappings'].keys())[0]
        mapping = result['mappings'][mapping_name]

        # Check subject (v3 format)
        assert 'subject' in mapping
        assert 'Person' in mapping['subject']['class']
        assert '{id}' in mapping['subject']['iri_template']  # RML uses {column} format

        # V3 format uses properties dict
        assert 'properties' in mapping
        assert len(mapping['properties']) == 2

        # Find name property
        assert 'name' in mapping['properties']
        assert 'name' in mapping['properties']['name']['predicate']

        # Find age property
        assert 'age' in mapping['properties']
        assert 'age' in mapping['properties']['age']['predicate']
        assert 'integer' in mapping['properties']['age']['datatype'].lower()

        # Check namespaces - should have a schema namespace (http or https)
        schema_namespaces = [
            v for k, v in result['namespaces'].items()
            if 'schema.org' in v
        ]
        assert len(schema_namespaces) > 0

    finally:
        # Cleanup
        temp_path.unlink()


def test_rml_parser_with_constants():
    """Test RML parsing with constant values."""
    rml_content = """
@prefix rr: <http://www.w3.org/ns/r2rml#>.
@prefix rml: <http://semweb.mmlab.be/ns/rml#>.
@prefix ql: <http://semweb.mmlab.be/ns/ql#>.
@prefix schema: <http://schema.org/>.

<#PersonMapping>
    a rr:TriplesMap;
    
    rml:logicalSource [
        rml:source "people.csv";
        rml:referenceFormulation ql:CSV
    ];
    
    rr:subjectMap [
        rr:template "http://example.org/person/{id}";
        rr:class schema:Person
    ];
    
    rr:predicateObjectMap [
        rr:predicate schema:nationality;
        rr:objectMap [ rr:constant "USA" ]
    ].
"""

    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as f:
        f.write(rml_content)
        temp_path = Path(f.name)

    try:
        result = parse_rml(temp_path)

        # Check v3 format structure
        assert 'mappings' in result
        mapping = list(result['mappings'].values())[0]

        # Constants are stored in properties dict with generated names
        # Look for the nationality property
        nationality_found = False
        for col_name, prop_def in mapping['properties'].items():
            if 'nationality' in prop_def['predicate']:
                assert prop_def['default'] == 'USA'
                nationality_found = True
                break

        assert nationality_found, "Nationality property with constant 'USA' not found"

    finally:
        temp_path.unlink()


def test_rml_parser_multiple_triples_maps():
    """Test parsing RML with multiple triples maps."""
    rml_content = """
@prefix rr: <http://www.w3.org/ns/r2rml#>.
@prefix rml: <http://semweb.mmlab.be/ns/rml#>.
@prefix ql: <http://semweb.mmlab.be/ns/ql#>.
@prefix schema: <http://schema.org/>.

<#PersonMapping>
    a rr:TriplesMap;
    rml:logicalSource [
        rml:source "people.csv";
        rml:referenceFormulation ql:CSV
    ];
    rr:subjectMap [
        rr:template "http://example.org/person/{id}";
        rr:class schema:Person
    ];
    rr:predicateObjectMap [
        rr:predicate schema:name;
        rr:objectMap [ rml:reference "name" ]
    ].

<#CompanyMapping>
    a rr:TriplesMap;
    rml:logicalSource [
        rml:source "companies.csv";
        rml:referenceFormulation ql:CSV
    ];
    rr:subjectMap [
        rr:template "http://example.org/company/{id}";
        rr:class schema:Organization
    ];
    rr:predicateObjectMap [
        rr:predicate schema:name;
        rr:objectMap [ rml:reference "company_name" ]
    ].
"""

    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as f:
        f.write(rml_content)
        temp_path = Path(f.name)

    try:
        result = parse_rml(temp_path)

        # Should have 2 sources and 2 mappings in v3 format
        assert len(result['sources']) == 2
        assert len(result['mappings']) == 2

        # Check mapping names
        mapping_names = set(result['mappings'].keys())
        assert 'people' in mapping_names or 'persons' in mapping_names
        assert 'companies' in mapping_names

        # Verify classes in v3 format (subject.class)
        for mapping_name, mapping in result['mappings'].items():
            if 'people' in mapping_name.lower() or 'person' in mapping_name.lower():
                assert 'Person' in mapping['subject']['class']
            elif 'compan' in mapping_name.lower():
                assert 'Organization' in mapping['subject']['class']

    finally:
        temp_path.unlink()


if __name__ == '__main__':
    # Run tests
    test_rml_parser_basic()
    print("✅ Basic RML parsing test passed")

    test_rml_parser_with_constants()
    print("✅ Constants test passed")

    test_rml_parser_multiple_triples_maps()
    print("✅ Multiple triples maps test passed")

    print("\n🎉 All RML parser tests passed!")

