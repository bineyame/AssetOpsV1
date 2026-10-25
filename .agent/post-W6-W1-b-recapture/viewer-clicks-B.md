# Viewer clicks, agent B (Q43: action-history "Show all N entries" only; no other clicks, no mutation)

Tool `probe/tools/B-viewer.mjs`; screenshots `batch-NN/viewer-*/<screen>-<case>-<w>-before.png` / `-after-show-all.png`.
URL is unchanged by the toggle (in-place state). Heights are the closed "Action history" panel.

| case | width | URL (path) | click | rows before -> after | panel h before -> after | URL after | overflowX before/after |
|---|---|---|---|---|---|---|---|
| all | 1440 | /sites/KOBO-001/actions/051aa3c2-9081-40ec-9403-43857ea84850/history | Show all 6 entries | 3 -> 6 | 355 -> 506 | /sites/KOBO-001/acti same URL | 0/0 |
| all | 390 | /sites/KOBO-001/actions/051aa3c2-9081-40ec-9403-43857ea84850/history | Show all 6 entries | 3 -> 6 | 451 -> 572 | /sites/KOBO-001/acti same URL | 0/0 |
| event-failed-stale | 1440 | /sites/KOBO-001/actions/051aa3c2-9081-40ec-9403-43857ea84850/history?e | not offered | 3 -> - | 362 -> - | - same URL | 0/- |
| event-failed-stale | 390 | /sites/KOBO-001/actions/051aa3c2-9081-40ec-9403-43857ea84850/history?e | not offered | 3 -> - | 442 -> - | - same URL | 0/- |
| recorded-at | 1440 | /sites/KOBO-001/actions/051aa3c2-9081-40ec-9403-43857ea84850/history?r | not offered | 2 -> - | 304 -> - | - same URL | 0/- |
| recorded-at | 390 | /sites/KOBO-001/actions/051aa3c2-9081-40ec-9403-43857ea84850/history?r | not offered | 2 -> - | 423 -> - | - same URL | 0/- |
| selector-conflict | 1440 | /sites/KOBO-001/actions/051aa3c2-9081-40ec-9403-43857ea84850/history?e | not offered | 0 -> - | 96 -> - | - same URL | 0/- |
| selector-conflict | 390 | /sites/KOBO-001/actions/051aa3c2-9081-40ec-9403-43857ea84850/history?e | not offered | 0 -> - | 96 -> - | - same URL | 0/- |
| verified-replay | 1440 | /sites/KOBO-001/actions/a44cec10-84d8-4cdd-8a1c-260f96fb43f8/history | not offered | 3 -> - | 313 -> - | - same URL | 0/- |
| verified-replay | 390 | /sites/KOBO-001/actions/a44cec10-84d8-4cdd-8a1c-260f96fb43f8/history | not offered | 3 -> - | 435 -> - | - same URL | 0/- |
| x-withdrawn | 1440 | /sites/KOBO-001/actions/cd814ebb-cafd-447b-9b45-be56fb1eb1ef/history | Show all 6 entries | 3 -> 6 | 312 -> 428 | /sites/KOBO-001/acti same URL | 0/0 |
| x-withdrawn | 390 | /sites/KOBO-001/actions/cd814ebb-cafd-447b-9b45-be56fb1eb1ef/history | Show all 6 entries | 3 -> 6 | 609 -> 700 | /sites/KOBO-001/acti same URL | 0/0 |

Note: the verified-replay viewer read ran before the helper's loading-wait fix and measured before the verification
history loaded (313/435); the capture evidence (authoritative) gives 332 (1440) / 501 (390). No toggle is offered there
(3 entries). The s601b and withdrawn reads match their capture evidence.
