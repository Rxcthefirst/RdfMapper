"""YARRRML Parser - Converts YARRRML format to internal MappingConfig model.

YARRRML (YAML-based RML) is a human-friendly format for declaring RDF mappings.
Specification: https://rml.io/yarrrml/spec/

This parser converts YARRRML to our internal Pydantic models so the existing
conversion engine can process it without modification.
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml


def parse_yarrrml(yarrrml_path: Path) -> Dict[str, Any]:
    """
    Parse YARRRML file and convert to internal mapping config format.

    Args:
        yarrrml_path: Path to YARRRML file

    Returns:
        Dictionary in internal mapping format (compatible with MappingConfig)
    """
    with open(yarrrml_path, 'r', encoding='utf-8') as f:
        yarrrml = yaml.safe_load(f)

    return yarrrml_to_internal(yarrrml, yarrrml_path.parent)


def yarrrml_to_internal(yarrrml: Dict[str, Any], config_dir: Path) -> Dict[str, Any]:
    """
    Convert YARRRML dictionary to internal mapping format.

    Args:
        yarrrml: YARRRML configuration dict
        config_dir: Directory containing the YARRRML file (for resolving relative paths)

    Returns:
        Dictionary compatible with MappingConfig Pydantic model
    """
    internal = {}

    # Convert prefixes to namespaces
    if 'prefixes' in yarrrml:
        internal['namespaces'] = yarrrml['prefixes'].copy()
    else:
        # Default namespaces if not provided
        internal['namespaces'] = {
            'xsd': 'http://www.w3.org/2001/XMLSchema#',
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'rdfs': 'http://www.w3.org/2000/01/rdf-schema#'
        }

    # Convert base to defaults
    internal['defaults'] = {
        'base_iri': yarrrml.get('base', 'http://example.org/')
    }

    # Convert sources and mappings to sheets
    sources = yarrrml.get('sources', {})
    mappings = yarrrml.get('mappings', {})

    sheets = []
    for mapping_name, mapping_config in mappings.items():
        sheet = _convert_mapping_to_sheet(
            mapping_name,
            mapping_config,
            sources,
            config_dir,
            internal['namespaces']
        )
        if sheet:
            sheets.append(sheet)

    internal['sheets'] = sheets

    # Convert options if present
    internal['options'] = _extract_options(yarrrml)

    # Store x-alignment extensions if present (AI metadata)
    if 'x-alignment' in yarrrml:
        internal['_x_alignment'] = yarrrml['x-alignment']

    return internal


def _convert_mapping_to_sheet(
    mapping_name: str,
    mapping_config: Dict[str, Any],
    sources: Dict[str, List[str]],
    config_dir: Path,
    namespaces: Dict[str, str]
) -> Optional[Dict[str, Any]]:
    """Convert a YARRRML mapping to internal sheet format."""

    sheet = {
        'name': mapping_name
    }

    # Get source file
    source_ref = mapping_config.get('sources', '')
    if isinstance(source_ref, str):
        if source_ref.startswith('$'):
            # Reference to sources dict: $source_name
            source_name = source_ref[1:]
            if source_name in sources:
                source_list = sources[source_name]
                if source_list:
                    # Format: ['file.csv~csv'] or [['file.csv~csv']]
                    # Handle nested list from YAML parsing
                    first_item = source_list[0]
                    if isinstance(first_item, list):
                        first_item = first_item[0]
                    source_file = str(first_item).split('~')[0]
                    sheet['source'] = str(config_dir / source_file)
            else:
                return None
        else:
            # Direct file reference
            sheet['source'] = str(config_dir / source_ref)
    elif isinstance(source_ref, list) and source_ref:
        # Direct list format: ['file.csv~csv'] or [['file.csv~csv']]
        first_item = source_ref[0]
        if isinstance(first_item, list):
            first_item = first_item[0]
        source_file = str(first_item).split('~')[0]
        sheet['source'] = str(config_dir / source_file)

    # Convert subject template to row_resource
    subject_template = mapping_config.get('s', '')
    if subject_template:
        # YARRRML uses $(column), we use {column}
        # Support column names with spaces: $(First Name) -> {First Name}
        iri_template = re.sub(r'\$\(([^)]+)\)', r'{\1}', subject_template)

        # Extract RDF type from po array
        rdf_class = None
        po_array = mapping_config.get('po', [])
        for po_entry in po_array:
            if len(po_entry) >= 2 and po_entry[0] == 'a':
                rdf_class = _expand_uri(po_entry[1], namespaces)
                break

        if rdf_class:
            sheet['row_resource'] = {
                'class': rdf_class,
                'iri_template': iri_template
            }

    # Convert predicate-object pairs to columns
    columns = {}
    po_array = mapping_config.get('po', [])

    for po_entry in po_array:
        if len(po_entry) < 2:
            continue

        predicate = po_entry[0]
        object_value = po_entry[1]

        # Skip rdf:type (already handled)
        if predicate == 'a':
            continue

        # Extract column name from $(column) or $(Column Name)
        # Match any characters except closing parenthesis to support spaces in column names
        column_match = re.search(r'\$\(([^)]+)\)', str(object_value))
        if column_match:
            column_name = column_match.group(1)

            # Expand predicate URI
            predicate_uri = _expand_uri(predicate, namespaces)

            # Build column mapping
            column_mapping = {
                'as': predicate_uri
            }

            # Add datatype if present
            if len(po_entry) >= 3:
                datatype = _expand_uri(po_entry[2], namespaces)
                column_mapping['datatype'] = datatype

            # Check for x-alignment metadata
            if 'x-alignment' in mapping_config:
                alignment = mapping_config['x-alignment']
                if column_name in alignment:
                    column_mapping['_alignment'] = alignment[column_name]

            columns[column_name] = column_mapping

    if columns:
        sheet['columns'] = columns

    # Handle object properties (relationships) if this is a sub-mapping
    # YARRRML often splits these into separate mappings with naming convention
    # For now, we handle simple cases

    return sheet


def _expand_uri(uri_or_curie: str, namespaces: Dict[str, str]) -> str:
    """
    Expand a CURIE to full URI using namespace prefixes.

    Args:
        uri_or_curie: URI or CURIE (e.g., "ex:Person" or full URI)
        namespaces: Prefix to namespace mappings

    Returns:
        Full URI
    """
    # If already a full URI, return as-is
    if uri_or_curie.startswith('http://') or uri_or_curie.startswith('https://'):
        return uri_or_curie

    # If it's a CURIE (prefix:localname)
    if ':' in uri_or_curie:
        prefix, local_name = uri_or_curie.split(':', 1)
        if prefix in namespaces:
            return namespaces[prefix] + local_name

    # Return as-is if can't expand
    return uri_or_curie


def _extract_options(yarrrml: Dict[str, Any]) -> Dict[str, Any]:
    """Extract processing options from YARRRML (if any custom extensions exist)."""
    options = {}

    # YARRRML doesn't have standard options, but we can check for x-options extension
    if 'x-options' in yarrrml:
        options = yarrrml['x-options'].copy()

    return options


def detect_format(config_path: Path) -> str:
    """
    Detect if a YAML file is in YARRRML format or internal format.

    Args:
        config_path: Path to configuration file

    Returns:
        'yarrrml' or 'internal'
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # YARRRML has 'prefixes' and 'mappings'
    if 'prefixes' in data and 'mappings' in data:
        return 'yarrrml'

    # Internal format has 'namespaces' and 'sheets'
    if 'namespaces' in data and 'sheets' in data:
        return 'internal'

    # Default to internal for backward compatibility
    return 'internal'

