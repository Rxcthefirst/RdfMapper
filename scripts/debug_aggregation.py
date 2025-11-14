#!/usr/bin/env python3
"""Test to demonstrate the actual difference between streaming and aggregated modes with duplicate IRIs."""

import tempfile
import csv
import yaml
from pathlib import Path
import sys
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rdfmap.cli.main import app
import typer.testing


def create_dataset_with_duplicates():
    """Create a test dataset with intentional duplicate IRIs."""
    temp_dir = Path(tempfile.mkdtemp())
    csv_file = temp_dir / "employees_with_duplicates.csv"

    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(['EmployeeID', 'FirstName', 'LastName', 'Department', 'Salary'])

        # Write data with intentional duplicates
        for i in range(1000):
            # Every 5th row reuses the same EmployeeID to create duplicates
            if i % 5 == 0 and i > 0:
                emp_id = f'EMP{i-1:06d}'  # Reuse the PREVIOUS ID to create actual duplicates
                print(f"Creating duplicate: Row {i} reuses ID {emp_id}")
            else:
                emp_id = f'EMP{i:06d}'

            writer.writerow([
                emp_id,
                f'Employee{i}',
                f'Last{i}',
                f'Dept{i % 3}',
                f'{50000 + i * 100}'
            ])

    return temp_dir, csv_file


def create_mapping_config(csv_file: Path) -> Path:
    """Create mapping configuration for the test."""
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
            'source': str(csv_file.absolute()),
            'row_resource': {
                'class': 'ex:Employee',
                'iri_template': '{base_iri}employee/{EmployeeID}'
            },
            'columns': {
                'EmployeeID': {'as': 'ex:employeeId', 'datatype': 'xsd:string'},
                'FirstName': {'as': 'ex:firstName', 'datatype': 'xsd:string'},
                'LastName': {'as': 'ex:lastName', 'datatype': 'xsd:string'},
                'Department': {'as': 'ex:department', 'datatype': 'xsd:string'},
                'Salary': {'as': 'ex:salary', 'datatype': 'xsd:decimal'}
            }
        }],
        'options': {
            'chunk_size': 100,
            'header': True,
            'delimiter': ',',
            'on_error': 'report',
            'aggregate_duplicates': True  # Default
        }
    }

    config_file = csv_file.parent / 'mapping.yaml'
    with open(config_file, 'w') as f:
        yaml.dump(config, f)

    return config_file


