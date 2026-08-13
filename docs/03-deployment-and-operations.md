# Middle East Geopolitical Intelligence Platform — Deployment and Operations Guide

This guide provides instructions for deploying, running, operating, and maintaining the Middle East Geopolitical Intelligence Platform in local development, staging, and single-server production environments.

---

## 1. System Topology Overview

The platform uses a modular monolith architecture with async application services, durable background task queues, vector/relational persistence, and object storage:

```text
  ┌─────────────────────────────────┐
  │  FastAPI REST API / Frontend    │
  │  (Port 8000 / Uvicorn / Next)   │
  └──────┬──────┬─────┬─────────────┘
         │      │     │
     ┌───┘      │     └───┐
     │          │         │
┌────▼────┐ ┌───▼───┐ ┌───▼─────────────┐
│PostgreSQL│ │ Redis │ │ MinIO / S3 Store│
│+pgvector│ │(Broker│ │ (Raw/Artifacts) │
│(Port5432)│ │Port6380│(Ports 9000/9001)│
└────▲────┘ └───▲───┘ └─────────────────┘
     │          │
     └────┬─────┘
          │
  ┌───────┴─────────┐
  │  Celery Worker &│
  │   Celery Beat   │
  └─────────────────┘
```

---

## 2. Prerequisites

### 2.1 Host Requirements
- **OS**: Linux (Ubuntu 22.04 LTS / Debian 12 recommended for production) or Windows 10/11 with WSL2 / PowerShell for development.
- **CPU**: Minimum 2 vCPUs (4+ vCPUs recommended).
- **RAM**: Minimum 4 GB RAM (8 GB+ recommended).
- **Storage**: Minimum 20 GB SSD storage.

### 2.2 Software Dependencies
- [Python 3.13+](https://www.python.org/)
- [`uv`](https://github.com/astral-sh/uv) (fast Python package and environment manager)
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
| `DATABASE_URL` | PostgreSQL connection string (asyncpg driver) | `postgresql+asyncpg://mei:mei@localhost:5432/mei` |
| `REDIS_URL` | Redis connection URL for Celery broker & caching | `redis://localhost:6380/0` |
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

---

## 4. Local Development Setup

### 4.1 Quickstart with `uv` and Native Services

1. **Install Python dependencies**:
   ```bash
   uv sync
   ```

2. **Start Infrastructure Services (Postgres, Redis, MinIO)**:
   ```bash
   make compose-up
   ```

3. **Run Database Migrations**:
   ```bash
   make migrate
   ```

4. **Seed Database with Initial Data**:
   ```bash
   make seed
   ```

5. **Start API Server**:
   ```bash
   make dev
   ```
   *The API will be live at `http://localhost:8000` with interactive Swagger docs at `http://localhost:8000/docs`.*

6. **Start Celery Background Worker**:
   ```bash
   make worker
   ```

7. **Start Celery Beat Scheduler (In a separate terminal)**:
   ```bash
   make beat
   ```

### 4.2 Full Docker Compose Development

To run all application components (API, Worker, Beat, Postgres, Redis, MinIO, Prometheus, Grafana) inside Docker:

```bash
docker compose up --build -d
```

To run database migrations inside the Docker stack:
```bash
docker compose exec api uv run alembic upgrade head
docker compose exec api uv run python scripts/seed.py
```

To view logs:
```bash
docker compose logs -f api worker beat
```

To stop all services:
```bash
make compose-down
```

---

## 5. Running Quality & Test Checks

Before committing or deploying, run the complete verification suite:

```bash
# Run unit & integration tests
make test

# Run linter & formatter checks
make lint

# Run static type checker
make typecheck
```

---

## 6. Single-Server Production Deployment

For production deployments on a dedicated Linux VPS/VM (e.g., Ubuntu 22.04 LTS):

### 7.1 Security Hardening
1. **Firewall (UFW)**: Allow only ports `80`, `443`, and `22` externally. Keep PostgreSQL (`5432`), Redis (`6379`), and MinIO (`9000`) internal to the Docker network.
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

2. **Reverse Proxy (Nginx / Traefik)**: Set up SSL/TLS termination with Let's Encrypt:
   ```nginx
   server {
       server_name mei.example.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

3. **Production Secrets**: Generate a strong random `APP_SECRET_KEY`:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

### 7.2 Deployment Steps

```bash
# Clone repository
git clone https://github.com/your-org/middle-east-geopolitic.git
cd middle-east-geopolitic

# Create production .env file
cp .env.example .env
nano .env

# Build and start services in detached mode
docker compose -f docker-compose.yml up -d --build

# Run migrations & seed data
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed.py
```

---

## 8. Backup and Maintenance Procedures

### 8.1 PostgreSQL Database Backup & Restore

**Automated Daily Backup Script**:
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

### 8.2 MinIO Data Volume Backup
Backup the MinIO Docker volume `postgres-data` and `minio-data`:
```bash
docker run --rm -v middle-east-geopolitic_minio-data:/volume -v /var/backups/mei:/backup busybox tar cvzf /backup/minio_data_$(date +%Y%m%d).tar.gz /volume
```

---

## 9. Observability & Health Monitoring

### 9.1 Health Check Endpoints
The platform exposes standardized health monitoring endpoints:

- `GET /api/v1/health/live`: Liveness check (returns `200 OK` if API is responsive).
- `GET /api/v1/health/ready`: Readiness check (verifies PostgreSQL database connection).
- `GET /api/v1/health/dependencies`: Detailed status of Postgres, Redis, MinIO, and Celery dependencies.

### 9.2 Prometheus & Grafana Dashboards
- **Prometheus**: Accessible at `http://localhost:9090` (scrapes API metrics every 15s).
- **Grafana**: Accessible at `http://localhost:3002` (default credentials: `admin` / `${GRAFANA_ADMIN_PASSWORD}`).

---

## 10. Troubleshooting FAQ

### Q1: Celery tasks are not executing.
- Check if Redis is running (`docker compose exec redis redis-cli ping`).
- Verify Celery worker logs (`docker compose logs -f worker`).
- Ensure `REDIS_URL` matches across API and Worker containers.

### Q2: Alembic migration errors or schema out of sync.
- Run `make migrate` or `uv run alembic upgrade head`.
- Check database revision status: `uv run alembic current`.

### Q3: MinIO bucket errors during file processing.
- Ensure the bucket specified in `S3_BUCKET` exists or let the application auto-create it on startup.
- Verify MinIO console access at `http://localhost:9001` (user: `mei`, pass: `mei-secret-key`).

### Q4: API request returns HTTP 401 Unauthorized.
- Ensure the `Authorization` header contains a valid Bearer API key starting with `mei_`.
- Verify the key has the required scopes for the requested endpoint (e.g., `intelligence:read`, `investigations:read`).
