/* ===== Layer 4 rev 5 mock-up · Protect as a declared structure of measured factors =====
   Each measure has a unit, a period, a target (0), an evidence class, per-site values and a Σ over sites
   (manifest tenants[*].portfolio.protect). Money-valued measures (liability, penalties) are the SAME factor as the
   cost-to-serve line, referenced, never added twice. Values at stake are listed, never summed. */
const PNAME = {unserved_critical_kwh:'Critical energy not served',customer_hours_interrupted:'Customer-hours interrupted',asset_value_at_risk:'Asset value at risk',obligation_hours_without_redundancy:'Obligation hours without a backup',asset_days_out_of_service:'Asset-days out of service',customer_liability:'Customer liability',
 batches_exposed:'Batches exposed above their limit',crate_minutes_above_limit:'Crate-minutes above the batch limit',days_backup_start_unproven:'Days with the backup start unproven',stock_value_exposed:'Customer stock value exposed',qa_confirmed_damage_liability:'Damage confirmed by inspection (liability)',
 departures_missed:'Required departures missed',nights_deliverable_below_required:'Nights with deliverable energy below required',charger_days_out_of_service:'Charger-days out of service',service_penalties:'Service penalties',rights_value_at_stake:'Rights and values at stake'};
const PUNIT = {'customer-hours':'customer-hours',kWh:'kWh',h:'hours','asset-days':'asset-days',USD:'US dollars',batches:'batches','crate-minutes':'crate-minutes',days:'days',departures:'departures',nights:'nights','charger-days':'charger-days'};
const TAGNAME = {'GEN-KS-02':'generator 2','GEN-KS-01':'generator 1','CH-R7':'charger 7','CH-K2':'charger 2','INV-MT-02':'inverter 2','BAT-001':'battery','GEN-CR-01':'backup generator','B-1031':'French-bean batch'};
function idPlain(t){return String(t).replace(/\b(GEN-KS-0[12]|CH-R7|CH-K2|INV-MT-02|BAT-001|GEN-CR-01|B-1031)\b/g,(m)=>`${TAGNAME[m]} (${m})`).replace(/(\d)-(\d)/g,'$1–$2').replace(/ x /g,' × ').replace(/ (\d+) C\b/g,' $1 °C').replace('O&M','maintenance-contract').replace('EPC','installation contractor’s').replace(' + service SLA',' and service agreement').replace(/ SLA\b/,' service agreement').replace(/^(\w)/,c=>c.toUpperCase());}
function rightName(site,r){const m=r.match(/^([A-Z]{2,3}-[A-Z0-9-]+) (.*)$/);const rest=m?m[2].replace(' + service SLA',' and service agreement'):'',par=m?(rest.match(/\(([^)]*)\)/)||[])[1]:'';return m?`${site} ${rest.replace(/\s*\([^)]*\)/,'')} (${m[1]}${par?'; '+par:''})`:`${site} ${idPlain(r).replace(/^./,c=>c.toLowerCase())}`;}
function siteKeyOf(op,name){return OPS[op].sites.find(sk=>siteM(sk).site===name);}
function protectOf(op){const P=OPS[op].t.portfolio.protect;return P.measures.map(m=>{const sites={};Object.entries(m.sites||{}).forEach(([n,v])=>{sites[siteKeyOf(op,n)]=v;});
 const nov=m.november_to_date?Object.fromEntries(Object.entries(m.november_to_date).filter(([k])=>k!=='detail').map(([k,v])=>[k==='portfolio'?'portfolio':siteKeyOf(op,k),v])):null;
 return {...m,name:PNAME[m.id]||m.id,sites,nov,novDetail:m.november_to_date?.detail,stake:m.class==='EXPOSURE'&&m.status!=='NOT_AVAILABLE_YET',na:m.status==='NOT_AVAILABLE_YET',money:m.unit==='USD',detailBy:m.detail?Object.fromEntries(Object.entries(m.detail).map(([n,v])=>[siteKeyOf(op,n),idPlain(v)])):{}};});}
