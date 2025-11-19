# Evidence UI Implementation Status & Testing Guide

## Current Status

✅ **Backend Implementation:** Complete  
✅ **React Component:** Complete  
🔄 **Frontend Integration:** Complete (just now)  
⚠️ **Data Flow:** Needs verification

## What Was Just Fixed

### Problem
You mentioned not seeing the evidence categories (✅ Semantic, ⭐ Ontological, 🔗 Structural) in the UI.

### Root Cause
The new `EvidenceExplorer` component was created but:
1. It was in `/web-ui/src/components/` (which appears to be a template directory)
2. The actual frontend in `/frontend/src/` was still using the old `EvidenceDrawer` implementation
3. The old implementation showed a flat evidence list, not categorized groups

### Solution Applied
I've just updated the frontend to use the new evidence categorization:

1. **Copied `EvidenceExplorer.tsx`** to `/frontend/src/components/`
2. **Updated `EvidenceDrawer.tsx`** in `/frontend/src/components/` to use the new component
3. **Preserved backward compatibility** with existing interfaces

## Files Modified

```
✅ frontend/src/components/EvidenceExplorer.tsx (NEW)
✅ frontend/src/components/EvidenceDrawer.tsx (UPDATED)
✅ web-ui/src/components/EvidenceExplorer.tsx (created earlier)
✅ web-ui/src/components/EvidenceDrawer.tsx (created earlier)
```

## Testing Steps

### Quick Verification

Run this script to verify backend evidence generation:

```bash
python verify_evidence_backend.py
```

This will test:
- ✅ Evidence categorization into groups
- ✅ Reasoning summary generation
- ✅ Performance metrics capture
- ✅ JSON serialization

### Full UI Testing

1. **Restart the frontend** (if running):
   ```bash
   cd frontend
   npm run dev
   ```

2. **Regenerate a mapping** to get new evidence structure:
   - Open the app at http://localhost:3000
   - Either create a new project OR
   - Re-run mapping generation for an existing project
   - This ensures the backend generates the new `evidence_groups` field

3. **Open Evidence Drawer**:
   - Click on any column mapping in the results table
   - You should NOW see:
     - **Three expandable sections** with icons (✅⭐🔗)
     - **Reasoning summary** in a blue alert box
     - **Performance badge** with speed metrics
     - **Color-coded confidence** chips

## What You Should See Now

### Before (Old Implementation)
```
Match Evidence
Column: employeeID

Evidence (5 items):
- SemanticSimilarityMatcher: 0.85
- LexicalMatcher: 0.80
- DataTypeInferenceMatcher: 0.68
- OWLCharacteristicsMatcher: 0.80
- StructuralMatcher: 0.70
```

### After (New Implementation)
```
employeeID → Employee ID
92% confidence

💡 Semantic match validated by 4 ontological constraints.
   Very high confidence - multiple strategies converge.

⚡ 45.2ms | 4.3x speedup | 9 matchers

✅ SEMANTIC REASONING ▼
   3 matchers, avg: 0.85
   - SemanticSimilarityMatcher: 0.85
   - LexicalMatcher: 0.80
   - ExactLocalNameMatcher: 0.90

⭐ ONTOLOGICAL VALIDATION ▼
   4 matchers, avg: 0.72
   - OWLCharacteristicsMatcher: 0.80
   - DataTypeInferenceMatcher: 0.68
   - PropertyHierarchyMatcher: 0.75
   - GraphReasoningMatcher: 0.70

🔗 STRUCTURAL CONTEXT ▼
   2 matchers, avg: 0.68
   - StructuralMatcher: 0.70
   - HistoryAwareMatcher: 0.65
```

## Troubleshooting

### Still seeing old flat list?

**Issue:** Evidence drawer shows flat list instead of categorized groups

**Fixes:**

1. **Clear browser cache** (hard refresh: Cmd+Shift+R or Ctrl+Shift+R)

