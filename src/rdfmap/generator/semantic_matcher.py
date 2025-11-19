"""Semantic similarity matcher using sentence embeddings with Polars-integrated cache."""

from typing import Optional, Tuple, List
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from .ontology_analyzer import OntologyProperty
from .data_analyzer import DataFieldAnalysis
from .embedding_cache import EmbeddingCache


class SemanticMatcher:
    """Match columns to properties using semantic embeddings with blazingly fast caching."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", use_cache: bool = True):
        """Initialize with a pre-trained model.

        Args:
            model_name: Hugging Face model name. Options:
                - "all-MiniLM-L6-v2" (fast, 80MB, good quality)
                - "all-mpnet-base-v2" (slower, 420MB, best quality)
            use_cache: Enable Polars-integrated embedding cache (default True)
        """
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        self._property_cache = {}  # Legacy cache for backward compatibility

        # Polars-integrated cache for blazingly fast operations
        self.use_cache = use_cache
        self._embedding_cache = EmbeddingCache(model_name) if use_cache else None

    def _encode_with_cache(self, text: str) -> np.ndarray:
        """Encode text with cache lookup.

        Args:
            text: Text to encode

        Returns:
            Embedding vector
        """
        if not self.use_cache or self._embedding_cache is None:
            return self.model.encode(text, convert_to_numpy=True)

        # Try cache first (blazingly fast!)
        cached = self._embedding_cache.get(text)
        if cached is not None:
            return cached

        # Cache miss - generate and store
        embedding = self.model.encode(text, convert_to_numpy=True)
        self._embedding_cache.put(text, embedding)
        return embedding

    def embed_column(self, column: DataFieldAnalysis) -> np.ndarray:
        """Create embedding for a column.

        Combines:
        - Column name
        - Sample values (for context)
        - Inferred type
        """
        # Build rich text representation
        parts = [column.name]

        # Identifier pattern enrichment
        name_lower = column.name.lower()
        if name_lower.endswith('id') or name_lower.endswith('_id') or name_lower.endswith('identifier'):
            parts.append('identifier id number code key')

        # Add sample values for context
        if column.sample_values:
            sample_str = " ".join(str(v)[:50] for v in column.sample_values[:3])
            parts.append(sample_str)

        # Add type information
        if column.inferred_type:
            parts.append(f"type: {column.inferred_type}")

        text = " ".join(parts)
        return self._encode_with_cache(text)

    def embed_property(self, prop: OntologyProperty) -> np.ndarray:
        """Create embedding for a property with caching.

        Combines:
        - All SKOS labels (prefLabel, altLabel, hiddenLabel)
        - rdfs:label
        - rdfs:comment
        - Local name
        """
        # Check legacy cache first for backward compatibility
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

        lname = (prop.label or local_name or '').lower()
        # Add generic synonyms for identifier-like properties
        if any(tok in lname for tok in ['number','id','identifier','code']):
            parts.append('identifier id number code key reference')

        text = " ".join(parts)
        embedding = self._encode_with_cache(text)

        # Cache it in legacy cache too
        self._property_cache[cache_key] = embedding
        return embedding

    def get_cache_statistics(self) -> dict:
        """Get cache performance statistics.

        Returns:
            Dictionary with cache statistics or empty dict if cache disabled
        """
        if self.use_cache and self._embedding_cache:
            return self._embedding_cache.get_statistics()
        return {
            'cache_enabled': False,
            'message': 'Cache is disabled'
        }

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        if self.use_cache and self._embedding_cache:
            self._embedding_cache.clear()
        self._property_cache.clear()

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

    def score_all(
        self,
        column: DataFieldAnalysis,
        properties: List[OntologyProperty]
    ) -> List[tuple[OntologyProperty, float]]:
        """Return cosine similarity scores for all properties for a given column.

        Useful for debugging/validation of the embedding model.
        """
        if not properties:
            return []
        col_emb = self.embed_column(column)
        prop_embs = np.array([self.embed_property(p) for p in properties])
        sims = cosine_similarity([col_emb], prop_embs)[0]
        return list(zip(properties, [float(s) for s in sims]))

    def _tokenize(self, text: str) -> List[str]:
        return [t for t in text.lower().replace('_',' ').replace('-',' ').split() if t]

    def _embed_tokens(self, tokens: List[str]) -> np.ndarray:
        if not tokens:
            return np.zeros(self.model.get_sentence_embedding_dimension())
        embs = self.model.encode(tokens, convert_to_numpy=True)
        if isinstance(embs, np.ndarray) and len(embs.shape) == 2:
            return embs.mean(axis=0)
        return embs

    def enhanced_score_all(self, column: DataFieldAnalysis, properties: List[OntologyProperty]) -> List[dict]:
        """Return enriched similarity scores per property.

        For each property we compute:
        - phrase_cosine: cosine between full column phrase embedding and property phrase embedding
        - token_cosine: cosine between average token embeddings (column tokens vs property tokens)
        - id_boost: small boost if both sides look like identifiers (contain id/number/code)
        - combined: max(phrase_cosine, token_cosine) + id_boost (capped at 1.0)
        """
        if not properties:
            return []
        col_phrase_emb = self.embed_column(column)
        col_tokens = self._tokenize(column.name)
        col_token_emb = self._embed_tokens(col_tokens)
        results = []
        for prop in properties:
            prop_phrase_emb = self.embed_property(prop)
            prop_tokens = self._tokenize(prop.label or str(prop.uri).split('#')[-1])
            prop_token_emb = self._embed_tokens(prop_tokens)
            # Phrase cosine
            phrase_cos = float(cosine_similarity([col_phrase_emb],[prop_phrase_emb])[0][0])
            # Token cosine
            token_cos = float(cosine_similarity([col_token_emb],[prop_token_emb])[0][0]) if (col_token_emb.any() and prop_token_emb.any()) else 0.0
            base = max(phrase_cos, token_cos)
            lname = (prop.label or '').lower()
            cname = column.name.lower()
            id_terms = {'id','identifier','number','code','key','ref','reference'}
            if any(t in cname for t in id_terms) and any(t in lname for t in id_terms):
                id_boost = 0.07 if base >= 0.50 else 0.03
            else:
                id_boost = 0.0
            combined = min(1.0, base + id_boost)
            results.append({
                'property': prop,
                'phrase_cosine': phrase_cos,
                'token_cosine': token_cos,
                'id_boost': id_boost,
                'combined': combined
            })
        # Sort by combined descending
        results.sort(key=lambda r: r['combined'], reverse=True)
        return results
