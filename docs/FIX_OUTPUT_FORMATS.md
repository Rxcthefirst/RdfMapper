# Fixed: Output Format Configuration

**Date**: November 25, 2025  
**Issue**: XML and JSON-LD output formats ignored, always outputting TTL  
**Status**: ✅ **FIXED**

---

## 🎯 The Problem

When setting `output_format` in the config file, the conversion would always output Turtle (TTL) format regardless of the configured format.

**Example Config**:
```yaml
options:
  output_format: xml  # ← This was being ignored!
```

**Result**: Output file had Turtle syntax instead of XML/RDF syntax.

**Affected Formats**:
- ✅ TTL (worked)
- ✅ NT (worked via streaming)
- ❌ XML (ignored, outputted TTL)
- ❌ JSON-LD (ignored, outputted TTL)
- ❌ N3 (ignored, outputted TTL)

---

## 🔍 Root Cause

In `src/rdfmap/cli/main.py` at line 522, the output format was hardcoded:

```python
# WRONG:
output_format = format or "ttl"  # Only checks CLI flag, ignores config!
```

This meant:
1. If you used `--format` CLI flag → It worked
2. If you set `output_format` in config → **Ignored!**
3. Default was always TTL

Meanwhile, line 370 properly checked the config:
```python
# CORRECT (used earlier for streaming decision):
output_format = format or config.options.output_format or "ttl"
```

---

## ✅ The Fix

**File**: `src/rdfmap/cli/main.py` (line ~522)

**Before**:
```python
if not dry_run and output and not nt_context_manager:
    # Use provided format or default to ttl
    output_format = format or "ttl"  # ❌ Ignores config!
    
    console.print(f"[blue]Writing {output_format.upper()} to {output}...[/blue]")
    serialize_graph(graph, output_format, output)
```

**After**:
```python
if not dry_run and output and not nt_context_manager:
    # Use command-line format, config format, or default to ttl
    final_output_format = format or config.options.output_format or "ttl"  # ✅ Checks config!
    
    console.print(f"[blue]Writing {final_output_format.upper()} to {output}...[/blue]")
    serialize_graph(graph, final_output_format, output)
```

---

## 📊 Supported Formats

All RDF formats are now properly supported:

| Format | Config Value | CLI Flag | File Extension | Status |
|--------|--------------|----------|----------------|---------|
| **Turtle** | `ttl` or `turtle` | `--format ttl` | `.ttl` | ✅ Working |
| **RDF/XML** | `xml`, `rdf`, `rdfxml` | `--format xml` | `.xml`, `.rdf` | ✅ **FIXED** |
| **JSON-LD** | `jsonld`, `json-ld` | `--format jsonld` | `.jsonld` | ✅ **FIXED** |
| **N-Triples** | `nt`, `ntriples` | `--format nt` | `.nt` | ✅ Working |
| **N3** | `n3` | `--format n3` | `.n3` | ✅ **FIXED** |

---

## 🧪 Testing

### Test 1: XML Format

**Config**:
```yaml
options:
  output_format: xml

sheets:
  - name: loans
    source: data/loans.csv
    row_resource:
      class: ex:MortgageLoan
      iri_template: http://example.org/loan/{LoanID}
    columns:
      Principal:
        as: ex:principalAmount
        datatype: xsd:integer
```

**Command**:
```bash
rdfmap convert -m config.yaml -o output.xml --limit 5
```

**Result**: ✅ Outputs valid RDF/XML
```xml
<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF
   xmlns:ex="https://example.com/mortgage#"
   xmlns:owl="http://www.w3.org/2002/07/owl#"
   xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about="http://example.org/loan/L-1001">
    <rdf:type rdf:resource="http://www.w3.org/2002/07/owl#NamedIndividual"/>
    <rdf:type rdf:resource="https://example.com/mortgage#MortgageLoan"/>
    <ex:principalAmount rdf:datatype="http://www.w3.org/2001/XMLSchema#integer">250000</ex:principalAmount>
  </rdf:Description>
</rdf:RDF>
```

### Test 2: JSON-LD Format

**Config**:
```yaml
options:
  output_format: jsonld
```

**Command**:
```bash
rdfmap convert -m config.yaml -o output.jsonld --limit 5
```

**Result**: ✅ Outputs valid JSON-LD
```json
[
  {
    "@id": "http://example.org/loan/L-1001",
    "@type": [
      "https://example.com/mortgage#MortgageLoan",
      "http://www.w3.org/2002/07/owl#NamedIndividual"
    ],
    "https://example.com/mortgage#principalAmount": [
      {
        "@type": "http://www.w3.org/2001/XMLSchema#integer",
        "@value": 250000
      }
    ]
  }
]
```

### Test 3: CLI Override

**Config**: `output_format: xml`

**Command**:
```bash
rdfmap convert -m config.yaml -o output.ttl --format ttl
```

**Result**: ✅ CLI flag overrides config, outputs Turtle

---

## 🎯 Priority Order

The format is now determined with proper priority:

1. **CLI flag** (`--format xml`) - Highest priority
2. **Config file** (`output_format: xml`) - Medium priority
3. **Default** (`ttl`) - Lowest priority

```python
final_output_format = format or config.options.output_format or "ttl"
```

---

## 📝 Format Mappings

The `serialize_graph` function in `src/rdfmap/emitter/graph_builder.py` properly maps all format aliases:

```python
format_map = {
    "ttl": "turtle",
    "turtle": "turtle",
    "xml": "xml",
    "rdf": "xml",
    "rdfxml": "xml",
    "jsonld": "json-ld",
    "json-ld": "json-ld",
    "nt": "nt",
    "ntriples": "nt",
    "n3": "n3",
}
```

All these variations now work correctly!

---

## ✅ Verification

**Quick test all formats**:
```bash
# TTL (default)
rdfmap convert -m config.yaml -o out.ttl --format ttl

# XML
rdfmap convert -m config.yaml -o out.xml --format xml

# JSON-LD
rdfmap convert -m config.yaml -o out.jsonld --format jsonld

# N-Triples
rdfmap convert -m config.yaml -o out.nt --format nt

# N3
rdfmap convert -m config.yaml -o out.n3 --format n3
```

All formats now produce correct syntax! ✅

---

## 📚 Documentation

Users can now set their preferred output format in the config:

```yaml
options:
  output_format: xml  # Now works correctly!
  chunk_size: 1000
  aggregate_duplicates: true
```

Or override via CLI:
```bash
rdfmap convert -m config.yaml -o output.xml --format jsonld  # CLI wins
```

---

## 🎉 Result

**All RDF output formats now work correctly!**

- ✅ TTL/Turtle
- ✅ RDF/XML  
- ✅ JSON-LD
- ✅ N-Triples
- ✅ N3

Config file `output_format` is now properly respected, with CLI override support.

---

**Files Modified**:
1. ✅ `src/rdfmap/cli/main.py` - Fixed output format selection
2. ✅ `docs/FIX_OUTPUT_FORMATS.md` - This documentation

**Status**: ✅ **COMPLETE**

