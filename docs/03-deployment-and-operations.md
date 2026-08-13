# Middle East Geopolitical Intelligence Platform — Deployment and Operations Guide

This guide provides instructions for deploying, running, operating, and maintaining the Middle East Geopolitical Intelligence Platform in local development, staging, and single-server production environments.

---

## 1. System Topology Overview

The platform uses a modular monolith architecture with async FastAPI application services, a Next.js web frontend, relational vector persistence, key-value caching, and object storage:

```text
  ┌────────────────────────┐      ┌─────────────────────────┐
  │  Next.js Web Frontend  │      │  FastAPI REST API       │
  │  (Port 3003 / Docker)  ├─────►│  (Port 8000 / Uvicorn)  │
  └────────────────────────┘      └────┬──────┬──────┬──────┘
                                       │      │      │
                                   ┌───┘      │      └───┐
                                   │          │          │
                              ┌────▼────┐ ┌───▼───┐ ┌────▼───────────┐
                              │PostgreSQL│ │ Redis │ │ MinIO / S3    │
                              │+pgvector│ │(Cache)│ │ (Raw/Artifacts)│
                              │(Port5432)│(Port6379)│(Ports 9000/9001)│
                              └─────────┘ └───────┘ └────────────────┘
```

---

## 2. Prerequisites

### 2.1 Host Requirements
- **OS**: Linux (Ubuntu 22.04 LTS / Debian 12 recommended for production) or macOS / Windows 10/11 with WSL2 for development.
- **CPU**: Minimum 2 vCPUs (4+ vCPUs recommended).
- **RAM**: Minimum 4 GB RAM (8 GB+ recommended).
- **Storage**: Minimum 20 GB SSD storage.

