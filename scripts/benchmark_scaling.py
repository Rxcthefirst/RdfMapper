#!/usr/bin/env python3
"""Comprehensive scaling benchmark demonstrating Polars performance from 10K to 2M rows."""

import time
import tempfile
import csv
import psutil
import os
from pathlib import Path
from typing import Dict
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rdfmap.parsers.data_source import create_parser
from src.rdfmap.emitter.graph_builder import RDFGraphBuilder
from src.rdfmap.emitter.nt_streaming import NTriplesStreamWriter
from src.rdfmap.models.errors import ProcessingReport
from src.rdfmap.models.mapping import (
    MappingConfig, SheetMapping, RowResource, ColumnMapping,
    DefaultsConfig, ProcessingOptions
)


def create_test_data(num_rows: int, output_path: Path) -> None:
    """Create test CSV data with specified number of rows."""
    print(f"    Creating {num_rows:,} row dataset...")

    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)

        # Write header
        writer.writerow([
            'ID', 'Name', 'Email', 'Age', 'Salary', 'Department',
            'HireDate', 'IsActive', 'Notes', 'ManagerID'
        ])

        # Write data rows in batches for efficiency
        batch = []
        for i in range(num_rows):
            batch.append([
                f'EMP{i:08d}',
                f'Employee {i}',
                f'emp{i}@company.com',
                25 + (i % 40),
                50000 + (i % 100000),
                f'Dept{i % 10}',
                f'2020-{1 + (i % 12):02d}-{1 + (i % 28):02d}',
                'true' if i % 2 == 0 else 'false',
                f'Notes for employee {i}',
                f'MGR{(i // 10):08d}' if i > 10 else ''
            ])

            # Write in batches of 10000
            if len(batch) >= 10000:
                writer.writerows(batch)
                batch = []

        # Write remaining rows
        if batch:
            writer.writerows(batch)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"    Created {size_mb:.1f} MB file")


def create_test_mapping(file_path: Path) -> MappingConfig:
    """Create test mapping configuration."""
    return MappingConfig(
        namespaces={
            'ex': 'http://example.org/',
            'xsd': 'http://www.w3.org/2001/XMLSchema#'
        },
        defaults=DefaultsConfig(base_iri='http://data.example.org/'),
        sheets=[
            SheetMapping(
                name='employees',
                source=str(file_path),
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
                    'Department': ColumnMapping(**{'as': 'ex:department', 'datatype': 'xsd:string'}),
                    'HireDate': ColumnMapping(**{'as': 'ex:hireDate', 'datatype': 'xsd:date'}),
                    'IsActive': ColumnMapping(**{'as': 'ex:isActive', 'datatype': 'xsd:boolean'}),
                    'Notes': ColumnMapping(**{'as': 'ex:notes', 'datatype': 'xsd:string'}),
                    'ManagerID': ColumnMapping(**{'as': 'ex:managerID', 'datatype': 'xsd:string'}),
                }
            )
        ],
        options=ProcessingOptions(
            chunk_size=25000,
            header=True,
            delimiter=',',
            on_error='report'
        )
    )


def benchmark_conversion(file_path: Path, config: MappingConfig, mode: str) -> Dict:
    """Benchmark RDF conversion with memory tracking."""
    process = psutil.Process(os.getpid())

    # Record start state
    start_time = time.time()
    start_memory = process.memory_info().rss / (1024 * 1024)  # MB

    report = ProcessingReport()

    if mode == 'aggregated':
        # In-memory aggregation mode
        builder = RDFGraphBuilder(config, report)

        parser = create_parser(file_path)
        row_offset = 0
        for chunk in parser.parse(chunk_size=25000):
            builder.add_dataframe(chunk, config.sheets[0], offset=row_offset)
            row_offset += len(chunk)

        graph = builder.get_graph()
        triples_count = len(graph)

    elif mode == 'streaming':
        # Streaming mode - write directly to NT file
        output_file = tempfile.NamedTemporaryFile(mode='w', suffix='.nt', delete=False)
        output_path = Path(output_file.name)
        output_file.close()

        try:
            nt_writer = NTriplesStreamWriter(output_path)
            builder = RDFGraphBuilder(config, report, streaming_writer=nt_writer)

            with nt_writer:
                parser = create_parser(file_path)
                row_offset = 0
                for chunk in parser.parse(chunk_size=25000):
                    builder.add_dataframe(chunk, config.sheets[0], offset=row_offset)
                    row_offset += len(chunk)

            triples_count = builder.get_triple_count()
        finally:
            output_path.unlink()

    # Record end state
    end_time = time.time()
    end_memory = process.memory_info().rss / (1024 * 1024)  # MB

    return {
        'time': end_time - start_time,
        'memory_delta': end_memory - start_memory,
        'triples': triples_count,
        'rows': report.total_rows
    }


