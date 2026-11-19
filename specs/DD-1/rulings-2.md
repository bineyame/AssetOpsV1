## DD1a1-R10: R6 assertion 7 restated as deterministic assertions; the batch-order cut goes to the backlog

- Architect: Claude (Architect 25), 2026-11-06. Binding checked: Claude in the lane worktrees' `.ai/ROLE_CONFIG.md` (owner, 2026-10-27). Input: `AssetOpsV1-dd1a1\.agent\review-packet-DD-1a1.md` "R6 degraded-day check" and `DD-1a1-handoff.md` at `68be2a339`. The builder's diagnosis is accepted.
- **Answer 1: grade equality to v1 is the wrong acceptance.** v1's degraded grade depends on which source's batches sort first by a random source id, so it is not a reference. R6's own premise ("the day grades as v1's degraded day") was wrong in the same way. An equality to a random value cannot pass or fail for the right reason.
- **Answer 2: the honest cut is by source time, not batch order.** A gateway outage is one instant: every signal stops together. The delivered part is every reading with source time before the outage instant, for every source; nothing at or after it. Batches that span the instant are split there. The instant is fixed by the kind, not chosen: the story run's start plus half its duration (06:00 + 4 h = 10:00 local, 07:00Z). The batch-order cut is not honest: one source stops at 02:55 while another continues, which is no real outage shape.
- **Answer 3: not defensibility-critical now; backlog it.** The v2 calendar has no `degraded` day (R6 scope note), so no shown story carries the defect. It matters only if a degraded day is added.
  - **Backlog (next free BL id, BL-18 at the time of writing): source-time outage cut** in `publish_first_half` and the `add_day` degraded path, with the instant above. Its check: the delivered set is identical across two builds, and every signal's last delivered source time is below the instant.
  - **Guard.** No `degraded` day may enter a shown calendar, demo script or live `add-day` demo until that backlog item lands. If one is asked for, stop and the Architect rules.
- **R6 assertion 7 now reads (deterministic):**
  - The day is one epoch with 0 AMBIGUOUS, and no Finding (equal to v1: none).
  - The day's window is not COMPLETE: it is LIMITED with an incomplete-evidence reason, in both v1 and the `with` build.
  - No story-window interval ends after the last delivered source time, except as OPEN_BOUND.
  - The post-outage hours add nothing: the story-window intervals in `with` equal those of `without` on the same build's delivered set.
  - No comparison of interval times or classes to v1.
- **Size: +0.** The check script changes only. DD-1a1 stays 4.5 and DD-1 stays 9.25. No owner question: no shown story changes.
- **Handoff:** builder applies the restated assertion 7 in `deg.sh`, reruns it, records the result in the packet's R6 section, and continues with the handoff's "Resume here" step 2. Context note: this Architect is fit for the next lane-2 ruling.

## DD1a1-R11: Q8 cost, projected full-day prepare against the 3 h cap

- Architect: Claude (Architect 25), 2026-11-06. Input: `AssetOpsV1-dd1a1\.agent\review-packet-DD-1a1.md` at `ff21f16e0` (Q8 line), `.agent\DD-0c-probe-results.md` §5, `.agent\DD-0b-probe-results.md` §7.
- **What the +226 % measures.** It compares v2's 8 Kobo story days with and without their complements: (330 − 27) / 8 = 37.9 s per story-only day against (1075 − 27) / 8 = 131 s per full day, ×3.46. But DD-0b/DD-0c never projected story-only days. They priced every Kobo day as a full 24 h day: `day_kobo = per_run × 24/8` = 123 s central, 138 s upper. So the measured full day is **+6.5 % over the projection's own Kobo term**, not +226 %. The +50 % gate was set against the wrong base. The 3 h cap is the binding test.
- **Assumptions.**
  - Kobo full day is 131 s central (measured, including the trial-day split). The upper is 147 s, scaled by DD-0c's 46/41.
  - Cold full day is 24 hourly runs (Q5) × 5.17 s = 124 s central, and × 6.84 s = 164 s upper. This is not yet measured as a whole day; the Cold failure day with 23 fill-ins will measure it.
  - EV, `tree`, `finish` and fixed costs are as DD-0c §5. Day counts are 22/22/3 (B-22) and 16/16/2 (B-16).
  - Drain: DD-0c's 32 s per Kobo day was measured on story-only data. Shown two ways: unscaled (DD-0c's 1,611 s at B-22) and scaled ×3.46 to full-day data (111 s per Kobo day + the 900 s tick allowance = 3,336 s at B-22, 2,431 s at B-16). Scaled is the planning case. The ticks remain unmeasured.
- **Projection (sequential, with drain; central / upper).**
  - **B-22 full days (as built):** 6,889 / 9,316 s before drain. With drain: unscaled 2.36 / 3.04 h, **scaled 2.84 / 3.51 h**.
  - **B-16 full days:** 4,990 / 6,683 s before drain. With drain: unscaled 1.71 / 2.18 h, **scaled 2.06 / 2.53 h**.
  - **B-22 with full story days and short (8 h) steady days:** **about 2.2 / 2.8 h** (scaled). It saves only about 0.6 h, because Cold and EV are unchanged.
  - **Accept a longer one-time build:** B-22 as built, at up to about 3.5 h. That is under the 6 h hard stop.
- **Fits 3 h?** On central, yes (2.4–2.8 h). On the upper case, no (3.0–3.5 h). The overrun rests on two unmeasured terms, the drain scaling and the tick allowance. So it is not yet a measured over-run.
- **Options.**
  1. **B-16, all days full:** 2.1 / 2.5 h. Every day is COMPLETE and the board window keeps 16 days of history. It loses 6 baseline days per Site.
  2. **Short steady days:** 2.2 / 2.8 h. The steady days grade LIMITED, as "without" did on 10-07, 10-14 and 11-01, so most of the history shows incomplete evidence that a real Site would not have. This contradicts CH9-R4 (full days) and weakens R9's continuous-data baseline. **Rejected** as dishonest for the saving it brings.
  3. **B-22 as built, one-time longer build:** up to about 3.5 h.
- **Recommendation: keep B-22 full days now.** R1's rule stands: the DD-1b2 rehearsal measures the whole prepare, including drain and ticks. If it is over 3 h, use B-16 (option 1). Option 3 only if the owner prefers 22 days over a 3 h build.
- **Owner question (plain language):** "The full demo history is projected to take about 2½–3 hours to build once, possibly up to 3½ hours. If the final rehearsal runs over 3 hours, should we (a) show 16 days of history instead of 22, every day complete, or (b) keep 22 days and accept a one-time build of up to about 3½ hours?" **Recommendation: (a).**
- **Size: +0.** Projection only; the measurement is already in the DD-1b2 rehearsal. Q8's +50 % gate is superseded by the 3 h cap on the projection base. Handoff: the coordinator puts the owner question; the builder continues with the packet's Open items; DD-1b2 reports the measured whole-prepare time against the 3 h cap. Context note: this Architect is fit for the next lane-2 ruling.

## DD1a1-R12: the mill-day probe; the dusk start state, other days' productive kWh, and the mill verdict's days

