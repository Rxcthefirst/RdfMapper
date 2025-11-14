"""Intelligent processing mode selection for optimal performance."""

import os
import psutil
from pathlib import Path
from typing import Dict, Literal, Tuple

ProcessingMode = Literal["regular", "streaming"]


def get_system_resources() -> Dict[str, float]:
    """Get current system resource availability."""
    try:
        memory = psutil.virtual_memory()
        return {
            "total_ram_gb": memory.total / (1024**3),
            "available_ram_gb": memory.available / (1024**3),
            "cpu_cores": psutil.cpu_count(),
        }
    except Exception:
        # Fallback defaults if psutil fails
        return {
            "total_ram_gb": 8.0,  # Conservative default
            "available_ram_gb": 4.0,
            "cpu_cores": 4,
        }


def estimate_file_size_mb(file_path: Path) -> float:
    """Estimate file size in MB."""
    try:
        return file_path.stat().st_size / (1024 * 1024)
    except Exception:
        return 0.0


def choose_processing_mode(
    file_path: Path,
    force_mode: ProcessingMode = None,
    available_ram_gb: float = None,
) -> Tuple[ProcessingMode, Dict[str, any]]:
    """Intelligently choose processing mode based on file size and system resources.

    Args:
        file_path: Path to the data file
        force_mode: Force a specific mode (overrides intelligent selection)
        available_ram_gb: Override detected available RAM

    Returns:
        Tuple of (processing_mode, decision_info)
    """
    if force_mode:
        return force_mode, {"reason": f"Forced to {force_mode} mode"}

    # Get system resources
    resources = get_system_resources()
    if available_ram_gb:
        resources["available_ram_gb"] = available_ram_gb

    # Get file info
    file_size_mb = estimate_file_size_mb(file_path)

    decision_info = {
        "file_size_mb": file_size_mb,
        "available_ram_gb": resources["available_ram_gb"],
        "cpu_cores": resources["cpu_cores"],
    }

    # Decision logic
    if file_size_mb < 1:
        # Very small files: regular mode (< 1MB)
        mode = "regular"
        decision_info["reason"] = "File too small for streaming overhead"

    elif file_size_mb < 10:
        # Small files: regular mode (1-10MB)
        mode = "regular"
        decision_info["reason"] = "Small file, regular mode sufficient"

    elif file_size_mb > resources["available_ram_gb"] * 1024 * 0.25:
        # Large files: streaming mode (> 25% of available RAM)
        mode = "streaming"
        decision_info["reason"] = "File size approaching memory limits"

    elif file_size_mb > 100:
        # Medium-large files: streaming mode (> 100MB)
        mode = "streaming"
        decision_info["reason"] = "File size benefits from streaming"

    elif file_size_mb > 50:
        # Medium files: streaming mode if RAM is limited
        if resources["available_ram_gb"] < 8:
            mode = "streaming"
            decision_info["reason"] = "Limited RAM available for medium file"
        else:
            mode = "regular"
            decision_info["reason"] = "Sufficient RAM for regular processing"
    else:
        # Small-medium files: regular mode
        mode = "regular"
        decision_info["reason"] = "File size suitable for regular processing"

    return mode, decision_info


def get_optimal_chunk_size(
    file_size_mb: float,
    available_ram_gb: float,
    processing_mode: ProcessingMode
) -> int:
    """Calculate optimal chunk size based on file size and available memory.

    Args:
        file_size_mb: File size in MB
        available_ram_gb: Available RAM in GB
        processing_mode: Selected processing mode

    Returns:
        Optimal chunk size in rows
    """
    if processing_mode == "regular":
        # For regular mode, chunk size less critical
        return min(50000, max(1000, int(file_size_mb * 100)))

    # For streaming mode, calculate based on memory
    available_ram_mb = available_ram_gb * 1024

    # Target using ~10% of available RAM for processing
    target_memory_mb = available_ram_mb * 0.1

    # Estimate rows per MB (rough approximation)
    # Assumes average of ~1KB per row (varies widely by data)
    estimated_rows_per_mb = 1000

    # Calculate chunk size to fit in target memory
    chunk_size = int(target_memory_mb * estimated_rows_per_mb)

    # Apply bounds
    chunk_size = max(1000, min(100000, chunk_size))

    return chunk_size


