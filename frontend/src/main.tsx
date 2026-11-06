import React, {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {RefreshCw, Waves} from './icons';
import {navigationItems} from './config/navigation';
import {getJSON, type Summary, type Trend, type Run, type RunDetail, type ApiCall, type ApiStat, type Incident, type Health} from './api';
import type {Page} from './types';
import type {DashboardData} from './components/DashboardCommon';
import DashboardPage from './pages/DashboardPage';
import RunsPage from './pages/RunsPage';
import ApiMonitoringPage from './pages/ApiMonitoringPage';
import IncidentsPage from './pages/IncidentsPage';
import './style.css';

function App(){
  const [page,setPage]=useState<Page>('dashboard');
  const [data,setData]=useState<DashboardData|null>(null);
  const [detail,setDetail]=useState<RunDetail|null>(null);
  const [selected,setSelected]=useState('');
  const [days,setDays]=useState(7);
  const [runStatus,setRunStatus]=useState('ALL');
  const [runSearch,setRunSearch]=useState('');
  const [provider,setProvider]=useState('ALL');
  const [apiStatus,setApiStatus]=useState('ALL');
  const [incidentStatus,setIncidentStatus]=useState('ALL');
  const [expandedIncident,setExpandedIncident]=useState<string|null>(null);
  const [error,setError]=useState('');
  const [loading,setLoading]=useState(false);
  async function refresh(){
    setLoading(true);setError('');
    try {
      const [summary,trends,runs,calls,incidents,health]=await Promise.all([
        getJSON<Summary>(`/api/v1/admin/dashboard/summary?days=${days}`),
        getJSON<{items:Trend[]}>(`/api/v1/admin/dashboard/trends?days=${days}`),
        getJSON<{items:Run[]}>('/api/v1/admin/agent-runs'),
        getJSON<{items:ApiCall[];stats:ApiStat[]}>('/api/v1/admin/api-calls'),
        getJSON<{items:Incident[]}>('/api/v1/admin/incidents'),
        getJSON<Health>('/api/v1/admin/health')]);
      setData({summary,trends:trends.items,runs:runs.items,apiCalls:calls.items,apiStats:calls.stats,incidents:incidents.items,health});
    } catch(e){setError(e instanceof Error?e.message:String(e));}
    finally{setLoading(false);}
  }
  useEffect(()=>{void refresh();},[days]);
  useEffect(()=>{
    if(!selected){setDetail(null);return;}
    let cancelled=false;
    let timer:number|undefined;
    const loadDetail=async()=>{
      try{
        const next=await getJSON<RunDetail>(`/api/v1/admin/agent-runs/${encodeURIComponent(selected)}`);
        if(cancelled)return;
        setDetail(next);
        setData(current=>current?{...current,runs:current.runs.map(run=>run.run_id===selected?{...run,...next.run}:run)}:current);
        if(next.run.status==='RUNNING')timer=window.setTimeout(()=>void loadDetail(),2000);
      }catch(e){if(!cancelled)setError(String(e));}
    };
    void loadDetail();
    return ()=>{cancelled=true;if(timer!==undefined)window.clearTimeout(timer);};
  },[selected]);
  const runs=data?.runs.filter(r=>(runStatus==='ALL'||r.status===runStatus)&&(`${r.run_id} ${r.route??''}`.toLowerCase().includes(runSearch.toLowerCase())))||[];
  const calls=data?.apiCalls.filter(c=>(provider==='ALL'||c.provider===provider)&&(apiStatus==='ALL'||(apiStatus==='SUCCESS')===c.success))||[];
  const incidents=data?.incidents.filter(i=>incidentStatus==='ALL'||i.status===incidentStatus)||[];
  const title=navigationItems.find(n=>n.id===page)?.label;
  return <div className="layout">
    <aside className="sidebar"><h2><Waves size={27}/> 한강버스<br/>AI 나들이 플래너</h2><nav>{navigationItems.map(n=><button key={n.id} className={`nav ${page===n.id?'active':''}`} onClick={()=>setPage(n.id)}><n.icon size={18}/><span>{n.label}</span></button>)}</nav><p className="sidefoot">PostgreSQL 운영 로그 조회</p></aside>
    <main><header><div><h1>{title}</h1><p>{page==='dashboard'?'AI 추천 서비스 운영 현황':page==='runs'?'LangGraph 실행 결과와 단계별 추적':page==='api'?'외부 API 호출 결과와 응답 성능':'장애 발생부터 자동 복구까지 확인'}</p></div><div className="actions">{page==='dashboard'&&<select aria-label="조회 기간" value={days} onChange={e=>setDays(Number(e.target.value))}><option value={7}>최근 7일</option><option value={30}>최근 30일</option></select>}<button onClick={()=>void refresh()} disabled={loading}><RefreshCw size={16}/>{loading?'불러오는 중':'새로고침'}</button></div></header>
    {error&&<div className="error" role="alert">API 요청 실패: {error} · 백엔드 실행 및 CORS 설정을 확인하세요.</div>}
    {!data?<div className="panel">{loading?'데이터를 불러오는 중입니다.':'조회된 데이터가 없습니다.'}</div>:<>
    {page==='dashboard'&&<DashboardPage data={data} setPage={setPage}/>}
    {page==='runs'&&<RunsPage data={data} runs={runs} selected={selected} setSelected={setSelected} detail={detail} runSearch={runSearch} setRunSearch={setRunSearch} runStatus={runStatus} setRunStatus={setRunStatus}/>}
    {page==='api'&&<ApiMonitoringPage data={data} calls={calls} provider={provider} setProvider={setProvider} apiStatus={apiStatus} setApiStatus={setApiStatus}/>}
    {page==='incidents'&&<IncidentsPage data={data} incidents={incidents} incidentStatus={incidentStatus} setIncidentStatus={setIncidentStatus} expandedIncident={expandedIncident} setExpandedIncident={setExpandedIncident}/>}
    </>}
    </main>
  </div>;
}
createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>);
