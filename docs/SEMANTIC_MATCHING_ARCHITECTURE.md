# Semantic Matching: Complete Architecture & Examples

**Purpose:** Document how true semantic matching works by combining embeddings with ontology reasoning

**Date:** November 15, 2025

---

## What "Semantic" Really Means

**Semantic matching** means understanding **meaning**, not just string similarity. It requires:

1. **Linguistic Semantics** - Understanding language/text (embeddings)
2. **Ontological Semantics** - Understanding formal relationships (graph reasoning)
3. **Data Semantics** - Understanding data patterns and types
4. **Context Semantics** - Understanding domain and usage patterns

True semantic matching **combines all four**.

---

## Complete Semantic Matching Architecture

### Layer 1: Linguistic Semantics (Embeddings)

**What It Does:** Understands natural language similarity

**Technology:** BERT/Sentence Transformers embeddings

**Example:**
```python
Column: "customer_birth_date"
Property: :dateOfBirth (label: "date of birth")

# Embedding captures semantic similarity even with different words
# "birth_date" ≈ "date of birth" (high cosine similarity)
```

**Problems It Solves:**
- ✅ Different phrasings of same concept
- ✅ Synonyms and paraphrases
- ✅ Word order variations
- ✅ Common abbreviations

**What It Misses:**
- ❌ Formal semantic relationships (hierarchy, equivalence)
- ❌ Domain-specific term meanings
- ❌ Structural context

---

### Layer 2: Ontological Semantics (Graph Reasoning)

**What It Does:** Understands formal semantic relationships defined in ontology

#### 2.1 Property Hierarchies (rdfs:subPropertyOf)

**Ontology Definition:**
```turtle
# Hierarchy
:hasIdentifier a owl:DatatypeProperty .
:hasName rdfs:subPropertyOf :hasIdentifier .
:hasFullName rdfs:subPropertyOf :hasName .
:hasFirstName rdfs:subPropertyOf :hasName .
:hasLastName rdfs:subPropertyOf :hasName .
```

**Semantic Meaning:**
- If something `hasFullName`, it also `hasName` and `hasIdentifier`
- A `hasName` is a specific kind of `hasIdentifier`
- Properties inherit characteristics from parents

**Matching Example:**
```python
Data Column: "full_name"

# Current behavior (NO HIERARCHY):
Match: :hasFullName (exact label match)
Confidence: 0.95
Alternatives: [:hasName (0.82), :hasIdentifier (0.70)]

# WITH HIERARCHY REASONING:
Match: :hasFullName (exact + hierarchy aware)
Confidence: 0.98  # Boosted because we know the hierarchy
Semantic Understanding: "This is also a :hasName and :hasIdentifier"
Inheritance: Properties from parent classes apply
Alternatives: 
  - :hasName (0.85, parent - more general)
  - :hasFirstName (0.75, sibling - same level)
  - :hasIdentifier (0.70, grandparent - very general)
```

**Problems It Solves:**
- ✅ Understanding specificity levels (specific vs general)
- ✅ Suggesting appropriate generalization/specialization
- ✅ Recognizing property families
- ✅ Inheritance of constraints and characteristics
- ✅ Better confidence scoring based on semantic distance

**Real-World Example:**
```turtle
# E-commerce ontology
:hasPrice rdfs:subPropertyOf :hasAmount .
:hasDiscountPrice rdfs:subPropertyOf :hasPrice .
:hasOriginalPrice rdfs:subPropertyOf :hasPrice .
```

```python
Data: "discount_price" column

WITHOUT hierarchy:
- Might match :hasDiscountPrice (0.85)
- Might suggest :hasPrice as alternative (0.78)
- No understanding they're related

WITH hierarchy:
- Matches :hasDiscountPrice (0.92) # Boosted
- Knows it's also a :hasPrice and :hasAmount
- Can validate: numeric data? ✓ (aligns with :hasAmount)
- Can suggest rollup: report as :hasPrice in summary views
```

---

#### 2.2 Class Hierarchies (rdfs:subClassOf)

