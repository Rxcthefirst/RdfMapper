"""Pure lexical/string-based matching without semantic embeddings."""

from typing import Optional, List, Dict, Set
from difflib import SequenceMatcher
import re

from .base import ColumnPropertyMatcher, MatchResult, MatchContext, MatchPriority
from ..ontology_analyzer import OntologyProperty
from ..data_analyzer import DataFieldAnalysis
from ...models.alignment import MatchType


class LexicalMatcher(ColumnPropertyMatcher):
    """Pure lexical/string similarity matching using multiple algorithms.

    This matcher uses five distinct algorithms:
    1. Exact match (normalized)
    2. Substring containment with ratio scoring
    3. Token-based Jaccard with synonym normalization
    4. Edit distance (SequenceMatcher)
    5. Character n-gram similarity

    Each algorithm has its own weight, and the final score is the weighted maximum.
    """

    def __init__(
        self,
        enabled: bool = True,
        threshold: float = 0.60,
        exact_weight: float = 1.0,
        substring_weight: float = 0.85,
        token_weight: float = 0.70,
        edit_distance_weight: float = 0.85,
        ngram_weight: float = 0.75,
    ):
        """Initialize the lexical matcher.

        Args:
            enabled: Whether this matcher is enabled
            threshold: Minimum similarity score to accept a match
            exact_weight: Weight for exact match algorithm (0-1)
            substring_weight: Weight for substring containment (0-1)
            token_weight: Weight for token-based Jaccard (0-1)
            edit_distance_weight: Weight for edit distance (0-1)
            ngram_weight: Weight for n-gram similarity (0-1)
        """
        super().__init__(enabled, threshold)
        self.exact_weight = exact_weight
        self.substring_weight = substring_weight
        self.token_weight = token_weight
        self.edit_distance_weight = edit_distance_weight
        self.ngram_weight = ngram_weight

    def name(self) -> str:
        return "LexicalMatcher"

    def priority(self) -> MatchPriority:
        return MatchPriority.MEDIUM

    def match(
        self,
        column: DataFieldAnalysis,
        properties: List[OntologyProperty],
        context: Optional[MatchContext] = None
    ) -> Optional[MatchResult]:
        """Find the best lexical match for a column.

        Args:
            column: Column to match
            properties: Available properties
            context: Optional matching context

        Returns:
            Best match result above threshold, or None
        """
        if not self.enabled or not properties:
            return None

        scores = self._compute_all_scores(column, properties)

        # Find best match
        best_prop = None
        best_score = 0.0
        best_method = None

        for prop_uri, score_info in scores.items():
            if score_info['final_score'] > best_score:
                best_score = score_info['final_score']
                best_prop = next(p for p in properties if str(p.uri) == prop_uri)
                best_method = score_info['best_method']

        if best_score >= self.threshold and best_prop:
            return MatchResult(
                property=best_prop,
                match_type=MatchType.PARTIAL,  # Lexical matches are partial/fuzzy
                confidence=best_score,
                matched_via=f"lexical ({best_method})",
                matcher_name=self.name()
            )

        return None

    def _compute_all_scores(
        self,
        column: DataFieldAnalysis,
        properties: List[OntologyProperty]
    ) -> Dict[str, Dict]:
        """Compute lexical scores for all properties using all algorithms.

        Returns:
            Dict mapping property URI to score information:
            {
                'final_score': float,
                'best_method': str,
                'exact': float,
                'substring': float,
                'token': float,
                'edit_distance': float,
                'ngram': float
            }
        """
        col_name = column.name
        scores = {}

        for prop in properties:
            prop_uri = str(prop.uri)

            # Get all text representations of the property
            prop_texts = self._get_property_texts(prop)

            # Compute scores using all algorithms
            algo_scores = {
                'exact': 0.0,
                'substring': 0.0,
                'token': 0.0,
                'edit_distance': 0.0,
                'ngram': 0.0
            }

            for prop_text in prop_texts:
                algo_scores['exact'] = max(algo_scores['exact'],
                                          self._exact_match(col_name, prop_text))
                algo_scores['substring'] = max(algo_scores['substring'],
                                               self._substring_match(col_name, prop_text))
                algo_scores['token'] = max(algo_scores['token'],
                                          self._token_match(col_name, prop_text))
                algo_scores['edit_distance'] = max(algo_scores['edit_distance'],
                                                   self._edit_distance_match(col_name, prop_text))
                algo_scores['ngram'] = max(algo_scores['ngram'],
                                          self._ngram_match(col_name, prop_text))

            # Apply weights and find best
            weighted_scores = {
                'exact': algo_scores['exact'] * self.exact_weight,
                'substring': algo_scores['substring'] * self.substring_weight,
                'token': algo_scores['token'] * self.token_weight,
                'edit_distance': algo_scores['edit_distance'] * self.edit_distance_weight,
                'ngram': algo_scores['ngram'] * self.ngram_weight
            }

            # Take the maximum weighted score
            best_method = max(weighted_scores.keys(), key=lambda k: weighted_scores[k])
            final_score = weighted_scores[best_method]

            scores[prop_uri] = {
                'final_score': final_score,
                'best_method': best_method,
                **algo_scores
            }

        return scores

    def _get_property_texts(self, prop: OntologyProperty) -> List[str]:
        """Get all text representations of a property for matching.

        Returns:
            List of normalized text strings to match against
        """
        texts = []

        # Add rdfs:label
        if prop.label:
            texts.append(prop.label.lower().strip())

        # Add all SKOS labels
        for label in prop.get_all_labels():
            texts.append(label.lower().strip())

        # Add local name with camelCase splitting
        local_name = str(prop.uri).split('#')[-1].split('/')[-1]
        local_split = re.sub(r'([a-z])([A-Z])', r'\1 \2', local_name).lower()
        texts.append(local_split)
        if local_split != local_name.lower():
            texts.append(local_name.lower())

        return texts

    def _normalize(self, text: str) -> str:
        """Normalize text for matching."""
        return text.lower().replace('_', ' ').replace('-', ' ').strip()

    def _exact_match(self, col_name: str, prop_text: str) -> float:
        """Algorithm 1: Exact match (normalized)."""
        col_norm = self._normalize(col_name).replace(' ', '')
        prop_norm = self._normalize(prop_text).replace(' ', '')
        return 0.95 if col_norm == prop_norm else 0.0

    def _substring_match(self, col_name: str, prop_text: str) -> float:
        """Algorithm 2: Substring containment with ratio scoring."""
        col_norm = self._normalize(col_name)
        prop_norm = self._normalize(prop_text)

        if col_norm in prop_norm:
            # Column is substring of property
            ratio = len(col_norm) / len(prop_norm)
            return 0.80 + (ratio * 0.15)
        elif prop_norm in col_norm:
            # Property is substring of column
            ratio = len(prop_norm) / len(col_norm)
            return 0.75 + (ratio * 0.15)

        return 0.0

    def _token_match(self, col_name: str, prop_text: str) -> float:
        """Algorithm 3: Token-based Jaccard with synonym normalization."""
        col_tokens = set(self._normalize(col_name).split())
        prop_tokens = set(self._normalize(prop_text).split())

        # Normalize synonyms (id/identifier/number are equivalent)
        col_tokens_norm = self._normalize_tokens(col_tokens)
        prop_tokens_norm = self._normalize_tokens(prop_tokens)

        if not col_tokens_norm or not prop_tokens_norm:
            return 0.0

        intersection = col_tokens_norm & prop_tokens_norm
        union = col_tokens_norm | prop_tokens_norm

        if len(intersection) == 0:
            return 0.0

        jaccard = len(intersection) / len(union)

        # Boost if all column tokens are in property
        if col_tokens_norm.issubset(prop_tokens_norm):
            return 0.75 + (jaccard * 0.15)

        return jaccard * 0.70

    def _normalize_tokens(self, tokens: Set[str]) -> Set[str]:
        """Normalize tokens with synonym equivalence."""
        normalized = set()
        for token in tokens:
            if token in ('id', 'identifier', 'num'):
                normalized.add('number')
                normalized.add('id')
            else:
                normalized.add(token)
        return normalized

    def _edit_distance_match(self, col_name: str, prop_text: str) -> float:
        """Algorithm 4: Edit distance (SequenceMatcher)."""
        col_norm = self._normalize(col_name)
        prop_norm = self._normalize(prop_text)

        ratio = SequenceMatcher(None, col_norm, prop_norm).ratio()

        # Only consider if reasonably similar
        if ratio > 0.60:
            return ratio * 0.85

        return 0.0

    def _ngram_match(self, col_name: str, prop_text: str) -> float:
        """Algorithm 5: Character n-gram similarity (bigrams)."""
        col_norm = self._normalize(col_name).replace(' ', '')
        prop_norm = self._normalize(prop_text).replace(' ', '')

        col_bigrams = self._get_ngrams(col_norm, 2)
        prop_bigrams = self._get_ngrams(prop_norm, 2)

        if not col_bigrams or not prop_bigrams:
            return 0.0

        intersection = col_bigrams & prop_bigrams
        union = col_bigrams | prop_bigrams

        jaccard = len(intersection) / len(union)

        if jaccard > 0.50:
            return jaccard * 0.75

        return 0.0

    def _get_ngrams(self, text: str, n: int) -> Set[str]:
        """Generate character n-grams from text."""
        if len(text) < n:
            return {text}
        return {text[i:i+n] for i in range(len(text) - n + 1)}

