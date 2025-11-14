"""Quick debug of semantic matcher."""

import sys
sys.path.insert(0, 'src')

from rdfmap.generator.semantic_matcher import SemanticMatcher
from rdfmap.generator.ontology_analyzer import OntologyProperty
from rdfmap.generator.data_analyzer import DataFieldAnalysis
from rdflib import URIRef

matcher = SemanticMatcher()

# Create test column
column = DataFieldAnalysis("customer_id", "customer_id")
column.sample_values = ["CUST-001", "CUST-002", "CUST-003"]
column.inferred_type = "string"

# Create test properties
props = [
    OntologyProperty(
        URIRef("http://ex.org/clientIdentifier"),
        label="Client Identifier",
        comment="Unique identifier for a client customer account"
    ),
    OntologyProperty(
        URIRef("http://ex.org/productCode"),
        label="Product Code",
        comment="Code identifying a product in the catalog"
    )
]

print("Testing semantic matcher...")
print(f"Column: {column.name}")
print(f"Sample values: {column.sample_values}")
print(f"Type: {column.inferred_type}")
print()

# Try with different thresholds
for threshold in [0.3, 0.4, 0.5, 0.6]:
    result = matcher.match(column, props, threshold=threshold)
    if result:
        prop, score = result
        print(f"Threshold {threshold}: MATCH! {prop.label} (score: {score:.3f})")
    else:
        print(f"Threshold {threshold}: No match")

# Show embeddings
print("\nColumn embedding:")
col_emb = matcher.embed_column(column)
print(f"Shape: {col_emb.shape}")

print("\nProperty embeddings:")
for prop in props:
    prop_emb = matcher.embed_property(prop)
    print(f"{prop.label}: shape {prop_emb.shape}")

    # Compute similarity manually
    from sklearn.metrics.pairwise import cosine_similarity
    similarity = cosine_similarity([col_emb], [prop_emb])[0][0]
    print(f"  Similarity to column: {similarity:.3f}")

