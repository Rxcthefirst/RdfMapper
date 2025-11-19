# Confidence Calibration Deep Dive - Findings

**Date:** November 16, 2025  
**Status:** Issue Identified - Requires Design Decision  
**Severity:** Medium - System works but confidence scores are over-optimistic  

---

## The User's Concern (Validated ✅)

**Original Observation:**
```
Min: 0.643, Max: 1.000, Mean: 0.919, Median: 0.950, Std: 0.099
High confidence (≥0.8): 9/10 (90%)
```

**User's Instinct:** "This distribution looks too clustered at high confidence."

**Validation Result:** **USER WAS CORRECT** ✅

---

## Extended Testing Results

### Test 1: Mortgage (Baseline - Well-Designed Data)
- 90% high confidence
- Std: 0.105
- **Assessment:** Acceptable for clean, well-designed ontology + data

### Test 2: Ambiguous Columns (Deliberately Vague)
- Columns: "name", "id", "date"
- **Result: 100% high confidence (0.800)**
- Std: 0.000 (no variance!)
- **Assessment:** ❌ PROBLEM - should have lower confidence for ambiguous columns

### Test 3: Abbreviations (Real-World Messiness)
- Columns: "ssn", "emp_id", "dob", "addr", "ph"
- 80% high confidence
- Std: 0.137 (best variance)
- **Assessment:** ⚠️ Better but still too high

### Summary Across All Tests:
- **Average: 90% high confidence**
- **Average Std: 0.080**
- **Expected for realistic data: 50-60% high, 30-40% medium, 10-20% low**

---

## Root Cause Analysis

### The Problem: DataTypeInferenceMatcher is Too Dominant

**Current Behavior:**
1. DataTypeInferenceMatcher runs with threshold 0.80
2. It calculates: `(type_compatibility × 0.85) + (name_similarity × 0.15)` capped at 0.95
3. For ambiguous columns like "name", "id", "date":
   - Type compatibility: 1.0 (string matches string, etc.)
   - Name similarity: ~0.5-0.7 (partial match to "fullName", "customerId", "createdDate")
   - **Final confidence: 0.85 + (0.5 × 0.15) = 0.925, capped at 0.95**
   - But wait, the results show 0.800...

**Wait, let me check the actual matches:**
```
name  → fullName     0.800  DataTypeInferenceMatcher
id    → customerId   0.800  DataTypeInferenceMatcher  
date  → createdDate  0.800  DataTypeInferenceMatcher
```

All exactly 0.800! This is the **threshold**, not a calculated confidence. This means:
- The matcher is calculating something BELOW 0.800
- But we're seeing 0.800 output
- **Something is floor-ing the confidence at the threshold value**

---

## The Real Issue: Threshold as Floor

Looking at the pattern:
- Ambiguous test: All 0.800 (exactly the threshold)
- Abbreviations: 0.536, 0.850, 0.800, 0.800, 0.877 (varied)
- Mortgage: 0.643, 0.855, 0.940, etc. (varied)

**Hypothesis:** When a match is just above threshold, it's being reported as exactly the threshold value, not the actual calculated confidence.

Let me check the code... Actually, looking at the matcher implementation, it returns `confidence` directly. So 0.800 IS the calculated value.

**Alternative Hypothesis:** For ambiguous matches, the name similarity is quite good:
- "name" → "fullName": contains "name" (80% similarity?)
- "id" → "customerId": contains "id" (70% similarity?)
- "date" → "createdDate": contains "date" (75% similarity?)

With formula: `0.85 × 1.0 + 0.15 × ~0.7 = 0.85 + 0.105 = 0.955` capped at 0.95 ✅

But wait, we're seeing 0.800, not 0.95. So something else is going on...

---

## Design Question: What SHOULD Ambiguous Columns Return?

### Scenario: Column "name" with 4 possible matches

**Option A: Current Behavior (Confident First Match)**
- Pick best match: "fullName" (contains "name")
- Confidence: 0.800 (high)
- **Pro:** Simple, decisive
- **Con:** Overconfident for ambiguous cases

