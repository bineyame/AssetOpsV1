/* Measure v69 mock panels (cards, statusbar, panels, notices) at 1440 and 390 via headless Chrome CDP.
   Usage: node tools/measure-mock-panels.mjs [--mock <dir>] <out-dir> <screen-id>...  -> mock-measure.json + PNGs. */
import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve, dirname } from "node:path";
import { pathToFileURL, fileURLToPath } from "node:url";
import { widthGuard } from "./evidence-checks.mjs";
const PORT = 9488;
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
// OUT-A A6: `--mock <dir>` (anywhere in the arguments) picks the mock folder, default frontend/mockups/v69; a relative
// dir resolves against the working directory. The positional shape `<out-dir> <screen-id>...` is unchanged.
const ARGS = process.argv.slice(2);
const mockAt = ARGS.indexOf("--mock");
let MOCK_DIR = resolve(dirname(fileURLToPath(import.meta.url)), "../frontend/mockups/v69");
if (mockAt !== -1) {
  if (!ARGS[mockAt + 1]) { console.error("usage: --mock <dir> needs a directory"); process.exit(2); }
  MOCK_DIR = resolve(ARGS[mockAt + 1]);
  ARGS.splice(mockAt, 2);
}
const MOCK = pathToFileURL(join(MOCK_DIR, "index.html")).href;
const OUT = ARGS[0];
const SCREENS = ARGS.slice(1);
if (!OUT || !SCREENS.length) { console.error("usage: node tools/measure-mock-panels.mjs [--mock <dir>] <out-dir> <screen-id>..."); process.exit(2); }
const profile = mkdtempSync(join(tmpdir(), "w302-mock-"));
const chrome = spawn(CHROME, ["--headless=new","--disable-gpu","--no-first-run",`--remote-debugging-port=${PORT}`,`--user-data-dir=${profile}`,"about:blank"],{stdio:"ignore"});
const sleep=(ms)=>new Promise(r=>setTimeout(r,ms));
let ws, seq=0; const pending=new Map();
for (let i=0;i<80;i++){ try{ const p=(await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find(t=>t.type==="page"); if(p){ ws=new WebSocket(p.webSocketDebuggerUrl); await new Promise((a,b)=>{ws.onopen=a;ws.onerror=b}); break;} }catch{} await sleep(250);}
ws.onmessage=(e)=>{const m=JSON.parse(e.data); if(m.id&&pending.has(m.id)){pending.get(m.id)(m);pending.delete(m.id);}};
const send=(method,params={})=>new Promise((res,rej)=>{const id=++seq;pending.set(id,m=>m.error?rej(new Error(JSON.stringify(m.error))):res(m.result));ws.send(JSON.stringify({id,method,params}));});
const js=async(e)=>(await send("Runtime.evaluate",{expression:e,returnByValue:true,awaitPromise:true})).result.value;
await send("Page.enable");
const requireWidth = widthGuard({ send });
const results=[];
for (const screen of SCREENS) for (const [w,h] of [[1440,1000],[390,900]]) {
  await send("Emulation.setDeviceMetricsOverride",{width:w,height:h,deviceScaleFactor:1,mobile:w<500});
  await requireWidth(w, h, `resize ${screen} ${w}`, { record: false });
  await send("Page.navigate",{url:`${MOCK}#/${screen}`});
  await sleep(1500);
  await requireWidth(w, h, `loaded ${screen} ${w}`, { record: false });
  await js(`location.hash='#/${screen}'`); await sleep(800);
  await requireWidth(w, h, `measure ${screen} ${w}`, { record: false });
  const r=await js(`(()=>{const R=e=>{const b=e.getBoundingClientRect();return {top:Math.round(b.top+scrollY),h:Math.round(b.height),w:Math.round(b.width)}};
   const main=document.querySelector('main')||document.body;
   const out=[];
   for(const e of main.querySelectorAll('.cards,.statusbar,section.panel,.notice')){ if(e.closest('section.panel')&&!e.matches('section.panel')) continue;
     const kind=e.matches('.cards')?'cards':e.matches('.statusbar')?'statusbar':e.matches('.notice')?'notice':'panel';
     const title=kind==='panel'?e.querySelector('h2')?.textContent.trim():kind==='cards'?[...e.querySelectorAll('.metric-label')].map(x=>x.textContent).join(' | '):e.textContent.trim().slice(0,80);
     const o={kind,title,...R(e)};
     if(kind==='cards') o.children=[...e.children].map(R);
     const tw=e.querySelector('.table-wrap'); if(tw){o.tableClient=tw.clientWidth;o.tableScroll=tw.scrollWidth; o.rows=[...tw.querySelectorAll('tbody tr')].map(t=>Math.round(t.getBoundingClientRect().height)); o.thead=Math.round(tw.querySelector('thead').getBoundingClientRect().height); o.cols=[...tw.querySelectorAll('thead th')].map(t=>t.textContent+':'+Math.round(t.getBoundingClientRect().width));}
     out.push(o);}
   const seen=new Set(out.length?[...main.querySelectorAll('.cards,.statusbar,section.panel,.notice')]:[]);
   const blocks=[]; const walk=(el,d)=>{ for(const e of el.children){ if(seen.has(e)) continue; const b=R(e); if(!b.h) continue;
       if(d<3 && e.children.length>1 && [...e.children].some(c=>seen.has(c)||c.children.length>1)) walk(e,d+1); else blocks.push(e);} };
   walk(main,0);
   for(const e of blocks){ const b=R(e); if(b.h<8) continue;
     out.push({kind:'block',title:(e.className||e.tagName.toLowerCase())+': '+((e.querySelector('h1,h2,h3,strong')?.textContent||e.textContent).trim().slice(0,60)),...b}); }
   const h1=document.querySelector('h1'); 
   return {h1:h1?.textContent.trim(), pageH:document.documentElement.scrollHeight, docScrollW:document.documentElement.scrollWidth, clientW:document.documentElement.clientWidth, items:out};})()`);
  await send("Emulation.setDeviceMetricsOverride",{width:w,height:h,deviceScaleFactor:1,mobile:w<500});
  await requireWidth(w, h, `capture ${screen} ${w}`, { record: false });
  const shot=await send("Page.captureScreenshot",{format:"png",captureBeyondViewport:true});
  writeFileSync(join(OUT,`mock-${screen}-${w}.png`),Buffer.from(shot.data,"base64"));
  results.push({screen,width:w,...r});
}
writeFileSync(join(OUT,"mock-measure.json"),JSON.stringify(results,null,1));
console.log(`wrote ${results.length} measurements to ${OUT}`);
ws.close(); chrome.kill(); process.exit(0);
