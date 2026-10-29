/* v7.0: site and estate cards organised by business outcome (commercial capability architecture rev 5, figure 3.1).
   Each outcome card wires existing v6.9 content: state, contributors, issues, what can be done, what is in hand,
   earlier interventions and evidence. Same illustrative records; nothing here is a new analytic. */
const OUTCOME={
 'MG-1':'Productive electricity sales','MG-2':'Supply cost per kWh','MG-3':'Site profitability','MG-4':'Battery and generator life','MG-5':'Reliable service','MG-6':'Cash collected','MG-7':'Evidence quality',
 'EV-1':'Buses ready to run','EV-2':'Energy cost per km','EV-3':'Charger use','EV-4':'Charger life','EV-5':'Room before expansion','EV-6':'Energy billed against metered','EV-7':'Evidence quality',
 'CC-1':'Stock kept saleable','CC-2':'Paid cold-room use','CC-3':'Cost per cooling unit','CC-4':'Market value of produce','CC-5':'Compressor life','CC-6':'Cooling continuity','CC-7':'Evidence quality'};
const TONE={needs:'amber',watch:'blue',unknown:'gray',notyet:'none',ontrack:'green',opp:'green'};
const STATE={needs:'Needs attention',watch:'Watch',unknown:'Unknown',notyet:'Not measured yet',ontrack:'On track',opp:'Opportunity'};
/* The four outcome categories (owner decision, 29 Oct 2026): name and one-line definition. */
const OUTCOMES=[
 ['grow','Grow revenue','Capture more value from existing infrastructure and expand earning potential'],
 ['cost','Optimize cost and efficiency','Eliminate avoidable expenditure and get more output from operational resources'],
 ['protect','Protect asset and capital','Preserve asset value, avoid premature replacement and reduce service disruption'],
 ['assure','Assure performance and returns','Establish with defensible evidence whether the infrastructure is delivering expected results']];
const CATN=Object.fromEntries(OUTCOMES.map(([k,n])=>[k,n]));
/* Which category each site-level outcome belongs to. */
const CAT_OF={'MG-1':'grow','MG-3':'grow','MG-6':'grow','MG-2':'cost','MG-4':'protect','MG-5':'protect','MG-7':'assure',
 'EV-3':'grow','EV-6':'grow','EV-2':'cost','EV-1':'protect','EV-4':'protect','EV-5':'protect','EV-7':'assure',
 'CC-2':'grow','CC-4':'grow','CC-3':'cost','CC-1':'protect','CC-5':'protect','CC-6':'protect','CC-7':'assure'};

/* What each Finding affects, in plain words (used in Findings lists and Portfolio rows). */
const AFFECTS={'F-104':[['MG-2'],['MG-5','MG-4']],'F-108':[['MG-7'],['MG-2']],'F-109':[['MG-1'],['MG-2','MG-5']],'F-118':[['CC-6','CC-1'],['CC-5']],'F-119':[['CC-1'],[]],'F-130':[['EV-1'],['EV-4']],
 'ACT-048':[['MG-2'],['MG-5','MG-4']]};
const RECUR={'F-104':'Seen on 24 of the last 30 days','F-118':'3 grid losses in 30 days · backup started by itself on 2','F-109':'Spare on 3 of 5 well-observed days','F-130':'Connector 2 status also unknown on 15 Sep'};
/* Group site-level outcomes by category, keeping their plain names: [[cat,[names]]]. */
function byCat(codes){const g=[];codes.forEach(c=>{const k=CAT_OF[c];let e=g.find(x=>x[0]===k);if(!e)g.push(e=[k,[]]);e[1].push(OUTCOME[c].toLowerCase());});return g;}
const affectsPill=fid=>AFFECTS[fid]?`<span class="oc-affects">${byCat(AFFECTS[fid][0]).map(([k])=>CATN[k]).join(' · ')}</span>`:'';
const recurNote=fid=>RECUR[fid]?`<small class="oc-recur">${RECUR[fid]}</small>`:'';
const catPills=(codes,quiet)=>byCat(codes).map(([k,ns])=>`<span class="oc-pill${quiet?' quiet':''}">${CATN[k]}<small>${ns.join(', ')}</small></span>`).join('');
function affectsLine(fid){const a=AFFECTS[fid];if(!a)return '';const act=fid.startsWith('ACT');
 return `<div class="oc-affectsline"><span class="oc-k">Affects</span>${catPills(a[0])}${a[1].length?`<span class="oc-k">${act?'Safeguards checked':'Also check'}</span>${catPills(a[1],true)}`:''}${RECUR[fid]?`<span class="oc-recurline">${RECUR[fid]}</span>`:''}</div>`;}

