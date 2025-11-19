#!/usr/bin/env python3
"""Test YARRRML parsing"""

from rdfmap.config.loader import load_mapping_config

print("Testing YARRRML parser...")
try:
    config = load_mapping_config('test_yarrrml.yaml')
    print(f'✅ Loaded {len(config.sheets)} sheets')
    print(f'✅ Base IRI: {config.defaults.base_iri}')
    print(f'✅ Namespaces: {list(config.namespaces.keys())}')
    print(f'✅ First sheet name: {config.sheets[0].name}')
    print(f'✅ Columns: {list(config.sheets[0].columns.keys())}')
    print(f'✅ Source: {config.sheets[0].source}')
    print("\n✅ YARRRML parsing successful!")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

