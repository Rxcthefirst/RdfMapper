# RDFMap - Docker Quick Start
🌟 Star us on [GitHub](https://github.com/Rxcthefirst/RdfMapper) if you find this useful!

**Built with ❤️ by the RDFMap team**

---

MIT License - see LICENSE file for details

## 📄 License

- **Discussions**: https://github.com/Rxcthefirst/RdfMapper/discussions
- **Issues**: https://github.com/Rxcthefirst/RdfMapper/issues

## 🤝 Support

- **API Docs**: http://localhost:8000/docs (after deployment)
- **Docker Hub**: https://hub.docker.com/r/rxcthefirst/rdfmap-api
- **GitHub**: https://github.com/Rxcthefirst/RdfMapper
- **PyPI Package**: https://pypi.org/project/semantic-rdf-mapper/

## 📚 Documentation

- ✅ **Production Ready**: Docker deployment, health checks, security
- ✅ **Full Transparency**: Evidence for every mapping decision
- ✅ **Multi-Format**: CSV, Excel, JSON, XML input
- ✅ **5x Performance**: Optimized matcher pipeline
- ✅ **YARRRML Support**: Standards-compliant RML ecosystem
- ✅ **95% Auto-Success**: Automatically maps 95% of columns correctly
- ✅ **AI-Powered Matching**: BERT embeddings for semantic understanding

## 🌟 Features

```
docker run --rm -v rdfmap_upload_data:/data -v $(pwd):/backup alpine tar czf /backup/uploads-backup.tar.gz /data
# Backup volumes

docker exec rdfmap-db pg_dump -U rdfmap rdfmap > backup.sql
# Backup database
```bash
### Backup volumes

- `rdf_data` - Generated RDF output
- `upload_data` - Uploaded files
- `redis_data` - Task queue
- `postgres_data` - Database

Data is persisted in named volumes:

## 💾 Data Persistence

```
VERSION=0.3.0 docker-compose -f docker-compose.prod.yml up -d
VERSION=0.3.0 docker-compose -f docker-compose.prod.yml pull
```bash
### Upgrade to specific version

```
docker pull rxcthefirst/rdfmap-ui:latest
docker pull rxcthefirst/rdfmap-api:latest
```bash
### Pull latest images

## 🔄 Updates

```
docker exec rdfmap-api python -c "from app.database import engine; engine.connect()"
# Check connection from API

docker exec rdfmap-db pg_isready -U rdfmap
# Check if database is ready
```bash
### Database connection issues

```
docker-compose -f docker-compose.prod.yml restart worker
# Restart worker

docker-compose -f docker-compose.prod.yml logs worker
# Check worker logs
```bash
### Worker not processing tasks

```
docker ps
# Check service health

docker-compose -f docker-compose.prod.yml logs api
# Check logs
```bash
### Service won't start

## 🐛 Troubleshooting

```
SQLALCHEMY_MAX_OVERFLOW=10
SQLALCHEMY_POOL_SIZE=20
# Add to environment
```bash
### Database Connection Pool

```
command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
# In docker-compose.prod.yml
```bash
### Redis Memory Limit

```
command: celery -A app.worker:celery_app worker --loglevel=info --concurrency=4
# In docker-compose.prod.yml
```bash
### Worker Concurrency

## 📈 Performance Tuning

   - Only expose 8080 (UI) and optionally 8000 (API)
   - Don't expose database ports publicly
5. **Use private networks**:

   ```
   CORS_ORIGINS=https://yourdomain.com
   ```bash
4. **Restrict CORS**:

   - Use Let's Encrypt certificates
   - Add reverse proxy (nginx/traefik)
3. **Enable TLS**:

   ```
   docker secret create postgres_password /path/to/password/file
   ```bash
2. **Use secrets management**:

   ```
   SECRET_KEY=generate-a-secure-secret-key
   POSTGRES_PASSWORD=strong-random-password
   ```bash
1. **Change default passwords**:

### For Production:

## 🔒 Security Best Practices

6. **Convert to RDF**: Generate knowledge graph
5. **Download YARRRML**: Get standards-compliant mapping config
4. **Manual override**: Adjust mappings as needed
3. **Review evidence**: See why each mapping was suggested
2. **Generate mappings**: AI automatically maps columns to ontology properties
1. **Upload files**: CSV data + OWL ontology

Once running, open http://localhost:8080 and:

## 🎨 Usage Example

```
docker-compose -f docker-compose.prod.yml up -d --scale worker=4
# Run 4 workers for faster processing
```bash
### Scale workers

```
docker-compose -f docker-compose.prod.yml ps
```bash
### Check status

```
docker-compose -f docker-compose.prod.yml logs -f worker
docker-compose -f docker-compose.prod.yml logs -f api
# Specific service

docker-compose -f docker-compose.prod.yml logs -f
# All services
```bash
### View logs

```
docker-compose -f docker-compose.prod.yml down
```bash
### Stop services

```
docker-compose -f docker-compose.prod.yml up -d
```bash
### Start services

## 📊 Service Management

```
docker-compose -f docker-compose.prod.yml --env-file .env up -d
# Or with .env file

VERSION=0.3.0 docker-compose -f docker-compose.prod.yml up -d
# Use environment variables
```bash

### Docker Compose with Environment

```
CORS_ORIGINS=http://localhost:8080,https://yourdomain.com
# CORS

CELERY_RESULT_BACKEND=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
REDIS_URL=redis://redis:6379/0
# Redis

DATABASE_URL=postgresql://rdfmap:rdfmap@db:5432/rdfmap
POSTGRES_PASSWORD=change-me-in-production
POSTGRES_USER=rdfmap
POSTGRES_DB=rdfmap
# Database

SECRET_KEY=your-secret-key-here
RDFMAP_VERSION=0.3.0
VERSION=0.3.0
# Application
```bash

Create a `.env` file:

### Environment Variables

## 🔧 Configuration

5. UI polls for completion → Shows results when done
4. Worker updates progress → Redis
3. Worker picks up job → Runs RDF conversion
2. API queues conversion job → Redis
1. User uploads 100MB CSV file → API returns immediately
### Workflow Example:

- **Resource isolation**: Heavy AI models don't block web requests
- **Resilient**: Workers can restart without affecting the API
- **Scalable**: Run multiple workers for parallel processing
- **Non-blocking**: Users don't wait for long operations
### Why separate workers?

- ✅ **YARRRML Generation** - Create standards-compliant mappings
- ✅ **File Processing** - Parse Excel, JSON, XML files
- ✅ **Ontology Analysis** - Deep graph reasoning operations
- ✅ **Semantic Matching** - Run AI/BERT models for column mapping
- ✅ **RDF Conversion** - Convert large datasets without blocking the UI
### Tasks it performs:

The **Celery Worker** handles long-running background tasks:

## 🎯 What Does the Worker Do?

```
                                    └─────────┘
                                    │(Celery) │
                                    │ Worker  │
                                    ┌────▼────┐
                                         │
                                    └────┬────┘          └─────────┘
                                    │ (Queue) │          │  (PG)   │
                                    │  Redis  │          │   DB    │
                                    ┌────▼────┐          ┌────▼────┐
                                         │                     │
                                         ┌──────────┴──────────┐
                                                    │
                           :8080                  :8000
└─────────────┘      └─────────────┘      └──────┬──────┘
│             │      │   (Nginx)   │      │  (FastAPI)  │
│   Browser   │─────▶│  Frontend   │─────▶│   Backend   │
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
```

- **📮 Redis**: Task queue for background jobs
- **💾 Database**: PostgreSQL for metadata storage
- **🔄 Worker**: Celery workers for async RDF conversion
- **⚙️ Backend (API)**: FastAPI REST API on port 8000
- **🎨 Frontend (UI)**: React + Vite web interface on port 8080

RDFMap uses a microservices architecture:

## 🏗️ Architecture

```
docker pull rxcthefirst/rdfmap-api:0.3.0
docker pull rxcthefirst/rdfmap-api:latest
```bash
### Backend API + Worker

```
docker pull rxcthefirst/rdfmap-ui:0.3.0
docker pull rxcthefirst/rdfmap-ui:latest
```bash
### Frontend UI

## 📦 Available Images

That's it! 🎉

```
# Access the UI at http://localhost:8080

docker-compose -f docker-compose.prod.yml up -d
# Start all services

curl -O https://raw.githubusercontent.com/Rxcthefirst/RdfMapper/main/docker-compose.prod.yml
# Download docker-compose file
```bash

Or use **Docker Compose** (recommended):

```
  rxcthefirst/rdfmap-stack:latest
  -p 8000:8000 \
  -p 8080:8080 \
  --name rdfmap \
docker run -d \
```bash

### One-Line Deploy

## 🚀 Quick Start

Convert CSV, Excel, JSON, and XML to RDF knowledge graphs with AI-powered semantic matching.

**Production-ready Docker images for RDFMap - AI-powered semantic data mapping tool**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Docker Image Size](https://img.shields.io/docker/image-size/rxcthefirst/rdfmap-api)](https://hub.docker.com/r/rxcthefirst/rdfmap-api)
[![Docker Pulls](https://img.shields.io/docker/pulls/rxcthefirst/rdfmap-api)](https://hub.docker.com/r/rxcthefirst/rdfmap-api)


