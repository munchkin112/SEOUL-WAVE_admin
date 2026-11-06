"""Bounded, read-only probes for configured external APIs."""
from __future__ import annotations

import json
import os
import time
from http.client import HTTPException as HttpProtocolError
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


OPENAI_API_BASE_URL = "https://api.openai.com/v1"
SEOUL_CULTURE_API_BASE_URL = "http://openapi.seoul.go.kr:8088"
SEOUL_CULTURE_SERVICE_NAME = "aiViewCulture"
PROBE_TIMEOUT_SECONDS = 4
DEFAULT_LANGGRAPH_HEALTH_URL = "http://itinerary-worker:8090/health"


def _result(
    name: str,
    status: str,
    reason_code: str,
    description: str,
    started_at: float,
) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "reason_code": reason_code,
        "description": description,
        "latency_ms": round((time.monotonic() - started_at) * 1000),
    }


def _http_error_status(status_code: int) -> tuple[str, str, str]:
    if status_code == 429:
        return "DEGRADED", "RATE_LIMITED", "API에 연결됐지만 요청 제한 응답을 받았습니다."
    if status_code in (401, 403):
        return "DOWN", "AUTHENTICATION_FAILED", "인증 또는 API 접근 권한을 확인할 수 없습니다."
    if status_code == 404:
        return "DOWN", "RESOURCE_NOT_FOUND", "설정한 모델 또는 API 경로를 찾을 수 없습니다."
    if 500 <= status_code <= 599:
        return "DOWN", "PROVIDER_ERROR", "외부 API가 서버 오류를 반환했습니다."
    return "DOWN", "HTTP_ERROR", "외부 API가 정상 응답을 반환하지 않았습니다."


def _network_failure(name: str, started_at: float) -> dict[str, Any]:
    return _result(
        name,
        "DOWN",
        "NETWORK_OR_TIMEOUT",
        "외부 API 연결에 실패했거나 제한 시간 안에 응답하지 않았습니다.",
        started_at,
    )


def _invalid_response(name: str, started_at: float) -> dict[str, Any]:
    return _result(
        name,
        "DOWN",
        "INVALID_RESPONSE",
        "외부 API 응답 형식을 확인할 수 없습니다.",
        started_at,
    )


def check_openai_model() -> dict[str, Any]:
    """Check key/model metadata access without making a model completion."""
    started_at = time.monotonic()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "").strip()
    if not api_key or not model:
        return _result(
            "LLM API",
            "NOT_CONFIGURED",
            "MISSING_CONFIGURATION",
            "OPENAI_API_KEY와 OPENAI_MODEL 설정이 필요합니다.",
            started_at,
        )

    request = Request(
        f"{OPENAI_API_BASE_URL}/models/{quote(model, safe='')}",
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=PROBE_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read())
        if not isinstance(payload, dict) or payload.get("id") != model:
            return _result(
                "LLM API", "DOWN", "MODEL_MISMATCH",
                "API 응답에서 설정한 모델을 확인할 수 없습니다.", started_at,
            )
        return _result(
            "LLM API", "UP", "MODEL_ACCESSIBLE",
            "인증 및 설정 모델 조회가 정상입니다. 추천 생성 요청 자체는 점검하지 않았습니다.",
            started_at,
        )
    except HTTPError as error:
        status, reason_code, description = _http_error_status(error.code)
        return _result("LLM API", status, reason_code, description, started_at)
    except (TimeoutError, URLError, OSError):
        return _network_failure("LLM API", started_at)
    except (json.JSONDecodeError, UnicodeDecodeError, HttpProtocolError):
        return _invalid_response("LLM API", started_at)
    except Exception:
        return _result(
            "LLM API", "UNKNOWN", "CHECK_FAILED",
            "상태 확인 중 예기치 않은 오류가 발생했습니다.", started_at,
        )


