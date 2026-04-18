import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    allowedHosts: [
      '.ngrok-free.dev', // Safely allows any Ngrok URL for your hackathon
      'beatris-metrizable-patrina.ngrok-free.dev' // Your specific URL just in case
    ],
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000', 
        changeOrigin: true,
      }
    }
  }
})