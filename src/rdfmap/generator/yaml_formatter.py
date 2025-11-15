"""Custom YAML formatter for mapping configurations.

Produces clean, well-commented YAML that matches the style of manual configurations.
"""

from typing import Dict, Any, TextIO, List
from pathlib import Path


class MappingYAMLFormatter:
    """Format mapping configurations with helpful comments and clean structure."""

    def __init__(self, indent: int = 2):
        self.indent = indent

    def write(self, mapping: Dict[str, Any], file: TextIO, wizard_config: Dict[str, Any] = None):
        """Write mapping to file with formatting and comments.

        Args:
            mapping: Mapping configuration dictionary
            file: File object to write to
            wizard_config: Optional wizard configuration for metadata
        """
        # Header
        self._write_header(file, wizard_config)

        # Namespaces
        file.write("namespaces:\n")
        for prefix, uri in mapping.get('namespaces', {}).items():
            file.write(f"  {prefix}: {uri}\n")
        file.write("\n")

        # Defaults
        file.write("defaults:\n")
        for key, value in mapping.get('defaults', {}).items():
            file.write(f"  {key}: {value}\n")
        file.write("\n")

        # Sheets
        file.write("sheets:\n")
        for sheet in mapping.get('sheets', []):
            self._write_sheet(file, sheet)

        # Validation
        if 'validation' in mapping:
            file.write("\n# Validation configuration\n")
            file.write("validation:\n")
            self._write_dict(file, mapping['validation'], indent=1)
            file.write("\n")

        # Options
        file.write("\n# Processing options\n")
        file.write("options:\n")
        for key, value in mapping.get('options', {}).items():
            if isinstance(value, str):
                file.write(f"  {key}: \"{value}\"\n")
            else:
                file.write(f"  {key}: {str(value).lower() if isinstance(value, bool) else value}\n")
        file.write("\n")

        # Add commented template sections for unused features
        self._write_template_sections(file, mapping)

    def _write_template_sections(self, file: TextIO, mapping: Dict[str, Any]):
        """Write commented template sections for unused features."""

        # Check what's already configured
        has_validation = 'validation' in mapping
        has_imports = 'imports' in mapping

        # Validation template (if not already configured)
        if not has_validation:
            file.write("# ────────────────────────────────────────────────────────────────────────────────\n")
            file.write("# Validation Configuration (Optional)\n")
            file.write("# ────────────────────────────────────────────────────────────────────────────────\n")
            file.write("# Uncomment to enable SHACL validation during conversion:\n")
            file.write("#\n")
            file.write("# validation:\n")
            file.write("#   shacl:\n")
            file.write("#     enabled: true\n")
            file.write("#     shapes_file: path/to/shapes.ttl\n")
            file.write("#     inference: none  # Options: none, rdfs, owlrl\n")
            file.write("#\n")
            file.write("# This validates generated RDF against SHACL shapes to catch:\n")
            file.write("#   - Missing required properties\n")
            file.write("#   - Invalid data types\n")
            file.write("#   - Cardinality violations\n")
            file.write("#   - Domain/range mismatches\n")
            file.write("#\n\n")

        # Ontology imports template (if not already configured)
        if not has_imports:
            file.write("# ────────────────────────────────────────────────────────────────────────────────\n")
            file.write("# Ontology Imports (Optional)\n")
            file.write("# ────────────────────────────────────────────────────────────────────────────────\n")
            file.write("# Uncomment to import additional ontologies:\n")
            file.write("#\n")
            file.write("# imports:\n")
            file.write("#   - path/to/external_ontology.ttl\n")
            file.write("#   - path/to/another_ontology.owl\n")
            file.write("#\n")
            file.write("# Use this when your ontology references external vocabularies like:\n")
            file.write("#   - FOAF (Friend of a Friend)\n")
            file.write("#   - Dublin Core\n")
            file.write("#   - Schema.org\n")
            file.write("#   - Domain-specific ontologies\n")
            file.write("#\n\n")

        # Advanced features template
        file.write("# ────────────────────────────────────────────────────────────────────────────────\n")
        file.write("# Advanced Features (Optional)\n")
        file.write("# ────────────────────────────────────────────────────────────────────────────────\n")
        file.write("#\n")
        file.write("# Multi-valued Cells:\n")
        file.write("#   columns:\n")
        file.write("#     Tags:\n")
        file.write("#       as: ex:hasTag\n")
        file.write("#       multi_valued: true\n")
        file.write("#       separator: \",\"  # Split \"tag1,tag2,tag3\" into multiple values\n")
        file.write("#\n")
        file.write("# Conditional Mapping:\n")
        file.write("#   columns:\n")
        file.write("#     Status:\n")
        file.write("#       as: ex:status\n")
        file.write("#       condition:\n")
        file.write("#         when: \"value == 'Active'\"\n")
        file.write("#         then: \"ex:ActiveStatus\"\n")
        file.write("#\n")
        file.write("# Custom Transforms:\n")
        file.write("#   columns:\n")
        file.write("#     Amount:\n")
        file.write("#       as: ex:amount\n")
        file.write("#       transform: \"lambda x: float(x.replace('$', '').replace(',', ''))\"\n")
        file.write("#\n")
        file.write("# Composite Keys:\n")
        file.write("#   row_resource:\n")
        file.write("#     class: ex:Transaction\n")
        file.write("#     iri_template: \"{base_iri}transaction/{Date}/{AccountID}/{TransactionID}\"\n")
        file.write("#\n")
        file.write("# Language Tags:\n")
        file.write("#   columns:\n")
        file.write("#     Name:\n")
        file.write("#       as: ex:name\n")
        file.write("#       language: \"en\"  # Add @en language tag\n")
        file.write("#\n")
        file.write("# Null Handling:\n")
        file.write("#   columns:\n")
        file.write("#     OptionalField:\n")
        file.write("#       as: ex:optional\n")
        file.write("#       skip_if_empty: true  # Don't create triple if value is null/empty\n")
        file.write("#\n\n")

        # Processing options template
        file.write("# ────────────────────────────────────────────────────────────────────────────────\n")
        file.write("# Additional Processing Options\n")
        file.write("# ────────────────────────────────────────────────────────────────────────────────\n")
        file.write("#\n")
        file.write("# options:\n")
        file.write("#   # CSV/TSV specific:\n")
        file.write("#   delimiter: \",\"           # Field separator (default: ',')\n")
        file.write("#   quote_char: '\"'          # Quote character (default: '\"')\n")
        file.write("#   header: true            # First row contains headers (default: true)\n")
        file.write("#   encoding: \"utf-8\"        # File encoding (default: 'utf-8')\n")
        file.write("#\n")
        file.write("#   # Memory management:\n")
        file.write("#   chunk_size: 1000        # Process data in chunks (for large files)\n")
        file.write("#   streaming: false        # Enable streaming mode (constant memory)\n")
        file.write("#\n")
        file.write("#   # Error handling:\n")
        file.write("#   on_error: \"report\"       # Options: report, skip, stop\n")
        file.write("#   skip_empty_values: true # Don't create triples for empty/null values\n")
        file.write("#   strict_mode: false      # Fail on any validation error\n")
        file.write("#\n")
        file.write("#   # Performance:\n")
        file.write("#   parallel: false         # Enable parallel processing\n")
        file.write("#   workers: 4              # Number of worker threads\n")
        file.write("#   batch_size: 10000       # RDF write batch size\n")
        file.write("#\n")
        file.write("#   # Output:\n")
        file.write("#   pretty_print: true      # Format output for readability\n")
        file.write("#   compression: \"gzip\"      # Compress output (gzip, bz2, xz)\n")
        file.write("#\n\n")

        # Usage examples
        file.write("# ════════════════════════════════════════════════════════════════════════════════\n")
        file.write("# Usage Examples\n")
        file.write("# ════════════════════════════════════════════════════════════════════════════════\n")
        file.write("#\n")
        file.write("# Test with sample data (dry run):\n")
        file.write("#   rdfmap convert --mapping <this-file> --limit 10 --dry-run\n")
        file.write("#\n")
        file.write("# Convert with validation:\n")
        file.write("#   rdfmap convert --mapping <this-file> --validate\n")
        file.write("#\n")
        file.write("# Convert to specific format:\n")
        file.write("#   rdfmap convert --mapping <this-file> --format nt --output output.nt\n")
        file.write("#\n")
        file.write("# Process large file with streaming:\n")
        file.write("#   rdfmap convert --mapping <this-file> --streaming --chunk-size 50000\n")
        file.write("#\n")
        file.write("# Generate validation report:\n")
        file.write("#   rdfmap convert --mapping <this-file> --validate --report validation.json\n")
        file.write("#\n")
        file.write("# For more information:\n")
        file.write("#   rdfmap convert --help\n")
        file.write("#   https://github.com/YourOrg/RDFMap/docs\n")
        file.write("#\n")
        file.write("# ════════════════════════════════════════════════════════════════════════════════\n")

    def _write_header(self, file: TextIO, wizard_config: Dict[str, Any] = None):
        """Write file header with helpful information."""
        file.write("# ════════════════════════════════════════════════════════════════════════════════\n")
        file.write("# RDFMap Mapping Configuration\n")
        file.write("# ════════════════════════════════════════════════════════════════════════════════\n")
        file.write("#\n")

        if wizard_config:
            file.write("# Generated by: Configuration Wizard\n")
            file.write(f"# Data source: {wizard_config.get('data_source', 'N/A')}\n")
            file.write(f"# Ontology: {wizard_config.get('ontology', 'N/A')}\n")
            file.write(f"# Target class: {wizard_config.get('target_class', 'N/A')}\n")
            file.write("#\n")

        file.write("# This configuration maps your data columns to ontology properties.\n")
        file.write("# Review and adjust as needed:\n")
        file.write("#   - Verify column mappings are correct\n")
        file.write("#   - Check foreign key relationships\n")
        file.write("#   - Confirm data type conversions\n")
        file.write("#\n")
        file.write("# Quick start:\n")
        file.write("#   rdfmap convert --mapping <this-file> --validate\n")
        file.write("#\n")
        file.write("# ════════════════════════════════════════════════════════════════════════════════\n")
        file.write("\n")

    def _write_sheet(self, file: TextIO, sheet: Dict[str, Any]):
        """Write sheet section with clean formatting."""
        file.write(f"  - name: {sheet.get('name')}\n")
        file.write(f"    source: {sheet.get('source')}\n")
        file.write("    \n")

        # Row resource
        file.write("    # Main resource configuration\n")
        file.write("    row_resource:\n")
        row_res = sheet.get('row_resource', {})
        file.write(f"      class: {row_res.get('class')}\n")
        file.write(f"      iri_template: \"{row_res.get('iri_template')}\"\n")
        file.write("    \n")

        # Columns
        file.write("    # Column mappings (data properties)\n")
        file.write("    columns:\n")
        columns = sheet.get('columns', {})
        for col_name, col_config in columns.items():
            file.write(f"      {col_name}:\n")
            file.write(f"        as: {col_config.get('as')}\n")

            if 'datatype' in col_config:
                file.write(f"        datatype: {col_config.get('datatype')}\n")

            # Add transform if datatype suggests it
            datatype = col_config.get('datatype', '')
            if 'decimal' in datatype:
                file.write(f"        transform: to_decimal\n")
            elif 'date' in datatype:
                file.write(f"        transform: to_date\n")
            elif 'integer' in datatype:
                file.write(f"        transform: to_integer\n")

            if col_config.get('required'):
                file.write(f"        required: true\n")

            file.write("      \n")

        # Objects
        if 'objects' in sheet and sheet['objects']:
            file.write("    # Linked objects (object properties)\n")
            file.write("    objects:\n")
            for obj_name, obj_config in sheet['objects'].items():
                file.write(f"      {obj_name}:\n")
                file.write(f"        predicate: {obj_config.get('predicate')}\n")
                file.write(f"        class: {obj_config.get('class')}\n")
                file.write(f"        iri_template: \"{obj_config.get('iri_template')}\"\n")
                file.write(f"        properties:\n")
                for prop in obj_config.get('properties', []):
                    file.write(f"          - column: {prop.get('column')}\n")
                    file.write(f"            as: {prop.get('as')}\n")
                    if 'datatype' in prop:
                        file.write(f"            datatype: {prop.get('datatype')}\n")
                    if prop.get('required'):
                        file.write(f"            required: true\n")
                file.write("      \n")

    def _write_dict(self, file: TextIO, d: Dict[str, Any], indent: int = 0):
        """Recursively write dictionary with indentation."""
        for key, value in d.items():
            if isinstance(value, dict):
                file.write(f"{'  ' * indent}{key}:\n")
                self._write_dict(file, value, indent + 1)
            elif isinstance(value, bool):
                file.write(f"{'  ' * indent}{key}: {str(value).lower()}\n")
            elif isinstance(value, str):
                file.write(f"{'  ' * indent}{key}: {value}\n")
            else:
                file.write(f"{'  ' * indent}{key}: {value}\n")


def save_formatted_mapping(mapping: Dict[str, Any], output_path: str, wizard_config: Dict[str, Any] = None):
    """Save mapping configuration with clean formatting.

    Args:
        mapping: Mapping configuration
        output_path: Path to save file
        wizard_config: Optional wizard configuration for header
    """
    formatter = MappingYAMLFormatter()
    with open(output_path, 'w') as f:
        formatter.write(mapping, f, wizard_config)

