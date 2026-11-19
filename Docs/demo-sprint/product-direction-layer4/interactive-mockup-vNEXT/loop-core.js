/* ===== Layer 4 rev 4 mock-up · core =====
   Design mock-up only: no API calls, no product code. Every figure is read from MANIFEST (fixtures.js, generated
   from ../demo-site-scenario-manifest.yaml with the private oracle removed) or derived by arithmetic that is shown
   on screen and listed in fixture-mapping.md. Outcomes are computed from declared factor structures (main design
   §2.1–2.2): factors are observed, the structure composes them, deviations are attributed to the factor where
   they arise; a residual appears only where a leaf factor is not observed. */
/* Rev 13 (spec §7, review M3): one renderer for every manifest string. {fig:<path>} is filled from the evaluation
   (DERIVED, derived-values.json), {fig:-<path>} with the negated value; {rec:<path>} restates a manifest record. Paths are
   dotted; a bracket names a key with special characters, or picks a list item by its tenant / site / id / driver / measure /
   batch field (a number picks by position). Numbers: thousands separators, 2 decimals only when not whole; ISO dates as
   "9 Nov". A placeholder that does not resolve renders "not available" and is listed in TPL.unresolved (the audit fails on it). */
const TPL = {fig:0, rec:0, strings:0, unresolved:[]};
function tplPath(root, path){let o=root;for(const m of path.matchAll(/\[([^\]]+)\]|([^.\[\]]+)/g)){const k=m[1]??m[2];if(o==null)return undefined;
 if(Array.isArray(o))o=/^\d+$/.test(k)?o[+k]:o.find(x=>x&&typeof x==='object'&&[x.tenant,x.site,x.id,x.driver,x.measure,x.batch].includes(k));else o=o[k];}return o;}
function tplFmt(v,neg){if(typeof v==='number'){const x=neg?-v:v,w=Number.isInteger(Math.round(x*100)/100)&&Math.abs(x-Math.round(x))<1e-9;return (x<0?'−':'')+Math.abs(x).toLocaleString('en-US',{minimumFractionDigits:w?0:2,maximumFractionDigits:w?0:2});}
 if(typeof v==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(v)){const [,mo,d]=v.split('-');return `${+d} ${['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][+mo-1]}`;}
 if(typeof v==='string'||typeof v==='number')return String(v);return undefined;}
function tpl(s){if(typeof s!=='string'||s.indexOf('{')<0)return s;let hit=false;
 const out=s.replace(/\{(fig|rec):(-?)([^{}]+)\}/g,(m,kind,neg,path)=>{hit=true;TPL[kind]++;const v=tplFmt(tplPath(kind==='fig'?DERIVED:TPL.raw,path),!!neg);if(v===undefined){TPL.unresolved.push(m);return 'not available';}return v;});
 if(hit)TPL.strings++;return out;}
window.__TPL_RENDERING = true; /* lets tools/rendered_strings.cjs ignore this one-time walk */
TPL.raw = JSON.parse(JSON.stringify(MANIFEST));
(function renderManifestStrings(o){if(Array.isArray(o)){o.forEach((v,i)=>{if(typeof v==='string')o[i]=tpl(v);else if(v&&typeof v==='object')renderManifestStrings(v);});return;}
 for(const k of Object.keys(o)){const v=o[k];if(typeof v==='string')o[k]=tpl(v);else if(v&&typeof v==='object')renderManifestStrings(v);}})(MANIFEST);
window.__TPL_RENDERING = false; window.TPL = TPL;
const M = MANIFEST, AS_OF = M.as_of;
const LS = {op:'lakeside', budget:5000, loi:true, agg:true, tou:true};
try{const o=sessionStorage.getItem('l4-op');if(['lakeside','harvest','metro'].includes(o))LS.op=o;}catch{}
const OPS = {
 lakeside:{t:M.tenants[0],ti:0,name:'Lakeside Power',vertical:'mini',kind:'contribution',sites:['kobo','kisiwa','mto'],crewWord:'crew visits',crewKey:'crew_visits_nov',typeWord:'village mini-grids'},
 harvest:{t:M.tenants[1],ti:1,name:'Harvest Cold Network',vertical:'cold',kind:'contribution',sites:['mwea','thika','kirinyaga'],crewWord:'technician visits',crewKey:'technician_visits_nov',typeWord:'pay-as-you-store cold rooms'},
 metro:{t:M.tenants[2],ti:2,name:'Metro Bus Depots',vertical:'ev',kind:'cost',sites:['embakasi','kasarani','ruiru'],crewWord:'technician visits',crewKey:'technician_visits_nov',typeWord:'captive electric bus depots'}};
const SK = {
 kobo:{op:'lakeside',i:0,name:'Kobo',type:'Mini-grid',v70:'mini'},kisiwa:{op:'lakeside',i:1,name:'Kisiwa',type:'Mini-grid'},mto:{op:'lakeside',i:2,name:'Mto',type:'Mini-grid'},
 mwea:{op:'harvest',i:0,name:'Mwea',type:'Cold room A'},thika:{op:'harvest',i:1,name:'Thika',type:'Cold room B',v70:'cold'},kirinyaga:{op:'harvest',i:2,name:'Kirinyaga',type:'Cold room C'},
 embakasi:{op:'metro',i:0,name:'Embakasi',type:'Bus depot'},kasarani:{op:'metro',i:1,name:'Kasarani',type:'Bus depot'},ruiru:{op:'metro',i:2,name:'Ruiru',type:'Bus depot',v70:'ev'}};
const V70SITE = {mini:'kobo',cold:'thika',ev:'ruiru'}, DOMAIN_OP = {mini:'lakeside',cold:'harvest',ev:'metro'};
const siteM = k => OPS[SK[k].op].t.sites[SK[k].i];
const sitePath = k => `tenants[${OPS[SK[k].op].ti}].sites[${SK[k].i}]`;
const OPN = () => OPS[LS.op];
function opName(){return OPN().name;}
function siteOverviewFor(domain){return V70SITE[domain]?`site/${V70SITE[domain]}`:'sites';}

/* ---------- formatting (plain words, "$" with separators, no ISO dates) ---------- */
const r2 = x => Math.round(x*100)/100;
function usd(n,sign=false){if(n===null||n===undefined)return 'not available yet';const neg=n<-0.0001,a=Math.abs(r2(n));const s=a.toLocaleString('en-US',{minimumFractionDigits:Number.isInteger(a)?0:2,maximumFractionDigits:2});return (neg?'−':(sign&&n>0.0001?'+':''))+'$'+s;}
const usd2 = n => '$'+r2(n).toFixed(2);
const num = (n,d=0) => n===null||n===undefined?'not available yet':Number(n).toLocaleString('en-US',{maximumFractionDigits:d});
const pct = (x,d=0) => (x*100).toFixed(d)+'%';
const MON=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
function fdate(iso){const [y,m,d]=iso.slice(0,10).split('-').map(Number);return `${d} ${MON[m-1]}${y!==2026||m<9?' '+y:''}`;}
const daysUntil = iso => Math.round((Date.parse(iso.slice(0,10))-Date.parse(AS_OF))/864e5);
const vh = t => `<span class="vh">${t}</span>`;
const cap = t => t?t[0].toUpperCase()+t.slice(1):'';

/* ---------- evidence classes, in words ---------- */
const CLS = {ECONOMIC_ACTUAL:['Emulated','rec'],RECORDED:['Emulated','rec'],ESTIMATED:['Estimated','est'],MEASURED:['Measured','rec'],DERIVED:['Calculated from records','der'],
 MODELLED:['Modelled','mod'],EXPOSURE:['At stake (not money)','stake'],VERIFIED:['Verified','ver'],MISSING:['Not available yet','na'],ECONOMIC_ACTUAL_FORWARD:['Emulated','rec'],
 PLAN:['Emulated','rec'],QUOTE:['Quoted','der'],NA:['Not available yet','na'],CONTRACT:['Emulated','rec']};
const ec = c => {const [t,k]=CLS[c]||[c,'na'];return `<span class="ec ec-${k}">${t}</span>`;};
const ecw = c => (CLS[c]||[c])[0];
/* a figure that opens the evidence drawer (two interactions to source) */
const fig = (key,text) => `<button class="ev-num" data-evd="${key}" aria-haspopup="dialog">${text}${vh(' · show how this is worked out')}</button>`;

/* ---------- outcome lenses (main design §3.1): outcomes over one factor structure; never summed ---------- */
const LENS = {grow:['Grow revenue','sun'],optimize:['Optimize cost and efficiency','money'],protect:['Protect asset and capital','asset'],assure:['Assure performance and returns','evidence']};
const lensTag = l => `<span class="lens lens-${l}">${LENS[l][0]}</span>`;
/* ---------- home categories (design rev 16.11 §2.0, register calls 17 and 18; worked-portfolios §1.0 "Home categories" row) ----------
   Read from the data's registry (MANIFEST.home_categories), never typed here and never inherited from a parent. A mock-up node
   is matched to its registry row by NODE_KEY (the evaluated node its figure reads); a bridge row by its factor
   (home_categories.bridge_drivers). The outcome at the root is `above` the headings. Potential (capacity with no customer)
   sits beside Grow, never as Grow's actual. A node with no registry row is a GAP: it shows no heading and is listed in
   HOME_GAPS; its heading is never guessed. */
