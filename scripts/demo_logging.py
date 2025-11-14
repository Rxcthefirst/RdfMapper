"""Demo script showing enhanced logging in action."""

import sys
import logging
sys.path.insert(0, 'src')

from rdfmap.generator.matchers import create_default_pipeline
from rdfmap.generator.ontology_analyzer import OntologyProperty
from rdfmap.generator.data_analyzer import DataFieldAnalysis
from rdfmap.generator.matching_logger import configure_logging
from rdflib import URIRef

# Configure logging
configure_logging(level='DEBUG')

print("=" * 70)
print("Enhanced Logging Demo")
print("=" * 70)
print()

# Create pipeline with logging enabled
pipeline = create_default_pipeline(
    use_semantic=False,  # Skip semantic to keep it fast
    enable_logging=True
)

# Test columns
columns = [
    DataFieldAnalysis("loan_amount", "loan_amount"),
    DataFieldAnalysis("borrower_id", "borrower_id"),
    DataFieldAnalysis("unknown_column", "unknown_column"),
]

columns[0].sample_values = [250000, 300000, 450000]
columns[0].inferred_type = "integer"

columns[1].sample_values = ["B123", "B456", "B789"]
columns[1].inferred_type = "string"

columns[2].sample_values = ["ABC", "DEF", "GHI"]
columns[2].inferred_type = "string"

# Test properties
props = [
    OntologyProperty(
        URIRef("http://ex.org/loanAmount"),
        label="Loan Amount",
        range_type=URIRef("http://www.w3.org/2001/XMLSchema#decimal")
    ),
    OntologyProperty(
        URIRef("http://ex.org/hasBorrower"),
        label="has Borrower",
        is_object_property=True
    ),
]

# Log pipeline start
if pipeline.logger:
    pipeline.logger.log_pipeline_start(len(columns), len(props), len(pipeline.matchers))

# Match each column
for i, column in enumerate(columns, 1):
    if pipeline.logger:
        pipeline.logger.log_column_start(column, i, len(columns))
        pipeline.logger.increment_columns_processed()

    result = pipeline.match(column, props)

    if not result:
        print(f"  ⚠️  No match found for '{column.name}'")
    print()

# Log summary
if pipeline.logger:
    pipeline.logger.log_pipeline_summary()

    # Get stats
    stats = pipeline.logger.get_stats()
    print(f"\nCollected Stats: {stats}")

print("\n" + "=" * 70)
print("Demo Complete!")
print("=" * 70)

