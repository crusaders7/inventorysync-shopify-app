# Container Orchestration Setup for InventorySync

## Overview
This setup uses Docker and Docker Compose to handle container orchestration for the InventorySync application, which includes both a frontend built with React (using Vite) and a backend using FastAPI, along with PostgreSQL and Redis for database and caching. Celery is used for background tasks.

## Docker Setup
- **Multi-Stage Build**: The project uses a multi-stage build to optimize the Docker images. The frontend and backend are built in separate stages.
- **Health Checks**: Each service is configured with health checks to ensure readiness.
- **Environment-Specific Configuration**: We provide `docker-compose.yml` for local development and `docker-compose.production.yml` for production.

## Development Configuration (docker-compose.dev.yml)
- Includes hot reloading for backend and frontend.
- Additional developer tools, like pgAdmin and Mailhog, are included to simplify testing and monitoring.
- Uses environment variables for configuration via `.env` files.

## Production Configuration (docker-compose.production.yml)
- Optimized for performance with resource limits and replicas.
- Includes Prometheus and Grafana for monitoring.
- Uses Nginx to serve the frontend and proxy requests to the backend.

## Usage
### Local Development
1. **Environment Setup**: Copy `.env.example` to `.env` and set appropriate variables.
2. **Build and Start**:
   ```bash
   docker-compose -f docker-compose.dev.yml up --build
   ```
3. **Access**:
   - Frontend: `http://localhost:5173`
   - Backend: `http://localhost:8000`

### Production Deployment
1. **Environment Setup**: Ensure `.env.production` is correctly configured with production variables.
2. **Build and Start**:
   ```bash
   docker-compose -f docker-compose.production.yml up --build -d
   ```
3. **Access**:
   - The application is accessible on ports 80 and 443.

## Monitoring
- **Prometheus** collects metrics from the application.
- **Grafana** is used to visualize metrics.
- **Health Checks** are in place to ensure each service is running correctly.

## Scaling
- Containers can be scaled horizontally based on the requirements, and resource limits are configured to prevent overutilization.

## Backup and Restore
- `postgres_backup` service handles backups of the database on a schedule.