const HC = M.home_categories||{nodes:{},potential:{},bridge_drivers:{},decisions:[]};
const VKEY = {mini:'MINI_GRID',cold:'COLD_CHAIN',ev:'EV_DEPOT_CAPTIVE'};
const NODE_KEY = {
 mini:{root:'contribution',rev:'revenue',billed:'billed_kwh',deliv:'delivered_kwh',loss:'technical_loss_kwh',lossx:'unexplained_loss_kwh',meter:'metered_kwh',adj:'adjustments_kwh',
  tariff:'tariff',cash:'collected',cost:'cost_to_serve',diesel:'fuel_cost',litres:'diesel_l',fb:'diesel_l',dprice:'diesel_price',om:'om',staff:'staff'},
 cold:{root:'contribution',rev:'revenue',cd:'crate_days',charge:'crate_days',idle:{potential:'idle_capacity'},rate:'rate',cash:'received',cost:'cost_to_serve',elec:'energy',kwh:'kwh',
  kmodel:'kwh_model',kexcess:'excess_kwh',staff:'staff',maint:'maint',liab:'liability'},
 ev:{root:'cost_per_departure_met',dep:'departures_met',chg:'deliverable_kwh_night',conn:'charger_days_out_of_service',cost:'cost_to_serve',bill:'energy_cost',
  peak:n=>n.unit==='$'?'peak_cost':'peak_kwh',off:'offpeak_cost',demand:'demand_cost',maxkw:'max_kw',pen:'penalties',maint:'maintenance',
  resid:{heading:['optimize','O1'],why:'the part of a bill-total target that cannot be attributed (worked-portfolios §1.0, EV depot: Optimize, O1)'}}};
const HOME_GAPS = [];
function homeRow(v,key){const r=HC.nodes[VKEY[v]]?.[key];return Array.isArray(r)?r:null;}
function placeHomes(sk,root){const v=OPS[SK[sk].op].vertical,K=NODE_KEY[v];
 walk(root,n=>{let k=K[n.id];if(typeof k==='function')k=k(n);
  if(k&&typeof k==='object'){if(k.potential){const p=(HC.potential[VKEY[v]]||[]).find(x=>x.name===k.potential);if(p){n.lens='grow';n.potential=true;n.home='potential';n.obj=p.objective;n.hkey=p.name;return;}}
   else if(k.heading){[n.lens,n.obj]=k.heading;n.home='named';n.hkey=n.id;return;}k=null;}
  n.hvia=k?'node':null;if(!k&&n.driver){k=HC.bridge_drivers[n.driver];n.hvia=k?'factor':null;}
  const row=k?homeRow(v,k):null;n.hkey=k||null;
  if(row&&row[0]==='above'){n.lens=null;n.above=true;n.home='above';}
  else if(row&&['grow','optimize','protect','assure'].includes(row[0])){n.lens=row[0];n.obj=row[1];n.home='named';}
  else{n.lens=null;n.home='gap';HOME_GAPS.push({site:sk,node:n.id,key:k||null,label:n.label});}});
 return root;}
window.HOME_GAPS = HOME_GAPS;

/* ---------- factor names in plain words (manifest bridge key `driver` = a factor of the structure, rule R6) ---------- */
const FAC = {
 CANDIDATE_RUNNING:['Generator running while solar could carry the load (candidate running)'],
 DEMAND_VOLUME:['Customer consumption against target'],
EVENING_LOAD_GROWTH:['Generator needed for evening load growth'],
 UNEXPLAINED_RESIDUAL:['Fuel used beyond what the generator model explains'],SOLAR_SHORTFALL_NECESSARY_GEN:['Generator needed in a rainy month'],
 METER_MAPPING_UNBILLED:['Meters not mapped to customers after a meter swap'],AUTHORISED_ADJUSTMENT:['Approved clinic allowance'],EVENING_NECESSARY_GEN:['Generator needed in the evening'],
 OCCUPANCY_REVENUE:['Occupied crate-days against target'],OCCUPANCY_ENERGY_VOLUME:['Less electricity at lower occupancy (not a saving)'],ENERGY_EFFICIENCY:['Electricity above what occupancy explains'],
 CUSTOMER_COMPENSATION:['Compensation for crates downgraded after the 6 Oct backup failure'],PEAK_ENERGY_SHARE:['Share of charging at peak price'],DEMAND_CHARGE:['Monthly peak demand']};
const PLAIN = [[' (Necessary by dispatch classification of metered generator energy x declared consumption rate)',' (needed, by dispatch classification of metered generator energy × declared fuel use)'],[' (rainy month; all generator time Necessary by dispatch classification)',' (rainy month; every generator interval needed, by dispatch classification)'],[' (Necessary evening running by dispatch classification)',' (needed evening running, by dispatch classification)'],[/(\d[\d,]*) L x (\d+\.\d+): generator running while solar could carry the load \(dispatch-3\.2 Candidate; plan (\d+) L\); model-implied litres from metered generator energy x SFC/,'$1 L × $$$2: generator running while solar and the battery could carry the load (target $3 L); litres implied by metered generator energy × fuel use per kWh'],[' x ',' × '],['forward-feasible share of Candidate fuel','share a forward replay shows is avoidable; design value, to be reproduced from your data'],['Candidate by dispatch-3.2, not avoidable by forward replay','beyond need, not avoidable in the replay'],['(Necessary)','(needed)'],
 ['consumed minus modelled; investigate (MG-L5)','used minus modelled; being investigated'],['all generator time Necessary','every generator interval needed'],['within 2% tolerance, reported not investigated','within the 2% tolerance; reported, not investigated'],
 ['6 customers, meter swap 3 Oct not applied','6 customers; the 3 Oct meter swap was not applied to billing'],[/credit note (CN-\d+): (\d+) crates downgraded from export grade by QA, compensated at the declared (\d+) per crate/,'credit note $2 crates downgraded from export grade by quality inspection, compensated at the declared $$$3 a crate (credit note $1)'],
 ['less energy at lower occupancy (not a saving)','less electricity at lower occupancy (not a saving)'],['inside 5% tolerance','inside the 5% tolerance'],['above occupancy/ambient model','above the occupancy and temperature model'],
 ['more at peak than plan (55% vs 30%)','more at peak price than the target (55% against 30%)'],['0.12 premium','$0.12 a kWh peak premium'],[/monthly peak (\d+) kW vs plan (\d+) kW (?:x|×) (\d+)/,'monthly peak $1 kW against a $2 kW target × $$$3 a kW'],['vs','against'],['driver overtime','overtime']];
const plain = t => PLAIN.reduce((a,[f,r])=>f instanceof RegExp?a.replace(f,r):a.split(f).join(r),String(t??''));
function qtyOf(basis){const m=String(basis).match(/^([\d,]+(?:\.\d+)?) (kWh|L|crate-days)/);return m?[Number(m[1].replace(/,/g,'')),m[2]]:null;}

/* ---------- factor structures per site (outcome → factors → leaf factors) ---------- */
/* node: {id,label,how,unit,plan,actual,eff,dev,cls,lens,src,kids,dec,bound,residual,obs,note}
   eff = effect of this factor's deviation on the site outcome in $ (+ better), only where attributed. */
const UNIT = {'$':v=>usd(v),'$/kWh':v=>usd2(v)+' a kWh','$/L':v=>usd2(v)+' a litre','$/dep':v=>usd2(v),'$/cd':v=>usd2(v)+' a crate-day',kWh:v=>num(v)+' kWh',L:v=>num(v)+' L','crate-days':v=>num(v)+' crate-days','%':v=>v+'%',kW:v=>num(v)+' kW',dep:v=>num(v),'kWh/night':v=>num(v)+' kWh a night',n:v=>num(v)};
const fmtU = (v,u) => v===null||v===undefined?null:(UNIT[u]||num)(v);
function bridgeNode(sk,b,i,costSide){const q=qtyOf(b.basis),[label]=FAC[b.driver];const sg=costSide?-Math.sign(b.amount):Math.sign(b.amount);
 return {id:'f'+i,label,how:plain(b.basis),unit:q?q[1]:'$',dev:q?sg*q[0]:null,eff:b.amount,cls:b.class,driver:b.driver,residual:b.driver==='UNEXPLAINED_RESIDUAL',src:SRC_OF[b.driver]||'model',evd:`bridge:${sk}:${i}`,dec:DEC_OF_FACTOR[sk]?.[b.driver]};}
const SRC_OF = {CANDIDATE_RUNNING:'ems',DEMAND_VOLUME:'billing',METER_MAPPING_UNBILLED:'meterreg',AUTHORISED_ADJUSTMENT:'billing',EVENING_LOAD_GROWTH:'ems',SOLAR_SHORTFALL_NECESSARY_GEN:'ems',EVENING_NECESSARY_GEN:'ems',UNEXPLAINED_RESIDUAL:'fuel',
 OCCUPANCY_REVENUE:'ledger',OCCUPANCY_ENERGY_VOLUME:'energymeter',ENERGY_EFFICIENCY:'energymeter',CUSTOMER_COMPENSATION:'qa',PEAK_ENERGY_SHARE:'utility',DEMAND_CHARGE:'utility'};
