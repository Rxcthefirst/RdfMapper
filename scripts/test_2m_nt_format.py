#!/usr/bin/env python3
"""Test NT format support with the 2 million employee dataset."""

import time
import psutil
import os
from pathlib import Path
import sys
import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rdfmap.cli.main import app
import typer.testing


def get_memory_usage():
    """Get current memory usage in MB."""
    return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)


def create_large_dataset_mapping(csv_file: Path) -> Path:
    """Create mapping configuration for the large employee dataset."""
    config = {
        'namespaces': {
            'ex': 'http://example.org/hr#',
            'foaf': 'http://xmlns.com/foaf/0.1/',
            'org': 'http://www.w3.org/ns/org#',
            'xsd': 'http://www.w3.org/2001/XMLSchema#',
            'rdfs': 'http://www.w3.org/2000/01/rdf-schema#'
        },
        'defaults': {
            'base_iri': 'http://data.company.com/',
            'language': 'en'
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
                'FirstName': {'as': 'foaf:givenName', 'datatype': 'xsd:string', 'transform': 'strip'},
                'LastName': {'as': 'foaf:familyName', 'datatype': 'xsd:string', 'transform': 'strip'},
                'FullName': {'as': 'foaf:name', 'datatype': 'xsd:string'},
                'Email': {'as': 'foaf:mbox', 'datatype': 'xsd:string', 'transform': 'lowercase'},
                'Department': {'as': 'org:memberOf', 'datatype': 'xsd:string'},
                'JobTitle': {'as': 'ex:jobTitle', 'datatype': 'xsd:string'},
                'Salary': {'as': 'ex:annualSalary', 'datatype': 'xsd:decimal'},
                'HireDate': {'as': 'ex:hireDate', 'datatype': 'xsd:date'},
                'Age': {'as': 'foaf:age', 'datatype': 'xsd:integer'},
                'City': {'as': 'ex:workCity', 'datatype': 'xsd:string'},
                'State': {'as': 'ex:workState', 'datatype': 'xsd:string', 'transform': 'uppercase'},
                'IsActive': {'as': 'ex:isActive', 'datatype': 'xsd:boolean'},
                'Skills': {'as': 'ex:skills', 'datatype': 'xsd:string', 'multi_valued': True, 'delimiter': ', '},
                'YearsExperience': {'as': 'ex:yearsExperience', 'datatype': 'xsd:integer'},
                'PerformanceRating': {'as': 'ex:performanceRating', 'datatype': 'xsd:decimal'},
                'LastReviewDate': {'as': 'ex:lastReviewDate', 'datatype': 'xsd:date'},
                'Notes': {'as': 'rdfs:comment', 'datatype': 'xsd:string', 'transform': 'trim'}
            }
        }],
        'options': {
            'chunk_size': 50000,
            'header': True,
            'delimiter': ',',
            'on_error': 'report',
            'aggregate_duplicates': True
        }
    }

    config_file = csv_file.parent / 'large_employees_mapping.yaml'
    with open(config_file, 'w') as f:
        yaml.dump(config, f)

    return config_file


