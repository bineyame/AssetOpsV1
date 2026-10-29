/* v7.0 outcome organisation (commercial capability architecture rev 5, sections 4 to 9).
   Presentation over the same illustrative records as v6.9. Nothing here is a new analytic. */
const O_NAME={O1:'Revenue',O2:'Operating cost',O3:'Service and stock protection',O4:'Asset life',O5:'Return on assets',O6:'Evidence and assurance'};
const VO={
 'MG-1':['Productive electricity sales','O1'],'MG-2':['Supply cost per kWh','O2'],'MG-3':['Site profitability','O5'],'MG-4':['Battery and generator life','O4'],'MG-5':['Reliable service','O3'],'MG-6':['Cash collected','O1'],'MG-7':['Evidence for investors','O6'],
 'EV-1':['Buses ready to run','O3'],'EV-2':['Energy cost per km','O2'],'EV-3':['Charger use','O1'],'EV-4':['Battery and charger life','O4'],'EV-5':['Room before depot expansion','O5'],'EV-6':['Energy billed against metered','O1'],'EV-7':['Evidence for depot investment','O6'],
 'CC-1':['Stock kept saleable','O3'],'CC-2':['Paid cold-room use','O1'],'CC-3':['Cost per cooling unit','O2'],'CC-4':['Market value of produce','O1'],'CC-5':['Compressor life','O4'],'CC-6':['Cooling continuity','O3'],'CC-7':['Quality evidence','O6']};
const voName=c=>VO[c][0];
const voLabel=c=>`${VO[c][0]} <span class="oc-code">${c}</span>`;
/* The seven status states (rev 5 §4.2), plain words on screen. */
const OST={
 na:['Not applicable','oc-na','The site’s set-up shows this does not apply'],
 notyet:['Not assessed yet','oc-notyet','Nothing measures this yet'],
 unknown:['Unknown','oc-unknown','Readings or records are incomplete'],
 needs:['Needs attention','oc-needs','Misses its objective, or an open problem needs action'],
 watch:['Watch','oc-watch','No objective set, but a signal points one way'],
 noobj:['No objective set','oc-noobj','Measured, but no objective is set'],
 ontrack:['On track','oc-ontrack','Meets its objective over a complete period']};
const ocChip=k=>`<span class="oc-chip ${OST[k][1]}">${OST[k][0]}</span>`;
const proposed=(text='Proposed, pending owner decision')=>`<span class="oc-proposed" title="Shown with the architect’s proposed default. The owner has not decided this yet.">${text}</span>`;
const declared=(p)=>`<span class="oc-declared">Declared objective</span>${p?proposed('Proposed objective, pending owner decision'):''}`;
/* What each Finding moves (rev 5 §4.3), with the outcomes it must not harm. */
const MOVES={
 'F-104':{moves:['MG-2'],via:'generator and battery settings',guard:['MG-5','MG-4']},
 'F-108':{moves:['MG-7'],via:'battery reporting',guard:[],note:'Also limits how far the supply-cost finding can go'},
 'F-109':{moves:['MG-1'],via:'spare daytime solar',guard:['MG-2','MG-5']},
 'F-118':{moves:['CC-6','CC-1'],via:'backup readiness',guard:['CC-5']},
 'F-119':{moves:['CC-1'],via:'chamber temperature control',guard:['CC-3']},
 'F-130':{moves:['EV-1'],via:'charger faults',guard:['EV-4']}};
function movesText(fid,short=false){const m=MOVES[fid];if(!m)return '';
 const mv=m.moves.map(voName).join(', ');
 return short?`Moves: ${mv}`:`Moves: ${mv} · through ${m.via}${m.guard.length?` · Must not harm: ${m.guard.map(voName).join(', ')}`:''}`;}
