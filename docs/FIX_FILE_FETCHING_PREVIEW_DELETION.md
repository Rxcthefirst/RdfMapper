# Fix: File Fetching, Mapping Preview & File Deletion

**Date**: November 25, 2025  
**Issues Fixed**:
1. External RML file fetch failing (wrong endpoint)
2. No mapping preview feature
3. No way to delete uploaded files
**Status**: 🟢 **COMPLETE**

---

## 🎯 Issues Fixed

### Issue 1: File Fetch Failing ✅

**Problem**: `/api/files/{projectId}/{filename}` endpoint didn't exist

**Solution**: 
- Created `/api/projects/{projectId}/files/{filename}` endpoint
- Reads files from project directory
- Returns file content as text
- Searches both UPLOAD_DIR and DATA_DIR

**Frontend Fix**: Updated fetch URL in ComprehensiveMappingTable

---

### Issue 2: No Mapping Preview ✅

**Problem**: Users couldn't preview mapping file content

**Solution**: Created `/api/projects/{projectId}/mapping-preview` endpoint

**Features**:
- Shows first N lines (default 50)
- Detects format (RML, YARRRML, v2-inline)
- Returns total line count
- Indicates if truncated

**Response**:
```json
{
  "format": "RML",
  "preview": "...(first 50 lines)...",
  "total_lines": 200,
  "showing_lines": 50,
  "is_truncated": true
}
```

---

### Issue 3: No File Deletion ✅

**Problem**: Users couldn't remove uploaded files

**Solution**: Created 3 deletion endpoints

#### 1. `DELETE /api/projects/{project_id}/data-file`
- Deletes uploaded data file
- Updates database (sets data_file = NULL)
- Resets project status to "created"

#### 2. `DELETE /api/projects/{project_id}/ontology-file`
- Deletes uploaded ontology file
- Updates database (sets ontology_file = NULL)
- Resets project status to "created"

#### 3. `DELETE /api/projects/{project_id}/mapping-file`
- Deletes mapping config file
- Deletes external RML/YARRRML file (if exists)
- Returns list of deleted files

---

## 🚀 New API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/projects/{id}/files/{filename}` | GET | Fetch file content |
| `/api/projects/{id}/mapping-preview` | GET | Preview mapping (first N lines) |
| `/api/projects/{id}/data-file` | DELETE | Delete data file |
| `/api/projects/{id}/ontology-file` | DELETE | Delete ontology file |
| `/api/projects/{id}/mapping-file` | DELETE | Delete mapping file(s) |

---

## 💻 Frontend API Methods Added

```typescript
api.getMappingPreview(projectId, limit?)
api.deleteDataFile(projectId)
api.deleteOntologyFile(projectId)
api.deleteMappingFile(projectId)
```

---

## 🎉 Result

✅ **External RML files now load correctly!**
✅ **Users can preview mappings**
✅ **Users can delete files**

All issues resolved! 🚀

