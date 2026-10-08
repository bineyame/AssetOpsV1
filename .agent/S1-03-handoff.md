# S1-03 handoff

**State:** built and in review on `task/S1-03-foundation-organization`. Packet: `.agent/S1-03-review-packet.md`. Nothing remains in progress.

## Where things are

- **Views:** `frontend/src/sites/StoredFoundationViews.tsx`. The row is `FoundationSubtabs.tsx`; routing is in `shell/SiteFoundationFrame.tsx` and `operatorSiteRoutes.ts` (`SITE_FOUNDATION_VIEW_ROUTE_PATH`).
- **Evidence:**
  - `.agent/S1-03-screens/`: captures, `INDEX.md`, `capture.mjs` and `behaviour.mjs`
  - `.agent/S1-03-behaviour.txt`
  - `.agent/S1-03-layout-evidence*.txt`
- **Owner guide:** `.agent/S1-03-owner-steps.md`
- **Open choices:** `.agent/S1-03-questions.md`

## Servers

These were left running for the owner on purpose, against the dev DB:

- backend `uvicorn` on :8010
- frontend `vite` on :5183

Processes already on :8000 and :5173 were there before this session and were not touched. The scratch servers (:8012 and :5184) and the scratch DB `assetops_s103_scratch` were removed at closeout.

## Next

1. Independent review.
2. Owner side-by-side UI check.
3. After owner acceptance, integrate S1-01, S1-02 and S1-03 in dependency order (decision §4).
