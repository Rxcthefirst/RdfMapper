"""Evidence categorization and reasoning summary generation.

This module provides utilities to:
1. Categorize matcher evidence into semantic/ontological/structural groups
2. Generate human-readable reasoning summaries
3. Support rich evidence display in alignment reports
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass

from ..models.alignment import EvidenceItem, EvidenceGroup, MatchType


# Matcher categorization
SEMANTIC_MATCHERS = {
    'SemanticSimilarityMatcher',
    'LexicalMatcher',
    'ExactPrefLabelMatcher',
    'ExactRdfsLabelMatcher',
    'ExactAltLabelMatcher',
    'ExactHiddenLabelMatcher',
    'PartialStringMatcher',
    'FuzzyStringMatcher'
}

ONTOLOGY_MATCHERS = {
    'PropertyHierarchyMatcher',
    'OWLCharacteristicsMatcher',
    'RestrictionBasedMatcher',
    'DataTypeInferenceMatcher',
    'SKOSRelationsMatcher'
}

STRUCTURAL_MATCHERS = {
    'GraphReasoningMatcher',
    'StructuralMatcher',
    'HistoryAwareMatcher',
    'ExactLocalNameMatcher'
}


def categorize_evidence(evidence_items: List[EvidenceItem]) -> List[EvidenceGroup]:
    """Categorize evidence items into semantic/ontological/structural groups.
    
    Args:
        evidence_items: List of evidence items from matchers
        
    Returns:
        List of evidence groups with categorized items
    """
    # Group by category
    semantic_items = []
    ontology_items = []
    structural_items = []
    other_items = []
    
    for item in evidence_items:
        if item.matcher_name in SEMANTIC_MATCHERS:
            item.evidence_category = 'semantic'
            semantic_items.append(item)
        elif item.matcher_name in ONTOLOGY_MATCHERS:
            item.evidence_category = 'ontological_validation'
            ontology_items.append(item)
        elif item.matcher_name in STRUCTURAL_MATCHERS:
            item.evidence_category = 'structural_context'
            structural_items.append(item)
        else:
            item.evidence_category = 'other'
            other_items.append(item)
    
    groups = []
    
    # Create semantic group
    if semantic_items:
        avg_conf = sum(item.confidence for item in semantic_items) / len(semantic_items)
        groups.append(EvidenceGroup(
            category='semantic',
            evidence_items=semantic_items,
            avg_confidence=avg_conf,
            description='Semantic reasoning based on embeddings and label matching'
        ))
    
    # Create ontology group
    if ontology_items:
        avg_conf = sum(item.confidence for item in ontology_items) / len(ontology_items)
        groups.append(EvidenceGroup(
            category='ontological_validation',
            evidence_items=ontology_items,
            avg_confidence=avg_conf,
            description='Ontological validation using OWL constraints and type system'
        ))
    
    # Create structural group
    if structural_items:
        avg_conf = sum(item.confidence for item in structural_items) / len(structural_items)
        groups.append(EvidenceGroup(
            category='structural_context',
            evidence_items=structural_items,
            avg_confidence=avg_conf,
            description='Structural patterns and relationships in data'
        ))
    
    # Create other group if needed
    if other_items:
        avg_conf = sum(item.confidence for item in other_items) / len(other_items)
        groups.append(EvidenceGroup(
            category='other',
            evidence_items=other_items,
            avg_confidence=avg_conf,
            description='Additional evidence'
        ))
    
    return groups


def generate_reasoning_summary(
    winner_matcher: str,
    winner_confidence: float,
    evidence_groups: List[EvidenceGroup],
    property_label: str
) -> str:
    """Generate human-readable reasoning summary.
    
    Args:
        winner_matcher: Name of the winning matcher
        winner_confidence: Confidence of the winner
        evidence_groups: Categorized evidence groups
        property_label: Label of the matched property
        
    Returns:
        Human-readable reasoning summary
    """
    # Find category of winner
    winner_category = 'other'
    if winner_matcher in SEMANTIC_MATCHERS:
        winner_category = 'semantic'
    elif winner_matcher in ONTOLOGY_MATCHERS:
        winner_category = 'ontological'
    elif winner_matcher in STRUCTURAL_MATCHERS:
        winner_category = 'structural'
    
    # Build summary parts
    parts = []
    
    # Winner statement
    parts.append(f"Matched to '{property_label}' with {winner_confidence:.2f} confidence.")
    
    # Find evidence groups
    semantic_group = next((g for g in evidence_groups if g.category == 'semantic'), None)
    ontology_group = next((g for g in evidence_groups if g.category == 'ontological_validation'), None)
    structural_group = next((g for g in evidence_groups if g.category == 'structural_context'), None)
    
    # Semantic reasoning
    if semantic_group:
        count = len(semantic_group.evidence_items)
        avg = semantic_group.avg_confidence
        parts.append(f"Semantic reasoning: {count} matchers agree (avg: {avg:.2f}).")
    
    # Ontology validation (key insight!)
    if ontology_group:
        count = len(ontology_group.evidence_items)
        avg = ontology_group.avg_confidence
        
        # List specific validations
        validations = []
        for item in ontology_group.evidence_items:
            if 'IFP' in item.matched_via or 'unique' in item.matched_via.lower():
                validations.append('uniqueness constraint')
            elif 'type' in item.matched_via.lower():
                validations.append('type compatibility')
            elif 'hierarchy' in item.matched_via.lower():
                validations.append('property hierarchy')
            elif 'restriction' in item.matched_via.lower():
                validations.append('OWL restrictions')
        
        if validations:
            val_str = ', '.join(validations)
            parts.append(f"Ontology validates: {val_str} ({count} checks, avg: {avg:.2f}).")
        else:
            parts.append(f"Ontology validation: {count} constraints verified (avg: {avg:.2f}).")
    
    # Structural context
    if structural_group:
        count = len(structural_group.evidence_items)
        avg = structural_group.avg_confidence
        parts.append(f"Structural context: {count} patterns detected (avg: {avg:.2f}).")
    
    # Confidence assessment
    if winner_confidence >= 0.9:
        parts.append("Very high confidence - multiple strategies converge.")
    elif winner_confidence >= 0.8:
        parts.append("High confidence - strong agreement across matchers.")
    elif winner_confidence >= 0.7:
        parts.append("Good confidence - evidence supports match.")
    elif winner_confidence >= 0.6:
        parts.append("Moderate confidence - consider reviewing.")
    else:
        parts.append("Lower confidence - manual review recommended.")
    
    return " ".join(parts)


def format_evidence_for_display(
    evidence_groups: List[EvidenceGroup],
    show_details: bool = True
) -> str:
    """Format evidence groups for human-readable display.
    
    Args:
        evidence_groups: Categorized evidence groups
        show_details: Whether to show detailed matched_via info
        
    Returns:
        Formatted string for display
    """
    lines = []
    
    for group in evidence_groups:
        # Group header
        icon = "✅" if group.category == 'semantic' else "⭐" if group.category == 'ontological_validation' else "🔗"
        lines.append(f"\n{icon} {group.description.upper()}")
        lines.append(f"   Average confidence: {group.avg_confidence:.2f}")
        
        # Evidence items
        for item in group.evidence_items:
            line = f"   - {item.matcher_name}: {item.confidence:.2f}"
            if show_details and item.matched_via:
                # Truncate long matched_via strings
                via = item.matched_via[:60] + "..." if len(item.matched_via) > 60 else item.matched_via
                line += f" ({via})"
            lines.append(line)
    
    return "\n".join(lines)


def get_ontology_validation_count(evidence_groups: List[EvidenceGroup]) -> int:
    """Count how many ontology validations are present.
    
    Args:
        evidence_groups: Categorized evidence groups
        
    Returns:
        Count of ontology validation evidence items
    """
    ontology_group = next((g for g in evidence_groups if g.category == 'ontological_validation'), None)
    return len(ontology_group.evidence_items) if ontology_group else 0


def calculate_evidence_statistics(evidence_items: List[EvidenceItem]) -> Dict[str, float]:
    """Calculate statistics about evidence quality.
    
    Args:
        evidence_items: List of evidence items
        
    Returns:
        Dictionary with statistics
    """
    if not evidence_items:
        return {
            'total_count': 0,
            'avg_confidence': 0.0,
            'semantic_count': 0,
            'ontology_count': 0,
            'structural_count': 0,
            'ontology_ratio': 0.0
        }
    
    semantic_count = sum(1 for item in evidence_items if item.matcher_name in SEMANTIC_MATCHERS)
    ontology_count = sum(1 for item in evidence_items if item.matcher_name in ONTOLOGY_MATCHERS)
    structural_count = sum(1 for item in evidence_items if item.matcher_name in STRUCTURAL_MATCHERS)
    
    total_count = len(evidence_items)
    avg_confidence = sum(item.confidence for item in evidence_items) / total_count
    ontology_ratio = ontology_count / total_count if total_count > 0 else 0.0
    
    return {
        'total_count': total_count,
        'avg_confidence': avg_confidence,
        'semantic_count': semantic_count,
        'ontology_count': ontology_count,
        'structural_count': structural_count,
        'ontology_ratio': ontology_ratio
    }

