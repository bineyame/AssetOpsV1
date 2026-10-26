# Architect request: ratify W4-mini provisional caps (Q18)

W4-mini merged to main (7dfd8f4e) on independent review ACCEPT. Its packet `.agent/post-W6-W4-packet.md` section "Provisional caps (Q18 ...)" lists caps computed with the accepted guide formula `50*ceil(peak*1.15/50)` (method in `frontend/docs/architecture/ui-ux-decision-guide.md` and `.agent/post-W6-W3-closeout-rulings.md`). Rulings context: `.agent/post-W6-W4-rulings.md`, `.agent/post-W6-W4-build-rulings.md`.

Decide, per panel row in that table: ratify the cap as stated, or set a different cap with the required fallback (wrap -> paging/disclosure -> labelled focusable scroll region). Specifically rule on "Maintenance at this site" (natural 832-865 / 1123-1205, not in a card; builder proposes 1000/1400) and "Opportunity panels" (range 250-350 per panel; give per-panel values or confirm the range rule). Say whether any panel needs a code change before the final full recapture.

Write `.agent/post-W6-W4-caps-rulings.md`: numbered rulings, one short paragraph each, plain and binding. Do not edit any other file. Do not commit.
