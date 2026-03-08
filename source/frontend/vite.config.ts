import { defineConfig } from 'vite'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [
    // The React and Tailwind plugins are both required for Make, even if
    // Tailwind is not being actively used – do not remove them
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      // Alias @ to the src directory
      '@': path.resolve(__dirname, './src'),
    },
  },

  server: {
    port: 5173,
    proxy: {
      '/api/ingestion': {
        target: 'http://localhost:8001',
        rewrite: (p: string) => p.replace(/^\/api\/ingestion/, ''),
      },
      '/api/automation': {
        target: 'http://localhost:8002',
        rewrite: (p: string) => p.replace(/^\/api\/automation/, ''),
      },
      '/api/rules': {
        target: 'http://localhost:8003',
        rewrite: (p: string) => p.replace(/^\/api\/rules/, ''),
      },
      '/api/notifications': {
        target: 'http://localhost:8004',
        rewrite: (p: string) => p.replace(/^\/api\/notifications/, ''),
      },
      '/api/actuators': {
        target: 'http://localhost:8005',
        rewrite: (p: string) => p.replace(/^\/api\/actuators/, ''),
      },
      '/api/history': {
        target: 'http://localhost:8006',
        rewrite: (p: string) => p.replace(/^\/api\/history/, ''),
      },
    },
  },

  // File types to support raw imports. Never add .css, .tsx, or .ts files to this.
  assetsInclude: ['**/*.svg', '**/*.csv'],
})
