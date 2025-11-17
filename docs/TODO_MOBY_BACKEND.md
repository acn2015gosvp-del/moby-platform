# MOBY Backend TODO 리스트 (from Gemini + Cursor 리뷰)

> 이 문서는 ARCHITECTURE_OVERVIEW, BACKEND_SERVICES_OVERVIEW, ALERT_ENGINE_DESIGN_REVIEW, DATA_PIPELINE_MQTT_INFLUX_GRAFANA 에서 나온 "개선 포인트"만 모은 실행용 체크리스트입니다.

**최종 업데이트**: 2025-11-17

---

## 1. 아키텍처 / 구조

- [ ] Edge / Backend / Data / Visualization 레이어별 책임을 docs에 더 명확히 구분하기
- [ ] 디렉토리 구조 리팩토링: `backend/api/core/` 디렉토리 생성하여 공통 설정, 상수, 유틸리티 통합
- [ ] 디렉토리 구조 리팩토링: `backend/api/schemas/` 디렉토리로 스키마를 상위 레벨로 이동
- [ ] `backend/api/services/`는 순수 비즈니스 로직만 유지하도록 정리

---

## 2. Backend Services (api/services/schemas/core)

- [ ] 서비스 모듈별 책임 범위 정리 문서 추가 (완료: `BACKEND_SERVICES_OVERVIEW.md`)
- [ ] 공통 예외/로그 유틸을 `core/utils.py`로 분리
- [ ] 의존성 주입 패턴 도입 (FastAPI의 `Depends` 활용)
- [ ] 커스텀 예외 클래스 정의 (`backend/api/core/exceptions.py`)
- [ ] 에러 처리 표준 가이드라인 문서화

---

## 3. Alert Engine / Anomaly Vector

- [ ] `alert_engine` + `anomaly_vector_service`에 대해 pytest 단위 테스트 추가
- [ ] LLM 요약 실패 시 fallback 메시지/플로우 정의
- [ ] severity ↔ level 매핑 규칙을 constants로 고정하고 문서화 (완료: `constants.py`에 정의됨)
- [ ] 임계값 처리 로직 명확화 (Pydantic v2의 `Field(one_of=...)` 활용 검토)
- [ ] 세밀한 에러 처리: `Either` 타입이나 커스텀 `Result` 객체 도입 검토
- [ ] 의존성 주입을 통한 테스트 가능성 향상
- [ ] `_now_iso()` 유틸리티 함수를 공통 유틸리티 모듈로 이동
- [ ] 알람 ID 생성 전략 개선 (UUID 사용 검토)
- [ ] LLM 요약 실패 정보를 알람 페이로드에 기록 (`meta` 필드 또는 `llm_error` 필드)

---

## 4. 데이터 파이프라인 / 운영

- [ ] MQTT → FastAPI → InfluxDB 구간에서 장애 시 재시도/로그 전략 정의
- [ ] MQTT 클라이언트 재연결 로직 구현 (exponential backoff)
- [ ] InfluxDB 쓰기 실패 시 임시 데이터 버퍼링 및 재전송 로직
- [ ] Grafana 대시보드 UID, 변수 구조를 docs/GRAFANA.md 쪽과 동기화
- [ ] 파이프라인 헬스체크(간단한 status API or dashboard) 설계 및 구현
- [ ] MQTT 메시지 큐잉 및 재시도 로직 구현
- [ ] InfluxDB 쓰기 배치 처리 최적화
- [ ] 데이터 파이프라인 모니터링 대시보드 구축

---

## 5. 로깅 및 모니터링

- [ ] `alerts_summary.py`에서 `print` 제거하고 `logging` 모듈 사용
- [ ] 모든 모듈에서 로깅 표준화 (레벨, 포맷 통일)
- [ ] `core/logger.py`를 통한 중앙 집중 로깅 설정

---

## 6. 타입 힌팅 및 코드 품질

- [ ] 모든 함수에 완전한 타입 힌팅 추가
- [ ] `alert_engine.py`의 `# type: ignore` 주석 제거
- [ ] mypy 정적 타입 검사 도입

---

## 7. API 문서화

- [ ] FastAPI 라우터에 상세한 docstring 추가
- [ ] FastAPI의 자동 문서화 기능 활용 (`/docs` 엔드포인트 확인)
- [ ] OpenAPI 스펙 자동 생성 및 관리

---

## 8. 환경 설정 관리

- [ ] `.env` 파일을 통한 환경 변수 관리
- [ ] `core/config.py`의 하드코딩된 기본값 제거 ("your-api-key" 등)
- [ ] 설정 검증 및 기본값 처리 개선
- [ ] 환경별 설정 분리 (dev, staging, prod)

---

## 9. 테스트 / 품질

- [ ] pytest 기본 설정 추가 (`backend/tests/` 디렉토리 생성)
- [ ] `AlertInputModel` 검증 로직 단위 테스트
- [ ] `process_alert` 함수의 다양한 임계값 시나리오 테스트
- [ ] LLM 요약 실패 시 fallback 동작 테스트
- [ ] 에러 처리 경로 테스트
- [ ] 통합 테스트 (end-to-end)
- [ ] CI에서 테스트 자동 실행 (GitHub Actions로 나중에 연결)

---

## 10. 성능 최적화

- [ ] InfluxDB 배치 쓰기 최적화
- [ ] FastAPI의 async/await 활용하여 동시성 향상
- [ ] MQTT 메시지 압축 검토 (필요 시)
- [ ] InfluxDB 보존 정책 설정
- [ ] Grafana 쿼리 최적화

---

**참고 문서**:
- `docs/ALERT_ENGINE_DESIGN_REVIEW.md`: Alert Engine 상세 리뷰
- `docs/BACKEND_SERVICES_OVERVIEW.md`: 백엔드 서비스 구조 개요
- `docs/DATA_PIPELINE_MQTT_INFLUX_GRAFANA.md`: 데이터 파이프라인 상세 설명
