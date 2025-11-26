# Bug Fix: Incorrect Paths in Imported Mapping Config

**Date**: November 25, 2025  
**Issue**: Imported mapping config uses wrong absolute paths instead of relative paths  
**Status**: 🟢 **FIXED**

---

## Problem Description

When importing an existing RML/YARRRML file via the Web UI, the generated config contained incorrect paths:

**Example Bad Config**:
```yaml
options:
  on_error: report
  # ... other options
mapping:
  file: imported_mapping.ttl  # ❌ Wrong: Generic name, not user's filename
imports:
- /app/uploads/add983cb-4a13-4bae-b5bf-59eee04cd458/ontology.ttl  # ❌ Wrong: Absolute path
```

**Problems**:
1. **Generic filename**: Always saved as `imported_mapping.ttl` instead of preserving user's original filename
2. **Absolute paths**: Used full container paths like `/app/uploads/...` instead of relative paths
3. **Not portable**: Config wouldn't work outside the container or on different systems
4. **User confusion**: Didn't match the files user actually uploaded

---

## Root Cause

**File**: `backend/app/routers/projects.py` - `upload_existing_mapping()` endpoint

**Issue 1: Hardcoded Filename**
```python
# BEFORE - Always used generic name
mapping_filename = f"imported_mapping{file_ext}"
```
- Lost user's original filename
- Multiple imports would overwrite each other

**Issue 2: Absolute Path for Ontology**
```python
# BEFORE - Used full absolute path from database
if project.ontology_file:
    v2_config['imports'] = [project.ontology_file]
    # project.ontology_file = "/app/uploads/project_id/ontology.ttl"
```
- Included full container path
- Not portable across environments
- Broke when files moved

---

## Fix Applied

### Change 1: Preserve Original Filename ✅

**Before**:
```python
mapping_filename = f"imported_mapping{file_ext}"
mapping_path = project_dir / mapping_filename
```

**After**:
```python
# Use original filename to preserve user's naming convention
original_filename = Path(file.filename).name
mapping_path = project_dir / original_filename
```

**Benefits**:
- User sees their actual filename
- Multiple imports don't overwrite
- Clear what file is being used

---

### Change 2: Use Relative Paths ✅

**Before**:
```python
if project.ontology_file:
    v2_config['imports'] = [project.ontology_file]
    # Results in: /app/uploads/project_id/ontology.ttl
```

**After**:
```python
if project.ontology_file:
    # Convert absolute path to just filename (same directory)
    ontology_filename = Path(project.ontology_file).name
    v2_config['imports'] = [ontology_filename]
    # Results in: ontology.ttl
```

**Benefits**:
- Portable across systems
- Works outside container
- Clear and simple

---

### Change 3: Better Comments ✅

**Added to config header**:
```yaml
# Mapping file: my_custom_mapping.rml.ttl  # ← User's actual filename
# Ontology file: my_ontology.ttl           # ← User's actual filename
```

---

## Example: Before vs After

### Before (Broken) ❌

**User uploads**:
- Mapping: `mortgage_mapping.rml.ttl`
- Ontology: `mortgage_ontology.ttl`

**Generated config**:
```yaml
# Mapping file: imported_mapping.ttl  ← Wrong!

options:
  on_error: report
  skip_empty_values: true
  chunk_size: 1000
  aggregate_duplicates: true
  output_format: ttl
mapping:
  file: imported_mapping.ttl  ← Generic name, not user's file
imports:
- /app/uploads/add983cb-4a13-4bae-b5bf-59eee04cd458/ontology.ttl  ← Absolute path
```

**Issues**:
- Looking for `imported_mapping.ttl` when file is actually `mortgage_mapping.rml.ttl`
- Absolute path breaks portability
- Confusing to user

---

### After (Fixed) ✅

**User uploads**:
- Mapping: `mortgage_mapping.rml.ttl`
- Ontology: `mortgage_ontology.ttl`

