# Grafana API 기반 임베딩 설정 가이드

## 개요

Grafana 대시보드를 iframe으로 임베딩할 때 Grafana API를 사용하여 동적으로 대시보드 URL을 생성하는 방식으로 변경되었습니다.

## 주요 변경사항

### 이전 방식 (Public Dashboard URL)
- 환경 변수에 전체 Public Dashboard URL을 직접 설정
- URL이 고정되어 있어 유연성이 부족
- 대시보드 정보를 가져올 수 없음

### 현재 방식 (Grafana API)
- Grafana API를 사용하여 대시보드 정보 가져오기
- 설비 ID와 시간 범위에 따라 동적으로 URL 생성
- 대시보드 존재 여부 및 메타데이터 확인 가능

## 환경 변수 설정

### Frontend (.env)

```env
# Grafana Base URL
VITE_GRAFANA_URL=http://192.168.80.99:3000

# Grafana API Key (필수)
# 생성 방법: Grafana → Configuration → API Keys → New API Key
# 권한: Viewer 이상 필요
VITE_GRAFANA_API_KEY=your-grafana-api-key-here

# Grafana Organization ID (기본값: 1)
VITE_GRAFANA_ORG_ID=1

# Grafana 대시보드 UID (필수)
VITE_GRAFANA_DASHBOARD_UID=conveyor-dashboard
```

### Backend (env.example)

```env
# Grafana Base URL
GRAFANA_URL=http://192.168.80.99:3000

# Grafana API Key
GRAFANA_API_KEY=your-grafana-api-key-here

# Grafana Organization ID
GRAFANA_ORG_ID=1

# Grafana 대시보드 UID
GRAFANA_DASHBOARD_UID=conveyor-dashboard
```

## Grafana API 키 생성 방법

1. Grafana에 로그인
2. **Configuration** → **API Keys** 메뉴로 이동
3. **New API Key** 클릭
4. 다음 정보 입력:
   - **Name**: 예) "MOBY Platform API Key"
   - **Role**: **Viewer** 이상 선택 (대시보드 읽기 권한 필요)
   - **Time to live**: 만료 시간 설정 (선택사항)
5. **Add** 클릭
6. 생성된 API 키를 복사하여 환경 변수에 설정

⚠️ **주의**: API 키는 한 번만 표시되므로 안전한 곳에 저장하세요.

## 대시보드 UID 확인 방법

1. Grafana에서 대시보드를 엽니다
2. 대시보드 설정 (⚙️)으로 이동
3. **General** 탭에서 **UID** 확인
4. 또는 URL에서 확인: `/d/{UID}/...`

## 코드 구조

### `frontend/src/utils/grafana.ts`

Grafana API 관련 유틸리티 함수:

- `getGrafanaDashboard(uid)`: 대시보드 정보 가져오기
- `buildGrafanaDashboardUrl(uid, deviceId, timeRange)`: 대시보드 URL 생성
- `checkGrafanaConnection()`: Grafana 서버 연결 확인
- `getGrafanaApiHeaders()`: API 요청 헤더 생성

### `frontend/src/pages/Monitoring.tsx`

모니터링 페이지:

- Grafana API를 사용하여 대시보드 정보 가져오기
- 설비 ID와 시간 범위에 따라 동적으로 URL 생성
- iframe으로 대시보드 임베딩
- 에러 처리 및 연결 상태 표시

## 동작 흐름

1. 페이지 로드 시 Grafana 서버 연결 확인
2. Grafana API를 사용하여 대시보드 정보 가져오기
3. 선택된 설비와 시간 범위에 따라 대시보드 URL 생성
4. iframe에 대시보드 로드
5. 로딩 상태 및 에러 처리

## 에러 처리

### API 키 미설정
- 에러 메시지: "Grafana API 키가 설정되지 않았습니다"
- 해결: 환경 변수 `VITE_GRAFANA_API_KEY` 설정

### 대시보드 UID 미설정
- 에러 메시지: "Grafana 대시보드 UID가 설정되지 않았습니다"
- 해결: 환경 변수 `VITE_GRAFANA_DASHBOARD_UID` 설정

### 대시보드를 찾을 수 없음
- 에러 메시지: "대시보드를 찾을 수 없습니다"
- 해결: 대시보드 UID가 올바른지 확인

### X-Frame-Options 에러
- 에러 메시지: "X-Frame-Options 정책 위반"
- 해결: Grafana 설정에서 `allow_embedding = true` 설정 후 서버 재시작

## X-Frame-Options 해결 방법

Grafana 설정 파일(`grafana.ini`)에 다음 추가:

```ini
[security]
allow_embedding = true
```

설정 후 Grafana 서버 재시작:

```bash
# Docker
docker restart grafana

# Linux
sudo systemctl restart grafana-server

# Windows
# Grafana 서비스 재시작
```

## 장점

1. **동적 URL 생성**: 설비와 시간 범위에 따라 URL 자동 생성
2. **대시보드 검증**: API를 통해 대시보드 존재 여부 확인
3. **메타데이터 활용**: 대시보드 제목 등 정보 표시 가능
4. **유연성**: 환경 변수만 변경하면 다른 대시보드 사용 가능

## 참고사항

- Grafana API는 CORS 정책을 준수해야 합니다
- API 키는 Viewer 권한만 있어도 대시보드 읽기 가능
- 대시보드 변수(`var-device_id`)는 URL 파라미터로 전달됩니다
- iframe 임베딩을 위해서는 `allow_embedding = true` 설정이 필요합니다

