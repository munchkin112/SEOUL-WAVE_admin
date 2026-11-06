import type {DashboardData} from '../components/DashboardCommon';
import {Activity, XCircle, RefreshCw, ArrowRight} from '../icons';
import {Metric,Status,FailureSource,formatTime} from '../components/DashboardCommon';
import type {Run,RunDetail} from '../api';
type Props = {data:DashboardData;runs:Run[];selected:string;setSelected:(id:string)=>void;detail:RunDetail|null;runSearch:string;setRunSearch:(v:string)=>void;runStatus:string;setRunStatus:(v:string)=>void;};

const componentLabels:Record<string,string>={
  POSTGRESQL:'PostgreSQL',
  OPERATIONAL_LOG_SCHEMA:'Operational log schema',
  LANGGRAPH:'LangGraph',
  LLM_API:'LLM API',
  SEOUL_CULTURAL_EVENTS:'Seoul Cultural Events',
};

export default function RunsPage({data,runs,selected,setSelected,detail,runSearch,setRunSearch,runStatus,setRunStatus}:Props){
  return <>
    <section className="kpis kpis-three">
      <Metric icon={<Activity/>} label="실행 기록" value={`${data.runs.length}건`}/>
      <Metric icon={<XCircle/>} label="실패" value={`${data.runs.filter(r=>r.status==='FAILED').length}건`}/>
      <Metric icon={<RefreshCw/>} label="복구 완료" value={`${data.incidents.filter(i=>i.status==='RESOLVED').length}건`}/>
    </section>
    <section className="panel">
      <div className="panelhead"><h3>AI 실행 목록</h3><div className="filters">
        <input aria-label="실행 검색" placeholder="실행 ID 또는 구간 검색" value={runSearch} onChange={e=>setRunSearch(e.target.value)}/>
        <select aria-label="실행 상태" value={runStatus} onChange={e=>setRunStatus(e.target.value)}><option value="ALL">전체 상태</option><option value="SUCCESS">성공</option><option value="FAILED">실패</option><option value="RUNNING">실행 중</option></select>
      </div></div>
      <table><thead><tr><th>실행 ID</th><th>요청 구간</th><th>동행 유형</th><th>시작 시각</th><th>상태</th><th>소요시간</th><th>실패 원인</th><th>상세</th></tr></thead>
        <tbody>{runs.map(r=><tr key={r.run_id} className={`clickrow ${selected===r.run_id?'selected':''}`} onClick={()=>setSelected(r.run_id)}>
          <td>{r.run_id}</td><td>{r.route||'—'}</td><td>{r.companion_type||'—'}</td><td>{formatTime(r.started_at)}</td><td><Status value={r.status}/></td><td>{((r.duration_ms??0)/1000).toFixed(2)}초</td><td><FailureSource source={r.error_source}/></td><td><button className="textbutton" onClick={e=>{e.stopPropagation();setSelected(r.run_id)}}>상세 보기</button></td>
        </tr>)}</tbody>
      </table>
      {runs.length===0&&<p className="empty">조건에 맞는 실행 기록이 없습니다.</p>}
    </section>
    <section className="panel">
      <h3>추천 실행 로그 {detail&&<small>{detail.run.run_id} · {detail.run.route||'구간 미기록'}{detail.run.status==='RUNNING'?' · 2초 간격으로 갱신 중':''}</small>}</h3>
      {!detail?<p className="empty">위 실행 목록에서 항목을 선택하면 해당 추천 테스트의 구성요소 상태와 상세 로그를 확인할 수 있습니다.</p>:<>
        <h4>구성요소 상태</h4>
        <div className="component-log-grid">
          {detail.components.map(component=><article className="component-log" key={component.component_name}>
            <div><strong>{componentLabels[component.component_name]||component.component_name}</strong><Status value={component.status}/></div>
            <small>{component.reason_code||'상태 코드 없음'}{component.latency_ms!==null?` · ${component.latency_ms}ms`:''}</small>
            <small>확인: {formatTime(component.checked_at)}</small>
          </article>)}
        </div>
        <h4>외부 API 호출</h4>
        {detail.api_calls.length?detail.api_calls.map(call=><div className="api-run-log" key={call.api_call_id}>
          <strong>{call.provider} · {call.api_type==='LLM'?'LLM API':call.api_type==='CULTURE'?'Seoul Cultural Events':call.api_type}</strong>
          <Status value={call.success?'UP':'DOWN'}/>
          <span>{call.http_status===null?'HTTP 응답 없음':`HTTP ${call.http_status}`} · {call.latency_ms}ms</span>
          {call.error_code&&<code>{call.error_code}</code>}
          <small>{formatTime(call.called_at)}</small>
        </div>):<p className="empty">기록된 외부 API 호출이 없습니다. 구성요소 상태의 미실행 여부를 확인하세요.</p>}
        <div className="detailgrid">
          <div><h4>LangGraph 실행 단계</h4><div className="steps">
            {detail.steps.length?detail.steps.map((s,index)=><div key={`${s.step_order}-${index}`} className="step"><span className={`dot ${s.status==='FAILED'?'bad':''}`}/><div><strong>{s.step_order}. {s.agent_name}</strong><p>{s.step_name} · <Status value={s.status}/> · {s.duration_ms??'—'}ms {s.error_source&&<> · <FailureSource source={s.error_source}/> {s.error_code}</>}</p></div></div>):<p className="empty">실행된 LangGraph 단계가 없습니다.</p>}
          </div></div>
          <div><h4>에이전트 Handoff</h4>{detail.handoffs.length?detail.handoffs.map((h,i)=><div className="handoff" key={i}>{h.from_agent}<ArrowRight size={15}/>{h.to_agent}<Status value={h.status}/>{h.error_code&&<small>{h.error_code}</small>}</div>):<p className="empty">전달 기록이 없습니다.</p>}</div>
        </div>
      </>}
    </section>
  </>;
}
