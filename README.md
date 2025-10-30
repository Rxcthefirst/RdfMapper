# Semantic Model Data Mapper

A Python application for converting spreadsheet data (CSV/XLSX) into RDF triples aligned with ontologies, using declarative mapping configurations.

## Features

- **Multi-format Input**: CSV and XLSX (single/multiple sheets)
- **Ontology-Driven**: Align data to OWL/RDF ontologies with full namespace support
- **Configuration-Based**: YAML/JSON mapping files for flexible column-to-property mappings
- **IRI Templating**: Deterministic, idempotent IRI construction
- **Data Transformation**: Type casting, normalization, value transforms, controlled vocabularies
- **Object Linking**: Cross-sheet joins and multi-valued cell unpacking
- **Multiple Output Formats**: Turtle, JSON-LD, N-Triples
- **SHACL Validation**: Validate generated RDF against shapes with detailed reports
- **Robust Error Handling**: Row-level error reporting with summary metrics
- **Performance**: Streaming support for 100k+ row datasets

## Installation

### Requirements
- Python 3.11+

### Setup

```bash
# Clone or navigate to the project
cd SemanticModelDataMapper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Quick Start

### 1. Run the Mortgage Example

```bash
# Convert mortgage loans data to RDF with validation
rdfmap convert \
  --ontology examples/mortgage/ontology/mortgage.ttl \
  --mapping examples/mortgage/config/mortgage_mapping.yaml \
  --format ttl \
  --output output/mortgage.ttl \
  --validate \
  --report output/validation_report.json

# Dry run with first 10 rows
rdfmap convert \
  --mapping examples/mortgage/config/mortgage_mapping.yaml \
  --limit 10 \
  --validate \
  --dry-run

# 🆕 Or auto-generate mapping from ontology + spreadsheet
rdfmap generate \
  --ontology examples/mortgage/ontology/mortgage.ttl \
  --spreadsheet examples/mortgage/data/loans.csv \
  --output auto_mapping.yaml \
  --export-schema
```

### 2. Understanding the Mortgage Example

The example converts loan data with this structure:

**Input CSV** (`examples/mortgage/data/loans.csv`):
```csv
LoanID,BorrowerID,BorrowerName,PropertyID,PropertyAddress,Principal,InterestRate,OriginationDate
L-1001,B-9001,Alex Morgan,P-7001,12 Oak St,250000,0.0525,2023-06-15
```

**Mapping Config** (`examples/mortgage/config/mortgage_mapping.yaml`):
- Maps `LoanID` → `ex:loanNumber`
- Creates linked resources for Borrower and Property
- Applies proper XSD datatypes
- Constructs IRIs using templates

**Output RDF** (Turtle):
```turtle
<https://data.example.com/loan/L-1001> a ex:MortgageLoan ;
  ex:loanNumber "L-1001"^^xsd:string ;
  ex:principalAmount "250000"^^xsd:decimal ;
  ex:hasBorrower <https://data.example.com/borrower/B-9001> ;
  ex:collateralProperty <https://data.example.com/property/P-7001> .
```

## Configuration Reference

### Mapping File Structure

```yaml
# Namespace declarations
namespaces:
  ex: https://example.com/mortgage#
  xsd: http://www.w3.org/2001/XMLSchema#

# Default settings
defaults:
  base_iri: https://data.example.com/
  language: en  # Optional default language tag

# Sheet/file mappings
sheets:
  - name: loans
    source: loans.csv  # Relative to mapping file or absolute
    
    # Main resource for each row
    row_resource:
      class: ex:MortgageLoan
      iri_template: "{base_iri}loan/{LoanID}"
    
    # Column mappings
    columns:
      LoanID:
        as: ex:loanNumber
        datatype: xsd:string
        required: true
      
      Principal:
        as: ex:principalAmount
        datatype: xsd:decimal
        transform: to_decimal  # Built-in transform
        default: 0  # Optional default value
      
      Notes:
        as: rdfs:comment
        datatype: xsd:string
        language: en  # Language tag for literal
    
    # Linked objects (object properties)
    objects:
      borrower:
        predicate: ex:hasBorrower
        class: ex:Borrower
        iri_template: "{base_iri}borrower/{BorrowerID}"
        properties:
          - column: BorrowerName
            as: ex:borrowerName
            datatype: xsd:string