const DEC_OF_FACTOR = {kobo:{CANDIDATE_RUNNING:'kobo-generator',UNEXPLAINED_RESIDUAL:'kobo-generator'},kisiwa:{SOLAR_SHORTFALL_NECESSARY_GEN:'kisiwa-genset'},
 mto:{METER_MAPPING_UNBILLED:'mto-billing',DEMAND_VOLUME:'mto-demand'},mwea:{OCCUPANCY_REVENUE:'mwea-occupancy'},kirinyaga:{ENERGY_EFFICIENCY:'kirinyaga-energy'},thika:{CUSTOMER_COMPENSATION:'thika-backup'},
 embakasi:{PEAK_ENERGY_SHARE:'embakasi-schedule',DEMAND_CHARGE:'embakasi-schedule'}};
const TREE_CACHE = {};
function tree(sk){return TREE_CACHE[sk]||(TREE_CACHE[sk]=placeHomes(sk,({mini:miniTree,cold:coldTree,ev:evTree})[OPS[SK[sk].op].vertical](sk)));}
function miniTree(sk){const s=siteM(sk),P=s.period.plan,A=s.period.actual,C=s.period.coverage,t=OPS.lakeside.t,tar=t.prices.tariff_usd_per_kwh[s.site],dp=t.prices.diesel_usd_per_l[s.site],br=s.period.bridge;
 const B=(d,cost)=>br.map((b,i)=>[b,i]).filter(([b])=>d.includes(b.driver)).map(([b,i])=>bridgeNode(sk,b,i,cost));
 const loss=A.technical_loss_kwh??A.expected_technical_loss_kwh, mto=sk==='mto', fb=s.period.fuel_balance;
 const billedKids=[{id:'deliv',label:'Energy delivered',how:'Supplied to the network, from the energy management export',unit:'kWh',actual:A.delivered_kwh,cls:'MEASURED',src:'ems',obs:true},
  {id:'loss',label:mto?'Expected technical losses':'Technical losses',how:'Delivered minus metered at customer meters',unit:'kWh',actual:loss,cls:mto?'DERIVED':'MEASURED',src:'meterreg',obs:true},
  ...(mto?[{id:'lossx',label:'Losses beyond expected (not priced)',how:`Delivered ${num(A.delivered_kwh)} − expected losses ${num(loss)} − metered ${num(A.metered_kwh)}; being investigated, not called theft, not priced`,unit:'kWh',actual:A.unexplained_kwh,cls:'DERIVED',residual:true,src:'meterreg',obs:true,dec:'mto-billing'}]:[]),
  {id:'meter',label:'Energy metered at customers',how:'Sum of customer meter readings for the period',unit:'kWh',actual:A.metered_kwh,cls:'MEASURED',src:'meterreg',obs:true},
  ...(mto?[]:[{id:'adj',label:'Authorised adjustments (within plan)',how:'Approved allowances deducted before billing',unit:'kWh',actual:A.adjustments_kwh,cls:'RECORDED',src:'billing',obs:true}]),
  ...B(['DEMAND_VOLUME','METER_MAPPING_UNBILLED','AUTHORISED_ADJUSTMENT'],false)];
 const litKids=[...B(['CANDIDATE_RUNNING','EVENING_LOAD_GROWTH','SOLAR_SHORTFALL_NECESSARY_GEN','EVENING_NECESSARY_GEN','UNEXPLAINED_RESIDUAL'],true)];
 if(fb)litKids.push({id:'fb',label:'Fuel balance',how:fb.opening_dip_l!==undefined?`Opening tank dip ${fb.opening_dip_l} L + deliveries ${num(fb.deliveries_l)} L − closing dip ${fb.closing_dip_l} L = ${num(fb.consumed_l)} L used; the generator model explains ${num(fb.model_implied_l)} L`:`${num(fb.consumed_l)} L used; the generator model explains ${num(fb.model_implied_l)} L`,unit:'L',actual:fb.consumed_l,cls:'RECORDED',src:'fuel',obs:true,bound:{text:`Not explained: ${fb.residual_l} L, ${(fb.residual_l/fb.consumed_l*100).toFixed(1)}% against a ${fb.tolerance_pct}% tolerance`,state:fb.residual_l/fb.consumed_l*100>fb.tolerance_pct?'off':'ok'}});
 const costP=P.diesel_cost+P.om+P.staff,costA=A.diesel_cost+A.om+A.staff;
 return {id:'root',label:'Contribution',how:'Revenue − cost to serve',unit:'$',plan:P.contribution,actual:A.contribution,eff:s.period.variance,cls:C.om==='ESTIMATED'?'ESTIMATED':'RECORDED',src:'statement',kids:[
  {id:'rev',label:'Revenue',how:`Billed kWh × tariff ($${tar.toFixed(2)} a kWh)`,unit:'$',plan:P.revenue,actual:A.revenue,eff:r2(A.revenue-P.revenue),cls:C.revenue,src:'billing',kids:[
   {id:'billed',label:'Billed kWh',how:'Metered kWh − authorised adjustments − meters not yet mapped to a customer',unit:'kWh',plan:P.billed_kwh,actual:A.billed_kwh,eff:r2(A.revenue-P.revenue),cls:'RECORDED',src:'billing',kids:billedKids},
   {id:'tariff',label:'Tariff',how:'Residential tariff from the tariff schedule',unit:'$/kWh',plan:tar,actual:tar,eff:0,cls:'RECORDED',src:'tariff'},
   {id:'cash',label:'Cash from October bills',how:`Collected ${usd(A.collected)} + in transit ${usd(A.in_transit)} + outstanding ${usd(A.outstanding)} = billed ${usd(A.revenue)}; cash does not change contribution`,unit:'$',actual:A.collected,cls:'RECORDED',src:'settlement',obs:true}]},
  {id:'cost',label:'Cost to serve',how:'Diesel + operations and maintenance + staff',unit:'$',plan:costP,actual:costA,eff:r2(costP-costA),cls:C.om==='ESTIMATED'?'ESTIMATED':'RECORDED',src:'statement',kids:[
   {id:'diesel',label:'Diesel cost',how:`Litres used × diesel price ($${dp.toFixed(2)} a litre)`,unit:'$',plan:P.diesel_cost,actual:A.diesel_cost,eff:r2(P.diesel_cost-A.diesel_cost),cls:C.diesel,src:'fuel',kids:[
    {id:'litres',label:'Litres used',how:'Generator fuel; the generator model splits it by why the generator ran',unit:'L',plan:P.diesel_l,actual:A.diesel_l,eff:r2(P.diesel_cost-A.diesel_cost),cls:'RECORDED',src:'fuel',kids:litKids},
    {id:'dprice',label:'Diesel price',how:'From delivery notes',unit:'$/L',plan:dp,actual:dp,eff:0,cls:'RECORDED',src:'fuel'}]},
   {id:'om',label:'Operations and maintenance',how:C.om==='ESTIMATED'?'October invoice not received: the target amount is carried as an estimate, never as zero':'Monthly contract invoice',unit:'$',plan:P.om,actual:A.om,eff:r2(P.om-A.om),cls:C.om,src:'om'},
   {id:'staff',label:'Staff',how:'Monthly staff cost',unit:'$',plan:P.staff,actual:A.staff,eff:r2(P.staff-A.staff),cls:C.staff,src:'staff'}]}]};}
