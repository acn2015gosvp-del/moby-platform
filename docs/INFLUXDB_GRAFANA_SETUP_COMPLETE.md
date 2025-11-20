# InfluxDB Cloud → Grafana 대시보드 연결 완료

## ✅ 완료된 작업

### 1. InfluxDB Cloud 연결 ✅
- **설정 완료**: 
  - `INFLUX_URL`: `https://us-east-1-1.aws.cloud2.influxdata.com`
  - `INFLUX_TOKEN`: 실제 토큰 설정됨
  - `INFLUX_ORG`: `wise`
  - `INFLUX_BUCKET`: `sensor_data_v2`
- **연결 상태**: 정상 작동 확인

### 2. 백엔드 설비 정보 개선 ✅
**파일**: `backend/api/routes_sensors.py`

**구현된 기능**:
- ✅ InfluxDB에서 각 device별 센서 수 계산 (최근 1시간 데이터 기반)
- ✅ 알림 데이터베이스에서 각 device별 알림 수 조회 (최근 24시간)
- ✅ 가동률 계산 (최근 24시간 중 데이터가 있는 시간 비율)
- ✅ 설비 상태 자동 결정:
  - `긴급`: Critical 알림이 있는 경우
  - `경고`: Warning 알림이 있는 경우
  - `정상`: 활성 센서이고 알림이 없는 경우
  - `오프라인`: 비활성 센서
- ✅ 설비 이름 및 카테고리 자동 매핑:
  - `conveyor`, `belt` → "컨베이어 벨트", "운송 시스템"
  - `cnc`, `machine` → "CNC 머신", "가공 장비"
  - `robot`, `arm` → "로봇 팔", "자동화 설비"
  - 기타 → "설비 {device_id}", "산업 설비"

### 3. 프론트엔드 Grafana 연결 ✅
**구현된 컴포넌트**:
- ✅ `EquipmentCard.tsx`: 설비 카드 컴포넌트 (Grafana 연결 기능 포함)
- ✅ `EquipmentList.tsx`: 설비 목록 페이지
- ✅ `grafana.ts`: Grafana URL 빌더 유틸리티
- ✅ 라우터: `/equipment` 경로 추가
- ✅ 사이드바: "설비 목록" 메뉴 추가

**기능**:
- 설비 카드 클릭 시 Grafana 대시보드로 이동 (새 창)
- Grafana URL 자동 생성:
  - 기본 URL: `VITE_GRAFANA_URL` 환경 변수 또는 `http://localhost:3000`
  - 대시보드 UID: `device_id` 사용
  - 변수 전달: `var-device_id={device_id}`
  - Kiosk 모드: `kiosk=tv`
  - 시간 범위: `from=now-6h`, `to=now`
  - 자동 새로고침: `refresh=30s`

## 설정 방법

### 1. Grafana URL 설정 (프론트엔드)

프론트엔드 루트에 `.env` 파일 생성:

```env
# Grafana URL
VITE_GRAFANA_URL=http://localhost:3000
```

또는 Grafana Cloud를 사용하는 경우:
```env
VITE_GRAFANA_URL=https://your-instance.grafana.net
```

**참고**: Vite는 `.env` 파일을 자동으로 읽습니다. 변경 후 프론트엔드 서버를 재시작하세요.

### 2. Grafana 대시보드 설정

#### 대시보드 UID 매핑
현재는 `device_id`를 `dashboardUID`로 사용합니다.

**Grafana에서 대시보드 생성 시:**
1. 대시보드 설정 → General → UID
2. UID를 `device_id`와 동일하게 설정
   - 예: `device_id`가 `sensor_001`이면 대시보드 UID도 `sensor_001`

#### 변수 설정 (선택사항)
Grafana 대시보드에서 `device_id` 변수를 사용하려면:

1. **대시보드 설정** → **Variables** → **New variable**
2. **Variable name**: `device_id`
3. **Variable type**: `Query` 또는 `Custom`
4. **Query**: InfluxDB에서 device_id 목록 조회

또는 URL 파라미터로 자동 전달됨:
- 현재 구현: `?var-device_id=sensor_001`
- Grafana에서 `$device_id` 변수 사용

## 사용 방법

### 1. 설비 목록 페이지 접근
- 사이드바에서 "🏭 설비 목록" 클릭
- 또는 URL: `http://localhost:5173/equipment`

### 2. Grafana 대시보드 열기
- 설비 카드 클릭
- 새 창에서 Grafana 대시보드가 열림

