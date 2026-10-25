// cap-q15 exploration: run an expression file against a URL at a width; print JSON.
import { readFileSync } from "node:fs";
import { session } from "./cdp.mjs";
const [file, url, w = "1440"] = process.argv.slice(2);
const s = await session();
try { await s.open(url, Number(w), Number(w) === 1440 ? 1000 : 900); console.log(JSON.stringify(await s.js(readFileSync(file, "utf8")), null, 1)); } finally { await s.close(); process.exit(0); }
