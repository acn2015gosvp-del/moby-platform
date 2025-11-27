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
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
        secure: false,  // ✅ HTTP 연결 허용 (개발 환경)
        ws: true,       // ✅ WebSocket 프록시 지원 (중요!)
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('[Proxy Error]', err);
          });
          proxy.on('proxyReq', (_proxyReq, req, _res) => {
            console.log('[Proxy Request]', req.method, req.url);
          });
        }
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
    // 이미지 관련 의존성 최적화
    include: [],
  },
})
