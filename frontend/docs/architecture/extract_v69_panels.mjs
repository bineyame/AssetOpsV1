/* Extract rendered v6.9 panel headings from the standalone mock, using local Chrome. */
import {spawn} from 'node:child_process';
import {mkdtempSync, writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {fileURLToPath} from 'node:url';

const here=fileURLToPath(new URL('./',import.meta.url));
const mock=new URL('../../mockups/v69/index.html',import.meta.url);
const profile=mkdtempSync(join(tmpdir(),'assetops-ledger-'));
const port=9448;
const chrome=spawn(process.env.CHROME_PATH||'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',[
  '--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check',
  `--remote-debugging-port=${port}`,`--user-data-dir=${profile}`,'about:blank'
],{stdio:'ignore',windowsHide:true});
const pause=ms=>new Promise(r=>setTimeout(r,ms));
let ws;
try {
  let target;
  for(let i=0;i<50;i++){
    try {target=(await(await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(x=>x.type==='page');if(target)break;}catch{}
    await pause(200);
  }
  if(!target)throw Error('Chrome did not expose review page');
  ws=new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true});});
  let seq=0;const pending=new Map();
  ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result);}});
  const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});
  const evalJs=async expression=>{const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(r.exceptionDetails.text);return r.result.value;};
  await send('Runtime.enable');await send('Page.enable');
  await send('Page.navigate',{url:mock.href});
  for(let i=0;i<60;i++){if(await evalJs('Boolean(window.mockupReady)'))break;await pause(100);}
  if(!await evalJs('Boolean(window.mockupReady)'))throw Error('Mock failed to boot');
  const ids=await evalJs('window.mockupManifest.map(x=>x.id)');
  const panels={};
  for(const id of ids){
    await evalJs(`location.hash=${JSON.stringify('/'+id)}`);await pause(40);
    panels[id]=await evalJs(`Array.from(document.querySelectorAll('main .panel')).map((p,i)=>({index:i+1,title:p.querySelector('h2,h3')?.textContent?.trim()||'Untitled panel'}))`);
  }
  writeFileSync(join(here,'v69-rendered-panels.json'),JSON.stringify({source:'mock DOM',panels},null,2)+'\n');
  process.stdout.write(`Extracted ${ids.length} screens and ${Object.values(panels).flat().length} panels\n`);
} finally {ws?.close();chrome.kill();}
