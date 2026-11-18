# S1-03 Architect answers — 2026-10-08

**Codex Architect**, per `.ai/ROLE_CONFIG.md`. This answers `.agent/S1-03-questions.md` and the S1-02 re-review's n6. It is a decision on the identified choices, not an independent S1-03 review or owner UI acceptance. The owner is checking the current tree; this answer changes no tracked file, branch, server or database.

## Q1 — Overrule the shell-wide selector; choose (b)

A 390 px Site view must have usable width, but S1-03's review did not establish that a new phone-width navigation layout works for the shared Simulator Lab shell. **Change:** scope the `≤640px` `.app-frame`, rail and content rules in `frontend/src/ui/primitives.css` to an explicit operator Site shell/page class, leaving Lab's shared classes unchanged; keep the same 390 px Site result and rerun the Site narrow-layout checks after the selector change. The Planner can schedule a separate Lab phone-layout check with its owning slice or V-01; do not claim Lab was verified by the Site screenshots. If the shared rail physically cannot be scoped without a small shell hook, add that hook rather than leaving an unreviewed Lab behavior change.

## Q2 — Accept the named legacy-site state

A direct link to a legacy Site's `/foundation/sld` or `/foundation/readiness` should explain why the persisted binding-based view is unavailable; redirecting to the single legacy Foundation page would hide the reason. Keep the named “needs an imported Site” panel and working return link, with no Postgres configuration, snapshot or readiness claim for that Site. **No change requested.**

## Q3 — Accept all three omissions from the imported Site model

“Configuration is fixed at creation” is false for a Site with versioned reserve publication; the ratings already appear in supported topology/component content; and configuration Readiness now has its own view. Keeping those legacy-only panels on unimported Sites preserves their existing honest presentation while letting the imported Site follow the mock's hierarchy. **No change requested**, provided the detailed component ratings and the link to Readiness remain discoverable as the S1-03 packet describes.

## Q4 — Accept attachment-based placement; correct the table wording

A declared unbound channel has a known device and attachment, but no published role-to-asset meaning; placing battery PCS controller SOC under the PCS states that known attachment without inferring it describes the battery. The bound SOC row correctly belongs under Battery because its binding explicitly names that asset. **Change:** in `StoredFoundationViews.tsx`, rename the “Bound channels” column to “Channels” (or “Declared and bound channels”) and make its caption/legend distinguish **bound channels describing this part** from **unbound channels on devices attached to this part**; keep the current row placement and the `Not bound` label. An unbound channel must not be counted or styled as a bound report from that part.

## S1-02 n6 — Defect, not intended Q5 behavior

Q5's period alignment says a Foundation reserve split creates new immutable binding rows and snapshots for each Foundation period; it does not make a semantically unchanged `SPLIT` copy an independent future binding decision. A user publishing a removal “from 10-04” must not see the old binding silently return at the 10-05 reserve boundary. **Fix this in the S1-02 binding-publication mechanism, not in S1-03's presentation code:** under the Site lock, apply the requested binding set through each contiguous later current binding period that is only an unchanged Foundation-alignment/split descendant of the set being edited, revalidate it against each period's Foundation, publish new period-aligned immutable rows and snapshots atomically, and preserve the earlier `knowledge_at` basis. Stop at a later *independent, explicitly published binding change*; because the current API accepts no end time, either return that actual end prominently in the publication result/UI or refuse the request with the boundary named so the user can choose another edit. Never report an open-ended change while a future unchanged split copy still restores the old set.

Treat n6 as a required, narrow S1-02 correction before S2-01a consumes the snapshot and before the combined S1 merge is presented as complete. The S1-03 branch should remain presentation-only; the coordinator can integrate the reviewed correction after the owner's current UI check, then run focused publication/historical tests and an independent correction review. Include the concrete 10-04 removal / 10-05 reserve-split fixture and an earlier `knowledge_at` recovery check. This does not reopen the accepted-with-carries technical verdicts generally, but it resolves a now-explicit acquisition-contract defect before S2.