- Architect: Claude (Architect 25), 2026-11-06. Input: the coordinator's mill-day probe report (local day 10-30); `config/scenarios/kobo-steady-dusk.yaml` (start state: lines 4 and 7, values 42 %, 300 L, STOPPED, "the parent's, declared at that parent's own start"); this sheet's Q3 night section ("Starting states: measured handover, never chosen").
- **1. The 15:50Z (18:50 local) generator start is a defect, not honest physics.**
  - `kobo-steady-dusk` restarts the battery at the evening parent's declared 42 %. Under the 18–20 evening peak with no sun, 42 % reaches the 35 % start threshold in about 50 minutes. The start comes from that declared reset, not from the day.
  - A real day reaches 18:00 with the state its daytime left. Probe S estimates about 68 % at 20:00 on a sunny day, so no dusk start.
  - It breaks the rule the nights follow: start states are measured handovers, never declared values.
  - The defect is on every day, not only the mill day. Every B-22 steady day runs `kobo-steady-dusk`, so it would put one dusk generator start, held by the 90 % stop, on every steady day. That is a recurring generator interval no parent declared. It could add MG-2 candidate-avoidable intervals and fuel cost to the baseline and muddy the 3 MG-2 Findings and ACT-K1's baseline.
  - The v2 probe did not show this: dusk appears only on the mill day, and the mill day was not in the probe calendar.
  - The 02:05Z (05:05 local) night start is the accepted pre-dawn start (R3 Q2; R3 L2 check 1) and stands.
- **Ruling: measured dusk start states.**
  - `kobo-steady-dusk` takes its SoC, fuel and generator state from Probe S at 18:00, the continuous steady day. The file cites the run id.
  - A derived `kobo-mill-dusk` (the same windows, each with its `# source:` line, labelled "Kobo 18:00–20:00 after the mill story day; start state measured at 18:00") takes them from one probe of `kobo-mill-midday` at its 18:00 end. The `mill-midday` complement uses it.
  - Both files go into `--check`. The physics then decides. Nothing is tuned, and no file is edited to avoid a start.
- **The checks (L2, own `*_test` DB).**
  - On 10-30 and on one steady day: generator starts, runtime and fuel per complement window.
  - Findings, threads, money rows and MG-2 candidate-avoidable intervals equal with and without full days.
  - The 18:00 seam shows no SoC, fuel or generator-state jump.
  - If a dusk start remains under measured states, or any of these differs, stop and the Architect rules.
- **2. Other days' productive kWh (168.333 → 210.333, 0 → 42): honest, and no proven figure moves.**
  - The +42 kWh is real daylight productive use in the steady-afternoon complement's 14–18 local hours. It was absent when story days ended at 14:00. Full days measure the whole daylight period, which is the point of CH-9 §9.
  - The CH-6 proofs are of computations, not of v2 values. Kobo's Grow 42.08 USD on clone 10-30 comes from polish data and is not affected.
  - On the v2/B-22 build, every Grow figure is whatever its own rows give. DD-1b2 F-THREADS reports each Grow value and proves it reproduces from those rows, as the coordinator's MG-2 note already requires. No value is pinned to a CH-6 number.
- **3. The mill verdict on B-22: not proven, and it is the Grow story's E3 risk.**
  - Full days make COMPLETE days possible. Without them none exist, which is why the probe was NOT_JUDGED. But no build has yet shown 3 COMPLETE days on each side.
  - A second risk is what the later days run. If the days after the mill Action's effective day are plain steady days (the pre-change mill window), the later window measures no change, and "Target met" cannot honestly come out.
  - **Named check, MILL-3, run as a dry run in DD-1a2 (where R4 places `mill-midday` on the B-22 list) and asserted in DD-1b2 F-THREADS.** From the B-22 day list and build, report:
    - the effective day;
    - the 3 baseline and 3 later days the plan freezes, within the 14-day look-ahead;
    - each day's grade, run set (scenario ids) and `productive_kwh`;
    - the MG-5 and MG-4 guardrail days;
    - the evaluator's outcome.
  - Acceptance: 3 COMPLETE days on each side, and an outcome of VERIFIED ("Target met") by the catalogue rule.
  - Stop and the Architect rules if any of these happens:
    - fewer than 3 COMPLETE days on either side;
    - the later days do not run the changed mill operation;
    - the outcome is not VERIFIED.
  - Never move days or tune values to pass.
- **Size: +0.25** for the two measured dusk start states, `kobo-mill-dusk` and their checks. MILL-3 is +0 inside the DD-1a2 placement and DD-1b2 F-THREADS acceptance. DD-1a1 4.5 → 4.75, DD-1 9.25 → 9.5; the plan rows need it. No owner question now. If MILL-3 stops, the Grow story's later days are an owner-visible choice.
- **Handoff:** the builder measures the two dusk start states, adds `kobo-mill-dusk`, reruns the mill-day probe with the checks above, and records them in the packet. MILL-3 is added to the DD-1a2 and DD-1b2 acceptance lists. Context note: this Architect is fit for the next lane-2 ruling.

## DD1a1-R13: the Cold failure day with full days, and the steady-afternoon generator start

