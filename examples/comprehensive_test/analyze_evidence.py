#!/usr/bin/env python3
"""
Final comprehensive test - show ALL matchers in action by examining evidence.
Even if a matcher doesn't WIN, it should appear in the evidence list.
"""

import json
from collections import defaultdict

print("="*80)
print("COMPREHENSIVE MATCHER EVIDENCE ANALYSIS")
print("="*80)
print()

# Load alignment report (has evidence)
with open('examples/comprehensive_test/alignment_report.json', 'r') as f:
    results = json.load(f)

# Count which matchers appear in evidence (not just winners)
all_matchers_in_evidence = set()
winner_matchers = defaultdict(int)
evidence_counts = defaultdict(int)

for match in results['match_details']:
    # Winner
    winner = match['matcher_name']
    winner_matchers[winner] += 1

    # All matchers in evidence
    if match.get('evidence'):
        for ev in match['evidence']:
            matcher_name = ev['matcher_name']
            all_matchers_in_evidence.add(matcher_name)
            evidence_counts[matcher_name] += 1

print(f"Matchers that WON matches: {len(winner_matchers)}")
for matcher, count in sorted(winner_matchers.items(), key=lambda x: -x[1]):
    print(f"  ✅ {matcher}: {count} wins")

print()
print(f"Matchers that appeared in EVIDENCE: {len(all_matchers_in_evidence)}")
print()
for matcher in sorted(all_matchers_in_evidence):
    wins = winner_matchers.get(matcher, 0)
    total_evidence = evidence_counts[matcher]
    if wins == 0:
        print(f"  📊 {matcher}: 0 wins, {total_evidence} evidence entries (never won)")
    else:
        print(f"  ✅ {matcher}: {wins} wins, {total_evidence} evidence entries")

print()
print(f"{'='*80}")
print("ANALYSIS")
print(f"{'='*80}")
print(f"\nTotal unique matchers in pipeline: 17")
print(f"Matchers that won matches: {len(winner_matchers)}")
print(f"Matchers that fired (in evidence): {len(all_matchers_in_evidence)}")
print(f"Matchers never seen: {17 - len(all_matchers_in_evidence)}")

if len(all_matchers_in_evidence) < 17:
    print(f"\n⚠️ Missing matchers:")
    all_17 = {
        'ExactPrefLabelMatcher', 'ExactRdfsLabelMatcher', 'ExactAltLabelMatcher',
        'ExactHiddenLabelMatcher', 'ExactLocalNameMatcher', 'PropertyHierarchyMatcher',
        'OWLCharacteristicsMatcher', 'RestrictionBasedMatcher', 'SKOSRelationsMatcher',
        'SemanticSimilarityMatcher', 'LexicalMatcher', 'DataTypeInferenceMatcher',
        'HistoryAwareMatcher', 'StructuralMatcher', 'GraphReasoningMatcher',
        'PartialStringMatcher', 'FuzzyStringMatcher'
    }
    missing = all_17 - all_matchers_in_evidence
    for m in sorted(missing):
        print(f"    ❌ {m}")

# Show examples where multiple matchers contributed
print(f"\n{'='*80}")
print("COLUMNS WITH MULTIPLE MATCHER EVIDENCE (Top 10)")
print(f"{'='*80}")

multi_evidence = [(m, len(m.get('evidence', []))) for m in results['match_details']]
multi_evidence.sort(key=lambda x: -x[1])

for match, ev_count in multi_evidence[:10]:
    if ev_count > 1:
        print(f"\n{match['column_name']} → {match['matched_property'].split('#')[-1]}")
        print(f"  Winner: {match['matcher_name']} ({match.get('confidence_score', match.get('confidence', 0.0)):.3f})")
        print(f"  Evidence ({ev_count} matchers):")
        for ev in match['evidence'][:7]:  # Top 7
            print(f"    - {ev['matcher_name']}: {ev['confidence']:.3f} via '{ev['matched_via']}'")


