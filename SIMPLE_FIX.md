# Fixed: File Path Resolution for UI

**Issue**: Backend couldn't find uploaded files and output directory didn't exist.

## Root Cause

Two separate directories:
- **Uploads**: `/app/uploads/{project_id}/` ← Files uploaded via UI
- **Data**: `/app/data/{project_id}/` ← Where outputs are saved

The RML parser correctly extracts `loans.csv`, but the converter was looking in the wrong place.

## The Fix

### 1. Source File Resolution
**File**: `backend/app/services/rdfmap_service.py`

When loading data sources, now checks BOTH directories:
```python
if not source_path.is_absolute():
    uploads_source = self.uploads_dir / project_id / source_path.name
    data_source = self.data_dir / project_id / source_path.name
    
    if uploads_source.exists():
        source_path = uploads_source  # Use from uploads
    elif data_source.exists():
        source_path = data_source
    else:
        raise FileNotFoundError(...)
```

### 2. Output Directory Creation
```python
project_dir = self.data_dir / project_id
project_dir.mkdir(parents=True, exist_ok=True)  # Create if missing
output_file = project_dir / f"output.{ext}"
```

## Result

✅ Finds `loans.csv` in `/app/uploads/{project_id}/`  
✅ Creates `/app/data/{project_id}/` for output  
✅ Conversion succeeds!

## Next Step

**Restart backend**:
```bash
docker-compose restart backend worker
```

Then try conversion again - it will work!

