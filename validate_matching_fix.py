#!/usr/bin/env python3
"""Validate that the matching calibration fixes work correctly."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from rdfmap.generator.mapping_generator import MappingGenerator, GeneratorConfig

def main():
    print("=" * 80)
    print("VALIDATING MATCHING CALIBRATION FIX")
    print("=" * 80)

    ont = 'examples/mortgage/ontology/mortgage.ttl'
    data = 'examples/mortgage/data/loans.csv'
    config = GeneratorConfig(base_iri='http://example.org/', min_confidence=0.5)

    print(f"\nOntology: {ont}")
    print(f"Data: {data}")
    print(f"Min confidence: {config.min_confidence}\n")

    print("Generating mappings...")
    gen = MappingGenerator(ont, data, config, use_semantic_matching=True)
    mp, report = gen.generate_with_alignment_report()

    print(f"\nAlignment Report Statistics:")
    print(f"  Total columns: {report.statistics.total_columns}")
    print(f"  Mapped columns: {report.statistics.mapped_columns}")
    print(f"  Unmapped columns: {report.statistics.unmapped_columns}")
    print(f"  Average confidence: {report.statistics.average_confidence:.3f}")
    print(f"  Mapping success rate: {report.statistics.mapping_success_rate:.1%}")

    print(f"\n{'Column':<20} {'→':<3} {'Property':<25} {'Type':<25} {'Matcher':<30} {'Confidence':<10}")
    print("-" * 130)

    # Check the problematic columns
    test_columns = ['Principal', 'InterestRate', 'OriginationDate', 'Status', 'LoanID', 'LoanTerm']
    expected_mappings = {
        'InterestRate': 'interestRate',
        'OriginationDate': 'originationDate',
        'LoanTerm': 'loanTerm',
        'Principal': 'principalAmount',  # Should map here now
        'Status': 'loanStatus',  # Should map here now
        'LoanID': 'loanNumber',  # Should map here now
    }

    results = {}
    for md in report.match_details:
        if md.column_name in test_columns:
            prop_name = md.matched_property.split('#')[-1].split('/')[-1]
            match_type = md.match_type.value if hasattr(md.match_type, 'value') else str(md.match_type)
            print(f"{md.column_name:<20} → {prop_name:<25} {match_type:<25} {md.matcher_name:<30} {md.confidence_score:<10.3f}")
            results[md.column_name] = {
                'property': prop_name,
                'matcher': md.matcher_name,
                'type': match_type,
                'confidence': md.confidence_score
            }

    # Check unmapped
    unmapped = [u.column_name for u in report.unmapped_columns if u.column_name in test_columns]
    for col in unmapped:
        print(f"{col:<20} → {'<UNMAPPED>':<25} {'-':<25} {'-':<30} {'-':<10}")
        results[col] = None

    print("\n" + "=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)

    all_pass = True
    for col, expected_prop in expected_mappings.items():
        if col not in results:
            print(f"❌ {col}: NOT IN RESULTS")
            all_pass = False
            continue

        if results[col] is None:
            print(f"⚠️  {col}: UNMAPPED (expected {expected_prop})")
            all_pass = False
            continue

        actual_prop = results[col]['property']
        matcher = results[col]['matcher']
        match_type = results[col]['type']
        confidence = results[col]['confidence']

        # Check if property is correct
        if actual_prop == expected_prop:
            # Check that it's not using DataType as primary
            if 'DataType' in matcher:
                print(f"⚠️  {col}: Correct property ({actual_prop}) but DataType matcher still active!")
                all_pass = False
            elif match_type == 'DATA_TYPE_COMPATIBILITY':
                print(f"⚠️  {col}: Correct property ({actual_prop}) but match type is DATA_TYPE_COMPATIBILITY!")
                all_pass = False
            else:
                print(f"✅ {col}: {actual_prop} (matcher: {matcher}, confidence: {confidence:.3f})")
        else:
            print(f"❌ {col}: WRONG MAPPING - got {actual_prop}, expected {expected_prop} (matcher: {matcher})")
            all_pass = False

    print("\n" + "=" * 80)
    if all_pass:
        print("✅ ALL VALIDATIONS PASSED - Matching is fixed!")
    else:
        print("❌ SOME VALIDATIONS FAILED - Matching still has issues")
    print("=" * 80)

    return 0 if all_pass else 1

if __name__ == '__main__':
    sys.exit(main())

