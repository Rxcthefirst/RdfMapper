#!/usr/bin/env python3
"""
Demonstration of the mapping generator feature.

This script shows how to:
1. Generate a mapping configuration from an ontology and spreadsheet
2. Export JSON Schema for validation
3. Use the JSON Schema to validate the generated mapping
"""

import json
from pathlib import Path

from rdfmap.generator import MappingGenerator, GeneratorConfig, OntologyAnalyzer, SpreadsheetAnalyzer
from rdfmap.models.mapping import MappingConfig


def main():
    print("=" * 70)
    print("MAPPING GENERATOR DEMONSTRATION")
    print("=" * 70)
    
    # File paths
    ontology_file = "../examples/mortgage/ontology/mortgage.ttl"
    spreadsheet_file = "../examples/mortgage/data/loans.csv"
    output_file = "../examples/mortgage/config/generated_mapping.yaml"
    schema_file = "../examples/mortgage/config/mapping_schema.json"
    
    print("\n📋 Step 1: Analyze Ontology")
    print("-" * 70)
    onto = OntologyAnalyzer(ontology_file)
    print(f"✓ Loaded ontology: {len(onto.classes)} classes, {len(onto.properties)} properties")
    
    print("\nClasses found:")
    for cls in list(onto.classes.values())[:5]:  # Show first 5
        print(f"  - {cls.label or cls.uri}")
    
    print("\n📊 Step 2: Analyze Spreadsheet")
    print("-" * 70)
    sheet = SpreadsheetAnalyzer(spreadsheet_file)
    print(f"✓ Analyzed spreadsheet: {len(sheet.columns)} columns")
    
    print("\nColumn analysis:")
    for col in list(sheet.columns.values())[:5]:  # Show first 5
        print(f"  - {col.name}: {col.inferred_type} (suggested: {col.suggested_datatype})")
    
    print("\nIdentifier columns:")
    for col in sheet.get_identifier_columns():
        print(f"  - {col.name}")
    
    print("\n⚙️  Step 3: Generate Mapping Configuration")
    print("-" * 70)
    
    config = GeneratorConfig(
        base_iri="http://example.org/mortgage/",
        include_comments=True,
        auto_detect_relationships=True,
    )
    
    generator = MappingGenerator(
        ontology_file,
        spreadsheet_file,
        config,
    )
    
    # Generate with auto-detected class
    mapping = generator.generate(target_class="MortgageLoan", output_path=output_file)
    print(f"✓ Generated mapping for class: MortgageLoan")
    
    # Save as YAML
    generator.save_yaml(output_file)
    print(f"✓ Saved mapping to: {output_file}")
    
    print("\n📐 Step 4: Export JSON Schema")
    print("-" * 70)
    
    # Get JSON Schema from Pydantic model
    schema = generator.get_json_schema()
    
    with open(schema_file, 'w') as f:
        json.dump(schema, f, indent=2)
    
    print(f"✓ Exported JSON Schema to: {schema_file}")
    print(f"  Title: {schema.get('title')}")
    print(f"  Properties: {len(schema.get('properties', {}))}")
    print(f"  Required fields: {schema.get('required', [])}")
    
    print("\n✅ Step 5: Validate Generated Mapping with JSON Schema")
    print("-" * 70)
    
    # Load the generated mapping
    try:
        validated_config = MappingConfig.model_validate(mapping)
        print("✓ Generated mapping is valid according to Pydantic model")
        print(f"  Namespaces: {len(validated_config.namespaces)}")
        print(f"  Sheets: {len(validated_config.sheets)}")
        print(f"  Columns mapped: {len(validated_config.sheets[0].columns)}")
    except Exception as e:
        print(f"✗ Validation failed: {e}")
    
    print("\n🎯 Step 6: Using JSON Schema for External Validation")
    print("-" * 70)
    print("\nThe JSON Schema can be used to:")
    print("  1. Validate mapping configurations in CI/CD pipelines")
    print("  2. Provide IDE autocomplete for mapping files")
    print("  3. Generate documentation")
    print("  4. Validate configurations before processing")
    
    print(f"\nExample with jsonschema library:")
    print(f"```python")
    print(f"import json")
    print(f"import jsonschema")
    print(f"")
    print(f"# Load schema")
    print(f"with open('{schema_file}') as f:")
    print(f"    schema = json.load(f)")
    print(f"")
    print(f"# Load mapping")
    print(f"with open('{output_file}') as f:")
    print(f"    mapping = yaml.safe_load(f)")
    print(f"")
    print(f"# Validate")
    print(f"jsonschema.validate(mapping, schema)")
    print(f"print('✓ Valid!')")
    print(f"```")
    
    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    
    print("\n📚 Summary:")
    print("  • Analyzed ontology and extracted classes/properties")
    print("  • Analyzed spreadsheet and inferred data types")
    print("  • Generated mapping configuration automatically")
    print("  • Exported JSON Schema from Pydantic models")
    print("  • Validated generated configuration")
    
    print("\n🚀 Next Steps:")
    print(f"  1. Review: {output_file}")
    print(f"  2. Refine manually if needed")
    print(f"  3. Run conversion:")
    print(f"     rdfmap convert --mapping {output_file} --format ttl --output output.ttl")


if __name__ == "__main__":
    main()
