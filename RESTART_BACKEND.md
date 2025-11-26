# Restart Backend to Apply RML Parser Fix

The RML parser fix is in the code, but the backend needs to reload the Python module.

## Option 1: Restart Docker Containers (Recommended)

```bash
cd /Users/rxcthefirst/Dev/PythonProjects/SemanticModelDataMapper
docker-compose restart backend worker
```

## Option 2: Rebuild if Code is Not Mounted

If the backend doesn't reload, the `rdfmap` package needs to be reinstalled:

```bash
cd /Users/rxcthefirst/Dev/PythonProjects/SemanticModelDataMapper
docker-compose down
docker-compose up --build -d
```

## Option 3: Manual Install in Container

```bash
# Get into the backend container
docker-compose exec backend bash

# Reinstall rdfmap package
pip install -e /app/src

# Exit
exit

# Restart backend
docker-compose restart backend worker
```

## Verify the Fix

After restarting, check the backend logs:

```bash
docker-compose logs backend | tail -50
```

Look for log messages about source path resolution when you run a conversion.

## Test the Conversion

1. Go to your project in the UI
2. Navigate to Step 4 (Convert)
3. Click "Convert to RDF"
4. It should now find `loans.csv` in the project directory!

---

**The fix changes**:
- `rml:source "examples/mortgage/data/loans.csv"`
- **To**: `loans.csv` (just the filename)
- **Backend finds**: `/app/uploads/{project_id}/loans.csv` ✅

