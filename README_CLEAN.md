# Semantic Model Data Mapper

A powerful tool for converting spreadsheet data (CSV, XLSX, JSON, XML) into RDF triples aligned with ontologies. Features intelligent mapping generation, semantic alignment analysis, and continuous improvement through ontology enrichment.

## Quick Start

```bash
# Install
pip install -e .

# Run demo
./quickstart_demo.sh

# Basic workflow
rdfmap generate --ontology ontology.ttl --data data.csv --output mapping.yaml
rdfmap convert --mapping mapping.yaml --format ttl --output output.ttl
```

## Key Features

- **Automated Mapping Generation**: Analyzes ontologies and data to create mapping configurations
- **Semantic Alignment Reports**: Identifies gaps and suggests improvements
- **Ontology Enrichment**: Adds SKOS labels to improve mapping quality
- **SHACL Validation**: Validates generated RDF against shapes
- **Multiple Formats**: Supports CSV, XLSX, JSON, XML input; TTL, RDF/XML, JSON-LD output
- **Statistics & Trends**: Tracks improvement over time

## Documentation

- **[Complete Guide](docs/README.md)** - Comprehensive usage documentation
- **[Developer Guide](docs/DEVELOPMENT.md)** - Technical implementation details
- **[Workflow Guide](docs/WORKFLOW_GUIDE.md)** - Detailed workflow examples
- **[Changelog](docs/CHANGELOG.md)** - Project history and recent fixes

## Working Examples

- **Basic Example**: `examples/mortgage/` - Loan data conversion
- **Complete Demo**: `examples/demo/` - Full improvement cycle
- **OWL2 Demo**: `examples/owl2_rdfxml_demo/` - Advanced ontology handling
- **Imports Demo**: `examples/imports_demo/` - Multiple ontology files

## Installation

```bash
git clone <repository>
cd SemanticModelDataMapper
pip install -e .
```

## Commands

- `rdfmap convert` - Convert data to RDF
- `rdfmap generate` - Generate mapping configurations
- `rdfmap enrich` - Enrich ontologies with SKOS labels
- `rdfmap validate` - Validate RDF against SHACL
- `rdfmap validate-ontology` - Check SKOS coverage
- `rdfmap stats` - Analyze improvement trends
- `rdfmap info` - Display mapping information

## Recent Fixes

All examples and demos have been tested and verified to work correctly. Recent fixes include:
- Missing RDF namespace imports resolved
- CLI parameter mismatches fixed
- Clean command outputs without confusing tracebacks
- Consolidated and organized documentation

## License

See [LICENSE](LICENSE) file for details.
