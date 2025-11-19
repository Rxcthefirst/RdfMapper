# Comprehensive Matcher Test Coverage Analysis

**Date:** November 16, 2025

## Matcher Inventory & Test Requirements

### Current Matchers in Pipeline

| # | Matcher | Threshold | Purpose | Test Required? |
|---|---------|-----------|---------|----------------|
| 1 | ExactPrefLabelMatcher | 0.98 | Match skos:prefLabel | ✅ YES |
| 2 | ExactRdfsLabelMatcher | 0.95 | Match rdfs:label | ✅ YES |
| 3 | ExactAltLabelMatcher | 0.90 | Match skos:altLabel | ✅ YES |
| 4 | ExactHiddenLabelMatcher | 0.85 | Match skos:hiddenLabel | ✅ YES |
| 5 | ExactLocalNameMatcher | 0.80 | Match property local name | ✅ YES |
| 6 | PropertyHierarchyMatcher | 0.65 | rdfs:subPropertyOf reasoning | ⚠️ **MISSING** |
| 7 | OWLCharacteristicsMatcher | 0.60 | Functional/IFP detection | ⚠️ **MISSING** |
| 8 | RestrictionBasedMatcher | 0.55 | OWL restrictions validation | ⚠️ **MISSING** |
| 9 | SKOSRelationsMatcher | 0.50 | skos:broader/narrower | ⚠️ **MISSING** |
| 10 | SemanticSimilarityMatcher | 0.45 | Embeddings (phrase+token) | ✅ YES |
| 11 | LexicalMatcher | 0.60 | String algorithms | ✅ YES |
| 12 | DataTypeInferenceMatcher | 0.0 | Type compatibility (booster) | ✅ YES |
| 13 | HistoryAwareMatcher | 0.60 | Previous mappings | ❓ Optional |
| 14 | StructuralMatcher | 0.70 | Co-occurrence patterns | ⚠️ **MISSING** |
| 15 | GraphReasoningMatcher | 0.60 | FK detection | ✅ YES (as RelationshipMatcher) |
| 16 | PartialStringMatcher | 0.60 | Partial/abbreviation | ✅ YES |
| 17 | FuzzyStringMatcher | 0.40 | Typo/fuzzy match | ✅ YES |

### Test Coverage Status

**Currently Tested:** 9/17 matchers (53%)
**Missing Tests:** 8/17 matchers (47%)

---

## Gap Analysis: HR Ontology vs. Requirements

### ✅ What We Have

#### 1. Basic SKOS Labels (Exact Matchers)
**In ontology:**
```turtle
ex:employeeID
    skos:prefLabel "Employee ID"@en ;
    skos:altLabel "Emp ID"@en ;
    skos:hiddenLabel "emp_num"@en .
```
**Test columns:** Employee ID, Birth Date, emp_num, hire_dt
**Status:** ✅ Ready

#### 2. Basic OWL Characteristics
**In ontology:**
```turtle
ex:socialSecurityNumber a owl:InverseFunctionalProperty .
ex:employeeNumber a owl:InverseFunctionalProperty .
```
**Test columns:** SSN (IFP)
**Status:** ⚠️ Partial - Need data uniqueness validation

#### 3. Semantic Similarity
**Test columns:** EmpID, Compensation, Office Location
**Status:** ✅ Working

#### 4. Lexical Matching
**Test columns:** annual_comp, mgr, phone
**Status:** ✅ Working

#### 5. Relationship Detection
**Test columns:** DepartmentID, ManagerID
**Status:** ✅ Working (as RelationshipMatcher)

---

### ❌ What We're Missing

#### 1. Property Hierarchy (rdfs:subPropertyOf)
**REQUIRED FROM ARCHITECTURE DOC:**
```turtle
# Example from doc
:hasIdentifier a owl:DatatypeProperty .
:hasName rdfs:subPropertyOf :hasIdentifier .
:hasFullName rdfs:subPropertyOf :hasName .
:hasFirstName rdfs:subPropertyOf :hasName .
:hasLastName rdfs:subPropertyOf :hasName .
```

