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
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
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
  },
})
