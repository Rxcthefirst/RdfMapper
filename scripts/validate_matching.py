#!/usr/bin/env python3
"""
Quick validation script to test matching system with mortgage example.
Run this to identify confidence scoring and matcher attribution issues.
"""

from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from rdfmap.generator.mapping_generator import MappingGenerator, GeneratorConfig


def main():
    print("="*70)
    print("MATCHING SYSTEM VALIDATION - Mortgage Example")
    print("="*70)
    print()

    # Paths
    ontology_file = Path('examples/mortgage/ontology/mortgage.ttl')
    data_file = Path('examples/mortgage/data/loans.csv')

    if not ontology_file.exists():
        print(f"❌ Ontology file not found: {ontology_file}")
        return 1

    if not data_file.exists():
        print(f"❌ Data file not found: {data_file}")
        return 1

    print(f"📊 Data: {data_file}")
    print(f"🔗 Ontology: {ontology_file}")
    print()

    # Generate mappings
    print("🔄 Generating mappings...")
    generator = MappingGenerator(
        ontology_file=str(ontology_file),
        data_file=str(data_file),
        config=GeneratorConfig(base_iri='http://example.org/'),
        use_semantic_matching=True
    )

    mapping_config, alignment_report = generator.generate_with_alignment_report()

    print(f"✅ Generated {len(alignment_report.match_details)} matches")
    print()

    # Analyze results
    print("="*70)
    print("MATCH ANALYSIS")
    print("="*70)
    print()

    confidence_scores = []
    match_types = {}
    matchers = {}

    print(f"{'Column':<20} {'Property':<25} {'Type':<20} {'Confidence':<12} {'Matcher':<25}")
    print("-"*102)

    for detail in alignment_report.match_details:
        # Extract property short name
        prop_name = detail.matched_property.split('#')[-1].split('/')[-1]

        # Track metrics
        confidence_scores.append(detail.confidence_score)
        match_types[detail.match_type] = match_types.get(detail.match_type, 0) + 1
        matchers[detail.matcher_name] = matchers.get(detail.matcher_name, 0) + 1

        # Print row
        print(f"{detail.column_name:<20} {prop_name:<25} {detail.match_type.value:<20} {detail.confidence_score:<12.3f} {detail.matcher_name:<25}")

    print()
    print("="*70)
    print("VALIDATION CHECKS")
    print("="*70)
    print()

    # Check 1: Semantic confidence scores
    semantic_scores = [
        (d.column_name, d.confidence_score)
        for d in alignment_report.match_details
        if 'SEMANTIC' in d.match_type.value
    ]

    print("1. Semantic Similarity Confidence Scores:")
    print("-" * 70)

    issues_found = False
    for col_name, score in semantic_scores:
        if score == 1.00:
            print(f"   ⚠️  {col_name}: {score:.3f} - Should be < 1.00 (likely 0.4-0.9)")
            issues_found = True
        elif score < 0.4:
            print(f"   ⚠️  {col_name}: {score:.3f} - Unusually low")
            issues_found = True
        elif score > 0.95:
            print(f"   ⚠️  {col_name}: {score:.3f} - Unusually high for semantic match")
            issues_found = True
        else:
            print(f"   ✅ {col_name}: {score:.3f} - Valid range")

    if not issues_found:
        print("   ✅ All semantic scores in valid range [0.4, 0.95]")

    print()

    # Check 2: Matcher attribution
    print("2. Matcher Attribution:")
    print("-" * 70)

    for matcher_name, count in sorted(matchers.items(), key=lambda x: -x[1]):
        print(f"   {matcher_name}: {count} matches")

    print()

    # Check if DataTypeInferenceMatcher is overused
    if 'DataTypeInferenceMatcher' in matchers:
        dt_count = matchers['DataTypeInferenceMatcher']
        total = len(alignment_report.match_details)
        if dt_count > total * 0.5:
            print(f"   ⚠️  DataTypeInferenceMatcher is primary matcher for {dt_count}/{total} columns")
            print(f"       This may indicate matcher priority issue")
        else:
            print(f"   ✅ Matcher attribution looks balanced")

    print()

    # Check 3: Confidence distribution
    print("3. Confidence Score Distribution:")
    print("-" * 70)

    import numpy as np
    scores_array = np.array(confidence_scores)

    print(f"   Min:    {scores_array.min():.3f}")
    print(f"   Max:    {scores_array.max():.3f}")
    print(f"   Mean:   {scores_array.mean():.3f}")
    print(f"   Median: {np.median(scores_array):.3f}")
    print(f"   Std:    {scores_array.std():.3f}")
    print()

    # Histogram
    high_conf = sum(1 for s in confidence_scores if s >= 0.8)
    med_conf = sum(1 for s in confidence_scores if 0.5 <= s < 0.8)
    low_conf = sum(1 for s in confidence_scores if s < 0.5)

    print(f"   High confidence (≥0.8): {high_conf}")
    print(f"   Med confidence (0.5-0.8): {med_conf}")
    print(f"   Low confidence (<0.5): {low_conf}")
    print()

    if scores_array.std() < 0.05:
        print(f"   ⚠️  Very low variance - scores may not be well calibrated")
    else:
        print(f"   ✅ Good variance in confidence scores")

    print()
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print()

    # Overall assessment
    issues = []

    # Check for 1.00 semantic scores
    if any(score == 1.00 for _, score in semantic_scores):
        issues.append("Semantic matches showing 1.00 confidence (should be <1.00)")

    # Check for low variance
    if scores_array.std() < 0.05:
        issues.append("Low confidence score variance")

    # Check matcher distribution
    if 'DataTypeInferenceMatcher' in matchers and matchers['DataTypeInferenceMatcher'] > len(alignment_report.match_details) * 0.5:
        issues.append("DataTypeInferenceMatcher may be overused")

    if issues:
        print("❌ Issues Found:")
        for issue in issues:
            print(f"   - {issue}")
        print()
        print("🔧 Recommended Actions:")
        print("   1. Review SemanticMatcher confidence calculation")
        print("   2. Check matcher priority in MappingGenerator")
        print("   3. Verify MatchDetail construction uses actual scores")
        return 1
    else:
        print("✅ All validation checks passed!")
        print()
        print("🎉 Matching system is working correctly")
        return 0


if __name__ == '__main__':
    sys.exit(main())

