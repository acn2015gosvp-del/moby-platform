# InfluxDB Cloud → Grafana 대시보드 연결 가이드

## 완료된 작업

### 1. InfluxDB Cloud 연결 ✅
- **설정 완료**: `INFLUX_URL`, `INFLUX_TOKEN`, `INFLUX_ORG`, `INFLUX_BUCKET`
- **연결 상태**: 정상 작동 확인
- **데이터 조회**: InfluxDB에서 센서 데이터 조회 기능 구현

### 2. 백엔드 설비 정보 개선 ✅
- **파일**: `backend/api/routes_sensors.py`
- **기능**:
  - InfluxDB에서 각 device별 센서 수 계산
  - 알림 데이터베이스에서 각 device별 알림 수 조회
  - 가동률 계산 (최근 24시간 데이터 기반)
  - 설비 상태 결정 (긴급/경고/정상/오프라인)
  - 설비 이름 및 카테고리 자동 매핑

### 3. 프론트엔드 Grafana 연결 ✅
- **컴포넌트**: `EquipmentCard.tsx`, `EquipmentList.tsx`
- **기능**: 설비 카드 클릭 시 Grafana 대시보드로 이동
- **라우터**: `/equipment` 경로 추가
- **사이드바**: "설비 목록" 메뉴 추가

## 설정 방법

### 1. Grafana URL 설정

#### 프론트엔드 환경 변수
프론트엔드 루트에 `.env` 파일 생성 (또는 `vite.config.ts`에서 설정):

```env
# Grafana URL (프론트엔드)
VITE_GRAFANA_URL=http://localhost:3000
```

또는 Grafana Cloud를 사용하는 경우:
```env
VITE_GRAFANA_URL=https://your-grafana-instance.grafana.net
```

#### 백엔드 환경 변수 (선택사항)
```env
# Grafana 설정 (백엔드, 선택사항)
GRAFANA_URL=http://localhost:3000
GRAFANA_API_KEY=your-grafana-api-key-here
```

### 2. Grafana 대시보드 설정

#### 대시보드 UID 매핑
현재는 `device_id`를 `dashboardUID`로 사용합니다. 

**Grafana에서 대시보드 생성 시:**
1. 대시보드 UID를 `device_id`와 동일하게 설정
2. 예: `device_id`가 `sensor_001`이면 대시보드 UID도 `sensor_001`

**또는 데이터베이스에 매핑 테이블 생성 (향후 개선):**
```sql
CREATE TABLE device_dashboard_mapping (
    device_id VARCHAR(255) PRIMARY KEY,
    dashboard_uid VARCHAR(255) NOT NULL,
    grafana_url VARCHAR(500)
);
```

### 3. Grafana 변수 설정

Grafana 대시보드에서 `device_id` 변수를 사용하려면:

1. **대시보드 설정** → **Variables** → **New variable**
2. **Variable name**: `device_id`
3. **Variable type**: `Query` 또는 `Custom`
4. **Query**: InfluxDB에서 device_id 목록 조회

또는 URL 파라미터로 전달:
- 현재 구현: `?var-device_id=sensor_001`
- Grafana에서 `$device_id` 변수 사용

## 사용 방법

### 1. 설비 목록 페이지 접근
- 사이드바에서 "설비 목록" 클릭
- 또는 `/equipment` URL로 직접 접근

### 2. Grafana 대시보드 열기
- 설비 카드 클릭
- 새 창에서 Grafana 대시보드가 열림

### 3. 대시보드 URL 형식
```
http://localhost:3000/d/{dashboardUID}/view?
  orgId=1&
  from=now-6h&
  to=now&
  refresh=30s&
  kiosk=tv&
  var-device_id={device_id}
```

## 데이터 흐름

```
InfluxDB Cloud
    ↓
백엔드 API (/sensors/status)
    ↓
- InfluxDB 쿼리: 센서 데이터 조회
- 알림 DB 쿼리: 알림 수 조회
- 계산: 센서 수, 가동률, 상태
    ↓
프론트엔드 (EquipmentList)
    ↓
EquipmentCard 클릭
    ↓
Grafana 대시보드 (새 창)
```

## 개선 사항

### 완료된 개선
- ✅ InfluxDB에서 실제 센서 데이터 조회
- ✅ 알림 수 계산
- ✅ 가동률 계산
- ✅ 설비 상태 자동 결정
- ✅ 설비 이름 및 카테고리 매핑

### 향후 개선 사항
1. **설비 정보 데이터베이스**: 설비 이름, 카테고리, Grafana UID를 데이터베이스에 저장
2. **대시보드 자동 생성**: Grafana API를 사용하여 대시보드 자동 생성
3. **실시간 업데이트**: WebSocket을 통한 실시간 설비 상태 업데이트
4. **필터링 및 검색**: 설비 목록 필터링 및 검색 기능

## 문제 해결

### Grafana 대시보드가 열리지 않는 경우
1. **Grafana URL 확인**: `VITE_GRAFANA_URL` 환경 변수 확인
2. **대시보드 UID 확인**: `device_id`와 `dashboardUID`가 일치하는지 확인
3. **CORS 설정**: Grafana에서 CORS 허용 확인

### 설비 정보가 표시되지 않는 경우
1. **InfluxDB 연결 확인**: 백엔드 로그에서 InfluxDB 쿼리 오류 확인
2. **데이터 존재 확인**: InfluxDB에 실제 센서 데이터가 있는지 확인
3. **캐시 확인**: 백엔드 캐시 TTL이 30초이므로 최대 30초 후 반영

## 참고 파일

- `backend/api/routes_sensors.py` - 센서 상태 조회 API
- `backend/api/services/influx_client.py` - InfluxDB 클라이언트
- `frontend/src/pages/EquipmentList.tsx` - 설비 목록 페이지
- `frontend/src/components/EquipmentCard.tsx` - 설비 카드 컴포넌트
- `frontend/src/utils/grafana.ts` - Grafana URL 빌더
- `frontend/src/components/layout/Sidebar.tsx` - 사이드바 메뉴

