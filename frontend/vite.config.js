import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/ipos': 'http://localhost:8001',
      '/capital': 'http://localhost:8001',
      '/backtests': 'http://localhost:8001',
      '/health': 'http://localhost:8001',
      '/live': 'http://localhost:8001',
    },
  },
})
