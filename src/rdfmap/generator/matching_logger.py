"""Enhanced logging for the matching process.

Provides structured, detailed logging to help understand and debug
the matching pipeline behavior.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from collections import defaultdict

from .matchers.base import MatchResult, ColumnPropertyMatcher
from .data_analyzer import DataFieldAnalysis
from .ontology_analyzer import OntologyProperty


class MatchingLogger:
    """Structured logging for matcher pipeline operations."""

    def __init__(self, logger_name: str = 'rdfmap.matching'):
        """Initialize the matching logger.

        Args:
            logger_name: Name for the logger instance
        """
        self.logger = logging.getLogger(logger_name)
        self.start_time = datetime.now()

        # Track statistics
        self.stats = {
            'columns_processed': 0,
            'matches_found': 0,
            'matches_rejected': 0,
            'matchers_tried': defaultdict(int),
            'matchers_succeeded': defaultdict(int),
            'total_confidence': 0.0,
            'errors': []
        }

    def log_pipeline_start(self, num_columns: int, num_properties: int, num_matchers: int):
        """Log the start of the matching pipeline.

        Args:
            num_columns: Number of columns to match
            num_properties: Number of available properties
            num_matchers: Number of matchers in pipeline
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting Matcher Pipeline")
        self.logger.info(f"  Columns to match: {num_columns}")
        self.logger.info(f"  Available properties: {num_properties}")
        self.logger.info(f"  Matchers in pipeline: {num_matchers}")
        self.logger.info("=" * 60)

    def log_column_start(self, column: DataFieldAnalysis, column_num: int, total: int):
        """Log the start of matching for a column.

        Args:
            column: Column being matched
            column_num: Current column number (1-indexed)
            total: Total number of columns
        """
        self.logger.info(f"\n[{column_num}/{total}] Matching column: '{column.name}'")

        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(f"  Type: {column.inferred_type}")
            if column.sample_values:
                samples = column.sample_values[:3]
                self.logger.debug(f"  Sample values: {samples}")

    def log_matcher_attempt(
        self,
        matcher: ColumnPropertyMatcher,
        column: DataFieldAnalysis
    ):
        """Log an attempt by a matcher.

        Args:
            matcher: Matcher being tried
            column: Column being matched
        """
        self.stats['matchers_tried'][matcher.name()] += 1
        self.logger.debug(f"  Trying: {matcher.name()} (priority: {matcher.priority()})")

    def log_match_found(
        self,
        result: MatchResult,
        column: DataFieldAnalysis
    ):
        """Log when a match is found.

        Args:
            result: Match result
            column: Column that was matched
        """
        self.stats['matches_found'] += 1
        self.stats['matchers_succeeded'][result.matcher_name] += 1
        self.stats['total_confidence'] += result.confidence

        confidence_emoji = "🟢" if result.confidence > 0.8 else "🟡" if result.confidence > 0.6 else "🟠"

        self.logger.info(
            f"  {confidence_emoji} MATCH: {result.property.label or result.property.uri}"
        )
        self.logger.info(f"    Matcher: {result.matcher_name}")
        self.logger.info(f"    Confidence: {result.confidence:.3f}")
        self.logger.info(f"    Match type: {result.match_type}")

        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(f"    Matched via: {result.matched_via}")
            self.logger.debug(f"    Property URI: {result.property.uri}")

    def log_match_rejected(
        self,
        matcher_name: str,
        column: DataFieldAnalysis,
        reason: str,
        confidence: Optional[float] = None
    ):
        """Log when a potential match is rejected.

        Args:
            matcher_name: Name of the matcher
            column: Column being matched
            reason: Reason for rejection
            confidence: Confidence score if available
        """
        self.stats['matches_rejected'] += 1

        if self.logger.isEnabledFor(logging.DEBUG):
            conf_str = f" (confidence: {confidence:.3f})" if confidence else ""
            self.logger.debug(f"  ✗ Rejected by {matcher_name}{conf_str}: {reason}")

    def log_no_match(self, column: DataFieldAnalysis, matchers_tried: int):
        """Log when no match is found for a column.

        Args:
            column: Column that couldn't be matched
            matchers_tried: Number of matchers that were tried
        """
        self.logger.warning(f"  ⚠️  NO MATCH found for '{column.name}' after {matchers_tried} matchers")

        if self.logger.isEnabledFor(logging.INFO):
            self.logger.info(f"    Suggestions:")
            self.logger.info(f"      - Add SKOS labels (prefLabel, altLabel) to ontology")
            self.logger.info(f"      - Check property naming conventions")
            self.logger.info(f"      - Lower confidence thresholds")
            self.logger.info(f"      - Review ontology coverage")

    def log_confidence_boost(
        self,
        original_confidence: float,
        boosted_confidence: float,
        reason: str
    ):
        """Log when confidence is boosted.

        Args:
            original_confidence: Original confidence score
            boosted_confidence: Boosted confidence score
            reason: Reason for boost
        """
        boost_amount = boosted_confidence - original_confidence

        if boost_amount > 0.01:  # Only log significant boosts
            self.logger.debug(
                f"  📈 Confidence boosted: {original_confidence:.3f} → {boosted_confidence:.3f} "
                f"(+{boost_amount:.3f}) - {reason}"
            )

    def log_error(self, error: Exception, column: Optional[DataFieldAnalysis] = None):
        """Log an error during matching.

        Args:
            error: Exception that occurred
            column: Column being processed when error occurred
        """
        self.stats['errors'].append({
            'error': str(error),
            'column': column.name if column else None,
            'timestamp': datetime.now().isoformat()
        })

        if column:
            self.logger.error(f"  ❌ Error matching '{column.name}': {error}")
        else:
            self.logger.error(f"  ❌ Error: {error}")

    def log_pipeline_summary(self):
        """Log a summary of the pipeline execution."""
        elapsed = (datetime.now() - self.start_time).total_seconds()

        self.logger.info("\n" + "=" * 60)
        self.logger.info("Matching Pipeline Summary")
        self.logger.info("=" * 60)

        # Overall stats
        self.logger.info(f"Columns processed: {self.stats['columns_processed']}")
        self.logger.info(f"Matches found: {self.stats['matches_found']}")
        self.logger.info(f"No matches: {self.stats['columns_processed'] - self.stats['matches_found']}")

        if self.stats['matches_found'] > 0:
            avg_confidence = self.stats['total_confidence'] / self.stats['matches_found']
            self.logger.info(f"Average confidence: {avg_confidence:.3f}")

        # Matcher performance
        if self.stats['matchers_succeeded']:
            self.logger.info("\nMatcher Performance:")
            for matcher_name in sorted(
                self.stats['matchers_succeeded'].keys(),
                key=lambda x: self.stats['matchers_succeeded'][x],
                reverse=True
            ):
                succeeded = self.stats['matchers_succeeded'][matcher_name]
                tried = self.stats['matchers_tried'][matcher_name]
                success_rate = (succeeded / tried * 100) if tried > 0 else 0

                self.logger.info(f"  {matcher_name}: {succeeded}/{tried} ({success_rate:.1f}%)")

        # Errors
        if self.stats['errors']:
            self.logger.warning(f"\nErrors encountered: {len(self.stats['errors'])}")
            for i, error_info in enumerate(self.stats['errors'][:5], 1):
                self.logger.warning(f"  {i}. {error_info['error']}")
                if error_info['column']:
                    self.logger.warning(f"     Column: {error_info['column']}")

        # Timing
        self.logger.info(f"\nElapsed time: {elapsed:.2f}s")
        if self.stats['columns_processed'] > 0:
            per_column = elapsed / self.stats['columns_processed']
            self.logger.info(f"Time per column: {per_column:.3f}s")

        self.logger.info("=" * 60)

    def get_stats(self) -> Dict[str, Any]:
        """Get the collected statistics.

        Returns:
            Dictionary of statistics
        """
        return dict(self.stats)

    def increment_columns_processed(self):
        """Increment the columns processed counter."""
        self.stats['columns_processed'] += 1


def configure_logging(
    level: str = 'INFO',
    format_string: Optional[str] = None,
    log_file: Optional[str] = None
):
    """Configure logging for the RDFMap application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        format_string: Custom format string
        log_file: Optional file to write logs to
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string
    )

    # Configure file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(logging.Formatter(format_string))

        logger = logging.getLogger('rdfmap')
        logger.addHandler(file_handler)

