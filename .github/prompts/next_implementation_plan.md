# Next Implementation Plan: Matcher Architecture Refinement

**Date:** November 16, 2025  
**Priority:** High (Foundation for future enhancements)  
**Estimated Effort:** 2-3 days

## Overview

Now that embeddings are working well, we need to refactor the matcher architecture to properly separate concerns. Currently, SemanticSimilarityMatcher is doing too much (embeddings + lexical fallback), and DataTypeInferenceMatcher needs clearer boundaries.

## Phase 1: Matcher Separation (Days 1-2)

### 1.1 Create Dedicated LexicalMatcher
**Goal:** Extract all lexical/string-based matching from SemanticSimilarityMatcher

**New File:** `src/rdfmap/generator/matchers/lexical_matcher.py`

**Features:**
- Five matching algorithms already implemented:
  1. Exact match (normalized)
  2. Substring containment with ratio scoring
  3. Token-based Jaccard with synonym normalization
  4. Edit distance (SequenceMatcher)
  5. Character n-gram similarity
- CamelCase splitting
- Synonym equivalence (id/identifier/number)
- Abbreviation detection (moved from SemanticSimilarityMatcher)

**Benefits:**
- Clear separation: embeddings vs. lexical
- Can be enabled/disabled independently
- Easier to tune thresholds per algorithm
- Better test coverage

**Implementation:**
```python
class LexicalMatcher(ColumnPropertyMatcher):
    """Pure lexical/string similarity matching."""
    
    def __init__(
        self,
        enabled: bool = True,
        threshold: float = 0.6,
        exact_weight: float = 1.0,
        substring_weight: float = 0.85,
        token_weight: float = 0.7,
        edit_distance_weight: float = 0.85,
        ngram_weight: float = 0.75,
    ):
        # ...
    
    def match(self, column, properties, context):
        # Five algorithms, weighted combination
        # Returns best lexical match above threshold
```

### 1.2 Refactor SemanticSimilarityMatcher
**Goal:** Pure embedding-based matching only

**Changes:**
- Remove `_get_lexical_scores()` method
- Remove abbreviation detection logic
- Keep only:
  - `embed_column()` with identifier enrichment
  - `embed_property()` with identifier enrichment
  - `enhanced_score_all()` (phrase + token + id_boost)
  - `match()` using embeddings only

**Fallback Strategy:**
- If embeddings fail to load: emit warning, return None
- Pipeline will fall back to LexicalMatcher automatically
- No more mixed lexical/embedding code path

### 1.3 Refine DataTypeInferenceMatcher
**Goal:** Pure type compatibility checking, no semantic inference

**Changes:**
- Remove any label/name-based logic
- Focus purely on data type alignment:
  - Column inferred type (string/integer/decimal/date/boolean)
  - Property range (xsd:string, xsd:integer, xsd:decimal, xsd:date, xsd:boolean)
  - Compatibility matrix (e.g., integer column → decimal property = compatible)
- Threshold remains 0.0 (always emits evidence for aggregation)
- Confidence based on type precision match:
  - Exact match (string→string): 0.95
  - Compatible match (int→decimal): 0.85
  - Loose match (string→anyURI): 0.70

**Benefits:**
- Clear single responsibility
- No more "DataType overriding semantic match" issues
- Acts purely as confidence booster in aggregation

### 1.4 Update Matcher Pipeline Order

**New Order:**
```python
# Tier 1: Exact Label Matchers (1.0 to 0.80)
ExactPrefLabelMatcher(threshold=1.0)
ExactRdfsLabelMatcher(threshold=0.95)
ExactAltLabelMatcher(threshold=0.90)
ExactHiddenLabelMatcher(threshold=0.85)
ExactLocalNameMatcher(threshold=0.80)

# Tier 2: Ontology Structure Matchers (0.65 to 0.75)
PropertyHierarchyMatcher(threshold=0.65)
OWLCharacteristicsMatcher(threshold=0.60)
RestrictionBasedMatcher(threshold=0.55)
SKOSRelationsMatcher(threshold=0.50)

# Tier 3: Semantic & Lexical Matchers (0.45 to 0.70)
SemanticSimilarityMatcher(threshold=0.45)  # Pure embeddings
LexicalMatcher(threshold=0.60)  # Pure string matching

# Tier 4: Context & Boosters (0.0 to 0.60)
DataTypeInferenceMatcher(threshold=0.0)  # Booster only
HistoryAwareMatcher(threshold=0.60)
StructuralMatcher(threshold=0.70)

# Tier 5: Graph Reasoning (0.60)
GraphReasoningMatcher(threshold=0.60)

# Tier 6: Fallback Fuzzy Matchers (0.40 to 0.60)
PartialStringMatcher(threshold=0.60)
FuzzyStringMatcher(threshold=0.40)
```

