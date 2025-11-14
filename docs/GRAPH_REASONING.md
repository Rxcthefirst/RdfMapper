# Graph Reasoning - Deep Ontology Structure Analysis

## Overview

The Graph Reasoning feature provides sophisticated semantic analysis capabilities that leverage the full structural richness of OWL/RDFS ontologies. Instead of treating the ontology as a flat list of properties, this system understands and reasons about:

- **Class hierarchies** (rdfs:subClassOf relationships)
- **Property inheritance** from parent classes
- **Domain and range constraints** for type validation
- **Property relationships** (rdfs:subPropertyOf)
- **Object property chains** connecting entities
- **Semantic paths** through the knowledge graph

## Key Components

### 1. GraphReasoner

The core reasoning engine that navigates and analyzes ontology structure.

**Location:** `src/rdfmap/generator/graph_reasoner.py`

**Capabilities:**

- **Hierarchical Navigation:**
  - Find all ancestor classes (transitive superclasses)
  - Find all descendant classes (transitive subclasses)
  - Navigate class hierarchies with depth limits

- **Property Discovery:**
  - Get inherited properties from parent classes
  - Find properties by domain and range
  - Discover related properties through various relationships

- **Type Validation:**
  - Validate property compatibility with data types
  - Support flexible type matching (e.g., integer compatible with decimal)
  - Confidence scoring for type matches

- **Semantic Pathfinding:**
  - Find paths between classes through object properties
  - Calculate semantic distance
  - Support indirect property access patterns

**Example Usage:**

```python
from rdfmap.generator.graph_reasoner import GraphReasoner
from rdfmap.generator.ontology_analyzer import OntologyAnalyzer

# Load ontology
analyzer = OntologyAnalyzer("mortgage_ontology.ttl")

# Create reasoner
reasoner = GraphReasoner(
    analyzer.graph,
    analyzer.classes,
    analyzer.properties
)

# Get all properties available to a class (including inherited)
from rdflib import URIRef
mortgage_class = URIRef("http://example.com/MortgageLoan")
all_properties = reasoner.get_inherited_properties(mortgage_class)

# Find ancestors
ancestors = reasoner.get_all_ancestors(mortgage_class)
# Returns: [Loan, FinancialInstrument, ...]

# Validate type compatibility
property = analyzer.properties[URIRef("http://example.com/interestRate")]
is_valid, confidence = reasoner.validate_property_for_data_type(
    property,
    "xsd:decimal"
)
# Returns: (True, 1.0) - perfect match
```

### 2. GraphReasoningMatcher

A column-to-property matcher that uses ontology structure for intelligent matching.

**Location:** `src/rdfmap/generator/matchers/graph_matcher.py`

**Matching Strategy:**

1. **Type Validation:** Ensures data types are compatible with property ranges
2. **Structural Analysis:** Identifies foreign key patterns and related columns
3. **Context Scoring:** Evaluates properties based on their ontology position
4. **Label Similarity:** Falls back to label matching when structure doesn't help

**Scoring Factors:**

- **Data Type Compatibility (30% weight):** Hard constraint - rejects incompatible types
- **Structural Fit (25% weight):** Bonus for FK patterns, sibling property matches
- **Property Context (20% weight):** Well-defined properties with domain/range score higher
- **Label Similarity (25% weight):** Traditional label-based matching

**Example Usage:**

```python
from rdfmap.generator.matchers.graph_matcher import GraphReasoningMatcher
from rdfmap.generator.matchers.base import MatchContext

# Create matcher
matcher = GraphReasoningMatcher(
    reasoner=reasoner,
    enabled=True,
    threshold=0.6,
    validate_types=True,
    use_inheritance=True
)

# Match a column
from rdfmap.generator.data_analyzer import DataFieldAnalysis

column = DataFieldAnalysis(name="interest_rate")
column.inferred_type = "xsd:decimal"
column.sample_values = [0.0525, 0.045, 0.0375]

result = matcher.match(
    column=column,
    properties=list(analyzer.properties.values())
)

if result:
    print(f"Matched to: {result.property.label}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Match type: {result.match_type}")
```

### 3. InheritanceAwareMatcher

