# CLI Improvements Summary

## Overview
Updated the CLI to provide clearer, more intuitive flags and expanded format support for ontologies.

## Changes Made

### 1. Improved Output Flags

**Before:**
```bash
rdfmap convert --mapping config.yaml --out ttl --out output.ttl
```
- Used double `--out` flag (confusing)
- First `--out` specified format
- Second `--out` specified path

**After:**
```bash
rdfmap convert --mapping config.yaml --format ttl --output output.ttl
# Or with short flags:
rdfmap convert --mapping config.yaml -f ttl -o output.ttl
```
- Separate `--format/-f` for output format
- Separate `--output/-o` for file path
- Much clearer and more intuitive

### 2. Expanded Ontology Format Support

**Before:**
- Documentation only mentioned TTL format
- Unclear if other formats were supported

**After:**
- Help text explicitly mentions: "supports TTL, RDF/XML, JSON-LD, N-Triples, etc."
- RDFLib auto-detection handles 16+ formats:
  - `.ttl` - Turtle
  - `.rdf` - RDF/XML
  - `.jsonld` - JSON-LD
  - `.nt` - N-Triples
  - `.n3` - Notation3
  - `.trig` - TriG
  - `.trix` - TriX
  - And more...

### 3. Bug Fixes

**Issue:** When using `--ontology` without `--validate`, the code tried to access `validation_report.conforms` when `validation_report` was None, causing an AttributeError.

**Fix:** Updated the exit code logic to only check SHACL validation results when the `--validate` flag was used:
```python
# Exit with error code if SHACL validation failed
if validate_flag and validation_report and not validation_report.conforms:
    console.print("[red]Validation failed[/red]")
    raise typer.Exit(code=1)
```

Also moved the display of SHACL validation results to only show when validation was actually performed.

## Updated Help Text

```
Usage: python -m rdfmap convert [OPTIONS]

Options:
  * --mapping   -m      FILE     Path to mapping configuration file (YAML/JSON) [required]
    --ontology          FILE     Path to ontology file (supports TTL, RDF/XML, JSON-LD, N-Triples, etc.)
    --format    -f      TEXT     Output format: ttl, xml, jsonld, nt (default: ttl)
    --output    -o      FILE     Output file path
    --validate                   Run SHACL validation after conversion
    --report            FILE     Path to write validation report (JSON)
    --limit             INTEGER  Process only first N rows (for testing)
    --dry-run                    Parse and validate without writing output
    --verbose   -v               Enable detailed logging
    --log               FILE     Write log to file
    --help                       Show this message and exit.
```

## Examples

### Basic Conversion
```bash
rdfmap convert \
  --mapping config.yaml \
  --format ttl \
  --output output.ttl
```

### With RDF/XML Ontology
```bash
rdfmap convert \
  --mapping config.yaml \
  --ontology ontology.rdf \
  --format xml \
  --output output.rdf
```

### Full Validation Stack
```bash
rdfmap convert \
  --mapping config.yaml \
  --ontology ontology.ttl \
  --format ttl \
  --output output.ttl \
  --validate \
  --report validation.json \
  --verbose
```

### Multiple Formats
```bash
# Turtle
rdfmap convert -m config.yaml -f ttl -o output.ttl

# RDF/XML
rdfmap convert -m config.yaml -f xml -o output.rdf

# JSON-LD
rdfmap convert -m config.yaml -f jsonld -o output.jsonld

# N-Triples
rdfmap convert -m config.yaml -f nt -o output.nt
```

## Testing

All scenarios tested successfully:
- ✅ Basic conversion without validation
- ✅ Conversion with SHACL validation (`--validate`)
- ✅ Conversion with ontology validation (`--ontology`)
- ✅ Conversion with both SHACL and ontology validation
- ✅ RDF/XML ontology input (`.rdf` file)
- ✅ Multiple output formats (TTL, RDF/XML, JSON-LD)
- ✅ All 15 validation tests still passing

## Documentation Updates

Updated the following files to reflect new CLI syntax:
- ✅ `README.md` - Main documentation
- ✅ `QUICKSTART.md` - Quick start guide
- ✅ `WALKTHROUGH.md` - Detailed walkthrough
- ✅ `examples/mortgage/README.md` - Mortgage example
- ✅ `docs/VALIDATION_GUARDRAILS.md` - Validation documentation

## Benefits

1. **Clarity**: Separate flags for format and output path are much clearer
2. **Consistency**: Follows common CLI patterns (e.g., `-f` for format, `-o` for output)
3. **Flexibility**: Short flags (`-f`, `-o`) for quick usage
4. **Transparency**: Help text explicitly documents format support
5. **Robustness**: Fixed edge case bug in validation exit logic
