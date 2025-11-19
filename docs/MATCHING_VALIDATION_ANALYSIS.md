# Matching System Validation & Analysis

**Date:** November 16, 2025  
**Status:** Comprehensive validation of multi-matcher system  
**Confidence:** High ✅

---

## Match Reasons Table Analysis

### Your Mortgage Example Results

| Column | Property | Match Type | Matcher | Matched Via | Confidence |
|--------|----------|------------|---------|-------------|------------|
| LoanID | loanNumber | Semantic Similarity | DataTypeInferenceMatcher | data type: string | 1.00 |
| Principal | principalAmount | Semantic Similarity | DataTypeInferenceMatcher | data type: integer | 1.00 |
| InterestRate | interestRate | Exact Label | DataTypeInferenceMatcher | data type: decimal | 0.95 |
| OriginationDate | originationDate | Exact Label | ExactRdfsLabelMatcher | origination date | 0.95 |
| LoanTerm | loanTerm | Exact Label | DataTypeInferenceMatcher | data type: integer | 0.95 |
| Status | loanStatus | Semantic Similarity | DataTypeInferenceMatcher | data type: string | 1.00 |
| BorrowerName | ex:borrowerName | Exact Label | ObjectPropertyMatcher | has borrower property | 0.95 |
| PropertyAddress | ex:propertyAddress | Exact Label | ObjectPropertyMatcher | collateral property property | 0.95 |
| BorrowerID | ex:hasBorrower | Graph Reasoning | RelationshipMatcher | Foreign key to has borrower | 1.00 |
| PropertyID | ex:collateralProperty | Graph Reasoning | RelationshipMatcher | Foreign key to collateral property | 1.00 |

---

## Initial Assessment

### ✅ What Looks Good

1. **Semantic Matches (3 columns):**
   - `LoanID` → `loanNumber` (semantic similarity detected)
   - `Principal` → `principalAmount` (semantic similarity detected)
   - `Status` → `loanStatus` (semantic similarity detected)
   - **Confidence:** 1.00 is high - these are strong semantic matches

2. **Exact Matches (5 columns):**
   - `InterestRate` → `interestRate` (exact label match)
   - `OriginationDate` → `originationDate` (exact rdfs:label match)
   - `LoanTerm` → `loanTerm` (exact label match)
   - `BorrowerName` → `borrowerName` (exact label match)
   - `PropertyAddress` → `propertyAddress` (exact label match)
   - **Confidence:** 0.95 is appropriate for exact matches

3. **Graph Reasoning (2 columns):**
   - `BorrowerID` → `hasBorrower` (relationship matcher detected FK)
   - `PropertyID` → `collateralProperty` (relationship matcher detected FK)
   - **Confidence:** 1.00 is correct - these are structural foreign keys

4. **All 10 columns mapped:** 100% coverage ✅

---

## 🚨 Potential Issues & Questions

### Issue 1: Semantic Similarity showing 1.00 confidence

**Problem:** Semantic similarity scores should typically range from 0.4-0.9, not exactly 1.00.

**Hypothesis:**
- The matcher might be falling back to exact string match first
- OR the DataTypeInferenceMatcher is boosting confidence to 1.00
- OR there's a bug in confidence calculation

**Expected behavior:**
- `LoanID` → `loanNumber`: similarity ~0.75-0.85
- `Principal` → `principalAmount`: similarity ~0.70-0.80
- `Status` → `loanStatus`: similarity ~0.80-0.90

**Action:** Review SemanticMatcher.match() - it should return actual similarity score, not 1.00.

---

### Issue 2: "DataTypeInferenceMatcher" appearing everywhere

**Problem:** DataTypeInferenceMatcher is listed as the matcher for:
- Semantic matches (LoanID, Principal, Status)
- Exact matches (InterestRate, LoanTerm)

**Question:** Is DataTypeInferenceMatcher the PRIMARY matcher, or is it just adding datatype context?

**Expected behavior:**
- **Primary matcher** should be SemanticMatcher (for LoanID, Principal, Status)
- **Primary matcher** should be ExactLabelMatcher (for InterestRate, LoanTerm)
- DataTypeInferenceMatcher should be listed as "additional context" or secondary

**Recommendation:** Clarify matcher hierarchy in output:
```
Match Type: Semantic Similarity
Primary Matcher: SemanticMatcher (similarity: 0.78)
Context: DataTypeInferenceMatcher (data type: string)
```

