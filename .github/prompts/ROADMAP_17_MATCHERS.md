# Roadmap: Activating All 17 Matchers
## Demonstrating Ontology-Based Reasoning in Real-World Scenarios

**Date:** November 17, 2025  
**Goal:** Get 17/17 matchers firing with rich evidence showing how ontology reasoning **supports** and **validates** semantic similarity matches

---

## Philosophy: Human-Like Reasoning

### The Vision
When a human maps data, they use **multiple reasoning strategies simultaneously:**

1. **Intuition** (Semantic Similarity): "Employee ID feels like it matches employeeID"
2. **Formal Knowledge** (Ontology): "Employee ID is an identifier, and identifiers have these characteristics..."
3. **Validation** (OWL/SHACL): "The data is 100% unique, confirming it's an InverseFunctionalProperty"
4. **Context** (Graph Reasoning): "This ID references the Employee entity based on the relationship structure"
5. **Experience** (History): "We've mapped similar columns before"

**Our system should mirror this by showing evidence from ALL reasoning strategies, not just the winner.**

### Current State vs Desired State

**Current (10/17 firing):**
```
Column: "EmpID" → employeeID
Winner: ExactAltLabelMatcher (0.95)
Evidence: 
  - ExactAltLabelMatcher: 0.90
  - SemanticSimilarityMatcher: 0.85
  - LexicalMatcher: 0.80
```

**Desired (17/17 firing):**
```
Column: "EmpID" → employeeID
Winner: ExactAltLabelMatcher (0.95)
Evidence:
  - ExactAltLabelMatcher: 0.90 (exact SKOS match)
  - SemanticSimilarityMatcher: 0.85 (embedding similarity)
  ⭐ OWLCharacteristicsMatcher: 0.82 (IFP + 100% unique validates choice)
  ⭐ PropertyHierarchyMatcher: 0.78 (confirms it's an identifier)
  ⭐ GraphReasoningMatcher: 0.75 (foreign key pattern detected)
  ⭐ DataTypeInferenceMatcher: +0.05 (string datatype aligns)
  - LexicalMatcher: 0.80 (token overlap)
  ⭐ StructuralMatcher: 0.70 (co-occurs with other ID fields)
```

**The ontology matchers provide supporting evidence that validates the semantic match!**

---

## Missing Matchers Analysis

### Currently Missing (7/17)

| Matcher | Current Status | Why It Matters | Use Case |
|---------|---------------|----------------|----------|
| DataTypeInferenceMatcher | Not firing | Validates type compatibility | "Age column has integers matching xsd:integer" |
| ExactLocalNameMatcher | Not firing | Catches camelCase conventions | "employeeID" column matches ex:employeeID URI |
| FuzzyStringMatcher | Not firing | Handles typos/abbreviations | "Emplyee ID" → employeeID (typo) |
| GraphReasoningMatcher | Not firing | Detects relationships/FKs | "DeptCode" → Department relationship |
| HistoryAwareMatcher | Not firing | Learns from past mappings | "We mapped similar columns before" |
| RestrictionBasedMatcher | Not firing | Validates OWL constraints | "Age 225 violates max 100" |
| StructuralMatcher | Not firing | Detects field groupings | "FirstName + LastName → MiddleName likely" |

---

## Roadmap: Getting to 17/17

### Phase 1: Quick Wins (1-2 hours)

#### 1.1 DataTypeInferenceMatcher - Make it Fire as Evidence
**Current Issue:** Acts as booster, never appears in evidence  
**Solution:** Change it to always return a result with low confidence

**Implementation:**
```python
# In datatype_matcher.py
def match(self, column, properties, context):
    # Current: returns None if threshold not met
    # New: always return best type match with confidence
    
    best_match = None
    best_score = 0.0
    
    for prop in properties:
        if self._types_compatible(column.inferred_type, prop.range_type):
            score = 0.60  # Low but present
            if score > best_score:
                best_match = prop
                best_score = score
    
    if best_match:
        return MatchResult(
            property=best_match,
            match_type=MatchType.DATA_TYPE_COMPATIBILITY,
            confidence=best_score,
            matched_via=f"Type compatibility: {column.inferred_type} → {best_match.range_type}",
            matcher_name="DataTypeInferenceMatcher"
        )
```

