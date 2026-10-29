/* v7.0: the v6.9 assessment cards, organised around business outcomes (commercial capability architecture rev 5).
   Same illustrative records as v6.9; nothing here is a new analytic. Outcome codes stay internal. */
const OUTCOME={
 'MG-1':'Productive electricity sales','MG-2':'Supply cost per kWh','MG-3':'Site profitability','MG-4':'Battery and generator life','MG-5':'Reliable service','MG-6':'Cash collected','MG-7':'Evidence quality',
 'EV-1':'Buses ready to run','EV-2':'Energy cost per km','EV-3':'Charger use','EV-4':'Charger life','EV-5':'Room before expansion','EV-6':'Energy billed against metered','EV-7':'Evidence quality',
 'CC-1':'Stock kept saleable','CC-2':'Paid cold-room use','CC-3':'Cost per cooling unit','CC-4':'Market value of produce','CC-5':'Compressor life','CC-6':'Cooling continuity','CC-7':'Evidence quality'};
const TONE={needs:'amber',watch:'blue',unknown:'gray',notyet:'none',ontrack:'green'};
const STATE={needs:'Needs attention',watch:'Watch',unknown:'Unknown',notyet:'Not measured yet',ontrack:'On track'};
const STEP_NAMES=['Aim set','Problem found','Fix chosen','Work done','Result proven'];

/* What each Finding affects, in plain words. */
const AFFECTS={'F-104':[['MG-2'],['MG-5','MG-4']],'F-108':[['MG-7'],['MG-2']],'F-109':[['MG-1'],['MG-2','MG-5']],'F-118':[['CC-6','CC-1'],['CC-5']],'F-119':[['CC-1'],[]],'F-130':[['EV-1'],['EV-4']]};
const RECUR={'F-104':'Seen on 24 of the last 30 days','F-118':'3 grid losses in 30 days · backup started by itself on 2','F-109':'Spare on 3 of 5 well-observed days','F-130':'Connector 2 status also unknown on 15 Sep'};
const affectsPill=fid=>AFFECTS[fid]?`<span class="oc-affects">${AFFECTS[fid][0].map(c=>OUTCOME[c]).join(' · ')}</span>`:'';
const recurNote=fid=>RECUR[fid]?`<small class="oc-recur">${RECUR[fid]}</small>`:'';
function affectsLine(fid){const a=AFFECTS[fid];if(!a)return '';
 return `<div class="oc-affectsline"><span class="oc-k">Affects</span>${a[0].map(c=>`<span class="oc-pill">${OUTCOME[c]}</span>`).join('')}${a[1].length?`<span class="oc-k">Also check</span>${a[1].map(c=>`<span class="oc-pill quiet">${OUTCOME[c]}</span>`).join('')}`:''}${RECUR[fid]?`<span class="oc-recurline">${RECUR[fid]}</span>`:''}</div>`;}