**Ontology Definition:**
```turtle
:LegalEntity a owl:Class .
:Organization rdfs:subClassOf :LegalEntity .
:Person rdfs:subClassOf :LegalEntity .
:Customer rdfs:subClassOf :Person .
:Employee rdfs:subClassOf :Person .

# Properties defined at different levels
:hasName rdfs:domain :LegalEntity .  # All legal entities have names
:hasTaxID rdfs:domain :LegalEntity .
:hasDateOfBirth rdfs:domain :Person .  # Only persons
:hasCustomerID rdfs:domain :Customer .  # Only customers
```

**Semantic Meaning:**
- Customers ARE Persons ARE LegalEntities (inheritance)
- Properties defined on parent classes apply to children
- More specific classes have more properties

**Matching Example:**
```python
Target Class: :Customer
Data Columns: ["customer_id", "name", "birth_date", "tax_id"]

# WITHOUT CLASS HIERARCHY:
Properties checked: Only those with domain=:Customer
- customer_id → :hasCustomerID ✓
- name → ? (domain is :LegalEntity, might miss)
- birth_date → ? (domain is :Person, might miss)
- tax_id → ? (domain is :LegalEntity, might miss)

# WITH CLASS HIERARCHY:
Properties available: :Customer + :Person + :LegalEntity
- customer_id → :hasCustomerID ✓ (direct)
- name → :hasName ✓ (inherited from :LegalEntity)
- birth_date → :hasDateOfBirth ✓ (inherited from :Person)
- tax_id → :hasTaxID ✓ (inherited from :LegalEntity)
```

**Problems It Solves:**
- ✅ Property inheritance from parent classes
- ✅ Understanding class specialization
- ✅ Filtering properties appropriate for class level
- ✅ Recognizing "is-a" relationships
- ✅ Multi-level domain reasoning

**Real-World Example:**
```turtle
# Library ontology
:Item a owl:Class .
:PhysicalItem rdfs:subClassOf :Item .
:DigitalItem rdfs:subClassOf :Item .
:Book rdfs:subClassOf :PhysicalItem .
:EBook rdfs:subClassOf :DigitalItem .

:hasTitle rdfs:domain :Item .
:hasISBN rdfs:domain :Book, :EBook .
:hasShelfLocation rdfs:domain :PhysicalItem .
:hasFileSize rdfs:domain :DigitalItem .
```

```python
Data: Book catalog with columns [isbn, title, shelf_location]

WITHOUT hierarchy:
- Only checks properties with domain=:Book
- Might miss :hasTitle (domain is :Item, parent)

WITH hierarchy:
- Knows :Book inherits from :PhysicalItem and :Item
- Matches :hasISBN (direct), :hasTitle (inherited), :hasShelfLocation (from PhysicalItem)
- Can validate: no file_size column (correct, PhysicalItem not DigitalItem)
```

---

#### 2.3 OWL Property Characteristics

**Ontology Definition:**
```turtle
# Functional: Each subject has at most one value
:hasDateOfBirth a owl:FunctionalProperty .
:hasSSN a owl:FunctionalProperty .

# InverseFunctional: Each value identifies at most one subject
:hasSSN a owl:InverseFunctionalProperty .
:hasEmail a owl:InverseFunctionalProperty .

# Transitive: If A→B and B→C then A→C
:isAncestorOf a owl:TransitiveProperty .

# Symmetric: If A→B then B→A
:isSiblingOf a owl:SymmetricProperty .

# Equivalent: Same meaning, different URI
:hasEmail owl:equivalentProperty :emailAddress .
```

**Semantic Meaning:**
- **Functional:** Can only have one value (like primary keys)
- **InverseFunctional:** Uniquely identifies entities (like SSN, email)
- **Transitive:** Relationship chains
- **Symmetric:** Bidirectional relationships
- **Equivalent:** Aliases

**Matching Example:**

