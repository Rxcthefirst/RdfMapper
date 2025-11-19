# Quick Checklist: Seeing Evidence Categories in UI

## ✅ What I Just Fixed

The evidence categorization was implemented but **not integrated into the actual frontend**. I've now:

1. ✅ Copied `EvidenceExplorer.tsx` to `/frontend/src/components/`
2. ✅ Updated `/frontend/src/components/EvidenceDrawer.tsx` to use it
3. ✅ Added all necessary interfaces for evidence groups

## 🚀 How to See It Working (3 Steps)

### Step 1: Verify Backend (30 seconds)

```bash
cd /Users/rxcthefirst/Dev/PythonProjects/SemanticModelDataMapper
python verify_evidence_backend.py
```

**Expected output:**
```
✅ VERIFICATION COMPLETE
All checks passed:
  ✅ Evidence items generated
  ✅ Evidence categorized into groups
  ✅ Reasoning summary created
  ✅ Performance metrics captured
```

### Step 2: Restart Frontend (if running)

```bash
cd frontend
npm run dev
```

Or just hard-refresh your browser: **Cmd+Shift+R** (Mac) or **Ctrl+Shift+R** (Windows)

### Step 3: Regenerate a Mapping

**IMPORTANT:** Old mappings don't have the new `evidence_groups` field!

Option A: Create a new project and generate mapping

Option B: Regenerate existing project:
```bash
curl -X POST "http://localhost:8000/api/mappings/{project_id}/generate"
```

## 🎯 What You Should See

When you click on a column to view evidence:

**OLD (Before):**
```
Evidence (5 items)
- SemanticSimilarityMatcher: 0.85
- LexicalMatcher: 0.80
...
```

**NEW (After):**
```
employeeID → Employee ID (92%)

💡 Reasoning: Semantic match validated by 4 
   ontological constraints...

⚡ 45ms | 4.3x speedup

✅ SEMANTIC REASONING ▼        [Expandable!]
   3 matchers, avg: 0.85

⭐ ONTOLOGICAL VALIDATION ▼    [Expandable!]
   4 matchers, avg: 0.72

🔗 STRUCTURAL CONTEXT ▼        [Expandable!]
   2 matchers, avg: 0.68
```

## ⚠️ Still Seeing Old UI?

### Quick Fixes (try in order):

1. **Hard refresh browser** (Cmd+Shift+R)
2. **Clear browser cache**
3. **Regenerate the mapping** (old data doesn't have groups)
4. **Check browser console** for errors (F12)
5. **Restart backend** (might be running old code)

### Verify Files Exist:

```bash
# Should exist now
ls -la frontend/src/components/EvidenceExplorer.tsx
ls -la frontend/src/components/EvidenceDrawer.tsx
```

### Check API Response:

```bash
# View actual evidence structure
curl http://localhost:8000/api/mappings/{project_id}/evidence/employeeID \
  | jq '.evidence_detail.evidence_groups'
```

**Should return:**
```json
[
  {
    "category": "semantic",
    "evidence_items": [...]
  },
  {
    "category": "ontological_validation",
    "evidence_items": [...]
  }
]
```

**If null:** Mapping was generated before update. Regenerate it!

## 📋 Visual Checklist

When evidence drawer opens, you should see:

- [ ] **Blue alert box** at top with brain icon (💡) and reasoning text
- [ ] **Performance badge** (⚡) with number showing matchers fired
- [ ] **Three accordion sections** (not flat list):
  - [ ] ✅ Green checkmark for "Semantic Reasoning"
  - [ ] ⭐ Orange star for "Ontological Validation"  
  - [ ] 🔗 Blue link for "Structural Context"
- [ ] **"X matchers, avg: Y.YY"** under each section header
- [ ] **Expandable/collapsible** sections (click to expand)
- [ ] **Progress bars** for each evidence item
- [ ] **Color-coded confidence** (green/yellow/orange/red)

## 🐛 Debugging Commands

```bash
# 1. Check backend has updates
python -c "from rdfmap.generator.evidence_categorizer import categorize_evidence; print('✅')"

# 2. Check frontend files
cat frontend/src/components/EvidenceDrawer.tsx | grep EvidenceExplorer

# 3. Check alignment report structure
cat data/*/alignment_report.json | jq '.match_details[0] | keys'
# Should include: evidence_groups, reasoning_summary, performance_metrics

# 4. Test API endpoint
curl localhost:8000/api/mappings/{project_id}/evidence | jq '.statistics'
```

## 📞 Still Stuck?

If you've tried everything above and still don't see the categories:

1. **Check exact error** in browser console (F12 → Console tab)
2. **Check backend logs** for Python errors
3. **Share screenshot** of what you're seeing
4. **Share API response** from `/api/mappings/{project_id}/evidence/columnName`

## 🎉 Success Looks Like

```
┌─────────────────────────────────────────┐
│ employeeID → Employee ID        [92%] ⚡9│
│                                          │
│ 💡 Semantic match validated by 4        │
│    ontological constraints...            │
│                                          │
│ ✅ SEMANTIC REASONING ▼                  │
│    3 matchers, avg: 0.85                │
│                                          │
│ ⭐ ONTOLOGICAL VALIDATION ▼              │
│    4 matchers, avg: 0.72                │
│                                          │
│ 🔗 STRUCTURAL CONTEXT ▼                  │
│    2 matchers, avg: 0.68                │
└─────────────────────────────────────────┘
```

---

**The fix is deployed. The most common issue is viewing old mapping data that doesn't have the new evidence structure. Regenerate a mapping to see the new UI!**

