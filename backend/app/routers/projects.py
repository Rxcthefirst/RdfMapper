"""Projects API router."""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, Response
from typing import List
from pathlib import Path
from sqlalchemy.orm import Session
import shutil
import uuid
import logging

from ..schemas.project import ProjectCreate, ProjectResponse
from ..config import settings
from ..database import get_db
from ..models.project import Project

router = APIRouter()
logger = logging.getLogger(__name__)

# Helper to fetch project or 404
def _get_project(db: Session, project_id: str) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.post("/", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project."""
    project_id = str(uuid.uuid4())

    # Create database record
    db_project = Project(
        id=project_id,
        name=project.name,
        description=project.description,
        status="created",
        data_file=None,
        ontology_file=None,
        config={},
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    # Create project directory
    project_dir = Path(settings.UPLOAD_DIR) / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    return {
        "id": db_project.id,
        "name": db_project.name,
        "description": db_project.description,
        "status": db_project.status,
        "data_file": db_project.data_file,
        "ontology_file": db_project.ontology_file,
        "config": db_project.config,
    }


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all projects."""
    projects = db.query(Project).offset(skip).limit(limit).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "status": p.status,
            "data_file": p.data_file,
            "ontology_file": p.ontology_file,
            "config": p.config,
        }
        for p in projects
    ]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    """Get a specific project."""
    project = _get_project(db, project_id)

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "data_file": project.data_file,
        "ontology_file": project.ontology_file,
        "config": project.config,
    }


@router.delete("/{project_id}")
async def delete_project(project_id: str, db: Session = Depends(get_db)):
    """Delete a project."""
    project = _get_project(db, project_id)

    # Delete project directory
    project_dir = Path(settings.UPLOAD_DIR) / project_id
    if project_dir.exists():
        shutil.rmtree(project_dir)

    # Delete database record
    db.delete(project)
    db.commit()

    return {"message": "Project deleted successfully"}


