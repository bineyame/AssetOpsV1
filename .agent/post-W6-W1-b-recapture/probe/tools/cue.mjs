import { session } from "./cdp.mjs";
const s = await session();
await s.open("http://localhost:5183/sites/KOBO-001/findings/9f74c89f-85d8-410e-a779-f2378012c7e3/history", 1440);
const q = "(async()=>{const vs=document.querySelector('[data-history-versions-scroll]');const cue=document.querySelector('[data-history-scroll-cue]');const a=cue.hidden;vs.querySelectorAll('details').forEach(d=>d.open=true);await new Promise(r=>setTimeout(r,500));return {before:a,after:cue.hidden,sh:vs.scrollHeight,ch:vs.clientHeight,visible:cue.getBoundingClientRect().height}})()";
console.log(JSON.stringify(await s.js(q)));
await s.close();
