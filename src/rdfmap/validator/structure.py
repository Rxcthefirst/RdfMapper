"""Ontology structural validation (domain/range & datatype compliance).

Provides a focused structural check separate from SHACL shapes and closed-world ontology term checks.
"""
from rdflib import Graph, RDF, RDFS, Literal, XSD
from pathlib import Path
from typing import Optional

from ..models.errors import ValidationReport, ValidationResult

def structural_validate(
    data_graph: Graph,
    ontology_graph: Optional[Graph] = None,
    ontology_file: Optional[Path] = None,
    sample_limit: int = 5,
) -> ValidationReport:
    """Validate structural compliance:
    - Domain: subjects of triples using property p should be instance of declared domain class
    - Range: objects of triples using property p should match declared range (class or datatype)

    Returns ValidationReport where each violation is a ValidationResult.
    compliance_rate is added via results_graph textual serialization omitted.
    """
    if ontology_graph is None:
        if ontology_file is None:
            raise ValueError("ontology_graph or ontology_file must be provided for structural validation")
        ontology_graph = Graph()
        ontology_graph.parse(ontology_file)

    # Build domain/range index
    prop_domains = {}
    prop_ranges = {}
    for s,_,o in ontology_graph.triples((None, RDFS.domain, None)):
        prop_domains.setdefault(s, set()).add(o)
    for s,_,o in ontology_graph.triples((None, RDFS.range, None)):
        prop_ranges.setdefault(s, set()).add(o)

    # Cache types in data graph
    type_cache = {}
    for s,_,o in data_graph.triples((None, RDF.type, None)):
        type_cache.setdefault(s, set()).add(o)

    violations: list[ValidationResult] = []
    checked = 0

    def short(u):
        if isinstance(u, Literal):
            return f'"{u}"^^{u.datatype}' if u.datatype else f'"{u}"'
        txt = str(u)
        return txt.split('#')[-1].split('/')[-1]

    for s,p,o in data_graph:
        checked += 1
        # Domain
        if p in prop_domains:
            subj_types = type_cache.get(s, set())
            expected = prop_domains[p]
            if expected and not (subj_types & expected):
                violations.append(ValidationResult(
                    focus_node=str(s),
                    result_path=str(p),
                    result_message=f"Domain violation: subject {short(s)} lacks required type for property {short(p)} (expected one of {[short(x) for x in expected]})",
                    severity="Violation",
                    source_constraint="domain-constraint",
                ))
        # Range
        if p in prop_ranges:
            expected_ranges = prop_ranges[p]
            if isinstance(o, Literal):
                literal_dt = o.datatype or XSD.string
                datatype_expected = {r for r in expected_ranges if str(r).startswith(str(XSD))}
                if datatype_expected and literal_dt not in datatype_expected:
                    violations.append(ValidationResult(
                        focus_node=str(s),
                        result_path=str(p),
                        result_message=f"Range datatype violation on {short(p)}: {literal_dt} not in {[str(x) for x in datatype_expected]}",
                        severity="Violation",
                        source_constraint="range-constraint",
                    ))
            else:
                obj_types = type_cache.get(o, set())
                class_expected = {r for r in expected_ranges if not str(r).startswith(str(XSD))}
                if class_expected and not (obj_types & class_expected):
                    violations.append(ValidationResult(
                        focus_node=str(o),
                        result_path=str(p),
                        result_message=f"Range class violation: object {short(o)} lacks required type for property {short(p)} (expected one of {[short(x) for x in class_expected]})",
                        severity="Violation",
                        source_constraint="range-constraint",
                    ))

    report = ValidationReport(
        conforms=len(violations) == 0,
        results=violations,
        results_graph=None,
    )
    return report

