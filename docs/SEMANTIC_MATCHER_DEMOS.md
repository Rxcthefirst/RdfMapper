# Semantic Matcher Demos

This document provides instructions for running demo scripts that showcase the semantic matchers.

## Overview

The semantic matchers use ontology reasoning (property hierarchies, OWL characteristics) to intelligently match data columns to properties.

---

## 🧠 Property Hierarchy Matcher Demo

**File:** `scripts/demo_hierarchy_matcher.py`  
**Purpose:** Demonstrates property hierarchy reasoning (rdfs:subPropertyOf)

### Running the Demo

```bash
python scripts/demo_hierarchy_matcher.py
```

### Expected Output

```
================================================================================
Testing Property Hierarchy Matcher
================================================================================

1. Creating test ontology with property hierarchy...
  ✓ Created ontology with property hierarchy
  ✓ Saved to test_data/test_hierarchy.ttl

2. Loading ontology...
  ✓ Loaded 7 properties

3. Creating Property Hierarchy Matcher...
  ✓ Hierarchy matcher created
  ✓ Hierarchy cache built for 7 properties

4. Test 1: Exact match - 'full_name' column
  ✓ Match found: has full name
  ✓ Confidence: 0.978
  ✓ Hierarchy depth: 2
  ✓ Specificity: 0.70
  ✓ Parents: ['has name']

5. Test 2: General term - 'name' column
  ✓ Match found: has name
  ✓ Confidence: 0.959
  ✓ Children: 3 more specific options

6. Test 3: Analyzing full hierarchy
  Root Property: has identifier
    ├── has name (depth: 1)
    │   ├── has full name (depth: 2)
    │   ├── has first name (depth: 2)
    │   └── has last name (depth: 2)
    └── has ID (depth: 1)
        └── has customer ID (depth: 2)

7. Test 4: Specific ID - 'customer_id' column
  ✓ Match found: has customer ID
  ✓ Confidence: 0.978

✓ All tests passing!
```

### Key Features Demonstrated

- **Hierarchy-aware matching** with confidence boosting
- **Parent/child property suggestions** for alternative matches
- **Depth and specificity calculations** to understand property position
- **"has" prefix handling** (hasFullName ↔ full_name)
- **Multiple normalization strategies** (spaces, underscores, hyphens)

### Related Test

Run the pytest test suite:
```bash
python -m pytest tests/test_hierarchy_matcher.py -v
```

---

## 🦉 OWL Characteristics Matcher Demo

**File:** `scripts/demo_owl_matcher.py`  
**Purpose:** Demonstrates OWL property characteristics matching (Functional, InverseFunctional)

### Running the Demo

```bash
python scripts/demo_owl_matcher.py
```

### Expected Output

```
================================================================================
Testing OWL Characteristics Matcher
================================================================================

1. Creating test ontology with OWL characteristics...
  ✓ Created ontology with OWL characteristics

2. Loading ontology...
  ✓ Loaded 10 properties

3. Creating OWL Characteristics Matcher...
  ✓ OWL matcher created
  ✓ OWL cache built for 10 properties

OWL Characteristics detected:
  • has customer ID: InverseFunctional
  • has email: InverseFunctional
  • has SSN: InverseFunctional
  • has date of birth: Functional
  • has age: Functional

4. Test 1: InverseFunctional Property - 'customer_id'
  ✓ Match: hasCustomerID
  ✓ Confidence: 0.95
  ✓ Uniqueness: 100%
  ✓ Can be identifier: True
  ✓ Data matches IFP semantics perfectly!

5. Test 2: InverseFunctional Property - 'email'
  ✓ Match: hasEmail
  ✓ Confidence: 0.95
  ✓ Perfect match for InverseFunctionalProperty

6. Test 3: IFP Violation - 'email' with duplicates
  ✓ Match: hasEmail
  ✓ Confidence: 0.55
  ⚠ Warning: InverseFunctionalProperty violation detected
  ✓ Lower confidence due to data not matching OWL semantics

7. Test 4: Functional Property - 'date_of_birth'
  ✓ Match: hasDateOfBirth
  ✓ Confidence: 0.85
  ✓ Expects single value: True

8. Test 5: Regular Property - 'name'
  ✓ Match: hasName
  ✓ No special OWL characteristics

9. Test 6: Unique ID without IFP - 'ssn'
  ✓ Match: hasSSN
  ✓ Property correctly declared as InverseFunctionalProperty

✓ All tests passing!
```

