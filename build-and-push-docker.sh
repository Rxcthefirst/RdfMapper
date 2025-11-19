#!/bin/bash
set -e

# RDFMap Docker Build and Push Script
# Usage: ./build-and-push-docker.sh [version]

VERSION="${1:-latest}"
RDFMAP_VERSION="${2:-0.3.0}"
DOCKER_USERNAME="${DOCKER_USERNAME:-rxcthefirst}"

echo "🐳 Building RDFMap Docker Images"
echo "================================"
echo "Version: ${VERSION}"
echo "RDFMap Library Version: ${RDFMAP_VERSION}"
echo "Docker Username: ${DOCKER_USERNAME}"
echo ""

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if logged in to Docker Hub
if ! docker info | grep -q "Username"; then
    echo "⚠️  Not logged in to Docker Hub. Please run: docker login"
    read -p "Do you want to login now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker login
    else
        echo "❌ Cannot push images without Docker Hub authentication."
        exit 1
    fi
fi

# Build backend/API image
echo -e "${BLUE}📦 Building backend API image...${NC}"
docker build \
    --build-arg RDFMAP_VERSION=${RDFMAP_VERSION} \
    -t ${DOCKER_USERNAME}/rdfmap-api:${VERSION} \
    -t ${DOCKER_USERNAME}/rdfmap-api:latest \
    -f backend/Dockerfile \
    backend/

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backend API image built successfully${NC}"
else
    echo "❌ Failed to build backend API image"
    exit 1
fi

# Build frontend/UI image
echo -e "${BLUE}📦 Building frontend UI image...${NC}"
docker build \
    --target production \
    -t ${DOCKER_USERNAME}/rdfmap-ui:${VERSION} \
    -t ${DOCKER_USERNAME}/rdfmap-ui:latest \
    -f frontend/Dockerfile \
    frontend/

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Frontend UI image built successfully${NC}"
else
    echo "❌ Failed to build frontend UI image"
    exit 1
fi

# List built images
echo ""
echo -e "${BLUE}📋 Built images:${NC}"
docker images | grep "rdfmap"

# Ask for confirmation to push
echo ""
read -p "🚀 Do you want to push these images to Docker Hub? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "⏸️  Skipping push. Images are built locally."
    exit 0
fi

# Push images
echo -e "${BLUE}🚀 Pushing images to Docker Hub...${NC}"

echo -e "${YELLOW}Pushing API image...${NC}"
docker push ${DOCKER_USERNAME}/rdfmap-api:${VERSION}
docker push ${DOCKER_USERNAME}/rdfmap-api:latest

echo -e "${YELLOW}Pushing UI image...${NC}"
docker push ${DOCKER_USERNAME}/rdfmap-ui:${VERSION}
docker push ${DOCKER_USERNAME}/rdfmap-ui:latest

echo ""
echo -e "${GREEN}✅ All images pushed successfully!${NC}"
echo ""
echo "📦 Your images are now available at:"
echo "   • https://hub.docker.com/r/${DOCKER_USERNAME}/rdfmap (All-in-One) ⭐"
echo "   • https://hub.docker.com/r/${DOCKER_USERNAME}/rdfmap-api"
echo "   • https://hub.docker.com/r/${DOCKER_USERNAME}/rdfmap-ui"
echo ""
echo "🚀 Quick Start (Recommended):"
echo "   docker run -d -p 8080:8080 ${DOCKER_USERNAME}/rdfmap:${VERSION}"
echo ""
echo "🚀 Advanced (Microservices):"
echo "   docker pull ${DOCKER_USERNAME}/rdfmap-api:${VERSION}"
echo "   docker pull ${DOCKER_USERNAME}/rdfmap-ui:${VERSION}"
echo "   VERSION=${VERSION} docker-compose -f docker-compose.prod.yml up -d"

