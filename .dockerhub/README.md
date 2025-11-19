# RDFMap Docker Hub Description

**AI-Powered Semantic Data Mapping - Convert Tabular Data to RDF Knowledge Graphs**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/Rxcthefirst/RdfMapper/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)

Transform your CSV, Excel, JSON, and XML data into semantic RDF triples with intelligent AI-powered ontology mapping.

## ✨ Key Features

- 🧠 **AI-Powered Matching** - BERT embeddings understand semantic relationships
- 🎯 **95% Auto-Success Rate** - Automatically maps columns to ontology properties
- ⚡ **5x Performance** - Optimized processing pipeline
- 📋 **YARRRML Support** - Standards-compliant RML ecosystem integration
- 🔍 **Full Transparency** - Evidence for every mapping decision
- 🎨 **Modern Web UI** - Intuitive interface for data mapping
- 🔄 **Async Processing** - Background workers for large datasets

## 🚀 Quick Start

```bash
# Pull images
docker pull rxcthefirst/rdfmap-api:latest
docker pull rxcthefirst/rdfmap-ui:latest

# Download docker-compose
curl -O https://raw.githubusercontent.com/Rxcthefirst/RdfMapper/main/docker-compose.prod.yml

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Access UI at http://localhost:8080
```

## 📦 What's Included

This image contains:
- **FastAPI Backend** - REST API for data processing
- **Celery Worker** - Async task processing for RDF conversion
- **semantic-rdf-mapper** - Core Python library (v0.3.0)
- **PostgreSQL Support** - Metadata storage
- **Redis Integration** - Task queue management

## 🏗️ Architecture

```
Frontend (UI) → Backend (API) → Worker (Celery)
     ↓              ↓              ↓
   Nginx       PostgreSQL       Redis
```

## 🔧 Usage

### Standalone API
```bash
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e REDIS_URL=redis://... \
  rxcthefirst/rdfmap-api:latest
```

### With Worker
```bash
# API
docker run -d --name rdfmap-api \
  -p 8000:8000 \
  rxcthefirst/rdfmap-api:latest

# Worker
docker run -d --name rdfmap-worker \
  rxcthefirst/rdfmap-api:latest \
  celery -A app.worker:celery_app worker --loglevel=info
```

### Full Stack (Recommended)
Use docker-compose for complete deployment with UI, API, worker, database, and Redis.

See full documentation at: https://github.com/Rxcthefirst/RdfMapper

## 🎯 Use Cases

- **Data Integration** - Merge heterogeneous data sources
- **Knowledge Graphs** - Build semantic knowledge bases
- **Linked Data** - Create RDF for the semantic web
- **Ontology Alignment** - Map data to standard ontologies
- **Data Validation** - Ensure semantic correctness

## 📊 Supported Formats

**Input**: CSV, Excel (XLSX), JSON, XML  
**Output**: RDF (Turtle, N-Triples, RDF/XML, JSON-LD), YARRRML

## 🔒 Security

- Non-root user execution
- Health checks included
- Environment-based configuration
- Secure defaults

## 📚 Links

- **GitHub**: https://github.com/Rxcthefirst/RdfMapper
- **PyPI**: https://pypi.org/project/semantic-rdf-mapper/
- **Documentation**: https://github.com/Rxcthefirst/RdfMapper/blob/main/docs
- **Issues**: https://github.com/Rxcthefirst/RdfMapper/issues

## 📄 License

MIT License - Free for commercial and personal use

---

**Built by the RDFMap Team** | [⭐ Star on GitHub](https://github.com/Rxcthefirst/RdfMapper)

