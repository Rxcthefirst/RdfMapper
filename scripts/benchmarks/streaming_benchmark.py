#!/usr/bin/env python3
"""Enhanced streaming performance benchmark demonstrating Polars streaming capabilities."""

import time
import tempfile
import csv
import psutil
import os
from pathlib import Path
from typing import List, Tuple
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.rdfmap.parsers.data_source import create_parser
from src.rdfmap.parsers.streaming_parser import StreamingCSVParser
from src.rdfmap.emitter.graph_builder import RDFGraphBuilder
from src.rdfmap.emitter.streaming_graph_builder import StreamingRDFGraphBuilder
from src.rdfmap.models.errors import ProcessingReport
from src.rdfmap.models.mapping import MappingConfig


def create_large_test_data(num_rows: int) -> Path:
    """Create large test CSV data for streaming benchmarks."""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)

    # Write header
    writer = csv.writer(temp_file)
    writer.writerow([
        'ID', 'Name', 'Email', 'Age', 'Salary', 'Department',
        'HireDate', 'IsActive', 'Notes', 'ManagerID', 'Region'
    ])

    # Write data rows
    for i in range(num_rows):
        writer.writerow([
            f'EMP{i:08d}',
            f'Employee {i}',
            f'emp{i}@company.com',
            25 + (i % 40),  # Age 25-65
            50000 + (i % 100000),  # Salary 50k-150k
            f'Department{i % 15}',
            f'2020-{1 + (i % 12):02d}-{1 + (i % 28):02d}',
            'true' if i % 2 == 0 else 'false',
            f'Notes for employee {i} with some longer text content',
            f'MGR{(i // 50):06d}' if i > 50 else '',
            f'Region{i % 5}'
        ])

    temp_file.close()
    return Path(temp_file.name)


def create_streaming_test_mapping() -> MappingConfig:
    """Create test mapping configuration for streaming tests."""
    from src.rdfmap.models.mapping import (
        MappingConfig, SheetMapping, RowResource, ColumnMapping,
        DefaultsConfig, ProcessingOptions
    )

    config = MappingConfig(
        namespaces={
            'ex': 'http://example.org/',
            'xsd': 'http://www.w3.org/2001/XMLSchema#'
        },
        defaults=DefaultsConfig(base_iri='http://data.example.org/'),
        sheets=[
            SheetMapping(
                name='employees',
                source='test_data.csv',
                row_resource=RowResource(
                    **{'class': 'ex:Employee'},
                    iri_template='{base_iri}employee/{ID}'
                ),
                columns={
                    'ID': ColumnMapping(**{'as': 'ex:employeeID', 'datatype': 'xsd:string'}),
                    'Name': ColumnMapping(**{'as': 'ex:name', 'datatype': 'xsd:string'}),
                    'Email': ColumnMapping(**{'as': 'ex:email', 'datatype': 'xsd:string'}),
                    'Age': ColumnMapping(**{'as': 'ex:age', 'datatype': 'xsd:integer'}),
                    'Salary': ColumnMapping(**{'as': 'ex:salary', 'datatype': 'xsd:decimal'}),
                    'Department': ColumnMapping(**{'as': 'ex:department', 'datatype': 'xsd:string', 'transform': 'lowercase'}),
                    'HireDate': ColumnMapping(**{'as': 'ex:hireDate', 'datatype': 'xsd:date'}),
                    'IsActive': ColumnMapping(**{'as': 'ex:isActive', 'datatype': 'xsd:boolean'}),
                    'Notes': ColumnMapping(**{'as': 'ex:notes', 'datatype': 'xsd:string', 'transform': 'trim'}),
                    'ManagerID': ColumnMapping(**{'as': 'ex:managerID', 'datatype': 'xsd:string'}),
                    'Region': ColumnMapping(**{'as': 'ex:region', 'datatype': 'xsd:string', 'transform': 'uppercase'}),
                }
            )
        ],
        options=ProcessingOptions(
            chunk_size=20000,
            header=True,
            delimiter=',',
            on_error='report'
        )
    )

    return config


