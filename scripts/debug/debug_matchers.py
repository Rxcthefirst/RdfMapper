#!/usr/bin/env python3
"""Simple debug script to test matcher pipeline."""

import sys
sys.path.insert(0, 'src')

from rdfmap.generator.ontology_analyzer import OntologyAnalyzer
from rdfmap.generator.data_analyzer import DataSourceAnalyzer
from rdfmap.generator.matchers import create_default_pipeline, MatchContext
from rdfmap.generator.graph_reasoner import GraphReasoner

print("="*80)
print("MATCHER PIPELINE DEBUG")
print("="*80)

# Load ontology
print("\n1. Loading ontology...")
ontology = OntologyAnalyzer('examples/mortgage/ontology/mortgage.ttl')
properties = list(ontology.properties.values())
print(f"   ✓ {len(properties)} properties")

# Load data
print("\n2. Loading data...")
data = DataSourceAnalyzer('examples/mortgage/data/loans.csv')
fields = list(data.field_analyses.values())
print(f"   ✓ {len(fields)} columns")

# Create reasoner
print("\n3. Creating reasoner...")
reasoner = GraphReasoner(ontology.graph, ontology.classes, ontology.properties)
print(f"   ✓ Reasoner created")

# Create matcher pipeline  
print("\n4. Creating matcher pipeline...")
pipeline = create_default_pipeline(
    use_graph_reasoning=True,
    reasoner=reasoner
)
print(f"   ✓ Pipeline with {len(pipeline.matchers)} matchers")

# Test each column
print("\n5. Testing matches...")
print("="*80)

expected_mappings = {
    'LoanID': 'loanNumber',
    'BorrowerID': '(FK)',
    'BorrowerName': '(FK property)',
    'PropertyID': '(FK)',
    'PropertyAddress': '(FK property)',
    'Principal': 'principalAmount',
    'InterestRate': 'interestRate',
    'OriginationDate': 'originationDate',
    'LoanTerm': 'loanTerm',
    'Status': 'loanStatus'
}

for field in fields:
    # Create context
    context = MatchContext(
        column=field,
        all_columns=fields,
        available_properties=properties,
        domain_hints=None
    )
    
    # Match
    result = pipeline.match(field, properties, context)
    
    expected = expected_mappings.get(field.name, '?')
    
    if result:
        matched_label = result.property.label
        status = "✓" if matched_label in expected or expected in matched_label else "✗"
        print(f"\n{status} {field.name:20} → {matched_label:25} (confidence: {result.confidence:.2f})")
        print(f"     Expected: {expected}")
        print(f"     Match type: {result.match_type}")
        print(f"     Via: {result.matched_via}")
        
        if status == "✗":
            print(f"     ⚠️  WRONG MATCH!")
    else:
        print(f"\n✗ {field.name:20} → NO MATCH")
        print(f"     Expected: {expected}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

# Count results
total = len(fields)
matched = sum(1 for f in fields if pipeline.match(f, properties, MatchContext(f, fields, properties)) is not None)
print(f"Matched: {matched}/{total} ({matched/total*100:.0f}%)")

