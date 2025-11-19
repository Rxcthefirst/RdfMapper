#!/usr/bin/env python3
"""Quick summary of matcher status."""

import json

with open('examples/comprehensive_test/test_results.json', 'r') as f:
    results = json.load(f)

print("="*80)
print("MATCHER STATUS SUMMARY")
print("="*80)
print()

# Count matchers
matcher_counts = {}
for match in results['match_details']:
    matcher = match['matcher']
    matcher_counts[matcher] = matcher_counts.get(matcher, 0) + 1

print(f"Total Matchers Working: {len(matcher_counts)}/17")
print()

for matcher, count in sorted(matcher_counts.items(), key=lambda x: -x[1]):
    print(f"  {matcher}: {count}")

print()
print(f"Total Columns: {results['statistics']['total_columns']}")
print(f"Mapped Columns: {results['statistics']['mapped_columns']}")
print(f"Success Rate: {results['statistics']['success_rate']*100:.1f}%")