**Test Case:**
- Column: "Age" (integers) → ex:age (xsd:integer)
- Expected: "DataTypeInferenceMatcher: 0.60 - Type compatibility validates match"

**Value:** Shows that ontology types align with data, providing formal validation

---

#### 1.2 ExactLocalNameMatcher - Add Test Cases
**Current Issue:** No columns match property local names  
**Solution:** Add camelCase columns to test data

**Test Data Addition:**
```csv
# Add these columns to employees.csv
employeeID,firstName,lastName,dateOfBirth,hireDate,annualSalary

E1001,John,Smith,1985-03-15,2020-01-15,95000
```

**Expected Evidence:**
```
Column: "employeeID" → employeeID
Evidence:
  - ExactLocalNameMatcher: 0.80 (URI local name exact match)
  - SemanticSimilarityMatcher: 0.75
```

**Value:** Shows property URI naming conventions are meaningful

---

#### 1.3 FuzzyStringMatcher - Add Messy Data
**Current Issue:** Test data is too clean  
**Solution:** Add deliberate typos and abbreviations

**Test Data Addition:**
```csv
# Add these messy columns
Emplyee_ID,Frist_Name,Brth_Date,Anual_Salary,Dept_Nam

E1001,John,1985-03-15,95000,Engineering
```

**Expected Evidence:**
```
Column: "Emplyee_ID" → employeeID
Winner: SemanticSimilarityMatcher (0.82)
Evidence:
  - SemanticSimilarityMatcher: 0.82 (embedding handles typo)
  ⭐ FuzzyStringMatcher: 0.65 (edit distance=2, confirms match)
  ⭐ OWLCharacteristicsMatcher: 0.70 (IFP validation)
```

**Value:** Fuzzy matching **validates** semantic match despite typo

---

### Phase 2: Ontology Reasoning (2-3 hours)

#### 2.1 GraphReasoningMatcher - Implement FK Detection
**Current Issue:** Needs reasoner instance  
**Solution:** Implement lightweight FK pattern detection without full reasoner

**Implementation:**
```python
# In graph_matcher.py
class GraphReasoningMatcher(ColumnPropertyMatcher):
    def match(self, column, properties, context):
        # Pattern 1: Column ends with ID/Code/Ref
        if self._is_foreign_key_pattern(column.name):
            # Look for object properties
            for prop in properties:
                if prop.is_object_property:
                    if self._fk_matches_property(column.name, prop):
                        return MatchResult(
                            property=prop,
                            match_type=MatchType.GRAPH_REASONING,
                            confidence=0.75,
                            matched_via=f"FK pattern: {column.name} references {prop.range_type}",
                            matcher_name="GraphReasoningMatcher"
                        )
        
        # Pattern 2: Data values reference entity IDs
        if self._values_reference_other_table(column, context):
            # Score based on referential integrity
            ...
```

**Test Cases:**
```csv
DepartmentCode,ManagerRef,ReportsToID,BelongsToDept

D001,M501,M501,D001
```

**Expected Evidence:**
```
Column: "DepartmentCode" → worksInDepartment
Winner: SemanticSimilarityMatcher (0.80)
Evidence:
  - SemanticSimilarityMatcher: 0.80
  ⭐ GraphReasoningMatcher: 0.75 (FK pattern detected, references Department)
  ⭐ OWLCharacteristicsMatcher: 0.70 (object property domain/range validated)
```

**Value:** Graph reasoning **confirms** that semantic match is a relationship, not just a property

---

#### 2.2 RestrictionBasedMatcher - Validation Evidence
**Current Issue:** Validation phase, not matching phase  
**Solution:** Make it contribute evidence showing constraint compliance

