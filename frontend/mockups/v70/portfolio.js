/* Portfolio composition: presentation of site-owned results, never a second analytic. */
const portfolioReview = {
 references:['v6.9 §8.1, p24: Portfolio command center','Client Demo Recommendation, Screen 1 and Appendix A1, p11'],
 decision:'v7.0 (commercial capability architecture rev 5): the objective matrix becomes outcome rows (owner-approved change); value cards carry their outcome codes; ranked rows say which outcome each finding moves; signals not yet priced appear beside the evidence prompt. Everything else is the v6.9 Portfolio.',
 sections:[
  ['Assessment and estate scope','PortfolioSummary','Deterministic roll-up of selected site assessments; no numeric composite health score.'],
  ['Value cards','PortfolioConsequenceRollup','Reuse site consequence revisions, periods, currencies and basis. Different categories are not additive.'],
  ['Ranked Findings','FindingIndex + ActionSummary','Priority orders Finding objects. Site, Finding and accepted Action links change to their own roots.'],
  ['Outcomes across the estate','Outcome status per site (rev 5 §4.2, §6.1)','One cell per site and outcome: its own outcome, status from the seven-state rule, and Declared where an objective is set. Not assessed yet and not applicable remain distinct.'],
  ['Productive-use opportunity','RenewableOpportunityWindow + FinancialConsequence','Reuse eligible window and declared tariff; electrical headroom is not proven demand.'],
  ['Change and verification','FindingRevision + WorkSummary + VerificationSummary','Event counts and outcome state are separate; activity completion cannot establish recovered value.']
 ],
 deferred:'Six-site estate, monthly extrapolation, productive-use share, comparable energy roll-up, asset valuation, reconciliation residual and verified recovered money require their own supporting records. None is inferred from this hour.',
};
function portfolioDesignNotes(){return `<div class="review-section"><strong>Portfolio revision · reference comparison</strong><p>${portfolioReview.references.join('<br>')}</p><p style="margin-top:10px">${portfolioReview.decision}</p><p style="margin-top:10px"><a href="previews/portfolio-previous.png" target="_blank">Compare the previous Portfolio mockup ↗</a></p></div><details class="review-section"><summary>Section ownership for implementation</summary>${table(['Visible section','Owner / read model','Contract'],portfolioReview.sections)}</details>`;}
function portfolioRows(lens='All priorities'){
 const rows=[
  {kind:'Risks',site:'cold',name:'GreenHarvest',domain:'Cold-chain',finding:'cold-finding',title:'Backup response failed',id:'F-118',mechanism:'Automatic start failed; cooling interrupted',impact:'Product conditions exposed',basis:'Measured peak 8.2°C · loss unpriced',window:'6 Oct · 19:00–20:00',priority:'High',tone:'red',confidence:'High',limit:'Observed sequence',action:'cold-action',actionId:'ACT-051',next:'Witness an automatic-start test',state:'Open'},
  {kind:'Cost',site:'mini',name:'Kobo',domain:'Mini-grid',finding:'finding',title:'Extended generator support',id:'F-104',mechanism:'30 min candidate; charging trade-off remains',impact:money(),basis:'Modelled fuel + scenario maintenance',window:'6 Oct · 14:20–15:20',priority:'High',tone:'amber',confidence:'Low',confKey:'f104',limit:'PCS capability gap',action:'verification',actionId:'ACT-048',next:'Verify the policy trial',state:'Outcome pending'},
  {kind:'Risks',site:'ev',name:'Depot',domain:'EV charging',finding:'ev-finding',title:'Charging session interrupted',id:'F-130',mechanism:'Fault-aborted session; root cause unknown',impact:'1 interrupted session',basis:'Measured events · revenue loss unpriced',window:'6 Oct · 08:00–16:00',priority:'Medium',tone:'blue',confidence:'Medium',confKey:'f130',limit:'1 other outcome unknown',action:'ev-action',actionId:'ACT-061',next:'Investigate connector 2',state:'Open'},
  {kind:'Risks',site:'cold',name:'GreenHarvest',domain:'Cold-chain',finding:'cold-finding-excursion',title:'Temperature excursion',id:'F-119',mechanism:'Chamber above 4°C after backup failed',impact:'25–35 min above policy',basis:'Measured peak 8.2°C · no spoilage determination',window:'6 Oct · 19:00–20:00',priority:'Medium',tone:'blue',confidence:'High',limit:'Stock and loading not recorded',action:null,next:'Record stock and connect the door log',state:'Open'},
  {kind:'Risks',site:'mini',name:'Kobo',domain:'Mini-grid',finding:'evidence',title:'Battery output-limit report missing',id:'F-108',mechanism:'One 14:50 report absent from the battery controller',impact:'30 min unclassified',basis:'Evidence gap · limits F-104',window:'6 Oct · 14:20–15:20',priority:'Medium',tone:'blue',confidence:'High',limit:'Reporting cause unknown',action:'sitework',actionId:'ACT-049',next:'Restore battery-limit reporting',state:'Open'},
  {kind:'Opportunities',site:'mini',name:'Kobo',domain:'Mini-grid',finding:'opportunity-finding',title:'Productive-use headroom',id:'F-109',mechanism:'Recurring renewable capacity available',impact:'18–20 kW usable',basis:'Modelled headroom · $2.50 scenario sales',window:'Separate 5-day study · 3 eligible days',priority:'Medium',tone:'green',confidence:'Medium',confKey:'f109',limit:'Demand not established',action:null,next:'Evaluate a 10 kW productive load',state:'Recommendation'}
 ].filter(r=>lens==='All priorities'||r.kind===lens);
 return table(['Site','Finding / operating mechanism','Value / consequence','Priority','Confidence','Action / next move'],rows.map(r=>[
  `${link(r.site,r.name,'strong')}<small>${r.domain}</small>`,
  `${link(r.finding,r.title,'strong')}<small>${r.id} · ${r.mechanism}</small>${movesLine(r.id)}`,
  `<strong class="impact ${r.tone}">${r.impact}</strong><small>${r.basis}</small><small>${r.window}</small>`,
  badge(r.priority,r.priority==='High'?'amber':'blue'),`${r.confKey?conf(r.confKey,''):badge(r.confidence)}<small>${r.limit}</small>`,
  `${r.action?link(r.action,r.actionId,'strong'):link(r.finding,'Review recommendation','strong')}<small>${r.next}</small><span class="workflow-text">${r.state}</span>`
 ]));
}
function portfolioValue(label,value,detail,basis,target,tone,ico){return `<a class="value-card ${tone}" href="#/${target}"><div class="value-label">${icon(ico)}<span>${label}</span>${icon('arrow')}</div><div class="value-number">${value}</div><p>${detail}</p><div class="value-basis">${basis}</div></a>`;}
function objectiveCell(label,tone,target){return `<a href="#/${target}" class="objective-cell ${tone}" aria-label="${label}">${label}</a>`;}
function portfolioObjectives(){return `<div class="objective-matrix"><div class="matrix-head"><span>Objective</span>${link('mini','Kobo')}${link('cold','Cold room')}${link('ev','Depot')}</div>${[
 ['Service / product',objectiveCell('Unknown','unknown','service'),objectiveCell('Attention','attention','temperature'),objectiveCell('Attention','attention','sessions')],
 ['Backup',objectiveCell('Unknown','unknown','backup'),objectiveCell('Degraded','degraded','coldbackup'),objectiveCell('N/A','na','ev-foundation')],
 ['Asset condition',objectiveCell('Watch','attention','asset'),objectiveCell('Investigate','attention','cold-health'),objectiveCell('Unknown','unknown','ev-health')],
 ['Cost control',objectiveCell('Review','attention','financials'),objectiveCell('Unassessed','unknown','cold-financials'),objectiveCell('Unassessed','unknown','ev-financials')],
 ['Evidence',objectiveCell('Limited','limited','evidence'),objectiveCell('Limited','limited','cold-evidence'),objectiveCell('Limited','limited','ev-evidence')]
 ].map(r=>`<div class="matrix-row"><span>${r[0]}</span>${r.slice(1).join('')}</div>`).join('')}</div><p class="chart-note">Site-owned assessments · Unknown is not healthy.<br>N/A means no configured objective. Select any cell for context.</p>`;}
