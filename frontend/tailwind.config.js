/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#0b1020',
        panel: '#121a2f',
        edge: '#1f2a44',
      },
    },
  },
  plugins: [],
}
