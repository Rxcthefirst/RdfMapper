"""Mappings router - handles mapping generation and management."""
from fastapi import APIRouter, HTTPException, Query, Response
from typing import Optional
import logging

from ..services.rdfmap_service import RDFMapService
from ..config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/{project_id}/generate")
async def generate_mappings(
    project_id: str,
    target_class: Optional[str] = Query(None, description="Target ontology class URI"),
    base_iri: str = Query("http://example.org/", description="Base IRI for resources"),
    use_semantic: bool = Query(True, description="Use semantic matching"),
    min_confidence: float = Query(0.5, description="Minimum confidence threshold"),
):
    """
    Generate automatic mappings between data and ontology.

    This endpoint analyzes the uploaded data and ontology files,
    then uses AI-powered matching to suggest column-to-property mappings.
    """
    try:
        logger.info(f"Generating mappings for project {project_id}")

        # Get project files from projects router storage
        # For now, we'll construct paths - in production, query from database
        from pathlib import Path
        project_dir = Path(settings.UPLOAD_DIR) / project_id

        # Find data and ontology files
        data_files = list(project_dir.glob("data.*"))
        ontology_files = list(project_dir.glob("ontology.*"))

        if not data_files:
            raise HTTPException(status_code=400, detail="No data file found for project")
        if not ontology_files:
            raise HTTPException(status_code=400, detail="No ontology file found for project")

        data_file = str(data_files[0])
        ontology_file = str(ontology_files[0])

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
        )

        sheet_columns = 0
        if isinstance(result.get("mapping_config"), dict):
            sheets = result["mapping_config"].get("sheets", [])
            if sheets:
                sheet_columns = len(sheets[0].get("columns", {}))
        return {
            "status": "success",
            "project_id": project_id,
            "mapping_file": result["mapping_file"],
            "alignment_report": result["alignment_report"],
            "mapping_summary": result.get("mapping_summary"),
            "formatted_yaml": result.get("formatted_yaml"),
            "match_details": result["alignment_report"].get("match_details", []) if result.get("alignment_report") else [],
            "mapping_preview": {
                "base_iri": result["mapping_config"].get("defaults", {}).get("base_iri"),
                "target_class": result["mapping_config"].get("sheets", [{}])[0].get("row_resource", {}).get("class"),
                "column_count": sheet_columns,
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
        mapping_file = Path(settings.DATA_DIR) / project_id / "mapping_config.yaml"
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
    Updates mapping_config.yaml, sets matcher to manual_override, confidence to 1.0, and refreshes alignment_report match_details entry.
    """
    try:
        from pathlib import Path
        import yaml, json
        project_dir = Path(settings.DATA_DIR) / project_id
        mapping_file = project_dir / "mapping_config.yaml"
        if not mapping_file.exists():
            raise HTTPException(status_code=404, detail="No mapping config found")
        raw = yaml.safe_load(mapping_file.read_text()) or {}
        # Only single-sheet support for override currently
        sheets = raw.get('sheets') or []
        if not sheets:
            raise HTTPException(status_code=400, detail="No sheets in mapping config")
        sheet0 = sheets[0]
        cols = sheet0.get('columns') or {}
        if column_name not in cols:
            # If column not present, create minimal mapping entry
            cols[column_name] = { 'as': property_uri }
        else:
            cols[column_name]['as'] = property_uri
        sheet0['columns'] = cols
        raw['sheets'][0] = sheet0
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

        project_dir = Path(settings.DATA_DIR) / project_id
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
