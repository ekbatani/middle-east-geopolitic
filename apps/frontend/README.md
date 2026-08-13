# Middle East Geopolitical Intelligence Platform — Web Frontend

The official web application interface for the Middle East Geopolitical Intelligence Platform, built with Next.js 15 (App Router), React, TypeScript, and Tailwind CSS.

---

## 1. Overview & Capabilities

The frontend provides interactive tools and dashboards for geopolitical analysts:

- **Intelligence Dashboard**: Real-time view of verified events, country risk scores, and breaking intelligence.
- **Geospatial Map & Kinetic Views**: Interactive mapping of geopolitical events, troop deployments, spatial clustering, and conflict hotspots.
- **Network Graph Analytics**: Multi-relational network topology visualization for state actors, armed proxy networks, and influence vectors.
- **Risk Engine & Calibration**: Detailed indicator breakdowns, score change explanations, and forecast Brier calibration charts.
- **Investigations & Monitor Center**: Workspace for initiating investigations, tracking open cases, taking notes, and configuring automated alert thresholds.
- **Multi-Model Review & Disagreement Tracking**: Stance analysis comparing candidate claims across different LLMs and tracking consensus/disagreement among analysts.
- **Imagery Evidence Viewer**: Inspection interface for satellite and open-source imagery evidence with geographic tags and bounding boxes.

---

## 2. Technology Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS & CSS Modules
- **State & Data Fetching**: React Hooks & Server/Client Components
- **API Client**: REST API integration connecting to FastAPI (`/api/v1`)

---

## 3. Environment Configuration

The frontend requires the API server URL configuration. Create or edit `.env.local` in `apps/frontend`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

| Variable | Description | Default |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Base URL of the FastAPI Backend API | `http://localhost:8000` |

---

## 4. Development & Running Locally

### Standalone Local Development

```bash
# Navigate to frontend directory
cd apps/frontend

# Install dependencies
npm install

# Start local development server (with hot reload)
npm run dev
```

The application will be accessible at [http://localhost:3000](http://localhost:3000).

### Build for Production

```bash
npm run build
npm run start
```

### Docker Compose Deployment

When running via the root `docker-compose.yml`, the frontend container is automatically built and served on port `3003`:

```bash
make compose-up
```

Access the frontend at [http://localhost:3003](http://localhost:3003).
