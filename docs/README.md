# Semantic Model Data Mapper Documentation

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Core Concepts](#core-concepts)
4. [Command Reference](#command-reference)
5. [Configuration Format](#configuration-format)
6. [Workflows](#workflows)
7. [Examples](#examples)
8. [Troubleshooting](#troubleshooting)

## Quick Start

### Install and Test
```bash
pip install -e .
./quickstart_demo.sh
```

### Basic Workflow
```bash
# Generate mapping configuration
rdfmap generate --ontology ontology.ttl --data data.csv --output mapping.yaml

# Convert data to RDF (powered by Polars for high performance)
rdfmap convert --mapping mapping.yaml --format ttl --output output.ttl

# Validate results
rdfmap validate --rdf output.ttl --shapes shapes.ttl
```

### High-Performance Big Data Processing
```bash
# Process large datasets efficiently with Polars
rdfmap convert --mapping config.yaml --output output.ttl

# Use streaming mode for datasets > 100K rows
rdfmap convert --mapping config.yaml --format nt --output output.nt --no-aggregate-duplicates

# Benchmark performance
python scripts/benchmark_scaling.py
```

## Installation

### From Source
```bash
git clone <repository>
cd SemanticModelDataMapper
pip install -e .
```

### Verify Installation
```bash
rdfmap --help
python examples/demo/run_demo.py
```

## Core Concepts

### Mapping Configuration
A YAML file that defines how to convert tabular data to RDF:
- **Namespaces**: URI prefixes for vocabularies
- **Sheets**: Data sources and their mappings
- **Row Resources**: Main entities created from each row
- **Columns**: Property mappings for data fields
- **Objects**: Linked entities and relationships

### Semantic Alignment
The process of matching data fields to ontology properties:
- **Confidence Scores**: Measure mapping quality (0.0-1.0)
- **SKOS Labels**: Used for fuzzy matching (prefLabel, altLabel, hiddenLabel)
- **Alignment Reports**: Detailed analysis of mapping success

### Ontology Enrichment
Adding SKOS labels to improve mapping quality:
- **Coverage Analysis**: Check percentage of properties with labels
- **Suggestion Generation**: Identify missing labels based on data
- **Interactive/Automatic**: Apply improvements manually or automatically

## Command Reference

### `rdfmap convert`
Convert tabular data to RDF using a mapping configuration.

```bash
rdfmap convert \
  --mapping config.yaml \
  --format ttl \
  --output output.ttl \
  --validate \
  --verbose
```

**Options:**
- `--mapping` (required): Path to mapping configuration
- `--format`: Output format (ttl, xml, jsonld, nt)
- `--output`: Output file path
- `--validate`: Run SHACL validation
- `--report`: Write validation report
- `--limit`: Process only first N rows
- `--dry-run`: Parse without writing output
- `--verbose`: Detailed logging

### `rdfmap generate`
Generate mapping configuration from ontology and data.

```bash
rdfmap generate \
  --ontology ontology.ttl \
  --data data.csv \
  --output mapping.yaml \
  --alignment-report \
  --class "TargetClass"
```

**Options:**
- `--ontology` (required): Path to ontology file
- `--data` (required): Path to data file
- `--output` (required): Output mapping file
- `--class`: Target ontology class
- `--alignment-report`: Generate alignment analysis
- `--base-iri`: Base IRI for resources
- `--format`: Output format (yaml/json)
- `--imports`: Additional ontology imports

### `rdfmap enrich`
Enrich ontology with SKOS labels based on alignment suggestions.

```bash
# Interactive mode
rdfmap enrich \
  --ontology ontology.ttl \
  --alignment-report report.json \
  --output enriched.ttl \
  --interactive

# Automatic mode
rdfmap enrich \
  --ontology ontology.ttl \
  --alignment-report report.json \
  --output enriched.ttl \
  --auto-apply \
  --confidence-threshold 0.7
```

### `rdfmap validate`
Validate RDF against SHACL shapes.

```bash
rdfmap validate \
  --rdf data.ttl \
  --shapes shapes.ttl \
  --report validation.json
```

### `rdfmap validate-ontology`
Check SKOS label coverage in ontology.

```bash
rdfmap validate-ontology \
  --ontology ontology.ttl \
  --min-coverage 0.7 \
  --output coverage.json
```

### `rdfmap stats`
Analyze alignment trends over time.

```bash
rdfmap stats \
  --reports-dir reports/ \
  --output stats.json \
  --format text
```

### `rdfmap info`
Display mapping configuration details.

```bash
rdfmap info --mapping config.yaml
```

## Configuration Format

### Basic Structure
```yaml
namespaces:
  ex: https://example.com#
  xsd: http://www.w3.org/2001/XMLSchema#

defaults:
  base_iri: https://data.example.com/
  language: en

sheets:
  - name: employees
    source: employees.csv
    row_resource:
      class: ex:Employee
      iri_template: "{base_iri}employee/{ID}"
    columns:
      Name:
        as: ex:name
        datatype: xsd:string
        required: true
    objects:
      - class: ex:Department
        iri_template: "{base_iri}dept/{DeptCode}"
        condition: "DeptCode != ''"
        properties:
          DeptName:
            as: ex:departmentName
            datatype: xsd:string
```

### Advanced Features
- **Transforms**: Data cleaning and conversion
- **Conditions**: Conditional object creation
- **Multi-sheet**: Multiple data sources
- **Validation**: SHACL constraints
- **Imports**: External ontology references

## Workflows

### 1. Basic Conversion
For straightforward data-to-RDF conversion:

1. Prepare mapping configuration
2. Convert data: `rdfmap convert`
3. Validate output: `rdfmap validate`

### 2. Intelligent Mapping Generation
For automatic mapping discovery:

1. Analyze coverage: `rdfmap validate-ontology`
2. Generate mapping: `rdfmap generate --alignment-report`
3. Review and refine mapping
4. Convert data: `rdfmap convert`

### 3. Continuous Improvement Cycle
For optimal mapping quality:

1. **Initial Analysis**: Check ontology SKOS coverage
2. **Generate Mapping**: Create mapping with alignment report
3. **Enrich Ontology**: Add SKOS labels for unmapped fields
4. **Re-generate**: Create improved mapping
5. **Track Progress**: Use stats to monitor improvement
6. **Iterate**: Repeat cycle for continuous enhancement

### 4. Large Dataset Processing
For efficient handling of large files:

1. Test with subset: `rdfmap convert --limit 100`
2. Optimize chunk size in configuration
3. Use streaming processing options
4. Monitor memory usage and performance

## Examples

### Working Examples
- **`examples/mortgage/`**: Basic loan data conversion
- **`examples/demo/`**: Complete improvement cycle demonstration  
- **`examples/owl2_rdfxml_demo/`**: OWL2 and RDF/XML handling
- **`examples/imports_demo/`**: Multiple ontology files

### Running Examples
```bash
# Quick demo
./quickstart_demo.sh

# Complete improvement cycle
python examples/demo/run_demo.py

# Mortgage example
cd examples/mortgage
rdfmap convert --mapping config/mortgage_mapping.yaml --format ttl --output output.ttl
```

## Troubleshooting

### Common Issues

**Low Mapping Success Rate**
- Check SKOS coverage: `rdfmap validate-ontology`
- Review alignment report for suggestions
- Enrich ontology with missing labels

**Validation Failures**
- Check SHACL shapes compatibility
- Review data types and constraints
- Use `--verbose` for detailed errors

**Import/Path Errors**
- Verify file paths are correct
- Check namespace declarations
- Ensure imported ontologies are accessible

**Performance Issues**
- Adjust chunk size in mapping configuration
- Use `--limit` for testing
- Monitor memory usage with large files

### Getting Help
```bash
# Command help
rdfmap --help
rdfmap generate --help

# Verbose output
rdfmap convert --mapping config.yaml --verbose

# Test with small subset
rdfmap convert --mapping config.yaml --limit 10 --dry-run
```

### Error Messages
Most error messages include suggestions for resolution. Use `--verbose` flag for detailed diagnostics.

## Additional Resources

### Technical Documentation
- **[Developer Guide](DEVELOPMENT.md)** - Architecture, implementation details, and extension points
- **[Workflow Guide](WORKFLOW_GUIDE.md)** - Comprehensive workflow examples and best practices
- **[Polars Integration](POLARS_INTEGRATION.md)** - High-performance big data processing with Polars

### Project Information  
- **[Changelog](CHANGELOG.md)** - Project history, features, and recent fixes
- **[Demo Issues Fixed](DEMO_ISSUES_FIXED.md)** - Documentation of resolved issues and lessons learned

### Working Examples
- **`../examples/mortgage/`** - Basic loan data conversion example
- **`../examples/demo/`** - Complete improvement cycle demonstration
- **`../examples/owl2_rdfxml_demo/`** - OWL2 and RDF/XML handling
- **`../examples/imports_demo/`** - Multiple ontology files example

---

**Note**: This documentation reflects the current working state after recent fixes and consolidation. All examples and commands have been tested and verified to work correctly.