/* Outcome category icons: simple 24-unit line icons, same stroke as the product icon set, each with its own label. */
const OC_ICONS={
 grow:['Rising trend','M3 17l6-6 4 4 7-7 M14 8h6v6'],
 cost:['Efficiency gauge','M3.5 17a8.5 8.5 0 0 1 17 0 M12 17l4-5.5 M7 17h.01 M17 17h.01 M12 8.5v1.5'],
 protect:['Shield','M12 3l7.5 3v5.5c0 4.6-3.2 8.2-7.5 9.5-4.3-1.3-7.5-4.9-7.5-9.5V6z'],
 assure:['Verified report','M6 3h8.5L19 7.5V21H6z M14 3v5h5 M9 14.5l2 2 4-4.5'],
 drives:['Drivers','M4 7h9 M17 7h3 M4 17h3 M11 17h9 M15 5v4 M9 15v4'],
 issues:['Issues','M12 4L3 20h18z M12 10v4 M12 17h.01'],
 can:['Options','M9 18h6 M10 21h4 M12 3a6 6 0 0 0-3.8 10.6c.7.6.8 1.4.8 2.4h6c0-1 .1-1.8.8-2.4A6 6 0 0 0 12 3z'],
 hand:['In hand','M8 4h11v17H5V4h3 M9 2h6v4H9z M8.5 13l2.5 2.5 4.5-5'],
 prev:['Earlier','M12 4a8 8 0 1 1-7.4 5 M4 4v5h5 M12 8v4.5l3 1.5'],
 guard:['Safeguard','M12 3l7.5 3v5.5c0 4.6-3.2 8.2-7.5 9.5-4.3-1.3-7.5-4.9-7.5-9.5V6z M9 12l2 2 4-4']};
const ocIcon=(k,label,cls='')=>`<svg class="oc-ic ${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" role="img" aria-label="${label||OC_ICONS[k][0]}"><title>${label||OC_ICONS[k][0]}</title><path d="${OC_ICONS[k][1]}"/></svg>`;
const catIcon=k=>ocIcon(k,CATN[k],'oc-cat oc-cat-'+k);
const colIcon=k=>`<svg class="oc-ic oc-colic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${OC_ICONS[k][1]}"/></svg>`;

/* Site outcome boards, one row per category. Contributors: [name, what we see, confidence (CONF key or word), link].
   Issues: [kind, text, link]. kind: finding | risk | opp | warn. Lists of [text, link, note].
   guard: [text, link] names the outcomes a lever in this row must not harm; they are shown, never netted. */
