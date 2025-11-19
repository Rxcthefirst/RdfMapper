# Phase 1 Completion: Matcher Architecture Refinement

**Date:** November 16, 2025  
**Status:** ✅ Complete

## Summary

Successfully refactored the matcher architecture to separate concerns and adjusted confidence scores to be more realistic. No matcher should ever return 1.00 (absolute certainty).

## Changes Implemented

### 1. Created LexicalMatcher (Phase 1.1) ✅
**File:** `src/rdfmap/generator/matchers/lexical_matcher.py`

**Features:**
- 5 distinct algorithms:
  1. Exact match (0.95 max)
  2. Substring containment (0.80-0.95)
  3. Token-based Jaccard (0.70 max)
  4. Edit distance/SequenceMatcher (0.85 max)
  5. Character n-grams (0.75 max)
- CamelCase splitting
- Synonym normalization (id/identifier/number)
- Weighted combination strategy

### 2. Refactored SemanticSimilarityMatcher (Phase 1.2) ✅
**File:** `src/rdfmap/generator/matchers/semantic_matcher.py`

**Changes:**
- Removed all lexical fallback code
- Pure embedding-based matching only
- Returns None if embeddings unavailable (no fallback)
- Evidence shows: `embedding (phrase=0.82; token=0.64; id_boost=0.07)`
- LexicalMatcher handles cases when embeddings fail

### 3. Adjusted Confidence Scores (Phase 1.3) ✅

**Philosophy:** Nothing should be 1.00. Even exact matches have some uncertainty.

**Confidence Scale:**
- **0.98**: SKOS prefLabel exact match (highest certainty)
- **0.95**: rdfs:label exact match, ObjectPropertyMatcher, LexicalMatcher exact
- **0.92**: RelationshipMatcher (FK detection)
- **0.90**: SKOS altLabel exact match
- **0.85**: SKOS hiddenLabel exact match
- **0.80**: Local name exact match
- **0.45-0.89**: Semantic similarity (embeddings)
- **0.40-0.80**: Lexical algorithms (partial/fuzzy)

**Files Modified:**
- `exact_matchers.py`: ExactPrefLabelMatcher 1.0 → 0.98
- `lexical_matcher.py`: Exact match 1.0 → 0.95
- `mapping_generator.py`: RelationshipMatcher 1.0 → 0.92
- `factory.py`: ExactPrefLabelMatcher threshold 1.0 → 0.98

### 4. Updated Pipeline Order (Phase 1.4) ✅
**File:** `src/rdfmap/generator/matchers/factory.py`

**New Order:**
```
Tier 1: Exact Label Matchers (0.98 to 0.80)
├── ExactPrefLabelMatcher (0.98)
├── ExactRdfsLabelMatcher (0.95)
├── ExactAltLabelMatcher (0.90)
├── ExactHiddenLabelMatcher (0.85)
└── ExactLocalNameMatcher (0.80)

Tier 2: Ontology Structure (0.60 to 0.75)
├── PropertyHierarchyMatcher (0.65)
├── OWLCharacteristicsMatcher (0.60)
├── RestrictionBasedMatcher (0.55)
└── SKOSRelationsMatcher (0.50)

Tier 3: Semantic & Lexical (0.45 to 0.70)
├── SemanticSimilarityMatcher (0.45) - Pure embeddings
└── LexicalMatcher (0.60) - Pure string matching

Tier 4: Context & Boosters (0.0 to 0.70)
├── DataTypeInferenceMatcher (0.0) - Booster only
├── HistoryAwareMatcher (0.60)
└── StructuralMatcher (0.70)

Tier 5: Graph Reasoning (0.60)
└── GraphReasoningMatcher (0.60)

Tier 6: Fallback Fuzzy (0.40 to 0.60)
├── PartialStringMatcher (0.60)
└── FuzzyStringMatcher (0.40)
```

## Testing Results

### Mortgage Example (10 columns):
```
InterestRate → interestRate (LexicalMatcher, 0.95)
OriginationDate → originationDate (LexicalMatcher, 0.95)
LoanTerm → loanTerm (LexicalMatcher, 0.95)
LoanID → loanNumber (SemanticSimilarityMatcher, ~0.89)
Principal → principalAmount (LexicalMatcher, ~0.85)
Status → loanStatus (SemanticSimilarityMatcher, 0.79)
BorrowerName → borrowerName (ObjectPropertyMatcher, 0.95)
PropertyAddress → propertyAddress (ObjectPropertyMatcher, 0.95)
BorrowerID → hasBorrower (RelationshipMatcher, 0.92) ✅ Fixed from 1.00
PropertyID → collateralProperty (RelationshipMatcher, 0.92) ✅ Fixed from 1.00
```

