# Bug Fixes: Mapping Detection & Download Options

**Date**: November 25, 2025  
**Issues Fixed**: 
1. False positive "Mapping Available" on new projects
2. Preview not working for new projects
3. Missing RML/YARRRML download buttons
**Status**: 🟢 **FIXED**

---

## Issues Identified

### Issue 1: False Positive "Mapping Available"

**Problem**: New projects showed "✓ Mapping Available" chip even without any mapping

**Root Cause**: `fetchMappingYaml` API method didn't handle 404 properly
```typescript
// Before - returned error text even on 404
fetchMappingYaml: (projectId) => 
  fetch(`/api/mappings/${projectId}?raw=true`).then(r => r.text())
```

**Impact**: 
- Confusing UX - users thought they had a mapping when they didn't
- Preview showed error text as YAML
- Step 2 showed tabs when no mapping existed

---

### Issue 2: MappingPreview Not Working

**Problem**: Preview component tried to parse error text as YAML

**Root Cause**: Same as Issue 1 - API returned error HTML/text instead of null on 404

**Impact**:
- Parse errors in MappingPreview
- Crash or show error messages
- User couldn't review imported/generated mappings

---

### Issue 3: Missing Download Options

**Problem**: Only "Download YAML" button available, but downloads main config instead of mapping formats

**Missing Features**:
- Download RML Turtle format
- Download RML RDF/XML format  
- Download YARRRML format

**Impact**:
- Users couldn't get standards-compliant RML
- Users couldn't get YARRRML for other tools
- Limited interoperability

---

## Fixes Applied

### Fix 1: Handle 404 in fetchMappingYaml ✅

**File**: `frontend/src/services/api.ts`

**Before**:
```typescript
fetchMappingYaml: (projectId: string) => 
  fetch(`/api/mappings/${projectId}?raw=true`).then(r => r.text())
```

**After**:
```typescript
fetchMappingYaml: (projectId: string) => 
  fetch(`/api/mappings/${projectId}?raw=true`).then(r => {
    if (r.status === 404) return null  // ← Key fix!
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    return r.text()
  })
```

**Result**:
- Returns `null` on 404 (no mapping)
- Frontend correctly shows "no mapping" state
- "✓ Mapping Available" only shows when mapping exists

---

### Fix 2: Add RML Download Endpoint ✅

**File**: `backend/app/routers/mappings.py`

**New Endpoint**: `GET /api/mappings/{project_id}/rml?format={turtle|xml}`

**Features**:
- Converts internal config to W3C-compliant RML
- Supports Turtle (default) and RDF/XML formats
- Checks both DATA_DIR and UPLOAD_DIR (like other endpoints)
- Returns downloadable file with correct content-type

**Code**:
```python
@router.get("/{project_id}/rml")
async def get_rml(project_id: str, format: str = Query("turtle")):
    # Check both directories
    # Load config
    # Convert to RML using internal_to_rml_graph()
    # Serialize to turtle or xml
    # Return with download headers
```

---

### Fix 3: Update YARRRML Endpoint ✅

**File**: `backend/app/routers/mappings.py`

**Issue**: YARRRML endpoint only checked DATA_DIR

**Fix**: Added UPLOAD_DIR check (consistency with other endpoints)

**Before**:
```python
project_dir = Path(settings.DATA_DIR) / project_id
mapping_file = project_dir / "mapping_config.yaml"
if not mapping_file.exists():
    raise HTTPException(404)
```

**After**:
```python
project_dir = Path(settings.DATA_DIR) / project_id
mapping_file = project_dir / "mapping_config.yaml"
if not mapping_file.exists():
    project_dir = Path(settings.UPLOAD_DIR) / project_id
    mapping_file = project_dir / "mapping_config.yaml"
    if not mapping_file.exists():
        raise HTTPException(404)
```

---

### Fix 4: Add Download Buttons in Frontend ✅

**File**: `frontend/src/pages/ProjectDetail.tsx`

**Location**: Step 2, "View/Edit Mapping" tab

**New Buttons**:
1. **Download Config** - Main config YAML (renamed from "Download YAML")
2. **Download RML (Turtle)** - W3C-compliant RML in Turtle format
3. **Download YARRRML** - YARRRML format for other tools

**Code**:
```typescript
<Stack direction="row" spacing={2}>
  <Button onClick={() => downloadConfig()}>
    Download Config
  </Button>
  <Button onClick={() => api.downloadRML(projectId, 'turtle')}>
    Download RML (Turtle)
  </Button>
  <Button onClick={() => api.downloadYARRRML(projectId)}>
    Download YARRRML
  </Button>
</Stack>
```

