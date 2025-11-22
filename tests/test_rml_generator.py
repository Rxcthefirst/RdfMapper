"""Tests for RML generator and roundtrip conversion."""

import pytest
from pathlib import Path
from rdfmap.config.rml_generator import RMLGenerator, generate_rml, internal_to_rml
from rdfmap.config.rml_parser import parse_rml
import json


def test_rml_generator_basic():
    """Test basic RML generation from internal format."""
    internal_config = {
        'namespaces': {
            'ex': 'http://example.org/',
            'schema': 'http://schema.org/',
            'xsd': 'http://www.w3.org/2001/XMLSchema#',
        },
        'defaults': {
            'base_iri': 'http://example.org/'
        },
        'sheets': [
            {
                'name': 'people',
                'source': 'people.csv',
                'format': 'csv',
                'class': 'schema:Person',
                'subject_template': 'http://example.org/person/$(id)',
                'columns': [
                    {
                        'column': 'name',
                        'property': 'schema:name',
                    },
                    {
                        'column': 'age',
                        'property': 'schema:age',
                        'datatype': 'xsd:integer',
                    }
                ]
            }
        ]
    }

    # Generate RML
    rml_content = generate_rml(internal_config)

    # Verify it's valid Turtle
    assert '@prefix' in rml_content
    assert 'rml:' in rml_content or 'http://semweb.mmlab.be/ns/rml#' in rml_content
    assert 'rr:' in rml_content or 'http://www.w3.org/ns/r2rml#' in rml_content

    # Verify content
    assert 'people.csv' in rml_content
    assert 'Person' in rml_content
    assert '{id}' in rml_content  # Should convert $(id) to {id}

    print("✅ Basic RML generation works")
    print(f"\nGenerated RML:\n{rml_content[:500]}...")


def test_rml_generator_with_constants():
    """Test RML generation with constant values."""
    internal_config = {
        'namespaces': {
            'schema': 'http://schema.org/',
        },
        'defaults': {
            'base_iri': 'http://example.org/'
        },
        'sheets': [
            {
                'name': 'people',
                'source': 'people.csv',
                'format': 'csv',
                'class': 'schema:Person',
                'subject_template': 'http://example.org/person/$(id)',
                'columns': [
                    {
                        'column': 'name',
                        'property': 'schema:name',
                    },
                    {
                        'constant': 'USA',
                        'property': 'schema:nationality',
                    }
                ]
            }
        ]
    }

    rml_content = generate_rml(internal_config)

    # Verify constant is in output
    assert 'USA' in rml_content
    assert 'rr:constant' in rml_content or 'constant' in rml_content.lower()

    print("✅ Constant values work")


def test_rml_roundtrip():
    """Test roundtrip: internal → RML → internal."""
    original_config = {
        'namespaces': {
            'ex': 'http://example.org/',
            'schema': 'http://schema.org/',
            'xsd': 'http://www.w3.org/2001/XMLSchema#',
        },
        'defaults': {
            'base_iri': 'http://example.org/'
        },
        'sheets': [
            {
                'name': 'people',
                'source': 'people.csv',
                'format': 'csv',
                'class': 'schema:Person',
                'subject_template': 'http://example.org/person/$(id)',
                'columns': [
                    {
                        'column': 'name',
                        'property': 'schema:name',
                    },
                    {
                        'column': 'age',
                        'property': 'schema:age',
                        'datatype': 'xsd:integer',
                    }
                ]
            }
        ]
    }

    # Generate RML
    rml_content = generate_rml(original_config)

    # Save to temp file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as f:
        f.write(rml_content)
        temp_path = Path(f.name)

    try:
        # Parse back
        parsed_config = parse_rml(temp_path)

        # Verify key elements are preserved
        assert len(parsed_config['sheets']) == 1
        sheet = parsed_config['sheets'][0]

        assert sheet['name'] == 'people'
        assert 'people.csv' in sheet['source']
        assert 'Person' in sheet['class']
        assert len(sheet['columns']) == 2

        # Find columns
        name_col = next((c for c in sheet['columns'] if 'name' in c['property']), None)
        age_col = next((c for c in sheet['columns'] if 'age' in c['property']), None)

        assert name_col is not None
        assert name_col['column'] == 'name'

        assert age_col is not None
        assert age_col['column'] == 'age'
        assert 'integer' in age_col.get('datatype', '').lower()

        print("✅ Roundtrip conversion preserves data")

    finally:
        temp_path.unlink()


