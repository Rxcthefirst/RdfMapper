# Enhanced Comprehensive Test Suite - Column Mapping Plan

**Version:** 2.0  
**Date:** November 17, 2025

## Overview

This enhanced test suite includes **31 columns** designed to exercise **all 17 matchers** in our pipeline. Each column is specifically crafted to test one or more matcher types.

## Column-by-Matcher Mapping

### Tier 1: Exact Label Matchers

#### 1. ExactPrefLabelMatcher (Confidence: 0.98)
| Column | Property | SKOS Label | Notes |
|--------|----------|------------|-------|
| Employee ID | ex:employeeID | skos:prefLabel "Employee ID" | Highest confidence match |

#### 2. ExactRdfsLabelMatcher (Confidence: 0.95)
| Column | Property | Label | Notes |
|--------|----------|-------|-------|
| Full Name | ex:fullName | rdfs:label "full name" | Standard RDFS label match |
| First Name | ex:firstName | rdfs:label "first name" | Part of name hierarchy |
| Last Name | ex:lastName | rdfs:label "last name" | Part of name hierarchy |
| startDate | ex:startDate | rdfs:label "start date" | Date property |
| Age | ex:age | rdfs:label "age" | Will trigger restrictions |

#### 3. ExactAltLabelMatcher (Confidence: 0.90)
| Column | Property | SKOS Label | Notes |
|--------|----------|------------|-------|
| Birth Date | ex:dateOfBirth | skos:altLabel "Birth Date" | Alternative label variant |

#### 4. ExactHiddenLabelMatcher (Confidence: 0.85)
| Column | Property | SKOS Label | Notes |
|--------|----------|------------|-------|
| emp_num | ex:employeeNumber | skos:hiddenLabel "emp_num" | Legacy database column |
| hire_dt | ex:hireDate | skos:hiddenLabel "hire_dt" | Legacy date abbreviation |
| mgr | ex:reportsTo | skos:hiddenLabel "mgr" | Manager abbreviation |
| adrs | ex:address | skos:hiddenLabel "adrs" | Typo/abbreviation |

#### 5. ExactLocalNameMatcher (Confidence: 0.80)
| Column | Property | Match | Notes |
|--------|----------|-------|-------|
| EmployeeID | ex:employeeID | Local name match | CamelCase property name |

---

### Tier 2: Ontology Structure Matchers

#### 6. PropertyHierarchyMatcher (Confidence: 0.65)
**Tests rdfs:subPropertyOf reasoning**

| Column | Property | Hierarchy Path | Notes |
|--------|----------|----------------|-------|
| identifier | ex:hasIdentifier | Top-level | Parent of hasName |
| name | ex:hasName | Middle-level | Child of hasIdentifier, parent of fullName |
| contact | ex:contactInformation | Top-level | Parent of email, phoneNumber |
| amount | ex:hasAmount | Top-level | Parent of hasSalary |
| salary | ex:hasSalary | Middle-level | Child of hasAmount, parent of annualSalary |

**Expected Behavior:**
- "identifier" → matches parent property
- "name" → matches middle of hierarchy (boost because child fullName already matched)
- Evidence shows: "matched via property hierarchy"

#### 7. OWLCharacteristicsMatcher (Confidence: 0.60)
**Tests Functional and InverseFunctionalProperty**

| Column | Property | OWL Characteristic | Data Pattern | Notes |
|--------|----------|-------------------|--------------|-------|
| SSN | ex:socialSecurityNumber | InverseFunctionalProperty | 100% unique | Uniquely identifies person |
| ContactEmail | ex:email | Functional + IFP | Should be unique | Each person has one email |

**Expected Behavior:**
- SSN: High confidence boost because data is 100% unique (matches IFP)
- ContactEmail: Validation check (should be unique per IFP)
- Evidence shows: "matched via InverseFunctionalProperty"

#### 8. RestrictionBasedMatcher (Confidence: 0.55)
**Tests OWL restrictions**