function coldTree(sk){const s=siteM(sk),P=s.period.plan,A=s.period.actual,C=s.period.coverage,t=OPS.harvest.t,br=s.period.bridge,rate=t.prices.storage_usd_per_crate_day,ep=t.prices.electricity_usd_per_kwh,capc=CAPCD(sk),tol=t.energy_model.tolerance_pct;
 const B=d=>br.map((b,i)=>[b,i]).filter(([b])=>d.includes(b.driver)).map(([b,i])=>bridgeNode(sk,b,i,true));
 const occ=B(['OCCUPANCY_ENERGY_VOLUME'])[0],eff=B(['ENERGY_EFFICIENCY'])[0],over=A.kwh-A.kwh_model,overPct=over/A.kwh_model*100;
 const kwhKids=[{id:'kmodel',label:'Electricity expected at this occupancy',how:`Model: ${num(SN(sk).base_kwh)} + ${SN(sk).k_kwh_per_crate_day} × crate-days at 24 °C → target ${num(P.kwh)} kWh, October ${num(A.kwh_model)} kWh`,unit:'kWh',plan:P.kwh,actual:A.kwh_model,eff:occ?occ.eff:0,cls:'MODELLED',src:'energymodel',evd:occ?.evd},
  {id:'kexcess',label:'Electricity above what occupancy explains',how:`Metered ${num(A.kwh)} − expected ${num(A.kwh_model)} kWh`,unit:'kWh',plan:0,actual:over,eff:eff?eff.eff:0,cls:'DERIVED',src:'energymeter',evd:eff?.evd,dec:DEC_OF_FACTOR[sk]?.ENERGY_EFFICIENCY,bound:{text:`${overPct>=0?'+':''}${overPct.toFixed(1)}% against a ${tol}% tolerance`,state:Math.abs(overPct)>tol?'off':'ok'}}];
 const occR=B(['OCCUPANCY_REVENUE'])[0];
 const costP=P.energy+P.staff+P.maint+(P.liability||0),costA=A.energy+A.staff+A.maint+(A.liability||0);
 const kids=[{id:'rev',label:'Revenue',how:`Occupied crate-days × $${rate.toFixed(2)} a crate-day`,unit:'$',plan:P.revenue,actual:A.revenue,eff:r2(A.revenue-P.revenue),cls:C.revenue,src:'ledger',kids:[
   {id:'cd',label:'Occupied crate-days',how:`Capacity ${num(capc)} crate-days × occupancy (target ${P.occupancy_pct}%, October ${A.occupancy_pct}%)`,unit:'crate-days',plan:P.crate_days,actual:A.crate_days,eff:occR?occR.eff:0,cls:'RECORDED',src:'ledger',evd:occR?.evd,dec:DEC_OF_FACTOR[sk]?.OCCUPANCY_REVENUE},
   {id:'charge',label:'Chargeable crate-days',how:'Occupied crate-days of compatible commodities at a rate-card price; observed by reconciling the storage ledger to invoices. October: no difference (chargeable = occupied, invoiced = revenue, received = collected), so no billing option exists this month',unit:'crate-days',actual:A.crate_days,cls:'DERIVED',src:'ledger',obs:true},
   {id:'idle',label:'Idle capacity',how:`Capacity ${num(capc)} − occupied crate-days`,unit:'crate-days',plan:capc-P.crate_days,actual:capc-A.crate_days,cls:'DERIVED',src:'ledger',obs:true},
   {id:'rate',label:'Storage rate',how:'Per crate per day, from the rate card',unit:'$/cd',plan:rate,actual:rate,eff:0,cls:'RECORDED',src:'tariff'},
   {id:'cash',label:'Cash from October invoices',how:`Collected ${usd(A.collected)} + outstanding ${usd(A.outstanding)} = invoiced ${usd(A.revenue)}; cash does not change contribution`,unit:'$',actual:A.collected,cls:'RECORDED',src:'settlement',obs:true}]},
  {id:'cost',label:'Cost to serve',how:'Electricity + staff + maintenance + customer compensation',unit:'$',plan:costP,actual:costA,eff:r2(costP-costA),cls:C.maint==='ESTIMATED'?'ESTIMATED':'RECORDED',src:'statement',kids:[
   {id:'elec',label:'Electricity',how:`kWh × $${ep.toFixed(2)} a kWh`,unit:'$',plan:P.energy,actual:A.energy,eff:r2(P.energy-A.energy),cls:C.energy,src:'utility',kids:[
    {id:'kwh',label:'Electricity used',how:'Room energy meter',unit:'kWh',plan:P.kwh,actual:A.kwh,eff:r2(P.energy-A.energy),cls:'MEASURED',src:'energymeter',kids:kwhKids}]},
   {id:'staff',label:'Staff',how:'Monthly staff cost',unit:'$',plan:P.staff,actual:A.staff,eff:0,cls:C.staff,src:'staff'},
   {id:'maint',label:'Maintenance',how:C.maint==='ESTIMATED'?'October refrigeration service invoice not received: target amount carried as an estimate, never as zero':'Monthly service invoice',unit:'$',plan:P.maint,actual:A.maint,eff:0,cls:C.maint,src:'om'},
   ...(P.liability!==undefined?[{...B(['CUSTOMER_COMPENSATION'])[0],id:'liab',label:'Customer compensation',how:plain(br[0].basis)+'. A cost to serve, under Optimize. Its Protect side is the batch exposed above its limit, counted under Protect in batches, never in money',unit:'$',plan:P.liability,actual:A.liability,dev:null,src:'qa',bound:{text:'The French-bean batch (B-1031, limit 5 °C) was above its limit for 20–30 minutes on 6 Oct; the contract makes the operator liable above 15 minutes',state:'off'}}]:[])]}];
 return {id:'root',label:'Contribution',how:'Revenue − cost to serve',unit:'$',plan:P.contribution,actual:A.contribution,eff:s.period.variance,cls:C.maint==='ESTIMATED'?'ESTIMATED':'RECORDED',src:'statement',kids};}
function evTree(sk){const s=siteM(sk),P=s.period.plan,A=s.period.actual,C=s.period.coverage,br=s.period.bridge||[];
 const B=d=>br.map((b,i)=>[b,i]).filter(([b])=>d.includes(b.driver)).map(([b,i])=>bridgeNode(sk,b,i,true));
 let bill;
 if(sk==='embakasi'){const pk=B(['PEAK_ENERGY_SHARE'])[0],dm=B(['DEMAND_CHARGE'])[0];
  bill={id:'bill',label:'Electricity bill',how:'Energy charges + demand charge (time-of-use tariff)',unit:'$',plan:P.energy_cost,actual:A.energy_cost,eff:r2(P.energy_cost-A.energy_cost),cls:C.energy,src:'utility',kids:[
   {...pk,id:'energy',label:'Energy charges',how:`Peak kWh × $0.24 + other kWh × $0.12 (October; the 00:00–05:00 rate starts 1 Nov)`,unit:'$',plan:r2(P.peak_cost+P.offpeak_cost),actual:r2(A.peak_cost+A.offpeak_cost),dev:null,kids:[
    {id:'kwh',label:'Energy charged',how:'Charger session log, matched to the invoice',unit:'kWh',plan:P.kwh,actual:A.kwh,eff:0,cls:'MEASURED',src:'ocpp'},
    {id:'peak',label:'Energy charged at peak price (18:00–22:00)',how:`Share at peak: target ${pct(P.peak_share)}, October ${pct(A.peak_share)}`,unit:'kWh',plan:P.peak_kwh,actual:A.peak_kwh,eff:pk.eff,cls:'RECORDED',src:'utility',evd:pk.evd,dec:'embakasi-schedule'}]},
   {...dm,id:'demand',label:'Demand charge',how:`Monthly peak kW × ${usd(SN(sk).demand_rate)}`,unit:'$',plan:P.demand_cost,actual:A.demand_cost,dev:null,kids:[
    {id:'maxkw',label:'Monthly peak import',how:'Highest 30-minute import in the month',unit:'kW',plan:P.max_kw,actual:A.max_kw,eff:dm.eff,cls:'RECORDED',src:'utility',evd:dm.evd,dec:'embakasi-schedule',bound:{text:`Import limit ${s.physical.import_limit_kw} kW: October peak reached the limit`,state:'at'}}]}]};}
 else if(sk==='kasarani'){bill={id:'bill',label:'Electricity bill',how:`kWh × $${s.tariff.usd_per_kwh.toFixed(2)} flat tariff (timing does not change cost)`,unit:'$',plan:P.energy_cost,actual:A.energy_cost,eff:0,cls:C.energy,src:'utility',kids:[{id:'kwh',label:'Energy charged',how:'Charger session log, matched to the invoice',unit:'kWh',actual:A.kwh,cls:'MEASURED',src:'ocpp',obs:true}]};}
 else {bill={id:'bill',label:'Electricity bill',how:'Energy charges + demand charge (older time-of-use tariff, no 00:00–05:00 rate)',unit:'$',plan:P.energy_cost,actual:A.energy_cost,eff:s.period.variance,cls:C.energy,src:'utility',kids:[
  {id:'peak',label:'Energy at peak price',how:`${num(A.peak_kwh)} kWh × $0.24`,unit:'$',actual:A.peak_cost,cls:'RECORDED',src:'utility',obs:true},
  {id:'off',label:'Energy at off-peak price',how:`${num(A.offpeak_kwh)} kWh × $0.12`,unit:'$',actual:A.offpeak_cost,cls:'RECORDED',src:'utility',obs:true},
  {id:'demand',label:'Demand charge',how:`Monthly peak ${A.max_kw} kW × ${usd(SN(sk).demand_rate)}`,unit:'$',actual:A.demand_cost,cls:'RECORDED',src:'utility',obs:true,bound:{text:`Peak import ${A.max_kw} kW of a ${s.physical.import_limit_kw} kW limit (${pct(A.max_kw/s.physical.import_limit_kw)})`,state:'near'}},
  {id:'resid',resLabel:'not attributed: the target is declared only as a bill total',label:'Not attributed: the target is declared only as a bill total',how:`Target ${usd(P.energy_cost)} − actual ${usd(A.energy_cost)}; the target has no split by time of day, so this difference cannot be attributed to a factor yet`,unit:'$',eff:s.period.variance,cls:'DERIVED',residual:true,src:'plan'}]};}
 const dep={id:'dep',label:'Required departures met',how:'Fleet roster: each bus leaves on time with the charge its route needs',unit:'dep',plan:P.departures_required,actual:A.departures_met,eff:0,cls:'RECORDED',src:'roster',bound:{text:'Every required departure met (a hard obligation)',state:'ok'}};
 const extra=[];
 if(sk==='kasarani'){const inc=s.incident;extra.push({id:'chg',label:'Charging energy deliverable per night (since 1 Nov)',how:`Charger 2 failed on 1 Nov (welded contactor): ${num(KN().deliverable_kwh_night)} kWh deliverable against ${num(KN().required_kwh_night)} kWh required`,unit:'kWh/night',plan:KN().required_kwh_night,actual:KN().deliverable_kwh_night,cls:'DERIVED',src:'ocpp',dec:'kasarani-charger',obs:true,bound:{text:`${Math.round(KN().buses_short_per_night)} bus short each night: ${KN().departures_missed} departures missed in November so far, ${usd(KN().penalties)} in penalties (calculated from records)`,state:'off'}});}
 if(sk==='ruiru')extra.push({id:'conn',label:'Charger 7, connector 2',how:'One charging session stopped on a fault on 6 Oct (see the connector 2 finding); connector 2 has reported no status since; connector 1 on the same charger works',unit:'n',cls:'MEASURED',src:'ocpp',dec:'ruiru-connector',obs:true,bound:{text:'No departure depends on it in the roster replay',state:'ok'}});
 const costP=P.total,costA=A.total,dp=r2(costP/P.departures_required),da=r2(costA/A.departures_met);
 return {id:'root',label:'Cost per required departure met',how:'Charging and depot cost ÷ required departures met',unit:'$/dep',plan:dp,actual:da,eff:s.period.variance,cls:C.maintenance==='ESTIMATED'?'ESTIMATED':'RECORDED',src:'statement',kids:[dep,...extra,
  {id:'cost',label:'Charging and depot cost',how:'Electricity bill + maintenance',unit:'$',plan:costP,actual:costA,eff:s.period.variance,cls:C.maintenance==='ESTIMATED'?'ESTIMATED':'RECORDED',src:'statement',kids:[bill,
   {id:'pen',label:'Penalties for missed departures',how:`Missed departures × ${usd(SN('kasarani').penalty_rate)} from the transport authority’s penalty statement; none in October because every required departure was met. A cost to serve, under Optimize. Its Protect side is the required departures missed, counted under Protect in departures, never in money`,unit:'$',plan:0,actual:0,eff:0,cls:'DERIVED',src:'penalty'},
   {id:'maint',label:'Maintenance',how:C.maintenance==='ESTIMATED'?'October invoice from the service contractor not received: target amount carried as an estimate, never as zero':'Monthly charger service fee',unit:'$',plan:P.maintenance,actual:A.maintenance,eff:0,cls:C.maintenance,src:'om'}]}]};}
