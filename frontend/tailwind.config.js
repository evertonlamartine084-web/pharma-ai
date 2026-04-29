/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#0B132B',
          900: '#111d3b',
          800: '#1C2541',
          700: '#1e3050',
          600: '#253b5e',
          500: '#2d4a6f',
        },
        accent: {
          cyan: '#22D3EE',
          teal: '#2DD4BF',
          green: '#A3E635',
          blue: '#3B82F6',
        },
      },
      fontFamily: {
        sans: ['Poppins', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