2. **Verify frontend is using latest code:**
   ```bash
   cd frontend
   npm run dev  # Should show hot reload
   ```

3. **Check console for errors:**
   - Open browser DevTools (F12)
   - Look for React errors in Console tab
   - Check Network tab for API responses

4. **Regenerate mapping:**
   - Old mappings don't have `evidence_groups`
   - Create a new project or regenerate existing one
   - Backend must run updated code

5. **Verify backend has updates:**
   ```bash
   # Check if evidence_categorizer exists
   python -c "from rdfmap.generator.evidence_categorizer import categorize_evidence; print('✅ Backend updated')"
   ```

### Evidence groups empty?

**Issue:** Groups exist but have no items

**Possible causes:**
- Matchers not firing
- Ontology file issues
- Column names too generic

**Solution:**
Use test data designed to trigger all matchers:
```bash
# Use messy_employees.csv with camelCase, typos, FK patterns
test_data/messy_employees.csv
```

### No reasoning summary?

**Issue:** Missing the blue alert box

**Check:**
```bash
# Verify alignment report structure
cat data/{project_id}/alignment_report.json | jq '.match_details[0].reasoning_summary'
```

Should output a sentence like:
```
"Matched to 'Employee ID' with 0.92 confidence. Semantic reasoning: 3 matchers agree..."
```

If null, the mapping was generated before the update. Regenerate it.

## API Testing

Test the evidence API directly:

```bash
# Get evidence for a column
curl http://localhost:8000/api/mappings/{project_id}/evidence/employeeID | jq '.evidence_detail.evidence_groups'

# Should show array of groups:
# [
#   {
#     "category": "semantic",
#     "evidence_items": [...],
#     "avg_confidence": 0.85
#   },
#   ...
# ]
```

## Component Architecture

```
ProjectDetail.tsx
  └─ Opens Evidence Drawer on row click
      └─ EvidenceDrawer.tsx (Updated wrapper)
          └─ EvidenceExplorer.tsx (New component)
              ├─ Evidence Groups (Accordions)
              ├─ Reasoning Summary (Alert)
              ├─ Performance Badge
              └─ Alternate Candidates
```

## Key Features Implemented

✅ **Evidence Categorization**
- Semantic: Embeddings, labels, lexical
- Ontological: OWL, types, hierarchy
- Structural: Relationships, patterns

✅ **Visual Indicators**
- Icons: ✅ (green), ⭐ (orange), 🔗 (blue)
- Color-coded confidence (green→red)
- Progress bars per evidence item

✅ **Reasoning Explanations**
- Multi-sentence summaries
- Shows how ontology validates semantic
- Natural language reasoning

✅ **Performance Metrics**
- Execution time
- Parallel speedup factor
- Number of matchers fired

✅ **Alternate Candidates**
- Shows near-matches
- Confidence comparison
- Evidence count

## Next Steps

1. **Run `verify_evidence_backend.py`** to confirm backend works
2. **Restart frontend** with `npm run dev` 
3. **Regenerate a mapping** to get new evidence structure
4. **Open Evidence Drawer** and look for the three expandable sections
5. **If still not working**, check `TESTING_EVIDENCE_UI.md` for detailed troubleshooting

## Success Criteria

You'll know it's working when you see:

- ✅ Three accordion sections (not flat list)
- ✅ Icons: ✅ Semantic, ⭐ Ontological, 🔗 Structural
- ✅ Blue alert box with reasoning summary
- ✅ Performance badge with speed icon
- ✅ Each accordion shows "X matchers, avg: Y.YY"
- ✅ Clicking accordions expands/collapses them

## Contact Points

If issues persist after trying all troubleshooting steps:

1. Check browser console for errors
2. Check backend logs for exceptions
3. Verify API responses in Network tab
4. Run verification script for detailed diagnosis

---

**Last Updated:** November 17, 2025  
**Status:** Frontend integration complete, ready for testing

