#!/usr/bin/env python3
"""Simple test of alignment reporter - standalone version."""

import sys
sys.path.insert(0, 'src')

from rdfmap.generator.alignment_reporter import AlignmentReporter, ColumnMatch

print("="*80)
print("Testing Alignment Reporter (Standalone)")
print("="*80)

# Create reporter
reporter = AlignmentReporter()

# Set metadata
reporter.set_metadata(
    data_source="examples/mortgage/data/loans.csv",
    ontology="examples/mortgage/ontology/mortgage.ttl",
    target_class="MortgageLoan",
    generation_time_seconds=1.23
)

# Add some sample matches
reporter.add_match(
    column_name="LoanID",
    matched_property="ex:loanNumber",
    matched_property_label="loan number",
    confidence=0.95,
    match_type="EXACT_LABEL",
    matched_via="exact match",
    data_type="xsd:string",
    is_required=True
)

reporter.add_match(
    column_name="Principal",
    matched_property="ex:principalAmount",
    matched_property_label="principal amount",
    confidence=0.92,
    match_type="SEMANTIC",
    matched_via="semantic similarity",
    data_type="xsd:integer",
    is_required=True
)

reporter.add_match(
    column_name="Status",
    matched_property="ex:loanStatus",
    matched_property_label="loan status",
    confidence=0.82,
    match_type="FUZZY",
    matched_via="fuzzy match",
    alternatives=[("ex:status", 0.78), ("ex:currentStatus", 0.75)],
    data_type="xsd:string",
    is_required=True
)

reporter.add_match(
    column_name="InternalCode",
    data_type="xsd:string",
    sample_values=["IC-001", "IC-002"],
    is_required=False
)

# Finalize
report = reporter.finalize()

print(f"\n✓ Report created with {report.total_columns} columns")
print(f"  Mapped: {report.mapped_columns}")
print(f"  Success rate: {report.mapping_success_rate:.1f}%")
print(f"  Avg confidence: {report.average_confidence:.2f}")

# Terminal output
print("\n" + "="*80)
print("TERMINAL OUTPUT")
print("="*80)
output = reporter.to_terminal(show_details=True)
print(output)

# Save reports
reporter.to_json("test_alignment_report.json")
reporter.to_html("test_alignment_report.html")

print("✓ JSON report saved to: test_alignment_report.json")
print("✓ HTML report saved to: test_alignment_report.html")
print("\n✓ All tests passed!")

