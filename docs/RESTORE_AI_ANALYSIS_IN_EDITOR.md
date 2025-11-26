# Restored: AI Analysis in Manual Mapping Editor

**Date**: November 25, 2025  
**Feature**: Integrated alignment report evidence into EnhancedMappingModal  
**Status**: 🟢 **COMPLETE**

---

## 🎯 What Was Restored

The **AI analysis/evidence section** that shows users why the AI chose a particular mapping, helping them make informed decisions when manually editing.

### What You See Now

When clicking **Edit** on any AI-generated mapping, the modal shows:

```
┌─────────────────────────────────────────────────────────┐
│ Edit Mapping: Principal → ex:principalAmount           │
├─────────────────────────────────────────────────────────┤
│ [Graph Visualization]  │  Current Mapping              │
│                        │  Principal → principalAmount   │
│  [Cytoscape diagram]   │                                │
│  showing context       │  🤖 AI Analysis                │
│                        │  Confidence: 95.5%             │
│                        │  Matchers: semantic, lexical   │
│                        │  Reasoning: "Strong semantic   │
│                        │  match based on domain expert  │
│                        │  knowledge..."                 │
│                        │                                │
│                        │  Evidence (3):                 │
│                        │  • semantic: Column name       │
│                        │    matches ontology property   │
│                        │  • lexical: Exact name match   │
│                        │  • structural: Correct domain  │
│                        │                                │
│                        │  Other Candidates:             │
│                        │  [loanAmount (67%)]           │
│                        │  [principalBalance (45%)]     │
│                        │                                │
│                        │  💡 Suggested Alternatives     │
│                        │  ...                           │
│                        │                                │
│                        │  All Properties                │
│                        │  [Search...]                   │
│                        │  ...                           │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Technical Implementation

### Backend API (Already Existed!)

Two endpoints for evidence data:

**1. Get evidence for specific column**:
```
GET /api/mappings/{project_id}/evidence/{column_name}
```

**2. Get all evidence**:
```
GET /api/mappings/{project_id}/evidence
```

Both read from `alignment_report.json` generated during AI mapping.

---

### Frontend Changes

**File**: `frontend/src/components/EnhancedMappingModal.tsx`

#### 1. Added Props & State
```typescript
interface EnhancedMappingModalProps {
  // ...existing props...
  projectId: string  // NEW!
}

const [evidenceData, setEvidenceData] = useState<any>(null)
const [loadingEvidence, setLoadingEvidence] = useState(false)
```

#### 2. Fetch Evidence on Modal Open
```typescript
useEffect(() => {
  if (!open || !mappingRow || !projectId) return

  const fetchEvidence = async () => {
    const response = await fetch(
      `/api/mappings/${projectId}/evidence/${encodeURIComponent(mappingRow.columnName)}`
    )
    if (response.ok) {
      const data = await response.json()
      setEvidenceData(data.evidence_detail)
    }
  }

  fetchEvidence()
}, [open, mappingRow, projectId])
```

#### 3. Display Evidence Section
```typescript
{evidenceData && (
  <Paper variant="outlined">
    <Typography variant="subtitle2">🤖 AI Analysis</Typography>
    
    {/* Confidence Score */}
    <Chip label={`${(evidenceData.confidence * 100).toFixed(1)}%`} />
    
    {/* Matchers */}
    <Typography>Matchers: {evidenceData.matchers_fired.join(', ')}</Typography>
    
    {/* Reasoning */}
    <Typography>{evidenceData.reasoning}</Typography>
    
    {/* Evidence Items */}
    {evidenceData.evidence.map(ev => (
      <Box>
        <strong>{ev.type}:</strong> {ev.description}
        <Chip label={`Score: ${ev.score}`} />
      </Box>
    ))}
    
    {/* Alternate Candidates */}
    {evidenceData.alternate_candidates.map(alt => (
      <Chip 
        label={`${alt.property_label} (${alt.confidence}%)`}
        onClick={() => setSelectedProperty(alt.property)}
      />
    ))}
  </Paper>
)}
```

---

## 📊 Evidence Data Structure

From `alignment_report.json`:

```json
{
  "column_name": "Principal",
  "mapped_property": "ex:principalAmount",
  "confidence": 0.955,
  "matchers_fired": ["semantic", "lexical", "structural"],
  "reasoning": "Strong semantic match based on domain context...",
  "evidence": [
    {
      "type": "semantic",
      "matcher": "SemanticMatcher",
      "description": "Column name semantically matches property",
      "score": 0.95
    },
    {
      "type": "lexical",
      "matcher": "LexicalMatcher",
      "description": "Exact name match",
      "score": 1.0
    }
  ],
  "alternate_candidates": [
    {
      "property": "ex:loanAmount",
      "property_label": "loanAmount",
      "confidence": 0.67,
      "reasoning": "Possible alternative based on domain"
    }
  ]
}
```

---

## 🎯 User Benefits

### Before (Missing)
- ❌ No context for why AI chose a mapping
- ❌ Users had to trust AI blindly
- ❌ No alternative suggestions from AI
- ❌ No confidence scores visible

### After (Restored)
- ✅ **Confidence scores** - See how sure the AI is
- ✅ **Matchers fired** - Understand which algorithms contributed
- ✅ **Reasoning** - Read AI's explanation
- ✅ **Evidence list** - See detailed evidence items with scores
- ✅ **Alternate candidates** - Clickable alternatives from AI analysis
- ✅ **Make informed decisions** - Choose better when overriding

---

## 🚀 User Workflows

### Workflow 1: Review High-Confidence Mapping
```
1. Generate mappings with AI
2. See "Principal → ex:principalAmount"
3. Click [Edit] to review
4. Modal shows:
   - Confidence: 95.5% ✅
   - Reasoning: Strong semantic match
   - Evidence: 3 items, all positive