const NAY='Not available yet';
const BOARD={
 mini:{
  grow:{st:'opp',lead:'MG-1',head:'18–20 kW of daytime solar unused',sub:'Sales to productive users are not metered, so revenue itself is not measured yet',
   contrib:[['Productive use','Spare solar on 3 of 5 well-observed days','f109','renewable'],['Cash collected',`${NAY} · no billing or payment records`,null,null],['Site earnings',`${NAY} · needs site income, operating cost and capital records`,null,null]],
   issues:[['opp','F-109 · Productive-use headroom','opportunity-finding']],
   can:[['Grain-mill what-if · $2.50 gross per eligible window','opportunity-finding'],['Site what-ifs','scenarios']],hand:[],prev:null,ev:['Renewable evidence','renewable']},
  cost:{st:'needs',lead:'MG-2',head:()=>`${money()} exposure in this hour`,sub:'Generator ran 30 minutes longer than the load needed · seen on 24 of the last 30 days',
   guard:['Reliable service and battery life are checked as safeguards in the generator trial; a fuel saving that harms them does not count','verification'],
   contrib:[['Generator use','30 min avoidable, 30 min unclear','f104','dispatch'],['Fuel','No complete fuel balance yet','Unknown','fuel'],['Fuel price','Declared at $1.20 per litre','Declared','assumptions']],
   issues:[['finding','F-104 · Generator support review','finding'],['finding','F-108 · Battery report missing limits this conclusion','evidence']],
   can:[['Trial a lower generator stop setting','recommendation'],['Proposed setting change CHG-019','changes']],
   hand:[['ACT-048 · Generator stop trial','verification',()=>stage.accepted?'Awaiting verification':'Plan ready']],
   prev:[['No earlier change has been checked at this site','',null]],ev:['Dispatch evidence','dispatch']},
  protect:{st:'watch',lead:'MG-4',head:'2 early warnings on battery and generator',sub:'Battery and generator condition is not assessed; these are early warnings only. Power was delivered, but what customers needed is not measured',
   contrib:[['Battery','Below its 30% reserve on 5 of 30 days · lowest 22%','Limited','asset-overview'],['Generator','462 of 500 running hours since service','Plan record','maintenance-preventive'],['Service delivery','Delivered load measured; demand not','Unknown','service'],['Backup readiness','No backup event in this window','Unknown','backup']],
   issues:[['warn','Battery below its reserve','asset-overview'],['warn','Generator service due soon','maintenance-preventive']],
   can:[['Battery capacity test PM-0447','maintenance-preventive']],hand:[['PM-0441 · 500-hour service','maintenance-preventive','Due soon'],['PM-0447 · Capacity test','asset-work','Scheduled 1 Nov']],
   prev:[['Service and reserve checked as safeguards in the generator trial','verification','Pending']],ev:['Battery evidence','asset-evidence']},
  assure:{st:'watch',lead:'MG-7',head:'No verified result yet · confidence low for this hour',sub:'One battery report is missing, so 30 minutes stay unclassified',
   contrib:[['Verified results','Generator trial ACT-048 not yet verified','Pending','verification'],['Actual against plan',`${NAY} · no target declared for this site`,null,null],['Readings','Generated test data source · 92% of expected readings','Limited','evidence'],['Battery reporting','14:50 output-limit report missing','High','evidence']],
   issues:[['finding','F-108 · Battery output-limit report missing','evidence']],can:[['Restore battery reporting','sitework']],hand:[['ACT-049 · Restore reporting','sitework','Open']],prev:null,ev:['Evidence overview','evidence']}},
 cold:{
  grow:{st:'notyet',lead:'CC-2',sub:'Needs occupancy, storage contract, income and sales records'},
  cost:{st:'needs',lead:'CC-3',head:'3 repair visits in 60 days without a result',sub:'None of the visits fixed the backup generator’s automatic start; repair cost is not recorded',
   guard:['Cooling continuity: a repair counts only when the backup then starts by itself','cold-recommendation'],
   contrib:[['Maintenance effectiveness','3 visits (14 Aug, 18 Sep, 6 Oct); automatic start still failed','High','wr-overview'],['Repair and call-out','No cost on work record WR-019','Unknown','cold-financials'],['Cooling energy',`${NAY} · no cooling energy meter`,null,null]],
   issues:[['warn','Repeated maintenance without a result','wr-overview']],can:[['Witnessed automatic-start test','cold-recommendation']],hand:[['WR-019 · Starter and control inspection','wr-overview','Completed']],
   prev:[['WR-011 · Starter battery replaced, 14 Aug','maintenance','Did not fix it'],['WR-016 · Control relay reset, 18 Sep','maintenance','Did not fix it']],ev:['Financial bridge','cold-financials']},
  protect:{st:'needs',lead:'CC-1',head:'Chamber above 4°C for 25–35 min',sub:'Backup did not start by itself; cooling stopped until it was started by hand. Compressor and backup condition are not assessed',
   contrib:[['Chamber temperature','Peak 8.2°C against a 4°C limit','High','temperature'],['Backup start','Automatic start failed; started by hand','High','coldbackup'],['Cooling recovery','Restarted with power; comparison incomplete','Medium','cooling'],['Backup generator','Monthly start test overdue since 2 Oct · warranty expired','Plan record','maintenance-preventive'],['Compressor','Coil cleaning due 15 Oct','Plan record','maintenance-preventive']],
   issues:[['finding','F-118 · Backup response failed','cold-finding'],['finding','F-119 · Temperature excursion','cold-finding-excursion'],['warn','Backup start test overdue','maintenance-preventive']],
   can:[['Witnessed automatic-start test','cold-recommendation'],['Stock value what-if','cold-scenarios']],
   hand:[['ACT-051 · Witness automatic-start test','cold-action','Open'],['INC-203 · Backup failure and excursion','incident','Investigating'],['PM-0455 · Witnessed start test','maintenance-preventive','Overdue'],['PM-0450 · Coil cleaning','maintenance-preventive','Due soon']],
   prev:[['WR-019 · Inspection completed','workverification','Not yet verified']],ev:['Cold-room evidence','cold-evidence']},
  assure:{st:'watch',lead:'CC-7',head:'Event fully reconstructed · no verified result yet',sub:'Loading and door records are not connected, so stock impact cannot be judged',
   contrib:[['Verified results','WR-019 completed; not yet verified','Pending','workverification'],['Storage service level',`${NAY} · no storage contract recorded`,null,null],['Power, backup and cooling chain','Every step recorded','High','cold-evidence'],['Loading and door records',NAY,null,null]],
   issues:[],can:[['Record stock and door log','cold-work']],hand:[],prev:null,ev:['Evidence overview','cold-evidence']}},
 ev:{
  grow:{st:'watch',lead:'EV-3',head:'$36.00 gross tariff estimate',sub:'120 kWh delivered in complete sessions; chargers used under a fifth of capacity',
   contrib:[['Charging delivered','120 kWh in 10 complete sessions','f130','energy'],['Charger use','Under a fifth of daily capacity','Medium','energy'],['Energy billed against metered',`${NAY} · no settlement records`,null,null]],
   issues:[['opp','Chargers mostly idle','energy'],['finding','F-130 · Interrupted session · lost revenue unknown','ev-finding']],
   can:[['Charging what-ifs','ev-scenarios']],hand:[],prev:null,ev:['Financial bridge','ev-financials']},
  cost:{st:'notyet',lead:'EV-2',sub:'Energy cost per km needs odometer readings; a tariff estimate exists in Financials'},
  protect:{st:'needs',lead:'EV-1',head:'1 interrupted · 1 unknown of 12 sessions',sub:'Connector 2 was out of service for 1 hour; which departures were affected is not known yet. Charger condition is not assessed',
   contrib:[['Session service','1 fault-aborted session, 1 outcome unknown','f130','sessions'],['Connector availability','Connector 2: 1 h out, 1 h unknown','Medium','availability'],['Connector 2 charger','Fault on 6 Oct · inspection overdue since 30 Sep','Medium','ev-health'],['Site power','Peak 76 kW of the 80 kW import limit','High','energy'],['Warranty','Claimable until Aug 2028','Record','assets-warranty']],
   issues:[['finding','F-130 · Charging session interrupted','ev-finding'],['risk','Connector 2 out of service','availability'],['warn','Charger fault and overdue inspection','ev-health'],['risk','Peak close to the import limit','energy']],
   can:[['Investigate connector 2','ev-recommendation'],['Claim under warranty or repair','assets-warranty']],
   hand:[['ACT-061 · Investigate connector 2','ev-action','Open'],['WR-021 · Connector 2 repair','maintenance','Waiting for diagnostics'],['PM-0452 · Connector inspection','maintenance-preventive','Overdue']],
   prev:[['No earlier repair on this connector','',null]],ev:['Depot evidence','ev-evidence']},
  assure:{st:'watch',lead:'EV-7',head:'Evidence limited · no verified result yet',sub:'One session end and 1 hour of connector status are missing',
   contrib:[['Departures against the timetable',`${NAY} · no bus roster connected`,null,null],['Session records','1 session has no accepted end','Medium','ev-evidence'],['Connector status','Missing 15:00–16:00','Medium','ev-evidence']],
   issues:[],can:[],hand:[],prev:null,ev:['Evidence overview','ev-evidence']}}};

