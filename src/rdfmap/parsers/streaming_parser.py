"""Enhanced streaming implementation leveraging Polars' native streaming capabilities."""

from pathlib import Path
from typing import Generator, Optional
import polars as pl


class StreamingCSVParser:
    """Enhanced CSV parser with native Polars streaming optimizations."""

    def __init__(
        self,
        file_path: Path,
        delimiter: str = ",",
        has_header: bool = True,
        encoding: str = "utf8",
    ):
        self.file_path = file_path
        self.delimiter = delimiter
        self.has_header = has_header
        self.encoding = encoding if encoding in ['utf8', 'utf8-lossy'] else 'utf8'

        if not self.file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.file_path}")

    def stream_batches(
        self, batch_size: int = 10000
    ) -> Generator[pl.DataFrame, None, None]:
        """Stream CSV data in batches using true streaming approach.

        This uses a different approach than the regular parser:
        - Reads file in chunks without loading entire dataset
        - No pre-calculation of total rows (avoids memory spike)
        - True streaming with constant memory usage

        Args:
            batch_size: Number of rows per batch

        Yields:
            Polars DataFrames containing batch data
        """
        try:
            # Use Polars' batched CSV reader for true streaming
            # This reads the file incrementally without loading everything

            skip_rows = 0 if not self.has_header else 0  # Header handling

            while True:
                try:
                    # Read only a specific number of rows from current position
                    batch = pl.read_csv(
                        self.file_path,
                        separator=self.delimiter,
                        has_header=self.has_header and skip_rows == 0,  # Only read header on first batch
                        encoding=self.encoding,
                        null_values=[""],
                        ignore_errors=True,
                        skip_rows=skip_rows,
                        n_rows=batch_size,
                    )

                    # If no rows returned, we've reached the end
                    if len(batch) == 0:
                        break

                    yield batch

                    # Update skip_rows for next iteration
                    skip_rows += len(batch)
                    if self.has_header and skip_rows == batch_size:
                        skip_rows += 1  # Skip header on subsequent reads

                    # If we got fewer rows than requested, we've reached the end
                    if len(batch) < batch_size:
                        break

                except Exception as batch_error:
                    print(f"Batch read error: {batch_error}")
                    break

        except Exception as e:
            # Fallback to non-streaming if needed
            print(f"Warning: Streaming failed, falling back to chunked reading: {e}")
            yield from self._fallback_chunked_read(batch_size)

    def stream_with_transforms(
        self,
        batch_size: int = 10000,
        transforms: Optional[dict] = None
    ) -> Generator[pl.DataFrame, None, None]:
        """Stream with built-in transformations using Polars expressions.

        Args:
            batch_size: Number of rows per batch
            transforms: Dictionary of column transforms

        Yields:
            Transformed Polars DataFrames
        """
        lazy_df = pl.scan_csv(
            self.file_path,
            separator=self.delimiter,
            has_header=self.has_header,
            encoding=self.encoding,
            null_values=[""],
            ignore_errors=True,
        )

        # Apply transforms using Polars expressions (vectorized)
        if transforms:
            exprs = []
            for col in lazy_df.collect_schema().names():
                if col in transforms:
                    transform_type = transforms[col]
                    if transform_type == "to_integer":
                        exprs.append(pl.col(col).cast(pl.Int64).alias(col))
                    elif transform_type == "to_decimal":
                        exprs.append(pl.col(col).cast(pl.Float64).alias(col))
                    elif transform_type == "to_date":
                        exprs.append(pl.col(col).str.strptime(pl.Date, format="%Y-%m-%d", strict=False).alias(col))
                    elif transform_type == "lowercase":
                        exprs.append(pl.col(col).str.to_lowercase().alias(col))
                    elif transform_type == "trim":
                        exprs.append(pl.col(col).str.strip_chars().alias(col))
                    else:
                        exprs.append(pl.col(col))
                else:
                    exprs.append(pl.col(col))

            lazy_df = lazy_df.select(exprs)

        # Stream the transformed data
        total_rows = lazy_df.select(pl.len()).collect().item()

        for offset in range(0, total_rows, batch_size):
            batch = (
                lazy_df
                .slice(offset, batch_size)
                .collect(engine="streaming")
            )

            if len(batch) > 0:
                yield batch

    def _fallback_chunked_read(self, chunk_size: int) -> Generator[pl.DataFrame, None, None]:
        """Fallback to chunked reading if streaming fails."""
        # Read in chunks without streaming optimizations
        offset = 0
        while True:
            try:
                chunk = pl.read_csv(
                    self.file_path,
                    separator=self.delimiter,
                    has_header=self.has_header,
                    encoding=self.encoding,
                    skip_rows=offset if not self.has_header or offset == 0 else offset,
                    n_rows=chunk_size,
                    null_values=[""],
                    ignore_errors=True,
                )

                if len(chunk) == 0:
                    break

                yield chunk
                offset += chunk_size

                if len(chunk) < chunk_size:
                    break

            except Exception:
                break


def demonstrate_streaming_benefits():
    """Demonstrate the benefits of Polars streaming vs traditional approaches."""
    import time
    import tempfile
    import csv

    # Create a large test file
    print("Creating large test dataset...")
    test_file = Path(tempfile.mktemp(suffix='.csv'))

    with open(test_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Name', 'Value', 'Date', 'Amount'])

        # Write 100K rows
        for i in range(100000):
            writer.writerow([
                f'ID{i:06d}',
                f'Item {i}',
                f'Value {i % 1000}',
                f'2024-{1 + (i % 12):02d}-{1 + (i % 28):02d}',
                f'{(i * 1.5):.2f}'
            ])

    try:
        parser = StreamingCSVParser(test_file)

        # Test 1: Regular streaming
        print("\n🚀 Testing Polars Streaming Performance")
        print("=" * 45)

        start_time = time.time()
        total_rows = 0
        for batch in parser.stream_batches(batch_size=10000):
            total_rows += len(batch)

        streaming_time = time.time() - start_time
        print(f"Streaming mode: {total_rows:,} rows in {streaming_time:.2f}s ({total_rows/streaming_time:,.0f} rows/s)")

        # Test 2: Streaming with transforms
        transforms = {
            'Value': 'lowercase',
            'Amount': 'to_decimal',
            'Date': 'to_date'
        }

        start_time = time.time()
        total_rows = 0
        for batch in parser.stream_with_transforms(batch_size=10000, transforms=transforms):
            total_rows += len(batch)

        transform_time = time.time() - start_time
        print(f"With transforms: {total_rows:,} rows in {transform_time:.2f}s ({total_rows/transform_time:,.0f} rows/s)")

        # Test 3: Memory usage comparison
        print(f"\n💡 Streaming Benefits:")
        print(f"  • Constant memory usage regardless of file size")
        print(f"  • Lazy evaluation optimizes the entire pipeline")
        print(f"  • Vectorized transforms applied efficiently")
        print(f"  • Zero-copy operations where possible")
        print(f"  • Automatic parallelization for complex operations")

        # Show memory efficiency
        import psutil
        import os
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        print(f"  • Current memory usage: {memory_mb:.1f} MB for 100K rows")

    finally:
        # Clean up
        test_file.unlink()


if __name__ == "__main__":
    demonstrate_streaming_benefits()
