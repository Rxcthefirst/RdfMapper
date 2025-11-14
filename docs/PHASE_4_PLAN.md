# Phase 4 Plan: Reaching 9.2/10 🎯

## Current Status

**Score: 8.7/10**  
**Target: 9.2/10**  
**Gap: 0.5 points (+6%)**

We've made incredible progress with Phases 1-3. Now let's push toward excellence!

---

## What's Left to Build

Based on our comprehensive analysis, here are the highest-impact improvements remaining:

### Priority 1: Structural/Relationship Matcher (2-3 hours)
**Impact:** +0.2 points  
**Benefit:** Automatic foreign key detection

### Priority 2: Domain-Specific Matchers (2-3 hours per domain)
**Impact:** +0.1-0.2 points per domain  
**Benefit:** Specialized knowledge for healthcare, finance, etc.

### Priority 3: Active Learning System (4-5 hours)
**Impact:** +0.2-0.3 points  
**Benefit:** Strategic questioning to minimize manual work

---

## Recommended Approach: Phase 4a - Structural Matcher

Let's start with the **Structural/Relationship Matcher** because:

1. **Clear use case** - Foreign keys are common
2. **Medium effort** - 2-3 hours to implement
3. **Good ROI** - Catches 3-5% more columns
4. **Complements existing matchers** - Fills a gap

### What It Will Do

The structural matcher will:

1. **Detect foreign key columns**
   - Patterns like `*_id`, `*_ref`, `*Id`, `*Ref`
   - Values that look like identifiers
   - References to other sheets/tables

2. **Identify relationships**
   - Find object properties in ontology
   - Match FK columns to appropriate relationships
   - Suggest linked object mappings

3. **Validate cardinality**
   - Check if FK values are unique (one-to-one)
   - Or repeated (one-to-many)
   - Match with OWL cardinality restrictions

### Example

**Data:**
```csv
loan_id, borrower_id, property_id, amount
L001, B123, P456, 250000
L002, B124, P457, 300000
```

**Before:**
- `borrower_id` → Not matched (no direct property)
- `property_id` → Not matched (no direct property)
- Manual: User must add object mappings

**After (with Structural Matcher):**
- `borrower_id` → Detected as FK
- Finds `hasBorrower` object property
- Suggests: Create linked object with `borrowerID` property
- `property_id` → Similar for `hasProperty`
- **Automatic object mapping creation!**

---

## Implementation Plan for Phase 4a

### Step 1: Pattern Detection (30 min)
```python
class StructuralPatternDetector:
    """Detect structural patterns in data."""
    
    FK_PATTERNS = [
        r'.*_id$', r'.*_ref$', r'.*Id$', r'.*Ref$',
        r'.*_key$', r'.*Key$', r'fk_.*'
    ]
    
    def detect_foreign_key(self, column: DataFieldAnalysis) -> bool:
        """Check if column looks like a foreign key."""
        # Check name patterns
        # Check value patterns (unique identifiers)
        # Check relationships to other columns
```

### Step 2: Relationship Inference (30 min)
```python
class RelationshipInferencer:
    """Infer relationships from foreign keys."""
    
    def find_object_properties(
        self,
        fk_column: str,
        ontology: OntologyAnalyzer
    ) -> List[OntologyProperty]:
        """Find object properties that match FK pattern."""
        # Extract base name: "borrower_id" → "borrower"
        # Look for "hasBorrower", "borrower" properties
        # Check if they are object properties
```

### Step 3: Structural Matcher (1 hour)
```python
class StructuralMatcher(ColumnPropertyMatcher):
    """Match based on structural patterns."""
    
    def match(
        self,
        column: DataFieldAnalysis,
        properties: List[OntologyProperty],
        context: Optional[MatchContext] = None
    ) -> Optional[MatchResult]:
        """Match foreign keys to object properties."""
        # Detect if column is FK
        # Find matching object properties
        # Suggest linked object creation
```

### Step 4: Integration (30 min)
- Add to matcher pipeline
- Create tests
- Update documentation

---

## Expected Impact

### Mapping Quality
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| FK detection | 0% | 80% | **+80%** |
| Object mappings | Manual | Auto | **Huge UX improvement** |
| Overall success | 92% | 95% | **+3%** |

### Score Improvement
**8.7 → 8.9 (+0.2 points)**

---

## Alternative: Phase 4b - Domain-Specific Matcher

If you prefer domain-specific knowledge instead:

### Healthcare Matcher
- SNOMED-CT terminology
- ICD-10 codes
- Medical abbreviations
- Patient/Provider/Diagnosis patterns

### Finance Matcher  
- FIBO ontology knowledge
- Financial terms (principal, interest, APR)
- Account/Transaction patterns
- Regulatory identifiers

**Pick one domain, get 5-8% better results in that domain.**

---

## Alternative: Phase 4c - Active Learning

For maximum long-term impact but more effort:

### Smart Question Selection
- Ask about uncertain matches
- Learn from corrections
- Propagate patterns
- Minimize manual work

**Reduces manual review from 15% to 5-8%**

---

## My Recommendation

**Start with Phase 4a: Structural Matcher**

**Why:**
1. ✅ Clear, concrete use case
2. ✅ Medium effort (2-3 hours)
3. ✅ Immediate value
4. ✅ Complements existing features
5. ✅ Gets us to 8.9/10

After that, we can:
- Add domain-specific matchers (pick your domain)
- Build active learning system
- Polish to 9.2+/10

---

## Ready to Start?

Let me know if you want to:
- **A) Build the Structural Matcher** (recommended)
- **B) Build a Domain-Specific Matcher** (which domain?)
- **C) Build Active Learning** (more complex)
- **D) Something else you have in mind**

We're 90% of the way to our 9.2 goal. Let's finish strong! 🚀

---

**Current Score:** 8.7/10  
**Next Target:** 8.9/10 (Structural Matcher)  
**Final Target:** 9.2/10  
**Status:** Ready to continue!

