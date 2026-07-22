import asyncio
import contextlib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any

import httpx

executor = ThreadPoolExecutor(max_workers=1)


def log(msg: str) -> None:
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()


API_URL = os.environ.get("API_URL", "http://localhost:8000")
HERMES_API_KEY = os.environ.get("HERMES_API_KEY", "")

if not HERMES_API_KEY:
    try:
        from mei.shared.config import get_settings
        settings = get_settings()
        HERMES_API_KEY = settings.hermes_api_key
    except Exception:
        pass

log(f"Starting Hermes MCP Server (API: {API_URL})")


async def call_api(method: str, path: str, json_data: Any = None, params: Any = None) -> Any:
    headers = {}
    if HERMES_API_KEY:
        headers["Authorization"] = f"Bearer {HERMES_API_KEY}"

    url = f"{API_URL}{path}"
    async with httpx.AsyncClient() as client:
        try:
            if method.upper() == "GET":
                resp = await client.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == "POST":
                resp = await client.post(url, headers=headers, json=json_data, timeout=30)
            elif method.upper() == "PATCH":
                resp = await client.patch(url, headers=headers, json=json_data, timeout=30)
            elif method.upper() == "DELETE":
                resp = await client.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method {method}")

            if resp.status_code >= 400:
                return {"error": f"API returned status {resp.status_code}", "detail": resp.text}
            if resp.status_code == 204:
                return {"status": "success"}
            return resp.json()
        except Exception as exc:
            return {"error": f"HTTP Request failed: {exc}"}


