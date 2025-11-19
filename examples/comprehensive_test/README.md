# Comprehensive Matcher Test Suite

**Purpose:** Validate that each matcher in the pipeline provides unique value and correctly identifies its target patterns.

## Dataset Overview

- **File:** `examples/comprehensive_test/employees.csv`
- **Ontology:** `examples/comprehensive_test/hr_ontology.ttl`
- **SKOS Vocabulary:** `examples/comprehensive_test/hr_vocabulary.ttl`
- **Total Columns:** 20
- **Total Properties:** 18

## Matcher-by-Matcher Validation

### 1. ExactPrefLabelMatcher (Confidence: 0.98)
**Threshold:** 0.98

**Test Column:**
- `Employee ID` → `ex:employeeID`

**Expected Behavior:**
- Column name exactly matches `skos:prefLabel "Employee ID"`
- Should be the highest confidence match (0.98)
- Evidence: `matched via skos:prefLabel`

**Validation:**
```bash
# Should show ExactPrefLabelMatcher with 0.98 confidence
grep "Employee ID" alignment_report.json
```

---

### 2. ExactRdfsLabelMatcher (Confidence: 0.95)
**Threshold:** 0.95

**Test Column:**
- `Full Name` → `ex:fullName`

**Expected Behavior:**
- Column name matches `rdfs:label "full name"` (case-insensitive, spaces normalized)
- Second highest confidence tier
- Evidence: `matched via rdfs:label`

**Validation:**
```bash
# Should show ExactRdfsLabelMatcher with 0.95 confidence
grep "Full Name" alignment_report.json
```

---

### 3. ExactAltLabelMatcher (Confidence: 0.90)
**Threshold:** 0.90

**Test Column:**
- `Birth Date` → `ex:dateOfBirth`

**Expected Behavior:**
- Column matches `skos:altLabel "Birth Date"`
- Property has `skos:prefLabel "Date of Birth"` (different from column)
- Demonstrates value of alternative labels for common variations

**Validation:**
```bash
# Should show ExactAltLabelMatcher with 0.90 confidence
grep "Birth Date" alignment_report.json
```

---

### 4. ExactHiddenLabelMatcher (Confidence: 0.85)
**Threshold:** 0.85

**Test Columns:**
- `emp_num` → `ex:employeeNumber`
- `hire_dt` → `ex:hireDate`

**Expected Behavior:**
- Matches legacy database abbreviations via `skos:hiddenLabel`
- `emp_num` matches hidden label (not visible in UI normally)
- `hire_dt` matches hidden label (common DB abbreviation pattern)
- Demonstrates support for legacy/database naming conventions

**Validation:**
```bash
# Should show ExactHiddenLabelMatcher with 0.85 confidence
grep "emp_num\|hire_dt" alignment_report.json
```

---

### 5. ExactLocalNameMatcher (Confidence: 0.80)
**Threshold:** 0.80

**Test Column:**
- `startDate` → `ex:startDate`

**Expected Behavior:**
- Column matches property local name (camelCase)
- No SKOS/RDFS label matches this exact form
- Lowest confidence among exact matchers
- Demonstrates matching when ontology lacks proper labels

**Validation:**
```bash
# Should show ExactLocalNameMatcher with 0.80 confidence
grep "startDate" alignment_report.json
```

---

### 6. SemanticSimilarityMatcher (Confidence: 0.45-0.89)
**Threshold:** 0.45

**Test Columns:**
- `EmpID` → `ex:employeeNumber` (embedding similarity ~0.85)
- `Compensation` → `ex:annualSalary` (embedding similarity ~0.75)
- `Office Location` → `ex:workLocation` (embedding similarity ~0.80)

**Expected Behavior:**
- Uses sentence transformers for semantic similarity
- `EmpID` has no exact label match but semantically close to "employee number"
- `Compensation` broadly related to "annual salary"
- `Office Location` semantically similar to "work location"
- Evidence shows: `embedding (phrase=X; token=Y; id_boost=Z)`

**Validation:**
```bash
# Should show SemanticSimilarityMatcher with confidence 0.45-0.89
grep "EmpID\|Compensation\|Office Location" alignment_report.json | grep "SemanticSimilarityMatcher"
```

**Unique Value:**
- Handles abbreviations and synonyms not in SKOS
- Works across languages/domains
- Catches semantically related terms

---

### 7. LexicalMatcher (Confidence: 0.40-0.95)
**Threshold:** 0.60

**Test Columns:**
- `annual_comp` → `ex:annualCompensation` (substring match ~0.85)
- `mgr` → `ex:reportsTo` or manager-related (abbreviation ~0.70)
- `phone` → `ex:phoneNumber` (partial match ~0.80)

