# What the owner wants now

Confirmed by the owner on 2026-11-19 (`owner-summary-confirmations-2026-11-19.md`,
`owner-rules-clarification-2026-11-19.md`). Agents read this first, then the verbatim
files in `owner/` (188, never edited) by the file named on each line. Where files
disagree, the later one governs. *(approved proposal)* marks a "yes" to a proposal the
line states. The 1 Nov walkthrough notes (`owner-walkthrough-notes-2026-11-01.md`) are
committed with the owner's 3-4 Nov additions; the owner's caveat: "some content may not
be relevant in light of our updated goals".

## 1. Current direction (18-19 Nov; read this first)

- **Core and boosters.** The current product is a solid core; "Desciplined factor connection to outcome, value chain and performance to target, financial and operational integrations are clear boosters". Changing the core must be "for merit and intentional clearly exposing the issue against the objective". `owner-design-regeneration-request-2026-11-19.md`
- **Findings are living outputs.** Findings are "results of condition evaluation as living artifact(output)", not conditions on keys; a finding "should have impact on the bottomline or is a risk or an opportunity - which means it needs to be acted on". (same file)
- **A person decides, acts and tracks.** The design must give users context to act on, then tracked, with "a few sensible roles"; the system does not act on its own. (same file)
- **The plan is a legitimate new construct.** "a plan is a legitmate new construct and need to be added as such and integrated with the existing constructs. e.g an action be raised against a plan or a finding"; spend and crew thresholds and deviation tolerance are configurable per Site or portfolio. Origin and plan membership as refined (one origin per Action, at most one plan membership), the ten pack defaults ("defaults for all 10, go ahead"), and the crew-visit default of zero "so long as it is configurable". (same file); `owner-pack-questions-defaults-2026-11-19.md`; `owner-recreate-document-packs-2026-11-19.md`
- **Document brief.** A small document: "very intentional, clearly explained , well illustrated"; section 1 the current architecture, its value and mechanics, section 2 the proposed changes on top; sequence, use-case and process diagrams for a mini-grid, only for what changes; "overall objective to be considerd, not narrow slice that is detacehd". Packs are recreated, "not update", from the reviewed design, with a new two-week plan "focussed on advancing as much as possible towarfs the new features, not the markting element"; the mock-up "more professional in temrs of ites usage of space and modern state of the art ui/ux", no technical words. `owner-design-regeneration-request-2026-11-19.md`; `owner-recreate-document-packs-2026-11-19.md`
- **Four outcome categories tie back.** Grow revenue, Optimize cost and efficiency, Protect asset and capital, Assure performance and returns: "building from factors doesn't mean these categories are irrelevant, things tie back to them , architect should address it in the design do with diagram, it is very important". `owner-summary-confirmations-2026-11-19.md`
- **Spec handshake.** After the owner reviews the file paths, work begins; the Architect specifies clearly to the implementer and gives a reviewer guide, and "the reviwer asks and clarifies questions with the architect before coding begingsg to avoid mid-implementation back and forth". A strategy round on test data and database build follows. `owner-build-start-and-spec-handshake-2026-11-19.md`
- **Test policy.** "to avoid expensive full test that holds back progress, so regression or smoke test or isolated test could be used then full test for key milestones". `owner-rules-clarification-2026-11-19.md`
- **Engagement path.** Initial call, alignment, deep-dive, integration pack and pilot timeline, monitor, then SaaS; file exports show value early; pilot fee or credit; price "disclosed after client conversation". D13 and D14 yes; first change agreed at the end of the deep-dive. `owner-d1-engagement-path-2026-11-18.md`; `owner-sitting1-answers-2026-11-18.md`
- **Decisions OD-1 to OD-20** (including OD-7 and OD-8, delivery lanes, "yes") are in the Layer 4 design pack's decisions register (`Docs/demo-sprint/product-direction-layer4/`, on branch `task/layer4-design-regeneration` until merged), not copied here. Delivery order: emulator lane and factor lane in parallel. `owner-design-regeneration-request-2026-11-19.md`

