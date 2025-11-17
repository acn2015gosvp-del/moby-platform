import axios from 'axios';

// 1. .env 파일에서 API 기본 주소를 가져옵니다.
const baseURL = import.meta.env.VITE_API_BASE_URL;

// 2. Axios 인스턴스 생성
const apiClient = axios.create({
  baseURL: baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10초 타임아웃
});

// 3. 에러 처리 인터셉터
apiClient.interceptors.response.use(
  
  (response) => {
    // 성공적인 응답은 그대로 반환
    return response;
  },
  
  (error) => {
    // 공통 에러 처리
    console.error('API Error:', error.response || error.message);
    return Promise.reject(error);
  }
);

export default apiClient;