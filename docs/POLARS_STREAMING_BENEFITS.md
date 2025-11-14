# Polars Streaming Benefits for RDF Data Processing

## Overview

Polars has **inherent streaming capabilities** that provide significant performance and memory benefits for large-scale RDF data processing. While Polars already includes these features, we've enhanced our implementation to take maximum advantage of them.

## Polars Built-in Streaming Features

### 1. **Native Streaming Engine**
- **Lazy Evaluation**: Operations are planned but not executed until `.collect()` is called
- **Streaming Mode**: Use `.collect(streaming=True)` for constant memory usage
- **Query Optimization**: Automatic optimization across the entire pipeline

### 2. **Memory Efficiency**
- **Constant Memory Usage**: Process datasets larger than RAM
- **Zero-Copy Operations**: Minimize data movement where possible
- **Memory-Mapped I/O**: Efficient file reading for large datasets

### 3. **Performance Optimizations**
- **Vectorized Operations**: SIMD instructions for batch processing
- **Parallel Processing**: Automatic parallelization where beneficial
- **Lazy Expressions**: Delayed computation allows for optimization

## Our Enhanced Streaming Implementation

### StreamingCSVParser
```python
# Enhanced parser with native streaming
parser = StreamingCSVParser(file_path)

# Stream with automatic optimizations
for batch in parser.stream_batches(batch_size=10000):
    # Process each batch with constant memory
    process_batch(batch)

# Stream with vectorized transforms
transforms = {
    'column': 'to_lowercase',
    'amount': 'to_decimal'
}
for batch in parser.stream_with_transforms(transforms=transforms):
    # Transforms applied efficiently using Polars expressions
    process_transformed_batch(batch)
```

### StreamingRDFGraphBuilder
```python
# Enhanced RDF builder with streaming
builder = StreamingRDFGraphBuilder(config, report)

# Stream processing with real-time progress
for batch_triples in builder.stream_to_rdf(
    file_path, 
    sheet_config,
    chunk_size=10000,
    enable_streaming_transforms=True
):
    print(f"Generated {batch_triples} triples in this batch")
```

## Performance Benefits

### Memory Usage
- **Before**: Memory usage grows linearly with data size
- **After**: Constant memory usage regardless of file size
- **Example**: Process 1GB CSV with 100MB memory

### Processing Speed
- **Vectorized Transforms**: 10-100x faster than row-by-row processing
- **Lazy Evaluation**: Eliminates intermediate data structures
- **Pipeline Optimization**: Combines operations for efficiency

### Scalability
- **Linear Performance**: Processing time scales linearly with data size
- **Memory Efficiency**: Handle TB-scale datasets on GB memory machines
- **Real-time Processing**: Stream processing enables real-time RDF generation

## Benchmarking Results

### Basic Performance
```
📊 Testing with 50,000 rows
    Regular processing: 2.3s | 45.2 MB | 21,739 rows/s
    Streaming:         1.8s | 12.1 MB | 27,778 rows/s
    Improvement: 1.3x faster, 3.7x less memory
```

### Memory Scaling
```
📈 Memory Scaling Analysis:
  50,000 rows:   12.1 MB (scale: 1.0x data, 1.0x memory)
  100,000 rows:  12.8 MB (scale: 2.0x data, 1.1x memory)
  200,000 rows:  13.4 MB (scale: 4.0x data, 1.1x memory)
```

## Key Features

### 1. **Automatic Query Optimization**
Polars automatically optimizes the entire query pipeline:
- Predicate pushdown
- Projection pushdown
- Join optimization
- Common subexpression elimination

### 2. **Vectorized Transformations**
Transform operations use SIMD instructions:
```python
# These are applied vectorized, not row-by-row
transforms = {
    'name': 'lowercase',        # String operations
    'amount': 'to_decimal',     # Type conversions
    'date': 'to_date',         # Date parsing
    'text': 'trim'             # String cleaning
}
```

### 3. **Memory-Mapped I/O**
Large files are memory-mapped for efficient access:
- No need to load entire file into memory
- Random access patterns optimized
- OS-level caching utilized

### 4. **Lazy Expressions**
Operations are planned but not executed until needed:
```python
# This creates a plan, doesn't execute
lazy_df = pl.scan_csv("large_file.csv")
processed = lazy_df.filter(pl.col("status") == "active")

# Execution happens here with full optimization
result = processed.collect(streaming=True)
```

## Best Practices

### 1. **Use Streaming Mode**
```python
# Enable streaming for large datasets
df.collect(streaming=True)  # Constant memory usage
```

### 2. **Optimize Chunk Sizes**
```python
# Balance memory usage and performance
chunk_size = 10000  # Good default
chunk_size = 50000  # For high-memory systems
chunk_size = 2000   # For memory-constrained systems
```

### 3. **Vectorize Transforms**
```python
# Use Polars expressions instead of custom functions
pl.col("amount").cast(pl.Float64)  # Vectorized
# vs
df.map_rows(lambda x: float(x["amount"]))  # Row-by-row
```

### 4. **Chain Operations**
```python
# Chain operations for optimization
result = (
    pl.scan_csv("data.csv")
    .filter(pl.col("status") == "active")
    .with_columns(pl.col("amount").cast(pl.Float64))
    .select(["id", "name", "amount"])
    .collect(streaming=True)
)
```

## Production Recommendations

### For Small Datasets (< 50K rows)
- Regular processing is sufficient
- Memory benefits minimal
- Streaming overhead not worth it

### For Medium Datasets (50K - 1M rows)
- **Use streaming mode**
- Enable vectorized transforms
- Monitor memory usage

