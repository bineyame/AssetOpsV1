/* ===== Layer 4 rev 4 mock-up · options, rights and decisions =====
   An option changes one or more factors; the counterfactual outcome is the same structure evaluated with the
   changed factors, against no action, on the same horizon, prices and contracts (main design §2.3). */
const OPT_LABEL = {
 'KOB-NOACT':'Keep the current generator settings','KOB-RESERVE':'Lower the battery reserve from 30% to 25%','KOB-STOPSOC':'Stop the generator at 70% battery instead of 90%','KOB-BATT100':'Buy 100 kWh more battery storage',
 'BAT-CLAIM-NOW':'Claim the battery warranty now','BAT-EVIDENCE':'Gather the evidence first: capacity test and temperature sensor','BAT-NOACT':'Do nothing for now',
 'KIS-REPAIR':'Repair generator 1 (alternator)','KIS-REPLACE':'Replace generator 1','KIS-BATT60':'Buy battery storage to cut generator hours','KIS-NOACT':'Do nothing: run every evening on one generator',
 'KIS-OM-REVIEW':'Send the response-time record for review, then request the credit if confirmed','KIS-OM-NOACT':'Do nothing: do not raise the late response',
 'MTO-HULLER':'Connect the cooperative’s rice huller (daytime)','MTO-WELDING':'Connect the evening welding workshop','MTO-DEMAND-NOACT':'Do nothing: no new connection',
 'MTO-BILLING':'Fix the meter records so the 6 customers are billed','MTO-METER-AUDIT':'Check the meters for the 120 kWh not explained','MTO-BILLING-NOACT':'Do nothing: leave the meter records as they are',
 'MTO-INV-CLAIM':'Claim the inverter under warranty and wait for the replacement','MTO-INV-BUYNOW':'Buy a replacement now, then claim the failed unit','MTO-INV-LOCAL':'Have the inverter repaired locally','MTO-INV-NOACT':'Do nothing: run on one inverter',
 'MWEA-AGG':'Sign the aggregator’s off-season storage contract (Dec–Mar)','MWEA-COMPRESSOR':'Replace the compressor','MWEA-NOACT':'Do nothing',
 'THIKA-EPC-STOPGAP':'Night cover until the contractor replaces the start controller','THIKA-EPC-WAIT':'Wait for the contractor’s repair on 8 Nov, with no cover','THIKA-SELF':'Buy and fit a start controller ourselves',
 'KIRI-REPAIR':'Clean the condenser and repair the leak','KIRI-REPLACE':'Replace the refrigeration unit','KIRI-NOACT':'Do nothing',
 'EMB-CHEAPEST':'Charge only in the cheapest hours (00:00–05:00)','EMB-DEADLINE':'Charge to each bus’s departure time, outside peak hours (22:00–05:15)','EMB-NOACT':'Keep the October charging pattern',
 'KAS-OEM-STOPGAP':'Charge one bus at Ruiru on each night until the repair','KAS-OEM-WAIT':'Wait for the manufacturer’s repair, with no cover','KAS-LOCAL':'Have the charger repaired locally','KAS-SCHEDULE':'Change the charging schedule',
 'RUI-ABSORB6':'Take the 6 extra buses on the existing chargers','RUI-ABSORB10':'Take 10 extra buses on the existing chargers','RUI-4CHARGERS':'Install 4 more chargers','RUI-NOACT':'Do nothing: decline the extra buses',
 'RUI-CONN-CLAIM':'Claim charger 7, connector 2 at the next routine visit','RUI-CONN-NOACT':'Do nothing: leave connector 2 out of service'};
const optLabel = id => OPT_LABEL[id]||id;
const OPT = {};
Object.keys(SK).forEach(sk=>{const s=siteM(sk),p=sitePath(sk);
 (s.decision?.options||[]).forEach((o,i)=>OPT[o.id]={...o,_site:sk,_path:`${p}.decision.options[${i}]`});
 (s.entitlement?.options||[]).forEach((o,i)=>OPT[o.id]={...o,_site:sk,_path:`${p}.entitlement.options[${i}]`});});
/* Rows the manifest does not list as options: stated from manifest lines, no money invented (fixture-mapping §5). */
const SYN = (id,sk,path,extra) => OPT[id]={id,kind:'NO_ACTION',_site:sk,_synthetic:true,_path:path,...extra};
SYN('MTO-DEMAND-NOACT','mto',`${sitePath('mto')}.decision`,{reason:'No connection cost and no new contribution; the cooperative’s letter of intent lapses on 30 Nov.'});
SYN('MTO-BILLING-NOACT','mto',`${sitePath('mto')}.period.bridge[1]`,{effectMonthly:siteM('mto').period.bridge[1].amount,reason:'The 6 customers stay unbilled: −$56 a month, as in October.'});
SYN('RUI-NOACT','ruiru',`${sitePath('ruiru')}.decision`,{reason:'No cost; the city places the route elsewhere.'});
SYN('KIS-OM-NOACT','kisiwa',`${sitePath('kisiwa')}.entitlements[1]`,{reason:'No credit is requested; nothing is recorded.'});
SYN('RUI-CONN-NOACT','ruiru',`${sitePath('ruiru')}.incident`,{reason:'Connector 2 stays out of service; no departure depends on it, but the warranty claim is not made.'});
OPT['KIS-OM-REVIEW']={id:'KIS-OM-REVIEW',kind:'RIGHTS_REVIEW',_site:'kisiwa',_synthetic:true,_path:`${sitePath('kisiwa')}.entitlements[1]`,disposition:'RECOMMENDED',reason:'Response took 96 hours against 48 and the weather was calm; a person reviews the weather exception before the credit is requested.'};
OPT['RUI-CONN-CLAIM']={id:'RUI-CONN-CLAIM',kind:'SUPPLIER_REMEDY',_site:'ruiru',_synthetic:true,_path:`${sitePath('ruiru')}.incident.entitlement`,disposition:'RECOMMENDED',reason:'No departure depends on connector 2, so the claim waits for the next routine visit.'};