**WHAT WE HAVE:**
```turtle
# NONE - No property hierarchies in HR ontology!
```

**IMPACT:** PropertyHierarchyMatcher has nothing to test
**CRITICALITY:** 🔴 HIGH - This is Layer 2.1 in architecture doc

**WHAT WE NEED TO ADD:**
```turtle
# Contact information hierarchy
ex:contactInformation a owl:DatatypeProperty ;
    rdfs:label "contact information"@en .

ex:email rdfs:subPropertyOf ex:contactInformation ;
    rdfs:label "email"@en .

ex:phoneNumber rdfs:subPropertyOf ex:contactInformation ;
    rdfs:label "phone number"@en .

# Name hierarchy
ex:hasIdentifier a owl:DatatypeProperty ;
    rdfs:label "identifier"@en .

ex:hasName rdfs:subPropertyOf ex:hasIdentifier ;
    rdfs:label "name"@en .

ex:fullName rdfs:subPropertyOf ex:hasName ;
    rdfs:label "full name"@en .

# Compensation hierarchy
ex:hasAmount a owl:DatatypeProperty ;
    rdfs:label "amount"@en .

ex:hasSalary rdfs:subPropertyOf ex:hasAmount ;
    rdfs:label "salary"@en .

ex:annualSalary rdfs:subPropertyOf ex:hasSalary ;
    rdfs:label "annual salary"@en .
```

**TEST SCENARIO:**
- Column: "full_name" should match via hierarchy
- Column: "ContactEmail" should get hierarchy boost
- Evidence should show: "matched via property hierarchy (child of contactInformation)"

---

#### 2. Class Hierarchy (rdfs:subClassOf)
**REQUIRED FROM ARCHITECTURE DOC:**
```turtle
:Person a owl:Class .
:Customer rdfs:subClassOf :Person .
:Employee rdfs:subClassOf :Person .
```

**WHAT WE HAVE:**
```turtle
ex:Manager rdfs:subClassOf ex:Employee .  # ✅ We have this!
```

**STATUS:** ⚠️ Partial - Need to validate property inheritance works

**WHAT WE NEED TO VERIFY:**
- Properties with domain Person should be available for Employee
- Properties with domain Employee should be available for Manager
- Inheritance chain works properly

---

#### 3. More OWL Characteristics
**REQUIRED FROM ARCHITECTURE DOC:**
```turtle
:hasDateOfBirth a owl:FunctionalProperty .  # At most one value
:hasSSN a owl:InverseFunctionalProperty .   # Uniquely identifies
```

**WHAT WE HAVE:**
```turtle
ex:employeeID a owl:FunctionalProperty .           # ✅ Have
ex:employeeNumber a owl:InverseFunctionalProperty . # ✅ Have
ex:socialSecurityNumber a owl:InverseFunctionalProperty . # ✅ Have
ex:email a owl:FunctionalProperty .                # ✅ Have
ex:annualSalary a owl:FunctionalProperty .         # ✅ Have
```

**STATUS:** ✅ Good, but needs testing
**WHAT'S MISSING:** Data validation against OWL characteristics

**TEST SCENARIOS NEEDED:**
1. **IFP with unique data:** SSN column with 100% unique → confidence boost
2. **IFP with duplicate data:** Email column with duplicates → validation warning
3. **Functional with single value:** Birth Date (one per person) → validation pass
4. **Functional with multiple values:** If data has multiple birth dates → validation error

---

#### 4. OWL Restrictions
**REQUIRED FROM ARCHITECTURE DOC:**
```turtle
:Person a owl:Class ;
    rdfs:subClassOf [
        a owl:Restriction ;
        owl:onProperty :hasAge ;
        owl:minInclusive 0 ;
        owl:maxInclusive 150
    ] .
```