##### Functional Properties
```python
Column: "social_security_number"
Data Analysis: 
  - 100% unique values
  - No duplicates
  - No nulls

WITHOUT OWL Characteristics:
Match: :hasSSN (fuzzy label match)
Confidence: 0.85
No understanding of uniqueness

WITH OWL Characteristics:
Match: :hasSSN (Functional + InverseFunctional)
Confidence: 0.95  # Boosted!
Reasoning:
  - Column has unique values ✓
  - Property is InverseFunctionalProperty ✓
  - Data pattern matches semantic definition ✓
  - Can be used as identifier ✓
Recommendation: Use this for IRI generation
```

##### InverseFunctional Properties
```python
Column: "email"
Data: ["john@ex.com", "jane@ex.com", "john@ex.com"]  # John appears twice

WITHOUT OWL Characteristics:
Match: :hasEmail (exact match)
Confidence: 0.95
No validation

WITH OWL Characteristics:
Match: :hasEmail (InverseFunctionalProperty)
Confidence: 0.95
Validation: ⚠️ WARNING - IFP has duplicate values
  - "john@ex.com" appears 2 times
  - This violates InverseFunctional constraint
  - Suggests: Data quality issue OR multiple records for same person
Recommendation: Review data or use composite key
```

**Problems It Solves:**
- ✅ Identifying potential identifiers (IFP)
- ✅ Understanding cardinality expectations (Functional = single value)
- ✅ Data quality validation
- ✅ IRI template suggestions
- ✅ Relationship type understanding

---

#### 2.4 Property Restrictions (OWL Restrictions)

**Ontology Definition:**
```turtle
:Person a owl:Class ;
    rdfs:subClassOf [
        a owl:Restriction ;
        owl:onProperty :hasAge ;
        owl:someValuesFrom xsd:integer ;
        owl:minInclusive 0 ;
        owl:maxInclusive 150
    ] ;
    rdfs:subClassOf [
        a owl:Restriction ;
        owl:onProperty :hasGender ;
        owl:allValuesFrom :Gender  # Must be from Gender class
    ] ;
    rdfs:subClassOf [
        a owl:Restriction ;
        owl:onProperty :hasParent ;
        owl:maxCardinality 2  # At most 2 parents
    ] .
```

**Semantic Meaning:**
- Defines expected data types for properties
- Specifies cardinality constraints
- Defines value ranges and constraints

**Matching Example:**
```python
Column: "age"
Data: [25, 30, 45, -5, 200, "unknown"]

WITHOUT Restrictions:
Match: :hasAge (label match)
Confidence: 0.90
No validation

WITH Restrictions:
Match: :hasAge 
Confidence: 0.90
Validation:
  ✓ Type: mostly integers (matches xsd:integer)
  ✗ Range violation: -5 < 0 (minInclusive)
  ✗ Range violation: 200 > 150 (maxInclusive)
  ✗ Type violation: "unknown" not integer
  
Report: 3 values violate restrictions (3 out of 6 = 50% invalid)
Recommendation: Clean data or use :hasAgeText for mixed types
```

**Problems It Solves:**
- ✅ Data type validation against ontology
- ✅ Value range checking
- ✅ Cardinality expectations
- ✅ Early detection of data quality issues
- ✅ Transformation suggestions

---

#### 2.5 SKOS Semantic Relations

**Ontology Definition:**
```turtle
:Vehicle a skos:Concept .
:MotorVehicle skos:broader :Vehicle ;
    skos:prefLabel "Motor Vehicle" ;
    skos:altLabel "Motorized Vehicle", "Automobile" .
    
:Car skos:broader :MotorVehicle ;
    skos:prefLabel "Car" ;
    skos:altLabel "Automobile", "Auto" ;
    skos:related :Truck, :Motorcycle .
    
:SportsCar skos:broader :Car ;
    skos:prefLabel "Sports Car" .

:Automobile skos:exactMatch :Car .  # Same concept
:PersonalVehicle skos:closeMatch :Car .  # Similar but not exact
```

**Semantic Meaning:**
- **broader/narrower:** Concept hierarchies (like subClassOf for concepts)
- **related:** Concepts in same domain but different
- **exactMatch:** Same meaning across vocabularies
- **closeMatch:** Similar meaning
- **altLabel:** Alternative terms for same concept