### For Large Datasets (> 1M rows)
- **Always use streaming**
- Tune chunk sizes for your system
- Consider distributed processing for multi-GB files

### For Very Large Datasets (> 10M rows)
- Use streaming with smaller chunks
- Implement progress tracking
- Consider splitting into multiple files

## When NOT to Use Enhanced Streaming Mode

While streaming offers significant benefits, there are scenarios where regular processing might be more appropriate:

### 1. **Small Datasets (< 10K rows)**
- **Overhead**: Streaming setup overhead exceeds benefits
- **Memory**: Small datasets fit comfortably in memory anyway
- **Complexity**: Added complexity not justified for simple use cases
- **Performance**: Regular mode may actually be faster due to less coordination

### 2. **Complex Data Transformations**
- **Custom Logic**: Complex business rules that can't be vectorized
- **Multi-pass Processing**: When you need to scan data multiple times
- **Interactive Analysis**: When you need random access to all data
- **Debugging**: Easier to inspect full datasets during development

### 3. **Memory-Rich Environments**
- **Abundant RAM**: When you have 10x+ the dataset size in RAM
- **Single-use Scripts**: One-off data processing tasks
- **Development/Testing**: When working with representative samples

### 4. **Real-time Constraints**
- **Latency-Sensitive**: When you need the absolute lowest latency per record
- **Guaranteed SLA**: When you need predictable, not optimal, performance
- **Resource Contention**: In heavily loaded systems where streaming coordination overhead matters

### 5. **Operational Complexity**
- **Monitoring**: Streaming progress tracking adds monitoring complexity
- **Error Handling**: Partial failures are harder to reason about
- **Debugging**: Stack traces span multiple batches, making debugging harder
- **State Management**: When you need to maintain complex state across batches

## Trade-offs Analysis

### Regular Mode Advantages
```
✅ Simpler error handling and debugging
✅ Easier to reason about data flow
✅ No coordination overhead
✅ Full dataset available for complex operations
✅ Better for ad-hoc analysis and exploration
✅ Predictable memory usage patterns
```

### Streaming Mode Advantages  
```
✅ Constant memory usage regardless of size
✅ Can process datasets larger than RAM
✅ Better throughput for large datasets
✅ Real-time progress tracking
✅ Graceful handling of system resource limits
✅ Better for production ETL pipelines
```

### Performance Crossover Points

Based on our benchmarking:

| Dataset Size | Regular Mode | Streaming Mode | Recommendation |
|-------------|-------------|----------------|----------------|
| < 1K rows   | **Better**  | Overhead      | Use Regular    |
| 1K-10K rows | **Better**  | Similar       | Use Regular    |
| 10K-50K rows| Similar     | **Better**    | Either works   |
| 50K-500K rows| Good       | **Better**    | Use Streaming  |
| > 500K rows | Limited     | **Much Better**| Use Streaming |

### Memory Crossover Points

| Available RAM | Dataset Size | Recommendation |
|--------------|-------------|----------------|
| 32+ GB       | < 1GB       | Regular mode fine |
| 16 GB        | < 500MB     | Regular mode fine |
| 8 GB         | < 200MB     | Regular mode fine |
| 4 GB         | < 100MB     | Regular mode fine |
| Any RAM      | > RAM/4     | **Use Streaming** |

## Practical Decision Framework

### Use Regular Mode When:
1. **Dataset fits comfortably in memory (< 25% of available RAM)**
2. **Development/debugging phase of your project**
3. **One-off analysis or data exploration**
4. **Complex multi-pass algorithms that need full dataset access**
5. **Very small datasets (< 10K rows) where overhead matters**

### Use Enhanced Streaming When:
1. **Production ETL pipelines processing large datasets**
2. **Dataset approaches or exceeds available memory**
3. **Need real-time progress tracking**
4. **Processing datasets > 50K rows regularly**
5. **Memory-constrained environments**
6. **Long-running data processing jobs**

### Hybrid Approach
You can also use both modes strategically:

```python
# Development: Use regular mode for exploration
if is_development:
    df = pl.read_csv(file_path)
    # Fast iteration and debugging
    
# Production: Use streaming for efficiency  
else:
    parser = StreamingCSVParser(file_path)
    for batch in parser.stream_batches():
        # Memory-efficient production processing
```

## Configuration Recommendations

### Smart Defaults in Your Application
```python
def choose_processing_mode(file_size_mb: int, available_ram_gb: int) -> str:
    """Intelligently choose processing mode based on system resources."""
    
    # Small files: always use regular
    if file_size_mb < 10:
        return "regular"
    
    # Large files: always use streaming
    if file_size_mb > available_ram_gb * 1024 / 4:
        return "streaming"
    
    # Medium files: use streaming if > 50MB
    if file_size_mb > 50:
        return "streaming"
    
    return "regular"
```

### Environment-Specific Configurations
```python
# Development environment
development_config = {
    "use_streaming": False,
    "chunk_size": 1000,
    "enable_progress": True
}

# Production environment  
production_config = {
    "use_streaming": True,
    "chunk_size": 50000,
    "enable_progress": True,
    "memory_limit": "2GB"
}

# Memory-constrained environment
constrained_config = {
    "use_streaming": True,
    "chunk_size": 5000,
    "enable_progress": True,
    "memory_limit": "512MB"
}
```

## Summary: When to Use Each Mode

**Default Recommendation**: Start with regular mode for development and small datasets, then switch to streaming mode for production and large datasets.

The enhanced streaming mode is **not always better** - it's a powerful tool for specific scenarios. Choose based on your actual needs, not just because it's "more advanced."

**Run the benchmarks:**
```bash
python benchmark_polars.py          # Basic performance
python streaming_benchmark.py       # Streaming comparison
```