**Implementation:**
```python
# In restriction_matcher.py
def match(self, column, properties, context):
    # Check OWL restrictions for each property
    for prop in properties:
        restrictions = self._get_restrictions(prop)
        
        if restrictions:
            compliance_score = self._check_compliance(column, restrictions)
            
            if compliance_score > 0.5:  # Even partial compliance is evidence
                violations = self._get_violations(column, restrictions)
                
                return MatchResult(
                    property=prop,
                    match_type=MatchType.RESTRICTION_BASED,
                    confidence=compliance_score,
                    matched_via=f"OWL constraints: {len(violations)} violations found",
                    matcher_name="RestrictionBasedMatcher"
                )
```

**Test Cases:**
```csv
Age,Salary,Email

39,95000,john@company.com     # Valid
225,-5000,invalid             # Invalid age, invalid salary
```

**Expected Evidence:**
```
Column: "Age" → age
Winner: ExactRdfsLabelMatcher (0.95)
Evidence:
  - ExactRdfsLabelMatcher: 0.95
  - SemanticSimilarityMatcher: 0.88
  ⭐ RestrictionBasedMatcher: 0.90 (9/10 values comply with range 18-100)
  ⚠️ Validation: 1 value (225) violates maxInclusive 100
```

**Value:** Shows ontology constraints validate data quality

---

#### 2.3 StructuralMatcher - Co-occurrence Patterns
**Current Issue:** Doesn't detect field groupings  
**Solution:** Implement sibling field detection

**Implementation:**
```python
# In structural_matcher.py
def match(self, column, properties, context):
    # If firstName and lastName already matched...
    matched_siblings = self._get_matched_siblings(column, context)
    
    if matched_siblings:
        # Look for properties in same domain/hierarchy
        for prop in properties:
            if self._is_sibling_property(prop, matched_siblings):
                confidence = 0.70 + (0.05 * len(matched_siblings))
                
                return MatchResult(
                    property=prop,
                    match_type=MatchType.STRUCTURAL_PATTERN,
                    confidence=confidence,
                    matched_via=f"Co-occurs with {len(matched_siblings)} related fields",
                    matcher_name="StructuralMatcher"
                )
```

**Test Cases:**
```csv
FirstName,LastName,MiddleInitial,FullName

John,Smith,A,John A. Smith
```

**Expected Evidence:**
```
Column: "MiddleInitial" → middleName
Winner: SemanticSimilarityMatcher (0.78)
Evidence:
  - SemanticSimilarityMatcher: 0.78
  ⭐ StructuralMatcher: 0.75 (co-occurs with firstName, lastName - name group detected)
  ⭐ PropertyHierarchyMatcher: 0.72 (all three are children of hasName)
```

**Value:** Structural patterns **validate** that the field belongs to a logical group

---

### Phase 3: Advanced Features (1-2 hours)

#### 3.1 HistoryAwareMatcher - Session History
**Current Issue:** Needs previous mapping runs  
**Solution:** Track mappings within current session

**Implementation:**
```python
# In history_matcher.py
class HistoryAwareMatcher(ColumnPropertyMatcher):
    def __init__(self):
        self.history = []  # List of (column_pattern, property) tuples
    
    def match(self, column, properties, context):
        # Check if similar column was mapped before
        for prev_column, prev_property in self.history:
            similarity = self._column_similarity(column.name, prev_column)
            
            if similarity > 0.8:
                # Find same property in current list
                matching_prop = self._find_property(prev_property, properties)
                
                if matching_prop:
                    return MatchResult(
                        property=matching_prop,
                        match_type=MatchType.HISTORY_BASED,
                        confidence=0.70 * similarity,
                        matched_via=f"Previously mapped similar column: {prev_column}",
                        matcher_name="HistoryAwareMatcher"
                    )
    
    def record_mapping(self, column, property):
        self.history.append((column, property))
```

**Test Cases:**
- Map employees.csv first
- Then map contractors.csv with similar columns

**Expected Evidence:**
```
Column: "Contractor_ID" → contractorID (new dataset)
Evidence:
  - SemanticSimilarityMatcher: 0.82
  ⭐ HistoryAwareMatcher: 0.75 (similar to "Employee_ID" mapped earlier)
  - ExactLocalNameMatcher: 0.80
```

**Value:** Shows learning from past mappings, human-like pattern recognition

---

## Implementation Priority

