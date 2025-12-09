# MOBY 백엔드 서비스 구조 개요 (backend/api/services)

> backend/api/services 구조와 각 모듈의 역할 및 개선 제안을 정리한 문서입니다.

---

## 1. 현재 디렉토리 구조 요약

```
backend/api/
├── routes_alerts.py          # 알람 관련 API 라우터
├── routes_sensors.py         # 센서 데이터 관련 API 라우터
└── services/                 # 비즈니스 로직 계층
    ├── alert_engine.py       # 알람 평가 및 페이로드 생성
    ├── alerts_summary.py     # LLM 기반 알람 요약
    ├── anomaly_vector_service.py  # 벡터 기반 이상 탐지
    ├── constants.py          # 상수 정의 (Severity, AlertLevel 등)
    ├── influx_client.py      # InfluxDB 클라이언트
    ├── llm_client.py         # LLM (OpenAI) 클라이언트
    ├── mqtt_client.py        # MQTT 클라이언트
    └── schemas/              # Pydantic 스키마
        ├── alert_schema.py   # 알람 스키마
        ├── sensor_schema.py  # 센서 데이터 스키마
        └── models/
            └── core/
                ├── config.py # 설정 관리
                └── logger.py # 로깅 설정
```

### 계층 구조

- **API 라우터 계층** (`routes_*.py`): FastAPI 엔드포인트 정의, HTTP 요청/응답 처리
- **서비스 계층** (`services/`): 비즈니스 로직, 데이터 처리, 외부 서비스 연동
- **스키마 계층** (`schemas/`): 데이터 모델 정의, 검증
- **코어 계층** (`schemas/models/core/`): 공통 설정, 로깅, 유틸리티

---

## 2. 각 서비스 모듈 요약

### 2.1 API 라우터 모듈

#### `routes_alerts.py`
- **역할**: 알람 관련 REST API 엔드포인트 제공
- **주요 함수**:
  - `get_latest_alert()`: 최신 알람 조회 (`GET /latest`)
- **의존성**: `services.alert_engine.evaluate_alert`, `schemas.alert_schema.AlertResponse`

#### `routes_sensors.py`
- **역할**: 센서 데이터 관련 REST API 엔드포인트 제공
- **주요 함수**:
  - `publish_sensor_data()`: 센서 데이터 MQTT 발행 (`POST /publish`)
- **의존성**: `services.mqtt_client.publish_message`, `schemas.sensor_schema.SensorData`

### 2.2 핵심 서비스 모듈

#### `alert_engine.py`
- **역할**: 알람 평가 및 페이로드 생성의 핵심 엔진
- **주요 기능**:
  - 벡터 기반 이상 탐지 (L2 norm 계산, 심각도 평가)
  - 표준화된 알람 페이로드 생성
  - LLM 요약 생성 (옵션)
- **의존성**: `anomaly_vector_service`, `alerts_summary`, `constants`
- **상세 문서**: `docs/ALERT_ENGINE_DESIGN_REVIEW.md` 참고

#### `anomaly_vector_service.py`
- **역할**: 벡터 norm 계산 및 임계값 기반 이상 탐지
- **주요 함수**:
  - `calculate_vector_norm()`: L2 norm 계산
  - `evaluate_anomaly_vector()`: 단일 임계값 기반 평가
  - `evaluate_anomaly_vector_with_severity()`: 경고/심각 임계값 기반 평가
- **특징**: 순수 함수로 구성, 재사용 가능한 수학적 연산

#### `alerts_summary.py`
- **역할**: LLM을 활용한 알람 요약 생성
- **주요 함수**:
  - `generate_alert_summary()`: 단일 알람 요약 생성
  - `generate_summary_batch()`: 여러 알람 일괄 요약 생성
- **의존성**: `llm_client.summarize_alert`

### 2.3 외부 서비스 클라이언트

#### `mqtt_client.py`
- **역할**: MQTT 브로커와의 통신
- **주요 함수**:
  - `publish_message()`: MQTT 토픽에 메시지 발행
- **설정**: `core.config`에서 MQTT 호스트/포트 가져옴
- **사용 위치**: 센서 데이터 발행, 알람 전송 (예정)

#### `influx_client.py`
- **역할**: InfluxDB 타임시리즈 데이터베이스와의 통신
- **주요 함수**:
  - `write_point()`: 시계열 데이터 포인트 기록
- **설정**: `core.config`에서 InfluxDB URL, 토큰, 조직 정보 가져옴
- **사용 위치**: 센서 데이터 저장

#### `llm_client.py`
- **역할**: OpenAI API를 통한 LLM 호출
- **주요 함수**:
  - `summarize_alert()`: 알람 데이터 요약
- **설정**: `core.config`에서 OpenAI API 키 가져옴
- **모델**: `gpt-4o-mini` 사용

### 2.4 스키마 모듈

#### `alert_schema.py`
- **역할**: 알람 응답 데이터 모델 정의
- **클래스**:
  - `AlertResponse`: API 응답 스키마 (status, message, llm_summary)