## Phase 2: Enhanced Evidence Display (Day 2)

### 2.1 Matcher Attribution Formatting
**Goal:** Show which specific algorithm/approach was used

**Current:** "Primary: SemanticSimilarityMatcher"  
**Proposed:** "Primary: Embedding (phrase=0.82, token=0.64) + ID boost"

**Implementation:**
- Each matcher returns structured `matched_via`:
  ```python
  {
    "method": "embedding",  # or "lexical", "exact_label", "skos_relation"
    "sub_method": "phrase_cosine",  # or "token_avg", "substring", "jaccard"
    "score": 0.82,
    "details": "phrase similarity + identifier pattern"
  }
  ```
- UI parses and formats with icons/badges
- Evidence drawer shows algorithm breakdown

### 2.2 Confidence Explanation
**Goal:** Help users understand why confidence is X%

**Format:**
```
Final Confidence: 87%

Base Match:
  ✓ Semantic Similarity (phrase): 82%
  
Boosters Applied:
  + Data Type Compatible: +5%
  
Penalties Applied:
  - No penalties
  
Alternate Properties:
  • principalAmount (79%)
  • loanAmount (65%)
```

**Implementation:**
- Expand `EvidenceDrawer` component
- Add tooltip on confidence score in main table
- Color-code boosters (green) and penalties (orange)

## Phase 3: SKOS Vocabulary Integration (Day 3)

### 3.1 Create Mortgage SKOS Vocabulary
**File:** `examples/mortgage/vocabulary/mortgage_vocab.ttl`

**Content:**
```turtle
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix ex: <https://example.com/mortgage#> .

# Property labels
ex:loanNumber
    skos:prefLabel "Loan Number"@en ;
    skos:altLabel "Loan ID"@en, "Loan Identifier"@en ;
    skos:hiddenLabel "LoanID"@en, "loan_id"@en, "loan_num"@en ;
    skos:definition "Unique identifier assigned to a mortgage loan"@en .

ex:principalAmount
    skos:prefLabel "Principal Amount"@en ;
    skos:altLabel "Loan Amount"@en, "Principal"@en ;
    skos:hiddenLabel "principal"@en, "loan_amt"@en ;
    skos:definition "The original amount of the loan"@en .

ex:interestRate
    skos:prefLabel "Interest Rate"@en ;
    skos:altLabel "Rate"@en, "APR"@en ;
    skos:hiddenLabel "interest"@en, "rate"@en, "apr"@en ;
    skos:definition "The annual interest rate as a decimal"@en .

# ... (continue for all properties)
```

### 3.2 SKOS-Aware Matching
**Goal:** Use SKOS labels in matching, track which label type matched

**Changes to OntologyAnalyzer:**
- Load SKOS files separately from ontology
- Parse skos:prefLabel, skos:altLabel, skos:hiddenLabel
- Associate with properties

**Changes to Exact Matchers:**
- `ExactPrefLabelMatcher`: Check skos:prefLabel first, then rdfs:label
- `ExactAltLabelMatcher`: Check skos:altLabel
- `ExactHiddenLabelMatcher`: Check skos:hiddenLabel

**Evidence Enhancement:**
- `matched_via`: "skos:prefLabel 'Loan Number'"
- `matched_via`: "skos:hiddenLabel 'LoanID'"
- Show in UI with SKOS icon/badge

### 3.3 UI SKOS Display
**Features:**
- SKOS vocabulary upload (already implemented)
- Display loaded vocabularies in Knowledge Inputs section
- Match Reasons table shows SKOS label type
- Evidence drawer shows SKOS definition/scope notes

## Phase 4: Validation Dashboard Enhancement (Day 3)

### 4.1 Ontology Structural Validation
**Goal:** More than just SHACL - validate against ontology semantics

**Checks:**
- Domain violations (property used on wrong class)
- Range violations (wrong datatype/class for object)
- Cardinality violations (functional properties with multiple values)
- Required properties missing (min cardinality)
- Inverse consistency (if A→B, then B→A via inverse)
- Disjoint class violations

**Implementation:**
- Already have `report.domain_violations`, `report.range_violations`
- Add to ValidationDashboard component
- Show samples of violations
- Link to specific rows in data

### 4.2 SHACL Integration
**Goal:** Separate SHACL validation from ontology validation

**Create:** `examples/mortgage/shapes/mortgage_shapes.ttl`