const DISP = {RECOMMENDED:['Recommended','green'],CONDITIONAL:['Conditional','amber'],ACCEPTABLE:['Acceptable',''],DEFERRED:['Deferred','blue'],REJECTED:['Rejected','red']};
const dispBadge = o => o.disposition?badge(...DISP[o.disposition]):badge('No action (baseline)','outline');
const TEXTFIX = {
 '6,430 needed with everything else; budget 5,000':'Needs $6,430 with everything else; the budget is $5,000',
 'wins if budget >= 6,430 and the cooperative will not extend its letter of intent':'Only if the budget is at least $6,430 and the cooperative will not extend its letter of intent',
 'fails the evening service obligation (P1 hard constraint) on a single genset':'Fails the evening supply obligation: one generator cannot be relied on alone',
 'LOI converts to supply contract; inverter INV-MT-02 restored first':'The letter of intent becomes a supply contract, and inverter 2 is restored first',
 'flat tariff: no schedule saving exists (EV-L1 immaterial here)':'Flat tariff: changing the schedule saves nothing here',
 'protects the right to claim; covered asset value 64,000 is EXPOSURE, not money gained':'Protects the right to claim; the $64,000 of covered battery value is at stake, not money gained',
 'every evening kWh is diesel; margin negative at 0.40 and no demand evidence':'Every evening kWh is diesel: the margin is negative at $0.40 a kWh and there is no demand evidence',
 'fails dawn adequacy safeguard':'Fails the dawn battery limit on some replayed days','repair restores redundancy for 1,800':'Repair restores the backup for $1,800','over budget; payback ~6 years':'Over budget; payback about 6 years',
 'payback about 6 years; outside the 12-month horizon and budget; revisit with a quote and 7-year lifecycle':'Payback about 6 years: outside the 12-month horizon and the budget; revisit with a quote and a 7-year life view',
 'exceeds the 400 kW import limit':'Exceeds the 400 kW grid import limit','connector compatibility confirmed for the 6 new buses':'Connector compatibility confirmed for the 6 new buses',
 'not needed for +6; insufficient alone for +10 (grid upgrade ~45,000 [assumption])':'Not needed for 6 more buses; not enough alone for 10 (a grid upgrade of about $45,000 would also be needed, an assumption)',
 'cheapest bill (12,975 a month) but 3 buses leave below required charge every night':'Cheapest bill ($12,975 a month), but 3 buses leave short of charge every night',
 'likely 2 missed departures in the 3 nights to 9 Nov (spare bus free on 1 night): 240 in penalties and 2 broken service obligations, against 90 for the stopgap':'Likely 2 missed departures in the 3 nights to 9 Nov (the spare bus is free on 1 night): about $240 in penalties and 2 broken departures, against $90 for the cover',
 'tariff applicability confirmed from invoice; 14-day supervised schedule':'Tariff confirmed from the utility invoice; 14 supervised nights first','supervised 14-day trial; verified before becoming policy':'Supervised 14-day trial; verified before it becomes policy',
 'no baseline capacity and no temperature record; a contested claim fails':'No baseline capacity test and no temperature record: a contested claim would fail','no cost now; cover stays at risk':'No cost now; the cover stays at risk',
 'the avoidable fuel is a policy problem; storage adds nothing the stop-threshold change does not':'The avoidable fuel is a settings problem; storage adds nothing the stop-setting change does not',
 'opening the unit voids the warranty; dominated by the claim':'Opening the unit voids the warranty; the claim is better in every case','half daytime capacity indefinitely; notice deadline lost on 27 Nov':'Half the daytime inverter capacity indefinitely; the warranty notice deadline passes on 27 Nov',
 'energy matches the occupancy model (+0.6%); no equipment problem to fix':'Electricity matches the occupancy model (+0.6%): no equipment problem to fix','contract signed':'Contract signed',
 'negative on 12 months; revisit if verified recovery after repair is below 60%':'Negative over 12 months; revisit if verified recovery after the repair is below 60%',
 'no protection for stock until 8 Nov; two evening grid outages in October':'No protection for stock until 8 Nov; there were two evening grid outages in October','self-funded controller voids the EPC workmanship cover; dominated':'A self-fitted controller voids the contractor’s workmanship cover',
 'voids power-stage warranty; dominated':'Voids the power-stage warranty','"restores billable charges; collection is a separate step"':'',
 'restores billable charges; collection is a separate step':'Restores billable charges; collection is a separate step','120 kWh unexplained after expected losses; no money attached':'120 kWh not explained after expected losses; no money attached',
 'baseline: 1,180 L/month pattern continues; 262.50/month avoidable fuel keeps being spent':'The 1,180-litre month repeats: $262.50 a month of avoidable fuel keeps being spent',
 'connector compatibility confirmed for the 6 new buses ':'Connector compatibility confirmed',
 'Removes only 20 L/month and puts dawn battery charge below 35% on 4 of 61 replayed days':'Removes only 20 L a month and leaves the battery below 35% at 5 am on 4 of 61 replayed days'};
const fx = t => {if(!t)return '';const v=TEXTFIX[t]??t;return cap(v);};
const NOACT_WHY = {'EMB-NOACT':'October’s pattern under the November tariff: $21,438 a month; the new 00:00–05:00 rate lowers it by $706.80 with no action, and that is never credited to an option.','MWEA-NOACT':'Nothing is broken; the room stays underused.','KIRI-NOACT':'The extra $194 a month of electricity continues.','KOB-NOACT':'Candidate running continues (330 L in October); stopping at 70% would avoid 210 L a month (Modelled).','BAT-NOACT':'No cost now; the cover stays at risk.'};
function optWhy(o){if(NOACT_WHY[o.id])return NOACT_WHY[o.id];if(o.disposition==='CONDITIONAL')return fx(o.condition);return fx(o.reason)||fx(o.note)||(o.condition?fx(o.condition):'');}
function optCost(o){
 if(o.capex!==undefined)return [o.capex===0?'$0':usd(o.capex),'capital purchase'];
 if(o.cost!==undefined)return [usd(o.cost),'one-off cost'];
 if(o.residual_cost!==undefined)return [usd(o.residual_cost),o.nights?`in total for ${o.nights} nights`:'our cost after the supplier’s remedy'];
 if(o.economics?.one_off!==undefined)return [usd(o.economics.one_off),'one-off set-up'];
 if(o.kind==='NO_ACTION')return ['$0','no spend'];
 if(o.kind==='COMMERCIAL_CORRECTION'||o.kind==='RIGHTS_REVIEW')return ['$0','office work'];
 if(o.id==='RUI-CONN-CLAIM')return ['$0','on the next routine visit'];
 return ['Not costed','rejected before costing'];}
function optEffect(o){const e=o.economics||{};
 if((o.safeguard||{}).result==='FAIL'&&!e.energy_cost_monthly)return ['Not valued','fails a limit, so it is not valued'];
 if(o.kind==='CAPEX'&&!e.net_12m&&o.net_12m===undefined)return ['Not valued',o.disposition==='DEFERRED'?'deferred before valuing':'rejected before valuing'];
 if(e.net_12m!==undefined)return [usd(e.net_12m,true),'over 12 months against no action'];
 if(o.net_12m!==undefined)return [usd(o.net_12m,true),'over 12 months against no action'];
 if(e.net_contract!==undefined)return [usd(e.net_contract,true),`over the ${e.months}-month contract`];
 if(e.charges_12m!==undefined)return [usd(e.charges_12m,true),'charges restored over 12 months (billed, not yet collected)'];
 if(e.net_monthly!==undefined)return [usd(e.net_monthly,true)+' a month','against no action'];
 if(o.id==='KIRI-NOACT')return ['$0','the extra $194 a month continues'];
 if(e.energy_cost_monthly!==undefined&&o.kind==='NO_ACTION')return ['$0',`bill ${usd(e.energy_cost_monthly)} a month continues`];
 if(e.energy_cost_monthly!==undefined)return ['Not valued','bill '+usd(e.energy_cost_monthly)+' a month, but fails a limit'];
 if(o.avoided_capex!==undefined)return [usd(o.avoided_capex),'capital not spent (avoided, not a saving)'];
 if(o.expected_penalties!==undefined)return [usd(-o.expected_penalties),'likely further penalties'];
 if(o.effectMonthly!==undefined)return [usd(o.effectMonthly)+' a month','charges stay unbilled'];
 if(o.monthly_net===0||o.kind==='NO_ACTION')return ['$0','baseline'];
 if(['REPAIR','SUPPLIER_REMEDY','STOPGAP_PLUS_CLAIM','INVESTIGATION','RIGHTS_REVIEW'].includes(o.kind))return ['No saving claimed','a cost to keep service, evidence or rights'];
 return ['Not modelled','no money effect modelled'];}
function optClass(o){if(optEffect(o)[0]==='Not valued')return o.forward_replay?'MODELLED':'NA';const c=o.economics?.class||o.avoided_capex_class;if(c)return c;if(o.kind==='NO_ACTION')return 'MODELLED';if(o.expected_penalties!==undefined)return 'MODELLED';return 'QUOTE';}
function whoPays(o){if(optCost(o)[0]==='Not costed')return '—';if(o.residual_cost!==undefined)return o.kind==='STOPGAP_PLUS_CLAIM'?'We pay now; the supplier replaces the failed unit (it becomes a spare, not cash)':o.kind==='SUPPLIER_REMEDY'?'Supplier remedies the fault; we pay the cost shown':'We pay';
 if(o.kind==='NO_ACTION')return '—';if(o.id==='MTO-HULLER')return 'We pay the connection contractor';if(o.id==='MTO-METER-AUDIT')return 'Routine maintenance budget';if(o.id==='KIS-REPAIR')return 'We pay: the warranty ended on 30 Jun 2026';return 'We pay';}
