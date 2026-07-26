# Middle East Geopolitical Intelligence Platform — Deployment and Operations Guide

This guide provides instructions for deploying, running, operating, and maintaining the Middle East Geopolitical Intelligence Platform in local development, staging, and single-server production environments.

---

## 1. System Topology Overview

The platform uses a modular monolith architecture with async application services, durable background task queues, vector/relational persistence, and object storage. The Hermes agent operator can run co-located or on a separated server over HTTPS:

```text
  ┌─────────────────────────────────┐        ┌──────────────────────────────────┐
  │  Hermes Host (Local Machine)    │        │  Hermes Server (Separated Host)  │
  │  (stdio / Claude / Cursor / CLI)│        │  (Remote Agent Server / Node)    │
  └────────────────┬────────────────┘        └────────────────┬─────────────────┘
                   │ stdio (JSON-RPC)                         │ stdio (JSON-RPC)
  ┌────────────────▼────────────────┐        ┌────────────────▼─────────────────┐
  │ Local Hermes MCP Bridge         │        │ Remote Hermes MCP Bridge         │
  │ (agents/hermes/mcp/server.py)   │        │ (agents/hermes/mcp/server.py)    │
  └────────────────┬────────────────┘        └────────────────┬─────────────────┘
                   │ HTTP / localhost                         │ HTTPS / TLS (API Key)
                   │                                          │
                   └──────────────────┬───────────────────────┘
                                      │ Network / REST API
                         ┌────────────▼─────────────┐
                         │    FastAPI REST API      │
                         │  (Port 8000 / Uvicorn)   │
                         └──────┬──────┬─────┬──────┘
                                │      │     │
            ┌───────────────────┘      │     └────────────────────┐
            │                          │                          │
   ┌────────▼────────┐        ┌────────▼────────┐        ┌────────▼────────┐
   │  PostgreSQL 16  │        │   Redis 7.0     │        │ MinIO / S3 Store│
   │   + pgvector    │        │  (Broker/Result)│        │ (Raw/Artifacts) │
   │   (Port 5432)   │        │   (Port 6380)   │        │(Ports 9000/9001)│
   └────────▲────────┘        └────────▲────────┘        └─────────────────┘
            │                          │
            └────────────┬─────────────┘
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

Hermes serves as the AI operator for the Middle East Geopolitical Intelligence Platform. It connects to the platform via the Model Context Protocol (MCP) over `stdio`, proxying authenticated HTTP/HTTPS requests to the FastAPI backend. Hermes must **never** bypass the API layer to connect directly to PostgreSQL, Redis, MinIO, or Celery.

---

### 6.1 Deployment Topologies

The platform supports two deployment topologies for the Hermes operator:

#### Topology A: Co-Located / Local Deployment
Hermes runs on the same physical host, developer workstation, or container network as the FastAPI backend.
- **Transport**: MCP over `stdio` launched directly by local client (Claude Desktop, Cursor, CLI).
- **Endpoint**: `API_URL=http://localhost:8000` (host) or `http://api:8000` (Docker Compose network).

#### Topology B: Separated Remote Hermes Server Deployment
The Hermes server/operator runs on a dedicated, isolated server (e.g., remote AI runner node, separate cloud VM, or edge server) distinct from the application server.
- **Transport**: MCP over `stdio` on the remote host, or local stdio tunneling over SSH to the remote host.
- **Endpoint**: `API_URL=https://intel.example.com` (Public HTTPS domain or private VPN IP of the FastAPI server).
- **Communication Boundary**: All interaction occurs strictly over TLS-encrypted HTTP REST calls. No database or queue ports are exposed to the Hermes server.

```text
┌───────────────────────────────────────────────────┐          HTTPS / REST API (Port 443)         ┌───────────────────────────────────────────────────┐
│              SEPARATED HERMES SERVER              │ ───────────────────────────────────────────> │              PLATFORM APPLICATION SERVER          │
│                                                   │                                              │                                                   │
│ ┌──────────────────────┐   stdio   ┌────────────┐ │ <─────────────────────────────────────────── │ ┌──────────────────────┐  Internal  ┌───────────┐ │
│ │  Hermes Client/Agent │ ────────> │ MCP Server │ │               Bearer mei_ Token              │ │    FastAPI Server    │ ──────────> │ PostgreSQL│ │
│ │   (CLI / Orchestrator│ <──────── │ (server.py)│ │                                              │ │    (Port 8000/443)   │             │ Redis/S3  │ │
│ └──────────────────────┘           └────────────┘ │                                              │ └──────────────────────┘             └───────────┘ │
└───────────────────────────────────────────────────┘                                              └───────────────────────────────────────────────────┘
```

---

### 6.2 Network & Security Hardening for Separated Setup

When Hermes is hosted on a separated server:

1. **Firewall Boundaries**:
   - **Platform Application Server**: Allow inbound traffic only on ports `80` / `443` (HTTP/HTTPS) from the Hermes server IP address (or open web if public). Keep PostgreSQL (`5432`), Redis (`6380`), MinIO (`9000`), and Celery workers strictly blocked from external/Hermes server network interfaces.
   - **Hermes Server**: Requires only outbound HTTPS access to `API_URL`. Does not require any inbound public ports unless remote SSH access is used.

