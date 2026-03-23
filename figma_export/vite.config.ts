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

  // File types to support raw imports. Never add .css, .tsx, or .ts files to this.
  assetsInclude: ['**/*.svg', '**/*.csv'],

  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: false,
    // OneDrive / cloud-synced folders can make file watching very slow; try excluding
    // this repo from sync or moving it to e.g. C:\dev\...
    watch: {
      ignored: ['**/node_modules/**', '**/.git/**'],
    },
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
    },
  },
  // Faster cold start / first paint in dev
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router', 'lucide-react', 'recharts'],
  },
})