**Matching Example:**
```python
Column: "automobile_type"
Values: ["sedan", "suv", "sports car", "truck"]

WITHOUT SKOS Relations:
Match: :hasVehicleType (fuzzy)
Confidence: 0.75
No concept hierarchy understanding

WITH SKOS Relations:
Match: :hasCarType (more specific)
Confidence: 0.88
Reasoning:
  - Values suggest Car-level concepts
  - "sports car" matches :SportsCar (narrower than :Car)
  - :Car is narrower than :MotorVehicle
  - Can map to hierarchy:
    * sedan → :Sedan (skos:broader :Car)
    * sports car → :SportsCar (skos:broader :Car)
    * suv → :SUV (skos:broader :Car)
  
Alternatives:
  - :hasVehicleType (broader, more general) - 0.85
  - :hasMotorVehicleType (middle level) - 0.82
  
Validation: ⚠️ "truck" found
  - :Truck is sibling of :Car, not child
  - Suggests: Use :hasVehicleType (more general) OR
  - Filter data to cars only
```

**Problems It Solves:**
- ✅ Understanding concept specificity levels
- ✅ Cross-vocabulary mappings (exactMatch)
- ✅ Finding related concepts
- ✅ Navigating concept hierarchies
- ✅ Alternative term recognition

---

### Layer 3: Graph Context Semantics

**What It Does:** Understands how properties relate to each other structurally

**Ontology Patterns:**
```turtle
# Common pattern: Name properties occur together
:Person rdfs:subClassOf [
    owl:onProperty :hasFirstName ;
    owl:onProperty :hasLastName ;
    owl:onProperty :hasMiddleName
] .

# Common pattern: Address properties are grouped
:hasStreetAddress rdfs:domain :Address .
:hasCity rdfs:domain :Address .
:hasState rdfs:domain :Address .
:hasZipCode rdfs:domain :Address .
```

**Matching Example:**
```python
# Scenario: We've already matched some columns
Matched:
  - "first_name" → :hasFirstName (0.95)
  - "last_name" → :hasLastName (0.92)
  
Unmatched:
  - "middle_initial" (not exact match to anything)

WITHOUT Graph Context:
Match: :hasMiddleName (fuzzy)
Confidence: 0.68 (low due to "initial" vs "name")

WITH Graph Context:
Analysis: 
  - :hasFirstName and :hasLastName already matched
  - These are part of name property group
  - :hasMiddleName is in same group
  - Strong structural evidence
  
Match: :hasMiddleName
Confidence: 0.85 # BOOSTED by graph context
Reasoning: "Part of name property cluster, siblings already matched"
```

**Another Example - Address Fields:**
```python
Matched:
  - "street" → :hasStreetAddress (0.93)
  - "city" → :hasCity (0.96)
  
Unmatched:
  - "zip" (ambiguous - could be file format)

WITHOUT Graph Context:
Match: :hasZipCode (fuzzy)
Confidence: 0.72

WITH Graph Context:
Analysis:
  - :hasStreetAddress and :hasCity already matched
  - These are address-related properties
  - All have domain :Address
  - :hasZipCode also has domain :Address
  - Structural evidence: appears in address property cluster
  
Match: :hasZipCode
Confidence: 0.88 # BOOSTED by context
Reasoning: "Part of address property group, siblings already matched"
```

**Problems It Solves:**
- ✅ Disambiguating ambiguous terms
- ✅ Boosting confidence for related properties
- ✅ Understanding property groupings
- ✅ Recognizing domain patterns
- ✅ Context-aware matching

---

### Layer 4: Data Pattern Semantics

**What It Does:** Uses data characteristics to inform semantic matching

**Data Pattern Recognition:**
```python
Column: "identifier_value"

Data Analysis:
  - All values unique (100%)
  - Format: "CUST-" followed by 6 digits
  - No nulls
  - String type

Property Candidates:
1. :hasCustomerID (InverseFunctionalProperty, range=xsd:string)
2. :hasCustomerName (range=xsd:string)
3. :hasDescription (range=xsd:string)
```

