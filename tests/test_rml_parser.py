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
        # Parse RML
        parser = RMLParser()
        result = parser.parse(temp_path)

        # Verify structure
        assert 'sheets' in result
        assert 'namespaces' in result
        assert 'defaults' in result

        # Check sheets
        assert len(result['sheets']) == 1
        sheet = result['sheets'][0]

        # Check basic sheet properties
        assert sheet['name'] == 'people'
        assert 'people.csv' in sheet['source']
        # Class should contain Person, prefix may vary (schema, schema1, etc.)
        assert 'Person' in sheet['class']
        assert '$(id)' in sheet['subject_template']  # Converted from {id}

        # Check columns
        assert len(sheet['columns']) == 2

        # Find name column (property may have schema or schema1 prefix)
        name_col = next(c for c in sheet['columns'] if 'name' in c['property'])
        assert name_col['column'] == 'name'

        # Find age column
        age_col = next(c for c in sheet['columns'] if 'age' in c['property'])
        assert age_col['column'] == 'age'
        assert 'integer' in age_col['datatype'].lower()

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

        # Check constant mapping (property may have schema or schema1 prefix)
        sheet = result['sheets'][0]
        nationality_col = next(
            c for c in sheet['columns']
            if 'nationality' in c['property']
        )
        assert nationality_col['constant'] == 'USA'

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

        # Should have 2 sheets
        assert len(result['sheets']) == 2

        # Check both sheets
        sheet_names = {s['name'] for s in result['sheets']}
        assert 'people' in sheet_names
        assert 'companies' in sheet_names

        # Verify classes (check for Person and Organization in class strings)
        person_sheet = next(s for s in result['sheets'] if s['name'] == 'people')
        company_sheet = next(s for s in result['sheets'] if s['name'] == 'companies')

        assert 'Person' in person_sheet['class']
        assert 'Organization' in company_sheet['class']

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

