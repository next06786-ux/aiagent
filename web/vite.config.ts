import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  // 加载环境变量
  const env = loadEnv(mode, process.cwd(), '');
  const apiBaseUrl = env.VITE_API_BASE_URL || 'http://localhost:8000';

  return {
    plugins: [react()],
    server: {
      host: 'localhost',
      port: 6008,
      strictPort: false,
      // 配置代理，将API请求转发到后端
      proxy: {
        '/api': {
          target: apiBaseUrl,
          changeOrigin: true,
          secure: false,
        },
        '/ws': {
          target: apiBaseUrl.replace('http', 'ws'),
          ws: true,
          changeOrigin: true,
        },
      },
    },
    preview: {
      host: 'localhost',
      port: 6008,
    },
  };
});
