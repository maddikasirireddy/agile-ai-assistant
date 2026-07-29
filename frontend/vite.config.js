// vite.config.js — Vite configuration for the React frontend
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,  // default dev server port (must match backend CORS setting)
  },
})
