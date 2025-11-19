#!/usr/bin/env python3
"""Debug script to see what matchers are producing."""

from rdfmap.generator.mapping_generator import MappingGenerator, GeneratorConfig
from rdfmap.generator.data_analyzer import DataSourceAnalyzer

# Test single column
print("Testing exact matching for 'Employee ID' column")
print("="*80)

gen = MappingGenerator(
    ontology_file='examples/comprehensive_test/hr_ontology.ttl',
    data_file='examples/comprehensive_test/employees.csv',
    config=GeneratorConfig(
        base_iri='http://example.org/employees/',
        min_confidence=0.40,
        imports=['examples/comprehensive_test/hr_vocabulary.ttl']
    )
)

# Check if SKOS labels were loaded
print("\nChecking if SKOS labels were loaded:")
for prop_uri, prop in list(gen.ontology.properties.items())[:5]:
    print(f"\nProperty: {prop_uri}")
    print(f"  rdfs:label: {prop.label}")
    print(f"  skos:prefLabel: {prop.pref_label}")
    print(f"  skos:altLabel: {prop.alt_labels}")
    print(f"  skos:hiddenLabel: {prop.hidden_labels}")

# Test exact matchers
print("\n" + "="*80)
print("Testing matchers on 'Employee ID' column:")
print("="*80)

col_analysis = gen.data_source.get_analysis("Employee ID")
properties = gen.ontology.get_datatype_properties(list(gen.ontology.classes.values())[0].uri)

from rdfmap.generator.matchers.base import MatchContext
context = MatchContext(
    column=col_analysis,
    all_columns=[gen.data_source.get_analysis(c) for c in gen.data_source.get_column_names()],
    available_properties=properties
)

# Try each exact matcher
from rdfmap.generator.matchers import (
    ExactPrefLabelMatcher,
    ExactRdfsLabelMatcher,
    ExactAltLabelMatcher,
    ExactHiddenLabelMatcher,
    ExactLocalNameMatcher,
    SemanticSimilarityMatcher,
    LexicalMatcher
)

matchers = [
    ExactPrefLabelMatcher(),
    ExactRdfsLabelMatcher(),
    ExactAltLabelMatcher(),
    ExactHiddenLabelMatcher(),
    ExactLocalNameMatcher(),
    SemanticSimilarityMatcher(),
    LexicalMatcher()
]

for matcher in matchers:
    result = matcher.match(col_analysis, properties, context)
    if result:
        print(f"\n✅ {matcher.name()}:")
        print(f"   Property: {result.property.uri}")
        print(f"   Confidence: {result.confidence}")
        print(f"   Matched via: {result.matched_via}")
    else:
        print(f"\n❌ {matcher.name()}: No match")

print("\n" + "="*80)

