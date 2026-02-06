"""
Configuration format adapter for backward compatibility.

This module provides conversion between v1 and v2 configuration formats:

V1 Format (0.3.0 and earlier):
    sheets:
      - name: people
        class: schema:Person
        subject_template: http://example.org/person/$(id)
        columns:
          - column: name
            property: schema:name

V2 Format (0.4.0+):
    sheets:
      - name: people
        row_resource:
          class: schema:Person
          iri_template: http://example.org/person/$(id)
        properties:
          name:
            as: schema:name
"""

from typing import Dict, Any, List, Optional
from copy import deepcopy


def detect_format_version(config: Dict[str, Any]) -> int:
    """
    Detect whether config is v1 or v2 format.

    Args:
        config: Configuration dictionary

    Returns:
        1 for v1 format, 2 for v2 format
    """
    if not config.get('sheets'):
        return 2  # Default to v2 for empty configs

    first_sheet = config['sheets'][0]

    # V2 has 'row_resource' nested object
    if 'row_resource' in first_sheet:
        return 2

    # V1 has 'class' directly in sheet
    if 'class' in first_sheet:
        return 1

    # Default to v2
    return 2


def v1_to_v2_format(v1_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert v1 configuration format to v2 format.

    Args:
        v1_config: Configuration in v1 format

    Returns:
        Configuration in v2 format
    """
    v2_config = {
        'namespaces': v1_config.get('namespaces', {}),
        'defaults': v1_config.get('defaults', {}),
        'sheets': []
    }

    for v1_sheet in v1_config.get('sheets', []):
        v2_sheet = {
            'name': v1_sheet['name'],
            'source': v1_sheet['source'],
            'format': v1_sheet.get('format', 'csv'),
            'row_resource': {
                'class': v1_sheet['class'],
                'iri_template': v1_sheet.get('subject_template', v1_sheet.get('iri_template', ''))
            },
            'properties': {},
            'objects': {}
        }

        # Convert columns list to properties dict
        for col in v1_sheet.get('columns', []):
            col_name = col['column']
            prop_def = {'as': col['property']}

            # Copy optional fields
            if 'datatype' in col:
                prop_def['datatype'] = col['datatype']
            if 'language' in col:
                prop_def['language'] = col['language']
            if 'default' in col:
                prop_def['default'] = col['default']
            if 'template' in col:
                prop_def['template'] = col['template']
            if 'required' in col:
                prop_def['required'] = col['required']

            # Check if it's an object property
            if col.get('object_property') or col.get('is_object_property'):
                # This is a reference to another entity
                # In v2, object properties have a different structure
                target_class = col.get('target_class', col.get('class', ''))
                obj_def = {
                    'predicate': col['property'],
                    'target_class': target_class,
                    'join_column': col_name,
                    'properties': {}
                }

                # Use property name as object key
                obj_key = col['property'].split(':')[-1]
                v2_sheet['objects'][obj_key] = obj_def
            else:
                # Regular data property
                v2_sheet['properties'][col_name] = prop_def

        # Handle nested objects from v1 'objects' field
        for obj_name, obj_def in v1_sheet.get('objects', {}).items():
            if obj_name not in v2_sheet['objects']:
                # Convert v1 object to v2 object
                v2_obj = {
                    'predicate': obj_def.get('predicate', obj_def.get('property', '')),
                    'target_class': obj_def.get('class', obj_def.get('target_class', '')),
                    'join_column': obj_def.get('join_column', obj_def.get('foreign_key', '')),
                    'properties': {}
                }

                # Convert nested columns
                for nested_col in obj_def.get('columns', []):
                    nested_col_name = nested_col['column']
                    nested_prop_def = {'as': nested_col['property']}

                    if 'datatype' in nested_col:
                        nested_prop_def['datatype'] = nested_col['datatype']
                    if 'language' in nested_col:
                        nested_prop_def['language'] = nested_col['language']

                    v2_obj['properties'][nested_col_name] = nested_prop_def

                v2_sheet['objects'][obj_name] = v2_obj

        v2_config['sheets'].append(v2_sheet)

    # Copy other top-level fields
    for key in ['validation', 'options', 'imports']:
        if key in v1_config:
            v2_config[key] = v1_config[key]

    return v2_config


def v2_to_v1_format(v2_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert v2 configuration format to v1 format for backward compatibility.

    Args:
        v2_config: Configuration in v2 format

    Returns:
        Configuration in v1 format
    """
    v1_config = {
        'namespaces': v2_config.get('namespaces', {}),
        'defaults': v2_config.get('defaults', {}),
        'sheets': []
    }

    for v2_sheet in v2_config.get('sheets', []):
        row_resource = v2_sheet.get('row_resource', {})

        v1_sheet = {
            'name': v2_sheet['name'],
            'source': v2_sheet['source'],
            'format': v2_sheet.get('format', 'csv'),
            'class': row_resource.get('class', ''),
            'subject_template': row_resource.get('iri_template', ''),
            'columns': [],
            'objects': {}
        }

        # Convert properties dict to columns list
        for col_name, prop_def in v2_sheet.get('properties', {}).items():
            col = {
                'column': col_name,
                'property': prop_def['as']
            }

            # Copy optional fields
            if 'datatype' in prop_def:
                col['datatype'] = prop_def['datatype']
            if 'language' in prop_def:
                col['language'] = prop_def['language']
            if 'default' in prop_def:
                col['default'] = prop_def['default']
            if 'template' in prop_def:
                col['template'] = prop_def['template']
            if 'required' in prop_def:
                col['required'] = prop_def['required']

            v1_sheet['columns'].append(col)

        # Convert objects dict to v1 format
        for obj_name, obj_def in v2_sheet.get('objects', {}).items():
            v1_obj = {
                'predicate': obj_def.get('predicate', ''),
                'class': obj_def.get('target_class', ''),
                'join_column': obj_def.get('join_column', ''),
                'columns': []
            }

            # Convert nested properties
            for nested_col_name, nested_prop_def in obj_def.get('properties', {}).items():
                nested_col = {
                    'column': nested_col_name,
                    'property': nested_prop_def['as']
                }

                if 'datatype' in nested_prop_def:
                    nested_col['datatype'] = nested_prop_def['datatype']
                if 'language' in nested_prop_def:
                    nested_col['language'] = nested_prop_def['language']

                v1_obj['columns'].append(nested_col)

            v1_sheet['objects'][obj_name] = v1_obj

        v1_config['sheets'].append(v1_sheet)

    # Copy other top-level fields
    for key in ['validation', 'options', 'imports']:
        if key in v2_config:
            v1_config[key] = v2_config[key]

    return v1_config


def normalize_config(config: Dict[str, Any], target_version: int = 2) -> Dict[str, Any]:
    """
    Normalize configuration to target version format.

    Args:
        config: Configuration dictionary (v1 or v2)
        target_version: Target format version (1 or 2)

    Returns:
        Configuration in target format
    """
    current_version = detect_format_version(config)

    if current_version == target_version:
        return deepcopy(config)

    if target_version == 2:
        return v1_to_v2_format(config)
    else:
        return v2_to_v1_format(config)


def ensure_v2_format(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure configuration is in v2 format.

    Args:
        config: Configuration dictionary (v1 or v2)

    Returns:
        Configuration in v2 format
    """
    return normalize_config(config, target_version=2)


def ensure_v1_format(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure configuration is in v1 format (for backward compatibility).

    Args:
        config: Configuration dictionary (v1 or v2)

    Returns:
        Configuration in v1 format
    """
    return normalize_config(config, target_version=1)

