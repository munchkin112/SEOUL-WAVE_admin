from uuid import UUID

from psycopg import Connection

FAILURE_SOURCES = ("LANGGRAPH", "LLM", "EXTERNAL_API", "DATABASE", "UNKNOWN")


def dashboard_summary(connection: Connection, days: int) -> dict:
    row = connection.execute(
        """
        SELECT count(*)::integer AS total,
               count(*) FILTER (WHERE status = 'SUCCESS')::integer AS success,
               count(*) FILTER (WHERE status = 'FAILED')::integer AS failed,
               count(*) FILTER (WHERE status <> 'RUNNING')::integer AS completed,
               coalesce(
                   round(avg(duration_ms) FILTER (WHERE status <> 'RUNNING'))::integer,
                   0
               ) AS avg_duration_ms
          FROM agent_runs
         WHERE started_at >= now() - (%s * interval '1 day')
        """,
        (days,),
    ).fetchone()
    recovered = connection.execute(
        """
        SELECT count(DISTINCT recovery.incident_id)::integer AS recovered
          FROM recovery_logs AS recovery
          JOIN agent_runs AS run USING (run_id)
         WHERE recovery.status = 'RECOVERED'
           AND run.started_at >= now() - (%s * interval '1 day')
        """,
        (days,),
    ).fetchone()["recovered"]
    source_rows = connection.execute(
        """
        SELECT incident.error_source, count(*)::integer AS count
          FROM incident_logs AS incident
          JOIN agent_runs AS run USING (run_id)
         WHERE run.started_at >= now() - (%s * interval '1 day')
         GROUP BY incident.error_source
        """,
        (days,),
    ).fetchall()
    failure_by_source = {source: 0 for source in FAILURE_SOURCES}
    failure_by_source.update(
        {item["error_source"]: item["count"] for item in source_rows}
    )
    completed = row["completed"]
    return {
        "total": row["total"],
        "success": row["success"],
        "failed": row["failed"],
        "recovered": recovered,
        "success_rate": round(100 * row["success"] / completed, 1)
        if completed
        else 0,
        "avg_duration_ms": row["avg_duration_ms"],
        "failure_by_source": failure_by_source,
        "mock": False,
    }


def dashboard_trends(connection: Connection, days: int) -> list[dict]:
    run_rows = connection.execute(
        """
        SELECT dates.day::date AS date,
               count(run.run_id) FILTER (WHERE run.status = 'SUCCESS')::integer
                   AS success,
               count(run.run_id) FILTER (WHERE run.status = 'FAILED')::integer
                   AS failed
          FROM generate_series(
                   (now() AT TIME ZONE 'Asia/Seoul')::date - (%s - 1),
                   (now() AT TIME ZONE 'Asia/Seoul')::date,
                   interval '1 day'
               ) AS dates(day)
          LEFT JOIN agent_runs AS run
            ON (run.started_at AT TIME ZONE 'Asia/Seoul')::date = dates.day::date
         GROUP BY dates.day
         ORDER BY dates.day
        """,
        (days,),
    ).fetchall()
    recovery_rows = connection.execute(
        """
        SELECT (recovery.finished_at AT TIME ZONE 'Asia/Seoul')::date AS date,
               count(DISTINCT recovery.incident_id)::integer AS recovered
          FROM recovery_logs AS recovery
         WHERE recovery.status = 'RECOVERED'
           AND recovery.finished_at >=
               ((now() AT TIME ZONE 'Asia/Seoul')::date - (%s - 1))
                   AT TIME ZONE 'Asia/Seoul'
         GROUP BY date
        """,
        (days,),
    ).fetchall()
    recoveries_by_date = {row["date"]: row["recovered"] for row in recovery_rows}
    return [
        {
            "date": row["date"],
            "success": row["success"],
            "failed": row["failed"],
            "recovered": recoveries_by_date.get(row["date"], 0),
        }
        for row in run_rows
    ]