const pfmt = (m,v) => v===undefined||v===null?'—':typeof v==='string'?v.replace(/-/g,'–'):m.money?usd(v):num(v);
const pnum = v => typeof v==='string'?Number(v.split(/[-–]/).pop().replace(/,/g,'')):Number(v||0);
const pstate = (m,v) => pnum(v)>0?badge('Above its target','red'):badge('At its target','green');
const sharedNote = m => m.shared_factor?`<small class="cellnote">Same factor as the cost-to-serve ${m.id==='service_penalties'?'penalties':m.id==='customer_liability'?'liability':'customer compensation'} line: shown once in money, never added twice</small>`:'';
function protectTable(op){const o=OPS[op],ms=protectOf(op).filter(m=>!m.stake&&!m.na),ev=o.vertical==='ev';
 const head=['Protect measure','Target',...o.sites.map(sk=>SK[sk].name),'Portfolio Σ','Evidence','State'];
 const rows=ms.map(m=>[`<b>${m.name}</b> <small class="cellnote">${PUNIT[m.unit]||m.unit}, October${m.basis?' · '+idPlain(m.basis):''}</small>${sharedNote(m)}`,m.money?usd(m.target):num(m.target),...o.sites.map(sk=>`${pfmt(m,m.sites[sk])}${m.detailBy[sk]?`<small class="cellnote">${m.detailBy[sk]}</small>`:''}`),`<b>${pfmt(m,m.portfolio)}</b>`,ec(m.class),pstate(m,m.portfolio)]);
 let html=region('Protect measures by site',table(head,rows));
 if(ev){const nv=ms.filter(m=>m.nov);html+=`<h3 class="h3s">November to 6 Nov (shown separately, not added to October)</h3>`+region('Protect measures, November to 6 Nov',table(['Protect measure',...o.sites.map(sk=>SK[sk].name),'Portfolio Σ','State'],nv.map(m=>[`<b>${m.name}</b>${m.novDetail?`<small class="cellnote">${idPlain(m.novDetail)}</small>`:''}${sharedNote(m)}`,...o.sites.map(sk=>pfmt(m,m.nov[sk]??0)),`<b>${pfmt(m,m.nov.portfolio??o.sites.reduce((a,sk)=>a+(m.nov[sk]||0),0))}</b>`,pstate(m,m.nov.portfolio??o.sites.reduce((a,sk)=>a+(m.nov[sk]||0),0))])));}
 return html+naList(op)+stakeList(op);}
function naList(op){const na=protectOf(op).filter(m=>m.na);if(!na.length)return '';return `<h3 class="h3s">Not available yet</h3><ul class="list">${na.map(m=>`<li><b>${m.name}</b> ${ec('MISSING')}: needs a failure-likelihood basis (condition data and failure history) that the demo does not hold; expected loss is shown only with a defensible likelihood. Deferred to a pilot.</li>`).join('')}</ul>`;}
function stakeList(op,sk){const items=[];protectOf(op).filter(m=>m.stake).forEach(m=>{if(m.items)m.items.forEach(it=>{const k=siteKeyOf(op,it.site);if(!sk||k===sk)items.push([rightName(SK[k].name,it.right),typeof it.value==='number'?usd(it.value):it.value,cap(idPlain(it.state))]);});else Object.entries(m.sites).forEach(([k,v])=>{if((!sk||k===sk)&&v)items.push([`${SK[k].name}: ${m.name.toLowerCase()}`,usd(v),cap(m.note?idPlain(m.note):'')]);});});
 if(!items.length)return '';
 return `<h3 class="h3s">At stake (not money): listed, never summed</h3>${region('Values at stake',table(['Right or value','Amount at stake','State'],items.map(r=>[r[0],`${r[1]} ${ec('EXPOSURE')}`,r[2]])))}<p class="note">These are values a right or an obligation protects. They are not money gained or lost and are never added to each other or to money figures.</p>`;}
