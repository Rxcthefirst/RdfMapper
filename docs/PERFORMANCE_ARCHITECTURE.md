# Performance and Scalability Architecture Guide

**Date**: November 25, 2025  
**Topic**: Handling large datasets in containerized RDFMap architecture  
**Status**: 🟢 **IMPLEMENTED**

---

## 🎯 The Problem

When processing large datasets (500k+ rows), you're experiencing:
1. **500 errors** after long waits
2. **Timeouts** at multiple layers
3. **No progress feedback** during long operations
4. **Unclear if data is being processed** correctly

---

## 🏗️ Architecture Overview

```
┌─────────────┐
│   Browser   │
│   (React)   │
└──────┬──────┘
       │ HTTP/WebSocket
       ▼
┌─────────────┐  proxy_timeout: 60s (default)
│    Nginx    │  ❌ Too short!
│  (Frontend) │
└──────┬──────┘
       │ Proxy
       ▼
┌─────────────┐
│   FastAPI   │  Gunicorn timeout: 30s (default)
│  (Backend)  │  ❌ Too short!
└──────┬──────┘
       │
       ├──────────────┐
       │              │
       ▼              ▼
┌──────────┐   ┌──────────┐
│  Celery  │   │   File   │
│  Worker  │   │  System  │
│ (Async)  │   │ (uploads)│
└──────────┘   └──────────┘
```

---

## 🔴 Bottlenecks Identified

### 1. Nginx Timeouts (60s default)
**Problem**: Nginx kills requests after 60 seconds by default

**Symptoms**:
- 504 Gateway Timeout
- Connection reset
- No response after ~1 minute

### 2. Missing File Size Limits
**Problem**: No client_max_body_size configured

**Symptoms**:
- 413 Request Entity Too Large
- Upload failures for large CSV files

### 3. Synchronous Processing
**Problem**: Large files processed in HTTP request/response cycle

**Symptoms**:
- Browser "waiting" indefinitely
- Memory spikes
- Timeout errors

### 4. No Progress Feedback
**Problem**: User has no idea what's happening

**Symptoms**:
- User frustration
- Repeated attempts
- Uncertain if it's working

---

## ✅ Solutions Implemented

### Solution 1: Nginx Configuration

**File**: `frontend/nginx.conf`

```nginx
# File upload limits
client_max_body_size 500M;        # Allow up to 500MB files
client_body_timeout 300s;          # 5 minutes to upload

# API proxy timeouts
location /api {
    proxy_connect_timeout 600s;    # 10 minutes
    proxy_send_timeout 600s;       # 10 minutes  
    proxy_read_timeout 600s;       # 10 minutes
    
    # Buffer settings
    proxy_buffering on;
    proxy_buffer_size 128k;
    proxy_buffers 8 128k;
}
```

**Why**:
- Allows large file uploads (500MB)
- Gives 10 minutes for operations to complete
- Proper buffering for large responses

---

### Solution 2: Auto Background Processing

**File**: `backend/app/routers/conversion.py`

```python
# Auto-detect if background processing needed
if use_background is None:
    file_size_mb = data_file.stat().st_size / (1024 * 1024)
    
    if file_size_mb > 5:
        use_background = True
        logger.info(f"Auto-enabling background for {file_size_mb:.1f}MB")
```

**Why**:
- Files > 5MB automatically use background worker
- No HTTP timeout issues
- Scales to any size dataset

---

### Solution 3: Task Status API

**File**: `backend/app/routers/conversion.py`

```python
@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """Check background task status with progress."""
    task = AsyncResult(task_id, app=celery_app)
    
    return {
        "task_id": task_id,
        "status": task.status,  # PENDING, STARTED, PROGRESS, SUCCESS, FAILURE
        "ready": task.ready(),
        "progress": task.info.get('percentage', 0),  # If available
        "result": task.result if task.successful() else None
    }
```

**Why**:
- Poll for status
- Show progress percentage
- Get results when ready

---

### Solution 4: Frontend Polling (TO DO)

**What's Needed**: Update frontend to poll task status

```typescript
// Pseudo-code for frontend
async function convertWithPolling(projectId: string) {
  // Start conversion
  const response = await fetch(`/api/conversion/${projectId}`, {
    method: 'POST'
  })
  
  const data = await response.json()
  
  if (data.status === 'queued') {
    // Poll for status
    const taskId = data.task_id
    const result = await pollTaskStatus(taskId)
    return result
  } else {
    // Synchronous response
    return data
  }
}

async function pollTaskStatus(taskId: string) {
  while (true) {
    const status = await fetch(`/api/conversion/task/${taskId}`)
    const data = await status.json()
    
    if (data.ready) {
      return data.result
    }
    
    // Update progress bar
    updateProgress(data.percentage || 0)
    
    // Wait 2 seconds before next check
    await sleep(2000)
  }
}
```

---

## 📊 Performance Characteristics

### Small Files (<5MB, <10k rows)
- **Mode**: Synchronous
- **Time**: <30 seconds
- **UX**: Immediate response

### Large Files (5MB-50MB, 10k-100k rows)
- **Mode**: Background (Celery)
- **Time**: 1-5 minutes
- **UX**: Poll for status

