# Quick Test Guide - Verify UX Fixes

## Test 1: Verify Match Reasons Section is Gone ✅

**Steps:**
1. Generate a mapping for a project
2. Scroll down through the page

**Expected:**
- ❌ No "Match Reasons" section anywhere
- ✅ Only see "Mapping Configuration" section
- ✅ Mapping Configuration has Evidence buttons

**Result:** Pass / Fail

---

## Test 2: Verify Accurate Mapping Counts ✅

**Steps:**
1. Generate mapping with some unmapped columns
2. Look at "Mapping Summary" section

**Expected:**
- Shows: "Mapped: X / Total: Y (Z%)"
- Numbers should match the statistics chips in Mapping Configuration
- If you have unmapped columns, mapped < total

**Example:**
```
Mapped: 35 / Total: 47 (74.5%)
```

**NOT:**
```
All columns mapped: 21/21 (100%)  ← This would be wrong
```

**Result:** Pass / Fail

---

## Test 3: Verify Immediate Updates After Manual Override ✅

**Test 3A: Map an Unmapped Column**

**Steps:**
1. Find an unmapped column in ⚠️ Unmapped Columns table
2. Click "Map Now"
3. Search for a property
4. Select property
5. Click "Map Column"

**Expected:**
- ✅ Success message appears
- ✅ Modal closes
- ✅ **Mapping Configuration section refreshes automatically**
- ✅ Statistics chips update (Mapped +1, Unmapped -1)
- ✅ Column appears in ✅ Mapped Columns table
- ✅ Column disappears from ⚠️ Unmapped Columns table
- ✅ No need to refresh page

**Result:** Pass / Fail

---

**Test 3B: Change an Existing Mapping**

**Steps:**
1. Find a mapped column in ✅ Mapped Columns table
2. Click "Change" button
3. Select different property
4. Click "Map Column"

**Expected:**
- ✅ Success message appears (e.g., "Mapping updated: Age → birthDate")
- ✅ Modal closes
- ✅ **Table row updates immediately**
- ✅ Shows new property name
- ✅ Shows 100% confidence (manual override)
- ✅ No need to refresh page

**Result:** Pass / Fail

---

## Test 4: Verify Evidence Still Works ✅

**Steps:**
1. Click "Evidence" button on any mapped column
2. Review evidence drawer

**Expected:**
- ✅ Drawer opens from right
- ✅ Shows evidence categories (✅ Semantic, ⭐ Ontological, 🔗 Structural)
- ✅ Shows reasoning summary
- ✅ Shows performance metrics
- ✅ Can close drawer

**Result:** Pass / Fail

---

## Test 5: End-to-End Workflow ✅

**Complete User Journey:**

1. **Upload files**
   - Upload data CSV
   - Upload ontology TTL

2. **Generate mapping**
   - Click "Generate Mappings"
   - Wait for completion

3. **Check Mapping Summary**
   - Should show accurate counts
   - Note the Mapped/Total numbers

4. **Review Mapping Configuration**
   - See mapped columns table
   - See unmapped columns table
   - Statistics chips match Mapping Summary

5. **Map an unmapped column**
   - Click "Map Now"
   - Select property
   - Confirm

6. **Verify immediate update**
   - Success message shows
   - Mapping Configuration updates
   - Statistics change (Mapped +1, Unmapped -1)
   - Column moves to mapped table

7. **Change a mapping**
   - Click "Change" on mapped column
   - Select different property
   - Confirm

8. **Verify change**
   - Row updates immediately
   - New property displayed

9. **Convert to RDF**
   - Click "Convert to RDF"
   - Should use all mappings (auto + manual)

10. **Download**
    - Download RDF file
    - Verify triples include manual mappings

**Result:** Pass / Fail

---

## Visual Checklist

When viewing the page after generating mappings, you should see:

### Top to Bottom Order:
```
1. ✅ Project Detail (title)
2. ✅ Status chips (Data: uploaded, Ontology: uploaded)
3. ✅ Upload Files section
4. ✅ Knowledge Inputs section
5. ✅ Ontology Summary section
6. ✅ Generate Mappings button
7. ✅ Convert to RDF section
8. ✅ Download section
9. ✅ Data Preview
10. ✅ Mapping Summary (accurate counts!)
11. ❌ NO "Match Reasons" section
12. ✅ Mapping Configuration section (with Evidence/Change/Map Now buttons)
```

### What You Should NOT See:
- ❌ "Match Reasons" section
- ❌ "Mapping YAML" raw code block
- ❌ "Reasoning Metrics" with cardinality violations
- ❌ "All columns mapped: 21/21" when unmapped exist

### What You SHOULD See:
- ✅ "Mapping Summary" with accurate counts
- ✅ "Mapping Configuration" with:
  - Statistics chips
  - ✅ Mapped Columns table
  - ⚠️ Unmapped Columns table
  - Evidence/Change/Map Now buttons

---

## Browser DevTools Check

**Open DevTools (F12) → Network Tab**

After clicking "Map Now" and confirming:

**Expected network requests:**
1. `POST /api/mappings/{id}/override?column_name=...&property_uri=...`
   - Status: 200 OK
   - Response: `{"status": "success", ...}`

2. `POST /api/mappings/{id}/generate` (from generate.mutate())
   - Status: 200 OK
   - Response includes updated alignment_report with the manual mapping

**Expected console:**
- No errors ✅
- No warnings about missing data ✅
- You'll see: "Mappings generated! X/Y columns mapped" as the generate mutation runs again

---

## Common Issues

### Issue: Mapping Configuration doesn't update after override

**Symptoms:**
- Success message appears
- But table doesn't change
- Have to refresh page

**Cause:** `generate.mutate()` not being called

**Fix:** Check that the onMap handler calls `generate.mutate()` (not `refetch()` - mutations don't have refetch)

---

### Issue: Statistics still show 21/21 when unmapped exist

**Symptoms:**
- Mapping Summary shows 100%
- But unmapped columns visible

**Cause:** Still using old `mappingInfo.stats`

**Fix:** Verify Mapping Summary uses `generate.data.alignment_report.statistics`

---

### Issue: Match Reasons section still visible

**Symptoms:**
- See both "Match Reasons" and "Mapping Configuration"

**Cause:** Section not fully deleted

**Fix:** Ensure entire `{mappingInfo?.matchDetails && ... }` block removed

---

## Quick Verification Commands

**Check file was edited:**
```bash
cd /Users/rxcthefirst/Dev/PythonProjects/SemanticModelDataMapper
git diff frontend/src/pages/ProjectDetail.tsx | head -50
```

**Verify no TypeScript errors:**
```bash
cd frontend
npm run build
```

**Start dev server:**
```bash
cd frontend
npm run dev
```

---

## Success Indicators

✅ No TypeScript errors  
✅ Match Reasons section gone  
✅ Accurate mapping counts  
✅ Immediate updates after override  
✅ Clean, uncluttered UI  
✅ Single source of truth (Mapping Configuration)  

---

**If all tests pass:** UX fixes are working correctly! 🎉

**If any test fails:** Check the specific section in FINAL_UX_FIXES_COMPLETE.md for details on what should have changed.

