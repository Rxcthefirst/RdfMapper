"""Projects API router."""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
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

    # Save file
    project_dir = Path(settings.UPLOAD_DIR) / project_id
    file_path = project_dir / f"data{file_ext}"

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

    # Save file
    project_dir = Path(settings.UPLOAD_DIR) / project_id
    file_path = project_dir / f"ontology{file_ext}"

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
    file_path = project_dir / f"shapes{file_ext}"
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
    # Name with increment to avoid overwriting
    base = "skos"
    target = project_dir / f"{base}{file_ext}"
    idx = 1
    while target.exists():
        target = project_dir / f"{base}-{idx}{file_ext}"
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
