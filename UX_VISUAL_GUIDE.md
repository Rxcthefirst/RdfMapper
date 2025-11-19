# Quick Visual Guide - New UX

## Before vs After

### BEFORE ❌
```
┌─────────────────────────────────────────────┐
│ Mapping YAML                                │
│ ┌─────────────────────────────────────────┐│
│ │ namespaces:                             ││
│ │   base: http://example.org/             ││
│ │ defaults:                               ││
│ │   base_iri: http://example.org/         ││
│ │ sheets:                                 ││
│ │   - name: Sheet1                        ││
│ │     ...                                 ││
│ └─────────────────────────────────────────┘│
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Alignment Report                            │
│ Success rate: 74.5% • Avg confidence: 0.87  │
│ Weak matches: 3 • Unmapped: 12              │
│                                             │
│ [Download JSON] [Download HTML] [YAML]      │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Reasoning Metrics                           │
│ [Inferred types: 42] [Inverse links: 15]   │
│ [Transitive links: 8] [Symmetric: 3]       │
│ [Cardinality violations: 2] ...            │
└─────────────────────────────────────────────┘
```

### AFTER ✅
```
┌─────────────────────────────────────────────────────┐
│ Mapping Configuration                               │
│ Review and refine the automated mappings...         │
│                                                     │
│ [Success Rate: 74.5%] [Avg Confidence: 0.87]      │
│ [Mapped: 35] [Unmapped: 12]                       │
│                                                     │
│ ✅ Mapped Columns                                   │
│ ┌─────────────────────────────────────────────────┐│
│ │ Column      │ Property │ Conf │ Actions        ││
│ ├─────────────┼──────────┼──────┼────────────────┤│
│ │ Age         │ age      │ 81%  │ [Evidence][Change]││
│ │ Name        │ fullName │ 92%  │ [Evidence][Change]││
│ │ Email       │ email    │ 95%  │ [Evidence][Change]││
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ ⚠️ Unmapped Columns                                 │
│ ┌─────────────────────────────────────────────────┐│
│ │ Column      │ Sample Values  │ Type  │ Actions ││
│ ├─────────────┼────────────────┼───────┼─────────┤│
│ │ Office Loc  │ Bldg A - F3... │ str   │ [Map Now]││
│ │ Badge ID    │ B12345, B12... │ str   │ [Map Now]││
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ ─────────────────────────────────────────────      │
│ Export configuration or reports for documentation   │
│ [Report JSON] [Report HTML] [Config YAML]         │
└─────────────────────────────────────────────────────┘
```

---

## User Actions

### 1. Review Mapped Columns
```
User sees: Age → age (81%)
User thinks: "Why 81%? Is this right?"
User clicks: [Evidence]
System shows: 
  ✅ Semantic: 2 matchers (avg: 0.85)
  ⭐ Ontological: 2 validators (avg: 0.77)
  💡 Reasoning: "Semantic match validated..."
User thinks: "Ok, makes sense!"
```

### 2. Change Incorrect Mapping
```
User sees: Salary → email (80%)
User thinks: "That's wrong!"
User clicks: [Change]
System shows: Property selector modal
User searches: "salary"
User selects: hasAmount
User clicks: [Map Column]
System updates: Salary → hasAmount (100%)
User thinks: "Fixed!"
```

### 3. Map Unmapped Column
```
User sees: ⚠️ Office Location (sample: "Bldg A - F3")
User thinks: "What should this be?"
User clicks: [Map Now]
System shows: Property selector modal
User searches: "location"
User selects: workLocation
User clicks: [Map Column]
System updates: Office Location → workLocation
User thinks: "Done!"
```

---

## Visual Indicators

### Statistics Chips
```
[Success Rate: 74.5%]  ← Blue outline
[Avg Confidence: 0.87] ← Green outline
[Mapped: 35]           ← Green filled
[Unmapped: 12]         ← Orange filled (warning)
```

### Confidence Colors
```
95%+ → Green   ✓ High confidence
80%+ → Green   ✓ Good
60%+ → Yellow  ⚠️ Review
<60% → Red     ❌ Uncertain
```

### Section Emojis
```
✅ Mapped Columns    → All good
⚠️ Unmapped Columns  → Needs attention
```

### Table Borders
```
Mapped:   1px solid gray      (neutral)
Unmapped: 2px solid orange    (warning/action)
```

---

## Information Flow

### What User Sees
```
┌──────────────────┐
│ Friendly Tables  │ ← User interacts here
└────────┬─────────┘
         │
         │ Clicks buttons
         ▼
┌──────────────────┐
│ Property Selector│ ← Modal with search
└────────┬─────────┘
         │
         │ Confirms selection
         ▼
┌──────────────────┐
│ API Call         │ ← Backend updates YAML
└────────┬─────────┘
         │
         │ Success response
         ▼
┌──────────────────┐
│ UI Updates       │ ← Table refreshes
└──────────────────┘
```

### What System Does (Hidden)
```
User Action → Override API → Update mapping_config.yaml
                          → Update alignment_report.json
                          → Return success
                          
Convert to RDF → Load mapping_config.yaml
              → Apply all mappings
              → Generate triples
```

---

## Button Language

### Before (Technical)
- "Override" → Sounds scary
- "Download YAML" → What's YAML?
- "Match Reasons" → Confusing

### After (User-Friendly)
- "Change" → Clear action
- "Map Now" → Call to action
- "Evidence" → Explain reasoning
- "Config YAML" → Downplayed

---

## Complete User Journey

```
1. Upload Files
   ├─ Data CSV
   └─ Ontology TTL

2. Generate Mapping
   └─ System matches columns automatically

3. Review Results
   ├─ See statistics chips
   ├─ Mapped: 35 ✓
   └─ Unmapped: 12 ⚠️

4. Check Mapped Columns
   ├─ Click "Evidence" to understand
   └─ Click "Change" if incorrect

5. Map Unmapped Columns
   ├─ Click "Map Now"
   ├─ Search properties
   ├─ Select property
   └─ Confirm

6. Convert to RDF
   ├─ All mappings applied
   └─ Download triples

7. Export (Optional)
   ├─ Report JSON (documentation)
   ├─ Report HTML (readable)
   └─ Config YAML (CLI/advanced)
```

---

## Key Improvements

✅ **Hidden Complexity**
- YAML configuration → Internal use only
- Technical metrics → Removed
- Query syntax → Hidden in API calls

✅ **Visual Hierarchy**
- Chips for statistics → Quick scan
- Emojis for sections → Clear distinction
- Color-coding → Immediate understanding

✅ **Action-Oriented**
- "Map Now" buttons → Clear CTA
- "Change" vs "Override" → Friendly
- Sample values shown → Context for decisions

✅ **Complete Workflow**
- Can map ALL columns through UI
- No need to edit YAML
- Immediate feedback

---

**Result:** Professional, user-friendly interface that makes semantic mapping accessible to non-technical users! 🎉

