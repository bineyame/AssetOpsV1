# Architect request: W2-04 review round 1 rulings (q9)

You are the AssetOps Architect. Read `.ai/ROLE_CONFIG.md` (the sections "Mockup drives the design; implementers never decide" and "Token Efficiency"), `.agent/W2-04-build-spec.md`, and the review `.agent/W2-04-review-r1.md`. The v69 mock in `frontend/mockups/v69/` is authoritative. The owner rule is to stay faithful to the mock and leave nothing for the implementer to decide.

Rule each item below exactly. For any copy, give the final string. For any CSS, give the exact property, value and selector scope.

- **M2.** Line-height 1.25 on the Accepted records table cells (`frontend/src/sites/w2-cold-site.css:126-129`) brings the panel from 370 px to 344 px (limit 345, 1.3x). Approve it, narrow it to specific cells, or revert it and accept the height with a stated reason.
- **M4.** The Financials Source cell shows `Finding link not available` (`coldSiteViews.tsx:1225`). Rule the null-link copy; the existing ruling elsewhere is `No linked page for this item`.
- **M5.** Cold chips render neutral, but the mock colours them green and amber. W2-03 does the same. Give one W2-wide chip-tone ruling: a mapping from chip value to tone token for the D1 contact chips (Recent/Old/Never/Unknown/Mixed/Not declared), the quality chips (Good/Limited/Mixed/No fact) and any W2-03 cold result chips. Say whether W2-03 is fixed in W2-04 or in the W2-03 follow-up.
- **L1.** Raw `degC_min` and `19–Unknown bound` shown to users (`coldSiteViews.tsx:1218`). Give the plain-language strings.
- **L2.** `Other recorded roles` appears in the closed What cell when only a non-primary role has accepted facts (`coldSiteViews.tsx:847-850`). Rule what text to show.
- **M1 (for confirmation only).** The reviewer says an unbound row's Affects cell must keep the Run-8 labels (`Backup`, `Temperature · cooling`) rather than `Claim effect not assessed`. Confirm, or correct it.

Append a section "Run 9 rulings (D-2026-10-18-w2-04-buildspec, review r1)" to `.agent/W2-04-build-spec.md`. Do an implementer dry-read and a copy dry-read before finishing. Write nothing else. Do not commit.