const val=v=>typeof v==='function'?v():v;
function confTag(c){if(!c)return '';if(CONF[c])return conf(c,'');return `<span class="oc-conf">${c}</span>`;}
function ocList(items,empty){return items&&items.length?`<ul class="ob-list">${items.map(([t,h,n])=>`<li>${h?link(h,t):t}${n?` <span class="oc-state">${val(n)}</span>`:''}</li>`).join('')}</ul>`:`<p class="ob-none">${empty}</p>`;}
const ISSUE_KIND={finding:['Finding','finding'],risk:['Risk','risk'],opp:['Opportunity','opp'],warn:['Early warning','stress']};
function issueList(items){return items.length?`<ul class="ob-list">${items.map(([k,t,h])=>`<li><span class="oc-kind ${ISSUE_KIND[k][1]}">${ISSUE_KIND[k][0]}</span> ${link(h,t)}</li>`).join('')}</ul>`:'<p class="ob-none">None open</p>';}
function obCol(ic,title,body){return `<div class="ob-col"><h4>${colIcon(ic)}${title}</h4>${body}</div>`;}
function obName(key,name,def){return `${catIcon(key)}<span class="ob-name">${name}<small>${def}</small></span>`;}
function outcomeRow(d,key,name,def){const x=BOARD[d][key],tone=TONE[x.st];
 if(x.st==='notyet')return `<div class="ob ob-later"><div class="ob-sum">${obName(key,name,def)}<span class="oc-chip tone-none">Not measured yet</span><span class="ob-head muted">${x.sub}</span></div></div>`;
 const n=x.issues.length,h=x.hand.length;
 return `<details class="ob tone-${tone}" ${x.st==='needs'?'open':''}><summary class="ob-sum">${obName(key,name,def)}<span class="oc-chip tone-${tone}">${STATE[x.st]}</span><span class="ob-head">${val(x.head)}</span><span class="ob-counts">${n?`${n} issue${n>1?'s':''}`:'No open issues'}${h?` · ${h} in hand`:''}</span></summary>
 <div class="ob-body"><p class="ob-sub">${x.sub}</p>${x.guard?`<p class="ob-guard">${colIcon('guard')}<span><b>Must not harm</b> ${link(x.guard[1],x.guard[0])}</span></p>`:''}
 <div class="ob-grid">${obCol('drives','What drives it',`<ul class="ob-list ob-contrib">${x.contrib.map(([nm,t,c,hr])=>`<li><div><b>${hr?link(hr,nm):nm}</b><small>${t}</small></div>${confTag(c)}</li>`).join('')}</ul>`)}
 ${obCol('issues','Issues',issueList(x.issues))}${obCol('can','What can be done',ocList(x.can,'Nothing proposed yet'))}${obCol('hand','Already in hand',ocList(x.hand,'No open action or work'))}${obCol('prev','Earlier interventions',x.prev?ocList(x.prev,''):`<p class="ob-none">${NAY}</p>`)}</div>
 <div class="ob-foot">${link(x.ev[1],`${x.ev[0]} →`)}</div></div></details>`;}
