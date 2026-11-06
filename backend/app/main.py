import hmac
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from psycopg import Connection

from . import repository
from .database import check_log_schema, connect_database, get_database
from .health_checks import (
    check_langgraph_worker,
    check_openai_model,
    check_seoul_culture_api,
)

app = FastAPI(title="Seoul Wave Admin API", version="2.0.0")
origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def admin_auth(x_admin_key: str | None = Header(default=None)) -> None:
    expected_key = os.getenv("ADMIN_API_KEY")
    if not expected_key:
        raise HTTPException(
            status_code=503,
            detail="Admin API authentication is not configured",
        )
    if not x_admin_key or not hmac.compare_digest(x_admin_key, expected_key):
        raise HTTPException(status_code=401, detail="Invalid admin key")


AUTH = [Depends(admin_auth)]
Database = Annotated[Connection, Depends(get_database)]


@app.get("/api/v1/admin/dashboard/summary", dependencies=AUTH)
def get_summary(
    connection: Database,
    days: int = Query(7, ge=1, le=30),
) -> dict:
    return repository.dashboard_summary(connection, days)


@app.get("/api/v1/admin/dashboard/trends", dependencies=AUTH)
def get_trends(
    connection: Database,
    days: int = Query(7, ge=1, le=30),
) -> dict:
    return {"items": repository.dashboard_trends(connection, days), "mock": False}


@app.get("/api/v1/admin/agent-runs", dependencies=AUTH)
def get_runs(
    connection: Database,
    limit: int = Query(100, ge=1, le=500),
) -> dict:
    total, items = repository.list_agent_runs(connection, limit)
    return {"items": items, "total": total, "mock": False}


@app.get("/api/v1/admin/agent-runs/{run_id}", dependencies=AUTH)
def get_run(run_id: UUID, connection: Database) -> dict:
    run = repository.get_agent_run(connection, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "run": run,
        "steps": repository.list_agent_steps(connection, run_id),
        "handoffs": repository.list_handoffs(connection, run_id),
        "components": repository.list_run_component_logs(connection, run_id),
        "api_calls": repository.list_run_api_calls(connection, run_id),
        "mock": False,
    }


@app.get("/api/v1/admin/api-calls", dependencies=AUTH)
def get_api_calls(
    connection: Database,
    limit: int = Query(500, ge=1, le=1000),
) -> dict:
    total, items, stats = repository.list_api_calls(connection, limit)
    return {"items": items, "total": total, "stats": stats, "mock": False}


@app.get("/api/v1/admin/incidents", dependencies=AUTH)
def get_incidents(
    connection: Database,
    limit: int = Query(500, ge=1, le=1000),
) -> dict:
    total, items = repository.list_incidents(connection, limit)
    return {"items": items, "total": total, "mock": False}


@app.get("/api/v1/admin/health", dependencies=AUTH)
def get_health() -> dict:
    checked_at = datetime.now(timezone.utc).isoformat()
    try:
        connection = connect_database()
    except HTTPException as error:
        status = "NOT_CONNECTED"
        description = str(error.detail)
        schema_status = "NOT_CHECKED"
        schema_description = None
    else:
        try:
            missing = check_log_schema(connection)
            status = "UP"
            description = "Read-only connection to the service database"
            schema_status = "NOT_CONFIGURED" if missing else "UP"
            schema_description = (
                f"Missing schema objects: {', '.join(missing)}" if missing else None
            )
        finally:
            connection.close()

    # Keep independent external probes concurrent so total wait is bounded by
    # one probe timeout, rather than adding both timeouts together.
    with ThreadPoolExecutor(max_workers=3) as executor:
        langgraph_future = executor.submit(check_langgraph_worker)
        llm_future = executor.submit(check_openai_model)
        culture_future = executor.submit(check_seoul_culture_api)
        langgraph_status = langgraph_future.result()
        llm_status = llm_future.result()
        culture_status = culture_future.result()

    checked_at = datetime.now(timezone.utc).isoformat()

    return {
        "mode": "POSTGRES",
        "checked_at": checked_at,
        "services": [
            {"name": "PostgreSQL", "status": status, "description": description},
            {
                "name": "Operational log schema",
                "status": schema_status,
                "description": schema_description,
            },
            {
                "name": "LangGraph",
                **langgraph_status,
            },
            {
                "name": "LLM API",
                **llm_status,
            },
            {
                "name": "Seoul Cultural Events",
                **culture_status,
            },
        ],
    }
