#!/usr/bin/env python3
"""Proper memory usage test to accurately measure streaming vs regular mode memory consumption."""

import time
import psutil
import os
import gc
from pathlib import Path
import sys
sys.path.insert(0, '.')

from src.rdfmap.parsers.data_source import create_parser
from src.rdfmap.parsers.streaming_parser import StreamingCSVParser


def get_memory_usage():
    """Get current memory usage in MB."""
    return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)


def memory_usage_test():
    """Accurate memory usage comparison test."""
    print("🧠 Memory Usage Analysis: Streaming vs Regular Mode")
    print("=" * 60)

    test_data_path = Path("test_data")

    # Test with multiple sizes to see the pattern
    test_sizes = [100_000, 500_000, 1_000_000]

    for size in test_sizes:
        emp_file = test_data_path / f'employees_{size}.csv'
        if not emp_file.exists():
            continue

        file_size_mb = emp_file.stat().st_size / (1024 * 1024)
        print(f"\n📊 Testing {size:,} records ({file_size_mb:.1f} MB file)")
        print("-" * 50)

        # Test 1: Regular mode memory usage
        print("  🔧 Testing Regular Mode...")

        # Force garbage collection and get baseline
        gc.collect()
        baseline_memory = get_memory_usage()

        start_time = time.time()
        parser1 = create_parser(emp_file)
        total_rows = 0
        peak_memory = baseline_memory

        for chunk in parser1.parse(chunk_size=50000):
            total_rows += len(chunk)
            current_memory = get_memory_usage()
            peak_memory = max(peak_memory, current_memory)

        regular_time = time.time() - start_time
        final_memory = get_memory_usage()
        regular_peak_usage = peak_memory - baseline_memory
        regular_final_usage = final_memory - baseline_memory

        print(f"    ⏱️  Time: {regular_time:.3f}s")
        print(f"    📈 Peak memory: {regular_peak_usage:.1f} MB")
        print(f"    📊 Final memory: {regular_final_usage:.1f} MB")
        print(f"    🚀 Rate: {total_rows/regular_time:,.0f} rows/s")

        # Clear memory between tests
        del parser1
        gc.collect()

        # Test 2: Streaming mode memory usage
        print("  🌊 Testing Streaming Mode...")

        # Get new baseline after cleanup
        baseline_memory = get_memory_usage()

        start_time = time.time()
        parser2 = StreamingCSVParser(emp_file)
        total_rows = 0
        peak_memory = baseline_memory

        for batch in parser2.stream_batches(batch_size=50000):
            total_rows += len(batch)
            current_memory = get_memory_usage()
            peak_memory = max(peak_memory, current_memory)

        streaming_time = time.time() - start_time
        final_memory = get_memory_usage()
        streaming_peak_usage = peak_memory - baseline_memory
        streaming_final_usage = final_memory - baseline_memory

        print(f"    ⏱️  Time: {streaming_time:.3f}s")
        print(f"    📈 Peak memory: {streaming_peak_usage:.1f} MB")
        print(f"    📊 Final memory: {streaming_final_usage:.1f} MB")
        print(f"    🚀 Rate: {total_rows/streaming_time:,.0f} rows/s")

        # Comparison
        peak_savings = ((regular_peak_usage - streaming_peak_usage) / regular_peak_usage * 100) if regular_peak_usage > 0 else 0
        final_savings = ((regular_final_usage - streaming_final_usage) / regular_final_usage * 100) if regular_final_usage > 0 else 0
        speedup = regular_time / streaming_time if streaming_time > 0 else 0

        print(f"\n  📊 Comparison:")
        print(f"    ⚡ Speed: {speedup:.2f}x {'faster' if speedup > 1 else 'slower'}")
        print(f"    🧠 Peak memory savings: {peak_savings:.1f}%")
        print(f"    💾 Final memory savings: {final_savings:.1f}%")
        print(f"    📉 Streaming peak vs regular: {streaming_peak_usage:.1f}MB vs {regular_peak_usage:.1f}MB")

        # Clear memory for next test
        del parser2
        gc.collect()

    print(f"\n💡 Memory Analysis Insights:")
    print(f"  • Peak memory = highest memory usage during processing")
    print(f"  • Final memory = memory after processing completes")
    print(f"  • Streaming should use less peak memory for large datasets")
    print(f"  • Regular mode loads larger chunks into memory at once")


def detailed_memory_test():
    """Detailed memory test with step-by-step monitoring."""
    print(f"\n🔬 Detailed Memory Monitoring (500K records)")
    print("=" * 50)

    test_data_path = Path("test_data")
    emp_file = test_data_path / f'employees_500000.csv'

    if not emp_file.exists():
        print("❌ 500K dataset not found")
        return

    print(f"📁 File: {emp_file.name} ({emp_file.stat().st_size / (1024*1024):.1f} MB)")

    # Test regular mode with detailed monitoring
    print(f"\n🔧 Regular Mode - Detailed Memory Tracking:")
    gc.collect()
    baseline = get_memory_usage()
    print(f"  Baseline: {baseline:.1f} MB")

    parser = create_parser(emp_file)
    chunk_num = 0
    total_rows = 0

    for chunk in parser.parse(chunk_size=100000):
        chunk_num += 1
        total_rows += len(chunk)
        memory = get_memory_usage()
        print(f"  Chunk {chunk_num}: {len(chunk):,} rows, Memory: {memory:.1f} MB (+{memory-baseline:.1f})")

    final_memory = get_memory_usage()
    print(f"  Final: {total_rows:,} total rows, Memory: {final_memory:.1f} MB (+{final_memory-baseline:.1f})")

    del parser
    gc.collect()

    # Test streaming mode with detailed monitoring
    print(f"\n🌊 Streaming Mode - Detailed Memory Tracking:")
    baseline = get_memory_usage()
    print(f"  Baseline: {baseline:.1f} MB")

    parser = StreamingCSVParser(emp_file)
    batch_num = 0
    total_rows = 0

    for batch in parser.stream_batches(batch_size=100000):
        batch_num += 1
        total_rows += len(batch)
        memory = get_memory_usage()
        print(f"  Batch {batch_num}: {len(batch):,} rows, Memory: {memory:.1f} MB (+{memory-baseline:.1f})")

    final_memory = get_memory_usage()
    print(f"  Final: {total_rows:,} total rows, Memory: {final_memory:.1f} MB (+{final_memory-baseline:.1f})")


if __name__ == "__main__":
    memory_usage_test()
    detailed_memory_test()
