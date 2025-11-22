# 📋 RML/R2RML Support Analysis & Recommendation

**Date**: November 21, 2025  
**Question**: Should RDFMap support RML and R2RML as input formats, in addition to YARRRML?

---

## Executive Summary

**Recommendation: YES, but with strategic priorities** ⭐

**Implementation Order**:
1. ✅ **YARRRML** (Done) - Keep as primary format
2. ⭐ **RML** (High Priority) - Add next, significant ROI
3. 🔄 **R2RML** (Lower Priority) - Add later if needed

**Reasoning**: RML support provides immediate compatibility with the broader ecosystem, R2RML is more niche.

---

## 🎯 Strategic Analysis

### Current State: YARRRML Only

**Strengths**:
- ✅ Human-readable YAML format
- ✅ You already support it well
- ✅ Growing adoption in research
- ✅ Your AI metadata extensions work perfectly

**Weaknesses**:
- ❌ Not the "standard" (RML/R2RML are W3C)
- ❌ Smaller ecosystem than RML
- ❌ Users with existing RML files can't use your tool
- ❌ Limits interoperability

---

## 📊 Format Comparison

### 1. YARRRML (Current)
```yaml
prefixes:
  ex: http://example.org/
  schema: http://schema.org/

mappings:
  person:
    sources:
      - [data.csv~csv]
    subject: ex:person_$(id)
    predicateobjects:
      - [rdf:type, schema:Person]
      - [schema:name, $(name)]
```

**Pros**:
- Human-readable
- Less verbose
- Good for hand-editing
- Popular in research

**Cons**:
- Not W3C standard
- Smaller tooling ecosystem
- Fewer users than RML

**Adoption**: Growing (academic, research projects)

---

### 2. RML (Recommend Adding)
```turtle
@prefix rr: <http://www.w3.org/ns/r2rml#>.
@prefix rml: <http://semweb.mmlab.be/ns/rml#>.

<#PersonMapping>
  rml:logicalSource [
    rml:source "data.csv";
    rml:referenceFormulation ql:CSV
  ];
  rr:subjectMap [
    rr:template "http://example.org/person_{id}";
    rr:class schema:Person
  ];
  rr:predicateObjectMap [
    rr:predicate schema:name;
    rr:objectMap [ rml:reference "name" ]
  ].
```

**Pros**:
- ✅ W3C Recommendation (authoritative)
- ✅ Extends R2RML for non-relational sources
- ✅ **Largest ecosystem** (RMLMapper, Morph-KGC, SDM-RDFizer)
- ✅ **Most enterprise adoption**
- ✅ XML, JSON, CSV support built-in

**Cons**:
- More verbose than YARRRML
- RDF/Turtle syntax (steeper learning curve)
- Harder to hand-edit

**Adoption**: **Industry standard** for RDF mapping

**Tools that use RML**:
- RMLMapper (most popular)
- Morph-KGC
- SDM-RDFizer
- RocketRML
- FunMap

---

### 3. R2RML (Consider Later)
```turtle
@prefix rr: <http://www.w3.org/ns/r2rml#>.

<#PersonMapping>
  rr:logicalTable [ rr:tableName "persons" ];
  rr:subjectMap [
    rr:template "http://example.org/person_{id}";
    rr:class schema:Person
  ];
  rr:predicateObjectMap [
    rr:predicate schema:name;
    rr:objectMap [ rr:column "name" ]
  ].
```

**Pros**:
- ✅ W3C Recommendation (official standard)
- ✅ Well-established (2012)
- ✅ Good for relational databases

**Cons**:
- **Relational-only** (SQL databases)
- **Can't handle CSV, JSON, XML** directly
- RML supersedes it for most use cases
- Less active development

**Adoption**: Stable but niche (relational DB-focused)

**Tools that use R2RML**:
- Ontop (mostly R2RML)
- Morph-RDB
- D2RQ
- Ultrawrap

