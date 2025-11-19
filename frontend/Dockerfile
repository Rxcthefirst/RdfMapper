# Build stage
FROM node:20-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && \
    npm cache clean --force

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine as production

# Install curl for healthcheck
RUN apk add --no-cache curl

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create non-root user
RUN addgroup -g 1000 rdfmap && \
    adduser -D -u 1000 -G rdfmap rdfmap && \
    chown -R rdfmap:rdfmap /usr/share/nginx/html /var/cache/nginx /var/log/nginx /etc/nginx/conf.d

# Switch to non-root user
USER rdfmap

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

# Development stage (for local development)
FROM node:20-alpine as development

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

