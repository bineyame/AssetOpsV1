// DTO render proof harness (post-W6 shell Q23/Q24). Root is this folder; product code is imported from frontend/src unchanged.
import { fileURLToPath, pathToFileURL } from "node:url";
import { dirname, resolve, sep } from "node:path";
const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, "../../..");
const nm = resolve(repo, "frontend/node_modules").split(sep).join("/");
const react = (await import(pathToFileURL(nm + "/@vitejs/plugin-react/dist/index.js").href)).default;
export default {
  root: here,
  cacheDir: resolve(here, ".vite-cache"),
  plugins: [react()],
  resolve: {
    alias: [{ find: /^(react|react-dom|react-router-dom|react-router|scheduler)(\/.*)?$/, replacement: nm + "/$1$2" }],
  },
  server: { port: 18108, strictPort: true, host: "127.0.0.1", fs: { allow: [repo] }, hmr: false },
};
