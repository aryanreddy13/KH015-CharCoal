/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        ops: {
          bg: '#0a0d14',
          surface: '#111726',
          card: '#161f33',
          border: '#23304a',
          hover: '#1d2a45',
          critical: '#ef4444',
          criticalGlow: 'rgba(239, 68, 68, 0.25)',
          high: '#f97316',
          moderate: '#eab308',
          low: '#10b981',
          accent: '#38bdf8',
          muted: '#94a3b8',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}
