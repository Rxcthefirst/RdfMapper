# Configuration Structure Refactoring Plan

**Date**: November 24, 2025  
**Status**: 🟢 IMPLEMENTATION IN PROGRESS  
**Priority**: HIGH - Better UX and consistency  
**Approval**: ✅ User approved - proceeding with implementation

---

## Problem Analysis

### Current Structure Issues

#### Issue 1: Inconsistent Grouping
```yaml
# Current - INCONSISTENT
namespaces:          # RML concept, top-level
  xsd: ...
defaults:            # RML concept, nested oddly
  base_iri: ...
sheets:              # Internal term, top-level
  - name: ...
validation:          # Pipeline config, top-level
  shacl: ...
options:             # Pipeline config, top-level
  on_error: ...
```

**Problems**:
- RML concepts (`namespaces`, `base_iri`) scattered
- Pipeline config (`validation`, `options`) mixed with mapping
- No clear separation of concerns

#### Issue 2: Wrong Terminology
- **`sheets`** - Too spreadsheet-centric
  - Doesn't fit JSON, XML, database sources
  - Not RML terminology
  - Should be: `sources` or `mappings`

#### Issue 3: Awkward Nesting
- `defaults.base_iri` - Why nested under "defaults"?
- In RML/YARRRML: `base:` is top-level in mapping section

---

## Proposed Solution

### Clean Two-Section Structure

```yaml
# ═══════════════════════════════════════════════════════════
# SECTION 1: Pipeline Configuration (RDFMap-specific)
# ═══════════════════════════════════════════════════════════

validation:
  shacl:
    enabled: true
    shapes_file: shapes/shapes.ttl
    inference: none

options:
  on_error: "report"           # or "fail-fast"
  skip_empty_values: true
  chunk_size: 1000
  aggregate_duplicates: true
  output_format: ttl

imports:
  - ontology/main.ttl
  - ontology/extensions.ttl

# ═══════════════════════════════════════════════════════════
# SECTION 2: Mapping Definition (RML-compatible)
# ═══════════════════════════════════════════════════════════

mapping:
  # RML standard concepts grouped together
  namespaces:
    xsd: http://www.w3.org/2001/XMLSchema#
    ex: https://example.com/#
  
  base_iri: http://example.org/
  
  # Data sources with their mappings
  sources:
    - name: loans
      file: data/loans.csv
      format: csv
      
      # Entity mapping
      entity:
        class: ex:MortgageLoan
        iri_template: "{base_iri}loan/{LoanID}"
      
      # Property mappings
      properties:
        LoanID:
          predicate: ex:loanNumber
          datatype: xsd:string
        Principal:
          predicate: ex:principalAmount
          datatype: xsd:decimal
      
      # Relationships
      relationships:
        - predicate: ex:hasBorrower
          class: ex:Borrower
          iri_template: "{base_iri}borrower/{BorrowerID}"
          properties:
            BorrowerName:
              predicate: ex:name
              datatype: xsd:string
```

### External Reference Mode

```yaml
# Pipeline configuration
validation:
  shacl:
    enabled: true
    shapes_file: shapes.ttl

options:
  on_error: "report"

# Reference external RML/YARRRML
mapping:
  file: generated_mapping.rml.ttl
```

---

## Design Principles

### 1. Clear Separation of Concerns

| Section | Purpose | Scope |
|---------|---------|-------|
| **Pipeline Config** | How to execute | RDFMap-specific features |
| **Mapping Definition** | What to map | RML-compatible structure |

### 2. RML Alignment

Everything under `mapping:` should align with RML/YARRRML concepts:
- ✅ `namespaces` (RML: prefixes)
- ✅ `base_iri` (RML: base)
- ✅ `sources` (RML: sources)
- ✅ `entity.class` (RML: rr:class)
- ✅ `entity.iri_template` (RML: rr:template)
- ✅ `properties` (RML: predicateObjectMap)

### 3. Source-Agnostic Terminology

- ❌ `sheets` - implies spreadsheets only
- ✅ `sources` - works for CSV, JSON, XML, DB, API

### 4. Flat Where Possible

- ❌ `defaults.base_iri` - unnecessary nesting
- ✅ `mapping.base_iri` - direct and clear

---

## Migration Path

### Phase 1: Add New Structure (Backward Compatible)

**Support both old and new simultaneously**:

