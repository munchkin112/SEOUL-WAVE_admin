"""Read-only controller. Mock UUID data; switch repository to PostgreSQL on integration."""
import os
from uuid import UUID
from fastapi import FastAPI, Header, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from . import models,services
app=FastAPI(title='Han River Admin API (UUID Contract)',version='1.6.0')
app.add_middleware(CORSMiddleware,allow_origins=os.getenv('CORS_ORIGINS','http://localhost:5173').split(','),allow_credentials=False,allow_methods=['GET'],allow_headers=['*'])
def admin_auth(x_admin_key: str|None=Header(default=None)):
 if x_admin_key!=os.getenv('ADMIN_API_KEY','local-demo-key'):
  raise HTTPException(status_code=401,detail='Invalid admin key')
AUTH=[Depends(admin_auth)]
@app.get('/api/v1/admin/dashboard/summary',dependencies=AUTH)
def get_summary(days:int=Query(7,ge=1,le=30)):return services.summary(days)
@app.get('/api/v1/admin/dashboard/trends',dependencies=AUTH)
def get_trends(days:int=Query(7,ge=1,le=30)):return {'items':services.trends(days),'mock':True}
@app.get('/api/v1/admin/agent-runs',dependencies=AUTH)
def get_runs(limit:int=Query(100,ge=1,le=100)):return {'items':models.RUNS[:limit],'total':len(models.RUNS),'mock':True}
@app.get('/api/v1/admin/agent-runs/{run_id}',dependencies=AUTH)
def get_run(run_id:UUID):
 key=str(run_id);run=next((r for r in models.RUNS if r['run_id']==key),None)
 if not run:raise HTTPException(status_code=404,detail='Run not found')
 return {'run':run,'steps':[s for s in models.STEPS if s['run_id']==key],'handoffs':[h for h in models.HANDOFFS if h['run_id']==key],'mock':True}
@app.get('/api/v1/admin/api-calls',dependencies=AUTH)
def get_api_calls():return {'items':models.CALLS,'stats':services.api_stats(),'mock':True}
@app.get('/api/v1/admin/incidents',dependencies=AUTH)
def get_incidents():return {'items':[{**i,'recoveries':[r for r in models.RECOVERIES if r['incident_id']==i['incident_id']]} for i in models.INCIDENTS],'mock':True}
@app.get('/api/v1/admin/health',dependencies=AUTH)
def get_health():return {'mode':'MOCK','checked_at':models.NOW.isoformat(),'services':[{'name':'FastAPI','status':'UP'},{'name':'PostgreSQL','status':'NOT_CONNECTED'},{'name':'LangGraph','status':'NOT_CONNECTED','description':'에이전트 실행 흐름'},{'name':'LLM API','status':'NOT_CHECKED','description':'모델 호출 상태'},{'name':'Seoul Cultural Events','status':'NOT_CHECKED'}]}