- Architect: Claude (Architect 25), 2026-11-06. Input: `AssetOpsV1-dd1a1\.agent\review-packet-DD-1a1.md` at `80f199328` ("Cold failure day with full days", and the `kobo-steady-dusk` observation); `backend/tests/test_w502_cold_scenario_producer.py:160-182` (`enqueue_window`, `finding_revision`: exact `ar.window_start`/`window_end` equality); `:213` (the case's release is start + 70 min, its window start + 65 min); DD-0c §1 (`_coalesce_job` widens a PENDING job on overlap, and Cold adds a 10-min bridge). The build DBs were dropped, so the cause is not yet observed.
- **1. Cold failure day: two candidate causes, one cheap probe decides.**
  - **(a) Matching defect in the tool.** The hourly fill-ins' recompute jobs lie within Cold's 10-min bridge of the failure run's job, so they coalesce. The failure is then assessed in a wider analytic run, and `finding_revision`'s exact-window match finds nothing, although a COLD_START_FAILURE Finding exists.
  - **(b) A real double send (tiling defect).** The failure case runs 65–70 min, but its hour slot is 60 min. If the next fill-in starts at the slot edge, its first 5–10 min re-send instants the failure run already covers. That breaks R5's "each instant is sent once" and can rightly change or refuse the assessment.
  - **Probe (L2, own `*_test` DB, the `cold` build to the failure day).** Report:
    - every cold_chain `analytic_run` window over the failure hour;
    - every COLD_START_FAILURE Finding and its interval;
    - per signal, any source time sent by two runs.
- **Ruling.**
  - **If (b):** the fill-in after the failure run is a derived file that starts at the failure run's last stamp plus one step, as in R7b. Each instant is sent once. The physics decides, and nothing is tuned. L0 adds that the Cold day's runs tile [00:00, 24:00) local with no instant twice.
  - **If (a) (after any (b) fix):** the BUILD path selects the failure Finding by its run, not by an equal window: the newest COLD_START_FAILURE revision whose analytic run window contains [case start, case window_end). The w502 test's own exact-window assertion stays for its test; only the build body changes. `enqueue_window` is not used to force the case's window on the full-day build.
  - **Acceptance:** with versus without full days, the failure day has the same 3 Findings: mechanism, episode interval, claim level, citations and the cold money/cost rows, apart from revision counts as R8 allows. 0 AMBIGUOUS.
  - **Stop and the Architect rules if:** no COLD_START_FAILURE Finding exists in any window after the (b) fix, or its interval or claim differs. Either would mean the fill-ins truly change the assessment.
- **2. The steady-afternoon 12:05Z (15:05 local) start: honest physics, not an R12-class defect.**
  - Its 14:00 seam is continuous (SoC step ≤ 0.16), so the run starts from the day's own state, not a declared reset.
  - The days that use it are story days after a `dispatch-necessary` morning, whose story is that the generator is needed. A low battery that meets the afternoon load and starts the generator follows from that declared cause.
  - MG-2 candidate-avoidable counts, Findings and money are already equal with and without full days (R3 check 2).
  - **R12 still binds B-22.** The pure steady days that DD-1a2 adds run `kobo-steady-day` + `kobo-steady-dusk` + `kobo-night-late` (Q3), so the measured dusk start state is needed there. R12's "every steady day" was premature for v2, but right for B-22.
  - **Checks, standing in DD-1a2 and DD-1b2.**
    - Per complement window on every Kobo day: generator starts, runtime and fuel, and the SoC step at each seam, which must be ≤ 0.5 percentage points with an equal generator state.
    - A pure steady day must show 0 starts from 06:00 to 20:00 local, as Probe S expects.
    - MG-2 counts, Findings and money must stay equal with and without full days.
    - If a seam step exceeds the bound, or a pure steady day starts the generator before 20:00, stop and the Architect rules.
- **Size: +0.25** for the probe, one derived Cold fill-in or the build-path selector (whichever the probe needs), and the checks. DD-1a1 4.75 → 5.0, DD-1 9.5 → 9.75; the plan rows need it. No owner question: no shown story changes.
- **Handoff:** the builder runs the Cold probe, applies (b) and/or (a) as found, reruns `cold` and `cold-without`, records the result in the packet, and adds the per-seam checks to the DD-1a2 and DD-1b2 lists. Context note: this Architect's context is getting heavy. One more short ruling at most; use a fresh Architect after that.

## DD1a1-R14: Cold full days are withdrawn (amends Q4); every complement seam carries the measured state of that day's previous run

- Architect: Claude (Architect 26, new standing lane-2 Architect), 2026-11-06. Binding checked: Claude (`.ai/ROLE_CONFIG.md` 2026-10-27, in the plan2 and dd1a1 worktrees). Input: `AssetOpsV1-dd1a1\.agent\review-packet-DD-1a1.md` "R13 (builder 18)" and `DD-1a1-handoff.md` "Builder 18", both at `b313fba57`. The probe is accepted: the cause is neither R13 (a) nor (b). It is the S4-05 source gate. The day-wide window holds evidence from 68 runs, `source_provenance.classify` returns MIXED (`MULTIPLE_RUNS_WITHOUT_COMPATIBLE_BASIS`), and `failure_finding = failure and gate.permitted` is false. COLD_EXCURSION is affected in the same way.
- **1. Cold failure day. Ruling: drop Cold full days (option 4). This reverses Q4 for Cold only; Kobo full days stand.**
  - **Why.** Rule N-L2 ("several runs are never coherent") is correct for central evidence. It cannot tell tool-made fill-ins from unrelated uploads, the same reason R5 (b) and (d) were rejected. Every tool option still leaves more than one run in the window: fewer or longer fill-ins, or a "shared basis", which only the product rule could grant. A gate change for "same Site, steady runs, one basis" is product-level S4-05 work. It would weaken a gate that defends every Cold Finding, so it is out of SCOPE-1.
  - Option 1 (story-only on Finding days only) is option 4 in practice, because the Cold days in v2 are its story days, and all of them carry the failure or the excursion. A partial-day rule that applies to some days and not others would also be harder to explain.
  - **How they grade.** Each Cold story day goes back to its v1/`cold-without` shape. It grades partial (partly checked), because only the declared example hours were sent, and it keeps its 3 failure-day Findings, its excursion and its cold money/cost rows exactly as reviewed before DD-1a1.
  - **Why that is defensible.** The partial grade is literally true: the hours with no data were not checked. Q4's only reason was the look of 23 unchecked hours. No Cold claim, number or "Why?" line depends on those hours, whereas with full days the Findings disappear. Presenting less beats a full day that shows no Finding.
  - **Build.** Cold leaves the v2 `complement` lists, and `cold-steady` is no longer used by the tool. Q7's L0 union check applies to Kobo days only. For Cold, L0 asserts that v2 days equal v1 days (R8 epoch and sequence exemption). If B-22 (DD-1a2) would add a Cold steady day, it is a story-only day on the same rule, or it is left out; it is never tiled.
  - **Acceptance.** `cold` equals `cold-without`: the same 3 Findings on the failure day, the excursion, the intervals, claims, citations and money/cost rows, with 0 AMBIGUOUS.
  - **Backlog (coordinator adds the id to `.agent/backlog-post-demo.md`).** For a real Cold site sending many uploads a day, the S4-05 multi-run gate could withhold every day-wide Cold Finding. This is a product question for after the demo: a compatible-run basis attestable from evidence. Source DD1a1-R14, size not estimated (S4-05 Architect pass first).
- **2. Seams. Ruling: every seam where a complement starts carries the measured end state of the run before it in the same Site-day stream. Story-run starts are the only declared resets.**
  - **Why.** R12's rule is "start states are measured handovers, never declared values". A handover measured on a different day (Probe S, the steady night probe) is still a declared value on a story day. That is exactly what makes 17:00Z step +38 pp (and +44 pp on 11-05), with RUNNING → STOPPED, and 15:00Z step +0.95 pp. A 38 pp jump with the generator switching off by itself cannot be explained to a client.
  - **Mechanism, as R12's `kobo-mill-dusk`.** For each distinct story-day chain on the v2 list (by story scenario id; 11-04 and 11-05 differ), the builder adds a derived dusk (18:00), late night (20:00) and next early night (00:00) file. Each one's SoC, fuel and generator state comes from one probe of the preceding run of that chain, and each cites the probe run id. The windows are verbatim with their `# source:` lines, and the label says "start state measured at HH:00 after <story day>". If the next local day is a story day, the chain ends at its 06:00 story start. All the files go into `--check`. The physics then decides. A generator still RUNNING at 20:00 keeps running, and nothing is tuned.
  - **Bound.** At every complement start (11:00Z, 15:00Z, 17:00Z and 21:00Z, plus any R7 split instant), the SoC step must be ≤ 0.5 pp, with equal generator state and a fuel step of ≤ 0.5 L. **15:00Z's 0.95 pp is not accepted**: it is the same cross-day handover defect, and the chain removes it.
  - **Exempt seams.** These are only the 03:00Z (06:00 local) story-run starts, where the story run is byte-equal to v1 (R5). They are declared starts. They are reported per day in the check output, and the preceding night's source line names the boundary (R3 item 5). No bound is applied, and the story is never edited to close the gap. On a steady-to-steady 06:00 seam the bound applies.
  - **Stops (L2, own `*_test` DB).** Stop and the Architect rules if, after the chain:
    - any non-exempt seam exceeds the bound;
    - a night adds a generator interval, Finding, thread or money change that the without-full-days build lacks (R2 stop gate and R13 check 3: MG-2 counts, Findings and money equal);
    - the R3, R6, R7, R7b and R12 checks change.
  - The pure-steady-day check (0 starts from 06:00 to 20:00) stays INFO here and binds in DD-1a2/B-22 (R13).
- **Size.**
  - Cold withdrawal: +0. Removing the Cold complement path and the v1-equality L0 offset the extra work.
  - Seam chain: +0.5. That covers derived files for each story chain, their probes and `--check`, the bound with its exemption, and the reruns.
  - DD-1a1 5.0 → 5.5 (2 planned), DD-1 9.75 → 10.25; the plan rows need it.
  - SCOPE-1 reasons: without (1) the board shows a Cold failure day with no Finding; without (2) the Kobo battery chart shows 38–44 pp jumps that no "Why?" line can explain.
- **Owner question (one, recommendation given; the build proceeds on it unless overridden):** "The cold-lab example days only have data for their example hours. Keep them shown as 'partly checked' so the cold failure findings still appear? Recommended: yes. The alternative, filling the whole day, makes the cold failure finding disappear."
- **Handoff:** the builder removes Cold from the v2 complement lists and reruns `cold`/`cold-without` to equality. It then builds the per-story chain files, reruns Kobo `with`/`without` with `dd1a1_r12_check.py` updated for the bound and the 03:00Z exemption, and records both in the packet. Context note: this Architect is fit for the next lane-2 ruling.

## DD1a1-R15: step back. Cut complements only where the generator is STOPPED: one rest-of-day run per story day (replaces R14 part 2's chain design)

- Architect: Claude (Architect 26), 2026-11-06. Binding: Claude. Input: `AssetOpsV1-dd1a1\.agent\review-packet-DD-1a1.md` "DD1a1-R14 (builder 19)", `DD-1a1-handoff.md` "Builder 19", `.agent/DD-1a1-r14-wip/` at `1debe5a9d`; `simulator/assetops_simulator/packs/mini_grid.py:9-11,96` and `backend/assetops_backend/runs/profiles.py:1240-1242` (`initial_values_supported={STOPPED, FAILED}`, "RUNNING and STARTING need timer history"). R14 part 1 (Cold) is done and stands.
- **The root cause behind R12, R13 and R14 part 2.** A run can start only from STOPPED. Any cut in a day where the previous run ends RUNNING can never be a true handover. Under R2's nights, a cut at 18:00 or 20:00 local often falls in a dusk or evening generator interval, and the 06:00 cut falls in the 05:05 pre-dawn interval. So more chained files cannot fix it. The fix is fewer cuts, placed only at instants where the generator is STOPPED.
- **Options weighed.**
  - **(A) One 24 h run per Kobo day: not possible as stated.** The story run is ACT-K1's run and is byte-equal to v1 (R5, R8). It starts at 06:00 from its declared state. A 24 h run starting at 00:00 would reach 06:00 in its own physical state, so the story hours would change and the story itself might not occur.
  - **(A′) The feasible nearest form: RECOMMENDED.**
    - The story run is untouched.
    - One derived **rest-of-day** run per story chain covers 14:00–24:00 local. It holds the afternoon, dusk (18–20 evening parent) and R2 late-night windows verbatim, each with its `# source:` line. This is Q3's original single 14–24 complement, with R2's night windows inside it. Its start state is measured on the **registered Site** at the story run's 14:00 end. R13 measured that seam at −0.16 pp with equal state.
    - Each early night (00–06) is one run from the previous built day's measured 24:00 state.
    - A pure steady day (B-22, DD-1a2) is one 00:00–24:00 run from the previous day's measured 24:00 state, which avoids the 06:00 cut.
    - R7's 03:00 split stays as ruled, since it falls before the pre-dawn start.
    - The 15:00Z and 17:00Z seams then no longer exist, and runs per day go down, which also helps Q8.
  - **(B) Allow a RUNNING start: rejected; product change, to the backlog.** It needs a declared runtime-so-far timer in the scenario contract, the simulator pack and the backend profile (`initial_values_supported`), with a profile-version and registered-basis check (R7b boundary). About 1–1.5 units plus regression risk on a defended path. The coordinator adds the backlog id: "RUNNING/STARTING initial state with timer history", source DD1a1-R15.
  - **(C) Keep stitching and disclose: not defensible as the main design.** Three or four resets a day, with the generator switching off by itself and 38–44 pp battery jumps, cannot be explained under questioning. Disclosure is defensible for **one** reset per story day, at 06:00 where the example day begins. That is R14's 03:00Z exemption and it stays: reported, and named by the night's source line (R3 item 5).
  - **(D) Story-only Kobo days: rejected while A′ holds.** It loses CH9-R2's "daytime solar unused" (and R12's +42 kWh daylight productive use), MG-5's full day, MILL-3's COMPLETE days and so the Grow "Target met" claim, and the owner's night decision. It is the fallback only if A′'s guards stop.
