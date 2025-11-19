# Comprehensive Test Results - Initial Run

**Date:** November 16, 2025

## Results Summary

**Columns Mapped:** 12/20 (60%)  
**Matchers Used:** 3/11 expected

### Matchers That Worked ✅
1. **SemanticSimilarityMatcher** - 9 matches
2. **ExactRdfsLabelMatcher** - 2 matches  
3. **LexicalMatcher** - 1 match

### Missing Matchers ⚠️
- ExactPrefLabelMatcher
- ExactAltLabelMatcher
- ExactHiddenLabelMatcher
- ExactLocalNameMatcher
- PropertyHierarchyMatcher
- OWLCharacteristicsMatcher
- RelationshipMatcher
- ObjectPropertyMatcher
- PartialStringMatcher
- FuzzyStringMatcher

## Issues Identified

### 1. SKOS Vocabulary Not Loaded
**Problem:** The test doesn't load `hr_vocabulary.ttl`  
**Impact:** SKOS-based matchers (prefLabel, altLabel, hiddenLabel) cannot work  
**Fix:** Update generator to accept SKOS files

### 2. Embedding Matcher Too Aggressive
**Problem:** SemanticSimilarityMatcher is matching everything with high confidence  
**Example:** `Employee ID → employeeID (0.95)` via embeddings, when it should use ExactPrefLabelMatcher (0.98)  
**Impact:** Higher-tier exact matchers are being bypassed  
**Fix:** Matcher pipeline should try exact matchers first (currently correct order, but embeddings scoring too high)

### 3. Some Columns Not Mapped
**Missing:**
- emp_num (should match via hiddenLabel)
- hire_dt (should match via hiddenLabel)  
- EmpID (duplicate of Employee ID?)
- Compensation (duplicate?)
- Office Location
- mgr
- phone
- ContactEmail
- SSN
- DepartmentID
- ManagerID
- Team
- pos
- adrs

## Next Steps

1. **Load SKOS in generator** - Add support for SKOS vocabulary files
2. **Review embedding confidence** - May be scoring too high, overshadowing exact matches
3. **Test with SKOS enabled** - Re-run with vocabulary loaded
4. **Verify duplicate columns** - Some columns may be identical, causing confusion

## Expected After Fixes

With SKOS loaded:
- ExactPrefLabelMatcher: "Employee ID" → employeeID (via skos:prefLabel)
- ExactHiddenLabelMatcher: "emp_num" → employeeNumber, "hire_dt" → hireDate
- ExactAltLabelMatcher: "Birth Date" → dateOfBirth (via skos:altLabel)

**Target:** 18-19/20 columns mapped using 10-11 different matchers

