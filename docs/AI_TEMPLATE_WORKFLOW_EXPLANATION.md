# AI 자동 생성 템플릿 프롬프트 워크플로우 설명

**작성일**: 2025-11-17  
**목적**: Cursor PRO와 Gemini CLI의 협업 구조 및 템플릿 프롬프트 역할 설명

---

## 🎯 핵심 개념

이 프로젝트는 **두 개의 AI 도구가 협력하여 자동으로 코드를 생성**하도록 설계되었습니다:

### 1. **Gemini CLI** = 시스템 설계자 (Architect)
- **역할**: 전체 시스템 구조 설계, 문서 작성, 구현 지침서 생성
- **출력**: 설계 문서, 구조 정의, Cursor가 따라야 할 지침서

### 2. **Cursor PRO** = 코드 구현자 (Implementer)
- **역할**: Gemini의 설계를 바탕으로 실제 코드 파일 생성
- **출력**: 실제 코드 파일, 폴더 구조, 구현 코드

---

## 📁 템플릿 프롬프트 파일 구조

```
프로젝트 루트/
├── CURSOR.md                              # Cursor PRO용 마스터 템플릿
├── GEMINI.md                              # Gemini CLI용 마스터 프롬프트
├── MASTER_PROMPT_TEMPLATE_v2.md           # 통합 마스터 프롬프트
│
└── docs/
    ├── MASTER_PROMPT_TEMPLATE_GEMINI_v1.md    # Gemini 상세 템플릿
    ├── WORKFLOW_GEMINI_CURSOR_MASTER_v1.md   # 협업 워크플로우
    └── FRONTEND_TEMPLATE_REQUIREMENTS.md      # 프론트엔드 구현 지침서 (새로 추가)
```

---

## 🔄 자동 생성 워크플로우

### 시나리오: 프론트엔드 프로젝트 생성

#### Step 1: Gemini CLI에게 요청
```
사용자: "프론트엔드 프로젝트 구조를 설계해줘"
```

#### Step 2: Gemini CLI의 작업
1. `GEMINI.md` 템플릿을 참조
2. `FRONTEND_TEMPLATE_REQUIREMENTS.md` 문서를 생성 (또는 참조)
3. **구현 지침서** 작성:
   ```
   - frontend/src/components/AlertToast.tsx 생성 필요
   - TypeScript 타입 정의 필요
   - Axios 서비스 레이어 구조 정의
   - ...
   ```

#### Step 3: Cursor PRO에게 전달
```
Gemini의 출력을 Cursor PRO에 복사/붙여넣기
또는
"FRONTEND_TEMPLATE_REQUIREMENTS.md 문서를 참조하여 프론트엔드 프로젝트 생성"
```

#### Step 4: Cursor PRO의 작업
1. `CURSOR.md` 템플릿을 참조
2. `FRONTEND_TEMPLATE_REQUIREMENTS.md` 문서를 읽음
3. **실제 파일 생성**:
   - `frontend/src/components/AlertToast.tsx` 생성
   - `frontend/src/services/api/client.ts` 생성
   - 모든 필요한 파일을 자동으로 생성

---

## 📋 각 템플릿의 역할

### 1. `CURSOR.md` (Cursor PRO용)
**목적**: Cursor가 코드를 생성할 때 따라야 할 규칙

**포함 내용**:
- 프로젝트 폴더 구조 규칙
- 백엔드/프론트엔드 코딩 규칙
- 파일 네이밍 규칙
- 코드 품질 요구사항
- Gemini와의 협업 방법

**예시**:
```markdown
# 🔧 Backend Rules
- Use FastAPI
- Every route → routes_xxx.py
- Business logic → services/
- Data models → schemas/
```

### 2. `GEMINI.md` (Gemini CLI용)
**목적**: Gemini가 설계 문서를 생성할 때 참조할 정보

**포함 내용**:
- 프로젝트 전체 개요
- 시스템 아키텍처 설명
- 디렉토리 구조 요약
- Gemini가 생성해야 할 문서 유형
- Cursor에게 전달할 지침서 형식

**예시**:
```markdown
# 📘 Gemini Should Generate:
- Architecture Documentation
- Technical Specifications
- Project Automation
- Implementation Guides for Cursor
```

### 3. `FRONTEND_TEMPLATE_REQUIREMENTS.md` (구현 지침서)
**목적**: Gemini가 설계하고, Cursor가 구현할 때 참조하는 **구체적인 요구사항**

**포함 내용**:
- 필수 파일 목록 (전체 경로 포함)
- 각 파일의 역할과 구현 내용
- 코드 예시
- 생성 우선순위
- API 연동 스펙

**예시**:
```markdown
#### `src/components/alerts/AlertToast.tsx`
- 실시간 알림 토스트 표시
- fade-in/fade-out 애니메이션
- 자동 닫기 기능
```

---

## 🎬 실제 사용 예시

### 예시 1: 새로운 기능 추가

**사용자 요청**: "센서 데이터 차트 컴포넌트를 만들어줘"

1. **Gemini에게**: "센서 데이터 차트 컴포넌트 설계해줘"
   - Gemini는 `FRONTEND_TEMPLATE_REQUIREMENTS.md`를 참조
   - 컴포넌트 구조, Props, 스타일링 요구사항 정의
   - 구현 지침서 생성

