"""Dashboard aggregates: final run success and incident recovery are separate metrics."""
from collections import defaultdict
from datetime import datetime,timedelta
from . import models

def summary(days=7):
 runs=models.filtered_runs(days)
 completed=[r for r in runs if r['status']!='RUNNING']
 success=sum(r['status']=='SUCCESS' for r in completed)
 failed=sum(r['status']=='FAILED' for r in completed)
 recovered=sum(i['status']=='RESOLVED' for i in models.INCIDENTS if i['run_id'] in {r['run_id'] for r in runs})
 failures=defaultdict(int)
 for i in models.INCIDENTS:
  if i['run_id'] in {r['run_id'] for r in runs}: failures[i['error_source']]+=1
 return {'total':len(runs),'success':success,'failed':failed,'recovered':recovered,'success_rate':round(100*success/len(completed),1) if completed else 0,'avg_duration_ms':round(sum(r['duration_ms'] or 0 for r in completed)/len(completed)) if completed else 0,'failure_by_source':{key:failures[key] for key in ('LANGGRAPH','LLM','EXTERNAL_API','DATABASE','UNKNOWN')},'mock':True}

def trends(days=7):
 runs=models.filtered_runs(days); result=[]
 for n in range(days-1,-1,-1):
  day=(models.NOW-timedelta(days=n)).date()
  items=[r for r in runs if datetime.fromisoformat(r['started_at']).date()==day]
  incident_ids={i['run_id'] for i in models.INCIDENTS if i['status']=='RESOLVED' and datetime.fromisoformat(i['occurred_at']).date()==day}
  result.append({'date':day.isoformat(),'success':sum(r['status']=='SUCCESS' for r in items),'failed':sum(r['status']=='FAILED' for r in items),'recovered':len(incident_ids)})
 return result

def api_stats():
 grouped=defaultdict(list)
 for c in models.CALLS:grouped[c['provider']].append(c)
 return [{'provider':p,'total':len(xs),'success':sum(x['success'] for x in xs),'failed':sum(not x['success'] for x in xs),'avg_latency_ms':round(sum(x['latency_ms'] for x in xs)/len(xs))} for p,xs in grouped.items()]
