# Manual Override - Quick Test Guide

## Issue Fixed

**Error:** `Override failed: Field required for column_name and property_uri`

**Cause:** Frontend was sending form data, backend expected query parameters

**Fix:** Changed `api.overrideMapping()` to send query parameters in URL

**File:** `frontend/src/services/api.ts`

---

## Test Steps

### 1. Refresh Frontend

```bash
# Hard refresh browser (Cmd+Shift+R or Ctrl+Shift+R)
# OR restart frontend dev server:
cd frontend
npm run dev
```

### 2. Test Override Flow

1. **Navigate to project with generated mapping**
   - Should see match details table

2. **Click "Override" button** on any row
   - Modal should open
   - Shows current mapping
   - Shows searchable property list

3. **Select a different property**
   - Type in search box to filter
   - Click on a property to select it
   - "Map Column" button should enable

4. **Click "Map Column"**
   - Should see: "Manual mapping override persisted..."
   - Modal closes
   - Table updates with new property

5. **Verify persistence**
   - Refresh page
   - New mapping should still be there
   - Or check `/api/mappings/{project_id}?raw=true`

---

## Expected API Call

### Before (Broken)
```http
POST /api/mappings/{project_id}/override
Content-Type: application/x-www-form-urlencoded

column_name=Age&property_uri=http://example.org/hr#birthDate
```

Backend looked for query params, got body → **Error**

### After (Fixed)
```http
POST /api/mappings/{project_id}/override?column_name=Age&property_uri=http://example.org/hr#birthDate
```

Backend gets query params → **Success**

---

## Verification

### Check the request in browser DevTools:

1. Open DevTools (F12)
2. Go to Network tab
3. Click Override button and confirm
4. Find the `override` request
5. Check:
   - **URL should include:** `?column_name=...&property_uri=...`
   - **Status should be:** `200 OK`
   - **Response should be:** `{"status": "success", ...}`

---

## Files Changed

- `frontend/src/services/api.ts` - Line 82-86
  - Changed from form data to query parameters

---

## Success Indicators

✅ No error message about "Field required"  
✅ Success message appears  
✅ Table updates immediately  
✅ mapping_config.yaml updated  
✅ alignment_report.json updated  

---

## If Still Failing

1. **Check backend logs** for actual error
2. **Verify backend endpoint** expects query params:
   ```python
   async def override_mapping(project_id: str, column_name: str, property_uri: str):
   ```
3. **Check browser console** for JavaScript errors
4. **Try manual API call:**
   ```bash
   curl -X POST "http://localhost:8000/api/mappings/{project_id}/override?column_name=Age&property_uri=http://example.org/hr#age"
   ```

---

**Status:** Issue fixed, ready to test!

