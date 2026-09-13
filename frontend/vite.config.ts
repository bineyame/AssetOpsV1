import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

/**
 * Dev-server configuration.
 *
 * The API proxy exists so that `npm run dev` can actually reach the backend.
 * Until T006 the UI read nothing at runtime that a screen depended on, so the
 * two dev servers could be run side by side and never talk; now the Sites
 * index and the create flow are real reads and a real write, and without this
 * the dev UI would state "the site store could not be read" on every screen.
 *
 * It affects the dev server only. Nothing about the served product depends on
 * it: the built app and the backend are served from one origin, and the paths
 * the UI requests are unchanged either way. It is deliberately one `/api`
 * rule rather than one per surface, so adding an endpoint never means editing
 * a proxy table, and it names no simulator path.
 */
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
  },
});