function portfolioScreen(){return `<div class="portfolio-v2">${buildOrderNote()}
 <div class="portfolio-context"><div>${badge('Portfolio: Needs attention','amber')}<span>3 simulated sites · 1 mini-grid / 1 cold room / 1 charging hub</span></div><button class="claim-link" data-portfolio-scope>Assessment scope & periods ↗</button></div>
 <div class="value-grid">
 ${portfolioValue('<span class="oc-ocode">O2</span>Operating-cost exposure',money(),'Kobo · 30 min avoidable generator time','Modelled + scenario · one-hour window','financials','amber','money')}
 ${portfolioValue('<span class="oc-ocode">O3</span>Service & stock risk','2 sites',`Cold-room excursion + interrupted charging · ${SIGNALS.filter(x=>x.dir==='risk'&&VO[x.code][1]==='O3').length} risk signals`,'Measured events · not priced','signals','red','finding')}
 ${portfolioValue('<span class="oc-ocode">O1</span>Productive-use opportunity','18–20 <small>kW</small>','Kobo · headroom on 3 of 5 days','Modelled · demand validation remains','renewable','green','sun')}
 ${portfolioValue('<span class="oc-ocode">O4</span>Asset life',`${SIGNALS.filter(x=>x.dir==='stress').length} <small>early stress warnings</small>`,'Battery below reserve · overdue servicing · charger fault','Not a condition assessment · not priced','signals','purple','asset')}
 ${portfolioValue('<span class="oc-ocode">O6</span>Verified value recovered','Not established','Intervention outcomes need more evidence','Completed work does not establish savings','globalfinancials','neutral','check')}
 </div>
 <div class="portfolio-pulse"><span>${icon('site')}<strong>3</strong> priority sites</span><span>${icon('sun')}<strong>1</strong> opportunity</span><span>${icon('evidence')}<strong>3</strong> site evidence gaps</span><span>${icon('action')}<strong>3</strong> accepted actions</span><span>${icon('finding')}<strong>${SIGNALS.length}</strong> signals not yet priced</span><span class="pulse-note">Distinct consequence categories · no combined savings total</span></div>
 <div class="portfolio-main">
 <section class="panel priority-panel"><div class="panel-head"><div><h2>Where management should act first</h2><p>Findings ranked by consequence and urgency, with evidence confidence alongside.</p></div><span class="eyebrow">6 findings</span></div>
 <div class="portfolio-lenses" aria-label="Finding lens">${['All priorities','Cost','Risks','Opportunities'].map((label,i)=>`<button class="chip ${i===0?'active':''}" data-portfolio-lens="${label}" aria-pressed="${i===0}">${label}</button>`).join('')}<span id="portfolio-result-count">6 findings</span></div>
 <div id="portfolio-findings">${portfolioRows()}</div><div class="panel-bottom">${link('findings','Open all Findings →')}<span>Priority and confidence answer different questions.</span></div></section>
 <aside class="portfolio-side">${panel('Outcomes across the estate',portfolioOutcomes(),'Each site’s own reading · not a composite health score')}
 <section class="portfolio-evidence"><div>${icon('evidence')}<h3>Evidence that would change a decision</h3></div><p>Restore Kobo’s missing PCS capability report to resolve two indeterminate dispatch intervals.</p>${link('evidence','Inspect the constraint →')}</section>${portfolioSignals()}</aside>
 </div>
 <div class="portfolio-bottom"><section class="panel opportunity-panel"><div class="panel-head"><div><div class="eyebrow">GROW USEFUL DEMAND</div><h2>An opportunity beyond reducing cost</h2></div>${badge('Scenario','green')}</div><div class="opportunity-story"><div><span class="opportunity-quantity">10 <small>kW × 1 h</small></span><p>Grain-mill evaluation at Kobo</p></div><span class="story-arrow">→</span><div><span class="opportunity-quantity">$2.50</span><p>Scenario gross sales per eligible window</p></div></div><p class="chart-note">Within 18–20 kW headroom · $0.25/kWh assumed tariff · before costs. Validate demand and service guardrails before committing.</p><div class="panel-bottom">${link('opportunity-finding','Review opportunity Finding →')}${link('renewable','Inspect physical headroom →')}</div></section>
 <section class="panel progress-panel"><div class="panel-head"><div><div class="eyebrow">CLOSE THE LOOP</div><h2>What changed in this review</h2></div><button class="claim-link" data-portfolio-progress>Inspect basis ↗</button></div>
 <div class="change-line"><span class="change-dot blue"></span><strong>1 maintenance activity completed</strong><span>Outcome unverified</span></div>
 <div class="change-line"><span class="change-dot amber"></span><strong>1 policy trial awaiting outcome evidence</strong><span>Guardrails incomplete</span></div>
 <div class="change-line"><span class="change-dot gray"></span><strong>0 verified resolutions in these examples</strong><span>Value not yet recovered</span></div>
 <div class="outcome-note">Observed change → comparable evidence → verified outcome → eligible financial value</div></section></div>
 <div class="portfolio-context-footer"><span>Business context: Depot delivered <strong>120 kWh</strong> in complete records; <strong>$36.00</strong> scenario tariff estimate.</span>${link('energy','Inspect energy basis →')}<span>Other sites lack comparable full-window energy coverage.</span></div>
 </div>`;}
