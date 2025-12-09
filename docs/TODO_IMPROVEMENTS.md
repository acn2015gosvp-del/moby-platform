# MOBY Platform 개선 포인트 통합 TODO

> 이 문서는 여러 아키텍처/리뷰 문서에서 추출한 개선점과 TODO 항목입니다.
> Gemini CLI 정리 과정에서 오류가 발생하여 원본 추출 내용을 그대로 표시합니다.
> 
> **최종 업데이트**: 2025-11-17 01:50:59
> 
> **생성 스크립트**: ./scripts/extract_todos.ps1
> 
> **오류**: Loaded cached credentials.

---


---
## 📄 출처: BACKEND_SERVICES_OVERVIEW.md
## 3. Gemini 개선 제안 요약

(여기에 Gemini 답변 중 “개선할 수 있다” 라고 한 부분만 정리해서 붙여넣기)

---




---
## 📄 출처: ALERT_ENGINE_DESIGN_REVIEW.md
## 3. 개선 포인트 요약

- (Gemini가 “개선점”으로 언급한 항목만 불릿으로 모아서 정리)
- ex) 예외 처리 보강, 로그 레벨 조정, 테스트 부족 등

---




---
## 📄 출처: TODO_MOBY_BACKEND.md
# MOBY Backend TODO 리스트 (from Gemini + Cursor 리뷰)

> 이 문서는 ARCHITECTURE_OVERVIEW, BACKEND_SERVICES_OVERVIEW, ALERT_ENGINE_DESIGN_REVIEW, DATA_PIPELINE_MQTT_INFLUX_GRAFANA 에서 나온 "개선 포인트"만 모은 실행용 체크리스트입니다.

---

## 1. 아키텍처 / 구조

- [ ] (예시) Edge / Backend / Data / Visualization 레이어별 책임을 docs에 더 명확히 구분하기
- [ ] (예시) InfluxDB + PostgreSQL 역할 구분 문서화

※ 위 예시는 지우고, ARCHITECTURE 문서에서 Gemini가 말한 개선점을 여기에 옮겨 적기.

---

## 2. Backend Services (api/services/schemas/core)

- [ ] (예시) services 모듈별 책임 범위 정리 문서 추가
- [ ] (예시) 공통 예외/로그 유틸을 core/utils로 분리

---

## 3. Alert Engine / Anomaly Vector

- [ ] alert_engine + anomaly_vector_service 에 대해 pytest 단위 테스트 추가
- [ ] LLM 요약 실패 시 fallback 메시지/플로우 정의
- [ ] severity ↔ level 매핑 규칙을 constants로 고정하고 문서화

---

## 4. 데이터 파이프라인 / 운영

- [ ] MQTT → FastAPI → InfluxDB 구간에서 장애 시 재시도/로그 전략 정의
- [ ] Grafana 대시보드 UID, 변수 구조를 docs/GRAFANA.md 쪽과 동기화
- [ ] 파이프라인 헬스체크(간단한 status API or dashboard) 설계

---

## 5. 테스트 / 품질

- [ ] pytest 기본 설정 추가 (backend/tests)
- [ ] CI에서 테스트 자동 실행 (GitHub Actions로 나중에 연결)


