#!/usr/bin/env python3
import json

with open('examples/comprehensive_test/alignment_report.json') as f:
    data = json.load(f)

print(f"Total matches: {len(data['match_details'])}")
print(f"\nFirst 3 columns:")
for match in data['match_details'][:3]:
    print(f"  - {match['column_name']} → {match['matched_property'].split('#')[-1]}")

print(f"\nLooking for numeric/date columns...")
for match in data['match_details']:
    col = match['column_name'].lower()
    if any(word in col for word in ['age', 'salary', 'amount', 'compensation', 'date', 'birth']):
        print(f"\nColumn: {match['column_name']}")
        print(f"Winner: {match['matcher_name']}")
        print(f"Evidence ({len(match.get('evidence', []))} matchers):")
        for ev in match.get('evidence', [])[:8]:
            print(f"  - {ev['matcher_name']}: {ev['confidence']:.3f}")

