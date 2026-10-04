# T028 presentation revision - Claude review

Fresh Claude Reviewer, 2026-10-04. This is a **Claude review** under the
owner's rule in `.ai/ROLE_CONFIG.md` that review rounds after a slice's first
review go to a fresh Claude reviewer. Independent of the implementers of the
revision; nothing on the branch was edited, fixed, committed or merged.

- Branch `task/T028-dispatch-finding-and-evidence`, HEAD `9e40a13`.
- Range reviewed: `30122ed..9e40a13` (25 commits, 68 files). `3fce4af..9e40a13`
  is documentation and evidence only, so the layout runs taken at `3fce4af`
  describe the code at HEAD.
- Criteria: owner direction and audience question (verbatim files), Architect
  spec `.agent/T028-architect-presentation.md`
  (`D-2026-10-04-plain-language-analysis-views`), amended AC21 and "Presentation
  revision" in the task, `D-2026-10-04-analytic-readiness-scope-and-gap-impact`,
  `D-2026-09-22-milestone-speed-over-purity` for block vs carry. Packet sections
  "Presentation correction", "checkpoint 1", "2a", "2b" were read as claims to
  verify.

## Verdict

**Accept with one finding fixed on the branch (F1).** The other findings are
carried. After F1, the revision is ready for the owner's first-reading walk.
That walk is still required; this review does not replace it.

The revision does what the owner asked and what the spec sets out. On Finding
Overview, Dispatch, the Overview card, the indexes and Site Evidence, the
default view now reads as a plain account of a site's operation. Analysis is a
real tab or local view, shared between the Finding and Dispatch, so a Needed
period gets its explanation. Every product sentence comes from
`analytics/plain.py` at read time from stored structured fields, and nothing is
persisted. I confirmed that `dispatch-2` and `readiness-3` are untouched and
that the reading is not written to the lineage. The four graphics follow the
spec's honesty rules:
- timeline parts sit at their supplied times with no minimum width;
- uncertain start/stop time is its own dotted band, never a part;
- open ends get a marker and a note, never an invented time;
- a missing input gets no bar, while a zero input gets a zero-width bar;
- unavailable fuel shows its reason and no bar;
- a coverage row with zero assessed parts reads "Not assessed".

The vocabulary guard scans backend-delivered text and accessible labels, and
the failing-example proofs it claims are in the suite.

## Findings

### F1 - Medium - BLOCK (fix on the branch; does not block the owner walk)

**A site with no generator records is told that "records exist".**
`frontend/src/sites/CapabilityReadiness.tsx:73-77` (`assessedText`) shows
"No period has been assessed yet: records exist, but whether they cover each
period has not been checked." whenever `assessed_intervals === 0`, whatever
the readiness level is. A None row always has zero assessed periods
(`declaration.py` `score_readiness`; backend
`test_no_generator_evidence_scores_none_with_no_claim` asserts
`assessed_intervals == 0`). So on a freshly created site with no evidence, the
Site Evidence default view shows the readiness table (`SiteEvidence.tsx:167-168`
renders it whether or not the site is empty). That table then contradicts
itself in one row:
- the served meaning (`plain.py:505-506`) says "Nothing can be assessed yet: no
  records of generator operation have been received and accepted";
- the line below it says "records exist, but whether they cover each period has
  not been checked".

The page's own "No accepted records" panel says the opposite of the second line.