function walk(n,f,d=0,parent=null){f(n,d,parent);(n.kids||[]).forEach(k=>walk(k,f,d+1,n));}
function findNode(sk,id){let r=null;walk(tree(sk),n=>{if(n.id===id)r=n;});return r;}

/* portfolio composition (identity M1): Σ eligible sites; ratios as Σ/Σ */
function opTotals(op){const o=OPS[op],cost=o.kind==='cost';let plan=0,actual=0;const ov=X=>X.status==='evaluated'?X.nodes[cost?'cost_to_serve':'contribution']:X.stated_total;o.sites.forEach(sk=>{const d=DERIVED.sites[`${o.t.tenant}/${siteM(sk).site}`];plan+=ov(d.plan);actual+=ov(d.actual);});plan=r2(plan);actual=r2(actual);return {plan,actual,variance:r2(cost?plan-actual:actual-plan)}; /* Σ of the evaluator's site outcomes */}
function residualOf(op){let r=0;OPS[op].sites.forEach(sk=>{walk(tree(sk),n=>{if(n.residual&&n.eff!=null)r+=n.eff;});});
 const v=opTotals(op).variance;return {residual:r2(r),attributed:r2(v-r)};}

/* ---------- sources (manifest `sources`), shaped sample rows for the drawer ---------- */
const PROV = {'demo-simulated':'Simulated demo data','source-emulated':'Source-emulated demo record','bench-tested':'Bench tested','field-integrated':'Field connected','observed-financial':'Observed financial record'};
const SRCDEF = {
 billing:['Customer billing export (prepaid vending and postpaid), CSV','customer, meter, period, kWh, tariff code, amount, adjustment code','source-emulated'],
 meterreg:['Meter register with effective dates','meter, customer, valid from, valid to','source-emulated'],
 settlement:['Mobile-money settlement statement and receipts','transaction, paid at, settled at, amount, customer reference','source-emulated'],
 ems:['Energy management system and inverter export (5-minute in evidence windows)','time, solar available kW, load kW, battery charge %, generator kW, interval class','source-emulated'],
 fuel:['Fuel delivery notes and tank dips','record, date, litres, price','source-emulated'],
 plan:['Monthly targets and budget spreadsheet','site, period, line, amount','source-emulated'],
 om:['Service and maintenance invoices','invoice, period, amount, status','source-emulated'],
 staff:['Expense records','period, line, amount','source-emulated'],
 tariff:['Tariff schedule and rate card','tariff, effective from, rate','source-emulated'],
 statement:['Site economics, composed from the lines below','line, plan, actual, class','source-emulated'],
 ledger:['Storage ledger (check-in and check-out per batch)','batch, customer, commodity, crates, in at, out at, rate','source-emulated'],
 energymeter:['Room energy meter and chamber controller','meter, period, kWh, mean outside temperature','demo-simulated'],
 energymodel:['Per-room occupancy energy model (proposed; fitted on 60 days of meter and storage records)','term, value','demo-simulated'],
 qa:['Quality inspection notes and credit notes','batch, inspected at, crates downgraded, inspector / credit note','source-emulated'],
 utility:['Utility invoice with time-of-use and demand lines','line, kWh or kW, rate, amount','source-emulated'],
 ocpp:['Charger management system log (session start, meter values, status)','charger, connector, event, time, value','source-emulated'],
 roster:['Fleet roster','bus, route block, return, departure, required kWh','source-emulated'],
 penalty:['Penalty statement from the transport authority (missed route blocks)','date, route block, penalty','source-emulated'],
 model:['Forward replay of site data (modelled)','item, value','demo-simulated']};
function sampleRows(src,sk,n){const s=siteM(sk),A=s.period.actual,P=s.period.plan,nm=SK[sk].name;
 const v=n.actual!=null?fmtU(n.actual,n.unit):'—';
 switch(src){
  case 'billing':return [['(all customers)','—','Oct 2026',num(A.billed_kwh),'residential',usd(A.revenue),'—'],[`(adjustments)`,'—','Oct 2026',`−${num(A.adjustments_kwh)}`,'—','—',sk==='mto'?'clinic allowance':'authorised']];
  case 'meterreg':return sk==='mto'?[['6 meters re-pointed','6 customers','3 Oct','—'],[`(${num(SN('mto').unmapped_kwh)} kWh metered on them in October)`,'—','—','not billed']]:[['(all meters)','(all customers)','before Oct','open']];
  case 'settlement':return [['(October statement)','to 31 Oct','to 2 Nov',usd(A.collected),'—'],...(A.in_transit?[['(paid 30–31 Oct)','30–31 Oct','2 Nov',usd(A.in_transit),'—']]:[])];
  case 'ems':return [['(11 of 31 October days)','—','—','—','—','beyond need after dawn'],['Example interval','42 kW','30 kW','74%','18 kW','beyond need']];
  case 'fuel':{const fb=s.period.fuel_balance||{};return fb.opening_dip_l!==undefined?[['Tank dip (opening)','1 Oct',fb.opening_dip_l,'—'],['Delivery notes (October)','Oct',num(fb.deliveries_l),usd2(OPS.lakeside.t.prices.diesel_usd_per_l[s.site])],['Delivery note recorded 9 days late','for 26 Oct, recorded 4 Nov','included above','—'],['Tank dip (closing)','31 Oct',fb.closing_dip_l,'—']]:[['Litres used (October)','Oct',num(A.diesel_l),usd2(OPS.lakeside.t.prices.diesel_usd_per_l[s.site])]];}
  case 'plan':return Object.entries(P).filter(([k,x])=>typeof x==='number').slice(0,6).map(([k,x])=>[nm,'Oct 2026',k.replace(/_/g,' '),k.includes('kwh')||k.includes('_l')||k.includes('days')||k.includes('pct')||k.includes('share')||k.includes('kw')||k.includes('departures')?num(x,2):usd(x)]);
  case 'om':return [[n.cls==='ESTIMATED'?'(not received)':'(October invoice)','Oct 2026',v,ecw(n.cls)]];
  case 'staff':return [['Oct 2026','staff',v]];
  case 'tariff':return [[n.label,'before Oct',v]];
  case 'ledger':return sk==='thika'?siteM('thika').incident.batches.map(b=>[b.batch,b.owner||'—',b.commodity,b.crates,'before 6 Oct',b.present===false?'5 Oct 16:00':'—','$0.20']):[['(October total)','—','—',`${num(A.crate_days)} crate-days`,'—','—','$0.20']];
  case 'energymeter':return [['Room meter','Oct 2026',num(A.kwh),'—']];
  case 'energymodel':return [['Base load',`${num(SN(sk).base_kwh)} kWh a month`],['Per crate-day',`${SN(sk).k_kwh_per_crate_day} kWh`],['Reference outside temperature','24 °C (+2.5% a degree above)'],['Tolerance','5%']];
  case 'qa':return [['French beans (B-1031)','7 Oct','6','quality inspector'],['Credit note (CN-0412)','Oct','—',usd(A.liability||0)]];
  case 'utility':return SK[sk].op==='harvest'?[['Electricity',num(A.kwh),'$0.20',usd(A.energy)]]:sk==='kasarani'?[['Energy (flat)',num(A.kwh),'$0.15',usd(A.energy_cost)]]:[['Peak energy',num(A.peak_kwh),'$0.24',usd(A.peak_cost)],['Off-peak energy',num(A.offpeak_kwh),'$0.12',usd(A.offpeak_cost)],['Demand charge',`${A.max_kw} kW`,usd2(SN(sk).demand_rate),usd(A.demand_cost)]];
  case 'ocpp':return sk==='kasarani'?[['Charger 2','—','status: faulted (welded contactor)','1 Nov 23:40','—']]:sk==='ruiru'?[['Charger 7','2','session stopped on a fault','6 Oct 14:11','3.6 kWh delivered']]:[['(all chargers)','—','meter values','Oct','sums to the invoice kWh']];
  case 'roster':return [['(all buses)','—','—','—',`${num(A.departures_required)} departures required in October`]];
  case 'penalty':return sk==='kasarani'?[['1–5 Nov',`${num(KN().departures_missed)} departures × ${usd(KN().penalty_rate)}`,usd(KN().penalties)]]:[['October','none','$0']];
  case 'statement':return [];
  default:return [['—','—']];}}

