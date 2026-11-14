/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        brand: {
          50: "#eef5f1",
          100: "#dcebe3",
          200: "#bad8c8",
          300: "#91c0a8",
          400: "#6ba987",
          500: "#4b9874",
          600: "#41906e",
          700: "#37785c",
          800: "#2d604a",
          900: "#234837",
        },
        lime: { 300: "#ffd36e", 400: "#fcb315", 500: "#e6a10c" },
        amber: {
          50: "#fff8e6",
          100: "#ffedc2",
          300: "#ffd36e",
          400: "#fcb315",
          500: "#e6a10c",
          800: "#805000",
          900: "#603d00",
        },
        ink: { DEFAULT: "#0f1f17", 800: "#14221b", 700: "#1c2f25", 600: "#2b4034" },
        cream: "#f6f8f4",
      },
      boxShadow: {
        card: "0 1px 2px rgba(15,31,23,.05), 0 6px 20px rgba(15,31,23,.05)",
      },
    },
  },
  plugins: [],
};