```python
class MappingConfig(BaseModel):
    # New structure (preferred)
    validation: Optional[ValidationConfig] = None
    options: ProcessingOptions = Field(default_factory=ProcessingOptions)
    imports: Optional[List[str]] = None
    mapping: Optional[MappingDefinition] = None
    
    # Old structure (deprecated but supported)
    namespaces: Optional[Dict[str, str]] = None
    defaults: Optional[DefaultsConfig] = None
    sheets: Optional[List[SheetMapping]] = None
    mapping_file: Optional[str] = None
    
    @model_validator(mode="after")
    def migrate_old_structure(self):
        # Auto-migrate old to new
        if self.namespaces and not self.mapping:
            # Old structure detected, convert to new
            ...
```

### Phase 2: Update Examples

Update all example files to new structure:
- `examples/mortgage/config/internal_inline.yaml`
- `examples/mortgage/config/external_mapping.yaml`
- Documentation examples

### Phase 3: Deprecation Notice

Add warnings for old structure:
```python
if config uses old structure:
    logger.warning("Old config structure detected. Please migrate to new structure. "
                  "See docs/CONFIGURATION_MIGRATION.md")
```

### Phase 4: Remove Old Structure (v1.0)

Eventually remove support for old structure.

---

## Implementation Details

### New Model Structure

```python
# models/mapping.py

class MappingDefinition(BaseModel):
    """RML-compatible mapping definition."""
    
    # Option 1: Inline mapping
    namespaces: Optional[Dict[str, str]] = None
    base_iri: Optional[str] = None
    sources: Optional[List[SourceMapping]] = None
    
    # Option 2: External reference
    file: Optional[str] = None
    
    @model_validator(mode="after")
    def validate_inline_or_file(self):
        has_inline = bool(self.sources)
        has_file = bool(self.file)
        
        if not has_inline and not has_file:
            raise ValueError("mapping must have either 'sources' (inline) or 'file' (external)")
        if has_inline and has_file:
            raise ValueError("mapping cannot have both 'sources' and 'file'")


class SourceMapping(BaseModel):
    """Mapping for a single data source."""
    
    name: str
    file: str  # Previously 'source'
    format: str  # csv, json, xml, etc.
    
    entity: EntityMapping
    properties: Dict[str, PropertyMapping]
    relationships: Optional[List[RelationshipMapping]] = None


class EntityMapping(BaseModel):
    """Entity (subject) mapping."""
    
    class_: str = Field(alias="class")
    iri_template: str


class PropertyMapping(BaseModel):
    """Property (predicate-object) mapping."""
    
    predicate: str  # Previously 'as'
    datatype: Optional[str] = None
    transform: Optional[str] = None
    required: bool = False
    language: Optional[str] = None


class RelationshipMapping(BaseModel):
    """Relationship (object property) mapping."""
    
    predicate: str
    class_: str = Field(alias="class")
    iri_template: str
    properties: Dict[str, PropertyMapping]


class MappingConfig(BaseModel):
    """Root configuration with pipeline + mapping."""
    
    # Pipeline configuration (RDFMap-specific)
    validation: Optional[ValidationConfig] = None
    options: ProcessingOptions = Field(default_factory=ProcessingOptions)
    imports: Optional[List[str]] = None
    
    # Mapping definition (RML-compatible)
    mapping: MappingDefinition
```

---

## Comparison: Old vs New

### Old Structure (Current)

```yaml
namespaces:
  xsd: http://www.w3.org/2001/XMLSchema#

defaults:
  base_iri: http://example.org/

sheets:
  - name: loans
    source: data.csv
    row_resource:
      class: ex:Loan
      iri_template: "{base_iri}loan/{ID}"
    columns:
      Name:
        as: ex:name
        datatype: xsd:string

validation:
  shacl: {...}

options:
  on_error: "report"
```

**Issues**:
- ❌ Scattered RML concepts
- ❌ `sheets` terminology
- ❌ `row_resource` awkward
- ❌ `columns` implies tabular only
- ❌ `as` unclear (predicate would be better)

### New Structure (Proposed)

```yaml
# Pipeline config (clear separation)
validation:
  shacl: {...}

options:
  on_error: "report"

# Mapping definition (RML-aligned)
mapping:
  namespaces:
    xsd: http://www.w3.org/2001/XMLSchema#
  
  base_iri: http://example.org/
  
  sources:
    - name: loans
      file: data.csv
      format: csv
      
      entity:
        class: ex:Loan
        iri_template: "{base_iri}loan/{ID}"
      
      properties:
        Name:
          predicate: ex:name
          datatype: xsd:string
```