- **Bound (amends R14).**
  - At every cut that is not a story start (14:00 local / 11:00Z, 24:00 local / 21:00Z, the R7 split instant), the generator must be **STOPPED on both sides**. The SoC step must be ≤ 0.5 pp and the fuel step ≤ 0.5 L.
  - The 06:00 story start is exempt, as in R14.
- **Probe first (L2, own `*_test` DB, registered Site via the `_shifted` drafter of `host/tests/test_dd1a1_registered_kobo.py`).** The template-Site probe is not evidence for the build and is set aside.
  - Probe each story chain to 14:00 and through its rest-of-day to 24:00: N, the R30 trial day and the mill day.
  - The R25 chain (the 25 % reserve after S+1) is probed with the Foundation revision applied on that Site, as the trial chain applies it.
  - Report the state at 14:00, the state at 24:00, and the generator intervals inside each run.
- **Stops.** Stop and the Architect rules if any of these happens; this is the only point where D for the affected days goes to the owner:
  - a story run ends RUNNING at 14:00 local;
  - a rest-of-day or steady run ends RUNNING at 24:00;
  - R14's stop list fails: MG-2 counts, Findings and money equal; the R2 night gate; the R3, R6, R7, R7b and R12 checks;
  - MILL-3 later fails.
- **Build.**
  - Retire R14's `afternoon-<c>`, `late-<c>` and dusk split kinds and the `kobo-steady-dusk`/`kobo-mill-dusk` files from the v2 list. The R12 files are superseded, since dusk is now inside the rest-of-day run.
  - Add `kobo-rest-<c>` (14–24) and `kobo-night-early-after-<c>` per chain, plus the steady-day 00–24 file for DD-1a2.
  - L0 tiles each local day with ≤ 3 Kobo runs (early night, story, rest-of-day), with each instant sent once (R5, R8).
  - `dd1a1_r12_check.py` takes the new bound, the STOPPED-at-cut rule and the 06:00 exemption.
  - The WIP's `after` hook and probe `chains()` are reused.
- **Size.** This replaces R14 part 2's +0.5 (not added to it). +0.25 more for the registered-Site probes, including the R25 Foundation revision. DD-1a1 5.5 → 5.75 (2 planned), DD-1 10.25 → 10.5; the plan rows need it. SCOPE-1 reason: the same as R14 part 2. Without it the Kobo battery chart shows jumps no "Why?" line explains. This is the last stitching design: if its guards stop, D goes to the owner rather than another seam ruling.
- **Owner.** No decision needed now: no shown story changes, and the owner's night decision and CH9-R4 hold. The coordinator informs the owner of the size against the 2 planned.
  - Only if A′ stops: "Some Kobo example days can't be filled to a full day honestly. Show them as 'partly checked', losing the 'daytime solar unused' figure and the mill 'Target met' result for those days?" The recommendation would then be given against the probe's numbers.