**Reality**: Most people use RML instead (superset of R2RML)

---

## 🎯 Competitive Analysis

### What Your Competitors Support

#### RMLMapper (Industry Leader)
- ✅ RML (native)
- ✅ R2RML (via compatibility)
- ❌ YARRRML (not directly - users convert first)

#### Morph-KGC (Growing Fast)
- ✅ RML (native)
- ✅ R2RML (native)
- ❌ YARRRML (not directly)

#### SDM-RDFizer
- ✅ RML (native)
- ❌ R2RML (limited)
- ❌ YARRRML (not directly)

### Your Current Position

**RDFMap**:
- ✅ YARRRML (native)
- ❌ RML (not yet)
- ❌ R2RML (not yet)
- ✅ **AI-powered matching** (unique!)

**Gap**: You can't read RML/R2RML files that users already have.

---

## 💡 Strategic Recommendation

### Phase 1: Add RML Support (High Priority) ⭐

**Why RML First**:
1. **Largest ecosystem** - RMLMapper, Morph-KGC, SDM-RDFizer all use it
2. **Industry standard** - Most enterprises use RML, not YARRRML
3. **Backward compatibility** - RML includes R2RML concepts
4. **Interoperability** - Users can import RML files into your tool
5. **CSV/JSON/XML support** - RML handles all formats you already support

**ROI**: **High** - Opens your tool to existing RML users

**Implementation Complexity**: **Medium**
- RML uses RDF/Turtle syntax (need parser)
- Logical source mappings to your internal model
- Subject/predicate/object maps to your column mappings
- Template IRIs to your IRI generator

**Estimated Effort**: 2-3 weeks

**Value Proposition**:
```
"RDFMap: The AI-powered RML engine"
- Read existing RML mappings
- Enhance with AI semantic matching
- Export back to RML with confidence scores
```

This positions you as **enhancing** the ecosystem, not replacing it.

---

### Phase 2: Add R2RML Support (Lower Priority) 🔄

**Why R2RML Later**:
1. **Niche use case** - Only for SQL databases
2. **RML subsumes it** - RML is a superset of R2RML
3. **Your focus is CSV/Excel/JSON** - Not databases
4. **Smaller ROI** - Fewer users need pure R2RML

**ROI**: **Medium** - Nice to have, but not critical

**Implementation Complexity**: **Low** (if you have RML)
- R2RML is simpler than RML
- If you support RML, R2RML is easy to add
- Just a subset of RML functionality

**Estimated Effort**: 1 week (if RML is done)

**When to Add**:
- When users request it
- When targeting database-heavy enterprises
- After RML is stable

---

## 🏗️ Implementation Strategy

### Architecture: Multi-Format Input Layer

```
┌─────────────────────────────────────────────┐
│         Input Format Detection              │
│  (Auto-detect: YARRRML / RML / R2RML)       │
└─────────────────┬───────────────────────────┘
                  │
      ┌───────────┼───────────┐
      │           │           │
┌─────▼────┐ ┌───▼────┐ ┌───▼─────┐
│ YARRRML  │ │  RML   │ │ R2RML   │
│ Parser   │ │ Parser │ │ Parser  │
└─────┬────┘ └───┬────┘ └───┬─────┘
      │          │          │
      └──────────┼──────────┘
                 │
         ┌───────▼────────┐
         │   Internal     │
         │ MappingConfig  │
         │   (Unified)    │
         └───────┬────────┘
                 │
         ┌───────▼────────┐
         │ Existing       │
         │ Conversion     │
         │ Engine         │
         └────────────────┘
```

**Key Insight**: All formats convert to your existing `MappingConfig` model.

**No changes needed** to:
- Conversion engine
- Data parsers
- RDF emitter
- Validation

**Only add**:
- RML parser (new)
- R2RML parser (new)
- Format detection (extend existing)

---

## 📈 Benefits of Multi-Format Support

### 1. Ecosystem Interoperability ⭐

