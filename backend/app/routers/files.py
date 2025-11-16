from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from ..config import settings

router = APIRouter()

WHITELIST = {
    'alignment_report.json',
    'alignment_report.html',
    'mapping_config.yaml',
    'output.ttl', 'output.jsonld', 'output.rdf', 'output.nt', 'output.n3'
}

@router.get('/{project_id}/{filename}')
async def get_project_file(project_id: str, filename: str):
    if filename not in WHITELIST:
        raise HTTPException(status_code=404, detail='File not found')
    file_path = Path(settings.DATA_DIR) / project_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail='File not found')
    media_types = {
        'yaml': 'text/yaml', 'ttl': 'text/turtle', 'jsonld': 'application/ld+json',
        'rdf': 'application/rdf+xml', 'nt': 'application/n-triples', 'n3': 'text/n3', 'html': 'text/html', 'json': 'application/json'
    }
    ext = file_path.suffix.lstrip('.')
    return FileResponse(str(file_path), media_type=media_types.get(ext, 'application/octet-stream'), filename=filename)