Specialized matcher that discovers properties inherited from parent classes.

**Use Case:** When mapping data to a specific class, automatically include properties from ancestor classes in the hierarchy.

**Example:**

If you're mapping data to `MortgageLoan` which extends `Loan` which extends `FinancialInstrument`, this matcher will find properties defined on any of those classes.

```python
from rdfmap.generator.matchers.graph_matcher import InheritanceAwareMatcher

matcher = InheritanceAwareMatcher(
    reasoner=reasoner,
    target_class="http://example.com/MortgageLoan",
    enabled=True,
    threshold=0.7
)

# Match a column
column = DataFieldAnalysis(name="principal_amount")
column.inferred_type = "xsd:decimal"

# Only provide direct MortgageLoan properties
direct_properties = [
    p for p in analyzer.properties.values()
    if p.domain == URIRef("http://example.com/MortgageLoan")
]

result = matcher.match(column, direct_properties)

# Will find 'principalAmount' even though it's defined on parent 'Loan' class
assert result.match_type == MatchType.INHERITED_PROPERTY
```

## Integration with Mapping Generator

To enable graph reasoning in your mapping workflow:

```python
from rdfmap.generator.matchers.factory import create_default_pipeline
from rdfmap.generator.ontology_analyzer import OntologyAnalyzer
from rdfmap.generator.graph_reasoner import GraphReasoner

# Load ontology
analyzer = OntologyAnalyzer("ontology.ttl")

# Create reasoner
reasoner = GraphReasoner(
    analyzer.graph,
    analyzer.classes,
    analyzer.properties
)

# Create pipeline with graph reasoning enabled
pipeline = create_default_pipeline(
    use_graph_reasoning=True,
    graph_reasoning_threshold=0.6,
    reasoner=reasoner
)

# Use pipeline in mapping generation...
```

## Benefits

### 1. Type Safety

The system validates that columns match properties with compatible data types:

- **Hard Type Validation:** Rejects mappings where types are incompatible
- **Flexible Matching:** Allows compatible types (e.g., integer → decimal)
- **Confidence Scoring:** Reflects type compatibility in match confidence

### 2. Semantic Awareness

Understanding the ontology structure enables:

- **Better Disambiguation:** Choose between similar properties based on context
- **Structural Validation:** Ensure mappings respect the ontology's semantic model
- **Relationship Discovery:** Find indirect connections through object properties

### 3. Inheritance Support

Automatically discovers properties from parent classes:

- **Complete Coverage:** Never miss properties due to class hierarchy
- **Explicit Tracking:** Marks inherited properties in match results
- **Hierarchical Understanding:** Respects object-oriented design patterns

### 4. Context-Aware Matching

Considers the broader ontology context:

- **Sibling Properties:** Bonus for columns that match multiple properties in same class
- **Domain Modeling:** Properties in well-defined classes score higher
- **FK Detection:** Recognizes foreign key patterns for object properties

## Configuration

### Matcher Configuration

```python
GraphReasoningMatcher(
    reasoner=reasoner,              # Required: GraphReasoner instance
    enabled=True,                    # Enable/disable matcher
    threshold=0.6,                   # Minimum confidence (0.0-1.0)
    validate_types=True,             # Enable type validation
    use_inheritance=True             # Consider inherited properties
)
```

### Pipeline Integration

```python
create_default_pipeline(
    use_graph_reasoning=True,              # Enable graph reasoning matcher
    graph_reasoning_threshold=0.6,         # Match threshold
    reasoner=reasoner,                     # GraphReasoner instance
    use_semantic=True,                     # Combine with semantic matching
    use_structural=True,                   # Combine with structural matching
    use_datatype=True                      # Combine with datatype matching
)
```

## Match Types

The system introduces two new match types:

- **`GRAPH_REASONING`**: Match found using ontology structure analysis
- **`INHERITED_PROPERTY`**: Property inherited from parent class

These appear in alignment reports alongside other match types (EXACT_LABEL, SEMANTIC_SIMILARITY, etc.).

## Performance Considerations

### Indexing

The GraphReasoner builds indexes on initialization:

- **Subclass Index:** Fast lookup of class hierarchies
- **Subproperty Index:** Fast lookup of property hierarchies
- **Domain/Range Index:** Fast lookup by type constraints