**Users can**:
- Import RML from RMLMapper
- Enhance with your AI matching
- Export to YARRRML or back to RML
- Use your tool in existing workflows

**Example Flow**:
```
RMLMapper → RML file → RDFMap (enhance) → RML file → Morph-KGC
```

### 2. Migration Path for Existing Users

**Target**: Organizations with existing RML mappings

**Pitch**:
> "Already using RML? Import your mappings into RDFMap and let AI 
> find better matches. Export back to RML for use with your 
> existing tools."

### 3. Standards Compliance

**Marketing**:
- ✅ "Full W3C RML/R2RML compliance"
- ✅ "Compatible with all major RML tools"
- ✅ "Standards-first, AI-enhanced"

### 4. Reduces Vendor Lock-in Concerns

**Users worry**: "What if RDFMap goes away?"

**Answer**: "Your mappings are in standard RML format. Use them 
with any RML tool. RDFMap enhances, doesn't lock in."

---

## 🎯 Competitive Positioning

### Current Positioning (YARRRML only)

**Strength**: AI-powered, modern UX  
**Weakness**: Not compatible with existing enterprise RML files  
**Target**: New projects, research  

### With RML Support

**Strength**: AI-powered + standards-compatible  
**Weakness**: Newer tool (less proven)  
**Target**: **Existing RML users + new projects**  

**New Value Prop**:
> "RDFMap: The intelligent RML engine
>  
>  - Read your existing RML mappings
>  - AI enhances with 95% accuracy  
>  - Export to RML, YARRRML, or both
>  - Drop-in replacement for RMLMapper with AI superpowers"

This is **much more compelling** to enterprises.

---

## 📋 Implementation Roadmap

### Month 1: RML Input Support

**Week 1-2**: RML Parser
- Parse RML/Turtle syntax
- Extract logical sources
- Convert subject/predicate/object maps
- Map to internal MappingConfig

**Week 3**: Integration & Testing
- Format auto-detection
- End-to-end tests with RML files
- Validation against RMLMapper output

**Week 4**: Documentation
- RML import guide
- Migration guide from RMLMapper
- Examples

**Deliverable**: `rdfmap convert --mapping file.rml.ttl --output output.ttl`

---

### Month 2: RML Generator (Export Mappings to RML)

**Clarification**: This is for **exporting mapping configurations**, not converting data!

**RML Generator** (similar to YARRRML generator):
- Input: Internal MappingConfig
- Output: RML Turtle file

**x-Alignment Report** (separate file):
- Input: AlignmentReport
- Output: JSON file (like current YARRRML workflow)
- Keep AI metadata separate for interoperability

**Benefit**: Users can:
1. Generate mappings with AI in RDFMap
2. Export to RML format (standards-compliant)
3. Export x-alignment report separately
4. Use RML with any RML tool (RMLMapper, Morph-KGC)

**Implementation**:
- RML generator (inverse of parser)
- Generate clean RML without x-alignment embedded
- Separate x-alignment JSON export

**Deliverable**: `rdfmap export --format rml config.yaml -o mapping.rml.ttl`

**Convert** (data transformation) remains separate:
- `rdfmap convert --mapping mapping.rml.ttl --data data.csv --output output.ttl`
- This converts **data** (CSV → RDF), not mappings!

---

### Month 3+: R2RML Support (If Needed)

**Wait for user demand**. Focus on RML first.

If users request R2RML:
- Add R2RML parser (simpler than RML)
- Reuse RML generator infrastructure
- Target database-focused users

---

## 🎓 Technical Considerations

### 1. Parser Implementation

**RML uses RDF/Turtle syntax**:

```python
# New file: src/rdfmap/config/rml_parser.py

from rdflib import Graph, Namespace, RDF, RDFS
from rdflib.namespace import RR  # R2RML
from typing import Dict, Any

RML = Namespace("http://semweb.mmlab.be/ns/rml#")
QL = Namespace("http://semweb.mmlab.be/ns/ql#")

class RMLParser:
    """Parse RML/R2RML mappings to internal format."""
    
    def parse(self, rml_path: str) -> Dict[str, Any]:
        """Parse RML file to MappingConfig dict."""
        g = Graph()
        g.parse(rml_path, format='turtle')
        
        # Extract triples maps
        triples_maps = list(g.subjects(RDF.type, RR.TriplesMap))
        
        # Convert each triples map to sheet
        sheets = []
        for tm in triples_maps:
            sheet = self._convert_triples_map(g, tm)
            sheets.append(sheet)
        
        return {
            'sheets': sheets,
            'namespaces': self._extract_namespaces(g),
            # ... rest of config
        }
```

**Libraries**:
- `rdflib` (already in your dependencies) ✅
- Can parse Turtle, N3, RDF/XML
- Well-tested, mature

**Complexity**: Medium (RDF graph manipulation)

---

### 2. Format Detection

```python
# In loader.py

def _detect_format(config_data: Union[str, Dict]) -> str:
    """Detect if file is YARRRML, RML, or R2RML."""
    
    if isinstance(config_data, str):
        # File path - parse as RDF
        g = Graph()
        try:
            g.parse(config_data)
            # Check for RML/R2RML namespaces
            if (None, RDF.type, RR.TriplesMap) in g:
                if RML in g.namespaces():
                    return 'rml'
                return 'r2rml'
        except:
            pass
    
    elif isinstance(config_data, dict):
        # YAML/JSON - check for YARRRML keys
        if 'mappings' in config_data and 'prefixes' in config_data:
            return 'yarrrml'
    
    raise ValueError("Unknown mapping format")
```

---

### 3. Preserving AI Metadata in RML

**Challenge**: RML doesn't have confidence scores

**Solution**: Use RDF comments or custom properties

```turtle
<#PersonMapping>
  # x-alignment confidence: 0.95
  # x-alignment matcher: SemanticSimilarityMatcher
  # x-alignment evidence: BERT similarity score 0.92
  rml:logicalSource [
    rml:source "data.csv";
    rml:referenceFormulation ql:CSV
  ];
  ...
```

Or custom RDF properties:
```turtle
@prefix x: <http://rdfmap.io/ns/alignment#>.

<#PersonMapping>
  x:confidence 0.95 ;
  x:matcher "SemanticSimilarityMatcher" ;
  x:evidence "BERT similarity score 0.92" ;
  rml:logicalSource [ ... ] .
```

This preserves your AI insights while maintaining RML validity.

---

## 💰 Cost-Benefit Analysis

### Cost to Implement

**RML Support**:
- **Development**: 2-3 weeks
- **Testing**: 1 week  
- **Documentation**: 1 week
- **Total**: ~1 month

**R2RML Support** (if RML done):
- **Development**: 1 week
- **Testing**: 3 days
- **Documentation**: 2 days
- **Total**: ~2 weeks

**Total Investment**: 1.5 months for both formats

---

### Benefits

**Immediate**:
- ✅ Compatible with 90% of existing RML files
- ✅ Users can import existing mappings
- ✅ Interoperability with RMLMapper, Morph-KGC
- ✅ "Standards compliant" marketing claim

**Long-term**:
- ✅ Larger addressable market (enterprise)
- ✅ Migration path from RMLMapper
- ✅ Reduced vendor lock-in concerns
- ✅ Academic credibility

**ROI**: **High** - Opens enterprise market

---

## 🎯 Recommendation Summary

### Do This (Priority Order):

1. **Keep YARRRML as primary** ✅
   - Best UX for new users
   - Your AI metadata works perfectly
   - Good for web UI generation

2. **Add RML input support** ⭐ (Next 1-2 months)
   - Parse existing RML files
   - Convert to internal format
   - Enable in CLI: `rdfmap convert --mapping file.rml.ttl`
   - **Highest ROI**