**Expected Behavior:**
- **Substring algorithm:** `annual_comp` is substring of `annualCompensation`
- **Token algorithm:** `mgr` matches via synonym normalization
- **Partial algorithm:** `phone` partially matches `phoneNumber`
- Evidence shows: `lexical (substring)`, `lexical (token)`, etc.

**Validation:**
```bash
# Should show LexicalMatcher with algorithm detail
grep "annual_comp\|mgr\|phone" alignment_report.json | grep "LexicalMatcher"
```

**Unique Value:**
- Fallback when embeddings unavailable
- Fast string matching without ML overhead
- Handles common abbreviation patterns

---

### 8. DataTypeInferenceMatcher (Confidence: 0.0, Booster: +0.05)
**Threshold:** 0.0 (always emits evidence)

**Test All Columns**

**Expected Behavior:**
- Never acts as primary matcher (threshold 0.0)
- Acts as booster (+0.05) when types align
- Validates: integer→integer, string→string, date→date
- Shows in evidence as secondary contributor

**Validation:**
```bash
# Check boosters_applied in match details
grep "DataTypeInferenceMatcher" alignment_report.json
```

**Unique Value:**
- Prevents wrong mappings (e.g., don't map string column to integer property)
- Boosts confidence when types align correctly
- Type safety validation

---

### 9. PropertyHierarchyMatcher (Confidence: 0.65)
**Threshold:** 0.65

**Test Column:**
- `ContactEmail` → `ex:email`

**Expected Behavior:**
- `ex:email` is `rdfs:subPropertyOf ex:contactInformation`
- Matcher recognizes hierarchical relationships
- Evidence shows: `matched via property hierarchy`

**Validation:**
```bash
# Should show PropertyHierarchyMatcher
grep "ContactEmail" alignment_report.json
```

**Unique Value:**
- Leverages ontology structure (subPropertyOf)
- Finds matches through inheritance
- Demonstrates ontology reasoning

---

### 10. OWLCharacteristicsMatcher (Confidence: 0.60)
**Threshold:** 0.60

**Test Column:**
- `SSN` → `ex:socialSecurityNumber`

**Expected Behavior:**
- `ex:socialSecurityNumber` is `owl:InverseFunctionalProperty`
- Matcher boosts confidence for unique identifier patterns
- Column data shows high uniqueness (100% distinct values)
- Evidence: `matched via InverseFunctionalProperty`

**Validation:**
```bash
# Should show OWLCharacteristicsMatcher
grep "SSN" alignment_report.json
```

**Unique Value:**
- Uses OWL semantics (functional, inverse functional)
- Validates identifier properties have appropriate uniqueness
- Demonstrates OWL reasoning

---

### 11. GraphReasoningMatcher (Confidence: 0.60)
**Threshold:** 0.60

**Test Columns:**
- `DepartmentID` → `ex:worksInDepartment` (FK to Department)
- `ManagerID` → `ex:reportsTo` (FK to Manager)

**Expected Behavior:**
- Detects foreign key relationships
- `DepartmentID` ends in "ID" and references Department class
- `ManagerID` references Manager class
- Evidence: `Foreign key to Department`, `Foreign key to Manager`

**Validation:**
```bash
# Should show RelationshipMatcher (GraphReasoningMatcher) with 0.92
grep "DepartmentID\|ManagerID" alignment_report.json | grep "RelationshipMatcher"
```

**Unique Value:**
- Detects object properties (relationships)
- Identifies foreign keys automatically
- Builds linked data structures

---

### 12. StructuralMatcher (Confidence: 0.70)
**Threshold:** 0.70

**Test Column:**
- `Team` → `ex:teamName`

**Expected Behavior:**
- Detects co-occurrence patterns with other columns
- If other "team" related columns exist, boosts confidence
- Evidence: `structural co-occurrence`

**Validation:**
```bash
# Should show StructuralMatcher
grep "Team" alignment_report.json
```

**Unique Value:**
- Uses column co-occurrence patterns
- Contextual matching
- Learns from data structure

---

### 13. PartialStringMatcher (Confidence: 0.60)
**Threshold:** 0.60

**Test Column:**
- `pos` → `ex:positionTitle`

**Expected Behavior:**
- `pos` is partial match to `position`
- Fuzzy/approximate string matching
- Evidence: `partial string match`

**Validation:**
```bash
# Should show PartialStringMatcher
grep "\"pos\"" alignment_report.json
```

**Unique Value:**
- Catches extreme abbreviations
- Last resort before failure
- Tolerance for poor data quality

---

### 14. FuzzyStringMatcher (Confidence: 0.40)
**Threshold:** 0.40

**Test Column:**
- `adrs` → `ex:address`

**Expected Behavior:**
- `adrs` is typo/abbreviation of `address`
- Edit distance/fuzzy matching
- Evidence: `fuzzy match`

**Validation:**
```bash
# Should show FuzzyStringMatcher
grep "adrs" alignment_report.json
```

**Unique Value:**
- Handles typos and misspellings
- Extreme abbreviations
- Lowest confidence fallback

---

## Expected Results Summary

| Column | Property | Matcher | Confidence | Notes |
|--------|----------|---------|------------|-------|
| Employee ID | employeeID | ExactPrefLabelMatcher | 0.98 | Highest confidence |
| Full Name | fullName | ExactRdfsLabelMatcher | 0.95 | rdfs:label match |
| Birth Date | dateOfBirth | ExactAltLabelMatcher | 0.90 | altLabel variant |
| emp_num | employeeNumber | ExactHiddenLabelMatcher | 0.85 | Legacy DB name |
| hire_dt | hireDate | ExactHiddenLabelMatcher | 0.85 | Legacy DB abbreviation |
| startDate | startDate | ExactLocalNameMatcher | 0.80 | Local name match |
| EmpID | employeeNumber | SemanticSimilarityMatcher | ~0.85 | Embedding similarity |
| Compensation | annualSalary | SemanticSimilarityMatcher | ~0.75 | Semantic relation |
| Office Location | workLocation | SemanticSimilarityMatcher | ~0.80 | Semantic similarity |
| annual_comp | annualCompensation | LexicalMatcher | ~0.85 | Substring match |
| mgr | reportsTo | LexicalMatcher | ~0.70 | Abbreviation |
| phone | phoneNumber | LexicalMatcher | ~0.80 | Partial match |
| ContactEmail | email | PropertyHierarchyMatcher | 0.65 | Property hierarchy |
| SSN | socialSecurityNumber | OWLCharacteristicsMatcher | 0.60 | InverseFunctionalProperty |
| DepartmentID | worksInDepartment | RelationshipMatcher | 0.92 | Foreign key |
| ManagerID | reportsTo | RelationshipMatcher | 0.92 | Foreign key |
| Team | teamName | StructuralMatcher | 0.70 | Co-occurrence |
| pos | positionTitle | PartialStringMatcher | 0.60 | Extreme abbreviation |
| adrs | address | FuzzyStringMatcher | 0.40 | Typo/misspelling |

**Total:** 19/20 columns should map successfully (95%)

## Running the Test

### Generate Mappings:
```bash
rdfmap generate \
  --ontology examples/comprehensive_test/hr_ontology.ttl \
  --skos examples/comprehensive_test/hr_vocabulary.ttl \
  --data examples/comprehensive_test/employees.csv \
  --output examples/comprehensive_test/mapping.yaml \
  --min-confidence 0.40
```

### Validate Results:
```bash
# Check alignment report
cat examples/comprehensive_test/alignment_report.json | jq '.match_details[] | {column: .column_name, property: .matched_property, matcher: .matcher_name, confidence: .confidence_score}'

# Verify each matcher was used
cat examples/comprehensive_test/alignment_report.json | jq '.match_details[].matcher_name' | sort | uniq -c

# Check confidence distribution
cat examples/comprehensive_test/alignment_report.json | jq '.statistics'
```

### Expected Matcher Usage:
```
2x ExactPrefLabelMatcher
1x ExactRdfsLabelMatcher
1x ExactAltLabelMatcher
2x ExactHiddenLabelMatcher
1x ExactLocalNameMatcher
3x SemanticSimilarityMatcher
3x LexicalMatcher
1x PropertyHierarchyMatcher
1x OWLCharacteristicsMatcher
2x RelationshipMatcher
1x StructuralMatcher
1x PartialStringMatcher
1x FuzzyStringMatcher
20x DataTypeInferenceMatcher (as booster)
```

## Success Criteria

✅ **All matchers used:** Each matcher should contribute at least one match  
✅ **No 1.00 confidence:** Maximum should be 0.98  
✅ **Evidence clarity:** Each match shows clear matcher attribution  
✅ **Confidence tiers respected:** Exact > Semantic > Lexical > Fuzzy  
✅ **Type safety:** DataTypeInferenceMatcher validates all mappings  
✅ **Relationship detection:** FKs correctly identified  
✅ **SKOS labels used:** Hidden labels catch legacy column names  
✅ **Hierarchy leveraged:** Property inheritance recognized  
✅ **OWL semantics:** InverseFunctionalProperty validated  

## Value Demonstration

Each matcher provides unique value:

1. **Exact matchers:** Handle well-labeled ontologies
2. **Semantic matcher:** Handles synonyms and semantic relations
3. **Lexical matcher:** Fallback for abbreviations and substrings
4. **Hierarchy matcher:** Leverages ontology structure
5. **OWL matcher:** Uses semantic web standards
6. **Graph matcher:** Builds linked data
7. **Fuzzy matchers:** Handles poor data quality

**Combined:** The matchers work together to achieve 95%+ mapping coverage across diverse column naming patterns.

