# v3 Format Migration - Progress Tracker

**Started**: December 9, 2025  
**Status**: 🎉 PHASE 3 COMPLETE - ENGINE UPDATED!  
**Target**: Complete v3 migration

---

## ✅ Phase 1: Models & Examples (DONE)

- [x] Created `src/rdfmap/models/config_v3.py` with new models
- [x] Updated mortgage example to v3 format

---

## ✅ Phase 2: Parser & Loader Updates (DONE)

### 2.1 RML Parser ✅
- [x] Updated `rml_parser.py` to output v3 format
- [x] All 3 RML parser tests passing
  
### 2.2 Config Loader ✅
- [x] Updated `loader.py` to handle v3 format
- [x] Removed v1/v2 migration logic
- [x] v3 is the ONLY format

---

## ✅ Phase 3: Engine Updates (DONE)

### 3.1 Graph Builder ✅
- [x] Updated `graph_builder.py` for v3 format
  - Access `config.mappings` instead of `config.sheets`
  - Access `mapping.subject` instead of `sheet.row_resource`
  - Access `mapping.properties` with `predicate` field
  - Access `mapping.relationships` instead of `sheet.objects`
  - Created `_add_relationships` and `_add_single_relationship`
  - Removed legacy merged sheet code
  
- [x] **Verified working**: Successfully processes v3 configs end-to-end!

---

## ⏳ Phase 3: Engine Updates

### 3.1 Graph Builder
- [ ] Update `graph_builder.py`
  - Access `config.mappings` instead of `config.sheets`
  - Access `mapping.subject` instead of `sheet.row_resource`
  - Access `mapping.properties` (no change)
  - Access `mapping.relationships` instead of `sheet.objects`

### 3.2 Data Parser
- [ ] Update `data_source.py`
  - Handle `DataSource` model
  - Support iterators (JSONPath, XPath)

### 3.3 Emitters
- [ ] Verify emitters work with new structure
  - Should be minimal changes

---

## ⏳ Phase 4: Test Updates

### 4.1 Core Tests
- [ ] `test_rml_parser.py` - Update for v3 output
- [ ] `test_yarrrml_parser.py` - Update for v3 output  
- [ ] `test_mortgage_example.py` - Already using updated config
- [ ] `test_config_validation.py` - Update for v3 models

### 4.2 Integration Tests
- [ ] `test_generator_workflow.py`
- [ ] `test_phase2_integration.py`

### 4.3 Remove Old Tests
- [ ] Delete format_adapter tests (no longer needed)
- [ ] Remove v1/v2 compatibility tests

---

## ⏳ Phase 5: Documentation

- [ ] Update `README.md` with v3 examples
- [ ] Update `CHANGELOG.md` for v0.4.0
- [ ] Create migration guide (v2 → v3)
- [ ] Update example READMEs

---

## Breaking Changes Summary

### Terminology Changes
| Old (v2) | New (v3) | Reason |
|----------|----------|--------|
| `sheets` | `sources` + `mappings` | Universal, not spreadsheet-specific |
| `sheet.row_resource` | `mapping.subject` | RML standard terminology |
| `sheet.objects` | `mapping.relationships` | Clearer meaning |
| `property.as` | `property.predicate` | RML standard terminology |

### Structure Changes
```yaml
# OLD (v2)
sheets:
  - name: loans
    source: data.csv
    row_resource:
      class: ex:Loan
      iri_template: "..."
    properties:
      col1: {as: ex:prop1}
    objects:
      obj1: {...}

# NEW (v3)
sources:
  loans_data:
    path: data.csv
    format: csv

mappings:
  Loan:
    sources: loans_data
    subject:
      class: ex:Loan
      iri_template: "..."
    properties:
      col1: {predicate: ex:prop1}
    relationships:
      rel1: {...}
```

---

## Timeline Estimate

| Phase | Estimated Time | Status |
|-------|---------------|---------|
| 1. Models & Examples | 2 hours | ✅ DONE |
| 2. Parser Updates | 4 hours | 🔜 NEXT |
| 3. Engine Updates | 6 hours | ⏳ TODO |
| 4. Test Updates | 4 hours | ⏳ TODO |
| 5. Documentation | 2 hours | ⏳ TODO |
| **Total** | **18-20 hours** | **~3 days** |

---

## Current Status

**Completed**: Phase 1 (Models & Examples)  
**Next Up**: Phase 2 (Parser Updates)  
**Blockers**: None

**Ready to continue with RML parser updates!**

