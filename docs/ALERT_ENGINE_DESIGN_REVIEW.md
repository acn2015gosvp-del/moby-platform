# Alert Engine 설계 리뷰 및 리팩토링 메모

> 이 문서는 `alert_engine.py`를 분석하여 정리한 설계 리뷰입니다.

---

## 1. Alert Engine 역할 요약

`alert_engine.py` 모듈은 MOBY 플랫폼의 핵심 서비스 중 하나로, 다음과 같은 역할을 담당합니다:

- **벡터 기반 이상 탐지**: `anomaly_vector_service`를 이용하여 센서 데이터 벡터의 L2 norm을 계산하고, 임계값 기준으로 이상 여부 및 심각도(warning/critical)를 평가합니다.

- **알람 페이로드 생성**: 이상이 탐지된 경우, 프론트엔드/백엔드에서 공통으로 사용할 수 있는 표준화된 알람 페이로드(`AlertPayloadModel`)를 생성합니다.

- **LLM 요약 생성** (선택): `alerts_summary` 서비스를 통해 이상 탐지 상황을 LLM으로 요약하여 사용자 친화적인 메시지를 생성할 수 있습니다.

- **실제 전송 분리**: 이 모듈은 알람 평가 및 페이로드 생성까지만 담당하며, 실제 슬랙/이메일/WebSocket 전송은 notifier 등 상위 레이어에서 처리합니다.

### 핵심 함수

- `process_alert(alert_data: Dict[str, Any]) -> Optional[AlertPayloadModel]`: 알람 평가 및 페이로드 생성의 핵심 로직
- `evaluate_alert(alert_data: Dict[str, Any]) -> Optional[AlertPayloadModel]`: 기존 코드 호환을 위한 래퍼 함수

---

## 2. 설계 상 강점

### 2.1 명확한 관심사 분리 (Separation of Concerns)

- 벡터 norm 계산과 threshold 판단 로직이 `anomaly_vector_service`로 분리되어 재사용 가능
- LLM 요약 로직이 `alerts_summary` 서비스로 분리되어 독립적으로 테스트 및 개선 가능
- 알람 전송 로직이 상위 레이어로 분리되어 단일 책임 원칙 준수

### 2.2 견고한 입력 검증 (Robust Input Validation)

- Pydantic `AlertInputModel`을 사용하여 모든 입력 데이터의 타입 및 유효성 검증
- 벡터가 비어있지 않은지, threshold가 제공되었는지 등을 사전에 검증
- 검증 실패 시 명확한 에러 메시지 제공

### 2.3 구조화된 출력 (Structured Output)

- `AlertPayloadModel`과 `AlertDetailsModel`을 통해 생성되는 알람 페이로드가 타입 안전하고 구조화됨
- UI나 다른 서비스에서 알람 데이터를 일관된 형식으로 처리 가능

### 2.4 유연한 이상 평가 (Flexible Anomaly Evaluation)

- 단일 `threshold` 또는 `warning_threshold`/`critical_threshold` 쌍 모두 지원
- 심각도 기반 평가와 단순 이상/정상 평가를 자동으로 선택

### 2.5 선택적 LLM 통합 (Optional LLM Integration)

- LLM 요약 기능이 선택적으로 동작 (`enable_llm_summary` 플래그)
- LLM 요약 생성 실패 시에도 알람 처리는 계속 진행 (graceful degradation)

### 2.6 효과적인 로깅 (Effective Logging)

- Python `logging` 모듈을 사용하여 디버깅과 모니터링에 필요한 정보 기록
- 검증 실패, 벡터 평가 오류, 알람 생성 완료 등 주요 이벤트 로깅

### 2.7 하위 호환성 (Backward Compatibility)

- `evaluate_alert` 함수를 제공하여 기존 코드와의 호환성 유지
- 내부적으로는 개선된 `process_alert` 함수 사용

### 2.8 상수 활용 (Usage of Constants)

- `constants.py`에 기본값과 검증 메시지를 중앙 집중 관리
- 코드의 가독성과 유지보수성 향상

---

## 3. 개선 포인트 요약

### 3.1 임계값 처리 로직 명확화

**현재 상태**: 
- `AlertInputModel`의 `check_thresholds` validator가 단일 threshold 또는 쌍 threshold 모두 허용
- `process_alert` 함수에서 두 가지 방식이 혼재되어 사용

