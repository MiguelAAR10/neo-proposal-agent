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
        serif: ["var(--font-serif)", "Georgia", "serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      colors: {
        // Legacy (kept for any unchanged components)
        background: "#000033",
        surface: "#05058c",
        "text-main": "#f5f5ff",
        "text-body": "#a8b8e8",
        accent: "#7ba3f0",
        // NEO brand palette
        "neo-bg": "#000033",
        "neo-surface": "#05058c",
        "neo-accent": "#7ba3f0",
        "neo-light": "#f5f5ff",
        "neo-muted": "#a8b8e8",
      },
    },
  },
};

export default config;