- **Handoff.** The builder takes the registered-Site probes first. If no stop fires, it derives the `kobo-rest-*` and early-night files, runs `--check`, rebuilds Kobo `with`/`without`, runs the R3–R14 checks with the amended bound, and runs guards V, A and W. Context note: this Architect is fit for one more lane-2 ruling.

## DD1a1-R16: after the R15 stops, Kobo goes hybrid: full days only where every join is STOPPED (recommended; owner decides)

- Architect: Claude (Architect 26), 2026-11-06. Input: `AssetOpsV1-dd1a1\.agent\review-packet-DD-1a1.md` "DD1a1-R15 (builder 20)" at `afe90e8c1` (registered KOBO-001 probe).
- **Probe results.**
  - N is RUNNING at 14:00 (06:25–14:00) and at 24:00.
  - R30 and R25 are STOPPED at 14:00, but RUNNING at 24:00 (22:05 and 23:25 on) and through their early nights.
  - The mill chain passes. It is STOPPED at its 18:00 story end (89.47 %) and at 24:00 (48.42 %). The 18:00 cut is accepted as a valid cut, since it is STOPPED on both sides.
- **What each option keeps and loses.**
  - **(1) Hybrid: RECOMMENDED.**
    - A day is full only if every join of its chain is STOPPED on registered-Site probes, under the R15 bound. Today that is the mill day, plus any steady 00–24 day whose 24:00 ends STOPPED (B-22, DD-1a2, probed per day).
    - The N (necessary-run), R30 and R25 trial days are story-only and read "partly checked", which is literally true.
    - **Keeps:**
      - The 3 generator Findings, their intervals and their citations ("without" = "with", R5/R8).
      - ACT-K1's trial outcome and metrics (Q6 equality: complements never moved them).
      - MG-2 counts and money (R3 check 2, equal).
      - On the mill/Grow day: "daytime solar unused", the R12 +42 kWh daylight productive use, and the MG-5 full day.
    - **MILL-3/"Target met"** stays possible, but it is not yet proven. It needs 3 COMPLETE days on each side, and those days must be mill or steady days that pass the join rule. The DD-1a2 dry run decides; if it fails, the R12 stop applies.
    - **Loses (generator/ACT-K1 days only):**
      - The full-day solar-unused and MG-5 readings on N/R30/R25 days. These show as "not available yet" or partly checked.
      - Those days' nights, so the owner's night profile shows only on full days.
      - The R6/R7/R7b night-split work for those days, which becomes moot.
      - Nothing the generator story claims.
  - **(2) All Kobo days story-only (D).** Everything in (1)'s losses, plus:
    - the mill day's solar-unused, MG-5 full day and daylight kWh;
    - MILL-3, so the Grow "Target met" result cannot be shown at all;
    - the owner's night decision entirely.
  - **(3) Option B.** It keeps full days everywhere, but only after a product/simulator change: a RUNNING start with a timer, in three contracts, with a profile-version/registered-basis check. That is about 1–1.5 units, plus re-probing every chain, which takes DD-1a1 to about 7–7.5, against 2 planned. It also puts regression risk on a defended path just before the demo. It fails SCOPE-1's "present less over building more" while (1) keeps every claim.
- **Build if (1).**
  - v2 keeps complements only for chains that pass. N/R30/R25 days become story-only, with v1-equal payloads.
  - The mill day gets `kobo-rest-mill` (18–24) and its early night.
  - L0: a full day tiles [00:00, 24:00); a story-only day equals v1.
  - `dd1a1_r12_check.py` applies the R15 bound to full days only.
  - DD-1a2's B-22 steady days are full only if their 24:00 probe is STOPPED, and story-only otherwise. They are never tuned.
- **Size: −0.25.** The N/R30/R25 chains, the R25 Foundation-revision probe build-out and the R7 night split for trial days are dropped. DD-1a1 5.75 → 5.5 and DD-1 10.5 → 10.25; the plan rows need it. SCOPE-1 reason: as in R15, but only for the days kept full.
- **Owner question (one; recommendation: yes, option 1; the build waits for the answer, because it reverses part of CH9-R4/Q4 for Kobo):** "On the example days where the generator is still running at the edge of the example, we can't fill in the rest of the day honestly. Show those days (the generator-support and trial days) as 'partly checked'? Their findings and the trial result stay the same, and the mill day keeps its full day and 'Target met'. Recommended: yes. The alternative is about 1–1.5 extra units of simulator work to fill every day."
- **Handoff.** Wait for the owner's answer. If it is yes, the builder applies "Build if (1)", rebuilds Kobo `with`/`without`, runs the R3–R15 checks on the full days and guards V, A and W, and adds the join rule to the DD-1a2 MILL-3 dry run. Context note: this Architect is fit for one more short lane-2 ruling.

## DD1a2-R: rulings on the DD-1a2 pre-flight (Architect, Claude, 2026-11-06)

- Architect: Claude (new standing lane-2 Architect). Binding checked: Claude (`.ai/ROLE_CONFIG.md` on this branch, owner 2026-10-27). Input: `.agent/DD-1a2-preflight.md` at `1592b5543`.
- **Evidence weight.** The builder's chain table comes from a scratch script on the template Site, and Findings and grades were not measured. R15 and R16 required registered-Site probes, so **no figure in that table binds anything here**. G0, G1 and G2 below re-measure on the registered Site. Everything in this ruling marked "read from code" is a code reading, not a measurement.

### Builder's claims, checked against code and files

| Claim | Result |
|---|---|
| Q2: `kobo-steady-day` and `kobo-mill-midday` have the same mill windows | **Correct.** Both are 0, 15, 18, 10, 12, 0 kW, verbatim `kobo-daytime`. |
| Q2: INEFFECTIVE TARGET_MISS "by construction" | **Correct, and it holds wherever both sides run these windows.** `assess` (`verification_families.py:321`) needs `10*l*nb >= 11*b*nl`. Equal non-zero means fail it. Placement cannot help. |
| Q2: `kobo-daytime-larger-mill` fails the join rule | Not verified on the registered Site. It is rejected anyway: its mill is 35, 40, 30, 32 kW, more than double the reference, so it declares a second machine, not a change of operating pattern. |
| Q3: the window rule and fixed days | **Correct** (`verification_families.py:13-16`, v2 `sites`). |
| Q4: `LATE_IN_STREAM` refuses S-4 and S-2 | **Correct** (`demo_story_days.py:296`). `plan_add_day` does not run this check. See Q4. |
| Q6: "the plan rows (`:781-787`) agree" | **Partly wrong.** The bullet below the table still says "above 2 h elapsed, the fallback is B-16". The owner's later decision says 3 h and it governs. |
| Q8.4: `DEGRADED_DAY_HELD` is vacuous on this list | **Correct** (`demo_story_days.py:163`, only with a `complement`). |

**What the builder did not raise, and it matters for Q2.**
- **The verdict measures whole-day mill energy, not midday.** `productive_kwh` has period `operating_hours` (`chain/measures.py:45`), and `day_kwh` sums every row of the day. The catalogue's `[midday]` is not applied by any code.
- This has two consequences:
  - A true shift that keeps the energy equal and moves it out of the sun would read no change and fail. So a conserved-energy "before" is not available without a metric change.
  - The sentence "Midday use before and after: 42 → 110 kWh" is only loosely true: all of this energy is in daylight, but not all at midday.
