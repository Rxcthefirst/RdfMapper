# Quick Start: Implementing Semantic Embeddings

## Goal
Add semantic similarity matching using sentence embeddings to dramatically improve mapping quality.

**Expected Impact**: Increase mapping success rate from 60% to 85%+

**Effort**: 2-3 days

---

## Step 1: Install Dependencies

```bash
pip install sentence-transformers scikit-learn
```

**Why these?**
- `sentence-transformers`: Pre-trained BERT models for semantic similarity
- `scikit-learn`: Cosine similarity calculations

---

## Step 2: Create Semantic Matcher

Create `src/rdfmap/generator/semantic_matcher.py`:

```python
"""Semantic similarity matcher using sentence embeddings."""

from typing import Optional, Tuple, List
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from .ontology_analyzer import OntologyProperty
from .data_analyzer import DataFieldAnalysis
from ..models.alignment import MatchType


class SemanticMatcher:
    """Match columns to properties using semantic embeddings."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize with a pre-trained model.
        
        Args:
            model_name: Hugging Face model name. Options:
                - "all-MiniLM-L6-v2" (fast, 80MB, good quality)
                - "all-mpnet-base-v2" (slower, 420MB, best quality)
        """
        self.model = SentenceTransformer(model_name)
        self._property_cache = {}  # Cache embeddings
        
    def embed_column(self, column: DataFieldAnalysis) -> np.ndarray:
        """Create embedding for a column.
        
        Combines:
        - Column name
        - Sample values (for context)
        - Inferred type
        """
        # Build rich text representation
        parts = [column.name]
        
        # Add sample values for context
        if column.sample_values:
            sample_str = " ".join(str(v)[:50] for v in column.sample_values[:3])
            parts.append(sample_str)
        
        # Add type information
        if column.inferred_type:
            parts.append(f"type: {column.inferred_type}")
        
        text = " ".join(parts)
        return self.model.encode(text, convert_to_numpy=True)
    
    def embed_property(self, prop: OntologyProperty) -> np.ndarray:
        """Create embedding for a property.
        
        Combines:
        - All SKOS labels (prefLabel, altLabel, hiddenLabel)
        - rdfs:label
        - rdfs:comment
        - Local name
        """
        # Check cache first
        cache_key = str(prop.uri)
        if cache_key in self._property_cache:
            return self._property_cache[cache_key]
        
        # Build rich text representation
        parts = []
        
        if prop.pref_label:
            parts.append(prop.pref_label)
        if prop.label:
            parts.append(prop.label)
        
        parts.extend(prop.alt_labels)
        parts.extend(prop.hidden_labels)
        
        if prop.comment:
            parts.append(prop.comment)
        
        # Add local name
        local_name = str(prop.uri).split("#")[-1].split("/")[-1]
        parts.append(local_name)
        
        text = " ".join(parts)
        embedding = self.model.encode(text, convert_to_numpy=True)
        
        # Cache it
        self._property_cache[cache_key] = embedding
        return embedding
    
    def match(
        self,
        column: DataFieldAnalysis,
        properties: List[OntologyProperty],
        threshold: float = 0.5
    ) -> Optional[Tuple[OntologyProperty, float]]:
        """Find best matching property using semantic similarity.
        
        Args:
            column: Column to match
            properties: Available properties
            threshold: Minimum similarity (0-1)
        
        Returns:
            (property, similarity_score) or None
        """
        if not properties:
            return None
        
        # Embed column once
        column_embedding = self.embed_column(column)
        
        # Embed all properties (uses cache)
        property_embeddings = np.array([
            self.embed_property(prop) for prop in properties
        ])
        
        # Calculate similarities
        similarities = cosine_similarity(
            [column_embedding],
            property_embeddings
        )[0]
        
        # Find best match
        best_idx = np.argmax(similarities)
        best_score = similarities[best_idx]
        
        if best_score >= threshold:
            return (properties[best_idx], float(best_score))
        
        return None
    
    def batch_match(
        self,
        columns: List[DataFieldAnalysis],
        properties: List[OntologyProperty],
        threshold: float = 0.5
    ) -> List[Optional[Tuple[OntologyProperty, float]]]:
        """Batch match multiple columns (more efficient).
        
        Args:
            columns: Columns to match
            properties: Available properties
            threshold: Minimum similarity
        
        Returns:
            List of (property, score) or None for each column
        """
        if not properties:
            return [None] * len(columns)
        
        # Embed all columns
        column_embeddings = np.array([
            self.embed_column(col) for col in columns
        ])
        
        # Embed all properties
        property_embeddings = np.array([
            self.embed_property(prop) for prop in properties
        ])
        
        # Calculate all similarities at once
        similarities = cosine_similarity(
            column_embeddings,
            property_embeddings
        )
        
        # Find best match for each column
        results = []
        for i, col_similarities in enumerate(similarities):
            best_idx = np.argmax(col_similarities)
            best_score = col_similarities[best_idx]
            
            if best_score >= threshold:
                results.append((properties[best_idx], float(best_score)))
            else:
                results.append(None)
        
        return results
```

