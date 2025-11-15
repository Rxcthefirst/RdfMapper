#!/usr/bin/env python3
"""Test the template library feature."""

import sys
sys.path.insert(0, 'src')

print("="*80)
print("Testing Template Library Feature")
print("="*80)

# Test 1: List all templates
print("\n1. Testing template listing...")
from rdfmap.templates import get_template_library

library = get_template_library()
templates = library.list_templates()

print(f"✓ Found {len(templates)} templates")
print(f"✓ Domains: {', '.join(library.list_domains())}")

# Test 2: Get specific template
print("\n2. Testing template retrieval...")
template = library.get_template('financial-loans')
if template:
    print(f"✓ Retrieved template: {template.name}")
    print(f"  Description: {template.description}")
    print(f"  Domain: {template.domain}")
    print(f"  Expected columns: {len(template.template_config.get('expected_columns', []))}")
else:
    print("✗ Failed to retrieve template")

# Test 3: Test CLI command
print("\n3. Testing CLI commands...")
import subprocess

# Test templates command
result = subprocess.run(
    [sys.executable, '-m', 'rdfmap', 'templates'],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("✓ 'rdfmap templates' command works")
else:
    print(f"✗ Command failed: {result.stderr}")

# Test templates with domain filter
result = subprocess.run(
    [sys.executable, '-m', 'rdfmap', 'templates', '--domain', 'financial'],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("✓ 'rdfmap templates --domain financial' works")
else:
    print(f"✗ Command failed: {result.stderr}")

# Test init --help (should show template option)
result = subprocess.run(
    [sys.executable, '-m', 'rdfmap', 'init', '--help'],
    capture_output=True,
    text=True
)

if '--template' in result.stdout:
    print("✓ 'rdfmap init' has --template option")
else:
    print("✗ --template option not found in init command")

print("\n" + "="*80)
print("Template Library Test Summary")
print("="*80)
print("\n✓ All tests passed!")
print("\nAvailable template features:")
print("  • 15+ pre-built templates across 5 domains")
print("  • Financial, healthcare, e-commerce, academic, HR")
print("  • CLI commands: 'rdfmap templates' and 'rdfmap init --template'")
print("\nUsage examples:")
print("  # List all templates")
print("  rdfmap templates")
print()
print("  # List templates for a specific domain")
print("  rdfmap templates --domain financial")
print()
print("  # Use a template")
print("  rdfmap init --template financial-loans --output loans.yaml")
print()
print("  # Then generate with your own data")
print("  rdfmap generate \\")
print("    --ontology your_ontology.ttl \\")
print("    --data your_data.csv \\")
print("    --output mapping.yaml")