/* ---------- evidence drawer: definition, formula with values, source rows, clocks, coverage, provenance ---------- */
function evRecord(key){const [kind,a,b,c]=key.split(':');
 if(kind==='node'){const sk=a,n=findNode(sk,b),s=siteM(sk),[sys,head,prov]=SRCDEF[n.src]||SRCDEF.model;
  const pl=n.plan!=null?fmtU(n.plan,n.unit):'no target declared at this factor',ac=n.actual!=null?fmtU(n.actual,n.unit):'—';
  const parts=(n.kids||[]).filter(k=>!k.obs).map(k=>[k.label,k.plan!=null?fmtU(k.plan,k.unit):'—',k.actual!=null?fmtU(k.actual,k.unit):'—',k.eff!=null?usd(k.eff,true):'—',ecw(k.cls)]);
  return {title:`${SK[sk].name} · ${n.label}`,value:ac,cls:n.cls,def:n.how,formula:`Target ${pl} · October ${ac}${n.eff!=null&&!n.obs?` · effect on the site outcome ${usd(n.eff,true)}`:''}`,parts,sys,head,rows:sampleRows(n.src,sk,n),prov,
   clocks:[['Service period','1–31 Oct'],['Recognised in','October books, closed 6 Nov'],...(n.id==='cash'?[['Settled','to 2 Nov (late settlement of 30–31 Oct payments)']]:[]),['Effective terms','tariff and contract terms in force in October']],
   coverage:n.cls==='ESTIMATED'?'Invoice missing: carried at target as an estimate, never as zero':n.residual?'Not explained by the model yet: shown as its own factor, never hidden':ecw(n.cls),path:`${sitePath(sk)}.period`};}
 if(kind==='bridge'){const sk=a,br=siteM(sk).period.bridge[+b],[label]=FAC[br.driver],src=SRC_OF[br.driver];const [sys,head,prov]=SRCDEF[src];
  return {title:`${SK[sk].name} · ${label}`,value:usd(br.amount,true),cls:br.class,def:`Attribution of this factor's deviation to the site outcome. ${br.class==='MODELLED'?'The split comes from the generator model applied to recorded litres.':br.driver==='UNEXPLAINED_RESIDUAL'?'Litres used beyond what the generator model explains: not explained by the model yet.':br.class==='DERIVED'?'Calculated from recorded litres and metered generator energy; observed, not an option’s effect.':''}`,formula:cap(plain(br.basis))+` = ${usd(br.amount,true)}`,parts:[],sys,head,rows:sampleRows(src,sk,{actual:null,cls:br.class}),prov:br.class==='MODELLED'?'demo-simulated':prov,
   clocks:[['Service period','1–31 Oct'],['Recognised in','October books, closed 6 Nov']],coverage:ecw(br.class),path:`${sitePath(sk)}.period.bridge[${b}]`};}
 if(kind==='port'){const o=OPS[a],P=o.t.portfolio,T=opTotals(a),cost=o.kind==='cost';
  const rows=o.sites.map(sk=>{const r=tree(sk);return [SK[sk].name,fmtU(cost?siteM(sk).period.plan.total:r.plan,'$'),fmtU(cost?siteM(sk).period.actual.total:r.actual,'$'),usd(siteM(sk).period.variance,true)];});
  if(b==='cov'){const cv=P.coverage;return {title:`${o.name} · cost on emulated records`,value:pct(cv.cost_recorded_share,1),cls:'DERIVED',def:'Share of the period cost to serve that rests on received invoices and records; the rest is carried as an estimate.',formula:`${usd(cv.cost_recorded_usd)} recorded ÷ ${usd(cv.cost_total_usd)} total = ${(cv.cost_recorded_share*100).toFixed(2)}%`,parts:[],sys:SRCDEF.om[0],head:'site, line, amount, class',rows:o.sites.flatMap(sk=>{const out=[];walk(tree(sk),n=>{if(n.cls==='ESTIMATED'&&!n.kids)out.push([SK[sk].name,n.label,fmtU(n.actual,'$'),'Estimated']);});return out;}),prov:'source-emulated',clocks:[['Service period','1–31 Oct'],['As of','6 Nov']],coverage:`${pct(cv.cost_recorded_share,1)} recorded`,path:`tenants[${o.ti}].portfolio.coverage`};}
  if(b==='m12')return planValueRecord(a);
  if(b==='spend'){const A=P.allocation;return {title:`${o.name} · plan spend`,value:usd(A.spend),cls:'QUOTE',def:'Sum of the one-off costs of the options in the plan, against the November–December budget.',formula:Object.entries(A.spend_breakdown).map(([k,v])=>usd(v)).join(' + ')+` = ${usd(A.spend)}`,parts:[],sys:'Quotes, contract terms and price lists',head:'option, spend',rows:Object.entries(A.spend_breakdown).map(([k,v])=>[optLabel(k),usd(v)]),prov:'source-emulated',clocks:[['Budget period','November–December']],coverage:'Quoted costs',path:`tenants[${o.ti}].portfolio.allocation.spend`};}
  const v=b==='plan'?T.plan:b==='actual'?T.actual:T.variance;
  return {title:`${o.name} · ${cost?'charging and depot cost':'contribution'} · ${b==='plan'?'plan':b==='actual'?'October':'difference from target'}`,value:usd(v,b==='variance'),cls:b==='plan'?'PLAN':'RECORDED',def:`Portfolio ${cost?'cost':'contribution'} is the sum of the three sites, computed from each site's factors (never an average of site percentages).`,formula:rows.map(r=>r[b==='plan'?1:b==='actual'?2:3]).join(' + ')+` = ${usd(v,b==='variance')}`,parts:rows.map(r=>[r[0],r[1],r[2],r[3],'']),sys:b==='plan'?SRCDEF.plan[0]:'Site economics (billing, fuel, invoices, ledgers)',head:'site, plan, actual, difference',rows,prov:'source-emulated',clocks:[['Service period','1–31 Oct'],['Recognised in','October books, closed 6 Nov']],coverage:`${pct(P.coverage.cost_recorded_share,1)} of cost on emulated records`,path:`tenants[${o.ti}].portfolio`};}
 if(kind==='opt'){const x=OPT[a],cost=b==='cost',[val,note]=cost?optCost(x):optEffect(x),e=x.economics||{};
  return {title:`${optLabel(a)} · ${cost?'one-off cost':'12-month result'}`,value:val,cls:cost?'QUOTE':(e.class||'MODELLED'),def:cost?(x.detail?`Breakdown: ${plain(x.detail).replace(/ \+ /g,', ')}.`:note):note,formula:cost?plain(x.one_off_detail||x.detail||'Quoted cost'):(derivedFormula(a)?derivedFormula(a)+(OPT_WORK[a]?' Factor detail: '+OPT_WORK[a]():''):(OPT_WORK[a]?OPT_WORK[a]():'As stated by the option.')),parts:[],sys:cost?'Quotes, contract terms and price lists':REPLAY_OPTS.has(a)?SRCDEF.model[0]:'Option valuation from quotes, contract terms, declared prices and stated assumptions',head:'item, value',rows:[[optLabel(a),val]],prov:'demo-simulated',clocks:[['Horizon','12 months, October prices and contracts']],coverage:cost?'Quoted':ecw(e.class||'MODELLED')+', not realised',path:x._path};}
 if(kind==='clause'){const r=rightsOf(a);return {title:`${r.asset} · contract clause`,value:r.type,cls:'CONTRACT',def:'Reviewed extraction from the contract document: assisted, then checked by a person.',formula:'—',parts:[],sys:'Contract documents (PDF) and reviewed extraction',head:'clause, page reference',rows:r.terms.map((t,i)=>[t,`clause ${i+1}; page reference shown in a pilot`]),prov:'source-emulated',clocks:[['Term',r.until?`to ${fdate(r.until)}`:'not stated']],coverage:'Reviewed extraction',path:r.path,legal:true};}
 if(kind==='stake'){const map={battery:['Kobo battery cover',OPS.lakeside.t.portfolio.allocation.listed_not_summed['BAT-001_cover_exposure'],'Asset value covered by the battery warranty. At stake, never money gained.',`${sitePath('kobo')}.entitlement`],
   batch:['Thika French-bean batch (B-1031) exposed',siteM('thika').incident.batches[0].exposed_value,`${num(siteM('thika').incident.batches[0].crates)} crates × declared ${usd(siteM('thika').incident.batches[0].declared_value_per_crate)} a crate. Exposure: the produce was above its limit; only the ${num(SN('thika').liability/siteM('thika').incident.batches[0].declared_value_per_crate)} crates downgraded by inspection (${usd(SN('thika').liability)}) became a liability.`,`${sitePath('thika')}.incident.batches[0]`],
   credit:['Possible Kisiwa service credit',siteM('kisiwa').entitlements[1].potential_credit,(e=>`${SCREDIT(e.contract.service_credit)} (${num(e.occurrence.response_hours)} hours against ${num(e.contract.response_hours)}). Counted only when a credit note arrives.`)(siteM('kisiwa').entitlements[1]),`${sitePath('kisiwa')}.entitlements[1]`],
   charges:['Charges restored at Mto over 12 months',OPS.lakeside.t.portfolio.allocation.listed_not_summed['MTO-BILLING_charges_12m'],`${num(SN('mto').unmapped_kwh)} kWh × ${usd2(SN('mto').tariff)} = ${usd(OPT['MTO-BILLING'].economics.charges_monthly)} a month × 12. Billed, not yet collected.`,`${sitePath('mto')}.decision.options[2]`],
   penalty:['Kasarani November penalties',KN().penalties,`${num(KN().departures_missed)} missed departures × ${usd(KN().penalty_rate)}.`,`${sitePath('kasarani')}.incident.november_to_date`]}[a];
  return {title:map[0],value:usd(map[1]),cls:a==='penalty'?'DERIVED':a==='charges'?'ECONOMIC_ACTUAL_FORWARD':'EXPOSURE',def:map[2],formula:map[2],parts:[],sys:a==='batch'?SRCDEF.ledger[0]:a==='penalty'?SRCDEF.penalty[0]:a==='charges'?SRCDEF.billing[0]:'Contract documents and service tickets',head:'item, amount',rows:[[map[0],usd(map[1])]],prov:'source-emulated',clocks:[['Period','October–November']],coverage:a==='penalty'?'Recorded':'Listed beside the plan, never added',path:map[3]};}
 return {title:'Source records',value:'—',cls:'MISSING',def:'Not available yet.',formula:'—',parts:[],sys:'—',head:'',rows:[],prov:'source-emulated',clocks:[],coverage:'—',path:'—'};}
