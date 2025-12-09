# 프론트엔드 템플릿 요구사항 정의

**작성일**: 2025-11-17  
**목적**: 프론트엔드 개발 시작 전 필수 파일 및 구조 정의  
**대상**: React + Vite + TypeScript 기반 MOBY Platform Frontend

---

## 📋 목차

1. [프로젝트 개요](#프로젝트-개요)
2. [기술 스택](#기술-스택)
3. [필수 파일 구조](#필수-파일-구조)
4. [파일별 상세 요구사항](#파일별-상세-요구사항)
5. [API 연동 스펙](#api-연동-스펙)
6. [컴포넌트 템플릿](#컴포넌트-템플릿)
7. [생성 우선순위](#생성-우선순위)

---

## 📦 프로젝트 개요

MOBY Platform의 프론트엔드는 다음 기능을 제공합니다:

- **실시간 알림 대시보드**: WebSocket을 통한 실시간 알림 수신 및 표시
- **센서 데이터 모니터링**: Grafana 임베드 및 센서 상태 조회
- **알림 관리**: 알림 생성, 조회, 상태 변경 (pending → acknowledged → resolved)
- **LLM 요약 표시**: 알림별 LLM 생성 요약 표시
- **반응형 UI**: 모바일/태블릿/데스크톱 지원

---

## 🛠 기술 스택

### 핵심 기술
- **React 18+**: UI 라이브러리
- **TypeScript**: 타입 안정성
- **Vite**: 빌드 도구 및 개발 서버
- **React Router**: 클라이언트 사이드 라우팅

### 스타일링
- **Tailwind CSS**: 유틸리티 기반 CSS 프레임워크
- **shadcn/ui**: 재사용 가능한 UI 컴포넌트 라이브러리 (선택사항)

### 상태 관리
- **React Context API**: 전역 상태 관리
- **React Hooks**: 상태 및 사이드 이펙트 관리

### HTTP 클라이언트
- **Axios**: REST API 호출
- **WebSocket API**: 실시간 알림 수신

### 개발 도구
- **ESLint**: 코드 품질 검사
- **Prettier**: 코드 포맷팅
- **TypeScript**: 타입 체크

---

## 📁 필수 파일 구조

```
frontend/
├── public/                          # 정적 파일
│   ├── favicon.ico
│   └── logo.svg
│
├── src/
│   ├── components/                  # 재사용 가능한 컴포넌트
│   │   ├── layout/                  # 레이아웃 컴포넌트
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── MainLayout.tsx
│   │   │   └── Footer.tsx
│   │   │
│   │   ├── alerts/                  # 알림 관련 컴포넌트
│   │   │   ├── AlertToast.tsx       # 토스트 알림
│   │   │   ├── AlertsPanel.tsx      # 알림 패널
│   │   │   ├── AlertCard.tsx        # 알림 카드
│   │   │   ├── AlertList.tsx        # 알림 리스트
│   │   │   └── AlertFilters.tsx     # 알림 필터
│   │   │
│   │   ├── sensors/                # 센서 관련 컴포넌트
│   │   │   ├── SensorCard.tsx       # 센서 카드
│   │   │   ├── SensorList.tsx       # 센서 리스트
│   │   │   └── SensorStatus.tsx     # 센서 상태
│   │   │
│   │   ├── dashboard/               # 대시보드 컴포넌트
│   │   │   ├── GrafanaEmbed.tsx     # Grafana 임베드
│   │   │   ├── StatsCard.tsx        # 통계 카드
│   │   │   └── ChartCard.tsx        # 차트 카드
│   │   │
│   │   └── common/                  # 공통 컴포넌트
│   │       ├── Button.tsx
│   │       ├── Input.tsx
│   │       ├── Modal.tsx
│   │       ├── Loading.tsx
│   │       └── ErrorBoundary.tsx
│   │
│   ├── pages/                       # 페이지 컴포넌트
│   │   ├── Dashboard.tsx           # 메인 대시보드
│   │   ├── Alerts.tsx              # 알림 페이지
│   │   ├── Sensors.tsx             # 센서 페이지
│   │   ├── Reports.tsx             # 보고서 페이지
│   │   └── Settings.tsx            # 설정 페이지
│   │
│   ├── services/                    # API 서비스 레이어
│   │   ├── api/                     # API 클라이언트
│   │   │   ├── client.ts            # Axios 인스턴스
│   │   │   ├── interceptors.ts      # 요청/응답 인터셉터
│   │   │   └── types.ts            # API 타입 정의
│   │   │
│   │   ├── alerts/                  # 알림 API 서비스
│   │   │   ├── alertService.ts     # 알림 CRUD
│   │   │   └── alertTypes.ts       # 알림 타입
│   │   │
│   │   ├── sensors/                # 센서 API 서비스
│   │   │   ├── sensorService.ts   # 센서 CRUD
│   │   │   └── sensorTypes.ts     # 센서 타입
│   │   │
│   │   └── websocket/              # WebSocket 서비스
│   │       ├── websocketService.ts # WebSocket 클라이언트
│   │       └── websocketTypes.ts   # WebSocket 타입
│   │
│   ├── hooks/                       # 커스텀 훅
│   │   ├── useAlerts.ts            # 알림 훅
│   │   ├── useSensors.ts           # 센서 훅
│   │   ├── useWebSocket.ts         # WebSocket 훅
│   │   ├── useAuth.ts              # 인증 훅 (선택사항)
│   │   └── useDebounce.ts          # 디바운스 훅
│   │
│   ├── context/                     # Context API
│   │   ├── AlertContext.tsx        # 알림 컨텍스트
│   │   ├── SensorContext.tsx       # 센서 컨텍스트
│   │   └── AppContext.tsx          # 앱 전역 컨텍스트
│   │
│   ├── utils/                       # 유틸리티 함수
│   │   ├── formatters.ts           # 날짜/숫자 포맷터
│   │   ├── validators.ts           # 입력 검증
│   │   ├── constants.ts            # 상수 정의
│   │   └── helpers.ts              # 헬퍼 함수
│   │
│   ├── types/                       # TypeScript 타입 정의
│   │   ├── alert.ts                # 알림 타입
│   │   ├── sensor.ts               # 센서 타입
│   │   ├── api.ts                  # API 응답 타입
│   │   └── common.ts               # 공통 타입
│   │
│   ├── styles/                      # 전역 스타일
│   │   ├── globals.css             # 전역 CSS
│   │   └── tailwind.css            # Tailwind 설정
│   │
│   ├── App.tsx                      # 루트 컴포넌트
│   ├── main.tsx                     # 진입점
│   └── router.tsx                  # 라우터 설정
│
├── .env.example                     # 환경 변수 예시
├── .env.local                       # 로컬 환경 변수 (gitignore)
├── .gitignore
├── .eslintrc.json                   # ESLint 설정
├── .prettierrc                      # Prettier 설정
├── index.html                       # HTML 템플릿
├── package.json                     # 의존성 관리
├── tsconfig.json                    # TypeScript 설정
├── vite.config.ts                   # Vite 설정
└── README.md                        # 프로젝트 설명
```

---

## 📄 파일별 상세 요구사항

### 1. 프로젝트 설정 파일

#### `package.json`
```json
{
  "name": "moby-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx",
    "format": "prettier --write \"src/**/*.{ts,tsx,css}\""
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.0",
    "zustand": "^4.4.0" // 또는 Context API 사용
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "@vitejs/plugin-react": "^4.2.0",
    "autoprefixer": "^10.4.0",
    "eslint": "^8.0.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.0",
    "postcss": "^8.4.0",
    "prettier": "^3.0.0",
    "tailwindcss": "^3.3.0",
    "typescript": "^5.2.0",
    "vite": "^5.0.0"
  }
}
```

#### `vite.config.ts`
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

#### `tsconfig.json`
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

---

### 2. API 서비스 레이어

#### `src/services/api/client.ts`
- Axios 인스턴스 생성
- 기본 URL 설정
- 요청/응답 인터셉터 설정
- 에러 처리

#### `src/services/api/interceptors.ts`
- 요청 인터셉터: 토큰 추가, 로딩 상태 관리
- 응답 인터셉터: 에러 처리, 토큰 갱신

#### `src/services/alerts/alertService.ts`
필수 함수:
- `getAlerts(params?)`: 알림 목록 조회
- `getAlertById(id)`: 알림 상세 조회
- `createAlert(data)`: 알림 생성
- `updateAlertStatus(id, status)`: 알림 상태 변경
- `deleteAlert(id)`: 알림 삭제

#### `src/services/sensors/sensorService.ts`
필수 함수:
- `getSensors()`: 센서 목록 조회
- `getSensorById(id)`: 센서 상세 조회
- `getSensorStatus()`: 센서 상태 조회
- `postSensorData(data)`: 센서 데이터 전송

#### `src/services/websocket/websocketService.ts`
- WebSocket 연결 관리
- 재연결 로직
- 메시지 수신/발송
- 연결 상태 관리

---

### 3. 타입 정의

#### `src/types/alert.ts`
```typescript
export type AlertLevel = 'info' | 'warning' | 'critical'
export type AlertStatus = 'pending' | 'acknowledged' | 'resolved'

export interface Alert {
  id: string
  level: AlertLevel
  message: string
  llm_summary?: string
  sensor_id: string
  source: string
  ts: string
  details: AlertDetails
}

export interface AlertDetails {
  vector: number[]
  norm: number
  threshold?: number
  warning_threshold?: number
  critical_threshold?: number
  severity: string
  meta?: Record<string, any>
}

export interface AlertRequest {
  vector: number[]
  threshold?: number
  warning_threshold?: number
  critical_threshold?: number
  sensor_id?: string
  enable_llm_summary?: boolean
}
```

#### `src/types/sensor.ts`
```typescript
export interface Sensor {
  device_id: string
  temperature?: number
  humidity?: number
  vibration?: number
  sound?: number
}

export interface SensorStatus {
  status: string
  count: number
  active: number
  inactive: number
}
```

---

### 4. Context API

#### `src/context/AlertContext.tsx`
- 알림 목록 상태 관리
- 알림 추가/업데이트/삭제 함수
- WebSocket을 통한 실시간 알림 수신
- 필터링 및 정렬 로직

#### `src/context/SensorContext.tsx`
- 센서 목록 상태 관리
- 센서 상태 조회 함수
- 실시간 센서 데이터 업데이트

---

### 5. 커스텀 훅

#### `src/hooks/useAlerts.ts`
```typescript
export function useAlerts() {
  // 알림 목록 조회
  // 알림 생성
  // 알림 상태 변경
  // 필터링 및 정렬
}
```

#### `src/hooks/useWebSocket.ts`
```typescript
export function useWebSocket(url: string) {
  // WebSocket 연결
  // 메시지 수신
  // 재연결 로직
  // 연결 상태 관리
}
```

---

### 6. 컴포넌트

#### `src/components/alerts/AlertToast.tsx`
- 실시간 알림 토스트 표시
- fade-in/fade-out 애니메이션
- 자동 닫기 기능
- 클릭 시 상세 보기

#### `src/components/alerts/AlertsPanel.tsx`
- 알림 목록 표시
- 필터링 UI
- 정렬 기능
- 페이지네이션

#### `src/components/dashboard/GrafanaEmbed.tsx`
- Grafana 대시보드 임베드
- iframe 관리
- 반응형 크기 조정

---

### 7. 페이지

#### `src/pages/Dashboard.tsx`
- 메인 대시보드 레이아웃
- 통계 카드
- Grafana 임베드
- 최근 알림 요약

#### `src/pages/Alerts.tsx`
- 알림 목록 페이지
- 필터링 및 검색
- 알림 상세 보기
- 상태 변경 기능

---

## 🔌 API 연동 스펙

### Base URL
```
Development: http://localhost:8000
Production: https://api.moby-platform.com
```

### 엔드포인트

#### 알림 API
- `POST /alerts/evaluate`: 알림 생성 및 평가
- `GET /alerts`: 알림 목록 조회 (향후 구현)
- `GET /alerts/{id}`: 알림 상세 조회 (향후 구현)
- `PATCH /alerts/{id}/status`: 알림 상태 변경 (향후 구현)

#### 센서 API
- `POST /sensors/data`: 센서 데이터 수신
- `GET /sensors/status`: 센서 상태 조회

### WebSocket
- `ws://localhost:8000/ws/alerts`: 실시간 알림 수신 (향후 구현)

---

## 🎨 컴포넌트 템플릿

### 기본 컴포넌트 구조
```typescript
import React from 'react'
import { Alert } from '@/types/alert'

interface AlertCardProps {
  alert: Alert
  onAcknowledge?: (id: string) => void
  onResolve?: (id: string) => void
}

export const AlertCard: React.FC<AlertCardProps> = ({
  alert,
  onAcknowledge,
  onResolve,
}) => {
  return (
    <div className="alert-card">
      {/* 컴포넌트 내용 */}
    </div>
  )
}
```

---

## 📊 생성 우선순위

### Phase 1: 프로젝트 초기 설정 (1일)
1. ✅ Vite + React + TypeScript 프로젝트 생성
2. ✅ 기본 폴더 구조 생성
3. ✅ Tailwind CSS 설정
4. ✅ ESLint/Prettier 설정
5. ✅ 라우터 설정

### Phase 2: API 서비스 레이어 (1일)
1. ✅ Axios 클라이언트 설정
2. ✅ 알림 API 서비스
3. ✅ 센서 API 서비스
4. ✅ 타입 정의

### Phase 3: 기본 레이아웃 (1일)
1. ✅ Header 컴포넌트
2. ✅ Sidebar 컴포넌트
3. ✅ MainLayout 컴포넌트
4. ✅ 기본 스타일링

### Phase 4: 알림 기능 (2일)
1. ✅ AlertContext 구현
2. ✅ AlertToast 컴포넌트
3. ✅ AlertsPanel 컴포넌트
4. ✅ 알림 페이지

### Phase 5: 센서 기능 (1일)
1. ✅ SensorContext 구현
2. ✅ 센서 컴포넌트
3. ✅ 센서 페이지

### Phase 6: 대시보드 (1일)
1. ✅ Grafana 임베드
2. ✅ 통계 카드
3. ✅ 대시보드 페이지

### Phase 7: WebSocket 통합 (1일)
1. ✅ WebSocket 서비스
2. ✅ 실시간 알림 수신
3. ✅ 재연결 로직

---

## ✅ 체크리스트

프론트엔드 템플릿 생성 시 다음 항목들을 확인하세요:

- [ ] 프로젝트 초기 설정 완료
- [ ] 모든 필수 폴더 구조 생성
- [ ] API 서비스 레이어 구현
- [ ] 타입 정의 완료
- [ ] 기본 레이아웃 컴포넌트 구현
- [ ] 라우팅 설정 완료
- [ ] 환경 변수 설정
- [ ] 에러 처리 구현
- [ ] 로딩 상태 관리
- [ ] 반응형 디자인 적용

---

## 📝 참고 사항

1. **백엔드 API와의 호환성**: 백엔드 API 스펙 변경 시 프론트엔드도 함께 업데이트 필요
2. **타입 안정성**: 모든 API 응답에 대한 타입 정의 필수
3. **에러 처리**: 모든 API 호출에 대한 에러 처리 구현
4. **로딩 상태**: 사용자 경험을 위한 로딩 상태 표시
5. **접근성**: WCAG 가이드라인 준수 (선택사항이지만 권장)

---

**다음 단계**: 이 문서를 기반으로 프론트엔드 프로젝트를 생성하고, 각 파일을 순차적으로 구현합니다.

