#!/usr/bin/env python3
"""Test if DataTypeInferenceMatcher fires."""

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

# Get employee class
employee_class = None
for cls_uri, cls in gen.ontology.classes.items():
    if 'Employee' in str(cls_uri):
        employee_class = cls
        break

properties = gen.ontology.get_datatype_properties(employee_class.uri)

# Test DataTypeInferenceMatcher directly
from rdfmap.generator.matchers.datatype_matcher import DataTypeInferenceMatcher

matcher = DataTypeInferenceMatcher(enabled=True, threshold=0.0)

test_columns = ["Age", "salary", "Birth Date", "ContactEmail"]

print("="*80)
print("DATATYPE INFERENCE MATCHER TEST")
print("="*80)
print()

for col_name in test_columns:
    try:
        col_analysis = gen.data_source.get_analysis(col_name)
        result = matcher.match(col_analysis, properties, None)

        if result:
            print(f"✅ {col_name}:")
            print(f"   → {str(result.property.uri).split('#')[-1]}")
            print(f"   Confidence: {result.confidence:.3f}")
            print(f"   Matched via: {result.matched_via}")
            print(f"   Column type: {col_analysis.inferred_type}")
            print(f"   Property range: {result.property.range_type}")
        else:
            print(f"❌ {col_name}: No match")
            print(f"   Column type: {col_analysis.inferred_type}")
        print()
    except Exception as e:
        print(f"❌ {col_name}: Error - {e}")
        print()

print("="*80)
print("Checking why it might not appear in evidence...")
print("="*80)

# Check if the matcher is in the pipeline
print(f"\nMatchers in pipeline: {len(gen.matcher_pipeline.matchers)}")
datatype_in_pipeline = any(m.name() == "DataTypeInferenceMatcher" for m in gen.matcher_pipeline.matchers)
print(f"DataTypeInferenceMatcher in pipeline: {datatype_in_pipeline}")

if datatype_in_pipeline:
    dt_matcher = [m for m in gen.matcher_pipeline.matchers if m.name() == "DataTypeInferenceMatcher"][0]
    print(f"  Enabled: {dt_matcher.enabled}")
    print(f"  Threshold: {dt_matcher.threshold}")