def test_rml_generator_with_alignment_report():
    """Test that alignment report is kept separate from RML."""
    internal_config = {
        'namespaces': {
            'schema': 'http://schema.org/',
        },
        'defaults': {
            'base_iri': 'http://example.org/'
        },
        'sheets': [
            {
                'name': 'people',
                'source': 'people.csv',
                'format': 'csv',
                'class': 'schema:Person',
                'subject_template': 'http://example.org/person/$(id)',
                'columns': [
                    {
                        'column': 'name',
                        'property': 'schema:name',
                    }
                ]
            }
        ]
    }

    alignment_report = {
        'generated_at': '2025-11-21T10:00:00',
        'statistics': {
            'total_columns': 5,
            'mapped_columns': 4,
            'unmapped_columns': 1,
        },
        'match_details': [
            {
                'column_name': 'name',
                'property': 'schema:name',
                'confidence': 0.95,
                'matcher_name': 'SemanticSimilarityMatcher',
            }
        ]
    }

    # Generate RML with alignment report
    rml_content, alignment_json = internal_to_rml(internal_config, alignment_report)

    # RML should NOT contain x-alignment data
    assert 'x-alignment' not in rml_content
    assert 'confidence' not in rml_content
    assert 'matcher' not in rml_content

    # Alignment should be in separate JSON
    assert alignment_json is not None
    alignment_data = json.loads(alignment_json)
    assert alignment_data['statistics']['total_columns'] == 5
    assert len(alignment_data['match_details']) == 1
    assert alignment_data['match_details'][0]['confidence'] == 0.95

    print("✅ Alignment report is kept separate from RML")
    print(f"\nRML (clean, no x-alignment):\n{rml_content[:300]}...")
    print(f"\nAlignment Report (separate JSON):\n{alignment_json[:200]}...")


def test_rml_generator_multiple_sheets():
    """Test RML generation with multiple sheets."""
    internal_config = {
        'namespaces': {
            'schema': 'http://schema.org/',
        },
        'defaults': {
            'base_iri': 'http://example.org/'
        },
        'sheets': [
            {
                'name': 'people',
                'source': 'people.csv',
                'format': 'csv',
                'class': 'schema:Person',
                'subject_template': 'http://example.org/person/$(id)',
                'columns': [
                    {'column': 'name', 'property': 'schema:name'}
                ]
            },
            {
                'name': 'companies',
                'source': 'companies.csv',
                'format': 'csv',
                'class': 'schema:Organization',
                'subject_template': 'http://example.org/company/$(id)',
                'columns': [
                    {'column': 'company_name', 'property': 'schema:name'}
                ]
            }
        ]
    }

    rml_content = generate_rml(internal_config)

    # Verify both TriplesMap are present
    assert 'peopleMapping' in rml_content or 'people' in rml_content.lower()
    assert 'companiesMapping' in rml_content or 'companies' in rml_content.lower()
    assert 'Person' in rml_content
    assert 'Organization' in rml_content

    print("✅ Multiple sheets (TriplesMap) work")


if __name__ == '__main__':
    print("Testing RML Generator...\n")

    test_rml_generator_basic()
    print()

    test_rml_generator_with_constants()
    print()

    test_rml_roundtrip()
    print()

    test_rml_generator_with_alignment_report()
    print()

    test_rml_generator_multiple_sheets()
    print()

    print("🎉 All RML generator tests passed!")

