// one-off probe: per-row heights of the two panels (same harness, same ports)
import { spawn } from "node:child_process"; import { mkdtempSync, writeFileSync } from "node:fs"; import { tmpdir } from "node:os"; import { join } from "node:path";
const PORT=18109; const chrome=spawn("C:/Program Files/Google/Chrome/Application/chrome.exe",["--headless=new","--disable-gpu","--hide-scrollbars",`--remote-debugging-port=${PORT}`,`--user-data-dir=${mkdtempSync(join(tmpdir(),"dto-probe-"))}`,"about:blank"],{stdio:"ignore"});
const sleep=(ms)=>new Promise(r=>setTimeout(r,ms)); let ws,seq=0; const P=new Map();
for(let i=0;i<80;i++){try{const p=(await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find(t=>t.type==="page"); if(p){ws=new WebSocket(p.webSocketDebuggerUrl); await new Promise(a=>ws.onopen=a); break;}}catch{} await sleep(250);}
ws.onmessage=e=>{const m=JSON.parse(e.data); if(m.id&&P.has(m.id)){P.get(m.id)(m);P.delete(m.id);}};
const send=(method,params={})=>new Promise(res=>{const id=++seq;P.set(id,m=>res(m.result));ws.send(JSON.stringify({id,method,params}));});
const js=async e=>(await send("Runtime.evaluate",{expression:e,returnByValue:true,awaitPromise:true})).result.value;
const out={};
for (const [name,url,head] of [["mini","/sites/KLG-014/evidence?from=2026-09-22T00:00:00Z&to=2026-09-23T00:00:00Z&view=analysis&record=3f6b2a10-0000-4000-8000-000000000005","Accepted records behind the conclusions"],["foundation","/sites/KLG-014/foundation","Identity and operating obligations"]]) for (const w of [1440,390]) {
  await send("Emulation.setDeviceMetricsOverride",{width:w,height:900,deviceScaleFactor:1,mobile:w<500});
  await send("Page.navigate",{url:"http://127.0.0.1:18108"+url}); await sleep(3500);
  out[name+w]=await js(`(()=>{const p=[...document.querySelectorAll("h2")].find(e=>e.textContent.trim()===${JSON.stringify(head)}).closest("section");
   const H=e=>Math.round(e.getBoundingClientRect().height);
   const dl=p.querySelector("dl"); const rv=p.querySelector(".evidence-record-view");
   const pair=p.parentElement; 
   return {panelH:H(p), parent:pair.className, siblings:[...pair.children].map(c=>(c.querySelector("h2")||{}).textContent+":"+H(c)),
     head:H(p.querySelector("header")||p.firstElementChild),
     dl: dl?[...dl.querySelectorAll("dd")].map(c=>H(c)+" "+c.tagName+" "+c.textContent.slice(0,30)):null,
     rv: rv?[...rv.querySelectorAll(":scope > * , :scope > div > *, :scope dl > *")].map(c=>H(c)+" "+c.tagName+" "+c.textContent.slice(0,30)):null,
     th: [...p.querySelectorAll("tr[data-evidence-record] > *")].slice(0,6).map(c=>Math.round(c.getBoundingClientRect().width)+"x"+H(c))};})()`);
}
writeFileSync("probe.json",JSON.stringify(out,null,1)); ws.close(); chrome.kill(); process.exit(0);