**API Methods Added**:
```typescript
downloadRML: async (projectId, format) => {
  const res = await fetch(`/api/mappings/${projectId}/rml?format=${format}`)
  // Create blob and download
}
```

---

## Testing

### Test Case 1: New Project (No Mapping)

**Before**:
- ✓ Shows "✓ Mapping Available" ❌
- Preview tries to parse error text ❌
- Download button downloads error HTML ❌

**After**:
- Shows no mapping indicator ✅
- Step 2 only shows "Generate" option ✅
- No false indicators ✅

---

### Test Case 2: Import RML → Download

**Before**:
- Import works ✅
- Preview works ✅ (after directory fix)
- Only "Download YAML" available ❌
- Can't download RML back out ❌

**After**:
- Import works ✅
- Preview works ✅
- Three download options ✅
- Can download RML Turtle ✅
- Can download YARRRML ✅

---

### Test Case 3: Generate → Download

**Before**:
- Generate works ✅
- Preview works ✅
- Only "Download YAML" available ❌
- Can't share RML with others ❌

**After**:
- Generate works ✅
- Preview works ✅
- Three download options ✅
- Can download RML for interoperability ✅
- Can download YARRRML for editing ✅

---

## Benefits

### For Users
✅ **Clear Status** - No false "Mapping Available" indicators  
✅ **Preview Works** - Correctly handles no-mapping state  
✅ **Export Options** - Download in multiple standards-compliant formats  
✅ **Interoperability** - Share RML with RMLMapper, Morph-KGC, etc.

### For Standards Compliance
✅ **W3C RML** - Can export to standard RML Turtle  
✅ **YARRRML** - Can export to human-friendly YARRRML  
✅ **Compatibility** - Works with other RML tools

---

## Files Modified

### Backend
1. ✅ `backend/app/routers/mappings.py`
   - Added `get_rml()` endpoint
   - Fixed `get_yarrrml()` to check both directories

### Frontend
1. ✅ `frontend/src/services/api.ts`
   - Fixed `fetchMappingYaml()` to return null on 404
   - Added `downloadRML()` method

2. ✅ `frontend/src/pages/ProjectDetail.tsx`
   - Added three download buttons in Step 2
   - Renamed "Download YAML" to "Download Config"
   - Added RML and YARRRML download handlers

---

## User Experience Flow

### Import Workflow
```
1. Upload ontology + data
2. Import RML file → "✓ Mapping Available" ✅
3. Step 2 shows [View/Edit Mapping] tab
4. Preview displays correctly ✅
5. Download options:
   - Download Config (main YAML)
   - Download RML (Turtle) ← Can get back original format
   - Download YARRRML ← Can convert to YARRRML
```

### Generate Workflow
```
1. Upload ontology + data
2. Generate with AI → "✓ Mapping Available" ✅
3. Step 2 shows [View/Edit Mapping] tab
4. Preview displays correctly ✅
5. Download options:
   - Download Config
   - Download RML (Turtle) ← Share with others
   - Download YARRRML ← Edit externally
```

### New Project (No Mapping)
```
1. Create project
2. No "✓ Mapping Available" ✅ (fixed!)
3. Step 2 only shows "Generate Mappings" ✅
4. No false indicators ✅
```

---

## API Endpoints Summary

### GET `/api/mappings/{project_id}`
- Returns main config
- Checks both DATA_DIR and UPLOAD_DIR ✅
- Returns 404 if no mapping ✅

### GET `/api/mappings/{project_id}?raw=true`
- Returns raw YAML string
- Returns 404 if no mapping ✅
- Frontend handles properly ✅

### GET `/api/mappings/{project_id}/yarrrml` ✅
- Converts to YARRRML format
- Checks both directories ✅
- Returns downloadable YAML

### GET `/api/mappings/{project_id}/rml?format={turtle|xml}` ✅ NEW!
- Converts to RML format
- Checks both directories ✅
- Supports Turtle (default) and RDF/XML
- Returns downloadable RDF

---

## Deployment Notes

**Backend Changes**: New endpoint added (`/rml`)  
**Frontend Changes**: API method signatures updated  
**Breaking Changes**: None  
**Migration Required**: No

**Restart Required**: Yes (both backend and frontend)

---

## Related Issues Resolved

1. ✅ False positive mapping detection
2. ✅ Preview crashes on new projects
3. ✅ Missing RML export
4. ✅ Missing YARRRML export
5. ✅ YARRRML endpoint not checking UPLOAD_DIR

---

**Status**: 🟢 **ALL ISSUES FIXED & TESTED**

Users now have:
1. ✅ Accurate mapping status detection
2. ✅ Working preview for all cases
3. ✅ Multiple export format options
4. ✅ Standards-compliant interoperability

**The mapping workflow is now complete and robust!** 🎉