function outcomeBoard(d){return `<section class="ob-board" aria-label="Outcomes at this site"><div class="ob-board-head"><h2>How this site is doing</h2><button class="oc-info" data-explain="board" aria-label="About this view">i</button></div>${OUTCOMES.map(([k,n,def])=>outcomeRow(d,k,n,def)).join('')}</section>`;}
function explainBoard(){drawer('How this site is doing',`<p class="prose">Each row is one of the four things the business is trying to achieve. It shows how it is doing, what is driving that, the problems and opportunities found, what could be done, what is already under way, and whether earlier work fixed anything. Every item opens the page that holds its detail.</p>`+table(['Outcome','What it means'],OUTCOMES.map(([k,n,def])=>[`<span class="oc-dname">${catIcon(k)}${n}</span>`,def]))+`<p class="prose" style="margin-top:10px">Money of different kinds is shown separately and never added together. Where a fix in one row could harm another, the row says what it must not harm.</p><p class="prose" style="margin-top:10px">Confidence says how complete and consistent the readings are. “Not measured yet” means the records needed to judge it are not connected.</p>`);}

/* Early warnings without a Finding of their own and no price yet. c is the site-level outcome the warning bears on. */
const WARNINGS=[
 {d:'cold',c:'CC-3',lens:'Cost',kind:'risk',title:'Repeated maintenance without a result',seen:'Backup generator visited 3 times in 60 days (14 Aug, 18 Sep, 6 Oct); the automatic start still failed',href:'wr-overview',price:'A cost per visit is not set for this site'},
 {d:'mini',c:'MG-4',lens:'Risks',kind:'stress',title:'Battery below its reserve',seen:'5 of the last 30 days · lowest 22%',href:'asset-overview',price:'Needs a tested battery wear model'},
 {d:'cold',c:'CC-5',lens:'Risks',kind:'stress',title:'Backup start test overdue',seen:'Monthly test due 2 Oct, not done',href:'maintenance-preventive',price:'Needs repair cost and wear history'},
 {d:'ev',c:'EV-4',lens:'Risks',kind:'stress',title:'Charger fault and overdue inspection',seen:'Connector 2 fault on 6 Oct · inspection overdue since 30 Sep',href:'ev-health',price:'Needs repair cost and fault history'},
 {d:'ev',c:'EV-1',lens:'Risks',kind:'risk',title:'Connector 2 out of service',seen:'1 h out and 1 h unknown on 6 Oct',href:'availability',price:'Needs the bus roster'},
 {d:'ev',c:'EV-5',lens:'Risks',kind:'risk',title:'Peak close to the import limit',seen:'76 kW against 80 kW',href:'energy',price:'Needs a demand forecast'},
 {d:'mini',c:'MG-4',lens:'Risks',kind:'stress',title:'Generator service due soon',seen:'462 of 500 running hours',href:'maintenance-preventive',price:'Needs service cost'},
 {d:'ev',c:'EV-3',lens:'Opportunities',kind:'opp',title:'Chargers mostly idle',seen:'Under a fifth of daily capacity used',href:'energy',price:'Needs other fleets’ demand and a rate'}];
