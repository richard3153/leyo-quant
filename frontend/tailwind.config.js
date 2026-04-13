/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#f59e0b',
        dark: {
          100: '#1e1e2e',
          200: '#181825',
          300: '#11111b',
        }
      }
    }
  },
  plugins: []
}