@router.post("/{project_id}/upload-data")
async def upload_data_file(
    project_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload data file (CSV, Excel, JSON, XML)."""
    project = _get_project(db, project_id)

    # Validate file type
    allowed_extensions = [".csv", ".xlsx", ".json", ".xml"]
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # Save file with original filename
    project_dir = Path(settings.UPLOAD_DIR) / project_id
    original_filename = Path(file.filename).name
    file_path = project_dir / original_filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Update project in database
    project.data_file = str(file_path)
    project.status = "data_uploaded" if not project.ontology_file else "ready"
    db.commit()

    return {
        "message": "Data file uploaded successfully",
        "file_path": str(file_path),
        "file_size": file_path.stat().st_size,
    }


@router.post("/{project_id}/upload-ontology")
async def upload_ontology_file(
    project_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload ontology file (TTL, OWL, RDF/XML)."""
    project = _get_project(db, project_id)

    # Validate file type
    allowed_extensions = [".ttl", ".owl", ".rdf"]
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # Save file with original filename
    project_dir = Path(settings.UPLOAD_DIR) / project_id
    original_filename = Path(file.filename).name
    file_path = project_dir / original_filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Update project in database
    project.ontology_file = str(file_path)
    project.status = "ontology_uploaded" if not project.data_file else "ready"
    db.commit()

    return {
        "message": "Ontology file uploaded successfully",
        "file_path": str(file_path),
        "file_size": file_path.stat().st_size,
    }


@router.post("/{project_id}/upload-shapes")
async def upload_shapes_file(
    project_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload SHACL shapes file and associate it with the project (stored in project.config)."""
    project = _get_project(db, project_id)

    allowed_extensions = [".ttl", ".rdf", ".owl", ".trig", ".n3"]
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}")

    project_dir = Path(settings.UPLOAD_DIR) / project_id
    original_filename = Path(file.filename).name
    file_path = project_dir / original_filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Update project config
    cfg = dict(project.config or {})
    cfg['shapes_file'] = str(file_path)
    project.config = cfg
    db.commit()

    return {"message": "Shapes file uploaded successfully", "file_path": str(file_path)}


@router.post("/{project_id}/upload-skos")
async def upload_skos_file(
    project_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a SKOS vocabulary file and associate it with the project (kept as a list in project.config['skos_files'])."""
    project = _get_project(db, project_id)

    allowed_extensions = [".ttl", ".rdf", ".owl", ".trig", ".n3"]
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}")

    project_dir = Path(settings.UPLOAD_DIR) / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    # Preserve original filename, add increment only if duplicate
    original_filename = Path(file.filename).name
    file_stem = Path(original_filename).stem
    file_ext = Path(original_filename).suffix

    target = project_dir / original_filename
    idx = 1
    while target.exists():
        target = project_dir / f"{file_stem}-{idx}{file_ext}"
        idx += 1

    with open(target, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    cfg = dict(project.config or {})
    skos_files = list(cfg.get('skos_files', []) or [])
    skos_files.append(str(target))
    cfg['skos_files'] = skos_files
    project.config = cfg
    db.commit()

    return {"message": "SKOS file uploaded successfully", "file_path": str(target), "total_skos_files": len(skos_files)}


@router.post("/{project_id}/upload-existing-mapping")
async def upload_existing_mapping(
    project_id: str,
    file: UploadFile = File(...),
    chunk_size: int = Query(10000, description="Chunk size for processing"),
    on_error: str = Query("report", description="Error handling: report, skip, fail"),
    skip_empty_values: bool = Query(True, description="Skip empty values"),
    aggregate_duplicates: bool = Query(True, description="Aggregate duplicate triples"),
    db: Session = Depends(get_db),
):
    """Upload existing RML or YARRRML mapping file and create v2 config wrapper."""
    import yaml
    project = _get_project(db, project_id)

    # Validate file type
    allowed_extensions = [".ttl", ".rdf", ".nt", ".n3", ".xml", ".yaml", ".yml"]
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # Determine format
    is_rml = file_ext in ['.ttl', '.rdf', '.nt', '.n3', '.xml']
    format_name = "RML" if is_rml else "YARRRML"

    # Save mapping file - preserve original filename
    project_dir = Path(settings.UPLOAD_DIR) / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    # Use original filename to preserve user's naming convention
    original_filename = Path(file.filename).name
    mapping_path = project_dir / original_filename

    with open(mapping_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Create v2 config wrapper with RELATIVE paths and user-configured options
    v2_config = {
        'options': {
            'on_error': on_error,
            'skip_empty_values': skip_empty_values,
            'chunk_size': chunk_size,
            'aggregate_duplicates': aggregate_duplicates,
            'output_format': 'ttl'
        },
        'mapping': {
            'file': original_filename  # Just filename, not full path
        }
    }

    # Add ontology import if exists - use RELATIVE path
    if project.ontology_file:
        # Convert absolute path to just filename (they're in same directory)
        ontology_filename = Path(project.ontology_file).name
        v2_config['imports'] = [ontology_filename]

    # Save config
    config_path = project_dir / "mapping_config.yaml"
    with open(config_path, 'w') as f:
        f.write("# ════════════════════════════════════════════════════════════════════════════════\n")
        f.write("# RDFMap v2 Configuration (Imported Existing Mapping)\n")
        f.write("# ════════════════════════════════════════════════════════════════════════════════\n")
        f.write("#\n")
        f.write("# Created by: Web UI import\n")
        f.write(f"# Format: v2 + External {format_name}\n")
        f.write(f"# Mapping file: {original_filename}\n")
        if project.ontology_file:
            f.write(f"# Ontology file: {ontology_filename}\n")
        f.write("#\n")
        f.write("# ════════════════════════════════════════════════════════════════════════════════\n\n")
        yaml.dump(v2_config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    return {
        "message": f"{format_name} mapping imported successfully",
        "mapping_file": str(mapping_path),
        "config_file": str(config_path),
        "format": format_name
    }


@router.get("/{project_id}/data-preview")
async def get_data_preview(project_id: str, limit: int = 10, db: Session = Depends(get_db)):
    """Get preview of data file (first N rows) with analysis."""
    project = _get_project(db, project_id)

    if not project.data_file:
        raise HTTPException(status_code=400, detail="No data file uploaded")

    try:
        from ..services.rdfmap_service import RDFMapService
        from rdfmap.parsers.data_source import create_parser

        data_file = str(project.data_file)

        service = RDFMapService(uploads_dir=settings.UPLOAD_DIR, data_dir=settings.DATA_DIR)
        analysis = service.analyze_data_file(data_file)

        parser = create_parser(Path(data_file))
        dataframes = list(parser.parse())

        rows = []
        if dataframes:
            df = dataframes[0]
            rows = df.head(limit).to_dicts()

        return {
            **analysis,
            "rows": rows,
            "showing": len(rows),
        }
    except Exception as e:
        logger.error(f"Error in data preview: {e}", exc_info=True)
        # Return error in response instead of raising
        return {
            "error": str(e),
            "columns": [],
            "rows": [],
            "total_rows": 0,
            "showing": 0,
        }


@router.get("/{project_id}/ontology-analysis")
async def get_ontology_analysis(project_id: str, db: Session = Depends(get_db)):
    """Get analysis of the uploaded ontology using persisted project in DB."""
    project = _get_project(db, project_id)

    if not project.ontology_file:
        raise HTTPException(status_code=400, detail="No ontology file uploaded")

    try:
        from ..services.rdfmap_service import RDFMapService
        ontology_file = str(project.ontology_file)
        service = RDFMapService(uploads_dir=settings.UPLOAD_DIR, data_dir=settings.DATA_DIR)
        analysis = service.analyze_ontology(ontology_file)
        return analysis
    except Exception as e:
        logger.error(f"Error analyzing ontology: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error analyzing ontology: {str(e)}")

@router.patch("/{project_id}/settings")
async def update_project_settings(project_id: str, payload: dict, db: Session = Depends(get_db)):
    """Update project settings (e.g., reasoning toggle)."""
    project = _get_project(db, project_id)
    cfg = dict(project.config or {})
    if 'enable_reasoning' in payload:
        cfg['enable_reasoning'] = bool(payload['enable_reasoning'])
    project.config = cfg
    db.commit()
    return {"message": "Settings updated", "config": cfg}

@router.delete("/{project_id}/skos")
async def remove_skos_file(project_id: str, file: str, db: Session = Depends(get_db)):
    """Remove a SKOS vocabulary file reference (and delete file)."""
    project = _get_project(db, project_id)
    cfg = dict(project.config or {})
    skos_files = list(cfg.get('skos_files', []) or [])
    if file in skos_files:
        skos_files.remove(file)
        cfg['skos_files'] = skos_files
        project.config = cfg
        db.commit()
        try:
            Path(file).unlink(missing_ok=True)
        except Exception:
            pass
        return {"message": "SKOS file removed", "remaining": skos_files}
    raise HTTPException(status_code=404, detail="SKOS file not found")

@router.delete("/{project_id}/shapes")
async def remove_shapes_file(project_id: str, db: Session = Depends(get_db)):
    """Remove SHACL shapes file reference (and delete file)."""
    project = _get_project(db, project_id)
    cfg = dict(project.config or {})
    shapes_file = cfg.pop('shapes_file', None)
    project.config = cfg
    db.commit()
    if shapes_file:
        try:
            Path(shapes_file).unlink(missing_ok=True)
        except Exception:
            pass
    return {"message": "Shapes file removed", "config": cfg}


@router.get("/{project_id}/files/{filename}")
async def get_project_file(project_id: str, filename: str, db: Session = Depends(get_db)):
    """Get content of a file in the project directory (e.g., RML/YARRRML mapping)."""
    project = _get_project(db, project_id)

    # Look in both DATA_DIR and UPLOAD_DIR
    project_dirs = [
        Path(settings.DATA_DIR) / project_id,
        Path(settings.UPLOAD_DIR) / project_id
    ]

    for project_dir in project_dirs:
        file_path = project_dir / filename
        if file_path.exists():
            try:
                content = file_path.read_text(encoding='utf-8')
                return Response(content=content, media_type='text/plain')
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

    raise HTTPException(status_code=404, detail=f"File not found: {filename}")


@router.get("/{project_id}/mapping-preview")
async def get_mapping_preview(project_id: str, limit: int = Query(50, description="Max lines to preview"), db: Session = Depends(get_db)):
    """Get preview of mapping file (first N lines)."""
    import yaml

    project = _get_project(db, project_id)

    # Find mapping config
    project_dirs = [
        Path(settings.DATA_DIR) / project_id,
        Path(settings.UPLOAD_DIR) / project_id
    ]

    mapping_content = None
    mapping_format = "unknown"

    for project_dir in project_dirs:
        config_file = project_dir / "mapping_config.yaml"
        if config_file.exists():
            try:
                config = yaml.safe_load(config_file.read_text())
                if config.get('mapping', {}).get('file'):
                    # External mapping file
                    mapping_file = project_dir / config['mapping']['file']
                    if mapping_file.exists():
                        mapping_content = mapping_file.read_text(encoding='utf-8')
                        ext = mapping_file.suffix.lower()
                        mapping_format = "RML" if ext in ['.ttl', '.rdf', '.nt', '.n3'] else "YARRRML"
                        break
                elif config.get('mapping', {}).get('sources'):
                    # Inline v2 format
                    mapping_content = config_file.read_text(encoding='utf-8')
                    mapping_format = "v2-inline"
                    break
            except Exception:
                continue

    if not mapping_content:
        raise HTTPException(status_code=404, detail="No mapping found")

    # Limit preview to N lines
    lines = mapping_content.split('\n')
    preview_lines = lines[:limit]
    is_truncated = len(lines) > limit

    return {
        "format": mapping_format,
        "preview": '\n'.join(preview_lines),
        "total_lines": len(lines),
        "showing_lines": len(preview_lines),
        "is_truncated": is_truncated
    }


@router.delete("/{project_id}/data-file")
async def delete_data_file(project_id: str, db: Session = Depends(get_db)):
    """Delete uploaded data file."""
    project = _get_project(db, project_id)

    if not project.data_file:
        raise HTTPException(status_code=404, detail="No data file to delete")

    data_file_path = Path(project.data_file)

    # Delete file
    try:
        if data_file_path.exists():
            data_file_path.unlink()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

    # Update database
    project.data_file = None
    project.status = "created"
    db.commit()

    return {"message": "Data file deleted successfully"}


@router.delete("/{project_id}/ontology-file")
async def delete_ontology_file(project_id: str, db: Session = Depends(get_db)):
    """Delete uploaded ontology file."""
    project = _get_project(db, project_id)

    if not project.ontology_file:
        raise HTTPException(status_code=404, detail="No ontology file to delete")

    ontology_file_path = Path(project.ontology_file)

    # Delete file
    try:
        if ontology_file_path.exists():
            ontology_file_path.unlink()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

    # Update database
    project.ontology_file = None
    project.status = "created"
    db.commit()

    return {"message": "Ontology file deleted successfully"}


@router.delete("/{project_id}/mapping-file")
async def delete_mapping_file(project_id: str, db: Session = Depends(get_db)):
    """Delete uploaded mapping file and config."""
    import yaml

    project = _get_project(db, project_id)

    # Find and delete mapping files
    project_dirs = [
        Path(settings.DATA_DIR) / project_id,
        Path(settings.UPLOAD_DIR) / project_id
    ]

    deleted_files = []

    for project_dir in project_dirs:
        config_file = project_dir / "mapping_config.yaml"
        if config_file.exists():
            try:
                config = yaml.safe_load(config_file.read_text())
                if config.get('mapping', {}).get('file'):
                    # Delete external mapping file
                    mapping_file = project_dir / config['mapping']['file']
                    if mapping_file.exists():
                        mapping_file.unlink()
                        deleted_files.append(str(mapping_file))

                # Delete config file
                config_file.unlink()
                deleted_files.append(str(config_file))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error deleting files: {str(e)}")

    if not deleted_files:
        raise HTTPException(status_code=404, detail="No mapping files to delete")

    return {"message": "Mapping files deleted successfully", "deleted": deleted_files}