## 2. Product direction: economic outcomes built from structured factors
- **The product starts from what customers earn, save, protect or improve, not from what it can detect.** "The starting point is no longer what AssetOps can detect, but what customers stand to earn, save, protect, or improve financially." `owner-commercial-capability-direction-2026-10-26.md`
- **The demo's purpose is to convert operator executives with value their monitoring tools do not give.** "convert minigrid, ev and colchain operator executives ... with real value that is not offered by monitoring tools" `owner-product-transition-request-2026-11-18.md`
- **What Portfolio and Site pages show must be useful and aligned with economic movers, fast; keep and extend what already fits.** "the core utility function being differentiation and usefulness that converts clients" `owner-grounded-transition-request-2026-11-18.md`
- **Outcomes are read upward from structurally defined factors, never detected at the top first.** "it is observed by the underlying factors which are stucturally defined- so in that sense you got it backward" `owner-layer4-direction-feedback-2026-11-17.md`
- **Define the fundamental mechanics first, then derive the specifics; never a design built around one site or path.** "I see a narrow focus overall instead of defining fundamental mechanics and derive the specifics accordingly." (same file)
- **Reuse on merit only; where an existing part does not fit, say why and design it properly.** "extend and reuse is on the bases of merit for efficency, to the extent it is aligned with where we want to go" (same file)
- **Restructure the Portfolio experience itself; no role filters, role menus, or executive questions written on screen.** "execute questions should not be stated verbatim, they should just naturally emerge on the way information is organized" (same file)
- **Telemetry order: EMS data upload and API first, then the edge gateway talking to hardware over Modbus.** Modbus sits in the emulation scope so it is proven before hardware exists; a BeagleBone Black running the edge gateway against the backend gateway comes later. `owner-summary-confirmations-2026-11-19.md`; `owner-telemetry-plan-feedback-2026-10-27.md`
- **All supported connection profiles are available to a Site within a portfolio.** "yes" `owner-summary-confirmations-2026-11-19.md`; `owner-commercial-capability-direction-2026-10-26.md`
- **Emulators are placeholders that define canonical data until real integrations replace them.** "the emulator is a palcehodler that should be replaced by real integration" `owner-grounded-transition-request-2026-11-18.md`
- **The simulator only produces operating reality; AssetOps discovers its meaning from ingested observations.** "the simulator generates operating reality; AssetOps must independently discover its implications from ingested observations." `owner-commercial-capability-direction-2026-10-26.md`
- **An operational KPI is not a commercial outcome or a potential.** "Do not confuse an operational KPI with a commercial outcome" `owner-commercial-architecture-reframe-2026-10-27.md`; "why are we conflating KPI with potential ?" `owner-walkthrough-notes-2026-11-01.md`

## 3. Data and analysis behaviour (any Site, any range)

- **Ingest and upload must work for every site; the UI only displays.** "there is no logic in the UI other than dispaly" `owner-questions-ingest-captures-2026-11-08.md`
- **Where data comes from (source, emulation, simulation) is a displayed data element, not screen logic.** "the source is a data element that should just be displayed no?" `owner-answers-open-questions-1-2026-10-27.md`
- **Data in the selected range gives output for that range, the same way for every Site type, on every tab.** "if there is data in the range, then there should be corresponding output" `owner-range-output-rule-2026-11-12.md`; "all tabs should respect the date range without exception" `owner-all-tabs-respect-range-2026-11-12.md`
- **Setup facts (foundation, single-line diagram) are not managed by date range; the range applies to telemetry and its consequences.** "i confirm that that setup facts are not manged by date range for now(may introduce version later but not a priority)" `owner-rules-clarification-2026-11-19.md`
- **Any range loads fast through a daily calculated snapshot that the UI reads, with defined recalculation triggers.** "the point was to avoiud recalculation and keep a calcualted daily snapshot that the UI would use ,ofcourse with triggers to recalulate and udpate if things change(defined as triggers)" `owner-summary-confirmations-2026-11-19.md`; "it should work for any date range i specify" `owner-any-range-speed-2026-11-10.md`
- **Missing data lowers confidence; it does not blank the result: compute and attach the quality.** "if the data completeness threshold is not met, calcuation should still happen but quality of the output attached" `owner-walkthrough-notes-2026-11-01.md`
- **Thresholds are configurable (coverage per portfolio; minimum days before a target is judged).** "this should be configurable per portfolio but is reasonable for now" `owner-walkthrough-2026-11-10.md`; "got to be configurable" `owner-walkthrough-notes-2026-11-01.md`

## 4. Honesty and wording on screen