const movesLine=(fid)=>MOVES[fid]?`<small class="oc-moves">${movesText(fid)}</small>`:'';
function movesStrip(fid){const m=MOVES[fid];if(!m)return '';
 return `<div class="oc-movestrip" role="note"><span class="oc-k">This finding moves</span>${m.moves.map(c=>`<span class="oc-pill">${voLabel(c)}</span>`).join('')}<span class="oc-k">through</span><span>${m.via}</span>${m.guard.length?`<span class="oc-k">Must not harm</span>${m.guard.map(c=>`<span class="oc-pill guard">${voLabel(c)}</span>`).join('')}`:''}${m.note?`<span class="muted">${m.note}</span>`:''}</div>`;}

/* Signals not yet priced (rev 5 §5). dir: risk | opp | stress. Always labelled "not priced". */
const SIGNALS=[
 {id:'s-dispatch',d:'mini',code:'MG-2',dir:'risk',kind:'Dispatch',title:'Generator kept running while the battery could carry the load',seen:'Some avoidable generator time on 24 of the last 30 days',persist:'Recurring',ev:['Dispatch','dispatch'],money:'Priced separately in Financials where the fuel price is set',missing:''},
 {id:'s-solar',d:'mini',code:'MG-1',dir:'opp',kind:'Headroom',title:'Daytime solar left unused',seen:'18–20 kW spare on 3 of 5 well-observed days',persist:'Recurring',ev:['Renewable','renewable'],money:'Needs: who would buy it, at what price, and what share gets paid'},
 {id:'s-reserve',d:'mini',code:'MG-4',dir:'stress',kind:'Early stress',title:'Battery went below its 30% reserve',seen:'5 of the last 30 days · lowest 22%',persist:'Recurring',ev:['Battery overview','asset-overview'],money:'Needs: a tested model of battery wear and a replacement cost'},
 {id:'s-genservice',d:'mini',code:'MG-4',dir:'stress',kind:'Early stress',title:'Generator service due soon',seen:'462 of 500 running hours since the last service',persist:'Observed',ev:['Preventive plan','maintenance-preventive'],money:'Needs: service cost and wear model'},
 {id:'s-mini-ev',d:'mini',code:'MG-7',dir:'risk',kind:'Evidence',title:'One battery report missing',seen:'30 minutes cannot be classified',persist:'Observed',ev:['Evidence','evidence'],money:'Not a money outcome; it limits the others'},
 {id:'s-maint',d:'cold',code:'CC-6',dir:'risk',kind:'Maintenance',title:'Repeated maintenance without result',seen:'Backup generator GEN-CR-01: 3 visits in 60 days (WR-011, WR-016, WR-019); the automatic start still failed on 6 Oct',persist:'Recurring',ev:['Work request WR-019','wr-overview'],money:'Needs: cost per visit, which is not set for this site',leak:true},
 {id:'s-cold-down',d:'cold',code:'CC-6',dir:'risk',kind:'Downtime',title:'Cooling stopped on grid loss',seen:'3 grid losses in 30 days · backup started by itself on 2',persist:'Recurring',ev:['Backup','coldbackup'],money:'Needs: contract terms or penalties for interrupted cooling'},
 {id:'s-exc',d:'cold',code:'CC-1',dir:'risk',kind:'Exposure',title:'Chamber above 4°C',seen:'25–35 min above the limit · peak 8.2°C',persist:'Observed',ev:['Temperature','temperature'],money:'Needs: which stock was in the room, its value and the product’s rules'},
 {id:'s-pm0455',d:'cold',code:'CC-5',dir:'stress',kind:'Early stress',title:'Backup start test overdue',seen:'Monthly witnessed start test due 2 Oct, not done',persist:'Persistent',ev:['Preventive plan','maintenance-preventive'],money:'Needs: wear model and repair cost'},
 {id:'s-coil',d:'cold',code:'CC-5',dir:'stress',kind:'Early stress',title:'Compressor coil cleaning due soon',seen:'Quarterly cleaning due 15 Oct · compressor cycles are not counted yet',persist:'Observed',ev:['Preventive plan','maintenance-preventive'],money:'Needs: compressor run and cycle counts, wear model'},
 {id:'s-ev-down',d:'ev',code:'EV-1',dir:'risk',kind:'Downtime',title:'Connector 2 out of service',seen:'1 h out of service and 1 h unknown on 6 Oct · status also unknown on 15 Sep',persist:'Recurring',ev:['Availability','availability'],money:'Needs: the bus roster, to know which departures were affected'},
 {id:'s-ev-fault',d:'ev',code:'EV-4',dir:'stress',kind:'Early stress',title:'Charger fault and overdue inspection',seen:'Connector 2 stopped a session on a fault · monthly connector inspection overdue since 30 Sep',persist:'Observed',ev:['Charger health','ev-health'],money:'Needs: repair cost and fault history per charger'},
 {id:'s-ev-idle',d:'ev',code:'EV-3',dir:'opp',kind:'Headroom',title:'Chargers mostly idle',seen:'120 kWh delivered in an 8-hour day, under a fifth of what the 80 kW limit allows',persist:'Observed',ev:['Energy','energy'],money:'Needs: other fleets’ demand and a rate for selling charging time'},
 {id:'s-ev-peak',d:'ev',code:'EV-5',dir:'risk',kind:'Capacity',title:'Peak close to the site import limit',seen:'Peak 76 kW against an 80 kW limit',persist:'Observed',ev:['Energy','energy'],money:'Needs: a demand forecast and the cost of expanding'}];
