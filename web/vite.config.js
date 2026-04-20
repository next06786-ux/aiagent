import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// 从环境变量读取API地址
const API_BASE_URL = process.env.VITE_API_BASE_URL || 'http://82.157.195.238:8000';

console.log('='.repeat(60));
console.log('Vite Proxy Configuration (vite.config.js):');
console.log('  API Base URL:', API_BASE_URL);
console.log('='.repeat(60));

export default defineConfig({
    plugins: [react()],
    server: {
        host: 'localhost',
        port: 6008,
        strictPort: false,
        proxy: {
            '/api': {
                target: API_BASE_URL,
                changeOrigin: true,
                secure: false,
                configure: (proxy, options) => {
                    proxy.on('error', (err, req, res) => {
                        console.log('proxy error', err);
                    });
                    proxy.on('proxyReq', (proxyReq, req, res) => {
                        console.log('Proxying:', req.method, req.url, '->', API_BASE_URL + req.url);
                    });
                    proxy.on('proxyRes', (proxyRes, req, res) => {
                        console.log('Response:', proxyRes.statusCode, req.url);
                    });
                }
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
