import type { Config } from "tailwindcss";
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        arc: {
          cyan:   "#00e5ff",
          blue:   "#0ea5e9",
          purple: "#a855f7",
          green:  "#22c55e",
          yellow: "#eab308",
          dark:   "#0a0a0f",
          card:   "#0f0f1a",
          border: "#1e1e3f",
        },
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4,0,0.6,1) infinite",
        "slide-in": "slideIn 0.3s ease-out",
        "glow": "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        slideIn: { from: { opacity: "0", transform: "translateY(-8px)" }, to: { opacity: "1", transform: "translateY(0)" } },
        glow: { from: { boxShadow: "0 0 5px #00e5ff40" }, to: { boxShadow: "0 0 20px #00e5ff80" } },
      },
    },
  },
  plugins: [],
};
export default config;
