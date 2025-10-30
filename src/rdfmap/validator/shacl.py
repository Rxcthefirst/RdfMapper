"""SHACL validation integration."""

import json
from pathlib import Path
from typing import Optional

from pyshacl import validate
from rdflib import Graph, RDF, RDFS, OWL
from rdflib.namespace import Namespace

from ..models.errors import ValidationReport, ValidationResult


def validate_rdf(
    data_graph: Graph,
    shapes_graph: Optional[Graph] = None,
    shapes_file: Optional[Path] = None,
    inference: Optional[str] = None,
) -> ValidationReport:
    """Validate RDF data against SHACL shapes.
    
    Args:
        data_graph: RDF graph to validate
        shapes_graph: SHACL shapes graph (optional if shapes_file provided)
        shapes_file: Path to SHACL shapes file (optional if shapes_graph provided)
        inference: Inference mode (rdfs, owlrl, both, none)
        
    Returns:
        Validation report
        
    Raises:
        ValueError: If neither shapes_graph nor shapes_file is provided
    """
    if not shapes_graph and not shapes_file:
        raise ValueError("Either shapes_graph or shapes_file must be provided")
    
    # Load shapes from file if needed
    if not shapes_graph and shapes_file:
        shapes_graph = Graph()
        shapes_graph.parse(shapes_file)
    
    # Run validation
    conforms, results_graph, results_text = validate(
        data_graph,
        shacl_graph=shapes_graph,
        inference=inference,
        abort_on_first=False,
        allow_infos=True,
        allow_warnings=True,
    )
    
    # Parse results
    validation_results = _parse_validation_results(results_graph)
    
    return ValidationReport(
        conforms=conforms,
        results=validation_results,
        results_graph=results_graph.serialize(format="turtle") if results_graph else None,
    )


def _parse_validation_results(results_graph: Graph) -> list[ValidationResult]:
    """Parse pyshacl validation results graph.
    
    Args:
        results_graph: RDF graph containing validation results
        
    Returns:
        List of validation results
    """
    from rdflib import RDF, Namespace
    from rdflib.namespace import SH
    
    results = []
    
    # Query for validation results
    for result in results_graph.subjects(RDF.type, SH.ValidationResult):
        focus_node = None
        result_path = None
        message = None
        severity = None
        source_constraint = None
        
        # Extract properties
        for s, p, o in results_graph.triples((result, None, None)):
            if p == SH.focusNode:
                focus_node = str(o)
            elif p == SH.resultPath:
                result_path = str(o)
            elif p == SH.resultMessage:
                message = str(o)
            elif p == SH.resultSeverity:
                severity = str(o).split("#")[-1]  # Extract local name
            elif p == SH.sourceConstraintComponent:
                source_constraint = str(o)
        
        if focus_node and message:
            results.append(
                ValidationResult(
                    focus_node=focus_node,
                    result_path=result_path,
                    result_message=message,
                    severity=severity or "Violation",
                    source_constraint=source_constraint,
                )
            )
    
    return results


def write_validation_report(report: ValidationReport, output_path: Path) -> None:
    """Write validation report to JSON file.
    
    Args:
        report: Validation report
        output_path: Path to output file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report_dict = report.model_dump(exclude={"results_graph"})
    
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, default=str)


def validate_against_ontology(
    data_graph: Graph,
    ontology_graph: Optional[Graph] = None,
    ontology_file: Optional[Path] = None,
) -> ValidationReport:
    """Validate that data graph only uses properties and classes defined in the ontology.
    
    This performs "closed world" validation to catch typos and undefined terms.
    
    Args:
        data_graph: RDF graph to validate
        ontology_graph: Ontology graph (optional if ontology_file provided)
        ontology_file: Path to ontology file (optional if ontology_graph provided)
        
    Returns:
        Validation report
        
    Raises:
        ValueError: If neither ontology_graph nor ontology_file is provided
    """
    if not ontology_graph and not ontology_file:
        raise ValueError("Either ontology_graph or ontology_file must be provided")
    
    # Load ontology from file if needed
    if not ontology_graph and ontology_file:
        ontology_graph = Graph()
        ontology_graph.parse(ontology_file)
    
    results = []
    
    # Get all defined classes in ontology
    defined_classes = set()
    for cls in ontology_graph.subjects(RDF.type, OWL.Class):
        defined_classes.add(str(cls))
    for cls in ontology_graph.subjects(RDF.type, RDFS.Class):
        defined_classes.add(str(cls))
    
    # Get all defined properties in ontology
    defined_properties = set()
    for prop in ontology_graph.subjects(RDF.type, OWL.ObjectProperty):
        defined_properties.add(str(prop))
    for prop in ontology_graph.subjects(RDF.type, OWL.DatatypeProperty):
        defined_properties.add(str(prop))
    for prop in ontology_graph.subjects(RDF.type, RDF.Property):
        defined_properties.add(str(prop))
    
    # Exclude RDF/RDFS/OWL built-in properties and types
    builtin_properties = {
        str(RDF.type),
        str(RDFS.label),
        str(RDFS.comment),
        str(RDFS.seeAlso),
        str(RDFS.isDefinedBy),
    }
    
    # Check all predicates used in data
    used_predicates = set()
    for s, p, o in data_graph:
        pred_str = str(p)
        # Skip RDF namespace predicates (rdf:type, etc.)
        if pred_str.startswith("http://www.w3.org/1999/02/22-rdf-syntax-ns#"):
            continue
        if pred_str.startswith("http://www.w3.org/2000/01/rdf-schema#"):
            continue
        if pred_str.startswith("http://www.w3.org/2002/07/owl#"):
            continue
        if pred_str in builtin_properties:
            continue
        
        used_predicates.add(pred_str)
        
        # Check if property is defined
        if pred_str not in defined_properties:
            results.append(
                ValidationResult(
                    focus_node=str(s),
                    result_path=pred_str,
                    result_message=f"Property '{pred_str}' is not defined in the ontology",
                    severity="Violation",
                    source_constraint="ontology-closed-world",
                )
            )
    
    # Check all classes used in data
    for s, p, o in data_graph.triples((None, RDF.type, None)):
        class_str = str(o)
        # Skip built-in RDF/RDFS/OWL classes
        if class_str.startswith("http://www.w3.org/1999/02/22-rdf-syntax-ns#"):
            continue
        if class_str.startswith("http://www.w3.org/2000/01/rdf-schema#"):
            continue
        if class_str.startswith("http://www.w3.org/2002/07/owl#"):
            continue
        
        # Check if class is defined
        if class_str not in defined_classes:
            results.append(
                ValidationResult(
                    focus_node=str(s),
                    result_path=str(RDF.type),
                    result_message=f"Class '{class_str}' is not defined in the ontology",
                    severity="Violation",
                    source_constraint="ontology-closed-world",
                )
            )
    
    return ValidationReport(
        conforms=len(results) == 0,
        results=results,
        results_graph=None,
    )