const KIND={risk:'Risk',stress:'Early warning',opp:'Opportunity'};
function warningList(filter,max){const rows=WARNINGS.filter(filter).slice(0,max||99);if(!rows.length)return '';
 return `<div class="oc-warn"><div class="oc-warn-head"><h3>Early warnings · not priced yet</h3><button class="oc-info" data-explain="warnings" aria-label="About early warnings">i</button></div><ul>${rows.map(x=>`<li><span class="oc-kind ${x.kind}">${KIND[x.kind]}</span><div>${link(x.href,x.title,'strong')}<small>${SITES[x.d].name.split(' ')[0]} · ${CATN[CAT_OF[x.c]]} · ${x.seen}</small></div></li>`).join('')}</ul></div>`;}
function explainWarnings(){drawer('Early warnings',`<p class="prose">An early warning points at something that tends to cost money or shorten equipment life, before its cost can be worked out. It shows what was seen and how often. It never shows a money figure.</p>`+table(['Warning','Outcome','What would put a value on it'],WARNINGS.map(x=>[x.title,CATN[CAT_OF[x.c]],x.price])));}

/* Portfolio: four outcome cards (replacing the five value cards) and the outcome matrix. */
const PF_SITE_NAME={mini:'Kobo',cold:'GreenHarvest',ev:'Depot'};
function pfCard(k,name,def){const sites=['mini','cold','ev'],st=sites.map(d=>BOARD[d][k].st);
 const stress=WARNINGS.filter(x=>CAT_OF[x.c]==='protect'&&x.kind==='stress').length;
 const cfg={
  grow:{tone:'green',value:'18–20 <small>kW unused</small>',detail:'Productive use at Kobo · idle chargers at Depot · site income not recorded',basis:'Opportunities · revenue not measured yet',to:'renewable'},
  cost:{tone:'amber',value:money(),detail:'Kobo generator time, 1 trial in hand · 3 repair visits without a result at GreenHarvest, cost not recorded',basis:'Modelled + scenario · one-hour window · reliability checked as a safeguard',to:'financials'},
  protect:{tone:'red',value:`2 <small>sites disrupted</small>`,detail:`Cold-room exposure · interrupted charging · ${stress} early warnings on battery, generator, charger and backup · Depot peak at 95% of its limit`,basis:'Measured events and early warnings, counted separately · loss not priced',to:'findings-risks'},
  assure:{tone:'neutral',value:'Not established',detail:'No verified result yet · no targets declared · evidence gaps at all 3 sites',basis:'Completed work does not establish savings',to:'globalevidence'}}[k];
 return `<a class="value-card ${cfg.tone} oc-pfcard" href="#/${cfg.to}"><div class="value-label">${catIcon(k)}<span>${name}</span>${icon('arrow')}</div><p class="oc-pfdef">${def}</p><div class="value-number">${cfg.value}</div><p>${cfg.detail}</p><div class="oc-sitedots">${sites.map((d,i)=>`<span class="tone-${TONE[st[i]]}" title="${PF_SITE_NAME[d]}: ${STATE[st[i]]}"><i></i>${PF_SITE_NAME[d]}</span>`).join('')}</div><div class="value-basis">${cfg.basis}</div></a>`;}