const DIR_TEXT={risk:'Risk to',opp:'Opportunity for',stress:'Early stress warning ·'};
function signalLabel(x){return x.dir==='stress'?`Early stress warning · ${voName(x.code)} · not a condition assessment · not priced`:`${DIR_TEXT[x.dir]} ${voName(x.code)} · not priced`;}
const sigTag=x=>`<span class="oc-sig ${x.dir}">${x.dir==='opp'?'Opportunity':x.dir==='stress'?'Early stress warning':'Risk'}</span>`;
function signalCard(x){return `<article class="oc-signal ${x.dir}"><div class="oc-signal-top">${sigTag(x)}<span class="oc-kind">${x.kind}</span><span class="oc-persist">${x.persist}</span></div><h3>${x.title}</h3><p>${x.seen}</p><p class="oc-label">${signalLabel(x)}</p><p class="oc-need">${x.money}${x.leak?` ${proposed('Cost per visit: proposed as a later site setting, pending owner decision')}`:''}</p>${link(x.ev[1],`${x.ev[0]} →`)}</article>`;}
const signalsFor=(d,code)=>SIGNALS.filter(x=>x.d===d&&(!code||x.code===code));

/* Per-site outcomes, in chain order: objective → status → drivers → problems and signals → levers → action → proof. */
const NA=(t)=>`<span class="oc-missing">Not available yet${t?': '+t:''}</span>`;
const SITE_OUT={
 mini:[
  {code:'MG-2',st:'needs',obj:['The generator runs only when the battery cannot carry the load',true],reason:'30 min of avoidable generator time in the selected hour; seen on most days',drivers:'Generator stop setting (90% charge) and battery reserve · fuel price · load and solar',problems:[['F-104 · Generator support review','finding']],sig:['s-dispatch'],levers:[['Trial a lower generator stop setting','recommendation']],action:['ACT-048 · Reduce extended generator support','verification'],proof:['Before-and-after check with three must-not-harm tests (service, reserve, stored energy)','verification','Then: cost per kWh compared on the same basis · not available yet']},
  {code:'MG-1',st:'unknown',obj:['At least 20 kWh a day of daytime solar sold to productive users',true],reason:'Sales to productive users are not metered',drivers:'Spare daytime solar and battery room · demand · tariff · payment',problems:[['F-109 · Productive-use headroom','opportunity-finding']],sig:['s-solar'],levers:[['Grain-mill what-if (gross sales only)','opportunity-finding']],action:null,proof:null},
  {code:'MG-5',st:'unknown',obj:['No unmet demand at the clinic',true],reason:'Power delivered is measured; what customers needed is not',drivers:'Battery reserve · generator readiness · faults and weather',problems:[],sig:[],levers:[['Raise reserve for critical hours','service']],action:null,proof:['Checked as a must-not-harm test inside the generator trial','verification']},
  {code:'MG-4',st:'watch',obj:null,reason:'Early stress warnings; battery condition itself is not assessed',drivers:'Depth and frequency of discharge · generator starts and running hours',problems:[],sig:['s-reserve','s-genservice'],levers:[['Reserve and depth limits','foundation'],['Service on schedule','maintenance-preventive']],action:null,proof:null},
  {code:'MG-7',st:'watch',obj:null,reason:'Evidence limited: one battery report missing',drivers:'Reporting coverage · source of readings',problems:[['F-108 · Battery output-limit report missing','evidence']],sig:['s-mini-ev'],levers:[['Restore battery reporting','sitework']],action:['ACT-049 · Restore reporting','sitework'],proof:null},
  {code:'MG-3',st:'notyet',obj:null,reason:'No site ledger: income, operating costs and capital are not recorded',drivers:'Everything above, plus fixed costs and capital',problems:[],sig:[],levers:[],action:null,proof:null,missing:'site income and cost records'},
  {code:'MG-6',st:'notyet',obj:null,reason:'No billing or payment records',drivers:'Metering · vending · payment discipline',problems:[],sig:[],levers:[],action:null,proof:null,missing:'billing and payment records'}],
 cold:[
  {code:'CC-6',st:'needs',obj:['Backup starts by itself on every grid loss',true],reason:'Automatic start failed on 6 Oct; three visits have not fixed it',drivers:'Backup readiness · maintenance response · grid reliability',problems:[['F-118 · Backup response failed','cold-finding']],sig:['s-maint','s-cold-down'],levers:[['Witnessed automatic-start test after repair','cold-action']],action:['ACT-051 · Witness automatic-start test','cold-action'],proof:['Check that the next automatic start succeeds, with chamber temperature as a must-not-harm test','cold-action','first']},
  {code:'CC-1',st:'needs',obj:['Chamber kept at 2–4°C',false],reason:'25–35 min above 4°C; peak 8.2°C',drivers:'Temperature control · door use · backup readiness',problems:[['F-119 · Temperature excursion','cold-finding-excursion'],['F-118 · Backup response failed','cold-finding']],sig:['s-exc'],levers:[['Stock value what-if (context only)','cold-scenarios']],action:['Record stock and door log','cold-work'],proof:null},
  {code:'CC-5',st:'watch',obj:null,reason:'Early stress warnings; compressor condition is not assessed',drivers:'Compressor cycling · servicing · backup starts',problems:[],sig:['s-pm0455','s-coil'],levers:[['Service on schedule','maintenance-preventive']],action:null,proof:null},
  {code:'CC-7',st:'watch',obj:null,reason:'Evidence complete for this event; calibration not recorded',drivers:'Probe coverage · calibration',problems:[],sig:[],levers:[],action:null,proof:null},
  {code:'CC-3',st:'notyet',obj:null,reason:'Cooling energy and stored volume are not measured',drivers:'Compressor duty · insulation · tariff',problems:[],sig:[],levers:[],action:null,proof:null,missing:'a cooling energy meter and stored-volume records'},
  {code:'CC-2',st:'notyet',obj:null,reason:'No occupancy or storage contracts recorded',drivers:'Occupancy · storage rates',problems:[],sig:[],levers:[],action:null,proof:null,missing:'occupancy and storage contract records'},
  {code:'CC-4',st:'notyet',obj:null,reason:'No quality, sales or market price records',drivers:'Product quality · market price',problems:[],sig:[],levers:[],action:null,proof:null,missing:'quality and sales records'}],
 ev:[
  {code:'EV-1',st:'needs',obj:['Every scheduled charge completes',true],reason:'1 session interrupted and 1 outcome unknown of 12; buses and departures are not linked yet',drivers:'Charger faults · shared site power · departure schedule',problems:[['F-130 · Charging session interrupted','ev-finding']],sig:['s-ev-down'],levers:[['Investigate connector 2','ev-action']],action:['ACT-061 · Investigate connector 2','ev-action'],proof:['Check that connector 2 completes its scheduled sessions','ev-action','alt']},
  {code:'EV-5',st:'ontrack',obj:['Stay under the 80 kW site import limit',false],reason:'Peak 76 kW · close to the limit',drivers:'Peak demand · charge scheduling',problems:[],sig:['s-ev-peak'],levers:[['Load sharing between chargers','ev-sld']],action:null,proof:null},
  {code:'EV-3',st:'watch',obj:null,reason:'Chargers mostly idle in the service day',drivers:'Spare connector time · other fleets’ demand',problems:[],sig:['s-ev-idle'],levers:[],action:null,proof:null},
  {code:'EV-2',st:'unknown',obj:['Charging cost within the declared tariff',true],reason:'Cost per km needs odometer readings; a tariff estimate exists',drivers:'Tariff · demand charge · charging efficiency',problems:[],sig:[],levers:[['Tariff assumption','ev-financials']],action:null,proof:null},
  {code:'EV-4',st:'watch',obj:null,reason:'Early stress warning; charger condition is not assessed',drivers:'Fault history · inspection',problems:[],sig:['s-ev-fault'],levers:[['Connector inspection','maintenance-preventive']],action:null,proof:null},
  {code:'EV-7',st:'watch',obj:null,reason:'Evidence limited: connector 2 status missing 15:00–16:00',drivers:'Reporting coverage',problems:[],sig:[],levers:[],action:null,proof:null},
  {code:'EV-6',st:'notyet',obj:null,reason:'No independent depot meter or settlement records',drivers:'Meter and settlement boundary',problems:[],sig:[],levers:[],action:null,proof:null,missing:'settlement records'}]};