**Benefits**:
- ✅ Clear two-section structure
- ✅ `sources` works for any format
- ✅ `entity` clearer than `row_resource`
- ✅ `properties` more semantic than `columns`
- ✅ `predicate` clearer than `as`
- ✅ All RML concepts grouped under `mapping`

---

## Benefits

### For Users

1. **Clearer Mental Model**
   - Pipeline config = "how to run"
   - Mapping = "what to map"

2. **Better Terminology**
   - `sources` not `sheets`
   - `entity` not `row_resource`
   - `properties` not `columns`
   - `predicate` not `as`

3. **RML Alignment**
   - Structure mirrors RML concepts
   - Easier to learn if you know RML
   - Natural translation to/from YARRRML

4. **Source-Agnostic**
   - Works equally well for CSV, JSON, XML, DB
   - No spreadsheet assumptions

### For Codebase

1. **Better Separation**
   - Pipeline logic separate from mapping logic
   - Easier to test independently

2. **Cleaner Models**
   - Each model has single responsibility
   - Better type hints

3. **Future Extensibility**
   - Easy to add new source types
   - Easy to add new pipeline features
   - Doesn't break mapping structure

---

## Terminology Changes

| Old | New | Reason |
|-----|-----|--------|
| `sheets` | `sources` | Source-agnostic |
| `source` (file) | `file` | Clearer (source is the whole thing) |
| `row_resource` | `entity` | More semantic |
| `columns` | `properties` | Not just columns anymore |
| `as` | `predicate` | RML terminology |
| `objects` | `relationships` | Clearer intent |
| `defaults.base_iri` | `mapping.base_iri` | Better grouping |
| `namespaces` (top) | `mapping.namespaces` | Part of mapping |
| `mapping_file` | `mapping.file` | Consistent nesting |

---

## Example Conversions

### CSV Example

**Old**:
```yaml
sheets:
  - name: data
    source: file.csv
    row_resource:
      class: ex:Entity
```

**New**:
```yaml
mapping:
  sources:
    - name: data
      file: file.csv
      format: csv
      entity:
        class: ex:Entity
```

### JSON Example

**Old** (awkward):
```yaml
sheets:  # Weird for JSON!
  - name: api_data
    source: data.json
    format: json
    iterator: "$.items[*]"
```

**New** (natural):
```yaml
mapping:
  sources:
    - name: api_data
      file: data.json
      format: json
      iterator: "$.items[*]"
```

### External Reference

**Old**:
```yaml
namespaces: {...}
defaults: {...}
mapping_file: map.rml.ttl
validation: {...}
```

**New** (cleaner):
```yaml
validation: {...}
options: {...}

mapping:
  file: map.rml.ttl
```

---

## Rollout Plan

### Week 1: Design & Review
- ✅ Document proposal (this doc)
- ⏳ Team review and feedback
- ⏳ Finalize design

### Week 2: Implementation
- ⏳ Create new models (`MappingDefinition`, `SourceMapping`, etc.)
- ⏳ Add backward compatibility layer
- ⏳ Update loader to support both structures
- ⏳ Add auto-migration logic

### Week 3: Testing & Examples
- ⏳ Update all examples
- ⏳ Update documentation
- ⏳ Add migration guide
- ⏳ Test backward compatibility

### Week 4: Deprecation
- ⏳ Add deprecation warnings
- ⏳ Update README
- ⏳ Announce in release notes

### Future: Removal (v1.0)
- ⏳ Remove old structure support
- ⏳ Clean up codebase

---

## Open Questions

1. **Timing**: Do we do this now or after other features?
2. **Breaking Change**: Can we justify it pre-1.0?
3. **Migration Tool**: Should we provide `rdfmap migrate-config`?
4. **Property vs Properties**: `properties:` or `property_mappings:`?
5. **Entity vs Subject**: `entity:` or `subject:` (RML uses subject)?

---

## Decision

**Status**: 🟡 PENDING USER APPROVAL

**Recommendation**: ✅ PROCEED
- Makes sense
- Better UX
- RML-aligned
- Pre-1.0 is best time for breaking changes

**Action Required**: User sign-off to proceed with implementation

---

**Next Steps**:
1. Get user approval
2. Start Phase 1 implementation
3. Create migration guide
4. Update examples

