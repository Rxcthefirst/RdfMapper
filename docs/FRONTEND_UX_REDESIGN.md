# Frontend UI/UX Redesign - Project Detail Page

**Date**: November 24, 2025  
**Issue**: Redundant inputs, poor organization, imported mappings not visible  
**Solution**: Complete UI reorganization with clearer workflow

---

## Problems Identified

1. **Redundant Ontology Upload**: Appears in both "Step 1" and "Knowledge Inputs"
2. **Poor Organization**: Import existing mapping in separate dashed box
3. **Missing Functionality**: Imported mappings don't display, can't be used
4. **Forced AI Generation**: Must generate new mapping even if one was imported
5. **Confusing Layout**: "Knowledge Inputs" mixes validation with core uploads

---

## Proposed Redesign

### New Structure

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Upload Required Files                               │
│                                                              │
│ 📊 Data File [Required]                                     │
│   CSV, JSON, or Excel file containing your data             │
│   [Choose File] [Upload] [✓ Uploaded]                       │
│                                                              │
│ ─────────────────────────────────────────────────────────── │
│                                                              │
│ 🎯 Ontology File [Required]                                 │
│   TTL, RDF/XML, or OWL file defining your data model        │
│   [Choose File] [Upload] [✓ Uploaded]                       │
│                                                              │
│ ─────────────────────────────────────────────────────────── │
│                                                              │
│ 📦 Existing Mapping [Optional]                              │
│   Already have RML/YARRRML? Import it and skip Step 2       │
│   [Choose File] [Import] [✓ Mapping Available]              │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Step 1b: Additional Knowledge (Optional)                    │
│ Enhance mapping quality and enable validation                │
│                                                              │
│ 📚 SKOS Vocabularies                                         │
│   Add controlled vocabularies for better term matching       │
│   [Choose File] [Add SKOS] [2 file(s)]                      │
│   [vocab1.ttl ×] [vocab2.ttl ×]                             │
│                                                              │
│ ✓ SHACL Shapes                                              │
│   Add validation rules to ensure data quality                │
│   [Choose File] [Add Shapes] [✓ Added]                      │
│   [shapes.ttl ×]                                            │
│                                                              │
│ 🧠 Reasoning                                                 │
│   Enable OWL reasoning to infer additional relationships     │
│   [✓ Enabled] / [Enable]                                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Step 2: Create or Review Mapping                            │
│                                                              │
│ [Option A: Generate with AI]  [Option B: View Imported]    │
│                                                              │
│ If Option A:                                                 │
│   Mapping Format: [v2 Inline ▼]                             │
│   [Generate Mappings]                                        │
│                                                              │
│ If Option B (or after generation):                           │
│   ┌───────────────────────────────────────────────────────┐ │
│   │ Mapping Preview                                       │ │
│   │ ─────────────────────────────────────────────────────│ │
│   │ • loans → ex:MortgageLoan                            │ │
│   │   LoanID → ex:loanNumber (xsd:string)      [Edit]   │ │
│   │   Principal → ex:principalAmount (xsd:int)  [Edit]   │ │
│   │   → ex:hasBorrower (ex:Borrower)            [Edit]   │ │
│   │      BorrowerName → ex:borrowerName                   │ │
│   │   → ex:collateralProperty (ex:Property)     [Edit]   │ │
│   │      PropertyAddress → ex:propertyAddress             │ │
│   │                                                       │ │
│   │ [View Full Mapping] [Download YAML] [Download RML]   │ │
│   └───────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Step 3: Convert to RDF                                       │
│                                                              │
│ Output Format: [Turtle (.ttl) ▼]                            │
│ ☑ Validate output                                            │
│                                                              │
│ [Convert (Sync)] [Convert (Background)]                     │
│                                                              │
│ ✅ RDF generated! 48 triples created.                       │
│ [Download RDF]                                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Changes

### 1. Consolidated Step 1
- **Before**: Separate sections for uploads and "Knowledge Inputs" with redundant ontology
- **After**: Single "Step 1" with all required files (data, ontology, optional mapping)
- **Benefit**: Clear, no redundancy, logical flow

### 2. Moved Import Existing Mapping
- **Before**: Separate dashed box between uploads and generation
- **After**: Part of Step 1 as third optional input
- **Benefit**: Users see it as an alternative path immediately

