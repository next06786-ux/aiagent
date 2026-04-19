import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({
    plugins: [react()],
    server: {
        host: 'localhost',
        port: 6008,
        strictPort: false,
        proxy: {
            '/api': {
                target: 'http://localhost:6006',
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/api/, '/api'),
                configure: (proxy, options) => {
                    proxy.on('error', (err, req, res) => {
                        console.log('proxy error', err);
                    });
                    proxy.on('proxyReq', (proxyReq, req, res) => {
                        console.log('Sending Request:', req.method, req.url);
                    });
                    proxy.on('proxyRes', (proxyRes, req, res) => {
                        console.log('Received Response:', proxyRes.statusCode, req.url);
                    });
                }
            },
        },
    },
    preview: {
        host: 'localhost',
        port: 6008,
    },
});