const outOf=(d,c)=>SITE_OUT[d].find(x=>x.code===c);
const OUT_ROUTE={mini:'mini-outcomes',cold:'cold-outcomes',ev:'ev-outcomes'};

function ocStep(label,body){return `<div class="oc-step"><div class="oc-step-k">${label}</div><div class="oc-step-v">${body}</div></div>`;}
function outcomeCard(d,o){
 const sig=o.sig.map(id=>SIGNALS.find(x=>x.id===id)),obj=o.obj?`${escapeHtml(o.obj[0])}<br>${declared(o.obj[1])}`:o.missing?NA(o.missing):`<span class="muted">No objective set</span>`;
 const list=a=>a.length?a.map(([t,h])=>link(h,t)).join('<br>'):'';
 const probs=[list(o.problems),sig.map(x=>`${sigTag(x)} ${x.title}`).join('<br>')].filter(Boolean).join('<br>')||(o.missing?NA():'<span class="muted">None open</span>');
 const proof=o.proof?`${link(o.proof[1],o.proof[0])}${o.proof[2]==='first'?`<br>${proposed('Proposed as the first full check outside the mini-grid, pending owner decision (alternative: Depot charging)')}`:o.proof[2]==='alt'?`<br>${proposed('Alternative first full check outside the mini-grid, pending owner decision')}`:o.proof[2]?`<br><span class="oc-missing">${o.proof[2]}</span>`:''}`:NA(o.missing?o.missing:'nothing checks this yet');
 return `<article class="oc-card st-${o.st}" id="oc-${o.code}"><header><div><h3>${voName(o.code)}</h3><span class="oc-code">${o.code} · ${O_NAME[VO[o.code][1]]}</span></div>${ocChip(o.st)}</header><p class="oc-reason">${o.reason}</p>
 <div class="oc-chain">${ocStep('Objective',obj)}${ocStep('What drives it',o.drivers)}${ocStep('Problems and signals',probs)}${ocStep('What can be done',list(o.levers)||NA(o.missing?'':'no lever yet'))}${ocStep('Action',o.action?link(o.action[1],o.action[0]):'<span class="muted">None</span>')}${ocStep('Proof',proof)}</div></article>`;}
