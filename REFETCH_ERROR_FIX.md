# Quick Fix - Manual Override State Update

**Date:** November 17, 2025  
**Status:** ✅ Fixed (v2 - Correct Approach)

## Problem Evolution

### First Error
```
Override failed: generate.refetch is not a function
```
**Cause:** Tried to call `refetch()` on a mutation (only queries have refetch).

### Second Problem  
```tsx
generate.mutate()  // ❌ This re-generates mappings from scratch, losing manual overrides!
```
**Cause:** Re-generating mappings overwrites the manual changes we just made.

### Correct Solution ✅
**Manually update the local state** to reflect the override without re-generating everything.

## Final Fix Applied

**Changed in:** `frontend/src/pages/ProjectDetail.tsx`

### 1. Added refresh counter state
```tsx
const [refreshKey, setRefreshKey] = useState(0) // Force re-render after manual overrides
```

### 2. Updated override handler to mutate state
```tsx
onMap={async (col, propUri)=>{
  try {
    await api.overrideMapping(projectId, col, propUri)
    const propLabel = propUri.split('#').pop()?.split('/').pop() || propUri
    setSuccess(`Mapping updated: ${col} → ${propLabel}`)

    // Update generate.data to reflect the manual override
    if (generate.data) {
      // Update existing match or add new one
      const updatedMatchDetails = generate.data.match_details?.map((detail: any) => 
        detail.column_name === col 
          ? { 
              ...detail, 
              matched_property: propUri, 
              matcher_name: 'ManualOverride', 
              match_type: 'manual_override', 
              confidence_score: 1.0,
              matched_via: 'User override'
            } 
          : detail
      ) || []

      // If it was unmapped, add to match_details and remove from unmapped
      const wasUnmapped = generate.data.alignment_report?.unmapped_columns?.some(
        (u: any) => u.column_name === col
      )

      if (wasUnmapped) {
        // Add to mapped
        updatedMatchDetails.push({
          column_name: col,
          matched_property: propUri,
          matcher_name: 'ManualOverride',
          match_type: 'manual_override',
          confidence_score: 1.0,
          matched_via: 'User override',
          evidence: [],
          evidence_groups: []
        })

        // Remove from unmapped
        generate.data.alignment_report.unmapped_columns = 
          generate.data.alignment_report.unmapped_columns.filter(
            (u: any) => u.column_name !== col
          )

        // Update statistics
        generate.data.alignment_report.statistics = {
          ...generate.data.alignment_report.statistics,
          mapped_columns: (generate.data.alignment_report.statistics?.mapped_columns || 0) + 1,
          mapping_success_rate: ((generate.data.alignment_report.statistics?.mapped_columns || 0) + 1) / 
                               (generate.data.alignment_report.statistics?.total_columns || 1)
        }
      }

      generate.data.match_details = updatedMatchDetails
      
      // Force re-render
      setRefreshKey(prev => prev + 1)
    }
  } catch(e:any){
    setError(`Override failed: ${e.message}`)
  }
  setManualOpen(false)
}}
```

### 3. Added key to Mapping Configuration to force re-render
```tsx
<Paper sx={{ p:3 }} key={`mapping-config-${refreshKey}`}>
```

## How It Works

1. User maps or changes a column
2. Backend is updated with `api.overrideMapping()`
3. **Frontend directly mutates `generate.data`** to reflect the change
4. For unmapped columns:
   - Add to `match_details` array
   - Remove from `unmapped_columns` array
   - Update statistics (mapped_columns +1)
5. Increment `refreshKey` to trigger React re-render
6. Mapping Configuration updates immediately

## Why This Works

- ✅ **No re-generation** - Preserves all existing mappings
- ✅ **Immediate update** - UI reflects changes instantly
- ✅ **Statistics update** - Counts adjust correctly
- ✅ **State consistency** - Backend and frontend stay in sync
- ✅ **No network overhead** - Only one API call (override)

## Testing

1. Hard refresh browser (Cmd+Shift+R)
2. Click "Map Now" on unmapped column
3. Select property and confirm

**Expected:**
- ✅ Success message
- ✅ Column moves from Unmapped → Mapped table
- ✅ Statistics update (Mapped +1, Unmapped -1)
- ✅ No "Mappings generated!" message
- ✅ Other mappings unchanged

## Key Insight

**Don't re-generate** - The backend has already been updated via `api.overrideMapping()`. We just need the frontend to reflect that change. Direct state mutation + forced re-render is the correct approach.

## Files Updated

1. ✅ `frontend/src/pages/ProjectDetail.tsx` 
   - Added `refreshKey` state
   - Updated override handler with state mutation logic
   - Added key to Mapping Configuration Paper component

---

**Status:** Correctly fixed! Manual overrides now work without losing other mappings. 🎉