function protectSite(sk){const op=SK[sk].op,ms=protectOf(op).filter(m=>!m.stake&&!m.na),ev=OPS[op].vertical==='ev';
 const rows=ms.map(m=>[`<b>${m.name}</b> <small class="cellnote">${PUNIT[m.unit]||m.unit}${m.detailBy[sk]?' · '+m.detailBy[sk]:''}</small>${sharedNote(m)}`,m.money?usd(m.target):num(m.target),`${pfmt(m,m.sites[sk])}`,...(ev?[m.nov?pfmt(m,m.nov[sk]??0):'—']:[]),ec(m.class),pstate(m,ev&&m.nov?pnum(m.sites[sk])+pnum(m.nov[sk]):m.sites[sk])]);
 return region(`Protect measures at ${SK[sk].name}`,table(['Protect measure','Target','October',...(ev?['November to 6 Nov']:[]),'Evidence','State'],rows))+stakeList(op,sk);}
/* one-line summaries for the Overview card and the site × outcome grid */
function protectCard(op){const ms=protectOf(op),ev=OPS[op].vertical==='ev',lines=[];
 ms.filter(m=>!m.stake&&!m.na).forEach(m=>{const v=m.portfolio,nv=m.nov?(m.nov.portfolio??Object.entries(m.nov).filter(([k])=>k!=='portfolio').reduce((a,[,x])=>a+x,0)):null;
  lines.push([`${m.name}: ${pfmt(m,v)}${m.money?'':' '+(PUNIT[m.unit]||m.unit)} in October${nv!==null?`; ${pfmt(m,nv)} in November to 6 Nov`:''} (target ${m.money?usd(m.target):num(m.target)})${m.shared_factor?' · same factor as the cost line':''}`,m.class]);});
 const above=ms.filter(m=>!m.stake&&!m.na&&(pnum(m.portfolio)>0||(m.nov&&pnum(m.nov.portfolio??0)>0))).length,tot=ms.filter(m=>!m.stake&&!m.na).length;
 const st=[];ms.filter(m=>m.stake).forEach(m=>{if(m.items)m.items.forEach(it=>{const k=siteKeyOf(op,it.site);st.push(`${rightName(SK[k].name,it.right)} ${typeof it.value==='number'?usd(it.value):it.value}`);});else Object.entries(m.sites).forEach(([k,v])=>{if(v)st.push(`${SK[k].name} ${m.name.toLowerCase()} ${usd(v)}`);});});
 ms.filter(m=>m.na).forEach(m=>lines.push([`${m.name}: not available yet (needs a failure-likelihood basis)`,'MISSING']));
 lines.push([`Listed, never summed: ${st.join('; ')}`,'EXPOSURE']);
 return {pos:`${above} of ${tot} measures above their target of 0${ev?' (October or November to date)':''}`,f:lines};}
function protectCell(op,sk){const ms=protectOf(op).filter(m=>!m.stake&&!m.na),out=[];
 ms.forEach(m=>{const v=m.sites[sk],nv=m.nov?m.nov[sk]:undefined;if(pnum(v)>0||pnum(nv)>0)out.push(`${m.name}: ${pfmt(m,v)}${nv!==undefined?` (Oct) · ${pfmt(m,nv)} (to 6 Nov)`:''}`);});
 return out.length?out.join('<br>'):'<span class="muted">Every measure at its target of 0</span>';}

