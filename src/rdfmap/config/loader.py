"""Configuration loading and validation."""

import logging
from pathlib import Path
from typing import Union

import yaml

from ..models.mapping import MappingConfig

logger = logging.getLogger(__name__)


def load_mapping_config(config_path: Union[str, Path]) -> MappingConfig:
    """Load and validate mapping configuration from YAML, JSON, or RML file.

    Supports both old (v1) and new (v2) config structures with automatic migration.

    New structure (v2) - RECOMMENDED:
    ```yaml
    validation: {...}
    options: {...}
    mapping:
      namespaces: {...}
      base_iri: ...
      sources: [...]  # or file: ...
    ```

    Old structure (v1) - DEPRECATED:
    ```yaml
    namespaces: {...}
    defaults: {...}
    sheets: [...]  # or mapping_file: ...
    validation: {...}
    ```

    Auto-detects format and version, converts to internal representation.

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

        # Detect config version and migrate if needed
        from .migration import detect_config_version, convert_v2_to_v1_for_engine

        config_version = detect_config_version(config_data)

        if config_version == 'v2':
            logger.info("New config structure (v2) detected - converting for engine compatibility")
            # Convert v2 back to v1 for engine compatibility (temporary bridge)
            config_data = convert_v2_to_v1_for_engine(config_data)
        else:
            # Old structure detected - issue deprecation warning
            logger.warning(
                "\n" + "="*70 + "\n"
                "⚠️  DEPRECATION WARNING: Old config structure detected\n"
                "="*70 + "\n"
                "Your configuration uses the old structure which will be removed in v1.0.\n"
                "Please migrate to the new structure for better organization.\n\n"
                "OLD (deprecated):\n"
                "  namespaces: {...}\n"
                "  defaults: {base_iri: ...}\n"
                "  sheets: [...]\n\n"
                "NEW (recommended):\n"
                "  validation: {...}\n"
                "  options: {...}\n"
                "  mapping:\n"
                "    namespaces: {...}\n"
                "    base_iri: ...\n"
                "    sources: [...]\n\n"
                "See docs/CONFIGURATION_FORMATS.md for migration guide.\n"
                "="*70
            )

        # Check if this is a config with external mapping_file reference
        if 'mapping_file' in config_data:
            # Mode 3: Load external mapping and merge with config options
            config_data = _load_with_external_mapping(config_data, config_path.parent)
        else:
            # Detect format and convert YARRRML if needed
            format_type = _detect_format(config_data)

            if format_type == 'yarrrml':
                # Mode 1: Convert YARRRML to internal format
                from .yarrrml_parser import yarrrml_to_internal
                config_data = yarrrml_to_internal(config_data, config_path.parent)

    # Validate with Pydantic
    try:
        config = MappingConfig(**config_data)
    except Exception as e:
        raise ValueError(f"Invalid configuration: {e}")
    
    # Resolve relative paths in sheet sources
    config_dir = config_path.parent

    # Note: If using external mapping_file, paths were already resolved
    # in _load_with_external_mapping relative to the mapping file location.
    # Only resolve paths that are still relative.

    if config.sheets:
        for sheet in config.sheets:
            source_path = Path(sheet.source)
            if not source_path.is_absolute():
                # Path is still relative, resolve it relative to config file
                sheet.source = str(config_dir / source_path)

            # Check if source file exists
            if not Path(sheet.source).exists():
                raise FileNotFoundError(f"Data source file not found: {sheet.source}")

    # Resolve validation shapes path
    if config.validation and config.validation.shacl:
        shapes_path = Path(config.validation.shacl.shapes_file)
        if not shapes_path.is_absolute():
            config.validation.shacl.shapes_file = str(config_dir / shapes_path)
    
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
