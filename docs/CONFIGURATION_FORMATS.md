# Configuration Formats Guide

**Last Updated**: November 24, 2025

## Overview

RDFMap supports **three configuration approaches** to maximize flexibility while maintaining a consistent pipeline:

1. **Inline Mapping** - Everything in one config file (original internal format)
2. **External RML/YARRRML** - Reference separate standard RML mapping
3. **Direct RML** - Use RML directly without wrapper config

All three approaches support the same pipeline features (validation, options, etc.).

---

## Format 1: Inline Mapping (Internal Format)

**Use when**: You want everything in one file with full control

**Structure**:
```yaml
namespaces:          # Required: Prefix declarations
defaults:            # Required: Base IRI and defaults
sheets:              # Required: Inline mapping definitions
validation:          # Optional: SHACL validation
options:             # Optional: Processing options
imports:             # Optional: Ontology files
```

**Example**: [`examples/mortgage/config/internal_inline.yaml`](../examples/mortgage/config/internal_inline.yaml)

```yaml
namespaces:
  xsd: http://www.w3.org/2001/XMLSchema#
  rdfs: http://www.w3.org/2000/01/rdf-schema#
  ex: https://example.com/mortgage#

defaults:
  base_iri: http://example.org/

sheets:
  - name: loans
    source: ../data/loans.csv
    row_resource:
      class: ex:MortgageLoan
      iri_template: "{base_iri}mortgage_loan/{LoanID}"
    columns:
      LoanID:
        as: ex:loanNumber
        datatype: xsd:string
      Principal:
        as: ex:principalAmount
        datatype: xsd:integer

validation:
  shacl:
    enabled: true
    shapes_file: ../shapes/mortgage_shapes.ttl

options:
  on_error: "report"
  skip_empty_values: true
  aggregate_duplicates: true
```

**Convert**:
```bash
rdfmap convert --mapping internal_inline.yaml --output data.ttl
```

**✅ Pros**:
- Everything in one place
- Full pipeline configuration
- No external dependencies
- Easy to version control

**❌ Cons**:
- Proprietary format (not standard RML)
- Must regenerate if mapping changes
- Larger file size

---

## Format 2: External RML/YARRRML Reference

**Use when**: You have existing RML/YARRRML or want standards compliance

**Structure**:
```yaml
namespaces:          # Required: Prefix declarations
defaults:            # Required: Base IRI
mapping_file:        # Required: Path to RML or YARRRML
validation:          # Optional: SHACL validation
options:             # Optional: Processing options
imports:             # Optional: Ontology files
```

**Example**: [`examples/mortgage/config/external_mapping.yaml`](../examples/mortgage/config/external_mapping.yaml)

```yaml
namespaces:
  xsd: http://www.w3.org/2001/XMLSchema#
  ex: https://example.com/mortgage#

defaults:
  base_iri: http://example.org/

# Reference external mapping (RML or YARRRML)
mapping_file: ../output/standard.yaml  # YARRRML
# OR: mapping_file: generated_mapping.rml.ttl  # RML Turtle
# OR: mapping_file: generated_mapping.rml.rdf  # RML RDF/XML

validation:
  shacl:
    enabled: true
    shapes_file: ../shapes/mortgage_shapes.ttl

options:
  on_error: "report"
  chunk_size: 1000
  aggregate_duplicates: true
```

**Convert**:
```bash
rdfmap convert --mapping external_mapping.yaml --output data.ttl
```

**✅ Pros**:
- **Standards compliant**: RML/YARRRML unchanged
- **Reusable**: Same RML with different configs
- **Interoperable**: Works with RMLMapper, Morph-KGC, etc.
- **Separation of concerns**: Mapping logic vs execution config
- **Team collaboration**: Different team members work on mapping vs config

**❌ Cons**:
- Two files to manage
- Slightly more complex setup

**💡 Use Cases**:
1. **Existing RML**: You have RML from another tool, add rdfmap features
2. **Standards Compliance**: Need pure RML for tool-agnostic workflows
3. **Reusability**: Same mapping, different validation/options for dev/prod
4. **Migration**: Gradual migration from RMLMapper to rdfmap

---

## Format 3: Direct RML

**Use when**: You just want to use standard RML directly

**Structure**: Standard RML file (Turtle, RDF/XML, N-Triples)

**Example**:
```turtle
@prefix rr: <http://www.w3.org/ns/r2rml#> .
@prefix rml: <http://semweb.mmlab.be/ns/rml#> .
@prefix ql: <http://semweb.mmlab.be/ns/ql#> .
@prefix ex: <https://example.com/mortgage#> .

<#LoansMapping> a rr:TriplesMap ;
    rml:logicalSource [
        rml:source "examples/mortgage/data/loans.csv" ;
        rml:referenceFormulation ql:CSV
    ] ;
    rr:subjectMap [
        rr:template "http://example.org/mortgage_loan/{LoanID}" ;
        rr:class ex:MortgageLoan
    ] ;
    rr:predicateObjectMap [
        rr:predicate ex:loanNumber ;
        rr:objectMap [
            rml:reference "LoanID" ;
            rr:datatype xsd:string
        ]
    ] .
```

**Convert**:
```bash
rdfmap convert --mapping mapping.rml.ttl --output data.ttl
```

**✅ Pros**:
- Pure W3C standard
- Works with any RML tool
- Simple, single file

