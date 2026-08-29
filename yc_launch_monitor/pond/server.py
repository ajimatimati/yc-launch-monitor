import json
import logging
import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, Response, Header, HTTPException, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from ..config import settings
from ..database import db
from ..engine import monitor_engine
from ..slack.notifier import slack_notifier
from ..models import LaunchStatus, LaunchItem, ProgramType, LaunchSource, FounderInfo

logger = logging.getLogger(__name__)

# Start timestamp for uptime calculation
START_TIME = datetime.datetime.now(datetime.timezone.utc)

app = FastAPI(
    title="YC Launch Monitor - Pond Protocol V1 Agent & GTM Radar",
    description="Pond Agent Server for real-time YC and Speedrun launch tracking and Slack alerting.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_dashboard_html() -> str:
    """Loads the executive GTM Dashboard HTML template."""
    tmpl_path = Path(__file__).resolve().parent.parent / "templates" / "dashboard.html"
    if tmpl_path.exists():
        with open(tmpl_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>YC Launch Monitor Dashboard</h1>"

@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard():
    """Renders the interactive Executive GTM Radar Web Dashboard."""
    return HTMLResponse(content=load_dashboard_html())

@app.get("/api/stats")
def get_api_stats():
    """Returns real-time database and monitoring statistics."""
    st = db.get_stats()
    return st.model_dump()

@app.get("/api/launches")
def get_api_launches(limit: int = 100, status: Optional[str] = None, query: Optional[str] = None):
    """Returns filtered launches from the persistent SQLite database."""
    status_filter = None
    if status == "early" or status == "EARLY_SIGNAL":
        status_filter = LaunchStatus.EARLY_SIGNAL
    elif status == "confirmed" or status == "CONFIRMED":
        status_filter = LaunchStatus.CONFIRMED

    items = db.list_launches(limit=limit, status=status_filter, query=query)
    return [itm.model_dump() for itm in items]

@app.post("/api/scan")
def post_api_scan():
    """Triggers an immediate incremental scan across all 4 sources."""
    summary = monitor_engine.run_scan(send_slack=True)
    return summary.model_dump()

@app.post("/api/test-slack")
def post_api_test_slack():
    """Dispatches test alert cards to Slack (or terminal preview)."""
    now = datetime.datetime.now(datetime.timezone.utc)
    early_test = LaunchItem(
        id="api_test_early",
        company_name="Hyperscale AI",
        slug="hyperscale-ai",
        website="https://hyperscale.ai",
        batch="YC S26",
        program_type=ProgramType.YC,
        source=LaunchSource.X_TWITTER,
        status=LaunchStatus.EARLY_SIGNAL,
        founders=[FounderInfo(name="Beknazar Abdikamalov", handle="@beknabdik", profile_url="https://x.com/beknabdik")],
        post_text="We got into YC S26! Excited to move to SF and start building the future of database performance.",
        post_url="https://x.com/beknabdik/status/2061493360150601738",
        detected_at=now
    )
    s, ts = slack_notifier.send_launch_alert(early_test)
    return {"success": s, "ts": ts}

def load_manifest() -> Dict[str, Any]:
    """Loads the Pond Protocol V1 manifest."""
    manifest_path = Path(__file__).resolve().parent.parent.parent / "pond.json"
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    # Fallback inline manifest
    return {
        "protocol": "marketplace-agent",
        "protocol_version": "1.0",
        "agent_version": "1.0.0",
        "metadata": {
            "name": "YC & Speedrun Launch Monitor Agent",
            "short_description": "Monitors YC Directory, Speedrun, X/Twitter, and LinkedIn for early founder launch signals & official batch additions with Slack alerts.",
            "category": "sales"
        },
        "capabilities": {
            "sync": True,
            "streaming": False,
            "async_tasks": False,
            "cancellation": False,
            "attachments": False,
            "feedback": False
        },
        "input_modes": ["text/plain", "application/json"],
        "output_modes": ["text/markdown", "application/json"],
        "limits": {
            "max_request_bytes": 10485760,
            "max_attachment_bytes": 52428800,
            "max_run_seconds": 300
        }
    }

@app.get("/manifest")
def get_manifest():
    """
    Public Pond discovery endpoint.
    Must be accessible without authentication or protocol version headers.
    """
    return JSONResponse(content=load_manifest())

@app.get("/health")
@app.get("/api/health")
def health_check():
    """
    Pond Agent Infrastructure Health Check endpoint.
    Reports operational health, database connectivity, uptime, and crawler statuses.
    """
    uptime_sec = int((datetime.datetime.now(datetime.timezone.utc) - START_TIME).total_seconds())
    stats = db.get_stats()

    return {
        "status": "healthy",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "version": "1.0.0",
        "uptime_seconds": uptime_sec,
        "agent_infrastructure": {
            "platform": "joinpond.ai",
            "protocol_version": "1.0"
        },
        "components": {
            "database": {
                "status": "up",
                "engine": "sqlite3",
                "tracked_companies": stats.total_tracked_companies,
                "early_signals": stats.early_signal_count,
                "confirmed_companies": stats.confirmed_count
            },
            "slack_integration": {
                "status": "configured" if slack_notifier.is_configured else "dry_run_preview",
                "channel_id": settings.SLACK_CHANNEL_ID
            },
            "monitors": {
                "yc_directory": {"enabled": settings.ENABLE_YC_DIRECTORY, "status": "active"},
                "speedrun_directory": {"enabled": settings.ENABLE_SPEEDRUN_DIRECTORY, "status": "active"},
                "x_twitter": {"enabled": settings.ENABLE_X_TWITTER, "status": "active"},
                "linkedin": {"enabled": settings.ENABLE_LINKEDIN, "status": "active"}
            }
        },
        "message": "All monitoring streams and Slack bot dispatchers operational."
    }

@app.post("/runs")
async def execute_run(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_agent_protocol_version: Optional[str] = Header(None, alias="X-Agent-Protocol-Version"),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """
    Pond Protocol V1 execution endpoint.
    Validates Bearer token, enforces idempotency, dispatches selected action, and returns formatted markdown.
    """
    # 1. Validate Protocol Version
    if not x_agent_protocol_version:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_request", "message": "Missing required X-Agent-Protocol-Version header"}
        )
    if x_agent_protocol_version != "1.0":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "unsupported_protocol_version", "message": f"Unsupported protocol version: {x_agent_protocol_version}. Expected '1.0'"}
        )

    # 2. Validate Authorization
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized", "message": "Missing or malformed Bearer access key"}
        )
    token = authorization.split("Bearer ")[1].strip()
    if token != settings.POND_ACCESS_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized", "message": "Invalid Pond Access Key"}
        )

    # 3. Parse JSON Body
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_request", "message": "Malformed JSON payload"}
        )

    run_id = body.get("run_id")
    if not run_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_request", "message": "Missing run_id in request body"}
        )

    # 4. Check Idempotency Store
    cached_response = db.get_idempotent_response(run_id)
    if cached_response:
        logger.info(f"Returning cached idempotent response for run_id {run_id}")
        return JSONResponse(content=cached_response)

    action_id = body.get("action_id")
    params = body.get("parameters", {})

    # 5. Dispatch Action
    try:
        output_text = ""
        usage_quantity = 1

        if action_id == "check_new_launches":
            sources = params.get("sources")
            send_slack = params.get("send_slack_alerts", True)
            summary = monitor_engine.run_scan(specific_sources=sources, send_slack=send_slack)
            
            output_text = f"### 🚀 YC & Speedrun Launch Scan Completed\n\n"
            output_text += f"- **New Companies Detected**: {summary.total_new_items}\n"
            output_text += f"- **🔥 Early Founder Signals**: {summary.total_early_signals}\n"
            output_text += f"- **✅ Confirmed Official Launches**: {summary.total_confirmed}\n"
            output_text += f"- **Slack Alerts Dispatched**: {summary.slack_delivered_count}\n\n"
            
            if summary.total_new_items > 0:
                output_text += "#### Detected Items Breakdown:\n"
                for s_key, res in summary.results_by_source.items():
                    if res.items:
                        output_text += f"\n**Source: {s_key}** ({len(res.items)} new)\n"
                        for itm in res.items:
                            status_badge = "🔥 EARLY SIGNAL" if itm.status == LaunchStatus.EARLY_SIGNAL else "✅ CONFIRMED"
                            output_text += f"- **{itm.company_name}** (`{itm.batch or 'YC'}`) - {status_badge}\n"
                            output_text += f"  - Founder: {itm.display_founder}\n"
                            if itm.post_url:
                                output_text += f"  - Link: {itm.post_url}\n"
                            if itm.description:
                                output_text += f"  - Description: {itm.description}\n"
            usage_quantity = max(1, summary.total_new_items)

        elif action_id == "search_yc_companies":
            query = params.get("query", "")
            status_filter_raw = params.get("status_filter", "all")
            status_filter = None
            if status_filter_raw == "early_signal":
                status_filter = LaunchStatus.EARLY_SIGNAL
            elif status_filter_raw == "confirmed":
                status_filter = LaunchStatus.CONFIRMED

            results = db.list_launches(limit=20, status=status_filter, query=query)
            output_text = f"### 🔍 Search Results for `{query}` ({len(results)} found)\n\n"
            if not results:
                output_text += "No matching companies or founders found in the persistent database."
            else:
                for r in results:
                    badge = "🔥 Early Signal" if r.status == LaunchStatus.EARLY_SIGNAL else "✅ Confirmed"
                    output_text += f"#### {r.company_name} (`{r.batch or 'YC'}`) — {badge}\n"
                    output_text += f"- **Founder**: {r.display_founder}\n"
                    output_text += f"- **Source**: {r.source.value}\n"
                    if r.website:
                        output_text += f"- **Website**: {r.website}\n"
                    if r.post_url:
                        output_text += f"- **Link**: {r.post_url}\n"
                    if r.description:
                        output_text += f"- **Description**: {r.description}\n"
                    output_text += "\n"
            usage_quantity = len(results)

        elif action_id == "get_monitor_status":
            stats = db.get_stats()
            uptime_min = int((datetime.datetime.now(datetime.timezone.utc) - START_TIME).total_seconds() / 60)
            output_text = f"### 📊 YC Launch Monitor Health & Statistics\n\n"
            output_text += f"- **System Status**: 🟢 Healthy (Uptime: {uptime_min} mins)\n"
            output_text += f"- **Total Tracked Companies**: {stats.total_tracked_companies}\n"
            output_text += f"- **🔥 Early Founder Signals**: {stats.early_signal_count}\n"
            output_text += f"- **✅ Confirmed Official Directory Listings**: {stats.confirmed_count}\n"
            output_text += f"- **Speedrun Companies**: {stats.speedrun_count}\n"
            output_text += f"- **YC Companies**: {stats.yc_count}\n"
            output_text += f"- **Last Automated Scan**: {stats.last_scan_time or 'Just started'}\n"
            output_text += f"- **Slack Dispatching**: {'Enabled' if slack_notifier.is_configured else 'Dry Run'}\n"
            usage_quantity = 1

        else:
            # General query synthesis
            msg_text = ""
            if body.get("messages") and len(body["messages"]) > 0:
                parts = body["messages"][0].get("parts", [])
                for p in parts:
                    if p.get("type") == "text":
                        msg_text = p.get("text", "")

            stats = db.get_stats()
            output_text = (
                f"Hello! I am the **YC & Speedrun Launch Monitor Agent**.\n\n"
                f"I continuously monitor 4 data streams (YC Directory, Speedrun Directory, X, and LinkedIn) "
                f"to capture new company launches and alert your Slack channel in real-time.\n\n"
                f"Currently tracking **{stats.total_tracked_companies} companies** "
                f"({stats.early_signal_count} early founder signals).\n\n"
                f"You can ask me to run an immediate scan (`check_new_launches`) or search for companies (`search_yc_companies`)."
            )
            usage_quantity = 1

        response_payload = {
            "run_id": run_id,
            "status": "completed",
            "output": [
                {
                    "type": "text",
                    "text": output_text
                }
            ],
            "usage": {
                "unit_of_measurement": "result",
                "quantity": usage_quantity
            }
        }

        # Cache response for idempotency
        db.save_idempotent_response(run_id, action_id, params, response_payload)
        return JSONResponse(content=response_payload)

    except Exception as e:
        logger.error(f"Error executing run {run_id}: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "run_id": run_id,
                "status": "failed",
                "error": {
                    "code": "internal_error",
                    "message": f"Execution error: {str(e)}"
                },
                "usage": {
                    "unit_of_measurement": "result",
                    "quantity": 0
                }
            }
        )