#### `sensor_schema.py`
- **역할**: 센서 데이터 모델 정의
- **클래스**:
  - `SensorData`: 센서 데이터 스키마 (device_id, temperature, humidity, vibration, sound)

### 2.5 코어 모듈

#### `constants.py`
- **역할**: 프로젝트 전역 상수 정의
- **주요 정의**:
  - `Severity`: 이상 심각도 enum (NORMAL, WARNING, CRITICAL)
  - `AlertLevel`: UI 레벨 enum (INFO, WARNING, CRITICAL)
  - `SEVERITY_TO_LEVEL_MAP`: 심각도 → 레벨 매핑
  - `Defaults`: 기본값 (SENSOR_ID, SOURCE, MESSAGE 등)
  - `ValidationMessages`: 검증 에러 메시지

#### `schemas/models/core/config.py`
- **역할**: 애플리케이션 설정 관리
- **주요 설정**:
  - MQTT 호스트/포트
  - InfluxDB URL, 토큰, 조직
  - OpenAI API 키
- **방식**: Pydantic `BaseSettings` 사용, 환경 변수에서 로드

---

## 3. 개선 제안 요약

### 3.1 디렉토리 구조 개선

**현재 상태**:
- `services/schemas/` 구조가 중첩되어 혼란 가능
- `constants.py`가 서비스 디렉토리에 위치

**개선 제안**:
- `backend/api/core/` 디렉토리 생성하여 공통 설정, 상수, 유틸리티 통합
- `backend/api/schemas/` 디렉토리로 스키마를 상위 레벨로 이동
- `backend/api/services/`는 순수 비즈니스 로직만 유지

```
backend/api/
├── core/
│   ├── config.py
│   ├── constants.py
│   └── utils.py
├── schemas/
│   ├── alert_schema.py
│   └── sensor_schema.py
└── services/
    ├── alert_engine.py
    ├── alerts_summary.py
    └── ...
```

### 3.2 모듈 간 의존성 관리

**현재 상태**:
- 일부 서비스가 직접 import하여 의존성 주입 부족
- 테스트 시 mocking이 어려움

**개선 제안**:
- 의존성 주입 패턴 도입 (FastAPI의 `Depends` 활용)
- 인터페이스 추상화를 통한 느슨한 결합

### 3.3 에러 처리 표준화

**현재 상태**:
- 각 모듈마다 에러 처리 방식이 일관되지 않음
- `None` 반환 vs 예외 발생 혼재

**개선 제안**:
- 커스텀 예외 클래스 정의 (`backend/api/core/exceptions.py`)
- 에러 처리 표준 가이드라인 문서화

### 3.4 로깅 개선

**현재 상태**:
- `alerts_summary.py`에서 `print` 사용
- 로깅 레벨과 포맷 통일성 부족

**개선 제안**:
- 모든 모듈에서 `logging` 모듈 통일 사용
- `core/logger.py`를 통한 중앙 집중 로깅 설정

### 3.5 타입 힌팅 완성도

**현재 상태**:
- 일부 함수에 타입 힌팅 누락
- `# type: ignore` 주석 존재

**개선 제안**:
- 모든 함수에 완전한 타입 힌팅 추가
- mypy 정적 타입 검사 도입

### 3.6 테스트 커버리지

**현재 상태**:
- 테스트 파일이 없음

**개선 제안**:
- `backend/tests/` 디렉토리 생성
- pytest 설정 및 단위 테스트 작성
- CI/CD 파이프라인에 테스트 통합

### 3.7 API 문서화

**현재 상태**:
- FastAPI 라우터에 문서 문자열 부족
- API 스펙 문서화 미흡

**개선 제안**:
- FastAPI의 자동 문서화 기능 활용 (`/docs` 엔드포인트)
- 각 엔드포인트에 상세한 docstring 추가
- OpenAPI 스펙 자동 생성 및 관리

### 3.8 환경 설정 관리

**현재 상태**:
- `core/config.py`에서 기본값이 하드코딩 ("your-api-key")

**개선 제안**:
- `.env` 파일을 통한 환경 변수 관리
- 설정 검증 및 기본값 처리 개선
- 환경별 설정 분리 (dev, staging, prod)

---

## 4. 모듈 간 데이터 흐름

```
센서 데이터 흐름:
MQTT → routes_sensors.py → mqtt_client.py → MQTT Broker
                                      ↓
                            routes_sensors.py → influx_client.py → InfluxDB

알람 생성 흐름:
routes_alerts.py → alert_engine.py → anomaly_vector_service.py
                                  ↓
                            alerts_summary.py → llm_client.py → OpenAI API
                                  ↓
                            routes_alerts.py → AlertResponse (JSON)
```

---

## 5. 다음 단계

- [ ] 디렉토리 구조 리팩토링 (`core/`, `schemas/` 분리)
- [ ] 의존성 주입 패턴 도입
- [ ] 커스텀 예외 클래스 정의
- [ ] 로깅 표준화
- [ ] 단위 테스트 작성
- [ ] API 문서화 강화
- [ ] 환경 설정 개선

---

**문서 최종 업데이트**: 2025-11-17
