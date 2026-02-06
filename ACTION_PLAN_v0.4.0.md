# Action Plan: Fix Tests and Prepare v0.4.0 Release

**Status**: 🔴 31 test failures + 2 errors to fix  
**Target**: ✅ All tests passing, ready for PyPI release  
**Timeline**: ~2-3 weeks

---

## Phase 1: Fix Configuration Format Issues (Priority: CRITICAL)

### Issue: Tests expect v1 format, parsers return v2 format

**v1 Format (OLD)**:
```python
{
    'sheets': [{
        'name': 'people',
        'source': 'people.csv',
        'class': 'schema:Person',  # ← Direct property
        'subject_template': 'http://example.org/person/$(id)',
        'columns': [  # ← List of column mappings
            {'column': 'name', 'property': 'schema:name'}
        ]
    }]
}
```

**v2 Format (NEW)**:
```python
{
    'sheets': [{
        'name': 'people',
        'source': 'people.csv',
        'row_resource': {  # ← Nested object
            'class': 'schema:Person',
            'iri_template': 'http://example.org/person/$(id)'
        },
        'properties': {  # ← Dictionary keyed by column name
            'name': {'as': 'schema:name'}
        }
    }]
}
```

### Tasks:

#### Task 1.1: Add Format Compatibility Layer
**File**: `src/rdfmap/config/format_adapter.py` (NEW)

```python
def v2_to_v1_format(v2_config: dict) -> dict:
    """Convert v2 format to v1 format for backward compatibility."""
    v1_config = {
        'namespaces': v2_config.get('namespaces', {}),
        'defaults': v2_config.get('defaults', {}),
        'sheets': []
    }
    
    for sheet in v2_config.get('sheets', []):
        v1_sheet = {
            'name': sheet['name'],
            'source': sheet['source'],
            'format': sheet.get('format', 'csv'),
            'class': sheet['row_resource']['class'],
            'subject_template': sheet['row_resource']['iri_template'],
            'columns': []
        }
        
        # Convert properties dict to columns list
        for col_name, prop_def in sheet.get('properties', {}).items():
            v1_sheet['columns'].append({
                'column': col_name,
                'property': prop_def['as'],
                'datatype': prop_def.get('datatype'),
                'language': prop_def.get('language')
            })
        
        # Convert objects dict to columns list (with object_property flag)
        for obj_name, obj_def in sheet.get('objects', {}).items():
            # Handle nested entity references
            pass  # Implementation needed
        
        v1_config['sheets'].append(v1_sheet)
    
    return v1_config
```

**Tests to Write**:
- `tests/unit/test_format_adapter.py` - Test v2→v1 and v1→v2 conversions

#### Task 1.2: Update RML Parser to Support Both Formats
**File**: `src/rdfmap/config/rml_parser.py`

**Change**: Add optional parameter `output_format='v2'`:
```python
def parse(self, rml_path: Path, output_format: str = 'v2') -> Dict[str, Any]:
    """
    Parse RML file.
    
    Args:
        rml_path: Path to RML file
        output_format: 'v1' or 'v2' (default: 'v2')
    """
    result = self._parse_to_v2(rml_path)
    
    if output_format == 'v1':
        from .format_adapter import v2_to_v1_format
        return v2_to_v1_format(result)
    
    return result
```

#### Task 1.3: Update All Tests
**Files to Update**:
1. `tests/test_rml_parser.py` - Use `output_format='v1'` or update assertions for v2
2. `tests/test_rml_generator.py` - Update expectations for v2
3. `tests/test_mortgage_example.py` - Update all mortgage tests
4. `tests/test_mapping.py` - Update schema expectations

**Decision**: Recommend updating tests to v2 format (future-proof) rather than using compatibility layer.

---

## Phase 2: Fix Matcher Pipeline Tests (Priority: HIGH)

### Issue: Tests expect 17 matchers, now have 5 optimized matchers

### Tasks:

#### Task 2.1: Update Matcher Count Tests
**File**: `tests/test_17_matchers_complete.py`