### 3. Step 1b for Optional Enhancements
- **Before**: Mixed with core uploads in "Knowledge Inputs"
- **After**: Separate optional section clearly labeled
- **Benefit**: Doesn't clutter required workflow, but available for advanced users

### 4. NEW: Mapping Preview
- **Before**: Imported mappings invisible, can't be used
- **After**: "Step 2" shows mapping preview for both imported and generated mappings
- **Benefit**: Users can see what they imported, verify it before conversion

### 5. Option A/B in Step 2
- **Before**: Forced to generate even with imported mapping
- **After**: Two clear options:
  - Option A: Generate new mapping with AI
  - Option B: Review imported mapping
- **Benefit**: Respects user's workflow choice

---

## Implementation Details

### Step 1: Required Files (Revised)

```tsx
<Paper sx={{ p: 3 }}>
  <Typography variant="h6" gutterBottom>
    Step 1: Upload Required Files
  </Typography>
  
  <Stack spacing={3}>
    {/* Data File */}
    <Box>
      <Typography variant="subtitle2" gutterBottom>
        📊 Data File <Chip label="Required" size="small" color="error" />
      </Typography>
      <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
        CSV, JSON, or Excel file containing your data
      </Typography>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <input type="file" id="data-file" accept=".csv,.xlsx,.json,.xml" />
        <Button onClick={() => uploadData.mutate()} startIcon={<CloudUploadIcon />}>
          Upload
        </Button>
        {projectQuery.data?.data_file && (
          <Chip label="✓ Uploaded" color="success" size="small" />
        )}
      </Box>
    </Box>

    <Divider />

    {/* Ontology File - NO REDUNDANCY */}
    <Box>
      <Typography variant="subtitle2" gutterBottom>
        🎯 Ontology File <Chip label="Required" size="small" color="error" />
      </Typography>
      <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
        TTL, RDF/XML, or OWL file defining your data model
      </Typography>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <input type="file" id="ont-file" accept=".ttl,.rdf,.owl" />
        <Button onClick={() => uploadOntology.mutate()} startIcon={<CloudUploadIcon />}>
          Upload
        </Button>
        {projectQuery.data?.ontology_file && (
          <Chip label="✓ Uploaded" color="success" size="small" />
        )}
      </Box>
    </Box>

    <Divider />

    {/* Existing Mapping - MOVED HERE */}
    <Box>
      <Typography variant="subtitle2" gutterBottom>
        📦 Existing Mapping <Chip label="Optional" size="small" />
      </Typography>
      <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
        Already have RML/YARRRML? Import it and skip Step 2 generation
      </Typography>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <input type="file" id="existing-mapping-file" accept=".ttl,.rdf,.yaml,.yml" />
        <Button onClick={() => uploadExistingMapping.mutate()} startIcon={<CloudUploadIcon />}>
          Import
        </Button>
        {mappingYamlQuery.data && (
          <Chip label="✓ Mapping Available" color="success" size="small" />
        )}
      </Box>
    </Box>
  </Stack>
</Paper>
```

### Step 2: NEW Mapping Preview

```tsx
<Paper sx={{ p: 3 }}>
  <Typography variant="h6" gutterBottom>
    Step 2: Create or Review Mapping
  </Typography>

  {/* Show tabs if mapping exists */}
  {mappingYamlQuery.data ? (
    <Box>
      <Tabs value={mappingTab} onChange={(e, v) => setMappingTab(v)}>
        <Tab label="View Imported Mapping" value="view" />
        <Tab label="Generate New Mapping" value="generate" />
      </Tabs>

      {mappingTab === 'view' && (
        <Box sx={{ mt: 2 }}>
          <Alert severity="success" sx={{ mb: 2 }}>
            Mapping available! You can proceed to Step 3 (Convert) or generate a new one.
          </Alert>
          
          {/* Mapping Preview Component */}
          <MappingPreview 
            mappingYaml={mappingYamlQuery.data}
            onEdit={(column) => handleEditMapping(column)}
          />

          <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
            <Button variant="outlined" onClick={() => downloadMapping('yaml')}>
              Download YAML
            </Button>
            <Button variant="outlined" onClick={() => downloadMapping('rml')}>
              Download RML
            </Button>
          </Stack>
        </Box>
      )}

      {mappingTab === 'generate' && (
        <Box sx={{ mt: 2 }}>
          {/* Format selector and generate button */}
          <GenerateMappingForm />
        </Box>
      )}
    </Box>
  ) : (
    // No mapping yet, only show generate option
    <Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Generate mappings using AI-powered semantic matching
      </Typography>
      <GenerateMappingForm />
    </Box>
  )}
</Paper>
```