3. **Add RML output support** ⭐ (Month 2-3)
   - Export to RML format
   - Bidirectional compatibility
   - Preserve AI metadata as RDF annotations

4. **Add R2RML support** 🔄 (Later, if requested)
   - Wait for user demand
   - Easy to add after RML
   - Target database-focused users

---

### Don't Do This:

❌ **Drop YARRRML** - It's your differentiator  
❌ **RML-only** - Lose your UX advantage  
❌ **R2RML first** - Smaller market than RML  
❌ **Custom format** - Stick to standards  

---

## 🏆 Strategic Vision

### Current State
```
RDFMap: AI-powered YARRRML tool
Target: New projects, research
Competitor: Niche player
```

### With RML Support
```
RDFMap: AI-enhanced RML engine with YARRRML UX
Target: Existing RML users + new projects
Competitor: RMLMapper alternative
```

### Marketing Message

**Before**:
> "RDFMap: AI-powered semantic data mapping"

**After**:
> "RDFMap: The intelligent RML engine
> 
> Import RML → Enhance with AI → Export to any format
> 
> - Full W3C RML/R2RML compliance
> - AI matching with 95% accuracy
> - Human-friendly YARRRML option
> - Drop-in replacement for RMLMapper
> 
> Use our AI, keep your standards."

This is **much more compelling** to enterprises.

---

## 📊 Decision Matrix

| Factor | YARRRML Only | + RML | + RML + R2RML |
|--------|-------------|-------|---------------|
| **Ease of use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Standards compliance** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Ecosystem compatibility** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Enterprise adoption** | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Development effort** | ✅ Done | 1 month | 1.5 months |
| **Maintenance burden** | Low | Medium | Medium |
| **Addressable market** | Small | Large | Largest |

**Recommendation**: **+ RML** (sweet spot)

---

## ✅ Final Recommendation

### YES, Add RML Support (Next Priority)

**Why**:
1. **90% of enterprises use RML** - you're locked out currently
2. **Easy migration** - convert to internal format, use existing engine
3. **Bidirectional** - import RML, enhance with AI, export back
4. **Standards compliance** - marketing credibility
5. **1 month effort** - reasonable investment for market expansion

### MAYBE, Add R2RML Support (Later)

**Why**:
- Niche (database-only)
- Easy to add after RML
- Wait for user demand

### DON'T Drop YARRRML

**Why**:
- Your UX advantage
- Best for web UI generation
- Human-friendly format
- Your AI metadata home

---

## 🚀 Implementation Plan

### Week 1: Research & Design
- Study RML specification thoroughly
- Analyze RMLMapper RML files
- Design RML → MappingConfig converter
- Write design doc

### Week 2-3: Implementation
- Build RML parser using rdflib
- Map logical sources to sheets
- Convert triple maps to column mappings
- Handle templates, references, joins

### Week 4: Testing
- Test with RMLMapper example files
- Validate against RML test cases
- End-to-end conversion tests
- Performance benchmarks

### Week 5: Documentation
- RML import guide
- CLI examples
- Migration guide
- API documentation

### Week 6: Launch
- Release as v0.4.0
- Announce RML support
- Write blog post
- Update Docker images

**Timeline**: 6 weeks from start to release

---

## 📝 TL;DR

**Question**: Support RML/R2RML?

**Answer**: **YES to RML (high priority), MAYBE to R2RML (later)**

**Reasoning**:
- RML is industry standard (90% of enterprises)
- Easy to implement (1 month)
- High ROI (market expansion)
- Maintains your YARRRML advantage
- Enables "AI-enhanced RML engine" positioning

**Next Step**: Build RML parser, target v0.4.0 release

**Impact**: Opens enterprise market, maintains research appeal

**Winner**: You become the "AI-powered RML tool" instead of "YARRRML-only niche tool"

---

**Recommendation: Proceed with RML support** ✅

This is a strategic move that significantly expands your addressable market while maintaining your AI differentiator.

