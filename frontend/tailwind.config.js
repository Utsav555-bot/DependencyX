/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        cyber: {
          bg: "#0B1120",
          card: "#0F172A",
          surface: "#1E293B",
          border: "#334155",
          muted: "#64748B",
          text: "#F8FAFC",
          accent: "#38BDF8",
          cyan: "#06B6D4",
          low: "#10B981",
          medium: "#F59E0B",
          high: "#F97316",
          critical: "#EF4444"
        }
      }
    },
  },
  plugins: [],
};
