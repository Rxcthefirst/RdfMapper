"""Configuration loading and validation."""

import logging
from pathlib import Path
from typing import Union

import yaml

from ..models.config_v3 import MappingConfig

logger = logging.getLogger(__name__)


def load_mapping_config(config_path: Union[str, Path]) -> MappingConfig:
    """Load and validate mapping configuration from YAML, JSON, or RML file.

    v3 Universal Format (RML/YARRRML-aligned):
    ```yaml
    namespaces: {...}
    base_iri: http://example.org/
    sources:
      data_name:
        path: data.csv
        format: csv
    mappings:
      EntityName:
        sources: data_name
        subject:
          class: ex:Entity
          iri_template: "..."
        properties: {...}
        relationships: {...}
    validation: {...}
    options: {...}
    ```

    Args:
        config_path: Path to configuration file
        
    Returns:
        Validated mapping configuration
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    # Check if it's an RDF format (RML/R2RML) - direct mode
    rdf_extensions = ['.ttl', '.rdf', '.nt', '.n3', '.xml']
    if config_path.suffix.lower() in rdf_extensions:
        # Parse as RML directly
        from .rml_parser import parse_rml
        config_data = parse_rml(config_path)
    else:
        # Load YAML/JSON
        with config_path.open("r", encoding="utf-8") as f:
            if config_path.suffix in [".yaml", ".yml"]:
                config_data = yaml.safe_load(f)
            elif config_path.suffix == ".json":
                import json
                config_data = json.load(f)
            else:
                raise ValueError(f"Unsupported config file format: {config_path.suffix}")

        # Check for external mapping file reference
        if 'mapping_file' in config_data or 'file' in config_data.get('mapping', {}):
            config_data = _load_with_external_mapping(config_data, config_path.parent)

        # Detect format and convert YARRRML if needed
        format_type = _detect_format(config_data)
        if format_type == 'yarrrml':
            from .yarrrml_parser import yarrrml_to_internal
            config_data = yarrrml_to_internal(config_data, config_path.parent)

    # Validate with Pydantic (v3 models)
    try:
        config = MappingConfig(**config_data)
    except Exception as e:
        raise ValueError(f"Invalid configuration: {e}")
    
    # Resolve relative paths in sources
    config_dir = config_path.parent

    for source_name, source in config.sources.items():
        source_path = Path(source.path)
        if not source_path.is_absolute():
            # Resolve relative to config file
            absolute_path = config_dir / source_path
            source.path = str(absolute_path)

            # Check if source file exists
            if not absolute_path.exists():
                logger.warning(f"Data source file not found: {absolute_path}")

    # Resolve validation shapes path
    if config.validation and config.validation.shacl and config.validation.shacl.shapes_file:
        shapes_path = Path(config.validation.shacl.shapes_file)
        if not shapes_path.is_absolute():
            config.validation.shacl.shapes_file = str(config_dir / shapes_path)
    
    # Resolve import paths
    if config.imports:
        resolved_imports = []
        for import_path_str in config.imports:
            import_path = Path(import_path_str)
            if not import_path.is_absolute():
                resolved_imports.append(str(config_dir / import_path))
            else:
                resolved_imports.append(import_path_str)
        config.imports = resolved_imports

    return config


def _load_with_external_mapping(config_data: dict, config_dir: Path) -> dict:
    """
    Load external mapping file and merge with configuration options.

    This allows users to:
    - Keep RML/YARRRML mapping separate
    - Add pipeline configuration (validation, options) to it
    - Reuse existing RML mappings with rdfmap-specific features

    Args:
        config_data: Configuration dict with 'mapping_file' key
        config_dir: Directory containing the config file (for resolving relative paths)

    Returns:
        Merged configuration with sheets from external file
    """
    mapping_file_path = config_data['mapping_file']
    mapping_path = Path(mapping_file_path)

    # Resolve relative path and normalize to remove '..' components
    if not mapping_path.is_absolute():
        mapping_path = (config_dir / mapping_path).resolve()
    else:
        mapping_path = mapping_path.resolve()

    if not mapping_path.exists():
        raise FileNotFoundError(f"External mapping file not found: {mapping_path}")

    # Load the external mapping file
    rdf_extensions = ['.ttl', '.rdf', '.nt', '.n3', '.xml']
    if mapping_path.suffix.lower() in rdf_extensions:
        # Parse as RML
        from .rml_parser import parse_rml
        mapping_data = parse_rml(mapping_path)
    else:
        # Load YAML/JSON
        with mapping_path.open("r", encoding="utf-8") as f:
            if mapping_path.suffix in [".yaml", ".yml"]:
                mapping_data = yaml.safe_load(f)
            elif mapping_path.suffix == ".json":
                import json
                mapping_data = json.load(f)
            else:
                raise ValueError(f"Unsupported mapping file format: {mapping_path.suffix}")

        # Convert YARRRML if needed
        format_type = _detect_format(mapping_data)
        if format_type == 'yarrrml':
            from .yarrrml_parser import yarrrml_to_internal
            # Pass the normalized parent directory
            mapping_data = yarrrml_to_internal(mapping_data, mapping_path.parent)

    # Merge: Start with sheets from external file
    merged = {
        'sheets': mapping_data.get('sheets', [])
    }

    # Resolve data source paths relative to the mapping file's directory
    for sheet in merged['sheets']:
        if 'source' in sheet:
            source_path = Path(sheet['source'])
            if not source_path.is_absolute():
                # Resolve relative to mapping file's directory
                resolved_path = (mapping_path.parent / source_path).resolve()
                sheet['source'] = str(resolved_path)

    # Add namespaces (prefer config file, fallback to mapping file)
    if 'namespaces' in config_data:
        merged['namespaces'] = config_data['namespaces']
    elif 'namespaces' in mapping_data:
        merged['namespaces'] = mapping_data['namespaces']
    else:
        # Default namespaces
        merged['namespaces'] = {
            'xsd': 'http://www.w3.org/2001/XMLSchema#',
            'rdfs': 'http://www.w3.org/2000/01/rdf-schema#'
        }

    # Add defaults (prefer config file, fallback to mapping file)
    if 'defaults' in config_data:
        merged['defaults'] = config_data['defaults']
    elif 'defaults' in mapping_data:
        merged['defaults'] = mapping_data['defaults']
    else:
        # Default base IRI
        merged['defaults'] = {'base_iri': 'http://example.org/'}

    # Add config-only fields (not in mapping file)
    if 'validation' in config_data:
        merged['validation'] = config_data['validation']

    if 'options' in config_data:
        merged['options'] = config_data['options']

    if 'imports' in config_data:
        merged['imports'] = config_data['imports']

    return merged


def _detect_format(config_data: dict) -> str:
    """
    Detect if config is YARRRML or internal format.

    Args:
        config_data: Parsed configuration dictionary

    Returns:
        'yarrrml' or 'internal'
    """
    # YARRRML has 'prefixes' and 'mappings'
    if 'prefixes' in config_data and 'mappings' in config_data:
        return 'yarrrml'

    # Internal format has 'namespaces' and 'sheets'
    if 'namespaces' in config_data and 'sheets' in config_data:
        return 'internal'

    # Default to internal for backward compatibility
    return 'internal'
