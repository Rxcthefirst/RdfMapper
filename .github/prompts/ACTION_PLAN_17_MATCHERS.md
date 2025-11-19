# Action Plan: Getting to 17/17 Matchers

## Current Situation

**Status:** 6/17 matchers actively winning matches  
**Root Cause:** Test data has perfect SKOS labels for everything  
**Reality:** All 17 matchers ARE in pipeline, but 11 are losing to exact matches

## The Problem

We're testing a **FERRARI with a SPEEDOMETER** - the car works great, but we're only driving in a school zone so we never see what it can really do.

Our exact matchers are TOO GOOD. We need messier, real-world data.

## Action Plan

### Step 1: Add Fuzzy/Partial Test Columns

**Add to employees.csv:**
```csv
# Current columns + these new ones:
ph,wrk_loc,emp_nm,pos_ttl,dept_nm,mgr_nm,loc,sal,comp,dob,hired,strt,tmname

# With messy data:
ph,wrk_loc,emp_nm,pos_ttl
5550101,Bldg A,Jhn Smth,Sr Eng
5550102,Bldg B,Jan Do,Engr
```

**Expected Results:**
- `ph` → phoneNumber via **PartialStringMatcher** (0.60)
- `wrk_loc` → workLocation via **FuzzyStringMatcher** (0.50)
- `emp_nm` → fullName via **PartialStringMatcher** (0.65)
- `pos_ttl` → positionTitle via **PartialStringMatcher** (0.62)

### Step 2: Remove Some SKOS Labels

**Edit hr_vocabulary.ttl - REMOVE these labels:**
```turtle
# Comment out these to force other matchers:
# ex:workLocation skos:hiddenLabel "work_location", "office_location", "location" .
# ex:teamName skos:hiddenLabel "team", "team_name" .
# ex:address skos:hiddenLabel "address", "addr", "adrs" .
```

**Expected Results:**
- `location` → workLocation via **LexicalMatcher** (0.70)
- `team` → teamName via **LexicalMatcher** (0.75)
- `addr` → address via **FuzzyStringMatcher** (0.55)

### Step 3: Add Hierarchy Test Columns

**Add columns that should match via hierarchy:**
```csv
super_id,generic_name,any_contact,some_amount,base_salary

E1001,John Smith,john@ex.com,95000,95000
```

**Expected Results:**
- `super_id` → hasIdentifier via **PropertyHierarchyMatcher** (0.68)
- `generic_name` → hasName via **PropertyHierarchyMatcher** (0.70)
- `any_contact` → contactInformation via **PropertyHierarchyMatcher** (0.65)
- `some_amount` → hasAmount via **PropertyHierarchyMatcher** (0.67)

### Step 4: Add OWL Characteristics Test

**Add columns with unique patterns:**
```csv
unique_ref,single_val,func_prop

REF-1001,SINGLE-1,VAL-1001
REF-1002,SINGLE-1,VAL-1002  # Same single_val = violates Functional
```

**Expected Results:**
- `unique_ref` → employeeNumber via **OWLCharacteristicsMatcher** (0.75, IFP + 100% unique)
- `func_prop` → employeeID via **OWLCharacteristicsMatcher** (0.72, Functional)

### Step 5: Add Restriction Violation Test

**Add invalid data:**
```csv
bad_age,bad_salary,missing_email

999,-50000,
15,-1000,
200,999999999,
```

**Expected Results:**
- Mapping succeeds but validation warnings issued
- **RestrictionBasedMatcher** fires and reports violations

### Step 6: Add Structural Co-occurrence Test

**Add related fields:**
```csv
first,last,middle_init

John,Smith,A
Jane,Doe,B
```

**Expected Results:**
- After matching `first` and `last`
- `middle_init` → middleName via **StructuralMatcher** (0.75, boosted by siblings)

### Step 7: Add Graph Reasoning Test

**Add FK columns without "ID" suffix:**
```csv
dept_ref,manager_ref,works_in,reports_to

D001,M501,Engineering,Alice Manager
```

**Expected Results:**
- `dept_ref` → worksInDepartment via **GraphReasoningMatcher** (0.65)
- `manager_ref` → reportsTo via **GraphReasoningMatcher** (0.67)

### Step 8: Add DataType Booster Test

**Add ambiguous columns:**
```csv
value1,value2,number1,text1

95000,87000,1001,ABC
```

**Expected Results:**
- **DataTypeInferenceMatcher** acts as booster (+0.05) for all numeric → integer mappings
- Shows in evidence but not as primary matcher

### Step 9: Add ExactLocalNameMatcher Test

**Add camelCase columns matching property URIs:**
```csv
employeeID,firstName,lastName,startDate

E1001,John,Smith,2020-01-15
```

**Expected Results:**
- These match via **ExactLocalNameMatcher** (0.80) when SKOS labels removed

## Expected Final Results

After implementing all steps:

```
ExactPrefLabelMatcher: 3-5 matches
ExactRdfsLabelMatcher: 2-3 matches
ExactAltLabelMatcher: 2-3 matches
ExactHiddenLabelMatcher: 1-2 matches
ExactLocalNameMatcher: 2-3 matches ✨ NEW
PropertyHierarchyMatcher: 4-5 matches ✨ NEW
OWLCharacteristicsMatcher: 2-3 matches ✨ NEW
RestrictionBasedMatcher: 0 matches, 3+ violations ✨ NEW
SKOSRelationsMatcher: 1-2 matches ✨ NEW
SemanticSimilarityMatcher: 2-3 matches
LexicalMatcher: 3-5 matches ✨ NEW
DataTypeInferenceMatcher: 30+ boosts ✨ NEW
HistoryAwareMatcher: 0 (needs previous runs) ⏭️
StructuralMatcher: 1-2 matches ✨ NEW
GraphReasoningMatcher: 2-3 matches ✨ NEW
PartialStringMatcher: 3-5 matches ✨ NEW
FuzzyStringMatcher: 2-4 matches ✨ NEW
```

**Target: 15-16/17 matchers active** (HistoryAwareMatcher needs previous mapping runs)

## Implementation Time Estimate

- Step 1-2: 15 minutes (add messy columns, remove some SKOS)
- Step 3-4: 10 minutes (hierarchy + OWL tests)
- Step 5-7: 15 minutes (restrictions, structural, graph)
- Step 8-9: 10 minutes (datatype, local name)
- Testing & validation: 20 minutes

**Total: ~70 minutes to get 15-16/17 matchers**

## Success Criteria

✅ 15+ matchers actively winning matches  
✅ Evidence shows each matcher's unique contribution  
✅ Validation warnings for restriction violations  
✅ Confidence scores distributed across ranges (0.40-0.98)  
✅ Test demonstrates BOTH exact matching AND fuzzy fallbacks

## Bottom Line

The system works. We just need to test it properly with realistic, messy data instead of pristine SKOS-labeled perfection.

**We built a Ferrari. Time to take it out of the school zone.**