**WHAT WE HAVE:**
```turtle
# NONE - No OWL restrictions in HR ontology!
```

**IMPACT:** RestrictionBasedMatcher has nothing to test
**CRITICALITY:** 🟡 MEDIUM - Useful for validation but not core matching

**WHAT WE NEED TO ADD:**
```turtle
ex:Employee rdfs:subClassOf [
    a owl:Restriction ;
    owl:onProperty ex:age ;
    owl:someValuesFrom xsd:integer ;
    owl:minInclusive 18 ;     # Must be 18+ to work
    owl:maxInclusive 100
] ;
    rdfs:subClassOf [
        a owl:Restriction ;
        owl:onProperty ex:annualSalary ;
        owl:someValuesFrom xsd:integer ;
        owl:minInclusive 0     # Salary can't be negative
    ] ;
    rdfs:subClassOf [
        a owl:Restriction ;
        owl:onProperty ex:email ;
        owl:cardinality 1      # Exactly one email required
    ] .
```

**TEST SCENARIOS:**
- Age column with value 200 → validation error (exceeds maxInclusive)
- Salary column with negative value → validation error
- Missing email → cardinality violation warning

---

#### 5. SKOS Semantic Relations
**REQUIRED FROM ARCHITECTURE DOC:**
```turtle
:MotorVehicle skos:broader :Vehicle .
:Car skos:broader :MotorVehicle .
:SportsCar skos:broader :Car .
:Automobile skos:exactMatch :Car .
```

**WHAT WE HAVE:**
```turtle
# In hr_vocabulary.ttl:
ex:email skos:broader ex:contactInformation .  # ✅ We have ONE!
```

**STATUS:** ⚠️ Minimal - Need more examples
**CRITICALITY:** 🟡 MEDIUM - Useful but not critical

**WHAT WE NEED TO ADD:**
```turtle
# Position hierarchy
ex:Employee a skos:Concept ;
    skos:prefLabel "Employee"@en .

ex:SeniorEmployee skos:broader ex:Employee ;
    skos:prefLabel "Senior Employee"@en .

ex:JuniorEmployee skos:broader ex:Employee ;
    skos:prefLabel "Junior Employee"@en .

ex:Manager skos:broader ex:SeniorEmployee ;
    skos:prefLabel "Manager"@en .

# Exact matches across vocabularies
ex:positionTitle skos:exactMatch ex:jobTitle ;
    skos:prefLabel "Position Title"@en .

ex:jobTitle skos:prefLabel "Job Title"@en .

# Related concepts
ex:department skos:related ex:team ;
    skos:prefLabel "Department"@en .

ex:team skos:prefLabel "Team"@en .
```

**TEST SCENARIOS:**
- Column "Senior Engineer" value → maps to SeniorEmployee concept
- Column "job_title" → matches via exactMatch to positionTitle
- Column "team" when "department" matched → boost via skos:related

---

#### 6. Structural/Graph Context Matcher
**REQUIRED FROM ARCHITECTURE DOC:**
```python
# Scenario: first_name and last_name matched
# Then "middle_initial" should get context boost
```

**STATUS:** ❓ Unclear if implemented
**CRITICALITY:** 🟡 MEDIUM - Nice to have

**WHAT WE NEED:**
- Co-occurrence pattern detection
- Property grouping by domain
- Boost confidence when siblings match

**TEST SCENARIO:**
- Match "first_name" and "last_name" first
- Then match "middle" column
- Should get boost because other name fields matched

---

## Revised HR Ontology Requirements

### Must Add (High Priority):

1. **Property Hierarchies**
   ```turtle
   ex:hasIdentifier (top)
     ├── ex:hasName
     │   └── ex:fullName
     └── ex:hasNumber
         ├── ex:employeeNumber
         └── ex:phoneNumber
   
   ex:contactInformation (top)
     ├── ex:email
     └── ex:phoneNumber
   
   ex:hasAmount (top)
     └── ex:hasSalary
         └── ex:annualSalary
   ```

