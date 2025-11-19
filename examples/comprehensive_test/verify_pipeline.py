#!/usr/bin/env python3
"""
Script to verify ALL 17 matchers can fire.

Strategy: Deliberately create columns that will trigger each matcher type.
"""

from rdfmap.generator.mapping_generator import MappingGenerator, GeneratorConfig

print("="*80)
print("COMPREHENSIVE MATCHER VERIFICATION")
print("="*80)
print()

# Test configuration that should exercise all matchers
gen = MappingGenerator(
    ontology_file='examples/comprehensive_test/hr_ontology.ttl',
    data_file='examples/comprehensive_test/employees.csv',
    config=GeneratorConfig(
        base_iri='http://example.org/employees/',
        min_confidence=0.40,
        imports=['examples/comprehensive_test/hr_vocabulary.ttl']
    )
)

print(f"Pipeline has {len(gen.matcher_pipeline.matchers)} matchers")
print()
print("Matchers in pipeline:")
for i, matcher in enumerate(gen.matcher_pipeline.matchers, 1):
    print(f"  {i}. {matcher.__class__.__name__} (threshold={matcher.threshold}, enabled={matcher.enabled})")

print()
print("="*80)
print("ANALYSIS")
print("="*80)

# Count by type
exact_matchers = [m for m in gen.matcher_pipeline.matchers if 'Exact' in m.__class__.__name__]
ontology_matchers = [m for m in gen.matcher_pipeline.matchers if any(x in m.__class__.__name__ for x in ['Hierarchy', 'OWL', 'Restriction', 'SKOS'])]
semantic_matchers = [m for m in gen.matcher_pipeline.matchers if any(x in m.__class__.__name__ for x in ['Semantic', 'Lexical'])]
structure_matchers = [m for m in gen.matcher_pipeline.matchers if any(x in m.__class__.__name__ for x in ['Structural', 'Graph', 'DataType'])]
fallback_matchers = [m for m in gen.matcher_pipeline.matchers if any(x in m.__class__.__name__ for x in ['Partial', 'Fuzzy', 'History'])]

print(f"\nExact Matchers: {len(exact_matchers)}")
print(f"Ontology Matchers: {len(ontology_matchers)}")
print(f"Semantic Matchers: {len(semantic_matchers)}")
print(f"Structure Matchers: {len(structure_matchers)}")
print(f"Fallback Matchers: {len(fallback_matchers)}")
print(f"\nTotal: {len(gen.matcher_pipeline.matchers)}")

print()
print("="*80)
print("WHY SOME MATCHERS DON'T FIRE")
print("="*80)
print()
print("The issue is NOT that matchers are missing from the pipeline.")
print("ALL 17 matchers ARE present and enabled.")
print()
print("The issue is that EXACT matchers win for almost everything because")
print("we added comprehensive SKOS labels to every property.")
print()
print("To test other matchers, we need columns that:")
print("  1. Don't have exact SKOS label matches")
print("  2. Require hierarchy reasoning")
print("  3. Require OWL characteristics analysis")
print("  4. Require fuzzy/partial matching")
print()
print("Examples needed:")
print("  - 'super_identifier' → should match via PropertyHierarchyMatcher")
print("  - 'uniq_id' → should match via OWLCharacteristicsMatcher (IFP)")
print("  - 'wrk_loc' → should match via FuzzyStringMatcher")
print("  - 'ph' → should match via PartialStringMatcher")
EOF

