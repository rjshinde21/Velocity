/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,js}",
    "./*.html",
    "./*.js"
  ],
  theme: {
    extend: {
      fontFamily: {
        'amenti': ['Amenti', 'sans-serif'],
      },
    },
  },
  plugins: [],
}