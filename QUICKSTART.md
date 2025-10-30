# Quick Start Guide

This guide will help you get started with the Semantic Model Data Mapper using the mortgage example.

## Installation

```bash
# Navigate to project directory
cd SemanticModelDataMapper

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

## Verify Installation

```bash
# Check that the CLI is available
rdfmap --help
```

## Run the Mortgage Example

### Step 1: Explore the Example Files

The mortgage example is located in `examples/mortgage/`:

```
examples/mortgage/
├── ontology/
│   └── mortgage.ttl          # OWL ontology
├── shapes/
│   └── mortgage_shapes.ttl   # SHACL validation shapes
├── data/
│   └── loans.csv             # Sample mortgage data
└── config/
    └── mortgage_mapping.yaml # Mapping configuration
```

### Step 2: Convert Data to RDF

```bash
# Basic conversion
rdfmap convert \
  --mapping examples/mortgage/config/mortgage_mapping.yaml \
  --format ttl \
  --output output/mortgage.ttl

# Conversion with validation
rdfmap convert \
  --mapping examples/mortgage/config/mortgage_mapping.yaml \
  --ontology examples/mortgage/ontology/mortgage.ttl \
  --format ttl \
  --output output/mortgage.ttl \
  --validate \
  --report output/validation_report.json

# Dry run to test configuration
rdfmap convert \
  --mapping examples/mortgage/config/mortgage_mapping.yaml \
  --dry-run \
  --verbose
```

### Step 3: Examine the Output

```bash
# View generated Turtle
cat output/mortgage.ttl

# View validation report (if validation was run)
cat output/validation_report.json
```

### Step 4: Validate Existing RDF

```bash
# Validate an RDF file against SHACL shapes
rdfmap validate \
  --rdf output/mortgage.ttl \
  --shapes examples/mortgage/shapes/mortgage_shapes.ttl \
  --report output/validation_report.json
```

## Understanding the Mapping Configuration

The mapping file (`mortgage_mapping.yaml`) defines:

1. **Namespaces**: Prefix declarations for ontology terms
2. **Defaults**: Base IRI and default values
3. **Sheets**: Data source mappings
   - **Row Resource**: Class and IRI template for main entities
   - **Columns**: Data property mappings with transformations
   - **Objects**: Linked object property mappings

Example snippet:

```yaml
sheets:
  - name: loans
    source: data/loans.csv
    row_resource:
      class: ex:MortgageLoan
      iri_template: "{base_iri}loan/{LoanID}"
    columns:
      Principal:
        as: ex:principalAmount
        datatype: xsd:decimal
        transform: to_decimal
    objects:
      borrower:
        predicate: ex:hasBorrower
        class: ex:Borrower
        iri_template: "{base_iri}borrower/{BorrowerID}"
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=rdfmap

# Run specific test file
pytest tests/test_mortgage_example.py -v
```

## Next Steps

1. **Modify the Example**: Edit `loans.csv` to add more data
2. **Extend the Ontology**: Add properties to `mortgage.ttl`
3. **Update Mappings**: Modify `mortgage_mapping.yaml` to map new fields
4. **Create Your Own**: Use the mortgage example as a template for your data

## Troubleshooting

### Common Issues

**Issue**: "Configuration file not found"
- **Solution**: Ensure you're running commands from the project root directory

**Issue**: "Column not found in data"
- **Solution**: Check that CSV column names exactly match those in the mapping file

**Issue**: "Unknown namespace prefix"
- **Solution**: Verify all prefixes used in mappings are declared in the `namespaces` section

**Issue**: Import errors when running tests
- **Solution**: Make sure you've installed the package: `pip install -e .`

## Getting Help

- Review the full README for detailed documentation
- Check test files for usage examples
- Open an issue for bugs or feature requests
