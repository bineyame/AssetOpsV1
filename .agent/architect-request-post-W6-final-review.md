# Architect request: rulings on the final whole-diff review findings

All 11 post-W6 fix cards are merged (main 5f71f6c9). An independent whole-diff review of `git diff 8b6ef3ed 5f71f6c9` (product code) found 3 Medium and 11 Low items, full text in `.agent/post-W6-final-review-findings.md`. Nothing High; security and backend clean. Rulings context: `.agent/post-W6-*-rulings.md`, `frontend/docs/architecture/ui-ux-decision-guide.md` (owner standing bar: state-of-the-art UI/UX within demo speed), backlog `.ai/MILESTONE_REVIEW_BACKLOG.md` "Post-W6 follow-ups" (a)–(i).

Rule on:
1. **M1** (default mini Work window: R338 UTC days vs R320 Site-local fields; on EAT Sites the form shows 8 days incl. tomorrow and Search re-reads a different window). Choose the fix: mini default as seven Site-local days, or another resolution. State whether cold/EV (UTC date fields) change.
2. **M2** (shared Action shell: cold 503 shows Retry, no technical disclosure; cold 409 falls to generic "The attempt was refused." dead end; EV shows Reload + disclosure + 409 sentence). Plus app-wide button label split Reload / Retry / Try again. Rule the single label and the cold mapping (expected: cold mirrors EV status map). Scope: Action shell only, or all refusal buttons app-wide now.
3. **M3** (estate.css 640px first-column 152px rule unscoped; applies to all estate tables not just Findings). Confirm scoping to the Findings table.
4. For each Low L1–L11: fix now in one combined fix round (before the full recapture / owner walkthrough), or backlog. Give the exact copy where a sentence is chosen (e.g. L3 EV tariff withheld sentence, L6 zone-unavailable label, L9 non-UTC window sentence). L2 (Site Work shows `Action <8 chars>` vs global `ACT-…` code; W6 Q10 excluded `site_index.py`) — decide fix now or follow-up.

Keep the fix round small and demo-speed: prefer one shared helper where duplication caused the drift only if cheap. Write `.agent/post-W6-final-review-rulings.md`: numbered, short, binding, with a final list "Fix round scope" and "Backlog". Do not edit other files. Do not commit.