def _culture_result_code(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    service_payload = payload.get(SEOUL_CULTURE_SERVICE_NAME)
    if not isinstance(service_payload, dict):
        return None
    result = service_payload.get("RESULT")
    if not isinstance(result, dict):
        return None
    code = result.get("CODE")
    return code if isinstance(code, str) else None


def check_seoul_culture_api() -> dict[str, Any]:
    """Fetch one aiViewCulture row; a valid INFO-200 empty response is healthy."""
    started_at = time.monotonic()
    api_key = os.getenv("SEOUL_CULTURE_API_KEY", "").strip()
    if not api_key:
        return _result(
            "Seoul Cultural Events",
            "NOT_CONFIGURED",
            "MISSING_CONFIGURATION",
            "SEOUL_CULTURE_API_KEY 설정이 필요합니다.",
            started_at,
        )

    encoded_key = quote(api_key, safe="")
    url = (
        f"{SEOUL_CULTURE_API_BASE_URL}/{encoded_key}/json/"
        f"{SEOUL_CULTURE_SERVICE_NAME}/1/1"
    )
    request = Request(url, headers={"Accept": "application/json"}, method="GET")
    try:
        with urlopen(request, timeout=PROBE_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read())
        result_code = _culture_result_code(payload)
        if result_code == "INFO-000":
            return _result(
                "Seoul Cultural Events", "UP", "SERVICE_RESPONDING",
                "aiViewCulture API가 정상 응답했습니다.", started_at,
            )
        if result_code == "INFO-200":
            return _result(
                "Seoul Cultural Events", "UP", "SERVICE_RESPONDING_EMPTY",
                "API가 정상 응답했습니다. 확인 범위의 행사 데이터는 비어 있습니다.", started_at,
            )
        if result_code is not None:
            # Provider RESULT.MESSAGE may contain request details; never return it.
            return _result(
                "Seoul Cultural Events", "DOWN", "SERVICE_REJECTED_REQUEST",
                "aiViewCulture API가 요청을 정상 처리하지 않았습니다.", started_at,
            )
        return _invalid_response("Seoul Cultural Events", started_at)
    except HTTPError as error:
        status, reason_code, description = _http_error_status(error.code)
        return _result("Seoul Cultural Events", status, reason_code, description, started_at)
    except (TimeoutError, URLError, OSError):
        return _network_failure("Seoul Cultural Events", started_at)
    except (json.JSONDecodeError, UnicodeDecodeError, HttpProtocolError):
        return _invalid_response("Seoul Cultural Events", started_at)
    except Exception:
        return _result(
            "Seoul Cultural Events", "UNKNOWN", "CHECK_FAILED",
            "상태 확인 중 예기치 않은 오류가 발생했습니다.", started_at,
        )


def _langgraph_status_from_payload(payload: Any, started_at: float) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return _invalid_response("LangGraph", started_at)
    checks = payload.get("checks")
    graph_status = checks.get("langgraph") if isinstance(checks, dict) else None
    if payload.get("status") == "ready" and graph_status == "ok":
        return _result(
            "LangGraph", "UP", "GRAPH_COMPILED_AND_WORKER_ALIVE",
            "워커가 실행 중이며 LangGraph 그래프 구조를 컴파일했습니다.", started_at,
        )
    if graph_status == "failed":
        return _result(
            "LangGraph", "DOWN", "GRAPH_COMPILE_FAILED",
            "워커에서 LangGraph 그래프 준비 확인에 실패했습니다.", started_at,
        )
    return _result(
        "LangGraph", "UNKNOWN", "INVALID_READINESS_STATUS",
        "워커가 인식 가능한 그래프 준비 상태를 반환하지 않았습니다.", started_at,
    )


def check_langgraph_worker() -> dict[str, Any]:
    """Check worker liveness and compiled graph topology over the compose network."""
    started_at = time.monotonic()
    health_url = os.getenv("LANGGRAPH_HEALTH_URL", DEFAULT_LANGGRAPH_HEALTH_URL).strip()
    if not health_url:
        return _result(
            "LangGraph", "NOT_CONFIGURED", "MISSING_CONFIGURATION",
            "LANGGRAPH_HEALTH_URL 설정이 필요합니다.", started_at,
        )
    request = Request(health_url, headers={"Accept": "application/json"}, method="GET")
    try:
        with urlopen(request, timeout=PROBE_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read(16_384))
        return _langgraph_status_from_payload(payload, started_at)
    except HTTPError as error:
        try:
            payload = json.loads(error.read(16_384))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return _result(
                "LangGraph", "DOWN", "WORKER_HTTP_ERROR",
                "LangGraph 워커가 정상 상태를 반환하지 않았습니다.", started_at,
            )
        return _langgraph_status_from_payload(payload, started_at)
    except (TimeoutError, URLError, OSError):
        return _result(
            "LangGraph", "DOWN", "WORKER_UNREACHABLE",
            "LangGraph 워커에 연결할 수 없거나 제한 시간 안에 응답하지 않았습니다.", started_at,
        )
    except (json.JSONDecodeError, UnicodeDecodeError, HttpProtocolError):
        return _invalid_response("LangGraph", started_at)
    except Exception:
        return _result(
            "LangGraph", "UNKNOWN", "CHECK_FAILED",
            "LangGraph 상태 확인 중 예기치 않은 오류가 발생했습니다.", started_at,
        )
