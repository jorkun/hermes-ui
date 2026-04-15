import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import UnoCSS from 'unocss/vite'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue(), UnoCSS()],
  resolve: {
    alias: { '@': resolve(__dirname, 'src') },
  },
  server: {
    port: 9120,
    proxy: {
      '/api': { target: 'http://127.0.0.1:9119', changeOrigin: true },
      '/ws': { target: 'ws://127.0.0.1:9120', ws: true, changeOrigin: true },
      '/health': { target: 'http://127.0.0.1:9120', changeOrigin: true },
      '/memory': { target: 'http://127.0.0.1:9120', changeOrigin: true },
      '/files': { target: 'http://127.0.0.1:9120', changeOrigin: true },
    },
  },
})