const OPT_WORK = {
 'KOB-STOPSOC':()=>{const e=OPT['KOB-STOPSOC'].economics;return `${OPT['KOB-STOPSOC'].forward_replay.avoidable_fuel_l} L × $1.25 = ${usd(e.gross_monthly)} − battery wear ${usd(e.wear_monthly)} = ${usd(e.net_monthly)} a month; × 12 − one-off ${usd(e.one_off)} (vendor remote change $60, trial supervision $30) = ${usd(e.net_12m)}`;},
 'MTO-HULLER':()=>{const e=OPT['MTO-HULLER'].economics;return `1,650 kWh × $0.30 = ${usd(e.revenue_monthly)} − fuel ${usd(e.fuel_monthly)} − collection ${usd(e.collection_cost_monthly)} = ${usd(e.net_monthly)} a month; × 12 − connection ${usd(e.one_off)} = ${usd(e.net_12m)}`;},
 'MTO-WELDING':()=>{const e=OPT['MTO-WELDING'].economics;return `660 kWh × $0.40 = ${usd(e.revenue_monthly)} − fuel ${usd(e.fuel_monthly)} = ${usd(e.net_monthly)} a month`;},
 'KIRI-REPAIR':()=>{const e=OPT['KIRI-REPAIR'].economics;return `$194 × 80% = ${usd(e.monthly)} a month; × 12 − $350 = ${usd(e.net_12m)}`;},
 'KIRI-REPLACE':()=>{const e=OPT['KIRI-REPLACE'].economics;return `${usd(e.monthly)} a month (full excess recovered plus 5% better than the model) × 12 − $4,800 = ${usd(e.net_12m)}`;},
 'EMB-DEADLINE':()=>{const e=OPT['EMB-DEADLINE'].economics;return `22:00–24:00: ${num(e.kwh_2200_2400)} kWh × $0.12 = ${usd(e.cost_2200_2400)}; 00:00–05:00: ${num(e.kwh_0000_0500)} kWh × $0.09 = ${usd(e.cost_0000_0500)}; demand 400 kW × $12 = ${usd(e.demand)}; bill ${usd(e.energy_cost_monthly)} a month. Against no action under the November tariff (${usd(OPT['EMB-NOACT'].economics.energy_cost_monthly)}): ${usd(e.saving_monthly)} a month; × 12 − ${usd(e.one_off)} = ${usd(e.net_12m)}`;},
 'EMB-CHEAPEST':()=>{const e=OPT['EMB-CHEAPEST'].economics;return `77,500 kWh × $0.09 = ${usd(e.energy)} + demand ${usd(e.demand)} = ${usd(e.energy_cost_monthly)} a month: the lowest bill only because it buys 9,300 kWh less a month (300 kWh short a night)`;},
 'MWEA-AGG':()=>{const e=OPT['MWEA-AGG'].economics;return `4,500 crate-days × $0.18 = ${usd(e.revenue_monthly)} − electricity ${usd(e.energy_monthly)} − handling ${usd(e.handling_monthly)} = ${usd(e.net_monthly)} a month; × ${e.months} − ${usd(e.one_off)} (sales $150, ethylene curtain $120) = ${usd(e.net_contract)}`;},
 'KIS-BATT60':()=>`${usd(OPT['KIS-BATT60'].monthly_fuel_saving_modelled)} a month × 12 − ${usd(OPT['KIS-BATT60'].capex)} = ${usd(OPT['KIS-BATT60'].net_12m)}`,
 'MTO-BILLING':()=>'140 kWh × $0.40 = $56 a month; × 12 = $672 billed (not collected)',
 'RUI-ABSORB6':()=>`20 buses × 140 kWh = 2,800 kWh a night against ${num(OPT['RUI-ABSORB6'].deliverable_kwh)} kWh deliverable: no new chargers, so the ${usd(OPT['RUI-ABSORB6'].avoided_capex)} purchase is avoided`};
const SG = {MG5_DAWN_ADEQUACY:'battery at least 35% at 5 am, so the clinic and homes are covered until dawn',MG4_BATTERY_WEAR:'extra battery wear',WARRANTY_OPERATING_LIMITS:'stays inside the battery warranty limits',EV1_DEPARTURE_READINESS:'every bus leaves with the charge it needs',EV5_IMPORT_LIMIT:'stays under the grid import limit'};
const OBL = {KOB_RESERVE_DAYS:()=>OPT['KOB-RESERVE'].forward_replay.soc_0500_below_35_days,
 'KOB-NOACT':[['unknown','Dawn battery limit under today’s settings is not reported by the replay']],'KOB-BATT100':[['unknown','Not checked: deferred before modelling']],
 'BAT-EVIDENCE':[['pass','No change to operation']],'BAT-CLAIM-NOW':[['unknown','Warranty conditions cannot be checked yet: no capacity test, no temperature record']],'BAT-NOACT':[['pass','No change to operation; cover stays at risk']],
 'KIS-REPAIR':[['pass','Evening supply has a backup generator again']],'KIS-REPLACE':[['pass','Evening supply has a backup generator again']],'KIS-BATT60':[['unknown','Not checked: deferred before a quote']],'KIS-NOACT':[['fail','Evening supply on one generator at 95% load: no backup']],
 'KIS-OM-REVIEW':[['pass','No operating effect']],'KIS-OM-NOACT':[['pass','No operating effect']],
 'MTO-HULLER':[['pass','Daytime supply covered; on 3 days a month the battery or generator supplies 225 kWh (in the fuel cost)'],['unknown','Needs inverter 2 restored first']],'MTO-WELDING':[['pass','Supply covered, but every evening kWh comes from diesel']],'MTO-DEMAND-NOACT':[['pass','No change']],
 'MTO-BILLING':[['pass','No operating effect']],'MTO-METER-AUDIT':[['pass','Done on the inverter visit']],'MTO-BILLING-NOACT':[['pass','No operating effect']],
 'MTO-INV-CLAIM':[['pass','Notice sent before the 27 Nov deadline']],'MTO-INV-BUYNOW':[['pass','Notice sent before the 27 Nov deadline']],'MTO-INV-LOCAL':[['fail','Opening the unit voids the warranty']],'MTO-INV-NOACT':[['fail','Warranty notice deadline passes on 27 Nov']],
 'MWEA-AGG':[['pass','Avocado with cabbage only with an ethylene curtain and a shared 5 °C setpoint (in the one-off cost)']],'MWEA-COMPRESSOR':[['pass','No change to temperature limits']],'MWEA-NOACT':[['pass','No change']],
 'THIKA-EPC-STOPGAP':[['pass','Stock covered at night by a manual-start rota and an SMS alarm until 8 Nov']],'THIKA-EPC-WAIT':[['fail','Batch temperature limits unprotected at night until 8 Nov']],'THIKA-SELF':[['fail','Voids the contractor’s workmanship cover']],
 'KIRI-REPAIR':[['pass','No change to temperature limits']],'KIRI-REPLACE':[['pass','No change to temperature limits']],'KIRI-NOACT':[['pass','No change']],
 'EMB-NOACT':[['pass','Every departure met in October']],
 'KAS-OEM-STOPGAP':[['pass','Every departure met: one bus charged at Ruiru each night']],'KAS-OEM-WAIT':[['fail','Likely 2 missed departures before 9 Nov']],'KAS-LOCAL':[['fail','Voids the power-stage warranty']],'KAS-SCHEDULE':[['pass','No effect: flat tariff']],
 'RUI-ABSORB6':[['pass','2,800 of 3,200 kWh a night; import limit held'],['unknown','Connector compatibility for the 6 new buses cannot be checked yet']],'RUI-ABSORB10':[['fail','3,360 kWh a night exceeds what the 400 kW import limit allows']],'RUI-4CHARGERS':[['fail','Not enough alone for 10 buses: the import limit still binds']],'RUI-NOACT':[['pass','No change']],
 'RUI-CONN-CLAIM':[['pass','No departure depends on connector 2']],'RUI-CONN-NOACT':[['pass','No departure depends on connector 2']]};
