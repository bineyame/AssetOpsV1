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

    /**
     * Vitest's default is 5s, which this suite has outgrown.
     *
     * Every file pays for its own jsdom environment, and on a loaded machine
     * that setup alone costs several seconds before a test body runs. The
     * symptom was `Test timed out in 5000ms` in a handful of files per run,
     * different ones each time, each passing when run alone - recorded as
     * flakiness in the T007, T008 and T009 packets and characterised in T009.
     * Adding the fetch seam file in T010A raised the file count to 15 and
     * tipped it from occasional to routine.
     *
     * This raises tolerance for a slow environment; it does not weaken an
     * assertion. A test that genuinely hangs still fails, four seconds of real
     * work still passes, and nothing waits longer than it needs to. The
     * alternative, capping worker threads, would slow every run on every
     * machine to fix a problem only loaded ones have.
     */
    testTimeout: 20000,
  },
});