### 2.2 Software Dependencies
- [Python 3.13+](https://www.python.org/)
- [`uv`](https://github.com/astral-sh/uv) (fast Python package and environment manager)
- [Node.js 18+](https://nodejs.org/) & `npm`
- [Docker Engine 24.0+](https://docs.docker.com/engine/install/) & [Docker Compose v2+](https://docs.docker.com/compose/)
- Git

---

## 3. Environment Configuration

Copy `.env.example` to `.env` and adjust the settings:

```bash
cp .env.example .env
```

### 3.1 Core Environment Variables

| Variable | Description | Default / Development Value |
|---|---|---|
| `APP_ENV` | Application environment (`development`, `staging`, `production`) | `development` |
| `APP_SECRET_KEY` | Secret key for JWT signing and security hashing | `change-me-in-production-min-32-chars!` |
| `DATABASE_URL` | PostgreSQL connection string (asyncpg driver) | `postgresql+asyncpg://mei:mei@postgres:5432/mei` |
| `REDIS_URL` | Redis connection URL for caching & session storage | `redis://localhost:6379/0` |
| `S3_ENDPOINT_URL` | S3 / MinIO endpoint URL | `http://localhost:9000` |
| `S3_ACCESS_KEY` | Object storage access key | `mei` |
| `S3_SECRET_KEY` | Object storage secret key | `mei-secret-key` |
| `S3_BUCKET` | Default storage bucket name | `mei-intelligence` |
| `LLM_PROVIDER` | LLM provider backend (`openai`, `openrouter`, `opencode_go`, `nvidia_build`, `ollama`, `fake`) | `openai` |
| `LLM_MODEL` | LLM model identifier | `gpt-4o-mini` |
| `LLM_API_KEY` | API key for LLM provider | `your-openai-api-key` |
| `LLM_BASE_URL` | Optional base URL override for LLM provider API | `` |
| `JWT_ISSUER` | JWT token issuer | `mei-platform` |
| `JWT_AUDIENCE` | JWT token audience | `mei-clients` |
| `NEXT_PUBLIC_API_URL` | API Base URL accessed by the Next.js Frontend | `http://localhost:8000` |

---

## 4. Local Development Setup

### 4.1 Quickstart with Docker Compose (Recommended)

1. **Copy Environment File**:
   ```bash
   cp .env.example .env
   ```

2. **Start Full Application Stack**:
   ```bash
   make compose-up
   ```

   This launches PostgreSQL+pgvector, Redis, MinIO, the FastAPI API container (which automatically runs database migrations and seeds initial data), and the Next.js Web Frontend.

3. **Access Services**:
   - Web Frontend: `http://localhost:3003`
   - FastAPI API: `http://localhost:8000`
   - API Documentation (Swagger): `http://localhost:8000/docs`

4. **Stop Application Stack**:
   ```bash
   make compose-down
   ```

### 4.2 Manual Development Setup

1. **Start Database and Storage Services**:
   ```bash
   docker compose up -d postgres redis minio
   ```

2. **Install Python Dependencies and Set Up Environment**:
   ```bash
   uv sync
   ```

3. **Run Database Migrations and Seed Data**:
   ```bash
   make migrate
   make seed
   ```

4. **Start API Server**:
   ```bash
   make dev
   ```
   *The API will be live at `http://localhost:8000`.*

5. **Start Frontend App**:
   ```bash
   cd apps/frontend
   npm install
   npm run dev
   ```
   *The Next.js frontend will be live at `http://localhost:3000`.*

---

## 5. Running Quality & Test Checks

Before committing code, run the full verification suite:

```bash
# Run unit & integration tests
make test

# Run linter & formatter checks
make lint

# Apply automatic formatting
make format

# Run static type checker
make typecheck
```

---

## 6. Production Deployment Guide

For single-server production deployments on a Linux VPS/VM:

### 6.1 Security Hardening
1. **Firewall (UFW)**: Allow only ports `80`, `443`, and `22` externally. Keep PostgreSQL (`5432`), Redis (`6379`), and MinIO (`9000`) internal to the Docker network.
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

2. **Reverse Proxy (Nginx / Traefik)**: Set up SSL/TLS termination routing to port 3003 (Frontend) and `/api` to port 8000 (API Server).

3. **Production Secrets**: Generate a strong random `APP_SECRET_KEY`:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

### 6.2 Deployment Steps

```bash
# Clone repository
git clone https://github.com/your-org/middle-east-geopolitic.git
cd middle-east-geopolitic

# Create production .env file
cp .env.example .env
nano .env

# Build and start services in detached mode
make compose-up
```

---

## 7. Backup and Maintenance Procedures

### 7.1 PostgreSQL Database Backup & Restore

**Daily Backup Script**:
```bash
#!/bin/bash
BACKUP_DIR="/var/backups/mei"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

docker compose exec -T postgres pg_dump -U mei mei | gzip > "$BACKUP_DIR/mei_backup_$TIMESTAMP.sql.gz"
find $BACKUP_DIR -type f -name "*.sql.gz" -mtime +30 -delete
```

**Restoring Database**:
```bash
gunzip -c /var/backups/mei/mei_backup_20260726_100000.sql.gz | docker compose exec -T postgres psql -U mei -d mei
```

---

## 8. Observability & Health Monitoring

### 8.1 Health Check Endpoints
The platform exposes standardized health monitoring endpoints:

- `GET /health/live`: Liveness check (returns `200 OK` if API server is responsive).
- `GET /health/ready`: Readiness check (verifies PostgreSQL database connection).
- `GET /health/dependencies`: Status of infrastructure dependencies (Postgres, Redis, MinIO).

---

## 9. Troubleshooting FAQ

### Q1: API service fails to connect to database in Docker Compose.
- Verify PostgreSQL container status (`docker compose ps postgres`).
- Ensure environment variable `DATABASE_URL` uses host `postgres` inside Docker (`postgresql+asyncpg://mei:mei@postgres:5432/mei`).

### Q2: Alembic migration errors or schema out of sync.
- Run `make migrate` or execute inside container: `docker compose exec api uv run alembic upgrade head`.
- Check database revision status: `uv run alembic current`.

### Q3: Next.js Frontend cannot communicate with API server.
- Verify `NEXT_PUBLIC_API_URL` environment variable is correctly set in `.env` or passed as build argument.
- Check CORS settings in API service.

### Q4: MinIO bucket errors during document processing.
- Ensure the bucket specified in `S3_BUCKET` exists or let the application auto-create it on startup.
- Verify MinIO console access at `http://localhost:9001` (user: `mei`, pass: `mei-secret-key`).
