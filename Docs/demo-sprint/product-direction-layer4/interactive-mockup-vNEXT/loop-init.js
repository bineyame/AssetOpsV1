/* ===== Layer 4 rev 4 mock-up · screen registration, change status, initial render ===== */
const V70IDS = new Set(SCREENS.map(s=>s.id));
const CHANGED = {
 portfolio:'Overview tab of the restructured Portfolio: outcomes computed from factors, the value chain strip, four outcome cards with their factors, factors needing attention, the look-alike contrast and first moves. Replaces the v7.0 Portfolio page (ranked Findings, count cards, objective matrix, Kobo-only opportunity, one depot’s tariff estimate).',
 sites:'Directory re-based on the selected demo operator: three sites with their outcome against target, the factor needing attention and the recommended move.',
 globalfinancials:'Becomes the operator’s economic statement: every site’s money factors against target with evidence classes, and portfolio ratios composed as Σ ÷ Σ.',
 mini:'Kept as the “Operating outcomes (earlier view)” sub-view of Kobo’s Overview; the site’s Overview tab now opens the factor structure.',cold:'Kept as the “Operating outcomes (earlier view)” sub-view of Thika’s Overview; names re-based.',ev:'Kept as the “Operating outcomes (earlier view)” sub-view of Ruiru’s Overview; names re-based.'};
function REG_STATUS(s){if(!V70IDS.has(s.id))return 'Added';if(ALIAS[s.id])return 'Merged';if(CHANGED[s.id]||preBody(s))return 'Changed';return 'Preserved';}
function REG_NOTE(s){const st=REG_STATUS(s);if(st==='Merged')return `Merged into ${ALIAS[s.id]} (site economics): what-ifs become decisions; assumptions are listed with their evidence class.`;
 if(CHANGED[s.id])return CHANGED[s.id];if(st==='Changed')return s.id==='opportunity-finding'||s.id==='renewable'?'Slim banner: spare solar without a customer is capacity, not opportunity value.':s.root==='Sites'?'Slim banner: these detailed views come from the earlier demo (2 connectors, 80 kW) and depot-wide figures are on the Ruiru overview.':s.id==='opportunity-finding'||s.id==='renewable'?'Slim banner: spare solar without a customer is capacity, not opportunity value.':'Slim banner: example items from the three demo operators shown together.';
 if(st==='Added')return s.question;return 'Unchanged apart from re-based display names where they occur.';}

const LOOPDOC = {anchor:'Layer 4 design rev 4 §6.2',models:['Factor structure (site × period)','Portfolio composition','Decision and options','Allocation run','Actions and rights'],
 preserved:'v7.0 shell, left menu, tab frame, drawer and accessibility patterns.',adapted:'Content re-based on the five mechanics: outcomes computed from declared factors; deviations seen at the factor where they arise.',deferred:'Live data, persistence and the v7.2 visual foundation (owner question).'};
function addL(id,title,root,section,question,render,extra={}){SCREENS.push({id,title,root,section,question,render,domain:'mini',loop:true,book:false,...LOOPDOC,...extra});}
function loopNotes(s){return `<div class="review-section"><strong>Layer 4 rev 4 · ${REG_STATUS(s)}</strong><p>${REG_NOTE(s)}</p><p style="margin-top:8px"><a href="../layer4-transformation-design.md" target="_blank">Design §6.2 ↗</a> · figures from the demo scenario file; see fixture-mapping.md.</p></div>`;}
const dyn = (o,k,f) => Object.defineProperty(o,k,{get:f,enumerable:true,configurable:true});

/* Portfolio: six owner-approved tabs */
const PQ = {portfolio:'Outcomes against target with the factors that make them, factors needing attention, and the first moves of the plan.','portfolio/act-first':'The issues needing a decision, each with who decides, and beside them the plan for November and December awaiting approval.','portfolio/outcomes-by-site':'Each outcome by site, broken down through its factors to target against actual; Protect measures against their targets.','portfolio/demand-and-capacity':'Demand that adds contribution, rejected demand with break-even, and capacity without a customer.','portfolio/what-changed':'Actions (each chosen option) with frozen predictions and three verdicts; contract rights and their states.','portfolio/scope':'Coverage by site and leaf factor, missing records, sources and the pilot request.'};
const PR = {portfolio:overviewScreen,'portfolio/act-first':actFirstScreen,'portfolio/outcomes-by-site':()=>outcomesBySiteScreen()+uxInsight(LS.op),'portfolio/demand-and-capacity':()=>uxChain(LS.op)+opportunityScreen(),'portfolio/what-changed':whatChangedScreen,'portfolio/scope':scopeScreen};
const portfolioCrumbs = s => [['Portfolio','portfolio'],...(s.id==='portfolio'?[]:[[PTABS.find(t=>t[1]===(s.ptab||s.id))[0],s.ptab&&s.ptab!==s.id?s.ptab:null]]),...(s.ptab&&s.ptab!==s.id?[[s.crumbLabel||'Pilot request']]:[])];
{const p=SCREENS.find(s=>s.id==='portfolio');Object.assign(p,{render:overviewScreen,loop:true,opScoped:true,ltabs:ptabs,crumbs:portfolioCrumbs,title:'Portfolio',question:PQ.portfolio,loopNotes,...LOOPDOC});dyn(p,'subtitle',()=>`${opName()} · ${OPN().typeWord} · October 2026, books closed 6 Nov`);}
PTABS.slice(1).forEach(([lab,id])=>{addL(id,'Portfolio','Portfolio','',PQ[id],PR[id],{opScoped:true,ltabs:ptabs,crumbs:portfolioCrumbs,loopNotes});dyn(SCREENS.at(-1),'subtitle',()=>`${opName()} · ${lab} · October 2026`);});
addL('portfolio/scope/pilot','A deep-dive and pilot on your data','Portfolio','','Deep-dive and pilot: minimum records, what you get, and the steps to a subscription.',pilotScreen,{opScoped:true,ptab:'portfolio/scope',ltabs:ptabs,crumbs:portfolioCrumbs,loopNotes});dyn(SCREENS.at(-1),'subtitle',()=>`${opName()} · minimum records and deliverables`);

