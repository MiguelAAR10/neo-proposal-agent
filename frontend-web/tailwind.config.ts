import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-body)", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      colors: {
        background: "#F9FAFB",
        surface: "#FFFFFF",
        "text-main": "#000000",
        "text-body": "#334155",
        "accent-violet": "#8B5CF6",
        "accent-fuchsia": "#D946EF",
      },
      boxShadow: {
        soft: "0 2px 8px rgba(0,0,0,0.04)",
      },
    },
  },
};

export default config;
