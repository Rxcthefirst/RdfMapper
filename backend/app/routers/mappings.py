"""Mappings router - handles mapping generation and management."""
from fastapi import APIRouter, HTTPException, Query, Response, Depends, Body
from typing import Optional
from sqlalchemy.orm import Session
import logging

from ..services.rdfmap_service import RDFMapService
from ..config import settings
from ..database import get_db
from ..models.project import Project

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/{project_id}/generate")
async def generate_mappings(
    project_id: str,
    target_class: Optional[str] = Query(None, description="Target ontology class URI"),
    base_iri: str = Query("http://example.org/", description="Base IRI for resources"),
    use_semantic: bool = Query(True, description="Use semantic matching"),
    min_confidence: float = Query(0.5, description="Minimum confidence threshold"),
    output_format: str = Query("inline", description="Output format: inline (v2 default), rml/ttl, rml/xml, yarrrml"),
    db: Session = Depends(get_db),
):
    """
    Generate automatic mappings between data and ontology.

    This endpoint analyzes the uploaded data and ontology files,
    then uses AI-powered matching to suggest column-to-property mappings.

    Output formats:
    - inline: v2 config with mapping inline (default, recommended)
    - rml/ttl: v2 config + external RML Turtle file (standards-compliant)
    - rml/xml: v2 config + external RML RDF/XML file
    - yarrrml: v2 config + external YARRRML file (human-friendly)
    """
    try:
        logger.info(f"Generating mappings for project {project_id} with format {output_format}")

        # Get project files from database
        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if not project.data_file:
            raise HTTPException(status_code=400, detail="No data file found for project")
        if not project.ontology_file:
            raise HTTPException(status_code=400, detail="No ontology file found for project")

        data_file = project.data_file
        ontology_file = project.ontology_file

        # Generate mappings
        service = RDFMapService(
            uploads_dir=settings.UPLOAD_DIR,
            data_dir=settings.DATA_DIR,
        )

        result = service.generate_mappings(
            project_id=project_id,
            ontology_file_path=ontology_file,
            data_file_path=data_file,
            target_class=target_class,
            base_iri=base_iri,
            use_semantic=use_semantic,
            min_confidence=min_confidence,
            output_format=output_format,
        )

        # Extract info from v2 or v1 config
        mapping_config = result.get("mapping_config", {})

        # Handle both v2 and v1 formats
        if "mapping" in mapping_config:
            # V2 format
            mapping_def = mapping_config["mapping"]
            base_iri_val = mapping_def.get("base_iri")
            sources = mapping_def.get("sources", [])
            target_class_val = sources[0].get("entity", {}).get("class") if sources else None
            column_count = len(sources[0].get("properties", {})) if sources else 0
        else:
            # V1 format (fallback)
            base_iri_val = mapping_config.get("defaults", {}).get("base_iri")
            sheets = mapping_config.get("sheets", [])
            target_class_val = sheets[0].get("row_resource", {}).get("class") if sheets else None
            column_count = len(sheets[0].get("columns", {})) if sheets else 0

        return {
            "status": "success",
            "project_id": project_id,
            "mapping_file": result["mapping_file"],
            "alignment_report": result["alignment_report"],
            "mapping_summary": result.get("mapping_summary"),
            "formatted_yaml": result.get("formatted_yaml"),
            "match_details": result["alignment_report"].get("match_details", []) if result.get("alignment_report") else [],
            "output_format": result.get("output_format", "unknown"),
            "mapping_preview": {
                "base_iri": base_iri_val,
                "target_class": target_class_val,
                "column_count": column_count,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating mappings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}")
async def get_mappings(project_id: str, raw: bool = False):
    """
    Get the current mapping configuration for a project.
    """
    try:
        from pathlib import Path
        import yaml

        # Check both DATA_DIR (generated) and UPLOAD_DIR (imported)
        mapping_file = Path(settings.DATA_DIR) / project_id / "mapping_config.yaml"
        if not mapping_file.exists():
            mapping_file = Path(settings.UPLOAD_DIR) / project_id / "mapping_config.yaml"
            if not mapping_file.exists():
                raise HTTPException(status_code=404, detail="No mappings found for project")

        if raw:
            return Response(content=mapping_file.read_text(), media_type="text/yaml")
        with open(mapping_file, 'r') as f:
            mapping_config = yaml.safe_load(f)
        return {
            "status": "success",
            "project_id": project_id,
            "mapping_config": mapping_config,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving mappings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/override")
async def override_mapping(project_id: str, column_name: str, property_uri: str):
    """Override a specific column mapping to a chosen property URI.
    Updates mapping_config.yaml (supports both v1 and v2 formats),
    sets matcher to manual_override, confidence to 1.0, and refreshes alignment_report match_details entry.
    """
    try:
        from pathlib import Path
        import yaml, json

        # Check both DATA_DIR (generated) and UPLOAD_DIR (imported)
        project_dir = Path(settings.DATA_DIR) / project_id
        mapping_file = project_dir / "mapping_config.yaml"
        if not mapping_file.exists():
            project_dir = Path(settings.UPLOAD_DIR) / project_id
            mapping_file = project_dir / "mapping_config.yaml"
            if not mapping_file.exists():
                raise HTTPException(status_code=404, detail="No mapping config found")

        raw = yaml.safe_load(mapping_file.read_text()) or {}

        # Detect format: v2 has 'mapping' key, v1 has 'sheets' key
        if 'mapping' in raw:
            # V2 format
            mapping_def = raw.get('mapping', {})

            if 'file' in mapping_def:
                # External mapping file (RML/YARRRML) - we can't override this easily
                raise HTTPException(
                    status_code=400,
                    detail="Cannot override mappings stored in external RML/YARRRML files. Please regenerate with inline format or edit the external file directly."
                )

            # Inline v2 format
            sources = mapping_def.get('sources', [])
            if not sources:
                raise HTTPException(status_code=400, detail="No sources in v2 mapping config")

            source = sources[0]
            properties = source.get('properties', {})

            # Update or add the property mapping
            # V2 format expects properties to be objects with 'predicate' field
            if column_name not in properties:
                properties[column_name] = {'predicate': property_uri}
            else:
                # Preserve existing structure but update predicate
                if isinstance(properties[column_name], dict):
                    properties[column_name]['predicate'] = property_uri
                else:
                    # If it was a string (shouldn't happen but handle it), convert to object
                    properties[column_name] = {'predicate': property_uri}

            source['properties'] = properties
            mapping_def['sources'][0] = source
            raw['mapping'] = mapping_def

        elif 'sheets' in raw:
            # V1 format (legacy)
            sheets = raw.get('sheets', [])
            if not sheets:
                raise HTTPException(status_code=400, detail="No sheets in mapping config")

            sheet0 = sheets[0]
            cols = sheet0.get('columns', {})

            if column_name not in cols:
                cols[column_name] = {'as': property_uri}
            else:
                cols[column_name]['as'] = property_uri

            sheet0['columns'] = cols
            raw['sheets'][0] = sheet0
        else:
            raise HTTPException(status_code=400, detail="Unknown mapping config format")

        # Persist YAML
        with open(mapping_file, 'w') as f:
            yaml.safe_dump(raw, f, sort_keys=False)

        # Load alignment report JSON if exists, update match_details entry
        report_json = project_dir / 'alignment_report.json'
        updated_match_details = []
        if report_json.exists():
            try:
                report = json.loads(report_json.read_text())
                md_list = report.get('match_details') or []
                found = False
                for md in md_list:
                    if md.get('column_name') == column_name:
                        md['matched_property'] = property_uri
                        md['match_type'] = 'manual_override'
                        md['confidence_score'] = 1.0
                        md['matcher_name'] = 'ManualOverride'
                        md['matched_via'] = 'User override'
                        found = True
                    updated_match_details.append(md)
                if not found:
                    updated_match_details.append({
                        'column_name': column_name,
                        'matched_property': property_uri,
                        'match_type': 'manual_override',
                        'confidence_score': 1.0,
                        'matcher_name': 'ManualOverride',
                        'matched_via': 'User override'
                    })
                report['match_details'] = updated_match_details
                with open(report_json, 'w') as f:
                    json.dump(report, f, indent=2)
            except Exception as e:
                logger.warning(f"Failed updating alignment report for override: {e}")
        return { 'status': 'success', 'column': column_name, 'property_uri': property_uri }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error overriding mapping: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/override-nested")
async def override_nested_mapping(
    project_id: str,
    parent_entity_index: int = Query(0, description="Index of parent entity in sources array"),
    nested_entity_index: int = Query(..., description="Index of nested entity"),
    column_name: str = Query(..., description="Column name in nested entity"),
    property_uri: str = Query(..., description="New property URI"),
):
    """Override a property mapping within a nested entity."""
    try:
        from pathlib import Path
        import yaml, json

        # Locate mapping config
        project_dir = Path(settings.DATA_DIR) / project_id
        mapping_file = project_dir / "mapping_config.yaml"
        if not mapping_file.exists():
            project_dir = Path(settings.UPLOAD_DIR) / project_id
            mapping_file = project_dir / "mapping_config.yaml"
            if not mapping_file.exists():
                raise HTTPException(status_code=404, detail="No mapping config found")

        raw = yaml.safe_load(mapping_file.read_text()) or {}

        # Only v2 inline format supports nested entities
        if 'mapping' not in raw:
            raise HTTPException(status_code=400, detail="Only v2 inline format supports nested entity overrides")

        mapping_def = raw.get('mapping', {})

        if 'file' in mapping_def:
            raise HTTPException(
                status_code=400,
                detail="Cannot override nested entities in external files"
            )

        sources = mapping_def.get('sources', [])
        if parent_entity_index >= len(sources):
            raise HTTPException(status_code=400, detail=f"Parent entity index {parent_entity_index} out of range")

        source = sources[parent_entity_index]
        # V2 uses 'relationships', not 'nested_entities'
        relationships = source.get('relationships', [])

        if nested_entity_index >= len(relationships):
            raise HTTPException(status_code=400, detail=f"Nested entity index {nested_entity_index} out of range")

        relationship = relationships[nested_entity_index]
        properties = relationship.get('properties', {})

        # V2 format expects properties to be objects with 'predicate' field
        if column_name not in properties:
            properties[column_name] = {'predicate': property_uri}
        else:
            # Preserve existing structure but update predicate
            if isinstance(properties[column_name], dict):
                properties[column_name]['predicate'] = property_uri
            else:
                # If it was a string (shouldn't happen but handle it), convert to object
                properties[column_name] = {'predicate': property_uri}

        relationship['properties'] = properties

        # Update back
        relationships[nested_entity_index] = relationship
        source['relationships'] = relationships
        sources[parent_entity_index] = source
        mapping_def['sources'] = sources
        raw['mapping'] = mapping_def

        # Persist
        with open(mapping_file, 'w') as f:
            yaml.safe_dump(raw, f, sort_keys=False)

        return {
            "status": "success",
            "parent_entity_index": parent_entity_index,
            "nested_entity_index": nested_entity_index,
            "column": column_name,
            "property_uri": property_uri
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error overriding nested mapping: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/add-nested-entity")
async def add_nested_entity(
    project_id: str,
    data: dict = Body(..., description="Nested entity configuration including parent_entity_index, join_column, target_class, iri_template, properties"),
):
    """Add a new nested entity relationship to a parent entity.

    Request body example:
    {
        "parent_entity_index": 0,
        "join_column": "BorrowerID",
        "target_class": "ex:Borrower",
        "iri_template": "{BorrowerID}",
        "properties": {
            "BorrowerName": "ex:name",
            "BorrowerSSN": "ex:ssn"
        }
    }
    """
    try:
        from pathlib import Path
        import yaml

        # Extract parameters from body
        parent_entity_index = data.get('parent_entity_index', 0)
        join_column = data.get('join_column')
        target_class = data.get('target_class')
        iri_template = data.get('iri_template')
        properties = data.get('properties', {})

        if not all([join_column, target_class, iri_template]):
            raise HTTPException(status_code=400, detail="Missing required fields: join_column, target_class, iri_template")

        # Locate mapping config
        project_dir = Path(settings.DATA_DIR) / project_id
        mapping_file = project_dir / "mapping_config.yaml"
        if not mapping_file.exists():
            project_dir = Path(settings.UPLOAD_DIR) / project_id
            mapping_file = project_dir / "mapping_config.yaml"
            if not mapping_file.exists():
                raise HTTPException(status_code=404, detail="No mapping config found")

        raw = yaml.safe_load(mapping_file.read_text()) or {}

        # Only v2 inline format
        if 'mapping' not in raw:
            raise HTTPException(status_code=400, detail="Only v2 inline format supports nested entities")

        mapping_def = raw.get('mapping', {})

        if 'file' in mapping_def:
            raise HTTPException(status_code=400, detail="Cannot add nested entities to external files")

        sources = mapping_def.get('sources', [])
        if parent_entity_index >= len(sources):
            raise HTTPException(status_code=400, detail=f"Parent entity index {parent_entity_index} out of range")

        source = sources[parent_entity_index]
        nested_entities = source.get('nested_entities', [])

        # Create new nested entity
        new_nested = {
            'join_condition': join_column,
            'target_class': target_class,
            'iri_template': iri_template,
            'properties': properties
        }

        nested_entities.append(new_nested)
        source['nested_entities'] = nested_entities
        sources[parent_entity_index] = source
        mapping_def['sources'] = sources
        raw['mapping'] = mapping_def

        # Persist
        with open(mapping_file, 'w') as f:
            yaml.safe_dump(raw, f, sort_keys=False)

        return {
            "status": "success",
            "parent_entity_index": parent_entity_index,
            "nested_entity_index": len(nested_entities) - 1,
            "nested_entity": new_nested
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding nested entity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}/nested-entity")
async def delete_nested_entity(
    project_id: str,
    parent_entity_index: int = Query(0, description="Index of parent entity"),
    nested_entity_index: int = Query(..., description="Index of nested entity to delete"),
):
    """Delete a nested entity relationship."""
    try:
        from pathlib import Path
        import yaml

        project_dir = Path(settings.DATA_DIR) / project_id
        mapping_file = project_dir / "mapping_config.yaml"
        if not mapping_file.exists():
            project_dir = Path(settings.UPLOAD_DIR) / project_id
            mapping_file = project_dir / "mapping_config.yaml"
            if not mapping_file.exists():
                raise HTTPException(status_code=404, detail="No mapping config found")

        raw = yaml.safe_load(mapping_file.read_text()) or {}

        if 'mapping' not in raw:
            raise HTTPException(status_code=400, detail="Only v2 format supports nested entities")

        mapping_def = raw.get('mapping', {})
        sources = mapping_def.get('sources', [])

        if parent_entity_index >= len(sources):
            raise HTTPException(status_code=400, detail="Parent entity index out of range")

        source = sources[parent_entity_index]
        nested_entities = source.get('nested_entities', [])

        if nested_entity_index >= len(nested_entities):
            raise HTTPException(status_code=400, detail="Nested entity index out of range")

        # Remove the nested entity
        deleted = nested_entities.pop(nested_entity_index)
        source['nested_entities'] = nested_entities
        sources[parent_entity_index] = source
        mapping_def['sources'] = sources
        raw['mapping'] = mapping_def

        # Persist
        with open(mapping_file, 'w') as f:
            yaml.safe_dump(raw, f, sort_keys=False)

        return {
            "status": "success",
            "deleted_entity": deleted
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting nested entity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/yarrrml")
async def get_yarrrml(project_id: str):
    """
    Get mapping configuration in YARRRML (YAML-based RML) format.

    YARRRML is the standard format for RDF Mapping Language (RML) specifications.
    It's compatible with tools like RMLMapper, RocketRML, Morph-KGC, and SDM-RDFizer.

    This endpoint converts the internal mapping format to standards-compliant YARRRML,
    including x-alignment extensions for AI-powered metadata.
    """
    try:
        from pathlib import Path
        import yaml

        # Check both DATA_DIR (generated) and UPLOAD_DIR (imported)
        project_dir = Path(settings.DATA_DIR) / project_id
        mapping_file = project_dir / "mapping_config.yaml"

        if not mapping_file.exists():
            project_dir = Path(settings.UPLOAD_DIR) / project_id
            mapping_file = project_dir / "mapping_config.yaml"
            if not mapping_file.exists():
                raise HTTPException(status_code=404, detail="No mappings found for project")

        # Load internal format
        with open(mapping_file, 'r') as f:
            internal_config = yaml.safe_load(f)

        # Convert to YARRRML
        from rdfmap.config.yarrrml_generator import internal_to_yarrrml

        # Try to load alignment report for x-alignment metadata
        alignment_report = None
        report_json = project_dir / 'alignment_report.json'
        if report_json.exists():
            try:
                import json
                with open(report_json, 'r') as f:
                    alignment_report = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load alignment report: {e}")

        # Generate YARRRML
        yarrrml = internal_to_yarrrml(internal_config, alignment_report)

        # Serialize as YAML
        yaml_content = yaml.dump(
            yarrrml,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True
        )

        return Response(
            content=yaml_content,
            media_type="text/yaml",
            headers={
                "Content-Disposition": f"attachment; filename={project_id}-mapping.yarrrml.yaml"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating YARRRML: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/rml")
async def get_rml(project_id: str, format: str = Query("turtle", description="RML format: turtle, xml")):
    """
    Get mapping configuration in RML (RDF Mapping Language) format.

    RML is the W3C standard for defining mappings from heterogeneous data to RDF.

    Supported formats:
    - turtle: RML in Turtle/TTL format (default, recommended)
    - xml: RML in RDF/XML format
    """
    try:
        from pathlib import Path
        import yaml

        # Check both DATA_DIR (generated) and UPLOAD_DIR (imported)
        project_dir = Path(settings.DATA_DIR) / project_id
        mapping_file = project_dir / "mapping_config.yaml"

        if not mapping_file.exists():
            project_dir = Path(settings.UPLOAD_DIR) / project_id
            mapping_file = project_dir / "mapping_config.yaml"
            if not mapping_file.exists():
                raise HTTPException(status_code=404, detail="No mappings found for project")

        # Load internal format
        with open(mapping_file, 'r') as f:
            internal_config = yaml.safe_load(f)

        # Convert to RML
        from rdfmap.config.rml_generator import internal_to_rml_graph

        # Try to load alignment report for metadata
        alignment_report = None
        report_json = project_dir / 'alignment_report.json'
        if report_json.exists():
            try:
                import json
                with open(report_json, 'r') as f:
                    alignment_report = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load alignment report: {e}")

        # Generate RML graph
        rml_graph = internal_to_rml_graph(internal_config, alignment_report)

        # Serialize to requested format
        if format == "xml":
            rml_content = rml_graph.serialize(format='xml')
            media_type = "application/rdf+xml"
            extension = "rdf"
        else:  # turtle (default)
            rml_content = rml_graph.serialize(format='turtle')
            media_type = "text/turtle"
            extension = "rml.ttl"

        return Response(
            content=rml_content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={project_id}-mapping.{extension}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating RML: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/evidence/{column_name}")
async def get_column_evidence(project_id: str, column_name: str):
    """
    Get rich evidence details for a specific column mapping.

    Returns comprehensive evidence including:
    - Evidence groups (semantic/ontological/structural)
    - Reasoning summary
    - Performance metrics
    - Alternate candidates
    - All matcher contributions
    """
    try:
        from pathlib import Path
        import json

        project_dir = Path(settings.DATA_DIR) / project_id
        report_json = project_dir / 'alignment_report.json'

        if not report_json.exists():
            raise HTTPException(
                status_code=404,
                detail="No alignment report found for project"
            )

        # Load alignment report
        report = json.loads(report_json.read_text())
        match_details = report.get('match_details', [])

        # Find the specific column
        column_detail = None
        for detail in match_details:
            if detail.get('column_name') == column_name:
                column_detail = detail
                break

        if not column_detail:
            raise HTTPException(
                status_code=404,
                detail=f"No evidence found for column '{column_name}'"
            )

        # Return rich evidence detail
        return {
            "status": "success",
            "project_id": project_id,
            "column_name": column_name,
            "evidence_detail": column_detail
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving evidence: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/evidence")
async def get_all_evidence(project_id: str):
    """
    Get all evidence details for all columns in the project.

    Returns the complete match_details array from the alignment report,
    which includes rich evidence for all mapped columns.
    """
    try:
        from pathlib import Path
        import json

        project_dir = Path(settings.DATA_DIR) / project_id
        report_json = project_dir / 'alignment_report.json'

        if not report_json.exists():
            raise HTTPException(
                status_code=404,
                detail="No alignment report found for project"
            )

        # Load alignment report
        report = json.loads(report_json.read_text())
        match_details = report.get('match_details', [])
        statistics = report.get('statistics', {})

        return {
            "status": "success",
            "project_id": project_id,
            "match_details": match_details,
            "statistics": {
                "total_columns": statistics.get('total_columns', 0),
                "mapped_columns": statistics.get('mapped_columns', 0),
                "average_confidence": statistics.get('average_confidence', 0),
                "matchers_fired_avg": statistics.get('matchers_fired_avg', 0),
                "avg_evidence_count": statistics.get('avg_evidence_count', 0),
                "ontology_validation_rate": statistics.get('ontology_validation_rate', 0)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving all evidence: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
