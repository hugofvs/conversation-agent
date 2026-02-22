import { defineConfig, mergeConfig } from 'vitest/config'
import viteConfig from './vite.config.js'

export default mergeConfig(viteConfig, defineConfig({
  resolve: {
    conditions: ['browser'],
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/__tests__/setup.js'],
    include: ['src/**/*.test.js'],
    css: false,
    coverage: {
      exclude: ['svelte.config.js', 'vite.config.js', 'vitest.config.js', 'src/main.js'],
    },
  },
}))