**Option A**: Rename file to `tests/test_optimized_pipeline.py` and update expectations:
```python
def test_optimized_pipeline_available():
    """Test that pipeline has 5 optimized matchers."""
    config = load_config()
    pipeline = create_matching_pipeline(config)
    
    # Should have exactly 5 matchers
    assert len(pipeline.matchers) == 5
    
    # Verify matcher types
    matcher_types = [type(m).__name__ for m in pipeline.matchers]
    expected = [
        'ExactPrefLabelMatcher',
        'ExactRdfsLabelMatcher',
        'SemanticSimilarityMatcher',
        'DataTypeInferenceMatcher',
        'PartialStringMatcher'
    ]
    assert set(matcher_types) == set(expected)
```

**Option B**: Keep comprehensive test but adjust expectations:
```python
def test_all_available_matchers_fire():
    """Test that available matchers fire appropriately."""
    # Should fire 1-3 matchers on average (not 10-15)
    avg_matchers = calculate_average_matchers_fired(results)
    assert 1 <= avg_matchers <= 3, f"Expected 1-3 matchers, got {avg_matchers}"
```

#### Task 2.2: Update Evidence Quality Tests
**File**: `tests/test_17_matchers_complete.py`

```python
def test_evidence_quality_with_optimized_pipeline():
    """Test that optimized pipeline produces high-quality evidence."""
    # With 5 matchers, expect 1-5 evidence items (not 6-8)
    for col in results['columns']:
        evidence_count = len(col.get('evidence', []))
        assert 1 <= evidence_count <= 5
        
        # Should still have mix of semantic + ontological evidence
        categories = categorize_evidence(col['evidence'])
        assert 'semantic' in categories  # From SemanticSimilarityMatcher
        # May or may not have ontological depending on ontology
```

#### Task 2.3: Update Matcher Integration Tests
**Files**:
- `tests/test_matcher_pipeline.py`
- `tests/test_phase2_integration.py`
- `tests/test_datatype_matcher.py`

**Strategy**: Update assertions to match new pipeline behavior, verify quality hasn't degraded.

---

## Phase 3: Fix Semantic Matcher Type Errors (Priority: HIGH)

### Issue: TypeError in `test_enhanced_semantic_matcher.py`

### Tasks:

#### Task 3.1: Fix Type Errors in Enhanced Semantic Matcher
**File**: `src/rdfmap/generator/matchers/semantic_matcher.py` (or enhanced version)

**Investigation Needed**:
1. Check what TypeError is occurring
2. Fix domain_aware_boost logic
3. Fix threshold_respected logic

**Run test to see exact error**:
```bash
pytest tests/test_enhanced_semantic_matcher.py::test_domain_aware_boost -v
```

#### Task 3.2: Update Test Expectations
Once fixed, ensure tests match current API.

---

## Phase 4: Add Tests for Untested Modules (Priority: CRITICAL)

### Issue: New v2 modules have 0% test coverage

### Tasks:

#### Task 4.1: Create `tests/unit/test_v2_generator.py`

```python
"""Tests for V2 configuration generator."""

import pytest
from pathlib import Path
from rdfmap.config.v2_generator import V2Generator


def test_v2_generator_basic():
    """Test basic v2 config generation."""
    generator = V2Generator(
        ontology_path=Path("examples/mortgage/ontology/mortgage_ontology.ttl"),
        data_path=Path("examples/mortgage/data/loans.csv")
    )
    
    config = generator.generate()
    
    # Verify v2 structure
    assert 'sheets' in config
    assert len(config['sheets']) > 0
    
    sheet = config['sheets'][0]
    assert 'row_resource' in sheet
    assert 'class' in sheet['row_resource']
    assert 'iri_template' in sheet['row_resource']
    assert 'properties' in sheet
    assert isinstance(sheet['properties'], dict)


def test_v2_generator_with_nested_entities():
    """Test v2 generation with nested entities."""
    # Test with ontology that has object properties
    pass


def test_v2_generator_preserves_alignment():
    """Test that AI alignment metadata is preserved."""
    pass
```

**Coverage Target**: >80% for new modules

#### Task 4.2: Create `tests/unit/test_yarrrml_generator.py`

```python
"""Tests for YARRRML generator."""

def test_yarrrml_generator_basic():
    """Test basic YARRRML generation."""
    # Generate from internal config → YARRRML
    pass


def test_yarrrml_with_alignment_metadata():
    """Test x-alignment extensions in YARRRML."""
    pass


def test_yarrrml_format_compliance():
    """Test output is valid YARRRML 1.3.0."""
    pass
```

#### Task 4.3: Create `tests/unit/test_yarrrml_parser.py`