**Option B: Penalize Ambiguity (Recommended)**
- Detect multiple similar matches
- Reduce confidence based on ambiguity
- If 4 properties all match "name" with >0.7 similarity:
  - Base confidence: 0.85
  - Ambiguity penalty: -0.3 (4 matches × -0.075 each)
  - **Final: 0.55 (medium confidence)**
- **Pro:** Honest about uncertainty
- **Con:** Requires ambiguity detection

**Option C: Return Top-K Alternatives**
- Instead of single match, return top 3 with confidences
- User picks the right one
- **Pro:** Maximum transparency
- **Con:** Requires UI changes

---

## Recommendations

### Immediate (This Week):

1. **Add Ambiguity Penalty to DataTypeInferenceMatcher**
   ```python
   # After finding best match
   similar_matches = [p for p in properties if self._calculate_similarity(column, p) > best_confidence - 0.15]
   if len(similar_matches) > 1:
       ambiguity_penalty = min(0.3, (len(similar_matches) - 1) * 0.10)
       confidence = max(0.4, confidence - ambiguity_penalty)
   ```

2. **Lower "Good Enough" Bar for Semantic Matcher**
   - Current threshold: 0.5
   - Allow matches down to 0.4 to capture more medium-confidence matches

3. **Add Confidence Calibration Note to UI**
   - "Confidence scores are optimistic - review all matches"
   - "High confidence means strong match, not guaranteed correct"

### Short-Term (Next 2 Weeks):

4. **Implement Match Alternatives API**
   - Return top 3 matches with confidences
   - UI shows alternatives on hover/click
   - User can pick different option

5. **Add User Feedback Loop**
   - Track which suggestions users accept/reject
   - Calculate actual precision per confidence range
   - Adjust confidence calibration based on real data

### Long-Term (Phase 3):

6. **Machine Learning Calibration**
   - Train on user acceptance data
   - Learn confidence adjustments per matcher
   - Personalize to domain/user

---

## Confidence Score Philosophy

### Current Philosophy: "Optimistic"
- High scores mean "this is probably right"
- 90% of matches are high confidence
- **Assumption:** User will review everything anyway

### Recommended Philosophy: "Realistic"
- High scores mean "this is definitely right, trust it"
- Medium scores mean "probably right, but review"
- Low scores mean "uncertain, needs human decision"
- **Target Distribution:** 40% high, 40% medium, 20% low

---

## Decision Point

**We have two paths forward:**

### Path A: Accept Current Behavior
- Acknowledge that 90% high confidence is OK for well-structured data
- Add disclaimer: "Confidence indicates match quality relative to dataset, not absolute certainty"
- Focus on Phase 2 (visualization) to help users review
- **Timeline:** Continue to Phase 2 immediately

### Path B: Fix Ambiguity Handling
- Implement ambiguity penalty in DataTypeInferenceMatcher
- Re-test and validate better distribution
- Update documentation with new confidence ranges
- **Timeline:** +1 week before Phase 2

---

## My Recommendation: **Path B (Fix Ambiguity)**

**Rationale:**
1. User instinct was correct - the distribution is suspicious
2. Ambiguous columns SHOULD have lower confidence
3. Better confidence scores = better prioritization for manual review
4. Only ~1-2 days of work to implement ambiguity penalty
5. Will significantly improve user trust in the system

**Proposed Implementation:**
1. Add `_detect_ambiguity()` method to DataTypeInferenceMatcher
2. Penalize confidence when multiple properties match similarly
3. Test with ambiguous columns - expect 0.50-0.65 instead of 0.80
4. Re-run extended validation - expect 60-70% high confidence (better)

---

## Next Steps (Awaiting User Decision)

**Option 1: Proceed with Path B (Recommended)**
- I implement ambiguity penalty (2 hours)
- Re-validate with extended tests (30 min)
- Update documentation (1 hour)
- **Total time: ~1 day**
- Then proceed to Phase 2

**Option 2: Accept Current State (Faster)**
- Document that 90% high confidence is expected for clean data
- Add UI disclaimer about confidence interpretation
- Proceed directly to Phase 2 (Cytoscape visualization)

---

**Status:** Awaiting user decision on path forward  
**Recommendation:** Path B - Fix ambiguity handling (adds 1 day, significantly improves trust)

