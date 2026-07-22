# Hermes Operator Agent

Hermes is the AI operator for the Middle East Geopolitical Intelligence Platform.

## Structure

- `SYSTEM.md`: Core prompt and rules.
- `mcp/server.py`: Model Context Protocol (MCP) server exposing tools over stdio to call the FastAPI endpoints.

## Tool Categories

1. **Read Tools**:
   - Querying actors, events, claims, evidence, relationships, risk scores, active scenarios, and submitted imagery.
2. **Analytical Tools**:
   - Launching investigations, comparing narratives, generating briefs or weekly outlooks, ranking/pathfinding over the actor-relationship graph, listing analyst disagreements, and reviewing multi-model agreement results.
3. **Controlled Write Tools**:
   - Submitting sources, adding analyst notes, recording analyst positions, submitting imagery, managing alerts/monitors, and approving content (requires verification).
