FROM python:3.11-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install RDFMap core library from PyPI
ARG RDFMAP_VERSION=0.3.0
RUN pip install --no-cache-dir semantic-rdf-mapper==${RDFMAP_VERSION}

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /app/uploads /app/data

# Create non-root user for security
RUN useradd -m -u 1000 rdfmap && \
    chown -R rdfmap:rdfmap /app
USER rdfmap

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

