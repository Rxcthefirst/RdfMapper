# Docker Components Update - v2 Configuration Support

**Date**: November 24, 2025  
**Status**: 🟢 **COMPLETE**  
**Changes**: Backend API updated to support v2 configuration format

---

## Summary

Updated the Docker backend API to support the new v2 configuration structure with multiple output formats (inline, rml/ttl, rml/xml, yarrrml).

---

## Changes Made

### 1. Backend Service (`backend/app/services/rdfmap_service.py`)

#### Updated `generate_mappings()` Method

**New Parameter**: `output_format` - Controls mapping generation format

**Supported Formats**:
- `inline` - v2 config with mapping inline (default, recommended)
- `rml/ttl` - v2 config + external RML Turtle file
- `rml/xml` - v2 config + external RML RDF/XML file  
- `yarrrml` - v2 config + external YARRRML file

**Implementation**:
```python
def generate_mappings(
    self,
    project_id: str,
    ontology_file_path: str,
    data_file_path: str,
    target_class: Optional[str] = None,
    base_iri: str = "http://example.org/",
    use_semantic: bool = True,
    min_confidence: float = 0.5,
    output_format: str = "inline",  # NEW
) -> Dict[str, Any]:
```

**Flow**:
1. Generate internal mapping using `MappingGenerator`
2. Convert to requested format using v2 generators
3. Save config file (and external mapping file if needed)
4. Return mapping config, alignment report, and summary

#### Updated `summarize_mapping()` Method

**Now supports both formats**:
- V1 format: `sheets`, `columns`, `objects`
- V2 format: `mapping.sources`, `properties`, `relationships`

**Auto-detection**:
```python
if "mapping" in mapping_config:
    # V2 format
    sources = mapping_config["mapping"].get("sources", [])
    use_v2 = True
else:
    # V1 format
    sources = mapping_config.get('sheets', [])
    use_v2 = False
```

### 2. API Router (`backend/app/routers/mappings.py`)

#### Updated `/api/mappings/{project_id}/generate` Endpoint

**New Query Parameter**:
```python
output_format: str = Query(
    "inline", 
    description="Output format: inline (v2 default), rml/ttl, rml/xml, yarrrml"
)
```

**Response Enhancement**:
```python
{
    "status": "success",
    "project_id": "...",
    "mapping_file": "...",
    "output_format": "inline",  # NEW - indicates which format was generated
    "mapping_preview": {
        "base_iri": "...",
        "target_class": "...",
        "column_count": 10
    },
    "alignment_report": {...},
    "mapping_summary": {...}
}
```

**Auto-detection for preview**:
- Handles both v1 (`sheets`) and v2 (`mapping.sources`) formats
- Extracts base_iri, target_class, and column_count from appropriate location

---

## API Usage Examples

### Generate v2 Inline Config (Default)

```bash
curl -X POST "http://localhost:8000/api/mappings/project123/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "base_iri": "http://example.org/",
    "use_semantic": true,
    "output_format": "inline"
  }'
```

**Result**: Creates `mapping_config.yaml` with v2 inline structure

### Generate v2 with External RML

```bash
curl -X POST "http://localhost:8000/api/mappings/project123/generate?output_format=rml/ttl"
```

**Result**: Creates:
- `mapping_config.yaml` - v2 config with reference
- `mapping.rml.ttl` - Standard RML Turtle file

### Generate v2 with External YARRRML

```bash
curl -X POST "http://localhost:8000/api/mappings/project123/generate?output_format=yarrrml"
```

**Result**: Creates:
- `mapping_config.yaml` - v2 config with reference
- `mapping_yarrrml.yaml` - YARRRML file

---

## Backward Compatibility

### V1 Configs Still Work ✅

- Existing v1 configs can still be converted
- `convert_to_rdf()` uses `load_mapping_config()` which auto-migrates
- No breaking changes to existing projects

### Auto-Migration

The loader (`src/rdfmap/config/loader.py`) automatically:
1. Detects config version (v1 vs v2)
2. Shows deprecation warning for v1
3. Converts v2 to v1 internally for the engine
4. Processes normally

---

## Frontend Integration (Next Step)

### UI Updates Needed

**1. Add Format Selector to Mapping Generation**

```typescript
// Add dropdown for output format selection
const formatOptions = [
  { value: 'inline', label: 'v2 Inline (Recommended)' },
  { value: 'rml/ttl', label: 'RML Turtle (Standards)' },
  { value: 'rml/xml', label: 'RML RDF/XML' },
  { value: 'yarrrml', label: 'YARRRML (Human-Friendly)' }
];

// Include in API call
const response = await fetch(`/api/mappings/${projectId}/generate`, {
  method: 'POST',
  body: JSON.stringify({
    ...otherParams,
    output_format: selectedFormat
  })
});
```

