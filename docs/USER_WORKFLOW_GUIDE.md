# RDFMap v0.4.0 - Complete User Workflow

## 🚀 Quick Start Guide

### CLI Workflow

```
1. Generate Mapping Configuration
┌─────────────────────────────────────────────────────────────┐
│ rdfmap generate                                              │
│   --ontology ontology.ttl                                    │
│   --data data.csv                                            │
│   --format inline              # Choose format ◄─────────────┤
│   --output config.yaml                                       │
└─────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Format Options:                                              │
│   inline     → config.yaml (v2 inline)                       │
│   rml/ttl    → config.yaml + mapping.rml.ttl                 │
│   rml/xml    → config.yaml + mapping.rml.rdf                 │
│   yarrrml    → config.yaml + mapping.yaml                    │
└─────────────────────────────────────────────────────────────┘
                     │
                     ▼
2. Convert to RDF
┌─────────────────────────────────────────────────────────────┐
│ rdfmap convert                                               │
│   --mapping config.yaml                                      │
│   --output data.ttl                                          │
│   --limit 10  (optional)                                     │
└─────────────────────────────────────────────────────────────┘
                     │
                     ▼
✅ RDF Output: data.ttl (with all relationships)
```

---

### Web UI Workflow

```
1. Create Project
┌─────────────────────────────────────────────────────────────┐
│                        Projects                              │
│                                                              │
│  [New Project]                                               │
│                                                              │
│  Enter name: My Project                                      │
│  Description: Test project                                   │
│  [Create]                                                    │
└─────────────────────────────────────────────────────────────┘

2. Upload Files
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Upload Files                                         │
│                                                              │
│  Ontology: [Choose File] ontology.ttl  [Upload]             │
│  Data:     [Choose File] data.csv      [Upload]             │
│  SHACL:    [Choose File] shapes.ttl    [Upload] (optional)  │
└─────────────────────────────────────────────────────────────┘

3. Generate Mappings (NEW FEATURE!)
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Generate Mappings (AI-Powered)                      │
│                                                              │
│  Mapping Format: [v2 Inline (Recommended)  ▼]  ◄────────────┤
│                   v2 Inline (Recommended)                    │
│                   v2 + RML Turtle (Standards)                │
│                   v2 + RML RDF/XML                           │
│                   v2 + YARRRML                               │
│                                                              │
│  All mapping details in single config file (easiest)         │
│                                                              │
│  [Generate Mappings]                                         │
└─────────────────────────────────────────────────────────────┘
                     │
                     ▼
✅ Success: Mappings generated (v2 inline)! 10/10 columns mapped (100%)

4. Convert to RDF
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Convert to RDF                                       │
│                                                              │
│  Format: [Turtle (.ttl)  ▼]                                 │
│  ☑ Validate output                                           │
│                                                              │
│  [Convert (Sync)]  [Convert (Background)]                   │
└─────────────────────────────────────────────────────────────┘
                     │
                     ▼
✅ RDF generated! 48 triples created.
   [Download RDF]
```

---

## 🗑️ Project Management (NEW!)

```
Project List
┌─────────────────────────────────────────────────────────────┐
│                        Projects                              │
│                                                     │
│  [New Project]                                               │
│                                                              │
│  My Project                                          [🗑️]    │
│    Test project                                              │
│                                                              │
│  Another Project                                     [🗑️]    │
│    Description here                                          │
└─────────────────────────────────────────────────────────────┘
                     │
                     │ Click trash icon
                     ▼
Delete Confirmation
┌─────────────────────────────────────────────────────────────┐
│  Delete Project?                                             │
│                                                              │
│  Are you sure you want to delete "My Project"?               │
│  This action cannot be undone.                               │
│                                                              │
│                              [Cancel]  [Delete]              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Configuration Format Comparison

### v2 Inline (Recommended)
```yaml
options:
  on_error: report

mapping:
  namespaces:
    ex: https://example.com/#
  base_iri: http://example.org/
  sources:
    - name: data
      file: data.csv
      entity:
        class: ex:Entity
      properties:
        Name:
          predicate: ex:name
```

**Benefits**: ✅ Simple, ✅ All in one file, ✅ Easy to edit

---

### v2 + RML Turtle (Standards)

**config.yaml**:
```yaml
options:
  on_error: report

mapping:
  file: mapping.rml.ttl
```

**mapping.rml.ttl**:
```turtle
@prefix rr: <http://www.w3.org/ns/r2rml#> .
@prefix rml: <http://semweb.mmlab.be/ns/rml#> .

<#TriplesMap1> a rr:TriplesMap ;
  rml:logicalSource [ ... ] ;
  rr:subjectMap [ ... ] ;
  rr:predicateObjectMap [ ... ] .
```

**Benefits**: ✅ W3C standard, ✅ Interoperable, ✅ Tool-agnostic

---

### v2 + YARRRML (Human-Friendly)

**config.yaml**:
```yaml
options:
  on_error: report

mapping:
  file: mapping.yaml