| Column | Property | Restriction | Invalid Data | Expected Warning |
|--------|----------|-------------|--------------|------------------|
| Age | ex:age | 18-100 range | Row 6: 225 | ⚠️ Exceeds maxInclusive |
| annual_comp | ex:annualSalary | min 0 | Row 6: -50000 | ⚠️ Negative salary |

**Expected Behavior:**
- Age 225 → validation warning "exceeds maxInclusive 100"
- Salary -50000 → validation warning "violates minInclusive 0"
- Evidence shows: "matched with restriction violations"

#### 9. SKOSRelationsMatcher (Confidence: 0.50)
**Tests skos:broader, skos:narrower, skos:exactMatch, skos:related**

| Column | Property | SKOS Relation | Notes |
|--------|----------|---------------|-------|
| role | ex:positionTitle | skos:exactMatch ex:jobTitle | Exact match across vocabularies |
| pos | ex:positionTitle | (partial) + skos relations | Position abbreviation |

**Expected Behavior:**
- "role" → recognizes exactMatch between positionTitle and jobTitle
- Evidence shows: "matched via skos:exactMatch"

---

### Tier 3: Semantic & Lexical Matchers

#### 10. SemanticSimilarityMatcher (Confidence: 0.45-0.89)
**Tests embedding-based matching**

| Column | Property | Semantic Relation | Expected Confidence |
|--------|----------|-------------------|---------------------|
| EmpID | ex:employeeNumber | Abbreviation + ID pattern | 0.85+ |
| Compensation | ex:annualSalary | Synonym | 0.75+ |
| Office Location | ex:workLocation | Semantic similarity | 0.80+ |

**Expected Behavior:**
- Uses BERT embeddings for phrase + token similarity
- ID boost for "EmpID"
- Evidence shows: "embedding (phrase=X; token=Y; id_boost=Z)"

#### 11. LexicalMatcher (Confidence: 0.60-0.95)
**Tests 5 lexical algorithms**

| Column | Property | Algorithm | Expected Score |
|--------|----------|-----------|----------------|
| annual_comp | ex:annualCompensation | Substring | 0.85+ |
| phone | ex:phoneNumber | Partial | 0.80+ |

**Expected Behavior:**
- "annual_comp" is substring of "annualCompensation"
- Evidence shows: "lexical (substring)" or "lexical (token)"

---

### Tier 4: Context & Boosters

#### 12. DataTypeInferenceMatcher (Confidence: 0.0, Booster: +0.05)
**Tests type compatibility**

| Column | Data Type | Property Range | Expected |
|--------|-----------|----------------|----------|
| All integer columns | xsd:integer | xsd:integer | ✓ Boost |
| All string columns | xsd:string | xsd:string | ✓ Boost |
| All date columns | xsd:date | xsd:date | ✓ Boost |

**Expected Behavior:**
- Never acts as primary matcher (threshold 0.0)
- Adds +0.05 boost when types align
- Shows in evidence as secondary contributor

#### 13. StructuralMatcher (Confidence: 0.70)
**Tests co-occurrence patterns**

| Column | Property | Context | Expected Boost |
|--------|----------|---------|----------------|
| middle | ex:middleName | After First Name + Last Name matched | 0.15+ boost |

**Expected Behavior:**
- After matching "First Name" and "Last Name"
- "middle" gets context boost because siblings matched
- Evidence shows: "structural co-occurrence with [firstName, lastName]"

---

### Tier 5: Graph Reasoning

#### 14. GraphReasoningMatcher / RelationshipMatcher (Confidence: 0.92)
**Tests foreign key detection**

| Column | Property | Relationship | Notes |
|--------|----------|--------------|-------|
| DepartmentID | ex:worksInDepartment | FK to Department | Object property |
| ManagerID | ex:reportsTo | FK to Manager | Object property |

**Expected Behavior:**
- Detects columns ending in "ID" as foreign keys
- Maps to object properties (relationships)
- Evidence shows: "Foreign key to Department"

