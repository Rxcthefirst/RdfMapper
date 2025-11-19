# 🐳 Docker Deployment Guide - RDFMap v0.3.0

**Complete guide for building and deploying RDFMap Docker images**

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Build](#quick-build)
3. [Docker Hub Publication](#docker-hub-publication)
4. [Image Details](#image-details)
5. [Deployment Options](#deployment-options)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools
- Docker 24.0+
- Docker Compose 2.0+
- Docker Hub account

### Check Installation
```bash
docker --version
docker-compose --version
docker info
```

## Quick Build

### 1. Make Build Script Executable
```bash
chmod +x build-and-push-docker.sh
```

### 2. Build Images Locally
```bash
# Build with latest tag
./build-and-push-docker.sh latest 0.3.0

# Or build specific version
./build-and-push-docker.sh 0.3.0 0.3.0
```

This builds:
- `rxcthefirst/rdfmap-api:0.3.0` (and `:latest`)
- `rxcthefirst/rdfmap-ui:0.3.0` (and `:latest`)

### 3. Test Locally
```bash
# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Access UI
open http://localhost:8080

# Stop services
docker-compose -f docker-compose.prod.yml down
```

## Docker Hub Publication

### Step 1: Login to Docker Hub
```bash
docker login
# Enter username: rxcthefirst
# Enter password: [your-token]
```

### Step 2: Build and Push
```bash
# Build and push (script will prompt)
./build-and-push-docker.sh 0.3.0 0.3.0

# Or push manually
docker push rxcthefirst/rdfmap-api:0.3.0
docker push rxcthefirst/rdfmap-api:latest
docker push rxcthefirst/rdfmap-ui:0.3.0
docker push rxcthefirst/rdfmap-ui:latest
```

### Step 3: Configure Docker Hub Repository

#### For rdfmap-api:

1. Go to https://hub.docker.com/r/rxcthefirst/rdfmap-api
2. Click "Manage Repository"
3. Set **Description**: Copy from `.dockerhub/README.md`
4. Set **Overview**: Use Docker Hub description template
5. Add **Tags**:
   - `latest` - Latest stable release
   - `0.3.0` - Specific version
   - `0.3` - Minor version
   - `dev` - Development builds (optional)

#### For rdfmap-ui:

1. Go to https://hub.docker.com/r/rxcthefirst/rdfmap-ui
2. Follow same steps as API
3. Set similar tags

### Step 4: Add Repository Badges

Add to GitHub README:

```markdown
[![Docker Pulls - API](https://img.shields.io/docker/pulls/rxcthefirst/rdfmap-api)](https://hub.docker.com/r/rxcthefirst/rdfmap-api)
[![Docker Pulls - UI](https://img.shields.io/docker/pulls/rxcthefirst/rdfmap-ui)](https://hub.docker.com/r/rxcthefirst/rdfmap-ui)
[![Docker Image Size - API](https://img.shields.io/docker/image-size/rxcthefirst/rdfmap-api)](https://hub.docker.com/r/rxcthefirst/rdfmap-api)
[![Docker Image Size - UI](https://img.shields.io/docker/image-size/rxcthefirst/rdfmap-ui)](https://hub.docker.com/r/rxcthefirst/rdfmap-ui)
```

## Image Details

### rdfmap-api (Backend + Worker)

**Size**: ~250-300MB (slim Python base)

**Contains**:
- Python 3.11-slim base
- FastAPI web framework
- Celery task queue
- semantic-rdf-mapper 0.3.0 (from PyPI)
- PostgreSQL client
- All backend dependencies

**Ports**: 8000 (HTTP)

**Health Check**: `GET /health`

**Usage**:
```bash
# As API server
docker run -p 8000:8000 rxcthefirst/rdfmap-api:latest

# As worker
docker run rxcthefirst/rdfmap-api:latest \
  celery -A app.worker:celery_app worker --loglevel=info
```

### rdfmap-ui (Frontend)

**Size**: ~50-80MB (nginx alpine base)

**Contains**:
- Nginx Alpine base
- React + Vite production build
- Optimized static assets
- Reverse proxy configuration

**Ports**: 8080 (HTTP)

**Health Check**: `GET /`

**Usage**:
```bash
docker run -p 8080:8080 rxcthefirst/rdfmap-ui:latest
```

## Deployment Options

### Option 1: Docker Compose (Recommended)

**Best for**: Complete deployments with all services

```bash
# Download compose file
curl -O https://raw.githubusercontent.com/Rxcthefirst/RdfMapper/main/docker-compose.prod.yml

# Create environment file
cp .env.example .env
# Edit .env with your configuration

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Option 2: Docker Swarm

**Best for**: Multi-node production clusters

```bash
# Initialize swarm
docker swarm init

# Create secrets
echo "your-secret-key" | docker secret create rdfmap_secret_key -
echo "your-db-password" | docker secret create postgres_password -

# Deploy stack
docker stack deploy -c docker-compose.prod.yml rdfmap

# Check services
docker service ls
```

### Option 3: Kubernetes

**Best for**: Large-scale enterprise deployments

Create Kubernetes manifests:
```bash
# Generate from compose (using kompose)
kompose convert -f docker-compose.prod.yml

# Or use Helm chart (create custom chart)
helm create rdfmap
```

### Option 4: Cloud Platforms

#### AWS ECS
```bash
# Use AWS CLI or Console
aws ecs create-cluster --cluster-name rdfmap-cluster
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

#### Google Cloud Run
```bash
gcloud run deploy rdfmap-api \
  --image rxcthefirst/rdfmap-api:latest \
  --platform managed
```

#### Azure Container Instances
```bash
az container create \
  --resource-group rdfmap \
  --name rdfmap-api \
  --image rxcthefirst/rdfmap-api:latest
```

## Image Optimization

### Current Optimizations

✅ Multi-stage builds (frontend)  
✅ Slim base images (python:3.11-slim)  
✅ Non-root user execution  
✅ Layer caching optimization  
✅ Health checks included  
✅ Minimal dependencies  

### Size Comparison

| Image | Base | Size | Optimized |
|-------|------|------|-----------|
| rdfmap-api | python:3.11-slim | ~280MB | ✅ |
| rdfmap-ui | nginx:alpine | ~60MB | ✅ |
| Total Stack | - | ~340MB | ✅ |

### Further Optimization (Optional)

```dockerfile
# Use distroless for even smaller size
FROM gcr.io/distroless/python3-debian11

# Use Alpine for API (requires compilation)
FROM python:3.11-alpine
```

## Versioning Strategy

### Semantic Versioning

We use SemVer: `MAJOR.MINOR.PATCH`

**Tags**:
- `latest` → Always points to latest stable
- `0.3.0` → Specific version (immutable)
- `0.3` → Latest patch in 0.3.x
- `0` → Latest minor in 0.x.x (not recommended)

### Update Policy

- `latest` updated with each stable release
- Version tags are immutable (never changed)
- Security patches get new patch versions

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build and Push Docker Images

on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to DockerHub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      
      - name: Extract version
        id: version
        run: echo "VERSION=${GITHUB_REF#refs/tags/v}" >> $GITHUB_OUTPUT
      
      - name: Build and push API
        uses: docker/build-push-action@v4
        with:
          context: ./backend
          push: true
          tags: |
            rxcthefirst/rdfmap-api:latest
            rxcthefirst/rdfmap-api:${{ steps.version.outputs.VERSION }}
          build-args: |
            RDFMAP_VERSION=${{ steps.version.outputs.VERSION }}
      
      - name: Build and push UI
        uses: docker/build-push-action@v4
        with:
          context: ./frontend
          push: true
          target: production
          tags: |
            rxcthefirst/rdfmap-ui:latest
            rxcthefirst/rdfmap-ui:${{ steps.version.outputs.VERSION }}
```

## Monitoring

### Prometheus Metrics (Optional)

Add to API:
```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

### Docker Stats
```bash
# Real-time stats
docker stats

# Specific service
docker stats rdfmap-api
```

### Logs
```bash
# Follow logs
docker logs -f rdfmap-api

# Last 100 lines
docker logs --tail 100 rdfmap-api

# With timestamps
docker logs -t rdfmap-api
```

## Troubleshooting

### Build Issues

**Problem**: Build fails with dependency errors
```bash
# Clear build cache
docker builder prune -a

# Rebuild without cache
docker build --no-cache -t rxcthefirst/rdfmap-api:latest backend/
```

**Problem**: Out of disk space
```bash
# Remove unused images
docker image prune -a

# Remove all stopped containers
docker container prune

# See disk usage
docker system df
```

### Runtime Issues

**Problem**: Container exits immediately
```bash
# Check logs
docker logs rdfmap-api

# Run interactively
docker run -it --entrypoint /bin/bash rxcthefirst/rdfmap-api:latest
```

**Problem**: Health check failing
```bash
# Test health endpoint
docker exec rdfmap-api curl http://localhost:8000/health

# Check if port is listening
docker exec rdfmap-api netstat -tlnp
```

### Push Issues

**Problem**: Authentication error
```bash
# Re-login
docker logout
docker login

# Use token instead of password
docker login -u rxcthefirst
```

**Problem**: Rate limit exceeded
```bash
# Wait or use paid Docker Hub account
# Check rate limit
curl "https://auth.docker.io/token?service=registry.docker.io&scope=repository:ratelimitpreview/test:pull" | jq
```

## Security Checklist

Before deploying to production:

- [ ] Change all default passwords in `.env`
- [ ] Generate secure `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Restrict CORS origins to your domain
- [ ] Use HTTPS/TLS with reverse proxy
- [ ] Enable container scanning (Docker Scout/Trivy)
- [ ] Implement secrets management (Vault/AWS Secrets Manager)
- [ ] Set up log aggregation (ELK/Splunk)
- [ ] Configure firewall rules
- [ ] Enable audit logging
- [ ] Regular security updates

## Next Steps

1. ✅ **Test locally** with docker-compose
2. ✅ **Push to Docker Hub**
3. ✅ **Update repository descriptions**
4. ✅ **Add badges to README**
5. ✅ **Create GitHub release**
6. ✅ **Announce on social media**
7. ✅ **Monitor pull statistics**
8. ✅ **Gather user feedback**

## Support

- **GitHub Issues**: https://github.com/Rxcthefirst/RdfMapper/issues
- **Discussions**: https://github.com/Rxcthefirst/RdfMapper/discussions
- **Docker Hub**: https://hub.docker.com/u/rxcthefirst

---

**Last Updated**: November 19, 2025  
**Version**: 0.3.0  
**Status**: ✅ Production Ready

