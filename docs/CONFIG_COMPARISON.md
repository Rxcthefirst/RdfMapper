# Configuration Structure Comparison

## Side-by-Side Comparison

### Current Structure (Problematic)

```yaml
# ❌ RML concepts scattered at top level
namespaces:
  xsd: http://www.w3.org/2001/XMLSchema#
  rdfs: http://www.w3.org/2000/01/rdf-schema#
  ex: https://example.com/mortgage#

# ❌ Awkward nesting
defaults:
  base_iri: http://example.org/

# ❌ Spreadsheet-centric terminology
sheets:
  - name: loans
    source: data/loans.csv              # ❌ "source" ambiguous
    
    # ❌ "row_resource" awkward
    row_resource:
      class: ex:MortgageLoan
      iri_template: "{base_iri}loan/{LoanID}"
    
    # ❌ "columns" implies tabular only
    columns:
      LoanID:
        as: ex:loanNumber                # ❌ "as" unclear
        datatype: xsd:string
      
      Principal:
        as: ex:principalAmount
        datatype: xsd:decimal
    
    # ❌ "objects" vague
    objects:
      borrower:
        predicate: ex:hasBorrower
        class: ex:Borrower
        iri_template: "{base_iri}borrower/{BorrowerID}"

# ✅ Pipeline config (good!)
validation:
  shacl:
    enabled: true
    shapes_file: shapes/mortgage_shapes.ttl

options:
  on_error: "report"
  skip_empty_values: true
  chunk_size: 1000
```

### Proposed Structure (Clean)

```yaml
# ═══════════════════════════════════════════════════════════
# SECTION 1: Pipeline Configuration (RDFMap Features)
# ═══════════════════════════════════════════════════════════

validation:
  shacl:
    enabled: true
    shapes_file: shapes/mortgage_shapes.ttl
    inference: none

options:
  on_error: "report"
  skip_empty_values: true
  chunk_size: 1000
  aggregate_duplicates: true

imports:
  - ontology/mortgage_ontology.ttl

# ═══════════════════════════════════════════════════════════
# SECTION 2: Mapping Definition (RML-Compatible)
# ═══════════════════════════════════════════════════════════

mapping:
  # ✅ All RML concepts grouped together
  namespaces:
    xsd: http://www.w3.org/2001/XMLSchema#
    rdfs: http://www.w3.org/2000/01/rdf-schema#
    ex: https://example.com/mortgage#
  
  # ✅ No awkward nesting
  base_iri: http://example.org/
  
  # ✅ Source-agnostic terminology
  sources:
    - name: loans
      file: data/loans.csv              # ✅ "file" clear
      format: csv
      
      # ✅ "entity" semantic and clear
      entity:
        class: ex:MortgageLoan
        iri_template: "{base_iri}loan/{LoanID}"
      
      # ✅ "properties" works for any format
      properties:
        LoanID:
          predicate: ex:loanNumber      # ✅ "predicate" RML term
          datatype: xsd:string
        
        Principal:
          predicate: ex:principalAmount
          datatype: xsd:decimal
      
      # ✅ "relationships" clear intent
      relationships:
        - predicate: ex:hasBorrower
          class: ex:Borrower
          iri_template: "{base_iri}borrower/{BorrowerID}"
          properties:
            BorrowerName:
              predicate: ex:name
              datatype: xsd:string
```

---

## Key Improvements

### 1. Clear Two-Section Structure

**Old**: Mixed pipeline and mapping config
```yaml
namespaces: ...  # mapping
defaults: ...    # mapping
sheets: ...      # mapping
validation: ...  # pipeline
options: ...     # pipeline
```

**New**: Clean separation
```yaml
# Pipeline Configuration
validation: ...
options: ...

# Mapping Definition
mapping:
  namespaces: ...
  base_iri: ...
  sources: ...
```

### 2. RML Alignment

**Old**: Proprietary structure
```yaml
namespaces:      # Top-level
defaults:
  base_iri:      # Nested oddly
sheets:          # Non-RML term
  columns:       # Non-RML term
```

**New**: RML-aligned
```yaml
mapping:
  namespaces:    # RML: prefixes
  base_iri:      # RML: base
  sources:       # RML: sources
    properties:  # RML: predicateObjectMap
```

### 3. Source-Agnostic Terminology

**Old**: Spreadsheet assumptions
```yaml
sheets:          # ❌ Implies spreadsheets
  - source:      # ❌ Ambiguous
    row_resource # ❌ Implies rows
    columns:     # ❌ Implies columns
```

**New**: Format-neutral
```yaml
sources:         # ✅ Works for any format
  - file:        # ✅ Clear file reference
    entity:      # ✅ Semantic
    properties:  # ✅ Format-agnostic
```

### 4. Clearer Property Mapping

**Old**:
```yaml
columns:
  Name:
    as: ex:name              # ❌ "as" unclear
    datatype: xsd:string
```

**New**:
```yaml
properties:
  Name:
    predicate: ex:name       # ✅ RML terminology
    datatype: xsd:string
```

---

## Format Comparison

### CSV Example

**Old**:
```yaml
sheets:                      # ❌ OK for CSV
  - name: data
    source: file.csv
    row_resource: ...        # ✅ Makes sense
    columns: ...             # ✅ Makes sense
```

