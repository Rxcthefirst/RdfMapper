# Testing the Evidence Categorization UI

## Overview

The new evidence categorization features have been integrated into the application. Here's how to see them in action.

## What to Look For

When you open the Evidence Drawer for a mapped column, you should now see:

### 1. **Evidence Groups (Categorized)**

Three expandable accordion sections with distinct icons:

- **✅ Semantic Reasoning** (Green checkmark icon)
  - Shows matches from: SemanticSimilarityMatcher, LexicalMatcher, ExactPrefLabelMatcher, etc.
  - Description: "Semantic reasoning based on embeddings and label matching"

- **⭐ Ontological Validation** (Orange star icon)
  - Shows matches from: PropertyHierarchyMatcher, OWLCharacteristicsMatcher, DataTypeInferenceMatcher, etc.
  - Description: "Ontological validation using OWL constraints and type system"

- **🔗 Structural Context** (Blue link icon)
  - Shows matches from: GraphReasoningMatcher, StructuralMatcher, HistoryAwareMatcher
  - Description: "Structural patterns and relationships in data"

### 2. **Reasoning Summary** (Blue alert box with brain icon)

A human-readable explanation like:
> "Matched to 'Employee ID' with 0.92 confidence. Semantic reasoning: 3 matchers agree (avg: 0.85). Ontology validates: uniqueness constraint, type compatibility, property hierarchy (4 checks, avg: 0.72). Very high confidence - multiple strategies converge."

### 3. **Performance Metrics Badge**

A speed icon with a badge showing the number of matchers that fired, with hover tooltip showing:
- Execution time in milliseconds
- Parallel speedup factor (e.g., "4.3x")

### 4. **Visual Confidence Indicators**

- Color-coded confidence chips and progress bars
- Green (≥90%), Light Green (≥80%), Yellow (≥70%), Orange (≥60%), Red (<60%)

## How to Test

### Step 1: Generate a Mapping with the Backend

```bash
# Make sure the backend is running
cd backend
python -m uvicorn app.main:app --reload

# Or if using Docker
docker-compose up backend
```

### Step 2: Upload Files and Generate Mapping

1. Go to http://localhost:3000 (or your frontend URL)
2. Create a new project
3. Upload:
   - Data file (use `test_data/messy_employees.csv` for best results)
   - Ontology file (e.g., `test_data/test_owl_ontology.ttl`)
4. Click "Generate Mapping"

### Step 3: View Evidence

1. After mapping generation completes, you'll see a table of column mappings
2. Click on any row to open the Evidence Drawer
3. **You should now see:**
   - Evidence groups with expandable accordions
   - Icons: ✅ (green), ⭐ (orange), 🔗 (blue)
   - Reasoning summary with brain icon (🧠)
   - Performance metrics badge

### Step 4: Interact with Evidence

- **Click on an evidence group** to expand/collapse it
- **Hover over the performance badge** to see execution metrics
- **Read the reasoning summary** to understand WHY the match was made
- **Scroll through each evidence item** to see individual matcher contributions

## Expected Behavior

### For a typical column like "employeeID":

```
Column: employeeID → Employee ID
Confidence: 92%

💡 REASONING SUMMARY:
Matched to 'Employee ID' with 0.92 confidence. Semantic reasoning: 
3 matchers agree (avg: 0.85). Ontology validates: uniqueness constraint, 
type compatibility, property hierarchy (4 checks, avg: 0.72). 
Very high confidence - multiple strategies converge.

✅ SEMANTIC REASONING (3 matchers, avg: 0.85)
  - SemanticSimilarityMatcher: 0.85 (embedding match)
  - LexicalMatcher: 0.80 (token overlap)
  - ExactLocalNameMatcher: 0.90 (camelCase match)

⭐ ONTOLOGICAL VALIDATION (4 matchers, avg: 0.72)
  - OWLCharacteristicsMatcher: 0.80 (IFP + unique ✓)
  - DataTypeInferenceMatcher: 0.68 (string type ✓)
  - PropertyHierarchyMatcher: 0.75 (identifier hierarchy ✓)
  - GraphReasoningMatcher: 0.70 (primary key pattern ✓)

🔗 STRUCTURAL CONTEXT (2 matchers, avg: 0.68)
  - StructuralMatcher: 0.70 (FK detection)
  - HistoryAwareMatcher: 0.65 (previous usage)

⚡ PERFORMANCE: 45.2ms | 4.3x speedup | 9 matchers fired
```

