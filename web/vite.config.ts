import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// 直接从环境变量读取，如果没有则使用默认值
const API_BASE_URL = process.env.VITE_API_BASE_URL || 'http://82.157.195.238:8000';

console.log('='.repeat(50));
console.log('Vite Proxy Configuration:');
console.log('  API Base URL:', API_BASE_URL);
console.log('='.repeat(50));

export default defineConfig({
  plugins: [react()],
  server: {
    host: 'localhost',
    port: 6008,
    strictPort: false,
    // 配置代理，将API请求转发到后端
    proxy: {
      '/api': {
        target: API_BASE_URL,
        changeOrigin: true,
        secure: false,
        configure: (proxy, options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            console.log('Proxying:', req.method, req.url, '->', API_BASE_URL + req.url);
          });
        },
      },
      '/ws': {
        target: API_BASE_URL.replace('http', 'ws'),
        ws: true,
        changeOrigin: true,
      },
    },
  },
  preview: {
    host: 'localhost',
    port: 6008,
  },
});
