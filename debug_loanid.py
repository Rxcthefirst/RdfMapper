#!/usr/bin/env python3
"""Debug why LoanID doesn't match loanNumber."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from rdfmap.generator.mapping_generator import MappingGenerator, GeneratorConfig

ont = 'examples/mortgage/ontology/mortgage.ttl'
data = 'examples/mortgage/data/loans.csv'
config = GeneratorConfig(base_iri='http://example.org/', min_confidence=0.5)

gen = MappingGenerator(ont, data, config, use_semantic_matching=True)
cls = gen._auto_detect_class()
props = gen.ontology.get_datatype_properties(cls.uri)

# Get the semantic matcher
sem_matcher = None
for m in gen.matcher_pipeline.matchers:
    if m.name() == 'SemanticSimilarityMatcher':
        sem_matcher = m
        break

if sem_matcher:
    col = gen.data_source.get_analysis('LoanID')
    print("Computing embedding cosine similarities for LoanID vs properties...\n")
    if sem_matcher._embeddings_matcher:
        pairs = sem_matcher._embeddings_matcher.score_all(col, props)
        # Sort descending by similarity
        pairs.sort(key=lambda x: x[1], reverse=True)
        print("Top similarities:")
        for prop, score in pairs[:10]:
            label = prop.label or str(prop.uri).split('#')[-1]
            print(f"  {label:30s}  {score:.3f}")
    else:
        print("Embeddings are DISABLED or failed to initialize.")
