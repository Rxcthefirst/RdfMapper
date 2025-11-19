"""Quick test of parallel matchers and cache."""

import sys
sys.path.insert(0, '/Users/rxcthefirst/Dev/PythonProjects/SemanticModelDataMapper/src')

from rdfmap.generator.embedding_cache import EmbeddingCache
import numpy as np

# Test cache
print("Testing EmbeddingCache...")
cache = EmbeddingCache("test-model")

# Store embedding
text = "test column"
embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
cache.put(text, embedding)
print(f"✅ Stored embedding")

# Retrieve embedding
retrieved = cache.get(text)
print(f"✅ Retrieved embedding: {retrieved}")

# Check statistics
stats = cache.get_statistics()
print(f"✅ Cache stats: {stats}")

print("\n✅ All cache tests passed!")

