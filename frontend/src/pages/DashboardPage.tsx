import type {DashboardData} from '../components/DashboardCommon';
import {Activity, Database, RefreshCw, Clock, CheckCircle2, XCircle, ArrowRight} from '../icons';
import {ResponsiveContainer, CartesianGrid, XAxis, YAxis, Tooltip, Legend, BarChart, Bar, PieChart, Pie, Cell} from 'recharts';
import {Metric,statusLabel} from '../components/DashboardCommon';
import type {Page} from '../types';
type Props = {data:DashboardData;setPage:(page:Page)=>void;};
export default function DashboardPage({data,setPage}:Props){
const sourceLabels: Record<string,string> = {LANGGRAPH:'LangGraph',LLM:'LLM API',EXTERNAL_API:'외부 API',DATABASE:'DB',UNKNOWN:'기타'};
const failureData = Object.entries(sourceLabels).map(([key,name])=>({name,count:data.summary.failure_by_source[key]??0}));
const outcomeData = [{name:'성공',value:data.summary.success,color:'#5368ef'},{name:'실패',value:data.summary.failed,color:'#f36c86'}].filter(item=>item.value>0);
const latencyData = [...data.apiStats].sort((a,b)=>b.avg_latency_ms-a.avg_latency_ms).slice(0,6);
return <>

      <section className="kpis">
        <Metric icon={<Activity/>} label="전체 AI 실행" value={`${data.summary.total}건`}/>
        <Metric icon={<CheckCircle2/>} label="성공" value={`${data.summary.success}건`} sub={`성공률 ${data.summary.success_rate}%`}/>
        <Metric icon={<XCircle/>} label="실패" value={`${data.summary.failed}건`}/>
        <Metric icon={<Clock/>} label="평균 실행 시간" value={`${(data.summary.avg_duration_ms/1000).toFixed(1)}초`}/>
        <Metric icon={<RefreshCw/>} label="복구 완료 장애" value={`${data.summary.recovered}건`}/>
      </section>
      <section className="two"><div className="panel"><h3>일별 AI 실행 추이</h3><div className="chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={data.trends}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="date" tickFormatter={s=>s.slice(5)} fontSize={11}/><YAxis allowDecimals={false}/><Tooltip/><Legend/><Bar dataKey="success" name="성공" fill="#5368ef"/><Bar dataKey="failed" name="실패" fill="#f36c86"/><Bar dataKey="recovered" name="복구" fill="#20b89b"/></BarChart></ResponsiveContainer></div></div>
      <div className="panel"><h3>서비스 상태 <small>모의 응답</small></h3><div className="health">{data.health.services.map(s=><div className="healthitem" key={s.name}><span title={s.description||s.name}><Database size={16}/>{s.name}</span><span className={s.status==='UP'?'ok':'muted'}>{statusLabel(s.status)}</span></div>)}</div></div></section>
      <section className="two dashboard-extra-charts">
        <div className="panel"><h3>전체 실행 성공·실패 비율 <small>최종 실행 결과</small></h3><div className="chart"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={outcomeData} dataKey="value" nameKey="name" cx="50%" cy="48%" innerRadius={62} outerRadius={90} label={({name,percent})=>`${name} ${(percent*100).toFixed(0)}%`}>{outcomeData.map(entry=><Cell key={entry.name} fill={entry.color}/>)}</Pie><Tooltip formatter={(value:number)=>`${value}건`}/><Legend/></PieChart></ResponsiveContainer></div>{outcomeData.length===0&&<p className="hint">실행 데이터가 없습니다.</p>}</div>
        <div className="panel"><h3>오류 발생 위치별 건수 <small>원인 분류</small></h3><div className="chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={failureData} layout="vertical" margin={{left:16,right:20}}><CartesianGrid strokeDasharray="3 3"/><XAxis type="number" allowDecimals={false}/><YAxis type="category" dataKey="name" width={90} fontSize={12}/><Tooltip formatter={(value:number)=>`${value}건`}/><Bar dataKey="count" name="오류 건수" fill="#ef8497" radius={[0,5,5,0]}/></BarChart></ResponsiveContainer></div></div>
      </section>
      <section className="panel"><h3>API 제공자별 평균 응답시간 <small>밀리초(ms) · 상위 6개</small></h3><div className="chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={latencyData}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="provider" fontSize={11}/><YAxis unit="ms" fontSize={11}/><Tooltip formatter={(value:number)=>`${value}ms`}/><Bar dataKey="avg_latency_ms" name="평균 응답시간" fill="#20b89b" radius={[5,5,0,0]}/></BarChart></ResponsiveContainer></div>{latencyData.length===0&&<p className="hint">API 호출 데이터가 없습니다.</p>}</section>
      <section className="panel"><h3>실패 원인 구분 <small>모의 실행 로그 기준</small></h3><div className="failure-summary"><div><strong>에이전트 흐름 오류</strong><b>{data.summary.failure_by_source.LANGGRAPH??0}건</b><span>LangGraph 노드·상태·Handoff 오류</span></div><div><strong>LLM 관련 오류</strong><b>{data.summary.failure_by_source.LLM??0}건</b><span>모델 호출·응답 형식·한도 오류</span></div></div><p className="hint">복구 완료 장애도 최초 장애 원인에 포함됩니다. 실제 연동 전까지는 예시 데이터입니다.</p></section>
      <section className="three">{[{id:'runs' as Page,title:'실행 이력',count:`${data.runs.length}건`,desc:'에이전트 실행 타임라인 확인'},{id:'api' as Page,title:'API 모니터링',count:`${data.apiCalls.length}건`,desc:'호출 성공률과 응답 시간 확인'},{id:'incidents' as Page,title:'장애·복구 기록',count:`${data.incidents.length}건`,desc:'장애 원인과 복구 시도 확인'}].map(c=><button key={c.id} className="jump panel" onClick={()=>setPage(c.id)}><strong>{c.title}</strong><b>{c.count}</b><span>{c.desc} <ArrowRight size={15}/></span></button>)}</section>
</>;
}
