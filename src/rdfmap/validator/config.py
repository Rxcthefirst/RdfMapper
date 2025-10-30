"""Configuration validation utilities."""

import re
from typing import List, Set, Tuple

from ..models.mapping import MappingConfig


def extract_prefixes_from_curie(curie: str) -> Set[str]:
    """Extract namespace prefix from a CURIE.
    
    Args:
        curie: CURIE string (e.g., "ex:property" or "https://example.com/property")
        
    Returns:
        Set containing the prefix if it's a CURIE, empty set otherwise
    """
    if ":" in curie and not curie.startswith("http"):
        prefix = curie.split(":", 1)[0]
        return {prefix}
    return set()


def validate_namespace_prefixes(config: MappingConfig) -> List[Tuple[str, str]]:
    """Validate that all prefixes used in mapping are declared in namespaces.
    
    Args:
        config: Mapping configuration
        
    Returns:
        List of (context, undefined_prefix) tuples for undefined prefixes
    """
    declared_prefixes = set(config.namespaces.keys())
    used_prefixes: Set[str] = set()
    errors: List[Tuple[str, str]] = []
    
    # Check each sheet
    for sheet in config.sheets:
        # Check row resource class
        if sheet.row_resource.class_type:
            prefixes = extract_prefixes_from_curie(sheet.row_resource.class_type)
            for prefix in prefixes:
                if prefix not in declared_prefixes:
                    errors.append((f"sheet '{sheet.name}' row_resource class", prefix))
                used_prefixes.update(prefixes)
        
        # Check column mappings
        for col_name, col_mapping in sheet.columns.items():
            # Check property
            prefixes = extract_prefixes_from_curie(col_mapping.as_property)
            for prefix in prefixes:
                if prefix not in declared_prefixes:
                    errors.append((f"sheet '{sheet.name}' column '{col_name}' property", prefix))
                used_prefixes.update(prefixes)
            
            # Check datatype
            if col_mapping.datatype:
                prefixes = extract_prefixes_from_curie(col_mapping.datatype)
                for prefix in prefixes:
                    if prefix not in declared_prefixes:
                        errors.append((f"sheet '{sheet.name}' column '{col_name}' datatype", prefix))
                    used_prefixes.update(prefixes)
        
        # Check linked objects
        if sheet.objects:
            for obj_name, obj_mapping in sheet.objects.items():
                # Check predicate
                prefixes = extract_prefixes_from_curie(obj_mapping.predicate)
                for prefix in prefixes:
                    if prefix not in declared_prefixes:
                        errors.append((f"sheet '{sheet.name}' object '{obj_name}' predicate", prefix))
                    used_prefixes.update(prefixes)
                
                # Check class
                prefixes = extract_prefixes_from_curie(obj_mapping.class_type)
                for prefix in prefixes:
                    if prefix not in declared_prefixes:
                        errors.append((f"sheet '{sheet.name}' object '{obj_name}' class", prefix))
                    used_prefixes.update(prefixes)
                
                # Check object properties
                for prop_mapping in obj_mapping.properties:
                    prefixes = extract_prefixes_from_curie(prop_mapping.as_property)
                    for prefix in prefixes:
                        if prefix not in declared_prefixes:
                            errors.append((f"sheet '{sheet.name}' object '{obj_name}' property", prefix))
                        used_prefixes.update(prefixes)
                    
                    if prop_mapping.datatype:
                        prefixes = extract_prefixes_from_curie(prop_mapping.datatype)
                        for prefix in prefixes:
                            if prefix not in declared_prefixes:
                                errors.append((f"sheet '{sheet.name}' object '{obj_name}' property datatype", prefix))
                            used_prefixes.update(prefixes)
    
    return errors


def validate_required_fields(config: MappingConfig) -> List[Tuple[str, str]]:
    """Validate that IRI templates don't use fields that might be null.
    
    Args:
        config: Mapping configuration
        
    Returns:
        List of (context, field_name) tuples for potentially problematic fields
    """
    warnings: List[Tuple[str, str]] = []
    
    # Pattern to extract template variables
    template_var_pattern = re.compile(r'\{([^}]+)\}')
    
    for sheet in config.sheets:
        # Check row resource IRI template
        if sheet.row_resource.iri_template:
            variables = template_var_pattern.findall(sheet.row_resource.iri_template)
            for var in variables:
                if var == "base_iri":
                    continue
                # Check if this variable corresponds to a required column
                if var in sheet.columns:
                    col_mapping = sheet.columns[var]
                    if not col_mapping.required:
                        warnings.append((
                            f"sheet '{sheet.name}' row IRI template",
                            f"field '{var}' used in IRI template but not marked as required"
                        ))
        
        # Check linked object IRI templates
        if sheet.objects:
            for obj_name, obj_mapping in sheet.objects.items():
                if obj_mapping.iri_template:
                    variables = template_var_pattern.findall(obj_mapping.iri_template)
                    for var in variables:
                        if var == "base_iri":
                            continue
                        # Check if variable is in any property mapping
                        prop_columns = [p.column for p in obj_mapping.properties]
                        if var not in prop_columns and var in sheet.columns:
                            col_mapping = sheet.columns[var]
                            if not col_mapping.required:
                                warnings.append((
                                    f"sheet '{sheet.name}' object '{obj_name}' IRI template",
                                    f"field '{var}' used in IRI template but not marked as required"
                                ))
    
    return warnings