2. **Cursor에게**: Gemini의 지침서를 전달
   - Cursor는 `CURSOR.md` 규칙을 따름
   - `frontend/src/components/sensors/SensorChart.tsx` 생성
   - TypeScript 타입 정의
   - Tailwind CSS 스타일링

### 예시 2: 프론트엔드 프로젝트 초기화

**사용자 요청**: "프론트엔드 프로젝트를 처음부터 만들어줘"

1. **Gemini에게**: "프론트엔드 프로젝트 구조 설계해줘"
   - Gemini는 `FRONTEND_TEMPLATE_REQUIREMENTS.md` 생성 (이미 완료됨)
   - 전체 파일 구조 정의
   - Phase별 생성 계획 제시

2. **Cursor에게**: "FRONTEND_TEMPLATE_REQUIREMENTS.md를 참조하여 프론트엔드 프로젝트 생성"
   - Cursor는 문서를 읽고 Phase 1부터 순차적으로 생성
   - Vite 프로젝트 초기화
   - 모든 폴더 구조 생성
   - 기본 파일들 생성

---

## 🔗 템플릿 간 관계도

```
┌─────────────────────────────────────────────────┐
│           사용자 요청                            │
│  "프론트엔드 프로젝트 만들어줘"                    │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│         Gemini CLI (설계자)                      │
│  ┌──────────────────────────────────────────┐   │
│  │ GEMINI.md 템플릿 참조                     │   │
│  │ → 프로젝트 구조 이해                      │   │
│  │ → 설계 문서 생성                          │   │
│  └──────────────────────────────────────────┘   │
│               │                                  │
│               ▼                                  │
│  ┌──────────────────────────────────────────┐  │
│  │ FRONTEND_TEMPLATE_REQUIREMENTS.md 생성    │  │
│  │ (구현 지침서)                              │  │
│  └──────────────────────────────────────────┘  │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│         Cursor PRO (구현자)                      │
│  ┌──────────────────────────────────────────┐  │
│  │ CURSOR.md 템플릿 참조                     │  │
│  │ → 코딩 규칙 준수                          │  │
│  │ → 폴더 구조 유지                          │  │
│  └──────────────────────────────────────────┘  │
│               │                                  │
│               ▼                                  │
│  ┌──────────────────────────────────────────┐  │
│  │ FRONTEND_TEMPLATE_REQUIREMENTS.md 읽기    │  │
│  │ → 구체적인 파일 목록 확인                 │  │
│  │ → 구현 내용 확인                          │  │
│  └──────────────────────────────────────────┘  │
│               │                                  │
│               ▼                                  │
│  ┌──────────────────────────────────────────┐  │
│  │ 실제 파일 생성                             │  │
│  │ - frontend/src/components/...             │  │
│  │ - frontend/src/services/...               │  │
│  │ - frontend/package.json                   │  │
│  └──────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

---

## ✅ 체크리스트: 템플릿 프롬프트 완성도

### 현재 상태

- [x] `CURSOR.md` - Cursor PRO용 마스터 템플릿 존재
- [x] `GEMINI.md` - Gemini CLI용 마스터 프롬프트 존재
- [x] `WORKFLOW_GEMINI_CURSOR_MASTER_v1.md` - 협업 워크플로우 정의
- [x] `FRONTEND_TEMPLATE_REQUIREMENTS.md` - 프론트엔드 구현 지침서 생성 완료

### 향후 추가 가능한 템플릿

- [ ] `BACKEND_TEMPLATE_REQUIREMENTS.md` - 백엔드 구현 지침서
- [ ] `API_TEMPLATE_REQUIREMENTS.md` - API 엔드포인트 구현 지침서
- [ ] `TEST_TEMPLATE_REQUIREMENTS.md` - 테스트 코드 구현 지침서
- [ ] `DEPLOYMENT_TEMPLATE_REQUIREMENTS.md` - 배포 자동화 지침서

---

## 💡 핵심 포인트

1. **Gemini = 설계, Cursor = 구현**
   - Gemini는 코드를 직접 작성하지 않음
   - Cursor는 설계 없이 임의로 구조를 만들지 않음

2. **템플릿 프롬프트의 역할**
   - 각 AI 도구가 프로젝트 컨텍스트를 이해하도록 도움
   - 일관된 코드 스타일과 구조 유지
   - 자동 생성의 품질 향상

3. **구현 지침서의 중요성**
   - `FRONTEND_TEMPLATE_REQUIREMENTS.md` 같은 문서는
   - Gemini가 설계하고 Cursor가 구현할 때의 **공통 참조 문서**
   - 두 도구가 같은 목표를 향해 작업할 수 있게 함

---

## 🚀 다음 단계

이제 프론트엔드 템플릿 요구사항이 정의되었으므로:

1. **Gemini에게**: "FRONTEND_TEMPLATE_REQUIREMENTS.md를 참조하여 프론트엔드 프로젝트 생성 계획을 세워줘"
2. **Cursor에게**: "FRONTEND_TEMPLATE_REQUIREMENTS.md Phase 1부터 순차적으로 구현해줘"

이렇게 하면 두 AI 도구가 협력하여 완전한 프론트엔드 프로젝트를 자동으로 생성할 수 있습니다!

