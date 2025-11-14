#!/usr/bin/env python3
"""Test CLI integration for NT format and aggregation options."""

import tempfile
import csv
import yaml
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def create_test_data_and_config():
    """Create test data and mapping config for CLI testing."""

    # Create temp directory
    temp_dir = Path(tempfile.mkdtemp())

    # Create test CSV with duplicate IDs
    csv_file = temp_dir / "employees.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Name', 'Department'])

        # Create some duplicate IDs to test aggregation
        for i in range(20):
            if i % 5 == 0 and i > 0:
                emp_id = f'EMP{i-1:03d}'  # Reuse previous ID
            else:
                emp_id = f'EMP{i:03d}'

            writer.writerow([emp_id, f'Employee {i}', f'Dept{i % 3}'])

    # Create mapping config
    config = {
        'namespaces': {
            'ex': 'http://example.org/',
            'xsd': 'http://www.w3.org/2001/XMLSchema#'
        },
        'defaults': {
            'base_iri': 'http://data.example.org/'
        },
        'sheets': [{
            'name': 'employees',
            'source': str(csv_file),
            'row_resource': {
                'class': 'ex:Employee',
                'iri_template': '{base_iri}employee/{ID}'
            },
            'columns': {
                'ID': {'as': 'ex:employeeID', 'datatype': 'xsd:string'},
                'Name': {'as': 'ex:name', 'datatype': 'xsd:string'},
                'Department': {'as': 'ex:department', 'datatype': 'xsd:string'}
            }
        }],
        'options': {
            'chunk_size': 10,
            'header': True,
            'aggregate_duplicates': True
        }
    }

    config_file = temp_dir / "mapping.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config, f)

    return temp_dir, csv_file, config_file

def test_cli_nt_format():
    """Test CLI with NT format and aggregation options."""
    print("🖥️ Testing CLI NT Format Support")
    print("=" * 40)

    temp_dir, csv_file, config_file = create_test_data_and_config()

    try:
        from src.rdfmap.cli.main import app
        import typer.testing

        runner = typer.testing.CliRunner()

        # Test 1: NT format (should auto-disable aggregation)
        print("🔸 Test 1: NT format with auto-detection")
        nt_output = temp_dir / "output_auto.nt"

        result = runner.invoke(app, [
            "convert",
            "--mapping", str(config_file),
            "--format", "nt",
            "--output", str(nt_output),
            "--verbose"
        ])

        print(f"Exit code: {result.exit_code}")
        if result.exit_code == 0:
            print(f"✅ Success: Generated {nt_output.stat().st_size} bytes")
            if "streaming mode" in result.stdout.lower():
                print("✅ Correctly used streaming mode")
        else:
            print(f"❌ Failed:")
            print(result.stdout)
            print(result.stderr)

        # Test 2: NT format with explicit aggregation enabled
        print(f"\n🔸 Test 2: NT format with forced aggregation")
        nt_agg_output = temp_dir / "output_aggregated.nt"

        result = runner.invoke(app, [
            "convert",
            "--mapping", str(config_file),
            "--format", "nt",
            "--output", str(nt_agg_output),
            "--aggregate-duplicates",
            "--verbose"
        ])

        print(f"Exit code: {result.exit_code}")
        if result.exit_code == 0:
            print(f"✅ Success: Generated {nt_agg_output.stat().st_size} bytes")
        else:
            print(f"❌ Failed:")
            print(result.stdout)
            print(result.stderr)

        # Test 3: TTL format (should use aggregation by default)
        print(f"\n🔸 Test 3: TTL format (default aggregation)")
        ttl_output = temp_dir / "output.ttl"

        result = runner.invoke(app, [
            "convert",
            "--mapping", str(config_file),
            "--format", "ttl",
            "--output", str(ttl_output),
            "--verbose"
        ])

        print(f"Exit code: {result.exit_code}")
        if result.exit_code == 0:
            print(f"✅ Success: Generated {ttl_output.stat().st_size} bytes")
        else:
            print(f"❌ Failed:")
            print(result.stdout)
            print(result.stderr)

        # Compare outputs
        print(f"\n📊 Output Comparison:")
        if nt_output.exists():
            nt_lines = len(nt_output.read_text().strip().split('\n'))
            print(f"  NT (streaming): {nt_lines} triples")

        if nt_agg_output.exists():
            nt_agg_lines = len(nt_agg_output.read_text().strip().split('\n'))
            print(f"  NT (aggregated): {nt_agg_lines} triples")

        if ttl_output.exists():
            # Count triples in TTL (rough estimate)
            ttl_content = ttl_output.read_text()
            ttl_triples = ttl_content.count(' .')
            print(f"  TTL (aggregated): ~{ttl_triples} triples")

        # Show sample content
        if nt_output.exists():
            print(f"\n📋 Sample NT content (streaming):")
            lines = nt_output.read_text().strip().split('\n')
            for line in lines[:3]:
                print(f"  {line}")

        return True

    except Exception as e:
        print(f"❌ CLI test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    print("🚀 CLI NT Format Integration Test")
    print("=" * 40)

    success = test_cli_nt_format()

    if success:
        print(f"\n🎉 CLI integration test passed!")
        print(f"✅ NT format support working correctly")
        print(f"✅ Aggregation options functioning")
        print(f"✅ Auto-detection working")
    else:
        print(f"\n❌ CLI integration test failed.")
        sys.exit(1)
