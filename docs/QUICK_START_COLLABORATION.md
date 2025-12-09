# ⚡ 빠른 시작: 협업 가이드

두 명이서 바로 시작할 수 있는 간단한 가이드입니다.

## 🚀 5분 안에 시작하기

### 1단계: 역할 분담 결정 (5분)

**옵션 A: 기능별 분담 (추천)**
- **개발자 A**: Backend (Alert Engine, Data Pipeline)
- **개발자 B**: Frontend + Testing

**옵션 B: 수직 분담**
- **개발자 A**: Alert System 전체 (Backend + Frontend)
- **개발자 B**: Sensor Data Pipeline 전체 (Backend + Frontend)

### 2단계: GitHub Projects 보드 생성 (5분)

1. GitHub 저장소 → **Projects** 탭
2. **New project** → **Board** 선택
3. 컬럼 추가: `Backlog`, `To Do`, `In Progress`, `Review`, `Done`

### 3단계: 첫 작업 이슈 생성 (5분)

1. **Issues** 탭 → **New issue**
2. `task_assignment` 템플릿 선택
3. 작업 설명 작성
4. 담당자 할당 및 라벨 추가
5. Projects 보드에 추가

### 4단계: 브랜치 생성 및 작업 시작

```bash
# 최신 코드 가져오기
git checkout main
git pull origin main

# 새 브랜치 생성 (예: feature/jh-alert-improvement)
git checkout -b feature/{이니셜}-{작업명}

# 작업 시작!
```

## 📋 일일 체크리스트

### 아침 (10분)
- [ ] GitHub에서 최신 코드 pull
- [ ] 오늘 할 작업 이슈 확인
- [ ] 상대방과 간단히 체크인 (슬랙/디스코드)

### 작업 중
- [ ] 작은 단위로 자주 커밋
- [ ] 충돌 가능성 있으면 미리 소통
- [ ] 중간에 막히면 즉시 질문

### 저녁 (10분)
- [ ] 작업한 내용 커밋 및 푸시
- [ ] PR 생성 (작업이 완료된 경우)
- [ ] 내일 계획 간단히 공유

## 🎯 이번 주 목표 예시

### 개발자 A
- [ ] Alert Engine 개선 (TODO_MOBY_BACKEND.md 참고)
- [ ] MQTT 재연결 로직 구현
- [ ] 관련 테스트 작성

### 개발자 B
- [ ] React Frontend 초기 설정
- [ ] Alert API 통합
- [ ] 기본 UI 컴포넌트 개발

## 🔥 핵심 원칙

1. **작은 단위로 자주 PR**: 큰 작업은 여러 PR로 분할
2. **명확한 커밋 메시지**: 나중에 추적 용이
3. **즉시 소통**: 막히면 바로 질문
4. **상호 리뷰**: 모든 PR은 리뷰 필수
5. **정기적 동기화**: 하루 2-3회 main 브랜치 pull

## 📚 더 자세한 정보

- 전체 협업 전략: [TEAM_COLLABORATION.md](TEAM_COLLABORATION.md)
- GitHub Projects 설정: [GITHUB_PROJECTS_SETUP.md](GITHUB_PROJECTS_SETUP.md)
- 주간 계획 템플릿: [WEEKLY_PLANNING.md](WEEKLY_PLANNING.md)
- 일일 스탠드업: [DAILY_STANDUP.md](DAILY_STANDUP.md)

---

**시작하세요!** 🚀