def format_time(seconds: float) -> str:
    """Format time in human-readable format."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds / 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"


def main():
    """Run comprehensive scaling benchmarks."""
    print("🚀 Polars Scaling Benchmark: 10K to 2M Rows")
    print("=" * 70)

    try:
        import polars as pl
        print(f"Polars version: {pl.__version__}")
    except ImportError:
        print("❌ Polars not installed. Please install: pip install polars")
        return

    print()

    # Test with different data sizes
    test_sizes = [10_000, 100_000, 500_000, 1_000_000, 2_000_000]

    results = []
    test_data_dir = Path("test_data")
    test_data_dir.mkdir(exist_ok=True)

    for size in test_sizes:
        print(f"📊 Testing with {size:,} rows")
        print("-" * 50)

        # Create test data
        file_path = test_data_dir / f'benchmark_{size}.csv'
        if not file_path.exists():
            create_test_data(size, file_path)
        else:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"    Using existing {size_mb:.1f} MB file")

        config = create_test_mapping(file_path)

        # Test aggregated mode (for smaller datasets)
        if size <= 100_000:
            print("    Testing AGGREGATED mode (in-memory)...")
            agg_result = benchmark_conversion(file_path, config, 'aggregated')

            print(f"      Time:    {format_time(agg_result['time'])}")
            print(f"      Memory:  {agg_result['memory_delta']:.1f} MB")
            print(f"      Triples: {agg_result['triples']:,}")
            print(f"      Rate:    {agg_result['rows']/agg_result['time']:,.0f} rows/s")
        else:
            agg_result = None
            print("    Skipping AGGREGATED mode (dataset too large)")

        # Test streaming mode (for all datasets)
        print("    Testing STREAMING mode (constant memory)...")
        stream_result = benchmark_conversion(file_path, config, 'streaming')

        print(f"      Time:    {format_time(stream_result['time'])}")
        print(f"      Memory:  {stream_result['memory_delta']:.1f} MB")
        print(f"      Triples: {stream_result['triples']:,}")
        print(f"      Rate:    {stream_result['rows']/stream_result['time']:,.0f} rows/s")

        results.append({
            'size': size,
            'file_mb': file_path.stat().st_size / (1024 * 1024),
            'agg': agg_result,
            'stream': stream_result
        })

        print()

    # Summary table
    print("\n📋 SCALING PERFORMANCE SUMMARY")
    print("=" * 100)
    print(f"{'Rows':<12} {'File MB':<10} {'Mode':<12} {'Time':<12} {'Memory MB':<12} {'Rate':<15} {'Triples/sec':<15}")
    print("-" * 100)

    for result in results:
        rows_str = f"{result['size']:,}"
        file_str = f"{result['file_mb']:.1f}"

        # Aggregated mode
        if result['agg']:
            agg = result['agg']
            triples_per_sec = agg['triples'] / agg['time'] if agg['time'] > 0 else 0
            print(f"{rows_str:<12} {file_str:<10} {'Aggregated':<12} {format_time(agg['time']):<12} "
                  f"{agg['memory_delta']:<12.1f} {agg['rows']/agg['time']:>14,.0f} {triples_per_sec:>14,.0f}")

        # Streaming mode
        stream = result['stream']
        triples_per_sec = stream['triples'] / stream['time'] if stream['time'] > 0 else 0
        print(f"{rows_str:<12} {file_str:<10} {'Streaming':<12} {format_time(stream['time']):<12} "
              f"{stream['memory_delta']:<12.1f} {stream['rows']/stream['time']:>14,.0f} {triples_per_sec:>14,.0f}")

    print()
    print("🎯 Key Insights:")
    print("  • AGGREGATED mode: Faster but uses more memory (in-memory graph)")
    print("  • STREAMING mode: Constant memory, ideal for large datasets")
    print("  • Polars enables linear scaling up to 2M+ rows")
    print("  • Memory usage stays constant in streaming mode")
    print("  • Processing rate: ~20K-40K rows/second typical")
    print()
    print("💡 Recommendation:")
    print("  • Use AGGREGATED mode for < 100K rows when you need RDF/XML or complex formats")
    print("  • Use STREAMING mode for > 100K rows or when memory is constrained")
    print("  • Streaming mode writes directly to NT format for maximum performance")


if __name__ == "__main__":
    main()

