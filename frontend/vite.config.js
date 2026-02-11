
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      // Also proxy specific endpoints if needed without /api prefix, or adjust backend to serve under /api
      '/route': 'http://localhost:8000',
      '/traffic': 'http://localhost:8000',
      '/network': 'http://localhost:8000',
      '/geocode': 'http://localhost:8000',
    }
  }
})