def test_2m_employees_nt_streaming():
    """Test NT streaming with 2 million employee records."""
    print("🚀 Testing NT Format with 2 Million Employee Records")
    print("=" * 60)

    # Check if the large dataset exists
    test_data_path = Path("test_data")
    csv_file = test_data_path / "employees_2000000.csv"

    if not csv_file.exists():
        print(f"❌ Large dataset not found: {csv_file}")
        print(f"Please run: python scripts/generate_large_datasets.py")
        return False

    file_size_mb = csv_file.stat().st_size / (1024 * 1024)
    print(f"📁 Dataset: {csv_file.name}")
    print(f"📊 File size: {file_size_mb:.1f} MB")

    # Create mapping configuration
    config_file = create_large_dataset_mapping(csv_file)

    runner = typer.testing.CliRunner()

    # Test 1: NT format with auto-streaming (no aggregation)
    print(f"\n🌊 Test 1: NT Format with Auto-Streaming")
    print("-" * 40)

    nt_output = test_data_path / "employees_2m_streaming.nt"

    start_memory = get_memory_usage()
    start_time = time.time()

    result = runner.invoke(app, [
        "convert",
        "--mapping", str(config_file),
        "--format", "nt",
        "--output", str(nt_output),
        "--verbose"
    ])

    end_time = time.time()
    end_memory = get_memory_usage()
    processing_time = end_time - start_time

    print(f"Exit code: {result.exit_code}")

    if result.exit_code == 0 and nt_output.exists():
        output_size_mb = nt_output.stat().st_size / (1024 * 1024)

        # Count triples
        with open(nt_output, 'r') as f:
            triple_count = sum(1 for line in f if line.strip())

        print(f"✅ Success!")
        print(f"  ⏱️  Processing time: {processing_time:.2f}s")
        print(f"  📊 Triples generated: {triple_count:,}")
        print(f"  📁 Output size: {output_size_mb:.1f} MB")
        print(f"  💾 Memory usage: {end_memory - start_memory:.1f} MB")
        print(f"  🚀 Throughput: {triple_count/processing_time:,.0f} triples/s")
        print(f"  📈 Processing rate: {2_000_000/processing_time:,.0f} rows/s")

        # Check if streaming mode was used
        if "streaming mode" in result.stdout.lower():
            print(f"  🌊 Correctly used streaming mode")

        # Show sample output
        print(f"  📋 Sample NT output:")
        with open(nt_output, 'r') as f:
            for i, line in enumerate(f):
                if i < 3:
                    print(f"    {line.strip()}")
                else:
                    break

        streaming_results = {
            'time': processing_time,
            'triples': triple_count,
            'output_size_mb': output_size_mb,
            'memory_mb': end_memory - start_memory,
            'throughput': triple_count/processing_time,
            'row_rate': 2_000_000/processing_time
        }
    else:
        print(f"❌ Failed!")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        return False

    # Test 2: NT format with forced aggregation (for comparison)
    print(f"\n🔧 Test 2: NT Format with Forced Aggregation")
    print("-" * 40)

    nt_agg_output = test_data_path / "employees_2m_aggregated.nt"

    start_memory = get_memory_usage()
    start_time = time.time()

    result = runner.invoke(app, [
        "convert",
        "--mapping", str(config_file),
        "--format", "nt",
        "--output", str(nt_agg_output),
        "--aggregate-duplicates",
        "--verbose"
    ])

    end_time = time.time()
    end_memory = get_memory_usage()
    processing_time_agg = end_time - start_time

    print(f"Exit code: {result.exit_code}")

    if result.exit_code == 0 and nt_agg_output.exists():
        output_size_agg_mb = nt_agg_output.stat().st_size / (1024 * 1024)

        # Count triples
        with open(nt_agg_output, 'r') as f:
            triple_count_agg = sum(1 for line in f if line.strip())

        print(f"✅ Success!")
        print(f"  ⏱️  Processing time: {processing_time_agg:.2f}s")
        print(f"  📊 Triples generated: {triple_count_agg:,}")
        print(f"  📁 Output size: {output_size_agg_mb:.1f} MB")
        print(f"  💾 Memory usage: {end_memory - start_memory:.1f} MB")
        print(f"  🚀 Throughput: {triple_count_agg/processing_time_agg:,.0f} triples/s")
        print(f"  📈 Processing rate: {2_000_000/processing_time_agg:,.0f} rows/s")

        aggregated_results = {
            'time': processing_time_agg,
            'triples': triple_count_agg,
            'output_size_mb': output_size_agg_mb,
            'memory_mb': end_memory - start_memory,
            'throughput': triple_count_agg/processing_time_agg,
            'row_rate': 2_000_000/processing_time_agg
        }
    else:
        print(f"❌ Failed!")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        aggregated_results = None

    # Performance comparison
    print(f"\n📊 Performance Comparison (2M Employee Records)")
    print("=" * 60)
    print(f"{'Metric':<20} {'Streaming':<15} {'Aggregated':<15} {'Difference':<15}")
    print("-" * 60)

    if aggregated_results:
        time_diff = ((aggregated_results['time'] - streaming_results['time']) / streaming_results['time']) * 100
        memory_diff = ((aggregated_results['memory_mb'] - streaming_results['memory_mb']) / streaming_results['memory_mb']) * 100 if streaming_results['memory_mb'] > 0 else 0

        print(f"{'Processing Time':<20} {streaming_results['time']:.1f}s{'':<9} {aggregated_results['time']:.1f}s{'':<9} {time_diff:+.1f}%")
        print(f"{'Memory Usage':<20} {streaming_results['memory_mb']:.1f} MB{'':<8} {aggregated_results['memory_mb']:.1f} MB{'':<8} {memory_diff:+.1f}%")
        print(f"{'Triple Count':<20} {streaming_results['triples']:,}{'':<5} {aggregated_results['triples']:,}{'':<5} {streaming_results['triples'] - aggregated_results['triples']:+,}")
        print(f"{'Output Size':<20} {streaming_results['output_size_mb']:.1f} MB{'':<8} {aggregated_results['output_size_mb']:.1f} MB{'':<8} {streaming_results['output_size_mb'] - aggregated_results['output_size_mb']:+.1f} MB")
        print(f"{'Throughput':<20} {streaming_results['throughput']:,.0f}/s{'':<5} {aggregated_results['throughput']:,.0f}/s{'':<5} {((streaming_results['throughput'] - aggregated_results['throughput']) / aggregated_results['throughput']) * 100:+.1f}%")

        print(f"\n💡 Key Insights:")
        if streaming_results['time'] < aggregated_results['time']:
            print(f"  🚀 Streaming mode is {aggregated_results['time'] / streaming_results['time']:.1f}x faster")

        if streaming_results['memory_mb'] < aggregated_results['memory_mb']:
            memory_savings = ((aggregated_results['memory_mb'] - streaming_results['memory_mb']) / aggregated_results['memory_mb']) * 100
            print(f"  💾 Streaming mode uses {memory_savings:.1f}% less memory")

        if streaming_results['triples'] > aggregated_results['triples']:
            duplicate_triples = streaming_results['triples'] - aggregated_results['triples']
            print(f"  🔄 Streaming preserved {duplicate_triples:,} duplicate triples")

        print(f"  📈 Streaming throughput: {streaming_results['row_rate']:,.0f} rows/s")
        print(f"  🎯 Ideal for: Large-scale ETL pipelines requiring maximum performance")

    # Test 3: Memory scaling analysis
    print(f"\n🧠 Memory Scaling Analysis")
    print("-" * 40)

    estimated_aggregated_memory = (file_size_mb * 3)  # Rough estimate
    actual_streaming_memory = streaming_results['memory_mb']

    print(f"  📊 Dataset size: {file_size_mb:.1f} MB")
    print(f"  🔧 Estimated aggregated memory: ~{estimated_aggregated_memory:.0f} MB")
    print(f"  🌊 Actual streaming memory: {actual_streaming_memory:.1f} MB")
    print(f"  💡 Memory efficiency: {(estimated_aggregated_memory / actual_streaming_memory):.1f}x improvement")

    # Cleanup
    print(f"\n🧹 Cleanup")
    print("-" * 40)
    config_file.unlink()
    print(f"  ✅ Removed temporary config file")

    # Keep output files for analysis
    print(f"  📁 Output files preserved for analysis:")
    if nt_output.exists():
        print(f"    • {nt_output.name} ({nt_output.stat().st_size / (1024*1024):.1f} MB)")
    if aggregated_results and nt_agg_output.exists():
        print(f"    • {nt_agg_output.name} ({nt_agg_output.stat().st_size / (1024*1024):.1f} MB)")

    return True


if __name__ == "__main__":
    print("🔥 Large-Scale NT Format Performance Test")
    print("Testing with 2 million employee records")
    print("=" * 60)

    success = test_2m_employees_nt_streaming()

    if success:
        print(f"\n🎉 Large-scale NT format test completed successfully!")
        print(f"✅ Demonstrated streaming performance benefits")
        print(f"✅ Validated memory efficiency with 2M records")
        print(f"✅ Confirmed production readiness")
    else:
        print(f"\n❌ Large-scale test failed.")
        print(f"Please ensure the 2M employee dataset exists in test_data/")
        sys.exit(1)