### 3. 대시보드 URL 예시
```
http://localhost:3000/d/sensor_001/view?
  orgId=1&
  from=now-6h&
  to=now&
  refresh=30s&
  kiosk=tv&
  var-device_id=sensor_001
```

## 데이터 흐름

```
InfluxDB Cloud (센서 데이터)
    ↓
백엔드 API (/sensors/status)
    ├─ InfluxDB 쿼리: 센서 데이터 조회
    │  ├─ 센서 수 계산
    │  ├─ 가동률 계산
    │  └─ 최근 업데이트 시간
    ├─ 알림 DB 쿼리: 알림 수 조회
    │  ├─ 전체 알림 수
    │  ├─ Warning 알림 수
    │  └─ Critical 알림 수
    └─ 설비 정보 생성
       ├─ 상태 결정 (긴급/경고/정상/오프라인)
       ├─ 이름 및 카테고리 매핑
       └─ Grafana UID 설정
    ↓
프론트엔드 (EquipmentList)
    ├─ 설비 목록 표시
    └─ EquipmentCard 클릭
    ↓
Grafana 대시보드 (새 창)
    └─ 실시간 센서 데이터 시각화
```

## API 응답 예시

### GET /sensors/status

```json
{
  "success": true,
  "data": {
    "status": "ok",
    "count": 5,
    "active": 5,
    "inactive": 0,
    "devices": [
      {
        "device_id": "sensor_001",
        "name": "Sensor 001",
        "category": "산업 설비",
        "dashboardUID": "sensor_001",
        "status": "정상",
        "sensorCount": 4,
        "alertCount": 0,
        "operationRate": 95.8,
        "lastUpdated": "2025-01-15T10:30:00Z"
      }
    ]
  },
  "message": "Sensor status retrieved successfully"
}
```

## 문제 해결

### 설비 목록이 비어있는 경우
1. **InfluxDB 데이터 확인**: InfluxDB에 실제 센서 데이터가 있는지 확인
2. **백엔드 로그 확인**: InfluxDB 쿼리 오류 확인
3. **캐시 확인**: 백엔드 캐시 TTL이 30초이므로 최대 30초 후 반영

### Grafana 대시보드가 열리지 않는 경우
1. **Grafana URL 확인**: `VITE_GRAFANA_URL` 환경 변수 확인
2. **대시보드 UID 확인**: `device_id`와 Grafana 대시보드 UID가 일치하는지 확인
3. **Grafana 서버 확인**: Grafana가 실행 중인지 확인
4. **CORS 설정**: Grafana에서 CORS 허용 확인

### 센서 수가 0으로 표시되는 경우
1. **InfluxDB 데이터 확인**: 최근 1시간 내 데이터가 있는지 확인
2. **필드 이름 확인**: InfluxDB에 `temperature`, `humidity`, `vibration`, `sound` 필드가 있는지 확인
3. **백엔드 로그 확인**: InfluxDB 쿼리 오류 확인

## 다음 단계 (선택사항)

### 향후 개선 사항
1. **설비 정보 데이터베이스**: 설비 이름, 카테고리, Grafana UID를 데이터베이스에 저장
2. **대시보드 자동 생성**: Grafana API를 사용하여 대시보드 자동 생성
3. **실시간 업데이트**: WebSocket을 통한 실시간 설비 상태 업데이트
4. **필터링 및 검색**: 설비 목록 필터링 및 검색 기능
5. **설비 상세 페이지**: 각 설비의 상세 정보 및 히스토리 표시

## 참고 파일

- `backend/api/routes_sensors.py` - 센서 상태 조회 API (설비 정보 포함)
- `backend/api/services/influx_client.py` - InfluxDB 클라이언트
- `backend/api/services/alert_storage.py` - 알림 데이터베이스 조회
- `frontend/src/pages/EquipmentList.tsx` - 설비 목록 페이지
- `frontend/src/components/EquipmentCard.tsx` - 설비 카드 컴포넌트
- `frontend/src/utils/grafana.ts` - Grafana URL 빌더
- `frontend/src/components/layout/Sidebar.tsx` - 사이드바 메뉴
- `frontend/src/router.tsx` - 라우터 설정

## 테스트 방법

1. **백엔드 서버 실행**
   ```bash
   python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **프론트엔드 서버 실행**
   ```bash
   cd frontend
   npm run dev
   ```

3. **설비 목록 페이지 접근**
   - http://localhost:5173/equipment

4. **Grafana 대시보드 테스트**
   - 설비 카드 클릭
   - 새 창에서 Grafana 대시보드가 열리는지 확인