**Semantic Reasoning:**
```python
WITHOUT Data Semantics:
All three are strings, fuzzy label match only
Best: :hasCustomerID (0.75)

WITH Data Semantics:
Match: :hasCustomerID
Confidence: 0.92 # BOOSTED
Reasoning:
  - Data is 100% unique ✓
  - Property is InverseFunctionalProperty ✓
  - Pattern suggests ID format ✓
  - No nulls (appropriate for ID) ✓
  - Data pattern aligns with property semantics ✓
  
Eliminated:
  - :hasCustomerName: Low confidence
    * Names not typically unique
    * Pattern doesn't match name format
  - :hasDescription: Very low confidence
    * Descriptions typically longer
    * Not typically unique
```

**Another Example - Date Recognition:**
```python
Column: "date_field"
Data: ["2024-01-15", "2024-02-20", "2023-12-01"]

Properties:
1. :hasCreatedDate (range=xsd:date)
2. :hasModifiedDate (range=xsd:date)
3. :hasBirthDate (range=xsd:date)

WITHOUT Data Semantics:
All are dates, label match only
No way to distinguish

WITH Data Semantics:
Additional Context from other columns:
  - "created_by" column exists → :hasCreatedDate (0.85)
  - "updated_by" column exists → :hasModifiedDate (0.88)
  - "first_name", "last_name" exist → :hasBirthDate (0.82)
  
Analysis: Presence of name columns suggests person entity
Match: :hasBirthDate (0.92) # BOOSTED by entity context
```

**Problems It Solves:**
- ✅ Type-based filtering
- ✅ Pattern-based matching
- ✅ Uniqueness-based ID detection
- ✅ Cross-column context
- ✅ Data quality alignment

---

## Complete Semantic Matching Pipeline

### Step 1: Exact Matching (Highest Confidence)
```
Column → Exact label match → Property
Confidence: 0.95-1.0
```

### Step 2: Linguistic Semantics (Embeddings)
```
Column text → BERT encoding → Semantic similarity → Property
Confidence: 0.6-0.95
Adjusted by: Match type (fuzzy vs semantic)
```

### Step 3: Ontology Semantics (Graph Reasoning)
```
Property + Ontology → Hierarchy position → Confidence boost
Property + OWL → Characteristics → Validation
Property + SKOS → Relations → Context
Confidence adjustment: ±0.1-0.3
```

### Step 4: Graph Context (Structural)
```
Matched properties → Graph patterns → Boost related properties
Unmatched columns → Cluster analysis → Suggest by proximity
Confidence adjustment: ±0.1-0.2
```

### Step 5: Data Semantics (Validation)
```
Column data → Pattern analysis → Match to property constraints
Data type + OWL range → Validation → Confidence adjustment
Confidence adjustment: ±0.05-0.15
```

---

## Comprehensive Example

**Ontology:**
```turtle
# Classes
:Person a owl:Class .
:Customer rdfs:subClassOf :Person .

# Property hierarchy
:hasIdentifier a owl:DatatypeProperty .
:hasName rdfs:subPropertyOf :hasIdentifier .
:hasFullName rdfs:subPropertyOf :hasName .
:hasFirstName rdfs:subPropertyOf :hasName .
:hasLastName rdfs:subPropertyOf :hasName .

# OWL characteristics
:hasCustomerID a owl:DatatypeProperty, owl:InverseFunctionalProperty ;
    rdfs:domain :Customer ;
    rdfs:range xsd:string .

:hasEmail a owl:DatatypeProperty, owl:InverseFunctionalProperty ;
    rdfs:domain :Person .

:hasDateOfBirth a owl:DatatypeProperty, owl:FunctionalProperty ;
    rdfs:domain :Person ;
    rdfs:range xsd:date .

# Restrictions
:Customer rdfs:subClassOf [
    a owl:Restriction ;
    owl:onProperty :hasEmail ;
    owl:cardinality 1
] .
```

**Data:**
```csv
customer_id,full_name,first_name,last_name,email,birth_date
C001,John Doe,John,Doe,john@ex.com,1990-01-15
C002,Jane Smith,Jane,Smith,jane@ex.com,1985-05-20
```

**Complete Semantic Matching Process:**