- **A "before" with the mill idle until 14:00 has a measured precedent.** R12 item 2 accepted "0 → 42 kWh" on the build's trial days as honest daylight use: the reserve-trial morning plus the evening parent's 14-18 windows. The builder's composition is that same shape.
- **On today's data the story has no "before" at all.** A plain steady day already runs the mill at midday, so "run the mill at midday" would be a change to nothing. This is a story defect as well as a check failure.

### Q1. Steady day: **(b), the mill-day shape, with a 06:00 start. This reverses R15's pure steady day and R14's "on a steady-to-steady 06:00 seam the bound applies". The owner is asked.**

- **The builder's gate is not the right decider, for three reasons.**
  - **A Finding a day is close to certain under (a) (read from code).** `dispatch._classify` works per segment. From 10:00, at 900 W/m² against about 30 kW of load, PV alone clears load plus 10% with no binding constraint, which is CANDIDATE. FINDING_CLAIM_LEVELS raises on that. The reserve-trial day has the same mixed interval (minimum-runtime minutes, then candidate) and it is exactly what raises ACT-K1's problem. So about 13 extra days would carry the problem that the story says recurs weekly, which breaks R13's "MG-2 counts, Findings and money equal".
  - **Even with no Finding, (a) damages the mill story.** The builder's scratch table shows about 7-9 L a day on the "before" pattern and about 22 L a day on the "after" pattern. Continuous physics would then show the mill change roughly tripling diesel on the Grow Action's own days, with no guardrail on screen (BL-09). That figure is template-Site only. It is enough to rule against, and not enough to quote as fact.
  - **(a) is not what the owner approved.** They were told about 0 L and no story figure changes.
- **What (b) costs, stated plainly.** Each full day starts 06:00 from a declared 55 %, 300 L, STOPPED. The battery line steps up at 06:00 and the generator stops by itself. Battery and fuel do not carry across 06:00, so the example adds energy each morning that the model did not earn. R15 option (C) already held that one disclosed reset a day, at 06:00 where the example day begins, is defensible. The mill day already has it and has passed every R3-R13 check on the registered Site. The 06:00 seam is reported per day, never bounded.
- **Disclosure, required on each 06:00 start file.** Label and first source line read: "Example data. Each full example day starts at 06:00 from a declared battery level and fuel level. Battery and fuel are not carried over from the night before." The existing `RESET_0600` line on `kobo-night-early` stays.
- **Gate G1 (L2, one registered day of each profile, about 5 min each).** Report intervals, classes, Findings and money.
  - **Pass:** only the pre-dawn start, all of its minutes classed needed, 0 L, 0 starts 06:00-20:00, 0 Findings, no money change. Build continues.
  - **Fail:** stop and the Architect rules. No value changes. The likely result is that those days cannot be full, MILL-3 stops, and the owner gets the "not judged yet" choice.
- **If the owner picks continuous days (a).** Run G1a first: one registered 00-24 day on each profile, same report. Report the measured figures back to the owner before building anything. If they still choose (a), it needs one file per chain position, +0.25, and the mill profile question reopens because of the fuel figures.

### Q2. **Option A in the corrected form below, as an owner question. Not "tuned", and not neutral.**

- **Is it an honest "before"? Yes, if it is called what it is.** It is an **authored** example. We wrote the before pattern because the story needs one, the same way the reserve-trial days are authored. It is not a measurement, and it cannot be called "no value chosen to reach a result" in the sense of a neutral draw: the pattern was deliberately chosen to differ. What keeps it honest:
  - Every value comes from an existing parent, and no new number is introduced.
  - The shape already exists on this build (R12 item 2).
  - The margin (about 162 % by windows, not measured) is nowhere near the 10 % line, so nothing is sitting on the threshold.
  - The evaluator is the real one over real rows, and the owner's 10 % is unchanged.
  - **The composition is frozen by this ruling, before any product measurement. It is never revisited after seeing a result.**
- **What the client is told (demo script, and if asked):** "This site is example data. In the example, the mill used to start at 2 pm. After the change it runs from 8 am and uses the spare solar. It runs more hours and grinds more, so this is more daytime use, not the same work moved. The check itself is real and applies the 10% rule to the readings." **Do not say** "same grain, moved to midday", "measured at a real mill", or quote the percentage as a result.
- **The file: `config/scenarios/kobo-steady-before-mill.yaml`,** generated by `tools/derive_steady_scenarios.py` and included in `--check`.
  - `kobo-daytime@2` windows and SoC verbatim for irradiance, residential and clinic. Start 55 %, 300 L, STOPPED, as `kobo-mill-midday`.
  - Mill, each with its `# source:` line: 06-08, 08-10, 10-12, 12-14 = 0 (`kobo-mini-grid-reserve-trial.yaml`, `mill-demand-1`); 14-16 = 18 and 16-18 = 3 (`kobo-mini-grid-evening.yaml`, `mill-demand-2`, `mill-demand-3`).
  - Label: "example data, the mill's pattern before the change (authored for this story: idle until 14:00 as in kobo-mini-grid-reserve-trial, afternoon as in kobo-mini-grid-evening; sun and other loads as kobo-daytime)".
  - R2's "reviewers diff against the parent" reads here: **the diff against `kobo-daytime` is exactly the six mill windows**, and L0 asserts that.
- **Rejected.**
  - **B (one profile everywhere, "not judged yet"):** see the branch below; it is not recommended.
  - **C (larger mill):** not a pattern change.
  - **D (show "Target missed"):** the data would be correct, but the claim false about what the example declares. It tells a client a working change failed.
  - **A conserved-energy shift:** fails on the whole-day metric (above).
- **If the owner picks "not judged yet" (branch B).**
  - All steady days are the `steady` kind. `mill-midday` is placed at **S-5**, the latest built full day, so it has no complete later days. Baseline is then S-9, S-8, S-6; there is no `steady-before*` kind and no `kobo-steady-before-mill`.
  - The screen reads "Not judged yet" and stays so while the look-ahead is open. **Three more added days would produce "Target missed"**, so the script adds at most two later Kobo days.
  - Size −0.25. CH-9b's stored-outcome path stays built and is not shown. F-THREADS (DD-1b2) expects the not-judged state. The owner's "keeps its 'Target met' check" (`owner-kobo-partial-days`) is then withdrawn by their own answer.
- **Story cracks to carry in the demo script (not code).**
  - S-7, S+0 and S+1 run the reserve-trial scenario, with the mill idle until 14:00 and story-only. S-7 falls after the mill change. On those days the day's productive energy reads 0.
  - S-1 and S-3 (`necessary-run`, 22 kW for 8 h) read about 168 kWh, and so do S-28 and S-21. These partly checked days are not in the verdict.
  - The honest answer: only fully checked days count, and those story days declare their own loads. They stay byte-equal (R5).
- **Backlog BL-23** (below): make the measure midday-only. Class: backlog. With all mill energy in daylight, no verdict changes; the script line above covers the wording.

### Q3. Placement: **accepted, E = S-9.** `mill-midday` on S-9.
- It is also the latest placement possible: anything later leaves fewer than 3 complete days after it (S-8, S-6, S-5 are the only ones after S-9 before the unbuilt S-4). This choice is by grade only, and it was made before the data, as R4 asks.
- Baseline S-13, S-12, S-11 (S-10 skipped as `missing`). Later S-8, S-6, S-5 (S-7 skipped as partly checked). It survives B-16.