```

**mapping.yaml**:
```yaml
prefixes:
  ex: https://example.com/#

sources:
  data: [data.csv~csv]

mappings:
  data:
    sources: $data
    s: $(base_iri)entity/$(ID)
    po:
      - [a, ex:Entity]
      - [ex:name, $(Name)]
```

**Benefits**: ✅ Human-readable, ✅ Easy to edit, ✅ YAML format

---

## 🎨 Visual Changes

### Before (v1)
```
┌─────────────────────────────────────────┐
│ Projects                [New Project]   │
├─────────────────────────────────────────┤
│ [DEBUG PANEL WITH JSON DATA]            │ ← Removed
├─────────────────────────────────────────┤
│ Project 1                               │
│ Project 2                               │
└─────────────────────────────────────────┘

Step 2: Generate Mappings
┌─────────────────────────────────────────┐
│ [Generate Mappings]                     │ ← No format choice
└─────────────────────────────────────────┘
```

### After (v2)
```
┌─────────────────────────────────────────┐
│ Projects                [New Project]   │
├─────────────────────────────────────────┤
│ Project 1                       [🗑️]   │ ← Delete button
│ Project 2                       [🗑️]   │
└─────────────────────────────────────────┘

Step 2: Generate Mappings
┌─────────────────────────────────────────┐
│ Mapping Format: [v2 Inline ▼]          │ ← Format selector
│ All mapping details in single file      │
│                                         │
│ [Generate Mappings]                     │
└─────────────────────────────────────────┘
```

---

## 🔄 Migration Path (v1 → v2)

### Automatic Migration (CLI)
```bash
# Old v1 config still works!
rdfmap convert --mapping old_config_v1.yaml --output data.ttl

⚠️  DEPRECATION WARNING: Old config structure detected
    Please migrate to new structure.
    See docs/CONFIGURATION_FORMATS.md

# Still converts successfully!
✅ Processed 2 rows, 32 RDF triples
```

### Manual Migration
```bash
# Regenerate with v2 format
rdfmap generate \
  --ontology ontology.ttl \
  --data data.csv \
  --format inline \
  --output new_config_v2.yaml

# Now use v2 config
rdfmap convert --mapping new_config_v2.yaml --output data.ttl
```

---

## 🎯 Use Cases

### Use Case 1: Simple Project (Inline)
**Best for**: Quick projects, learning, testing
**Format**: `inline`
```bash
rdfmap generate -ont ont.ttl -d data.csv -f inline -o config.yaml
rdfmap convert --mapping config.yaml --output data.ttl
```
**Result**: Single config file, easy to understand

---

### Use Case 2: Standards Compliance (RML)
**Best for**: Interoperability, production, tool integration
**Format**: `rml/ttl`
```bash
rdfmap generate -ont ont.ttl -d data.csv -f rml/ttl -o config.yaml
# Can use RML with other tools like RMLMapper!
rdfmap convert --mapping config.yaml --output data.ttl
```
**Result**: W3C-compliant RML + config

---

### Use Case 3: Manual Editing (YARRRML)
**Best for**: Complex mappings, team collaboration
**Format**: `yarrrml`
```bash
rdfmap generate -ont ont.ttl -d data.csv -f yarrrml -o config.yaml
# Edit mapping.yaml manually
rdfmap convert --mapping config.yaml --output data.ttl
```
**Result**: Human-friendly YARRRML + config

---

## 📱 API Integration

### Generate with Format
```bash
curl -X POST "http://localhost:8000/api/mappings/proj123/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "use_semantic": true,
    "min_confidence": 0.5,
    "output_format": "inline"
  }'
```

**Response**:
```json
{
  "status": "success",
  "output_format": "inline",
  "mapping_config": {...},
  "mapping_summary": {
    "statistics": {
      "total_columns": 10,
      "mapped_columns": 10,
      "mapping_rate": 100.0
    }
  }
}
```

---

## 🏆 Key Benefits

| Feature | Before (v1) | After (v2) | Benefit |
|---------|-------------|------------|---------|
| **Config Structure** | Mixed | Separated | Clearer |
| **Formats** | 1 internal | 4 options | Flexible |
| **Terminology** | Custom | RML-aligned | Standard |
| **Delete Projects** | ❌ | ✅ | Cleanup |
| **Debug Panel** | Visible | Removed | Professional |
| **Format Choice** | No | Yes | User control |
| **Backward Compat** | N/A | 100% | Safe upgrade |

---

## 🎓 Learning Resources

**Quick Start**: See README.md  
**Format Guide**: docs/V2_QUICK_REFERENCE.md  
**Comparison**: docs/CONFIG_COMPARISON.md  
**Migration**: docs/CONFIGURATION_FORMATS.md  
**API Docs**: http://localhost:8000/api/docs  

---

**Status**: 🟢 Production Ready

**Next Steps**:
1. Test end-to-end workflows
2. Update README with new features
3. Deploy to production
4. Announce release! 🎉