const REPLAY_OPTS=new Set(['KOB-STOPSOC','KOB-RESERVE','KOB-NOACT','MTO-HULLER','EMB-DEADLINE','EMB-CHEAPEST']);
function provChips(active){return `<div class="prov" aria-label="Where the data came from">${Object.entries(PROV).map(([k,p])=>`<span class="${k===active?'on':''}">${k===active?icon('check'):''}${p}</span>`).join('')}</div>`;}
function openEvidence(key){const r=evRecord(key);
 drawer(r.title,`<div class="evhead"><div class="evval">${r.value}</div>${ec(r.cls)}</div>
 <h3>What this is</h3><p>${r.def}</p>
 <h3>How it is worked out</h3><p>${r.formula}</p>${r.parts.length?`<div class="table-wrap scroll-region" tabindex="0" role="region" aria-label="Factors that compose it">${table(['Factor','Target','October','Effect on outcome','Evidence'],r.parts)}</div>`:''}
 <h3>Source records</h3><p><strong>${r.sys}</strong></p>${r.rows.length?`<div class="table-wrap scroll-region" tabindex="0" role="region" aria-label="Source record sample"><table class="srcrows"><thead><tr>${r.head.split(', ').map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${r.rows.map(row=>`<tr>${row.map(c=>`<td>${c}</td>`).join('')}</tr>`).join('')}</tbody></table></div><p class="note">Sample in the shape of the source record; customer-level rows are not reproduced in this mock-up.</p>`:''}
 <h3>Period and clocks</h3>${kv(r.clocks)}
 <h3>Coverage</h3><p>${r.coverage}</p>
 <h3>Where the data came from</h3>${provChips(r.prov)}<p class="note">Demo data only: nothing here is field connected or from a client’s books.</p>
 ${r.legal?'<p class="legal">This is not a legal decision. Coverage is decided by the supplier or insurer.</p>':''}
 <details class="tech"><summary>For reviewers: demo data reference</summary><pre class="code">${escapeHtml(r.path)}\ndemo data version ${MANIFEST_SHA}</pre></details>`,true);tagReplay(document.querySelector('.drawer'));plainWords(document.querySelector('.drawer'));}

/* ---------- shell hooks used by the re-based v7.0 screens.js ---------- */
const LOOP_SITE_TABS=['Overview','Foundation','Health','Performance','Findings','Work','Financials','Evidence'];
const DEEP = {kobo:{Foundation:'foundation',Health:'health',Performance:'dispatch',Findings:'sitefindings',Work:'sitework',Evidence:'evidence'},
 thika:{Foundation:'cold-foundation',Health:'cold-health',Performance:'temperature',Findings:'cold-findings',Work:'cold-work',Evidence:'cold-evidence'},
 ruiru:{Foundation:'ev-foundation',Health:'ev-health',Performance:'sessions',Findings:'ev-findings',Work:'ev-work',Evidence:'ev-evidence'}};
const tabRoute = (sk,tab) => tab==='Overview'?`site/${sk}`:tab==='Financials'?`site/${sk}/economics`:DEEP[sk]?DEEP[sk][tab]:`site/${sk}/${tab.toLowerCase()}`;
function siteRoutes(domain){const sk=V70SITE[domain];return LOOP_SITE_TABS.map(t=>tabRoute(sk,t));}
function siteTabRow(sk,active){return tabRow(LOOP_SITE_TABS.map(t=>[t,tabRoute(sk,t)]),tabRoute(sk,active));}
function siteSwitch(s){const cur=s.site||V70SITE[s.domain],op=SK[cur].op;return `<label class="site-switch"><span class="sr-only">Site</span><select id="loop-site-switch" aria-label="Switch site">${OPS[op].sites.map(k=>`<option value="${k}" ${k===cur?'selected':''}>${SK[k].name} · ${SK[k].type}</option>`).join('')}</select></label>`;}
/* the calculated daily snapshot (design §2.8, OD-23; register call 19): each portfolio's record (MANIFEST.snapshot.portfolios)
   gives its "as of" time and whether a recalculation is pending, with what triggered it, when, and the Sites it affects. Every
   figure screen shows the "as of" time with the hour, and says so while a recalculation is pending. */
const hhmm = iso => /T\d{2}:\d{2}/.test(iso||'')?iso.slice(11,16):null;
function snapOf(op){const t=OPS[op].t.tenant,s=M.snapshot||{},p=(s.portfolios||[]).find(x=>x.tenant===t)||null;
 return {asOf:p?.as_of||s.as_of||null,pending:p?.recalculation_pending===true,detail:p?.pending||null,books:AS_OF};}
function snapText(op=LS.op){const S=snapOf(op),h=hhmm(S.asOf);return S.asOf?`Figures as of ${h?h+', ':''}${fdate(S.asOf)}`:`Figures as of ${fdate(S.books)}, when the October books closed`;}
function pendingText(op=LS.op){const S=snapOf(op),p=S.detail;if(!S.pending)return '';
 const names=(p?.sites||[]).map(n=>{const k=siteKeyOf(op,n);return k?SK[k].name:n;}),who=[...names,...(p?.portfolio_also?['the portfolio']:[])],at=p?.received?`At ${hhmm(p.received)||''}${hhmm(p.received)?' on ':''}${fdate(p.received)}, `:'';
 const what=p?.what?`${at}${at?p.what:cap(p.what)}. `:'';
 return `Recalculation pending. ${what}${who.length?`${who.join(' and ')} still show${who.length===1?'s':''} the ${hhmm(S.asOf)||fdate(S.asOf)} figures until ${who.length===1?'it is':'they are'} recalculated.`:'These figures are about to change.'}`;}
function periodChip(s){const sk=s&&s.site,op=sk&&SK[sk]?SK[sk].op:LS.op,S=snapOf(op);
 return `<span class="period-chip" data-snapshot="${S.asOf||S.books}">${icon('clock')}October 2026 · ${snapText(op)}</span>${S.pending?` <span class="snap-pending" role="status" data-op="${op}">${badge(pendingText(op),'amber')}</span>`:''}`;}
function reviewOperatorSelect(){return `<label class="op-select">Demo operator <select id="op-switch" aria-label="Demo operator (review tool, not part of the product)">${Object.entries(OPS).map(([k,o])=>`<option value="${k}" ${k===LS.op?'selected':''}>${o.name}</option>`).join('')}</select></label>`;}
function loopCrumbs(s){return `<div class="breadcrumbs">${s.crumbs(s).map(([t,id])=>id?link(id,t):escapeHtml(t)).join('<span>›</span>')}</div>`;}
const GLOBAL_ROOTS=['Assets','Findings','Actions','Incidents','Maintenance','Operational records','Evidence','Settings'];
function preBody(s){
 if(s.loop)return '';
 if(GLOBAL_ROOTS.includes(s.root)&&(!s.section||s.gtabs))return `<div class="slim-banner">${icon('info')}<p>Example items from the three demo operators shown together: Kobo (Lakeside Power), Thika (Harvest Cold Network) and Ruiru (Metro Bus Depots). A real operator sees only its own sites.</p></div>`;
 if(s.root==='Sites'&&s.section&&s.domain==='ev')return `<div class="slim-banner">${icon('info')}<p>Detailed views from the earlier demo: they show Ruiru’s charger 7 (connectors 1 and 2) on 6 Oct, with that example’s 2-connector, 80 kW set-up. Depot-wide figures (${num(SN('ruiru').chargers_installed)} chargers, ${num(SN('ruiru').import_limit_kw)} kW import limit) are on the ${link('site/ruiru','Ruiru overview')}.</p></div>`;
 if(s.id==='opportunity-finding'||s.id==='renewable')return `<div class="slim-banner">${icon('info')}<p>Spare daytime solar without a paying customer is capacity, not an opportunity value. The Portfolio shows it as capacity; only customer evidence makes it a demand factor. ${link('portfolio/demand-and-capacity','Open Demand and capacity →')}</p></div>`;
 return '';}
function selectorLabel(p){const st=REG_STATUS(p);return `${st==='Merged'?'[Merged] ':st==='Added'?'[New] ':''}${p.root} · ${typeof p.title==='function'?p.title():p.title}${p.section?' / '+p.section:''}`;}

/* routing: merged v7.0 screens resolve to the screen that absorbed them */
const ALIAS = {'portfolio/opportunity':'portfolio/demand-and-capacity',financials:'site/kobo/economics',assumptions:'site/kobo/economics',scenarios:'site/kobo/economics','cold-financials':'site/thika/economics','cold-assumptions':'site/thika/economics','cold-scenarios':'site/thika/economics','ev-financials':'site/ruiru/economics','ev-assumptions':'site/ruiru/economics','ev-scenarios':'site/ruiru/economics'};
function resolveScreen(id){
 let target=id;if(ALIAS[id]){target=ALIAS[id];try{history.replaceState(null,'','#/'+target);}catch{}}
 const s=SCREENS.find(x=>x.id===target)||SCREENS[0];
 const op=s.site?SK[s.site].op:s.op?s.op:(s.section&&!s.gtabs&&DOMAIN_OP[s.domain]&&s.root!=='Portfolio')?DOMAIN_OP[s.domain]:null;
 if(op&&op!==LS.op)setOp(op);
 return s;}
function setOp(op){LS.op=op;try{sessionStorage.setItem('l4-op',op);}catch{}}
/* rev 7 (N-M2): every figure that rests on a replay carries the visible design-value tag in its own container */
const REPLAY_RE=new RegExp(REPLAY_PATTERNS.join('|')); /* derived from the manifest by tools/gen_fixtures.py */
const DV_CONTAINER='tr,li,p,dd,.hero,.path,.total,.evhead';
function tagReplay(root){if(!root)return;const w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT),conts=new Set();let n;
 while((n=w.nextNode())){const pe=n.parentElement;if(pe.closest('.dv,.vh,select,option,details.tech,script,style'))continue;if(REPLAY_RE.test(n.textContent)){const c=pe.closest(DV_CONTAINER);if(c&&!c.querySelector('.dv'))conts.add(c);}}
 conts.forEach(c=>{const t=c.tagName==='TR'?c.lastElementChild:c;t.insertAdjacentHTML('beforeend',' '+dvTag());});}
