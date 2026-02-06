# RDFMap v3 Quick Start Guide

## What's New in v3

RDFMap v3 introduces a universal, standards-compliant configuration format aligned with RML/YARRRML:

**Key Changes**:
- ✅ `sources` + `mappings` (not `sheets`)
- ✅ `subject` (not `row_resource`)  
- ✅ `properties` with `predicate` field (not `as`)
- ✅ `relationships` (not `objects`)
- ✅ Universal data source support (CSV, JSON, XML, SQL, APIs)

---

## Basic Example

### Configuration File (v3 format)

```yaml
# config.yaml

# Namespace prefixes
namespaces:
  ex: https://example.com/
  xsd: http://www.w3.org/2001/XMLSchema#

# Base IRI for generated resources
base_iri: http://example.org/

# Data sources
sources:
  employees_data:
    path: data/employees.csv
    format: csv

# Entity mappings
mappings:
  Employee:
    sources: employees_data
    
    # Subject (main resource) configuration
    subject:
      class: ex:Employee
      iri_template: "{base_iri}employee/{EmployeeID}"
    
    # Data properties (literals)
    properties:
      Name:
        predicate: ex:name
        datatype: xsd:string
        required: true
      
      Salary:
        predicate: ex:salary
        datatype: xsd:integer
        transform: to_integer
      
      HireDate:
        predicate: ex:hireDate
        datatype: xsd:date
        transform: to_date
    
    # Relationships (links to other entities)
    relationships:
      department:
        predicate: ex:worksIn
        object:
          class: ex:Department
          iri_template: "{base_iri}department/{DepartmentID}"
          properties:
            DeptName:
              predicate: ex:departmentName
              datatype: xsd:string

# Processing options
options:
  output_format: ttl
  skip_empty_values: true
  chunk_size: 1000
```

---

## Usage

### Command Line

```bash
# Convert data to RDF
rdfmap convert --mapping config.yaml --output output.ttl

# With options
rdfmap convert \
  --mapping config.yaml \
  --output output.ttl \
  --limit 1000 \
  --format ttl

# Generate mapping from ontology and data
rdfmap generate \
  --ontology ontology.ttl \
  --data data.csv \
  --output mapping.yaml \
  --format inline
```

### Python API

```python
from pathlib import Path
from rdfmap.config.loader import load_mapping_config
from rdfmap.emitter.graph_builder import RDFGraphBuilder
from rdfmap.parsers.data_source import create_parser
from rdfmap.models.errors import ProcessingReport

# Load configuration
config = load_mapping_config("config.yaml")

# Get mapping and source
mapping_name = "Employee"
mapping = config.mappings[mapping_name]
source = config.sources[mapping.sources]

# Create parser and builder
parser = create_parser(Path(source.path))
report = ProcessingReport()
builder = RDFGraphBuilder(config, report)

# Process data
for chunk in parser.parse():
    builder.add_dataframe(chunk, mapping, mapping_name)

# Export RDF
builder.graph.serialize("output.ttl", format="turtle")
print(f"Generated {len(builder.graph)} triples")
```

---

## Configuration Reference

### Sources

Define data sources (files, databases, APIs):

```yaml
sources:
  # CSV file
  csv_data:
    path: data.csv
    format: csv
  
  # JSON with iterator
  json_data:
    path: data.json
    format: json
    iterator: $.records[*]  # JSONPath
  
  # XML with iterator
  xml_data:
    path: data.xml
    format: xml
    iterator: //record  # XPath
```

### Mappings

Define how to transform sources to RDF:

```yaml
mappings:
  EntityName:
    sources: source_name
    
    subject:
      class: ex:Entity  # Can be list: [ex:Entity, owl:NamedIndividual]
      iri_template: "{base_iri}entity/{id}"
    
    properties:
      column_name:
        predicate: ex:property
        datatype: xsd:string
        transform: to_upper  # Optional
        required: false
        language: en  # For string literals
    
    relationships:
      rel_name:
        predicate: ex:relatesTo
        object:
          class: ex:RelatedEntity
          iri_template: "{base_iri}related/{related_id}"
          properties: {...}
```

### Options

Configure processing behavior:

```yaml
options:
  output_format: ttl  # ttl, nt, xml, jsonld
  on_error: report  # report, skip, fail
  skip_empty_values: true
  chunk_size: 1000
  aggregate_duplicates: true
```

---

## Data Formats Supported

### CSV / TSV
```yaml
sources:
  data:
    path: data.csv
    format: csv
```

### JSON (Nested)
```yaml
sources:
  data:
    path: data.json
    format: json
    iterator: $.items[*]  # JSONPath for nested data
```

### XML (Hierarchical)
```yaml
sources:
  data:
    path: data.xml
    format: xml
    iterator: //record  # XPath for nested data
```

### Excel
```yaml
sources:
  data:
    path: data.xlsx
    format: xlsx
```

---

## Transformations

Built-in transforms:

- `to_integer` - Convert to integer
- `to_decimal` - Convert to decimal
- `to_date` - Parse date (YYYY-MM-DD)
- `to_datetime` - Parse datetime
- `to_upper` / `to_lower` - Case conversion
- `trim` - Strip whitespace

Example:
```yaml
properties:
  BirthDate:
    predicate: ex:birthDate
    datatype: xsd:date
    transform: to_date
```

---

## RML Compatibility

v3 configs are compatible with standard RML/YARRRML:

### Load RML directly
```bash
rdfmap convert --mapping mapping.rml.ttl --output output.ttl
```

### Load YARRRML
```bash
rdfmap convert --mapping mapping.yarrrml.yaml --output output.ttl
```

### Generate RML/YARRRML
```bash
# Generate RML (Turtle)
rdfmap generate ... --format rml/ttl

# Generate YARRRML
rdfmap generate ... --format yarrrml
```

---

## Migration from v2

### Key Changes

| v2 | v3 | Reason |
|----|----|----|
| `sheets` | `sources` + `mappings` | Universal, not spreadsheet-specific |
| `sheet.row_resource` | `mapping.subject` | RML standard |
| `property.as` | `property.predicate` | RML terminology |
| `sheet.objects` | `mapping.relationships` | Clearer semantics |
| `defaults.base_iri` | `base_iri` (root) | Simplified |

### Example Migration

**Before (v2)**:
```yaml
defaults:
  base_iri: http://example.org/

sheets:
  - name: people
    source: data.csv
    row_resource:
      class: ex:Person
      iri_template: "..."
    columns:
      Name: {as: ex:name}
    objects:
      company: {...}
```

**After (v3)**:
```yaml
base_iri: http://example.org/

sources:
  people_data:
    path: data.csv
    format: csv

mappings:
  Person:
    sources: people_data
    subject:
      class: ex:Person
      iri_template: "..."
    properties:
      Name: {predicate: ex:name}
    relationships:
      company: {...}
```

---

## Examples

See `examples/` directory for complete working examples:

- `examples/mortgage/` - Complete mortgage loan example
  - CSV data with nested entities
  - Full ontology
  - SHACL validation shapes
  - AI-generated mappings

---

## Documentation

- **Full Documentation**: See `docs/`
- **Configuration Guide**: `CONFIGURATION_FINAL_DECISION.md`
- **Migration Guide**: Coming in v0.4.0

---

## Support

- **Issues**: https://github.com/yourusername/rdfmap/issues
- **PyPI**: https://pypi.org/project/semantic-rdf-mapper/

---

**RDFMap v3** - Universal Data Mapping to RDF 🚀

