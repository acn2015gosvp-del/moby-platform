/**
 * 상수 정의
 * 
 * 개발 편의를 위해 window.location.hostname을 활용하여
 * IP 주소를 쉽게 변경할 수 있도록 설정
 */

// 백엔드 서버 주소 설정
// 방법 1: 환경변수 사용 (VITE_API_BASE_URL, VITE_WS_BASE_URL)
// 방법 2: window.location.hostname 자동 감지 (같은 서버에서 실행 시)
// 방법 3: 하드코딩 (아래 BACKEND_HOST 상수 수정)

// 백엔드 호스트 주소 설정
// 현재 컴퓨터의 실제 IP 주소 사용 (자동 감지)
// window.location.hostname을 사용하면 브라우저가 실행되는 컴퓨터의 IP를 자동으로 감지
const BACKEND_HOST = import.meta.env.VITE_API_HOST || window.location.hostname || 'localhost'
const BACKEND_PORT = '8000'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || `http://${BACKEND_HOST}:${BACKEND_PORT}`
// WebSocket은 현재 컴퓨터의 백엔드 서버로 연결
export const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || `ws://${BACKEND_HOST}:${BACKEND_PORT}/ws`

// 📋 프론트엔드 WebSocket 주소 설정 안내:
// - WebSocket은 FastAPI 서버로 연결됩니다
// - Grafana 서버(192.168.80.183:8080)는 대시보드 임베딩용입니다
// - 수동 설정: VITE_WS_BASE_URL 환경변수 또는 위의 BACKEND_HOST 상수 수정

export const ALERT_LEVELS = {
  INFO: 'info',
  WARNING: 'warning',
  CRITICAL: 'critical',
} as const

export const ALERT_STATUS = {
  PENDING: 'pending',
  ACKNOWLEDGED: 'acknowledged',
  RESOLVED: 'resolved',
} as const