function stateLegend(){return `<details class="oc-legend"><summary>How status is read</summary><ul>${Object.values(OST).map(([t,c,why])=>`<li><span class="oc-chip ${c}">${t}</span> ${why}</li>`).join('')}</ul><p class="muted">First match wins, in this order: not applicable, not assessed yet, unknown, needs attention, watch, no objective set, on track. Status is a reading, not a score; outcomes are never combined into one health number.</p></details>`;}
function outcomesScreen(d){const rows=SITE_OUT[d],n=k=>rows.filter(x=>x.st===k).length;
 return status(`${badge(`${n('needs')} need attention`,'amber')} ${badge(`${n('watch')} on watch`,'blue')} ${badge(`${n('notyet')} not assessed yet`,'outline')}`,'Each outcome read along the same path: objective, what drives it, problems and signals, what can be done, action, proof',link(SITES[d].overview,'Back to overview →'))+
 stateLegend()+`<div class="oc-cards">${rows.map(o=>outcomeCard(d,o)).join('')}</div>`+
 panel('Signals at this site · not priced',`<div class="oc-signals">${signalsFor(d).map(signalCard).join('')}</div>`,'Direction and evidence only, until a price or cost basis exists')+
 notice('Objectives marked “Declared objective” are set for this demonstration. They are not the customer’s own targets.','blue');}