/* Outcome cards per site: the v6.9 assessment cards, relabelled and regrouped. steps: 2 done, 1 partly, 0 not yet. */
const OUT_CARDS={
 mini:{cards:[
  {c:'MG-2',st:'needs',note:'30 min of generator time avoidable in this hour',href:'dispatch',steps:[2,2,2,2,1],stepNote:'Trial under way · result pending',
   d:{aim:['The generator runs only when the battery cannot carry the load',true],drives:'The generator stop setting (90% charge), the battery reserve, fuel price, and the day’s load and sun.',found:[['Generator support review','finding'],['Fuel balance not complete yet','fuel']],fix:[['Trial a lower generator stop setting','recommendation']],done:[['Trial accepted · ACT-048','verification']],proven:'The trial is checked against generator time, service, reserve and stored energy. A cost comparison on the same basis follows once the check is complete.'}},
  {c:'MG-5',st:'unknown',note:'Power delivered is measured; what customers needed is not',href:'service',steps:[2,0,1,0,0],stepNote:'Watched during the generator trial',
   d:{aim:['No unmet demand at the clinic',true],drives:'Battery reserve, generator readiness, faults and weather.',found:[],fix:[['Raise the reserve for critical hours','service']],done:[],proven:'Checked as part of the generator trial, so a cost saving cannot come at the clinic’s expense.'}},
  {c:'MG-1',st:'unknown',note:'18–20 kW of solar spare on 3 of 5 days · sales not metered',href:'renewable',steps:[2,2,1,0,0],stepNote:'Opportunity found · not acted on yet',
   d:{aim:['At least 20 kWh a day of daytime solar sold to productive users',true],drives:'Spare daytime solar and battery room, demand from users, tariff and payment.',found:[['Productive-use headroom','opportunity-finding']],fix:[['Grain-mill what-if','opportunity-finding']],done:[],proven:'Not available yet: sales to productive users are not metered.'}},
  {c:'MG-4',st:'watch',note:'Battery below its 30% reserve on 5 of 30 days · generator service due soon',href:'asset-overview',steps:[0,2,1,0,0],stepNote:'Early warning · condition not checked',
   d:{aim:null,drives:'How deep and how often the battery discharges; generator starts and running hours.',found:[['Battery below reserve on 5 days, lowest 22%','asset-overview'],['Generator 500-hour service due (462 h now)','maintenance-preventive']],fix:[['Reserve and depth limits','foundation'],['Service on schedule','maintenance-preventive']],done:[],proven:'Battery condition and remaining life are not assessed. These are early warnings, not a condition check.'}},
  {c:'MG-7',st:'watch',note:'One battery report missing · 30 min unclassified',href:'evidence',steps:[0,2,2,1,0],stepNote:'Reporting fix open',
   d:{aim:null,drives:'Which readings arrive, and from which sources.',found:[['Battery output-limit report missing','evidence']],fix:[['Restore battery reporting','sitework']],done:[['ACT-049 · open','sitework']],proven:'Not yet.'}}],
  later:[['MG-3','MG-6'],'Needs site income, cost and billing records']},
 cold:{cards:[
  {c:'CC-1',st:'needs',note:'25–35 min above 4°C · peak 8.2°C',href:'temperature',steps:[2,2,1,1,0],stepNote:'Exposure found · stock impact unknown',
   d:{aim:['Chamber kept at 2–4°C',false],drives:'Temperature control, door use and backup readiness.',found:[['Temperature excursion','cold-finding-excursion'],['Backup response failed','cold-finding']],fix:[['Stock value what-if','cold-scenarios']],done:[['Stock and door log requested','cold-work']],proven:'Not available yet: which stock was in the room, and its value, is not recorded.'}},
  {c:'CC-6',st:'needs',note:'Automatic start failed · 3 repair visits without a result',href:'coldbackup',steps:[2,2,2,2,0],stepNote:'Repair done · start not proven',
   d:{aim:['Backup starts by itself on every grid loss',true],drives:'Backup readiness and maintenance response; grid reliability.',found:[['Backup response failed','cold-finding'],['Same generator visited 3 times in 60 days','cold-work-maintenance']],fix:[['Witnessed automatic-start test','cold-action']],done:[['Starter and control inspection completed','wr-overview']],proven:'The next automatic start is checked, with chamber temperature watched at the same time.'}},
  {c:'CC-5',st:'watch',note:'Recovered after power returned · start test overdue, coil cleaning due',href:'cooling',steps:[0,2,1,0,0],stepNote:'Early warning · condition not checked',
   d:{aim:null,drives:'Compressor cycling, servicing and backup starts.',found:[['Witnessed start test overdue since 2 Oct','maintenance-preventive'],['Coil cleaning due 15 Oct','maintenance-preventive']],fix:[['Service on schedule','maintenance-preventive']],done:[],proven:'Compressor condition is not assessed. These are early warnings, not a condition check.'}},
  {c:'CC-7',st:'watch',note:'Loading and door records not connected',href:'cold-evidence',steps:[0,2,0,0,0],stepNote:'Gap known',
   d:{aim:null,drives:'Probe coverage, calibration, and the operator’s records.',found:[['Loading and door records not connected','cold-evidence']],fix:[],done:[],proven:'Not yet.'}}],
  later:[['CC-2','CC-3','CC-4'],'Needs occupancy, cooling energy and sales records']},
 ev:{cards:[
  {c:'EV-1',st:'needs',note:'1 interrupted · 1 unknown of 12 sessions · connector 2 out 1 h',href:'sessions',steps:[2,2,2,1,0],stepNote:'Connector check open',
   d:{aim:['Every scheduled charge completes',true],drives:'Charger faults, shared site power and the departure schedule.',found:[['Charging session interrupted','ev-finding'],['Connector 2 out of service 1 h','availability']],fix:[['Investigate connector 2','ev-action']],done:[['ACT-061 · open','ev-action']],proven:'Connector 2 is checked over its next scheduled sessions. Which departures were affected is not known yet: buses and the roster are not linked.'}},
  {c:'EV-5',st:'ontrack',note:'Peak 76 kW of the 80 kW limit',href:'energy',meter:[76,80],steps:[2,2,0,0,0],stepNote:'Within the limit · little room left',
   d:{aim:['Stay under the 80 kW site import limit',false],drives:'Peak demand and how charging is scheduled.',found:[['Peak 76 kW at 10:40','energy']],fix:[['Load sharing between chargers','ev-sld']],done:[],proven:'Not needed while within the limit.'}},
  {c:'EV-3',st:'watch',note:'120 kWh in an 8-hour day · under a fifth of capacity',href:'energy',meter:[120,640],steps:[0,2,0,0,0],stepNote:'Opportunity seen',
   d:{aim:null,drives:'Spare connector time and other fleets’ demand.',found:[['Chargers mostly idle','energy']],fix:[],done:[],proven:'Not available yet: no demand from other fleets is recorded.'}},
  {c:'EV-4',st:'watch',note:'Fault on connector 2 · inspection overdue since 30 Sep',href:'ev-health',steps:[0,2,1,0,0],stepNote:'Early warning · condition not checked',
   d:{aim:null,drives:'Fault history and inspection.',found:[['Connector fault on 6 Oct','ev-health'],['Monthly connector inspection overdue','maintenance-preventive']],fix:[['Connector inspection','maintenance-preventive']],done:[],proven:'Charger condition is not assessed. These are early warnings, not a condition check.'}},
  {c:'EV-7',st:'watch',note:'One session end and 1 h of status missing',href:'ev-evidence',steps:[0,2,0,0,0],stepNote:'Gap known',
   d:{aim:null,drives:'Which reports arrive from the chargers and the site meter.',found:[['Status missing 15:00–16:00','ev-evidence']],fix:[],done:[],proven:'Not yet.'}}],
  later:[['EV-2','EV-6'],'Needs odometer readings and settlement records']}};