/* ===== rev 6: operations measures (O2) and rights measures (P4/A5) ===== */
const ONAME = {asset_availability:'Asset availability',field_visits:'Field visits',delivered_kwh_per_field_visit:'Delivered kWh per field visit',cooling_availability:'Cooling availability',crate_days_without_excursion:'Crate-days without an excursion',charger_energy_utilisation:'Charger energy use',departures_met_per_charger_in_service:'Required departures met per charger in service'};
function opsOf(op){return OPS[op].t.portfolio.operations.measures.map(m=>{const site={},key=n=>siteKeyOf(op,n);
 if(m.numerator_asset_days_available)Object.keys(m.denominator_asset_days).forEach(n=>{const a=m.numerator_asset_days_available[n],d=m.denominator_asset_days[n];site[key(n)]=`${(a/d*100).toFixed(2)}% <small class="cellnote">${a} of ${d} asset-days</small>`;});
 else if(m.minutes_unavailable)Object.entries(m.minutes_unavailable).forEach(([n,v])=>{site[key(n)]=`${(100*(1-v/m.minutes_per_room)).toFixed(3)}% <small class="cellnote">${v} minutes lost</small>`;});
 else if(m.sites_pct)Object.entries(m.sites_pct).forEach(([n,v])=>{site[key(n)]=`${v.toFixed(2)}% <small class="cellnote">${num(m.numerator_kwh_per_night[n])} of ${num(m.denominator_kwh_per_night[n])} kWh a night</small>`;});
 else if(m.sites)Object.entries(m.sites).forEach(([n,v])=>{site[key(n)]=num(v);});
 const port=m.portfolio_pct!==undefined?`${m.portfolio_pct}%`:num(m.portfolio,2);
 const plan=m.plan===undefined?'not declared':m.unit.startsWith('%')?`${m.plan}%`:num(m.plan);
 return {...m,name:ONAME[m.id]||m.id,site,port,plan};});}
function opsTable(op){const o=OPS[op],ms=opsOf(op);
 return region('Operations measures by site',table(['Operations measure','Plan',...o.sites.map(sk=>SK[sk].name),'Portfolio (Σ ÷ Σ)','Evidence'],ms.map(m=>[`<b>${m.name}</b> <small class="cellnote">${m.unit}, October · ${idPlain(m.basis||'')}</small>`,m.plan,...o.sites.map(sk=>m.site[sk]||'—'),`<b>${m.port}</b>`,ec(m.class)])));}
function opsSite(sk){const op=SK[sk].op,ms=opsOf(op).filter(m=>m.site[sk]);if(!ms.length)return '';return region(`Operations measures at ${SK[sk].name}`,table(['Operations measure','Plan','October','Evidence'],ms.map(m=>[`<b>${m.name}</b> <small class="cellnote">${m.unit}</small>`,m.plan,m.site[sk],ec(m.class)])));}
function opsCardLines(op){return opsOf(op).map(m=>[`${m.name}: ${m.port}${m.plan!=='not declared'?` (plan ${m.plan})`:''}`,m.class]);}
const RNAME = {tracked_assets_with_complete_contract_evidence:'Tracked assets with complete contract evidence',rights_with_open_deadline:'Rights with an open deadline',remedy_completion_days:'Remedy completion',operator_funded_residual_expense:'Operator-funded residual expense, October',recognised_credits:'Credits recognised, October'};
function rightsMeasures(op){const ms=OPS[op].t.portfolio.rights.measures;
 const val=m=>{if(m.share){const it=m.items||{};return `${m.share}<small class="cellnote">${[['Complete',it.complete],['Incomplete',it.incomplete],['Expired or excluded',it.expired_or_excluded]].filter(([,v])=>v&&v.length).map(([k,v])=>`${k}: ${v.map(idPlain).join('; ')}`).join(' · ')}</small>`;}
  if(m.count!==undefined)return `${m.count}<small class="cellnote">Nearest: ${m.nearest.replace(/ \(([A-Z]{2,3}-[A-Z0-9-]+) (.*)\)/,(x,tag,rest)=>`: ${TAGNAME[tag]} (${tag}) ${rest.replace('SLA','service agreement')}`)}</small>`;
  if(m.october!==undefined)return usd(m.october);
  if(m.items)return m.items.length?m.items.map(i=>`${idPlain(i.right)}: ${i.days!==undefined?i.days+' days, ':''}${i.state}${i.from?` (from ${i.from}${i.to?' to '+i.to:''})`:''}`).join('<br>'):'none';return '—';};
 return region('Rights measures',table(['Measure','Value','Evidence','Note'],ms.map(m=>[`<b>${RNAME[m.id]||m.id}</b>`,val(m),ec(m.class),m.note?cap(idPlain(m.note).replace(/credit 70/,'credit $70').replace(/stopgap (\d+)/,'stop-gap $$$1')):'—'])))+'<p class="legal">This is not a legal decision. Coverage is decided by the supplier or insurer.</p>';}
