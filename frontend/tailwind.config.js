/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        slate: {
          850: '#151e2e',
          950: '#070c18',
        },
        brand: {
          50: '#f0fdf4',
          500: '#22c55e',
          600: '#16a34a',
        },
        wind: '#38bdf8', // Sky cyan for wind
        actual: '#10b981', // Emerald for actuals
        thermal: '#f59e0b', // Amber for thermal
        danger: '#ef4444', // Red for shortfall
      }
    },
  },
  plugins: [],
}
