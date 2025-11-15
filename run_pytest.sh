#!/bin/bash
cd /Users/rxcthefirst/Dev/PythonProjects/SemanticModelDataMapper
python -m pytest tests/test_multisheet_support.py::TestMultiSheetAnalyzer::test_relationship_detection -xvs 2>&1 | tee /tmp/pytest_output.txt
echo "Exit code: $?"

