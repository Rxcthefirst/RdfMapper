"""Semantic Model Data Mapper - Convert spreadsheet data to RDF triples."""

__version__ = "0.2.0"

# Export main classes and functions for easy access
from .generator.matchers import (
    create_default_pipeline,
    create_exact_only_pipeline,
    create_fast_pipeline,
    create_custom_pipeline,
    ColumnPropertyMatcher,
    MatcherPipeline,
)

__all__ = [
    "__version__",
    "create_default_pipeline",
    "create_exact_only_pipeline",
    "create_fast_pipeline",
    "create_custom_pipeline",
    "ColumnPropertyMatcher",
    "MatcherPipeline",
]

