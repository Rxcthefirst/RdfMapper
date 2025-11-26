# Fix: Preserve Original Filenames on Upload

**Date**: November 25, 2025  
**Issue**: Files renamed to generic names (data.csv, ontology.ttl, shapes.ttl)  
**Root Cause**: Upload endpoints were renaming files instead of preserving original names  
**Status**: 🟢 **FIXED**

---

## Problem

When uploading files through the UI, the backend was **renaming** them to generic names:

- Your `mortgage_data_2024.csv` → Saved as `data.csv`
- Your `financial_ontology.ttl` → Saved as `ontology.ttl`
- Your `validation_shapes.ttl` → Saved as `shapes.ttl`

### Issues This Caused

1. ❌ **Lost original filename** - Can't tell which file you uploaded
2. ❌ **Confusing for users** - "Where did `ontology.ttl` come from? I uploaded `my_ontology.ttl`!"
3. ❌ **Overwrites on re-upload** - Upload a new file and it replaces the old one
4. ❌ **No file history** - Can't upload multiple versions

---

## Root Cause

**File**: `backend/app/routers/projects.py`

### Data Upload (Line 132)
```python
# BEFORE - Generic naming
file_path = project_dir / f"data{file_ext}"
# User's "loans.csv" becomes "data.csv"
```

### Ontology Upload (Line 170)
```python
# BEFORE - Generic naming
file_path = project_dir / f"ontology{file_ext}"
# User's "mortgage_ontology.ttl" becomes "ontology.ttl"
```

### Shapes Upload (Line 203)
```python
# BEFORE - Generic naming
file_path = project_dir / f"shapes{file_ext}"
# User's "validation_rules.ttl" becomes "shapes.ttl"
```

### SKOS Upload (Lines 220-227)
```python
# BEFORE - Generic naming with increment
base = "skos"
target = project_dir / f"{base}{file_ext}"
# User's "financial_terms.ttl" becomes "skos.ttl", "skos-1.ttl", etc.
```

---

## Solution

### Fix 1: Data Upload ✅
```python
# AFTER - Preserve original filename
original_filename = Path(file.filename).name
file_path = project_dir / original_filename
# User's "loans.csv" stays "loans.csv" ✓
```

### Fix 2: Ontology Upload ✅
```python
# AFTER - Preserve original filename
original_filename = Path(file.filename).name
file_path = project_dir / original_filename
# User's "mortgage_ontology.ttl" stays "mortgage_ontology.ttl" ✓
```

### Fix 3: Shapes Upload ✅
```python
# AFTER - Preserve original filename
original_filename = Path(file.filename).name
file_path = project_dir / original_filename
# User's "validation_rules.ttl" stays "validation_rules.ttl" ✓
```

### Fix 4: SKOS Upload ✅
```python
# AFTER - Preserve original filename, increment only if duplicate
original_filename = Path(file.filename).name
file_stem = Path(original_filename).stem
file_ext = Path(original_filename).suffix

target = project_dir / original_filename
idx = 1
while target.exists():
    target = project_dir / f"{file_stem}-{idx}{file_ext}"
    idx += 1
# User's "terms.ttl" stays "terms.ttl" ✓
# Second upload of "terms.ttl" becomes "terms-1.ttl" ✓
```

---

## Benefits

### Before Fix ❌
```
uploads/project_id/
  ├── data.csv          ← What was this originally?
  ├── ontology.ttl      ← Which ontology?
  ├── shapes.ttl        ← What validation rules?
  └── skos.ttl          ← Which vocabulary?
```

**Problems**:
- Can't tell what the original files were
- Confusing for users
- No way to identify files later

### After Fix ✅
```
uploads/project_id/
  ├── mortgage_loans_2024.csv           ← Clear!
  ├── financial_ontology_v3.ttl         ← Descriptive!
  ├── loan_validation_rules.ttl         ← Understandable!
  └── banking_terminology.ttl           ← Obvious!
```

**Benefits**:
- ✅ Original filenames preserved
- ✅ Clear what each file is
- ✅ Better user experience
- ✅ Easier debugging
- ✅ Professional file management

---

## Example: Before vs After

### User Action
Upload file named: `mortgage_ontology_v2.ttl`

### Before Fix ❌
- Saved as: `/app/uploads/abc-123/ontology.ttl`
- Database stores: `/app/uploads/abc-123/ontology.ttl`
- UI shows: `ontology.ttl`
- User thinks: "Wait, I didn't upload `ontology.ttl`! 😕"

### After Fix ✅
- Saved as: `/app/uploads/abc-123/mortgage_ontology_v2.ttl`
- Database stores: `/app/uploads/abc-123/mortgage_ontology_v2.ttl`
- UI shows: `mortgage_ontology_v2.ttl`
- User thinks: "Perfect! That's my file! ✓"

---

## Impact on Existing Projects

**Existing projects** with old generic names (data.csv, ontology.ttl) will continue to work - no breaking changes.

**New uploads** will use original filenames.

**No migration needed** - system works with both old and new naming.

---

## Testing

### Test Case 1: Upload Data File
**Steps**:
1. Upload file: `customer_orders_2024.csv`
2. Check uploads directory

**Expected**: File saved as `customer_orders_2024.csv` ✓  
**Before**: File saved as `data.csv` ❌

---

### Test Case 2: Upload Ontology
**Steps**:
1. Upload file: `ecommerce_ontology_v1.ttl`
2. Check uploads directory

**Expected**: File saved as `ecommerce_ontology_v1.ttl` ✓  
**Before**: File saved as `ontology.ttl` ❌

---

### Test Case 3: Multiple SKOS Files
**Steps**:
1. Upload: `terms.ttl`
2. Upload another: `terms.ttl` (same name)
3. Check uploads directory

**Expected**:
- First: `terms.ttl` ✓
- Second: `terms-1.ttl` ✓

**Before**:
- First: `skos.ttl` ❌
- Second: `skos-1.ttl` ❌

---

## Files Modified

1. ✅ `backend/app/routers/projects.py`
   - `upload_data_file()` - Preserve original filename
   - `upload_ontology_file()` - Preserve original filename
   - `upload_shapes_file()` - Preserve original filename
   - `upload_skos_file()` - Preserve original filename with smart increment

---

## Backward Compatibility

✅ **Fully backward compatible**

Old projects with generic names will continue to work:
- Existing paths in database remain valid
- File references resolve correctly
- No migration scripts needed

---

## User Experience Improvement

**Before**:
- User: "Why is my file called `ontology.ttl`? I uploaded `financial_ontology.ttl`"
- Developer: "The system renames them for consistency"
- User: "But now I can't tell which ontology I uploaded! 😠"

**After**:
- User: "Great! My file `financial_ontology.ttl` is right there!"
- User: "I can see exactly what files I've uploaded ✓"
- User: "This is much better! 😊"

---

**Status**: 🟢 **FIXED & DEPLOYED**

Original filenames are now preserved on all uploads!

**No more mystery `ontology.ttl` and `data.csv` files - users see their actual filenames!** 🎉

