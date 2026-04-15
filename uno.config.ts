import { defineConfig, presetUno, presetIcons, transformerDirectives } from 'unocss'

export default defineConfig({
  presets: [
    presetUno(),
    presetIcons({
      scale: 1.2,
      extraProperties: { 'display': 'inline-block', 'vertical-align': 'middle' },
    }),
  ],
  transformers: [transformerDirectives()],
  theme: {
    colors: {
      bg: { primary: '#0f1117', secondary: '#161b27', tertiary: '#1e2535' },
      accent: { primary: '#7c6af7', hover: '#9d8fff', dim: '#4a3fa8' },
      text: { primary: '#e8eaf0', secondary: '#8892a4', muted: '#5a6270' },
      border: { primary: '#2a3040', subtle: '#1e2535' },
      success: '#34d399',
      warning: '#fbbf24',
      error: '#f87171',
    },
  },
  shortcuts: {
    'btn': 'px-4 py-2 rounded-lg font-medium transition-all duration-200 cursor-pointer',
    'btn-primary': 'btn bg-accent-primary text-white hover:bg-accent-hover',
    'btn-ghost': 'btn bg-transparent text-text-secondary hover:bg-bg-tertiary hover:text-text-primary',
    'card': 'bg-bg-secondary rounded-xl border border-border-primary p-4',
    'input-base': 'bg-bg-tertiary border border-border-primary rounded-lg px-3 py-2 text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-primary transition-colors',
  },
})
