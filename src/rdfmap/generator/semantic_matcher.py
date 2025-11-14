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

