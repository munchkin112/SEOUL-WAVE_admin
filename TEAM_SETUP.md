# SEOUL-WAVE + 운영 대시보드 팀원 로컬 실행

이 안내대로 각자 PC에서 SEOUL-WAVE, 관리자 대시보드, PostgreSQL을 같은 Docker Compose 프로젝트로 실행합니다. 공용 DB는 사용하지 않으며, 각 PC의 로그 데이터는 해당 PC에 저장됩니다.

## 1. 저장소 준비

Docker Desktop을 실행한 뒤 두 저장소를 같은 상위 폴더에 둡니다.

```text
workspace/
├── SEOUL-WAVE/
└── SEOUL-WAVE_admin/
```

두 저장소의 최신 변경사항을 각각 내려받습니다. 운영 로그 스키마는 SEOUL-WAVE의 [003_operations_logging.sql](../SEOUL-WAVE/backend/migrations/003_operations_logging.sql)에 있고, 대시보드 Compose 설정은 이 저장소의 [docker-compose.admin.yml](./docker-compose.admin.yml)에 있습니다.

## 2. 로컬 환경변수 준비

SEOUL-WAVE 최상위 `.env`를 각자 로컬에서 설정합니다. 기존 DB/API 환경변수는 해당 프로젝트 안내에 따라 설정하고, 아래 키를 추가합니다.

```dotenv
ADMIN_API_KEY=<각자 생성한 로컬 전용 임의의 긴 값>
```

`.env` 파일이나 실제 비밀번호/API 키는 팀 채팅, 저장소, 커밋에 올리지 마세요. 대시보드 인증 키는 로컬 개발용이며 브라우저에 전달되므로 외부 공개 서비스에는 사용하면 안 됩니다.

## 3. 운영 로그 테이블 생성

아래 명령은 PowerShell의 현재 폴더가 `SEOUL-WAVE_admin`일 때 실행합니다. 첫 명령으로 SEOUL-WAVE 폴더로 이동하며, 이후 단계도 그 폴더에서 실행합니다.

```powershell
Set-Location ..\SEOUL-WAVE
docker compose exec -T db psql -U seoul_wave_app -d seoul_wave -c "SELECT t.name, to_regclass('public.' || t.name) AS table_name FROM unnest(ARRAY['agent_runs','agent_step_logs','api_call_logs','handoff_logs','incident_logs','recovery_logs']) AS t(name);"
```

테이블이 모두 존재하면 migration을 다시 실행하지 않습니다. 테이블이 하나도 없을 때만 아래 migration을 한 번 실행합니다. 일부 테이블만 있다면 먼저 DB 상태를 확인하고 팀 담당자와 상의하세요.

```powershell
docker compose -f compose.yaml -f ..\SEOUL-WAVE_admin\docker-compose.admin.yml --profile db-migration run --rm db-migrate-operations
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
docker compose -f compose.yaml -f ..\SEOUL-WAVE_admin\docker-compose.admin.yml up --build -d
```

브라우저 주소:

- SEOUL-WAVE: http://localhost:5174
- 운영 대시보드: http://localhost:5175
- 관리자 API 및 DB 상태: http://localhost:8002/api/v1/admin/health

DB 상태 응답에서 PostgreSQL과 Operational log schema가 `UP`인지 확인합니다. 데이터가 아직 기록되지 않았다면 대시보드에 0건이 표시될 수 있습니다.

## 5. 중지 및 데이터 보존

서비스만 중지하려면 같은 Compose 파일 조합으로 다음을 실행합니다.

```powershell
docker compose -f compose.yaml -f ..\SEOUL-WAVE_admin\docker-compose.admin.yml down
```

DB 데이터를 보존하려면 `down -v`를 사용하지 마세요. Compose는 기존 `postgres_data` 볼륨을 함께 사용합니다.
