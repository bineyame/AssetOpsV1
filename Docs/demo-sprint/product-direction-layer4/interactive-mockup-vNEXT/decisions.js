/* vNEXT decision experience (Layer 4 Deliverable 6). Design mock-up only: no API calls, no product code.
   Every figure is read from MANIFEST (fixtures.js, generated from demo-site-scenario-manifest.yaml) or derived
   by arithmetic stated on screen and in fixture-mapping.md. Data-driven templates; no per-page hand-written figures. */

const AS_OF = MANIFEST.as_of; /* 2026-11-06 */
const TEN = MANIFEST.tenants;
const DSTATE = {op:'lakeside', role:'CEO', budget:{lakeside:'base'}};
const OPS = {
 lakeside:{ti:0,name:'Lakeside Power',short:'Lakeside',vertical:'mini',kind:'contribution',sites:['kobo','kisiwa','mto'],crewKey:'crew_visits_nov',crewWord:'crew visits',verifyOpt:'KOB-STOPSOC',verifySite:'kobo'},
 harvest:{ti:1,name:'Harvest Cold Network',short:'Harvest Cold',vertical:'cold',kind:'contribution',sites:['mwea','thika','kirinyaga'],crewKey:'technician_visits_nov',crewWord:'technician visits',verifyOpt:'KIRI-REPAIR',verifySite:'kirinyaga'},
 metro:{ti:2,name:'Metro Bus Depots',short:'Metro Bus',vertical:'ev',kind:'cost',sites:['embakasi','kasarani','ruiru'],crewKey:'technician_visits_nov',crewWord:'technician visits',verifyOpt:'EMB-DEADLINE',verifySite:'embakasi'}
};
OPS.lakeside.t=TEN[0];OPS.harvest.t=TEN[1];OPS.metro.t=TEN[2];
const SITEKEY = {kobo:['lakeside',0,'Kobo'],kisiwa:['lakeside',1,'Kisiwa'],mto:['lakeside',2,'Mto'],
 mwea:['harvest',0,'Room A · Mwea'],thika:['harvest',1,'Room B · Thika'],kirinyaga:['harvest',2,'Room C · Kirinyaga'],
 embakasi:['metro',0,'Embakasi'],kasarani:['metro',1,'Kasarani'],ruiru:['metro',2,'Ruiru']};
const siteM = k => OPS[SITEKEY[k][0]].t.sites[SITEKEY[k][1]];
const siteName = k => SITEKEY[k][2];
const sitePath = k => `tenants[${OPS[SITEKEY[k][0]].ti}].sites[${SITEKEY[k][1]}]`;
const SITE_STORY = {
 kobo:'Generator keeps running after dawn on 11 of 31 days',kisiwa:'Most diesel in the portfolio, all of it needed',mto:'Spare daytime solar, a failed inverter and unbilled customers',
 mwea:'Underused room: low occupancy, not equipment',thika:'Backup failure exposed one batch of tomatoes',kirinyaga:'Busy room using 24% more energy than it should',
 embakasi:'Paying peak prices for charging that could wait',kasarani:'Charger fault puts departures at risk',ruiru:'Looks underused; room for 6 more buses, not 10'};
const OPS_DETAIL = {kobo:'mini',mwea:'cold',thika:'cold',kirinyaga:'cold',embakasi:'ev',kasarani:'ev',ruiru:'ev'};