TOOLS = [
    {
        "name": "search_intelligence",
        "description": "Search the platform's intelligence database (actors, events, claims, documents) using a text query.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search term or query."},
                "limit": {"type": "integer", "description": "Maximum number of results to return.", "default": 50}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_actor_profile",
        "description": "Fetch detailed profile for a given actor by UUID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "actor_id": {"type": "string", "description": "The UUID of the actor."}
            },
            "required": ["actor_id"]
        }
    },
    {
        "name": "get_country_profile",
        "description": "Fetch the current country profile, risk assessments, and relationships.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "country_actor_id": {"type": "string", "description": "The UUID of the country actor."},
                "as_of": {"type": "string", "description": "Optional ISO timestamp boundary."}
            },
            "required": ["country_actor_id"]
        }
    },
    {
        "name": "get_event",
        "description": "Retrieve detailed information about a specific event by UUID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "The UUID of the event."}
            },
            "required": ["event_id"]
        }
    },
    {
        "name": "search_events",
        "description": "Search or list events in the system.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "lifecycle_status": {"type": "string", "description": "Filter by status: e.g., approved, extracted."},
                "limit": {"type": "integer", "description": "Limit results."}
            }
        }
    },
    {
        "name": "get_claim_evidence",
        "description": "Retrieve supporting and contradictory evidence for a claim by UUID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "claim_id": {"type": "string", "description": "The UUID of the claim."}
            },
            "required": ["claim_id"]
        }
    },
    {
        "name": "get_relationship",
        "description": "Fetch the relationship status and score history between actors.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "relationship_id": {"type": "string", "description": "The UUID of the relationship."}
            },
            "required": ["relationship_id"]
        }
    },
    {
        "name": "compare_relationships",
        "description": "Compare multiple relationships as of a specific date.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "relationship_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of relationship UUIDs."
                },
                "as_of": {"type": "string", "description": "Optional ISO timestamp."}
            },
            "required": ["relationship_ids"]
        }
    },
    {
        "name": "get_risk_scores",
        "description": "Retrieve risk assessment scores for a definition and scope.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "risk_definition_id": {"type": "string", "description": "The UUID of the risk definition."},
                "scope_type": {"type": "string", "description": "Scope type: country, relationship, conflict, global."},
                "scope_id": {"type": "string", "description": "Optional scope UUID."}
            },
            "required": ["risk_definition_id", "scope_type"]
        }
    },
    {
        "name": "explain_risk_change",
        "description": "Retrieve detailed contributions and changed indicators for a risk assessment score change.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "risk_definition_id": {"type": "string", "description": "The UUID of the risk definition."},
                "scope_type": {"type": "string", "description": "Scope type: country, relationship, conflict, global."},
                "scope_id": {"type": "string", "description": "Optional scope UUID."}
            },
            "required": ["risk_definition_id", "scope_type"]
        }
    },
    {
        "name": "get_active_scenarios",
        "description": "List active scenarios in the platform.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "scope_type": {"type": "string", "description": "Optional scope type filter."},
                "scope_id": {"type": "string", "description": "Optional scope UUID filter."}
            }
        }
    },
    {
        "name": "get_latest_report",
        "description": "Get the latest report of a given type.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "report_type": {"type": "string", "description": "Report type: daily_brief, weekly_outlook, country_brief, conflict_brief."}
            },
            "required": ["report_type"]
        }
    },
    {
        "name": "get_job_status",
        "description": "Check the status of an ongoing investigation (job).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "The UUID of the investigation."}
            },
            "required": ["job_id"]
        }
    },
    # Analytical
    {
        "name": "start_event_investigation",
        "description": "Launch a deep analytical investigation regarding a specific event.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "The UUID of the event."},
                "priority": {"type": "string", "description": "Priority: low, medium, high. Default is medium."}
            },
            "required": ["event_id"]
        }
    },
    {
        "name": "compare_source_narratives",
        "description": "Run narrative search and comparison across documents and reports.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Query term to compare narratives."}
            },
            "required": ["query"]
        }
    },
    {
        "name": "generate_country_brief",
        "description": "Trigger generation of a country profile and brief report.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "country_actor_id": {"type": "string", "description": "The UUID of the country actor."},
                "as_of": {"type": "string", "description": "Optional ISO timestamp."}
            },
            "required": ["country_actor_id"]
        }
    },
    {
        "name": "generate_conflict_brief",
        "description": "Generate a comparison brief for multiple relationships.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "relationship_ids": {"type": "array", "items": {"type": "string"}, "description": "List of relationship UUIDs."}
            },
            "required": ["relationship_ids"]
        }
    },
    {
        "name": "generate_daily_brief",
        "description": "Trigger the generation of the platform daily brief.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "generate_weekly_outlook",
        "description": "Trigger generation of the weekly outlook brief.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "simulate_scenario",
        "description": "Simulate a hypothetical scenario and get probability/impact recommendations.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "scope_type": {"type": "string", "description": "Scope type: country, relationship, conflict, global."},
                "scope_id": {"type": "string", "description": "Optional scope UUID."},
                "scenario_family": {"type": "string", "description": "controlled_deescalation, managed_confrontation, regional_escalation, systemic_regional_war."},
                "time_horizon": {"type": "string", "description": "e.g., 3 months, 6 months."},
                "hypothetical_context": {"type": "string", "description": "Hypothetical event or development context."}
            },
            "required": ["scope_type", "scenario_family", "time_horizon", "hypothetical_context"]
        }
    },
    {
        "name": "get_actor_centrality",
        "description": "Rank actors by their centrality (degree, betweenness, eigenvector) in the actor-relationship graph.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "relationship_status": {"type": "string", "description": "Filter relationships by status: active, dormant, ended. Default is active."}
            }
        }
    },
    {
        "name": "find_actor_path",
        "description": "Find the shortest path of relationships connecting two actors.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source_actor_id": {"type": "string", "description": "The UUID of the source actor."},
                "target_actor_id": {"type": "string", "description": "The UUID of the target actor."},
                "relationship_status": {"type": "string", "description": "Filter relationships by status: active, dormant, ended. Default is active."}
            },
            "required": ["source_actor_id", "target_actor_id"]
        }
    },
    # Write
    {
        "name": "submit_source",
        "description": "Manually submit a source URL for parsing and text extraction.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL of the source document."},
                "title": {"type": "string", "description": "Optional title for the document."}
            },
            "required": ["url"]
        }
    },
    {
        "name": "add_analyst_note",
        "description": "Attach an evidence record (stance, excerpt, and optional analyst note) from a document to a claim.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "claim_id": {"type": "string", "description": "The claim UUID."},
                "document_id": {"type": "string", "description": "The UUID of the document the evidence excerpt comes from."},
                "stance": {"type": "string", "description": "Stance: supports, contradicts, partially_supports, contextualizes, repeats."},
                "excerpt": {"type": "string", "description": "Evidence text excerpt."},
                "analyst_note": {"type": "string", "description": "Optional free-text analyst commentary."}
            },
            "required": ["claim_id", "document_id", "stance", "excerpt"]
        }
    },
    {
        "name": "approve_event",
        "description": "Explicitly approve a candidate event (requires confirm).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "The UUID of the event."}
            },
            "required": ["event_id"]
        }
    },
    {
        "name": "reject_event",
        "description": "Explicitly reject a candidate event (requires confirm).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "The UUID of the event."}
            },
            "required": ["event_id"]
        }
    },
    {
        "name": "approve_report",
        "description": "Explicitly approve a generated report brief.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "report_id": {"type": "string", "description": "The UUID of the report."}
            },
            "required": ["report_id"]
        }
    },
    {
        "name": "create_monitor",
        "description": "Create a new alert monitor.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Descriptive name."},
                "monitor_type": {"type": "string", "description": "relationship_threshold, country_risk."},
                "condition_json": {"type": "object", "description": "JSON condition details."},
                "delivery_channel": {"type": "string", "description": "telegram or email. Default is telegram."}
            },
            "required": ["name", "monitor_type", "condition_json"]
        }
    },
    {
        "name": "update_monitor",
        "description": "Update an existing alert monitor.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "monitor_id": {"type": "string", "description": "The UUID of the monitor."},
                "enabled": {"type": "boolean", "description": "Enable or disable."}
            },
            "required": ["monitor_id"]
        }
    },
    {
        "name": "cancel_monitor",
        "description": "Delete an alert monitor.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "monitor_id": {"type": "string", "description": "The UUID of the monitor."}
            },
            "required": ["monitor_id"]
        }
    }
]