def benchmark_regular_vs_streaming(file_path: Path, config: MappingConfig, num_rows: int) -> dict:
    """Benchmark regular vs streaming processing."""
    results = {}

    # Update config with actual file path
    config.sheets[0].source = str(file_path)

    print(f"  📊 Benchmarking {num_rows:,} rows...")

    # Benchmark 1: Regular processing
    print("    Testing regular processing...")
    start_time = time.time()
    start_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024

    report1 = ProcessingReport()
    builder1 = RDFGraphBuilder(config, report1)

    parser1 = create_parser(file_path)
    for chunk in parser1.parse(chunk_size=config.options.chunk_size):
        builder1.add_dataframe(chunk, config.sheets[0])

    graph1 = builder1.get_graph()
    regular_time = time.time() - start_time
    regular_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    regular_triples = len(graph1)

    results['regular'] = {
        'time': regular_time,
        'memory_mb': regular_memory - start_memory,
        'triples': regular_triples,
        'rate': num_rows / regular_time
    }

    # Clear memory
    del graph1, builder1, report1

    # Benchmark 2: Streaming processing
    print("    Testing streaming processing...")
    start_time = time.time()
    start_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024

    report2 = ProcessingReport()
    builder2 = StreamingRDFGraphBuilder(config, report2)

    # Use streaming with real-time progress
    total_streaming_triples = 0
    for batch_triples in builder2.stream_to_rdf(
        file_path,
        config.sheets[0],
        chunk_size=config.options.chunk_size,
        enable_streaming_transforms=True
    ):
        total_streaming_triples += batch_triples

    graph2 = builder2.get_graph()
    streaming_time = time.time() - start_time
    streaming_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    streaming_triples = len(graph2)

    results['streaming'] = {
        'time': streaming_time,
        'memory_mb': streaming_memory - start_memory,
        'triples': streaming_triples,
        'rate': num_rows / streaming_time,
        'stats': builder2.get_streaming_stats()
    }

    return results


def format_time(seconds: float) -> str:
    """Format time in human-readable format."""
    if seconds < 1:
        return f"{seconds*1000:.1f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        return f"{seconds/60:.1f}m"


def main():
    """Run streaming performance benchmarks."""
    print("🚀 Polars Streaming vs Regular Processing Benchmark")
    print("=" * 60)

    try:
        import polars as pl
        print(f"Polars version: {pl.__version__}")
        print(f"System: {psutil.cpu_count()} CPU cores, {psutil.virtual_memory().total // (1024**3)} GB RAM")
    except ImportError:
        print("❌ Polars not installed. Please install: pip install polars")
        return

    print()

    # Test with different sizes
    test_sizes = [10_000, 25_000]  # Moderate sizes for comparison
    config = create_streaming_test_mapping()

    all_results = []

    for num_rows in test_sizes:
        print(f"🔄 Testing with {num_rows:,} rows")
        print("-" * 35)

        # Create test data
        print("  Creating test data...")
        file_path = create_large_test_data(num_rows)

        try:
            # Run benchmark
            results = benchmark_regular_vs_streaming(file_path, config, num_rows)
            all_results.append({
                'rows': num_rows,
                **results
            })

            # Show results
            reg = results['regular']
            stream = results['streaming']

            print(f"  📈 Results:")
            print(f"    Regular:   {format_time(reg['time'])} | {reg['memory_mb']:.1f} MB | {reg['rate']:,.0f} rows/s")
            print(f"    Streaming: {format_time(stream['time'])} | {stream['memory_mb']:.1f} MB | {stream['rate']:,.0f} rows/s")

            time_improvement = reg['time'] / stream['time']
            memory_improvement = reg['memory_mb'] / stream['memory_mb'] if stream['memory_mb'] > 0 else float('inf')

            print(f"    Improvement: {time_improvement:.1f}x faster, {memory_improvement:.1f}x less memory")
            print(f"    Triples: {stream['triples']:,} ({stream['triples'] // stream['time']:,.0f} triples/sec)")
            print()

        finally:
            file_path.unlink()

    # Summary
    print("📋 STREAMING PERFORMANCE SUMMARY")
    print("=" * 45)
    print(f"{'Rows':<10} {'Regular':<12} {'Streaming':<12} {'Speedup':<10} {'Memory'}")
    print("-" * 60)

    for result in all_results:
        reg_time = format_time(result['regular']['time'])
        stream_time = format_time(result['streaming']['time'])
        speedup = f"{result['regular']['time'] / result['streaming']['time']:.1f}x"
        memory_ratio = f"{result['regular']['memory_mb'] / result['streaming']['memory_mb']:.1f}x" if result['streaming']['memory_mb'] > 0 else "∞x"

        print(f"{result['rows']:,:<10} {reg_time:<12} {stream_time:<12} {speedup:<10} {memory_ratio}")

    print()
    print("🎯 Polars Streaming Benefits:")
    print("  • Native streaming engine with lazy evaluation")
    print("  • Vectorized transformations applied in-stream")
    print("  • Constant memory usage regardless of file size")
    print("  • Zero-copy operations where possible")
    print("  • Automatic query optimization")
    print("  • Parallel processing for complex operations")
    print("  • Real-time progress tracking")

    print()
    print("💡 Recommendation:")
    print("  Use streaming mode for datasets > 50K rows")
    print("  Enable streaming transforms for better performance")
    print("  Adjust chunk_size based on available memory")


if __name__ == "__main__":
    main()