- **State missing data in the UI as missing.** "if there is data missing to show yet, it should be stated as such in the UI" `owner-V-01a-round2-feedback-2026-10-12.md`
- **Say "unexplained fuel", never "theft".** "'Unexplained fuel', never 'theft'" `owner-missing-fuel-2026-11-07.md`
- **Evidence classes (recorded, calculated, assumed, modelled) replace the claim ladder; a simulated result is never labelled "Verified realized field commercial value".** "evidence class is also fine" `owner-summary-confirmations-2026-11-19.md`; "Never use the fourth label for simulated results." `owner-commercial-capability-feedback-2-2026-10-26.md`
- **Never present synthetic data as an observed field measurement.** "Never present synthetic measurements as authentic field observations." `owner-demo-data-strategy-2026-10-28.md`
- **Claim compatibility and readiness only for what was actually tested.** "Do not advertise Victron VRM compatibility from an invented “VRM-shaped” export." `owner-telemetry-plan-feedback-2026-10-27.md`
- **"Not analysed yet" only while the system still has work pending; otherwise say what is wrong with the data.** "not analysed yet only makes sense when system action is pending, for when the data is not complete, that fact need to be stated" `owner-answers-17nov-scope-2026-11-11.md`
- **A partly covered Site shows money for the analysed days, labelled, never estimating the missing day** *(approved option)*. "option 2 for money" (same file)
- **Status words say exactly what they mean ("checked" must not imply a failure to check).** "the user facing text for 'checked' should tell exactly what it means" `owner-walkthrough-2026-11-10.md`
- **No simulator or system vocabulary for users; present each site as a real site.** "simulator specific language such as run, binding...etc should not appear, it should be regarded as a real site." `owner-T028-presentation-direction-2026-10-04.md`
- **Every capability claimed as available must be demonstrable.** "every capability claimed as available must be demonstrable." `owner-commercial-capability-direction-2026-10-26.md`

## 5. Look, mock fidelity and UI quality

- **Mocks: v70 for screens and content, v72 for visual style and its four hi-fi pages; the Layer 4 mock-up is being recreated.** "v70 + v72 style" `owner-repo-declutter-request-2026-11-18.md`; for the new mock-up see section 1 (`owner-recreate-document-packs-2026-11-19.md`)
- **Stay faithful to the mock; align the technical design to it (both Architects).** "stay faithful to the mock-up in ui/ux and align technial desgin accordingly. there should not be drfit" `owner-fidelity-and-design-ownership-2026-10-18.md`; `owner-architect-mock-fidelity-2026-10-22.md`
- **Write for users with minimal technical assumptions: plain text and graphs first, deeper analysis on its own tab.** "plain clear text and graphs ... with option for deeper analysis offered as its own tab" `owner-T028-presentation-direction-2026-10-04.md`
- **Later UI work: international grade; English, French, Swahili; dark and light themes; a brand font.** "english, french and swhaili ... dark and white for the user to select" `owner-walkthrough-2026-11-10.md`

## 6. Commercial plan and pace

- **Two-week build: ambitious, as much important work as possible, reviewed after two weeks.** "i belive we can accomplish a whole lot more in two weeks(months worth of work)" `owner-gtm-documents-request-2026-11-18.md`
- **The deferred list is a queue: pull the next item when a lane is free.** "it is not deferred as such, it is queued" `owner-deferred-is-queued-2026-11-13.md`
- **Progress overrides the 5% contest rule (dropped).** "progress overrides this and i agree with your recommendation" `owner-summary-confirmations-2026-11-19.md`
- **Keep moving on items awaiting the owner; the owner reviews and corrects later.** "i'll review and inform of any changes later, we want progress" `owner-proceed-waiting-items-2026-11-13.md`

## 7. Workflow, roles and review

