/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0F1729",
        slate: {
          50: "#F8FAFC",
          100: "#F1F5F9",
          600: "#475569",
        },
        brand: {
          50: "#EFF6FF",
          100: "#DBEAFE",
          400: "#5B9BFF",
          500: "#3B7DFF",
          600: "#2563EB",
          700: "#1D4ED8",
        },
        accent: {
          green: "#16A34A",
          amber: "#D97706",
          red: "#DC2626",
        },
      },
      fontFamily: {
        display: ["'Söhne'", "'Inter'", "system-ui", "sans-serif"],
        body: ["'Inter'", "system-ui", "sans-serif"],
      },
      borderRadius: {
        xl2: "1.25rem",
      },
      boxShadow: {
        card: "0 1px 2px rgba(15,23,42,0.04), 0 8px 24px -8px rgba(15,23,42,0.08)",
      },
    },
  },
  plugins: [],
};