These indexes are built once and reused for all matching operations.

### Caching

Consider caching GraphReasoner instances:

```python
# Cache reasoner for reuse
from functools import lru_cache

@lru_cache(maxsize=1)
def get_reasoner(ontology_path: str) -> GraphReasoner:
    analyzer = OntologyAnalyzer(ontology_path)
    return GraphReasoner(
        analyzer.graph,
        analyzer.classes,
        analyzer.properties
    )
```

### Depth Limits

Traversal operations have configurable depth limits:

```python
# Limit recursion depth
ancestors = reasoner.get_all_ancestors(class_uri, max_depth=10)
path = reasoner.find_semantic_path(start, target, max_hops=3)
```

## Examples

### Example 1: Mortgage Loan Hierarchy

```
FinancialInstrument
  ├─ instrumentId: string
  └─ Loan (subClassOf FinancialInstrument)
      ├─ principalAmount: decimal
      ├─ interestRate: decimal
      └─ MortgageLoan (subClassOf Loan)
          ├─ loanNumber: string
          ├─ loanTerm: integer
          └─ hasBorrower → Borrower
```

**Mapping to MortgageLoan:**

| Column Name | Matched Property | Match Type | Notes |
|-------------|-----------------|------------|-------|
| loan_number | loanNumber | GRAPH_REASONING | Direct property |
| principal_amount | principalAmount | INHERITED_PROPERTY | From Loan |
| instrument_id | instrumentId | INHERITED_PROPERTY | From FinancialInstrument |
| borrower_id | hasBorrower | GRAPH_REASONING | FK pattern detected |

### Example 2: Type Validation

```python
# Column with decimal values
column = DataFieldAnalysis(name="interest_rate")
column.inferred_type = "xsd:decimal"

# Property with decimal range
property = ontology.properties[URIRef("ex:interestRate")]
property.range_type = XSD.decimal

# Validation passes with high confidence
is_valid, confidence = reasoner.validate_property_for_data_type(
    property, "xsd:decimal"
)
# Result: (True, 1.0)

# Column with string values
column2 = DataFieldAnalysis(name="interest_rate")
column2.inferred_type = "xsd:string"

# Validation fails - incompatible types
is_valid, confidence = reasoner.validate_property_for_data_type(
    property, "xsd:string"
)
# Result: (False, 0.0) or (True, 0.3) - very low confidence
```

### Example 3: Semantic Path Finding

```python
# Find path from MortgageLoan to borrower's properties
# Path: MortgageLoan → (hasBorrower) → Borrower → borrowerName

loan_class = URIRef("ex:MortgageLoan")
borrower_name_prop = URIRef("ex:borrowerName")

path = reasoner.find_semantic_path(
    start_class=loan_class,
    target_property=borrower_name_prop,
    max_hops=3
)

if path:
    print(f"Found path with {path.hops} hops")
    print(f"Confidence: {path.confidence:.2f}")
    print(f"Path type: {path.path_type}")
```

## Testing

Comprehensive test suites are included:

- **`tests/test_graph_reasoning.py`**: Tests for GraphReasoner core functionality
- **`tests/test_graph_matcher.py`**: Tests for matching strategies

Run tests:

```bash
pytest tests/test_graph_reasoning.py -v
pytest tests/test_graph_matcher.py -v
```

## Future Enhancements

Potential areas for expansion:

1. **Transitive Property Support:** Handle transitive relationships
2. **Property Chains:** Complex paths through multiple object properties  
3. **Cardinality Constraints:** Respect min/max cardinality restrictions
4. **SWRL Rules:** Support custom reasoning rules
5. **Named Individuals:** Reason about specific instances
6. **Equivalence Classes:** Handle owl:equivalentClass relationships

## See Also

- [Semantic Matching Documentation](SEMANTIC_MATCHING_IMPLEMENTATION.md)
- [Datatype Matcher Documentation](DATATYPE_MATCHER.md)
- [Quick Reference Guide](QUICK_REFERENCE.md)
- [OWL 2 Web Ontology Language Primer](https://www.w3.org/TR/owl2-primer/)

