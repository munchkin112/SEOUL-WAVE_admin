/** UUID-based API contract. Production must use authenticated session, not browser-stored admin key. */
const BASE=import.meta.env.VITE_API_BASE_URL||(import.meta.env.DEV?'http://localhost:8002':'/admin');
const ADMIN_KEY=import.meta.env.DEV?import.meta.env.VITE_DEMO_ADMIN_KEY:undefined;
export async function getJSON<T>(path:string):Promise<T>{const headers:HeadersInit=ADMIN_KEY?{'X-Admin-Key':ADMIN_KEY}:{};const r=await fetch(`${BASE}${path}`,{headers});if(!r.ok)throw new Error(`${r.status} ${r.statusText}`);return r.json() as Promise<T>}
export type UUID=string;
export type FailureSource='LANGGRAPH'|'LLM'|'EXTERNAL_API'|'DATABASE'|'UNKNOWN'|null;
export type RunStatus='RUNNING'|'SUCCESS'|'FAILED';
export type RecoveryStatus='RUNNING'|'RECOVERED'|'FAILED';
export type IncidentStatus='OPEN'|'RECOVERING'|'RESOLVED';
export type Run={run_id:UUID;status:RunStatus;duration_ms:number|null;started_at:string;finished_at:string|null;route:string|null;companion_type:string|null;error_source:FailureSource;error_code:string|null;failed_step_name:string|null};
export type Summary={total:number;success:number;failed:number;recovered:number;success_rate:number;avg_duration_ms:number;failure_by_source:Record<string,number>;mock:boolean};
export type Trend={date:string;success:number;failed:number;recovered:number};
export type ApiCall={api_call_id:UUID;run_id:UUID;provider:string;api_type:'LLM'|'CULTURE'|'MAPS'|'OTHER';http_status:number|null;success:boolean;latency_ms:number;called_at:string;error_source:FailureSource;error_code:string|null};
export type ApiStat={provider:string;total:number;success:number;failed:number;avg_latency_ms:number};
export type Recovery={recovery_id:UUID;incident_id:UUID;run_id:UUID|null;attempt_number:number;recovery_action:string;status:RecoveryStatus;started_at:string;finished_at:string|null;duration_ms:number|null};
export type Incident={incident_id:UUID;run_id:UUID|null;api_call_id:UUID|null;status:IncidentStatus;severity:string;error_source:FailureSource;error_code:string;error_message:string|null;failed_step_name:string|null;occurred_at:string;resolved_at:string|null;recoveries:Recovery[]};
export type Step={step_log_id:UUID;run_id:UUID;step_order:number;agent_name:string;step_name:string;status:RunStatus;started_at:string;finished_at:string|null;duration_ms:number|null;error_source:FailureSource;error_code:string|null};
export type Handoff={handoff_id:UUID;run_id:UUID;from_agent:string;to_agent:string;status:RunStatus;started_at:string;finished_at:string|null;duration_ms:number|null;error_source:FailureSource;error_code:string|null};
export type RunComponent={run_id:UUID;component_name:'POSTGRESQL'|'OPERATIONAL_LOG_SCHEMA'|'LANGGRAPH'|'LLM_API'|'SEOUL_CULTURAL_EVENTS';status:'UP'|'DOWN'|'DEGRADED'|'RUNNING'|'NOT_RUN'|'UNKNOWN';started_at:string|null;checked_at:string;latency_ms:number|null;reason_code:string|null};
export type RunDetail={run:Run;steps:Step[];handoffs:Handoff[];components:RunComponent[];api_calls:ApiCall[]};
export type HealthService={name:string;status:string;description?:string;reason_code?:string;latency_ms?:number};
export type Health={mode:string;checked_at:string;services:HealthService[]};