function portfolioOutcomeCards(){return `<div class="value-grid oc-pfgrid">${OUTCOMES.map(([k,n,def])=>pfCard(k,n,def)).join('')}</div>`;}
function portfolioOutcomes(){const sites=['mini','cold','ev'];
 return `<div class="oc-matrix" role="table" aria-label="Outcomes across the estate"><div class="oc-mrow oc-mhead" role="row"><span role="columnheader"></span>${sites.map(d=>`<span role="columnheader">${link(SITES[d].overview,PF_SITE_NAME[d])}</span>`).join('')}</div>${OUTCOMES.map(([k,name,def])=>`<div class="oc-mrow" role="row"><span role="rowheader" class="oc-orow" title="${def}">${catIcon(k)}<span>${name}</span></span>${sites.map(d=>{const x=BOARD[d][k],st=x.st;return `<span role="cell"><a class="oc-cell tone-${TONE[st]}" href="#/${SITES[d].overview}" title="${PF_SITE_NAME[d]} · ${name}: ${OUTCOME[x.lead]}"><b>${STATE[st]}</b><small>${OUTCOME[x.lead]}</small></a></span>`;}).join('')}</div>`).join('')}</div><div class="oc-key">${['needs','watch','opp','ontrack','unknown','notyet'].map(k=>`<span><i class="tone-${TONE[k]}"></i>${STATE[k]}</span>`).join('')}</div>`;}

/* Reviewer-only: open owner decisions, shown as proposed defaults in this mock. */
function ownerDecisions(){drawer('Owner decisions shown with proposed defaults',`<p class="prose">These are open. The mock shows the architect’s proposed default for each so it can be judged in context.</p>`+table(['Decision','Proposed default in this mock','Where to see it'],[
 ['Build order','1 labels and links · 2 objectives and status · 3 early warnings · 4 cost check after the generator trial · 5 asset-life warnings · 6 first full check outside the mini-grid · 7 productive-use contribution','Portfolio and site overviews'],
 ['First full check outside the mini-grid','Cooling continuity at GreenHarvest (alternative: Depot charging interruptions)',`${link('cold','GreenHarvest overview')} · Protect asset and capital`],
 ['Which outcomes get an objective for the demo','Supply cost, productive sales, reliable service, cooling continuity, buses ready to run (the chamber range and import limit already exist)','Site overviews'],
 ['Cost per maintenance visit','Added later as a site setting; until then the warning has no money value',`${link('cold','GreenHarvest overview')} · Optimize cost and efficiency`]]),true);}
document.addEventListener('click',e=>{
 if(e.target.closest('[data-explain="warnings"]')){explainWarnings();return;}
 if(e.target.closest('[data-explain="board"]')){explainBoard();return;}
 if(e.target.closest('[data-owner-decisions]'))ownerDecisions();});