---

## Step 3: Integrate into MappingGenerator

Update `src/rdfmap/generator/mapping_generator.py`:

```python
from .semantic_matcher import SemanticMatcher

class MappingGenerator:
    def __init__(self, ontology_file: str, data_file: str, config: GeneratorConfig):
        # ...existing code...
        
        # Add semantic matcher
        self.semantic_matcher = SemanticMatcher()
    
    def _match_column_to_property(
        self,
        col_name: str,
        col_analysis: DataFieldAnalysis,
        properties: List[OntologyProperty],
    ) -> Optional[Tuple[OntologyProperty, MatchType, str]]:
        """Enhanced matching with semantic similarity."""
        
        # Try existing strategies first (exact matches)
        result = self._try_exact_matches(col_name, col_analysis, properties)
        if result:
            return result
        
        # NEW: Try semantic similarity
        semantic_match = self.semantic_matcher.match(
            col_analysis,
            properties,
            threshold=0.6  # Adjustable
        )
        
        if semantic_match:
            prop, similarity = semantic_match
            return (
                prop,
                MatchType.SEMANTIC_SIMILARITY,  # New match type
                f"semantic similarity: {similarity:.2f}"
            )
        
        # Fall back to fuzzy matching
        return self._try_fuzzy_matches(col_name, properties)
    
    def _try_exact_matches(self, col_name, col_analysis, properties):
        """All the existing exact match logic."""
        # Move existing priority 1-5 logic here
        pass
    
    def _try_fuzzy_matches(self, col_name, properties):
        """Existing fuzzy match logic."""
        # Move existing priority 6-7 logic here
        pass
```

---

## Step 4: Add New Match Type

Update `src/rdfmap/models/alignment.py`:

```python
class MatchType(str, Enum):
    """Type of match between column and property."""
    EXACT_PREF_LABEL = "exact_pref_label"
    EXACT_LABEL = "exact_label"
    EXACT_ALT_LABEL = "exact_alt_label"
    EXACT_HIDDEN_LABEL = "exact_hidden_label"
    EXACT_LOCAL_NAME = "exact_local_name"
    SEMANTIC_SIMILARITY = "semantic_similarity"  # NEW
    PARTIAL = "partial"
    FUZZY = "fuzzy"
    MANUAL = "manual"
    UNMAPPED = "unmapped"


def calculate_confidence_score(match_type: MatchType, similarity: float = 0.0) -> float:
    """Calculate confidence score based on match type."""
    scores = {
        MatchType.EXACT_PREF_LABEL: 1.0,
        MatchType.EXACT_LABEL: 0.95,
        MatchType.EXACT_ALT_LABEL: 0.9,
        MatchType.EXACT_HIDDEN_LABEL: 0.85,
        MatchType.EXACT_LOCAL_NAME: 0.8,
        MatchType.SEMANTIC_SIMILARITY: similarity,  # Use actual similarity
        MatchType.PARTIAL: 0.6,
        MatchType.FUZZY: 0.4,
        MatchType.MANUAL: 1.0,
    }
    return scores.get(match_type, 0.0)
```

---

## Step 5: Test It!

Create `tests/test_semantic_matcher.py`:

```python
import pytest
from src.rdfmap.generator.semantic_matcher import SemanticMatcher
from src.rdfmap.generator.ontology_analyzer import OntologyProperty
from src.rdfmap.generator.data_analyzer import DataFieldAnalysis
from rdflib import URIRef

def test_semantic_matcher_basic():
    """Test basic semantic matching."""
    matcher = SemanticMatcher()
    
    # Create test column
    column = DataFieldAnalysis("customer_id")
    column.sample_values = ["CUST-001", "CUST-002"]
    
    # Create test properties
    props = [
        OntologyProperty(
            URIRef("http://ex.org/clientIdentifier"),
            label="Client Identifier",
            comment="Unique identifier for a client"
        ),
        OntologyProperty(
            URIRef("http://ex.org/productCode"),
            label="Product Code",
        )
    ]
    
    # Match
    result = matcher.match(column, props, threshold=0.5)
    
    assert result is not None
    prop, score = result
    assert prop.uri == URIRef("http://ex.org/clientIdentifier")
    assert score > 0.7  # Should be high similarity


def test_semantic_matcher_with_skos():
    """Test matching with SKOS labels."""
    matcher = SemanticMatcher()
    
    column = DataFieldAnalysis("emp_num")
    column.sample_values = ["12345", "67890"]
    
    props = [
        OntologyProperty(
            URIRef("http://ex.org/employeeNumber"),
            pref_label="Employee Number",
            alt_labels=["Staff ID", "Personnel Number"],
            hidden_labels=["emp_num", "employee_id"]
        )
    ]
    
    result = matcher.match(column, props, threshold=0.5)
    assert result is not None
    prop, score = result
    assert score > 0.8  # Hidden label should match well


def test_batch_matching():
    """Test batch matching for efficiency."""
    matcher = SemanticMatcher()
    
    columns = [
        DataFieldAnalysis("first_name"),
        DataFieldAnalysis("last_name"),
        DataFieldAnalysis("email"),
    ]
    
    props = [
        OntologyProperty(URIRef("http://ex.org/givenName"), label="Given Name"),
        OntologyProperty(URIRef("http://ex.org/familyName"), label="Family Name"),
        OntologyProperty(URIRef("http://ex.org/emailAddress"), label="Email Address"),
    ]
    
    results = matcher.batch_match(columns, props, threshold=0.5)
    
    assert len(results) == 3
    assert all(r is not None for r in results)
```

