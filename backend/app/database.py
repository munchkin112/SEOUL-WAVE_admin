import logging
import os
from collections.abc import Iterator

import psycopg
from fastapi import HTTPException
from psycopg import Connection
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)

REQUIRED_TABLES = (
    "agent_runs",
    "agent_step_logs",
    "api_call_logs",
    "handoff_logs",
    "incident_logs",
    "recovery_logs",
    "run_component_logs",
)
REQUIRED_COLUMNS = (
    ("incident_logs", "monitor_event_id"),
    ("itinerary_executions", "next_retry_at"),
)
REQUIRED_NULLABLE_COLUMNS = (
    ("incident_logs", "run_id"),
    ("recovery_logs", "run_id"),
)


def connect_database() -> Connection:
    names = (
        "DATABASE_HOST",
        "DATABASE_PORT",
        "DATABASE_NAME",
        "DATABASE_USER",
        "DATABASE_PASSWORD",
    )
    config = {name: os.getenv(name) for name in names}
    config["DATABASE_SSLMODE"] = os.getenv("DATABASE_SSLMODE", "prefer")
    missing = [name for name, value in config.items() if not value]
    if missing:
        raise HTTPException(
            status_code=503,
            detail=f"Database configuration is missing: {', '.join(missing)}",
        )

    try:
        return psycopg.connect(
            host=config["DATABASE_HOST"],
            port=config["DATABASE_PORT"],
            dbname=config["DATABASE_NAME"],
            user=config["DATABASE_USER"],
            password=config["DATABASE_PASSWORD"],
            sslmode=config["DATABASE_SSLMODE"],
            connect_timeout=3,
            autocommit=True,
            options="-c default_transaction_read_only=on",
            row_factory=dict_row,
        )
    except psycopg.OperationalError as error:
        logger.error("PostgreSQL connection failed (%s)", type(error).__name__)
        raise HTTPException(
            status_code=503,
            detail="PostgreSQL is unavailable",
        ) from error


def check_log_schema(connection: Connection) -> list[str]:
    rows = connection.execute(
        """
        SELECT table_name
          FROM information_schema.tables
         WHERE table_schema = 'public'
           AND table_name = ANY(%s)
        """,
        (list(REQUIRED_TABLES),),
    ).fetchall()
    existing = {row["table_name"] for row in rows}
    missing = [table for table in REQUIRED_TABLES if table not in existing]
    if missing:
        return missing
    column_rows = connection.execute(
        """
        SELECT table_name, column_name, is_nullable
          FROM information_schema.columns
         WHERE table_schema = 'public'
           AND (table_name, column_name) IN (
               ('incident_logs', 'monitor_event_id'),
               ('itinerary_executions', 'next_retry_at'),
               ('incident_logs', 'run_id'),
               ('recovery_logs', 'run_id')
           )
        """
    ).fetchall()
    existing_columns = {
        (row["table_name"], row["column_name"]) for row in column_rows
    }
    missing.extend(
        f"{table}.{column}"
        for table, column in REQUIRED_COLUMNS
        if (table, column) not in existing_columns
    )
    nullable_columns = {
        (row["table_name"], row["column_name"])
        for row in column_rows
        if row["is_nullable"] == "YES"
    }
    missing.extend(
        f"{table}.{column} must allow NULL"
        for table, column in REQUIRED_NULLABLE_COLUMNS
        if (table, column) not in nullable_columns
    )
    return missing


def get_database() -> Iterator[Connection]:
    connection = connect_database()
    try:
        missing = check_log_schema(connection)
        if missing:
            raise HTTPException(
                status_code=503,
                detail=f"Operational log schema is missing objects: {', '.join(missing)}",
            )
        yield connection
    finally:
        connection.close()
