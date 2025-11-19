"""Polars-integrated embedding cache for blazingly fast semantic matching.

Uses Polars DataFrame as the cache backend for zero-copy operations and Arrow memory format.
"""

from typing import Optional, List, Tuple
import numpy as np
import polars as pl
from datetime import datetime
import hashlib


class EmbeddingCache:
    """Polars-backed cache for sentence embeddings with session lifecycle."""

    def __init__(self, model_name: str, max_size: int = 10000):
        """Initialize embedding cache.

        Args:
            model_name: Name of the embedding model (for cache key)
            max_size: Maximum cache entries before eviction (LRU)
        """
        self.model_name = model_name
        self.max_size = max_size

        # Initialize empty Polars DataFrame with schema
        self._cache_df = pl.DataFrame({
            'text': pl.Series([], dtype=pl.Utf8),
            'text_hash': pl.Series([], dtype=pl.Utf8),
            'embedding': pl.Series([], dtype=pl.List(pl.Float32)),
            'model_name': pl.Series([], dtype=pl.Utf8),
            'timestamp': pl.Series([], dtype=pl.Datetime),
            'access_count': pl.Series([], dtype=pl.UInt32),
        })

        # Statistics
        self._hits = 0
        self._misses = 0
        self._total_embeddings_generated = 0

    def _hash_text(self, text: str) -> str:
        """Generate hash for text key."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]

    def get(self, text: str) -> Optional[np.ndarray]:
        """Get embedding from cache.

        Args:
            text: Text to look up

        Returns:
            Embedding vector as numpy array, or None if not cached
        """
        text_hash = self._hash_text(text)

        # Query cache using Polars (blazingly fast!)
        result = self._cache_df.filter(
            (pl.col('text_hash') == text_hash) &
            (pl.col('model_name') == self.model_name)
        )

        if result.height == 0:
            self._misses += 1
            return None

        # Cache hit! Update access count and timestamp
        self._hits += 1

        # Update access tracking (in-place for performance)
        self._cache_df = self._cache_df.with_columns([
            pl.when(
                (pl.col('text_hash') == text_hash) &
                (pl.col('model_name') == self.model_name)
            )
            .then(pl.col('access_count') + 1)
            .otherwise(pl.col('access_count'))
            .alias('access_count'),

            pl.when(
                (pl.col('text_hash') == text_hash) &
                (pl.col('model_name') == self.model_name)
            )
            .then(pl.lit(datetime.now()))
            .otherwise(pl.col('timestamp'))
            .alias('timestamp')
        ])

        # Extract embedding as numpy array
        embedding_list = result['embedding'][0]
        return np.array(embedding_list, dtype=np.float32)

    def put(self, text: str, embedding: np.ndarray) -> None:
        """Store embedding in cache.

        Args:
            text: Original text
            embedding: Embedding vector
        """
        text_hash = self._hash_text(text)

        # Ensure embedding is float32 for consistency
        if embedding.dtype != np.float32:
            embedding = embedding.astype(np.float32)

        # Check if already exists
        exists = self._cache_df.filter(
            (pl.col('text_hash') == text_hash) &
            (pl.col('model_name') == self.model_name)
        ).height > 0

        if exists:
            # Update existing entry
            self._cache_df = self._cache_df.with_columns([
                pl.when(
                    (pl.col('text_hash') == text_hash) &
                    (pl.col('model_name') == self.model_name)
                )
                .then(pl.lit(embedding.tolist()))
                .otherwise(pl.col('embedding'))
                .alias('embedding'),

                pl.when(
                    (pl.col('text_hash') == text_hash) &
                    (pl.col('model_name') == self.model_name)
                )
                .then(pl.lit(datetime.now()))
                .otherwise(pl.col('timestamp'))
                .alias('timestamp')
            ])
        else:
            # Add new entry - must match schema exactly
            new_row = pl.DataFrame({
                'text': pl.Series([text], dtype=pl.Utf8),
                'text_hash': pl.Series([text_hash], dtype=pl.Utf8),
                'embedding': pl.Series([embedding.tolist()], dtype=pl.List(pl.Float32)),
                'model_name': pl.Series([self.model_name], dtype=pl.Utf8),
                'timestamp': pl.Series([datetime.now()], dtype=pl.Datetime),
                'access_count': pl.Series([1], dtype=pl.UInt32)
            })

            self._cache_df = pl.concat([self._cache_df, new_row], how='vertical')
            self._total_embeddings_generated += 1

            # Evict oldest entries if cache is full (LRU)
            if self._cache_df.height > self.max_size:
                self._evict_lru()

    def _evict_lru(self) -> None:
        """Evict least recently used entries to maintain cache size."""
        # Keep top max_size entries by timestamp (most recent)
        self._cache_df = self._cache_df.sort('timestamp', descending=True).head(self.max_size)

    def get_batch(self, texts: List[str]) -> Tuple[List[Optional[np.ndarray]], List[str]]:
        """Get multiple embeddings from cache.

        Args:
            texts: List of texts to look up

        Returns:
            Tuple of (embeddings list, missing texts list)
            - embeddings list has None for cache misses
            - missing texts list contains texts that need embedding generation
        """
        embeddings = []
        missing = []

        for text in texts:
            embedding = self.get(text)
            embeddings.append(embedding)
            if embedding is None:
                missing.append(text)

        return embeddings, missing

    def put_batch(self, texts: List[str], embeddings: List[np.ndarray]) -> None:
        """Store multiple embeddings in cache.

        Args:
            texts: List of texts
            embeddings: List of embedding vectors
        """
        for text, embedding in zip(texts, embeddings):
            self.put(text, embedding)

    def get_statistics(self) -> dict:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

        # Calculate memory usage (approximate)
        if self._cache_df.height > 0:
            # Each embedding is typically 384 dims * 4 bytes (float32) = 1536 bytes
            avg_embedding_size = 1536
            memory_bytes = self._cache_df.height * (avg_embedding_size + 100)  # +100 for metadata
            memory_mb = memory_bytes / (1024 * 1024)
        else:
            memory_mb = 0.0

        return {
            'total_entries': self._cache_df.height,
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': hit_rate,
            'memory_mb': memory_mb,
            'total_embeddings_generated': self._total_embeddings_generated,
            'model_name': self.model_name,
            'max_size': self.max_size
        }

    def clear(self) -> None:
        """Clear the cache."""
        self._cache_df = pl.DataFrame({
            'text': pl.Series([], dtype=pl.Utf8),
            'text_hash': pl.Series([], dtype=pl.Utf8),
            'embedding': pl.Series([], dtype=pl.List(pl.Float32)),
            'model_name': pl.Series([], dtype=pl.Utf8),
            'timestamp': pl.Series([], dtype=pl.Datetime),
            'access_count': pl.Series([], dtype=pl.UInt32),
        })
        self._hits = 0
        self._misses = 0

    def __repr__(self):
        stats = self.get_statistics()
        return f"EmbeddingCache(entries={stats['total_entries']}, hit_rate={stats['hit_rate']:.2%}, memory={stats['memory_mb']:.1f}MB)"