**Why it matters.** Spec section 1 says "an empty or unassessed site gets a
stated absence". Section 5 names "zero assessed periods and no evidence" as a
distinction verification must show. This is a false statement on a default
view: a user-visible claim, not a wording preference. The old text ("No
intervals assessed; signal availability only.") was neutral, so this is a
regression introduced by the revision.

**Why the tests did not catch it.** The packet's section-5 map proves "Zero
assessed periods; no evidence" with two things:
- a Full-level fixture (`t028EvidenceCapability.test.tsx:219-244`);
- the vocabulary states "Site Evidence, no evidence" and "Dispatch, nothing
  assessed" (`t028Vocabulary.test.tsx:132,151`).

Both vocabulary states use `EMPTY_ANALYTICS_CLIENT`, and its `getDeclaration`
and `getDispatch` return `not_found` (`analyticsFixtures.ts:406-415`). As a
result:
- Site Evidence renders no readiness table at all;
- Performance renders "Performance unavailable" rather than the Dispatch empty
  state ("No period of generator operation has been assessed ...") or the empty
  Analysis view.

The real None and empty-Dispatch states are therefore never rendered or
scanned. The live journey only visits a populated site.

**Fix.** Make the zero-period sentence depend on the level. For None, use the
served meaning alone, or "No period can be assessed until records of generator
operation are accepted." Keep the current sentence for Full or Limited with
zero periods. Then add two fixtures: a loaded declaration with None readiness,
and a loaded empty Dispatch. Use them in the `t028EvidenceCapability` suite and
in the vocabulary states that claim to cover these cases.

Block or carry: block. It is cheap to fix, it is a false user-visible claim,
and it is a named section-5 verification item that is currently recorded as
proven.

### F2 - Low - carry

**The Overview card shows nothing about fuel when the lead's fuel is
unavailable.** `SiteOverview.tsx:375-377` renders `FuelRange` only when the
status is `BOUNDED`. For a Possibly avoidable lead whose fuel is UNAVAILABLE
(for example an open end, or no generator output reported), the card says
nothing about fuel. Spec section 1 (card row) asks for "the associated fuel
range when supplied, or an honest unavailable state". The packet discloses the
choice (2a "Card fuel"). The omission is not misleading, because absence is not
shown as zero, so this is carried. The fix is small: render the served
`lead_timeline.fuel.note` when the status is UNAVAILABLE.

### F3 - Low - carry

**The equipment name is always "Generator".** `plain.py:428`
(`"generator": "Generator"`). The spec says to "use the existing equipment
display name where available; otherwise say 'Generator'". The site foundation
carries a display name ("Diesel generator" on the Kobo template). This is
honest but deviates from the spec. Carry it to T029, which touches the same
Finding header.

### F4 - Low - carry (to the post-T029 legacy copy inventory)

**One guard exemption is broader than the packet says.**
`productVocabulary.ts:131-138` refuses an exemption only when it has element
children. An exempt element can still hold a whole prose sentence or a backend
string as a single text node, and `source-reference` exemptions get no
identifier-shape check (only `data-vocabulary-reference` does). The packet's
statement that "no panel or backend response can be exempted" is therefore
stronger than what the code enforces.

The one prose use is the foundation summary on Site Overview
(`SiteDetails.tsx:293-296`, `user-owned`). For template-created sites that text
is product-shipped template copy, not something a person typed, and it contains
"device-to-signal mappings" and "archetype". The packet names and justifies
this exemption (2b "Choices"), so it is not hidden.

Suggested follow-up:
- record the foundation summary as a named exception in
  `productVocabulary.json` rather than as "user-owned";
- apply `REFERENCE_SHAPE` to `source-reference` exemptions.

### F5 - Low - carry

**Bare identifiers appear as prose on the Site Evidence default view.**
`SiteEvidence.tsx:288-290` (`CoverageSummary`) shows "No records in this window
for: residential-meter / active-power, ...". These are device and signal ids in
an unlabelled sentence on the Overview view. Spec section 4 says identifiers
"may remain in clearly labelled reference fields; they are not product prose".
Possible fixes: use the configured signal display name, or label the list as
references.

### F6 - Low - fix with the next packet touch (documentation only, non-blocking)

**The packet's residual-risk list is stale.** `T028-review-packet.md:714-715`
says "Layout: one non-known failure named above". Section 2b (lines 655-659) and
`.agent/T028-layout-evidence-final.txt` show the 4 failures are all on the known
list (3 Lab "blocked table" at lines 124/135/146, and the T025e p95 at 559).
This is a stale claim in the record, and it costs one line to fix.

### F7 - Low - carry (cosmetic batch)

- `FindingDetail.tsx:372`: renders "Compare 0 other possible explanations still
  open" when none are open. The count also leaves out the solar-variation item
  that the Alternatives tab lists as "Still possible".
- `assessmentAnalysis.tsx:224`: shows "4 to 4.17 h" next to "4 h to 4 h 10 min"
  for the same quantity on the same view.
- `assessmentAnalysis.tsx:139`: says "the first part with the period's outcome
  is shown", but `defaultPart` (lines 59-66) can fall back to another part.
- `SiteEvidence.tsx:835-848`: when the Dispatch read fails (unavailable), it
  says the period "may have been withdrawn or replaced". That is wrong for a
  failed read.
- `operatorSiteRoutes.ts:70-79`: the new `siteEvidenceAssessmentHref` was
  inserted between `siteEvidenceRecordHref`'s doc comment and its function, so
  that comment now describes the wrong function.
- `.ai/ARCHITECT_DEMO_RECOMMENDATION.md`: the amended tree line lost its
  indentation in the ASCII hierarchy.

## Criteria walk (spot-checked against code, not adopted from the packet)

| Criterion | Result |
| --- | --- |
| Owner: minimal technical assumption by default | Met on the five surfaces. The default views carry no IDs, method versions or disclosures. Finding Overview gives the outcome, reason, meaning, timeline, recorded vs assessed portions, confidence with its principal limitation, fuel or the reason there is none, still-open explanations, and next steps. |
| Owner: plain text plus graphs | Met. All four graphics are present, and each has a text or table equivalent, units, UTC and a caption. |
| Owner: deeper analysis as its own tab | Met. Finding `/analysis`; Dispatch and Site Evidence `?view=analysis`; card and index "View analysis" links; no index-wide Analysis. |
| Owner: no run/binding/simulator language | Met for rendered product text. The guard covers backend text and labels, and the Lab is exempt only for its own entries. See F4 and F5 for the edges. |
| AC21 as amended | Met. The tabs are `Overview, Analysis, Evidence, Alternatives` (`FindingDetail.tsx:50-55`, `SiteAnalyticsFrames.tsx` `FINDING_TABS`). Dispatch is still the only subtab. The drawer keeps the root. |
| Spec section 2 honesty boundaries | Met. Portions are shown as separate labelled values with "not parts of one total". Missing values get no bar. Nothing is interpolated or stacked. Values are labelled "Values used at the start/end of the assessed part". |
| Backend owns semantics; frontend only geometry | Met. The frontend computes bar and band fractions and `niceMax` only. `INPUT_WORDS`/`OUTCOME_WORDS` are presentation mappings, with served text preferred. |
| Immutability and no new revision | Met. `lineage_summary` attaches `reading` at read time. Targeted backend file `test_t028_dispatch_analytic.py`: 34 passed (run by me). |
| Unavailable or retired assessment stated, not substituted | Met for Finding, Dispatch and the Site Evidence coverage panel. F7 covers the failed-read wording. |
| Readiness scope (D-2026-10-04 readiness) | Met: "Scope: whole site" is kept apart from "Selected window", and Full is qualified. Not met for the zero-period case under None (F1). |
| Layout evidence | Present and recorded honestly. `.agent/T028-layout-evidence-final.txt`: 615 PASS / 4 FAIL, all on the known list. Lab-off run: 4/0. I read the files; I could not rerun them. |

## Checks

- **Run by me:** `.venv\Scripts\python.exe -m pytest backend/tests/test_t028_dispatch_analytic.py -q` returned 34 passed. `git rev-parse` returned `9e40a13`. The only working-tree changes are unrelated: `.agent/coordinator-handoff.md` and untracked `Docs/` files.
- **Not rerun (the dispatch says the coordinator verified them at `9e40a13`):** backend 1493, host 619, simulator 244, frontend 1132, `tsc --noEmit`, the production build, both `tools/check-*.ps1`, and the layout runs. I did not independently reproduce the frontend numbers. I read the frontend tests rather than ran them; under this sandbox vitest and the build cannot load `vite.config.ts`.
- **Read in full:** `plain.py`, `assessmentGraphics.tsx`, `assessmentAnalysis.tsx`, `FindingDetail.tsx`, `SitePerformance.tsx`, `CapabilityReadiness.tsx`, the vocabulary list, scanner and suite, and the backend and frontend diffs of the remaining touched modules.

## Residual risk not already named in the packet

- **Live backend text was scanned on one assessed period only.** The live journey on SITET26 found 1 period, a Possibly avoidable one (see the lab-off evidence line). Needed and Cannot determine wording is covered only by fixtures and by the backend `_assert_plain` regex, which is stricter but has no word boundaries.
- **Possible tension on the candidate's first reading.** The headline says "no reason the generator was needed was recorded". On the same page, the "Generator stop setting" explanation (Still possible) says keeping the generator on "is consistent with the setting". The analytic deliberately treats the stop policy as context rather than as a reason the generator was needed, and the Overview links it as still open, so the text is not wrong. A first-time reader may still see a contradiction. The owner walk (step 2) should probe this specifically.
- **Technical copy remains on Site Overview.** Some Site Overview text still reads as technical without using a banned word: metric labels such as "Highest interval mean solar output" and "measured intervals", and the "Generator dispatch interval" type label. This belongs to the post-T029 inventory, but it is on the T028 journey.

Files: `.agent/T028-presentation-claude-review.md` (this file).
