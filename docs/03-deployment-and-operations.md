# Middle East Geopolitical Intelligence Platform — Deployment and Operations Guide

This guide provides instructions for deploying, running, operating, and maintaining the Middle East Geopolitical Intelligence Platform in local development, staging, and single-server production environments.

---

## 1. System Topology Overview

The platform uses a modular monolith architecture with async application services, durable background task queues, vector/relational persistence, and object storage:

```text
                               ┌──────────────────────────┐
                               │   Hermes MCP Operator    │
                               │   (stdio or stdio/HTTP)  │
                               └────────────┬─────────────┘
                                            │ API Key / HTTP
                               ┌────────────▼─────────────┐
                               │    FastAPI REST API      │
                               │  (Port 8000 / Uvicorn)   │
                               └──────┬──────┬─────┬──────┘
                                      │      │     │
                 ┌────────────────────┘      │     └────────────────────┐
                 │                           │                          │
        ┌────────▼────────┐         ┌────────▼────────┐        ┌────────▼────────┐
        │  PostgreSQL 16  │         │   Redis 7.0     │        │ MinIO / S3 Store│
        │   + pgvector    │         │  (Broker/Result)│        │ (Raw/Artifacts) │
        │   (Port 5432)   │         │   (Port 6380)   │        │(Ports 9000/9001)│
        └────────▲────────┘         └────────▲────────┘        └─────────────────┘
                 │                           │
                 └────────────┬──────────────┘
                              │
                    ┌─────────┴─────────┐
                    │  Celery Worker &  │
                    │   Celery Beat     │
                    └───────────────────┘
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
| `HERMES_API_KEY` | API key for Hermes operator integration | `hermes-secret-api-key` |

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

## 6. Hermes MCP Agent Operator Setup

Hermes serves as the AI operator for the Middle East Geopolitical Intelligence Platform. It connects to the platform via the Model Context Protocol (MCP) over `stdio`, proxying authenticated requests to the FastAPI backend. Hermes must never bypass the API to connect directly to PostgreSQL, Redis, MinIO, or Celery.

---

### 6.1 Overview & Architecture

```text
┌─────────────────────────┐          stdio (JSON-RPC)          ┌───────────────────────────┐
│  Hermes Host / Client   │ ─────────────────────────────────> │   agents/hermes/mcp/      │
│ (Claude / Cursor / CLI) │ <───────────────────────────────── │         server.py         │
└─────────────────────────┘                                    └─────────────┬─────────────┘
                                                                             │ HTTP + Bearer Token
                                                               ┌─────────────▼─────────────┐
                                                               │     FastAPI Backend       │
                                                               │  (http://localhost:8000)  │
                                                               └───────────────────────────┘
```

The Hermes entrypoint is located at [`agents/hermes/mcp/server.py`](file:///c:/Users/a.ekbatani/source/personal/middle-east-geopolitic/agents/hermes/mcp/server.py). Detailed profile guidance is available in [`agents/hermes/PROFILE-SETUP.md`](file:///c:/Users/a.ekbatani/source/personal/middle-east-geopolitic/agents/hermes/PROFILE-SETUP.md).

---

### 6.2 Step-by-Step Configuration Guide

#### Step 1: Verify Application & API Health
Before configuring Hermes, ensure the FastAPI application and backend services are active and healthy.

```bash
# Check basic API health
curl -f http://localhost:8000/api/v1/health/live

# Check database & readiness status
curl -f http://localhost:8000/api/v1/health/ready
```

#### Step 2: Issue a Dedicated Scoped API Key
Hermes requires a valid API key (prefixed with `mei_`). Do not use default or placeholder keys in production. Assign API key scopes based on the required role profile:

| Profile Role | Required Scopes | Intended Capability |
|---|---|---|
| `hermes-read` | `intelligence:read`, `investigations:read` | Read-only search, risk scores, evidence retrieval, graph queries, and report browsing. |
| `hermes-analyst` | Read scopes + `sources:submit`, `investigations:create`, `reports:generate`, `scenarios:simulate`, `analyst_assessments:record`, `imagery:submit` | Analytical workflows capable of creating working draft records and running simulations. |
| `hermes-monitor` | `monitors:manage` + Read scopes | Creating, modifying, and cancelling event/indicator monitors. |
| `hermes-approver` | Read scopes + `events:approve`, `reports:approve` | High-privilege approval or publication of intelligence products (requires human confirmation). |

> [!IMPORTANT]
> Never grant an approver key to standard automated Hermes sessions. Always apply the principle of least privilege.

#### Step 3: Configure Environment Variables
Hermes MCP server relies on two primary environment variables:

| Variable | Description | Development / Production Value |
|---|---|---|
| `API_URL` | Base URL of the FastAPI server | `http://localhost:8000` (Local), `http://api:8000` (Docker Compose network), or `https://intel.example.com` (Prod) |
| `HERMES_API_KEY` | Bearer API token created in Step 2 | `mei_live_secret_key_12345` |

#### Step 4: Configure the MCP Client

##### Option A: Claude Desktop Configuration
Add the following entry to your `claude_desktop_config.json` (located at `%APPDATA%\Claude\claude_desktop_config.json` on Windows or `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "middle-east-intelligence": {
      "command": "uv",
      "args": [
        "--directory",
        "C:/Users/a.ekbatani/source/personal/middle-east-geopolitic",
        "run",
        "python",
        "agents/hermes/mcp/server.py"
      ],
      "env": {
        "API_URL": "http://localhost:8000",
        "HERMES_API_KEY": "mei_your_generated_api_key_here"
      }
    }
  }
}
```

##### Option B: Generic MCP Client / Profile Configuration
For generic MCP runners, use standard `stdio` transport settings:

```json
{
  "name": "middle-east-intelligence",
  "transport": "stdio",
  "command": "uv",
  "args": ["run", "python", "agents/hermes/mcp/server.py"],
  "cwd": "/path/to/middle-east-geopolitic",
  "env": {
    "API_URL": "http://localhost:8000",
    "HERMES_API_KEY": "mei_your_generated_api_key_here"
  },
  "system_prompt_file": "agents/hermes/SYSTEM.md"
}
```

##### Option C: PowerShell / Command Line Direct Launch
To test running the MCP server interactively from PowerShell (diagnostics output to `stderr`):

```powershell
$env:API_URL = "http://localhost:8000"
$env:HERMES_API_KEY = "mei_your_generated_api_key_here"
uv run python agents/hermes/mcp/server.py
```

> [!NOTE]
> Standard output (`stdout`) is strictly reserved for JSON-RPC messages. All logging and startup status messages are directed to `stderr`.

#### Step 5: Load System Instructions (`SYSTEM.md`)
Always load [`agents/hermes/SYSTEM.md`](file:///c:/Users/a.ekbatani/source/personal/middle-east-geopolitic/agents/hermes/SYSTEM.md) into the Hermes agent prompt configuration. This file enforces essential operational guardrails:
- Grounding responses in retrieved database evidence rather than pre-trained assumptions.
- Distinguishing verified facts from disputed claims and forecasts.
- Requiring explicit user confirmation prior to executing consequential write or approval operations.

#### Step 6: Verification & Validation
1. **Start the MCP Client**: Launch your MCP client (or restart Claude Desktop).
2. **Inspect Tool Availability**: Confirm that Hermes registers tools such as `search_intelligence`, `get_event`, `get_active_scenarios`, `launch_investigation`, and `record_analyst_assessment`.
3. **Execute a Test Query**: Ask Hermes:
   > "Search the intelligence database for recent events in Lebanon."
4. **Audit Log Verification**: Verify that HTTP requests appear in the FastAPI backend log with the correct API key context.

---

## 7. Single-Server Production Deployment

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

### Q4: Hermes agent tool calls fail with HTTP 401.
- Ensure `HERMES_API_KEY` set in your MCP client environment (or `.env`) is a valid, active API key starting with `mei_`.
- Verify the key has the required scopes for the endpoints Hermes is attempting to access (e.g., `intelligence:read`, `investigations:read`).