function obligations(o){const sg=o.safeguards||(o.safeguard?[o.safeguard]:null);let rows;
 if(sg)rows=sg.map(x=>x.mode==='COSTED_TRADEOFF'?['cost',`Costed: ${SG[x.policy]}, ${usd(x.cost_monthly)} a month (in the result)`]:[x.result==='PASS'?'pass':'fail',cap(SG[x.policy])+(o.id==='KOB-RESERVE'?`: broken on ${OBL.KOB_RESERVE_DAYS()} of 61 replayed days`:o.id==='EMB-CHEAPEST'&&x.result==='FAIL'?': 3 buses short every night':'')]);
 else rows=OBL[o.id]||[['unknown','Cannot be checked yet']];
 const W={pass:'Passes',fail:'Fails',unknown:'Cannot be checked yet',cost:'Costed'};
 return rows.map(([st,t])=>`<span class="obl obl-${st}">${icon(st==='pass'?'check':st==='fail'?'finding':st==='cost'?'money':'info')}<b>${W[st]}</b>&nbsp;${t}</span>`).join('');}

/* ---------- contract rights ---------- */
const STAGES=['Potential','Evidence assembled','Notified','Acknowledged','Accepted, denied or disputed','Remedy delivered','Credit booked','Cash received'];
const STAGE_IX={NONE:-1,POTENTIAL:0,EVIDENCE_ASSEMBLED:1,NOTIFIED:2,ACKNOWLEDGED:3,ACCEPTED:4,DENIED:4,DISPUTED:4,REMEDY_DELIVERED:5,CREDIT_BOOKED:6,CASH_RECEIVED:7};
function rightsOf(key){const k=siteM('kobo'),ks=siteM('kisiwa'),m=siteM('mto'),th=siteM('thika'),ka=siteM('kasarani'),ru=siteM('ruiru');
 const R={
 'kobo-battery':()=>{const e=k.entitlement;return{site:'kobo',dec:'kobo-battery',asset:'Kobo battery',who:e.contract.counterparty,type:'Equipment warranty',until:e.contract.term_end,state:e.claim_state,elig:['Not enough evidence yet','amber'],
  terms:['Lowest battery charge at least 10%','Cell temperature at most 45 °C','Charge and discharge at most half the capacity an hour','Capacity at least 95% at year 3 (interim guarantee)','Capacity at least 70% at the end of the term'],evidence:[['Temperature record','Not available yet'],['Commissioning capacity test','Not available yet'],['Cycles used',e.evidence.cycles],['Energy throughput',e.evidence.throughput]],
  deadline:null,deadlineNote:'No notice clock is running: no claim has been made.',cost:'$430 to gather the evidence',stake:'$64,000 of cover at stake, not money',path:`${sitePath('kobo')}.entitlement`};},
 'kisiwa-genset':()=>{const e=ks.entitlements[0];return{site:'kisiwa',dec:'kisiwa-genset',asset:'Kisiwa generator 1',who:e.contract.counterparty,type:'Equipment warranty',until:e.contract.term_end,state:e.claim_state,elig:['Expired; condition not met','red'],
  terms:[`Requires the ${e.contract.condition}`],evidence:[['Run hours at failure',num(e.evidence.run_hours_at_failure)],['1,000-hour service record','Not available yet']],deadline:null,deadlineNote:`The warranty ended on ${fdate(e.contract.term_end)}: no claim is possible; we fund the repair.`,cost:usd(e.operator_funded),path:`${sitePath('kisiwa')}.entitlements[0]`};},
 'kisiwa-om':()=>{const e=ks.entitlements[1];return{site:'kisiwa',dec:'kisiwa-om',asset:'Kisiwa operations and maintenance contract',who:e.contract.counterparty,type:'Service agreement (response time)',until:null,state:e.claim_state,elig:['Review required','amber'],
  terms:[`Response within ${e.contract.response_hours} hours`,'Service credit: 10% of the $700 monthly fee when response is late',`Exception: ${e.contract.exclusion.replace('sea access prevented by weather','sea access prevented by weather')}`],
  evidence:[['Reported','30 Oct, 19:10'],['Responded','3 Nov, 19:30'],['Response time',`${e.occurrence.response_hours} hours`],['Weather','Calm (port authority bulletin attached)']],deadline:null,deadlineNote:'Notice period not stated in the reviewed extraction: not available yet.',cost:'$0',stake:`Possible credit ${usd(e.potential_credit)}, counted only on a credit note`,path:`${sitePath('kisiwa')}.entitlements[1]`};},
 'mto-inverter':()=>{const e=m.entitlement;return{site:'mto',dec:'mto-inverter',asset:'Mto inverter 2',who:e.contract.counterparty,type:'Equipment warranty',until:e.contract.term_end,state:e.claim_state,elig:['Potentially covered','green'],
  terms:['Certified installer','Ambient temperature within specification','Firmware current','Remedy: replacement unit; shipping at our cost',`Notice within ${e.contract.notice_days} days; replacement in about ${e.contract.lead_time_days} days`],
  evidence:[['Installer certificate','On file'],['Ambient temperature','Highest 38 °C (specification 45 °C)'],['Firmware','Current'],['Fault log','On file']],deadline:e.notice_deadline,deadlineNote:'Notice deadline for the warranty claim.',cost:'$360 (claim and wait) or $2,910 (buy now, claim the failed unit)',path:`${sitePath('mto')}.entitlement`};},
 'thika-epc':()=>{const e=th.entitlement;return{site:'thika',dec:'thika-backup',asset:'Thika backup generator start controller',who:e.contract.counterparty,type:'Contractor workmanship warranty',until:e.contract.term_end,state:e.claim_state,elig:['Accepted by the contractor','green'],
  terms:['Condition: quarterly backup test logged',`Notice within ${e.contract.notice_days} days`,`Remedy: ${e.contract.remedy.replace('replace start controller','replace the start controller')}`],evidence:[['Quarterly backup tests',e.evidence.quarterly_tests],['Event log','On file'],['Inspection',`The ${link('wr-overview','starter and control-circuit inspection')} found the controller fault (7 Oct)`]],
  events:e.claim_events,deadline:e.remedy_scheduled,deadlineNote:'Contractor’s scheduled replacement date; then a witnessed automatic-start test.',cost:'$100 night cover',path:`${sitePath('thika')}.entitlement`};},
 'thika-insurance':()=>{const i=th.incident.insurance;return{site:'thika',dec:'thika-backup',asset:'Produce in our custody',who:'Insurer',type:'Goods-in-custody insurance',until:null,state:'NOTIFIED',stopped:'Not filed',elig:['Below the deductible',''],
  terms:[`Deductible ${usd(i.deductible)}`,`Notice within ${i.notice_days} days`],evidence:[['Notified',fdate(i.notified)],['Confirmed loss',usd(th.incident.batches[0].confirmed_damage)],['Reimbursement recorded',usd(i.reimbursement_recorded)]],
  events:[{state:'NOTIFIED',at:i.notified}],deadline:null,deadlineNote:'Notice given in time; no claim filed because the $108 loss is below the $500 deductible.',cost:'$108 compensation stays with us',path:`${sitePath('thika')}.incident.insurance`};},
 'kasarani-charger':()=>{const e=ka.entitlement;return{site:'kasarani',dec:'kasarani-charger',asset:'Kasarani charger 2',who:e.contracts[0].counterparty,type:'Equipment warranty and service agreement',until:e.contracts[0].term_end,state:e.claim_state,elig:['Covered part (power stage)','green'],
  terms:['Covers power-stage parts, including the contactor','Exception: an unauthorised repair voids the power-stage cover',`Response within ${e.contracts[1].response_hours} hours; restore within ${e.contracts[1].restore_business_days} business days`,'Service credit: 5% of the $400 monthly fee per business day late'],
  evidence:[['Responded within',`${e.sla_clock.responded_within_hours} hours`],['Restore due',fdate(e.sla_clock.restore_due)],['Service clock','Running']],events:e.claim_events,deadline:e.sla_clock.restore_due,deadlineNote:'Restore deadline under the service agreement.',cost:'$90 cover (one bus charged at Ruiru each night)',path:`${sitePath('kasarani')}.entitlement`};},
 'ruiru-connector':()=>{const e=ru.incident;return{site:'ruiru',dec:'ruiru-connector',asset:'Ruiru charger 7, connector 2',who:e.entitlement.counterparty,type:'Equipment warranty',until:null,state:e.entitlement.claim_state,elig:['Low priority',''],
  terms:['Charger warranty (power-stage and connector parts)'],evidence:[['Fault',`One session stopped on a fault on 6 Oct (see the ${link('ev-finding','connector 2 finding')}); connector status silent since`],['Effect on departures','None in the roster replay']],deadline:null,deadlineNote:'Plan: claim at the next routine visit.',cost:'$0',path:`${sitePath('ruiru')}.incident`};}};
 return R[key]();}