5. User: "Looks good, I'll keep it"
6. Click [Cancel] to close
✅ Confident in AI's choice!
```

---

### Workflow 2: Override Low-Confidence Mapping
```
1. Generate mappings with AI
2. See "Status → ex:loanStatus" 
3. Click [Edit] to review
4. Modal shows:
   - Confidence: 62.3% ⚠️
   - Reasoning: Ambiguous field name
   - Evidence: Mixed signals
   - Other Candidates:
     • ex:statusCode (58%)
     • ex:applicationStatus (45%)
5. User reviews graph context
6. User clicks "ex:statusCode" from candidates
7. Click [Save]
✅ Made informed override decision!
```

---

### Workflow 3: Explore Alternatives
```
1. Edit mapping
2. See AI analysis with 3 alternate candidates
3. Click on alternate candidate chip
4. Property is selected in list
5. Graph updates to show new property context
6. User compares original vs alternate
7. Chooses best option based on evidence
✅ Explored alternatives with AI guidance!
```

---

## 🎨 Visual Layout

**Evidence Section Position**:
```
Right Panel (30% width):
  ┌─────────────────────────┐
  │ Current Mapping         │ ← Always visible
  ├─────────────────────────┤
  │ 🤖 AI Analysis          │ ← NEW! Shows when evidence exists
  │   Confidence: 95.5%     │
  │   Matchers: ...         │
  │   Reasoning: ...        │
  │   Evidence (3): ...     │
  │   Other Candidates: ... │
  ├─────────────────────────┤
  │ 💡 Suggested Alts       │ ← From ontology analysis
  ├─────────────────────────┤
  │ All Properties          │ ← Search & browse
  │ [Search...]             │
  │ [List...]               │
  └─────────────────────────┘
```

**Scrollable**: Evidence section scrolls if too long  
**Collapsible**: Could add collapse feature in future

---

## ✅ Integration Points

### Works With
- ✅ **RML Workflow**: No evidence (section doesn't show)
- ✅ **YARRRML Workflow**: No evidence (section doesn't show)
- ✅ **AI-Generated Workflow**: Shows rich evidence ✨
- ✅ **Manual Overrides**: Evidence preserved, can be reviewed later

### Fallback Behavior
- If `alignment_report.json` doesn't exist → No evidence section (graceful)
- If column not in report → No evidence section (graceful)
- If evidence fetch fails → Log warning, continue without evidence

---

## 🔍 Edge Cases Handled

| Scenario | Behavior |
|----------|----------|
| No alignment report file | Section doesn't show |
| Column not in report | Section doesn't show |
| API returns 404 | Section doesn't show |
| Evidence array empty | Shows confidence but no evidence list |
| No alternate candidates | Doesn't show candidates section |
| Loading evidence | Shows spinner |

---

## Files Modified

1. ✅ `frontend/src/components/EnhancedMappingModal.tsx`
   - Added `projectId` prop
   - Added `evidenceData` and `loadingEvidence` state
   - Added `useEffect` to fetch evidence
   - Added Evidence section UI with:
     - Confidence score chip
     - Matchers list
     - Reasoning text
     - Evidence items with scores
     - Clickable alternate candidates

2. ✅ `frontend/src/pages/ProjectDetail.tsx`
   - Pass `projectId` prop to EnhancedMappingModal

---

## 🎯 Result

**AI analysis is back in the manual editor!**

✅ **Evidence displayed** - See why AI chose this mapping  
✅ **Confidence scores** - Know how sure AI is  
✅ **Reasoning shown** - Understand AI's logic  
✅ **Evidence items** - Review detailed evidence  
✅ **Alternate candidates** - Click to explore alternatives  
✅ **Informed decisions** - Make better overrides  
✅ **Only for AI workflow** - Gracefully absent for RML/YARRRML

**Users can now confidently review and override AI-generated mappings with full context!** 🎉

---

**Status**: 🟢 **COMPLETE**

**Test it**: Generate mappings with AI, click Edit on any property, see the AI Analysis section with evidence!

