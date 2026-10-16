# W1-UX-03 handoff

Branch `task/W1-UX-03` (base main `b4a89314`), phases 1-2 built, `in_review`. Not merged. Packet `.agent/W1-UX-03-review-packet.md`.

## What later UX slices can reuse

- `frontend/src/sites/periodStrip.tsx` `PeriodStrip { name, title, start, end, rows[{key,label,segments[{start,end,tone,label,href?,selected?}],summary,notKnown?}], legend, startText?, endText? }`. Tones: covered, gap, problem, not-known, necessary, avoidable, undetermined, marker. Zero-length segment = an instant marker. Kept local (not in `src/ui`) to avoid shared-file conflicts; promote to `src/ui` in the combined pass if UX-04/05 need it.
- Wrap pattern for domain word maps: `statusWords()` in `PerformanceDispatch.tsx` takes label/tone from `currentnessWords` and only the sentence from the domain map (`STATUS_SENTENCES`).
- Technical disclosures that must keep many fields (S3-02b Technical, dispatch stored record) stay `Disclosure`s, with each value in `<code data-vocabulary-exempt="source-reference">` and plain labels, so the W1 scan passes over them.

## Routes opted into W1 here

`evidence-analysis` (`v01bEvidenceVisual.test.tsx` and `evidenceClaimLimit.test.tsx`), `dispatch`, `analysis` (`performanceDispatch.test.tsx`). `evidence` was opted in by UX-01.

## Open

- G-04 must tag the Dispatch Analysis fuel/money sentence through `MissingClaim`; then drop the allowance in `performanceDispatch.test.tsx` ("Known deviation").
- Combined walkthrough: `evidence` via `s2_demo_walkthrough.py run/serve`; `evidence-analysis` via `s302_claim_limit_walkthrough.py`; `dispatch`/`analysis` via `s3_dispatch_walkthrough.py`; capture with `node tools/w1-ux-03-evidence.mjs <out> <mock-id>[:<case>]=<url>`.
