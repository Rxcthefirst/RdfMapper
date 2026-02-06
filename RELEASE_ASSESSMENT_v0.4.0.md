# Release Assessment for v0.4.0

**Assessment Date**: December 9, 2025  
**Current Version**: 0.3.0  
**Target Version**: 0.4.0  
**Assessment Status**: 🔴 **NOT READY - Critical Issues Found**

---

## Executive Summary

The project has undergone significant refactoring to support RML/YARRRML standards compliance and v2 configuration format. However, this has introduced **31 test failures and 2 errors** that must be resolved before release.

### Current Test Status
- ✅ **349 tests passing** (88%)
- ⏭️ **15 tests skipped**
- ❌ **31 tests failing** (8%)
- 🔥 **2 tests with errors** (0.5%)
- **Test Coverage**: 55% (down from target of 70%+)

### Critical Issues
1. **Configuration Format Migration** - Tests expect v1 format but parser returns v2 format
2. **RML Parser Compatibility** - RML parser output doesn't match expected v1 schema
3. **Missing Generator Features** - v2 generators (RML, YARRRML) not fully integrated
4. **Broken Test Assumptions** - Tests written for old format need updates

---

## Test Failure Analysis

### Category 1: Configuration Format Issues (12 failures)

**Root Cause**: Tests written for v1 config format (`sheets[].class`, `sheets[].columns`) but parsers now return v2 format (`sheets[].row_resource`, `sheets[].properties`)

**Affected Tests**:
- `test_rml_parser.py::test_rml_parser_basic` - KeyError: 'class'
- `test_rml_parser.py::test_rml_parser_with_constants` - TypeError: string indices
- `test_rml_parser.py::test_rml_parser_multiple_triples_maps` - KeyError: 'class'
- `test_rml_generator.py::test_rml_roundtrip` - KeyError: 'class'
- `test_mortgage_example.py::TestMortgageExample::test_load_mortgage_config` - Format mismatch
- `test_mortgage_example.py::TestMortgageExample::test_parse_mortgage_data` - Format mismatch
- `test_mortgage_example.py::TestMortgageExample::test_build_rdf_graph` - Format mismatch
- `test_mortgage_example.py::TestMortgageExample::test_processing_report` - Format mismatch
- `test_mortgage_example.py::TestDataTransformations::test_decimal_transformation` - Format mismatch
- `test_mortgage_example.py::TestDataTransformations::test_date_transformation` - Format mismatch
- `test_mapping.py::TestMappingConfig::test_error_handling_enum` - Pydantic validation error
- `test_generator_workflow.py::TestGeneratorWorkflowComplete::test_full_workflow_employees` - Format mismatch

**Solution Required**: 
- Option A: Update all tests to expect v2 format
- Option B: Add v1→v2 migration layer in tests
- Option C: Make parsers support both v1 and v2 output (recommended)

---

### Category 2: Matcher Pipeline Issues (8 failures)

**Root Cause**: Recent optimization reduced matchers from 17→5, but tests expect old behavior

**Affected Tests**:
- `test_17_matchers_complete.py::test_all_17_matchers_available` - Assert expects 17, got 5
- `test_17_matchers_complete.py::test_evidence_quality_messy_data` - Insufficient matchers
- `test_17_matchers_complete.py::test_matcher_firing_rates` - Rates changed
- `test_matcher_pipeline.py::test_exact_pref_label_matcher` - Matcher behavior changed
- `test_matcher_pipeline.py::test_pipeline_match_all` - Expected match count wrong
- `test_datatype_matcher.py::test_integer_type_inference` - Inference logic changed
- `test_datatype_matcher.py::test_property_without_range` - Range handling changed
- `test_phase2_integration.py::test_phase2_pipeline_integration` - Pipeline structure changed

**Solution Required**:
- Update test expectations to match new 5-matcher pipeline
- Update documentation to reflect simplified pipeline
- Consider renaming `test_17_matchers_complete.py` to `test_5_matchers_complete.py`

---

### Category 3: Semantic Matcher Integration (5 failures)

**Root Cause**: Enhanced semantic matcher has different API/behavior

