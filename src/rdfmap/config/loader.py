"""Configuration loading and validation."""

from pathlib import Path
from typing import Union

import yaml

from ..models.mapping import MappingConfig


def load_mapping_config(config_path: Union[str, Path]) -> MappingConfig:
    """Load and validate mapping configuration from YAML or JSON file.
    
    Supports both YARRRML standard format and internal format.
    Auto-detects format and converts YARRRML to internal representation.

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
    
    # Load YAML/JSON
    with config_path.open("r", encoding="utf-8") as f:
        if config_path.suffix in [".yaml", ".yml"]:
            config_data = yaml.safe_load(f)
        elif config_path.suffix == ".json":
            import json
            config_data = json.load(f)
        else:
            raise ValueError(f"Unsupported config file format: {config_path.suffix}")
    
    # Detect format and convert YARRRML if needed
    format_type = _detect_format(config_data)

    if format_type == 'yarrrml':
        # Convert YARRRML to internal format
        from .yarrrml_parser import yarrrml_to_internal
        config_data = yarrrml_to_internal(config_data, config_path.parent)

    # Validate with Pydantic
    try:
        config = MappingConfig(**config_data)
    except Exception as e:
        raise ValueError(f"Invalid configuration: {e}")
    
    # Resolve relative paths in sheet sources
    config_dir = config_path.parent
    for sheet in config.sheets:
        source_path = Path(sheet.source)
        if not source_path.is_absolute():
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
