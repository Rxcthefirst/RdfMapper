# Large Dataset Generator

High-performance data generator using Polars for creating large test datasets. Perfect for performance testing and benchmarking.

## Features

- ⚡ **Lightning Fast**: Uses Polars for high-performance generation (100k+ rows/second)
- 🔧 **Configurable**: JSON-based configuration for any data schema
- 📊 **Rich Data Types**: IDs, strings, integers, floats, dates, emails, addresses, names, enums
- 🎯 **Reproducible**: Seed-based generation for consistent results
- 💾 **Memory Efficient**: Streams data generation without loading everything in memory

## Installation

```bash
pip install polars numpy
```

Or add to requirements.txt:
```
polars>=0.19.0
numpy>=1.24.0
```

## Quick Start

### Generate 500k mortgage loans (default config)

```bash
python scripts/generate_large_dataset.py \
  --rows 500000 \
  --output examples/mortgage/data/loans_500k.csv
```

### Use custom configuration

```bash
python scripts/generate_large_dataset.py \
  --config scripts/config_mortgage_500k.json \
  --output data/loans_large.csv
```

### Generate and save the config

```bash
python scripts/generate_large_dataset.py \
  --rows 1000000 \
  --output data/loans_1m.csv \
  --save-config scripts/config_1m.json
```

## Configuration Format

### Full Example

```json
{
  "num_rows": 500000,
  "seed": 42,
  "columns": [
    {
      "name": "LoanID",
      "type": "id",
      "format": "L"
    },
    {
      "name": "Principal",
      "type": "integer",
      "min": 100000,
      "max": 1000000
    },
    {
      "name": "InterestRate",
      "type": "float",
      "min": 0.03,
      "max": 0.08,
      "decimals": 4
    },
    {
      "name": "Status",
      "type": "enum",
      "values": ["Active", "Paid Off", "Delinquent"]
    }
  ]
}
```

### Column Types

| Type | Description | Options | Example |
|------|-------------|---------|---------|
| `id` | Sequential IDs with prefix | `format`: prefix (default: "ID") | `L-000001`, `B-000042` |
| `string` | Random strings | `format`: length (default: 10) | `aBcDeFgHiJ` |
| `integer` | Random integers | `min`, `max` | `250000` |
| `float` | Random floats | `min`, `max`, `decimals` | `0.0525` |
| `date` | Random dates | `format`: "start:end" | `2023-06-15` |
| `boolean` | Random booleans | - | `true`, `false` |
| `email` | Random emails | - | `user1234@gmail.com` |
| `phone` | Random phone numbers | - | `555-123-4567` |
| `address` | Random addresses | - | `123 Oak St` |
| `name` | Random person names | - | `Alex Morgan` |
| `enum` | Pick from list | `values`: array | `Active` |

### Column Configuration Examples

#### ID Column
```json
{
  "name": "LoanID",
  "type": "id",
  "format": "L"
}
```
Output: `L-000001`, `L-000002`, ...

#### Integer Column
```json
{
  "name": "Principal",
  "type": "integer",
  "min": 100000,
  "max": 1000000
}
```
Output: Random integers between 100,000 and 1,000,000

#### Float Column
```json
{
  "name": "InterestRate",
  "type": "float",
  "min": 0.03,
  "max": 0.08,
  "decimals": 4
}
```
Output: `0.0525`, `0.0647`, ...

#### Date Column
```json
{
  "name": "OriginationDate",
  "type": "date",
  "format": "2020-01-01:2023-12-31"
}
```
Output: Random dates between 2020-01-01 and 2023-12-31

#### Enum Column
```json
{
  "name": "Status",
  "type": "enum",
  "values": ["Active", "Paid Off", "Delinquent", "Foreclosed"]
}
```
Output: Randomly picks from the values list

## Performance

Expected performance on modern hardware:

| Rows | Columns | Generation Time | Speed | File Size |
|------|---------|----------------|-------|-----------|
| 10k | 10 | ~0.1s | 100k rows/s | ~1 MB |
| 100k | 10 | ~1s | 100k rows/s | ~10 MB |
| 500k | 10 | ~5s | 100k rows/s | ~50 MB |
| 1M | 10 | ~10s | 100k rows/s | ~100 MB |