---

### Issue 3: "Matched Via" descriptions inconsistent

**Examples:**
- `data type: string` (just datatype)
- `origination date` (rdfs:label value)
- `has borrower property` (relationship description)
- `Foreign key to has borrower` (structural reasoning)

**Problem:** Different matchers use different formats for "matched via"

**Recommendation:** Standardize format:
```
ExactLabelMatcher: "exact match on rdfs:label: 'origination date'"
SemanticMatcher: "semantic similarity (0.78) on column name"
DataTypeMatcher: "datatype alignment: string → xsd:string"
RelationshipMatcher: "foreign key pattern detected (BorrowerID → hasBorrower)"
```

---

## Validation Test Cases

### Test Set 1: Contrived Examples (Edge Cases)

#### 1.1 Abbreviations & Acronyms
```yaml
Data Columns:
  - ssn            # Social Security Number
  - emp_id         # Employee ID
  - dob            # Date of Birth
  - addr           # Address
  
Ontology Properties:
  - socialSecurityNumber
  - employeeIdentifier
  - dateOfBirth
  - residentialAddress

Expected Matches:
  ssn → socialSecurityNumber (Semantic: 0.72)
  emp_id → employeeIdentifier (Semantic: 0.68)
  dob → dateOfBirth (Semantic: 0.75)
  addr → residentialAddress (Semantic: 0.65)
```

#### 1.2 Domain-Specific Terminology
```yaml
Data Columns:
  - apr            # Annual Percentage Rate
  - ltv            # Loan-to-Value ratio
  - piti           # Principal, Interest, Taxes, Insurance
  - fico           # FICO credit score
  
Ontology Properties:
  - annualPercentageRate
  - loanToValueRatio
  - monthlyPayment
  - creditScore

Expected Matches:
  apr → annualPercentageRate (Exact/Semantic: 0.85)
  ltv → loanToValueRatio (Semantic: 0.70)
  piti → monthlyPayment (Semantic: 0.55 - WEAK)
  fico → creditScore (Semantic: 0.60)
```

#### 1.3 Synonym Variations
```yaml
Data Columns:
  - customer_name
  - client_id
  - purchase_date
  - item_cost
  
Ontology Properties:
  - clientName
  - customerId
  - transactionDate
  - productPrice

Expected Matches:
  customer_name → clientName (Semantic: 0.82)
  client_id → customerId (Semantic: 0.80)
  purchase_date → transactionDate (Semantic: 0.65)
  item_cost → productPrice (Semantic: 0.58)
```

#### 1.4 Ambiguous Matches
```yaml
Data Columns:
  - name           # Could be person name, product name, company name
  - date           # Could be any date field
  - amount         # Could be price, quantity, balance
  - status         # Could be order status, account status, etc.
  
Ontology Properties:
  - personName, productName, organizationName
  - createdDate, modifiedDate, expirationDate
  - orderAmount, balanceAmount, paymentAmount
  - accountStatus, orderStatus, deliveryStatus

Expected Behavior:
  name → Multiple suggestions (confidence < 0.7)
  date → Multiple suggestions (confidence < 0.6)
  amount → Multiple suggestions (confidence < 0.6)
  status → Context-dependent (need data analysis)
```

---

### Test Set 2: Real-World Examples

#### 2.1 Healthcare Dataset (HL7 FHIR)
```yaml
Data Source: patient_records.csv
Ontology: FHIR Patient resource

Columns:
  patient_id          → Patient.identifier
  mrn                 → Patient.identifier (MRN type)
  first_name          → Patient.name.given
  last_name           → Patient.name.family
  birth_date          → Patient.birthDate
  gender              → Patient.gender
  phone               → Patient.telecom (phone type)
  email               → Patient.telecom (email type)
  street_address      → Patient.address.line
  city                → Patient.address.city
  state               → Patient.address.state
  zip                 → Patient.address.postalCode
  insurance_provider  → Patient.coverage.payor

Expected Matcher Distribution:
  - Exact matches: 40% (birth_date, gender, city, state, zip)
  - Semantic matches: 35% (mrn, first_name, last_name, phone, email)
  - Partial matches: 15% (street_address, insurance_provider)
  - Graph reasoning: 10% (FK relationships)

Challenges:
  - "mrn" (Medical Record Number) is domain-specific
  - "insurance_provider" is ambiguous (could be name or ID)
  - Address fields need structured mapping
```

