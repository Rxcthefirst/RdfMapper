# Semantic Model Data Mapper - Complete Workflow Guide

## Overview

The Semantic Model Data Mapper is a powerful tool that converts spreadsheet data (CSV, XLSX, JSON, XML) into RDF triples aligned with ontologies. It provides an intelligent mapping generation system with continuous improvement through ontology enrichment.

## Key Features

- **Automated Mapping Generation**: Analyzes ontologies and data to generate mapping configurations
- **Semantic Alignment Reports**: Identifies gaps and suggests improvements
- **Ontology Enrichment**: Adds SKOS labels to improve mapping quality
- **SHACL Validation**: Validates generated RDF against shapes
- **Statistics & Trends**: Tracks improvement over time
- **Multiple Formats**: Supports various input/output formats

## Core Workflow

### 1. Basic Conversion Workflow

```bash
# Step 1: Analyze your data and ontology
rdfmap generate \
  --ontology my_ontology.ttl \
  --data my_data.csv \
  --output mapping.yaml \
  --alignment-report

# Step 2: Convert data to RDF
rdfmap convert \
  --mapping mapping.yaml \
  --format ttl \
  --output output.ttl \
  --validate

# Step 3: Validate results
rdfmap validate \
  --rdf output.ttl \
  --shapes shapes.ttl \
  --report validation_report.json
```

### 2. Improvement Cycle Workflow

```bash
# Step 1: Check ontology SKOS coverage
rdfmap validate-ontology \
  --ontology my_ontology.ttl \
  --min-coverage 0.7

# Step 2: Generate mapping with alignment report
rdfmap generate \
  --ontology my_ontology.ttl \
  --data my_data.csv \
  --output mapping.yaml \
  --alignment-report

# Step 3: Enrich ontology based on suggestions
rdfmap enrich \
  --ontology my_ontology.ttl \
  --alignment-report mapping_alignment_report.json \
  --output enriched_ontology.ttl \
  --interactive

# Step 4: Regenerate mapping with enriched ontology
rdfmap generate \
  --ontology enriched_ontology.ttl \
  --data my_data.csv \
  --output improved_mapping.yaml \
  --alignment-report

# Step 5: Track improvements over time
rdfmap stats \
  --reports-dir alignment_reports/ \
  --format text
```

## Available Commands

### `convert` - Convert Data to RDF
Convert spreadsheet data to RDF triples using a mapping configuration.

```bash
rdfmap convert \
  --mapping config.yaml \
  --format ttl \
  --output output.ttl \
  --validate \
  --verbose
```

### `generate` - Generate Mapping Configuration
Automatically generate mapping configuration from ontology and data.

```bash
rdfmap generate \
  --ontology ontology.ttl \
  --data data.csv \
  --class "MyClass" \
  --output mapping.yaml \
  --alignment-report \
  --verbose
```

### `enrich` - Enrich Ontology with SKOS Labels
Add SKOS labels to ontology based on alignment report suggestions.

```bash
# Interactive mode
rdfmap enrich \
  --ontology ontology.ttl \
  --alignment-report report.json \
  --output enriched.ttl \
  --interactive

# Auto-apply mode
rdfmap enrich \
  --ontology ontology.ttl \
  --alignment-report report.json \
  --output enriched.ttl \
  --auto-apply \
  --confidence-threshold 0.7
```

### `validate` - Validate RDF against SHACL
Validate generated RDF data against SHACL shapes.

```bash
rdfmap validate \
  --rdf data.ttl \
  --shapes shapes.ttl \
  --report validation_report.json
```

### `validate-ontology` - Check SKOS Coverage
Analyze ontology SKOS label coverage for mapping quality.

```bash
rdfmap validate-ontology \
  --ontology ontology.ttl \
  --min-coverage 0.7 \
  --output coverage_report.json \
  --verbose
```

### `stats` - Analyze Improvement Trends
Track mapping improvements over time using alignment reports.

```bash
rdfmap stats \
  --reports-dir reports/ \
  --output stats.json \
  --format text \
  --verbose
```

### `info` - Display Mapping Information
Show details about a mapping configuration.

```bash
rdfmap info --mapping config.yaml
```

## Working Examples

### 1. Mortgage Example (Basic Workflow)
Location: `examples/mortgage/`

A complete example showing mortgage loan data mapping.

```bash
cd examples/mortgage

# View mapping configuration
rdfmap info --mapping config/mortgage_mapping.yaml

# Convert with validation
rdfmap convert \
  --mapping config/mortgage_mapping.yaml \
  --format ttl \
  --output mortgage_output.ttl \
  --validate \
  --verbose
```

**Files:**
- `ontology/mortgage.ttl` - Mortgage domain ontology
- `data/loans.csv` - Sample loan data
- `config/mortgage_mapping.yaml` - Pre-configured mapping
- `shapes/mortgage_shapes.ttl` - SHACL validation shapes