# Validation configuration
validation:
  shacl:
    enabled: true
    shapes_file: shapes/mortgage_shapes.ttl

# Processing options
options:
  delimiter: ","
  header: true
  on_error: "report"  # "report" or "fail-fast"
  skip_empty_values: true
```

### Built-in Transforms

- `to_decimal`: Convert to decimal number
- `to_integer`: Convert to integer
- `to_date`: Parse date (ISO format)
- `to_datetime`: Parse datetime with timezone support
- `to_boolean`: Convert to boolean
- `uppercase`: Convert string to uppercase
- `lowercase`: Convert string to lowercase
- `strip`: Trim whitespace

### IRI Templates

Use Python-style string formatting with column names:
- `{base_iri}loan/{LoanID}` → `https://data.example.com/loan/L-1001`
- `{base_iri}{EntityType}/{ID}` → Combine multiple columns

## CLI Reference

### Commands

#### `convert`

Convert spreadsheet data to RDF.

```bash
rdfmap convert [OPTIONS]
```

**Options:**

- `--ontology PATH`: Path to ontology file (supports TTL, RDF/XML, JSON-LD, N-Triples, etc.)
- `--mapping PATH`: Path to mapping configuration (YAML/JSON) [required]
- `--format, -f TEXT`: Output format: ttl, xml, jsonld, nt (default: ttl)
- `--output, -o FILE`: Output file path
- `--validate`: Run SHACL validation after conversion
- `--report PATH`: Write validation report to file (JSON)
- `--limit N`: Process only first N rows (for testing)
- `--dry-run`: Parse and validate without writing output
- `--verbose, -v`: Enable detailed logging
- `--log PATH`: Write log to file

**Examples:**

```bash
# Basic conversion to Turtle
rdfmap convert --mapping config.yaml --format ttl --output output.ttl

# With ontology validation and SHACL validation
rdfmap convert \
  --mapping config.yaml \
  --ontology ontology.ttl \
  --format jsonld \
  --output output.jsonld \
  --validate \
  --report validation.json

# Test with limited rows
rdfmap convert --mapping config.yaml --limit 100 --dry-run --verbose
```

#### `generate`

**NEW**: Automatically generate mapping configuration from ontology and spreadsheet.

```bash
rdfmap generate [OPTIONS]
```

**Options:**