```python
"""Tests for YARRRML parser."""

def test_yarrrml_parser_basic():
    """Test parsing basic YARRRML file."""
    pass


def test_yarrrml_parser_with_nested_entities():
    """Test parsing YARRRML with nested mappings."""
    pass


def test_yarrrml_roundtrip():
    """Test YARRRML → internal → YARRRML preserves structure."""
    pass
```

#### Task 4.4: Create Integration Tests
**File**: `tests/integration/test_rml_yarrrml_roundtrip.py`

```python
"""Test that RML and YARRRML formats are fully interoperable."""

def test_rml_to_internal_to_rml():
    """Test RML → internal format → RML preserves structure."""
    pass


def test_yarrrml_to_internal_to_yarrrml():
    """Test YARRRML → internal format → YARRRML preserves structure."""
    pass


def test_rml_to_yarrrml_conversion():
    """Test RML can be converted to YARRRML and back."""
    pass


def test_works_with_rmlmapper():
    """Test that generated RML works with RMLMapper-java."""
    # If RMLMapper is available, test compatibility
    pass
```

---

## Phase 5: Clean Up Project Structure (Priority: MEDIUM)

### Tasks:

#### Task 5.1: Reorganize Test Fixtures

```bash
# Create new structure
mkdir -p tests/fixtures/{configs,data,ontologies,mappings,outputs}

# Move files
mv test_configs/* tests/fixtures/configs/
mv test_data/* tests/fixtures/data/
mv test_formats/* tests/fixtures/data/formats/

# Update .gitignore
echo "tests/fixtures/outputs/" >> .gitignore

# Remove old directories
rm -rf test_configs test_data test_formats test_outputs
```

#### Task 5.2: Clean Up Root Directory

```bash
# Remove test artifacts
rm rml_conversion_output.ttl rml_output.ttl test_alignment.json build.log

# Remove Docker leftovers
rm -rf uploads/

# Add to .gitignore
cat >> .gitignore << EOF

# Test outputs
*.ttl
*.rdf
*.nt
*.jsonld
*_output.*
test_*.json
build.log

# Upload directories
uploads/
EOF
```

#### Task 5.3: Reorganize Tests

```bash
mkdir -p tests/{unit,integration,validation,fixtures}

# Move unit tests
mv tests/test_*_matcher*.py tests/unit/
mv tests/test_datatype*.py tests/unit/
mv tests/test_iri.py tests/unit/
mv tests/test_mapping.py tests/unit/
mv tests/test_rml*.py tests/unit/

# Move integration tests
mv tests/test_generator_workflow.py tests/integration/
mv tests/test_phase*.py tests/integration/
mv tests/test_end_to_end.py tests/integration/
mv tests/test_mortgage_example.py tests/integration/

# Validation tests already in tests/validation/

# Update imports in moved tests
# (May need to adjust relative imports)
```

---

## Phase 6: Create Clean Example Suite (Priority: MEDIUM)

### Task 6.1: Create Basic CSV Example
**Directory**: `examples/01_basic_csv/`

```
01_basic_csv/
├── README.md          # Step-by-step tutorial
├── data.csv           # Simple 3-column CSV
├── ontology.ttl       # Minimal ontology
├── config.yaml        # v2 config with inline mapping
└── output.ttl         # Expected output
```

**README.md** should include:
- What this example demonstrates
- How to run it
- Expected output
- Explanation of each config section

### Task 6.2: Create JSON Nested Example
**Directory**: `examples/02_json_nested/`

```
02_json_nested/
├── README.md
├── data.json          # 3-level nested JSON
├── ontology.ttl
├── config.yaml        # With nested entity mappings
└── output.ttl
```

### Task 6.3: Create XML Complex Example
**Directory**: `examples/03_xml_complex/`

```
03_xml_complex/
├── README.md
├── data.xml           # XML with attributes and nesting
├── ontology.ttl
├── config.rml.ttl     # RML format example
└── output.ttl
```

### Task 6.4: Create Multi-Sheet Excel Example
**Directory**: `examples/04_multi_sheet_excel/`

```
04_multi_sheet_excel/
├── README.md
├── data.xlsx          # Multiple sheets with relationships
├── ontology.ttl
├── config.yaml        # Multi-sheet mapping
└── output.ttl
```

### Task 6.5: Enhance Mortgage Example
**Directory**: `examples/05_mortgage_complete/`

```
# Rename examples/mortgage → examples/05_mortgage_complete
# Add comprehensive README with all workflows
```

