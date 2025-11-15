#!/usr/bin/env python3
"""Debug script to trace generator matching decisions."""

import sys
sys.path.insert(0, 'src')

from rdfmap.generator.mapping_generator import MappingGenerator, GeneratorConfig
from rdfmap.generator.ontology_analyzer import OntologyAnalyzer
from rdfmap.generator.data_analyzer import DataSourceAnalyzer

print("="*80)
print("GENERATOR MATCHING DEBUG")
print("="*80)

# Configuration
config = GeneratorConfig(
    base_iri="http://example.org/mortgage/",
    include_comments=True,
    auto_detect_relationships=True,
    min_confidence=0.5
)

print("\n1. Loading ontology...")
ontology = OntologyAnalyzer('examples/mortgage/ontology/mortgage.ttl')
print(f"   ✓ Loaded {len(ontology.classes)} classes")
print(f"   ✓ Loaded {len(ontology.properties)} properties")

print("\n   Properties found:")
for prop_uri, prop in ontology.properties.items():
    domain = prop.domain or "None"
    range_type = prop.range_type or "None"
    print(f"   - {prop.label:20} | domain: {str(domain)[:40]:40} | range: {str(range_type)[:20]}")

print("\n2. Analyzing data...")
data_analyzer = DataSourceAnalyzer('examples/mortgage/data/loans.csv')
fields = list(data_analyzer.field_analyses.values())
print(f"   ✓ Found {len(fields)} columns")

print("\n   Columns found:")
for field in fields:
    samples = str(field.sample_values[:2]) if field.sample_values else "[]"
    print(f"   - {field.name:20} | type: {field.inferred_type:15} | samples: {samples[:40]}")

print("\n3. Creating generator...")
generator = MappingGenerator(
    ontology_file='examples/mortgage/ontology/mortgage.ttl',
    data_file='examples/mortgage/data/loans.csv',
    config=config
)

print("\n4. Matching columns to properties...")
print("\n" + "="*80)

# Manually test each column
test_columns = ['LoanID', 'BorrowerID', 'BorrowerName', 'PropertyID', 'PropertyAddress',
                'Principal', 'InterestRate', 'OriginationDate', 'LoanTerm', 'Status']

for col_name in test_columns:
    # Find the field
    field = next((f for f in fields if f.name == col_name), None)
    if not field:
        print(f"\n❌ Column '{col_name}' not found")
        continue

    print(f"\n📊 Column: {col_name}")
    print(f"   Type: {field.inferred_type}")
    print(f"   Samples: {field.sample_values[:3] if field.sample_values else 'None'}")

    # Try to find matches manually using the matcher pipeline
    if hasattr(generator, 'matcher_pipeline'):
        from rdfmap.generator.matchers import MatchContext

        context = MatchContext(
            column=field,
            all_columns=[f.name for f in fields],
            target_class_uri=generator.target_class_uri if hasattr(generator, 'target_class_uri') else None
        )

        # Run through matchers
        result = generator.matcher_pipeline.match(field, list(ontology.properties.values()), context)

        if result:
            print(f"   ✓ MATCHED: {result.property.label} ({result.property.uri})")
            print(f"     Confidence: {result.confidence:.2f}")
            print(f"     Match type: {result.match_type}")
            print(f"     Explanation: {result.matched_via}")
        else:
            print(f"   ✗ NO MATCH FOUND")
            print(f"     Min confidence threshold: {config.min_confidence}")
    else:
        print("   ⚠ Generator has no matcher_pipeline attribute")

print("\n" + "="*80)
print("Expected mappings (from mortgage_mapping.yaml):")
print("="*80)

expected = {
    'LoanID': 'ex:loanNumber',
    'BorrowerID': '(FK to Borrower)',
    'BorrowerName': 'Borrower.ex:borrowerName',
    'PropertyID': '(FK to Property)',
    'PropertyAddress': 'Property.ex:propertyAddress',
    'Principal': 'ex:principalAmount',
    'InterestRate': 'ex:interestRate',
    'OriginationDate': 'ex:originationDate',
    'LoanTerm': 'ex:loanTerm',
    'Status': 'ex:loanStatus'
}

for col, expected_prop in expected.items():
    print(f"  {col:20} → {expected_prop}")

print("\n" + "="*80)

