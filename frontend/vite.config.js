import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
        host: true, // 允許外部主機訪問（包括 ngrok）
        strictPort: true, // 強制使用指定端口
        // 明確允許 ngrok 主機
        allowedHosts: [
            'localhost',
            '.ngrok.io',
            '.ngrok-free.dev',
            '.ngrok.app',
            'cgmh.ddns.net',
        ],
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            },
        },
    },
});