/* ---------- plain words (owner, 19 Nov: no technical words on anything user-facing) ----------
   One display vocabulary for every string a loop screen shows, whether typed in these modules or read from the demo
   data file: applied to the text of the canvas and of each evidence drawer after render. Figures are never touched
   (no rule contains a digit). tools/vocab_check.cjs scans the rendered result against the banned list. */
const PLAIN_WORDS=[
 [/\bstructure evaluator\b/g,'calculation'],[/\bevaluator(?:'s|’s)\b/g,'calculation’s'],[/\bevaluator\b/g,'calculation'],
 [/\bProtect structure\b/g,'Protect measures'],[/\bevaluated through\b/g,'worked out through'],
 [/\bFactor structures?\b/g,'Breakdown'],[/\bfactor structures?\b/g,'breakdown'],
 [/\bhow it composes\b/g,'how it adds up'],[/\bthe structure composes them\b/g,'they add up'],[/\bcomposes\b/g,'builds up'],
 [/\b12-month horizon\b/g,'12 months'],[/\bhorizons?\b/g,'period'],[/\bHorizon\b/g,'Period'],
 [/\bforward replay\b/g,'forward simulation'],[/\bForward replay\b/g,'Forward simulation'],[/\bforward-replay\b/g,'forward-simulation'],
 [/\breplayed\b/g,'simulated'],[/\bReplayed\b/g,'Simulated'],[/\breplays\b/g,'simulations'],[/\breplay\b/g,'simulation'],[/\bReplay\b/g,'Simulation'],
 [/\bNot admissible\b/g,'Not allowed'],[/\bnot admissible\b/g,'not allowed'],[/\bAdmissible\b/g,'Allowed'],[/\badmissible\b/g,'allowed'],
 [/\bdecides admissibility\b/g,'decides whether it is allowed'],[/\bAdmissibility\b/g,'Allowed or not'],[/\bEvaluated through\b/g,'Worked out through'],[/\bspecification\b/g,'description'],[/\badmissibility\b/g,'whether it is allowed'],
 [/Σ ÷ Σ/g,'total ÷ total'],[/Σ over\b/g,'summed over'],[/Σ of\b/g,'sum of'],[/Σ\s?/g,'sum '],
 [/\bwith the evidence class in words\b/g,'with how each figure is evidenced'],[/\bthe evidence class is in words\b/g,'each figure says how it is evidenced'],
 [/\bevidence classes\b/g,'evidence types'],[/\bevidence class\b/g,'evidence type'],[/\bEvidence class\b/g,'Evidence type'],
 [/\bIts levers\b/g,'What can be changed'],[/\blevers\b/g,'moves'],[/\blever\b/g,'move'],
 [/\bleaf factors\b/g,'base factors'],[/\bleaf factor\b/g,'base factor'],[/\bLeaf factors?\b/g,'Base factor'],
 [/\bDisposition\b/g,'Status'],[/\bdisposition\b/g,'status'],[/\bguardrails\b/g,'safety limits'],[/\bguardrail\b/g,'safety limit'],
];
function plainWords(root){if(!root)return;const w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT,{acceptNode:n=>n.parentElement&&n.parentElement.closest('details.tech,pre.code,script,style')?NodeFilter.FILTER_REJECT:NodeFilter.FILTER_ACCEPT});let n;
 while((n=w.nextNode())){let v=n.nodeValue;if(!/[A-Za-zΣ]/.test(v))continue;const o=v;for(const [r,s] of PLAIN_WORDS)v=v.replace(r,s);if(v!==o)n.nodeValue=v;}
 root.querySelectorAll('[aria-label],[title]').forEach(e=>['aria-label','title'].forEach(a=>{const v=e.getAttribute(a);if(!v)return;let x=v;for(const [r,s] of PLAIN_WORDS)x=x.replace(r,s);if(x!==v)e.setAttribute(a,x);}));}
function afterRender(s){if(s.loop||s.opScoped){tagReplay(document.querySelector('.canvas'));plainWords(document.querySelector('.canvas'));} /* preserved v7.0 pages carry no replay figures; their numbers are left untouched */document.querySelectorAll('.scroll-region').forEach(el=>{if(el.scrollWidth>el.clientWidth+1)el.classList.add('scrolls');});}

/* click and change hooks */
/* ---------- theme: follow the system, or light, or dark (top bar) ---------- */
const THEMES=['system','light','dark'],THEME_WORD={system:'Theme: follows your system',light:'Theme: light',dark:'Theme: dark'};
let THEME='system';try{const v=localStorage.getItem('l4-theme');if(THEMES.includes(v))THEME=v;}catch{}
function applyTheme(){const r=document.documentElement;if(THEME==='system')r.removeAttribute('data-theme');else r.setAttribute('data-theme',THEME);}
applyTheme();
function themeToggle(){const g={system:'◐',light:'☀',dark:'☾'}[THEME];return `<button class="theme-toggle" data-theme-toggle aria-label="${THEME_WORD[THEME]}. Change theme" title="${THEME_WORD[THEME]}"><span aria-hidden="true">${g}</span></button>`;}
function loopClick(e){const el=e.target.closest('button,a,input');if(!el)return false;
 if(el.matches('[data-theme-toggle]')){THEME=THEMES[(THEMES.indexOf(THEME)+1)%3];try{localStorage.setItem('l4-theme',THEME);}catch{}applyTheme();el.outerHTML=themeToggle();document.querySelector('[data-theme-toggle]')?.focus();return true;}
 if(el.dataset.evd){e.preventDefault();openEvidence(el.dataset.evd);return true;}
 if(el.hasAttribute('data-loop-changes')){loopChanges();return true;}
 if(el.hasAttribute('data-pilot-submit')){e.preventDefault();toast('Example only: nothing is sent from this mock-up.');return true;}
 if(el.dataset.pilotDrawer!==undefined&&el.hasAttribute('data-pilot-drawer')){pilotDrawer();return true;}
 return false;}
function loopChange(e){const t=e.target;
 if(t.id==='op-switch'){const s=currentScreen();setOp(t.value);if(s.opScoped||(!s.section&&!s.site&&s.root!=='Sites')||s.gtabs){render();}else location.hash='/portfolio';return true;}
 if(t.id==='loop-site-switch'){const s=currentScreen();const tab=s.siteTab||({Overview:'Overview',Financials:'Financials'})[s.section]||s.section||'Overview';location.hash='/'+tabRoute(t.value,LOOP_SITE_TABS.includes(tab)?tab:'Overview');return true;}
 if(t.name==='sw-budget'){LS.budget=+t.value;rerenderKeep(t);return true;}
 if(t.name==='sw-loi'){LS.loi=t.value==='yes';rerenderKeep(t);return true;}
 if(t.name==='sw-agg'){LS.agg=t.value==='yes';rerenderKeep(t);return true;}
 if(t.name==='sw-tou'){LS.tou=t.value==='yes';rerenderKeep(t);return true;}
 return false;}
function rerenderKeep(t){const sel=`input[name="${t.name}"][value="${t.value}"]`;const y=window.scrollY;render();window.scrollTo(0,y);document.querySelector(sel)?.focus();const live=document.getElementById('plan-live');if(live)live.textContent=live.dataset.say||'';}