**2. Display Format in UI**

```typescript
// Show which format was generated
<Badge>{response.output_format}</Badge>

// If external format, show both files
{response.output_format !== 'inline' && (
  <FileList>
    <File>mapping_config.yaml (v2 config)</File>
    <File>mapping.rml.ttl (RML mapping)</File>
  </FileList>
)}
```

**3. Update Config Viewer**

```typescript
// Handle both v1 and v2 in config display
const getEntityClass = (config) => {
  if (config.mapping?.sources) {
    // v2 format
    return config.mapping.sources[0]?.entity?.class;
  } else {
    // v1 format
    return config.sheets?.[0]?.row_resource?.class;
  }
};
```

---

## Testing

### Test Backend API

```bash
# Start backend
cd backend
uvicorn app.main:app --reload

# Test inline generation
curl -X POST "http://localhost:8000/api/mappings/test/generate?output_format=inline"

# Test RML generation
curl -X POST "http://localhost:8000/api/mappings/test/generate?output_format=rml/ttl"

# Test YARRRML generation
curl -X POST "http://localhost:8000/api/mappings/test/generate?output_format=yarrrml"
```

### Verify Files

```bash
# Check generated files
ls -la data/test/
# Should show:
# - mapping_config.yaml (v2 config)
# - mapping.rml.ttl (if rml/ttl format)
# - mapping_yarrrml.yaml (if yarrrml format)

# Validate format
head -20 data/test/mapping_config.yaml
# Should show v2 structure with "mapping:" section
```

---

## Configuration Examples

### Example: Inline Format Output

```yaml
# RDFMap v2 Configuration (Generated via Web UI)
# Format: inline mapping

options:
  on_error: report
  skip_empty_values: true
  chunk_size: 1000

imports:
  - /uploads/project123/ontology.ttl

mapping:
  namespaces:
    xsd: http://www.w3.org/2001/XMLSchema#
    ex: https://example.com/#
  
  base_iri: http://example.org/
  
  sources:
    - name: data
      file: /uploads/project123/data.csv
      format: csv
      entity:
        class: ex:Entity
        iri_template: "{base_iri}entity/{ID}"
      properties:
        Name:
          predicate: ex:name
          datatype: xsd:string
```

### Example: External RML Format Output

**mapping_config.yaml**:
```yaml
# RDFMap v2 Configuration (Generated via Web UI)
# Format: external TURTLE
# RML file: mapping.rml.ttl

options:
  on_error: report

imports:
  - /uploads/project123/ontology.ttl

mapping:
  file: mapping.rml.ttl
```

**mapping.rml.ttl**:
```turtle
@prefix rr: <http://www.w3.org/ns/r2rml#> .
@prefix rml: <http://semweb.mmlab.be/ns/rml#> .
...
```

---

## Docker Compose

No changes needed to `docker-compose.yml` - the updated Python code is automatically picked up via volume mounts:

```yaml
services:
  api:
    volumes:
      - ./backend:/app
      - ./src/rdfmap:/usr/local/lib/python3.11/site-packages/rdfmap
```

The updated rdfmap library code is mounted directly.

---

## Deployment

### Development

```bash
# Rebuild backend if needed
docker-compose build api worker

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f api
```

### Production

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# Backend will use latest rdfmap from PyPI
# Or build with local rdfmap if needed
```

---

## Next Steps

1. ✅ **Backend API** - Complete (this document)
2. ⏳ **Frontend UI** - Add format selector, update config viewer
3. ⏳ **Testing** - End-to-end testing with all formats
4. ⏳ **Documentation** - Update user guide with format options
5. ⏳ **Docker Images** - Build and publish updated images

---

## Files Modified

- ✅ `backend/app/services/rdfmap_service.py` - Updated generate_mappings and summarize_mapping
- ✅ `backend/app/routers/mappings.py` - Updated API endpoint with format parameter

---

## Benefits

✅ **Format Flexibility** - Users can choose output format via API  
✅ **Standards Compliance** - Can generate pure RML for interoperability  
✅ **Backward Compatible** - Old v1 configs still work  
✅ **Future-Proof** - Clean v2 structure for future enhancements  
✅ **User Choice** - Inline for simplicity, external for standards

---

**Status**: 🟢 **BACKEND COMPLETE - READY FOR FRONTEND UPDATES**

The backend now fully supports v2 configuration generation with multiple formats. Frontend updates needed to expose format selector to users.

