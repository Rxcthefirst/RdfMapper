"""Tests for configuration format adapter."""

import pytest
from rdfmap.config.format_adapter import (
    detect_format_version,
    v1_to_v2_format,
    v2_to_v1_format,
    normalize_config,
    ensure_v2_format,
    ensure_v1_format
)


@pytest.fixture
def sample_v1_config():
    """Sample v1 format configuration."""
    return {
        'namespaces': {
            'schema': 'http://schema.org/',
            'ex': 'http://example.org/'
        },
        'defaults': {
            'base_iri': 'http://example.org/'
        },
        'sheets': [{
            'name': 'people',
            'source': 'data/people.csv',
            'format': 'csv',
            'class': 'schema:Person',
            'subject_template': 'http://example.org/person/$(id)',
            'columns': [
                {
                    'column': 'name',
                    'property': 'schema:name',
                    'datatype': 'xsd:string'
                },
                {
                    'column': 'age',
                    'property': 'schema:age',
                    'datatype': 'xsd:integer'
                }
            ]
        }]
    }


@pytest.fixture
def sample_v2_config():
    """Sample v2 format configuration."""
    return {
        'namespaces': {
            'schema': 'http://schema.org/',
            'ex': 'http://example.org/'
        },
        'defaults': {
            'base_iri': 'http://example.org/'
        },
        'sheets': [{
            'name': 'people',
            'source': 'data/people.csv',
            'format': 'csv',
            'row_resource': {
                'class': 'schema:Person',
                'iri_template': 'http://example.org/person/$(id)'
            },
            'properties': {
                'name': {
                    'as': 'schema:name',
                    'datatype': 'xsd:string'
                },
                'age': {
                    'as': 'schema:age',
                    'datatype': 'xsd:integer'
                }
            },
            'objects': {}
        }]
    }


def test_detect_v1_format(sample_v1_config):
    """Test detecting v1 format."""
    version = detect_format_version(sample_v1_config)
    assert version == 1


def test_detect_v2_format(sample_v2_config):
    """Test detecting v2 format."""
    version = detect_format_version(sample_v2_config)
    assert version == 2


def test_v1_to_v2_conversion(sample_v1_config):
    """Test converting v1 to v2 format."""
    v2_config = v1_to_v2_format(sample_v1_config)

    # Check structure
    assert 'sheets' in v2_config
    assert len(v2_config['sheets']) == 1

    sheet = v2_config['sheets'][0]

    # Check row_resource
    assert 'row_resource' in sheet
    assert sheet['row_resource']['class'] == 'schema:Person'
    assert sheet['row_resource']['iri_template'] == 'http://example.org/person/$(id)'

    # Check properties
    assert 'properties' in sheet
    assert 'name' in sheet['properties']
    assert sheet['properties']['name']['as'] == 'schema:name'
    assert sheet['properties']['name']['datatype'] == 'xsd:string'

    assert 'age' in sheet['properties']
    assert sheet['properties']['age']['as'] == 'schema:age'
    assert sheet['properties']['age']['datatype'] == 'xsd:integer'

    # Check objects dict exists (even if empty)
    assert 'objects' in sheet


def test_v2_to_v1_conversion(sample_v2_config):
    """Test converting v2 to v1 format."""
    v1_config = v2_to_v1_format(sample_v2_config)

    # Check structure
    assert 'sheets' in v1_config
    assert len(v1_config['sheets']) == 1

    sheet = v1_config['sheets'][0]

    # Check class and subject_template
    assert 'class' in sheet
    assert sheet['class'] == 'schema:Person'
    assert sheet['subject_template'] == 'http://example.org/person/$(id)'

    # Check columns
    assert 'columns' in sheet
    assert len(sheet['columns']) == 2

    # Find name column
    name_col = next(c for c in sheet['columns'] if c['column'] == 'name')
    assert name_col['property'] == 'schema:name'
    assert name_col['datatype'] == 'xsd:string'

    # Find age column
    age_col = next(c for c in sheet['columns'] if c['column'] == 'age')
    assert age_col['property'] == 'schema:age'
    assert age_col['datatype'] == 'xsd:integer'


def test_roundtrip_v1_to_v2_to_v1(sample_v1_config):
    """Test that v1 → v2 → v1 preserves structure."""
    v2_config = v1_to_v2_format(sample_v1_config)
    v1_again = v2_to_v1_format(v2_config)

    # Should have same structure (may differ in order)
    assert v1_again['sheets'][0]['name'] == sample_v1_config['sheets'][0]['name']
    assert v1_again['sheets'][0]['class'] == sample_v1_config['sheets'][0]['class']
    assert len(v1_again['sheets'][0]['columns']) == len(sample_v1_config['sheets'][0]['columns'])


def test_roundtrip_v2_to_v1_to_v2(sample_v2_config):
    """Test that v2 → v1 → v2 preserves structure."""
    v1_config = v2_to_v1_format(sample_v2_config)
    v2_again = v1_to_v2_format(v1_config)

    # Should have same structure
    assert v2_again['sheets'][0]['name'] == sample_v2_config['sheets'][0]['name']
    assert v2_again['sheets'][0]['row_resource']['class'] == sample_v2_config['sheets'][0]['row_resource']['class']
    assert len(v2_again['sheets'][0]['properties']) == len(sample_v2_config['sheets'][0]['properties'])


def test_normalize_config_v1_to_v2(sample_v1_config):
    """Test normalizing v1 config to v2."""
    normalized = normalize_config(sample_v1_config, target_version=2)

    # Should be v2 format
    assert detect_format_version(normalized) == 2
    assert 'row_resource' in normalized['sheets'][0]