### NEW: MappingPreview Component

```tsx
const MappingPreview = ({ mappingYaml, onEdit }) => {
  // Parse YAML to extract mapping structure
  const mapping = useMemo(() => parseMappingYaml(mappingYaml), [mappingYaml])

  return (
    <Box sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 1, p: 2 }}>
      <Typography variant="subtitle2" gutterBottom>Mapping Preview</Typography>
      
      {mapping.sources?.map((source) => (
        <Box key={source.name} sx={{ mb: 2 }}>
          <Typography variant="body2" fontWeight="bold">
            {source.name} → {source.entity?.class}
          </Typography>
          
          {/* Data properties */}
          <Stack sx={{ ml: 2, mt: 1 }} spacing={0.5}>
            {Object.entries(source.properties || {}).map(([col, prop]) => (
              <Box key={col} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="body2" sx={{ fontSize: '0.875rem' }}>
                  {col} → {prop.predicate} ({prop.datatype})
                </Typography>
                <IconButton size="small" onClick={() => onEdit(col)}>
                  <EditIcon fontSize="small" />
                </IconButton>
              </Box>
            ))}
            
            {/* Relationships */}
            {source.relationships?.map((rel, idx) => (
              <Box key={idx} sx={{ ml: 2, mt: 1, p: 1, bgcolor: 'action.hover', borderRadius: 1 }}>
                <Typography variant="body2" fontWeight="bold">
                  → {rel.predicate} ({rel.class})
                </Typography>
                <Stack sx={{ ml: 2 }} spacing={0.5}>
                  {Object.entries(rel.properties || {}).map(([col, prop]) => (
                    <Typography key={col} variant="body2" sx={{ fontSize: '0.875rem' }}>
                      {col} → {prop.predicate}
                    </Typography>
                  ))}
                </Stack>
              </Box>
            ))}
          </Stack>
        </Box>
      ))}
    </Box>
  )
}
```

---

## Benefits

### User Experience
✅ **Clearer Workflow**: Logical progression through steps  
✅ **No Redundancy**: Single ontology upload location  
✅ **Visible Mappings**: Can see what was imported  
✅ **Flexible Path**: Generate OR import, not forced  
✅ **Optional Enhancements**: Clear separation of advanced features

### Technical
✅ **Better Organization**: Related features grouped  
✅ **Conditional Rendering**: Show preview only when mapping exists  
✅ **Extensible**: Easy to add edit functionality  
✅ **Maintainable**: Clear component boundaries

---

## Implementation Steps

1. **Consolidate Step 1** ✅
   - Merge data + ontology + existing mapping
   - Remove redundant ontology upload
   - Add status chips for each upload

2. **Create Step 1b (Optional)** ✅
   - Move SKOS, SHACL, Reasoning here
   - Add clear "Optional" labeling
   - Keep visual separation

3. **Add Mapping Preview Component** 🆕
   - Parse v1/v2 YAML
   - Display sources, properties, relationships
   - Add edit buttons (can wire up later)

4. **Redesign Step 2** 🆕
   - Add tabs: "View Imported" vs "Generate New"
   - Show preview when mapping exists
   - Allow proceeding to Step 3 without regenerating

5. **Update Logic** 🆕
   - Check for existing mapping before showing tabs
   - Enable Step 3 if mapping exists (imported or generated)
   - Add download mapping buttons

---

## Migration Path

### Phase 1: Immediate Fixes
- Remove duplicate ontology upload
- Move existing mapping import to Step 1
- Consolidate into clean sections

### Phase 2: Add Preview (Critical!)
- Create MappingPreview component
- Parse YAML to show structure
- Display in Step 2

### Phase 3: Enable Editing
- Add edit mapping functionality
- Manual override UI
- Save edited mappings

---

**Status**: Design Complete, Ready for Implementation

This redesign addresses all identified issues and creates a clear, logical workflow for users.

