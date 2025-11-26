"""Generate v2 configuration structure from internal mapping.

Converts the internal mapping format to the new v2 structure with clean
separation between pipeline config and mapping definition.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path


def internal_to_v2_config(
    internal_mapping: Dict[str, Any],
    base_iri: str,
    alignment_report: Optional[Dict] = None,
    imports: Optional[List[str]] = None,
    validation_enabled: bool = True,
    shapes_file: Optional[str] = None
) -> Dict[str, Any]:
    """Convert internal mapping format to v2 config structure.

    Args:
        internal_mapping: Internal mapping dict from generator
        base_iri: Base IRI for resources
        alignment_report: Optional alignment report dict
        imports: Optional list of ontology files to import
        validation_enabled: Whether SHACL validation is enabled
        shapes_file: Path to SHACL shapes file

    Returns:
        V2 config structure dict
    """
    v2_config = {}

    # Section 1: Pipeline Configuration
    if validation_enabled and shapes_file:
        v2_config['validation'] = {
            'shacl': {
                'enabled': True,
                'shapes_file': shapes_file,
                'inference': 'none'
            }
        }

    v2_config['options'] = {
        'on_error': 'report',
        'skip_empty_values': True,
        'chunk_size': 1000,
        'aggregate_duplicates': True,
        'output_format': 'ttl'
    }

    if imports:
        v2_config['imports'] = imports

    # Section 2: Mapping Definition
    mapping_def = {
        'namespaces': internal_mapping.get('namespaces', {}),
        'base_iri': base_iri,
        'sources': _convert_sheets_to_sources(internal_mapping.get('sheets', []))
    }

    v2_config['mapping'] = mapping_def

    return v2_config


def internal_to_v2_with_external(
    internal_mapping: Dict[str, Any],
    base_iri: str,
    mapping_file_path: str,
    alignment_report: Optional[Dict] = None,
    imports: Optional[List[str]] = None,
    validation_enabled: bool = True,
    shapes_file: Optional[str] = None
) -> Dict[str, Any]:
    """Convert internal mapping to v2 config with external mapping file reference.

    Args:
        internal_mapping: Internal mapping dict from generator
        base_iri: Base IRI for resources
        mapping_file_path: Relative path to external mapping file
        alignment_report: Optional alignment report dict
        imports: Optional list of ontology files to import
        validation_enabled: Whether SHACL validation is enabled
        shapes_file: Path to SHACL shapes file

    Returns:
        V2 config structure dict with external reference
    """
    v2_config = {}

    # Section 1: Pipeline Configuration
    if validation_enabled and shapes_file:
        v2_config['validation'] = {
            'shacl': {
                'enabled': True,
                'shapes_file': shapes_file,
                'inference': 'none'
            }
        }

    v2_config['options'] = {
        'on_error': 'report',
        'skip_empty_values': True,
        'chunk_size': 1000,
        'aggregate_duplicates': True,
        'output_format': 'ttl'
    }

    if imports:
        v2_config['imports'] = imports

    # Section 2: Mapping Definition (external reference)
    mapping_def = {
        'file': mapping_file_path
    }

    v2_config['mapping'] = mapping_def

    return v2_config


def _convert_sheets_to_sources(sheets: List[Dict]) -> List[Dict]:
    """Convert internal sheets format to v2 sources format.

    Changes:
    - source → file
    - row_resource → entity
    - columns → properties (with as → predicate)
    - objects → relationships
    """
    sources = []

    for sheet in sheets:
        source = {
            'name': sheet['name'],
            'file': sheet.get('source', ''),
            'format': sheet.get('format', 'csv')
        }

        # Convert row_resource to entity
        if 'row_resource' in sheet:
            source['entity'] = {
                'class': sheet['row_resource']['class'],
                'iri_template': sheet['row_resource']['iri_template']
            }

        # Convert columns to properties
        if 'columns' in sheet:
            properties = {}
            for col_name, col_config in sheet['columns'].items():
                prop_config = col_config.copy()

                # Rename 'as' to 'predicate'
                if 'as' in prop_config:
                    prop_config['predicate'] = prop_config.pop('as')

                # Remove 'as_property' if it exists (old alias)
                if 'as_property' in prop_config:
                    if 'predicate' not in prop_config:
                        prop_config['predicate'] = prop_config.pop('as_property')
                    else:
                        prop_config.pop('as_property')

                properties[col_name] = prop_config

            source['properties'] = properties

        # Convert objects to relationships
        if 'objects' in sheet:
            relationships = []
            for obj_name, obj_config in sheet['objects'].items():
                relationship = {
                    'predicate': obj_config['predicate'],
                    'class': obj_config['class'],
                    'iri_template': obj_config['iri_template']
                }

                # Convert properties
                if 'properties' in obj_config:
                    # Handle list format (with column field)
                    if isinstance(obj_config['properties'], list):
                        props_dict = {}
                        for prop in obj_config['properties']:
                            if 'column' in prop:
                                col_name = prop['column']
                                prop_copy = prop.copy()
                                prop_copy.pop('column')

                                # Rename 'as' to 'predicate'
                                if 'as' in prop_copy:
                                    prop_copy['predicate'] = prop_copy.pop('as')

                                props_dict[col_name] = prop_copy
                        relationship['properties'] = props_dict
                    # Handle dict format
                    else:
                        props_dict = {}
                        for col_name, prop_config in obj_config['properties'].items():
                            prop_copy = prop_config.copy()

                            # Rename 'as' to 'predicate'
                            if 'as' in prop_copy:
                                prop_copy['predicate'] = prop_copy.pop('as')

                            props_dict[col_name] = prop_copy
                        relationship['properties'] = props_dict

                relationships.append(relationship)

            source['relationships'] = relationships

        # Optional fields
        if 'iterator' in sheet:
            source['iterator'] = sheet['iterator']

        if 'filter_condition' in sheet:
            source['filter_condition'] = sheet['filter_condition']

        sources.append(source)

    return sources

