module.exports = {
  darkMode: 'class',   // we’ll toggle a “dark” class on <html>
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Pastel orchid pink – used for light backgrounds and subtle highlights
        orchid: {
          DEFAULT: '#F7C8E0',
          100: '#FDEBF5',
          200: '#FBD9EB',
        },
        // Deep elegant violet – primary actions, borders, headings
        violet: {
          DEFAULT: '#5A0FC5',
          600: '#4B0CA8',
          800: '#350679',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
