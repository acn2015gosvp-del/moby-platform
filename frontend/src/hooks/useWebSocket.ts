import { useState, useEffect, useRef, useCallback } from 'react';
import { useToast } from '../context/ToastContext';
import type { Alert } from '../types/api';

const useWebSocket = (httpUrl: string) => {
  const [isConnected, setIsConnected] = useState(false);
  const { showToast } = useToast();
  const ws = useRef<WebSocket | null>(null);
  const connectAttempt = useRef(0);
  const MAX_RECONNECT_ATTEMPTS = 10;
  
  // 1. WebSocket URL은 한 번만 계산됩니다.
  const protocol = httpUrl.startsWith('https') ? 'wss' : 'ws';
  // Backend 라우터 Prefix를 포함하여 전체 WS 경로를 구성합니다.
  const wsUrl = `${protocol}://${new URL(httpUrl).host}/api/v1/alerts/ws/alerts`; 

  // 2. setupWebSocket 함수를 useCallback으로 안정화합니다.
  const setupWebSocket = useCallback((url: string) => {
    // 기존 연결 닫기
    if (ws.current) {
      ws.current.close();
    }
    
    // WebSocket 객체 생성
    ws.current = new WebSocket(url);
    
    // 연결 성공 핸들러
    ws.current.onopen = () => {
      console.log('WS: 연결 성공');
      setIsConnected(true);
      connectAttempt.current = 0;
    };
    
    // 메시지 수신 핸들러
    ws.current.onmessage = (event) => {
      try {
        const data: Alert = JSON.parse(event.data);
        showToast(data.message, data.level, 7000); 
      } catch (e) {
        console.error('WS: 수신 메시지 파싱 오류', event.data);
        showToast('알 수 없는 형식의 알림 메시지가 수신되었습니다.', 'error', 5000);
      }
    };
    
    // 연결 닫힘 및 재연결 로직
    ws.current.onclose = () => {
      console.log('WS: 연결 해제');
      setIsConnected(false);
      
      if (connectAttempt.current < MAX_RECONNECT_ATTEMPTS) {
        const delay = Math.min(1000 * 2 ** connectAttempt.current, 30000); 
        connectAttempt.current += 1;
        showToast(`WS 연결 끊김. ${delay / 1000}초 후 재시도...`, 'warning', 3000);
        // setupWebSocket 재귀 호출
        setTimeout(() => setupWebSocket(url), delay);
      } else {
        showToast('WS 연결에 실패했습니다. (최대 재시도 횟수 초과)', 'critical', 0);
      }
    };
    
    // 6. 에러 처리 (close 호출 제거)
    ws.current.onerror = (error) => {
    };

  }, [showToast]); // setupWebSocket end

  
  // 7. 컴포넌트 마운트 시 연결 설정
  useEffect(() => {
    setupWebSocket(wsUrl); // 계산된 최종 URL 사용
    
    // 컴포넌트 언마운트 시 연결 정리 (Clean-up)
    return () => {
      console.log('WS: 컴포넌트 정리 -> 연결 닫기');
      ws.current?.close();
    };
  }, [setupWebSocket]); // setupWebSocket이 변경될 때만 재실행

  return { isConnected, send: (data: string) => ws.current?.send(data) };
};

export default useWebSocket;