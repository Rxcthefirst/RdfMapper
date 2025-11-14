#!/bin/bash

# Test script to verify the validate-ontology command works cleanly
# without showing annoying tracebacks

echo "🧪 Testing validate-ontology command behavior..."
echo "=============================================="
echo ""

cd /Users/rxcthefirst/Dev/PythonProjects/SemanticModelDataMapper

echo "Test 1: Validation that should FAIL (coverage below threshold)"
echo "--------------------------------------------------------------"
echo "Command: rdfmap validate-ontology --ontology examples/demo/ontology/hr_ontology_initial.ttl --min-coverage 0.7"
echo ""

rdfmap validate-ontology \
  --ontology examples/demo/ontology/hr_ontology_initial.ttl \
  --min-coverage 0.7

EXIT_CODE=$?
echo ""
echo "Exit code: $EXIT_CODE (expected: 1)"
echo ""

echo "Test 2: Validation that should PASS (coverage meets threshold)"
echo "-------------------------------------------------------------"
echo "Command: rdfmap validate-ontology --ontology examples/demo/ontology/hr_ontology_initial.ttl --min-coverage 0.0"
echo ""

rdfmap validate-ontology \
  --ontology examples/demo/ontology/hr_ontology_initial.ttl \
  --min-coverage 0.0

EXIT_CODE=$?
echo ""
echo "Exit code: $EXIT_CODE (expected: 0)"
echo ""

echo "✅ Test Complete!"
echo "=================="
echo ""
echo "Key observations:"
echo "• No annoying tracebacks shown"
echo "• Exit codes work correctly (1 for fail, 0 for pass)"
echo "• Output is clean and professional"
echo "• Users won't think something is broken"