---

### Tier 6: Fallback Matchers

#### 15. PartialStringMatcher (Confidence: 0.60)
**Tests partial/abbreviation matching**

| Column | Property | Pattern | Notes |
|--------|----------|---------|-------|
| pos | ex:positionTitle | "pos" ⊂ "position" | Extreme abbreviation |

**Expected Behavior:**
- Catches partial matches
- Evidence shows: "partial string match"

#### 16. FuzzyStringMatcher (Confidence: 0.40)
**Tests typo/fuzzy matching**

| Column | Property | Pattern | Notes |
|--------|----------|---------|-------|
| adrs | ex:address | Edit distance | Typo/abbreviation |

**Expected Behavior:**
- Uses edit distance algorithms
- Evidence shows: "fuzzy match"

---

## Expected Test Results

### Matcher Usage Summary
| Matcher | Expected Count | Example Columns |
|---------|----------------|----------------|
| ExactPrefLabelMatcher | 1 | Employee ID |
| ExactRdfsLabelMatcher | 5-6 | Full Name, First Name, Last Name, startDate, Age |
| ExactAltLabelMatcher | 1 | Birth Date |
| ExactHiddenLabelMatcher | 4 | emp_num, hire_dt, mgr, adrs |
| ExactLocalNameMatcher | 1 | EmployeeID |
| **PropertyHierarchyMatcher** | 5 | identifier, name, contact, amount, salary |
| **OWLCharacteristicsMatcher** | 2 | SSN, ContactEmail |
| **RestrictionBasedMatcher** | 2 | Age, annual_comp (with warnings) |
| **SKOSRelationsMatcher** | 1-2 | role |
| SemanticSimilarityMatcher | 3-5 | EmpID, Compensation, Office Location |
| LexicalMatcher | 2-3 | annual_comp, phone |
| DataTypeInferenceMatcher | 31 | All (as booster) |
| **StructuralMatcher** | 1 | middle (after First/Last matched) |
| RelationshipMatcher | 2 | DepartmentID, ManagerID |
| PartialStringMatcher | 1 | pos |
| FuzzyStringMatcher | 1 | adrs |

**Target Coverage:** 16-17/17 matchers (94-100%)

### Validation Checks

#### Data Quality Warnings Expected:
1. **Age 225** (Row 6) → "Exceeds maxInclusive 100"
2. **Salary -50000** (Row 6) → "Violates minInclusive 0"

#### OWL Characteristic Validation:
1. **SSN uniqueness** → Should pass (all unique)
2. **Email IFP** → Should pass (all unique in this dataset)

### Evidence Format Examples

```
Column: identifier
Property: hasIdentifier
Matcher: PropertyHierarchyMatcher
Confidence: 0.68
Evidence: "matched via property hierarchy (parent of hasName)"

Column: SSN
Property: socialSecurityNumber
Matcher: OWLCharacteristicsMatcher
Confidence: 0.65
Evidence: "InverseFunctionalProperty + 100% unique data"

Column: Age (row 6)
Property: age
Matcher: ExactRdfsLabelMatcher
Confidence: 0.95
Validation: ⚠️ "Value 225 exceeds maxInclusive 100"
```

---

## Running the Test

```bash
# Test with SKOS vocabulary
python examples/comprehensive_test/test_matchers.py

# Expected output:
# ✅ 28-30/31 columns mapped (90-97%)
# ✅ 16-17/17 matchers used
# ⚠️ 2 validation warnings (Age, Salary)
```

---

## Success Criteria

✅ All 17 matchers contribute at least one match  
✅ Property hierarchy reasoning works  
✅ OWL characteristics validated against data  
✅ Restrictions trigger validation warnings  
✅ SKOS relations recognized  
✅ No confidence scores = 1.00  
✅ Evidence clearly attributes each matcher  
✅ Structural patterns detected

**This comprehensive test validates the full semantic matching architecture!**

