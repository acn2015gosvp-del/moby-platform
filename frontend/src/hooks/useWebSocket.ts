import { useState, useEffect, useRef } from 'react';
import { useToast } from '../context/ToastContext'; // 토스트 띄우기 위해 import
import type { Alert } from '../types/api'; // Alert 타입 import

const useWebSocket = (httpUrl: string) => {
  const [isConnected, setIsConnected] = useState(false);
  const { showToast } = useToast();
  const ws = useRef<WebSocket | null>(null);
  const connectAttempt = useRef(0);
  const MAX_RECONNECT_ATTEMPTS = 10;
  
  const setupWebSocket = (wsUrl: string) => {
    // 1. 기존 연결 닫기
    if (ws.current) {
      ws.current.close();
    }
    
    // 2. WebSocket 객체 생성
    ws.current = new WebSocket(wsUrl);
    
    // 3. 연결 성공
    ws.current.onopen = () => {
      console.log('WS: 연결 성공');
      setIsConnected(true);
      connectAttempt.current = 0; // 재시도 횟수 초기화
      showToast('실시간 데이터 서버에 연결되었습니다.', 'info', 3000);
    };
    
    // 4. 메시지 수신 처리 (Alert Engine 메시지 수신)
    ws.current.onmessage = (event) => {
      try {
        const data: Alert = JSON.parse(event.data);
        
        // Alert Engine에서 받은 메시지를 Toast로 바로 띄웁니다.
        showToast(data.message, data.level, 7000); // 7초 표시

      } catch (e) {
        console.error('WS: 수신 메시지 파싱 오류', event.data);
        showToast('알 수 없는 형식의 알림 메시지가 수신되었습니다.', 'error', 5000);
      }
    };
    
    // 5. 연결 닫힘 및 재연결 로직 (Task 5 요구사항)
    ws.current.onclose = () => {
      console.log('WS: 연결 해제');
      setIsConnected(false);
      
      // 지수 백오프(Exponential Backoff)를 사용하여 재시도
      if (connectAttempt.current < MAX_RECONNECT_ATTEMPTS) {
        // 1초 -> 2초 -> 4초... 지수적으로 딜레이 증가
        const delay = Math.min(1000 * 2 ** connectAttempt.current, 30000); 
        connectAttempt.current += 1;
        
        showToast(`WS 연결 끊김. ${delay / 1000}초 후 재시도...`, 'warning', 3000);
        setTimeout(() => setupWebSocket(wsUrl), delay);
      } else {
        showToast('WS 연결에 실패했습니다. (최대 재시도 횟수 초과)', 'critical', 0);
      }
    };
    
    // 6. 에러 처리
    ws.current.onerror = (error) => {
      console.error('WS: 에러 발생', error);
      showToast('WebSocket에서 치명적인 에러가 발생했습니다.', 'error', 0);
      ws.current?.close(); 
    };
  };
  
  // 7. 컴포넌트 마운트 시 연결 설정
  useEffect(() => {
    // HTTP URL을 WS URL로 변환 (http -> ws, https -> wss)
    const protocol = httpUrl.startsWith('https') ? 'wss' : 'ws';
    // 백엔드 Fast API의 WebSocket 엔드포인트 경로 가정
    const wsUrl = `${protocol}://${new URL(httpUrl).host}/ws/alerts`; 
    
    setupWebSocket(wsUrl);
    
    // 컴포넌트 언마운트 시 연결 정리 (Clean-up)
    return () => {
      console.log('WS: 컴포넌트 정리 -> 연결 닫기');
      ws.current?.close();
    };
  }, [httpUrl, showToast]); // showToast는 안정적이지만, 의존성 배열에 추가하여 ESLint 경고 방지

  // 현재 연결 상태와 메시지 전송 함수만 외부에 제공
  return { isConnected, send: (data: string) => ws.current?.send(data) };
};

export default useWebSocket;