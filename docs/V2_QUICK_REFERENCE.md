# v2 Configuration Quick Reference

## Generate Commands

```bash
# INLINE (recommended - everything in one file)
rdfmap generate -ont ont.ttl -d data.csv -f inline -o config.yaml

# EXTERNAL RML TURTLE (standards-compliant)
rdfmap generate -ont ont.ttl -d data.csv -f rml/ttl -o config.yaml

# EXTERNAL RML RDF/XML (XML tools)
rdfmap generate -ont ont.ttl -d data.csv -f rml/xml -o config.yaml

# EXTERNAL YARRRML (human-friendly)
rdfmap generate -ont ont.ttl -d data.csv -f yarrrml -o config.yaml
```

## v2 Structure

```yaml
# ═══════════════════════════════════════
# Pipeline Configuration
# ═══════════════════════════════════════
validation:
  shacl:
    enabled: true
    shapes_file: shapes.ttl

options:
  on_error: "report"
  chunk_size: 1000

imports:
  - ontology.ttl

# ═══════════════════════════════════════
# Mapping Definition
# ═══════════════════════════════════════
mapping:
  namespaces:
    xsd: http://www.w3.org/2001/XMLSchema#
    ex: https://example.com/#
  
  base_iri: http://example.org/
  
  # INLINE MODE
  sources:
    - name: data
      file: data.csv
      format: csv
      entity:
        class: ex:Entity
        iri_template: "{base_iri}entity/{ID}"
      properties:
        Name:
          predicate: ex:name
          datatype: xsd:string
      relationships:
        - predicate: ex:relatedTo
          class: ex:Related
          iri_template: "{base_iri}related/{RelID}"
  
  # OR EXTERNAL MODE
  file: mapping.rml.ttl
```

## Terminology Changes

| Old v1 | New v2 | Usage |
|--------|--------|-------|
| `sheets` | `sources` | `mapping.sources:` |
| `source` (field) | `file` | `sources[].file:` |
| `row_resource` | `entity` | `sources[].entity:` |
| `columns` | `properties` | `sources[].properties:` |
| `as` | `predicate` | `properties[].predicate:` |
| `objects` | `relationships` | `sources[].relationships:` |
| `defaults.base_iri` | `base_iri` | `mapping.base_iri:` |
| `namespaces` (top) | `namespaces` | `mapping.namespaces:` |
| `mapping_file` | `file` | `mapping.file:` |

## Convert Command

```bash
# Works with both v1 and v2
rdfmap convert --mapping config.yaml --output data.ttl
```

## Examples

- `examples/mortgage/config/v2_inline.yaml` - Inline mapping
- `examples/mortgage/config/v2_external.yaml` - External reference

## Documentation

- `docs/CONFIG_V2_IMPLEMENTATION_COMPLETE.md` - Full implementation details
- `docs/CONFIG_COMPARISON.md` - Side-by-side v1 vs v2
- `docs/CONFIG_REFACTORING_PLAN.md` - Technical design