#### 2.2 E-Commerce Dataset (schema.org)
```yaml
Data Source: products.csv
Ontology: schema.org Product

Columns:
  sku                 → Product.sku
  product_name        → Product.name
  description         → Product.description
  brand               → Product.brand
  category            → Product.category
  price               → Product.offers.price
  currency            → Product.offers.priceCurrency
  stock_qty           → Product.offers.availability
  image_url           → Product.image
  manufacturer        → Product.manufacturer
  model_number        → Product.model
  weight_lbs          → Product.weight (unit conversion needed)
  dimensions          → Product.height, width, depth (parse needed)

Expected Matcher Distribution:
  - Exact matches: 50% (sku, name, description, brand, category, price)
  - Semantic matches: 25% (stock_qty, manufacturer, model_number)
  - Transform needed: 25% (currency, weight_lbs, dimensions)

Challenges:
  - "stock_qty" → "availability" requires datatype transform (int → enum)
  - "weight_lbs" requires unit conversion
  - "dimensions" requires string parsing (e.g., "10x5x3" → height/width/depth)
```

#### 2.3 Financial Dataset (FIBO Ontology)
```yaml
Data Source: transactions.csv
Ontology: FIBO Financial Instruments

Columns:
  transaction_id      → Transaction.identifier
  account_num         → Account.accountNumber
  routing_num         → Account.routingNumber
  transaction_type    → Transaction.type (DEBIT/CREDIT)
  amount              → Transaction.amount
  balance_before      → Account.balance (pre-transaction)
  balance_after       → Account.balance (post-transaction)
  merchant_name       → Merchant.name
  merchant_category   → MerchantCategory.code
  timestamp           → Transaction.dateTime
  auth_code           → Transaction.authorizationCode
  card_last4          → PaymentCard.lastFourDigits

Expected Matcher Distribution:
  - Exact matches: 35% (amount, timestamp, auth_code)
  - Semantic matches: 40% (transaction_type, merchant_name, card_last4)
  - Graph reasoning: 15% (account_num, routing_num)
  - Domain-specific: 10% (merchant_category)

Challenges:
  - "balance_before/after" are temporal - need state management
  - "merchant_category" uses MCC codes (needs lookup table)
  - "card_last4" is PII-sensitive (masking needed)
```

---

## Validation Metrics

### What to Measure

1. **Precision:** Of the matches suggested, how many are correct?
   ```
   Precision = Correct Matches / Total Suggested Matches
   ```

2. **Recall:** Of the columns that SHOULD be matched, how many were found?
   ```
   Recall = Correct Matches / Total Columns
   ```

3. **Confidence Calibration:** Do high-confidence matches succeed more often?
   ```
   For matches with confidence > 0.8: Acceptance rate should be > 90%
   For matches with confidence 0.5-0.8: Acceptance rate should be 60-80%
   For matches with confidence < 0.5: Acceptance rate should be < 50%
   ```

4. **Matcher Contribution:** Which matchers are most useful?
   ```
   Track: Exact (%), Semantic (%), Partial (%), Fuzzy (%), Graph (%)
   ```

5. **False Positive Rate:** How many incorrect suggestions?
   ```
   FPR = Incorrect Suggestions / Total Suggestions
   ```

---

## Recommended Validation Process

### Step 1: Create Test Dataset
```python
# tests/test_data/validation_suite.yaml
test_cases:
  - name: "Mortgage Loans"
    data: "tests/fixtures/loans.csv"
    ontology: "tests/fixtures/mortgage.ttl"
    expected_matches:
      LoanID: {property: "loanNumber", matcher: "semantic", min_confidence: 0.7}
      Principal: {property: "principalAmount", matcher: "semantic", min_confidence: 0.7}
      # ... etc
    
  - name: "Healthcare Patients"
    data: "tests/fixtures/patients.csv"
    ontology: "tests/fixtures/fhir_patient.ttl"
    expected_matches:
      # ... etc

  - name: "Ambiguous Columns"
    data: "tests/fixtures/ambiguous.csv"
    ontology: "tests/fixtures/general.ttl"
    expected_behavior: "multiple_suggestions"
    columns:
      name: {expected_count: ">= 3", max_confidence: "<= 0.70"}
```