**Example Shapes:**
```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <https://example.com/mortgage#> .

ex:MortgageLoanShape
    a sh:NodeShape ;
    sh:targetClass ex:MortgageLoan ;
    sh:property [
        sh:path ex:loanNumber ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:datatype xsd:string ;
        sh:minLength 1 ;
    ] ;
    sh:property [
        sh:path ex:principalAmount ;
        sh:minCount 1 ;
        sh:datatype xsd:integer ;
        sh:minInclusive 0 ;
    ] ;
    # ...
```

**UI Display:**
- Separate tabs: "Ontology Validation" | "SHACL Validation"
- SHACL shows constraint violations by shape
- Link violations to fixing suggestions

## Phase 5: Ontology Graph Visualization Fix (Bonus)

### 5.1 Fix Cytoscape Modal Loading Issue
**Problem:** Modal shows "Loading..." indefinitely

**Root Cause Analysis Needed:**
- Check if data is passing correctly to modal
- Verify Cytoscape initialization timing
- Check for React lifecycle issues

**Quick Fix:**
- Add loading state management
- Add error boundary
- Show fallback if Cytoscape fails

### 5.2 Node Label Display
**Implementation:**
- Use rdfs:label or skos:prefLabel if available
- Fallback to local name
- Truncate long labels with tooltip

### 5.3 Highlight Matched Properties
**Feature:**
- When viewing project with mappings:
  - Highlight nodes/edges for properties that were mapped
  - Color-code by confidence (green=high, yellow=medium, red=low)
  - Click node to see which column(s) mapped to it

## Success Criteria

### Phase 1 (Matcher Refactoring):
- ✅ LexicalMatcher exists and passes all tests
- ✅ SemanticSimilarityMatcher contains ONLY embedding code
- ✅ DataTypeInferenceMatcher is purely type-based
- ✅ Mortgage example still maps 10/10 columns correctly
- ✅ Evidence shows clear matcher attribution

### Phase 2 (Evidence Display):
- ✅ Match Reasons table shows algorithm details
- ✅ Evidence drawer explains confidence calculation
- ✅ Users can understand why each match was made

### Phase 3 (SKOS):
- ✅ Mortgage SKOS vocabulary created
- ✅ SKOS labels used in matching
- ✅ Match evidence shows "matched via skos:hiddenLabel"
- ✅ UI displays SKOS metadata

### Phase 4 (Validation):
- ✅ Ontology violations displayed in dashboard
- ✅ SHACL shapes separate from ontology
- ✅ Violations linked to data rows

### Phase 5 (Graph):
- ✅ Cytoscape modal displays graph
- ✅ Nodes show labels
- ✅ Matched properties highlighted

## Testing Strategy

### Unit Tests:
```bash
pytest tests/test_lexical_matcher.py
pytest tests/test_semantic_matcher_pure.py
pytest tests/test_datatype_matcher.py
```

### Integration Tests:
```bash
pytest tests/test_matcher_pipeline.py
pytest tests/test_skos_integration.py
```

### End-to-End Validation:
```bash
# Test with mortgage example
rdfmap generate --ontology examples/mortgage/ontology/mortgage.ttl \
                --skos examples/mortgage/vocabulary/mortgage_vocab.ttl \
                --data examples/mortgage/data/loans.csv \
                --output test_output.ttl

# Verify output
rdfmap convert test_output.ttl --validate --shapes examples/mortgage/shapes/mortgage_shapes.ttl
```

## Risk Mitigation

### Breaking Changes:
- Create feature branch: `feature/matcher-refactoring`
- Maintain backward compatibility with existing configs
- Add deprecation warnings for old behavior
- Migration guide for custom matchers

### Performance:
- Benchmark before/after refactoring
- Ensure no regression in speed
- Profile embedding cache efficiency

### User Experience:
- Gradual rollout via feature flags
- A/B test with existing vs. new matcher attribution
- Gather feedback on evidence clarity

## Timeline

**Day 1:**
- Morning: Create LexicalMatcher
- Afternoon: Refactor SemanticSimilarityMatcher, test mortgage example

**Day 2:**
- Morning: Refine DataTypeInferenceMatcher, update pipeline
- Afternoon: Enhanced evidence display in UI

**Day 3:**
- Morning: SKOS vocabulary creation and integration
- Afternoon: Validation dashboard enhancements

**Buffer:** Ontology graph fixes (if time permits)

## Next After This

Once matcher architecture is solid:
1. **Alternative Embedding Models** - Allow users to choose MiniLM vs MPNet vs domain-specific
2. **Feedback Loop** - Capture manual corrections to improve matching
3. **Batch Processing** - Handle large datasets (millions of rows)
4. **Export/Import** - Share matcher configurations across projects
5. **Documentation** - User guide for matcher customization

---

**Recommendation:** Start with Phase 1 immediately. The matcher separation will make all future enhancements easier and more maintainable.