### Key Features Demonstrated

- **InverseFunctional Property detection** for identifying unique identifiers
- **Functional Property validation** for single-valued properties
- **Data uniqueness validation** against OWL semantics
- **Confidence boosting/penalties** based on data-OWL alignment
- **Data quality issue detection** (IFP violations with duplicates)
- **Enrichment suggestions** for properties that should be IFP

### What Each Test Shows

1. **Test 1:** Perfect match - data is 100% unique, matches IFP perfectly
2. **Test 2:** Another perfect IFP match with email data
3. **Test 3:** IFP violation - duplicate emails reduce confidence significantly
4. **Test 4:** Functional property with high uniqueness
5. **Test 5:** Regular property without OWL characteristics
6. **Test 6:** Property correctly marked as IFP

### Related Test

Run the pytest test suite:
```bash
python -m pytest tests/test_owl_characteristics_matcher.py -v
```

---

## 🔍 Hierarchy Debug Script

**File:** `scripts/debug_hierarchy.py`  
**Purpose:** Debug script for understanding property hierarchies in ontologies

### Running the Debug Script

```bash
python scripts/debug_hierarchy.py
```

### Expected Output

```
================================================================================
Debugging Hierarchy Matcher
================================================================================

1. Loading ontology from test_data/test_hierarchy_ontology.ttl...
  ✓ Loaded 7 properties

2. Properties in ontology:
  • URI: http://example.org/hasIdentifier
    Label: has identifier
    All Labels: ['has identifier']

3. Checking graph for subPropertyOf relationships:
  http://example.org/hasName --subPropertyOf--> http://example.org/hasIdentifier
  http://example.org/hasFullName --subPropertyOf--> http://example.org/hasName
  [... more relationships ...]

4. Checking for property type declarations:
  http://example.org/hasIdentifier is a DatatypeProperty
    Label: has identifier

5. Testing label matching manually:
  Testing: 'full_name'
    ✓ MATCH: has full name (http://example.org/hasFullName)
  
  Testing: 'fullname'
    ✓ MATCH: has full name (http://example.org/hasFullName)
  
  Testing: 'has full name'
    ✓ MATCH: has full name (http://example.org/hasFullName)
```

### Use Cases

- Debugging why a property isn't matching
- Understanding the hierarchy structure
- Verifying label variations
- Testing normalization strategies

---

## 📚 Related Documentation

### Implementation Documentation
- [PROPERTY_HIERARCHY_MATCHER_COMPLETE.md](PROPERTY_HIERARCHY_MATCHER_COMPLETE.md) - Property hierarchy matcher details
- [OWL_CHARACTERISTICS_MATCHER_COMPLETE.md](OWL_CHARACTERISTICS_MATCHER_COMPLETE.md) - OWL characteristics matcher details
- [SEMANTIC_MATCHING_ARCHITECTURE.md](SEMANTIC_MATCHING_ARCHITECTURE.md) - Complete semantic matching architecture

### Testing
- `tests/test_hierarchy_matcher.py` - 12 pytest tests for hierarchy matcher
- `tests/test_owl_characteristics_matcher.py` - 18 pytest tests for OWL matcher

### Run All Tests

```bash
# Run all semantic matcher tests
python -m pytest tests/test_hierarchy_matcher.py tests/test_owl_characteristics_matcher.py -v

# With coverage
python -m pytest tests/test_hierarchy_matcher.py tests/test_owl_characteristics_matcher.py --cov=rdfmap.generator.matchers --cov-report=term
```

---

## 🎯 Key Takeaways

### Property Hierarchy Matcher
- Uses `rdfs:subPropertyOf` to understand property relationships
- Boosts confidence for properties in the right specificity level
- Suggests parent (more general) and child (more specific) alternatives
- Handles multiple naming conventions automatically

### OWL Characteristics Matcher
- Uses OWL property types (Functional, InverseFunctional, etc.)
- Validates data patterns against ontology definitions
- Identifies columns suitable for IRI generation (IFP properties)
- Detects data quality issues (duplicates in IFP)
- Suggests ontology improvements

### Combined Impact
Together, these matchers provide **true semantic reasoning** that goes beyond string matching to understand the formal semantics of properties and data.