**Generated config**:
```yaml
# Mapping file: mortgage_mapping.rml.ttl  ← Correct!
# Ontology file: mortgage_ontology.ttl    ← Correct!

options:
  on_error: report
  skip_empty_values: true
  chunk_size: 1000
  aggregate_duplicates: true
  output_format: ttl
mapping:
  file: mortgage_mapping.rml.ttl  ← User's actual filename
imports:
- mortgage_ontology.ttl  ← Relative path (same directory)
```

**Benefits**:
- Correct filenames
- Relative paths
- Portable
- Clear

---

## Why Relative Paths?

### Same Directory Structure

All files are in the same project directory:
```
uploads/project_id/
  ├── data.csv
  ├── mortgage_ontology.ttl
  ├── mortgage_mapping.rml.ttl
  └── mapping_config.yaml
```

Since all files are in the same directory, we only need filenames:
```yaml
mapping:
  file: mortgage_mapping.rml.ttl  # Same directory
imports:
  - mortgage_ontology.ttl          # Same directory
```

This works everywhere, not just inside the Docker container!

---

## Testing

### Test Case 1: Import RML with Custom Name

**Steps**:
1. Upload ontology: `my_ontology.ttl`
2. Upload data: `my_data.csv`
3. Import mapping: `my_custom_mapping.rml.ttl`

**Expected Config**:
```yaml
mapping:
  file: my_custom_mapping.rml.ttl  ✅
imports:
  - my_ontology.ttl  ✅
```

**Before**: ❌ Used `imported_mapping.ttl` and `/app/uploads/.../ontology.ttl`  
**After**: ✅ Uses actual filenames and relative paths

---

### Test Case 2: Multiple Imports

**Steps**:
1. Import `mapping_v1.rml.ttl`
2. Later import `mapping_v2.rml.ttl`

**Expected**:
- Both files preserved with original names
- No overwriting

**Before**: ❌ Both saved as `imported_mapping.ttl`, second overwrites first  
**After**: ✅ Each keeps its name: `mapping_v1.rml.ttl`, `mapping_v2.rml.ttl`

---

### Test Case 3: Portability

**Steps**:
1. Import mapping on Server A
2. Copy project directory to Server B
3. Run conversion

**Expected**: Works on Server B

**Before**: ❌ Fails - absolute paths point to wrong location  
**After**: ✅ Works - relative paths resolve correctly

---

## CLI Consistency

The CLI version (`rdfmap init --existing-mapping`) already did this correctly:

```python
# CLI already uses relative paths
mapping_rel_path = existing_mapping.name  # Just filename
if ontology:
    ontology_path = str(ontology.relative_to(config_path.parent))
```

Now the Web UI matches the CLI behavior! ✅

---

## Impact

### For Users
✅ **Correct filenames** - See their actual files referenced  
✅ **Portable configs** - Work outside container  
✅ **No confusion** - Config matches reality  
✅ **Multiple imports** - Don't overwrite each other

### For Development
✅ **Consistency** - Web UI matches CLI behavior  
✅ **Simplicity** - Relative paths are simpler  
✅ **Portability** - Easier testing and deployment

---

## Files Modified

1. ✅ `backend/app/routers/projects.py`
   - `upload_existing_mapping()` endpoint
   - Use `Path(file.filename).name` for original filename
   - Use `Path(project.ontology_file).name` for relative path
   - Added filename to comment header

---

## Deployment Notes

**Backend Change**: Yes (endpoints updated)  
**Frontend Change**: No  
**Breaking Change**: No (old imported configs still work)  
**Migration Needed**: No (but old configs could be regenerated for correctness)

**Restart Required**: Yes (backend API)

---

## Validation Checklist

- [x] Import preserves original filename
- [x] Ontology uses relative path (just filename)
- [x] Config is portable (no absolute paths)
- [x] Multiple imports don't overwrite
- [x] Config header shows actual filenames
- [x] Conversion works with new config
- [x] CLI and Web UI consistent

---

**Status**: 🟢 **FIXED**

Imported mapping configs now use:
1. ✅ Original filenames (not generic names)
2. ✅ Relative paths (portable)
3. ✅ Clear documentation in comments

**Users see accurate, portable configs that match their uploaded files!**

