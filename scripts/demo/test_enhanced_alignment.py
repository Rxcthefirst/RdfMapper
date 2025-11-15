#!/usr/bin/env python3
"""Test the enhanced alignment report system."""

import sys
sys.path.insert(0, 'src')

from rdfmap.generator.mapping_generator import MappingGenerator, GeneratorConfig

print("="*80)
print("Testing Enhanced Alignment Report System")
print("="*80)

# Create generator
config = GeneratorConfig(
    base_iri="http://example.org/",
    include_comments=True,
    auto_detect_relationships=True,
    min_confidence=0.5
)

print("\nGenerating mapping with alignment report...")
generator = MappingGenerator(
    ontology_file='examples/mortgage/ontology/mortgage.ttl',
    data_file='examples/mortgage/data/loans.csv',
    config=config
)

# Generate mapping WITH alignment report
mapping, report = generator.generate_with_alignment_report(
    target_class='https://example.com/mortgage#MortgageLoan',
    output_path='test_enhanced_alignment.yaml'
)

print("✓ Mapping and alignment report generated")

# Save the mapping
generator.save_yaml('test_enhanced_alignment.yaml')
print("✓ Mapping saved to test_enhanced_alignment.yaml")

# Export alignment reports
generator.export_alignment_report('test_enhanced_alignment.json')
print("✓ JSON report saved to test_enhanced_alignment.json")

generator.export_alignment_html('test_enhanced_alignment.html')
print("✓ HTML report saved to test_enhanced_alignment.html")

# Display rich terminal output
print("\n" + "="*80)
print("ALIGNMENT REPORT (Rich Terminal Output)")
print("="*80)
generator.print_alignment_summary(show_details=True)

print("\n✓ All tests passed!")
print("\nYou can now:")
print("  1. View the mapping: test_enhanced_alignment.yaml")
print("  2. Open HTML report: open test_enhanced_alignment.html")
print("  3. Check JSON report: cat test_enhanced_alignment.json | jq .")

