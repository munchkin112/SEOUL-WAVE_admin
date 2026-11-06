import React from 'react';
import type {Summary, Trend, Run, RunDetail, ApiCall, ApiStat, Incident, Health} from '../api';
export type DashboardData = {summary:Summary;trends:Trend[];runs:Run[];apiCalls:ApiCall[];apiStats:ApiStat[];incidents:Incident[];health:Health};
export function statusLabel(status:string){return ({SUCCESS:'성공',FAILED:'실패',RECOVERED:'복구 완료',RUNNING:'실행 중',UP:'정상',NOT_CONNECTED:'미연결',NOT_CHECKED:'미확인',NOT_CONFIGURED:'미설정',RESOLVED:'해결',OPEN:'미해결',RECOVERING:'복구 중',MEDIUM:'보통',HIGH:'높음',LOW:'낮음'} as Record<string,string>)[status] || status;}
export function Status({value}:{value:string}){return <span className={`pill ${value.toLowerCase()}`}>{statusLabel(value)}</span>}
export function failureLabel(source?:string|null){return ({LANGGRAPH:'에이전트 흐름',LLM:'LLM 호출',EXTERNAL_API:'외부 API',DATABASE:'데이터베이스'} as Record<string,string>)[source||''] || '해당 없음';}
export function FailureSource({source}:{source?:string|null}){return source?<span className={`pill ${source.toLowerCase()}`}>{failureLabel(source)}</span>:<span className="muted">—</span>;}
export function formatTime(iso:string){return new Date(iso).toLocaleString('ko-KR',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});}
export function Metric({icon,label,value,sub}:{icon:React.ReactNode;label:string;value:string;sub?:string}){return <div className="metric"><div className="metricicon">{icon}</div><span>{label}</span><strong>{value}</strong>{sub&&<small>{sub}</small>}</div>}
