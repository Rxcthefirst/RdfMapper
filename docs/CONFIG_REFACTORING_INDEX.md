# Configuration Refactoring - Documentation Index

**Date**: November 24, 2025  
**Status**: 🟡 Awaiting Approval

---

## Quick Links

1. **[Quick Summary](./CONFIG_REFACTORING_SUMMARY.md)** - 1-page overview
2. **[Visual Comparison](./CONFIG_VISUAL_COMPARISON.txt)** - ASCII art diagrams
3. **[Detailed Comparison](./CONFIG_COMPARISON.md)** - Side-by-side examples
4. **[Refactoring Plan](./CONFIG_REFACTORING_PLAN.md)** - Full implementation plan
5. **[Current Status](./CONFIG_FORMAT_RESTORATION.md)** - What's implemented now

---

## The Problem in One Sentence

Current config structure mixes pipeline configuration with RML mapping concepts and uses spreadsheet-centric terminology that doesn't work well for JSON/XML.

---

## The Solution in One Sentence

Clean two-section structure: **pipeline configuration** (validation, options) separate from **mapping definition** (namespaces, sources, properties) with format-agnostic terminology.

---

## Key Changes

### Structure
```yaml
# OLD (mixed)
namespaces: ...
defaults: ...
sheets: ...
validation: ...

# NEW (separated)
validation: ...
options: ...
mapping:
  namespaces: ...
  sources: ...
```

### Terminology
| Old | New | Why |
|-----|-----|-----|
| `sheets` | `sources` | Works for JSON/XML/DB |
| `row_resource` | `entity` | More semantic |
| `columns` | `properties` | Format-agnostic |
| `as` | `predicate` | RML terminology |

---

## Impact

**User Experience**: 
- ✅ Clearer mental model
- ✅ Better for JSON/XML sources
- ✅ RML-aligned (easier to learn)

**Code Quality**:
- ✅ Better separation of concerns
- ✅ Easier to extend
- ✅ More maintainable

**Timeline**: 2-3 weeks with backward compatibility

---

## Decision Required

**Recommendation**: ✅ **PROCEED**

**Rationale**: 
- Pre-1.0 is the right time for breaking changes
- Significantly improves UX
- Future-proof for new source types
- Better RML alignment

---

## Next Steps

1. ✅ Document proposal (complete)
2. ⏳ Get approval
3. ⏳ Implement with backward compatibility
4. ⏳ Update examples and docs
5. ⏳ Add deprecation warnings
6. ⏳ Remove old structure in v1.0

---

## Read in Order

For detailed understanding, read in this order:

1. **Start Here**: [Quick Summary](./CONFIG_REFACTORING_SUMMARY.md)
   - 1-page overview of problem and solution
   
2. **Visualize**: [Visual Comparison](./CONFIG_VISUAL_COMPARISON.txt)
   - ASCII diagrams showing structure differences
   
3. **Examples**: [Detailed Comparison](./CONFIG_COMPARISON.md)
   - Side-by-side YAML examples for all scenarios
   
4. **Implementation**: [Refactoring Plan](./CONFIG_REFACTORING_PLAN.md)
   - Full technical plan with models, migration, timeline
   
5. **Context**: [Current Status](./CONFIG_FORMAT_RESTORATION.md)
   - What's implemented now and why refactoring is needed

---

## Questions?

See the documents above or create an issue.

**Contact**: GitHub Issues or Discussions

---

**Status**: 🟡 AWAITING USER APPROVAL TO PROCEED

