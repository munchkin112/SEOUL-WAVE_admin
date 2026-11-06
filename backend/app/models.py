"""UUID-based demo repository. Replace with PostgreSQL repository when DATABASE_URL is configured."""
from datetime import datetime, timedelta, timezone
from uuid import uuid5, NAMESPACE_DNS
KST = timezone(timedelta(hours=9))
NOW = datetime.now(KST)
def uid(kind, n): return str(uuid5(NAMESPACE_DNS, f"hanriver-{kind}-{n}"))
def ts(minutes=0): return (NOW-timedelta(minutes=minutes)).isoformat()
RUNS = [
 {"run_id":uid('run',0),"status":"SUCCESS","started_at":ts(10),"finished_at":ts(9),"duration_ms":4100,"route":"망원 → 여의도","companion_type":"FAMILY","error_source":None,"error_code":None,"failed_step_name":None},
 {"run_id":uid('run',1),"status":"SUCCESS","started_at":ts(60),"finished_at":ts(59),"duration_ms":3800,"route":"여의도 → 잠실","companion_type":"FRIENDS","error_source":None,"error_code":None,"failed_step_name":None},
 {"run_id":uid('run',2),"status":"FAILED","started_at":ts(120),"finished_at":ts(119),"duration_ms":9700,"route":"망원 → 여의도","companion_type":"SOLO","error_source":"LANGGRAPH","error_code":"NODE_EXECUTION_ERROR","failed_step_name":"코스 검증"},
 {"run_id":uid('run',3),"status":"SUCCESS","started_at":ts(1440),"finished_at":ts(1439),"duration_ms":12300,"route":"잠실 → 망원","companion_type":"COUPLE","error_source":None,"error_code":None,"failed_step_name":None},
]
STEPS=[]; HANDOFFS=[]
for ri,run in enumerate(RUNS):
 for si,(agent,name,duration) in enumerate([('ConditionAgent','조건 분석',400),('DataAgent','DB·문화행사 API 조회',1200),('RecommendationAgent','코스 생성',1800),('CriticAgent','코스 검증',600)]):
  fail=ri==2 and si==3
  STEPS.append({"step_log_id":uid('step',ri*4+si),"run_id":run['run_id'],"step_order":si+1,"agent_name":agent,"step_name":name,"status":"FAILED" if fail else "SUCCESS","started_at":run['started_at'],"finished_at":run['finished_at'],"duration_ms":duration,"error_source":"LANGGRAPH" if fail else None,"error_code":"NODE_EXECUTION_ERROR" if fail else None})
  if si<3:
   HANDOFFS.append({"handoff_id":uid('handoff',ri*3+si),"run_id":run['run_id'],"from_agent":agent,"to_agent":['DataAgent','RecommendationAgent','CriticAgent'][si],"status":"SUCCESS","started_at":run['started_at'],"finished_at":run['finished_at'],"duration_ms":25,"error_source":None,"error_code":None})
CALLS=[
 {"api_call_id":uid('api',0),"run_id":RUNS[0]['run_id'],"provider":"Seoul Cultural Events","api_type":"CULTURE","http_status":200,"success":True,"latency_ms":320,"called_at":ts(9),"error_source":None,"error_code":None},
 {"api_call_id":uid('api',1),"run_id":RUNS[1]['run_id'],"provider":"OpenAI LLM","api_type":"LLM","http_status":200,"success":True,"latency_ms":1820,"called_at":ts(59),"error_source":None,"error_code":None},
 {"api_call_id":uid('api',2),"run_id":RUNS[2]['run_id'],"provider":"Seoul Cultural Events","api_type":"CULTURE","http_status":200,"success":True,"latency_ms":310,"called_at":ts(119),"error_source":None,"error_code":None},
 {"api_call_id":uid('api',3),"run_id":RUNS[3]['run_id'],"provider":"OpenAI LLM","api_type":"LLM","http_status":429,"success":False,"latency_ms":960,"called_at":ts(1439),"error_source":"LLM","error_code":"LLM_RATE_LIMIT"},
 {"api_call_id":uid('api',4),"run_id":RUNS[3]['run_id'],"provider":"OpenAI LLM","api_type":"LLM","http_status":200,"success":True,"latency_ms":1580,"called_at":ts(1438),"error_source":None,"error_code":None},
]
INCIDENTS=[
 {"incident_id":uid('incident',0),"run_id":RUNS[2]['run_id'],"api_call_id":None,"status":"OPEN","severity":"HIGH","error_source":"LANGGRAPH","error_code":"NODE_EXECUTION_ERROR","error_message":"코스 검증 노드 처리 실패","failed_step_name":"코스 검증","occurred_at":ts(119),"resolved_at":None},
 {"incident_id":uid('incident',1),"run_id":RUNS[3]['run_id'],"api_call_id":CALLS[3]['api_call_id'],"status":"RESOLVED","severity":"MEDIUM","error_source":"LLM","error_code":"LLM_RATE_LIMIT","error_message":"모델 호출 요청 제한","failed_step_name":"코스 생성","occurred_at":ts(1439),"resolved_at":ts(1438)},
]
RECOVERIES=[
 {"recovery_id":uid('recovery',0),"incident_id":INCIDENTS[0]['incident_id'],"run_id":RUNS[2]['run_id'],"attempt_number":1,"recovery_action":"RETRY","status":"FAILED","started_at":ts(119),"finished_at":ts(118),"duration_ms":800},
 {"recovery_id":uid('recovery',1),"incident_id":INCIDENTS[1]['incident_id'],"run_id":RUNS[3]['run_id'],"attempt_number":1,"recovery_action":"RETRY_WITH_BACKOFF","status":"RECOVERED","started_at":ts(1439),"finished_at":ts(1438),"duration_ms":1200},
]
def filtered_runs(days):
 cutoff=NOW-timedelta(days=days)
 return [r for r in RUNS if datetime.fromisoformat(r['started_at'])>=cutoff]