const RIGHTS_OF_OP = {lakeside:['mto-inverter','kisiwa-genset','kobo-battery','kisiwa-om'],harvest:['thika-epc','thika-insurance'],metro:['kasarani-charger','ruiru-connector']};
function claimSteps(r){const cur=STAGE_IX[r.state]??-1,ev={};(r.events||[]).forEach(x=>ev[STAGE_IX[x.state]]={at:x.at,label:x.state==='ACCEPTED'?'Accepted':null});
 return `<ol class="steps" aria-label="Claim stage">${STAGES.map((st,i)=>{const done=i<=cur&&cur>=0,now=i===cur;const lab=i===4&&ev[4]?.label?ev[4].label:st;
  return `<li class="${done?'done':''} ${now?'now':''}" ${now?'aria-current="step"':''}><span class="dot" aria-hidden="true"></span><b>${lab}</b><small>${ev[i]?fdate(ev[i].at):now?'current stage':i===cur+1&&r.stopped?r.stopped:''}</small></li>`;}).join('')}</ol>${cur<0?`<p class="note">No claim stage applies. ${r.deadlineNote}</p>`:''}`;}
function rightsPanel(key){const r=rightsOf(key),dl=r.deadline?daysUntil(r.deadline):null;
 return `<section class="panel rights" aria-labelledby="r-${key}"><div class="panel-head"><div><div class="eyebrow">Contract rights: who bears the cost</div><h2 id="r-${key}">${r.asset} · ${r.type}</h2><p>${r.who}${r.until?` · cover to ${fdate(r.until)}`:''}</p></div>${badge(...r.elig)}</div>
 ${claimSteps(r)}
 <div class="grid2"><div><h3>What the contract says</h3><ul class="list">${r.terms.map(t=>`<li>${t}</li>`).join('')}</ul>${fig('clause:'+key,'Contract clause and page reference')}</div><div><h3>Evidence we hold</h3>${kv(r.evidence)}</div></div>
 <div class="deadline ${dl!==null&&dl<=21?'soon':''}">${icon('clock')}<div>${dl!==null?`<strong>${dl} days left</strong> · ${fdate(r.deadline)} · `:''}${r.deadlineNote}</div></div>
 ${kv([['Our cost',r.cost],['Money recorded','None: nothing is recorded until a credit note or receipt arrives'],...(r.stake?[['Listed, never added',r.stake]]:[])])}
 <p class="legal">This is not a legal decision. Coverage is decided by the supplier or insurer.</p></section>`;}

/* ---------- decisions: anchored on the factor the options change ---------- */
const DEC = [
 {id:'kobo-generator',site:'kobo',q:'Kobo generator stop setting',node:'litres',opts:['KOB-STOPSOC','KOB-RESERVE','KOB-BATT100','KOB-NOACT'],commit:'KOB-STOPSOC'},
 {id:'kobo-battery',site:'kobo',q:'Kobo battery warranty evidence',node:null,opts:['BAT-EVIDENCE','BAT-CLAIM-NOW','BAT-NOACT'],rights:['kobo-battery']},
 {id:'kisiwa-genset',site:'kisiwa',q:'Kisiwa evening backup generator',node:'litres',opts:['KIS-REPAIR','KIS-REPLACE','KIS-BATT60','KIS-NOACT'],rights:['kisiwa-genset']},
 {id:'kisiwa-om',site:'kisiwa',q:'Kisiwa late repair response and service credit',node:'om',opts:['KIS-OM-REVIEW','KIS-OM-NOACT'],rights:['kisiwa-om']},
 {id:'mto-demand',site:'mto',q:'Mto new daytime demand',node:'billed',opts:['MTO-HULLER','MTO-WELDING','MTO-DEMAND-NOACT']},
 {id:'mto-billing',site:'mto',q:'Mto billing after the meter swap',node:'billed',opts:['MTO-BILLING','MTO-METER-AUDIT','MTO-BILLING-NOACT']},
 {id:'mto-inverter',site:'mto',q:'Mto inverter 2 restore path',node:null,opts:['MTO-INV-CLAIM','MTO-INV-BUYNOW','MTO-INV-LOCAL','MTO-INV-NOACT'],rights:['mto-inverter']},
 {id:'mwea-occupancy',site:'mwea',q:'Mwea occupancy',node:'cd',opts:['MWEA-AGG','MWEA-COMPRESSOR','MWEA-NOACT']},
 {id:'thika-backup',site:'thika',q:'Thika stock cover until the start controller is replaced',node:'liab',opts:['THIKA-EPC-STOPGAP','THIKA-EPC-WAIT','THIKA-SELF'],rights:['thika-epc','thika-insurance']},
 {id:'kirinyaga-energy',site:'kirinyaga',q:'Kirinyaga electricity above the occupancy model',node:'kexcess',opts:['KIRI-REPAIR','KIRI-REPLACE','KIRI-NOACT'],commit:'KIRI-REPAIR'},
 {id:'embakasi-schedule',site:'embakasi',q:'Embakasi charging schedule',node:'energy',opts:['EMB-DEADLINE','EMB-CHEAPEST','EMB-NOACT'],commit:'EMB-DEADLINE'},
 {id:'kasarani-charger',site:'kasarani',q:'Kasarani departures while charger 2 is repaired',node:'chg',opts:['KAS-OEM-STOPGAP','KAS-OEM-WAIT','KAS-LOCAL','KAS-SCHEDULE'],rights:['kasarani-charger']},
 {id:'ruiru-expansion',site:'ruiru',q:'Ruiru route expansion: extra buses',node:'dep',opts:['RUI-ABSORB6','RUI-ABSORB10','RUI-4CHARGERS','RUI-NOACT']},
 {id:'ruiru-connector',site:'ruiru',q:'Ruiru idle connector claim',node:'conn',opts:['RUI-CONN-CLAIM','RUI-CONN-NOACT'],rights:['ruiru-connector']}];
const decById = id => DEC.find(d=>d.id===id);
const decOf = optId => DEC.find(d=>d.opts.includes(optId));
const DEC_SEE_ALSO = {'MTO-INV-CLAIM':'mto-inverter','MTO-INV-BUYNOW':'mto-inverter'};

