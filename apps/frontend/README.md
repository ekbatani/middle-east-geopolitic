# Middle East Geopolitical Intelligence Platform — Web Frontend

The official web application interface for the Middle East Geopolitical Intelligence Platform, built with Next.js 15 (App Router), React 19, TypeScript, and Tailwind CSS.

---

## 1. Overview & Operational Modules

The frontend provides a comprehensive command & control suite across 15 operational modules:

1. **Executive Intelligence Dashboard**: Real-time theater metrics, country risk matrix, recent kinetic developments, and daily briefings.
2. **Tactical Geospatial Map**: Interactive SVG Middle East map with coordinate projection, severity filters (1–5), incident clustering, coordinate inspection, and event logging.
3. **Multi-Relational Network Graph**: Graph topology visualization of state actors & armed proxy networks, centrality rankings (degree, betweenness, eigenvector), and shortest-path influence tracing.
4. **Deterministic Risk Engine**: Risk catalog, weighted indicator decomposition, bounded LLM score adjustments, and manual recalculation trigger.
5. **Scenarios & What-If Sandbox**: Scenario registers by family (Status Quo, Rapid Escalation, De-escalation, Regime Crisis, Proxy Shift, Economic Collapse) with probability bounds and hypothetical sandbox simulations.
6. **Probabilistic Forecasts & Brier Calibration**: Auditable prediction registry with target dates, confidence, assumptions, outcome resolution, and Brier reliability scores.
7. **Executive Briefings & Reports**: Daily briefs, weekly strategic outlooks, country and conflict assessments with rich markdown rendering, senior analyst approval, and publication workflows.
8. **Autonomous Investigations Workspace**: Multi-step hypothesis investigation workflows with step execution timelines and findings inspector.
9. **Automated Monitors & Real-Time Alert Dispatch**: Continuous background condition evaluations with multi-channel delivery (Telegram, Webhook, Email).
10. **Actors & Regional Entity Directory**: State powers, armed non-state proxies, leadership tenure timelines, multilingual aliases, and bilateral relationship matrices.
11. **Claims & Verification Stances**: Corroboration and debunking registry linking source document excerpts with stance confidence ratings (supports, refutes, neutral, context).
12. **Analyst Review Queue**: Human-in-the-loop validation queue for entity disambiguation candidates and critical high-impact event confirmations.
13. **Multi-Model LLM Reviews & Disagreements**: Secondary model cross-evaluation score deltas and analyst consensus/spread tracking.
14. **Satellite & Tactical Imagery Evidence**: Commercial SAR/Electro-Optical imagery viewer with bounding box annotations, geotags, and computer vision re-analysis.
15. **Intelligence Sources & Document Ingestion**: Feed registry, document archive, and live URL ingestion with instant text extraction and token chunking.

---

## 2. Architecture & Directory Structure

```
apps/frontend/
├── src/
│   ├── types/                  # 21 domain TypeScript definitions mapping to backend schemas
│   │   ├── common.ts           # UUID, ScopeType, ProblemDetails, etc.
│   │   ├── auth.ts             # JWT, Bearer scopes, Principal
│   │   ├── actors.ts           # Actor, Aliases, Leadership
│   │   ├── events.ts           # Events, Impacts, Map Coordinates
│   │   ├── sources.ts          # Feeds, Documents, Chunks
│   │   ├── claims.ts           # Claims, Evidence stances
│   │   ├── relationships.ts    # Bilateral observations & metrics
│   │   ├── indicators.ts       # Economic & military indicators
│   │   ├── risks.ts            # Score catalog & explanations
│   │   ├── scenarios.ts        # Contingency pathways & simulations
│   │   ├── forecasts.ts        # Probabilistic forecasts & Brier scores
│   │   ├── reports.ts          # Briefings & publication models
│   │   ├── investigations.ts   # Investigation cases & step workflows
│   │   ├── monitors.ts         # Trigger rules & channel dispatch
│   │   ├── graph.ts            # Network topology & centrality
│   │   ├── analyst.ts          # Analyst positions & spreads
│   │   ├── modelReviews.ts     # Multi-LLM review deltas
│   │   ├── imagery.ts          # Satellite evidence & CV annotations
│   │   ├── review.ts           # Review queue items
│   │   ├── intelligence.ts     # Search & composite intelligence
│   │   └── index.ts            # Unified export
│   │
│   ├── services/               # 22 typed API service modules
│   │   ├── client.ts           # Robust base HTTP client with RFC 9457 error parsing & auth injection
│   │   ├── auth.service.ts
│   │   ├── actors.service.ts
│   │   ├── events.service.ts
│   │   ├── sources.service.ts
│   │   ├── documents.service.ts
│   │   ├── claims.service.ts
│   │   ├── relationships.service.ts
│   │   ├── indicators.service.ts
│   │   ├── risks.service.ts
│   │   ├── scenarios.service.ts
│   │   ├── forecasts.service.ts
│   │   ├── reports.service.ts
│   │   ├── intelligence.service.ts
│   │   ├── investigations.service.ts
│   │   ├── monitors.service.ts
│   │   ├── graph.service.ts
│   │   ├── analyst.service.ts
│   │   ├── modelReviews.service.ts
│   │   ├── imagery.service.ts
│   │   ├── review.service.ts
│   │   ├── health.service.ts
│   │   └── index.ts            # Unified service export
│   │
│   ├── context/
│   │   └── AuthContext.tsx     # Bearer token & API key management
│   │
│   ├── components/
│   │   ├── common/             # Zero-dependency UI primitives (Icons, Badges, Modals, Cards)
│   │   ├── layout/             # Top Navbar with Live Health & Global Cmd+K Search, Sidebar
│   │   ├── intelligence/       # Dashboard & Executive Briefings
│   │   ├── map/                # Tactical Geospatial SVG Map
│   │   ├── graph/              # Network Graph & Influence Path Tracer
│   │   ├── risks/              # Deterministic Risk Engine & Breakdown
│   │   ├── scenarios/          # Scenarios & What-If Sandbox
│   │   ├── forecasts/          # Forecast Issuance & Brier Calibration
│   │   ├── reports/            # Markdown Report Reader & Approvals
│   │   ├── investigations/     # Case Step Timelines & Launcher
│   │   ├── monitors/           # Alert Thresholds & Dispatch Rules
│   │   ├── actors/             # Actor Directory & Command Timelines
│   │   ├── claims/             # Claims Registry & Corroboration Stances
│   │   ├── review/             # Entity Resolution & Event Queue
│   │   ├── analysis/           # Multi-Model Reviews & Consensus Tracking
│   │   ├── imagery/            # Satellite Evidence & CV Object Detection
│   │   └── sources/            # Feed Collectors & URL Ingestion
│   │
│   └── app/
│       ├── layout.tsx          # Root Layout & Typography
│       ├── globals.css         # Dark Tactical Theme & Custom Scrollbars
│       └── page.tsx            # Main Application Orchestrator
```

---

## 3. Environment Configuration

Create or edit `.env.local` in `apps/frontend`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

| Variable | Description | Default |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Base URL of the FastAPI Backend API | `http://localhost:8000` |

---

## 4. Development & Running Locally

```bash
# Navigate to frontend directory
cd apps/frontend

# Install dependencies
npm install

# Start local development server
npm run dev
```

The application will be accessible at [http://localhost:3000](http://localhost:3000).