### Week 1: Core Ontology Matchers (High Priority)
1. ✅ DataTypeInferenceMatcher - Always fire (4 hours)
2. ✅ GraphReasoningMatcher - FK detection (6 hours)
3. ✅ RestrictionBasedMatcher - Validation evidence (4 hours)

**Impact:** These provide **ontological validation** of semantic matches

### Week 2: Pattern Recognition (Medium Priority)
4. ✅ StructuralMatcher - Co-occurrence (4 hours)
5. ✅ ExactLocalNameMatcher - Add test data (2 hours)
6. ✅ FuzzyStringMatcher - Add messy data (2 hours)

**Impact:** Handles real-world messiness while showing formal support

### Week 3: Learning Features (Low Priority)
7. ✅ HistoryAwareMatcher - Session tracking (4 hours)

**Impact:** Demonstrates experience-based reasoning

---

## Success Criteria

### Per-Matcher Goals

Each matcher should:
1. **Fire for at least 3 different columns** in test suite
2. **Appear in evidence** for 10+ columns (even when not winner)
3. **Demonstrate unique value** (not redundant with other matchers)
4. **Show ontology-based reasoning** that validates/supports semantic matches

### Evidence Quality Goal

**Target evidence format:**
```
Column: "employee_id" → employeeID
Winner: SemanticSimilarityMatcher (0.85)

Semantic Reasoning:
  ✅ SemanticSimilarityMatcher: 0.85 (embedding similarity)
  ✅ LexicalMatcher: 0.75 (token overlap)
  ✅ FuzzyStringMatcher: 0.65 (handles underscore variant)

Ontological Validation:
  ⭐ OWLCharacteristicsMatcher: 0.80 (IFP + 100% unique data)
  ⭐ PropertyHierarchyMatcher: 0.75 (confirmed as identifier type)
  ⭐ DataTypeInferenceMatcher: 0.60 (string type aligns)
  ⭐ GraphReasoningMatcher: 0.70 (primary key pattern)

Structural Context:
  ⭐ StructuralMatcher: 0.72 (co-occurs with other employee fields)

Confidence: VERY HIGH
Reason: Semantic match validated by 4 ontological constraints + structural patterns
```

**This shows human-like multi-perspective reasoning!**

---

## Communication Strategy

### For Users: "Why This Match?"

**Before (10/17 matchers):**
> "Matched 'EmpID' to employeeID with 0.85 confidence based on semantic similarity."

**After (17/17 matchers):**
> "Matched 'EmpID' to employeeID with 0.92 confidence.
> 
> **Reasoning:**
> - ✅ Semantic similarity: 0.85 (strong embedding match)
> - ⭐ Ontology validates: employeeID is an InverseFunctionalProperty with 100% unique values ✓
> - ⭐ Type system confirms: String data type matches xsd:string ✓
> - ⭐ Graph structure: Primary key pattern detected ✓
> - ⭐ Property hierarchy: Confirmed as identifier (top of hierarchy) ✓
> 
> **Conclusion:** Semantic match validated by 4 independent ontological checks. Very high confidence."

### For Technical Users: "How Does It Work?"

**Evidence Table:**
| Matcher | Type | Confidence | Reasoning |
|---------|------|------------|-----------|
| SemanticSimilarityMatcher | Semantic | 0.85 | BERT embedding similarity |
| OWLCharacteristicsMatcher | Ontology | 0.80 | IFP + data uniqueness validated |
| PropertyHierarchyMatcher | Ontology | 0.75 | Identifier hierarchy confirmed |
| GraphReasoningMatcher | Ontology | 0.70 | Primary key pattern |
| DataTypeInferenceMatcher | Ontology | 0.60 | Type alignment |
| StructuralMatcher | Context | 0.72 | Field grouping detected |

**6 different reasoning strategies agree!**

---

## Testing Strategy

### Test Suite Requirements

1. **Clean Data Test** (exact matching dominates)
   - Validates SKOS vocabulary works
   - Exact matchers win, ontology provides supporting evidence

2. **Messy Data Test** (semantic + ontology)
   - Typos, abbreviations, inconsistent naming
   - Semantic wins, ontology validates
   - **This is the key test for demonstrating value**