- `--ontology, -ont PATH`: Path to ontology file (TTL, RDF/XML, etc.) [required]
- `--spreadsheet, -s PATH`: Path to spreadsheet file (CSV/XLSX) [required]
- `--output, -o PATH`: Output path for generated mapping config [required]
- `--base-iri, -b TEXT`: Base IRI for resources (default: http://example.org/)
- `--class, -c TEXT`: Target ontology class (auto-detects if omitted)
- `--format, -f TEXT`: Output format: yaml or json (default: yaml)
- `--analyze-only`: Show analysis without generating mapping
- `--export-schema`: Export JSON Schema for validation
- `--verbose, -v`: Enable detailed logging

**Examples:**

```bash
# Auto-generate mapping configuration
rdfmap generate \
  --ontology ontology.ttl \
  --spreadsheet data.csv \
  --output mapping.yaml

# Specify target class and export JSON Schema
rdfmap generate \
  -ont ontology.ttl \
  -s data.csv \
  -o mapping.yaml \
  --class MortgageLoan \
  --export-schema

# Analyze only (no generation)
rdfmap generate \
  --ontology ontology.ttl \
  --spreadsheet data.csv \
  --output mapping.yaml \
  --analyze-only
```

**What it does:**
- Analyzes ontology classes and properties
- Examines spreadsheet columns and data types
- Intelligently matches columns to properties
- Suggests appropriate XSD datatypes
- Generates IRI templates from identifier columns
- Detects relationships for linked objects
- Exports JSON Schema for validation

See [docs/MAPPING_GENERATOR.md](docs/MAPPING_GENERATOR.md) for details.

#### `validate`

Validate existing RDF file against shapes.

```bash
rdfmap validate --rdf PATH --shapes PATH [--report PATH]
```

#### `info`

Display information about mapping configuration.

```bash
rdfmap info --mapping PATH
```

## Architecture

```
rdfmap/
├── parsers/          # CSV/XLSX data source parsers
├── models/           # Pydantic schemas for mapping config
├── transforms/       # Data transformation functions
├── iri/              # IRI templating and generation
├── emitter/          # RDF graph construction with rdflib
├── validator/        # SHACL validation integration
└── cli/              # Command-line interface
```

### Key Design Principles

1. **Configuration-Driven**: All mappings declarative in YAML/JSON
2. **Modular**: Clear separation between parsing, transformation, and emission
3. **Deterministic**: Same input always produces same IRIs (idempotency)
4. **Extensible**: Easy to add new transforms, datatypes, or ontology patterns
5. **Robust**: Comprehensive error handling with row-level tracking

## Extending the Application

### Adding Custom Transforms

Edit `rdfmap/transforms/functions.py`:

```python
@register_transform("custom_transform")
def custom_transform(value: Any, **kwargs) -> Any:
    """Your custom transformation logic."""
    return transformed_value
```

### Supporting New Ontology Patterns

1. Update mapping schema in `rdfmap/models/mapping.py` if needed
2. Implement pattern handler in `rdfmap/emitter/graph_builder.py`
3. Add test cases in `tests/test_patterns.py`

### Adding New Output Formats

Extend `rdfmap/emitter/serializer.py`:

```python
def serialize(graph: Graph, format: str, output_path: Path):
    if format == "your_format":
        # Custom serialization logic
        pass
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=rdfmap --cov-report=html

# Run specific test file
pytest tests/test_transforms.py

# Run mortgage example test
pytest tests/test_mortgage_example.py -v
```

## Error Handling

The application provides detailed error reporting:

### Row-Level Errors

```json
{
  "row": 42,
  "error": "Invalid datatype for column 'Principal': cannot convert 'N/A' to xsd:decimal",
  "severity": "error"
}
```

### Validation Reports

```json
{
  "conforms": false,
  "results": [
    {
      "focusNode": "https://data.example.com/loan/L-1001",
      "resultPath": "ex:principalAmount",
      "resultMessage": "Value must be greater than 0"
    }
  ]
}
```

## Performance Tips

1. **Large Files**: The application automatically streams data for files >10MB
2. **Chunking**: Process in batches using `--limit` and multiple runs
3. **Validation**: Skip validation during development (`--validate` only for final runs)
4. **Dry Runs**: Test mappings with `--limit 100 --dry-run` before full processing

## Troubleshooting

### "Column not found" errors
- Check CSV column names match mapping config exactly (case-sensitive)
- Verify CSV delimiter matches config (`delimiter: ","`)

### Invalid IRIs
- Ensure IRI template variables match column names exactly
- Check that base_iri ends with `/` or `#`

### Datatype conversion errors
- Review data for unexpected values (nulls, text in numeric fields)
- Use `transform` to normalize before typing
- Set `skip_empty_values: true` to ignore nulls

### SHACL validation failures
- Review validation report for specific violations
- Ensure ontology and shapes are compatible
- Check that required properties are mapped

## Contributing

Contributions welcome! Please:

1. Follow PEP 8 style guidelines
2. Add unit tests for new features
3. Update documentation
4. Run `pytest` and `mypy` before submitting

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or feature requests, please open an issue on the project repository.

## Acknowledgments

Built with:
- [rdflib](https://rdflib.readthedocs.io/) - RDF processing
- [pandas](https://pandas.pydata.org/) - Data manipulation
- [pydantic](https://docs.pydantic.dev/) - Data validation
- [pyshacl](https://github.com/RDFLib/pySHACL) - SHACL validation
- [typer](https://typer.tiangolo.com/) - CLI framework