### The Kobo list, `backend/conversions/demo-story-days-v3.json` (becomes `DEFAULT_FILE`; v1 and v2 kept)

| Day | Kind | Runs |
|---|---|---|
| S-28, S-21 | `normal`, `overcast` | unchanged, story-only |
| S-20 | `steady-before-first` | `night-early`, `kobo-steady-before-mill`, `before-rest` |
| S-19 to S-15 | `steady-before` | `night-early-after-before`, `kobo-steady-before-mill`, `before-rest` |
| S-14 | `overuse` | story-only |
| S-13 | `steady-before-first` | as S-20 |
| S-12, S-11 | `steady-before` | as S-19 |
| S-10 | `missing` | existing v1 entry |
| S-9 | `mill-midday` | as v2 |
| S-8, S-6, S-5 | `steady` | `night-early`, `kobo-steady-day`, `mill-rest` |
| S-7 | `overuse` | story-only |
| S-4, S-2 | no entry | NO_DATA |
| S-3 | `late`, as `normal` | story-only |
| S-1, S+0, S+1 | `normal`, `trial-before`, `trial-after` | story-only |

- That is 13 fully checked days, 6 partly checked, 3 with no data, inside `[S-20, S+1]`.
- **New files, all generated and in `--check`:**
  - `kobo-steady-before-mill` (above).
  - `kobo-rest-before-mill` (18-24, the same windows as `kobo-rest-mill`, start state measured at the 18:00 end of `kobo-steady-before-mill` on the registered Site).
  - `kobo-night-early-after-before-mill` (00-06, `kobo-night-early`'s windows, start state measured at `kobo-rest-before-mill`'s 24:00).
- **Reused:** `kobo-steady-day` is un-held (its HELD header goes) and `kobo-rest-mill` is reused. L0 asserts `kobo-steady-day`'s windows and start equal `kobo-mill-midday`'s, so its 18:00 state is the same one R16 measured.
- **Add a top-level `"mill_change_day": "S-9d"`.** L0, in `resolve` and `plan_add_day`: a `steady-before*` kind only before it, a `steady` kind only after it. A refusal uses `MILL_PROFILE_WRONG_SIDE`. This stops a live fill of S-10 from putting the "after" pattern on a "before" day.
- **`ADD_DAY_KINDS["kobo"]` gains `steady`, `steady-before-first`.** S-10 is filled with the second, because its predecessor is S-11 but the fresh start is the honest one for a live fill.
- **G0 (registered Site, `_shifted` drafter, before any v3 use).** The 18:00 and 24:00 states of `kobo-steady-before-mill` and `kobo-rest-before-mill`, the 06:00 end of the night, generator intervals per run, all recorded in `full_days`.
  - **Pass:** STOPPED at 18:00 and 24:00, 0 starts 06:00-20:00, and for `steady`, the 24:00 within R15's bound of `kobo-night-early`'s declared start.
  - **Fail:** stop and the Architect rules. No value changes. A `before` day that cannot be full removes the baseline, so it goes to the owner as branch B.

### Q4. **Accepted: S-4 and S-2 are not built.** The late day is not moved and the guard is not weakened.
- Building them is backlog (BL-25): no shown claim needs those two days.
- **Add to `plan_add_day`:** refuse a Kobo day next to a `late` entry with `LATE_IN_STREAM`. Today `add-day` would skip this check by minting its own epoch, so a live add on S-4 would produce a case nobody has tested. +0, one test. These days read "no data", which is true.