**Affected Tests**:
- `test_enhanced_semantic_matcher.py::test_basic_label_and_comment_usage` - API changed
- `test_enhanced_semantic_matcher.py::test_domain_aware_boost` - TypeError in boost logic
- `test_enhanced_semantic_matcher.py::test_threshold_respected` - TypeError in threshold
- `test_phase2_integration.py::test_semantic_with_phase2_integration` - Integration changed
- `test_generator_workflow.py::TestColumnMatchingWithSKOS::test_matches_multiple_hidden_labels` - Matching behavior changed

**Solution Required**:
- Fix type errors in enhanced semantic matcher
- Update test expectations for new behavior
- Ensure backward compatibility where possible

---

### Category 4: Generator Workflow Issues (4 failures)

**Root Cause**: Generator workflow changed with v2 format introduction

**Affected Tests**:
- `test_generator_workflow.py::TestGeneratorWorkflowComplete::test_workflow_with_linked_objects` - Objects handling changed
- `test_generator_workflow.py::TestMatchingPriority::test_matching_priority_order` - Priority logic changed
- `test_hierarchy_matcher.py::TestHierarchyMatcherIntegration::test_matcher_in_pipeline` - Integration broken
- Validation accuracy tests (3 failures)

**Solution Required**:
- Update generator tests for v2 format
- Verify linked objects/nested entities work correctly
- Update validation benchmarks

---

### Category 5: Coverage Gaps (No Test Coverage)

**Modules with 0% Coverage**:
- `config/v2_generator.py` (71 statements) - **NEW MODULE, NO TESTS**
- `config/yarrrml_generator.py` (89 statements) - **NEW MODULE, NO TESTS**
- `config/yarrrml_parser.py` (147 statements) - **NEW MODULE, NO TESTS**
- `emitter/columnwise_builder.py` (133 statements)
- `emitter/nt_streaming.py` (90 statements)
- `emitter/streaming_graph_builder.py` (144 statements)
- `cli/wizard.py` (329 statements)
- `cli/interactive_review.py` (191 statements)

**Critical Gap**: New v2 generators have NO test coverage!

---

## Project Structure Assessment

### ✅ **What's Good**

1. **Examples Directory** - Well organized:
   ```
   examples/mortgage/
   ├── config/          # Multiple config formats (inline, external, YARRRML)
   ├── data/            # CSV data with various sizes
   ├── ontology/        # OWL ontology
   ├── shapes/          # SHACL validation
   └── vocabulary/      # SKOS vocabularies
   ```

2. **Source Code Organization**:
   ```
   src/rdfmap/
   ├── cli/             # Command-line interface
   ├── config/          # Configuration loaders/generators
   ├── generator/       # AI mapping generation
   ├── emitter/         # RDF graph building
   ├── models/          # Data models
   ├── parsers/         # Data source parsers
   ├── validator/       # Validation logic
   └── transforms/      # Data transformations
   ```

3. **Documentation** - Comprehensive README with usage examples

### ❌ **What Needs Fixing**

1. **Test Organization** - Tests are flat, should be organized by module:
   ```
   tests/
   ├── unit/
   │   ├── test_config_loaders.py
   │   ├── test_generators.py
   │   └── test_parsers.py
   ├── integration/
   │   ├── test_full_workflow.py
   │   └── test_rml_roundtrip.py
   └── validation/
       └── test_accuracy.py
   ```

2. **Example Organization** - Missing examples for key features:
   ```
   examples/
   ├── basic_csv/           # Simple CSV → RDF (NEEDED)
   ├── json_nested/         # Nested JSON → RDF (NEEDED)
   ├── xml_complex/         # Complex XML → RDF (NEEDED)
   ├── mortgage/            # ✅ EXISTS
   └── multi_sheet_excel/   # Excel with relationships (NEEDED)
   ```

3. **Test Data** - Scattered across multiple directories:
   - `test_configs/` - Should be in `tests/fixtures/configs/`
   - `test_data/` - Should be in `tests/fixtures/data/`
   - `test_formats/` - Should be in `tests/fixtures/formats/`
   - `test_outputs/` - Should be in `tests/outputs/` (gitignored)