async def execute_tool(name: str, arguments: dict[str, Any]) -> Any:
    # Read Tools
    if name == "search_intelligence":
        return await call_api("POST", "/api/v1/intelligence/search", json_data={"query": arguments["query"], "limit": arguments.get("limit", 50)})
    elif name == "get_actor_profile":
        return await call_api("GET", f"/api/v1/actors/{arguments['actor_id']}")
    elif name == "get_country_profile":
        return await call_api("POST", "/api/v1/intelligence/country-brief", json_data={"country_actor_id": arguments["country_actor_id"], "as_of": arguments.get("as_of")})
    elif name == "get_event":
        return await call_api("GET", f"/api/v1/events/{arguments['event_id']}")
    elif name == "search_events":
        params = {}
        if "lifecycle_status" in arguments:
            params["lifecycle_status"] = arguments["lifecycle_status"]
        if "limit" in arguments:
            params["limit"] = arguments["limit"]
        return await call_api("GET", "/api/v1/events", params=params)
    elif name == "get_claim_evidence":
        return await call_api("GET", f"/api/v1/claims/{arguments['claim_id']}/evidence")
    elif name == "get_relationship":
        return await call_api("GET", f"/api/v1/relationships/{arguments['relationship_id']}")
    elif name == "compare_relationships":
        return await call_api(
            "POST",
            "/api/v1/intelligence/relationship-comparison",
            json_data={
                "relationship_ids": arguments["relationship_ids"],
                "as_of": arguments.get("as_of", datetime.now(UTC).isoformat()),
                "include_evidence": arguments.get("include_evidence", True),
            },
        )
    elif name in ("get_risk_scores", "explain_risk_change"):
        return await call_api(
            "POST",
            "/api/v1/intelligence/risk-explanation",
            json_data={
                "risk_definition_id": arguments["risk_definition_id"],
                "scope_type": arguments["scope_type"],
                "scope_id": arguments.get("scope_id"),
                "as_of": arguments.get("as_of"),
            },
        )
    elif name == "get_active_scenarios":
        params = {"status": "active"}
        if "scope_type" in arguments:
            params["scope_type"] = arguments["scope_type"]
        if "scope_id" in arguments:
            params["scope_id"] = arguments["scope_id"]
        return await call_api("GET", "/api/v1/scenarios", params=params)
    elif name == "get_latest_report":
        params = {"report_type": arguments["report_type"], "limit": 1}
        return await call_api("GET", "/api/v1/reports", params=params)
    elif name == "get_job_status":
        return await call_api("GET", f"/api/v1/investigations/{arguments['job_id']}")

    # Analytical Tools
    elif name == "start_event_investigation":
        return await call_api("POST", "/api/v1/intelligence/event-investigation", json_data={"event_id": arguments["event_id"], "priority": arguments.get("priority", "medium")})
    elif name == "compare_source_narratives":
        return await call_api("POST", "/api/v1/intelligence/search", json_data={"query": arguments["query"]})
    elif name == "generate_country_brief":
        return await call_api("POST", "/api/v1/intelligence/country-brief", json_data={"country_actor_id": arguments["country_actor_id"], "as_of": arguments.get("as_of")})
    elif name == "generate_conflict_brief":
        return await call_api(
            "POST",
            "/api/v1/intelligence/relationship-comparison",
            json_data={
                "relationship_ids": arguments["relationship_ids"],
                "as_of": arguments.get("as_of", datetime.now(UTC).isoformat()),
            },
        )
    elif name == "generate_daily_brief":
        return await call_api("POST", "/api/v1/intelligence/daily-brief", json_data={})
    elif name == "generate_weekly_outlook":
        return await call_api("POST", "/api/v1/reports/generate", json_data={"report_type": "weekly_outlook"})
    elif name == "simulate_scenario":
        return await call_api(
            "POST",
            "/api/v1/intelligence/scenario-simulation",
            json_data={
                "scope_type": arguments["scope_type"],
                "scope_id": arguments.get("scope_id"),
                "scenario_family": arguments["scenario_family"],
                "time_horizon": arguments["time_horizon"],
                "hypothetical_context": arguments["hypothetical_context"],
            },
        )

    elif name == "get_actor_centrality":
        params = {}
        if "relationship_status" in arguments:
            params["relationship_status"] = arguments["relationship_status"]
        return await call_api("GET", "/api/v1/graph/centrality", params=params)
    elif name == "find_actor_path":
        params = {
            "source_actor_id": arguments["source_actor_id"],
            "target_actor_id": arguments["target_actor_id"],
        }
        if "relationship_status" in arguments:
            params["relationship_status"] = arguments["relationship_status"]
        return await call_api("GET", "/api/v1/graph/path", params=params)

    # Controlled Write Tools
    elif name == "submit_source":
        return await call_api("POST", "/api/v1/sources/submit", json_data={"url": arguments["url"], "title": arguments.get("title")})
    elif name == "add_analyst_note":
        return await call_api(
            "POST",
            f"/api/v1/claims/{arguments['claim_id']}/evidence",
            json_data={
                "document_id": arguments["document_id"],
                "stance": arguments["stance"],
                "excerpt": arguments["excerpt"],
                "analyst_note": arguments.get("analyst_note"),
            },
        )
    elif name == "approve_event":
        return await call_api("POST", f"/api/v1/events/{arguments['event_id']}/approve")
    elif name == "reject_event":
        return await call_api("POST", f"/api/v1/events/{arguments['event_id']}/reject")
    elif name == "approve_report":
        return await call_api("POST", f"/api/v1/reports/{arguments['report_id']}/approve")
    elif name == "create_monitor":
        return await call_api(
            "POST",
            "/api/v1/monitors",
            json_data={
                "name": arguments["name"],
                "monitor_type": arguments["monitor_type"],
                "condition_json": arguments["condition_json"],
                "delivery_channel": arguments.get("delivery_channel", "telegram"),
            },
        )
    elif name == "update_monitor":
        return await call_api("PATCH", f"/api/v1/monitors/{arguments['monitor_id']}", json_data={"enabled": arguments["enabled"]})
    elif name == "cancel_monitor":
        return await call_api("DELETE", f"/api/v1/monitors/{arguments['monitor_id']}")

    else:
        return {"error": f"Tool {name} not found"}


def read_line() -> str:
    return sys.stdin.readline()


async def main_loop() -> None:
    loop = asyncio.get_running_loop()
    while True:
        line = await loop.run_in_executor(executor, read_line)
        if not line:
            break

        line = line.strip()
        if not line:
            continue

        try:
            req = json.loads(line)
        except Exception as exc:
            log(f"Invalid JSON received: {exc}")
            continue

        req_id = req.get("id")
        method = req.get("method")

        # Basic JSON-RPC routing
        if method in ("tools/list", "listTools"):
            resp = {
                "jsonrpc": "2.0",
                "result": {"tools": TOOLS},
                "id": req_id,
            }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        elif method in ("tools/call", "callTool"):
            params = req.get("params", {})
            name = params.get("name")
            arguments = params.get("arguments", {})

            try:
                res = await execute_tool(name, arguments)
                resp = {
                    "jsonrpc": "2.0",
                    "result": {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]},
                    "id": req_id,
                }
            except Exception as exc:
                resp = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": str(exc)},
                    "id": req_id,
                }

            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        elif method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "hermes-mcp", "version": "0.1.0"},
                },
                "id": req_id,
            }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        else:
            if req_id is not None:
                resp = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Method {method} not found"},
                    "id": req_id,
                }
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main_loop())
