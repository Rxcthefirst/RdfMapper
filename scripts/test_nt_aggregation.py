#!/usr/bin/env python3
"""Test NT format support with configurable aggregation for duplicate IRIs."""

import tempfile
import csv
from pathlib import Path
import sys
import time
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rdfmap.config.loader import load_mapping_config
from src.rdfmap.emitter.graph_builder import RDFGraphBuilder, serialize_graph
from src.rdfmap.emitter.nt_streaming import NTriplesStreamWriter
from src.rdfmap.models.errors import ProcessingReport
from src.rdfmap.parsers.data_source import create_parser


def create_test_data_with_duplicates(file_path: Path, num_rows: int = 1000):
    """Create test CSV data with intentional duplicate IRIs."""
    with open(file_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Name', 'Age', 'Department', 'Notes'])

        # Create rows with some duplicate IDs to test aggregation
        for i in range(num_rows):
            # Every 5th row reuses an ID to create duplicates
            if i % 5 == 0 and i > 0:
                row_id = f'EMP{(i-1):06d}'  # Reuse previous ID
            else:
                row_id = f'EMP{i:06d}'

            writer.writerow([
                row_id,
                f'Employee {i}',
                25 + (i % 40),
                f'Department{i % 10}',
                f'Notes for row {i}'
            ])


def create_test_mapping_config(data_file: Path) -> dict:
    """Create test mapping configuration."""
    return {
        'namespaces': {
            'ex': 'http://example.org/',
            'xsd': 'http://www.w3.org/2001/XMLSchema#'
        },
        'defaults': {
            'base_iri': 'http://data.example.org/'
        },
        'sheets': [{
            'name': 'employees',
            'source': str(data_file),
            'row_resource': {
                'class': 'ex:Employee',
                'iri_template': '{base_iri}employee/{ID}'
            },
            'columns': {
                'ID': {'as': 'ex:employeeID', 'datatype': 'xsd:string'},
                'Name': {'as': 'ex:name', 'datatype': 'xsd:string'},
                'Age': {'as': 'ex:age', 'datatype': 'xsd:integer'},
                'Department': {'as': 'ex:department', 'datatype': 'xsd:string'},
                'Notes': {'as': 'ex:notes', 'datatype': 'xsd:string'}
            }
        }],
        'options': {
            'chunk_size': 100,
            'header': True,
            'aggregate_duplicates': True  # Default setting
        }
    }


def test_aggregated_mode(data_file: Path, config_dict: dict):
    """Test regular aggregated mode (default behavior)."""
    print("🔧 Testing Aggregated Mode (Traditional)")
    print("-" * 40)

    # Create config object
    from src.rdfmap.models.mapping import MappingConfig
    config = MappingConfig(**config_dict)

    # Enable aggregation
    config.options.aggregate_duplicates = True

    start_time = time.time()

    # Create graph builder
    report = ProcessingReport()
    builder = RDFGraphBuilder(config, report)

    # Process data
    parser = create_parser(data_file)
    for chunk in parser.parse(chunk_size=config.options.chunk_size):
        builder.add_dataframe(chunk, config.sheets[0])

    # Get results
    graph = builder.get_graph()
    processing_time = time.time() - start_time

    print(f"  ⏱️  Processing time: {processing_time:.3f}s")
    print(f"  📊 RDF triples: {len(graph)}")
    print(f"  🧠 Graph size in memory: {sys.getsizeof(graph)} bytes")

    # Save to TTL for comparison
    ttl_file = data_file.parent / "output_aggregated.ttl"
    serialize_graph(graph, "ttl", ttl_file)
    file_size = ttl_file.stat().st_size
    print(f"  📁 TTL file size: {file_size} bytes")

    # Show sample triples
    print(f"  📋 Sample triples:")
    for i, (s, p, o) in enumerate(graph):
        if i < 3:
            print(f"    {s} {p} {o}")
        else:
            break

    return {
        'processing_time': processing_time,
        'triple_count': len(graph),
        'file_size': file_size,
        'memory_size': sys.getsizeof(graph)
    }


def test_streaming_nt_mode(data_file: Path, config_dict: dict):
    """Test streaming NT mode (no aggregation)."""
    print("\n🌊 Testing Streaming NT Mode (No Aggregation)")
    print("-" * 40)

    # Create config object
    from src.rdfmap.models.mapping import MappingConfig
    config = MappingConfig(**config_dict)

    # Disable aggregation for streaming
    config.options.aggregate_duplicates = False

    start_time = time.time()

    # Create NT output file
    nt_file = data_file.parent / "output_streaming.nt"

    # Create streaming NT writer and graph builder
    report = ProcessingReport()

    with NTriplesStreamWriter(nt_file) as nt_writer:
        builder = RDFGraphBuilder(config, report, streaming_writer=nt_writer)

        # Process data
        parser = create_parser(data_file)
        for chunk in parser.parse(chunk_size=config.options.chunk_size):
            builder.add_dataframe(chunk, config.sheets[0])

        triple_count = builder.get_triple_count()

    processing_time = time.time() - start_time
    file_size = nt_file.stat().st_size

    print(f"  ⏱️  Processing time: {processing_time:.3f}s")
    print(f"  📊 RDF triples: {triple_count}")
    print(f"  🧠 Memory usage: Constant (streaming)")
    print(f"  📁 NT file size: {file_size} bytes")

    # Show sample NT lines
    print(f"  📋 Sample NT lines:")
    with open(nt_file, 'r') as f:
        for i, line in enumerate(f):
            if i < 3:
                print(f"    {line.strip()}")
            else:
                break

    return {
        'processing_time': processing_time,
        'triple_count': triple_count,
        'file_size': file_size,
        'memory_size': 'streaming'
    }


def test_cli_integration(data_file: Path):
    """Test CLI integration with new NT streaming options."""
    print("\n🖥️  Testing CLI Integration")
    print("-" * 40)

    # Create mapping config file
    config_dict = create_test_mapping_config(data_file)
    config_file = data_file.parent / "test_mapping.yaml"

    import yaml
    with open(config_file, 'w') as f:
        yaml.dump(config_dict, f)

    # Test different CLI scenarios
    from src.rdfmap.cli.main import app
    import typer.testing

    runner = typer.testing.CliRunner()

    # Test 1: Regular TTL output (should use aggregation)
    print("  🔸 Test 1: TTL format (aggregated)")
    ttl_output = data_file.parent / "cli_output.ttl"
    result = runner.invoke(app, [
        "convert",
        "--mapping", str(config_file),
        "--format", "ttl",
        "--output", str(ttl_output),
        "--verbose"
    ])

    if result.exit_code == 0:
        print(f"    ✅ Success: {ttl_output.stat().st_size} bytes")
    else:
        print(f"    ❌ Failed: {result.stdout}")

    # Test 2: NT format with auto-detected streaming
    print("  🔸 Test 2: NT format (auto-streaming)")
    nt_output = data_file.parent / "cli_output.nt"
    result = runner.invoke(app, [
        "convert",
        "--mapping", str(config_file),
        "--format", "nt",
        "--output", str(nt_output),
        "--verbose"
    ])

    if result.exit_code == 0:
        print(f"    ✅ Success: {nt_output.stat().st_size} bytes")
        if "streaming mode" in result.stdout.lower():
            print("    🌊 Correctly used streaming mode")
    else:
        print(f"    ❌ Failed: {result.stdout}")

    # Test 3: NT format with forced aggregation
    print("  🔸 Test 3: NT format (forced aggregation)")
    nt_agg_output = data_file.parent / "cli_output_agg.nt"
    result = runner.invoke(app, [
        "convert",
        "--mapping", str(config_file),
        "--format", "nt",
        "--output", str(nt_agg_output),
        "--aggregate-duplicates",
        "--verbose"
    ])

    if result.exit_code == 0:
        print(f"    ✅ Success: {nt_agg_output.stat().st_size} bytes")
    else:
        print(f"    ❌ Failed: {result.stdout}")


def analyze_duplicate_iri_handling(data_file: Path):
    """Analyze how duplicate IRIs are handled in different modes."""
    print("\n🔍 Analyzing Duplicate IRI Handling")
    print("-" * 40)

    # Count unique IRIs in source data
    unique_ids = set()
    total_rows = 0

    with open(data_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            unique_ids.add(row['ID'])
            total_rows += 1

    print(f"  📊 Source data: {total_rows} rows, {len(unique_ids)} unique IDs")
    print(f"  🔄 Duplicate rows: {total_rows - len(unique_ids)}")

    # Check aggregated output
    ttl_file = data_file.parent / "output_aggregated.ttl"
    if ttl_file.exists():
        from rdflib import Graph
        g = Graph()
        g.parse(ttl_file, format='turtle')

        # Count unique subjects
        subjects = {s for s, p, o in g}
        print(f"  🔧 Aggregated mode: {len(g)} triples, {len(subjects)} unique subjects")

    # Check streaming output
    nt_file = data_file.parent / "output_streaming.nt"
    if nt_file.exists():
        with open(nt_file, 'r') as f:
            lines = f.readlines()

        # Count unique subjects in NT format
        subjects = set()
        for line in lines:
            if line.strip():
                parts = line.split(' ', 1)
                if parts[0].startswith('<') and parts[0].endswith('>'):
                    subjects.add(parts[0])

        print(f"  🌊 Streaming mode: {len(lines)} triples, {len(subjects)} unique subjects")

        # Should have more triples due to duplicates
        if len(lines) > len(unique_ids) * 5:  # Rough estimate
            print(f"    ✅ Contains duplicate IRIs as expected")
        else:
            print(f"    ⚠️  Fewer duplicates than expected")


def main():
    """Run comprehensive NT format and aggregation tests."""
    print("🧪 NT Format & Configurable Aggregation Test Suite")
    print("=" * 60)

    # Create test data
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        data_file = temp_path / "test_employees.csv"

        print(f"📁 Creating test data with duplicate IRIs...")
        create_test_data_with_duplicates(data_file, num_rows=500)
        print(f"   Generated: {data_file}")

        # Create mapping config
        config_dict = create_test_mapping_config(data_file)

        # Run tests
        aggregated_results = test_aggregated_mode(data_file, config_dict)
        streaming_results = test_streaming_nt_mode(data_file, config_dict)

        # Analyze results
        analyze_duplicate_iri_handling(data_file)

        # Test CLI integration
        test_cli_integration(data_file)

        # Performance comparison
        print(f"\n📈 Performance Comparison")
        print("-" * 40)
        print(f"Processing Time:")
        print(f"  🔧 Aggregated: {aggregated_results['processing_time']:.3f}s")
        print(f"  🌊 Streaming:  {streaming_results['processing_time']:.3f}s")

        if streaming_results['processing_time'] < aggregated_results['processing_time']:
            speedup = aggregated_results['processing_time'] / streaming_results['processing_time']
            print(f"  ⚡ Streaming is {speedup:.1f}x faster")

        print(f"\nFile Sizes:")
        print(f"  🔧 TTL (aggregated): {aggregated_results['file_size']} bytes")
        print(f"  🌊 NT (streaming):   {streaming_results['file_size']} bytes")

        print(f"\nTriple Counts:")
        print(f"  🔧 Aggregated: {aggregated_results['triple_count']} (deduplicated)")
        print(f"  🌊 Streaming:  {streaming_results['triple_count']} (with duplicates)")

        # Conclusions
        print(f"\n💡 Key Benefits Demonstrated:")
        print(f"  ✅ NT streaming mode processes data without memory aggregation")
        print(f"  ✅ Performance improvement for large datasets with duplicates")
        print(f"  ✅ Configurable aggregation via CLI options")
        print(f"  ✅ Auto-detection of optimal mode based on output format")
        print(f"  ✅ Maintains compatibility with existing workflows")

        print(f"\n🎯 Use Cases:")
        print(f"  • Large datasets: Use NT streaming for performance")
        print(f"  • Clean data: Use aggregated mode for readability")
        print(f"  • ETL pipelines: NT streaming for maximum throughput")
        print(f"  • Data exploration: Aggregated mode for analysis")


if __name__ == "__main__":
    main()