## Troubleshooting

### Issue: Not seeing evidence groups

**Problem:** Evidence drawer shows flat list instead of categorized groups

**Solution:** The backend needs to be updated to generate `evidence_groups`. Check:
1. Is the backend running the latest code?
2. Was the mapping generated after the updates?
3. Try regenerating the mapping for the project

**To regenerate:**
```bash
# Via API
curl -X POST "http://localhost:8000/api/mappings/{project_id}/generate" \
  -H "Content-Type: application/json"
```

### Issue: Evidence categories are empty

**Problem:** Evidence groups exist but have no items

**Solution:** This means matchers aren't firing. Check:
1. Is the ontology file valid?
2. Do column names have semantic meaning? (Try `messy_employees.csv`)
3. Are all 17 matchers enabled in the pipeline?

**Verify matchers:**
```python
from rdfmap.generator.matchers import create_default_pipeline

pipeline = create_default_pipeline()
stats = pipeline.get_matcher_stats()
print(f"Total matchers: {stats['total_matchers']}")
print(f"Enabled: {stats['enabled_matchers']}")
```

### Issue: Performance metrics not showing

**Problem:** No speed badge or metrics

**Solution:** Performance metrics are only available when using parallel execution:
1. Check that `parallel=True` in `match_all()` call
2. Ensure `PerformanceMetrics` are being captured in mapping generator

### Issue: Reasoning summary is missing

**Problem:** No blue alert box with explanation

**Solution:** Reasoning summaries are generated in `_aggregate_matches`:
1. Check that `evidence_categorizer` is imported
2. Verify `generate_reasoning_summary()` is being called
3. Look for the `reasoning_summary` field in match_details

## Verifying Backend Evidence Generation

### Check Alignment Report JSON

```bash
# View the alignment report for a project
cat data/{project_id}/alignment_report.json | jq '.match_details[0]'
```

You should see:
```json
{
  "column_name": "employeeID",
  "confidence_score": 0.92,
  "evidence_groups": [
    {
      "category": "semantic",
      "evidence_items": [...],
      "avg_confidence": 0.85,
      "description": "Semantic reasoning..."
    },
    {
      "category": "ontological_validation",
      "evidence_items": [...],
      "avg_confidence": 0.72,
      "description": "Ontological validation..."
    }
  ],
  "reasoning_summary": "Matched to 'Employee ID' with 0.92 confidence...",
  "performance_metrics": {
    "execution_time_ms": 45.2,
    "parallel_speedup": 4.3,
    "matchers_fired": 9
  }
}
```

### Test Evidence API Endpoint

```bash
# Get evidence for a specific column
curl http://localhost:8000/api/mappings/{project_id}/evidence/employeeID

# Get all evidence for project
curl http://localhost:8000/api/mappings/{project_id}/evidence
```

## Frontend Development

If you're developing the frontend and want to see changes immediately:

```bash
cd frontend
npm install  # Install dependencies if needed
npm run dev  # Start development server
```

The frontend should hot-reload when you edit files.

## Success Criteria

You know the implementation is working when you see:

✅ Three distinct evidence groups with colored icons  
✅ Evidence items nested under their categories  
✅ Reasoning summary with multi-sentence explanation  
✅ Performance badge with metrics  
✅ Confidence color-coding (green/yellow/red)  
✅ Progress bars for each evidence item  
✅ Expandable/collapsible accordions  

## Still Not Working?

If you've tried all the above and still don't see the categorized evidence:

1. **Check browser console** for React errors
2. **Verify API responses** using browser DevTools → Network tab
3. **Regenerate the mapping** after backend updates
4. **Check logs** in backend terminal for errors
5. **File an issue** with screenshots showing what you see vs. what's expected

## Demo Video (Coming Soon)

A video demonstration will be added showing the complete flow from mapping generation to evidence exploration.

---

**Last Updated:** November 17, 2025  
**Status:** Ready for Testing