**개선 제안**:
- Pydantic v2의 `Field(one_of=...)` 기능을 활용하거나, 더 명확한 타입 정의로 임계값 처리 방식을 명확히 구분
- `evaluate_anomaly_vector` 호출 시 `# type: ignore` 주석 제거를 위한 코드 구조 개선

### 3.2 세밀한 에러 처리

**현재 상태**: 
- 검증 실패나 벡터 평가 오류 시 모두 `None`을 반환
- 구체적인 에러 유형(입력 데이터 오류, 벡터 평가 오류, 네트워크 문제 등) 구분이 어려움

**개선 제안**:
- `Either` 타입이나 커스텀 `Result` 객체를 반환하여 발생한 에러 유형을 명시적으로 처리
- 특정 에러 상황에 대한 세부 정보 제공

### 3.3 의존성 주입 / 테스트 가능성

**현재 상태**: 
- `anomaly_vector_service`와 `alerts_summary` 모듈이 직접 import되어 사용
- 단위 테스트 시 의존성을 mocking하기 어려움

**개선 제안**:
- 함수 파라미터로 의존성을 주입하는 방식 또는 의존성 주입 패턴을 사용하여 테스트 가능성 향상

### 3.4 `_now_iso()` 유틸리티 함수 위치

**현재 상태**: 
- `_now_iso()` 함수가 `alert_engine.py` 내부에 정의되어 있음

**개선 제안**:
- 공통 유틸리티 모듈(`utils` 모듈)로 이동하여 재사용 가능하도록 개선

### 3.5 알람 ID 생성 전략

**현재 상태**: 
- `alert_id`가 `_now_iso()`를 기본으로 생성
- 동시에 여러 알람이 생성되는 경우 고유성 문제 가능성

**개선 제안**:
- UUID(Universally Unique Identifier) 사용하여 고유성 보장

### 3.6 LLM 요약 실패 정보

**현재 상태**: 
- `generate_alert_summary`가 실패하면 `llm_summary` 필드만 `None`으로 설정
- 실패 원인 추적이 어려움

**개선 제안**:
- LLM 실패 정보를 알람 페이로드에 기록(예: `meta` 필드 또는 별도 `llm_error` 필드)

### 3.7 상수 위치

**현재 상태**: 
- `constants.py`가 현재 서비스 디렉토리(`backend/api/services/`)에서 직접 관리됨

**개선 제안**:
- 프로젝트 전체 구조를 고려하여 `backend/schemas/` 또는 `backend/core/` 등 중앙 위치로 이동 검토

---

## 4. 코드 구조 분석

### 4.1 주요 클래스 및 모델

```python
# 입력 검증 모델
AlertInputModel
  - vector: List[float]
  - threshold: Optional[float]
  - warning_threshold: Optional[float]
  - critical_threshold: Optional[float]
  - enable_llm_summary: bool

# 페이로드 모델
AlertPayloadModel
  - id: str
  - level: str (info/warning/critical)
  - message: str
  - llm_summary: Optional[str]
  - sensor_id: str
  - details: AlertDetailsModel

AlertDetailsModel
  - vector: List[float]
  - norm: float
  - severity: str
  - threshold 정보
  - meta: Dict[str, Any]
```

### 4.2 처리 흐름

1. **입력 검증**: `AlertInputModel`로 입력 데이터 검증
2. **벡터 평가**: 
   - `warning_threshold`/`critical_threshold`가 있으면 → `evaluate_anomaly_vector_with_severity`
   - 단일 `threshold`만 있으면 → `evaluate_anomaly_vector`
3. **이상 판단**: `is_anomaly`가 `True`이고 `severity != NORMAL`인 경우만 알람 생성
4. **페이로드 생성**: `AlertPayloadModel` 생성
5. **LLM 요약** (선택): `enable_llm_summary`가 `True`이면 LLM 요약 생성

### 4.3 의존성 모듈

- `anomaly_vector_service`: 벡터 norm 계산 및 임계값 평가
- `alerts_summary`: LLM 요약 생성
- `constants`: 상수 정의 (Severity, AlertLevel, 기본값 등)

---

## 5. 테스트 권장 사항

- [ ] `AlertInputModel` 검증 로직 단위 테스트
- [ ] `process_alert` 함수의 다양한 임계값 시나리오 테스트
- [ ] LLM 요약 실패 시 fallback 동작 테스트
- [ ] 에러 처리 경로 테스트
- [ ] 통합 테스트 (end-to-end)

---

**문서 최종 업데이트**: 2025-11-17