3. **Ambiguous Data Test** (ontology disambiguates)
   - Multiple semantic matches possible
   - Ontology constraints break tie
   - Example: "ID" could be many things, but IFP + FK pattern → employeeID

4. **Invalid Data Test** (ontology catches errors)
   - Semantic match looks good
   - Ontology restrictions show violations
   - User warned: "Match confidence reduced due to constraint violations"

### Expected Results

| Test Type | Matchers Firing | Ontology Impact |
|-----------|-----------------|-----------------|
| Clean | 12-14/17 | Supporting evidence (60% of decisions) |
| Messy | 15-16/17 | Validation evidence (80% of decisions) |
| Ambiguous | 14-15/17 | Tie-breaking evidence (40% of decisions) |
| Invalid | 16-17/17 | Warning evidence (100% of decisions) |

**Target: 17/17 in messy data test** with ontology matchers providing crucial validation

---

## Documentation Requirements

### Per-Matcher Documentation

Each matcher needs:

1. **Purpose Statement**
   - "GraphReasoningMatcher detects foreign key relationships based on data patterns and naming conventions"

2. **When It Fires**
   - "When column names end with 'ID', 'Code', 'Ref' AND target property is object property"

3. **Ontological Basis**
   - "Uses OWL object properties (rdfs:domain, rdfs:range) to validate relationships"

4. **Real-World Scenario**
   - "Dataset: Customer orders with 'CustomerCode' column"
   - "Semantic match: 'customer' → Customer entity (0.78)"
   - "Graph reasoning: Validates it's a relationship to Customer (0.75)"
   - "Combined confidence: 0.85 (validated by graph structure)"

5. **Evidence Example**
   ```json
   {
     "matcher": "GraphReasoningMatcher",
     "confidence": 0.75,
     "reasoning": "FK pattern detected: CustomerCode references Customer entity",
     "ontological_basis": "owl:ObjectProperty with rdfs:range ex:Customer",
     "data_validation": "95% of values exist in Customer.ID column"
   }
   ```

---

## Timeline

### Week 1: Foundation (16 hours)
- Day 1-2: DataTypeInferenceMatcher always fires
- Day 3-4: GraphReasoningMatcher FK detection
- Day 5: RestrictionBasedMatcher validation evidence

**Milestone:** 13/17 matchers firing, ontology validation present in 70% of matches

### Week 2: Patterns (8 hours)
- Day 1: StructuralMatcher co-occurrence
- Day 2: ExactLocalNameMatcher + FuzzyStringMatcher test data
- Day 3: Integration testing

**Milestone:** 16/17 matchers firing, evidence quality high

### Week 3: Learning (4 hours)
- Day 1: HistoryAwareMatcher session tracking
- Day 2: Documentation
- Day 3: Final testing

**Milestone:** 17/17 matchers firing, comprehensive documentation

**Total Time:** ~28 hours over 3 weeks

---

## Success Metrics

### Quantitative
- ✅ 17/17 matchers firing in messy data test
- ✅ Average 6-8 evidence entries per column
- ✅ Ontology matchers present in 80%+ of evidence lists
- ✅ Confidence scores more accurate (validated by ontology)

### Qualitative
- ✅ Users understand WHY matches were made
- ✅ Ontology provides formal validation of semantic intuition
- ✅ System feels "intelligent" - multiple reasoning strategies
- ✅ Edge cases handled gracefully with explanations

### User Feedback Target
> "The system doesn't just guess - it shows me that the semantic match is validated by the ontology structure, data types, and relationship patterns. I trust it because I can see the reasoning."

---

## Conclusion

This roadmap transforms our system from:
- **"Smart text matcher"** (embeddings only)

To:
- **"Ontology-aware semantic reasoner"** (embeddings + formal logic)

The key insight: **Ontology matchers don't compete with semantic matching - they validate it.**

Like a human who uses both intuition (embeddings) and formal knowledge (ontology), our system will show:
1. "This looks like a match" (semantic)
2. "And here's why it's definitely right" (ontology)

**This is the future of explainable, trustworthy AI for data integration.**

---

**Next Step:** Begin Week 1 implementation with DataTypeInferenceMatcher