function stepBar(steps,note){return `<div class="oc-steps" role="img" aria-label="${steps.map((v,i)=>`${STEP_NAMES[i]}: ${v===2?'yes':v===1?'partly':'not yet'}`).join(', ')}">${steps.map((v,i)=>`<span class="s${v}" title="${STEP_NAMES[i]}"></span>`).join('')}</div><div class="oc-stepnote">${note}</div>`;}
function outcomeCard(d,x,i){
 return `<div class="oc-ocard tone-${TONE[x.st]}"><div class="oc-ocard-top"><span class="oc-oname">${OUTCOME[x.c]}</span><button class="oc-info" data-outcome="${d}:${i}" aria-label="How ${OUTCOME[x.c].toLowerCase()} is doing">i</button></div>
 <div class="oc-ostate">${STATE[x.st]}</div><p class="oc-onote">${x.note}</p>${x.meter?`<div class="oc-meter" aria-hidden="true"><span style="width:${Math.min(100,Math.round(x.meter[0]/x.meter[1]*100))}%"></span></div>`:''}${stepBar(x.steps,x.stepNote)}${link(x.href,'View detail →')}</div>`;}
function outcomeCards(d){const o=OUT_CARDS[d];
 return `<div class="oc-ocards">${o.cards.map((x,i)=>outcomeCard(d,x,i)).join('')}<div class="oc-ocard later"><span class="oc-oname">Not measured yet</span><p class="oc-onote">${o.later[0].map(c=>OUTCOME[c]).join(', ')}</p><p class="oc-onote muted">${o.later[1]}</p></div></div>`;}
