# 운영 배포

로컬 개발은 기존 docker-compose.admin.yml을 사용한다. 운영은 사용자 서비스의 compose.prod.yaml에 compose.prod.admin.yaml을 합친다. 독립 PostgreSQL을 만들지 않는다.

- 운영 프론트: frontend/Dockerfile.prod로 TypeScript/Vite 빌드 후 Nginx에서 /admin/을 제공한다.
- 운영 API: 기존 backend/Dockerfile을 사용한다.
- 브라우저에는 VITE_DEMO_ADMIN_KEY를 포함하지 않는다. Basic 인증을 통과한 요청에만 Nginx가 서버의 ADMIN_API_KEY를 추가해 admin-api로 전달한다.
- ADMIN_API_KEY는 URL-safe 32~128자, ADMIN_HTPASSWD_FILE은 저장소 밖의 htpasswd 파일 경로다. Basic 인증과 사이트 접속은 승인된 HTTP 학원 시연 범위에서 사용하며 HTTP 자체는 암호화하지 않는다.
- CI는 관리자 인증 테스트와 TypeScript·Vite 빌드, demo key 미포함을 검사한다.
- 이미지 게시는 SEOUL-WAVE 서비스 저장소의 Publish frozen Admin images를 dev에서 수동 실행한다. 이 저장소의 검토된 40자리 SHA를 넣는다. 기존 서비스 OIDC와 seoulwave ECR 권한을 재사용한다. 태그는 admin-api-<SHA>, admin-frontend-<SHA>이다.
- 호스트 Nginx의 /admin/을 127.0.0.1:8081로 프록시한다. 브라우저 API 경로는 /admin/api/v1/admin/...이다.

전체 DB 마이그레이션·초기 데이터·Nginx 적용과 롤백 절차는 SEOUL-WAVE의 docs/operations/ec2-deployment.md를 따른다. 실제 EC2 실행과 DB 마이그레이션, Nginx 적용은 사용자 승인 후 수행한다.
