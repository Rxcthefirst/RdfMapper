# Quick Reference: Tests vs Demos

## Understanding the Difference

### Tests (pytest)
- **Purpose:** Automated validation of functionality
- **Location:** `tests/` directory
- **How to run:** `python -m pytest tests/test_*.py`
- **Output:** Pass/fail assertions
- **When to use:** Development, CI/CD, validation

### Demos (scripts)
- **Purpose:** Show features to users, visual output
- **Location:** `scripts/` directory  
- **How to run:** `python scripts/demo_*.py`
- **Output:** Formatted console output with explanations
- **When to use:** Learning, presentations, documentation

---

## Running Tests

### Run All Tests
```bash
python -m pytest
```

### Run Specific Test File
```bash
python -m pytest tests/test_hierarchy_matcher.py
```

### Run Specific Test Class
```bash
python -m pytest tests/test_hierarchy_matcher.py::TestPropertyHierarchyMatcher
```

### Run Specific Test
```bash
python -m pytest tests/test_hierarchy_matcher.py::TestPropertyHierarchyMatcher::test_exact_match_with_hierarchy
```

### Run with Verbose Output
```bash
python -m pytest tests/test_hierarchy_matcher.py -v
```

### Run with Coverage
```bash
python -m pytest tests/test_hierarchy_matcher.py --cov=rdfmap.generator.matchers --cov-report=html
```

---

## Running Demos

### Property Hierarchy Matcher Demo
```bash
python scripts/demo_hierarchy_matcher.py
```

Shows:
- Property hierarchy tree visualization
- Confidence scores with explanations
- Parent/child relationships
- Real matching examples

### OWL Characteristics Matcher Demo
```bash
python scripts/demo_owl_matcher.py
```

Shows:
- OWL property characteristics (Functional, InverseFunctional)
- Data validation against OWL semantics
- Violation detection
- Enrichment suggestions

### Debug Scripts
```bash
python scripts/debug_hierarchy.py
```

Shows:
- Raw ontology structure
- Label variations
- Relationship debugging

---

## Semantic Matcher Tests & Demos

| Feature | Test File | Demo Script | Documentation |
|---------|-----------|-------------|---------------|
| Property Hierarchy | `tests/test_hierarchy_matcher.py` | `scripts/demo_hierarchy_matcher.py` | [PROPERTY_HIERARCHY_MATCHER_COMPLETE.md](PROPERTY_HIERARCHY_MATCHER_COMPLETE.md) |
| OWL Characteristics | `tests/test_owl_characteristics_matcher.py` | `scripts/demo_owl_matcher.py` | [OWL_CHARACTERISTICS_MATCHER_COMPLETE.md](OWL_CHARACTERISTICS_MATCHER_COMPLETE.md) |

---

## Example Workflow

### Development Workflow
```bash
# 1. Write a test (TDD)
# Edit tests/test_hierarchy_matcher.py

# 2. Run test (should fail initially)
python -m pytest tests/test_hierarchy_matcher.py::TestPropertyHierarchyMatcher::test_new_feature -v

# 3. Implement feature
# Edit src/rdfmap/generator/matchers/hierarchy_matcher.py

# 4. Run test again (should pass now)
python -m pytest tests/test_hierarchy_matcher.py::TestPropertyHierarchyMatcher::test_new_feature -v

# 5. Run all tests to ensure nothing broke
python -m pytest tests/test_hierarchy_matcher.py -v
```

### Demo/Presentation Workflow
```bash
# Show the feature working
python scripts/demo_hierarchy_matcher.py

# Beautiful output for users to see
```

---

## Test Organization

```
tests/
├── test_hierarchy_matcher.py          # 12 pytest tests
│   ├── TestPropertyHierarchyMatcher   # Core functionality (8 tests)
│   ├── TestHierarchyCacheBuilding     # Cache logic (3 tests)
│   └── TestHierarchyMatcherIntegration # Integration (1 test)
│
└── test_owl_characteristics_matcher.py # 14 pytest tests
    ├── TestOWLCharacteristicsMatcher   # Core functionality (7 tests)
    ├── TestOWLValidation               # Validation logic (3 tests)
    ├── TestOWLMatcherIntegration       # Integration (2 tests)
    └── TestConfidenceAdjustment        # Scoring logic (2 tests)
```

---

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.13
      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest pytest-cov
      - name: Run tests
        run: |
          python -m pytest tests/test_hierarchy_matcher.py tests/test_owl_characteristics_matcher.py -v --cov=rdfmap
```

---

## Key Principles

### Tests Should:
✅ Be automated (assertions, not print statements)  
✅ Be fast (use fixtures, avoid unnecessary setup)  
✅ Be isolated (each test independent)  
✅ Be repeatable (same result every time)  
✅ Cover edge cases  
✅ Have clear assertions  

### Demos Should:
✅ Be educational (explain what's happening)  
✅ Be visual (formatted output, colors)  
✅ Show real examples  
✅ Include multiple scenarios  
✅ Be self-contained  

---

## Quick Commands

### Run everything
```bash
# All tests
python -m pytest

# All demos (note: run individually, they don't return exit codes)
python scripts/demo_hierarchy_matcher.py
python scripts/demo_owl_matcher.py
```

### Development
```bash
# Run tests in watch mode (requires pytest-watch)
pip install pytest-watch
ptw tests/test_hierarchy_matcher.py
```

### Coverage
```bash
# Generate coverage report
python -m pytest --cov=rdfmap.generator.matchers --cov-report=html
open htmlcov/index.html  # View in browser
```

---

## Summary

- **Tests** = Automated validation (pytest)
- **Demos** = User-facing examples (scripts)
- **Tests** validate **Demos** showcase
- Both are important and serve different purposes!

For more details, see:
- [SEMANTIC_MATCHER_DEMOS.md](SEMANTIC_MATCHER_DEMOS.md) - Demo documentation
- [TDD_CONVERSION_COMPLETE.md](TDD_CONVERSION_COMPLETE.md) - TDD conversion details