**❌ Cons**:
- No validation configuration
- No processing options
- No imports support
- Default error handling only

**💡 Use Cases**:
1. **Quick conversion**: Simple mapping, no special features needed
2. **Tool comparison**: Test same RML across multiple tools
3. **Interoperability**: Share mappings with others

---

## Feature Comparison

| Feature | Inline | External Reference | Direct RML |
|---------|--------|-------------------|------------|
| **Pipeline Configuration** | ✅ | ✅ | ❌ |
| SHACL Validation | ✅ | ✅ | ❌ |
| Processing Options | ✅ | ✅ | ❌ |
| Ontology Imports | ✅ | ✅ | ❌ |
| Error Handling Config | ✅ | ✅ | ❌ (default) |
| Chunk Size Control | ✅ | ✅ | ❌ (default: 1000) |
| **Standards Compliance** | ❌ | ✅ | ✅ |
| Pure RML/YARRRML | ❌ | ✅ | ✅ |
| Tool Interoperability | ❌ | ✅ (mapping file) | ✅ |
| **Ease of Use** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Single File | ✅ | ❌ (2 files) | ✅ |
| Setup Complexity | Low | Medium | Lowest |

---

## Decision Matrix

### Choose **Inline Mapping** if:
- ✅ You're starting fresh (no existing RML)
- ✅ You want all configuration in one file
- ✅ You need full pipeline features
- ✅ Standards compliance isn't critical
- ✅ You won't share mappings with other tools

### Choose **External Reference** if:
- ✅ You have existing RML/YARRRML files
- ✅ You need standards compliance
- ✅ You want to reuse mappings across tools
- ✅ You need different configs for dev/test/prod
- ✅ Team members need to work independently on mapping vs config
- ✅ You're migrating from another RML tool

### Choose **Direct RML** if:
- ✅ You have a simple, one-off conversion
- ✅ You don't need validation or special options
- ✅ You're testing/comparing RML tools
- ✅ You want maximum simplicity

---

## Migration Paths

### From RMLMapper to RDFMap

**Option A: Minimal Change (Direct RML)**
```bash
# Just use your existing RML file
rdfmap convert --mapping your_mapping.rml.ttl --output data.ttl
```

**Option B: Add RDFMap Features (External Reference)**
1. Keep your RML file as-is
2. Create a wrapper config:
```yaml
namespaces:
  xsd: http://www.w3.org/2001/XMLSchema#
defaults:
  base_iri: http://example.org/
mapping_file: your_mapping.rml.ttl
validation:
  shacl:
    enabled: true
    shapes_file: shapes.ttl
```
3. Convert: `rdfmap convert --mapping config.yaml --output data.ttl`

### From rdfmap v0.2 (Old Internal Format)

**Your old configs still work!** No changes needed.

If you want to use standard RML:
```bash
# Option 1: Generate RML from old config
rdfmap generate --ontology ont.ttl --data data.csv -f rml -o map.rml.ttl

# Option 2: Convert old config to external reference format
# (Create wrapper config pointing to generated RML)
```

---

## Path Resolution Rules

### Inline Mapping
- All paths resolved relative to **config file directory**
- Example: `config/mapping.yaml` with `source: ../data/file.csv`
  - Resolves to: `config/../data/file.csv` = `data/file.csv`

### External Reference
- `mapping_file` path resolved relative to **config file directory**
- Data source paths in RML resolved relative to **RML file directory**
- Example: `config/wrapper.yaml` references `output/map.yaml`
  - wrapper.yaml: `mapping_file: ../output/map.yaml` → `config/../output/map.yaml`
  - map.yaml: `source: ../data/file.csv` → `output/../data/file.csv` = `data/file.csv`

### Direct RML
- Data source paths resolved relative to **RML file directory**

---

## Examples

See working examples in:
- [`examples/mortgage/config/internal_inline.yaml`](../examples/mortgage/config/internal_inline.yaml)
- [`examples/mortgage/config/external_mapping.yaml`](../examples/mortgage/config/external_mapping.yaml)
- [`generated_mapping.rml.ttl`](../generated_mapping.rml.ttl) (direct RML)

Test them:
```bash
# Inline
rdfmap convert --mapping examples/mortgage/config/internal_inline.yaml --limit 5

# External reference
rdfmap convert --mapping examples/mortgage/config/external_mapping.yaml --limit 5

# Direct RML
rdfmap convert --mapping generated_mapping.rml.ttl --limit 5
```

---

## Best Practices

1. **Development**: Use external reference for flexibility
2. **Production**: Use inline for simplicity (everything in one file)
3. **Sharing**: Use direct RML or external reference for interoperability
4. **Testing**: Use direct RML for quick iterations
5. **Enterprise**: Use external reference for governance (separate mapping approval from config)

---

## Validation Rules

The configuration loader validates:
- ✅ Either `sheets` OR `mapping_file` must be present (not both, not neither)
- ✅ Referenced `mapping_file` must exist
- ✅ Data source files must exist
- ✅ SHACL shapes files must exist (if validation enabled)
- ✅ Namespaces include required prefixes (xsd)

---

## Related Documentation

- [RML Format Support](./RML_FORMATS_SUPPORT.md) - RML serialization formats
- [YARRRML Specification](https://rml.io/yarrrml/spec/) - YARRRML format details
- [RML Specification](https://rml.io/specs/rml/) - W3C RML standard