2. **Authentication & Least Privilege**:
   - Issue a dedicated `mei_...` Bearer API key specifically for the separated Hermes instance.
   - Store `HERMES_API_KEY` securely in the Hermes server environment secrets manager (e.g., systemd environment file, HashiCorp Vault, Docker secret, or `.env` on the Hermes server).
   - Assign only required role scopes (`hermes-read`, `hermes-analyst`, or `hermes-monitor`). Avoid granting `hermes-approver` keys to un-monitored remote sessions.

---

### 6.3 Deployment Methods on a Separated Hermes Server

#### Option 1: Native Python / `uv` Execution on Separated Server
Deploy the lightweight Hermes MCP files onto the separated server and execute directly:

1. **Copy Hermes Files to Remote Host**:
   Copy the `agents/hermes/` directory and `pyproject.toml` / `uv.lock` (or minimal Python environment) to the separated server:
   ```bash
   scp -r agents/hermes pyproject.toml uv.lock user@hermes-server:/opt/mei-hermes/
   ```

2. **Install Dependencies on Remote Host**:
   ```bash
   ssh user@hermes-server
   cd /opt/mei-hermes
   uv sync
   ```

3. **Configure Environment File (`/opt/mei-hermes/.env`)**:
   ```env
   API_URL=https://intel.example.com
   HERMES_API_KEY=mei_live_secret_key_from_platform_server
   ```

4. **Launch MCP Bridge**:
   ```bash
   uv run python agents/hermes/mcp/server.py
   ```

#### Option 2: Remote MCP stdio Tunneling over SSH
If your MCP client (e.g., Claude Desktop, Cursor) is on Machine A and the separated Hermes server is Machine B, connect via an SSH stdio wrapper:

Add to your local `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "middle-east-intelligence-remote": {
      "command": "ssh",
      "args": [
        "-i", "~/.ssh/id_ed25519",
        "user@hermes-server.example.com",
        "API_URL=https://intel.example.com HERMES_API_KEY=mei_live_secret_key uv run --directory /opt/mei-hermes python agents/hermes/mcp/server.py"
      ]
    }
  }
}
```

#### Option 3: Containerized Hermes MCP Bridge on Separated Host
Build a minimal standalone container on the separated Hermes server:

```dockerfile
# Dockerfile.hermes (placed on separated server)
FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app
COPY agents/hermes /app/agents/hermes
COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen
ENV API_URL="https://intel.example.com"
ENV HERMES_API_KEY=""
ENTRYPOINT ["uv", "run", "python", "agents/hermes/mcp/server.py"]
```

Run container interactively over stdio:
```bash
docker run -i --rm \
  -e API_URL="https://intel.example.com" \
  -e HERMES_API_KEY="mei_live_secret_key_12345" \
  mei-hermes-mcp
```

---

### 6.4 Step-by-Step Configuration Guide

#### Step 1: Verify Application & API Health
Before configuring Hermes, verify that the FastAPI backend health endpoints respond cleanly from the separated Hermes host:

```bash
# Test from the separated Hermes server terminal
curl -f https://intel.example.com/api/v1/health/live
curl -f https://intel.example.com/api/v1/health/ready
```

#### Step 2: Issue a Dedicated Scoped API Key
Issue an API key starting with `mei_` on the platform server for the Hermes server identity. Assign scopes based on operational requirements:

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

| Variable | Description | Value for Local Setup | Value for Separated Server |
|---|---|---|---|
| `API_URL` | Base URL of the FastAPI server | `http://localhost:8000` | `https://intel.example.com` or `http://192.168.1.50:8000` |
| `HERMES_API_KEY` | Bearer API token created in Step 2 | `mei_dev_secret_key` | `mei_live_secret_key_12345` |

#### Step 4: Configure the MCP Client

##### Local Host Configuration (`claude_desktop_config.json`)
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
        "HERMES_API_KEY": "mei_live_secret_key_12345"
      }
    }
  }
}
```

##### Separated Remote Server Profile (`mcp_config.json`)
```json
{
  "name": "middle-east-intelligence-remote",
  "transport": "stdio",
  "command": "uv",
  "args": ["run", "python", "agents/hermes/mcp/server.py"],
  "cwd": "/opt/mei-hermes",
  "env": {
    "API_URL": "https://intel.example.com",
    "HERMES_API_KEY": "mei_live_secret_key_12345"
  },
  "system_prompt_file": "agents/hermes/SYSTEM.md"
}
```

> [!NOTE]
> Standard output (`stdout`) is strictly reserved for JSON-RPC messages. All logging and startup status messages are directed to `stderr`.

#### Step 5: Load System Instructions (`SYSTEM.md`)
Always load [`agents/hermes/SYSTEM.md`](file:///c:/Users/a.ekbatani/source/personal/middle-east-geopolitic/agents/hermes/SYSTEM.md) into the Hermes agent prompt configuration. This file enforces essential operational guardrails:
- Grounding responses in retrieved database evidence rather than pre-trained assumptions.
- Distinguishing verified facts from disputed claims and forecasts.
- Requiring explicit user confirmation prior to executing consequential write or approval operations.

#### Step 6: Verification & Validation
1. **Start the MCP Client**: Launch your MCP client (or restart Claude Desktop/Hermes agent).
2. **Inspect Tool Availability**: Confirm that Hermes registers tools such as `search_intelligence`, `get_event`, `get_active_scenarios`, `launch_investigation`, and `record_analyst_assessment`.
3. **Execute a Test Query**: Ask Hermes:
   > "Search the intelligence database for recent events in Lebanon."
4. **Audit Log Verification**: Check the FastAPI backend server logs to verify that HTTP requests arrive with the correct Bearer API key context and IP address of the separated Hermes server.

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
