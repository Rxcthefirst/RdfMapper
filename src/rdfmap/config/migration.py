"""Configuration migration utilities.

Handles automatic migration from old config structure to new structure
while maintaining backward compatibility.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def detect_config_version(config_data: dict) -> str:
    """Detect which config structure version is being used.

    Args:
        config_data: Parsed configuration dictionary

    Returns:
        'v2' for new structure, 'v1' for old structure
    """
    # V2 has 'mapping' at top level with pipeline sections
    if 'mapping' in config_data:
        # Check if it's truly v2 (mapping has sources or file)
        mapping = config_data['mapping']
        if isinstance(mapping, dict) and ('sources' in mapping or 'file' in mapping):
            return 'v2'

    # V1 has 'sheets' or 'mapping_file' at top level with namespaces/defaults scattered
    if 'sheets' in config_data or 'mapping_file' in config_data:
        return 'v1'

    # Default to v1 for backward compatibility
    return 'v1'


def convert_v2_to_v1_for_engine(v2_config: dict) -> dict:
    """Convert v2 config back to v1 format for the existing conversion engine.

    This is a temporary bridge until the engine is updated to use v2 directly.

    Args:
        v2_config: New structure configuration

    Returns:
        Old structure configuration compatible with current engine
    """
    v1_config = {}

    # Pipeline config (keep as-is)
    if 'validation' in v2_config:
        v1_config['validation'] = v2_config['validation']

    if 'options' in v2_config:
        v1_config['options'] = v2_config['options']

    if 'imports' in v2_config:
        v1_config['imports'] = v2_config['imports']

    # Mapping definition (restructure back)
    mapping = v2_config.get('mapping', {})

    # Extract from mapping section
    if 'namespaces' in mapping:
        v1_config['namespaces'] = mapping['namespaces']

    if 'base_iri' in mapping:
        v1_config['defaults'] = {'base_iri': mapping['base_iri']}

    # Convert sources back to sheets or file back to mapping_file
    if 'sources' in mapping:
        v1_config['sheets'] = _convert_sources_to_sheets(mapping['sources'])
    elif 'file' in mapping:
        v1_config['mapping_file'] = mapping['file']

    return v1_config


def _convert_sources_to_sheets(sources: List[dict]) -> List[dict]:
    """Convert sources (v2) back to sheets (v1) for engine compatibility."""
    sheets = []

    for source in sources:
        sheet = {
            'name': source['name'],
            'source': source['file'],
            'format': source.get('format', 'csv')
        }

        # Convert entity back to row_resource
        if 'entity' in source:
            sheet['row_resource'] = {
                'class': source['entity']['class'],
                'iri_template': source['entity']['iri_template']
            }

        # Convert properties back to columns
        if 'properties' in source:
            sheet['columns'] = {}
            for field_name, prop_config in source['properties'].items():
                column_config = prop_config.copy()

                # Rename 'predicate' back to 'as'
                if 'predicate' in column_config:
                    column_config['as'] = column_config.pop('predicate')

                sheet['columns'][field_name] = column_config

        # Convert relationships back to objects
        if 'relationships' in source:
            sheet['objects'] = {}
            for idx, rel in enumerate(source['relationships']):
                # Generate a key name from predicate if possible
                key = rel.get('predicate', f"relationship_{idx}").split(':')[-1].split('/')[-1]

                obj_config = {
                    'predicate': rel['predicate'],
                    'class': rel['class'],
                    'iri_template': rel['iri_template']
                }

                # Convert properties
                if 'properties' in rel:
                    obj_config['properties'] = []
                    for field_name, prop_config in rel['properties'].items():
                        prop_copy = prop_config.copy()
                        prop_copy['column'] = field_name

                        # Rename 'predicate' back to 'as'
                        if 'predicate' in prop_copy:
                            prop_copy['as'] = prop_copy.pop('predicate')

                        obj_config['properties'].append(prop_copy)

                sheet['objects'][key] = obj_config

        # Optional fields
        if 'iterator' in source:
            sheet['iterator'] = source['iterator']

        if 'filter_condition' in source:
            sheet['filter_condition'] = source['filter_condition']

        sheets.append(sheet)

    return sheets