*Actual speed depends on CPU, column types, and disk I/O*

## Usage Examples

### Test Performance with Different Sizes

```bash
# Small test (1k rows)
python scripts/generate_large_dataset.py --rows 1000 --output test_1k.csv

# Medium test (100k rows)
python scripts/generate_large_dataset.py --rows 100000 --output test_100k.csv

# Large test (500k rows)
python scripts/generate_large_dataset.py --rows 500000 --output test_500k.csv

# Extra large (1M rows)
python scripts/generate_large_dataset.py --rows 1000000 --output test_1m.csv
```

### Generate Multiple Files

```bash
# Generate different sizes for benchmarking
for size in 1000 10000 100000 500000 1000000; do
  python scripts/generate_large_dataset.py \
    --rows $size \
    --output data/loans_${size}.csv
done
```

### Create Custom Schema

Create a config file `my_schema.json`:

```json
{
  "num_rows": 100000,
  "seed": 123,
  "columns": [
    {"name": "CustomerID", "type": "id", "format": "CUST"},
    {"name": "Email", "type": "email"},
    {"name": "FullName", "type": "name"},
    {"name": "Age", "type": "integer", "min": 18, "max": 80},
    {"name": "Balance", "type": "float", "min": 0, "max": 10000, "decimals": 2},
    {"name": "AccountType", "type": "enum", "values": ["Checking", "Savings", "Credit"]},
    {"name": "CreatedDate", "type": "date", "format": "2015-01-01:2023-12-31"},
    {"name": "Active", "type": "boolean"}
  ]
}
```

Generate:
```bash
python scripts/generate_large_dataset.py \
  --config my_schema.json \
  --output customers.csv
```

## Integration with RDFMap

### Performance Testing Workflow

1. **Generate large dataset**:
   ```bash
   python scripts/generate_large_dataset.py \
     --rows 500000 \
     --output examples/mortgage/data/loans_500k.csv
   ```

2. **Test mapping generation**:
   ```bash
   time rdfmap generate \
     --ontology examples/mortgage/ontology/mortgage_ontology.ttl \
     --data examples/mortgage/data/loans_500k.csv \
     --output-format inline \
     --config mapping_500k.yaml
   ```

3. **Test conversion**:
   ```bash
   time rdfmap convert \
     --mapping mapping_500k.yaml \
     --limit 500000 \
     --output output_500k.ttl
   ```

4. **Benchmark results**:
   - Generation time
   - Conversion time
   - Output file size
   - Memory usage

## Tips & Tricks

### Speed Optimization

1. **Use simple data types**: IDs and enums are fastest
2. **Avoid complex formats**: Emails and addresses are slower
3. **Use batch sizes**: For memory-constrained environments
4. **Set seed**: For reproducible benchmarks

### Memory Management

For very large datasets (10M+ rows), consider:
- Generating in chunks
- Streaming to disk
- Using compressed formats

### Reproducibility

Always use the same seed for comparable benchmarks:
```json
{
  "seed": 42
}
```

## Troubleshooting

### Memory Error

If you get a memory error:
- Reduce `num_rows`
- Use simpler column types
- Close other applications

### Slow Generation

If generation is slow:
- Check disk I/O (SSD vs HDD)
- Simplify column types
- Reduce number of columns

### Import Error

If you see `ModuleNotFoundError: No module named 'polars'`:
```bash
pip install polars numpy
```

## Advanced: Extending Data Types

To add custom data types, edit `generate_large_dataset.py`:

```python
def _generate_custom(self, name: str) -> pl.Series:
    """Generate custom data."""
    data = [f"CUSTOM-{i}" for i in range(self.num_rows)]
    return pl.Series(name, data, dtype=pl.Utf8)
```

Then add to the type mapping in `generate_column()`.

## License

Part of the SemanticModelDataMapper project.

## See Also

- [RDFMap Documentation](../README.md)
- [Polars Documentation](https://pola-rs.github.io/polars/)
- [Performance Testing Guide](../docs/PERFORMANCE_TESTING.md)

