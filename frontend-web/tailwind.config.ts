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
        // NEO ELECTRIC MIDNIGHT v4 — Design System
        background: "#0a0a2e",
        surface: "#12124a",
        "surface-dim": "#1a1a5e",
        "surface-elevated": "#1a1a5e",
        "text-main": "#f0f0ff",
        "text-body": "#a5b4fc",
        accent: "#4f8cff",
        "accent-purple": "#8b5cf6",
        "accent-lilac": "#c084fc",
        "accent-iris": "#6366f1",
        "accent-cyan": "#60a5fa",
        // NEO brand palette (legacy compatibility)
        "neo-bg": "#0a0a2e",
        "neo-surface": "#12124a",
        "neo-accent": "#4f8cff",
        "neo-light": "#f0f0ff",
        "neo-muted": "#a5b4fc",
      },
    },
  },
};

export default config;
