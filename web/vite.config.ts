import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// the API on the pages' origin, so no request crosses to another one
const api = { '/api': 'http://127.0.0.1:8000' }

export default defineConfig({
  plugins: [react()],
  server: { proxy: api },
  preview: { proxy: api },
})
