#!/bin/bash
set -e

echo "🚀 Starting RDFMap All-in-One Container..."
echo "==========================================="
echo ""

# Set default environment variables if not provided
export DATABASE_URL="${DATABASE_URL:-sqlite:///app/data/rdfmap.db}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
export CELERY_BROKER_URL="${CELERY_BROKER_URL:-${REDIS_URL}}"
export CELERY_RESULT_BACKEND="${CELERY_RESULT_BACKEND:-${REDIS_URL}}"
export SECRET_KEY="${SECRET_KEY:-change-me-in-production}"
export CORS_ORIGINS="${CORS_ORIGINS:-*}"

echo "📋 Configuration:"
echo "  - Database: ${DATABASE_URL}"
echo "  - Redis: ${REDIS_URL}"
echo "  - Port: 8080"
echo ""

# Create necessary directories
mkdir -p /app/uploads /app/data /var/log/supervisor /var/log/nginx

echo "✅ Starting services (nginx + API + worker)..."
echo ""

# Execute the CMD
exec "$@"