---

## Phase 7: Update Documentation (Priority: HIGH)

### Task 7.1: Create UPGRADE_GUIDE.md

```markdown
# Upgrading from v0.3.0 to v0.4.0

## Breaking Changes

### Configuration Format

v0.3.0 used "v1" format, v0.4.0 introduces "v2" format:

**v0.3.0 (v1 format)**:
```yaml
sheets:
  - name: people
    source: people.csv
    class: schema:Person
    subject_template: http://example.org/person/$(id)
    columns:
      - column: name
        property: schema:name
```

**v0.4.0 (v2 format)**:
```yaml
sheets:
  - name: people
    source: people.csv
    row_resource:
      class: schema:Person
      iri_template: http://example.org/person/$(id)
    properties:
      name:
        as: schema:name
```

### Migration Script

Use the included migration script:
```bash
rdfmap migrate-config old_config.yaml new_config.yaml
```

### Matcher Pipeline

v0.4.0 uses optimized 5-matcher pipeline (was 17 matchers).
This is faster and more accurate, but evidence may look different.

## New Features

- RML/YARRRML format support
- RDF/XML output format
- Named individual support
- Improved nested entity handling

## Deprecations

- v1 config format (still supported via `--legacy` flag)
```

### Task 7.2: Update README.md

- Add v0.4.0 to "What's New" section
- Update feature list
- Add examples of new formats (RML, YARRRML)
- Update command examples
- Add troubleshooting section for migration

### Task 7.3: Update CHANGELOG.md

```markdown
## [0.4.0] - 2025-12-XX

### 🎉 Major Release: V2 Configuration Format & Enhanced RML/YARRRML Support

**Breaking Changes**:
- New v2 configuration format (v1 deprecated but supported)
- Matcher pipeline optimized from 17→5 matchers

**New Features**:
- Full RML 1.0 compliance (Turtle, RDF/XML, N-Triples)
- YARRRML 1.3.0 support (read and write)
- Named individual support (multiple classes per entity)
- Enhanced nested entity handling
- RDF/XML output format
- Configuration migration tool

**Improvements**:
- 5x faster mapping generation (optimized matchers)
- Better type inference
- Improved error messages
- Comprehensive example suite

**Bug Fixes**:
- Fixed RML parser edge cases
- Fixed YARRRML column name handling
- Fixed path resolution for external mappings

**Documentation**:
- Added UPGRADE_GUIDE.md
- 5 new example projects
- Improved CLI documentation
```

### Task 7.4: Update pyproject.toml

```toml
[project]
version = "0.4.0"
description = "Convert data to RDF with AI-powered semantic mapping. Full RML/YARRRML support."
keywords = [
    "rdf", "ontology", "semantic-web", "knowledge-graph", "owl",
    "rml", "yarrrml", "r2rml", "rdf-mapping",
    "ai-semantic-matching", "data-integration"
]
```

---

## Phase 8: Final Testing and Release (Priority: CRITICAL)

### Task 8.1: Run Full Test Suite

```bash
# Clean environment
rm -rf .pytest_cache
rm -rf htmlcov
rm -rf dist/ build/ *.egg-info

# Activate venv
source .venv_py313/bin/activate

# Run tests with coverage
pytest --cov=src/rdfmap --cov-report=html --cov-report=term -v

# Verify all tests pass
pytest --tb=short -v

# Check coverage
open htmlcov/index.html
```

**Quality Gates**:
- ✅ 0 test failures
- ✅ 0 test errors
- ✅ ≥70% coverage on core modules
- ✅ ≥80% coverage on new modules (v2_generator, yarrrml_*)

### Task 8.2: Test in Clean Virtual Environment

```bash
# Create fresh venv
python3.13 -m venv /tmp/test_rdfmap_venv
source /tmp/test_rdfmap_venv/bin/activate

# Build package
python -m build

# Install from wheel
pip install dist/semantic_rdf_mapper-0.4.0-py3-none-any.whl

# Test CLI works
rdfmap --version
rdfmap --help

# Run example
cd examples/01_basic_csv
rdfmap convert -m config.yaml -o output.ttl

# Verify output
cat output.ttl
```

### Task 8.3: Test on TestPyPI

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ semantic-rdf-mapper==0.4.0

