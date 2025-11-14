# When NOT to Use Enhanced Streaming Mode - Quick Reference

## TL;DR Decision Matrix

| File Size | Available RAM | Recommendation | Why |
|-----------|---------------|----------------|-----|
| < 1MB | Any | **Regular** | Streaming overhead > benefits |
| 1-10MB | Any | **Regular** | Simple processing sufficient |
| 10-50MB | > 8GB | **Regular** | Fits comfortably in memory |
| 10-50MB | < 8GB | **Streaming** | Memory efficiency matters |
| 50-100MB | Any | **Streaming** | Sweet spot for streaming benefits |
| > 100MB | Any | **Streaming** | Always better with streaming |
| > 25% RAM | Any | **Streaming** | Risk of memory pressure |

## Use Cases

### ✅ Always Use Regular Mode
- **Development & debugging** (easier to inspect data)
- **Small datasets** (< 10K rows)
- **One-off analysis** (quick scripts)
- **Memory-rich environments** with small files

### ⚖️ Context Dependent
- **Medium datasets** (10-100MB files)
- **Production vs development** environments
- **Interactive analysis** vs batch processing

### ✅ Always Use Streaming Mode  
- **Production ETL pipelines**
- **Large datasets** (> 100MB)
- **Memory-constrained environments**
- **Long-running processes**

## Key Trade-offs

### Regular Mode Wins When:
- **Simplicity** is more important than optimization
- **Debugging** and development speed matter
- **File size << available memory**
- **One-time processing** tasks

### Streaming Mode Wins When:
- **Memory efficiency** is critical
- **Consistent performance** across file sizes is needed
- **Production reliability** matters
- **Processing very large datasets**

## Smart Defaults

```python
# Simple rule of thumb
if file_size_mb < available_ram_gb * 256:  # 25% of RAM
    use_regular_mode()
else:
    use_streaming_mode()
```

The enhanced streaming mode is **a tool for specific scenarios**, not a universal improvement. Choose based on your actual constraints and requirements.
