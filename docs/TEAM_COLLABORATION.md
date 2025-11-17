# 👥 팀 협업 전략 가이드

두 명이서 효율적으로 협업하기 위한 전략과 워크플로우입니다.

## 🎯 업무 분담 전략

### 전략 1: 기능별 분담 (추천) ⭐

**장점**: 충돌 최소화, 독립적 개발 가능, 책임 명확

#### 분담 예시:

**👤 개발자 A (Backend Core / Data Pipeline)**
- ✅ Alert Engine 개발 및 개선
- ✅ InfluxDB 클라이언트 및 데이터 파이프라인
- ✅ MQTT 클라이언트 및 메시지 처리
- ✅ API 라우터 및 엔드포인트
- ✅ 데이터 검증 및 스키마 관리

**👤 개발자 B (Frontend / Integration / Testing)**
- ✅ React Frontend 개발 (Vite)
- ✅ WebSocket 클라이언트 구현
- ✅ UI 컴포넌트 (AlertToast, AlertsPanel)
- ✅ 테스트 코드 작성 (pytest)
- ✅ API 통합 및 문서화

---

### 전략 2: 수직 분담 (Feature-based)

**장점**: 기능 단위로 완전한 책임, 빠른 피드백 루프

#### 분담 예시:

**👤 개발자 A: "Alert System" 담당**
- Alert Engine 전체
- Alert API 엔드포인트
- Alert Frontend UI
- Alert 테스트

**👤 개발자 B: "Sensor Data Pipeline" 담당**
- Sensor API 엔드포인트
- MQTT → InfluxDB 파이프라인
- Sensor Frontend UI
- 데이터 시각화

---

### 전략 3: 레이어별 분담

**장점**: 전문성 집중, 깊이 있는 개발

#### 분담 예시:

**👤 개발자 A: Backend Specialist**
- 모든 Backend 서비스
- 데이터베이스 및 인프라
- API 설계 및 구현

**👤 개발자 B: Frontend Specialist**
- 모든 Frontend 개발
- UI/UX 디자인
- 사용자 경험 최적화

---

## 📋 추천: 하이브리드 접근법

현재 프로젝트 상태를 고려한 **실용적인 분담**:

### Phase 1: 현재 (Backend 중심)

**👤 개발자 A**
- [ ] Alert Engine 개선 (TODO_MOBY_BACKEND.md 참고)
- [ ] InfluxDB/MQTT 클라이언트 안정화
- [ ] API 엔드포인트 확장
- [ ] Backend 테스트 작성

**👤 개발자 B**
- [ ] React Frontend 초기 설정
- [ ] API 통합 및 테스트
- [ ] 기본 UI 컴포넌트 개발
- [ ] 문서화 및 스펙 정리

### Phase 2: 통합 단계

- 두 명이 함께 API 스펙 검토
- Frontend-Backend 통합 테스트
- 버그 수정 및 개선

---

## 🔄 일일 워크플로우

### 아침 체크인 (10분)
1. **어제 한 일** 공유
2. **오늘 할 일** 계획
3. **블로커** 확인 (상대방 도움이 필요한 것)

### 작업 중
- **독립 작업**: 각자 브랜치에서 개발
- **의존성 발생 시**: 즉시 소통 (슬랙/디스코드)
- **중간 체크인**: 점심 시간 간단히 공유

### 저녁 체크아웃 (10분)
1. **완료한 작업** 공유
2. **PR 생성** 및 리뷰 요청
3. **내일 계획** 미리 공유

---

## 🌿 브랜치 전략

### 브랜치 네이밍 규칙

```
feature/{담당자-이니셜}-{기능명}
fix/{담당자-이니셜}-{버그명}
docs/{담당자-이니셜}-{문서명}
```

**예시:**
- `feature/jh-alert-engine-improvement`
- `feature/sm-frontend-setup`
- `fix/jh-mqtt-reconnection`

### 작업 플로우

1. **최신 코드 가져오기**
```bash
git checkout main
git pull origin main
```

2. **새 브랜치 생성**
```bash
git checkout -b feature/jh-alert-engine-improvement
```

3. **작업 및 커밋**
```bash
git add .
git commit -m "feat: 알림 엔진 개선"
```

4. **푸시 및 PR 생성**
```bash
git push origin feature/jh-alert-engine-improvement
# GitHub에서 PR 생성
```

5. **리뷰 및 병합**
- 상대방이 리뷰
- 승인 후 `main`에 병합
- 브랜치 삭제

---

## 📊 작업 추적 방법

### GitHub Issues 활용

각 작업을 이슈로 생성:
- **라벨 사용**: `backend`, `frontend`, `bug`, `feature`
- **담당자 할당**: Assignee 설정
- **마일스톤**: 주간 목표 설정

### GitHub Projects 보드

간단한 칸반 보드 구성:
```
To Do → In Progress → Review → Done
```

### 주간 회고

매주 금요일 오후:
1. 이번 주 완료 사항
2. 다음 주 계획
3. 개선점 논의

---

## 🚨 충돌 방지 전략

### 1. 파일/디렉토리 소유권 명확화

**개발자 A 소유:**
- `backend/api/services/alert_engine.py`
- `backend/api/services/influx_client.py`
- `backend/api/services/mqtt_client.py`
- `backend/api/routes_alerts.py`

**개발자 B 소유:**
- `frontend/` (전체)
- `backend/tests/` (테스트 코드)
- `docs/` (문서)

**공유 영역 (소통 필수):**
- `backend/main.py`
- `backend/api/services/schemas/`
- `requirements.txt`
- `.env.example`

### 2. 코드 리뷰 필수

- 모든 PR은 최소 1명의 리뷰 필요
- 작은 단위로 자주 PR 생성 (하루 1-2회)
- 리뷰는 24시간 내 완료 목표

### 3. 통신 규칙

- **긴급**: 즉시 연락 (슬랙/전화)
- **일반**: 이슈 코멘트 또는 PR 코멘트
- **질문**: GitHub Discussions 활용

---

## 📝 체크리스트: 새 기능 시작 전

- [ ] GitHub Issue 생성
- [ ] 담당자 할당 및 라벨 설정
- [ ] 관련 문서 확인 (docs/)
- [ ] API 스펙 논의 (필요 시)
- [ ] 브랜치 생성 및 작업 시작

---

## 🎯 성공 지표

- **일일 커밋**: 각자 최소 1회
- **PR 주기**: 1-2일마다 PR 생성
- **리뷰 시간**: 24시간 이내
- **충돌 해결**: 1시간 이내

---

## 💡 팁

1. **작은 단위로 작업**: 큰 작업은 여러 PR로 분할
2. **명확한 커밋 메시지**: 나중에 히스토리 추적 용이
3. **문서화 습관**: 코드 변경 시 관련 문서도 업데이트
4. **테스트 작성**: 새 기능은 테스트와 함께
5. **정기적 동기화**: 하루 2-3회 `main` 브랜치 pull

---

## 📞 소통 채널

- **코드 리뷰**: GitHub PR 코멘트
- **일반 논의**: GitHub Discussions
- **긴급 사항**: [팀 채팅 도구]
- **회의**: 주간 1회 (30분)

---

**마지막 업데이트**: 2025-01-XX

