# Register reconciliation (final complete review, part: register reconciliation)

Source: `.agent/mock-departure-register.md` at main 5f71f6c9 (read-only; no tests, builds or servers run). Parsed with a script: every line starting `| R<n>`.

## 1. Parse result

- Rows parsed: **405** (IDs R01..R470, unique; no duplicate IDs; no malformed rows: 109 rows in the original 9-column tables, 296 rows in the 6-column 'Post-W6 audit Architect rulings' table).
- Rows by category (all statuses): Backlog (non-departure) 1, D1 133, D2 72, D3 140, D4 53, D5 6.
- Status by category (open = standing; 'standing' for D1/D2/D4/D5 means the departure still exists in the app, whatever the word planned/built/open):
  - Backlog (non-departure): open/standing 1
  - D1: open/standing 132, closed 1
  - D2: open/standing 70, superseded 1, closed 1
  - D3: resolved 6, withdrawn 1, open/standing 119, closed 14
  - D4: open/standing 53
  - D5: resolved 5, open/standing 1

### Anomalies in the register itself

1. **Header and category table are stale.** The header says 109 distinct rows / 103 open / 5 resolved / 1 withdrawn and the category table totals 369 (D1 119, D2 61, D3 137, D4 47, D5 5, D6 0). Actual: 405 rows (D1 133, D2 72, D3 140, D4 53, D5 6, backlog 1). The shell card packet already noted the count table was not updated for R375-R382; nobody updated it afterwards.
2. **117 D3 rows still read `open` although their card is merged** (see section 2). Only W5-cold (R334, R336-R339, R344, R460, R461), W5-EV (R345-R350, R470 as D2), R373 and the older W5-F1 rows were closed in place. The shell, W1-a, W1-b, W2-cold, W2-EV, W3, W4 and W6 cards never wrote closure into the register. The Architect's audit-ruling table rows (R114-R373) carry status `open` / `Fix in <card>` text that was never replaced.
3. **Split parents left open.** Where a D3 row was split into a D3 fix plus a standing departure, the parent D3 row (R149, R157, R159, R170, R186, R187, R190-R192, R196, R253/R254 etc.) still says `open` while the child (R380, R387, R388, R381, R389-R394, R435-R437) carries the live departure. Closing the parents is a pure status edit.
4. **'planned' status is stale.** 60 non-D3 rows still say `planned` (R01-R11, R13-R15, R17-R19, R46, R49, R51, ... W5-01..W5-04, W6-01 rows) although those slices are built and merged. They are standing departures either way; only the word is out of date. A further 23 say `built`/`built; audit verified`; 14 rows say `ruled correction`, `ruled pre-flight` or `ruled build-time`.
5. **Same departure listed twice:** R207 and R224 (Action tab 'Application' vs 'Execution'; R224 says 'No register row found' and R207 says the same). R395 is correctly marked superseded by R383 (kept for traceability).
6. **Closure wording thin on a few rows:** R460 closed with 'classes tested' but no paired capture cited (packet says the colours rely on W4's styles; reviewed via tests only); R23/R24 `resolved` and R32/R33 `resolved` carry no commit or capture reference; R373 `resolved (merged 2026-10-25)` has no hash (merge is 85be95de; verification in `.agent/post-W6-R373-coordinator-verification.md`, recaptures 36/36). R344 closed with a disclosed capture gap (linked 'cancelled' case has no producer mode). R40 closed 'for built depth destinations' with remaining link defects tracked as D3 (those are the audit rows R319 etc.).
7. **R111 (D4)** says `built; owner approval pending`; R382-R385 and R396 say `open pending owner decision`; R453 says `open (owner)`. All are standing owner items and are in the owner list.
8. **ID gaps are intentional:** R61-R64 (renumbered to R65-R73 on 2026-10-23), R397-R419 (reserved for W6, only R396 used), R422-R434 (W2-EV reserved), R438-R449 (W2-cold reserved), R455-R459 (W4), R462-R469 (W5-cold), R471-R479 (W5-EV). None of the reserved blocks was exceeded; no ID collisions.
9. Every open D1/D2/D4/D5 row in the 6-column audit table carries a `MOCK DEVIATION` label sentence in its text (script check: no row of that kind lacks one, and no D3 row carries one; label letters match the category column on every row).

## 2. D3 rows

- D3 rows: 140. Closed/resolved/withdrawn in the register: 21 (R22, R23, R24, R37, R38, R60 withdrawn, R334, R336-R339, R344-R350, R373, R460, R461).
- D3 rows still `open`: **119**. Of these **2 are genuinely open** and **117 are stale status** (the card merged with review ACCEPT; the register was not updated).

### 2a. Genuinely open D3 rows

| ID | Card that should close it | Why still open | Verdict |
| --- | --- | --- | --- |
| R328 (B13-11, mini Alternatives crumb) | W4-mini | W4 build ruling 1: the crumb now reads `Finding` (never 'Finding code unavailable'), but the proper `Findings > {code} > Alternatives` crumb needs a backend change exposing a public Site-scoped Finding code on the mini Finding read. W4 packet: 'R328 stays open (backend public-code dependency)'. Backlog item (c). | Open by Architect ruling; needs a backend slice. Not a W4 miss. Owner-visible meanwhile: breadcrumb shows only 'Finding'. |
| R374 (security) | none (out of scope of every card) | Registered by the R373 rulings (Q4) and review L1: estate and some Site reads combine with `development_access`; needs a separate security audit and slice before real user roles. Not a mock departure; carries category D3 by the register's convention. Backlog item (d). | Open by design; a pre-launch gate, not a UI defect. |

### 2b. Stale-open D3 rows by card (card merged; closure confirmed from packet/review)

| Card | Merge | D3 IDs on the card | Register still `open` | Closure evidence |
| --- | --- | ---: | --- | --- |
| shell-typography-copy | 4fc39160 | 16 | R115, R119, R120, R125, R127, R129, R130, R133, R140, R141, R149, R151, R152, R170, R203, R319 | shell packet + capture review ACCEPT + closeout rulings; 346/370 recapture pairs qualifying, 24 pairs disclosed as capture gaps after a permission refusal (later batch 10-12 recapture a6424de2: 370/370 qualifying) |
| W1-mini-Action-a | 3b4979d0 | 18 | R156, R157, R159, R164, R171, R178, R184, R185, R186, R187, R188, R189, R190, R191, R192, R193, R195, R196 | W1-a review ACCEPT after fix rounds; 98-pair recapture + probe; two caps stress cases not met were ruled by caps2 rulings |
| W1-mini-Action-b | 9147cdd5 | 18 | R197, R198, R199, R200, R201, R202, R204, R205, R209, R218, R219, R220, R221, R222, R223, R228, R229, R230 | W1-b review ACCEPT; caps per W1-b caps rulings |
| W2-cold | 4d51df61 | 14 | R241, R242, R244, R245, R246, R247, R249, R253, R254, R255, R256, R258, R259, R261 | W2-cold review ACCEPT + fix round (refusal disclosure; one-sentence Finding refusal per Architect ruling); R435-R437 labelled |
| W2-EV | 09196de0 | 14 | R265, R267, R268, R270, R271, R275, R276, R280, R281, R283, R284, R285, R286 | W2-EV review ACCEPT + fix round (R420/R421 labels, alert role, zone-unavailable headers) |
| W3-estate | d9a73b80 | 9 | R293, R294, R295, R296, R297, R300, R302, R307, R308 | W3 review ACCEPT-with-findings (M1 Medium: R295 column) then fix round + coordinator history rebuild; fix round recapture `post-W6-W3-estate-recapture/fix-round`. The packet and review cite rulings by Q-number, not R-ID, so R293/R294/R296/R297/R300/R302/R307/R308 are not named individually; they map to rulings Q5, Q7, Q12, Q10/Q4, Q11, Q12, Q13, Q14. |
| W4-mini | 7dfd8f4e | 15 | R309, R310, R311, R312, R313, R316, R318, R320, R321, R322, R324, R325, R331, R333 (R328 genuinely open, above) | W4 packet (R309-R333 listed done), final checks; no standalone review file in .agent, but backlog records W4-mini review Lows (fresh review happened); one deliberate exception R328 (above) |
| W5-cold-Work | c7d03073 | 6 | none | closed in the register |
| W5-EV-Work | 77bd20c3 | 5 | none | closed in the register |
| W6-global-Work | 14696fda | 15 | R352, R353, R354, R356, R357, R359, R360, R361, R364, R366, R367, R368, R370, R371, R372 | W6 review ACCEPT + fix round; backend suite 4063+1 |

Stale-open total: 117 (matches 119 open minus R328 and R374). Cross-check: every ID on every card was found mentioned in that card's packet/review/handoff text, except W3 (cited by Q-number, see above) and R347 (owned by W2-EV mechanism, closed by W5-EV; closed in the register).

Recommended action (not done; read-only): flip these 117 rows to `closed in <card> (merge <sha>)` and add R328 and R374 as the only open D3 rows. Refresh the header counts and category table.

No D3 row is open because a card missed it. Cards' own recorded misses were fixed in fix rounds before merge (W3 M1, W2 refusal disclosure, W5-EV R350 scope, W1-a caps). Disclosed unmet capture items (not D3 rows): W5-cold R344 'cancelled' linked state has no producer mode; W4 EV worst-case mode refused by the producer; shell 24 capture gaps (later closed by batch 10-12).

## 3. Owner list: open owner-visible departures

Counts of standing (not closed/resolved/superseded) rows: **D1 132, D2 70, D4 53, D5 1**, total **256**. D6: 0 rows. Backlog (non-departure): 1 (R386). Note R207/R224 are the same departure, so 255 distinct decisions.
Decision hints: D1 = a thing the design shows that the app cannot yet show because the information or feature does not exist (shown as 'Not available yet' or an honest gap). D2 = the app does something better or different on purpose; owner can approve or reject. D4 = the design's example wording or numbers are replaced by real stored values. D5 = temporary until a later piece is built (R394 only).
Owner-decision flags: R382, R383, R384, R385 (D2) and R396 (D1) are `open pending owner decision`; R453 is `open (owner)`; R111 `owner approval pending`.

### Whole app: top bar, menu and page chrome  (D1 4, D2 3, D4 0, D5 0)
- R114 (D1): The design has a top bar (organisation name, screen search, Site picker, date window picker, avatar). The app has none; each page has its own small date controls instead. No source for these exists yet.
- R116 (D2): On a phone the design shows a white top bar and hides the side menu; the app shows a dark band with a Menu button instead.
- R117 (D1): In the side menu, Assets and Settings say 'Not available yet' (design shows them live), the 'Demo workspace' footer is missing, and the lab link wording differs.
- R118 (D2): Setup pages show an extra status line (version picker, 'as of' time, 'how this was worked out') and 'Advanced details' sections the design does not have; added so readers can see what the page is based on.
- R153 (D1): Pages use their own small date controls (UTC day, From/To) instead of the design's top-bar date window.
- R154 (D1): Status strips on Overview, Evidence, Dispatch, Analysis and Health show different chips and links than the design (e.g. no 'Needs attention / Confidence' chips) because no stored assessment exists to fill them.
- R453 (D2): On narrow screens the row of Site tabs wraps onto two lines showing every label, instead of scrolling sideways as in the design. **[owner decision pending]**

### Sites list  (D1 4, D2 0, D4 4, D5 0)
- R121 (D1): The 'Directory / Add site / From template / Batch upload / Setup history' tab row is absent; a button to create a site in the Simulator Lab stands in.
- R122 (D4): Type filter chips show only 'All sites' and 'Mini-grid only'; the design also offers Cold-chain and EV charging.
- R123 (D1): The 'Needs attention' and 'Evidence limited' count cards say 'Not available' with a reason; the design shows numbers.
- R124 (D1): The design's Assessment, Top issue, Evidence and Last analysed columns are merged into one 'Operating view: Not available yet' column; no site-level assessment exists yet.
- R126 (D1): In the 'sites in setup' list, the design's add buttons and columns (Created by, State, Next step) are replaced by a simpler Lifecycle column.
- R375 (D4): The page subtitle reads 'Every site configured in this build.' instead of the design's wording.
- R376 (D4): The data badge says 'Demonstration data' rather than 'Simulated'; colour now matches the design.
- R378 (D4): No closing note on the Sites and single-line-diagram pages; the design's note claims things these pages do not show.

### Site setup pages (mini-grid): Foundation, Readiness, Single line diagram, Changes, Asset  (D1 13, D2 5, D4 3, D5 0)
- R128 (D2): Panel title reads 'Identity and operating obligations' instead of '... & ...'. Wording change already approved earlier; recorded for completeness.
- R131 (D1): The control table has five rows instead of four (adds critical service order) and some cells are plain text where the design has links.
- R132 (D2): A working 'Change the battery reserve' form sits in the control panel; the design has no form there, and the panel is taller as a result.
- R134 (D4): The gateway panel title uses the real gateway name instead of the design's example name.
- R135 (D1): Readiness table has six areas instead of five, different area names and a 'Next step' column instead of 'Owner', plus a few note lines.
- R136 (D1): Gateway panel lacks the contact timeline bar; availability and completeness say 'Not available'; adds a registration block.
- R137 (D1): The single-line-diagram panel title has no '- AC-coupled mini-grid' suffix; the subtitle says the topology type is not stated.
- R138 (D1): Circuit breakers, feeder meters, the monitoring row and reporting dots are absent on the diagram; each part says readings are not assessed here.
- R139 (D1): The 'What each part does' table lists ten per-part rows with ratings and channels instead of the design's four grouped rows.
- R142 (D1): When no change (or an unknown change) is selected, the Changes page shows a notice and short gap lines instead of the design's strip, four figure cards and list.
- R143 (D1): The Asset page lacks the design's asset-centred frame (Assets menu entry, asset breadcrumb, asset tabs).
- R144 (D2): Third panel is titled 'Condition evidence and its limits' instead of '... and claim boundary'.
- R145 (D1): Reserve exposure and Power stress say 'Not available'; the weekly bars are replaced by a simple list.
- R146 (D1): Interpretation shows three missing inputs instead of two actions; the 'Create test action' and 'Review capability gap' links are absent.
- R147 (D1): The warranty callout is replaced by a plain note that 'Unknown' means not yet measurable, with a Back to Health link.
- R148 (D4): The Asset page heading is 'Battery energy storage' (the stored name) instead of 'Kobo battery', and no asset code is shown.
- R150 (D1): On an applied change, the table has two rows instead of four and Target/Guardrail cards say 'Not recorded yet'; the outcome says no verification.
- R377 (D2): Topology cards show one icon per declared part with clickable part names instead of the design's single centred icon. Proposed improvement.
- R379 (D1): When a change has no stored target or guardrails, the cards say 'Set in the plan / Plan details are not available yet' instead of values.
- R380 (D4): If a battery is unnamed or the read is refused, the heading stays a generic 'Battery'.
- R382 (D2): On phones the single-line diagram shrinks to fit and a small 12 px part key with buttons is added below it; the design has no key. Proposed improvement. **[owner decision pending]**

### Mini-grid Site Overview and Performance (Overview, Evidence, Dispatch, Analysis, Health, Renewable, Service, Scenarios)  (D1 30, D2 7, D4 3, D5 0)
- R155 (D4): Page subtitle says 'Overview - operating objectives for the selected period' instead of the example plant description.
- R158 (D1): 'What happened in the selected hour' reads a whole day with an 'Hour not selected' state instead of the design's five-event hour timeline.
- R160 (D4): 'Needs attention' shows one finding item plus an overlap line instead of three numbered items with links.
- R161 (D2): The money range reads '0.00 to 15.82 USD' (a bounded range) with the link in the panel head, instead of the design's single example figure.
- R162 (D1): The 'Next step' offers a secondary 'Open the Finding' button and a Dispatch link instead of a primary 'Review recommendation' button.
- R163 (D2): An extra closed section 'Site record: identity, provenance and actions' is added at the bottom.
- R165 (D1): 'What we can conclude now' shows readings-arrived bars and notes instead of the design's five-row capability table.
- R166 (D1): 'Data sources' shows status facts and a source table instead of the design's per-source quality table.
- R167 (D1): 'Most useful next evidence' says a ranking is not available yet and lists sources with no readings, instead of a ranked list.
- R168 (D1): The bottom notice drops the first sentence about managed actions.
- R169 (D2): Panel 2 is titled 'How each limit is set' instead of 'How a claim limit is set' (approved earlier).
- R172 (D2): A third row of tabs (Overview / Analysis) sits under the Performance tabs; the design reaches Analysis through a link.
- R173 (D2): Metric cards read 'Needed / Possibly avoidable / Cannot determine' instead of 'Candidate avoidable / Necessary / Indeterminate'.
- R174 (D1): Sources and 15-minute blocks use a generator bar and a 22-30 tile grid instead of the design's kW chart and four tiles.
- R175 (D1): 'Selected block' shows bullets and period facts instead of key/value rows with 'Observed/Declared' tags and a link to the finding.
- R176 (D1): The amber notice about generator charging not being a demonstrated saving is absent.
- R177 (D1): The sample-coverage table has different columns (Input / Set up / Accepted readings / Not good quality) and 11 rows.
- R179 (D1): The Analysis page shows the same three-panel layout as Performance instead of the design's finding-analysis context.
- R180 (D1): The constraint comparison has different columns and up to 30 rows plus three explanation cards.
- R181 (D1): The bounded fuel calculation block says no fuel quantity, saving or money claim is available yet.
- R182 (D1): Coverage, confidence and alternatives is a list and a versions list instead of the design's four-row table.
- R183 (D1): Physical asset condition shows one battery row (design shows battery, generator and inverter); 'Open findings/work' say 'Not recorded'.
- R231 (D1): Site Work actions table: Owner and Success criterion say 'Not recorded'; source reads 'Finding, version N'.
- R232 (D1): Extra states with no design equivalent: no actions in window, no window chosen, invalid window.
- R314 (D1): Renewable and Service pages show some links as 'Not available yet' even though the destinations exist, unless a window holds exactly one day.
- R315 (D1): Example content (grain-mill scenario, 'Day N') is replaced by honest states such as 'No productive-use scenario has been assessed' and dated rows.
- R317 (D1): Some load and backup labels show raw asset codes (e.g. load-clinic) because no friendlier name is stored.
- R323 (D2): Every incident or maintenance row carries a 'UTC and IDs' link the design lacks. Proposed improvement.
- R326 (D4): Scenarios list shows real authored rows with different columns and says scenario creation is unavailable.
- R327 (D1): A reversed date window shows only 'Select a valid Site-local window.'; it is not yet proved whether other bad windows behave the same.
- R329 (D1): On the Opportunity page the 'Findings' breadcrumb is a disabled sentence saying global Findings are unavailable.
- R330 (D1): Opportunity cards say 'scenario name unavailable', 'Scenario energy: Unavailable' and 'Tariff: Unavailable' where the design shows figures.
- R332 (D1): With five incidents the panel is 1.4 times the design's height at desktop width (the design shows an empty state).
- R381 (D1): The evidence analysis has no 'Missing / Inspect the gap' row and no external-link marker on 'Open record'.
- R387 (D1): The objective cards show the stored words ('Assessed', 'Not available') rather than the design's numbers.
- R388 (D1): The operating-context lanes keep the simpler timeline and context rows approved earlier.
- R450 (D2): Scenarios gets a small date-window control (From/To in site time) that the design does not have. Proposed improvement.
- R451 (D1): Renewable strip says 'Confidence: Not assessed' instead of 'Medium'; no confidence rule has been approved.
- R452 (D1): A load with no stored 'positive' rating keeps the default colour instead of the design's green; only critical loads show red.
- R454 (D1): The 'Lens: Opportunity' chip is neutral grey, not green, because green is reserved for a stored positive result.

### Mini-grid Findings, Recommendation and Action pages  (D1 13, D2 11, D4 1, D5 1)
- R65 (D1): Cold sites show 'Finding {short id}' instead of the design's example codes (F-118/F-119).
- R194 (D1): Evidence bundle adds a Records column; sources say 'not named'; coverage and use say 'Not available'.
- R206 (D4): Subtitles on Action, Recommendation and related pages use stored wording instead of the design's example question.
- R207 (D2): The Action sub-tab is called 'Application' instead of 'Execution' (a deliberate operator word). Same departure also listed as R224.
- R208 (D1): The Recommendation breadcrumb says 'Finding code unavailable' where the design shows a code; no public finding code is stored.
- R210 (D2): Recommendation, Plan and Evidence pages carry an extra status strip (badge, state chip, as-of time, links).
- R211 (D2): Proposed intervention adds a 'Trial only' paragraph and, when held, a disabled 'Accept trial' button.
- R212 (D1): 'Declare success' adds a lead line and footer note; the role reads 'Limit' instead of 'Guardrail'.
- R213 (D1): The closing 'Accepting creates managed work' note is a left-bar callout at a larger size than the design's small icon callout.
- R214 (D1): Evidence-needed items use slightly different wording and add a verification chip.
- R215 (D1): Action overview lists six scope rows instead of five; owner reads 'Not recorded'.
- R216 (D2): Activity log has five columns instead of three, plus a state line, note and 'Show all steps' footer.
- R217 (D2): Action history has four columns instead of two and shows raw failure codes in the Meaning column.
- R224 (D2): Verification page also says 'Application' where the design says 'Execution' (same departure as R207).
- R225 (D1): Verification header uses the stored action title and code instead of the design's intervention title.
- R226 (D1): Verification status strip shows two outcome chips and extra sentences instead of one line.
- R227 (D1): Activity evidence rows use different labels and omit the design's change reference.
- R383 (D2): Four Finding pages keep the Site tab row above the Finding section row; the design has none there. Awaiting owner decision. **[owner decision pending]**
- R384 (D2): The Action plan's success-criteria panel adds a fifth stored row, notes and a 'Dig deeper' section. Awaiting owner decision. **[owner decision pending]**
- R385 (D2): The Action evidence panel adds a fourth requirement row, detail text and a closed section. Awaiting owner decision. **[owner decision pending]**
- R389 (D2): Finding pages add a subtitle '{Site} - generator support finding' that the design lacks.
- R390 (D1): Finding Priority and Confidence say 'not assessed' and the Claim/Lens chips are absent; nothing is stored for them.
- R391 (D1): 'What to do next' has no stored heading or policy text; the rule sentence and recommendation button stand in.
- R392 (D2): 'What limits this' has an extra closed section about access and review context.
- R393 (D1): No 'Linked action' item in 'Where to look' because no action is linked.
- R394 (D5): Cost, Risks and Opportunities chips on the Site Findings list are greyed 'Not available yet' until Site-level lens pages exist (build-order item).

### Cold-chain Site pages  (D1 17, D2 6, D4 5, D5 0)
- R05 (D1): Cooling page shows a chart frame with category marks, not recovery temperature curves; no numeric series is stored.
- R13 (D2): Cooling and cold Health pages add an amber notice when the reading is pending, stale or historical. Proposed improvement.
- R14 (D2): Cold Health adds an amber notice that fault evidence is not a physical diagnosis. Proposed improvement.
- R20 (D2): Cold pages use plainer headings ('compressor response', claim limit wording). Proposed improvement.
- R25 (D4): Cold scenarios show authored rows or an honest 'pending' state; the design's placeholder subtitle is replaced.
- R233 (D2): Cold setup pages add extra status items (configuration only, effective dates, 'in effect now').
- R234 (D4): Physical site table has eight rows instead of six.
- R235 (D4): Heading, badge and subtitles come from the stored site ('Cold replay lab', 'Demonstration data').
- R236 (D4): Readiness table has nine rows instead of four, all 'Unconfirmed'.
- R237 (D1): Gateway panel uses the raw gateway name, shows 'No contact received yet' and a hatched empty timeline.
- R238 (D2): Breadcrumb adds the sub-tab (Foundation / Readiness); the design's ends at Foundation.
- R239 (D1): Cold single-line diagram shows the site's eight configured parts with no solar, battery, breakers or meter; every dot reads 'not assessed'.
- R240 (D1): 'What each part does' lists eight per-part rows instead of five grouped rows with descriptions.
- R243 (D1): Temperature chart: legend 'Policy band' vs 'Upper policy limit', UTC axis labels, four timeline events instead of three.
- R248 (D1): Cold finding: Recommendation tab says 'Not available yet'; next step is a gap sentence.
- R250 (D4): The conclusion says a commanded generator start failed and adds 'Not observed: transfer to backup'; the design adds recovery and peak figures.
- R251 (D1): Unknown finding or refused window shows a generic heading and one gap line per panel.
- R252 (D1): With no version selected, every panel is a single gap sentence and the phone header band is tall.
- R257 (D1): The cold overview strip lacks the 'fully reconstructed' sentence; the money panel states only a lower bound.
- R260 (D2): Cold assumptions adds a 'Selected window' line and refuses the whole panel on an invalid window.
- R335 (D1): Recovery curves panel is 1.75 times the design's height on phones because it carries an accessible table.
- R340 (D1): Cold Overview's Cooling card link behaves differently from the others (not established).
- R341 (D1): Some cold panels exceed 1.3 times design height when all disclosure sections are open.
- R342 (D1): Cold action chrome checked; remaining small differences recorded.
- R343 (D1): The closing notice drops the sentence about starting new work from a global create flow.
- R435 (D1): Cold Findings: Priority and Lens columns say 'Not assessed' in every row; nothing is stored for them.
- R436 (D1): Cold Findings strip says cold findings are not in the global list and 'Manage in Findings' is unavailable.
- R437 (D1): Cold Overview's Maintenance card says 'Not summarised here' and points to Work instead of showing status and outcome.

### Cold-chain Work pages (Work, Incidents, Maintenance, Action)  (D1 8, D2 10, D4 3, D5 0)
- R01 (D1): Work notice leaves out the sentence promising a global 'create work' flow; none exists.
- R02 (D1): Actions strip describes only cold actions and offers no 'Manage' link; the global list excludes cold sites.
- R35 (D1): No create-work destination and no repair or stock money figures (cold Work, EV Work, cold Financials); no source exists.
- R66 (D1): Linked Finding is shown as a plain label with a note that the exact version cannot be opened.
- R67 (D4): 'Due dates are not yet set' replaces the design's example wording.
- R68 (D1): The work-request code opens the request Overview instead of the design's Verification page.
- R70 (D2): Maintenance activity shows the Completed chip plus a small expandable detail.
- R71 (D2): Maintenance outcome shows the Unverified badge plus an expandable outcome note.
- R72 (D1): Next-evidence column shows stored copy or 'No next evidence recorded' instead of the example test.
- R73 (D1): Incident codes are plain text, not links.
- R88 (D1): A compact 'Window' control sits after the sub-tabs instead of the design's top-bar range picker.
- R89 (D4): Asset cell shows the stored asset ('generator-1 - backup generator') instead of the example.
- R90 (D4): Subtitle reads 'Cold-room operations at this site.' instead of the example.
- R91 (D2): A notice appears between strip and panel when the reading is historical, pending, stale or unknown. Proposed improvement.
- R92 (D2): Case panels end with a 'What this list is based on' section. Proposed improvement.
- R93 (D2): Case tables get a 'Showing a-b of N' pager instead of one example row. Proposed improvement.
- R94 (D2): Long text shows as two-line previews with 'Read full text'. Proposed improvement.
- R99 (D2): Action heading and owner strip show the full stored title and wrap. Proposed improvement.
- R100 (D2): 'Related activity' says no completed inspection is linked when none is.
- R101 (D2): Action loading, not-found and refusal states show one plain panel instead of two headed panels.
- R102 (D2): 'Related activity' names the actual linked request and its state.

### EV charging Site pages  (D1 15, D2 7, D4 22, D5 0)
- R06 (D1): Energy chart shows sample marks and a limit but no connected line; coverage is not continuous.
- R15 (D2): Availability, Energy, Health and Scenarios add amber notices about the reading's cutoff or status. Proposed improvement.
- R16 (D2): EV Health adds an amber notice that session/fault rows are not a charger diagnosis. Proposed improvement.
- R26 (D4): Availability uses real spans and percentages, not the fixed example axis.
- R27 (D2): EV Scenarios shows authored scenarios in place of the empty placeholder. Proposed improvement.
- R36 (D1): Load manager, breakers, feeder meters and the investigation action show as unknown slots or 'unavailable'.
- R43 (D4): Availability status text uses the real connector count and hours.
- R44 (D4): Availability card notes and the 93.75% example use real numerators and denominators, or say unknown.
- R45 (D4): Connector chart note and prose use real durations and timestamps.
- R46 (D2): Energy adds a collapsed Measure/Value table under the chart. Proposed improvement.
- R47 (D4): Energy conclusion sentence about incomplete sessions appears only when supported.
- R48 (D4): Energy card notes use real kWh, window and tariff or an honest fallback.
- R49 (D2): Energy adds partial-kWh and unknown-duration lines under the cards. Proposed improvement.
- R50 (D4): 'Energy basis' badge says 'limited' when the full basis is unsupported.
- R51 (D1): Stationary battery reads 'Unknown' instead of 'Not configured'; the setup cannot state it.
- R52 (D4): Revenue note appears only when an eligible estimate and payment evidence exist.
- R53 (D4): Bridge row 1 shows real quantity, tariff and amount or an 'unpriced' gap, not 120 kWh / $36.
- R54 (D4): Bridge row 2 shows a gap or real partial kWh / 'Not priced'.
- R55 (D4): Import chart shows real sample marks and axes and the declared limit, not 76/80 kW.
- R56 (D1): EV Health shows stationary battery as 'Unknown' with a note, never 'None installed'.
- R57 (D4): Connector card notes and tones use the real fault count or 'Unknown'.
- R58 (D2): Condition table may add a third row for another connector. Proposed improvement.
- R59 (D4): Site-meter row says 'Power limit not assessed from selected samples'.
- R86 (D1): Connector service period is shown in UTC, explicitly labelled.
- R87 (D4): 'Peak below limit' shows Yes, No or Unknown from real samples.
- R95 (D4): Connector cards use stored connector names.
- R96 (D2): One card per connector (not always two), then battery.
- R97 (D1): No Site-meter row when the meter has no import role.
- R98 (D1): EV Scenarios lists up to 50 authored rows with a 'showing first N' note.
- R103 (D4): Health subtitle reads 'site-level asset-condition summary' instead of the example.
- R262 (D4): Physical site table says 'Not declared' for stationary storage and 'Charger session events' for the data source.
- R263 (D4): Tariff statement says 'No tariff set for estimates' although a tariff exists elsewhere.
- R264 (D4): EV heading, badge and subtitles come from the stored site ('EV charging lab', 'Demonstration data').
- R266 (D1): EV gateway panel uses the raw gateway name and shows 'No gateway contact recorded'.
- R269 (D1): Sessions table has one row per case instead of four, and shows a shortened raw session id.
- R272 (D4): 'How to read the denominator' is a longer bold-line explanation instead of one short sentence.
- R273 (D1): Refused window keeps the strip and shows 'Unknown' tiles and gap lines.
- R274 (D1): EV finding chrome is Site-rooted (Sites / EV charging lab / Findings) instead of Findings-rooted.
- R277 (D1): Operational context shows full 64-character session ids that wrap to several lines.
- R278 (D1): EV finding Recommendation tab and button say 'Not available yet'.
- R279 (D1): Unknown finding or refused window shows a generic heading and a reason with no site name.
- R282 (D1): With no version selected, every EV panel is one gap sentence.
- R420 (D4): If some started attempts fit none of the three outcome tiles, one line says so rather than inventing a fourth category.
- R421 (D4): Billing shows 'No record' or 'Not connected' instead of the design's example billing text.

### EV charging Work pages  (D1 8, D2 11, D4 5, D5 0)
- R03 (D1): Work notice leaves out the 'create work' promise; no create flow exists.
- R04 (D1): EV Actions strip describes only EV actions with no 'Manage' link.
- R74 (D1): Finding codes show as 'Finding {short id}' instead of the example code.
- R75 (D1): Finding link is plain text with a 'Finding version' note that the exact version cannot be opened.
- R76 (D4): 'Due dates are not yet set' appears only when all due dates are empty.
- R77 (D4): The window labels read 'From (UTC)' / 'To (UTC, exclusive)' instead of the example EAT window.
- R78 (D4): Subtitle is always 'EV charging operations at this site.'
- R79 (D2): Scope strip says '1 action' instead of '1 actions'.
- R80 (D2): A notice appears for historical, pending, stale or unknown readings. Proposed improvement.
- R81 (D2): Maintenance activity adds an expandable stored-activity detail.
- R82 (D2): Maintenance outcome adds an expandable outcome note.
- R83 (D1): Work-request code opens the request Overview instead of Verification.
- R84 (D1): Next evidence shows stored copy or 'No next evidence recorded'.
- R85 (D1): Incident codes are plain text.
- R104 (D2): The currentness notice uses blue for historical/unknown and amber for pending/stale.
- R105 (D2): Case panels end with 'What this list is based on'.
- R106 (D2): Case tables get a 'Showing a-b of N' pager.
- R107 (D2): Long cells show two-line previews with 'Read full text'.
- R108 (D2): Actions panel shows the first four rows with 'Show all N Actions'.
- R109 (D2): EV Action heading and owner wrap to show full text.
- R110 (D2): EV Action loading and refusal states show one plain panel.
- R111 (D4): Site name is the stored name, not 'Depot Charging Hub'. Owner approval pending. **[owner decision pending]**
- R112 (D1): A compact page-level 'Window' control replaces the top-bar picker.
- R351 (D4): EV Work strip and notice copy differ; the 'new work starts from the global create flow' sentence is dropped.

### Estate-wide pages (Findings, Evidence, Financials, Portfolio)  (D1 9, D2 4, D4 0, D5 0)
- R287 (D1): Departures on the five estate Findings screens were never registered one by one; recorded as a group.
- R288 (D1): Summary cards say 'Supported findings'; High priority and Low confidence read 'Not assessed' instead of numbers.
- R289 (D2): State filter chips are All / Supported / Unconfirmed / No longer supported / Merged instead of All / Open / Recommendation.
- R290 (D1): Only the mini-grid finding title is a link; cold and EV finding titles are plain text.
- R291 (D1): Priority and Confidence are plain 'Not assessed' text; state chip says 'Supported'.
- R292 (D1): Cost, Risks and Opportunities pages are empty in every current state.
- R298 (D1): Mini-grid rows open the Site page without the chosen window.
- R299 (D2): Capability coverage has one row per site and capability (13+) instead of one per site (3).
- R301 (D1): Evidence tiles show '4 of 4' and 'Not assessed' instead of the design's 3 and counts.
- R303 (D2): Aggregation rule adds state chips and a results disclosure. Proposed improvement.
- R304 (D1): Portfolio cards and footer show honest states ('Not assessed') instead of example values.
- R305 (D1): Portfolio priority table has three rows instead of six, with 'not recorded' cells.
- R306 (D2): The Objectives matrix scrolls sideways inside a box at desktop width.

### Work requests, incidents, maintenance and operating records (all sites)  (D1 11, D2 6, D4 7, D5 0)
- R07 (D1): Maintenance lifecycle notice says activity is recorded but outcome unverified; no follow-up tracking exists.
- R08 (D1): Preventive plans show 'Due status not assessed' instead of overdue badges and due cards.
- R09 (D1): The Assets link is unavailable; assets show as plain labels.
- R10 (D1): Preventive trigger shows a calendar or running-hours fact and 'Draft' instead of Monthly/Quarterly and due badges.
- R11 (D1): Plan completion is unavailable; the performed record is separate.
- R12 (D1): Manual-reading form is inert with 'submission unavailable'.
- R17 (D2): Incidents add a source disclosure instead of fixed source text. Proposed improvement.
- R18 (D2): Incidents have no adjustable cutoff control; historical views come via links. Proposed improvement.
- R19 (D2): Request history times show full UTC date with seconds. Proposed improvement.
- R21 (D2): Menu entries for unbuilt destinations show as 'Not available yet' instead of live links. Preserves layout.
- R28 (D4): Preventive plan narrative shows no incident link or cause.
- R29 (D4): Operating-records cards show no example counts; no publication or request list exists.
- R30 (D4): Operating-records rows show stored submitted records and actor ids, not example roles.
- R31 (D4): Operating-records prose is two short paragraphs about authored records and missing requests.
- R39 (D4): Incident and history rows show stored rows and names, or 'Name not recorded'.
- R41 (D1): Work request history shows two gap rows ('Site visit start not recorded', 'Verification pending - no outcome') where the design has events.
- R42 (D4): Request history says 'Completed - outcome not established' instead of 'witness test outstanding'.
- R355 (D1): Corrective work requests panel is capped with an inner scroll; rows 4-5 sit behind a scrollbar.
- R358 (D1): Incident cards 2-4 and Severity column read 'Not assessed / Not recorded'.
- R362 (D4): The inert 'Record a manual reading' form lists a mock-only site (GreenHarvest Cold Room).
- R363 (D2): A date bar 'As known at ... Reload' sits between tabs and strip on request pages. Proposed improvement.
- R365 (D1): Request overview shows 'Not set' / 'Not recorded' for due date, source and success criterion.
- R369 (D2): Request history keeps UTC seconds, 'Name not recorded' and gap rows as registered.
- R396 (D1): The Verification tab on work-request pages shows 'Not available yet'; no verification page exists for requests. **[owner decision pending]**

## 4. Backlog-only and not-closed items

| ID | State | Note |
| --- | --- | --- |
| R386 | open (backlog), non-departure | No page-wide error safety net: if a screen crashes while drawing, the page can go blank. W1-a fixed the one known trigger (the Dispatch window-shaped revision, R178). Needs its own Architect-scoped slice with an honest fallback screen. Backlog item (e). No mock label. |
| R328 | D3 open (backlog (c)) | Breadcrumb needs a public Finding code from the backend (see 2a). |
| R374 | D3 open (backlog (d)) | Security audit before real users: estate roots, decision-contexts and action-index reads combine with development access; global lists treat an access 401 as an empty result. |
| R373 | resolved (merged 2026-10-25, 85be95de) | Request access seam; recapture 36/36. Done. |
| R395 | superseded by R383 | Kept for traceability only. |
| R40 | resolved for built depth destinations | Remaining link defects tracked as D3 audit rows (all merged). |
| other backlog from final-review list (not register rows) | open | (a) W6 L1: global Work row basis does not bind site type (a site with cases but no evidence could change type between pages without a conflict); (f) W4 Lows (a refused-window paragraph not announced to screen readers; a repeated UTC time when the site zone is UTC; a midnight clock-change edge in unusual zones); (g) W4 producer late gate still carries retired caps; (h) W5-cold: unmapped-code Action refusal wording; caps not stress-probed; (i) W5-EV: R350 probe covers 404 only, transient 503 on a domain Action id shows a plain not-found. Source `.ai/MILESTONE_REVIEW_BACKLOG.md` line 2456. |