def print_processing_recommendation(
    file_path: Path,
    mode: ProcessingMode,
    decision_info: Dict[str, any],
    chunk_size: int = None
) -> None:
    """Print a user-friendly explanation of the processing recommendation."""
    print(f"📊 Processing Mode Recommendation for {file_path.name}")
    print(f"   File size: {decision_info['file_size_mb']:.1f} MB")
    print(f"   Available RAM: {decision_info['available_ram_gb']:.1f} GB")
    print(f"   CPU cores: {decision_info['cpu_cores']}")
    print()

    if mode == "streaming":
        print(f"🌊 Recommended: STREAMING MODE")
        print(f"   Reason: {decision_info['reason']}")
        if chunk_size:
            print(f"   Chunk size: {chunk_size:,} rows")
        print(f"   Benefits: Constant memory usage, better for large datasets")
    else:
        print(f"⚡ Recommended: REGULAR MODE")
        print(f"   Reason: {decision_info['reason']}")
        if chunk_size:
            print(f"   Chunk size: {chunk_size:,} rows")
        print(f"   Benefits: Simpler processing, faster for small datasets")


# Example usage
if __name__ == "__main__":
    # Test with different file sizes
    test_cases = [
        ("small.csv", 0.5),    # 500KB
        ("medium.csv", 25),    # 25MB
        ("large.csv", 500),    # 500MB
        ("huge.csv", 2000),    # 2GB
    ]

    print("🎯 Processing Mode Selection Examples")
    print("=" * 45)

    for filename, size_mb in test_cases:
        # Calculate decision based on file size directly
        resources = get_system_resources()

        decision_info = {
            "file_size_mb": size_mb,
            "available_ram_gb": resources["available_ram_gb"],
            "cpu_cores": resources["cpu_cores"],
        }

        # Apply decision logic directly
        if size_mb < 1:
            mode = "regular"
            decision_info["reason"] = "File too small for streaming overhead"
        elif size_mb < 10:
            mode = "regular"
            decision_info["reason"] = "Small file, regular mode sufficient"
        elif size_mb > resources["available_ram_gb"] * 1024 * 0.25:
            mode = "streaming"
            decision_info["reason"] = "File size approaching memory limits"
        elif size_mb > 100:
            mode = "streaming"
            decision_info["reason"] = "File size benefits from streaming"
        elif size_mb > 50:
            if resources["available_ram_gb"] < 8:
                mode = "streaming"
                decision_info["reason"] = "Limited RAM available for medium file"
            else:
                mode = "regular"
                decision_info["reason"] = "Sufficient RAM for regular processing"
        else:
            mode = "regular"
            decision_info["reason"] = "File size suitable for regular processing"

        chunk_size = get_optimal_chunk_size(size_mb, resources["available_ram_gb"], mode)

        print(f"\n📁 {filename} ({size_mb}MB)")
        if mode == "streaming":
            print(f"   🌊 Mode: STREAMING")
            print(f"   💡 Benefits: Constant memory, handles large files")
        else:
            print(f"   ⚡ Mode: REGULAR")
            print(f"   💡 Benefits: Simple, fast for small files")
        print(f"   📊 Chunk size: {chunk_size:,} rows")
        print(f"   🤔 Reason: {decision_info['reason']}")

    print(f"\n💻 System Resources:")
    print(f"   RAM: {resources['available_ram_gb']:.1f} GB available")
    print(f"   CPU: {resources['cpu_cores']} cores")

    print(f"\n📈 Decision Thresholds:")
    print(f"   < 1MB: Always regular mode")
    print(f"   1-10MB: Regular mode (small files)")
    print(f"   10-50MB: Regular mode if RAM > 8GB, else consider streaming")
    print(f"   50-100MB: Streaming mode recommended")
    print(f"   > 100MB: Always streaming mode")
    print(f"   > 25% RAM: Always streaming mode")

