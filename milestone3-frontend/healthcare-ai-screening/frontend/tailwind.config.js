/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: { extend: { colors: { brand: { 50: '#eefbf9', 100: '#d3f4ef', 600: '#0f766e', 700: '#115e59', 900: '#134e4a' } } } },
  plugins: [],
}