### Q5. **Accepted: Cold has no steady day.** Cold stays v1's 3 days.
- R14 and the owner's cold decision stand: a `cold-normal` day repeats its Finding, and no day is tiled. Re-deriving a `cold-steady` (the alternative) fails SCOPE-1, since it exists only so the board looks fuller.
- **DD-1b2's partial prepare and SCOPE-1's phrase become "Cold 3 story days".** R1's "Kobo and Cold 24 h" no longer applies to Cold.
- Saving is about 36 min of E3 (the builder's estimate, not measured); DD-1b2's rehearsal re-projects it.

### Q6. **Confirmed, with one correction.** Build B-22. B-16 applies only if the DD-1b2 rehearsal measures the whole prepare above **3 h** (`owner-build-time-2026-11-06`). The plan's "above 2 h elapsed" bullet is stale.
- **The fallback must exist as a switch, or it is not a fallback.** `prepare --baseline b16` drops every entry whose **resolved** offset lies in `[S-20, S-15]`. That includes an EV Tuesday that `weekday_offset` lands there. S-28 and S-21 stay. There is no second file.
- L0: with the filter, the MILL-3 days are unchanged. +0.

### Plan row `client-demo-plan.html:781` (and `:782`). **The builder is right, and the row is false in two claims, not one.** The coordinator applies this; the builder does not touch the plan.
- "The story week reads 7 of 7" is false. S-5 to S+1 is 1 fully checked (S-5), 4 partly checked, 2 no data.
- "MG-1 judged on 21 fully checked October days" is also false: 13 are fully checked.
- **`:781` "What the client sees" becomes:** "One normal week before the first overrun. Three weekly recurrences. 13 of 22 Kobo days fully checked; the generator and trial days read partly checked; S-10, S-4 and S-2 have no data. Cold shows its 3 story days. EV shows 3 Tuesdays."
- **`:782` becomes:** "The first overrun falls on the first day, so there is no normal history before the problem. 7 of 16 Kobo days fully checked."
- **DD-1b2:** F-THREADS reports how many days MG-1's verdict actually reads, and says so if that is not what the screen implies.
- The owner's B-16 answer carried the words "every day fully checked", which R16 and this list overtook. The coordinator tells the owner (see "Owner, informed").

### Q7. **Accepted: the after-overcast night pair is withdrawn.** R2's own fallback ("presents less") applies, and the owner delegated the night design to the Architect (`owner-kobo-nights`). DD-1a2 −0.25.
- **Lost:** the only night generator cost shown.
- **Removed:** `kobo-night-late-after-overcast`, `kobo-night-early-after-overcast`, `kobo-steady-afternoon`, `kobo-steady-dusk`, `kobo-night-late`.
- **Kept:** `kobo-steady-day`, un-held under (b). The `NIGHTS` table entry that `rest_document` reads stays, but it writes no file.
- **Tests to edit:** `host/tests/test_dd1a1_registered_kobo.py:40-44`, `host/tests/test_dd1a1_stream_probe.py:88`, and any fingerprint list `--check` names. The handover JSON's old probe entries stay as history.

### Q8. The five rules

1. **Steady day after a story-only or missing day: accepted.** A fresh declared start, 48.42 %, 300 L, STOPPED, which is `kobo-night-early` unchanged. There is no bound and it is reported per day as a real data gap. The kinds are in the table above.
2. **A steady day whose 24:00 is RUNNING:** never silently partly checked on this list. On G0 it is a stop, because these days carry MILL-3. Partly checked (the 06-18 run alone) applies only to an add-day (item 3).
3. **ST-7 add-day after S+1: accepted, with the gate.**
   - The kind is `steady`; `plan_add_day` expands it into its three runs through `_expand`, with `received_at` at DB now and each run's offset kept in order. +0.25.
   - **Gate:** one registered probe of the three runs on the Foundation with the 25 % reserve, as the trial chain applies it.
   - **Pass (STOPPED at 18:00 and 24:00, no Finding):** the day is full.
   - **Fail:** the kind on that side of S+1 runs 06-18 only and reads partly checked. The script says so, and no Architect return is needed.
   - **Class: demo-critical.** The live add is ST-7, and a live normal day should read like its 13 neighbours. The price is the +0.25.
4. **Degraded guard: reading confirmed.** Refuse any Kobo `degraded` entry and add-day regardless of `complement`, with only `DEGRADED_PROBE` passing. Update `test_demo_story_days.py:461-475`: `test_r10_no_shown_calendar_...` loses its `complement` clause. Cold's S-3 `degraded` is `cold-missing-probe`, not an outage cut, and stays allowed.
5. **The MILL-3 dry run (G2): allowed. It does not count as a demo prepare, on these terms.**
   - **Allowed:** `tools/dd1a2_mill3_dry_run.py` drives the Kobo child's existing build path for v3's S-14 to S-5 (10 days, S-10 stays empty) on the builder's own `*_test` DB.
   - **Barred:** the `tools/demo_combined.py prepare` parent; the finish rows; Cold and EV; any `assetops_polish_*` DB; the full-prepare test; `test_demo_combined_*` beyond the scoped ones. Any need to cross these is a stop.
   - Machine idle, one heavy job at a time. Start `tools/keep-awake-during-tests.ps1`. Cap at 40 min, twice the estimate. Past the cap, stop and report.
   - Then call `assess()` directly with an in-memory plan: `effective_day` = S-9, baseline chosen by `choose_days`. No Action is recorded (that is DD-1b).
   - Report to `.agent/DD-1a2-mill3-dry-run.json`: every R12 item, run sets, and the S-14 and S-7 Findings compared to the story-only build.
   - **Pass:** 3 COMPLETE each side, the later days' run sets contain `kobo-steady-day`, VERIFIED by the catalogue rule, and S-14 and S-7 have the same Findings, intervals, claims and money.
   - **Fewer than 3 COMPLETE days, or not VERIFIED:** R12 stop, report, never tune. The Architect rules, and if no honest fix exists, the owner gets branch B.
   - **A story Finding on S-14 or S-7 changes because of its neighbours:** the generator Findings win (R16). The next step is leaving the neighbouring steady days unbuilt. That shortens the MILL-3 windows, so the Architect re-rules with the owner's B option in view. Do not widen any product gate (BL-20).

### Accepted without change
- **Guard extension,** list-level checks in `resolve`, proved by mutation, closing `review-DD-1a1.md:108-110`: each full kind's complement list matches `full_days`; each 00:00 start matches the previous built full day's recorded 24:00 within R15's bound, unless item 1 applies.
- **EV `S-14d normal`.** A 4th Tuesday is reported, never moved.
- **S-10 `missing`** stays.
- **FILL-1's** five refusals, plus the test that `DAY_HAS_EVIDENCE` fires before provisioning (DD0c-R Q4).

### Tests
- **L0 (`backend/tests/test_demo_story_days.py`):**
  - v3 resolves on the table above; each full day tiles; S-4 and S-2 absent;
  - the `kobo-steady-before-mill` six-window diff; `kobo-steady-day` equals `kobo-mill-midday`;
  - `MILL_PROFILE_WRONG_SIDE`; `LATE_IN_STREAM` on add-day; degraded always refused;
  - `--baseline b16`; the guard mutations; the five refusals; add-day expanding to three runs.
- **L2 (`host/tests/test_dd1a2_registered_kobo.py`):** G0, G1, the R25 add-day probe, and one `add-day steady` end to end with real-time delivery and story-time readings.
- **Scoped as DD-1a1. Guards A, W, N, V, M.**
- **Carried into DD-1b2:** F-THREADS asserts MILL-3 and the G1 pass on the whole build.

### Scope and size (SCOPE-1)

| Item | Class | Reason | Size |
|---|---|---|---|
| Withdraw the after-overcast pair | removal | No legal place under R15/R16 | −0.25 |
| `kobo-steady-before-mill` chain and probes | demo-critical | Without a "before", the mill Action changes nothing and "Target met" cannot be true | +0.25 |
| Add-day expands to three runs, with R25 gate | demo-critical | ST-7's live day must read like its neighbours | +0.25 |
| G1, guards, B-16 switch, late check on add-day | demo-critical | Inside existing acceptance | +0 |
| BL-23 midday-only measure | backlog | No verdict changes on current data; the script covers the wording | 0.5 est. |
| BL-24 continuous days without the 06:00 start | backlog | Needs a site energy balance and Findings work; the disclosure covers the demo | not estimated |
| BL-25 late day inside a stream (build S-4, S-2) | backlog | No shown claim needs them | est. |

**DD-1a2 2.0 → 2.25. DD-1 +0.25 (10.25 at R16 → 10.5); the plan rows need it.** Branch B: −0.25, DD-1a2 2.0. BL-23 to BL-25 are the next free ids in this worktree and on `main` at this ruling. **Lane 1's Architect is also writing backlog rows, so whoever merges second re-checks the ids and renumbers.**

### Owner questions (ask together; the recommendation is the first answer of each)

**Question 1. "Normal days on the Kobo example."** "A sunny day at this example site doesn't put back what the night takes out. If we run normal days as one continuous stretch, the generator comes on around 5am and stays on until about noon, on a test copy about 22 litres a day. That isn't what you approved (about 0 litres). It would also very likely raise a 'generator ran longer than needed' problem nearly every day, against the handful the story is about, and show fuel going up after the mill change.
- **Each normal day starts at 6am from a set battery and fuel level (recommended).** Keeps what you approved: about 0 litres, and the same problems and money. It costs a visible jump in the battery line at 6am, with the generator stopping by itself, on each fully checked day. The mill day already does this, and a line on screen says so.
- **Continuous days.** Keeps a smooth line and true day-to-day fuel. It loses the 0 litres and likely changes the problems and costs shown. We'd measure it on the real example site first and come back to you."

**Question 2. "How the mill 'before' is written."** "The check on 'run the mill at midday' compares days before and after. Today the example's ordinary days already run the mill at midday, so there is no before, and the check would say 'Target missed'. Nothing was measured here; we write both patterns.
- **Write a 'before' pattern (recommended):** the mill idle until 2pm, then the late-afternoon pattern, both taken from other example days. Keeps 'Target met', as you were told. The check would read roughly 40 up to 110 kWh a day. We'd present it as example data and as more daytime use, not the same work moved, because the mill grinds more after the change.
- **No 'before':** the mill change shows 'Not judged yet'. It loses 'Target met', and adding three more days live would show 'Target missed', so the script avoids that. It is simpler, but the Grow story ends without a result."

**Does the build wait?** Yes for the scenario files, the day list and the gates, since both answers change them. The builder may meanwhile do the items that do not depend on them: Q7's removals, Q8.4, the late check, the B-16 switch, the EV entry. If the owner is in a delegated absence, the build proceeds on both recommendations and each is logged for owner review.

### Owner, informed (no decision)
- Kobo: 13 of 22 days fully checked, not "every day" as an earlier question said; S-4 and S-2 read "no data" in the story week.
- Cold: its 3 story days only.
- No night generator cost is shown (the after-overcast night is withdrawn).

### Handoff
Wait for the owner's answers, then: G0, the files and v3, G1, the R25 probe, G2, the scoped tests and guards. Stops are as ruled above; a stop returns to this Architect with its report.