#### Column: "customer_id"

**Layer 1 - Linguistic:**
- Embedding similarity to :hasCustomerID: 0.92

**Layer 2 - Ontology:**
- Property is InverseFunctionalProperty ✓
- Domain is :Customer (matches target class) ✓
- Range is xsd:string ✓

**Layer 3 - Graph Context:**
- Part of customer entity properties
- No conflicting matches

**Layer 4 - Data:**
- 100% unique values ✓ (matches IFP)
- Pattern: "C" + digits (ID format) ✓
- No nulls ✓

**Final Match:**
- Property: :hasCustomerID
- Confidence: 0.98
- Reasoning: Perfect alignment across all layers
- Recommendation: Use for IRI template

---

#### Column: "full_name"

**Layer 1 - Linguistic:**
- Exact match to :hasFullName label: 0.95

**Layer 2 - Ontology:**
- :hasFullName subPropertyOf :hasName subPropertyOf :hasIdentifier
- Understands specificity hierarchy
- Domain check: :hasName domain is :Person, :Customer inherits ✓

**Layer 3 - Graph Context:**
- "first_name" and "last_name" also present
- Validates this is the composite name field
- Structural consistency

**Layer 4 - Data:**
- String type (matches range) ✓
- Format: "First Last" pattern ✓

**Final Match:**
- Property: :hasFullName
- Confidence: 0.97
- Reasoning: Exact match + hierarchy awareness + context
- Note: Also satisfies :hasName and :hasIdentifier (inheritance)

---

#### Column: "email"

**Layer 1 - Linguistic:**
- Exact match: 0.95

**Layer 2 - Ontology:**
- Property is InverseFunctionalProperty ✓
- Cardinality restriction: exactly 1 ✓

**Layer 3 - Graph Context:**
- Common in person/customer entities ✓

**Layer 4 - Data:**
- All values unique ✓ (matches IFP)
- Email format validation ✓
- No nulls ✓ (matches cardinality 1)

**Final Match:**
- Property: :hasEmail
- Confidence: 0.98
- Reasoning: Perfect semantic alignment
- Recommendation: Can be used as identifier

---

## Summary: What Makes Matching "Semantic"

### String Matching (NOT Semantic)
```
"customer_id" matches "customerID" → 0.92
# Just string similarity
```

### Shallow Semantic (Current State)
```
"customer_id" matches :hasCustomerID
# Label similarity + BERT embeddings
# Confidence: 0.85
```

### Deep Semantic (Target State)
```
"customer_id" matches :hasCustomerID

BECAUSE:
1. Label similarity (0.92) - Linguistic
2. Is InverseFunctionalProperty (identifier) - Ontology
3. Data is 100% unique (matches IFP) - Data pattern
4. Domain is :Customer (target class) - Class hierarchy
5. Other ID-like columns not matched (uniqueness) - Graph context

# Confidence: 0.98
# Full semantic understanding across all dimensions
```

---

## Implementation Priority

Based on this analysis, here's what we need to implement:

### Phase 1: Critical (Current → 9.0/10)
1. **Property Hierarchy Matcher** ← START HERE
   - rdfs:subPropertyOf reasoning
   - Inheritance-aware matching
   - Specificity scoring

2. **OWL Characteristics Matcher**
   - Functional/InverseFunctional detection
   - Data pattern validation against OWL
   - IRI template suggestions

3. **Graph Context Matcher**
   - Property co-occurrence patterns
   - Structural similarity
   - Context-based confidence boosting

4. **Enhanced Semantic Matcher**
   - Use comments + labels in embeddings
   - Class-aware matching
   - Multi-field semantic comparison

### Phase 2: Important (9.0 → 9.5/10)
5. **Restriction-Based Matcher**
6. **SKOS Relations Matcher**

### Phase 3: Excellence (9.5 → 10.0/10)
7. **Probabilistic Graph Reasoning**
8. **Ontology-Driven Validation**

---

**Ready to implement Property Hierarchy Matcher?**

This will be the foundation for true semantic reasoning, enabling inheritance-aware matching and proper understanding of property relationships.