def list_agent_runs(connection: Connection, limit: int) -> tuple[int, list[dict]]:
    total = connection.execute(
        "SELECT count(*)::integer AS total FROM agent_runs"
    ).fetchone()["total"]
    items = connection.execute(
        """
        SELECT run_id, status, duration_ms, started_at, finished_at,
               error_source, error_code, failed_step_name,
               NULL::text AS route, NULL::text AS companion_type
          FROM agent_runs
         ORDER BY started_at DESC, run_id DESC
         LIMIT %s
        """,
        (limit,),
    ).fetchall()
    return total, items


def get_agent_run(connection: Connection, run_id: UUID) -> dict | None:
    return connection.execute(
        """
        SELECT run_id, status, duration_ms, started_at, finished_at,
               error_source, error_code, failed_step_name,
               NULL::text AS route, NULL::text AS companion_type
          FROM agent_runs
         WHERE run_id = %s
        """,
        (run_id,),
    ).fetchone()


def list_agent_steps(connection: Connection, run_id: UUID) -> list[dict]:
    return connection.execute(
        """
        SELECT step_log_id, run_id, step_order, agent_name, step_name, status,
               started_at, finished_at, duration_ms, error_source, error_code
          FROM agent_step_logs
         WHERE run_id = %s
         ORDER BY step_order, started_at, step_log_id
        """,
        (run_id,),
    ).fetchall()


def list_handoffs(connection: Connection, run_id: UUID) -> list[dict]:
    return connection.execute(
        """
        SELECT handoff_id, run_id, from_agent, to_agent, status, started_at,
               finished_at, duration_ms, error_source, error_code
          FROM handoff_logs
         WHERE run_id = %s
         ORDER BY started_at, handoff_id
        """,
        (run_id,),
    ).fetchall()


def list_api_calls(connection: Connection, limit: int) -> tuple[int, list[dict], list[dict]]:
    total = connection.execute(
        "SELECT count(*)::integer AS total FROM api_call_logs"
    ).fetchone()["total"]
    items = connection.execute(
        """
        SELECT api_call_id, run_id, provider, api_type, http_status, success,
               latency_ms, called_at, error_source, error_code
          FROM api_call_logs
         ORDER BY called_at DESC, api_call_id DESC
         LIMIT %s
        """,
        (limit,),
    ).fetchall()
    stats = connection.execute(
        """
        SELECT provider,
               count(*)::integer AS total,
               count(*) FILTER (WHERE success)::integer AS success,
               count(*) FILTER (WHERE NOT success)::integer AS failed,
               coalesce(round(avg(latency_ms))::integer, 0) AS avg_latency_ms
          FROM api_call_logs
         GROUP BY provider
         ORDER BY provider
        """
    ).fetchall()
    return total, items, stats


def list_incidents(connection: Connection, limit: int) -> tuple[int, list[dict]]:
    total = connection.execute(
        "SELECT count(*)::integer AS total FROM incident_logs"
    ).fetchone()["total"]
    items = connection.execute(
        """
        SELECT incident_id, run_id, api_call_id, status, severity, error_source,
               error_code, error_message, failed_step_name, occurred_at, resolved_at
          FROM incident_logs
         ORDER BY occurred_at DESC, incident_id DESC
         LIMIT %s
        """,
        (limit,),
    ).fetchall()
    incident_ids = [item["incident_id"] for item in items]
    recoveries = connection.execute(
        """
        SELECT recovery_id, incident_id, run_id, attempt_number, recovery_action,
               status, started_at, finished_at, duration_ms
          FROM recovery_logs
         WHERE incident_id = ANY(%s)
         ORDER BY incident_id, attempt_number
        """,
        (incident_ids,),
    ).fetchall() if incident_ids else []
    recoveries_by_incident: dict[UUID, list[dict]] = {
        incident_id: [] for incident_id in incident_ids
    }
    for recovery in recoveries:
        recoveries_by_incident[recovery["incident_id"]].append(recovery)
    for incident in items:
        incident["recoveries"] = recoveries_by_incident[incident["incident_id"]]
    return total, items
