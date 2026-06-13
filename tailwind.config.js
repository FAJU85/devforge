/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // DevForge color palette
        dev: {
          light: "#0D1116",
          dark: "#FFFFFF",
        },
        frog: "#E19200",
        primary: {
          light: "#239A82",
          dark: "#76CD1D",
        },
        bg: {
          light: "#FFFFFF",
          dark: "#0D1116",
          secondary: {
            light: "#F4F7F6",
            dark: "#131920",
          },
        },
        border: {
          light: "#E8ECEB",
          dark: "#1A2228",
        },
      },
      fontFamily: {
        sans: ['system-ui', 'sans-serif'],
      },
    },
  },
  darkMode: 'class',
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