function siteOutcomeStrip(d){return `<nav class="oc-strip" aria-label="Outcomes at this site">${SITE_OUT[d].map(o=>`<a href="#/${OUT_ROUTE[d]}" class="oc-strip-item st-${o.st}"><span>${voName(o.code)}</span>${ocChip(o.st)}</a>`).join('')}</nav>`;}

/* Findings › Signals not yet priced */
function signalsTable(f='All'){const rows=SIGNALS.filter(x=>f==='All'||(f==='Risks'&&x.dir==='risk')||(f==='Opportunities'&&x.dir==='opp')||(f==='Early stress'&&x.dir==='stress'));
 return table(['Signal','Site · outcome','What was seen','How often','What would put a price on it'],rows.map(x=>[`${sigTag(x)}<br>${link(x.ev[1],x.title,'strong')}<small>${signalLabel(x)}</small>`,`${link(OUT_ROUTE[x.d],SITES[x.d].name)}<small>${voLabel(x.code)}</small>`,x.seen,x.persist,`${x.money}${x.leak?`<br>${proposed('Cost per visit: proposed later, pending owner decision')}`:''}`]));}
function signalsScreen(){const c=k=>SIGNALS.filter(x=>x.dir===k).length;
 return cards([metric('Risks',String(c('risk')),'Pointing against an outcome','amber'),metric('Opportunities',String(c('opp')),'Pointing toward an outcome','green'),metric('Early stress warnings',String(c('stress')),'Not a condition assessment'),metric('Money shown','None','A signal is never a money figure')])+
 `<div class="chips" data-filter-group="signals">${['All','Risks','Opportunities','Early stress'].map((x,i)=>`<button class="chip ${i===0?'active':''}" data-signal-filter="${x}" aria-pressed="${i===0}">${x}</button>`).join('')}</div>`+
 panel('Signals not yet priced',`<div id="signals-table">${signalsTable()}</div>`,'Each signal names the outcome it points at and what is missing to price it')+
 notice('A signal says which way something points and how often it was seen. It becomes a money figure only when a price or cost basis, a unit and enough history exist.','blue');}