# Test again
rdfmap --version
```

### Task 8.4: Release to PyPI

```bash
# Tag release
git tag -a v0.4.0 -m "Release v0.4.0: V2 Format & Enhanced RML/YARRRML Support"
git push origin v0.4.0

# Upload to PyPI
python -m twine upload dist/*

# Verify on PyPI
open https://pypi.org/project/semantic-rdf-mapper/

# Test install
pip install --upgrade semantic-rdf-mapper
rdfmap --version
```

### Task 8.5: Create GitHub Release

- Go to GitHub releases
- Create release for v0.4.0
- Copy CHANGELOG entry
- Upload wheel and source distribution
- Publish release

---

## Execution Checklist

### Phase 1: Configuration Format (Week 1, Days 1-3)
- [ ] Create `format_adapter.py` with v2↔v1 conversion
- [ ] Add tests for format adapter
- [ ] Update RML parser to support both formats
- [ ] Update YARRRML parser to support both formats
- [ ] Update all configuration-related tests
- [ ] Verify 12 tests now pass

### Phase 2: Matcher Pipeline (Week 1, Days 4-5)
- [ ] Rename/update `test_17_matchers_complete.py`
- [ ] Update matcher count expectations
- [ ] Update evidence quality expectations
- [ ] Update integration test expectations
- [ ] Verify 8 tests now pass

### Phase 3: Semantic Matcher (Week 2, Days 1-2)
- [ ] Debug TypeErrors in enhanced semantic matcher
- [ ] Fix domain_aware_boost
- [ ] Fix threshold_respected
- [ ] Update test expectations
- [ ] Verify 5 tests now pass

### Phase 4: Add Missing Tests (Week 2, Days 3-5)
- [ ] Write `test_v2_generator.py` (>80% coverage)
- [ ] Write `test_yarrrml_generator.py` (>80% coverage)
- [ ] Write `test_yarrrml_parser.py` (>80% coverage)
- [ ] Write `test_rml_yarrrml_roundtrip.py`
- [ ] Verify overall coverage ≥70%

### Phase 5: Clean Up Structure (Week 3, Day 1)
- [ ] Reorganize test fixtures
- [ ] Clean up root directory
- [ ] Reorganize tests into unit/integration/validation
- [ ] Update .gitignore
- [ ] Verify all tests still pass after reorganization

### Phase 6: Create Examples (Week 3, Days 2-3)
- [ ] Create `01_basic_csv` example
- [ ] Create `02_json_nested` example
- [ ] Create `03_xml_complex` example
- [ ] Create `04_multi_sheet_excel` example
- [ ] Enhance `05_mortgage_complete` example
- [ ] Test all examples work

### Phase 7: Update Documentation (Week 3, Days 4-5)
- [ ] Create UPGRADE_GUIDE.md
- [ ] Update README.md
- [ ] Update CHANGELOG.md
- [ ] Update pyproject.toml version and metadata
- [ ] Review all documentation for accuracy

### Phase 8: Final Testing (Week 4, Days 1-3)
- [ ] Run full test suite (all pass)
- [ ] Check coverage (≥70%)
- [ ] Test in clean venv
- [ ] Test on TestPyPI
- [ ] Run all examples

### Phase 9: Release (Week 4, Day 4)
- [ ] Create git tag
- [ ] Upload to PyPI
- [ ] Create GitHub release
- [ ] Announce release
- [ ] Monitor for issues

---

## Success Criteria

✅ **All tests passing** (0 failures, 0 errors)  
✅ **Test coverage ≥70%** (core modules)  
✅ **Test coverage ≥80%** (new modules)  
✅ **5 working examples** with documentation  
✅ **Clean repository** (no artifacts, organized structure)  
✅ **Complete documentation** (README, CHANGELOG, UPGRADE_GUIDE)  
✅ **PyPI package works** (installs and runs correctly)  
✅ **Backward compatibility** (v1 configs still work)  

---

## Estimated Effort

- **Phase 1-3** (Fix Tests): ~40 hours
- **Phase 4** (Add Tests): ~24 hours
- **Phase 5** (Clean Up): ~8 hours
- **Phase 6** (Examples): ~16 hours
- **Phase 7** (Documentation): ~16 hours
- **Phase 8-9** (Testing & Release): ~16 hours

**Total**: ~120 hours (~3 weeks full-time or ~6 weeks part-time)

---

**Status**: 📋 Plan Created  
**Next Step**: Begin Phase 1 - Fix Configuration Format Issues