### Very Large Files (>50MB, >100k rows)
- **Mode**: Background (Celery)
- **Time**: 5-30 minutes
- **UX**: Poll for status + progress bar

---

## 🚀 Recommended Configuration

### For Production

**docker-compose.yml** additions:

```yaml
services:
  backend:
    environment:
      - GUNICORN_TIMEOUT=600  # 10 minute timeout
      - GUNICORN_WORKERS=4
      - GUNICORN_THREADS=2
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
  
  worker:
    deploy:
      replicas: 2  # Multiple workers for parallelism
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
    environment:
      - CELERY_CONCURRENCY=2  # Tasks per worker
```

---

## 🔧 File Upload Strategy

### Current Implementation

1. **User uploads file** → Saved to disk immediately
2. **Generate mappings** → References file path (not content)
3. **Convert data** → Reads from disk, streams RDF output

**✅ This is correct!**  
Files are NOT sent in HTTP body during generation/conversion.  
Only the file PATH is passed to the worker.

### File Flow

```
Upload
  │
  ▼
┌──────────────┐
│  /uploads/   │ ← Files stored here
│  {project}/  │
└──────┬───────┘
       │
       ▼ (file path only)
┌──────────────┐
│   Worker     │ ← Reads file from disk
│  Process     │
└──────────────┘
```

---

## 🎯 Checklist: Is Your Setup Correct?

### ✅ Nginx Configuration
- [ ] `client_max_body_size` set to 500M or higher
- [ ] `proxy_read_timeout` set to 600s or higher
- [ ] Proxy buffering enabled

### ✅ Backend Configuration  
- [ ] Auto background processing for large files
- [ ] Task status endpoint available
- [ ] Celery worker running

### ✅ Frontend (TODO)
- [ ] Poll task status for background jobs
- [ ] Show progress indicator
- [ ] Handle both sync and async responses

### ✅ Docker
- [ ] Adequate memory limits (4GB+ for worker)
- [ ] Multiple worker replicas if needed
- [ ] Persistent volume for uploads

---

## 🐛 Debugging Tips

### Check if file was uploaded correctly
```bash
docker exec rdfmap-backend ls -lh /app/uploads/{project_id}/
```

### Check worker logs
```bash
docker logs rdfmap-worker --tail 100 -f
```

### Check task status manually
```bash
curl http://localhost:8000/api/conversion/task/{task_id}
```

### Monitor resource usage
```bash
docker stats rdfmap-backend rdfmap-worker
```

---

## 📈 Performance Benchmarks (Expected)

| Rows | File Size | Generation Time | Conversion Time | Mode |
|------|-----------|-----------------|-----------------|------|
| 1k | 100KB | <1s | <5s | Sync |
| 10k | 1MB | <5s | <30s | Sync |
| 100k | 10MB | 30s-1m | 2-5m | Background |
| 500k | 50MB | 2-5m | 10-20m | Background |
| 1M | 100MB | 5-10m | 20-40m | Background |

*Times vary based on CPU, complexity of ontology, and number of columns*

---

## 🔮 Future Enhancements

### WebSocket Implementation (Recommended)
Instead of polling, use WebSocket for real-time updates:

```python
# Backend
@app.websocket("/ws/task/{task_id}")
async def task_websocket(websocket: WebSocket, task_id: str):
    await websocket.accept()
    
    while True:
        status = get_task_status(task_id)
        await websocket.send_json(status)
        
        if status['ready']:
            break
            
        await asyncio.sleep(2)
    
    await websocket.close()
```

```typescript
// Frontend
const ws = new WebSocket(`ws://localhost:8000/ws/task/${taskId}`)

ws.onmessage = (event) => {
  const status = JSON.parse(event.data)
  updateProgressBar(status.percentage)
  
  if (status.ready) {
    showResults(status.result)
  }
}
```

---

## Files Modified

1. ✅ `frontend/nginx.conf`
   - Added timeout configurations
   - Added file size limits
   - Added buffer settings

2. ✅ `backend/app/routers/conversion.py`
   - Auto background processing for large files
   - Enhanced task status endpoint
   - Better error handling

3. 📝 `docs/PERFORMANCE_ARCHITECTURE.md`
   - This documentation

---

## Next Steps

### Immediate (Backend done ✅)
- [x] Configure nginx timeouts
- [x] Add file size limits
- [x] Auto background processing
- [x] Task status API

### Frontend (TODO)
- [ ] Implement task polling in UI
- [ ] Add progress indicator
- [ ] Handle async responses
- [ ] Show "Processing..." state

### Optional (Future)
- [ ] WebSocket for real-time progress
- [ ] Streaming RDF output
- [ ] Chunked processing
- [ ] Result caching

---

## Summary

**Your current bottleneck is NOT file upload** - files are correctly saved to disk.

**The bottleneck is timeout configuration** - nginx and the backend need longer timeouts for large operations.

**Solution implemented**:
1. ✅ Nginx now allows 10 minute operations
2. ✅ Backend auto-detects large files and uses background processing
3. ✅ Task status API ready for frontend polling
4. ⏳ Frontend needs to poll task status (TO DO)

**Restart services to apply nginx changes**:
```bash
docker-compose down
docker-compose up -d
```

Then test with your 500k row dataset! 🚀