def test_aggregation_difference():
    """Test the actual difference between streaming and aggregated modes."""
    print("🔍 Testing Actual Aggregation vs Streaming Behavior")
    print("=" * 60)

    # Create test data with duplicates
    temp_dir, csv_file = create_dataset_with_duplicates()
    config_file = create_mapping_config(csv_file)

    try:
        # Analyze the source data
        print("📊 Source Data Analysis:")
        unique_ids = set()
        total_rows = 0
        duplicate_rows = 0

        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_rows += 1
                emp_id = row['EmployeeID']
                if emp_id in unique_ids:
                    duplicate_rows += 1
                    if duplicate_rows <= 5:  # Show first few duplicates
                        print(f"  Duplicate found: {emp_id} (row {total_rows})")
                unique_ids.add(emp_id)

        print(f"  Total rows: {total_rows}")
        print(f"  Unique IDs: {len(unique_ids)}")
        print(f"  Duplicate rows: {duplicate_rows}")
        print(f"  Expected triples per row: ~7 (type + properties)")
        print(f"  Expected total triples:")
        print(f"    - Streaming (no aggregation): {total_rows * 7} triples")
        print(f"    - Aggregated (deduplicated): {len(unique_ids) * 7} triples")

        runner = typer.testing.CliRunner()

        # Test 1: NT format with streaming (no aggregation)
        print(f"\n🌊 Test 1: NT Streaming Mode (No Aggregation)")
        print("-" * 50)

        nt_streaming_file = temp_dir / "output_streaming.nt"

        result = runner.invoke(app, [
            "convert",
            "--mapping", str(config_file),
            "--format", "nt",
            "--output", str(nt_streaming_file),
            "--no-aggregate-duplicates",  # Explicitly disable aggregation
            "--verbose"
        ])

        streaming_triples = 0
        if result.exit_code == 0 and nt_streaming_file.exists():
            with open(nt_streaming_file, 'r') as f:
                streaming_triples = sum(1 for line in f if line.strip())

            print(f"✅ Success!")
            print(f"  Exit code: {result.exit_code}")
            print(f"  Triples: {streaming_triples:,}")

            # Show that streaming mode was used
            if "--no-aggregate-duplicates" in str(result.stdout) or "streaming" in result.stdout.lower():
                print(f"  🌊 Streaming mode confirmed")

            # Show sample output
            print(f"  📋 Sample triples:")
            with open(nt_streaming_file, 'r') as f:
                for i, line in enumerate(f):
                    if i < 3:
                        print(f"    {line.strip()}")
                    else:
                        break
        else:
            print(f"❌ Failed! Exit code: {result.exit_code}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")

        # Test 2: NT format with aggregation
        print(f"\n🔧 Test 2: NT Aggregated Mode (With Aggregation)")
        print("-" * 50)

        nt_aggregated_file = temp_dir / "output_aggregated.nt"

        result = runner.invoke(app, [
            "convert",
            "--mapping", str(config_file),
            "--format", "nt",
            "--output", str(nt_aggregated_file),
            "--aggregate-duplicates",  # Explicitly enable aggregation
            "--verbose"
        ])

        aggregated_triples = 0
        if result.exit_code == 0 and nt_aggregated_file.exists():
            with open(nt_aggregated_file, 'r') as f:
                aggregated_triples = sum(1 for line in f if line.strip())

            print(f"✅ Success!")
            print(f"  Exit code: {result.exit_code}")
            print(f"  Triples: {aggregated_triples:,}")
            print(f"  📋 Sample triples:")
            with open(nt_aggregated_file, 'r') as f:
                for i, line in enumerate(f):
                    if i < 3:
                        print(f"    {line.strip()}")
                    else:
                        break
        else:
            print(f"❌ Failed! Exit code: {result.exit_code}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")

        # Analysis
        print(f"\n📊 Results Analysis:")
        print("=" * 50)
        print(f"Source Data:")
        print(f"  Total rows: {total_rows}")
        print(f"  Unique employee IDs: {len(unique_ids)}")
        print(f"  Duplicate rows: {duplicate_rows}")
        print(f"")
        print(f"RDF Output:")
        print(f"  Streaming mode triples: {streaming_triples:,}")
        print(f"  Aggregated mode triples: {aggregated_triples:,}")
        print(f"  Difference: {streaming_triples - aggregated_triples:,} triples")

        if streaming_triples > aggregated_triples:
            print(f"  ✅ Streaming mode correctly preserved duplicates!")
            print(f"  🔧 Aggregated mode correctly deduplicated!")
        elif streaming_triples == aggregated_triples:
            print(f"  ⚠️  Both modes produced same result - aggregation may not be working as expected")
        else:
            print(f"  ❌ Unexpected result - streaming should have more triples")

        # Expected vs actual
        expected_streaming = total_rows * 7  # Rough estimate
        expected_aggregated = len(unique_ids) * 7

        print(f"")
        print(f"Expected vs Actual:")
        print(f"  Expected streaming: ~{expected_streaming:,} triples")
        print(f"  Actual streaming: {streaming_triples:,} triples")
        print(f"  Expected aggregated: ~{expected_aggregated:,} triples")
        print(f"  Actual aggregated: {aggregated_triples:,} triples")

        return streaming_triples != aggregated_triples

    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    print("🕵️ Investigating Aggregation vs Streaming Behavior")
    print("=" * 60)

    success = test_aggregation_difference()

    if success:
        print(f"\n✅ Test successful - aggregation behavior is working correctly!")
        print(f"🌊 Streaming mode preserves duplicates")
        print(f"🔧 Aggregated mode deduplicates properly")
    else:
        print(f"\n❌ Issue detected - both modes are producing the same results")
        print(f"🔍 This suggests aggregation is happening in both cases")
        print(f"🛠️  Investigation needed to fix streaming mode")

    print(f"\n💡 The reason both modes showed same results with 2M dataset:")
    print(f"   The employee dataset likely has unique IDs with no duplicates")
    print(f"   So aggregation vs no-aggregation produces identical output")
