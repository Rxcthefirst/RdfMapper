# Developer Guide

## Architecture Overview

```
src/rdfmap/
├── cli/           # Command-line interface (typer-based)
├── config/        # Configuration loading and validation
├── parsers/       # Data source parsers (CSV, XLSX, JSON, XML)
├── analyzer/      # Data and ontology analysis
├── generator/     # Mapping generation and alignment
├── emitter/       # RDF graph building and serialization
├── validator/     # SHACL and SKOS coverage validation
├── transforms/    # Data transformation utilities
├── iri/           # IRI template processing
└── models/        # Pydantic data models and schemas
```

## Key Components

### CLI (`cli/main.py`)
- Typer-based command-line interface
- Commands: convert, generate, enrich, validate, stats, info
- Rich console output with progress indicators
- Error handling and exit codes

### Configuration (`config/`)
- YAML/JSON mapping configuration loading
- Namespace prefix validation
- Required field checking
- Schema validation with detailed error messages

### Parsers (`parsers/`)
- **CSV/TSV**: pandas-based with delimiter detection
- **Excel**: openpyxl support for multiple sheets
- **JSON**: Nested object flattening and array handling
- **XML**: Element-to-row conversion with xpath support

### Analyzer (`analyzer/`)
- **Data Analysis**: Column type detection, pattern recognition
- **Ontology Analysis**: Class/property extraction, relationship mapping
- **Alignment Analysis**: Statistical tracking and trend analysis

### Generator (`generator/`)
- **Mapping Generation**: Automated configuration creation
- **Semantic Alignment**: Fuzzy matching with SKOS labels
- **Confidence Scoring**: Quality metrics for mappings
- **Enrichment Suggestions**: SKOS label recommendations

### Emitter (`emitter/`)
- **Graph Building**: RDFLib-based triple generation
- **IRI Processing**: Template-based URI creation
- **Serialization**: Multiple format support (TTL, RDF/XML, JSON-LD, N-Triples)
- **Validation Integration**: SHACL constraint checking

### Validator (`validator/`)
- **SHACL Validation**: pySHACL integration with inference support
- **SKOS Coverage**: Label coverage analysis and reporting
- **Configuration Validation**: Namespace and field validation

## Data Models (`models/`)

### Core Models
- **MappingConfig**: Complete mapping configuration
- **SheetConfig**: Individual data source mapping
- **ColumnMapping**: Field-to-property mapping
- **ObjectMapping**: Linked entity configuration

### Analysis Models
- **AlignmentReport**: Semantic alignment analysis results
- **SKOSCoverageReport**: Ontology label coverage analysis
- **ProcessingReport**: Data conversion statistics

### Enrichment Models
- **EnrichmentSuggestion**: SKOS label addition recommendations
- **EnrichmentResult**: Applied enrichment tracking
- **ProvenanceInfo**: Change tracking and attribution

## Implementation Details

### Mapping Generation Algorithm

1. **Ontology Analysis**
   - Extract classes and properties using SPARQL
   - Build property-to-class relationships
   - Collect existing SKOS labels for matching

2. **Data Analysis**
   - Analyze column names, types, and value patterns
   - Identify potential identifier columns
   - Detect nested structures and relationships

3. **Semantic Alignment**
   - Fuzzy string matching between columns and properties
   - SKOS label matching (exact, partial, hidden)
   - Confidence scoring based on multiple factors
   - Threshold-based acceptance/rejection

4. **Configuration Generation**
   - Create IRI templates from identifier columns
   - Map high-confidence column-property pairs
   - Generate object mappings for relationships
   - Add validation constraints where appropriate

### SKOS Enrichment Process

1. **Gap Analysis**
   - Identify unmapped columns from alignment reports
   - Analyze column name patterns and variations
   - Generate label suggestions (prefLabel, altLabel, hiddenLabel)

2. **Suggestion Generation**
   - Common abbreviations (emp_num → employeeNumber)
   - Camel case splitting (firstName → first name)
   - Domain-specific patterns
   - Confidence scoring for suggestions

3. **Interactive Application**
   - Present suggestions with context
   - Allow editing and annotation
   - Track provenance information
   - Batch apply high-confidence suggestions

### Data Processing Pipeline

1. **Configuration Loading**
   - Parse YAML/JSON mapping files
   - Validate namespaces and references
   - Check required fields and templates

2. **Data Parsing**
   - Auto-detect format and encoding
   - Handle chunked processing for large files
   - Apply data transformations
   - Error handling and reporting

3. **RDF Generation**
   - Process each row according to mapping
   - Generate subject URIs from templates
   - Create property assertions
   - Handle linked objects and relationships

4. **Validation and Output**
   - Optional SHACL validation
   - Multi-format serialization
   - Progress reporting and statistics

## Testing Strategy

### Unit Tests
- Individual component testing
- Mock external dependencies
- Edge case handling
- Error condition testing

### Integration Tests
- End-to-end workflow testing
- Example validation
- Performance benchmarking
- Multi-format compatibility

### Demo Validation
- Automated example execution
- Output verification
- Error-free demonstration runs
- Documentation accuracy

## Development Workflow

### Setup
```bash
git clone <repository>
cd SemanticModelDataMapper
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install -r requirements-dev.txt
```

### Testing
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src/rdfmap

# Test examples
./quickstart_demo.sh
python examples/demo/run_demo.py
```

### Code Quality
```bash
# Linting
ruff check src/

# Formatting
ruff format src/

# Type checking
mypy src/rdfmap
```

## Performance Considerations

### Memory Management
- Chunked data processing for large files
- Streaming RDF generation
- Configurable chunk sizes
- Memory usage monitoring

### Optimization Techniques
- Lazy loading of ontologies
- Cached SPARQL queries
- Efficient string matching algorithms
- Parallel processing where appropriate

### Scalability
- Horizontal scaling through chunking
- Database backend support for large ontologies
- Distributed processing capabilities
- Memory-mapped file handling

## Extension Points

### Custom Parsers
Implement `DataSourceParser` interface for new formats:
```python
class CustomParser(DataSourceParser):
    def parse(self, chunk_size: int) -> Iterator[pd.DataFrame]:
        # Implementation
        pass
```

### Custom Transforms
Add data transformation functions:
```python
def custom_transform(value: Any, context: Dict) -> Any:
    # Implementation
    return transformed_value
```

### Custom Validators
Extend validation with domain-specific rules:
```python
class CustomValidator:
    def validate(self, graph: Graph) -> ValidationReport:
        # Implementation
        pass
```

## Deployment

### Package Distribution
- PyPI publishing workflow
- Version management
- Dependency specification
- Documentation packaging

### Docker Containerization
- Multi-stage builds
- Minimal runtime images
- Volume mounting for data
- Environment configuration

### CI/CD Pipeline
- Automated testing
- Code quality checks
- Documentation generation
- Release automation

---

This guide provides the technical foundation for understanding and extending the Semantic Model Data Mapper codebase.
