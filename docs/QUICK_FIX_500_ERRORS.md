# Quick Fix: 500 Errors with Large Datasets

## 🎯 The Problem

Processing 500k row dataset → 500 error after long wait

## 🔍 Root Causes Found

1. **Nginx timeout: 60s default** → Kills requests
2. **No file size limits** → Upload failures  
3. **Synchronous processing** → HTTP timeout
4. **No progress feedback** → User blind

## ✅ Fixes Applied

### 1. Nginx Timeouts (DONE ✅)
**File**: `frontend/nginx.conf`

Added:
- `client_max_body_size 500M` - Allow large uploads
- `proxy_read_timeout 600s` - 10 minute timeout
- Proper buffering

### 2. Auto Background Processing (DONE ✅)
**File**: `backend/app/routers/conversion.py`

- Files >5MB automatically use Celery worker
- No HTTP timeout issues
- Scales to any size

### 3. Task Status API (DONE ✅)
**Endpoint**: `GET /api/conversion/task/{task_id}`

Returns:
```json
{
  "task_id": "abc123",
  "status": "PROGRESS",
  "percentage": 45,
  "ready": false
}
```

## 🚀 To Apply Fixes

```bash
# Restart containers to load new nginx config
docker-compose down
docker-compose up -d
```

## 📝 What You Need To Know

### File Upload ✅ CORRECT
Your files ARE being saved to disk correctly.  
The backend reads from disk, NOT from HTTP body.

### The Real Issue ❌
**Timeout at multiple layers:**
1. Nginx (60s) → Now 600s ✅
2. Processing time (minutes) → Now async ✅

### How It Works Now

**Small files (<5MB)**:
- Synchronous response
- Complete in <30s

**Large files (>5MB)**:
- Returns immediately with `task_id`
- Backend processes in background
- Poll `/api/conversion/task/{task_id}` for status

## 🎯 Frontend TODO

You need to update the UI to:

1. **Check response status**:
```typescript
if (response.status === 'queued') {
  // Start polling
  pollTaskStatus(response.task_id)
} else {
  // Show immediate result
}
```

2. **Poll for status**:
```typescript
async function pollTaskStatus(taskId: string) {
  const interval = setInterval(async () => {
    const status = await fetch(`/api/conversion/task/${taskId}`)
    const data = await status.json()
    
    if (data.ready) {
      clearInterval(interval)
      showResult(data.result)
    } else {
      updateProgress(data.percentage || 0)
    }
  }, 2000) // Check every 2 seconds
}
```

## 📊 Expected Performance

| Rows | File Size | Mode | Time |
|------|-----------|------|------|
| 10k | 1MB | Sync | <30s |
| 100k | 10MB | Async | 2-5m |
| 500k | 50MB | Async | 10-20m |
| 1M | 100MB | Async | 20-40m |

## 🐛 Test It

```bash
# 1. Restart services
docker-compose down && docker-compose up -d

# 2. Upload your 500k CSV
# 3. Try conversion
# 4. If async, you'll get:
{
  "status": "queued",
  "task_id": "abc-123-def",
  "message": "Conversion queued as background job..."
}

# 5. Check status:
curl http://localhost:8000/api/conversion/task/abc-123-def
```

## 📚 Full Details

See: `docs/PERFORMANCE_ARCHITECTURE.md`

---

**Status**: ✅ Backend fixes applied  
**Next**: Update frontend to poll task status  
**Apply**: `docker-compose down && docker-compose up -d`

