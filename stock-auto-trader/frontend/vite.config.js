import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  define: {
    'import.meta.env.VITE_OTLP_ENDPOINT': JSON.stringify(
      process.env.VITE_OTLP_ENDPOINT || 'http://localhost:4318/v1/traces'
    ),
  },
})
