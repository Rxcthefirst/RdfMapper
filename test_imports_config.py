#!/usr/bin/env python3

# Test script for imports functionality
import tempfile
from pathlib import Path
from src.rdfmap.config.loader import load_mapping_config

# Create a simple test
with tempfile.TemporaryDirectory() as temp_dir:
    temp_path = Path(temp_dir)

    # Create test CSV
    csv_path = temp_path / "test.csv"
    csv_path.write_text("employee_id,name\nE001,John Smith\nE002,Jane Doe")

    # Create mapping config with imports
    config_path = temp_path / "test_mapping.yaml"
    config_yaml = f"""
namespaces:
  hr: http://example.org/hr#
  shared: http://example.org/shared#
  xsd: http://www.w3.org/2001/XMLSchema#

imports:
  - examples/imports_demo/shared_ontology_fixed.ttl

defaults:
  base_iri: http://example.org/

sheets:
  - name: test_sheet
    source: {csv_path}
    row_resource:
      class: hr:Employee
      iri_template: employee:{{employee_id}}
    columns:
      employee_id:
        as: hr:hasEmployeeID
        datatype: xsd:string

options:
  on_error: report
"""

    config_path.write_text(config_yaml)

    # Test loading
    try:
        config = load_mapping_config(config_path)
        print("✓ Configuration loaded successfully!")
        print(f"  Imports: {config.imports}")
        print(f"  Sheets: {len(config.sheets)}")

        # Test accessing the source
        sheet = config.sheets[0]
        print(f"  Sheet source: {sheet.source}")
        print(f"  Source exists: {Path(sheet.source).exists()}")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
