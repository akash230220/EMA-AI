// vite.config.js
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

/**
 * Vite configuration for AI Email OS frontend.
 *
 * Key responsibilities:
 *  - "@/" path alias -> src/ (used in literally every component,
 *    page, hook, and api file generated so far — e.g.
 *    `import { cn } from "@/lib/utils"`)
 *  - Dev server proxy for /api -> FastAPI backend, avoiding CORS
 *    friction during local development (optional convenience;
 *    axiosClient.js's VITE_API_BASE_URL works standalone too)
 *  - Production build tuned for a mid-size SPA: manual chunk
 *    splitting for the heaviest third-party deps (recharts, d3-ish
 *    chart internals, framer-motion) so the initial bundle stays
 *    lean and route-level code doesn't all land in one huge file
 */
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");

  return {
    plugins: [react()],

    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },

    server: {
      port: 5173,
      host: true, // exposes on LAN (0.0.0.0) — useful for testing on a phone
      proxy: {
        // Lets the frontend call relative "/api/v1/..." paths during
        // dev without CORS issues, proxying straight to FastAPI.
        // axiosClient.js still defaults to the full VITE_API_BASE_URL,
        // so this proxy is a convenience fallback, not a hard dependency.
        "/api": {
          target: env.VITE_API_PROXY_TARGET || "http://localhost:8000",
          changeOrigin: true,
        },
      },
    },

    build: {
      outDir: "dist",
      sourcemap: mode !== "production",
      chunkSizeWarningLimit: 1000,
      rollupOptions: {
        output: {
          manualChunks: {
            "vendor-react": ["react", "react-dom", "react-router-dom"],
            "vendor-query": ["@tanstack/react-query"],
            "vendor-charts": ["recharts"],
            "vendor-motion": ["framer-motion"],
            "vendor-dnd": ["@dnd-kit/core", "@dnd-kit/sortable", "@dnd-kit/utilities"],
            "vendor-radix": [
              "@radix-ui/react-dialog",
              "@radix-ui/react-dropdown-menu",
              "@radix-ui/react-tabs",
              "@radix-ui/react-select",
              "@radix-ui/react-tooltip",
              "@radix-ui/react-avatar",
              "@radix-ui/react-switch",
              "@radix-ui/react-checkbox",
              "@radix-ui/react-progress",
              "@radix-ui/react-label",
              "@radix-ui/react-separator",
            ],
          },
        },
      },
    },

    // Allows import.meta.env.VITE_* to be typed/read consistently;
    // Vite does this automatically for VITE_-prefixed vars, this
    // just documents the intent alongside the proxy target above.
    envPrefix: "VITE_",
  };
});