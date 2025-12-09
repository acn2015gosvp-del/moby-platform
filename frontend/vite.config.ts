import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: true, // 모든 네트워크 인터페이스에서 접속 가능 (0.0.0.0 + IPv6)
    strictPort: false,
    // 서버 시작 시 자동으로 브라우저 열기 비활성화 (로딩 문제 방지)
    open: false,
    // HMR 최적화
    hmr: {
      overlay: true,
      // HMR 클라이언트 포트 설정
      clientPort: 5173,
    },
    // 프록시 설정 (성능 최적화)
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
        secure: false,
        ws: true,
        // 프록시 타임아웃 설정 (보고서 생성은 최대 5분 소요 가능)
        timeout: 300000, // 300초 (5분) - InfluxDB 쿼리 최적화 후에도 LLM 생성 시간 고려
        // 연결 재사용 (Keep-Alive)
        configure: (proxy) => {
          proxy.on('proxyReq', (proxyReq) => {
            // 요청 헤더 최적화
            proxyReq.setHeader('Connection', 'keep-alive');
          });
          // 프록시 에러 처리
          proxy.on('error', (err) => {
            console.error('[Vite Proxy] 프록시 오류:', err);
          });
        },
      },
    },
  },
  build: {
    // 번들 크기 최적화
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor 라이브러리 분리
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          // 큰 라이브러리 분리
          'ui-vendor': ['axios'],
        },
      },
    },
    // 청크 크기 경고 임계값 증가 (500KB)
    chunkSizeWarningLimit: 500,
    // 이미지 최적화 설정
    assetsInlineLimit: 4096, // 4KB 이하 이미지는 base64로 인라인화
  },
  // 이미지 최적화 설정
  assetsInclude: ['**/*.png', '**/*.jpg', '**/*.jpeg', '**/*.gif', '**/*.svg', '**/*.webp'],
  optimizeDeps: {
    // 사전 번들링할 의존성 명시 (시작 속도 개선)
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'axios',
    ],
    // 강제 사전 번들링 (선택적)
    force: false, // 필요시 true로 변경하여 의존성 재빌드
  },
})