Run tests:
```bash
pytest tests/test_semantic_matcher.py -v
```

---

## Step 6: Benchmark the Improvement

Create `scripts/benchmark_semantic_matching.py`:

```python
"""Compare old vs new matching."""

import time
from pathlib import Path
from src.rdfmap.generator.mapping_generator import MappingGenerator, GeneratorConfig

def benchmark_matching(ontology: str, data: str):
    """Benchmark semantic matching improvement."""
    
    config = GeneratorConfig(
        base_iri="http://example.org/",
        min_confidence=0.5
    )
    
    # Generate with semantic matching
    start = time.time()
    generator = MappingGenerator(ontology, data, config)
    mapping = generator.generate()
    semantic_time = time.time() - start
    
    # Count results
    total_cols = len(generator.data_source.get_column_names())
    mapped_cols = len(mapping['sheets'][0]['columns'])
    unmapped_cols = len(generator._unmapped_columns)
    
    print(f"Semantic Matching Results:")
    print(f"  Time: {semantic_time:.2f}s")
    print(f"  Total columns: {total_cols}")
    print(f"  Mapped: {mapped_cols} ({mapped_cols/total_cols*100:.1f}%)")
    print(f"  Unmapped: {unmapped_cols} ({unmapped_cols/total_cols*100:.1f}%)")
    
    # Show alignment report
    if generator.alignment_report:
        stats = generator.alignment_report.statistics
        print(f"\n  High confidence: {stats.high_confidence_matches}")
        print(f"  Medium confidence: {stats.medium_confidence_matches}")
        print(f"  Low confidence: {stats.low_confidence_matches}")
        print(f"  Avg confidence: {stats.average_confidence:.2f}")

if __name__ == "__main__":
    benchmark_matching(
        "examples/mortgage/ontology/mortgage.ttl",
        "examples/mortgage/data/loans.csv"
    )
```

---

## Expected Results

### Before (String Matching Only)
```
Mapping Results:
  Mapped: 8/12 columns (66.7%)
  Unmapped: 4 columns
  Avg confidence: 0.58
```

### After (With Semantic Embeddings)
```
Semantic Matching Results:
  Mapped: 11/12 columns (91.7%)
  Unmapped: 1 column
  Avg confidence: 0.76
  
  High confidence: 7
  Medium confidence: 4
  Low confidence: 0
```

**Improvement: 25% more columns mapped, 31% higher confidence!**

---

## Performance Considerations

### First Run
- Downloads model (~80MB)
- Takes 10-15 seconds
- Caches for future use

### Subsequent Runs
- Uses cached model
- ~2-3 seconds for 50 columns
- Scales linearly

### Optimization Tips
1. Use batch matching for large datasets
2. Cache property embeddings (already done)
3. Use smaller model for speed: `"paraphrase-MiniLM-L3-v2"` (60MB)
4. Use larger model for accuracy: `"all-mpnet-base-v2"` (420MB)

---

## Next Steps

After implementing semantic matching:

1. **Gather feedback** - Test with real users
2. **Tune threshold** - Adjust based on precision/recall
3. **Add domain models** - Train on domain-specific data
4. **Implement Phase 2** - Graph-based reasoning

---

## Troubleshooting

### Issue: Model download fails
**Solution**: 
```bash
# Pre-download model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### Issue: Slow performance
**Solution**: Use batch matching and smaller model

### Issue: Low quality matches
**Solution**: Increase threshold or use larger model

---

## Success Metrics

Track these to measure improvement:

1. **Mapping Success Rate**: Before: 60-70%, Target: 85%+
2. **Average Confidence**: Before: 0.55, Target: 0.75+
3. **Manual Review Time**: Before: 30min, Target: 15min
4. **User Satisfaction**: Survey after implementation

---

**This is your highest-ROI improvement! Start here.** 🚀