/* ---------- formatting ---------- */
const r2 = x => Math.round(x*100)/100;
function usd(n,sign=false){if(n===null||n===undefined)return 'not available yet';const neg=n<0,a=Math.abs(r2(n));const s=a.toLocaleString('en-US',{minimumFractionDigits:Number.isInteger(a)?0:2,maximumFractionDigits:2});return (neg?'−':(sign&&n>0?'+':''))+'$'+s;}
const num = (n,d=0) => n===null||n===undefined?'not available yet':Number(n).toLocaleString('en-US',{maximumFractionDigits:d,minimumFractionDigits:0});
const pct = (x,d=1) => (x*100).toFixed(d).replace(/\.0$/,'')+'%';
const fdate = iso => {const d=new Date(iso.slice(0,10)+'T00:00:00Z');return d.toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric',timeZone:'UTC'});};
const daysUntil = iso => Math.round((Date.parse(iso.slice(0,10))-Date.parse(AS_OF))/864e5);
const vh = t => `<span class="vh">${t}</span>`;
const money$ = (key,value,sign=false) => `<button class="d-money" data-evd="${key}">${usd(value,sign)}${vh(' – show source records')}</button>`;

/* ---------- plain-language vocabulary (no codes on screen) ---------- */
const DRIVER = {DEMAND_VOLUME:'Sales volume against plan',GEN_POLICY_RUNNING_AVOIDABLE:'Generator ran when solar and battery could carry the load (avoidable)',GEN_POLICY_RUNNING_CONSTRAINED:'Generator ran beyond need, but not avoidable in the replay',EVENING_LOAD_GROWTH:'Evening demand grew (generator needed)',UNEXPLAINED_RESIDUAL:'Fuel not explained yet',SOLAR_SHORTFALL_NECESSARY_GEN:'Rainy month: generator needed',METER_MAPPING_UNBILLED:'Customers not billed after a meter swap',AUTHORISED_ADJUSTMENT:'Approved clinic allowance',EVENING_NECESSARY_GEN:'Evening generator use (needed)',OCCUPANCY_REVENUE:'Fewer crate-days stored',OCCUPANCY_ENERGY_VOLUME:'Less energy at lower occupancy (not a saving)',ENERGY_EFFICIENCY:'Energy above what occupancy explains',CUSTOMER_COMPENSATION:'Compensation for damaged crates',PEAK_ENERGY_SHARE:'More charging at peak prices',DEMAND_CHARGE:'Higher monthly peak demand'};
const CLASS = {ECONOMIC_ACTUAL:['Recorded','rec'],MODELLED:['Modelled','mod'],DERIVED:['Not explained yet','unx'],ECONOMIC_ACTUAL_FORWARD:['From recorded bills','rec'],EXPOSURE:['Exposure, not money','exp']};
const SRC = {RECORDED:['Recorded','green'],ESTIMATED:['Estimated','amber'],MODELLED:['Modelled','blue'],NONE:['Coverage not stated yet','']};
const DISP = {RECOMMENDED:['Recommended','green'],ACCEPTABLE:['Acceptable fallback',''],CONDITIONAL:['Only if conditions change','amber'],DEFERRED:['Later','blue'],REJECTED:['Not chosen','red'],COMPARISON:['Shown for comparison','outline']};
const SAFEGUARD = {MG5_DAWN_ADEQUACY:'Battery at least 35% at 5 am, so the clinic and homes are covered until dawn',MG4_BATTERY_WEAR:'Extra battery wear',WARRANTY_OPERATING_LIMITS:'Stays inside the battery warranty limits',EV1_DEPARTURE_READINESS:'Every bus leaves with the charge it needs',EV5_IMPORT_LIMIT:'Stays under the grid import limit'};
const OPT_LABEL = {
 'KOB-NOACT':'Keep the current generator settings','KOB-RESERVE':'Lower the battery reserve from 30% to 25%','KOB-STOPSOC':'Change the generator stop setting (stop at 70% battery, not 90%)','KOB-BATT100':'Buy more battery storage',
 'BAT-CLAIM-NOW':'Claim the battery warranty now','BAT-EVIDENCE':'Gather the evidence first: capacity test and temperature sensor','BAT-NOACT':'Do nothing for now',
 'KIS-REPAIR':'Repair generator 1 (alternator)','KIS-REPLACE':'Replace generator 1','KIS-BATT60':'Buy battery storage to cut generator hours','KIS-NOACT':'Do nothing: run every evening on one generator',
 'MTO-HULLER':'Connect the cooperative’s rice huller (daytime)','MTO-WELDING':'Connect the evening welding workshop','MTO-BILLING':'Fix the meter records so 6 customers are billed','MTO-METER-AUDIT':'Check the meters for the 120 kWh we cannot explain',
 'MTO-INV-CLAIM':'Claim the inverter under warranty and wait for the replacement','MTO-INV-BUYNOW':'Buy a replacement now, then claim the failed unit','MTO-INV-LOCAL':'Have the inverter repaired locally','MTO-INV-NOACT':'Do nothing: run on one inverter',
 'MTO-DEMAND-NOACT':'Do nothing: no new connection','MTO-BILLING-NOACT':'Do nothing: leave the meter records as they are',
 'MWEA-AGG':'Sign the aggregator storage contract (Dec to Mar)','MWEA-COMPRESSOR':'Replace the compressor','MWEA-NOACT':'Do nothing',
 'THIKA-EPC-STOPGAP':'Night cover until the contractor replaces the switch controller','THIKA-EPC-WAIT':'Do nothing extra: wait for the contractor’s repair on 8 Nov','THIKA-SELF':'Buy and fit a controller ourselves',
 'KIRI-REPAIR':'Clean the condenser and repair the leak','KIRI-REPLACE':'Replace the refrigeration unit','KIRI-NOACT':'Do nothing',
 'EMB-CHEAPEST':'Charge only in the cheapest hours (00:00–05:00)','EMB-DEADLINE':'Charge to each bus’s departure time, avoiding peak prices','EMB-NOACT':'Keep the current charging pattern',
 'KAS-OEM-STOPGAP':'Charge one bus at Ruiru each night until the manufacturer repairs','KAS-OEM-WAIT':'Do nothing extra: wait for the manufacturer’s repair','KAS-LOCAL':'Have the charger repaired locally','KAS-SCHEDULE':'Change the charging schedule',
 'RUI-ABSORB6':'Take the 6 extra buses on the existing chargers','RUI-ABSORB10':'Take 10 extra buses on the existing chargers','RUI-4CHARGERS':'Install 4 more chargers','RUI-NOACT':'Do nothing: decline the extra buses',
 'CH-R7':'Claim Ruiru charger 7, connector 2 at the next routine visit'};

/* ---------- option index over the manifest ---------- */
const OPT = {};
OPS && Object.entries(SITEKEY).forEach(([sk])=>{const s=siteM(sk),p=sitePath(sk);
 (s.decision?.options||[]).forEach((o,i)=>OPT[o.id]={...o,_site:sk,_path:`${p}.decision.options[${i}]`});
 (s.entitlement?.options||[]).forEach((o,i)=>OPT[o.id]={...o,_site:sk,_path:`${p}.entitlement.options[${i}]`});});
/* Do-nothing rows the manifest does not list: no money invented; effect stated from manifest lines. */
OPT['MTO-DEMAND-NOACT']={id:'MTO-DEMAND-NOACT',kind:'NO_ACTION',_site:'mto',_synthetic:true,disposition:'COMPARISON',reason:'No connection cost and no new contribution; the cooperative’s letter of intent lapses on 30 Nov.'};
OPT['MTO-BILLING-NOACT']={id:'MTO-BILLING-NOACT',kind:'NO_ACTION',_site:'mto',_synthetic:true,disposition:'COMPARISON',effectMonthly:siteM('mto').period.bridge[1].amount,reason:'The 6 customers stay unbilled: −$56 a month, as in October’s variance.'};
OPT['RUI-NOACT']={id:'RUI-NOACT',kind:'NO_ACTION',_site:'ruiru',_synthetic:true,disposition:'COMPARISON',reason:'No cost; the city places the route elsewhere.'};

/* ---------- decisions (one comparator each) ---------- */
const DEC = [
 {id:'kobo-generator',site:'kobo',title:'Change when Kobo’s generator stops',opts:['KOB-STOPSOC','KOB-RESERVE','KOB-BATT100','KOB-NOACT'],verify:true},
 {id:'kobo-battery',site:'kobo',title:'Protect Kobo’s battery warranty',opts:['BAT-EVIDENCE','BAT-CLAIM-NOW','BAT-NOACT'],rights:['kobo-battery']},
 {id:'kisiwa-generator',site:'kisiwa',title:'Restore Kisiwa’s backup generator',opts:['KIS-REPAIR','KIS-REPLACE','KIS-BATT60','KIS-NOACT'],rights:['kisiwa-genset','kisiwa-om']},
 {id:'mto-inverter',site:'mto',title:'Restore Mto’s failed inverter',opts:['MTO-INV-CLAIM','MTO-INV-BUYNOW','MTO-INV-LOCAL','MTO-INV-NOACT'],rights:['mto-inverter']},
 {id:'mto-demand',site:'mto',title:'Sell Mto’s spare daytime solar',opts:['MTO-HULLER','MTO-WELDING','MTO-DEMAND-NOACT']},
 {id:'mto-billing',site:'mto',title:'Bill the Mto customers missed after the meter swap',opts:['MTO-BILLING','MTO-METER-AUDIT','MTO-BILLING-NOACT']},
 {id:'mwea-demand',site:'mwea',title:'Fill Mwea’s empty space',opts:['MWEA-AGG','MWEA-COMPRESSOR','MWEA-NOACT']},
 {id:'thika-backup',site:'thika',title:'Protect Thika’s stock until the switch is fixed',opts:['THIKA-EPC-STOPGAP','THIKA-EPC-WAIT','THIKA-SELF'],rights:['thika-ats','thika-insurance']},
 {id:'kirinyaga-energy',site:'kirinyaga',title:'Bring Kirinyaga’s energy use back to normal',opts:['KIRI-REPAIR','KIRI-REPLACE','KIRI-NOACT'],verify:true},
 {id:'embakasi-schedule',site:'embakasi',title:'Charge Embakasi’s buses outside peak hours',opts:['EMB-DEADLINE','EMB-CHEAPEST','EMB-NOACT'],verify:true},
 {id:'kasarani-charger',site:'kasarani',title:'Keep Kasarani’s buses running while charger 2 is repaired',opts:['KAS-OEM-STOPGAP','KAS-OEM-WAIT','KAS-LOCAL','KAS-SCHEDULE'],rights:['kasarani-charger']},
 {id:'ruiru-expansion',site:'ruiru',title:'Can Ruiru take the city’s extra buses?',opts:['RUI-ABSORB6','RUI-ABSORB10','RUI-4CHARGERS','RUI-NOACT'],rights:['ruiru-connector']}
];
const decOf = optId => DEC.find(d=>d.opts.includes(optId));

/* Experience invariant text (L3.6): built from manifest values only. */
function decText(d){
 const s=siteM(d.site),P=s.period,o=k=>OPT[k],e=k=>OPT[k].economics||{};
 const T={
 'kobo-generator':()=>{const st=o('KOB-STOPSOC'),ex=s.findings_expected[0],fb=P.fuel_balance;return{
  happened:`On ${ex.days} October days the generator kept running after dawn while solar and the battery could have carried the load. Fuel used: ${num(P.actual.diesel_l)} L against a plan of ${num(P.plan.diesel_l)} L.`,
  matters:`Replaying September and October with the new stop setting removes ${st.forward_replay.avoidable_fuel_l} L a month: ${usd(e('KOB-STOPSOC').gross_monthly)} of diesel. Extra battery wear costs ${usd(e('KOB-STOPSOC').wear_monthly)} a month, so the modelled net is ${usd(e('KOB-STOPSOC').net_monthly)} a month and ${usd(e('KOB-STOPSOC').net_12m)} over 12 months after a one-off ${usd(e('KOB-STOPSOC').one_off)} (vendor remote reconfiguration $60 and 14-day trial supervision $30).`,
  why:`Lowering the battery reserve looks similar but removes only ${o('KOB-RESERVE').forward_replay.avoidable_fuel_l} L a month and leaves the battery below 35% at 5 am on ${o('KOB-RESERVE').forward_replay.soc_0500_below_35_days} of 61 replayed days. More storage (${usd(o('KOB-BATT100').capex)}) adds nothing the setting change does not.`,
  prevents:`${st.condition[0].toUpperCase()+st.condition.slice(1)}. The upper bound of ${usd(ex.gross_exposure_usd[1])} (all generator time on those days) is not the decision value. Separately, ${fb.residual_l} L of fuel is not explained by the model and is above the ${fb.tolerance_pct}% tolerance: it is being investigated and no recovery is claimed.`,
  prove:[['Operation',pt(s.decision.verification_plan.operational_target)],['Money',pt(s.decision.verification_plan.economic)],['Attribution',pt(s.decision.verification_plan.causal)]],
  records:['Fuel delivery notes and tank dips','Energy management system export (5-minute in the trial window)','Customer billing export','Monthly plan or budget spreadsheet'],
  sensitivity:[`Diesel 20% cheaper: ${usd(st.sensitivity.diesel_minus_20pct_net_12m)} over 12 months; ranking unchanged.`,`Only 160 L a month proves avoidable: ${usd(st.sensitivity.feasible_fuel_160l_net_12m)} over 12 months; still first.`]};},
 'kobo-battery':()=>{const en=s.entitlement;return{
  happened:`Usable capacity is estimated at 184 kWh (92% of ${num(s.physical.battery_kwh)} kWh) at 2.7 years. If confirmed, that is below the warranty’s interim guarantee of 95% at year 3. The estimate comes from reconstructing charge and energy, not from a capacity test.`,
  matters:`The battery is under the supplier’s warranty until ${fdate(en.contract.term_end)}. The cover on the battery is an exposure we protect, not money we will receive.`,
  why:`A claim now would fail: there is no commissioning capacity test and no temperature record. Gathering the evidence costs ${usd(o('BAT-EVIDENCE').cost)} (capacity test $250 and temperature sensor $180) and one crew visit.`,
  prevents:'It needs one of the three November crew visits; it is last in the crew plan because nothing breaks if it waits a month.',
  prove:[['Operation','Capacity test result on file; cell temperature logged from the day the sensor is fitted'],['Money','None expected now: protecting the right to claim is not a saving'],['Attribution','Not applicable: no money effect is claimed']],
  records:['Commissioning documents and capacity test','Battery management system logs (cycles, temperature)','Warranty contract (reviewed extraction with page references)'],
  sensitivity:['If capacity falls further before the test, the claim case gets stronger only with the temperature record in place.']};},
 'kisiwa-generator':()=>{const b60=o('KIS-BATT60');return{
  happened:`Generator 1 failed (alternator). Generator 2 now carries every evening alone at 95% load. Kisiwa uses the most diesel in the portfolio (${num(P.actual.diesel_l)} L in October), but every generator hour was needed.`,
  matters:`Without a second generator, the next failure cuts evening supply (18:00–23:00). Repair costs ${usd(o('KIS-REPAIR').cost)}; replacement ${usd(o('KIS-REPLACE').capex)}. The warranty ended on 30 Jun 2026, so we pay for the repair.`,
  why:`Repair restores the backup for ${usd(o('KIS-REPAIR').cost)}. Battery storage (${usd(b60.capex)}) saves a modelled ${usd(b60.monthly_fuel_saving_modelled)} a month: ${usd(b60.net_12m)} over 12 months, payback about 6 years.`,
  prevents:'Must do: evening supply is a firm service obligation. Uses one November crew visit. Negative control: Kisiwa has the highest diesel use, yet no fuel-saving option qualifies.',
  prove:[['Operation','Generator 1 back in service; no evening without a standby generator'],['Money','Repair invoice matches the quoted cost'],['Attribution','Not needed: this protects service; no saving is claimed']],
  records:['Generator service log (1,000-hour service record)','Operations and maintenance invoices','Port authority weather bulletin for the response-time review'],
  sensitivity:['A storage quote and a 7-year life view could revisit battery storage later; it stays outside this 12-month plan.']};},
 'mto-inverter':()=>{const en=s.entitlement,c=o('MTO-INV-CLAIM'),b=o('MTO-INV-BUYNOW');return{
  happened:`Inverter 2 of 2 tripped and latched on ${fdate(en.occurrence.failed)}. Mto runs at half its daytime inverter capacity.`,
  matters:`The warranty path costs us ${usd(c.residual_cost)} (shipping $150, installation $80, extra fuel $130 over ${en.contract.lead_time_days} days) and restores supply by ${fdate(c.restore_by)}. Buying now costs ${usd(b.residual_cost)} and restores it by ${fdate(b.restore_by)}.`,
  why:`Local repair (${usd(o('MTO-INV-LOCAL').cost)}) opens the unit and voids the warranty. Doing nothing loses the notice deadline on ${fdate(en.notice_deadline)}.`,
  prevents:`The rice-huller connection depends on this inverter, and the cooperative’s letter of intent lapses on 30 Nov unless extended. Buying now only wins with a budget of at least $6,430 and if the cooperative will not extend.`,
  prove:[['Operation','Inverter 2 back in service by the restore date; daytime capacity restored'],['Money','Supplier delivers the replacement unit; our cost stays at the residual'],['Attribution','Not needed: a repair, not a saving']],
  records:['Installer certificate, ambient log, firmware record and fault log (on file)','Warranty contract with the notice clause','Shipping and installation invoices'],
  sensitivity:MANIFEST.tenants[0].portfolio.allocation.sensitivity.slice(0,1).map(x=>'With a budget of $6,430 or more and no extension of the letter of intent, buying now replaces the warranty-and-wait path (see Plan and budget).')};},
 'mto-demand':()=>{const hu=o('MTO-HULLER'),w=o('MTO-WELDING'),he=hu.economics,we=w.economics;return{
  happened:`The Mto Farmers Cooperative has signed a letter of intent for a ${hu.load.kw} kW rice huller, ${hu.load.window}, ${hu.load.days_per_month} days a month (${num(hu.load.kwh_month)} kWh). A welding workshop asked, verbally, for ${w.load.kw} kW in the evening.`,
  matters:`Huller: ${usd(he.revenue_monthly)} a month in sales, ${usd(he.fuel_monthly)} fuel, ${usd(he.collection_cost_monthly)} collection cost: ${usd(he.net_monthly)} net a month, ${usd(he.net_12m)} over 12 months after a ${usd(he.one_off)} connection.`,
  why:`Evening welding runs on diesel for every kWh: ${usd(we.revenue_monthly)} in sales against ${usd(we.fuel_monthly)} fuel, ${usd(we.net_monthly)} a month. It breaks even only at $${w.break_even_tariff_usd_per_kwh}/kWh, and there is no contract.`,
  prevents:`The huller needs inverter 2 restored first. On ${hu.forward_replay.days_without_headroom} days a month there is not enough solar: ${hu.forward_replay.kwh_from_battery_or_genset} kWh comes from the battery or generator, ${hu.forward_replay.extra_fuel_l} L of fuel (already in the fuel cost).`,
  prove:[['Operation','Huller metered kWh each month against the planned load'],['Money','Billed and collected huller sales against the modelled monthly figure'],['Attribution','Direct: a new metered customer']],
  records:['Signed supply contract','Meter register','Customer billing export','Mobile-money settlement statement'],
  sensitivity:['If the huller contract is not signed, the huller drops out; the inverter warranty path is still recommended.']};},
 'mto-billing':()=>{const bi=o('MTO-BILLING').economics,a=s.period.actual;return{
  happened:`Six customers’ meters were swapped on 3 Oct, but billing was not updated: ${a.unbilled_mapping_kwh} kWh was delivered and metered but not billed. A further ${a.unexplained_kwh} kWh is not explained after expected losses.`,
  matters:`Fixing the records restores ${usd(bi.charges_monthly)} a month of charges (${usd(bi.charges_12m)} over 12 months). October’s ${usd(bi.back_bill_oct_potential)} can be back-billed. Billed is not collected: collection is a separate step.`,
  why:`The ${a.unexplained_kwh} kWh is deliberately not priced: it may be meter error and is not assumed to be theft or collectible. A meter check costs ${usd(o('MTO-METER-AUDIT').cost)} from the routine maintenance budget.`,
  prevents:'No crew visit is needed for the billing fix; the meter check rides on the inverter visit.',
  prove:[['Operation','Next bill run includes the 6 customers; unexplained kWh falls after the meter check'],['Money','Charges appear in the November billing export; collections tracked separately'],['Attribution','Direct: records corrected for named meters']],
  records:['Meter register with effective dates','Customer billing export','Mobile-money settlement statement'],
  sensitivity:['Charges restored are listed, never added to the modelled plan total.']};},
 'mwea-demand':()=>{const ag=o('MWEA-AGG'),ae=ag.economics,a=P.actual;return{
  happened:`Mwea was ${a.occupancy_pct}% full in October against a ${P.plan.occupancy_pct}% plan: ${num(a.crate_days)} crate-days instead of ${num(P.plan.crate_days)}. It earns least per crate-day.`,
  matters:`Energy is what the room should use at this occupancy: ${num(a.kwh)} kWh against ${num(a.kwh_model)} kWh expected (+0.6%). The cost per crate-day is high because the room is underused, not because the equipment is failing.`,
  why:`A new compressor (${usd(o('MWEA-COMPRESSOR').capex)}) fixes nothing. The aggregator contract (150 crates, Dec to Mar, at $0.18) nets a modelled ${usd(ae.net_monthly)} a month, ${usd(ae.net_contract)} over ${ae.months} months after ${usd(ae.one_off)} set-up.`,
  prevents:`${ag.compatibility[0].toUpperCase()+ag.compatibility.slice(1)}. The contract is still a draft.`,
  prove:[['Operation','Crate-days per month from the storage ledger'],['Money','Aggregator invoices paid'],['Attribution','Direct: a named customer’s crates']],
  records:['Storage ledger (check-in and check-out per batch)','Invoices and receipts','Draft aggregator contract'],
  sensitivity:['If the contract is not signed, Mwea stays as it is; doing nothing is acceptable because nothing is broken.']};},
 'thika-backup':()=>{const inc=s.incident,b=inc.batches[0];return{
  happened:`On 14 Oct the grid failed ${inc.grid_outage}. The backup transfer switch controller faulted; staff started the generator by hand at 04:05. The chamber was above 8 °C for ${inc.chamber.minutes} minutes (peak ${inc.chamber.peak_c} °C).`,
  matters:`One tomato batch (${b.crates} crates, ${usd(b.exposed_value)} of the customer’s produce) was exposed: that is exposure, not a loss. Inspection downgraded ${6} crates and we compensated ${usd(b.liability)} (credit note CN-0412).`,
  why:`The contractor has accepted the claim and will replace the controller on ${fdate(s.entitlement.remedy_scheduled)}. Night cover until then costs ${usd(o('THIKA-EPC-STOPGAP').residual_cost)} (SMS alarm relay $40, labour $60). Fitting a controller ourselves (${usd(o('THIKA-SELF').cost)}) voids the contractor’s cover.`,
  prevents:'Two night outages happened in October; waiting leaves stock unprotected for two more nights.',
  prove:[['Operation','Controller replaced; the next backup test and the next outage switch over automatically'],['Money','No further compensation credit notes'],['Attribution','Direct: a repaired component']],
  records:['Chamber temperature log','Quality inspection notes','Credit notes','Storage ledger','Contractor and insurance documents'],
  sensitivity:['Insurance does not change the choice: the $108 loss is below the $500 deductible.']};},
 'kirinyaga-energy':()=>{const rp=o('KIRI-REPAIR'),rl=o('KIRI-REPLACE'),a=P.actual;return{
  happened:`Kirinyaga was ${a.occupancy_pct}% full, as planned, but used ${num(a.kwh)} kWh against ${num(a.kwh_model)} kWh expected at that occupancy: 970 kWh (24%) more.`,
  matters:`That costs ${usd(-s.period.bridge[0].amount)} a month at $0.20 per kWh.`,
  why:`Cleaning the condenser and repairing the leak (${usd(rp.cost)}) should recover 80% (60–90%): ${usd(rp.economics.monthly)} a month, ${usd(rp.economics.net_12m)} over 12 months. Replacement (${usd(rl.capex)}) recovers ${usd(rl.economics.monthly)} a month but is ${usd(rl.economics.net_12m)} over 12 months.`,
  prevents:'One technician visit in November.',
  prove:[['Operation','Energy back within the 5% model tolerance at the same occupancy and temperature'],['Money','Electricity invoice for the room against the modelled monthly figure'],['Attribution','Compared with Mwea and Thika as rooms without the repair (proposed in this mock-up)']],
  records:['Hourly energy meter readings','Storage ledger (occupancy)','Electricity invoices'],
  sensitivity:['If verified recovery after the repair is below 60%, replacement is reconsidered.']};},
 'embakasi-schedule':()=>{const dl=o('EMB-DEADLINE'),ch=o('EMB-CHEAPEST'),a=P.actual;return{
  happened:`All ${num(a.departures_met)} departures left on time, but ${pct(a.peak_share,0)} of charging was at peak price (plan ${pct(P.plan.peak_share,0)}) and the monthly peak reached ${a.max_kw} kW (plan ${P.plan.max_kw} kW). Charging cost ${usd(a.energy_cost)} against ${usd(P.plan.energy_cost)} planned.`,
  matters:`Charging to each departure time costs a modelled ${usd(dl.economics.energy_cost_monthly)} a month: ${usd(dl.economics.saving_monthly)} less, ${usd(dl.economics.net_12m)} over 12 months after ${usd(dl.economics.one_off)} set-up.`,
  why:`Charging only 00:00–05:00 is cheapest but delivers ${num(ch.deliverable_kwh)} kWh of the ${num(ch.required_kwh)} kWh needed each night: ${ch.buses_short} buses leave short. It is rejected.`,
  prevents:'The tariff is an assumption until confirmed from the utility invoice. A supervised 14-day schedule comes first.',
  prove:[['Operation','Peak share and monthly peak fall; every departure still met (14 supervised days)'],['Money','Utility invoice time-of-use and demand lines against the modelled figure'],['Attribution','Kasarani is on a flat tariff, so not comparable; Ruiru as the comparison depot (proposed in this mock-up)']],
  records:['Utility invoice with time-of-use and demand lines','Charger session log','Fleet roster (departure times and required charge)'],
  sensitivity:['If the invoice shows a different tariff, the saving is recomputed before approval.']};},
 'kasarani-charger':()=>{const inc=s.incident,n=inc.november_to_date;return{
  happened:`Charger 2 failed on 1 Nov (welded contactor). The remaining chargers deliver ${num(inc.capacity_after.deliverable_kwh)} kWh of the ${num(inc.capacity_after.required_kwh)} kWh needed: one bus short each night. ${n.missed_departures} departures missed so far in November, ${usd(n.penalties)} in penalties.`,
  matters:`Each missed block costs ${usd(n.penalty_per_missed_block)}. Waiting for the repair is likely to miss 2 more (${usd(o('KAS-OEM-WAIT').expected_penalties)}).`,
  why:`Charging one bus at Ruiru overnight costs ${usd(o('KAS-OEM-STOPGAP').residual_cost)} (overtime $70, energy $20). Local repair (${usd(o('KAS-LOCAL').cost)}) voids the power-stage warranty. A schedule change saves nothing on a flat tariff.`,
  prevents:`The manufacturer must restore the charger by ${fdate(s.entitlement.sla_clock.restore_due)} under the service agreement.`,
  prove:[['Operation','Every Kasarani departure met each night until and after the repair'],['Money','No further penalties'],['Attribution','Direct']],
  records:['Charger status log','Vendor service tickets','Fleet roster'],
  sensitivity:['If the repair slips past the restore date, the stop-gap continues and service credits may apply (not counted as money).']};},
 'ruiru-expansion':()=>{const a6=o('RUI-ABSORB6'),a10=o('RUI-ABSORB10');return{
  happened:`Ruiru’s chargers were in use ${pct(P.actual.charger_hour_utilisation,0)} of charger-hours in October. The city offers a route expansion.`,
  matters:`With 6 more buses, Ruiru needs ${num(a6.required_kwh)} kWh a night against ${num(a6.deliverable_kwh)} kWh it can deliver, with no new chargers. That avoids a modelled ${usd(a6.avoided_capex)} purchase: an avoided cost, not a saving in the books.`,
  why:`Ten more buses need ${num(a10.required_kwh)} kWh: more than the ${s.physical.import_limit_kw} kW import limit allows. Four more chargers (${usd(o('RUI-4CHARGERS').capex)}) are not needed for 6 and not enough alone for 10.`,
  prevents:'Connector compatibility must be confirmed for the 6 new buses.',
  prove:[['Operation','All Ruiru departures met after the 6 buses join; peak import stays under the limit'],['Money','Utility invoices for the extra charging'],['Attribution','Direct']],
  records:['Fleet roster for the new route','Charger session log','Utility invoice'],
  sensitivity:['Ten buses would need a grid upgrade (about $45,000, an assumption) plus chargers: not modelled in this plan.']};}
 };
 return T[d.id]();
}

/* ---------- contract rights (entitlement) ---------- */
const STAGES=['Potential','Evidence assembled','Notified','Acknowledged','Accepted, denied or disputed','Remedy delivered','Credit booked','Cash received'];
const STAGE_IX={NONE:-1,POTENTIAL:0,EVIDENCE_ASSEMBLED:1,NOTIFIED:2,ACKNOWLEDGED:3,ACCEPTED:4,DENIED:4,DISPUTED:4,REMEDY_DELIVERED:5,CREDIT_BOOKED:6,CASH_RECEIVED:7};
function rights(key){
 const k=siteM('kobo'),ks=siteM('kisiwa'),m=siteM('mto'),th=siteM('thika'),ka=siteM('kasarani'),ru=siteM('ruiru');
 const R={
 'kobo-battery':()=>{const e=k.entitlement;return{site:'kobo',asset:'Kobo battery',who:e.contract.counterparty,type:'Equipment warranty',until:e.contract.term_end,state:e.claim_state,elig:['Not enough evidence yet','amber'],
  terms:['Lowest battery charge at least 10%','Cell temperature at most 45 °C','Charge and discharge at most half the capacity per hour','Capacity at least 95% at year 3 (interim guarantee)','Capacity at least 70% at the end of the term'],evidence:[['Temperature record','Missing'],['Commissioning capacity test','Missing'],['Cycles used',e.evidence.cycles],['Energy throughput',e.evidence.throughput]],
  deadline:null,deadlineNote:'No notice clock is running: no claim has been made.',paths:['BAT-EVIDENCE','BAT-CLAIM-NOW','BAT-NOACT'],
  listed:[['Cover on the battery',usd(MANIFEST.tenants[0].portfolio.allocation.listed_not_summed['BAT-001_cover_exposure']),'Exposure we protect, not money gained','port:lakeside:listed:cover']],path:`${sitePath('kobo')}.entitlement`};},
 'kisiwa-genset':()=>{const e=ks.entitlements[0];return{site:'kisiwa',asset:'Kisiwa generator 1',who:e.contract.counterparty,type:'Equipment warranty',until:e.contract.term_end,state:e.claim_state,elig:['Expired and condition not met','red'],
  terms:[`Requires the ${e.contract.condition}`],evidence:[['Run hours at failure',num(e.evidence.run_hours_at_failure)],['1,000-hour service record','Missing']],
  deadline:null,deadlineNote:`The warranty ended on ${fdate(e.contract.term_end)}. No claim is possible; we fund the repair (${usd(e.operator_funded)}).`,paths:['KIS-REPAIR','KIS-REPLACE'],listed:[],path:`${sitePath('kisiwa')}.entitlements[0]`};},
 'kisiwa-om':()=>{const e=ks.entitlements[1];return{site:'kisiwa',asset:'Operations and maintenance contract',who:e.contract.counterparty,type:'Service agreement (response time)',until:null,state:e.claim_state,elig:['Review required','amber'],
  terms:[`Response within ${e.contract.response_hours} hours`,`Service credit: ${e.contract.service_credit}`,`Exception: ${e.contract.exclusion}`],
  evidence:[['Reported',e.occurrence.reported.replace('T',' ').slice(0,16)],['Responded',e.occurrence.responded.replace('T',' ').slice(0,16)],['Response time',`${e.occurrence.response_hours} hours`],['Weather',e.evidence.weather_log]],
  deadline:null,deadlineNote:'Notice period: not available yet (the contract extraction does not state one).',paths:[],
  listed:[['Possible service credit',usd(e.potential_credit),'Not counted until a credit note arrives','port:lakeside:listed:credit']],path:`${sitePath('kisiwa')}.entitlements[1]`};},
 'mto-inverter':()=>{const e=m.entitlement;return{site:'mto',asset:'Mto inverter 2',who:e.contract.counterparty,type:'Equipment warranty',until:e.contract.term_end,state:e.claim_state,elig:['Potentially covered','green'],
  terms:[...e.contract.conditions.map(c=>c[0].toUpperCase()+c.slice(1)),`Remedy: ${e.contract.remedy}`,`Notice within ${e.contract.notice_days} days; replacement in about ${e.contract.lead_time_days} days`],
  evidence:[['Installer certificate','On file'],['Ambient temperature',e.evidence.ambient_log.replace(/ C\b/g,' °C')],['Firmware','Current'],['Fault log','On file']],
  deadline:e.notice_deadline,deadlineNote:'Notice deadline for the warranty claim.',paths:['MTO-INV-CLAIM','MTO-INV-BUYNOW','MTO-INV-LOCAL','MTO-INV-NOACT'],listed:[],path:`${sitePath('mto')}.entitlement`};},
 'thika-ats':()=>{const e=th.entitlement;return{site:'thika',asset:'Thika transfer switch controller',who:e.contract.counterparty,type:'Contractor workmanship warranty',until:e.contract.term_end,state:e.claim_state,elig:['Accepted by the contractor','green'],
  terms:[`Condition: ${e.contract.conditions[0]}`,`Notice within ${e.contract.notice_days} days`,`Remedy: ${e.contract.remedy}`],evidence:[['Quarterly backup tests',e.evidence.quarterly_tests],['Event log','On file']],
  events:e.claim_events,deadline:e.remedy_scheduled,deadlineNote:'Contractor’s scheduled replacement date.',paths:['THIKA-EPC-STOPGAP','THIKA-EPC-WAIT','THIKA-SELF'],listed:[],path:`${sitePath('thika')}.entitlement`};},
 'thika-insurance':()=>{const i=th.incident.insurance;return{site:'thika',asset:'Stock in our custody',who:'Insurer',type:'Goods-in-custody insurance',until:null,state:'NOTIFIED',stopped:'Not filed',elig:['Below the deductible','neutral'],
  terms:[`Deductible ${usd(i.deductible)}`,`Notice within ${i.notice_days} days`],evidence:[['Notified',fdate(i.notified)],['Confirmed loss',usd(th.incident.batches[0].confirmed_damage)],['Reimbursement recorded',usd(i.reimbursement_recorded)]],
  events:[{state:'NOTIFIED',at:i.notified}],deadline:null,deadlineNote:'Notice was given in time; no claim filed because the loss is below the deductible.',
  pathsText:[['File a claim',`$0 back: the ${usd(th.incident.batches[0].confirmed_damage)} loss is below the ${usd(i.deductible)} deductible`],['Do not file (chosen)',`${usd(th.incident.batches[0].liability)} compensation stays with us`]],listed:[],path:`${sitePath('thika')}.incident.insurance`};},
 'kasarani-charger':()=>{const e=ka.entitlement;return{site:'kasarani',asset:'Kasarani charger 2',who:e.contracts[0].counterparty,type:'Equipment warranty and service agreement',until:e.contracts[0].term_end,state:e.claim_state,elig:['Covered part (power stage)','green'],
  terms:[`Covers ${e.contracts[0].covers}`,`Exception: ${e.contracts[0].exclusion}`,`Response within ${e.contracts[1].response_hours} hours; restore within ${e.contracts[1].restore_business_days} business days`,`Service credit: ${e.contracts[1].service_credit}`],
  evidence:[['Responded within',`${e.sla_clock.responded_within_hours} hours`],['Restore due',fdate(e.sla_clock.restore_due)],['Clock','Running']],events:e.claim_events,
  deadline:e.sla_clock.restore_due,deadlineNote:'Restore deadline under the service agreement.',paths:['KAS-OEM-STOPGAP','KAS-OEM-WAIT','KAS-LOCAL'],
  listed:[['Possible service credit if late','5% of the $400 monthly fee per business day late','Not counted until a credit note arrives','']],path:`${sitePath('kasarani')}.entitlement`};},
 'ruiru-connector':()=>{const e=ru.incident;return{site:'ruiru',asset:'Ruiru charger 7, connector 2',who:e.entitlement.counterparty,type:'Equipment warranty',until:null,state:e.entitlement.claim_state,elig:['Low priority','neutral'],
  terms:['Connector out of service since 29 Oct; connector 1 on the same charger works'],evidence:[['Effect on departures','None in the replay']],
  deadline:null,deadlineNote:'Plan: claim at the next routine visit. No departure is affected.',paths:[],listed:[],path:`${sitePath('ruiru')}.incident`};}
 };
 return R[key]();
}
function claimTimeline(r){
 const cur=STAGE_IX[r.state]??-1,ev={};(r.events||[]).forEach(x=>ev[STAGE_IX[x.state]]={at:x.at,label:x.state==='ACCEPTED'?'Accepted':null});
 return `<ol class="d-steps" aria-label="Claim stage">${STAGES.map((st,i)=>{const done=i<cur||(i===cur&&cur>=0),now=i===cur;const lab=i===4&&ev[4]?.label?ev[4].label:st;
  return `<li class="${done?'done':''} ${now?'now':''}" ${now?'aria-current="step"':''}><span class="dot" aria-hidden="true"></span><b>${lab}</b><small>${ev[i]?fdate(ev[i].at):now?'Current stage':i>cur&&r.stopped&&i===cur+1?r.stopped:''}</small></li>`;}).join('')}</ol>${cur<0?`<p class="d-note">No claim stage applies: ${r.deadlineNote}</p>`:''}`;
}
function rightsPanel(key){
 const r=rights(key);const dl=r.deadline?daysUntil(r.deadline):null;
 const paths=r.pathsText?table(['Path','Cost to us'],r.pathsText):r.paths.length?table(['Path','Cost to us'],r.paths.map(id=>[OPT_LABEL[id],optCost(OPT[id])[0]])):'';
 return `<section class="panel d-rights" aria-labelledby="r-${key}"><div class="panel-head"><div><div class="eyebrow">Contract rights</div><h2 id="r-${key}">${r.asset} · ${r.type}</h2><p>${r.who}${r.until?` · cover to ${fdate(r.until)}`:''}</p></div>${badge(r.elig[0],r.elig[1])}</div>
 ${claimTimeline(r)}
 <div class="d-grid2"><div><h3>What the contract says</h3><ul class="d-list">${r.terms.map(t=>`<li>${t}</li>`).join('')}</ul><button class="claim-link" data-evd="clause:${key}">Contract clause and page reference ↗</button></div>
 <div><h3>Evidence we hold</h3>${kv(r.evidence)}</div></div>
 <div class="d-deadline ${dl!==null&&dl<=7?'soon':''}">${icon('clock')}<div>${dl!==null?`<strong>${dl} days left</strong> · ${fdate(r.deadline)} · `:''}${r.deadlineNote}</div></div>
 ${paths?`<h3>Cost to us under each path</h3>${paths}`:''}
 ${r.listed.length?`<h3>Listed, never counted as money gained</h3>${table(['Item','Amount','Treatment'],r.listed.map(([a,b,c,k])=>[a,k?`<button class="d-money" data-evd="${k}">${b}${vh(' – show source records')}</button>`:b,c]))}`:''}
 <p class="d-legal">This is not a legal decision. Coverage is decided by the supplier or insurer.</p></section>`;
}

/* ---------- option helpers ---------- */
function optCost(o){
 if(o.capex!==undefined)return [o.capex===0?'$0':usd(o.capex),'Capital purchase'];
 if(o.cost!==undefined)return [usd(o.cost),'One-off cost'];
 if(o.residual_cost!==undefined)return [usd(o.residual_cost),'Cost to us after the supplier’s remedy'];
 if(o.economics?.one_off!==undefined)return [usd(o.economics.one_off),'One-off set-up'];
 if(o.kind==='NO_ACTION')return ['$0','No spend'];
 if(o.kind==='COMMERCIAL_CORRECTION')return ['$0','Office work'];
 return ['Not costed','Rejected before costing'];
}
function optEffect(o){
 const e=o.economics||{};
 if(e.net_12m!==undefined)return [usd(e.net_12m,true),'12-month net'];
 if(o.net_12m!==undefined)return [usd(o.net_12m,true),'12-month net'];
 if(e.net_contract!==undefined)return [usd(e.net_contract,true),`net over the ${e.months}-month contract`];
 if(e.charges_12m!==undefined)return [usd(e.charges_12m,true),'charges restored over 12 months (billed, not yet collected)'];
 if(e.net_monthly!==undefined)return [usd(e.net_monthly,true)+' a month','monthly net'];
 if(e.monthly!==undefined)return [usd(e.monthly,true)+' a month','continues every month'];
 if(e.energy_cost_monthly!==undefined)return [usd(e.energy_cost_monthly)+' a month','charging cost continues'];
 if(o.avoided_capex!==undefined)return [usd(o.avoided_capex),'capital not spent (avoided cost, not a saving)'];
 if(o.expected_penalties!==undefined)return [usd(-o.expected_penalties),'likely further penalties'];
 if(o.effectMonthly!==undefined)return [usd(o.effectMonthly)+' a month','charges stay unbilled'];
 if(o.monthly_net===0)return ['$0 change',`avoidable fuel keeps being spent (${usd(262.5)} a month)`];
 if(o.kind==='NO_ACTION')return ['$0 change','no effect'];
 if(['REPAIR','SUPPLIER_REMEDY','STOPGAP_PLUS_CLAIM','INVESTIGATION'].includes(o.kind))return ['No saving claimed','a cost to keep service or evidence'];
 return ['Not modelled','no money effect modelled'];
}
function optEvidence(o){const c=o.economics?.class||o.avoided_capex_class;if(c)return CLASS[c]?.[0]||c;if(o.kind==='NO_ACTION')return 'Baseline';if(o.residual_cost!==undefined||o.cost!==undefined||o.capex!==undefined)return 'Quoted cost';if(o.expected_penalties!==undefined)return 'Recorded penalty rate';return '—';}
function optSafeguards(o){
 const sg=o.safeguards||(o.safeguard?[o.safeguard]:[]);
 if(!sg.length){if(o.id==='KIS-NOACT')return `<span class="d-sg fail">${icon('finding')}Fails: evening supply obligation</span>`;return '<span class="muted">None applies</span>';}
 return sg.map(x=>x.mode==='COSTED_TRADEOFF'?`<span class="d-sg cost">${icon('money')}Costed: ${SAFEGUARD[x.policy]} ${usd(x.cost_monthly)} a month</span>`:`<span class="d-sg ${x.result==='PASS'?'pass':'fail'}">${icon(x.result==='PASS'?'check':'finding')}${x.result==='PASS'?'Pass':'Fails'}: ${SAFEGUARD[x.policy]}</span>`).join('');
}
/* Plain-language rewrites of manifest reason strings that carry codes or symbols (meaning unchanged; see CHANGE-REGISTER). */
const TEXTFIX = {
 '6,430 needed with everything else; budget 5,000':'Needs $6,430 with everything else; the budget is $5,000',
 'wins if budget >= 6,430 and the cooperative will not extend its letter of intent':'Only if the budget is at least $6,430 and the cooperative will not extend its letter of intent',
 'fails the evening service obligation (P1 hard constraint) on a single genset':'Fails the evening supply obligation: one generator cannot be relied on alone',
 'LOI converts to supply contract; inverter INV-MT-02 restored first':'The letter of intent becomes a supply contract, and inverter 2 is restored first',
 'flat tariff: no schedule saving exists (EV-L1 immaterial here)':'Flat tariff: changing the schedule saves nothing here',
 'protects the right to claim; covered asset value 64,000 is EXPOSURE, not money gained':'Protects the right to claim; the $64,000 of covered battery value is exposure, not money gained',
 'every evening kWh is diesel; margin negative at 0.40 and no demand evidence':'Every evening kWh is diesel: the margin is negative at $0.40/kWh and there is no demand evidence',
 'fails dawn adequacy safeguard':'Fails the safeguard: battery below 35% at 5 am on some replayed days',
 'not needed for +6; insufficient alone for +10 (grid upgrade ~45,000 [assumption])':'Not needed for 6 more buses; not enough alone for 10 (a grid upgrade of about $45,000 would also be needed, an assumption)',
 'repair restores redundancy for 1,800':'Repair restores the backup for $1,800',
 'over budget; payback ~6 years':'Over budget; payback about 6 years',
 'exceeds the 400 kW import limit':'Exceeds the 400 kW grid import limit',
 'connector compatibility confirmed for the 6 new buses':'Connector compatibility confirmed for the 6 new buses'};
const PLAIN = [[' (forward-feasible share of Candidate fuel)',' (the share a forward replay shows is avoidable)'],[' (Candidate by dispatch-3.2, not avoidable by forward replay)',' (beyond need, but not avoidable in the replay)'],[' (Necessary)',' (needed)'],['; investigate (MG-L5)','; being investigated'],['all generator time Necessary','all generator time needed'],
 ['Candidate generator minutes down >= 50% on comparable days; MG-5 dawn SOC >= 35% every day','Generator time beyond need down by at least half on comparable days; battery at least 35% at 5 am every day'],
 ['comparability bands PV +/-10%, load +/-10%; Kisiwa/Mto as non-treated controls','Compared on days with similar solar and load (within 10%); Kisiwa and Mto as sites without the change'],
 ['14 matched days before change (Sep 29 - Oct 12 class days)','14 matched days before the change (29 Sep to 12 Oct)'],['14 days after apply','14 days after the change'],[' x ',' × '],['fuel consumed (dips + deliveries) per delivered kWh, weather-normalised, vs baseline','Fuel used (tank dips and deliveries) per delivered kWh, adjusted for weather, against the days before']];
const pt = t => PLAIN.reduce((a,[f,r])=>a.split(f).join(r),String(t??''));
const fx = t => {if(!t)return '';const v=TEXTFIX[t]||t;return v[0].toUpperCase()+v.slice(1);};
const dispBadge = d => {const [t,c]=DISP[d]||[d,''];return badge(t,c);};
function optWhy(o){if(o.disposition==='CONDITIONAL')return fx(o.condition);return fx(o.reason)||o.condition&&`Condition: ${fx(o.condition)}`||fx(o.note)||'';}

/* ---------- charts (inline SVG, text alternatives, not colour alone) ---------- */
let svgUid=0;
const PATTERNS = id => `<defs><pattern id="hatch-${id}" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="8" height="8" fill="#fff"/><rect width="3.5" height="8" fill="currentColor"/></pattern><pattern id="dots-${id}" width="6" height="6" patternUnits="userSpaceOnUse"><rect width="6" height="6" fill="#fff"/><circle cx="3" cy="3" r="1.4" fill="currentColor"/></pattern></defs>`;
function barSvg(x0,x1,dom,cls,tone,label){
 const id=++svgUid,sc=v=>(v-dom[0])/(dom[1]-dom[0])*1000,a=sc(Math.min(x0,x1)),b=sc(Math.max(x0,x1)),w=Math.max(b-a,3),z=sc(0);
 const fill=cls==='mod'?`url(#hatch-${id})`:cls==='unx'?`url(#dots-${id})`:'currentColor';
 return `<svg class="d-bar tone-${tone}" viewBox="0 0 1000 22" preserveAspectRatio="none" role="img" aria-label="${escapeHtml(label)}"><title>${escapeHtml(label)}</title>${PATTERNS(id)}${dom[0]<0?`<line x1="${z}" x2="${z}" y1="0" y2="22" stroke="#8a94a6" stroke-width="2"/>`:''}<rect x="${a}" y="3" width="${w}" height="16" rx="2" fill="${fill}" stroke="currentColor" stroke-width="${cls==='unx'?2:1}" ${cls==='unx'?'stroke-dasharray="6 4"':''}/></svg>`;
}
function chartLegend(items){return `<div class="d-legend">${items.map(([t,cls,tone])=>`<span><svg viewBox="0 0 22 14" class="tone-${tone}" aria-hidden="true">${PATTERNS('lg'+cls+tone)}<rect x="1" y="1" width="20" height="12" rx="2" fill="${cls==='mod'?`url(#hatch-lg${cls}${tone})`:cls==='unx'?`url(#dots-lg${cls}${tone})`:'currentColor'}" stroke="currentColor" ${cls==='unx'?'stroke-dasharray="3 2"':''}/></svg>${t}</span>`).join('')}</div>`;}
function planActualChart(op){
 const o=OPS[op],cost=o.kind==='cost',f=cost?'energy_cost':'contribution';
 const rows=o.sites.map(sk=>{const P=siteM(sk).period;const pl=cost?(P.plan.total??P.plan.energy_cost):P.plan.contribution,ac=cost?(P.actual.total??P.actual.energy_cost):P.actual.contribution;return [sk,pl,ac];});
 const vals=rows.flatMap(r=>[r[1],r[2]]),dom=[Math.min(0,...vals)*1.1,Math.max(...vals)*1.08];
 const title=`${cost?'Charging and depot cost':'Contribution'} by site, plan against actual, October 2026`;
 return `<figure class="d-chart" aria-labelledby="pa-${op}"><figcaption id="pa-${op}"><strong>${title}</strong></figcaption>${chartLegend([['Plan','solid','plan'],['Actual','solid','actual']])}
 ${rows.map(([sk,pl,ac])=>`<div class="d-crow"><a class="d-clabel" href="#/econ-${sk}">${siteName(sk)}</a><div class="d-ctrack">${barSvg(0,pl,dom,'solid','plan',`${siteName(sk)} plan ${usd(pl)}`)}${barSvg(0,ac,dom,'solid','actual',`${siteName(sk)} actual ${usd(ac)}`)}</div><div class="d-cval"><span>Plan ${usd(pl)}</span><span><b>Actual ${usd(ac)}</b></span></div></div>`).join('')}
 <details class="d-table"><summary>Show as a table</summary>${table(['Site','Plan','Actual','Difference'],rows.map(([sk,pl,ac])=>[siteName(sk),usd(pl),usd(ac),usd(r2(ac-pl),true)]))}</details></figure>`;
}
function bridgeRows(op){
 const o=OPS[op],cost=o.kind==='cost',P=o.t.portfolio;let run=cost?P.plan_cost:P.plan_contribution;const rows=[{label:'Plan',total:true,from:0,to:run,value:run}];
 o.sites.forEach(sk=>{const s=siteM(sk),br=s.period.bridge||[];
  br.forEach((b,i)=>{const amt=cost?-b.amount:b.amount;rows.push({site:sk,label:DRIVER[b.driver]||b.driver,from:run,to:r2(run+amt),value:amt,cls:b.class,basis:pt(b.basis),key:`bridge:${sk}:${i}`});run=r2(run+amt);});
  if(!br.length&&s.period.variance){const amt=cost?-s.period.variance:s.period.variance;rows.push({site:sk,label:'Not broken down yet (no driver lines recorded)',from:run,to:r2(run+amt),value:amt,cls:'DERIVED',basis:'Site difference from plan with no driver lines in the fixture',key:`line:${sk}:variance`});run=r2(run+amt);}});
 rows.push({label:'Actual',total:true,from:0,to:run,value:run});return rows;
}
function waterfall(op){
 const o=OPS[op],cost=o.kind==='cost',rows=bridgeRows(op),dom=[0,Math.max(...rows.map(r=>Math.max(r.from,r.to)))*1.04];
 const worse=v=>cost?v>0:v<0;const P=o.t.portfolio;
 const desc=`Starts at plan ${usd(rows[0].value)} and ends at actual ${usd(rows.at(-1).value)}. ${rows.length-2} steps by site and driver; hatched steps are modelled, dotted steps are not explained yet, solid steps are recorded.`;
 return `<figure class="d-chart d-wf" aria-labelledby="wf-t-${op}" aria-describedby="wf-d-${op}"><figcaption id="wf-t-${op}"><strong>From plan to actual ${cost?'cost':'contribution'}, October 2026</strong></figcaption><p id="wf-d-${op}" class="d-note">${desc}</p>
 ${chartLegend([['Recorded','solid','neutral'],['Modelled','mod','neutral'],['Not explained yet','unx','neutral'],[cost?'Cost higher than plan':'Worse than plan','solid','worse'],[cost?'Cost lower than plan':'Better than plan','solid','better']])}
 <div class="d-wfrows">${rows.map(r=>{const cls=r.total?'solid':(CLASS[r.cls]?.[1]==='mod'?'mod':CLASS[r.cls]?.[1]==='unx'?'unx':'solid'),tone=r.total?'total':worse(r.value)?'worse':'better',klab=r.total?'':CLASS[r.cls]?.[0]||'';
  const lab=`${r.site?siteName(r.site)+' · ':''}${r.label}`,aria=`${lab}: ${usd(r.value,!r.total)}${klab?' · '+klab:''}`;
  const inner=`<span class="d-wflabel">${r.site?`<small>${siteName(r.site)}</small>`:''}${r.label}</span>${barSvg(r.from,r.to,dom,cls,tone,aria)}<span class="d-wfval">${usd(r.value,!r.total)}${klab?`<small>${klab}</small>`:''}</span>`;
  return r.site?`<a class="d-wfrow" href="#/econ-${r.site}">${inner}</a>`:`<div class="d-wfrow total">${inner}</div>`;}).join('')}</div>
 <details class="d-table"><summary>Show as a table</summary>${table(['Site','Driver','Amount','Evidence','Basis'],rows.filter(r=>!r.total).map(r=>[siteName(r.site),r.label,usd(r.value,true),CLASS[r.cls]?.[0]||'',r.basis]))}</details></figure>`;
}

/* ---------- shared page parts ---------- */
const ROLE_Q = {CEO:'Which sites and investments create the best returns from existing capital?',COO:'Where should limited crews work, and which changes are physically feasible?',CFO:'Why is performance off plan, which amounts are actual or estimated, and what may be recoverable?',CCO:'Which demand can be sold profitably, and what limits it?'};
const ROLE_ORDER = {CEO:['first','sites','demand','why','rights','crew','coverage'],COO:['crew','first','sites','rights','why','demand','coverage'],CFO:['coverage','why','rights','first','sites','demand','crew'],CCO:['demand','first','sites','why','rights','crew','coverage']};
function dtabs(s){const op=s.op;return tabRow([['Decision home',`decide-${op}`],['Why off plan',`bridge-${op}`],['Plan and budget',`plan-${op}`],['Proof it worked',`verify-${op}`],['Pilot request',`pilot-${op}`]],s.id);}
function decisionRailGroup(s){const op=s.op||DSTATE.op,k=s.dkind;
 const items=[['Decision home',`decide-${op}`,'grid',['home','econ','choice']],['Why off plan',`bridge-${op}`,'money',['bridge']],['Plan and budget',`plan-${op}`,'action',['plan']],['Proof it worked',`verify-${op}`,'check',['verify']],['Pilot request',`pilot-${op}`,'book',['pilot']]];
 return `<div class="rail-group"><div class="eyebrow">DECISIONS</div>${items.map(([l,id,ic,kinds])=>link(id,`${icon(ic)}${l}`,kinds.includes(k)?'active':'')).join('')}</div>`;}
function decisionShell(s,book=false){
 if(s.op)DSTATE.op=s.op;const o=OPS[s.op];
 const crumbs=[link(`decide-${s.op}`,'Decisions'),link(`decide-${s.op}`,o.name)];if(s.site)crumbs.push(link(`econ-${s.site}`,siteName(s.site)));if(s.crumb)crumbs.push(escapeHtml(s.crumb));
 return `<div class="shell">${rail(s)}<main class="workspace" id="main"><header class="topbar d-topbar"><div class="portfolio-name">${o.name} <span class="muted">/ demo operator · illustrative figures</span></div><div class="right"><label class="d-opswitch">Operator <select id="op-switch" aria-label="Choose operator">${Object.entries(OPS).map(([k,v])=>`<option value="${k}" ${k===s.op?'selected':''}>${v.name}</option>`).join('')}</select></label><span class="d-period">${icon('clock')}October 2026 · books closed 6 Nov</span><span class="avatar">BY</span></div></header>
 <div class="canvas"><div class="breadcrumbs">${crumbs.join('<span>›</span>')}</div><div class="page-heading"><div><div class="title-row"><h1>${s.title}</h1>${badge('Illustrative demo data','outline')}</div><p>${s.subtitle}</p></div></div>${s.dkind==='econ'||s.dkind==='choice'?siteTabs(s):dtabs(s)}${s.render()}${footer()}</div></main></div>`;
}
function siteTabs(s){const o=OPS[s.op];return tabRow([['← Decision home',`decide-${s.op}`],...o.sites.map(sk=>[siteName(sk),`econ-${sk}`])],s.dkind==='econ'?s.id:`econ-${s.site}`);}

/* ---------- decision home ---------- */
function opTotals(op){const o=OPS[op],P=o.t.portfolio;return o.kind==='cost'?{plan:P.plan_cost,actual:P.actual_cost,variance:P.variance}:{plan:P.plan_contribution,actual:P.actual_contribution,variance:P.variance};}
function coverageLine(op){
 if(op==='lakeside'){const c=OPS.lakeside.t.portfolio.coverage;return `<strong><button class="d-money" data-evd="cov:lakeside">${pct(c.cost_recorded_share)}${vh(' – show source records')}</button> of costs from recorded invoices</strong> (${usd(c.cost_recorded_usd)} of ${usd(c.cost_total_usd)}); Kisiwa’s operations and maintenance cost is estimated because October’s invoice has not arrived.`;}
 return `<strong>Coverage: not available yet.</strong> The demo fixture does not state which ${op==='metro'?'cost':'revenue and cost'} lines come from recorded invoices for this operator.${op==='metro'?' Embakasi’s tariff is an assumption until confirmed from the utility invoice.':''}`;
}
const CONTRAST = {
 lakeside:[['Highest diesel use is not where the saving is.',`Kisiwa burned ${num(siteM('kisiwa').period.actual.diesel_l)} L, every hour of it needed. Kobo burned ${num(siteM('kobo').period.actual.diesel_l)} L, and ${siteM('kobo').decision.options[2].forward_replay.avoidable_fuel_l} L a month of it is avoidable with one setting change.`,'kobo-generator','kisiwa-generator'],
  ['Spare solar is not the same as paying demand.',`Mto’s daytime headroom has a signed buyer (rice huller, ${usd(OPT['MTO-HULLER'].economics.net_monthly)} a month net). The evening welding enquiry loses ${usd(-OPT['MTO-WELDING'].economics.net_monthly)} a month because every evening kWh is diesel.`,'mto-demand']],
 harvest:[['The room with the highest cost per crate-day has nothing wrong with it.',`Mwea uses ${num(siteM('mwea').period.actual.kwh)} kWh against ${num(siteM('mwea').period.actual.kwh_model)} expected at 35% occupancy. Busy Kirinyaga uses 24% more energy than its occupancy explains: that is the equipment problem.`,'mwea-demand','kirinyaga-energy'],
  ['Stock exposed is not stock lost.',`At Thika ${usd(siteM('thika').incident.batches[0].exposed_value)} of a customer’s tomatoes were exposed in an outage; inspection confirmed ${usd(siteM('thika').incident.batches[0].confirmed_damage)} of damage, and that is what we owed.`,'thika-backup']],
 metro:[['Every bus left on time, yet charging cost more than planned.',`Embakasi charged ${pct(siteM('embakasi').period.actual.peak_share,0)} at peak prices against a ${pct(siteM('embakasi').period.plan.peak_share,0)} plan. The cheapest schedule is rejected: it leaves 3 buses short every night.`,'embakasi-schedule'],
  ['The quiet depot has room for 6 more buses, not 10.',`Ruiru’s chargers were busy ${pct(siteM('ruiru').period.actual.charger_hour_utilisation,0)} of the time, yet the grid import limit caps it at 6 extra buses. No new chargers are needed for 6.`,'ruiru-expansion']]};
function insightPanel(op){
 const o=OPS[op],t=opTotals(op),cost=o.kind==='cost',P=o.t.portfolio;
 const heroes=cost?[['Plan cost',money$(`port:${op}:plan`,t.plan)],['Actual cost',money$(`port:${op}:actual`,t.actual)],['Over plan',money$(`port:${op}:variance`,-t.variance)],['Departures met',`${num(P.departures_met)} of ${num(P.departures_required)}`,`${usd(P.cost_per_departure_actual)} per departure`]]
  :[['Plan contribution',money$(`port:${op}:plan`,t.plan)],['Actual contribution',money$(`port:${op}:actual`,t.actual)],['Against plan',money$(`port:${op}:variance`,t.variance,true)]];
 return `<section class="panel d-insight"><div class="panel-head"><div><div class="eyebrow">Opening insight · October 2026</div><h2>${cost?'Charging cost against plan: every bus still left on time':'Contribution against plan, by site'}</h2></div>${link(`bridge-${op}`,'Why off plan →')}</div>
 <div class="d-heroes">${heroes.map(([l,v,n])=>`<div class="d-hero"><span>${l}</span><div class="d-herov">${v}</div>${n?`<small>${n}</small>`:''}</div>`).join('')}</div>
 <div class="d-grid2 wide">${planActualChart(op)}<div class="d-contrast">${CONTRAST[op].map(([h,b,...ids])=>`<article><h3>${h}</h3><p>${b}</p><p>${ids.map(id=>link(`choice-${id}`,`${DEC.find(d=>d.id===id).title} →`)).join('<br>')}</p></article>`).join('')}</div></div>
 <div class="d-coverage">${icon('evidence')}<p>${coverageLine(op)}</p></div></section>`;
}
function rankedItems(op){
 const A=OPS[op].t.portfolio.allocation,rec=(A.recommended||[]);
 const items=rec.map(id=>({id,o:OPT[id]}));
 if(op==='lakeside')items.splice(items.length,0);
 return items;
}
function firstPanel(op,focus){
 const o=OPS[op],A=o.t.portfolio.allocation,M=o.t.portfolio_constraints,budget=M.budget_usd_nov_dec,crew=M[o.crewKey];
 const used=A.crew_visits_used??A.technician_visits_used;
 const rec=A.recommended.map((id,i)=>{const x=OPT[id],d=decOf(id),sp=A.spend_breakdown[id];return `<li><span class="rank">${i+1}</span><div><a href="#/choice-${d.id}"><strong>${OPT_LABEL[id]}</strong></a><small>${siteName(x._site)} · ${sp!==undefined?`spend ${usd(sp)}`:id==='MTO-METER-AUDIT'?'$60 from the routine maintenance budget':''} · ${/^(Not modelled|No saving claimed)$/.test(optEffect(x)[0])?'no saving claimed':`${optEffect(x)[0]} ${optEffect(x)[1]}`}${x.economics?.class?` · ${CLASS[x.economics.class][0]}`:''}</small></div>${dispBadge('RECOMMENDED')}</li>`;}).join('');
 const extra=op==='metro'?`<li><span class="rank">${A.recommended.length+1}</span><div><a href="#/choice-ruiru-expansion"><strong>${OPT_LABEL['CH-R7']}</strong></a><small>Ruiru · no departure affected · lowest priority</small></div>${badge('Low priority','')}</li>`:'';
 const cond=Object.values(OPT).filter(x=>OPS[SITEKEY[x._site][0]]===o&&x.disposition==='CONDITIONAL');
 const excludedIds=new Set((A.excluded||[]).map(x=>x.id));cond.forEach(x=>excludedIds.add(x.id));
 const others=[...(A.excluded||[]).filter(x=>OPT[x.id].disposition!=='CONDITIONAL').map(x=>({id:x.id,reason:x.reason,d:OPT[x.id].disposition})),...Object.values(OPT).filter(x=>OPS[SITEKEY[x._site][0]]===o&&['REJECTED','DEFERRED'].includes(x.disposition)&&!excludedIds.has(x.id)).map(x=>({id:x.id,reason:x.reason,d:x.disposition}))];
 return `<section class="panel d-first ${focus}" id="p-first"><div class="panel-head"><div>${focusTag(focus)}<h2>What to do first</h2><p>The recommended set for November and December: must-do work first, then the best 12-month result within budget and ${o.crewWord}.</p></div>${link(`plan-${op}`,'Plan and budget →')}</div>
 <ol class="d-rank">${rec}${extra}</ol>
 ${cond.length?`<h3 class="d-sub">Only if conditions change</h3><ul class="d-rank minor">${cond.map(x=>`<li><div><a href="#/choice-${decOf(x.id).id}"><strong>${OPT_LABEL[x.id]}</strong></a><small>${fx(x.condition)}</small></div>${dispBadge('CONDITIONAL')}</li>`).join('')}</ul>`:''}
 <h3 class="d-sub">Considered and not chosen</h3><ul class="d-rank minor">${others.map(x=>`<li><div><a href="#/choice-${decOf(x.id).id}"><strong>${OPT_LABEL[x.id]}</strong></a><small>${fx(x.reason)}</small></div>${dispBadge(x.d)}</li>`).join('')}</ul>
 <div class="d-meters">${meter('Budget, Nov–Dec',A.spend,budget,usd,`port:${op}:spend`)}${meter(o.crewWord[0].toUpperCase()+o.crewWord.slice(1)+', November',used,crew,num)}</div></section>`;
}
function meter(label,used,cap,f,key){const p=Math.min(100,used/cap*100);return `<div class="d-meter"><div class="d-meterhead"><span>${label}</span><strong>${key?`<button class="d-money" data-evd="${key}">${f(used)}${vh(' – show source records')}</button>`:f(used)} of ${f(cap)}</strong></div><div class="d-metertrack" role="meter" aria-valuemin="0" aria-valuemax="${cap}" aria-valuenow="${used}" aria-label="${label}: ${f(used)} of ${f(cap)}"><span style="width:${p}%"></span></div></div>`;}
const focusTag = f => f?`<div class="eyebrow d-focustag">Focus for ${DSTATE.role}</div>`:'';
function sitesPanel(op,focus){const o=OPS[op],cost=o.kind==='cost';
 return `<section class="panel ${focus}"><div class="panel-head"><div>${focusTag(focus)}<h2>Sites at a glance</h2><p>Same October figures as every other view. Select a site for its economics.</p></div></div>${table(['Site',cost?'Plan cost':'Plan','Actual',cost?'Over (−) / under plan':'Against plan','What is going on'],o.sites.map(sk=>{const P=siteM(sk).period,pl=cost?(P.plan.total??P.plan.energy_cost):P.plan.contribution,ac=cost?(P.actual.total??P.actual.energy_cost):P.actual.contribution;return [link(`econ-${sk}`,`<strong>${siteName(sk)}</strong>`),money$(`line:${sk}:${cost?'costplan':'plan'}`,pl),money$(`line:${sk}:${cost?'costactual':'contribution'}`,ac),usd(P.variance,true),SITE_STORY[sk]];}))}</section>`;}
function whyPanel(op,focus){const o=OPS[op];
 return `<section class="panel ${focus}"><div class="panel-head"><div>${focusTag(focus)}<h2>Why we are off plan</h2><p>Largest driver at each site; recorded, modelled and not-yet-explained amounts are labelled.</p></div>${link(`bridge-${op}`,'Full variance bridge →')}</div>${table(['Site','Difference','Largest driver','Evidence'],o.sites.map(sk=>{const s=siteM(sk),br=s.period.bridge||[];const big=[...br].sort((a,b)=>Math.abs(b.amount)-Math.abs(a.amount))[0];return [siteName(sk),usd(s.period.variance,true),big?`${DRIVER[big.driver]} (${usd(big.amount,true)})`:s.period.variance?'Not broken down yet':'On plan',big?CLASS[big.class][0]:'—'];}))}</section>`;}
function coveragePanel(op,focus){const o=OPS[op];
 const body=op==='lakeside'?table(['Site','Revenue','Diesel','Maintenance','Staff'],o.sites.map(sk=>{const c=siteM(sk).period.coverage;return [siteName(sk),...['revenue','diesel','om','staff'].map(k=>badge(SRC[c[k]][0],SRC[c[k]][1]))];}))+`<p class="d-note">Money by kind, never added across kinds: recorded actuals; estimated (Kisiwa maintenance ${money$('line:kisiwa:om',siteM('kisiwa').period.actual.om)}); modelled option effects (Plan and budget); exposures and possible credits (listed only); verified results: none yet.</p>`:`<p class="d-note">Coverage is not available yet for this operator in the demo fixture. Lines are shown with “Coverage not stated yet” rather than assumed recorded.</p>`;
 return `<section class="panel ${focus}"><div class="panel-head"><div>${focusTag(focus)}<h2>What is recorded and what is estimated</h2><p>Coverage by line for October.</p></div></div>${body}</section>`;}
function demandPanel(op,focus){
 const ids={lakeside:['MTO-HULLER','MTO-WELDING','MTO-BILLING'],harvest:['MWEA-AGG'],metro:['RUI-ABSORB6','RUI-ABSORB10']}[op];
 return `<section class="panel ${focus}"><div class="panel-head"><div>${focusTag(focus)}<h2>${op==='metro'?'Demand we can take on':'Demand worth selling'}</h2><p>${op==='metro'?'Captive fleet: charging earns no revenue. Demand here is the city’s offer of more buses.':'Qualified customer demand only: a named customer, a price and the cost of serving it.'}</p></div></div>
 ${table(['Opportunity','Effect','Decision','Limit'],ids.map(id=>{const x=OPT[id];return [link(`choice-${decOf(id).id}`,OPT_LABEL[id]),`${optEffect(x)[0]}<small class="d-cellnote">${optEffect(x)[1]}</small>`,dispBadge(x.disposition),fx(x.condition||x.reason||x.note)];}))}</section>`;}
function crewPanel(op,focus){const o=OPS[op],A=o.t.portfolio.allocation,M=o.t.portfolio_constraints,crew=M[o.crewKey],used=A.crew_visits_used??A.technician_visits_used;
 const jobs=A.recommended.map(id=>OPT[id]).filter(x=>(x.crew_visits||0)>0||x.id==='MTO-METER-AUDIT');
 return `<section class="panel ${focus}"><div class="panel-head"><div>${focusTag(focus)}<h2>Where the ${o.crewWord.replace(' visits','')}s go in November</h2><p>Physically feasible work only; safeguards checked before anything is scheduled.</p></div></div>
 ${meter(`${o.crewWord[0].toUpperCase()+o.crewWord.slice(1)} used`,used,crew,num)}
 ${jobs.length?table(['Work','Site','Visits'],jobs.map(x=>[link(`choice-${decOf(x.id).id}`,OPT_LABEL[x.id]),siteName(x._site),x.id==='MTO-METER-AUDIT'||x.id==='MTO-HULLER'?'Same visit as the inverter':String(x.crew_visits)])):`<p class="d-note">No recommended item needs a technician visit this month; ${num(crew)} visits stay free.</p>`}
 ${op==='lakeside'?'<p class="d-note">Mto’s inverter, huller connection and meter check share one visit.</p>':''}</section>`;}
function rightsSummary(op,focus){const keys=DEC.filter(d=>OPS[SITEKEY[d.site][0]]===OPS[op]&&d.rights).flatMap(d=>d.rights.map(k=>[k,d.id]));
 return `<section class="panel ${focus}"><div class="panel-head"><div>${focusTag(focus)}<h2>Rights under contracts</h2><p>Warranty, service and insurance positions that change a decision. Possible credits are never counted as money gained.</p></div></div>
 ${table(['Asset','Position','Claim stage','Next date'],keys.map(([k,did])=>{const r=rights(k);return [link(`choice-${did}`,r.asset),badge(r.elig[0],r.elig[1]),STAGES[STAGE_IX[r.state]]||'No claim possible',r.deadline?`${fdate(r.deadline)} (${daysUntil(r.deadline)} days)`:'—'];}))}
 <p class="d-legal">This is not a legal decision. Coverage is decided by the supplier or insurer.</p></section>`;}
function homeScreen(op){
 const r=DSTATE.role,order=ROLE_ORDER[r];
 const P={first:firstPanel,sites:sitesPanel,why:whyPanel,coverage:coveragePanel,demand:demandPanel,crew:crewPanel,rights:rightsSummary};
 return `<div class="d-roles" role="group" aria-label="Role emphasis"><span>View as</span>${['CEO','COO','CFO','CCO'].map(x=>`<button class="chip ${x===r?'active':''}" data-role="${x}" aria-pressed="${x===r}">${x}</button>`).join('')}<span class="d-rolenote">Changes the order and emphasis only. The numbers never change.</span></div>
 <div class="d-question"><span class="eyebrow">${r} question</span><p>${ROLE_Q[r]}</p></div>
 ${insightPanel(op)}<div class="d-panels">${order.map((k,i)=>P[k](op,i<2?'d-focus':'')).join('')}</div>`;
}

/* ---------- variance bridge ---------- */
function bridgeScreen(op){const o=OPS[op];
 return status(badge('Reconciles to the cent','green'),`Plan ${usd(opTotals(op).plan)} → actual ${usd(opTotals(op).actual)} · ${o.kind==='cost'?'cost':'contribution'} · October 2026`)+
 `<section class="panel">${waterfall(op)}</section>`+
 notice(`Select a step to open that site’s economics. The “not explained yet” steps are shown on purpose: ${op==='lakeside'?'Kobo’s 120 L of fuel above the 2% tolerance is being investigated; Kisiwa’s 20 L is within tolerance and reported only.':op==='metro'?'Ruiru came in slightly under plan with no driver lines recorded, so the difference is shown unexplained rather than hidden.':'Mwea’s 15 kWh above model is within the 5% tolerance.'} Modelled steps come from replaying site data, not from invoices.`,'blue');}

/* ---------- site economics ---------- */
const LINES = {
 mini:[['Revenue (billed)','revenue',1,'revenue'],['Diesel','diesel_cost',-1,'diesel'],['Operations and maintenance','om',-1,'om'],['Staff','staff',-1,'staff']],
 cold:[['Storage revenue','revenue',1],['Electricity','energy',-1],['Staff','staff',-1],['Maintenance','maint',-1],['Customer compensation','liability',-1]],
 ev:[['Energy at peak price','peak_cost',-1],['Energy at off-peak price','offpeak_cost',-1],['Demand charge','demand_cost',-1],['Energy (flat tariff)','energy_cost',-1,null,'flat'],['Maintenance','maintenance',-1]]};
function lineSrc(sk,field,cov){const s=siteM(sk),v=OPS[SITEKEY[sk][0]].vertical;
 if(v==='mini')return cov?SRC[s.period.coverage[cov]]:SRC.NONE;
 if(field==='liability')return SRC.RECORDED;
 if(sk==='embakasi')return SRC.RECORDED;
 return SRC.NONE;}
function pnl(sk){const s=siteM(sk),o=OPS[SITEKEY[sk][0]],P=s.period,cost=o.kind==='cost';
 let lines=LINES[o.vertical].filter(([,f,,,flag])=>P.plan[f]!==undefined||P.actual[f]!==undefined);
 if(cost&&sk!=='kasarani')lines=lines.filter(l=>l[4]!=='flat');
 if(sk==='kasarani')lines=lines.filter(l=>['energy_cost','maintenance'].includes(l[1]));
 const rows=lines.map(([lab,f,sg,cov])=>{const pl=P.plan[f],ac=P.actual[f],[st,tone]=lineSrc(sk,f,cov);const diff=pl!==undefined&&ac!==undefined?r2((ac-pl)*sg):null;
  return [lab,pl!==undefined?usd(pl):'<span class="muted">not available yet</span>',ac!==undefined?money$(`line:${sk}:${f}`,ac):'<span class="muted">not available yet</span>',diff===null?'—':usd(diff,true),badge(st,tone)];});
 const tot=cost?['Total cost','total','energy_cost']:['Contribution','contribution'];
 const pl=cost?(P.plan.total??P.plan.energy_cost):P.plan.contribution,ac=cost?(P.actual.total??P.actual.energy_cost):P.actual.contribution;
 rows.push([`<strong>${tot[0]}</strong>`,`<strong>${usd(pl)}</strong>`,`<strong>${money$(`line:${sk}:${cost?'costactual':'contribution'}`,ac)}</strong>`,`<strong>${usd(P.variance,true)}</strong>`,'']);
 return table(['Line','Plan','Actual','Effect on result','Source'],rows)+(sk==='kisiwa'?`<p class="d-note">${s.period.coverage_note}.</p>`:'')+(cost&&sk==='ruiru'?'<p class="d-note">Ruiru’s plan is one line; the plan split by time of day is not available yet.</p>':'');}
function flowSvg(parts,total,title){const id=++svgUid;let x=0;
 return `<svg class="d-flowbar" viewBox="0 0 1000 40" preserveAspectRatio="none" role="img" aria-labelledby="fl-${id}"><title id="fl-${id}">${escapeHtml(title)}</title>${PATTERNS(id)}${parts.map(([v,tone,cls])=>{const w=v/total*1000,r=`<rect x="${x}" y="4" width="${Math.max(w-2,1)}" height="32" class="tone-${tone}" fill="${cls==='unx'?`url(#dots-${id})`:cls==='mod'?`url(#hatch-${id})`:'currentColor'}" stroke="currentColor"/>`;x+=w;return r;}).join('')}</svg>`;}
function energyToCash(sk){const s=siteM(sk),a=s.period.actual;
 if(a.delivered_kwh===undefined)return `<p class="d-note">Delivered and metered energy for ${siteName(sk)} are not available yet in the fixture; billed energy was ${num(a.billed_kwh)} kWh (plan ${num(s.period.plan.billed_kwh)}).</p>`;
 const mto=sk==='mto',loss=mto?a.expected_technical_loss_kwh:a.technical_loss_kwh;
 const steps=mto?[['Delivered',`${num(a.delivered_kwh)} kWh`],['Expected losses',`−${num(loss)} kWh`],['Not explained',`−${num(a.unexplained_kwh)} kWh`,'unx'],['Metered',`${num(a.metered_kwh)} kWh`],['Not billed after meter swap',`−${num(a.unbilled_mapping_kwh)} kWh`],['Approved allowance',`−${num(a.adjustments_kwh)} kWh`],['Billed',`${num(a.billed_kwh)} kWh · ${usd(a.revenue)}`]]
  :[['Delivered',`${num(a.delivered_kwh)} kWh`],['Technical losses',`−${num(loss)} kWh`],['Metered',`${num(a.metered_kwh)} kWh`],['Adjustments',`−${num(a.adjustments_kwh)} kWh`],['Billed',`${num(a.billed_kwh)} kWh · ${usd(a.revenue)}`]];
 const parts=mto?[[a.billed_kwh,'actual'],[a.adjustments_kwh,'plan'],[a.unbilled_mapping_kwh,'worse'],[a.unexplained_kwh,'neutral','unx'],[loss,'neutral']]:[[a.billed_kwh,'actual'],[a.adjustments_kwh,'plan'],[loss,'neutral']];
 const cash=[['Collected',a.collected,'better'],['In transit',a.in_transit,'plan'],['Outstanding',a.outstanding,'worse']];
 return `<figure class="d-chart" aria-label="Energy to cash at ${siteName(sk)}"><figcaption><strong>Energy to cash, October</strong> · where delivered energy went, and where billed money is</figcaption>
 <ol class="d-flow">${steps.map(([l,v,c])=>`<li class="${c||''} ${v.startsWith('−')?'loss':''}"><small>${l}</small><b>${v}</b></li>`).join('')}</ol>
 ${flowSvg(parts,a.delivered_kwh,`Delivered ${a.delivered_kwh} kWh split into billed ${a.billed_kwh}, adjustments ${a.adjustments_kwh}${mto?`, unbilled ${a.unbilled_mapping_kwh}, unexplained ${a.unexplained_kwh}`:''}, losses ${loss}`)}
 ${chartLegend(mto?[['Billed','solid','actual'],['Allowance','solid','plan'],['Not billed (meter swap)','solid','worse'],['Not explained','unx','neutral'],['Expected losses','solid','neutral']]:[['Billed','solid','actual'],['Adjustments','solid','plan'],['Technical losses','solid','neutral']])}
 <h3 class="d-sub">Billed ${money$(`line:${sk}:revenue`,a.revenue)} → cash</h3>
 ${flowSvg(cash.map(([,v,t])=>[v,t]),a.revenue,`Billed ${usd(a.revenue)}: collected ${usd(a.collected)}, in transit ${usd(a.in_transit)}, outstanding ${usd(a.outstanding)}`)}
 <div class="d-legend">${cash.map(([l,v,t])=>`<span><i class="sw tone-${t}"></i>${l} ${money$(`cash:${sk}:${l}`,v)}</span>`).join('')}</div>
 ${mto?'<p class="d-note">The 120 kWh not explained is deliberately not priced: it is for investigation and is not assumed to be theft or collectible. The $150 in transit was paid on 30–31 Oct and settled on 2 Nov.</p>':''}
 <details class="d-table"><summary>Show as a table</summary>${table(['Step','Value'],steps.map(([l,v])=>[l,v]))}</details></figure>`;}
function fuelBalance(sk){const fb=siteM(sk).period.fuel_balance;if(!fb)return '';
 const rows=fb.opening_dip_l!==undefined?[['Opening tank dip',`${num(fb.opening_dip_l)} L`],['Deliveries',`${num(fb.deliveries_l)} L`],['Closing tank dip',`${num(fb.closing_dip_l)} L`],['Consumed',`${num(fb.consumed_l)} L`]]:[['Consumed',`${num(fb.consumed_l)} L`]];
 rows.push(['Explained by the site model',`${num(fb.model_implied_l)} L`],['Not explained',`${num(fb.residual_l)} L · ${fb.residual_l/fb.consumed_l*100>fb.tolerance_pct?'above':'within'} the ${fb.tolerance_pct}% tolerance`]);
 return `<h3 class="d-sub">Fuel balance, October</h3>${kv(rows)}`;}
function coldEnergy(sk){const s=siteM(sk),a=s.period.actual,m=MANIFEST.tenants[1];const over=a.kwh-a.kwh_model,p=over/a.kwh_model*100,tol=m.energy_model.tolerance_pct;
 const max=Math.max(a.kwh,a.kwh_model)*1.15,dom=[0,max];
 const verdict=Math.abs(p)<=tol?['Low occupancy, not equipment','green',`Energy is within ${tol}% of what the room should use at ${a.occupancy_pct}% occupancy.`]:['Equipment, not occupancy','red',`Energy is ${p.toFixed(0)}% above what the room should use at ${a.occupancy_pct}% occupancy.`];
 const inc=s.incident;
 return `<figure class="d-chart" aria-labelledby="ce-${sk}"><figcaption id="ce-${sk}"><strong>Energy used against what this occupancy explains</strong> · ${num(a.crate_days)} crate-days (${a.occupancy_pct}% full; plan ${s.period.plan.occupancy_pct}%)</figcaption>
 ${chartLegend([['Expected at this occupancy (modelled)','mod','plan'],['Actual (meter)','solid','actual']])}
 <div class="d-crow"><span class="d-clabel">Expected</span><div class="d-ctrack">${barSvg(0,a.kwh_model,dom,'mod','plan',`Expected ${a.kwh_model} kWh`)}</div><div class="d-cval"><span>${num(a.kwh_model)} kWh</span></div></div>
 <div class="d-crow"><span class="d-clabel">Actual</span><div class="d-ctrack">${barSvg(0,a.kwh,dom,'solid','actual',`Actual ${a.kwh} kWh`)}</div><div class="d-cval"><span><b>${num(a.kwh)} kWh</b></span></div></div>
 <div class="d-verdict">${badge(verdict[0],verdict[1])}<p>${verdict[2]} Model: ${m.energy_model.form} (proposed per-room model).</p></div>
 <details class="d-table"><summary>Show as a table</summary>${table(['Measure','kWh'],[['Expected at this occupancy',num(a.kwh_model)],['Actual',num(a.kwh)],['Difference',`${over>0?'+':''}${num(over)}`]])}</details></figure>
 ${inc?`<h3 class="d-sub">14 Oct outage and the stock in the room</h3>${kv([['Grid outage',inc.grid_outage],['Backup',inc.backup],['Chamber above 8 °C',`${inc.chamber.above_8c} (${inc.chamber.minutes} min, peak ${inc.chamber.peak_c} °C)`]])}${table(['Batch','Produce','Crates','Exposed?','Money'],inc.batches.map(b=>[b.batch,b.commodity,b.crates,b.present===false?`Not in the room (${b.reason})`:b.exposed?'Yes, above its limit':`No (${b.reason})`,b.exposed?`${money$('liab:thika:exposed',b.exposed_value)} exposed (not a loss) · ${money$('line:thika:liability',b.liability)} owed after inspection`:'—']))}`:''}`;}
function evDepot(sk){const s=siteM(sk),P=s.period,a=P.actual;
 const dep=`${num(a.departures_met)} of ${num(a.departures_required)} departures met in October`;
 if(sk==='embakasi'){const dom=[0,1];return `<figure class="d-chart" aria-labelledby="ev-${sk}"><figcaption id="ev-${sk}"><strong>Share of charging at peak price</strong> · ${dep}</figcaption>${chartLegend([['Plan','solid','plan'],['Actual','solid','actual']])}
  <div class="d-crow"><span class="d-clabel">Plan</span><div class="d-ctrack">${barSvg(0,P.plan.peak_share,dom,'solid','plan',`Plan ${pct(P.plan.peak_share,0)} at peak`)}</div><div class="d-cval"><span>${pct(P.plan.peak_share,0)} · ${num(P.plan.peak_kwh)} kWh</span></div></div>
  <div class="d-crow"><span class="d-clabel">Actual</span><div class="d-ctrack">${barSvg(0,a.peak_share,dom,'solid','actual',`Actual ${pct(a.peak_share,0)} at peak`)}</div><div class="d-cval"><span><b>${pct(a.peak_share,0)} · ${num(a.peak_kwh)} kWh</b></span></div></div>
  <p class="d-note">Peak ${s.tariff.peak}; off-peak $${s.tariff.offpeak}/kWh; demand charge $${s.tariff.demand_usd_per_kw_month} per kW of monthly peak (${a.max_kw} kW actual, plan ${P.plan.max_kw} kW). Tariff applicability is an assumption until confirmed from the invoice.</p>
  <details class="d-table"><summary>Show as a table</summary>${table(['','Plan','Actual'],[['Peak share',pct(P.plan.peak_share,0),pct(a.peak_share,0)],['Peak kWh',num(P.plan.peak_kwh),num(a.peak_kwh)],['Monthly peak kW',P.plan.max_kw,a.max_kw]])}</details></figure>`;}
 if(sk==='kasarani'){const inc=s.incident;return `${kv([['October',dep],['Tariff',`Flat $${s.tariff.usd_per_kwh}/kWh: timing does not change cost`],['Fault',`Charger 2, ${inc.fault.code}, ${inc.fault.at.replace('T',' ').slice(0,16)}`],['Capacity after the fault',`${num(inc.capacity_after.deliverable_kwh)} of ${num(inc.capacity_after.required_kwh)} kWh a night (${inc.capacity_after.buses_short} bus short)`],['November to date',`${inc.november_to_date.missed_departures} missed departures · ${inc.november_to_date.spare_bus_lent_nights} nights with a spare bus lent`]])}<p class="d-note">November penalties so far: ${money$('pen:kasarani',inc.november_to_date.penalties)} (recorded; $120 per missed block).</p>`;}
 return `${kv([['October',dep],['Charger use',`${pct(a.charger_hour_utilisation,0)} of charger-hours`],['Peak share',`${pct(a.peak_kwh/a.kwh,0)} (${num(a.peak_kwh)} of ${num(a.kwh)} kWh)`],['Monthly peak',`${a.max_kw} kW of a ${s.physical.import_limit_kw} kW import limit`],['Charger 7, connector 2',s.incident.service_consequence]])}`;}
function econScreen(sk){const s=siteM(sk),op=SITEKEY[sk][0],o=OPS[op],decs=DEC.filter(d=>d.site===sk);
 const chain=o.vertical==='mini'?energyToCash(sk)+fuelBalance(sk):o.vertical==='cold'?coldEnergy(sk):evDepot(sk);
 const br=s.period.bridge||[];
 return status(badge(SITE_STORY[sk],''),`${o.name} · October 2026`,OPS_DETAIL[sk]?link(OPS_DETAIL[sk],'Operations detail (v7.0 site view) →','button'):'<span class="muted">No v7.0 operations view for this site</span>')+
 `<div class="two-col"><section class="panel"><div class="panel-head"><div><h2>${o.kind==='cost'?'Cost against plan':'Profit and loss against plan'}</h2><p>Every amount opens its source records. Source shows whether the line is recorded, estimated or not yet stated.</p></div></div>${pnl(sk)}
 ${br.length?`<h3 class="d-sub">What moved the result</h3>${table(['Driver','Amount','Evidence','How it was worked out'],br.map((b,i)=>[DRIVER[b.driver],money$(`bridge:${sk}:${i}`,o.kind==='cost'?-b.amount:b.amount,true),CLASS[b.class][0],pt(b.basis)]))}`:''}</section>
 <aside><section class="panel"><div class="panel-head"><div><h2>Decisions at this site</h2></div></div><ul class="d-rank minor">${decs.length?decs.map(d=>{const rec=d.opts.map(id=>OPT[id]).find(x=>x.disposition==='RECOMMENDED');return `<li><div><a href="#/choice-${d.id}"><strong>${d.title}</strong></a><small>${rec?'Recommended: '+OPT_LABEL[rec.id]:''}</small></div></li>`;}).join(''):'<li><div><small>No open decision at this site.</small></div></li>'}</ul></section>
 ${OPS_DETAIL[sk]?notice('The v7.0 operations view shows the earlier demo site with the same equipment type; its names and figures belong to that earlier estate.','blue'):''}</aside></div>
 <section class="panel"><div class="panel-head"><div><h2>${o.vertical==='mini'?'From energy to cash':o.vertical==='cold'?'Is it the room or the equipment?':'Buses ready to leave, and what charging cost'}</h2></div></div>${chain}</section>`;}

/* ---------- decision comparator ---------- */
function choiceScreen(d){const s=siteM(d.site),t=decText(d),o=OPS[SITEKEY[d.site][0]];
 const origin={FINDING:'Found in site data',PLAN_VARIANCE:'Found in the plan comparison',CUSTOMER_PROPOSAL:'Customer proposal'}[s.decision?.origin]||'Contract and asset condition';
 const rows=d.opts.map(id=>{const x=OPT[id],[c,cn]=optCost(x),[e,en]=optEffect(x),rej=['REJECTED','DEFERRED','COMPARISON'].includes(x.disposition);
  const cKey=x.capex!==undefined||x.cost!==undefined||x.residual_cost!==undefined||x.economics?.one_off!==undefined;
  return `<tr class="${rej?'d-rej':''} ${x.disposition==='RECOMMENDED'?'d-recrow':''}"><th scope="row">${OPT_LABEL[id]}${x.kind==='NO_ACTION'?' <span class="badge outline">Do nothing</span>':''}</th><td data-label="What it costs">${cKey&&c!=='$0'?`<button class="d-money" data-evd="opt:${id}:cost">${c}${vh(' – show source records')}</button>`:c}<small class="d-cellnote">${cn}</small></td><td data-label="Effect">${/^[−+$]/.test(e)?`<button class="d-money" data-evd="opt:${id}:effect">${e}${vh(' – show how it was worked out')}</button>`:e}<small class="d-cellnote">${en}</small></td><td data-label="Evidence">${optEvidence(x)}</td><td data-label="Safeguards">${optSafeguards(x)}</td><td data-label="Decision">${dispBadge(x.disposition)}</td><td data-label="Why / why not">${x.disposition==='RECOMMENDED'?(x.condition?`Condition: ${fx(x.condition)}`:fx(x.reason||x.note)):`${x.disposition==='CONDITIONAL'?'':`<strong>${x.disposition==='COMPARISON'?'Effect:':'Why not:'}</strong> `}${optWhy(x)}`}</td></tr>`;}).join('');
 const cards=[['What happened',t.happened],['Why it matters in money',t.matters],['Why this option, not the others',t.why],['What could stop it',t.prevents]];
 return status(badge(origin,'blue'),`${siteName(d.site)} · ${o.name}`,link(`econ-${d.site}`,'Site economics →','button'))+
 `<div class="d-answer">${cards.map(([h,b])=>`<article><h3>${h}</h3><p>${b}</p></article>`).join('')}</div>
 <section class="panel"><div class="panel-head"><div><h2>Options compared</h2><p>Every option stays visible, including doing nothing. Amounts open their source or working.</p></div></div>
 <div class="table-wrap d-scroll" tabindex="0" role="region" aria-label="Options compared (scrolls sideways on small screens)"><table class="d-opts"><thead><tr><th scope="col">Option</th><th scope="col">What it costs</th><th scope="col">Effect</th><th scope="col">Evidence</th><th scope="col">Safeguards</th><th scope="col">Decision</th><th scope="col">Why / why not</th></tr></thead><tbody>${rows}</tbody></table></div>
 <h3 class="d-sub">If things change</h3><ul class="d-list">${t.sensitivity.map(x=>`<li>${x}</li>`).join('')}</ul>
 <div class="form-footer"><button class="button primary" data-example="Example only: approval would be recorded against a named person; nothing was approved.">Approve the recommended option (example)</button>${link(`plan-${o===OPS.lakeside?'lakeside':o===OPS.harvest?'harvest':'metro'}`,'See it in the plan →','button')}</div></section>
 ${(d.rights||[]).map(rightsPanel).join('')}
 <div class="d-grid2"><section class="panel"><div class="panel-head"><div><h2>How we would prove it worked</h2><p>Three separate answers; one never stands in for another.</p></div>${d.verify?link(`verify-${SITEKEY[d.site][0]}`,'Proof view →'):''}</div>${kv(t.prove)}</section>
 <section class="panel"><div class="panel-head"><div><h2>What records we need from you</h2><p>Exports you already have; no device integration needed to start.</p></div></div><ul class="d-list">${t.records.map(x=>`<li>${x}</li>`).join('')}</ul></section></div>`;}

/* ---------- plan and budget ---------- */
function planScreen(op){const o=OPS[op],A=o.t.portfolio.allocation,M=o.t.portfolio_constraints;
 const hi=op==='lakeside'&&DSTATE.budget.lakeside==='high';
 const budget=hi?6500:M.budget_usd_nov_dec,crew=M[o.crewKey],used=A.crew_visits_used??A.technician_visits_used;
 let rec=[...A.recommended];if(hi)rec=rec.map(id=>id==='MTO-INV-CLAIM'?'MTO-INV-BUYNOW':id);
 const spendOf=id=>id==='MTO-INV-BUYNOW'?OPT[id].residual_cost:A.spend_breakdown[id];
 const spend=hi?r2(A.spend-A.spend_breakdown['MTO-INV-CLAIM']+OPT['MTO-INV-BUYNOW'].residual_cost):A.spend;
 const budgetCtl=op==='lakeside'?`<fieldset class="d-budget"><legend>Budget for November and December</legend>${[['base',M.budget_usd_nov_dec],['high',6500]].map(([k,v])=>`<label><input type="radio" name="budget" value="${k}" data-budget="${k}" ${DSTATE.budget.lakeside===k?'checked':''}> ${usd(v)}</label>`).join('')}<small>The ${usd(6500)} case assumes the cooperative cannot extend its letter of intent past 30 Nov.</small></fieldset>`
  :`<fieldset class="d-budget"><legend>Budget for November and December</legend><label><input type="radio" checked disabled> ${usd(M.budget_usd_nov_dec)}</label><small>Only one budget case is modelled for this operator in the fixture.</small></fieldset>`;
 const m12=A.modelled_12m_change;
 let total;if(op==='lakeside'){total=hi?r2(m12['KOB-STOPSOC']+m12['MTO-HULLER']-OPT['MTO-INV-BUYNOW'].residual_cost):m12.total;}
 const recRows=rec.map(id=>{const x=OPT[id];return [link(`choice-${decOf(id).id}`,OPT_LABEL[id]),siteName(x._site),id==='MTO-METER-AUDIT'?'$60 (routine maintenance budget)':money$(`opt:${id}:cost`,spendOf(id)),`${optEffect(x)[0]} <small class="d-cellnote">${optEffect(x)[1]}</small>`,x.economics?.class?CLASS[x.economics.class][0]:x.kind==='SUPPLIER_REMEDY'||x.kind==='STOPGAP_PLUS_CLAIM'?'Cost of the path':'—'];});
 const excl=hi?[{id:'MTO-INV-CLAIM',reason:'Replaced: with this budget and no extension, buying now restores the inverter by 12 Nov, before the letter of intent lapses'},...A.excluded.filter(x=>x.id!=='MTO-INV-BUYNOW')]:(A.excluded||[]);
 const listed=A.listed_not_summed;
 return `<div class="d-grid2 controls">${budgetCtl}<div>${meter('Budget used',spend,budget,usd,hi?'':`port:${op}:spend`)}${meter(o.crewWord[0].toUpperCase()+o.crewWord.slice(1)+' used',used,crew,num)}</div></div>
 ${hi?notice(`Budget ${usd(6500)}: buying the inverter now replaces the warranty-and-wait path. Spend becomes ${usd(spend)} (${usd(A.spend)} − ${usd(A.spend_breakdown['MTO-INV-CLAIM'])} + ${usd(OPT['MTO-INV-BUYNOW'].residual_cost)}). The earlier restoration date is not given a money value in the fixture.`,'blue'):''}
 <section class="panel"><div class="panel-head"><div><h2>Recommended set</h2><p>${A.method||'Must-do work first, then the best 12-month result within budget and visits.'}</p></div></div>${table(['Option','Site','Spend','Effect','Evidence'],recRows)}
 ${op==='lakeside'?`<div class="d-total"><span>Modelled 12-month change, not realized</span><strong>${hi?`<span>${usd(total,true)}</span>`:money$('port:lakeside:m12',total,true)}</strong><small>${hi?`${usd(m12['KOB-STOPSOC'])} + ${usd(m12['MTO-HULLER'])} − ${usd(OPT['MTO-INV-BUYNOW'].residual_cost)}`:`${usd(m12['KOB-STOPSOC'])} + ${usd(m12['MTO-HULLER'])} − ${usd(-m12['MTO-INV-CLAIM'])}`} · separate drivers, each counted once</small></div>
 <h3 class="d-sub">Listed, not added</h3>${table(['Item','Amount','Why it is not added'],[['Charges restored at Mto (12 months)',usd(listed['MTO-BILLING_charges_12m']),'Billed, not yet collected'],['Possible Kisiwa service credit',usd(listed['KIS-OM-SLA_potential_credit']),'Not counted until a credit note arrives'],['Kobo battery cover',usd(listed['BAT-001_cover_exposure']),'Exposure we protect, not money gained']])}<p class="d-note">${A.meter_audit_note.replace('MTO-METER-AUDIT','The meter check')}.</p>`
 :`<p class="d-note">No portfolio 12-month total is given for this operator: each effect is listed above and not added.</p>`}</section>
 <section class="panel"><div class="panel-head"><div><h2>Not in the plan, and why</h2></div></div>${table(['Option','Reason'],excl.map(x=>[link(`choice-${decOf(x.id).id}`,OPT_LABEL[x.id]),fx(x.reason)]))}</section>
 ${A.sensitivity?`<section class="panel"><div class="panel-head"><div><h2>What would change the ranking</h2></div></div><ul class="d-list"><li>Budget of $6,430 or more and the letter of intent cannot be extended: buying the inverter now replaces the warranty path.</li><li>Diesel 20% cheaper: the generator setting change is worth ${usd(OPT['KOB-STOPSOC'].sensitivity.diesel_minus_20pct_net_12m)} over 12 months; ranking unchanged.</li><li>Huller contract not signed: the huller drops out; the inverter warranty path is still recommended.</li></ul></section>`:''}
 ${A.priority_order?`<section class="panel"><div class="panel-head"><div><h2>Order of work</h2></div></div><ol class="d-list"><li>Kasarani stop-gap: departures at risk now</li><li>Embakasi schedule: the largest money</li><li>Ruiru extra buses: a contract decision</li><li>Ruiru connector claim: no consequence</li></ol></section>`:''}`;}

/* ---------- verification ---------- */
function verifyScreen(op){const o=OPS[op],id=o.verifyOpt,x=OPT[id],d=decOf(id),s=siteM(o.verifySite);
 const vp=s.decision.verification_plan||{},plan=Object.fromEntries(Object.entries(vp).map(([k,v])=>[k,pt(v)]));const proposed='<span class="badge outline">Proposed in this mock-up</span>';
 const V={lakeside:[['Did the operation change?',`Trial not started (as of ${fdate(AS_OF)}).`,plan.operational_target,`Energy management export, 5-minute, for ${plan.after}; baseline ${plan.baseline}.`],
  ['Did the money show up in the books?','November books not closed.',plan.economic,`November fuel delivery notes and tank dips. Expected (modelled, not realized): ${usd(x.economics.net_monthly)} a month.`],
  ['How sure are we it was the change?','Not assessed until both above have results.',plan.causal,'Comparable days for weather and load; the untreated sites’ data for the same days.']],
  harvest:[['Did the operation change?','Repair not done yet.',`Energy back within the ${MANIFEST.tenants[1].energy_model.tolerance_pct}% model tolerance at the same occupancy and temperature ${proposed}`,'Hourly energy meter and storage ledger for 30 days after the repair.'],
  ['Did the money show up in the books?','No invoice after the repair yet.',`Room electricity cost per month against the modelled ${usd(x.economics.monthly)} recovery ${proposed}`,'Electricity invoices for the room.'],
  ['How sure are we it was the change?','Not assessed.',`Mwea and Thika as rooms without the repair ${proposed}`,'Same-period meter data for the comparison rooms.']],
  metro:[['Did the operation change?','Schedule not started.',`Peak share falls from ${pct(s.period.actual.peak_share,0)} toward the ${pct(s.period.plan.peak_share,0)} plan; monthly peak at or below ${x.max_kw} kW; every departure met over 14 supervised days ${proposed}`,'Charger session log and fleet roster for the 14 days.'],
  ['Did the money show up in the books?','November invoice not received.',`Time-of-use and demand lines against the modelled ${usd(x.economics.saving_monthly)} a month ${proposed}`,'Utility invoice with time-of-use and demand lines; confirms the tariff.'],
  ['How sure are we it was the change?','Not assessed.',`Ruiru as the comparison depot; Kasarani’s flat tariff is not comparable ${proposed}`,'Ruiru invoice and session log for the same period.']]}[op];
 return status(badge('Not yet','amber'),`${OPT_LABEL[id]} · ${siteName(o.verifySite)}`,link(`choice-${d.id}`,'Back to the decision →','button'))+
 `<div class="d-verdicts">${V.map(([q,now,test,need],i)=>`<section class="panel"><div class="eyebrow">Answer ${i+1} of 3</div><h2>${q}</h2><div class="d-vstate">${badge('Not yet','amber')}<span>${now}</span></div><h3>What counts as yes</h3><p>${test}</p><h3>Data needed</h3><p>${need}</p></section>`).join('')}</div>`+
 notice('Each answer is separate. A completed job does not prove the money arrived, and money arriving does not prove the change caused it. Simulated trials never count as real savings.','blue');}

/* ---------- pilot request ---------- */
const PILOT_SRC = {lakeside:MANIFEST.sources.mini_grid,harvest:[...MANIFEST.sources.cold_chain,MANIFEST.sources.mini_grid[5],MANIFEST.sources.mini_grid[6]],metro:[...MANIFEST.sources.ev_depot,MANIFEST.sources.mini_grid[5],MANIFEST.sources.mini_grid[6]]};
const PROV = {'demo-simulated':'Simulated demo data','source-emulated':'Emulated source','bench-tested':'Bench tested','field-integrated':'Field connected','observed-financial':'Observed financial'};
function plainSource(x){return x.system.replace(/\s*\(GX-shaped[^)]*\)/,'').replace(/\(existing operational records [^)]*\)/,'').replace('CPMS OCPP 1.6J log (StartTransaction, MeterValues, StatusNotification)','Charger management system session and status log').replace('EMS / inverter','Energy management system or inverter export');}
function pilotScreen(op){const o=OPS[op],src=PILOT_SRC[op];
 return `<div class="d-grid2 wide"><section class="panel"><div class="panel-head"><div><div class="eyebrow">Paid diagnostic for ${o.name}</div><h2>${o.t.opening_proposition}</h2><p>A bounded diagnostic on your own records. Nothing here uses your real economics yet: every figure in this demo is illustrative.</p></div></div>
 <h3>Records we need (${src.length} categories)</h3><ol class="d-list">${src.map(x=>`<li>${plainSource(x)}${x.record?`<small class="d-cellnote">Typical fields: ${x.record.replace(/_/g,' ')}</small>`:''}</li>`).join('')}</ol>
 <h3>What you get</h3><ul class="d-list"><li>Site economics against your plan for each site, with recorded and estimated lines marked</li><li>A variance bridge from plan to actual, with the unexplained part shown</li><li>Ranked decisions with costed alternatives, “do nothing” and the reasons options were rejected</li><li>A contract-rights calendar: warranty, service and insurance positions with notice dates (not legal advice)</li><li>A verification plan for the first recommended change</li></ul>
 <h3>How we check it is right</h3><ul class="d-list"><li>Monthly totals reconcile to your management accounts to the cent</li><li>Every figure opens its source records</li><li>One negative control: a site where the obvious saving is not real</li></ul>
 <h3>Timeline ${'<span class="badge outline">Proposed</span>'}</h3><ol class="d-list"><li>Week 1: exports agreed and received (no device integration)</li><li>Weeks 2–3: reconciliation and first findings reviewed with your team</li><li>Week 4: decision review and verification plan</li></ol>
 <p class="d-note">Price: set in the written proposal; not shown in this mock-up.</p></section>
 <section class="panel"><div class="panel-head"><div><h2>Request a diagnostic</h2><p>Example form: nothing is sent.</p></div></div>
 <form class="d-form" data-pilot-form><label class="field">Your name<input name="n" autocomplete="name"></label><label class="field">Organisation<input name="o" value="${o.name}" autocomplete="organization"></label><label class="field">Number of sites<input name="s" inputmode="numeric" value="3"></label><label class="field">Data contact (email)<input name="e" type="email" autocomplete="email"></label><label class="field">First question you want answered<textarea name="q" rows="3">${o.t.opening_proposition}</textarea></label><div class="form-footer"><button class="button primary" type="submit">Request the diagnostic</button></div></form></section></div>`;}

