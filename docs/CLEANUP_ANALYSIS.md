# Root Directory Cleanup Analysis

**Date:** November 15, 2025

## Scripts Found in Root Directory

### Debug Scripts (Need to move to scripts/)
1. `check_context.py` - Context checking utility
2. `debug_column_mismatch.py` - Column mismatch debugging
3. `debug_generator.py` - Generator debugging
4. `debug_json.py` - JSON parsing debugging
5. `debug_matchers.py` - Matchers debugging
6. `debug_objects.py` - Object handling debugging
7. `debug_ontology.py` - Ontology loading debugging
8. `debug_parser_conversion.py` - Parser conversion debugging
9. `debug_rdf.py` - RDF generation debugging

### Demo Scripts (Need to move to scripts/)
10. `demo_generator.py` - Generator demonstration
11. `demonstrate_ontology_vs_import.py` - Ontology vs import demonstration

### Test Scripts (Need proper pytest tests)
12. `test_alignment_report.py` - Alignment report testing
13. `test_alignment_reporter_standalone.py` - Standalone alignment reporter
14. `test_enhanced_alignment.py` - Enhanced alignment testing
15. `test_enhanced_json.py` - Enhanced JSON testing
16. `test_formatter_templates.py` - Formatter templates testing
17. `test_imports.py` - Imports testing
18. `test_imports_config.py` - Imports config testing
19. `test_interactive_review.py` - Interactive review testing
20. `test_json_parser.py` - JSON parser testing
21. `test_multisheet.py` - Multi-sheet testing
22. `test_object_datatypes.py` - Object datatypes testing
23. `test_templates.py` - Templates testing

### Data Generation Scripts (Keep or move?)
24. `create_multisheet_testdata.py` - Test data generator
25. `streaming_benchmark.py` - Benchmark script

### Configuration Files (Keep in root)
- `my_config.yaml`, `my_mapping.yaml`, etc. - User config examples

---

## Action Plan

### Phase 1: Move Debug Scripts to scripts/
Move all debug_*.py files to scripts/debug/ subdirectory

### Phase 2: Move Demo Scripts to scripts/
Move demo*.py and demonstrate*.py to scripts/

### Phase 3: Move Test Data Generators
Move create_*_testdata.py and benchmarks to scripts/

### Phase 4: Convert Test Scripts to Proper Pytest
For each test_*.py in root:
1. Analyze what it tests
2. Create proper pytest in tests/ directory
3. Move original to scripts/ as demo

### Phase 5: Organize Scripts Directory
Create subdirectories:
- scripts/debug/ - Debug utilities
- scripts/demo/ - Demo scripts
- scripts/benchmarks/ - Performance tests
- scripts/utils/ - Utility scripts

---

## Tests to Create

Based on the test scripts found, we need pytest tests for:

1. **Alignment Report** (`tests/test_alignment_report.py` - already exists!)
2. **Enhanced Alignment** - Need to create
3. **JSON Parser** - Need to create
4. **Multi-sheet Support** - Need to create
5. **Templates Library** - Need to create
6. **Interactive Review** - Need to create
7. **Imports/Config** - Need to create
8. **Formatter Templates** - Need to create
9. **Object Datatypes** - Need to create

---

## Priority Order

### High Priority (Core functionality)
1. JSON Parser tests
2. Multi-sheet support tests
3. Object datatypes tests

### Medium Priority (User-facing features)
4. Templates library tests
5. Interactive review tests
6. Formatter templates tests

### Lower Priority (Already have some coverage)
7. Enhanced alignment tests
8. Imports/config tests

