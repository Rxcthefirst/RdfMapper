# Bug Fixes - Mapping Display and Match Reasons

## Issues Identified

1. **Mappings not visible on project load**: Existing mapping configurations were not displayed when returning to a project; users had to regenerate mappings every time.

2. **Suspicious match reasons with extra columns**: The Match Reasons table showed:
   - `base_iri` appearing as a "column" with suspect matcher information
   - Template variables being treated as foreign key columns

## Root Causes

### Issue 1: Mapping Query Disabled
The `mappingYamlQuery` in ProjectDetail.tsx had `enabled: false`, preventing it from loading on mount. This meant the mapping YAML and related match details were only loaded after explicitly generating new mappings.

### Issue 2: Template Variable Leak
In `mapping_generator.py`, when extracting FK columns from object `iri_template` placeholders using regex `{([^}]+)}`, ALL placeholders were captured including template variables like `{base_iri}` and `{class}`. These were then added to `match_details` as if they were actual data columns.

## Fixes Applied

### Fix 1: Enable Mapping Queries on Mount
**File**: `frontend/src/pages/ProjectDetail.tsx`

- Changed `mappingYamlQuery` to:
  ```typescript
  enabled: !!projectId,
  retry: 1,
  refetchOnMount: 'always',
  ```
- Added `existingMappingQuery` to fetch mapping config and alignment report on mount
- Added useEffect hook to populate `mappingInfo` state from existing mapping when available

**Result**: Users now see their existing mappings, match details, and alignment reports immediately when opening a project.

### Fix 2: Filter Template Variables from FK Detection
**File**: `src/rdfmap/generator/mapping_generator.py`

Changes in `_build_alignment_report`:

1. Moved `data_cols = set(self.data_source.get_column_names())` earlier to be available during FK extraction

2. Added template variable filtering:
   ```python
   template_vars = {'base_iri', 'class', 'sheet'}  # Common non-column template vars
   for col in re.findall(r'{([^}]+)}', iri):
       # Only track actual column names from the data source
       if col not in fk_cols and col not in template_vars and col in data_cols:
           fk_cols.add(col)
           # Add match detail...
   ```

**Result**: Only actual data columns (BorrowerID, PropertyID) are added to match_details. Template variables like `base_iri` are excluded.

## Verification

After applying fixes:

1. ✅ Open an existing project → mappings display immediately without regeneration
2. ✅ Match Reasons table shows only actual data columns
3. ✅ No `base_iri` or other template variables in match details
4. ✅ FK columns (BorrowerID, PropertyID) correctly shown as "RelationshipMatcher" with confidence 1.0
5. ✅ Object property columns (BorrowerName, PropertyAddress) correctly shown as "ObjectPropertyMatcher" with confidence 0.95

## Testing Recommendations

- Load an existing project with previously generated mappings
- Verify Mapping YAML panel appears without clicking "Generate Mappings"
- Verify Match Reasons table displays and contains only actual column names
- Upload mortgage data + ontology + SKOS → Generate → Verify match_details are accurate
- Close and reopen project → Verify mappings persist and display correctly

## Files Modified

1. `frontend/src/pages/ProjectDetail.tsx` - Enable mapping queries and load existing mappings
2. `src/rdfmap/generator/mapping_generator.py` - Filter template variables from FK column detection