addL('portfolio/act-first/plan','The plan for November and December','Portfolio','','The plan: its items and the Actions under each, with creator, owner, due date and release; the approval; items left out and why.',planScreen,{opScoped:true,ptab:'portfolio/act-first',crumbLabel:'The plan',ltabs:ptabs,crumbs:portfolioCrumbs,loopNotes});dyn(SCREENS.at(-1),'subtitle',()=>`${opName()} · version ${uxPlanState(LS.op).version}, ${STATE_WORD[uxPlanState(LS.op).state].toLowerCase()}`);

/* Sites directory and Financials root, re-based on the operator */
/* one shell model (UX audit C1.4): Findings and Actions read the plan's store, scoped to the operator; one page, no sub-tabs */
{const f=SCREENS.find(x=>x.id==='findings');Object.assign(f,{render:uxFindingsScreen,loop:true,opScoped:true,ltabs:()=>'',crumbs:()=>[['Findings']],question:'What is wrong at our Sites, and what is being done about each?',loopNotes});dyn(f,'subtitle',()=>`${opName()} · October 2026`);}
{const a=SCREENS.find(x=>x.id==='actions');Object.assign(a,{render:uxActionsScreen,loop:true,opScoped:true,ltabs:()=>'',crumbs:()=>[['Actions']],question:'What has been set in motion under the plan, by whom, and is it released?',loopNotes});dyn(a,'subtitle',()=>`${opName()} · the plan for November and December`);}
addL('not-found','Page not found','','','',uxNotFound,{opScoped:true,noFigures:true,ltabs:()=>'',crumbs:()=>[['Portfolio','portfolio'],['Page not found']],loopNotes});
{const s=SCREENS.find(x=>x.id==='sites');Object.assign(s,{render:sitesScreen,opScoped:true,loopNotes,question:'The operator’s sites: outcome against target, factor needing attention, recommended move.'});dyn(s,'subtitle',()=>`${opName()} · October 2026`);}
{const s=SCREENS.find(x=>x.id==='globalfinancials');Object.assign(s,{render:financialsScreen,loop:true,opScoped:true,loopNotes,title:'Financials',crumbs:()=>[['Financials']],question:'Economic statement: every site’s money factors against target.'});dyn(s,'subtitle',()=>`${opName()} · economic statement · October 2026`);}
['mini','cold','ev'].forEach(d=>{const s=SCREENS.find(x=>x.id===d),sk=V70SITE[d];s.ltabs=()=>siteTabRow(sk,'Overview')+tabRow([['Economics and decisions',`site/${sk}`],['Operating outcomes (earlier view)',d]],d,true);s.loopNotes=loopNotes;});

/* Sites: overview, economics and deep-view placeholders for all nine */
Object.keys(SK).forEach(sk=>{const st=SK[sk],op=st.op,sub=()=>`${st.type} · ${OPS[op].name} · October 2026`;
 const crumbs=s=>[['Sites','sites'],...(s.siteTab==='Overview'?[[st.name]]:[[st.name,`site/${sk}`],[s.siteTab]])];
 addL(`site/${sk}`,st.name,'Sites','Overview',`${st.name}: outcomes with their factor structure, Protect measures, attention, decisions, obligations and rights.`,()=>siteOverview(sk),{site:sk,siteTab:'Overview',ltabs:()=>siteTabs(sk,'Overview'),crumbs,loopNotes,subtitle:sub()});
 addL(`site/${sk}/economics`,st.name,'Sites','Financials',`${st.name} economics: every factor against target, prices and models used.`,()=>siteEconomics(sk),{site:sk,siteTab:'Financials',ltabs:()=>siteTabRow(sk,'Financials'),crumbs,loopNotes,subtitle:sub()});
 if(!st.v70)['Foundation','Health','Performance','Findings','Work','Evidence'].forEach(tab=>addL(`site/${sk}/${tab.toLowerCase()}`,st.name,'Sites',tab,`${tab} views for ${st.name} (not built in this mock-up).`,()=>deepPlaceholder(sk,tab),{site:sk,siteTab:tab,stub:true,ltabs:()=>siteTabRow(sk,tab),crumbs,loopNotes,subtitle:sub()}));});

/* Decisions: drill-down pages, not a menu */
DEC.forEach(d=>addL(`decision/${d.id}`,d.q,'Portfolio','Decision',d.q,()=>decisionScreen(d.id),{site:d.site,h1:()=>['choose','none'].includes(uxDecState(d.id).key)?uxDecQuestion(d):d.q, /* UX audit C17: a question only while a choice is waiting */ltabs:()=>'',crumbs:()=>[['Portfolio','portfolio'],['Act first','portfolio/act-first'],[SK[d.site].name,`site/${d.site}`],['Decision']],loopNotes,
 subtitle:`${SK[d.site].name} · ${OPS[SK[d.site].op].name} · options ${BASIS_WORDS[decBasis(d)]?`compared ${BASIS_WORDS[decBasis(d)]}`:'compared, not valued in money'}`,actions:()=>btn(`site/${d.site}`,'Open site')}));

window.mockupManifest = SCREENS.map(({render,ltabs,crumbs,actions,loopNotes:_l,...meta})=>({...meta,title:typeof meta.title==='string'?meta.title:'',layer4_status:REG_STATUS({...meta}),layer4_note:REG_NOTE({...meta})}));
render();
