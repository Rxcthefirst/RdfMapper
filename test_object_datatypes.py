#!/usr/bin/env python3
"""Test script to verify object property datatypes are included."""

import sys
sys.path.insert(0, 'src')

from rdfmap.generator.mapping_generator import MappingGenerator, GeneratorConfig
from rdfmap.generator.yaml_formatter import save_formatted_mapping

# Create generator
config = GeneratorConfig(
    base_iri="http://example.org/",
    include_comments=True,
    auto_detect_relationships=True,
    min_confidence=0.5
)

generator = MappingGenerator(
    ontology_file='examples/mortgage/ontology/mortgage.ttl',
    data_file='examples/mortgage/data/loans.csv',
    config=config
)

# Generate mapping
mapping = generator.generate(
    target_class='https://example.com/mortgage#MortgageLoan',
    output_path='test_with_object_datatypes.yaml'
)

# Save with formatter
save_formatted_mapping(mapping, 'test_with_object_datatypes.yaml')

print("✓ Generated test_with_object_datatypes.yaml")
print("\nChecking object properties...")

# Verify object properties have datatypes
for sheet in mapping.get('sheets', []):
    objects = sheet.get('objects', {})
    for obj_name, obj_config in objects.items():
        print(f"\n{obj_name}:")
        for prop in obj_config.get('properties', []):
            has_datatype = 'datatype' in prop
            has_required = 'required' in prop
            print(f"  - {prop.get('column')}: datatype={has_datatype}, required={has_required}")
            if has_datatype:
                print(f"    → datatype: {prop.get('datatype')}")
            if has_required:
                print(f"    → required: {prop.get('required')}")

print("\n✓ Complete!")

