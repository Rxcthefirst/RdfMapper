"""Abstract base classes for column-property matching strategies.

This module provides the foundation for a plugin-based matching architecture
where different matching strategies can be composed and prioritized.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from dataclasses import dataclass
from enum import IntEnum
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
import time
import os

from ..ontology_analyzer import OntologyProperty
from ..data_analyzer import DataFieldAnalysis
from ...models.alignment import MatchType


class MatchPriority(IntEnum):
    """Priority levels for matchers (lower = higher priority)."""
    CRITICAL = 0   # Exact matches with prefLabel
    HIGH = 10      # Exact matches with label/altLabel
    MEDIUM = 20    # Semantic similarity, partial matches
    LOW = 30       # Fuzzy matches
    FALLBACK = 40  # Last resort


@dataclass
class MatchResult:
    """Result of a matching attempt."""
    property: OntologyProperty
    match_type: MatchType
    confidence: float
    matched_via: str  # What label/method was used
    matcher_name: str  # Which matcher found this

    def __repr__(self):
        return f"MatchResult({self.property.label}, {self.match_type}, confidence={self.confidence:.3f})"


@dataclass
class PerformanceMetrics:
    """Performance metrics for matcher execution."""
    execution_time_ms: float = 0.0
    matchers_fired: int = 0
    matchers_succeeded: int = 0
    matchers_failed: int = 0
    matchers_timeout: int = 0
    parallel_speedup: Optional[float] = None  # Speedup factor vs sequential
    cache_hits: int = 0
    cache_misses: int = 0


@dataclass
class MatchContext:
    """Rich context for matching decisions."""
    column: DataFieldAnalysis
    all_columns: List[DataFieldAnalysis]
    available_properties: List[OntologyProperty]
    domain_hints: Optional[str] = None  # "finance", "healthcare", etc.
    matched_properties: Optional[Dict[str, str]] = None  # column_name -> property_uri mapping


class ColumnPropertyMatcher(ABC):
    """Abstract base class for all matching strategies."""

    def __init__(self, enabled: bool = True, threshold: float = 0.5):
        """Initialize matcher.

        Args:
            enabled: Whether this matcher is active
            threshold: Minimum confidence threshold for matches
        """
        self.enabled = enabled
        self.threshold = threshold

    @abstractmethod
    def name(self) -> str:
        """Return human-readable name of this matcher."""
        pass

    @abstractmethod
    def priority(self) -> MatchPriority:
        """Return priority level (lower = higher priority)."""
        pass

    @abstractmethod
    def match(
        self,
        column: DataFieldAnalysis,
        properties: List[OntologyProperty],
        context: Optional[MatchContext] = None
    ) -> Optional[MatchResult]:
        """Attempt to match a column to a property.

        Args:
            column: Column to match
            properties: Available properties to match against
            context: Optional rich context for matching

        Returns:
            MatchResult if match found above threshold, None otherwise
        """
        pass

    def can_match(self, column: DataFieldAnalysis) -> bool:
        """Check if this matcher can handle this column type.

        Default implementation returns True. Override for specialized matchers.
        """
        return self.enabled

    def __repr__(self):
        return f"{self.__class__.__name__}(priority={self.priority()}, threshold={self.threshold})"


class MatcherPipeline:
    """Orchestrates multiple matchers in priority order with parallel execution support."""

    def __init__(
        self,
        matchers: Optional[List[ColumnPropertyMatcher]] = None,
        logger=None,
        calibrator=None,
        max_workers: Optional[int] = None,
        matcher_timeout: float = 2.0
    ):
        """Initialize pipeline with matchers.

        Args:
            matchers: List of matchers to use (will be sorted by priority)
            logger: Optional MatchingLogger instance for detailed logging
            calibrator: Optional ConfidenceCalibrator for dynamic confidence adjustment
            max_workers: Max threads for parallel execution (auto-tuned if None)
            matcher_timeout: Timeout per matcher in seconds (default 2.0)
        """
        self.matchers = matchers or []
        self.logger = logger
        self.calibrator = calibrator
        self.matcher_timeout = matcher_timeout

        # Auto-tune max_workers based on CPU cores
        if max_workers is None:
            cpu_count = os.cpu_count() or 4
            self.max_workers = min(17, cpu_count * 2)  # Cap at 17 (number of matchers)
        else:
            self.max_workers = max_workers

        self._sort_matchers()
        self._last_performance_metrics: Optional[PerformanceMetrics] = None

    def _sort_matchers(self):
        """Sort matchers by priority (lower = higher priority)."""
        self.matchers.sort(key=lambda m: m.priority())

    def add_matcher(self, matcher: ColumnPropertyMatcher):
        """Add a matcher to the pipeline."""
        self.matchers.append(matcher)
        self._sort_matchers()

    def remove_matcher(self, matcher_name: str):
        """Remove a matcher by name."""
        self.matchers = [m for m in self.matchers if m.name() != matcher_name]

    def match(
        self,
        column: DataFieldAnalysis,
        properties: List[OntologyProperty],
        context: Optional[MatchContext] = None
    ) -> Optional[MatchResult]:
        """Run column through all matchers until one succeeds.

        Args:
            column: Column to match
            properties: Available properties
            context: Optional context

        Returns:
            First MatchResult found above threshold, or None
        """
        for matcher in self.matchers:
            if not matcher.enabled or not matcher.can_match(column):
                continue

            # Log attempt
            if self.logger:
                self.logger.log_matcher_attempt(matcher, column)

            try:
                result = matcher.match(column, properties, context)

                if result and result.confidence >= matcher.threshold:
                    # Calibrate confidence if calibrator is available
                    if self.calibrator:
                        original_confidence = result.confidence
                        result = self.calibrator.calibrate_result(result)

                        # Log calibration if logger is available
                        if self.logger and result.confidence != original_confidence:
                            self.logger.log_confidence_boost(
                                original_confidence,
                                result.confidence,
                                "historical calibration"
                            )

                    # Log success
                    if self.logger:
                        self.logger.log_match_found(result, column)
                    return result
                elif result:
                    # Log rejection (found but below threshold)
                    if self.logger:
                        self.logger.log_match_rejected(
                            matcher.name(),
                            column,
                            f"Below threshold ({result.confidence:.3f} < {matcher.threshold})",
                            result.confidence
                        )
            except Exception as e:
                # Log error
                if self.logger:
                    self.logger.log_error(e, column)
                # Continue to next matcher

        # No match found
        if self.logger:
            self.logger.log_no_match(column, len([m for m in self.matchers if m.enabled]))

        return None

    def match_all(
        self,
        column: DataFieldAnalysis,
        properties: List[OntologyProperty],
        context: Optional[MatchContext] = None,
        top_k: int = 5,
        parallel: bool = True
    ) -> List[MatchResult]:
        """Get all matches from all matchers, sorted by confidence.

        Uses parallel execution by default for blazingly fast performance.

        Args:
            column: Column to match
            properties: Available properties
            context: Optional context
            top_k: Return top K results
            parallel: Use parallel execution (default True)

        Returns:
            List of MatchResults sorted by confidence (highest first)
        """
        if parallel:
            return self._match_all_parallel(column, properties, context, top_k)
        else:
            return self._match_all_sequential(column, properties, context, top_k)

    def _match_all_sequential(
        self,
        column: DataFieldAnalysis,
        properties: List[OntologyProperty],
        context: Optional[MatchContext] = None,
        top_k: int = 5
    ) -> List[MatchResult]:
        """Sequential implementation (legacy)."""
        results = []

        for matcher in self.matchers:
            if not matcher.enabled or not matcher.can_match(column):
                continue

            result = matcher.match(column, properties, context)
            if result:
                results.append(result)

        # Sort by confidence (descending)
        results.sort(key=lambda r: r.confidence, reverse=True)
        return results[:top_k]

    def _match_all_parallel(
        self,
        column: DataFieldAnalysis,
        properties: List[OntologyProperty],
        context: Optional[MatchContext] = None,
        top_k: int = 5
    ) -> List[MatchResult]:
        """Parallel implementation using ThreadPoolExecutor."""
        start_time = time.time()
        results = []
        metrics = PerformanceMetrics()

        # Filter enabled matchers
        active_matchers = [m for m in self.matchers if m.enabled and m.can_match(column)]
        metrics.matchers_fired = len(active_matchers)

        def run_matcher(matcher: ColumnPropertyMatcher) -> Optional[MatchResult]:
            """Run a single matcher with timeout protection."""
            try:
                result = matcher.match(column, properties, context)
                return result
            except Exception as e:
                if self.logger:
                    self.logger.log_error(e, column)
                return None

        # Execute matchers in parallel with timeout
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all matcher tasks
            future_to_matcher = {
                executor.submit(run_matcher, matcher): matcher
                for matcher in active_matchers
            }

            # Collect results as they complete
            for future in as_completed(future_to_matcher, timeout=self.matcher_timeout * 2):
                matcher = future_to_matcher[future]
                try:
                    result = future.result(timeout=self.matcher_timeout)
                    if result:
                        results.append(result)
                        metrics.matchers_succeeded += 1
                except TimeoutError:
                    metrics.matchers_timeout += 1
                    if self.logger:
                        self.logger.log_error(
                            TimeoutError(f"{matcher.name()} timeout after {self.matcher_timeout}s"),
                            column
                        )
                except Exception as e:
                    metrics.matchers_failed += 1
                    if self.logger:
                        self.logger.log_error(e, column)

        # Calculate performance metrics
        execution_time = (time.time() - start_time) * 1000  # Convert to ms
        metrics.execution_time_ms = execution_time

        # Estimate sequential time (rough approximation)
        avg_matcher_time = execution_time / max(1.0, float(len(active_matchers)))
        estimated_sequential = avg_matcher_time * len(active_matchers)
        metrics.parallel_speedup = estimated_sequential / max(1.0, execution_time)

        self._last_performance_metrics = metrics

        # Sort by confidence (descending)
        results.sort(key=lambda r: r.confidence, reverse=True)
        return results[:top_k]

    def get_last_performance_metrics(self) -> Optional[PerformanceMetrics]:
        """Get performance metrics from last match_all execution."""
        return self._last_performance_metrics

    def get_matcher_stats(self) -> dict:
        """Get statistics about matchers in pipeline."""
        return {
            "total_matchers": len(self.matchers),
            "enabled_matchers": sum(1 for m in self.matchers if m.enabled),
            "matchers": [
                {
                    "name": m.name(),
                    "priority": m.priority(),
                    "enabled": m.enabled,
                    "threshold": m.threshold
                }
                for m in self.matchers
            ]
        }

    def __repr__(self):
        return f"MatcherPipeline(matchers={len(self.matchers)})"

