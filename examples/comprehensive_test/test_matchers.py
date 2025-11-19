#!/usr/bin/env python3
"""
Test script to validate all matchers are exercised by the comprehensive test dataset.
"""

from rdfmap.generator.mapping_generator import MappingGenerator, GeneratorConfig
import json
from collections import Counter

def test_comprehensive_matchers():
    """Run the comprehensive test and analyze matcher usage."""

    print("=" * 80)
    print("COMPREHENSIVE MATCHER TEST SUITE")
    print("=" * 80)
    print()

    # Generate mappings
    print("📊 Generating mappings...")
    gen = MappingGenerator(
        ontology_file='examples/comprehensive_test/hr_ontology.ttl',
        data_file='examples/comprehensive_test/employees.csv',
        config=GeneratorConfig(
            base_iri='http://example.org/employees/',
            min_confidence=0.35,  # Lower to allow partial/fuzzy matchers
            imports=['examples/comprehensive_test/hr_vocabulary.ttl']  # Load SKOS vocabulary
        )
    )

    mapping, report = gen.generate_with_alignment_report()

    # Statistics
    stats = report.statistics
    print(f"✅ Mapped: {stats.mapped_columns}/{stats.total_columns} columns ({stats.mapping_success_rate*100:.1f}%)")
    print(f"📈 Average confidence: {stats.average_confidence:.3f}")
    print()

    # Analyze matcher usage
    print("=" * 80)
    print("MATCHER USAGE ANALYSIS")
    print("=" * 80)
    print()

    matcher_counts = Counter()
    matcher_examples = {}

    for detail in report.match_details:
        matcher = detail.matcher_name
        matcher_counts[matcher] += 1

        if matcher not in matcher_examples:
            matcher_examples[matcher] = []

        matcher_examples[matcher].append({
            'column': detail.column_name,
            'property': detail.matched_property.split('#')[-1].split('/')[-1],
            'confidence': detail.confidence_score,
            'matched_via': detail.matched_via
        })

    # Print results
    print(f"Total unique matchers used: {len(matcher_counts)}")
    print()

    for matcher, count in sorted(matcher_counts.items(), key=lambda x: -x[1]):
        print(f"{matcher}:")
        print(f"  Count: {count}")
        print(f"  Examples:")
        for ex in matcher_examples[matcher][:3]:  # Show first 3 examples
            print(f"    • {ex['column']} → {ex['property']} ({ex['confidence']:.2f})")
            print(f"      via: {ex['matched_via']}")
        print()

    # Validation checks
    print("=" * 80)
    print("VALIDATION CHECKS")
    print("=" * 80)
    print()

    expected_matchers = {
        'ExactPrefLabelMatcher',
        'ExactRdfsLabelMatcher',
        'ExactAltLabelMatcher',
        'ExactHiddenLabelMatcher',
        'ExactLocalNameMatcher',
        'SemanticSimilarityMatcher',
        'LexicalMatcher',
        'PropertyHierarchyMatcher',
        'OWLCharacteristicsMatcher',
        'RelationshipMatcher',
        'ObjectPropertyMatcher'
    }

    found_matchers = set(matcher_counts.keys())
    missing_matchers = expected_matchers - found_matchers

    if missing_matchers:
        print(f"⚠️  Missing matchers: {', '.join(missing_matchers)}")
    else:
        print("✅ All expected matchers were used!")

    print()

    # Check confidence range
    confidences = [d.confidence_score for d in report.match_details]
    max_conf = max(confidences)
    min_conf = min(confidences)

    print(f"Confidence range: {min_conf:.2f} - {max_conf:.2f}")

    if max_conf >= 0.99:
        print(f"⚠️  Found confidence >= 0.99: {max_conf:.2f}")
    else:
        print("✅ No confidence scores >= 0.99")

    print()

    # Export detailed report
    report_data = {
        'statistics': {
            'total_columns': stats.total_columns,
            'mapped_columns': stats.mapped_columns,
            'success_rate': stats.mapping_success_rate,
            'average_confidence': stats.average_confidence
        },
        'matcher_usage': dict(matcher_counts),
        'match_details': [
            {
                'column': d.column_name,
                'property': d.matched_property,
                'matcher': d.matcher_name,
                'confidence': d.confidence_score,
                'match_type': d.match_type.value if hasattr(d.match_type, 'value') else str(d.match_type),
                'matched_via': d.matched_via
            }
            for d in report.match_details
        ]
    }

    with open('examples/comprehensive_test/test_results.json', 'w') as f:
        json.dump(report_data, f, indent=2)

    print("📄 Detailed report saved to: examples/comprehensive_test/test_results.json")
    print()

    # Save alignment report
    gen.export_alignment_report('examples/comprehensive_test/alignment_report.json')
    gen.export_alignment_html('examples/comprehensive_test/alignment_report.html')

    print("📄 Alignment report saved to: examples/comprehensive_test/alignment_report.json")
    print("📄 HTML report saved to: examples/comprehensive_test/alignment_report.html")
    print()

    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    test_comprehensive_matchers()

