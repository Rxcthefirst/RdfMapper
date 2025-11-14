#!/usr/bin/env python3
"""Demonstrate the difference between subject-grouped (aggregated) and column-wise (streaming) triple output."""

import tempfile
import csv
import yaml
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rdfmap.cli.main import app
import typer.testing


def create_test_data():
    """Create simple test data to demonstrate triple ordering."""
    temp_dir = Path(tempfile.mkdtemp())
    csv_file = temp_dir / "employees.csv"

    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(['EmployeeID', 'Name', 'Department', 'Salary'])

        # Write 5 employees
        for i in range(5):
            writer.writerow([
                f'EMP{i+1:03d}',
                f'Employee {i+1}',
                f'Dept{(i % 3) + 1}',
                f'{50000 + i * 5000}'
            ])

    return temp_dir, csv_file


def create_mapping_config(csv_file: Path) -> Path:
    """Create mapping configuration."""
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
                'Name': {'as': 'ex:name', 'datatype': 'xsd:string'},
                'Department': {'as': 'ex:department', 'datatype': 'xsd:string'},
                'Salary': {'as': 'ex:salary', 'datatype': 'xsd:decimal'}
            }
        }],
        'options': {
            'chunk_size': 10,
            'header': True,
            'aggregate_duplicates': True
        }
    }

    config_file = csv_file.parent / 'mapping.yaml'
    with open(config_file, 'w') as f:
        yaml.dump(config, f)

    return config_file


def analyze_triple_ordering(nt_file: Path, mode_name: str):
    """Analyze how triples are ordered in the NT file."""
    print(f"\n📋 {mode_name} Triple Ordering Analysis:")
    print("-" * 50)

    if not nt_file.exists():
        print("❌ File not found")
        return

    subjects = []
    subject_groups = {}

    with open(nt_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            # Extract subject (everything up to first space)
            parts = line.split(' ', 1)
            if len(parts) >= 1:
                subject = parts[0]
                subjects.append(subject)

                if subject not in subject_groups:
                    subject_groups[subject] = []
                subject_groups[subject].append(line_num)

    print(f"  Total triples: {len(subjects)}")
    print(f"  Unique subjects: {len(subject_groups)}")

    # Analyze grouping
    grouped_subjects = 0
    scattered_subjects = 0

    for subject, line_nums in subject_groups.items():
        if len(line_nums) > 1:
            # Check if all line numbers are consecutive
            is_grouped = all(line_nums[i] + 1 == line_nums[i+1] for i in range(len(line_nums)-1))
            if is_grouped:
                grouped_subjects += 1
            else:
                scattered_subjects += 1
                print(f"  Scattered: {subject} appears on lines {line_nums}")

    print(f"  Subjects with grouped triples: {grouped_subjects}")
    print(f"  Subjects with scattered triples: {scattered_subjects}")

    # Show ordering pattern
    print(f"  📊 Triple ordering pattern (first 10 triples):")
    with open(nt_file, 'r') as f:
        for i, line in enumerate(f):
            if i >= 10:
                break
            line = line.strip()
            if line:
                subject = line.split(' ', 1)[0]
                predicate = line.split(' ')[1] if len(line.split(' ')) > 1 else ""
                # Extract predicate name for readability
                pred_name = predicate.split('#')[-1].split('/')[-1].rstrip('>')
                subj_name = subject.split('/')[-1].rstrip('>')
                print(f"    {i+1:2d}. {subj_name} -> {pred_name}")

    return len(subject_groups), grouped_subjects, scattered_subjects


def test_triple_ordering():
    """Test the difference between aggregated (grouped) and streaming (column-wise) triple ordering."""
    print("🔄 Testing Triple Ordering: Aggregated vs Streaming")
    print("=" * 60)

    # Create test data
    temp_dir, csv_file = create_test_data()
    config_file = create_mapping_config(csv_file)

    try:
        # Show the source data
        print("📊 Source Data:")
        with open(csv_file, 'r') as f:
            for i, line in enumerate(f):
                print(f"  {i}: {line.strip()}")

        runner = typer.testing.CliRunner()

        # Test 1: Aggregated mode (triples grouped by subject)
        print(f"\n🔧 Test 1: Aggregated Mode (Subject Grouping)")
        print("-" * 50)

        nt_aggregated = temp_dir / "aggregated.nt"
        result = runner.invoke(app, [
            "convert",
            "--mapping", str(config_file),
            "--format", "nt",
            "--output", str(nt_aggregated),
            "--aggregate-duplicates",
            "--verbose"
        ])

        print(f"Exit code: {result.exit_code}")
        if result.exit_code == 0:
            print("✅ Success")
        else:
            print(f"❌ Failed: {result.stdout}")

        # Test 2: Streaming mode (column-wise processing)
        print(f"\n🌊 Test 2: Streaming Mode (Column-wise Processing)")
        print("-" * 50)

        nt_streaming = temp_dir / "streaming.nt"
        result = runner.invoke(app, [
            "convert",
            "--mapping", str(config_file),
            "--format", "nt",
            "--output", str(nt_streaming),
            "--no-aggregate-duplicates",
            "--verbose"
        ])

        print(f"Exit code: {result.exit_code}")
        if result.exit_code == 0:
            print("✅ Success")
        else:
            print(f"❌ Failed: {result.stdout}")

        # Analyze the results
        print(f"\n📊 Comparative Analysis")
        print("=" * 60)

        agg_subjects, agg_grouped, agg_scattered = analyze_triple_ordering(nt_aggregated, "Aggregated")
        stream_subjects, stream_grouped, stream_scattered = analyze_triple_ordering(nt_streaming, "Streaming")

        print(f"\n💡 Expected Behavior:")
        print(f"  🔧 Aggregated mode: All triples for each subject grouped together")
        print(f"     - Better for XML/RDF nested structures")
        print(f"     - More readable output")
        print(f"     - Requires more memory (must collect all triples before writing)")
        print(f"")
        print(f"  🌊 Streaming mode: Triples written as columns are processed")
        print(f"     - Polars processes column-wise: all IDs, then all names, etc.")
        print(f"     - Lower memory usage (immediate writing)")
        print(f"     - Triples for same subject may be scattered")

        print(f"\n🎯 Results Summary:")
        print(f"  Mode              Grouped    Scattered   Memory   Readability")
        print(f"  ---------------   -------    ---------   ------   -----------")
        print(f"  Aggregated        {agg_grouped:7d}    {agg_scattered:9d}   Higher   Better")
        print(f"  Streaming         {stream_grouped:7d}    {stream_scattered:9d}   Lower    Worse")

        if agg_grouped > stream_grouped:
            print(f"\n✅ Aggregation is working correctly!")
            print(f"   Aggregated mode groups {agg_grouped}/{agg_subjects} subjects")
            print(f"   Streaming mode groups {stream_grouped}/{stream_subjects} subjects")
        else:
            print(f"\n⚠️  Both modes show similar grouping - investigation needed")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    print("🔍 Triple Ordering Analysis: Understanding Aggregation vs Streaming")
    print("=" * 70)
    print("Testing the difference between:")
    print("• Aggregated: Subject-grouped triples (all triples for a subject together)")
    print("• Streaming: Column-wise processing (triples scattered by processing order)")
    print()

    success = test_triple_ordering()

    if success:
        print(f"\n🎉 Triple ordering test completed!")
        print(f"This demonstrates the key difference between aggregation modes:")
        print(f"• Subject grouping (aggregated) vs column-wise processing (streaming)")
    else:
        print(f"\n❌ Test failed - see output above for details")