/* ---------- evidence drawer ---------- */
function provChips(active){return `<div class="d-prov" aria-label="Provenance">${Object.values(PROV).map(p=>`<span class="${p===active?'on':''}">${p===active?icon('check'):''}${p}</span>`).join('')}</div>`;}
function evidenceRecord(key){
 const [kind,a,b,c]=key.split(':');const S=sk=>siteM(sk),srcE='Emulated source';
 const R=(title,value,path,transform,sys,header,rows,coverage,prov=srcE,extra='')=>({title,value,path,transform,sys,header,rows,coverage,prov,extra});
 if(kind==='port'){const o=OPS[a],P=o.t.portfolio,t=opTotals(a);
  if(b==='spend')return R(`${o.name} · recommended spend`,usd(P.allocation.spend),`tenants[${o.ti}].portfolio.allocation.spend`,`Sum of the recommended options’ spend: ${Object.entries(P.allocation.spend_breakdown).map(([k,v])=>`${usd(v)}`).join(' + ')} = ${usd(P.allocation.spend)}`,'Option set (decision records)','option, spend',Object.entries(P.allocation.spend_breakdown).map(([k,v])=>[OPT_LABEL[k],usd(v)]),'All recommended options costed','Simulated demo data');
  if(b==='m12')return R('Modelled 12-month change','+'+usd(P.allocation.modelled_12m_change.total),`tenants[0].portfolio.allocation.modelled_12m_change`,'Generator setting change + rice huller − inverter warranty path cost. Separate drivers, each counted once. Not realized.','Forward replay of site data (modelled)','option, 12-month',[[OPT_LABEL['KOB-STOPSOC'],usd(2916)],[OPT_LABEL['MTO-HULLER'],usd(3540)],[OPT_LABEL['MTO-INV-CLAIM'],usd(-360)]],'Modelled, not recorded','Simulated demo data');
  if(b==='listed')return c==='cover'?R('Kobo battery cover',usd(P.allocation.listed_not_summed['BAT-001_cover_exposure']),'tenants[0].portfolio.allocation.listed_not_summed.BAT-001_cover_exposure','Asset value covered by the warranty. Exposure, never money gained.','Warranty contract (reviewed extraction)','clause, value',[['Battery warranty to 1 Mar 2034',usd(64000)]],'Exposure'):R('Possible Kisiwa service credit',usd(70),'tenants[0].sites[1].entitlements[1].potential_credit','10% of the $700 monthly fee when response is late (96 hours against 48). Counted only when a credit note arrives.','Operations and maintenance contract; work ticket times','reported, responded, hours',[['2026-10-30 19:10','2026-11-03 19:30','96']],'Exposure');
  const rows=o.sites.map(sk=>{const P2=S(sk).period;return [siteName(sk),usd(o.kind==='cost'?(P2.plan.total??P2.plan.energy_cost):P2.plan.contribution),usd(o.kind==='cost'?(P2.actual.total??P2.actual.energy_cost):P2.actual.contribution)];});
  const v=b==='plan'?t.plan:b==='actual'?t.actual:t.variance;
  return R(`${o.name} · ${b==='plan'?'plan':b==='actual'?'actual':'difference from plan'}`,usd(v,b==='variance'),`tenants[${o.ti}].portfolio.${o.kind==='cost'?(b==='variance'?'variance':b+'_cost'):(b==='variance'?'variance':b+'_contribution')}`,`Sum of the three sites (${o.kind==='cost'?'cost':'contribution'}); one currency (USD, illustrative).`,b==='plan'?'Monthly plan / budget spreadsheet':'Site economics (billing, fuel, invoices)','site, plan, actual',rows,a==='lakeside'?'91.5% of costs recorded; Kisiwa maintenance estimated':'Coverage not stated yet');}
 if(kind==='cov'){const c=OPS.lakeside.t.portfolio.coverage;return R('Cost coverage · Lakeside Power',pct(c.cost_recorded_share),'tenants[0].portfolio.coverage',`${usd(c.cost_recorded_usd)} recorded ÷ ${usd(c.cost_total_usd)} total cost = ${pct(c.cost_recorded_share,2)}. Total cost = diesel + maintenance + staff at the three sites; the one estimated line is Kisiwa maintenance (${usd(700)}).`,'Invoices and expense records','site, line, amount, status',[['Kobo','all cost lines',usd(2575),'Recorded'],['Kisiwa','diesel + staff',usd(3620),'Recorded'],['Kisiwa','maintenance',usd(700),'Estimated (invoice missing)'],['Mto','all cost lines',usd(1350),'Recorded']],'91.5%');}
 if(kind==='line'||kind==='cash'||kind==='liab'||kind==='pen'){const sk=a,s=S(sk),P=s.period,op=SITEKEY[sk][0],v=OPS[op].vertical,f=b;
  const pth=`${sitePath(sk)}.period.actual.${f}`;
  if(kind==='pen')return R('Kasarani · November penalties',usd(240),`${sitePath(sk)}.incident.november_to_date.penalties`,'2 missed departure blocks × $120','Fleet operations penalty notices','date, block, penalty',[['November to date','2 blocks',usd(240)]],'Recorded');
  if(kind==='liab')return R('Thika · batch exposed',usd(2160),`${sitePath(sk)}.incident.batches[0].exposed_value`,'Value of the batch held above its temperature limit. Exposure, not a loss.','Storage ledger (check-in) and chamber log','batch, customer, commodity, crates, in at, rate',[['B-1031','Kamau Cooperative','tomato','120','before 14 Oct','$0.20 / crate-day']],'Exposure','Emulated source');
  if(kind==='cash'){const fld={Collected:'collected','In transit':'in_transit',Outstanding:'outstanding'}[f];return R(`${siteName(sk)} · ${f.toLowerCase()}`,usd(P.actual[fld]),`${sitePath(sk)}.period.actual.${fld}`,`Billed ${usd(P.actual.revenue)} = collected ${usd(P.actual.collected)} + in transit ${usd(P.actual.in_transit)} + outstanding ${usd(P.actual.outstanding)}`,'Mobile-money settlement statement','txn_id, paid_at, settled_at, amount, customer_ref',[['(October statement)','2026-10','to 2026-11-02',usd(P.actual[fld]),'—']],'Recorded');}
  if(f==='variance')return R(`${siteName(sk)} · difference from plan`,usd(P.variance,true),`${sitePath(sk)}.period.variance`,'Site plan minus actual with no driver lines recorded; shown as not explained yet.','Utility invoice and plan line','line, plan, actual',[['Charging cost',usd(P.plan.energy_cost),usd(P.actual.energy_cost)]],'Coverage not stated yet');
  if(f==='plan'||f==='costplan')return R(`${siteName(sk)} · plan`,usd(f==='plan'?P.plan.contribution:(P.plan.total??P.plan.energy_cost)),`${sitePath(sk)}.period.plan`,'Monthly plan line for October.','Monthly plan / budget spreadsheet','site, period, line, amount',Object.entries(P.plan).filter(([k,x])=>typeof x==='number'&&!/kwh|_l$|share|pct|days|crate|max_kw|departures/.test(k)).map(([k,x])=>[siteName(sk),'2026-10',k.replace(/_/g,' '),usd(x)]),'Plan');
  if(f==='contribution'||f==='costactual'){const val=f==='contribution'?P.actual.contribution:(P.actual.total??P.actual.energy_cost);return R(`${siteName(sk)} · ${f==='contribution'?'contribution':'total cost'}`,usd(val),`${sitePath(sk)}.period.actual.${f==='contribution'?'contribution':(P.actual.total!==undefined?'total':'energy_cost')}`,f==='contribution'?`Revenue minus every cost line: ${Object.entries(P.actual).filter(([k])=>['revenue','diesel_cost','om','staff','energy','maint','liability'].includes(k)).map(([k,x])=>(k==='revenue'?'':'− ')+usd(x)).join(' ')} = ${usd(val)}`:`Sum of the cost lines = ${usd(val)}`,'Site economics (all lines)','line, amount',Object.entries(P.actual).filter(([k,x])=>typeof x==='number'&&/revenue|cost|om$|staff|energy$|maint|liability|maintenance|total/.test(k)).map(([k,x])=>[k.replace(/_/g,' '),usd(x)]),v==='mini'?Object.entries(P.coverage).map(([k,x])=>`${k}: ${SRC[x][0].toLowerCase()}`).join(' · '):'Coverage not stated yet');}
  const tariff=v==='mini'?OPS[op].t.prices.tariff_usd_per_kwh[s.site]:null,diesel=v==='mini'?OPS[op].t.prices.diesel_usd_per_l[s.site]:null;
  const M={
   revenue:()=>v==='mini'?R(`${siteName(sk)} · billed revenue`,usd(P.actual.revenue),pth,`${num(P.actual.billed_kwh)} kWh billed × $${tariff.toFixed(2)}/kWh = ${usd(P.actual.revenue)}`,'Customer billing export (prepaid vending and postpaid), CSV','customer_id, meter_id, period, kwh, tariff_code, amount, adjustment_code',[['(all customers)','—','2026-10',num(P.actual.billed_kwh),'residential',usd(P.actual.revenue).replace('$',''),'—'],...(P.actual.adjustments_kwh?[['(adjustments)','—','2026-10',`−${P.actual.adjustments_kwh}`,'—','—',sk==='mto'?'clinic allowance':'adjustment']]:[])],SRC[P.coverage.revenue][0],srcE,sk==='mto'?'<p class="d-note">A duplicate re-upload of this file adds no new rows. Six meters were re-pointed on 3 Oct (meter register, effective dates); 140 kWh shows as not billed, not as a loss.</p>':''):
    R(`${siteName(sk)} · storage revenue`,usd(P.actual.revenue),pth,`${num(P.actual.crate_days)} crate-days × $0.20 = ${usd(P.actual.revenue)}`,'Storage ledger (check-in and check-out per batch)','batch_id, customer, commodity, crates, in_at, out_at, rate',sk==='thika'?S('thika').incident.batches.map(x=>[x.batch,x.owner||'—',x.commodity,x.crates,'—',x.present===false?'2026-10-13 16:00':'—','0.20']):[['(October total)','—','—',`${num(P.actual.crate_days)} crate-days`,'—','—','0.20']],'Coverage not stated yet'),
   diesel_cost:()=>{const fb=P.fuel_balance;return R(`${siteName(sk)} · diesel`,usd(P.actual.diesel_cost),pth,`${num(P.actual.diesel_l)} L consumed × $${diesel.toFixed(2)}/L = ${usd(P.actual.diesel_cost)}${fb?.opening_dip_l!==undefined?`; consumed = opening dip ${fb.opening_dip_l} + deliveries ${num(fb.deliveries_l)} − closing dip ${fb.closing_dip_l}`:''}`,'Fuel delivery notes and tank dips','record, date, litres',fb?.opening_dip_l!==undefined?[['Tank dip (opening)','2026-10-01',fb.opening_dip_l],['Delivery notes (October total)','2026-10',num(fb.deliveries_l)],['Delivery note, recorded late','for 2026-10-26, recorded 2026-11-04','included above'],['Tank dip (closing)','2026-10-31',fb.closing_dip_l]]:[['Consumed (October)','2026-10',num(P.actual.diesel_l)]],SRC[P.coverage.diesel][0],srcE,sk==='kobo'?'<p class="d-note">One delivery note arrived 9 days late. October’s fuel balance was revised and the earlier version kept.</p>':'');},
   om:()=>R(`${siteName(sk)} · operations and maintenance`,usd(P.actual.om),pth,P.coverage.om==='ESTIMATED'?`Invoice not received: plan amount ${usd(P.plan.om)} carried as an estimate. Never shown as zero.`:'Monthly contract invoice.','Operations and maintenance invoices','invoice, period, amount, status',[[P.coverage.om==='ESTIMATED'?'(missing)':'(October invoice)','2026-10',usd(P.actual.om),SRC[P.coverage.om][0]]],SRC[P.coverage.om][0],srcE,sk==='kisiwa'?'<p class="d-note">One Kisiwa expense is invoiced in Kenyan shillings; it is converted at the declared monthly rate with the basis shown (rate not available yet in this mock-up), never added unconverted.</p>':''),
   staff:()=>R(`${siteName(sk)} · staff`,usd(P.actual.staff),pth,'Monthly staff cost for the site.','Expense records','period, line, amount',[['2026-10','staff',usd(P.actual.staff)]],v==='mini'?SRC[P.coverage.staff][0]:'Coverage not stated yet'),
   energy:()=>R(`${siteName(sk)} · electricity`,usd(P.actual.energy),pth,`${num(P.actual.kwh)} kWh × $0.20 = ${usd(P.actual.energy)}. Model at this occupancy: 1,550 + 0.25 × ${num(P.actual.crate_days)} = ${num(P.actual.kwh_model)} kWh.`,'Energy meter (hourly) and chamber controller','meter, period, kWh',[['Room meter','2026-10',num(P.actual.kwh)]],'Coverage not stated yet','Simulated demo data'),
   maint:()=>R(`${siteName(sk)} · maintenance`,usd(P.actual.maint),pth,'Monthly maintenance cost.','Invoices and receipts','period, amount',[['2026-10',usd(P.actual.maint)]],'Coverage not stated yet'),
   liability:()=>R('Thika · customer compensation',usd(P.actual.liability),pth,'6 crates downgraded by inspection × $18 = $108. Contract: we compensate inspection-confirmed damage when an excursion caused by our equipment exceeds 120 minutes (it lasted 135).','Quality inspection notes and credit notes','batch_id, inspected_at, crates_downgraded, inspector / credit note',[['B-1031','2026-10-15','6','QA inspector'],['Credit note CN-0412','2026-10','—',usd(108)]],'Recorded'),
   peak_cost:()=>R(`${siteName(sk)} · energy at peak price`,usd(P.actual.peak_cost),pth,`${num(P.actual.peak_kwh)} kWh × $0.24 = ${usd(P.actual.peak_cost)}`,'Utility invoice with time-of-use and demand lines','line, kWh or kW, rate, amount',[['Peak energy',num(P.actual.peak_kwh),'0.24',usd(P.actual.peak_cost)],['Off-peak energy',num(P.actual.offpeak_kwh),'0.12',usd(P.actual.offpeak_cost)],['Demand charge',`${P.actual.max_kw} kW`,'12.00',usd(P.actual.demand_cost)]],sk==='embakasi'?'Recorded':'Coverage not stated yet',srcE,`<p class="d-note">${sk==='embakasi'?'Tariff applicability is an assumption until confirmed from the real invoice.':'Ruiru’s rates are implied by its invoice lines (same as Embakasi’s tariff).'} Charger log sample: <code>StatusNotification · connector status, meter values · clock offset corrected where a charger clock runs fast</code>.</p>`),
   energy_cost:()=>R(`${siteName(sk)} · energy`,usd(P.actual.energy_cost),pth,sk==='kasarani'?`${num(P.actual.kwh)} kWh × $0.15 flat = ${usd(P.actual.energy_cost)}`:'Sum of invoice lines','Utility invoice','line, kWh, rate, amount',[['Energy (flat)',num(P.actual.kwh),'0.15',usd(P.actual.energy_cost)]],'Coverage not stated yet'),
   maintenance:()=>R(`${siteName(sk)} · maintenance`,usd(P.actual.maintenance),pth,'Monthly charger service fee line.','Vendor service tickets and invoices','period, amount',[['2026-10',usd(P.actual.maintenance)]],'Coverage not stated yet')};
  M.offpeak_cost=M.peak_cost;M.demand_cost=M.peak_cost;
  return M[f]();}
 if(kind==='bridge'){const sk=a,br=S(sk).period.bridge[+b],cost=OPS[SITEKEY[sk][0]].kind==='cost';const cl=CLASS[br.class][0];
  return R(`${siteName(sk)} · ${DRIVER[br.driver]}`,usd(cost?-br.amount:br.amount,true),`${sitePath(sk)}.period.bridge[${b}]`,pt(br.basis),br.class==='MODELLED'?'Forward replay of site data (energy management export, fuel records)':br.class==='DERIVED'?'Fuel or energy balance (consumed minus modelled)':'Invoices, billing or ledger records','driver, amount, basis',[[DRIVER[br.driver],usd(cost?-br.amount:br.amount,true),pt(br.basis)]],cl,br.class==='MODELLED'?'Simulated demo data':srcE);}
 if(kind==='opt'){const x=OPT[a],e=x.economics||{};const cost=b==='cost';
  const val=cost?optCost(x)[0]:optEffect(x)[0];
  const work={'KOB-STOPSOC':`Gross ${usd(e.gross_monthly)} (210 L × $1.25) − wear ${usd(e.wear_monthly)} = ${usd(e.net_monthly)} a month; × 12 − one-off ${usd(e.one_off)} (${e.one_off_detail}) = ${usd(e.net_12m)}`,'MTO-HULLER':`${usd(e.revenue_monthly)} (1,650 kWh × $0.30) − fuel ${usd(e.fuel_monthly)} − collection ${usd(e.collection_cost_monthly)} = ${usd(e.net_monthly)} a month; × 12 − ${usd(e.one_off)} = ${usd(e.net_12m)}`,'MTO-WELDING':`${usd(e.revenue_monthly)} (660 kWh × $0.40) − fuel ${usd(e.fuel_monthly)} = ${usd(e.net_monthly)} a month`,'KIRI-REPAIR':`$194 × 80% = ${usd(e.monthly)} a month; × 12 − $350 = ${usd(e.net_12m)}`,'KIRI-REPLACE':`${usd(e.monthly)} a month × 12 − $4,800 = ${usd(e.net_12m)}`,'EMB-DEADLINE':`$22,144.80 − ${usd(e.energy_cost_monthly)} = ${usd(e.saving_monthly)} a month; × 12 − ${usd(e.one_off)} = ${usd(e.net_12m)}`,'MWEA-AGG':`${usd(e.revenue_monthly)} (4,500 crate-days × $0.18) − energy ${usd(e.energy_monthly)} − handling ${usd(e.handling_monthly)} = ${usd(e.net_monthly)} a month; × ${e.months} − ${usd(e.one_off)} (${e.one_off_detail}) = ${usd(e.net_contract)}`,'KIS-BATT60':`${usd(x.monthly_fuel_saving_modelled)} a month × 12 − ${usd(x.capex)} = ${usd(x.net_12m)}`,'MTO-BILLING':`140 kWh × $0.40 = ${usd(e.charges_monthly)} a month; × 12 = ${usd(e.charges_12m)} billed (not collected)`};
  const detail=x.detail?`Breakdown: ${x.detail}.`:'';
  return R(`${OPT_LABEL[a]} · ${cost?'cost':'effect'}`,val,`${x._path}${cost?(x.capex!==undefined?'.capex':x.cost!==undefined?'.cost':x.residual_cost!==undefined?'.residual_cost':'.economics.one_off'):(e.net_12m!==undefined?'.economics.net_12m':'.economics')}`,cost?(detail||'Quoted cost.'):(work[a]||detail||'As stated by the option.'),cost?'Quotes, contract terms and price list':'Forward replay of site data and declared prices','option, figure, evidence',[[OPT_LABEL[a],val,optEvidence(x)]],cost?'Quoted':'Modelled, not realized','Simulated demo data');}
 if(kind==='clause'){const r=rights(a);return R(`${r.asset} · contract clause`,'—',r.path,'Reviewed extraction from the contract document (assisted, then checked by a person).','Contract documents (PDF) and reviewed extraction','obligation / condition / exception / notice / remedy, page reference',r.terms.map((t,i)=>[t,`clause ${i+1}, page reference shown in the pilot (illustrative here)`]),'Reviewed extraction','Emulated source','<p class="d-legal">This is not a legal decision. Coverage is decided by the supplier or insurer.</p>');}
 return R('Source records','—','—','Not available yet.','—','—',[],'—');
}
function openEvidence(key){const r=evidenceRecord(key);
 drawer(r.title,`<div class="d-evhead"><div class="d-herov">${r.value}</div>${badge(r.coverage,/Recorded/.test(r.coverage)?'green':/Estimated|Exposure/.test(r.coverage)?'amber':/Modelled|Quoted/.test(r.coverage)?'blue':'')}</div>
 <h3>Source records</h3><p><strong>${r.sys}</strong></p>${r.rows.length?`<div class="table-wrap d-scroll" tabindex="0" role="region" aria-label="Source record sample"><table class="d-src"><thead><tr>${r.header.split(', ').map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${r.rows.map(row=>`<tr>${row.map(c=>`<td>${c}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`:''}<p class="d-note">Source-shaped sample: rows show the record layout with October totals; customer-level rows are not reproduced in this mock-up.</p>${r.extra}
 <h3>How the figure is worked out</h3><p>${r.transform}</p>
 <h3>Coverage</h3><p>${r.coverage}</p>
 <h3>Where the data came from</h3>${provChips(r.prov)}<p class="d-note">Demo data only: nothing on this screen is field connected or from a client’s books.</p>
 <details class="tech"><summary>Fixture reference (for reviewers)</summary><pre class="code">${escapeHtml(r.path)}\nmanifest sha256 ${MANIFEST_SHA}</pre></details>`,true);}

/* ---------- v70 integration hooks ---------- */
function vnextPortfolioBanner(){return `<div class="notice blue d-banner">${icon('info')}<p><strong>New in vNEXT:</strong> the decision home leads with October results against plan, ranked choices and their evidence for three demo operators. This operations view is kept as it was and shows the earlier three-site demo estate. ${link('decide-lakeside','Open the decision home →')}</p></div>`;}
const VNEXT_CHANGED = {portfolio:'Changed: decision-home banner; Optimize card basis gains the period note (one finding’s exposure on the window’s last day, not a period total).'};
function vnextManifest(){return SCREENS.map(({render,...m})=>({...m,vnext_status:m.vnext?'Added':VNEXT_CHANGED[m.id]?'Changed':'Preserved',vnext_note:m.vnext?m.question:VNEXT_CHANGED[m.id]||''}));}
function vnextChanges(){drawer('What changed in vNEXT',`<p class="prose">vNEXT adds a decision layer on top of the v7.0 mock-up. Every v7.0 screen stays reachable.</p>${table(['Change','Where'],[
 ['New Decisions group at the top of the left menu; decision home is the default page','All screens'],
 ['Decision home, variance bridge, site economics (9), decision comparators (12), plan and budget, proof view and pilot request for 3 demo operators','Decisions'],
 ['Evidence drawer from every money figure','Decision screens'],
 ['Portfolio renamed “Operations view” in the menu; its page gains a link to the decision home','Operations view'],
 ['Optimize card states that its figure is one finding’s exposure on the window’s last day','Operations view'],
 ['Review bar: vNEXT label, this list, notes stored separately from v7.0, export includes the screen inventory','Review bar']])}<p class="d-note">Not approved: awaits owner inspection.</p>`,true);}

/* ---------- screen registration ---------- */
(function registerDecisionScreens(){
 const L=[],base={root:'Decisions',section:'',anchor:'Layer 4 · Deliverable 6',models:['DemoManifest'],domain:'mini',vnext:true,preserved:'v7.0 shell, rail, typography, palette, panels, tables, drawer and review bar.',adapted:'New decision layer over the Layer 4 demo manifest.',deferred:'No API wiring; figures are illustrative demo data.'};
 const add2=(o)=>L.push({...base,...o});
 Object.entries(OPS).forEach(([op,o])=>{
  add2({id:`decide-${op}`,op,dkind:'home',title:'Decision home',subtitle:`${o.name}: October 2026 against plan, what to do first, and the evidence behind it`,question:'What happened against plan, why, and what should we do first?',render:()=>homeScreen(op)});
  add2({id:`bridge-${op}`,op,dkind:'bridge',title:'Why we are off plan',subtitle:'Variance bridge from plan to actual, by site and driver',question:'Which sites and drivers explain the difference from plan, and how much is not explained yet?',render:()=>bridgeScreen(op),crumb:'Variance bridge'});
 });
 Object.keys(SITEKEY).forEach(sk=>{const op=SITEKEY[sk][0];add2({id:`econ-${sk}`,op,site:sk,dkind:'econ',title:`${siteName(sk)} · site economics`,subtitle:`${OPS[op].name} · plan against actual, with the ${OPS[op].vertical==='mini'?'energy-to-cash chain':OPS[op].vertical==='cold'?'occupancy-normalised energy':'departures and tariff'} behind it`,question:'Why did this site land where it did?',render:()=>econScreen(sk),crumb:'Site economics'});});
 DEC.forEach(d=>{const op=SITEKEY[d.site][0];add2({id:`choice-${d.id}`,op,site:d.site,dkind:'choice',title:d.title,subtitle:siteM(d.site).decision?.thread&&d.id!=='kobo-battery'&&d.id!=='mto-inverter'&&d.id!=='mto-billing'?`Question: ${siteM(d.site).decision.thread.replace(/GEN-KS-0(\d)/g,'generator $1')}`:'Compare every option, including doing nothing',question:d.title,render:()=>choiceScreen(d),crumb:'Decision'});});
 Object.entries(OPS).forEach(([op,o])=>{
  add2({id:`plan-${op}`,op,dkind:'plan',title:'Plan and budget',subtitle:'The recommended set within budget and visits, what was left out and why',question:'Which options fit the budget and crews, and what changes if the budget changes?',render:()=>planScreen(op),crumb:'Plan and budget'});
  add2({id:`verify-${op}`,op,dkind:'verify',title:'Proof it worked',subtitle:`${OPT_LABEL[o.verifyOpt]}: three separate answers`,question:'Did the change happen, did the money arrive, and was it the change?',render:()=>verifyScreen(op),crumb:'Verification'});
  add2({id:`pilot-${op}`,op,dkind:'pilot',title:'Pilot request',subtitle:'A bounded paid diagnostic on your own records',question:'What would a diagnostic need from us and deliver?',render:()=>pilotScreen(op),crumb:'Pilot request'});
 });
 SCREENS.unshift(...L);
})();
window.mockupManifest=vnextManifest();

/* ---------- interactions ---------- */
document.addEventListener('click',e=>{
 const el=e.target.closest('button,a');if(!el)return;
 if(el.dataset.evd){e.preventDefault();openEvidence(el.dataset.evd);return;}
 if(el.dataset.role){DSTATE.role=el.dataset.role;render();document.querySelector(`[data-role="${DSTATE.role}"]`)?.focus();return;}
 if(el.hasAttribute('data-vnext-changes')){vnextChanges();return;}
 if(el.dataset.example){toast(el.dataset.example);return;}
});
document.addEventListener('change',e=>{
 if(e.target.id==='op-switch'){const s=currentScreen(),op=e.target.value;DSTATE.op=op;const kind=['home','econ','choice'].includes(s.dkind)?'decide':{bridge:'bridge',plan:'plan',verify:'verify',pilot:'pilot'}[s.dkind];location.hash=`/${kind}-${op}`;return;}
 if(e.target.dataset.budget){DSTATE.budget.lakeside=e.target.dataset.budget;render();document.querySelector(`[data-budget="${DSTATE.budget.lakeside}"]`)?.focus();}
});
document.addEventListener('submit',e=>{if(e.target.matches('[data-pilot-form]')){e.preventDefault();toast('Example only: no request was sent.');}});
render();