function outcomeDrawer(d,i){const x=OUT_CARDS[d].cards[i],y=x.d,list=a=>a.length?a.map(([t,h])=>link(h,t)).join('<br>'):'<span class="muted">Nothing yet</span>';
 drawer(OUTCOME[x.c],status(`<span class="oc-chip tone-${TONE[x.st]}">${STATE[x.st]}</span>`,SITES[d].name)+stepBar(x.steps,x.stepNote)+
  kv([['What we aim for',y.aim?`${escapeHtml(y.aim[0])}${y.aim[1]?'<br><small class="muted">Set for this demonstration, not the customer’s own target</small>':''}`:'<span class="muted">No objective set yet</span>'],['What drives it',y.drives],['What we found',list(y.found)],['What can be done',list(y.fix)],['What has been done',list(y.done)],['Did it work',y.proven]]));}

/* Early warnings that have no Finding of their own and no price yet. lens: Cost | Risks | Opportunities */
const WARNINGS=[
 {d:'cold',c:'CC-6',lens:'Cost',kind:'risk',title:'Repeated maintenance without a result',seen:'Backup generator visited 3 times in 60 days (14 Aug, 18 Sep, 6 Oct); the automatic start still failed',href:'wr-overview',price:'A cost per visit is not set for this site'},
 {d:'mini',c:'MG-4',lens:'Risks',kind:'stress',title:'Battery below its reserve',seen:'5 of the last 30 days · lowest 22%',href:'asset-overview',price:'Needs a tested battery wear model'},
 {d:'cold',c:'CC-5',lens:'Risks',kind:'stress',title:'Backup start test overdue',seen:'Monthly test due 2 Oct, not done',href:'maintenance-preventive',price:'Needs repair cost and wear history'},
 {d:'ev',c:'EV-4',lens:'Risks',kind:'stress',title:'Charger fault and overdue inspection',seen:'Connector 2 fault on 6 Oct · inspection overdue since 30 Sep',href:'ev-health',price:'Needs repair cost and fault history'},
 {d:'ev',c:'EV-1',lens:'Risks',kind:'risk',title:'Connector 2 out of service',seen:'1 h out and 1 h unknown on 6 Oct',href:'availability',price:'Needs the bus roster'},
 {d:'ev',c:'EV-5',lens:'Risks',kind:'risk',title:'Peak close to the import limit',seen:'76 kW against 80 kW',href:'energy',price:'Needs a demand forecast'},
 {d:'mini',c:'MG-4',lens:'Risks',kind:'stress',title:'Generator service due soon',seen:'462 of 500 running hours',href:'maintenance-preventive',price:'Needs service cost'},
 {d:'ev',c:'EV-3',lens:'Opportunities',kind:'opp',title:'Chargers mostly idle',seen:'Under a fifth of daily capacity used',href:'energy',price:'Needs other fleets’ demand and a rate'}];
const KIND={risk:'Risk',stress:'Early warning',opp:'Opportunity'};
function warningList(filter,max){const rows=WARNINGS.filter(filter).slice(0,max||99);if(!rows.length)return '';
 return `<div class="oc-warn"><div class="oc-warn-head"><h3>Early warnings · not priced yet</h3><button class="oc-info" data-explain="warnings" aria-label="About early warnings">i</button></div><ul>${rows.map(x=>`<li><span class="oc-kind ${x.kind}">${KIND[x.kind]}</span><div>${link(x.href,x.title,'strong')}<small>${SITES[x.d].name.split(' ')[0]} · ${OUTCOME[x.c]} · ${x.seen}</small></div></li>`).join('')}</ul></div>`;}
