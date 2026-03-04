import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        "alert-fraud": "#E03E3E",
        "alert-risk": "#F79F1F",
        "op-cost": "#3ECF8E",
        "primary-brand": "#4F73FF",
        "text-main": "#E0E3EB",
        "midnight-charcoal": "#090B0F",
      },
    },
  },
};

export default config;
