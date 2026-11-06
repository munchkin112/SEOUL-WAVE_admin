# SEOUL-WAVE + 운영 대시보드 팀원 로컬 실행

이 안내대로 각자 PC에서 SEOUL-WAVE, 관리자 대시보드, PostgreSQL을 같은 Docker Compose 프로젝트로 실행합니다. 공용 DB는 사용하지 않으며, 각 PC의 로그 데이터는 해당 PC에 저장됩니다.

## 1. 저장소 준비

Docker Desktop을 실행한 뒤 두 저장소를 같은 상위 폴더에 둡니다.

```text
workspace/
├── SEOUL-WAVE/
└── SEOUL-WAVE_admin/
```

두 저장소의 최신 변경사항을 각각 내려받습니다. 운영 로그 스키마는 SEOUL-WAVE의 `003_operations_logging.sql`, 실행별 구성요소 상태는 `007_run_component_logs.sql`, 자동 복구와 DB 장애 전환 로그는 `008_auto_recovery.sql`에 있습니다. 대시보드 Compose 설정은 이 저장소의 [docker-compose.admin.yml](./docker-compose.admin.yml)에 있습니다.

## 2. 로컬 환경변수 준비

SEOUL-WAVE 최상위 `.env`에는 DB/API 설정을 둡니다. 이 저장소의 `.env`에는 로컬 대시보드 인증 키 `VITE_DEMO_ADMIN_KEY`를 둡니다. Compose 명령은 두 파일을 함께 읽습니다.

```dotenv
OPENAI_API_KEY=<서비스에서 사용하는 OpenAI API 키>
OPENAI_MODEL=<서비스에서 사용하는 모델명>
SEOUL_CULTURE_API_KEY=<서비스에서 사용하는 서울시 문화행사 API 키>
```

운영 대시보드 저장소의 `.env`:

```dotenv
VITE_DEMO_ADMIN_KEY=<로컬에서만 사용할 긴 임의의 값>
```

`.env` 파일이나 실제 비밀번호/API 키는 팀 채팅, 저장소, 커밋에 올리지 마세요. 공급자 키는 admin-api에만 전달됩니다. `VITE_DEMO_ADMIN_KEY`는 브라우저에 포함되는 로컬 전용 키이므로 외부 공개 서비스에 사용하면 안 됩니다.

## 3. 운영 로그 테이블 생성

아래 명령은 PowerShell의 현재 폴더가 `SEOUL-WAVE_admin`일 때 실행합니다. 첫 명령으로 SEOUL-WAVE 폴더로 이동하며, 이후 단계도 그 폴더에서 실행합니다.

```powershell
Set-Location ..\SEOUL-WAVE
docker compose exec -T db psql -U seoul_wave_app -d seoul_wave -c "SELECT t.name, to_regclass('public.' || t.name) AS table_name FROM unnest(ARRAY['agent_runs','agent_step_logs','api_call_logs','handoff_logs','incident_logs','recovery_logs']) AS t(name);"
```

테이블이 모두 존재하면 migration을 다시 실행하지 않습니다. 테이블이 하나도 없을 때만 아래 migration을 한 번 실행합니다. 일부 테이블만 있다면 먼저 DB 상태를 확인하고 팀 담당자와 상의하세요.

```powershell
docker compose --env-file .env --env-file ..\SEOUL-WAVE_admin\.env -f compose.yaml -f ..\SEOUL-WAVE_admin\docker-compose.admin.yml --profile db-migration run --rm db-migrate-operations
```

003 운영 로그 테이블과 007 구성요소 상태 테이블이 이미 적용된 기존 DB에는 자동 복구 마이그레이션도 적용합니다. 008은 재시도 시각과 DB 장애 로그를 위한 nullable 실행 ID를 추가하며, 기존 003은 수정하지 않습니다.

```powershell
docker compose --env-file .env --env-file ..\SEOUL-WAVE_admin\.env -f compose.yaml -f ..\SEOUL-WAVE_admin\docker-compose.admin.yml --profile db-migration run --rm db-migrate-run-components
docker compose --env-file .env --env-file ..\SEOUL-WAVE_admin\.env -f compose.yaml -f ..\SEOUL-WAVE_admin\docker-compose.admin.yml --profile db-migration run --rm db-migrate-auto-recovery
```

Migration은 다음 여섯 테이블과 인덱스를 생성합니다.

- `agent_runs`
- `agent_step_logs`
- `api_call_logs`
- `handoff_logs`
- `incident_logs`
- `recovery_logs`

기존 DB에 기록된 로그를 다른 PC로 복사하지는 않습니다. migration은 스키마만 생성하며, 데이터는 각자 실행 중인 서비스가 새 로그를 기록해야 표시됩니다.

## 4. 전체 서비스 실행

SEOUL-WAVE 저장소 폴더에서 두 저장소를 함께 실행합니다.

```powershell
docker compose --env-file .env --env-file ..\SEOUL-WAVE_admin\.env -f compose.yaml -f ..\SEOUL-WAVE_admin\docker-compose.admin.yml up --build -d
```

브라우저 주소:

- SEOUL-WAVE: http://localhost:5174
- 운영 대시보드: http://localhost:5175
- 관리자 API 및 DB 상태: http://localhost:8002/api/v1/admin/health

상태 응답에서 PostgreSQL과 Operational log schema가 `UP`인지 확인합니다. 실행 이력에서 추천 요청을 선택하면 `run_id`별 다섯 구성요소의 상태와 실제 API 호출, LangGraph 단계 로그를 확인할 수 있습니다. 실행 중인 상세는 2초 간격으로 갱신됩니다. 일시 장애 복구 이력과 PostgreSQL 연결 장애는 기존 장애·복구 화면에서 확인할 수 있습니다. DB가 내려간 동안 감시 컨테이너가 별도 영속 볼륨에 감지 시각을 보관하고, DB 복구 후 기존 운영 로그 테이블로 전달합니다. 대시보드의 전체 LLM health 상태는 모델 메타데이터 조회이며, 추천 실행 상세의 LLM 상태는 해당 추천 요청에서 발생한 실제 호출 로그를 보여줍니다.

## 5. 중지 및 데이터 보존

서비스만 중지하려면 같은 Compose 파일 조합으로 다음을 실행합니다.

```powershell
docker compose --env-file .env --env-file ..\SEOUL-WAVE_admin\.env -f compose.yaml -f ..\SEOUL-WAVE_admin\docker-compose.admin.yml down
```

DB 데이터를 보존하려면 `down -v`를 사용하지 마세요. Compose는 기존 `postgres_data` 볼륨을 함께 사용합니다.
