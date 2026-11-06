import type {DashboardData} from '../components/DashboardCommon';
import {Network,CheckCircle2,Clock,Download} from '../icons';
import {exportApiCallsCsv} from '../utils/exportCsv';
import {Metric,Status,FailureSource,formatTime} from '../components/DashboardCommon';
import type {ApiCall} from '../api';
type Props = {data:DashboardData;calls:ApiCall[];provider:string;setProvider:(v:string)=>void;apiStatus:string;setApiStatus:(v:string)=>void;};
export default function ApiMonitoringPage({data,calls,provider,setProvider,apiStatus,setApiStatus}:Props){
return <>

      <section className="kpis kpis-three"><Metric icon={<Network/>} label="전체 API 호출" value={`${data.apiCalls.length}건`}/><Metric icon={<CheckCircle2/>} label="성공 호출" value={`${data.apiCalls.filter(c=>c.success).length}건`}/><Metric icon={<Clock/>} label="평균 응답 시간" value={`${data.apiCalls.length?Math.round(data.apiCalls.reduce((a,c)=>a+c.latency_ms,0)/data.apiCalls.length):0}ms`}/></section>
      <section className="panel"><h3>제공자별 API 성능</h3><table><thead><tr><th>제공자</th><th>전체 호출</th><th>성공</th><th>실패</th><th>성공률</th><th>평균 응답시간</th></tr></thead><tbody>{data.apiStats.map(s=><tr key={s.provider}><td>{s.provider}</td><td>{s.total}</td><td>{s.success}</td><td>{s.failed}</td><td>{s.total?(100*s.success/s.total).toFixed(1):'0'}%</td><td>{s.avg_latency_ms}ms</td></tr>)}</tbody></table></section>
      <section className="panel"><div className="panelhead"><h3>API 호출 로그</h3><div className="filters"><button type="button" className="csv-button" onClick={()=>exportApiCallsCsv(calls)} disabled={calls.length===0} title="현재 필터에 표시된 API 호출 로그를 CSV로 저장"><Download size={16}/> CSV 다운로드 ({calls.length}건)</button><select aria-label="API 제공자" value={provider} onChange={e=>setProvider(e.target.value)}><option value="ALL">모든 제공자</option>{[...new Set(data.apiCalls.map(c=>c.provider))].map(p=><option key={p} value={p}>{p}</option>)}</select><select aria-label="호출 결과" value={apiStatus} onChange={e=>setApiStatus(e.target.value)}><option value="ALL">전체 결과</option><option value="SUCCESS">성공</option><option value="FAILED">실패</option></select></div></div><table><thead><tr><th>호출 ID</th><th>실행 ID</th><th>제공자</th><th>유형</th><th>HTTP</th><th>결과</th><th>응답시간</th><th>오류 구분</th><th>호출 시각</th></tr></thead><tbody>{calls.map(c=><tr key={c.api_call_id}><td>{c.api_call_id}</td><td title={c.run_id}>{c.run_id.slice(0,8)}…</td><td>{c.provider}</td><td>{c.api_type}</td><td>{c.http_status??"—"}</td><td><Status value={c.success?'SUCCESS':'FAILED'}/></td><td>{c.latency_ms}ms</td><td><FailureSource source={c.error_source}/>{c.error_code&&<small> {c.error_code}</small>}</td><td>{formatTime(c.called_at)}</td></tr>)}</tbody></table>{calls.length===0&&<p className="empty">조건에 맞는 호출 기록이 없습니다.</p>}</section>
</>;
}
