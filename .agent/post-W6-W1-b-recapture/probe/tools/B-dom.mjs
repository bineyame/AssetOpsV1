import { session } from "./B-cdp.mjs";
const [url, w, expr] = process.argv.slice(2);
const s = await session();
try { await s.open(url, Number(w), Number(w) === 1440 ? 1000 : 900); console.log(JSON.stringify(await s.js(expr), null, 1)); } finally { await s.close(); }