function explainWarnings(){drawer('Early warnings',`<p class="prose">An early warning points at something that tends to cost money or shorten equipment life, before its cost can be worked out. It shows what was seen and how often. It never shows a money figure.</p>`+table(['Warning','What would put a value on it'],WARNINGS.map(x=>[x.title,x.price])));}

/* Portfolio outcome matrix (owner-approved outcome rows). */
const PF_ROWS=[['Revenue',{mini:'MG-1',cold:'CC-2',ev:'EV-3'}],['Operating cost',{mini:'MG-2',cold:'CC-3',ev:'EV-2'}],['Service and stock',{mini:'MG-5',cold:'CC-6',ev:'EV-1'}],['Asset life',{mini:'MG-4',cold:'CC-5',ev:'EV-4'}],['Return on assets',{mini:'MG-3',cold:'CC-2',ev:'EV-5'}],['Evidence',{mini:'MG-7',cold:'CC-7',ev:'EV-7'}]];
function cellState(d,c){const x=OUT_CARDS[d].cards.find(y=>y.c===c);return x?x.st:'notyet';}
function portfolioOutcomes(){const sites=['mini','cold','ev'];
 return `<div class="oc-matrix" role="table" aria-label="Outcomes across the estate"><div class="oc-mrow oc-mhead" role="row"><span role="columnheader"></span>${sites.map(d=>`<span role="columnheader">${link(SITES[d].overview,SITES[d].name.split(' ')[0])}</span>`).join('')}</div>${PF_ROWS.map(([name,m])=>`<div class="oc-mrow" role="row"><span role="rowheader" class="oc-orow">${name}</span>${sites.map(d=>{const st=cellState(d,m[d]);return `<span role="cell"><a class="oc-cell tone-${TONE[st]}" href="#/${SITES[d].overview}" title="${OUTCOME[m[d]]}"><b>${STATE[st]}</b><small>${OUTCOME[m[d]]}</small></a></span>`;}).join('')}</div>`).join('')}</div><div class="oc-key">${['needs','watch','ontrack','unknown','notyet'].map(k=>`<span><i class="tone-${TONE[k]}"></i>${STATE[k]}</span>`).join('')}</div>`;}

/* Reviewer-only: open owner decisions, shown as proposed defaults in this mock. */
function ownerDecisions(){drawer('Owner decisions shown with proposed defaults',`<p class="prose">These are open. The mock shows the architect’s proposed default for each so it can be judged in context.</p>`+table(['Decision','Proposed default in this mock','Where to see it'],[
 ['Build order','1 labels and links · 2 objectives and status · 3 early warnings · 4 cost check after the generator trial · 5 asset-life warnings · 6 first full check outside the mini-grid · 7 productive-use contribution','Portfolio and site overviews'],
 ['First full check outside the mini-grid','Cooling continuity at GreenHarvest (alternative: Depot charging interruptions)',`${link('cold','GreenHarvest overview')} · Cooling continuity card`],
 ['Which outcomes get an objective for the demo','Supply cost, productive sales, reliable service, cooling continuity, buses ready to run (the chamber range and import limit already exist)','Info button on each outcome card: “Set for this demonstration”'],
 ['Cost per maintenance visit','Added later as a site setting; until then the warning has no money value',`${link('wr-overview','WR-019')} · Findings › Cost`]]),true);}
document.addEventListener('click',e=>{const o=e.target.closest('[data-outcome]');if(o){const [d,i]=o.dataset.outcome.split(':');outcomeDrawer(d,Number(i));return;}
 if(e.target.closest('[data-explain="warnings"]')){explainWarnings();return;}
 if(e.target.closest('[data-owner-decisions]'))ownerDecisions();});
