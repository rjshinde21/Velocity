import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        // Ensure consistent file naming and structure
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]',
      }
    },
    // Generate source maps for debugging
    sourcemap: true,
    // Ensure assets are properly processed
    assetsDir: 'assets',
    // Clean the output directory before building
    emptyOutDir: true
  },
  server: {
    // Configure dev server to serve correct MIME types
    headers: {
      'Content-Type': 'application/javascript',
    }
  }
})