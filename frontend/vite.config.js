import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Forward all backend API requests to FastAPI (port 8000) during local dev.
      // On Render, frontend and backend share the same origin so this proxy is unused.
      '/workspaces': 'http://localhost:8000',
      '/ingest-acf': 'http://localhost:8000',
      '/parse-docx': 'http://localhost:8000',
      '/preview-html': 'http://localhost:8000',
      '/preview-file': 'http://localhost:8000',
      '/render-html': 'http://localhost:8000',
      '/page-blueprint': 'http://localhost:8000',
      '/save-temp-json': 'http://localhost:8000',
      '/save-to-workspace': 'http://localhost:8000',
      '/compile-workspace': 'http://localhost:8000',
      '/workspace-tree': 'http://localhost:8000',
      '/workspace-link-catalog': 'http://localhost:8000',
      '/delete-page': 'http://localhost:8000',
      '/build-website': 'http://localhost:8000',
      '/build-status': 'http://localhost:8000',
      '/build-file': 'http://localhost:8000',
      '/assets': 'http://localhost:8000',
      '/download-build': 'http://localhost:8000',
      '/detect-parent': 'http://localhost:8000',
      '/remap-parent': 'http://localhost:8000',
      '/generate-specialization-stub': 'http://localhost:8000',
      '/drafts': 'http://localhost:8000',
      '/media': 'http://localhost:8000',
      '/static': 'http://localhost:8000',
    },
  },
})
