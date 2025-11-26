# RDF/XML Format Support Summary

## Overview
We now support **RDF/XML format** for both reading and writing RML mappings, in addition to the existing Turtle format support.

## What was added

### 1. RML Generator (`rml_generator.py`)
- Added `format` parameter to `generate()` method
- Added `format` parameter to `generate_rml()` function
- Added `format` parameter to `internal_to_rml()` function
- Supports multiple serialization formats:
  - `turtle` / `ttl` (default) - Turtle format
  - `xml` / `rdf/xml` / `rdfxml` - RDF/XML format
  - `nt` / `ntriples` - N-Triples format
  - `n3` - Notation3 format  
  - `json-ld` / `jsonld` - JSON-LD format

### 2. RML Parser (`rml_parser.py`)
- Already supported reading multiple formats:
  - `.ttl` - Turtle
  - `.rdf`, `.xml` - RDF/XML  
  - `.nt` - N-Triples
  - `.n3` - Notation3

### 3. CLI (`cli/main.py`)
- Updated `generate` command to auto-detect RML serialization format from file extension
- Updated help text to document format options
- Examples added for RDF/XML generation

## Usage

### Generate RML in different formats

```bash
# Turtle format (default, recommended)
rdfmap generate --ontology ont.ttl --data data.csv -f rml -o map.rml.ttl

# RDF/XML format
rdfmap generate --ontology ont.ttl --data data.csv -f rml -o map.rml.rdf

# N-Triples format
rdfmap generate --ontology ont.ttl --data data.csv -f rml -o map.rml.nt

# JSON-LD format
rdfmap generate --ontology ont.ttl --data data.csv -f rml -o map.rml.jsonld
```

### Convert using RML in different formats

```bash
# Using Turtle RML
rdfmap convert --mapping map.rml.ttl --output data.ttl

# Using RDF/XML RML
rdfmap convert --mapping map.rml.rdf --output data.ttl

# Using N-Triples RML
rdfmap convert --mapping map.rml.nt --output data.ttl
```

## Testing

Tests verify:
1. ✅ RML can be generated in Turtle, RDF/XML, and N-Triples formats
2. ✅ All formats produce valid RDF (same number of triples)
3. ✅ Round-trip works: Generate RDF/XML → Parse it back → Use for conversion
4. ✅ Format auto-detection from file extension works

## Benefits

1. **Interoperability**: RDF/XML is widely supported by RDF tools
2. **Flexibility**: Users can choose their preferred serialization
3. **Standards compliance**: Supports multiple W3C RDF serializations
4. **Tool compatibility**: Can integrate with XML-based RDF pipelines

## Compatibility

- Fully backwards compatible - Turtle remains the default format
- The convert engine works with any format (format-agnostic parsing)
- File extension determines output format automatically

