# W1-F5b re-review (fix round, cbb88be1)

Verdict: RETURN (1 Medium: lost capture state)

Checks: `npx.cmd tsc --noEmit` clean. Focused s404SiteFindingIndex, v01bEvidenceVisual, w1f4RecommendationStructure: 3 files, 63 passed (npm.cmd test ran here). Full suite (2140 passed) is the implementer's, not rerun.

Verified fixed
- H1: Lens column with "Not assessed" badge present in part09 capture; test asserts the full 8-column header row and per-row badge. Fixed.
- M2: h1 now "Generator support review" on Recommendation, test asserts it. Residual (a Finding titled "...merits review" shows the short name here) is honest and disclosed in the packet; accepted.
- M3: part04 record capture shows plain words (Feeder demand, Good, Accepted, times, delivery progress) and a single closed "Exact references" disclosure; test asserts one closed details, message and IDs inside, none outside, no GOOD/ACCEPTED. Fixed.
- L4: Analysis Coverage stacks at <480px (CSS present); audit reasons are per-case. L6: parts recaptured on fix-round code.

Findings
1. MEDIUM - Analysis "limited" and "supported" captures collapsed into duplicates, and neither shows a supported or limited result. Parts 06/07 now load without a pinned revision. `part06-evidence-analysis/evidence-analysis-supported-1440-app.png` (day 10/06) and `...limited-1440-app.png` (day 10/11) both render "No assessment selected ... We have not checked this period" with the identical records table. Before the fix (7bc18c62) the limited capture showed "The readings support calling this period of generator operation avoidable for at most 5 min; ... Using the latest checked readings ... Open this assessment in Performance", with the assessed-period link set and "Clear selection". The owner's walkthrough has lost both states. Also check part07 for the same loss (same pinning change). Fix: have the capture pick the assessed period (click the "Whole day 08:00-08:30" link, or pass the period/assessment parameter without the revision pin) so supported and limited each show their own result; regenerate pairs, audit and index.
2. LOW - part09 Findings table at 1440 scrolls horizontally after the Lens column was added (scrollbar visible, Period column at edge). Not blocking; consider tighter column widths.

No assertion appears weakened; the diff only adds assertions.
