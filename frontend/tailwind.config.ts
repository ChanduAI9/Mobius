import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        mobius: {
          bg: "#0A0A0F",
          surface: "#12121A",
          elevated: "#1A1A24",
          border: "#2A2A3A",
          text: "#F0F0F5",
          muted: "#8888A0",
          accent: "#00D4FF",
          success: "#00E676",
          warning: "#FFB300",
          error: "#FF5252",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
