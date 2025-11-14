#!/usr/bin/env python3
"""Generate large-scale realistic datasets and show file information."""

from pathlib import Path
import sys
sys.path.insert(0, '.')

from generate_realistic_data import RealisticDataGenerator


def generate_large_datasets():
    """Generate the large datasets and show file information."""
    print("🏭 Generating Large-Scale Realistic Test Datasets")
    print("=" * 55)

    generator = RealisticDataGenerator()
    test_data_path = Path("test_data")

    # Generate datasets of different sizes including very large ones
    sizes = [10_000, 100_000, 500_000, 1_000_000, 2_000_000]

    print("📊 Dataset generation plan:")
    estimated_sizes = []
    for size in sizes:
        # Rough estimate: ~250 bytes per employee record
        estimated_mb = (size * 250) / (1024 * 1024)
        estimated_sizes.append(estimated_mb)
        print(f"  {size:,} employees -> ~{estimated_mb:.1f} MB")

    total_estimated = sum(estimated_sizes)
    print(f"\nTotal estimated storage: ~{total_estimated:.1f} MB")

    # Ask for confirmation for large datasets
    if any(size >= 1_000_000 for size in sizes):
        print(f"\n⚠️  Large datasets will be generated (1M+ rows)")
        print(f"   This may take several minutes and use significant disk space.")
        response = input("Continue? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("Cancelled.")
            return

    print(f"\n🚀 Starting generation...")
    files = generator.generate_test_datasets(test_data_path, sizes)

    print(f"\n📁 Generated Files Summary:")
    print("=" * 60)
    print(f"{'Dataset':<12} {'Size':<12} {'File Size':<12} {'Records':<12}")
    print("-" * 60)

    total_disk_usage = 0
    for dataset_type, file_list in files.items():
        for file_path in file_list:
            if file_path.exists():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                total_disk_usage += size_mb

                # Extract row count from filename
                size_str = file_path.stem.split('_')[-1]

                print(f"{dataset_type:<12} {size_str:<12} {size_mb:.1f} MB{'':<6} {size_str:>12}")

    print("-" * 60)
    print(f"{'TOTAL':<12} {'':<12} {total_disk_usage:.1f} MB{'':<6} {'Multiple':<12}")

    print(f"\n✅ All datasets generated successfully!")
    print(f"📍 Location: {test_data_path.absolute()}")
    print(f"💾 Total disk usage: {total_disk_usage:.1f} MB")

    print(f"\n🔍 File Details:")
    for dataset_type, file_list in files.items():
        print(f"  {dataset_type.title()} Files:")
        for file_path in file_list:
            if file_path.exists():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                print(f"    📄 {file_path.name:<25} {size_mb:>8.1f} MB")

    print(f"\n🚀 Ready to run: python realistic_streaming_test.py")
    print(f"   This will test streaming performance on all generated datasets.")


if __name__ == "__main__":
    generate_large_datasets()
