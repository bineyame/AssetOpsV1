# Architect request - W2-04 D1, D2, R1, R2 (2026-10-18). Brief, exact rulings faithful to the v69 mock; edit `.agent/W2-04-build-spec.md` in place; amend `D-2026-10-18-w2-04-buildspec`. No code.

From `.agent/W2-04-review-packet.md` (copied from branch task/W2-04-cold-site-evidence-money; captures `.agent/W2-04-evidence/` there):
- D1 (High, visible): cold-evidence Data sources - the ruled column widths (17%/13%) and "chip on one line" (nowrap, `w2-cold-site.css:101`) conflict: "Source contact unknown" is clipped, "Accepted facts · good quality" overflows the next column, header "STATUS AT WINDOW END" collides with "QUALITY". Rule exact widths/wrapping/copy so nothing clips or overlaps and the panel stays <=569 px at 1440.
- D2 (Medium): Accepted records Record cell wraps to 3 lines (short ID + "Analysis view not available for this cold record"), breaking the ruled two-line maximum; panel is 423 px vs <=345. Rule: move the sentence into Record details, widen the column, or other - exact.
- R1: unbound rows (Transfer switch, Loading / door log) closed What cell - Run-7 "No accepted report for this role" vs Run-8 labels "Transfer position" / "Door/loading context". Rule which.
- R2: confirm or replace the nowrap rule per D1.
Print a 3-line summary.
