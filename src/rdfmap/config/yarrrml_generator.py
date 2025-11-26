"""YARRRML Generator - Converts internal format to YARRRML standard."""

import re
from typing import Dict, Any, Optional


def internal_to_yarrrml(internal_config: Dict[str, Any],
                       alignment_report: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Convert internal mapping format to YARRRML standard format.

    Args:
        internal_config: Internal mapping configuration dict
        alignment_report: Optional alignment report with AI metadata

    Returns:
        YARRRML-compliant dictionary
    """
    yarrrml = {}

    # Convert namespaces to prefixes
    if 'namespaces' in internal_config:
        yarrrml['prefixes'] = internal_config['namespaces'].copy()

    # Convert defaults to base
    if 'defaults' in internal_config:
        yarrrml['base'] = internal_config['defaults'].get('base_iri', 'http://example.org/')

    # Extract sources from sheets
    sources = {}
    for sheet in internal_config.get('sheets', []):
        sheet_name = sheet.get('name', 'data')
        source_file = sheet.get('source', 'data.csv')
        file_ext = source_file.split('.')[-1] if '.' in source_file else 'csv'
        sources[sheet_name] = [f"{source_file}~{file_ext}"]

    if sources:
        yarrrml['sources'] = sources

    # Convert sheets to mappings
    mappings = {}
    for sheet in internal_config.get('sheets', []):
        # Main mapping
        mapping = _convert_sheet_to_mapping(sheet, alignment_report)
        if mapping:
            mappings[sheet['name']] = mapping

        # Create child mappings for objects (relationships)
        if 'objects' in sheet:
            for obj_name, obj_config in sheet['objects'].items():
                child_mapping = _convert_object_to_mapping(
                    sheet['name'],
                    obj_name,
                    obj_config,
                    sheet.get('name', 'data')
                )
                if child_mapping:
                    mappings[f"{sheet['name']}_{obj_name}"] = child_mapping

    if mappings:
        yarrrml['mappings'] = mappings

    # Add x-alignment for AI metadata
    if alignment_report:
        yarrrml['x-alignment'] = {
            'generated_at': alignment_report.get('generated_at'),
            'statistics': alignment_report.get('statistics', {}),
            'unmapped_columns': [
                uc.get('column_name')
                for uc in alignment_report.get('unmapped_columns', [])
            ]
        }

    return yarrrml


def _convert_sheet_to_mapping(sheet: Dict[str, Any],
                              alignment_report: Optional[Dict] = None) -> Dict[str, Any]:
    """Convert internal sheet to YARRRML mapping."""
    mapping = {}

    sheet_name = sheet.get('name', 'data')
    mapping['sources'] = f"${sheet_name}"

    # Convert row_resource to subject
    if 'row_resource' in sheet:
        row_res = sheet['row_resource']
        iri_template = row_res.get('iri_template', '')
        # Convert {column} to $(column)
        iri_template = re.sub(r'\{(\w+)\}', r'$(\1)', iri_template)
        mapping['s'] = iri_template

        # Add rdf:type
        mapping['po'] = [['a', row_res.get('class', '')]]
    else:
        mapping['po'] = []

    # Convert columns to predicate-object pairs
    column_alignments = {}
    for col_name, col_config in sheet.get('columns', {}).items():
        predicate = col_config.get('as', '')
        po_entry = [predicate, f"$({col_name})"]

        if 'datatype' in col_config:
            po_entry.append(col_config['datatype'])

        mapping['po'].append(po_entry)

        # Collect alignment metadata
        if alignment_report and 'match_details' in alignment_report:
            for detail in alignment_report['match_details']:
                if detail.get('column_name') == col_name:
                    column_alignments[col_name] = {
                        'matcher': detail.get('matcher_name'),
                        'confidence': detail.get('confidence_score'),
                        'match_type': detail.get('match_type'),
                        'evidence_count': len(detail.get('evidence', []))
                    }
                    break

    # Convert objects (relationships) to predicate-object pairs with parent triples maps
    # YARRRML uses array format: [predicate, [parentTriplesMap]]
    if 'objects' in sheet:
        for obj_name, obj_config in sheet['objects'].items():
            predicate = obj_config.get('predicate', '')
            # Reference to child mapping (will be created separately)
            child_mapping_ref = f"{sheet_name}_{obj_name}"
            po_entry = [predicate, [child_mapping_ref]]
            mapping['po'].append(po_entry)

    if column_alignments:
        mapping['x-alignment'] = column_alignments

    return mapping


def _convert_object_to_mapping(sheet_name: str,
                               obj_name: str,
                               obj_config: Dict[str, Any],
                               source_name: str) -> Dict[str, Any]:
    """Convert internal object (relationship) to YARRRML child mapping.

    Creates a separate mapping for the linked object with its own subject and properties.
    """
    mapping = {}

    # Use same source as parent
    mapping['sources'] = f"${source_name}"

    # Convert IRI template
    iri_template = obj_config.get('iri_template', '')
    iri_template = re.sub(r'\{(\w+)\}', r'$(\1)', iri_template)
    mapping['s'] = iri_template

    # Add rdf:type for the object class
    object_class = obj_config.get('class', '')
    mapping['po'] = [['a', object_class]]

    # Convert object properties
    properties = obj_config.get('properties', [])

    # Handle both list format (with 'column' field) and dict format
    if isinstance(properties, list):
        for prop in properties:
            if 'column' in prop:
                col_name = prop['column']
                predicate = prop.get('as', '')
                po_entry = [predicate, f"$({col_name})"]

                if 'datatype' in prop:
                    po_entry.append(prop['datatype'])

                mapping['po'].append(po_entry)
    elif isinstance(properties, dict):
        for col_name, prop_config in properties.items():
            predicate = prop_config.get('as', '')
            po_entry = [predicate, f"$({col_name})"]

            if 'datatype' in prop_config:
                po_entry.append(prop_config['datatype'])

            mapping['po'].append(po_entry)

    return mapping