- **Workflow W1-W9 (D11) is adopted.** "yes, adopt D11 and start the declutter after" `owner-repo-declutter-request-2026-11-18.md`
- **Structure first: figures are outputs; fix classes; checks independent of what they check; small scope** *(approved points 1-4)*. "yes, send points 1-4 to the architect" `owner-layer4-direction-feedback-2026-11-17.md`
- **Reviewers also check the structural mechanics.** "make sure the reviewer also checks your points, the structural aspect of mechanics are still very important" (same file)
- **The Architect specifies the implementation approach so implementers make no isolated decisions; it answers their questions and records them.** "so that the implementer does not make its own isolated decisions" `owner-build-plan-depth-2026-10-27.md`
- **Decision requests go to the active Architect, which decides, informs the owner, and says when it wants the owner to weigh in.** "let the active architect make them and inform me if the architect wants me to weigh in" `owner-T028-closeout-2026-10-04.md`
- **When the owner is away and delegates, the Architect decides from how real sites work.** "decisions based on understanding of how real sites work ... no cutting corners on fundamentals" `owner-away-architect-decides-2026-11-08.md`; standing absent rule "keep the owner-absent rule" `owner-autonomy-2026-10-14.md`
- **The default Architect is Claude.** "let the default architect be claude instead of codex" `owner-default-architect-claude-2026-10-27.md`
- **Builders pre-flight and batch questions; full suites only on a quiet machine** *(approved proposal)*. "yes, adopt 1 and 2" `owner-speed-preflight-quiet-suite-2026-10-22.md`
- **Tests: regression, smoke or isolated tests while building, a full test at key milestones; no expensive full run that holds back progress.** "to avoid expensive full test that holds back progress" `owner-rules-clarification-2026-11-19.md`; "we need speed" `owner-overnight-2026-11-10.md`
- **Approved 18 Nov: D-1 fix, PIPE-1, OD-4 (a verified DB clone counts as the clean, good DB), OD-6 (one full backend suite overnight on the VPS).** "8.yes 9.yes" `owner-sitting1-answers-2026-11-18.md`

## 8. Safety on the machine

- **Databases: create and drop only `*_test` and producer `<prefix>_audit` scratch databases.** "yes, allow creating and dropping the test databases" `owner-test-db-authorization-2026-10-18.md`; "Allow tool scratch DBs" `owner-producer-scratch-db-authorization-2026-10-24.md`
- **Never switch off a safety setting (no execution-policy bypass); if refused, stop and report, no workaround** *(approved option)*. "Start it plainly (Recommended)" `owner-local-servers-authorization-2026-10-26.md`
- **Walkthroughs only on a clean, good database; time is flexible.** "walkththrough on a clean, good DB" `owner-rules-clarification-2026-11-19.md`; "the walkthrough has to be cleaen on a good database, so getting it right more important than the walthroughh time" `owner-clean-walkthrough-over-time-2026-11-13.md`
- **Do not touch port 5490 or Docker where it would interfere with tests or the owner's validation; port 8990 is not ours.** "not to interfe with tests or affect my valiodation" `owner-rules-clarification-2026-11-19.md`
- **Docker may be restarted on this server, as needed.** "if it helps on this server, on a need bases" `owner-summary-confirmations-2026-11-19.md`
- **Generated evidence lives outside the repo, for two weeks.** "outisde the repo, needed only for 2 weeks" `owner-repo-declutter-request-2026-11-18.md`

## 9. Open owner decisions and their status

| Decision | Status | Source |
| --- | --- | --- |
| Layer 4 design and recreated packs | owner reviews the file paths, then build begins | `owner-build-start-and-spec-handshake-2026-11-19.md` |
| Merge the Layer 4 pack to main; approve the mock-up for client use | "After i review and confirm" | `owner-sitting1-answers-2026-11-18.md` |
| Git history rewrite and worktree pruning (O5) | "later after demo" | `owner-repo-declutter-request-2026-11-18.md` |
| Analytics port size; SQL vs NoSQL | Architect to weigh in; outcome not recorded | `owner-analytics-port-and-db-choice-2026-11-13.md` |
| Versioned setup facts | "later ... not a priority" | `owner-rules-clarification-2026-11-19.md` |
| Test-data and database strategy round | to come | `owner-build-start-and-spec-handshake-2026-11-19.md` |

## 10. Pending owner confirmation

Standing owner rules not yet in `.ai/RULES.md` (the owner has not answered; they stay
here until confirmed):

1. "Unexplained fuel", never "theft".
2. Synthetic never shown as observed; claims only for what was tested.
3. "Not analysed yet" only while system work is pending.
4. Missing data lowers confidence but still computes; zero contributors shown as zero.
5. Source is a displayed data element; ingest works for any site.
6. Refused by a safety check: stop and report, no workaround.
7. Stop old walkthrough servers found running.
8. Tag every demo build; the deferred list is a queue; estimate at agent speed.
9. Every capability claimed as available must be demonstrable.
10. Executive questions never written on screen.
11. Decision routing, the owner-absent rule and review routing (consistent; no change needed).
