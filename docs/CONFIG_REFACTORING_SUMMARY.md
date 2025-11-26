# Configuration Refactoring - Quick Summary

**Date**: November 24, 2025  
**Priority**: HIGH - Better UX and consistency

---

## The Problem

Current config structure is inconsistent:

```yaml
# ❌ Scattered and confusing
namespaces: ...      # RML concept at top
defaults:
  base_iri: ...      # RML concept nested oddly  
sheets: ...          # Wrong term for JSON/XML
validation: ...      # Pipeline config mixed in
```

**Issues**:
- RML concepts scattered across levels
- "sheets" doesn't work for JSON/XML
- No clear separation between pipeline config and mapping
- "as", "row_resource", "columns" - unclear terminology

---

## The Solution

Clean two-section structure:

```yaml
# ═══════════════════════════════════════════════
# Pipeline Configuration (How to execute)
# ═══════════════════════════════════════════════
validation:
  shacl: {...}

options:
  on_error: "report"

# ═══════════════════════════════════════════════
# Mapping Definition (What to transform)  
# ═══════════════════════════════════════════════
mapping:
  namespaces: {...}
  base_iri: http://example.org/
  
  sources:              # Not "sheets"
    - name: loans
      file: data.csv    # Not "source"
      format: csv
      
      entity:           # Not "row_resource"
        class: ex:Loan
        iri_template: "{base_iri}loan/{ID}"
      
      properties:       # Not "columns"
        Name:
          predicate: ex:name    # Not "as"
          datatype: xsd:string
      
      relationships:    # Not "objects"
        - predicate: ex:hasBorrower
          class: ex:Borrower
```

---

## Key Improvements

### 1. Clear Separation
- **Pipeline config** = validation, options, imports
- **Mapping definition** = namespaces, sources, properties

### 2. Better Terminology
- `sources` not `sheets` (works for JSON/XML/DB)
- `entity` not `row_resource` (more semantic)
- `properties` not `columns` (format-agnostic)
- `predicate` not `as` (RML terminology)
- `relationships` not `objects` (clearer)

### 3. RML Alignment
All mapping concepts under `mapping:` mirror RML structure

### 4. External Reference
```yaml
validation: {...}
options: {...}

mapping:
  file: map.rml.ttl    # Clean!
```

---

## Migration

### Backward Compatible
- Old structure still works
- Auto-migration in loader
- Deprecation warnings
- Remove in v1.0

### Timeline
- Week 1: Design finalization
- Week 2: Implementation
- Week 3: Testing & examples
- Week 4: Deprecation warnings

---

## Benefits

✅ **Clearer** - Two-section model is intuitive  
✅ **RML-aligned** - Easier to learn if you know RML  
✅ **Source-agnostic** - Works for CSV, JSON, XML, DB  
✅ **Extensible** - Easy to add new features  
✅ **Professional** - Better terminology

---

## Decision Needed

**Recommendation**: ✅ PROCEED

**Reason**: Pre-1.0 is the best time for breaking changes that improve UX

---

## Documents

- **[Refactoring Plan](./CONFIG_REFACTORING_PLAN.md)** - Full implementation details
- **[Structure Comparison](./CONFIG_COMPARISON.md)** - Side-by-side examples
- **[Current Status](./CONFIG_FORMAT_RESTORATION.md)** - What's implemented now

---

## Next Steps

1. **Approve** design
2. **Implement** new models with backward compatibility
3. **Update** examples and docs
4. **Test** migration path
5. **Deploy** with deprecation warnings

**Estimated Effort**: 2-3 weeks

**Impact**: Significantly better UX and consistency