4. **Cleanup Needed**:
   - Keep: `uploads/` (used by RDF-Starchart UI, ignore in RDFMap)
   - Remove: `rml_conversion_output.ttl`, `rml_output.ttl` (test artifacts)
   - Remove: `build.log` (should be gitignored)
   - Remove: `test_alignment.json` (test artifact)
   - Note: Docker files are for **RDF-Starchart** (separate project), can coexist

---

## Feature Completeness Assessment

### ✅ **Complete Features** (Ready for v0.4.0)

1. **RML/YARRRML Support**
   - ✅ RML parser (Turtle format)
   - ✅ YARRRML parser
   - ✅ RML generator (Turtle, RDF/XML, N-Triples)
   - ✅ YARRRML generator
   - ✅ CLI support for all formats

2. **Data Format Support**
   - ✅ CSV
   - ✅ Excel (XLSX)
   - ✅ TSV
   - ✅ JSON (basic and nested)
   - ✅ XML (basic structures)

3. **Output Formats**
   - ✅ Turtle (.ttl)
   - ✅ N-Triples (.nt)
   - ✅ RDF/XML (.rdf, .xml)
   - ⚠️ JSON-LD (.jsonld) - Partial support

4. **Core Features**
   - ✅ AI-powered semantic matching (5 optimized matchers)
   - ✅ Confidence scoring and evidence tracking
   - ✅ SKOS vocabulary integration
   - ✅ OWL ontology analysis
   - ✅ Data type inference and validation
   - ✅ IRI template generation
   - ✅ Nested entity support

### ⚠️ **Incomplete Features** (Block v0.4.0)

1. **V2 Format Integration** - **CRITICAL**
   - ❌ Tests not updated for v2 format
   - ❌ Migration path from v1→v2 not tested
   - ❌ Documentation doesn't explain format differences
   - ❌ No validation that v2 configs work end-to-end

2. **RDF-Star Support** - **MENTIONED BUT NOT IMPLEMENTED**
   - ❌ No RDF-Star triple generation
   - ❌ No RDF-Star parsing
   - ❌ Not documented anywhere except user conversation

3. **Named Individuals** - **PARTIALLY WORKING**
   - ⚠️ Support in parser but validation fails
   - ⚠️ Need list support for multiple classes per entity

4. **Complex Nested Structures** - **NEEDS MORE TESTING**
   - ⚠️ Deeply nested JSON (3+ levels)
   - ⚠️ XML with attributes and mixed content
   - ⚠️ Multiple join conditions

5. **Performance Optimization** - **MENTIONED BUT NOT TESTED**
   - ⚠️ Single-pass RML processing
   - ❌ No benchmarks for large datasets (500k+ rows)
   - ❌ No streaming mode tests

### 🔮 **Future Features** (Not for v0.4.0)

1. **RDF-Star** - Requires design and implementation
2. **GraphQL Integration** - Not started
3. **SPARQL Endpoint Output** - Not started
4. **Web UI** - Available separately as **RDF-Starchart** (Docker/full-stack solution)

**Note**: Docker support exists but is for the **RDF-Starchart** project (full-stack UI), not the **RDFMap** engine (PyPI package)

---

## Recommendations for v0.4.0 Release

### 🚨 **MUST FIX (Blockers)**

1. **Fix All Test Failures** - Target: 0 failures
   - Update tests for v2 format
   - Fix matcher pipeline tests
   - Fix semantic matcher type errors

2. **Add Tests for New Modules** - Target: 70%+ coverage
   - `config/v2_generator.py`
   - `config/yarrrml_generator.py`
   - `config/yarrrml_parser.py`
   - Integration tests for RML/YARRRML round-trip

3. **Create Clean Example Suite**:
   ```
   examples/
   ├── 01_basic_csv/
   │   ├── README.md
   │   ├── data.csv
   │   ├── ontology.ttl
   │   └── config.yaml
   ├── 02_json_nested/
   ├── 03_xml_complex/
   ├── 04_multi_sheet_excel/
   └── 05_mortgage_complete/ (existing mortgage example)
   ```

4. **Clean Up Repository**:
   - Move test fixtures to `tests/fixtures/`
   - Remove artifact files
   - Update `.gitignore`

5. **Update Documentation**:
   - Document v1 vs v2 config format
   - Add migration guide
   - Update README with v0.4.0 features
   - Add UPGRADE_GUIDE.md

### ⚡ **SHOULD FIX (Important)**