document.addEventListener('click',e=>{const el=e.target.closest('[data-signal-filter]');if(!el)return;
 document.querySelectorAll('[data-signal-filter]').forEach(x=>{x.classList.toggle('active',x===el);x.setAttribute('aria-pressed',String(x===el));});
 const t=document.querySelector('#signals-table');if(t)t.innerHTML=signalsTable(el.dataset.signalFilter);});

/* Portfolio: outcome rows (owner-approved change from v6.9's five operating rows). */
const PF_ROWS=[['O1',{mini:'MG-1',cold:'CC-2',ev:'EV-3'}],['O2',{mini:'MG-2',cold:'CC-3',ev:'EV-2'}],['O3',{mini:'MG-5',cold:'CC-6',ev:'EV-1'}],['O4',{mini:'MG-4',cold:'CC-5',ev:'EV-4'}],['O5',{mini:'MG-3',cold:'CC-2',ev:'EV-5'}],['O6',{mini:'MG-7',cold:'CC-7',ev:'EV-7'}]];
function pfCell(d,code){if(!code)return `<span class="oc-cell oc-na"><b>Not applicable</b><small>Shared with revenue for cold rooms</small></span>`;
 const o=outOf(d,code),also=d==='cold'&&code==='CC-6'?outOf('cold','CC-1'):null;
 return `<a class="oc-cell ${OST[o.st][1]}" href="#/${OUT_ROUTE[d]}" aria-label="${voName(code)}: ${OST[o.st][0]}"><b>${OST[o.st][0]}</b><small>${voName(code)}${also?' · '+voName(also.code):''}</small><small class="oc-code">${code}${also?', '+also.code:''}</small>${o.obj?`<span class="oc-declared">Declared</span>`:''}</a>`;}
function portfolioOutcomes(){return `<div class="oc-matrix" role="table" aria-label="Outcomes across the estate"><div class="oc-mrow oc-mhead" role="row"><span role="columnheader">Outcome</span>${['mini','cold','ev'].map(d=>`<span role="columnheader">${link(OUT_ROUTE[d],SITES[d].name.split(' ')[0])}</span>`).join('')}</div>${PF_ROWS.map(([o,m])=>`<div class="oc-mrow" role="row"><span role="rowheader" class="oc-orow"><b>${O_NAME[o]}</b><small>${o}</small></span>${['mini','cold','ev'].map(d=>`<span role="cell">${pfCell(d,m[d])}</span>`).join('')}</div>`).join('')}</div><p class="chart-note">Each cell is that site’s own reading of the outcome. Not assessed yet is not healthy. ${link('signals','Signals not yet priced →')}</p><p class="chart-note">“Declared” objectives are set for this demonstration ${proposed('Which outcomes get one: proposed, pending owner decision')}</p>`;}
function portfolioSignals(){const pick=['s-maint','s-dispatch','s-reserve','s-ev-down','s-solar'].map(id=>SIGNALS.find(x=>x.id===id));
 return `<section class="panel oc-pf-signals"><div class="panel-head"><div><h2>Signals not yet priced</h2><p>Direction and evidence where money cannot be calculated yet</p></div>${link('signals',`All ${SIGNALS.length} →`)}</div><ul class="oc-siglist">${pick.map(x=>`<li>${sigTag(x)}<div>${link(x.ev[1],x.title,'strong')}<small>${SITES[x.d].name.split(' ')[0]} · ${signalLabel(x)}</small></div></li>`).join('')}</ul></section>`;}
function buildOrderNote(){return `<details class="oc-review"><summary>${proposed('Proposed build order, pending owner decision')}</summary><ol><li>Label and link every screen by outcome</li><li>Declared objectives and status</li><li>Signals not yet priced, including repeated maintenance</li><li>Proof for supply cost: compare cost on the same basis after the trial</li><li>Early stress warnings for asset life</li><li>First full check outside the mini-grid: cooling continuity (alternative: Depot charging)</li><li>Productive-use contribution what-if</li></ol><p class="muted">Reviewer note, not part of the product screen.</p></details>`;}
