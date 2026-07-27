/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        poke: {
          dark: '#1F1B2E',
          card: '#2D264B',
          accent: '#FFDE00',
          gold: '#FFD700',
          gray: '#A09BB5',
          red: '#FF3B30',
          green: '#34C759',
        }
      },
      fontFamily: {
        mono: ['"Courier New"', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
}