6. **Reorganize Tests**:
   - Create `tests/unit/`, `tests/integration/`, `tests/validation/`
   - Separate fast tests from slow tests
   - Add pytest markers

7. **Add Missing Examples**:
   - JSON with 3+ nesting levels
   - XML with complex structures
   - Multi-sheet Excel with FK relationships

8. **Performance Benchmarks**:
   - Test with 100k, 500k, 1M rows
   - Document memory usage
   - Add performance regression tests

### 💡 **NICE TO HAVE (Optional)**

9. **Improve CLI UX**:
   - Better progress bars
   - Clearer error messages
   - `--dry-run` mode improvements

10. **Add Validation Suite**:
    - SHACL validation examples
    - OWL consistency checking examples

---

## Proposed Timeline

### Week 1: Fix Critical Test Failures
- Days 1-2: Fix configuration format issues (12 tests)
- Days 3-4: Fix matcher pipeline issues (8 tests)
- Day 5: Fix semantic matcher issues (5 tests)

### Week 2: Add Missing Test Coverage
- Days 1-2: Write tests for v2_generator, yarrrml_generator, yarrrml_parser
- Days 3-4: Write integration tests for RML/YARRRML round-trip
- Day 5: Code review and quality check

### Week 3: Examples and Documentation
- Days 1-2: Create 4 new example projects
- Days 3-4: Update documentation (README, CHANGELOG, UPGRADE_GUIDE)
- Day 5: Clean up repository, final testing

### Week 4: Release Preparation
- Days 1-2: Final testing on clean venv
- Day 3: Build and test PyPI package locally
- Day 4: Release to TestPyPI, verify install
- Day 5: Release to PyPI, announce v0.4.0

**Total Estimated Time**: 4 weeks to production-ready v0.4.0

---

## Quality Gates for Release

### Must Pass Before Release:

- [ ] **All tests passing** (0 failures, 0 errors)
- [ ] **Test coverage ≥ 70%** for core modules
- [ ] **All new features have tests**
- [ ] **Examples run successfully**
- [ ] **Documentation updated**
- [ ] **CHANGELOG.md updated** with v0.4.0 changes
- [ ] **Clean `git status`** (no uncommitted changes, artifacts removed)
- [ ] **Version bumped** in `pyproject.toml`
- [ ] **Builds successfully** with `python -m build`
- [ ] **Installs cleanly** in fresh venv
- [ ] **CLI commands work** after install

---

## Risk Assessment

### 🔴 **HIGH RISK**

1. **Breaking Changes in v2 Format** - Users upgrading from v0.3.0 may have broken configs
   - **Mitigation**: Add v1→v2 migration script, clear docs

2. **Test Suite Instability** - 31 failing tests indicates significant regression
   - **Mitigation**: Fix all tests before any new features

### 🟡 **MEDIUM RISK**

3. **Performance with Large Datasets** - Not tested at scale
   - **Mitigation**: Add benchmark tests, document limitations

4. **RML/YARRRML Interoperability** - May not work with all RML tools
   - **Mitigation**: Test with RMLMapper, document known issues

### 🟢 **LOW RISK**

5. **Documentation Completeness** - README is comprehensive
6. **Core Features Stable** - Mapping generator works well

---

## Conclusion

**Current Status**: 🔴 **NOT READY FOR RELEASE**

**Recommendation**: **DO NOT release v0.4.0 until all test failures are fixed** and new modules have adequate test coverage.

**Next Steps**:
1. Create plan to fix 31 test failures
2. Add tests for untested modules (v2_generator, YARRRML)
3. Create clean example suite
4. Update documentation
5. **THEN** proceed with v0.4.0 release

**Estimated Time to Ready**: 3-4 weeks of focused work

---

## Alternative: Emergency Patch Release

If urgent bug fixes are needed for v0.3.0 users:

**v0.3.1 (Patch Release)**:
- Fix critical bugs only
- No new features
- No breaking changes
- Can release in 1 week

**v0.4.0 (Major Release)**:
- Complete all items above
- Release in 4 weeks
- Proper testing and documentation

---

**Assessment Prepared By**: AI Code Assistant  
**Date**: December 9, 2025  
**Review Status**: Awaiting human review and decision

