"""Confidence calibration for matching results.

Dynamically adjusts confidence scores based on historical matcher performance
to provide more accurate confidence estimates.
"""

from typing import Optional, Dict
from dataclasses import dataclass

from .matchers.base import MatchResult
from .mapping_history import MappingHistory
from ..models.alignment import MatchType


@dataclass
class CalibrationStats:
    """Statistics for calibrating a matcher's confidence."""
    total_matches: int
    accepted_matches: int
    avg_reported_confidence: float
    actual_success_rate: float
    calibration_factor: float


class ConfidenceCalibrator:
    """Calibrates confidence scores based on historical accuracy."""
    
    def __init__(self, history: Optional[MappingHistory] = None, min_samples: int = 10):
        """Initialize the calibrator.
        
        Args:
            history: MappingHistory instance for stats (creates default if None)
            min_samples: Minimum samples needed before calibrating
        """
        self.history = history or MappingHistory()
        self.min_samples = min_samples
        self._calibration_cache: Dict[str, CalibrationStats] = {}
    
    def calibrate_result(self, result: MatchResult) -> MatchResult:
        """Calibrate a match result's confidence score.
        
        Args:
            result: Original match result
            
        Returns:
            New MatchResult with calibrated confidence
        """
        calibrated_confidence = self.calibrate_score(
            result.confidence,
            result.matcher_name,
            result.match_type
        )
        
        # Create new result with calibrated confidence
        return MatchResult(
            property=result.property,
            match_type=result.match_type,
            confidence=calibrated_confidence,
            matched_via=result.matched_via,
            matcher_name=result.matcher_name
        )
    
    def calibrate_score(
        self,
        base_confidence: float,
        matcher_name: str,
        match_type: MatchType
    ) -> float:
        """Calibrate a confidence score.
        
        Args:
            base_confidence: Original confidence score
            matcher_name: Name of the matcher
            match_type: Type of match
            
        Returns:
            Calibrated confidence score
        """
        # Get calibration stats for this matcher
        stats = self._get_calibration_stats(matcher_name)
        
        if stats is None:
            # Not enough history, return original
            return base_confidence
        
        # Apply calibration factor
        calibrated = base_confidence * stats.calibration_factor
        
        # Additional adjustment based on match type reliability
        type_adjustment = self._get_match_type_adjustment(match_type, stats)
        calibrated *= type_adjustment
        
        # Ensure within valid range
        return max(0.0, min(1.0, calibrated))
    
    def _get_calibration_stats(self, matcher_name: str) -> Optional[CalibrationStats]:
        """Get calibration statistics for a matcher.
        
        Args:
            matcher_name: Name of the matcher
            
        Returns:
            CalibrationStats if enough data, None otherwise
        """
        # Check cache first
        if matcher_name in self._calibration_cache:
            return self._calibration_cache[matcher_name]
        
        # Get performance from history
        perf = self.history.get_matcher_performance(matcher_name)
        
        if perf is None or perf['total_matches'] < self.min_samples:
            return None
        
        # Calculate calibration factor
        actual_success_rate = perf['accepted_matches'] / perf['total_matches']
        avg_confidence = perf['avg_confidence']
        
        if avg_confidence > 0:
            # Calibration factor adjusts predicted confidence to match actual success
            calibration_factor = actual_success_rate / avg_confidence
            
            # Limit calibration to reasonable bounds (0.8 - 1.2)
            calibration_factor = max(0.8, min(1.2, calibration_factor))
        else:
            calibration_factor = 1.0
        
        stats = CalibrationStats(
            total_matches=perf['total_matches'],
            accepted_matches=perf['accepted_matches'],
            avg_reported_confidence=avg_confidence,
            actual_success_rate=actual_success_rate,
            calibration_factor=calibration_factor
        )
        
        # Cache it
        self._calibration_cache[matcher_name] = stats
        
        return stats
    
    def _get_match_type_adjustment(
        self,
        match_type: MatchType,
        stats: CalibrationStats
    ) -> float:
        """Get additional adjustment based on match type.
        
        Different match types have different inherent reliability.
        
        Args:
            match_type: Type of match
            stats: Calibration statistics
            
        Returns:
            Adjustment factor (typically 0.9 - 1.1)
        """
        # Exact matches are highly reliable
        if match_type in [
            MatchType.EXACT_PREF_LABEL,
            MatchType.EXACT_LABEL,
            MatchType.EXACT_ALT_LABEL
        ]:
            return 1.05  # Boost exact matches slightly
        
        # Fuzzy matches are less reliable
        elif match_type == MatchType.FUZZY:
            return 0.95  # Reduce fuzzy matches slightly
        
        # Others stay neutral
        return 1.0
    
    def get_matcher_reliability(self, matcher_name: str) -> Optional[float]:
        """Get reliability score for a matcher (0-1).
        
        Args:
            matcher_name: Name of the matcher
            
        Returns:
            Reliability score or None if insufficient data
        """
        stats = self._get_calibration_stats(matcher_name)
        
        if stats is None:
            return None
        
        return stats.actual_success_rate
    
    def get_all_matcher_reliabilities(self) -> Dict[str, float]:
        """Get reliability scores for all matchers with sufficient history.
        
        Returns:
            Dictionary mapping matcher names to reliability scores
        """
        all_stats = self.history.get_all_matcher_stats()
        
        reliabilities = {}
        for stat in all_stats:
            if stat['total_matches'] >= self.min_samples:
                matcher_name = stat['matcher_name']
                stats = self._get_calibration_stats(matcher_name)
                if stats:
                    reliabilities[matcher_name] = stats.actual_success_rate
        
        return reliabilities
    
    def generate_calibration_report(self) -> str:
        """Generate a report on calibration statistics.
        
        Returns:
            Formatted report string
        """
        lines = ["Confidence Calibration Report", "=" * 50, ""]
        
        all_stats = self.history.get_all_matcher_stats()
        
        if not all_stats:
            lines.append("No calibration data available yet.")
            return "\n".join(lines)
        
        for stat in sorted(all_stats, key=lambda x: x['total_matches'], reverse=True):
            matcher_name = stat['matcher_name']
            total = stat['total_matches']
            
            if total < self.min_samples:
                continue
            
            calibration = self._get_calibration_stats(matcher_name)
            if not calibration:
                continue
            
            lines.append(f"{matcher_name}:")
            lines.append(f"  Matches: {total}")
            lines.append(f"  Success Rate: {calibration.actual_success_rate:.1%}")
            lines.append(f"  Avg Confidence: {calibration.avg_reported_confidence:.3f}")
            lines.append(f"  Calibration Factor: {calibration.calibration_factor:.3f}")
            
            # Show adjustment
            if calibration.calibration_factor > 1.05:
                lines.append(f"  → Confidence will be BOOSTED (over-conservative)")
            elif calibration.calibration_factor < 0.95:
                lines.append(f"  → Confidence will be REDUCED (over-confident)")
            else:
                lines.append(f"  → Confidence well-calibrated")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def clear_cache(self):
        """Clear the calibration cache.
        
        Call this if history has been updated and you want fresh calibrations.
        """
        self._calibration_cache.clear()
    
    def close(self):
        """Close the history database connection."""
        if self.history:
            self.history.close()

