#!/usr/bin/env python3
"""Debug script to check if evidence is being captured."""

from rdfmap.generator.mapping_generator import MappingGenerator, GeneratorConfig

gen = MappingGenerator(
    ontology_file='examples/comprehensive_test/hr_ontology.ttl',
    data_file='examples/comprehensive_test/employees.csv',
    config=GeneratorConfig(
        base_iri='http://example.org/employees/',
        min_confidence=0.35,
        imports=['examples/comprehensive_test/hr_vocabulary.ttl']
    )
)

# Generate mapping
mapping, report = gen.generate_with_alignment_report()

print("="*80)
print("EVIDENCE DEBUG")
print("="*80)
print()

# Check _match_extras
print(f"Total columns in _match_extras: {len(gen._match_extras)}")
print()

# Show first 5
for i, (col_name, extras) in enumerate(list(gen._match_extras.items())[:5]):
    print(f"\nColumn: {col_name}")
    print(f"  Evidence count: {len(extras.get('evidence', []))}")
    print(f"  Base type: {extras.get('base_type')}")

    evidence = extras.get('evidence', [])
    if evidence:
        print(f"  Evidence:")
        for ev in evidence[:3]:
            print(f"    - {ev.get('matcher_name')}: {ev.get('confidence')} ({ev.get('match_type')})")
    else:
        print(f"  ⚠️ NO EVIDENCE CAPTURED")

print()
print("="*80)
print("ALIGNMENT REPORT CHECK")
print("="*80)

# Check alignment report
if report and report.match_details:
    print(f"\nTotal match details: {len(report.match_details)}")

    for match in report.match_details[:5]:
        print(f"\n{match.column_name} → {match.matched_property.split('#')[-1]}")
        print(f"  Matcher: {match.matcher_name}")
        print(f"  Evidence items: {len(match.evidence) if match.evidence else 0}")

        if match.evidence:
            for ev in match.evidence[:3]:
                print(f"    - {ev.matcher_name}: {ev.confidence}")
        else:
            print(f"  ⚠️ NO EVIDENCE IN MATCH DETAIL")

