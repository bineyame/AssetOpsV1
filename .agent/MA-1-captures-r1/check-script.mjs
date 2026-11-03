import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
const OUT=process.argv[2], MOCK=pathToFileURL(process.argv[3]).href, PORT=9333;
const chrome=spawn("C:/Program Files/Google/Chrome/Application/chrome.exe",["--headless=new","--disable-gpu","--no-first-run",`--remote-debugging-port=${PORT}`,`--user-data-dir=${mkdtempSync(join(tmpdir(),"ma1-"))}`,"about:blank"],{stdio:"ignore"});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
let ws,seq=0;const pending=new Map();
for(let i=0;i<80;i++){try{const p=(await(await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find(t=>t.type==="page");if(p){ws=new WebSocket(p.webSocketDebuggerUrl);await new Promise((a,b)=>{ws.onopen=a;ws.onerror=b});break;}}catch{}await sleep(250);}
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){pending.get(m.id)(m);pending.delete(m.id);}};
const send=(method,params={})=>new Promise((res,rej)=>{const id=++seq;pending.set(id,m=>m.error?rej(new Error(JSON.stringify(m.error))):res(m.result));ws.send(JSON.stringify({id,method,params}));});
const js=async e=>(await send("Runtime.evaluate",{expression:e,returnByValue:true,awaitPromise:true})).result.value;
const key=async(k,code,text)=>{for(const t of ["keyDown","keyUp"])await send("Input.dispatchKeyEvent",{type:t,key:k,code,text:t==="keyDown"?text:undefined,windowsVirtualKeyCode:{Enter:13," ":32,Escape:27}[k]});};
await send("Page.enable");
const screens=["portfolio","mini","cold","ev","findings-opportunities","finding-history","verification"];
const res=[];const bad=[];
for(const s of screens)for(const [w,h] of [[1440,1000],[390,900]]){
  await send("Emulation.setDeviceMetricsOverride",{width:w,height:h,deviceScaleFactor:1,mobile:w<500});
  await send("Page.navigate",{url:`${MOCK}?r=${Math.random()}#/${s}`});await sleep(900);await js(`location.hash='#/${s}'`);await sleep(700);
  const sw=()=>js(`[document.documentElement.scrollWidth,document.documentElement.clientWidth]`);
  const [a,b]=await sw();const r={s,w,scrollW:a,clientW:b,whys:0,modes:{}};
  if(a>b)bad.push(`hscroll ${s} ${w}`);
  const n=await js(`document.querySelectorAll('.why-btn').length`);r.whys=n;
  for(let i=0;i<n;i++){
    for(const mode of ["click","enter","space"]){
      await js(`document.querySelectorAll('.why-btn')[${i}].scrollIntoView({block:'center'})`);
      if(mode==="click"){const p=await js(`(()=>{const r=document.querySelectorAll('.why-btn')[${i}].getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]})()`);
        for(const t of ["mousePressed","mouseReleased"])await send("Input.dispatchMouseEvent",{type:t,x:p[0],y:p[1],button:"left",clickCount:1});}
      else{await js(`document.querySelectorAll('.why-btn')[${i}].focus()`);mode==="enter"?await key("Enter","Enter","\r"):await key(" ","Space"," ");}
      await sleep(150);
      const open=await js(`!!document.querySelector('.why-pop')`);
      const [a2,b2]=await sw();
      if(!open)bad.push(`no open ${s} ${w} #${i} ${mode}`);
      if(a2>b2)bad.push(`hscroll-open ${s} ${w} #${i} ${mode} ${a2}>${b2}`);
      if(w<500&&mode==="click"){ // sheet close button
        const vis=await js(`(()=>{const c=document.querySelector('.why-close');if(!c)return null;const r=c.getBoundingClientRect();return r.width>0&&r.bottom<=innerHeight})()`);
        if(!vis)bad.push(`close btn not visible ${s} ${w} #${i}`);
        await js(`document.querySelector('.why-close').click()`);await sleep(100);
        const f=await js(`document.activeElement===document.querySelectorAll('.why-btn')[${i}]&&!document.querySelector('.why-pop')`);
        if(!f)bad.push(`close btn focus ${s} ${w} #${i}`);
        continue;
      }
      await key("Escape","Escape");await sleep(100);
      const f=await js(`!document.querySelector('.why-pop')&&document.activeElement===document.querySelectorAll('.why-btn')[${i}]`);
      if(!f)bad.push(`escape/focus ${s} ${w} #${i} ${mode}`);
    }
    // second click closes
    if(w>=500){await js(`document.querySelectorAll('.why-btn')[${i}].focus()`);await key("Enter","Enter","\r");await sleep(100);await js(`document.querySelectorAll('.why-btn')[${i}].click()`);await sleep(100);
      if(await js(`!!document.querySelector('.why-pop')`))bad.push(`toggle close ${s} ${w} #${i}`);}
  }
  // default open rows + Grow closed check
  r.openRows=await js(`[...document.querySelectorAll('details.ob')].map(d=>d.open+':'+(d.querySelector('.ob-name,.ob-title')?.textContent||d.textContent.slice(0,12)).trim().slice(0,14))`);
  res.push(r);
  if(["mini","ev","portfolio"].includes(s)){
    await js(`document.querySelectorAll('details.ob:not([open]) > summary').forEach(x=>{if(/Grow/i.test(x.textContent))x.click()})`);await sleep(300);
    r.growParts=await js(`document.querySelectorAll('.ob-grow .ob-part').length`);
    const shot=await send("Page.captureScreenshot",{format:"png",captureBeyondViewport:true});
    writeFileSync(join(OUT,`m3-${s}-${w}.png`),Buffer.from(shot.data,"base64"));
  }
}
writeFileSync(join(OUT,"check.json"),JSON.stringify({res,bad},null,1));
console.log(JSON.stringify(res.map(r=>({s:r.s,w:r.w,sw:r.scrollW,cw:r.clientW,whys:r.whys,grow:r.growParts,open:r.openRows?.filter(x=>x.startsWith('true')).length}))));
console.log("BAD",JSON.stringify(bad));
ws.close();chrome.kill();process.exit(0);
