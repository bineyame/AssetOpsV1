import { session } from "./cdp.mjs";
const [url, w, expr] = process.argv.slice(2);
const s = await session();
try { await s.open(url, Number(w)); console.log(JSON.stringify(await s.js(expr), null, 1)); } finally { await s.close(); }