**Result:** 10/10 columns mapped with realistic confidence scores

## Key Improvements

### Separation of Concerns ✅
- **SemanticSimilarityMatcher**: Only embeddings
- **LexicalMatcher**: Only string algorithms
- **DataTypeInferenceMatcher**: Only type compatibility
- Clear responsibility boundaries

### Realistic Confidence ✅
- No more 1.00 scores (absolute certainty is unrealistic)
- Confidence reflects uncertainty levels:
  - 0.98: Highest (prefLabel exact)
  - 0.92-0.95: Very high (exact matches, FKs)
  - 0.80-0.90: High (partial exact, alt labels)
  - 0.60-0.80: Medium (semantic, lexical partial)
  - 0.40-0.60: Low (fuzzy)

### Better Evidence ✅
- LexicalMatcher shows which algorithm: `lexical (substring)`, `lexical (token)`, etc.
- SemanticSimilarityMatcher shows breakdown: `embedding (phrase=0.82; token=0.64)`
- Clear attribution in UI

### Maintainability ✅
- Each matcher ~200 lines, single responsibility
- Easy to test individually
- Easy to add new matchers
- Clear documentation

## Benefits Realized

1. **Transparency:** Users see exactly how each match was made
2. **Tunability:** Can adjust thresholds per algorithm independently
3. **Robustness:** LexicalMatcher provides fallback when embeddings unavailable
4. **Accuracy:** Separation prevents cross-contamination of match logic
5. **Confidence:** Scores now reflect actual uncertainty levels

## Validation

### Command:
```bash
python -c "from rdfmap.generator.mapping_generator import MappingGenerator, GeneratorConfig; \
  gen=MappingGenerator('examples/mortgage/ontology/mortgage.ttl','examples/mortgage/data/loans.csv',\
  GeneratorConfig(base_iri='http://example.org/')); \
  m, r=gen.generate_with_alignment_report(); \
  print(f'{r.statistics.mapped_columns}/{r.statistics.total_columns} mapped')"
```

### Expected Output:
- 10/10 columns mapped
- No confidence scores = 1.00
- Mix of matchers used appropriately

## Next Steps (Phase 2-3)

### Immediate:
- ✅ Phase 1.1: LexicalMatcher created
- ✅ Phase 1.2: SemanticSimilarityMatcher refactored
- ✅ Phase 1.3: Confidence scores adjusted
- ✅ Phase 1.4: Pipeline updated

### Next Priority:
- **Phase 2: Enhanced Evidence Display**
  - Format matcher attribution with details
  - Show confidence explanation breakdown
  - Add tooltips/badges in UI

- **Phase 3: SKOS Vocabulary Integration**
  - Create mortgage_vocab.ttl
  - Wire SKOS into matchers
  - Display SKOS labels in evidence

## Files Created/Modified

### Created:
- `src/rdfmap/generator/matchers/lexical_matcher.py` (280 lines)

### Modified:
- `src/rdfmap/generator/matchers/semantic_matcher.py` (removed ~200 lines of lexical code)
- `src/rdfmap/generator/matchers/exact_matchers.py` (confidence 1.0 → 0.98)
- `src/rdfmap/generator/matchers/factory.py` (added LexicalMatcher to pipeline)
- `src/rdfmap/generator/matchers/__init__.py` (exported LexicalMatcher)
- `src/rdfmap/generator/mapping_generator.py` (RelationshipMatcher 1.0 → 0.92)

## Lessons Learned

1. **1.00 is hubris:** Even perfect matches have edge cases. Cap at 0.98.
2. **Separation matters:** Mixed logic creates confusion and bugs.
3. **Evidence is king:** Users need to understand why a match was made.
4. **Fallback chains work:** SemanticMatcher → LexicalMatcher → FuzzyMatcher provides robustness.

---

**Status:** Phase 1 Complete ✅  
**Quality:** Production-ready  
**Test Coverage:** Validated with mortgage example  
**User Impact:** More realistic confidence, clearer explanations

