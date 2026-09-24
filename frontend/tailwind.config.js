/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        dark: {
          900: '#0a0f1e',
          800: '#0f1729',
          700: '#111827',
          600: '#1e2a3a',
        },
        brand: {
          500: '#6366f1',
          600: '#4f46e5',
          400: '#818cf8',
        },
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
