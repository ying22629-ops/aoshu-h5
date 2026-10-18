import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Relative base + hash routing lets the build run from any static host or sub-path.
export default defineConfig({
  base: './',
  plugins: [vue()],
})