### 2. HR Demo (Improvement Cycle)
Location: `examples/demo/`

Demonstrates the complete improvement cycle with HR employee data.

```bash
cd examples/demo

# Run the complete demo
python run_demo.py

# Or run individual steps
rdfmap validate-ontology --ontology ontology/hr_ontology_initial.ttl --min-coverage 0.7
rdfmap generate --ontology ontology/hr_ontology_initial.ttl --data data/employees.csv --class "Employee" --output mapping.yaml --alignment-report
rdfmap enrich --ontology ontology/hr_ontology_initial.ttl --alignment-report mapping_alignment_report.json --output enriched.ttl --auto-apply
```

**What this demo shows:**
- Initial SKOS coverage: 0% → Poor mapping (14% success)
- After enrichment: 28.6% coverage → Better mapping (43% success)
- Statistics tracking improvement over time

### 3. OWL2 RDF/XML Demo
Location: `examples/owl2_rdfxml_demo/`

Shows proper OWL2 ontology handling and RDF/XML output.

```bash
cd examples/owl2_rdfxml_demo
python run_owl2_demo.py
```

### 4. Ontology Imports Demo
Location: `examples/imports_demo/`

Demonstrates working with multiple ontology files using imports.

```bash
cd examples/imports_demo

# Generate mapping with imports
rdfmap generate \
  --ontology core_ontology.ttl \
  --import shared_ontology.ttl \
  --data employees_with_imports.csv \
  --class "Employee" \
  --output mapping.yaml
```

## Key Concepts

### Mapping Configuration Structure
```yaml
namespaces:
  ex: https://example.com#
  xsd: http://www.w3.org/2001/XMLSchema#

defaults:
  base_iri: https://data.example.com/

sheets:
  - name: my_sheet
    source: data.csv
    row_resource:
      class: ex:MyClass
      iri_template: "{base_iri}item/{ID}"
    columns:
      Name:
        as: ex:name
        datatype: xsd:string
        required: true
    objects:
      - class: ex:RelatedClass
        iri_template: "{base_iri}related/{RelatedID}"
        condition: "RelatedID != ''"
        properties:
          RelatedName:
            as: ex:relatedName
            datatype: xsd:string
```

### SKOS Enrichment Impact
- **Hidden Labels**: Match abbreviated column names (e.g., emp_num → employeeNumber)
- **Alternative Labels**: Handle synonyms and variations
- **Preferred Labels**: Improve primary matching

### Alignment Reports
Generated reports contain:
- Mapping success statistics
- Confidence scores
- Unmapped columns list
- SKOS enrichment suggestions
- Weak matches needing review

## Best Practices

### 1. Start with Coverage Analysis
Always check your ontology's SKOS coverage first:
```bash
rdfmap validate-ontology --ontology ontology.ttl --min-coverage 0.7
```

### 2. Use Alignment Reports
Generate alignment reports to understand mapping quality:
```bash
rdfmap generate --ontology ontology.ttl --data data.csv --alignment-report
```

### 3. Iterative Enrichment
Use interactive enrichment to carefully review suggestions:
```bash
rdfmap enrich --interactive --confidence-threshold 0.6
```

### 4. Track Progress
Use statistics to monitor improvement over time:
```bash
rdfmap stats --reports-dir reports/ --format text
```

### 5. Validate Results
Always validate your generated RDF:
```bash
rdfmap convert --mapping config.yaml --validate --report validation.json
```

## Troubleshooting

### Common Issues

1. **Low Mapping Success Rate**
   - Check SKOS coverage: `rdfmap validate-ontology`
   - Review alignment report for suggestions
   - Enrich ontology with missing labels

2. **Validation Failures**
   - Check SHACL shapes for compatibility
   - Review data types and constraints
   - Use `--verbose` for detailed error messages

3. **Import Errors**
   - Verify ontology file paths
   - Check namespace declarations
   - Ensure imported ontologies are accessible

### Getting Help

```bash
# Command-specific help
rdfmap generate --help
rdfmap convert --help
rdfmap enrich --help

# Show all available commands
rdfmap --help
```

## File Structure

```
examples/
├── demo/                    # Complete improvement cycle demo
├── mortgage/               # Basic conversion example
├── owl2_rdfxml_demo/      # OWL2 and RDF/XML example
└── imports_demo/          # Multiple ontology files example

src/rdfmap/
├── cli/                   # Command-line interface
├── generator/             # Mapping generation
├── analyzer/              # Data and ontology analysis
├── emitter/               # RDF generation
├── validator/             # SHACL and coverage validation
└── models/                # Data models and schemas
```

This guide provides a comprehensive overview of the current working state. All examples have been tested and are functional.