**New**:
```yaml
mapping:
  sources:                   # ✅ Better
    - name: data
      file: file.csv
      entity: ...            # ✅ Clearer
      properties: ...        # ✅ Semantic
```

### JSON Example

**Old**:
```yaml
sheets:                      # ❌ Weird for JSON!
  - name: api_data
    source: data.json
    row_resource: ...        # ❌ JSON has no "rows"
    columns: ...             # ❌ JSON has no "columns"
```

**New**:
```yaml
mapping:
  sources:                   # ✅ Natural
    - name: api_data
      file: data.json
      entity: ...            # ✅ Makes sense
      properties: ...        # ✅ Works perfectly
```

### XML Example

**Old**:
```yaml
sheets:                      # ❌ Very weird for XML!
  - name: xml_data
    source: data.xml
    row_resource: ...        # ❌ XML has no "rows"
    columns: ...             # ❌ XML has no "columns"
```

**New**:
```yaml
mapping:
  sources:                   # ✅ Perfect
    - name: xml_data
      file: data.xml
      entity: ...            # ✅ Natural
      properties: ...        # ✅ Semantic
```

---

## External Reference Comparison

### Old Structure

```yaml
# ❌ Mapping concepts mixed with pipeline
namespaces:
  xsd: ...

defaults:
  base_iri: ...

# Reference
mapping_file: map.rml.ttl

# Pipeline config
validation: ...
options: ...
```

### New Structure

```yaml
# ✅ Clean pipeline section
validation: ...
options: ...

# ✅ All mapping under one section
mapping:
  file: map.rml.ttl
```

---

## Migration Examples

### Simple CSV Mapping

**Before**:
```yaml
namespaces:
  xsd: http://www.w3.org/2001/XMLSchema#
  ex: https://example.com/#

defaults:
  base_iri: http://example.org/

sheets:
  - name: people
    source: people.csv
    row_resource:
      class: ex:Person
      iri_template: "{base_iri}person/{ID}"
    columns:
      Name:
        as: ex:name
        datatype: xsd:string
      Age:
        as: ex:age
        datatype: xsd:integer

options:
  on_error: "report"
```

**After**:
```yaml
options:
  on_error: "report"

mapping:
  namespaces:
    xsd: http://www.w3.org/2001/XMLSchema#
    ex: https://example.com/#
  
  base_iri: http://example.org/
  
  sources:
    - name: people
      file: people.csv
      format: csv
      
      entity:
        class: ex:Person
        iri_template: "{base_iri}person/{ID}"
      
      properties:
        Name:
          predicate: ex:name
          datatype: xsd:string
        Age:
          predicate: ex:age
          datatype: xsd:integer
```

### With Relationships

**Before**:
```yaml
sheets:
  - name: loans
    source: loans.csv
    row_resource:
      class: ex:Loan
      iri_template: "{base_iri}loan/{ID}"
    columns:
      Amount:
        as: ex:amount
        datatype: xsd:decimal
    objects:
      borrower:
        predicate: ex:hasBorrower
        class: ex:Borrower
        iri_template: "{base_iri}borrower/{BorrowerID}"
```

**After**:
```yaml
mapping:
  sources:
    - name: loans
      file: loans.csv
      format: csv
      
      entity:
        class: ex:Loan
        iri_template: "{base_iri}loan/{ID}"
      
      properties:
        Amount:
          predicate: ex:amount
          datatype: xsd:decimal
      
      relationships:
        - predicate: ex:hasBorrower
          class: ex:Borrower
          iri_template: "{base_iri}borrower/{BorrowerID}"
```

---

## Benefits Summary

| Aspect | Old | New | Benefit |
|--------|-----|-----|---------|
| **Structure** | Mixed | Separated | Clearer mental model |
| **Terminology** | Spreadsheet-centric | Source-agnostic | Works for all formats |
| **RML Alignment** | Scattered | Grouped | Easier RML translation |
| **Nesting** | Inconsistent | Logical | Better organization |
| **Clarity** | `as`, `row_resource` | `predicate`, `entity` | More semantic |
| **Extensibility** | Limited | Clean | Easy to add features |

---

## User Experience Impact

### Learning Curve

**Old**: "Where do I put this?"
- Is `base_iri` top-level or nested?
- Why is `namespaces` separate from `sheets`?
- When do I use `columns` vs `objects`?

**New**: "Clear two-section model"
- Pipeline config = how to execute
- Mapping = what to transform
- Everything RML-related in `mapping:`

### Cross-Tool Compatibility

**Old**: "How do I convert to RML?"
- Need to understand proprietary structure
- Mapping concepts scattered
- Not obvious what maps to RML

**New**: "Direct RML mapping"
- `mapping:` section maps 1:1 to RML concepts
- Easy to generate RML from this
- Easy to understand for RML users

---

## Recommendation

✅ **PROCEED WITH REFACTORING**

**Reasons**:
1. Better user experience
2. RML alignment
3. Source-agnostic (future-proof)
4. Clearer structure
5. Pre-1.0 is the right time

**Timeline**: 2-3 weeks with backward compatibility