### Step 2: Run Automated Validation
```python
# scripts/validate_matching.py
def validate_matching_system():
    results = {
        'total_cases': 0,
        'passed': 0,
        'failed': 0,
        'precision': [],
        'recall': [],
        'confidence_calibration': {}
    }
    
    for test_case in load_test_cases():
        generator = MappingGenerator(
            ontology_file=test_case.ontology,
            data_file=test_case.data,
            config=GeneratorConfig(base_iri="http://test.org/"),
            use_semantic_matching=True
        )
        
        mapping, report = generator.generate_with_alignment_report()
        
        # Validate matches
        actual_matches = extract_matches(mapping)
        expected_matches = test_case.expected_matches
        
        # Calculate metrics
        correct = count_correct_matches(actual_matches, expected_matches)
        precision = correct / len(actual_matches)
        recall = correct / len(expected_matches)
        
        results['total_cases'] += 1
        results['precision'].append(precision)
        results['recall'].append(recall)
        
        if precision >= 0.80 and recall >= 0.80:
            results['passed'] += 1
        else:
            results['failed'] += 1
            print(f"FAILED: {test_case.name}")
            print(f"  Precision: {precision:.2f}, Recall: {recall:.2f}")
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Validation Results:")
    print(f"  Total Cases: {results['total_cases']}")
    print(f"  Passed: {results['passed']}")
    print(f"  Failed: {results['failed']}")
    print(f"  Avg Precision: {np.mean(results['precision']):.2f}")
    print(f"  Avg Recall: {np.mean(results['recall']):.2f}")
    print(f"{'='*60}\n")
```

### Step 3: Manual Review Process
```yaml
# For each failed case:
1. Inspect the suggested matches
2. Identify why the matcher failed:
   - Semantic embeddings too weak?
   - Label mismatch?
   - Missing context?
3. Add to regression test suite
4. Tune matcher or add new matcher type
```

---

## Recommended Actions

### Immediate (This Week)

1. **Fix Semantic Confidence Scores**
   - Review SemanticMatcher.match() implementation
   - Ensure it returns actual similarity (0.4-0.9), not 1.00
   - Test with `pytest tests/test_semantic_matcher.py -v`

2. **Clarify Matcher Attribution**
   - Update alignment report to show PRIMARY matcher clearly
   - List DataTypeInferenceMatcher as "context" not "matcher"
   - Format: `Primary: SemanticMatcher (0.78) | Context: DataType (string)`

3. **Standardize "Matched Via" Format**
   - Each matcher should have consistent format
   - Include confidence/score in description
   - Example: `"semantic similarity (0.78) on column name + samples"`

### Short-term (Next 2 Weeks)

4. **Create Validation Test Suite**
   - Add 10 test cases covering edge cases
   - Include ambiguous columns
   - Test matcher priority correctly

5. **Run Benchmark**
   - Test on 5 real-world datasets
   - Measure precision, recall, confidence calibration
   - Document results

6. **Build Confidence Calibration Tool**
   - Track which confidence ranges correlate with user acceptance
   - Adjust confidence scores accordingly

### Medium-term (Next Month)

7. **Implement Matcher Explainability**
   - Add detailed "why this match?" explanation
   - Show top 5 alternatives with reasons
   - Help users understand AI decisions

8. **Add Manual Override UI**
   - Let users reject suggestions
   - Let users pick from alternatives
   - Learn from user feedback

---

## Conclusion

### Current Status: 🟡 Partially Validated

**Strengths:**
- ✅ All 10 columns matched (100% recall)
- ✅ Diverse matcher types working together
- ✅ Graph reasoning detecting FK relationships
- ✅ Semantic matching catching non-exact matches

**Concerns:**
- ⚠️ Semantic confidence scores showing 1.00 (should be 0.4-0.9)
- ⚠️ Matcher attribution unclear (DataTypeInferenceMatcher appearing everywhere)
- ⚠️ No validation against ground truth yet
- ⚠️ No precision/recall metrics calculated

**Recommendation:**
Create automated validation suite ASAP to measure:
- Precision (% of suggestions that are correct)
- Recall (% of columns that get matched)
- Confidence calibration (do high-confidence matches succeed more?)

Once we have metrics, we can tune thresholds and improve matcher quality.

**Next Steps:**
1. Fix semantic confidence scoring bug
2. Create 10-case validation test suite
3. Run benchmark and document results
4. Build confidence calibration based on user feedback

---

**Status:** Ready for validation suite creation ✅  
**Confidence in System:** 7.5/10 (needs validation data)  
**Expected After Validation:** 8.5/10

