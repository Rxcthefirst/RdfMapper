#!/usr/bin/env python3
"""Test the alignment report feature."""

import sys
sys.path.insert(0, 'src')

from rdfmap.generator.mapping_generator import MappingGenerator, GeneratorConfig

print("="*80)
print("Testing Alignment Report Feature")
print("="*80)

# Create generator
config = GeneratorConfig(
    base_iri="http://example.org/",
    include_comments=True,
    auto_detect_relationships=True,
    min_confidence=0.5
)

print("\nGenerating mapping...")
generator = MappingGenerator(
    ontology_file='examples/mortgage/ontology/mortgage.ttl',
    data_file='examples/mortgage/data/loans.csv',
    config=config
)

# Generate mapping
mapping = generator.generate(
    target_class='https://example.com/mortgage#MortgageLoan',
    output_path='test_alignment.yaml'
)

print("✓ Mapping generated")

# Save the mapping
generator.save_yaml('test_alignment.yaml')
print("✓ Mapping saved to test_alignment.yaml")

# Save alignment reports
json_path, html_path = generator.save_alignment_report('.')
print(f"✓ Alignment reports saved:")
print(f"  • JSON: {json_path}")
print(f"  • HTML: {html_path}")

# Display terminal output
print("\n" + "="*80)
print("ALIGNMENT REPORT")
print("="*80)
generator.print_alignment_summary(show_details=True)

# Get report for programmatic access
report = generator.get_alignment_report()
print(f"\nProgrammatic access:")
print(f"  Total columns: {report.total_columns}")
print(f"  Mapped: {report.mapped_columns}")
print(f"  Success rate: {report.mapping_success_rate:.1f}%")
print(f"  Avg confidence: {report.average_confidence:.2f}")

print("\n✓ All tests passed!")
print("\nYou can now:")
print("  1. Open alignment_report.html in a browser")
print("  2. Review alignment_report.json programmatically")
print("  3. Check test_alignment.yaml for the mapping")