2. **OWL Restrictions**
   - Age: 18-100
   - Salary: > 0
   - Email: cardinality 1
   - SSN: exactly 1

3. **More Test Columns**
   - "identifier" → should match hasIdentifier (parent)
   - "name" → should match hasName (middle)
   - "amount" → should match hasAmount (parent)
   - "contact" → should match contactInformation (parent)

### Should Add (Medium Priority):

4. **SKOS Relations**
   - Position concept hierarchy
   - exactMatch/closeMatch examples
   - skos:related between team/department

5. **Age Column** (for restriction testing)
   - Add to CSV with some invalid values (e.g., 200, -5)
   - Add age property with restrictions

6. **Duplicate Data** (for IFP testing)
   - Add duplicate email to test IFP validation
   - Add duplicate SSN to show violation warnings

---

## Recommended Actions

### 1. Enhance HR Ontology (CRITICAL)
Create `hr_ontology_v2.ttl` with:
- ✅ Property hierarchies (3 levels deep)
- ✅ OWL restrictions on age, salary, email
- ✅ More class hierarchy depth
- ✅ Additional properties to test inheritance

### 2. Enhance HR Vocabulary (CRITICAL)
Update `hr_vocabulary.ttl` with:
- ✅ SKOS broader/narrower for positions
- ✅ SKOS exactMatch examples
- ✅ SKOS related concepts

### 3. Enhance CSV Data (IMPORTANT)
Update `employees.csv` with:
- ✅ Age column (with invalid values for testing)
- ✅ Duplicate email (to test IFP validation)
- ✅ More columns to test hierarchy matching
- ✅ "identifier", "name", "amount" generic columns

### 4. Create Validation Test Script (IMPORTANT)
Script that checks:
- ✅ Each matcher is used at least once
- ✅ Evidence shows correct matcher attribution
- ✅ Confidence scores are in expected range
- ✅ Validation warnings appear where expected

---

## Expected Test Results After Fixes

| Matcher | Count | Example Columns |
|---------|-------|----------------|
| ExactPrefLabelMatcher | 1-2 | Employee ID |
| ExactRdfsLabelMatcher | 2-3 | Full Name, startDate |
| ExactAltLabelMatcher | 1-2 | Birth Date |
| ExactHiddenLabelMatcher | 2-3 | emp_num, hire_dt |
| ExactLocalNameMatcher | 1-2 | startDate |
| **PropertyHierarchyMatcher** | 3-4 | **identifier, name, contact** |
| **OWLCharacteristicsMatcher** | 2-3 | **SSN (IFP), email (Func)** |
| **RestrictionBasedMatcher** | 2-3 | **age, salary (with validation)** |
| **SKOSRelationsMatcher** | 1-2 | **position via broader** |
| SemanticSimilarityMatcher | 3-5 | EmpID, Compensation, Office Location |
| LexicalMatcher | 2-3 | annual_comp, mgr, phone |
| DataTypeInferenceMatcher | 20 | All (as booster) |
| StructuralMatcher | 1-2 | middle (after first/last matched) |
| RelationshipMatcher | 2 | DepartmentID, ManagerID |
| PartialStringMatcher | 1-2 | pos |
| FuzzyStringMatcher | 1-2 | adrs |

**Target:** 15-17/17 matchers used (88-100%)

---

## Next Steps

1. **Create Enhanced Ontology** - Add property hierarchies, restrictions
2. **Update SKOS Vocabulary** - Add broader/narrower relations
3. **Enhance CSV Data** - Add test columns and invalid values
4. **Run Comprehensive Test** - Validate all matchers
5. **Document Results** - Create test report showing each matcher's contribution

**Shall I proceed with creating the enhanced ontology files?**

