#!/usr/bin/env python3
"""Fixed memory comparison test between regular and streaming parsers."""

import psutil
import os
import gc
import time
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rdfmap.parsers.data_source import create_parser
from src.rdfmap.parsers.streaming_parser import StreamingCSVParser


def get_memory_mb():
    """Get current memory usage in MB."""
    return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)


def test_memory_usage():
    """Test memory usage with fixed parsers."""
    print("🔧 Fixed Memory Usage Comparison")
    print("=" * 50)

    test_file = Path('test_data/employees_500000.csv')
    if not test_file.exists():
        print("❌ Test file not found")
        return

    file_size_mb = test_file.stat().st_size / (1024 * 1024)
    print(f"📁 File: {test_file.name} ({file_size_mb:.1f} MB)")

    # Test 1: Regular Parser (now fixed)
    print(f"\n🔧 Regular Parser (Fixed):")
    gc.collect()
    baseline = get_memory_mb()
    print(f"  Baseline: {baseline:.1f} MB")

    start_time = time.time()
    parser1 = create_parser(test_file)
    total_rows = 0
    peak_memory = baseline

    for i, chunk in enumerate(parser1.parse(chunk_size=50000)):
        total_rows += len(chunk)
        current_memory = get_memory_mb()
        peak_memory = max(peak_memory, current_memory)

        if i % 2 == 0:  # Print every other chunk to reduce output
            print(f"  Chunk {i+1}: {len(chunk):,} rows, Memory: {current_memory:.1f} MB (+{current_memory-baseline:.1f})")

    regular_time = time.time() - start_time
    final_memory = get_memory_mb()
    regular_peak = peak_memory - baseline
    regular_final = final_memory - baseline

    print(f"  Final: {total_rows:,} rows in {regular_time:.2f}s")
    print(f"  Peak memory: +{regular_peak:.1f} MB")
    print(f"  Final memory: +{regular_final:.1f} MB")

    del parser1
    gc.collect()

    # Test 2: Streaming Parser
    print(f"\n🌊 Streaming Parser:")
    baseline = get_memory_mb()
    print(f"  Baseline: {baseline:.1f} MB")

    start_time = time.time()
    parser2 = StreamingCSVParser(test_file)
    total_rows = 0
    peak_memory = baseline

    for i, batch in enumerate(parser2.stream_batches(batch_size=50000)):
        total_rows += len(batch)
        current_memory = get_memory_mb()
        peak_memory = max(peak_memory, current_memory)

        if i % 2 == 0:  # Print every other batch to reduce output
            print(f"  Batch {i+1}: {len(batch):,} rows, Memory: {current_memory:.1f} MB (+{current_memory-baseline:.1f})")

    streaming_time = time.time() - start_time
    final_memory = get_memory_mb()
    streaming_peak = peak_memory - baseline
    streaming_final = final_memory - baseline

    print(f"  Final: {total_rows:,} rows in {streaming_time:.2f}s")
    print(f"  Peak memory: +{streaming_peak:.1f} MB")
    print(f"  Final memory: +{streaming_final:.1f} MB")

    # Comparison
    print(f"\n📊 Comparison:")
    print(f"  Speed: {regular_time/streaming_time:.2f}x {'streaming faster' if streaming_time < regular_time else 'regular faster'}")
    print(f"  Peak memory: {regular_peak:.1f} MB vs {streaming_peak:.1f} MB")
    print(f"  Memory savings: {(regular_peak - streaming_peak)/regular_peak*100:.1f}% with streaming")
    print(f"  Throughput: Regular {total_rows/regular_time:,.0f} rows/s, Streaming {total_rows/streaming_time:,.0f} rows/s")

    if streaming_peak < regular_peak:
        print(f"  ✅ Streaming uses {regular_peak - streaming_peak:.1f} MB less memory!")
    else:
        print(f"  ❌ Streaming uses {streaming_peak - regular_peak:.1f} MB more memory")


if __name__ == "__main__":
    test_memory_usage()
