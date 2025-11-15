#!/usr/bin/env python3

from src.rdfmap.generator.ontology_analyzer import OntologyAnalyzer

try:
    print("Testing core ontology loading...")
    analyzer = OntologyAnalyzer('examples/imports_demo/core_ontology.ttl')
    print(f'Classes found: {len(analyzer.classes)}')
    for uri, cls in analyzer.classes.items():
        print(f'  - {cls.label}: {uri}')
    print(f'Properties found: {len(analyzer.properties)}')
    for uri, prop in analyzer.properties.items():
        print(f'  - {prop.label}: {uri}')

    print("\nTesting with imports...")
    analyzer_with_imports = OntologyAnalyzer(
        'examples/imports_demo/core_ontology.ttl',
        imports=['examples/imports_demo/shared_ontology.ttl']
    )
    print(f'Classes found (with imports): {len(analyzer_with_imports.classes)}')
    for uri, cls in analyzer_with_imports.classes.items():
        print(f'  - {cls.label}: {uri}')
    print(f'Properties found (with imports): {len(analyzer_with_imports.properties)}')
    for uri, prop in analyzer_with_imports.properties.items():
        print(f'  - {prop.label}: {uri}')

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
