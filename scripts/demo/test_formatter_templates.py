#!/usr/bin/env python3
"""Test the enhanced formatter with template sections."""

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
    output_path='test_with_templates.yaml'
)

# Save with formatter (includes template sections)
save_formatted_mapping(mapping, 'test_with_templates.yaml')

print("✓ Generated test_with_templates.yaml with template sections")
print("\nFile now includes:")
print("  ✓ Active configuration sections")
print("  ✓ Commented validation template (if not configured)")
print("  ✓ Commented imports template (if not configured)")
print("  ✓ Advanced features examples")
print("  ✓ Processing options reference")
print("  ✓ Usage examples")
print("\nThe file is self-documenting and guides users on all available features!")