/* text and counterfactual structure per decision (manifest values only) */
function decText(d){const s=siteM(d.site),P=s.period,o=k=>OPT[k],e=k=>OPT[k].economics||{};
 const T={
 'kobo-generator':()=>{const st=o('KOB-STOPSOC'),fb=P.fuel_balance;return{
  factor:`Litres used: ${num(P.actual.diesel_l)} L in October against ${num(P.plan.diesel_l)} L planned. Observed through the generator model, the extra 480 L is 330 L of candidate running (the generator ran while solar and the battery could carry the load), 30 L of needed running for evening load growth, and 120 L the model cannot explain (above the 2% tolerance, being investigated).`,
  change:'Each option changes one factor: candidate running litres. How much of the 330 L an option avoids is that option’s modelled effect, never part of what was observed. Everything else in the structure (price, tariff, staff) stays as in no action.',
  why:`Of the 330 L of candidate running, stopping at 70% avoids ${st.forward_replay.avoidable_fuel_l} L a month in a forward replay of 61 days, with the battery at least 35% at 5 am on every day. Lowering the reserve looks similar but removes only ${o('KOB-RESERVE').forward_replay.avoidable_fuel_l} L and breaks the dawn limit on ${o('KOB-RESERVE').forward_replay.soc_0500_below_35_days} of 61 days. More storage (${usd(o('KOB-BATT100').capex)}) adds nothing the setting change does not. The forward-replay litres are design values, to be reproduced from your data.`,
  cf:[['Candidate running a month','330 L (October)','120 L: 210 L avoided (Modelled)','310 L: 20 L avoided (Modelled)'],['Battery at least 35% at 5 am','not reported by the replay','held on 61 of 61 days','broken on 4 of 61 days'],['Battery wear','—','$12 a month (costed)','—'],['Effect on contribution','$0','+$250.50 a month','not valued: fails a limit']],cfHead:['Factor','No action','Stop at 70%','Lower the reserve'],
  sens:[`Diesel 20% cheaper: ${usd(st.sensitivity.diesel_minus_20pct_net_12m)} over 12 months; ranking unchanged.`,`Only 160 L a month proves avoidable: ${usd(st.sensitivity.feasible_fuel_160l_net_12m)} over 12 months; still first.`],
  verify:[['Operational','Generator time beyond need down by at least half on comparable days; battery at least 35% at 5 am every day (14 matched days before and after)'],['Economic','Fuel used (tank dips and deliveries) per delivered kWh, adjusted for weather, against the days before; November books'],['Causal','Compared on days with similar solar and load (within 10%); Kisiwa and Mto as sites without the change']],
  records:[['node:kobo:litres','Litres used and their split'],['node:kobo:fb','Fuel balance'],['opt:KOB-STOPSOC:effect','How the 12-month result is worked out']]};},
 'kobo-battery':()=>{const en=s.entitlement;return{
  factor:`Who bears the cost if the battery fades: usable capacity is estimated at 184 kWh (92% of ${num(s.physical.battery_kwh)} kWh) at 2.7 years, below the warranty’s 95% interim guarantee if confirmed. The estimate comes from reconstructing charge and energy, not from a capacity test.`,
  change:'Gathering evidence changes the rights factor (whether a claim can succeed); it does not change any money factor this year.',
  why:`A claim now would fail: there is no commissioning capacity test and no temperature record. The evidence costs ${usd(o('BAT-EVIDENCE').cost)} (capacity test $250, temperature sensor $180) and one crew visit, and keeps $64,000 of cover claimable. That cover is at stake, not money gained.`,
  cf:[['Evidence held','none','capacity test and temperature record','none'],['Cover on the battery','at risk','claimable if capacity falls','claim likely to fail'],['Our cost','$0','$430','$0']],cfHead:['Factor','No action','Gather evidence','Claim now'],
  sens:['If capacity falls further before the test, the claim case gets stronger only with the temperature record in place.'],
  verify:[['Operational','Capacity test result on file; cell temperature logged from the day the sensor is fitted'],['Economic','None expected now: protecting the right to claim is not a saving'],['Causal','Not applicable: no money effect is claimed']],
  records:[['clause:kobo-battery','Warranty clause'],['stake:battery','Cover at stake']]};},
 'kisiwa-genset':()=>{const b60=o('KIS-BATT60');return{
  factor:`Generators available for the evening: generator 1 failed on 30 Oct (alternator), so generator 2 carries every evening alone at 95% load. Evening supply (18:00–23:00) is a firm obligation. Kisiwa uses the most diesel in the portfolio (${num(P.actual.diesel_l)} L), but every generator interval was needed, so no fuel option qualifies.`,
  change:'Repair restores the generators-available factor to 2; it does not change litres (all needed).',
  why:`Repair restores the backup for ${usd(o('KIS-REPAIR').cost)} against ${usd(o('KIS-REPLACE').capex)} to replace. The warranty ended on 30 Jun 2026 and the 1,000-hour service was missed, so we pay. Battery storage (${usd(b60.capex)}) saves a modelled ${usd(b60.monthly_fuel_saving_modelled)} a month: ${usd(b60.net_12m,true)} over 12 months.`,
  cf:[['Generators available in the evening','1, at 95% load','2','2'],['Evening supply obligation','at its limit, no backup','held','held'],['One-off cost','$0','$1,800','$9,500']],cfHead:['Factor','No action','Repair','Replace'],
  sens:['A storage quote and a 7-year life view could revisit battery storage; it stays outside this 12-month plan.'],
  verify:[['Operational','Generator 1 back in service; no evening without a standby generator'],['Economic','Repair invoice matches the quote'],['Causal','Not needed: this protects service; no saving is claimed']],
  records:[['node:kisiwa:litres','Litres used and their split'],['clause:kisiwa-genset','Warranty clause']]};},
 'kisiwa-om':()=>{const en=s.entitlements[1];return{
  factor:`Who bears the cost of a late repair response: the contractor responded in ${en.occurrence.response_hours} hours against ${en.contract.response_hours}. The contract gives a service credit of 10% of the $700 monthly fee when late, except when weather prevents sea access; the port bulletin says the weather was calm. October’s maintenance-contract invoice is also missing, so that line is an estimate.`,
  change:'A confirmed credit would lower the maintenance-contract line only when a credit note arrives; until then nothing is recorded.',
  why:'The weather exception is a judgement for a person, so the system flags the case for review rather than deciding coverage.',
  cf:[['Service credit','not requested','requested after review (possible $70)'],['Maintenance-contract line','estimated at plan','unchanged until a credit note']],cfHead:['Factor','No action','Review, then request'],
  sens:['If the reviewer finds weather did prevent access, no credit applies.'],
  verify:[['Operational','Review recorded by a named person'],['Economic','Credit note received and booked'],['Causal','Not applicable']],
  records:[['clause:kisiwa-om','Service clause'],['stake:credit','Possible credit']]};},
 'mto-demand':()=>{const hu=o('MTO-HULLER'),w=o('MTO-WELDING');return{
  factor:`A new demand factor appeared: the Mto Farmers Cooperative signed a letter of intent for a ${hu.load.kw} kW rice huller, ${hu.load.window}, ${hu.load.days_per_month} days a month (${num(hu.load.kwh_month)} kWh). A welding workshop asked, verbally, for ${w.load.kw} kW in the evening.`,
  change:'Connecting a customer adds billed kWh at the productive tariff and adds generator litres where solar cannot carry the load.',
  why:`Huller: ${usd(hu.economics.revenue_monthly)} a month in sales, ${usd(hu.economics.fuel_monthly)} fuel, ${usd(hu.economics.collection_cost_monthly)} collection: ${usd(hu.economics.net_monthly)} net a month. Welding runs on diesel for every kWh: ${usd(w.economics.net_monthly)} a month; it breaks even only at $${w.break_even_tariff_usd_per_kwh} a kWh and there is no contract.`,
  cf:[['Billed kWh a month','+0','+1,650 (daytime)','+660 (evening)'],['Generator fuel a month','+$0','+$85 (68 L on 3 low-sun days)','+$272.25'],['Effect on contribution','$0','+$395 a month','−$8.25 a month']],cfHead:['Factor','No action','Rice huller','Welding'],
  sens:['If the huller contract is not signed, the huller drops; the inverter warranty path is still recommended.',`If the cooperative will not extend past 30 Nov and the budget is at least $6,430, buying the inverter now keeps the huller (see Act first).`],
  verify:[['Operational','Huller metered kWh each month against the planned load'],['Economic','Billed and collected huller sales against the modelled monthly figure'],['Causal','Direct: a new metered customer']],
  records:[['opt:MTO-HULLER:effect','How the huller result is worked out'],['node:mto:billed','Billed kWh']]};},
 'mto-billing':()=>{const a=P.actual;return{
  factor:`Billed kWh: ${num(a.unbilled_mapping_kwh)} kWh was metered but not billed because 6 meters were swapped on 3 Oct and the meter register was not applied to billing. Separately, ${num(a.unexplained_kwh)} kWh is lost beyond expected losses: not priced, investigated, not called theft.`,
  change:'Fixing the register restores the billed-kWh factor; the meter check observes the losses factor that is not explained yet.',
  why:`Fixing the records restores $56 a month of charges ($672 over 12 months). Billed is not collected: collection is a separate step, so these charges are listed beside the plan, not added. The meter check costs $60 from the routine maintenance budget.`,
  cf:[['kWh metered but not billed','140 a month','0'],['Losses beyond expected','120 kWh, not priced','checked on the inverter visit'],['Charges','−$56 a month','restored (billed, not collected)']],cfHead:['Factor','No action','Fix records + meter check'],
  sens:['Charges restored are listed, never added to the modelled plan total.'],
  verify:[['Operational','Next bill run includes the 6 customers; unexplained kWh falls after the meter check'],['Economic','Charges appear in the November billing export; collections tracked separately'],['Causal','Direct: records corrected for named meters']],
  records:[['node:mto:billed','Billed kWh and its parts'],['node:mto:lossx','Losses beyond expected'],['stake:charges','Charges restored']]};},
 'mto-inverter':()=>{const en=s.entitlement,c=o('MTO-INV-CLAIM'),b=o('MTO-INV-BUYNOW');return{
  factor:`Inverters in service: inverter 2 of 2 tripped and latched on ${fdate(en.occurrence.failed)}, so Mto runs at half its daytime inverter capacity. It is potentially covered by warranty to ${fdate(en.contract.term_end)}; notice is due by ${fdate(en.notice_deadline)}.`,
  change:'Each path restores the inverters-in-service factor on a different date and puts a different cost on the cost-bearer factor.',
  why:`Claim and wait costs us ${usd(c.residual_cost)} (shipping $150, installation $80, extra fuel $130 over ${en.contract.lead_time_days} days) and restores by ${fdate(c.restore_by)}. Buying now costs ${usd(b.residual_cost)} and restores by ${fdate(b.restore_by)}. The rice huller needs the inverter and 5 working days to connect before its letter of intent lapses on 30 Nov, so the path depends on whether the cooperative extends.`,
  cf:[['Inverters in service','1 of 2','2 of 2 by 28 Nov','2 of 2 by 12 Nov'],['Rice huller','lost','kept if the letter is extended','kept'],['Our cost','$0, cover lost after 27 Nov','$360','$2,910']],cfHead:['Factor','No action','Claim and wait','Buy now, then claim'],
  sens:[`Letter of intent not extended and budget at least $6,430: buying now gives +$3,546 over 12 months against +$2,556 for claim and wait, which loses the huller.`,'Letter of intent extended: claim and wait stays best (+$6,096 for the plan) at any budget.'],
  verify:[['Operational','Inverter 2 back in service by the restore date'],['Economic','Supplier delivers the replacement unit; our cost stays at the residual'],['Causal','Not needed: a repair, not a saving']],
  records:[['clause:mto-inverter','Warranty clause'],['opt:MTO-INV-CLAIM:cost','Our cost, claim and wait'],['opt:MTO-INV-BUYNOW:cost','Our cost, buy now']]};},
 'mwea-occupancy':()=>{const ag=o('MWEA-AGG'),a=P.actual;return{
  factor:`Occupied crate-days: ${num(a.crate_days)} in October (${a.occupancy_pct}% full) against ${num(P.plan.crate_days)} planned (${P.plan.occupancy_pct}%). Electricity is what the room should use at that occupancy (${num(a.kwh)} kWh against ${num(a.kwh_model)} expected, +0.6%), so the high cost per crate-day comes from low occupancy, not equipment.`,
  change:'The contract adds 4,500 crate-days a month (December to March); the electricity factor rises with occupancy, as the model predicts.',
  why:`A new compressor (${usd(o('MWEA-COMPRESSOR').capex)}) fixes nothing. The aggregator contract (150 crates at $0.18) nets a modelled ${usd(ag.economics.net_monthly)} a month, ${usd(ag.economics.net_contract)} over ${ag.economics.months} months after ${usd(ag.economics.one_off)} set-up. Avocado stored with cabbage needs an ethylene curtain and a shared 5 °C setpoint.`,
  cf:[['Occupied crate-days a month','4,340 (October)','+4,500 (Dec–Mar)'],['Electricity','as the model, at low occupancy','+$225 a month (model)'],['Effect on contribution','$0','+$485 a month']],cfHead:['Factor','No action','Aggregator contract'],
  sens:['If the contract is not signed, Mwea stays as it is; nothing is broken.'],
  verify:[['Operational','Crate-days a month from the storage ledger'],['Economic','Aggregator invoices paid'],['Causal','Direct: a named customer’s crates']],
  records:[['node:mwea:cd','Occupied crate-days'],['node:mwea:kexcess','Electricity against the occupancy model'],['opt:MWEA-AGG:effect','How the contract result is worked out']]};},
 'thika-backup':()=>{const inc=s.incident,b=inc.batches[0];return{
  factor:`The backup-start factor failed on 6 Oct: the grid was lost ${inc.grid_outage}; automatic start was requested at 19:11:05 and the backup generator (GEN-CR-01) failed to start at 19:11:10 (start controller); staff started it by hand at 19:14. The chamber was above its 2–4 °C band for 25–35 minutes, peak 8.2 °C at 19:19. The French-bean batch (B-1031, export grade, limit 5 °C) was above its limit for 20–30 minutes; avocados (limit 12 °C) were not exposed; the cabbage batch had left on 5 Oct.`,
  change:'Night cover changes the backup-start factor until the contractor’s repair; the compensation factor then stays at zero.',
  why:`The French-bean batch was ${usd(b.exposed_value)} of the customer’s produce at stake (not money); inspection downgraded 6 crates and the contract made that a ${usd(b.liability)} liability. The contractor accepted the warranty claim on 17 Oct and replaces the controller on ${fdate(s.entitlement.remedy_scheduled)}. Night cover until then costs ${usd(o('THIKA-EPC-STOPGAP').residual_cost)} (SMS alarm relay $40, labour $60). Fitting a controller ourselves (${usd(o('THIKA-SELF').cost)}) voids the contractor’s cover. Insurance is not claimed: $108 is below the $500 deductible.`,
  cf:[['Backup start at night, to 8 Nov','unreliable','manual-start rota + SMS alarm','repaired, cover lost'],['Batch limits','unprotected at night','covered','covered'],['Our cost','$0','$100','$710']],cfHead:['Factor','Wait with no cover','Night cover','Fit it ourselves'],
  sens:['Insurance does not change the choice: the $108 loss is below the $500 deductible.'],
  verify:[['Operational',`The ${link('cold-action','witnessed automatic-start test')} after the controller is replaced on 8 Nov`],['Economic','No further compensation credit notes'],['Causal','Direct: a repaired component']],
  records:[['node:thika:liab','Customer compensation'],['stake:batch','Batch exposed (at stake)'],['clause:thika-epc','Workmanship warranty clause']]};},
 'kirinyaga-energy':()=>{const rp=o('KIRI-REPAIR'),rl=o('KIRI-REPLACE'),a=P.actual;return{
  factor:`Electricity above what occupancy explains: Kirinyaga was ${a.occupancy_pct}% full, as planned, but used ${num(a.kwh)} kWh against ${num(a.kwh_model)} expected: 970 kWh (24%) more, against a 5% tolerance. That costs $194 a month at $0.20 a kWh.`,
  change:'The repair targets that one factor (excess kWh); occupancy and prices stay as in no action.',
  why:`Cleaning the condenser and repairing the leak (${usd(rp.cost)}) should recover 80% (range 60–90%): ${usd(rp.economics.monthly)} a month, ${usd(rp.economics.net_12m)} over 12 months. Replacement (${usd(rl.capex)}) recovers ${usd(rl.economics.monthly)} a month but is ${usd(rl.economics.net_12m,true)} over 12 months.`,
  cf:[['Electricity above the model a month','970 kWh','about 194 kWh (80% recovered)','none (5% better than the model)'],['Effect on contribution','$0','+$155.20 a month','+$234.30 a month'],['One-off cost','$0','$350','$4,800']],cfHead:['Factor','No action','Repair','Replace'],
  sens:['If verified recovery after the repair is below 60%, replacement is reconsidered.'],
  verify:[['Operational','Electricity back within the 5% model tolerance at the same occupancy and temperature, over 30 days'],['Economic','Room electricity invoice against the modelled recovery'],['Causal','Mwea and Thika as rooms without the repair']],
  records:[['node:kirinyaga:kexcess','Electricity above the model'],['opt:KIRI-REPAIR:effect','How the repair result is worked out']]};},
 'embakasi-schedule':()=>{const dl=o('EMB-DEADLINE'),ch=o('EMB-CHEAPEST'),na=o('EMB-NOACT'),a=P.actual;return{
  factor:`Share of charging at peak price: ${pct(a.peak_share)} in October against ${pct(P.plan.peak_share)} planned, and the monthly peak reached ${a.max_kw} kW (plan ${P.plan.max_kw} kW, which is also the import limit). All ${num(a.departures_met)} departures were met. From 1 Nov the tariff adds a 00:00–05:00 rate at $0.09.`,
  change:'A schedule changes two factors, peak share and peak kW; departures must stay met. No action is October’s pattern under the November tariff.',
  why:`Charging to each departure time costs a modelled ${usd(dl.economics.energy_cost_monthly)} a month: ${usd(dl.economics.saving_monthly)} less than no action (${usd(na.economics.energy_cost_monthly)}), ${usd(dl.economics.net_12m)} over 12 months after ${usd(dl.economics.one_off)} set-up. The new rate also lowers no action by $706.80 a month; that is not credited to the schedule. Charging only 00:00–05:00 gives the cheapest bill (${usd(ch.economics.energy_cost_monthly)}) but delivers ${num(ch.deliverable_kwh)} of the ${num(ch.required_kwh)} kWh needed each night, so 3 buses leave short: rejected.`,
  cf:[['Share at peak price','55%','near 0%','0%'],['Monthly peak import','500 kW','400 kW','500 kW'],['Energy deliverable a night','2,800 needed','2,900','2,500'],['Required departures met','all','all','3 buses short a night'],['Monthly bill','$21,438','$13,356','$12,975']],cfHead:['Factor','No action (November tariff)','Charge to departure time','Cheapest hours only'],
  sens:['If the invoice shows a different tariff, the saving is recomputed before approval (see the switch on Act first).','A 21-bus night needs about 406 kW: inside the 500 kW limit, above the 400 kW plan.'],
  verify:[['Operational','Peak share near 0%, about 62,000 kWh a month at the 00:00–05:00 rate, every departure met, over 14 supervised nights'],['Economic','Next utility invoice: time-of-use and demand lines against the modelled figure'],['Causal','Ruiru as the comparison depot; Kasarani’s flat tariff is not comparable']],
  records:[['node:embakasi:peak','Energy at peak price'],['node:embakasi:maxkw','Monthly peak import'],['opt:EMB-DEADLINE:effect','How the schedule result is worked out']]};},
 'kasarani-charger':()=>{const inc=s.incident,n=inc.november_to_date;return{
  factor:`Charging energy deliverable a night fell when charger 2 failed on 1 Nov (welded contactor): ${num(inc.capacity_after.deliverable_kwh)} of ${num(inc.capacity_after.required_kwh)} kWh, one bus short each night. Kasarani was on plan in October; the departures factor went below its limit at once, before any invoice. ${n.missed_departures} departures missed in November so far (${usd(n.penalties)} in penalties, recorded).`,
  change:'The cover adds one bus’s charge a night (charged at Ruiru) until the manufacturer restores charger 2 by 9 Nov.',
  why:`Charging one bus at Ruiru on each of the ${o('KAS-OEM-STOPGAP').nights} nights to 9 Nov costs ${usd(o('KAS-OEM-STOPGAP').residual_cost)} in total (overtime $70, energy $20), against about $240 in penalties and 2 broken departures if we wait. Local repair (${usd(o('KAS-LOCAL').cost)}) voids the power-stage warranty. A schedule change saves nothing on a flat tariff.`,
  cf:[['Energy deliverable a night','1,050 of 1,200 kWh','1,200 kWh (one bus at Ruiru)'],['Departures missed to 9 Nov','about 2','none'],['Cost','about $240 in penalties','$90']],cfHead:['Factor','Wait with no cover','Cover until repair'],
  sens:['If the repair slips past 9 Nov, the cover continues and service credits may apply (counted only on a credit note).'],
  verify:[['Operational','Every Kasarani departure met each night until and after the repair'],['Economic','No further penalties'],['Causal','Direct']],
  records:[['node:kasarani:chg','Energy deliverable a night'],['stake:penalty','November penalties'],['clause:kasarani-charger','Warranty and service clause']]};},
 'ruiru-expansion':()=>{const a6=o('RUI-ABSORB6'),a10=o('RUI-ABSORB10');return{
  factor:`A new demand factor: the city offers a route expansion of 6 buses. Ruiru’s chargers were in use ${pct(P.actual.charger_hour_utilisation)} of charger-hours in October, and its peak import was ${P.actual.max_kw} kW of a ${s.physical.import_limit_kw} kW limit.`,
  change:'More buses raise the required-kWh factor; the import limit bounds the deliverable kWh a night.',
  why:`With 6 more buses Ruiru needs ${num(a6.required_kwh)} kWh a night against ${num(a6.deliverable_kwh)} kWh it can deliver, with no new chargers: a modelled ${usd(a6.avoided_capex)} purchase avoided (avoided capital, not a saving in the books). Ten more need ${num(a10.required_kwh)} kWh: more than the import limit allows.`,
  cf:[['Required kWh a night','1,960 (14 buses × 140)','2,800 (20 buses)','3,360 (24 buses)'],['Deliverable kWh a night','3,200','3,200','3,200'],['Import limit','held','held','exceeded']],cfHead:['Factor','No action','6 more buses','10 more buses'],
  sens:['Ten buses would need a grid upgrade (about $45,000, an assumption) plus chargers: not modelled in this plan.'],
  verify:[['Operational','All Ruiru departures met after the 6 buses join; peak import stays under the limit'],['Economic','Utility invoices for the extra charging'],['Causal','Direct']],
  records:[['node:ruiru:dep','Required departures met'],['node:ruiru:demand','Peak import and demand charge']]};},
 'ruiru-connector':()=>({factor:'Charger 7, connector 2: one session stopped on a fault on 6 Oct (see the connector 2 finding); the connector has reported no status since; connector 1 on the same charger works. No departure depends on it in the roster replay, so it ranks below Kasarani’s fault.',
  change:'A claim changes only the cost-bearer factor for the repair.',why:'With no departure at risk, the claim waits for the next routine visit; no technician visit is spent on it now.',
  cf:[['Departures affected','none','none'],['Repair cost bearer','not raised','supplier, under warranty']],cfHead:['Factor','No action','Claim at next visit'],
  sens:['If the roster changes so a departure depends on charger 7, the claim moves up.'],
  verify:[['Operational','Connector 2 back in service after the visit'],['Economic','No cost to us'],['Causal','Not applicable']],records:[['node:ruiru:conn','Connector record']]})};
 return T[d.id]();}