def test_normalize_config_v2_to_v1(sample_v2_config):
    """Test normalizing v2 config to v1."""
    normalized = normalize_config(sample_v2_config, target_version=1)

    # Should be v1 format
    assert detect_format_version(normalized) == 1
    assert 'class' in normalized['sheets'][0]
    assert 'columns' in normalized['sheets'][0]


def test_normalize_config_same_version(sample_v2_config):
    """Test normalizing config to same version returns copy."""
    normalized = normalize_config(sample_v2_config, target_version=2)

    # Should be different object but same structure
    assert normalized is not sample_v2_config
    assert normalized == sample_v2_config


def test_ensure_v2_format_from_v1(sample_v1_config):
    """Test ensure_v2_format converts v1 to v2."""
    v2_config = ensure_v2_format(sample_v1_config)

    assert detect_format_version(v2_config) == 2
    assert 'row_resource' in v2_config['sheets'][0]


def test_ensure_v2_format_from_v2(sample_v2_config):
    """Test ensure_v2_format returns v2 unchanged."""
    v2_config = ensure_v2_format(sample_v2_config)

    assert detect_format_version(v2_config) == 2
    assert v2_config['sheets'][0]['name'] == sample_v2_config['sheets'][0]['name']


def test_ensure_v1_format_from_v2(sample_v2_config):
    """Test ensure_v1_format converts v2 to v1."""
    v1_config = ensure_v1_format(sample_v2_config)

    assert detect_format_version(v1_config) == 1
    assert 'class' in v1_config['sheets'][0]
    assert 'columns' in v1_config['sheets'][0]


def test_ensure_v1_format_from_v1(sample_v1_config):
    """Test ensure_v1_format returns v1 unchanged."""
    v1_config = ensure_v1_format(sample_v1_config)

    assert detect_format_version(v1_config) == 1
    assert v1_config['sheets'][0]['name'] == sample_v1_config['sheets'][0]['name']


def test_v1_to_v2_with_objects():
    """Test converting v1 with nested objects to v2."""
    v1_config = {
        'sheets': [{
            'name': 'loans',
            'source': 'loans.csv',
            'format': 'csv',
            'class': 'ex:Loan',
            'subject_template': 'http://example.org/loan/$(id)',
            'columns': [
                {'column': 'amount', 'property': 'ex:amount', 'datatype': 'xsd:decimal'}
            ],
            'objects': {
                'borrower': {
                    'predicate': 'ex:hasBorrower',
                    'class': 'ex:Borrower',
                    'join_column': 'borrower_id',
                    'columns': [
                        {'column': 'borrower_name', 'property': 'ex:name'}
                    ]
                }
            }
        }]
    }

    v2_config = v1_to_v2_format(v1_config)

    # Check objects conversion
    assert 'objects' in v2_config['sheets'][0]
    assert 'borrower' in v2_config['sheets'][0]['objects']

    borrower = v2_config['sheets'][0]['objects']['borrower']
    assert borrower['predicate'] == 'ex:hasBorrower'
    assert borrower['target_class'] == 'ex:Borrower'
    assert borrower['join_column'] == 'borrower_id'
    assert 'borrower_name' in borrower['properties']


def test_v2_to_v1_with_objects():
    """Test converting v2 with objects to v1."""
    v2_config = {
        'sheets': [{
            'name': 'loans',
            'source': 'loans.csv',
            'format': 'csv',
            'row_resource': {
                'class': 'ex:Loan',
                'iri_template': 'http://example.org/loan/$(id)'
            },
            'properties': {
                'amount': {'as': 'ex:amount', 'datatype': 'xsd:decimal'}
            },
            'objects': {
                'borrower': {
                    'predicate': 'ex:hasBorrower',
                    'target_class': 'ex:Borrower',
                    'join_column': 'borrower_id',
                    'properties': {
                        'borrower_name': {'as': 'ex:name'}
                    }
                }
            }
        }]
    }

    v1_config = v2_to_v1_format(v2_config)

    # Check objects conversion
    assert 'objects' in v1_config['sheets'][0]
    assert 'borrower' in v1_config['sheets'][0]['objects']

    borrower = v1_config['sheets'][0]['objects']['borrower']
    assert borrower['predicate'] == 'ex:hasBorrower'
    assert borrower['class'] == 'ex:Borrower'
    assert borrower['join_column'] == 'borrower_id'
    assert len(borrower['columns']) == 1
    assert borrower['columns'][0]['column'] == 'borrower_name'


def test_empty_config():
    """Test handling empty config."""
    empty_config = {'sheets': []}

    # Should detect as v2 (default)
    assert detect_format_version(empty_config) == 2

    # Should convert without error
    v2_config = ensure_v2_format(empty_config)
    assert v2_config['sheets'] == []

    v1_config = ensure_v1_format(empty_config)
    assert v1_config['sheets'] == []


def test_preserves_additional_fields():
    """Test that additional fields are preserved during conversion."""
    v1_config = {
        'namespaces': {'ex': 'http://example.org/'},
        'defaults': {'base_iri': 'http://example.org/'},
        'validation': {'enabled': True},
        'options': {'on_error': 'report'},
        'imports': ['ontology.ttl'],
        'sheets': [{
            'name': 'test',
            'source': 'test.csv',
            'class': 'ex:Test',
            'subject_template': 'http://example.org/test/$(id)',
            'columns': []
        }]
    }

    v2_config = v1_to_v2_format(v1_config)

    # Check that additional fields are preserved
    assert v2_config['namespaces'] == v1_config['namespaces']
    assert v2_config['defaults'] == v1_config['defaults']
    assert v2_config['validation'] == v1_config['validation']
    assert v2_config['options'] == v1_config['options']
    assert v2_config['imports'] == v1_config['imports']

