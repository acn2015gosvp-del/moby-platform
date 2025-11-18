# CI/CD 파이프라인 가이드

MOBY Platform의 CI/CD 파이프라인 설정 및 사용 가이드입니다.

## 📋 개요

이 프로젝트는 GitHub Actions를 사용하여 자동화된 CI/CD 파이프라인을 제공합니다.

### CI (Continuous Integration) 파이프라인

**트리거 조건**:
- `main` 또는 `develop` 브랜치에 push
- `main` 또는 `develop` 브랜치로의 Pull Request

**실행 작업**:
1. **Backend Tests**: Python 테스트 실행 및 커버리지 수집
2. **Frontend Tests**: TypeScript/React 빌드 및 린트 검사
3. **Lint**: 코드 포맷팅 및 린팅 검사
4. **Security Scan**: 의존성 취약점 및 보안 검사

### CD (Continuous Deployment) 파이프라인

**트리거 조건**:
- `main` 브랜치에 push (Staging 배포)
- `v*` 태그가 push됨 (Production 배포)

**실행 작업**:
1. **Build and Push**: Docker 이미지 빌드 및 푸시
2. **Deploy Staging**: Staging 환경 배포
3. **Deploy Production**: Production 환경 배포 (태그 기반)

---

## 🔧 설정 방법

### 1. GitHub Secrets 설정

Docker Hub 인증을 위해 GitHub Secrets에 다음을 추가하세요:

**Settings → Secrets and variables → Actions → New repository secret**

- `DOCKER_USERNAME`: Docker Hub 사용자명
- `DOCKER_PASSWORD`: Docker Hub 비밀번호 또는 액세스 토큰

### 2. 환경 변수 설정

각 환경(Staging, Production)에 필요한 환경 변수를 GitHub Environments에 설정하세요:

**Settings → Environments → New environment**

필수 환경 변수:
- `ENVIRONMENT`: `staging` 또는 `production`
- `SECRET_KEY`: 프로덕션용 시크릿 키
- `INFLUX_URL`: InfluxDB URL
- `INFLUX_TOKEN`: InfluxDB 토큰
- `INFLUX_ORG`: InfluxDB 조직명
- `MQTT_HOST`: MQTT 브로커 호스트
- `MQTT_PORT`: MQTT 브로커 포트
- `GEMINI_API_KEY`: Gemini API 키 (보고서 생성 기능 사용 시)
- `OPENAI_API_KEY`: OpenAI API 키 (LLM 요약 기능 사용 시, 선택사항)

---

## 📊 파이프라인 상세

### CI 파이프라인 (`.github/workflows/ci.yml`)

#### Backend Tests
- Python 3.12 환경 설정
- 의존성 설치
- pytest를 사용한 테스트 실행
- 커버리지 리포트 생성 (Codecov 업로드)

#### Frontend Tests
- Node.js 20 환경 설정
- npm 의존성 설치
- 린트 검사
- 프로덕션 빌드 테스트

#### Lint
- Black (코드 포맷터) 검사
- Flake8 (린터) 검사

#### Security Scan
- Safety (의존성 취약점 검사)
- Bandit (보안 린터)

### CD 파이프라인 (`.github/workflows/cd.yml`)

#### Build and Push
- Docker Buildx 설정
- Backend 및 Frontend 이미지 빌드
- Docker Hub에 푸시 (선택사항)

#### Deploy Staging
- `main` 브랜치에 push 시 자동 실행
- Staging 환경 배포

#### Deploy Production
- `v*` 태그가 push될 때만 실행
- Production 환경 배포

---

## 🚀 사용 방법

### 개발 워크플로우

1. **기능 개발**
   ```bash
   git checkout -b feature/my-feature
   # 코드 작성 및 커밋
   git push origin feature/my-feature
   ```

2. **Pull Request 생성**
   - GitHub에서 PR 생성
   - CI 파이프라인이 자동 실행
   - 모든 테스트 통과 후 머지

3. **Staging 배포**
   ```bash
   git checkout main
   git merge feature/my-feature
   git push origin main
   # 자동으로 Staging 환경에 배포
   ```

4. **Production 배포**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   # 자동으로 Production 환경에 배포
   ```

---

## 🔍 파이프라인 상태 확인

### GitHub Actions 탭

1. GitHub 저장소에서 **Actions** 탭 클릭
2. 실행 중인 워크플로우 확인
3. 각 작업의 로그 확인

### 배지 추가 (선택사항)

README.md에 CI 상태 배지를 추가할 수 있습니다:

```markdown
![CI](https://github.com/your-org/moby-platform/workflows/CI%20Pipeline/badge.svg)
```

---

## ⚙️ 커스터마이징

### 테스트 커버리지 임계값 설정

`.github/workflows/ci.yml`에서 커버리지 임계값을 설정할 수 있습니다:

```yaml
- name: Run tests
  run: |
    pytest tests/ -v --cov=backend --cov-report=xml --cov-report=term --cov-fail-under=80
```

### 배포 스크립트 수정

`.github/workflows/cd.yml`의 `deploy-staging` 및 `deploy-production` 단계에서 실제 배포 스크립트를 추가하세요:

```yaml
- name: Deploy to staging
  run: |
    # kubectl, docker-compose, ssh 등을 사용한 배포 스크립트
    kubectl apply -f k8s/staging/
    # 또는
    docker-compose -f docker-compose.staging.yml up -d
```

---

## 🐛 문제 해결

### CI 실패 시

1. **로컬에서 테스트 실행**
   ```bash
   cd backend
   pytest tests/ -v
   ```

2. **로컬에서 린트 실행**
   ```bash
   black --check backend/
   flake8 backend/
   ```

3. **로컬에서 빌드 테스트**
   ```bash
   cd frontend
   npm run build
   ```

### CD 실패 시

1. **Docker 이미지 빌드 확인**
   ```bash
   docker build -t moby-platform-backend .
   docker build -t moby-platform-frontend ./frontend
   ```

2. **환경 변수 확인**
   - GitHub Secrets 및 Environments 설정 확인
   - 필수 환경 변수가 모두 설정되었는지 확인

---

## 📝 참고 사항

- CI 파이프라인은 모든 PR에서 실행됩니다
- CD 파이프라인은 `main` 브랜치와 태그에만 실행됩니다
- Production 배포는 태그 기반이므로 신중하게 진행하세요
- 보안 검사는 경고만 표시하며 파이프라인을 중단하지 않습니다 (필요 시 수정 가능)

---

## 🔐 보안 고려사항

- GitHub Secrets에 민감한 정보 저장
- Production 환경 변수는 별도로 관리
- Docker 이미지에 시크릿 포함 금지
- 배포 스크립트에 적절한 권한 설정

---

**참고**: 이 CI/CD 파이프라인은 기본 설정입니다. 실제 배포 환경에 맞게 수정이 필요할 수 있습니다.

