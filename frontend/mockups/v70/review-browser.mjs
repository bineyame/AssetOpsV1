/* Render the standalone prototype with installed Chrome; no dependencies. */
import {spawn} from 'node:child_process';
import {mkdtempSync, writeFileSync, mkdirSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {fileURLToPath} from 'node:url';
const dir=fileURLToPath(new URL('./',import.meta.url));
const profile=mkdtempSync(join(tmpdir(),'assetops-mockups-'));
const port=9447;
const chrome=spawn(process.env.CHROME_PATH||'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',[
 '--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check',`--remote-debugging-port=${port}`,`--user-data-dir=${profile}`,'about:blank'
],{stdio:'ignore',windowsHide:true});
let ws;
const pause=ms=>new Promise(r=>setTimeout(r,ms));
const errors=[],checks=[],measurements=[];
function assert(label,passed,detail=''){checks.push({label,passed,detail});if(!passed)throw Error(`${label}: ${detail}`);}
try{
 let target;
 for(let i=0;i<50;i++){try{target=(await(await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(x=>x.type==='page');if(target)break;}catch{}await pause(200);}
 if(!target)throw Error('Chrome did not expose its review page.');
 ws=new WebSocket(target.webSocketDebuggerUrl);
 await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true});});
 let seq=0;const pending=new Map();
 ws.addEventListener('message',e=>{const msg=JSON.parse(e.data);if(msg.id&&pending.has(msg.id)){const p=pending.get(msg.id);pending.delete(msg.id);clearTimeout(p.timer);msg.error?p.reject(Error(JSON.stringify(msg.error))):p.resolve(msg.result);}if(msg.method==='Runtime.exceptionThrown')errors.push(msg.params.exceptionDetails);});
 const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++seq;const timer=setTimeout(()=>{pending.delete(id);reject(Error(`Timed out: ${method}`));},30000);pending.set(id,{resolve,reject,timer});ws.send(JSON.stringify({id,method,params}));});
 const evaluate=async expression=>{const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(r.exceptionDetails.text+' '+r.exceptionDetails.exception?.description);return r.result.value;};
 await send('Runtime.enable');await send('Page.enable');
 await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1100,deviceScaleFactor:1,mobile:false});
 const base=new URL('index.html',import.meta.url).href;
 await send('Page.navigate',{url:base});
 for(let i=0;i<60;i++){if(await evaluate('Boolean(window.mockupReady)'))break;await pause(100);}
 assert('Prototype booted',await evaluate('Boolean(window.mockupReady)'),JSON.stringify(errors));
 const manifest=await evaluate('window.mockupManifest');
 writeFileSync(join(dir,'screen-manifest.json'),JSON.stringify(manifest,null,2)+'\n');
 const navigate=async id=>{await evaluate(`location.hash=${JSON.stringify('/'+id)}`);await pause(40);};
 for(const s of manifest){
  await navigate(s.id);
  const m=await evaluate(`({id:${JSON.stringify(s.id)},title:document.querySelector('h1')?.textContent,width:innerWidth,scrollWidth:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight,tabRows:document.querySelectorAll('.tabs').length,subRows:document.querySelectorAll('.subtabs').length,broken:[...document.querySelectorAll('a[href^="#/"]')].map(a=>a.getAttribute('href').slice(2)).filter(id=>!window.mockupManifest.some(s=>s.id===id))})`);
  measurements.push(m);
  assert(`${s.id}: visible page`,Boolean(m.title));
  assert(`${s.id}: no horizontal page overflow`,m.scrollWidth<=m.width,`${m.scrollWidth}/${m.width}`);
  assert(`${s.id}: one subtab row maximum`,m.subRows<=1&&m.tabRows<=2);
  assert(`${s.id}: all route targets exist`,m.broken.length===0,m.broken.join(','));
 }
 await navigate('sites');
 await evaluate(`document.querySelector('[data-site-filter="Cold-chain"]').click()`);
 assert('Site domain filter',await evaluate(`document.querySelectorAll('#site-table tbody tr').length===1 && document.querySelector('#site-table').textContent.includes('GreenHarvest')`));
 await navigate('portfolio');
 assert('Portfolio value-led headline',await evaluate(`document.querySelectorAll('.value-card').length===5 && document.querySelector('.value-grid').textContent.includes('Not established')`));
 await evaluate(`document.querySelector('[data-portfolio-lens="Opportunities"]').click()`);
 assert('Opportunity lens keeps Finding ownership',await evaluate(`document.querySelectorAll('#portfolio-findings tbody tr').length===1 && document.querySelector('#portfolio-findings a[href="#/opportunity-finding"]')!==null`));
 await evaluate(`document.querySelector('[data-portfolio-lens="Risks"]').click()`);
 assert('Risk lens keeps all risk findings across domains',await evaluate(`document.querySelectorAll('#portfolio-findings tbody tr').length===4&&['GreenHarvest','Depot','Kobo'].every(t=>document.querySelector('#portfolio-findings').textContent.includes(t))`));
 await evaluate(`document.querySelector('[data-portfolio-lens="Cost"]').click()`);
 assert('Cost lens preserves consequence basis',await evaluate(`document.querySelectorAll('#portfolio-findings tbody tr').length===1 && document.querySelector('#portfolio-findings').textContent.includes('scenario maintenance')`));
 await evaluate(`document.querySelector('[data-portfolio-scope]').click()`);
 assert('Portfolio scope discloses unlike periods',await evaluate(`document.querySelector('.drawer').textContent.includes('Separate five-day study') && document.querySelector('.drawer').textContent.includes('not a comparable full-month')`));
 await evaluate(`document.querySelector('[data-close]').click();document.querySelector('[data-portfolio-progress]').click()`);
 assert('Recovered value is not work completion',await evaluate(`document.querySelector('.drawer').textContent.includes('No complete verified outcome')`));
 await evaluate(`document.querySelector('[data-close]').click();document.querySelector('[data-notes]').click()`);
 assert('Portfolio notes retain both references',await evaluate(`document.querySelector('.drawer').textContent.includes('Appendix A1') && document.querySelector('.drawer').textContent.includes('Section ownership')`));
 await evaluate(`document.querySelector('[data-close]').click()`);
 await navigate('dispatch');await evaluate(`document.querySelector('[data-interval="1"]').click()`);
 assert('Gap interval opens bounded evidence',await evaluate(`document.querySelector('.drawer').textContent.includes('Indeterminate') && document.querySelector('.drawer').textContent.includes('PCS')`));
 await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape'});
 assert('Escape closes drawer',await evaluate(`!document.querySelector('.drawer')`));
 await navigate('assumptions');await evaluate(`document.querySelector('#fuel-price').value='1.50';document.querySelector('[data-save-price]').click()`);
 await navigate('portfolio');assert('Assumption reaches portfolio',await evaluate(`document.querySelector('main').textContent.includes('$4.04–4.86')`));
 await navigate('assumptions');await evaluate(`document.querySelector('#fuel-price').value='1.20';document.querySelector('[data-save-price]').click()`);
 await navigate('recommendation');await evaluate(`document.querySelector('[data-accept]').click()`);await pause(50);
 assert('Accept changes to Actions root',await evaluate(`location.hash==='#/action-overview'&&document.querySelector('.rail a.active').textContent==='Actions'`));
 await navigate('verification');assert('Work does not auto-verify',await evaluate(`document.querySelector('main').textContent.includes('Pending')`));
 await navigate('mini');await evaluate(`document.querySelector('#view-select').value='empty';document.querySelector('#view-select').dispatchEvent(new Event('change',{bubbles:true}))`);
 assert('Empty state withholds money',await evaluate(`document.querySelector('main').textContent.includes('No evidence in this window')&&!document.querySelector('main').textContent.includes('$3.31')`));
 await navigate('cold');await evaluate(`document.querySelector('.tabs a[href="#/cold-foundation"]').click()`);await pause(40);
 assert('Cold shell retains site context',await evaluate(`document.querySelector('h1').textContent==='GreenHarvest Cold Room'`));
 for(const s of manifest.filter(x=>x.root==='Sites')){await navigate(s.id);
  assert(`${s.id}: no Lab route or simulator wording in site page`,await evaluate(`!document.querySelector('main a[href="#/lab"]')&&!/Lab run|Private truth|private world/i.test(document.querySelector('main').textContent)`));}
 await navigate('mini');
 assert('Mini overview cards use canonical assessments only',await evaluate(`[...document.querySelectorAll('.cards.five .metric-value')].every(e=>['Healthy','Watch','Needs attention','Degraded','Unknown'].includes(e.textContent.trim()))`));
 assert('Mini overview shows the causal strip',await evaluate(`document.querySelectorAll('.timeline-event').length===5`));
 await navigate('sitefindings');await evaluate(`document.querySelector('[data-site-lens="Opportunities"]').click()`);
 assert('Site lens filters in place',await evaluate(`location.hash==='#/sitefindings'&&document.querySelectorAll('#site-findings tbody tr').length===1&&document.querySelector('#site-findings').textContent.includes('F-109')`));
 for(const id of ['sitework','cold-work','ev-work']){await navigate(id);assert(`${id}: Actions | Incidents | Maintenance subtabs`,await evaluate(`[...document.querySelectorAll('.subtabs a')].map(a=>a.textContent.split(' ')[0]).join('|')==='Actions|Incidents|Maintenance'`));}
 await navigate('sitework-incidents');assert('Empty site work state is explicit',await evaluate(`document.querySelector('.empty').textContent.includes('No incidents at this site')`));
 for(const id of ['evidence','cold-evidence','ev-evidence']){await navigate(id);assert(`${id}: shared evidence layout`,await evaluate(`document.querySelectorAll('main table').length===2&&document.querySelector('.subtabs').textContent.includes('Analysis')`));}
 for(const id of ['financials','cold-financials','ev-financials']){await navigate(id);assert(`${id}: bridge keeps basis, confidence and source`,await evaluate(`['Basis','Confidence','Source'].every(h=>[...document.querySelectorAll('main th')].some(t=>t.textContent===h))`));}
 await navigate('coldbackup');assert('Cold backup separates backup from refrigeration failure',await evaluate(`document.querySelector('main').textContent.includes('The backup failed; the refrigeration did not.')`));
 await navigate('dispatch');await evaluate(`document.querySelector('[data-interval="3"]').click()`);await pause(40);
 assert('Selected block follows selection',await evaluate(`document.querySelector('.drawer')&&[...document.querySelectorAll('main h2')].some(h=>h.textContent.includes('15:05–15:20'))`));
 await evaluate(`document.querySelector('[data-close]').click()`);
 await navigate('ev');assert('EV shell has distinct service content',await evaluate(`document.querySelector('main').textContent.includes('Buses ready to run')&&!document.querySelector('main').textContent.includes('Generator support')`));
 await evaluate(`document.querySelector('[data-notes]').click();const t=document.querySelector('#review-note');t.value='Browser review smoke check';t.dispatchEvent(new Event('input',{bubbles:true}));document.querySelector('[data-close]').click();document.querySelector('[data-notes]').click()`);
 assert('Review notes retained locally',await evaluate(`document.querySelector('#review-note').value==='Browser review smoke check'`));
 await evaluate(`localStorage.removeItem('assetops-v70-review-notes');document.querySelector('[data-close]').click()`);
 const shot0=async name=>{mkdirSync(join(dir,'previews'),{recursive:true});const p=await send('Page.captureScreenshot',{format:'png'});writeFileSync(join(dir,'previews',`${name}.png`),Buffer.from(p.data,'base64'));};
 const switchTo=async d=>{await evaluate(`{const e=document.querySelector('#site-switch');e.value=${JSON.stringify(d)};e.dispatchEvent(new Event('change',{bubbles:true}));}`);await pause(60);};
 for(const sc of manifest){await navigate(sc.id);
  assert(`${sc.id}: no Simulated badge in page chrome`,await evaluate(`!/Simulated/.test(document.querySelector('.heading-actions')?.textContent||'')&&!document.querySelector('main .period-bar')`));
  if(sc.root==='Sites'&&sc.section&&!sc.gtabs)assert(`${sc.id}: site and window in top bar; provenance beside site name`,await evaluate(`Boolean(document.querySelector('.topbar #site-switch')&&document.querySelector('.topbar [data-range-toggle]')&&document.querySelector('.title-row .prov-tag'))`));}
 for(const id of ['scenarios','cold-scenarios','ev-scenarios']){await navigate(id);assert(`${id}: Scenarios placeholder`,await evaluate(`document.querySelector('.subtabs a.active').textContent==='Scenarios'&&document.querySelector('.empty').textContent.includes('No scenario defined yet')`));}
 await navigate('findings');assert('Global Findings lists F-108 and F-119',await evaluate(`['F-108','F-119'].every(t=>document.querySelector('#findings-table').textContent.includes(t))`));
 await navigate('portfolio');assert('Portfolio lists F-108 and F-119',await evaluate(`['F-108','F-119'].every(t=>document.querySelector('#portfolio-findings').textContent.includes(t))&&document.querySelector('#portfolio-result-count').textContent==='6 findings'`));
 await navigate('cold-sld');assert('Cold-room diagram is hybrid',await evaluate(`['DC BUS','Solar array','Battery','Grid supply','Backup generator','Transfer','Compressor CMP-003'].every(t=>document.querySelector('svg.sld').textContent.includes(t))`));
 await navigate('mini');await evaluate(`document.querySelector('[data-range-toggle]').click();`);await pause(60);await shot0('date-window-topbar');await evaluate(`document.querySelector('[data-range-toggle]').click();`);
 for(const id of ['portfolio','sites','assets','findings','actions','incidents','maintenance','globalevidence','globalfinancials']){await navigate(id);
  assert(`${id}: window picker in top bar`,await evaluate(`Boolean(document.querySelector('.topbar [data-range-toggle] .range-name'))&&document.querySelector('.topbar .range-name').textContent.startsWith('Window:')`));
  await evaluate(`document.querySelector('[data-range-toggle]').click();document.querySelector('[data-range="7d"]').click()`);
  assert(`${id}: window picker works`,await evaluate(`document.querySelector('.range-name').textContent==='Window: Last 7 days'&&document.querySelector('#topbar-window').textContent.includes('30 Sep')&&document.querySelectorAll('.range-pop .period-strip div').length===6`));
  await evaluate(`document.querySelector('[data-range="event"]').click()`);}
 await navigate('lab');assert('Lab shell keeps its own window label',await evaluate(`!document.querySelector('[data-range-toggle]')`));
 await navigate('portfolio');await evaluate(`document.querySelector('[data-range-toggle]').click();document.querySelector('[data-range="30d"]').click()`);await navigate('dispatch');
 assert('Window persists from Portfolio into a site',await evaluate(`document.querySelector('.range-name').textContent==='Window: Last 30 days'`));await evaluate(`document.querySelector('[data-range-toggle]').click();document.querySelector('[data-range="event"]').click()`);
 await navigate('portfolio');await evaluate(`document.querySelector('[data-range-toggle]').click()`);await pause(60);await shot0('window-picker-portfolio');await evaluate(`document.querySelector('[data-range-toggle]').click()`);
 let confChips=0;
 for(const sc of manifest){await navigate(sc.id);
  assert(`${sc.id}: no plain Low confidence without a cause`,await evaluate(`[...document.querySelectorAll('main .badge, main td')].filter(e=>/^(Data )?(Confidence: )?Low$|^(Data )?Confidence: Medium$/.test(e.textContent.trim())&&!e.querySelector('[data-conf]')&&!e.closest('[data-conf]')).length===0`));
  const keys=await evaluate(`[...new Set([...document.querySelectorAll('main [data-conf]')].map(c=>c.dataset.conf))]`);
  for(const k of keys){confChips++;await evaluate(`document.querySelector('main [data-conf="${k}"]').click()`);
   assert(`${sc.id}: ${k} names its causes with a working call to action`,await evaluate(`(()=>{const p=document.querySelector('.conf-pop');if(!p)return false;const cs=[...p.querySelectorAll('.conf-cause')];return cs.length>0&&cs.every(c=>c.querySelector('.cause-tag')&&c.querySelector('p').textContent.length>20&&((c.querySelector('a[href^="#/"]')&&window.mockupManifest.some(s=>'#/'+s.id===c.querySelector('a').getAttribute('href')))||c.querySelector('[data-new-action]')))})()`));
   await evaluate(`document.body.click()`);
   assert(`${sc.id}: ${k} popover closes`,await evaluate(`!document.querySelector('.conf-pop')`));}}
 assert('Confidence chips found across the mock-up',confChips>=15,String(confChips));
 await evaluate(`stage.selected=0`);await navigate('dispatch');await evaluate(`document.querySelector('main [data-conf="f104"]').click()`);await pause(60);await shot0('confidence-popover');
 await evaluate(`document.querySelector('.conf-pop a[href^="#/"]').click()`);await pause(60);
 assert('Confidence call to action navigates',await evaluate(`location.hash==='#/sitework'&&!document.querySelector('.conf-pop')`));
 await navigate('ev');await evaluate(`document.querySelector('main [data-conf="f130"]').click()`);await evaluate(`document.querySelector('.conf-pop [data-new-action]').click()`);
 assert('Pre-filled new action opens from a cause',await evaluate(`document.querySelector('.drawer').textContent.includes('New action · pre-filled')&&document.querySelector('.drawer').textContent.includes('Export charger 2 diagnostics')`));
 await evaluate(`document.querySelector('[data-close]').click()`);
 await navigate('dispatch');await evaluate(`document.querySelector('[data-interval="0"]').click()`);await evaluate(`document.querySelector('.drawer [data-conf]').click()`);
 assert('Evidence drawer confidence explains itself',await evaluate(`Boolean(document.querySelector('.conf-pop'))&&document.querySelector('.conf-pop').textContent.includes('Source availability')`));
 await evaluate(`document.body.click();document.querySelector('[data-close]').click()`);await evaluate(`stage.selected=0`);
 for(const id of ['readiness','cold-readiness','ev-readiness']){await navigate(id);
  assert(`${id}: gateway status panel`,await evaluate(`(()=>{const g=document.querySelector('.gw-panel');if(!g)return false;const t=g.textContent;return ['Status','Availability','Data completeness','Clock and delivery','Connected sources','Effect on readiness and confidence','Last message'].every(x=>t.includes(x))&&g.querySelectorAll('.gw-cell').length>=4&&[...g.querySelectorAll('a[href^="#/"]')].every(a=>window.mockupManifest.some(s=>'#/'+s.id===a.getAttribute('href')))&&!/simulat|envelope|\brun\b/i.test(t)})()`));
  assert(`${id}: Readiness subtab active`,await evaluate(`document.querySelector('.subtabs a.active').textContent==='Readiness'`));}
 await navigate('readiness');const gwEvent=await evaluate(`document.querySelector('.gw-panel .cards').textContent`);
 await evaluate(`document.querySelector('[data-range-toggle]').click();document.querySelector('[data-range="30d"]').click()`);
 assert('Gateway figures follow the analysis window',await evaluate(`(()=>{const t=document.querySelector('.gw-panel').textContent;return t.includes('7 Sep')&&/[1-9]\\d* outages?/.test(t)&&document.querySelectorAll('.gw-cell').length===30})()`)&&gwEvent.includes('100%'));
 await evaluate(`document.querySelector('[data-range="event"]').click();document.body.click()`);
 await navigate('dispatch');await evaluate(`document.querySelector('main [data-conf="f104"]').click()`);
 assert('Source-availability cause links to gateway status',await evaluate(`Boolean(document.querySelector('.conf-pop a[href="#/readiness"]'))`));
 await evaluate(`document.body.click()`);
 await navigate('readiness');await evaluate(`document.querySelector('.gw-panel').scrollIntoView({block:'start'});window.scrollBy(0,-20)`);await pause(80);await shot0('gateway-status');await evaluate('window.scrollTo(0,0)');
 const shotFull=async name=>{const p=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});writeFileSync(join(dir,'previews',`${name}.png`),Buffer.from(p.data,'base64'));};
 const has=async(t)=>evaluate(`document.querySelector('main').textContent.includes(${JSON.stringify(t)})`);
 await navigate('portfolio');assert('Rail: Work holds Operational records; Admin holds Settings',await evaluate(`(()=>{const g=[...document.querySelectorAll('.rail-group')].map(x=>x.textContent);return g.some(t=>t.startsWith('WORK')&&['Actions','Incidents','Maintenance','Operational records'].every(k=>t.includes(k)))&&g.some(t=>t.startsWith('ADMIN')&&t.includes('Settings'))})()`));
 await navigate('assets');assert('Assets index: condition, evidence, findings, work and warranty columns',await evaluate(`['Condition','Evidence','Open findings','Open work','Warranty'].every(h=>[...document.querySelectorAll('main th')].some(t=>t.textContent===h))`));
 await evaluate(`document.querySelector('[data-asset-filter="Warranty attention"]').click()`);assert('Warranty attention filter',await evaluate(`document.querySelectorAll('#asset-table tbody tr').length===4`));
 await navigate('asset-warranty');assert('Battery warranty: terms against evidence, cover at risk, claim chip',await evaluate(`[...document.querySelectorAll('.tabs a')].map(a=>a.textContent).join('|')==='Overview|Health|Performance|Configuration|Work|Evidence|Warranty'&&document.querySelector('.tabs a.active').textContent==='Warranty'&&['Northwind Storage','Cell temperature','Cannot show','What puts cover at risk','Highland Energy Supplies'].every(t=>document.querySelector('main').textContent.includes(t))&&Boolean(document.querySelector('[data-conf="batwarranty"]'))`));
 await navigate('sites');assert('Sites: Directory and three creation routes as subtabs; In setup panel',await evaluate(`[...document.querySelectorAll('.tabs a')].map(a=>a.textContent).join('|')==='Directory|Add site · form|From template|Batch upload|Setup history'&&document.querySelector('main').textContent.includes('In setup')&&document.querySelector('main').textContent.includes('MG-LAKE-01')`));
 for(const id of ['site-create-form','site-create-template','site-batch-upload','site-setup-history']){await navigate(id);assert(`${id}: estate-level page, no site selector or site provenance tag`,await evaluate(`!document.querySelector('#site-switch')&&!document.querySelector('.prov-tag')&&Boolean(document.querySelector('[data-range-toggle]'))`));}
 await navigate('site-create-form');assert('Site form: six steps, blocking checks clear, gaps expected at creation',await evaluate(`document.querySelectorAll('.reg-steps li').length===6&&document.querySelectorAll('.reg-check.amber').length===4&&document.querySelector('main').textContent.includes('Gateway not connected yet')&&Boolean(document.querySelector('[data-site-activate]'))`));
 await shotFull('site-create-form');
 await navigate('site-create-template');await evaluate(`document.querySelector('[data-tpl="dc"]').click()`);
 assert('Template preview redraws its diagram with nothing reporting',await evaluate(`document.querySelector('svg.sld').textContent.includes('DC BUS')&&[...document.querySelectorAll('svg.sld circle[r="5.5"]')].every(c=>c.getAttribute('fill')==='#fff')&&document.querySelectorAll('.tpl-card').length===4&&!/CMP-003|GEN-CR-01|TMP-003/.test(document.querySelector('svg.sld').textContent)`));
 await evaluate(`document.querySelector('[data-tpl="cold"]').click()`);await shotFull('site-create-template');
 await navigate('site-batch-upload');assert('Batch preview: per-row results',await evaluate(`document.querySelectorAll('main table tbody tr').length===6&&document.querySelectorAll('main td .badge.red').length===3`));
 await shotFull('site-batch-upload');
 await evaluate(`document.querySelector('[data-batch-fix="3"]').click()`);assert('Fixing a row clears its error',await evaluate(`document.querySelectorAll('main td .badge.red').length===2`));
 await evaluate(`document.querySelector('[data-batch-import]').click()`);assert('Import shows results and drafts',await evaluate(`document.querySelector('main').textContent.includes('Import complete')&&document.querySelectorAll('main td .badge.green').length===4`));
 await navigate('sites');assert('Imported drafts appear In setup',await evaluate(`document.querySelector('main').textContent.includes('MG-SUN-01')&&document.querySelector('main').textContent.includes('CR-NG-01')`));
 await navigate('site-setup-history');assert('Setup history records the import',await evaluate(`document.querySelector('main').textContent.includes('Batch imported')`));
 await evaluate(`stage.batchDone=false;stage.batchFixed=[];stage.tpl='cold'`);
 await navigate('assets');assert('Assets index opens BAT-001 at Overview',await evaluate(`Boolean(document.querySelector('#asset-table a[href="#/asset-overview"]'))`));
 await navigate('health');assert('Site Health opens BAT-001 at Overview',await evaluate(`Boolean(document.querySelector('main a[href="#/asset-overview"]'))`));
 await navigate('asset-overview');assert('Asset Overview: identity, provenance, status with cause chip, five cards, timeline, attention, money, next step',await evaluate(`document.querySelector('.tabs a.active').textContent==='Overview'&&document.querySelector('.tabs a').textContent==='Overview'&&Boolean(document.querySelector('.asset-id .prov-tag'))&&Boolean(document.querySelector('[data-conf="batcond"]'))&&document.querySelectorAll('.cards.five .metric').length===5&&document.querySelectorAll('.timeline-event').length===4&&['Needs attention','Money consequence','Next step','$64,000','Northwind Storage'].every(t=>document.querySelector('main').textContent.includes(t))`));
 await evaluate(`document.querySelector('[data-range-toggle]').click();document.querySelector('[data-range="30d"]').click()`);
 assert('Asset Overview follows the window',await evaluate(`document.querySelectorAll('.timeline-event').length===5&&document.querySelector('main').textContent.includes('5 reserve breaches in this window')`));
 await evaluate(`document.querySelector('[data-range="event"]').click();document.body.click()`);
 await shotFull('asset-overview');
 await navigate('assets-warranty');assert('Warranty and vendors: repair or claim, vendor performance',(await has('Repair or claim · CHG-002 connector fault'))&&(await has('Vendor performance'))&&(await has('Cover at risk')));
 await navigate('asset-register');assert('Registration draft shows validation states',await evaluate(`document.querySelectorAll('.reg-check.amber').length>=3&&document.querySelectorAll('.reg-steps li').length===6`));
 await evaluate(`document.querySelector('[data-reg-submit]').click()`);assert('Registration submit explains validation',await evaluate(`document.querySelector('.toast').textContent.includes('draft')`));
 await navigate('asset-edit');assert('Edit registration keeps Configuration tab active',await evaluate(`document.querySelector('.tabs a.active').textContent==='Configuration'`));
 await navigate('findings');assert('Findings lenses are the subtab row',await evaluate(`[...document.querySelectorAll('.tabs a')].map(a=>a.textContent).join('|')==='All findings|Cost|Risks|Opportunities'`));
 await evaluate(`document.querySelector('[data-fstate="Recommendation"]').click()`);assert('Workflow state is a filter, not a lens',await evaluate(`document.querySelectorAll('#findings-table tbody tr').length===1&&document.querySelector('#findings-table').textContent.includes('F-109')`));
 await navigate('findings-risks');assert('Risks lens',await evaluate(`document.querySelectorAll('#findings-table tbody tr').length===4`));
 await navigate('finding');assert('Finding detail: priority, confidence, state, claim, lens and where to look next',(await has('Where to look next'))&&(await has('Lens: Cost'))&&(await has('Priority: High')));
 await navigate('dispatch');await evaluate(`document.querySelector('[data-interval="1"]').click()`);assert('Evidence drawer: chain with basis, settings at the time',await evaluate(`['Evidence chain','Observed absence','Settings at the time','Approvals or overrides'].every(t=>document.querySelector('.drawer').textContent.includes(t))`));await evaluate(`document.querySelector('[data-close]').click();stage.selected=0`);
 await navigate('maintenance-preventive');assert('Maintenance: Corrective | Preventive, plan with due states',await evaluate(`[...document.querySelectorAll('.tabs a')].map(a=>a.textContent).join('|')==='Corrective|Preventive · scheduled'&&document.querySelectorAll('main table tbody tr').length===5&&document.querySelector('main').textContent.includes('Overdue')`));
 await navigate('wr-record');assert('Maintenance record with managed header',await evaluate(`document.querySelector('.tabs a.active').textContent==='Maintenance record'&&document.querySelectorAll('.mheader div').length===5`));
 for(const id of ['verification','incident','workverification'])
  {await navigate(id);assert(`${id}: managed-object header`,await evaluate(`document.querySelectorAll('.mheader div').length===5`));}
 await navigate('oprecords');await evaluate(`document.querySelector('[data-rec-type="Manual reading"]').click()`);assert('Operational records filter by type',await evaluate(`document.querySelectorAll('#oprec-table tbody tr').length===3`));
 await navigate('settings-policies');await evaluate(`document.querySelector('[data-policy-save]').click()`);assert('Policies save as a new version',await evaluate(`document.querySelectorAll('main table')[0].querySelectorAll('tbody tr').length===7&&document.querySelector('.toast').textContent.includes('v4')`));
 await navigate('settings-tenant');assert('Tenant settings keep the workspace out of operator wording',(await has('Simulation workspace'))&&!(await has('Simulator Lab'))&&(await has('Users and roles')));
 await navigate('financials');assert('Site Financials reads the warranty record',await has('covered by warranty'));
 await navigate('ev-financials');assert('EV Financials shows repair or claim line',await has('$850 if repaired locally'));
 await evaluate(`document.querySelector('.toast')?.remove()`);
 for(const [id,name] of [['assets','assets-index'],['finding','finding-detail'],['oprecords','operational-records'],['asset-warranty','asset-warranty'],['asset-register','asset-register'],['maintenance-preventive','maintenance-preventive'],['settings-policies','settings-policies'],['assets-warranty','assets-warranty'],['settings-tenant','settings-tenant'],['wr-record','wr-record']]){await navigate(id);await pause(80);await shotFull(name);}
 for(const [from,to,expect] of [['sitework-incidents','cold','cold-work-incidents'],['coldbackup','mini','backup'],['temperature','ev','sessions'],['evidence-analysis','ev','ev-evidence-analysis'],['sld','cold','cold-sld'],['readiness','ev','ev-readiness']]){await navigate(from);await switchTo(to);assert(`Site switch ${from} → ${to} keeps the tab`,await evaluate(`location.hash==='#/${expect}'`),await evaluate('location.hash'));}
 await navigate('mini');await evaluate(`document.querySelector('[data-range-toggle]').click();document.querySelector('[data-range="30d"]').click()`);
 assert('30-day range updates window and figures',await evaluate(`document.querySelector('#topbar-window').textContent.includes('7 Sep')&&document.querySelector('.period-strip').textContent.includes('Reserve breaches5')`));
 await navigate('coldbackup');await evaluate(`document.querySelector('[data-range-toggle]').click();`);assert('Range persists across sites and tabs',await evaluate(`document.querySelector('#topbar-window').textContent.includes('30 days')&&document.querySelector('.period-strip').textContent.includes('2 of 3')`));
 await evaluate(`document.querySelector('[data-range="custom"]').click()`);await evaluate(`document.querySelector('#range-from').value='2026-10-01';document.querySelector('#range-to').value='2026-10-06';document.querySelector('[data-range-apply]').click()`);
 assert('Custom range applies',await evaluate(`document.querySelector('#period-label').textContent.startsWith('1 Oct – 6 Oct')`));
 await evaluate(`document.querySelector('[data-range="event"]').click()`);assert('Event window restores event labels',await evaluate(`document.querySelector('#topbar-window').textContent.includes('19:00–20:00')`));
 for(const id of ['sld','cold-sld','ev-sld']){await navigate(id);assert(`${id}: single line diagram rendered as product view`,await evaluate(`document.querySelectorAll('svg.sld circle').length>10&&!/simulat/i.test(document.querySelector('main section.panel').textContent)`));}
 await navigate('ev');assert('EV overview uses canonical cards and causal strip',await evaluate(`[...document.querySelectorAll('.cards.five .metric-value')].every(e=>['Healthy','Watch','Needs attention','Degraded','Unknown','Limited'].includes(e.textContent.trim()))&&document.querySelectorAll('.timeline-event').length===7`));
 await navigate('ev-recommendation');assert('EV recommendation names owner, consequence and criteria',await evaluate(`['Charging operations lead','What it is worth','Declare success before evaluating'].every(t=>document.querySelector('main').textContent.includes(t))`));
 await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:false});
 for(const id of ['portfolio','mini','dispatch','cold','ev','lab','sld','ev-recommendation','coldbackup','site-create-form','site-create-template','site-batch-upload']){await navigate(id);assert(`${id}: mobile containment`,await evaluate('document.documentElement.scrollWidth<=innerWidth'));}
 await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1100,deviceScaleFactor:1,mobile:false});
 mkdirSync(join(dir,'previews'),{recursive:true});
 await evaluate(`document.querySelector('.toast')?.remove();stage.accepted=false;stage.selected=0;`);
 for(const id of ['portfolio','mini','dispatch','cold','ev','verification','lab','temperature','coldbackup','service','fuel','health','evidence','cold-evidence','financials','cold-financials','sitefindings','sitework','cold-work-incidents','ev-recommendation','sessions','sld','cold-sld','ev-sld','ev-evidence','ev-financials','scenarios','findings','readiness','cold-readiness','ev-readiness']){
  await navigate(id);await pause(100);
  const p=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});
  writeFileSync(join(dir,'previews',`${id}.png`),Buffer.from(p.data,'base64'));
 }
 const shot=async name=>{const p=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});writeFileSync(join(dir,'previews',`${name}.png`),Buffer.from(p.data,'base64'));};
 await navigate('mini');await evaluate(`document.querySelector('[data-range-toggle]').click();document.querySelector('[data-range="30d"]').click()`);await pause(80);await shot('date-range-30-days');
 await navigate('dispatch');await evaluate(`document.querySelector('[data-range-toggle]').click();document.querySelector('[data-range="custom"]').click()`);await evaluate(`document.querySelector('#range-from').value='2026-10-01';document.querySelector('#range-to').value='2026-10-06';document.querySelector('[data-range-apply]').click()`);await pause(80);await shot('date-range-custom');
 await evaluate(`document.querySelector('[data-range="event"]').click()`);
 await navigate('sitework');await switchTo('ev');await pause(80);await shot('site-switch-ev-work');
 await navigate('cold-findings');await switchTo('ev');await evaluate(`document.querySelector('#site-switch').focus()`);await pause(80);await shot('site-switch-ev-findings');
 await navigate('dispatch');await evaluate(`document.querySelector('[data-interval="1"]').click()`);
 const drawer=await send('Page.captureScreenshot',{format:'png'});writeFileSync(join(dir,'previews','evidence-drawer.png'),Buffer.from(drawer.data,'base64'));
 await send('Page.navigate',{url:base+'?book=1'});await pause(400);
 await send('Emulation.setEmulatedMedia',{media:'print'});
 const pages=await evaluate(`[...document.querySelectorAll('.bookpage')].map(e=>({id:e.id,height:e.getBoundingClientRect().height,width:e.getBoundingClientRect().width}))`);
 const max=Math.max(...pages.map(p=>p.height));
 const pageHeight=Math.max(1200,Math.ceil(max+30));
 checks.push({label:'PDF page height (v7.0: outcome screens are taller, so pages may be portrait)',passed:true,detail:`${1728} x ${pageHeight} · tallest: ${pages.slice().sort((a,b)=>b.height-a.height).slice(0,5).map(p=>p.id+':'+Math.round(p.height)).join(' ')}`});
 await evaluate(`{const s=document.createElement('style');s.textContent='@page{size:18in ${pageHeight/96}in;margin:0}';document.head.appendChild(s);}`);
 const pdf=await send('Page.printToPDF',{printBackground:true,preferCSSPageSize:true,generateDocumentOutline:true});
 writeFileSync(join(dir,'AssetOps-v70-Screen-Review.pdf'),Buffer.from(pdf.data,'base64'));
 const portfolioPdf=await send('Page.printToPDF',{printBackground:true,preferCSSPageSize:true,pageRanges:'1'});
 writeFileSync(join(dir,'AssetOps-Portfolio-v2.pdf'),Buffer.from(portfolioPdf.data,'base64'));
 assert('No browser runtime errors',errors.length===0,JSON.stringify(errors));
 const report={checked_at:new Date().toISOString(),screens:manifest.length,book_pages:pages.length,page_height_px:pageHeight,checks,measurements,print_measurements:pages,errors};
 writeFileSync(join(dir,'browser-review.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({screens:manifest.length,bookPages:pages.length,checks:checks.length,maxScreenHeight:max,pdfPageHeight:pageHeight,errors:errors.length},null,2));
}finally{ws?.close();chrome.kill();}
