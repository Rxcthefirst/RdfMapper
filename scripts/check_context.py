import json

with open('../examples/demo/output/context_test_alignment_report.json') as f:
    data = json.load(f)

print('Report includes ontology context:', 'ontology_context' in data)
if 'ontology_context' in data:
    ctx = data['ontology_context']
    print(f'Target class: {ctx["target_class"]["label"]} ({ctx["target_class"]["local_name"]})')
    print(f'Target class properties: {len(ctx["target_class"]["properties"])}')
    print(f'Related classes: {len(ctx["related_classes"])}')
    print(f'All properties: {len(ctx["all_properties"])}')
    print(f'Object properties: {len(ctx["object_properties"])}')

    print('\nFirst 5 target class properties:')
    for prop in ctx['target_class']['properties'][:5]:
        print(f'  - {prop["local_name"]} ({prop["label"]})')

    print('\nFirst unmapped column:')
    unmapped = data['unmapped_columns'][0]
    print(f'Column: {unmapped["column_name"]}')
    print(f'Has ontology context: {"ontology_context" in unmapped}')

# Show a sample of the SKOS suggestions with more conservative approach
print(f'\nSKOS suggestions: {len(data["skos_enrichment_suggestions"])}')
for i, sugg in enumerate(data['skos_enrichment_suggestions'][:3], 1):
    print(f'{i}. {sugg["suggested_label_value"]} -> {sugg["property_label"]} ({sugg["suggested_label_type"]})')
