# Large Dataset Generator - Quick Start Guide

## 🚀 What You Got

A high-performance data generator using **Polars** that can create 500,000+ row CSV files in seconds.

---

## 📦 Installation

```bash
# Install required dependencies
pip install polars numpy

# Or add to requirements.txt
echo "polars>=0.19.0" >> requirements.txt
echo "numpy>=1.24.0" >> requirements.txt
pip install -r requirements.txt
```

---

## ⚡ Quick Usage

### Method 1: Shell Script (Easiest)

```bash
# Generate 500k rows (default)
./scripts/generate_test_data.sh

# Generate custom size
./scripts/generate_test_data.sh 1000000  # 1 million rows

# Specify output location
./scripts/generate_test_data.sh 500000 my_data.csv
```

### Method 2: Python Script (More Control)

```bash
# Generate 500k mortgage loans
python scripts/generate_large_dataset.py \
  --rows 500000 \
  --output examples/mortgage/data/loans_500k.csv

# Use custom config
python scripts/generate_large_dataset.py \
  --config scripts/config_mortgage_500k.json \
  --output data/loans_large.csv
```

---

## 📊 Performance

**Expected speed**: 100,000+ rows/second

| Rows | Time | File Size |
|------|------|-----------|
| 10k | ~0.1s | ~1 MB |
| 100k | ~1s | ~10 MB |
| 500k | ~5s | ~50 MB |
| 1M | ~10s | ~100 MB |

---

## 🔧 Configuration

The default mortgage config includes:
- **LoanID**: `L-000001`, `L-000002`, ...
- **BorrowerID**: `B-000001`, `B-000002`, ...
- **BorrowerName**: Random names (Alex Morgan, Jamie Lee, ...)
- **PropertyID**: `P-000001`, `P-000002`, ...
- **PropertyAddress**: Random addresses (123 Oak St, ...)
- **Principal**: Random $100k-$1M
- **InterestRate**: Random 3%-8%
- **OriginationDate**: Random 2020-2023
- **LoanTerm**: 180, 240, 300, or 360 months
- **Status**: Active, Paid Off, Delinquent, or Foreclosed

### Customize Configuration

Edit `scripts/config_mortgage_500k.json`:

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
    }
  ]
}
```

**Supported Types**:
- `id` - Sequential IDs with prefix
- `string` - Random strings
- `integer` - Random integers in range
- `float` - Random floats with decimals
- `date` - Random dates in range
- `boolean` - Random true/false
- `email` - Random email addresses
- `phone` - Random phone numbers
- `address` - Random street addresses
- `name` - Random person names
- `enum` - Pick from list of values

---

## 🎯 Performance Testing Workflow

### 1. Generate Large Dataset
```bash
./scripts/generate_test_data.sh 500000
```

### 2. Test Your RDFMap Application

```bash
# Test mapping generation
time rdfmap generate \
  --ontology examples/mortgage/ontology/mortgage_ontology.ttl \
  --data examples/mortgage/data/loans_500k.csv \
  --output-format inline \
  --config mapping_500k.yaml

# Test conversion
time rdfmap convert \
  --mapping mapping_500k.yaml \
  --limit 500000 \
  --output output_500k.ttl
```

### 3. Benchmark Different Sizes

```bash
# Generate multiple sizes
for size in 10000 50000 100000 500000 1000000; do
  echo "Testing with $size rows..."
  ./scripts/generate_test_data.sh $size data/loans_${size}.csv
  
  # Run your performance tests here
  time rdfmap convert --mapping config.yaml --limit $size
done
```

---

## 📝 Examples

### Example 1: Small Test (1k rows)
```bash
python scripts/generate_large_dataset.py --rows 1000 --output test_small.csv
```

### Example 2: Medium Test (100k rows)
```bash
python scripts/generate_large_dataset.py --rows 100000 --output test_medium.csv
```

### Example 3: Large Test (500k rows)
```bash
python scripts/generate_large_dataset.py --rows 500000 --output test_large.csv
```

### Example 4: Extra Large (1M rows)
```bash
python scripts/generate_large_dataset.py --rows 1000000 --output test_xl.csv
```

### Example 5: Custom Config
```bash
python scripts/generate_large_dataset.py \
  --config my_custom_config.json \
  --output custom_data.csv \
  --save-config my_config_backup.json
```

---

## 🔍 Verify Output

### Check file size
```bash
ls -lh examples/mortgage/data/loans_500k.csv
```

### View first few rows
```bash
head examples/mortgage/data/loans_500k.csv
```

### Count rows
```bash
wc -l examples/mortgage/data/loans_500k.csv
```

### View sample in Python
```python
import polars as pl
df = pl.read_csv('examples/mortgage/data/loans_500k.csv')
print(df.head())
print(f"Shape: {df.shape}")
```

---

## 🛠️ Troubleshooting

### "ModuleNotFoundError: No module named 'polars'"
```bash
pip install polars numpy
```

### Slow generation?
- Check if using HDD instead of SSD
- Reduce column complexity
- Use simpler data types (id, enum instead of email, address)

### Out of memory?
- Reduce `num_rows`
- Close other applications
- Generate in smaller batches

---

## 📁 Files Created

```
scripts/
├── generate_large_dataset.py      # Main generator script
├── generate_test_data.sh          # Convenience wrapper
├── config_mortgage_500k.json      # Example config
└── README_DATA_GENERATOR.md       # Full documentation
```

---

## 🎓 Next Steps

1. **Install dependencies**: `pip install polars numpy`
2. **Generate test data**: `./scripts/generate_test_data.sh 500000`
3. **Test your application**: Run your performance benchmarks
4. **Measure**: Time, memory, throughput
5. **Optimize**: Based on results
6. **Scale up**: Test with 1M+ rows

---

## 📚 Full Documentation

See `scripts/README_DATA_GENERATOR.md` for:
- Complete configuration reference
- All data types and options
- Advanced usage examples
- Performance tuning tips
- Custom data type extensions

---

**Ready to generate 500k rows? Run:**
```bash
./scripts/generate_test_data.sh 500000
```

🚀 **Fast. Configurable. Built for performance testing.**

