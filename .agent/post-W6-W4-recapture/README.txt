post-W6 W4-mini unit-5 recapture (PARTIAL - stopped when Claude Code reaped background jobs for low system memory).

Valid at final code:
  part-a-main/ + probe/part-a/      rev 021fcf3c  batch-12 main 20 targets x 1440/390 (240/240 claims), W4-02 seed
                                                  (w402r_test, API 18451, Vite 5451, CDP 9451/9452); Q18 probe,
                                                  bar/chip contrast (tools/caps.py probe/part-a/inspect.json)
  part-b-one/ + probe/part-b-one/   rev 98c50573  batch-13 "one" 14 targets (168/168), w403 walkthrough w4rc_b_test,
  part-b-w403/                      rev 98c50573  renewable w403-decision-positive (12/12)
  part-b-stocked/                   rev 98c50573  incidents/maintenance stocked (24/24)
Not yet done: probe stocked, late phase (11 targets + probe), cold/EV Work regression, cold/EV 390 tab rows.
Resume: tools/run_b_full.sh (end-to-end, serial, fresh DB; then drop), then phase C (see handoff).
All servers stopped by PID; w402r_test and w4rc_b_test dropped; var/w4rc_b removed.
Synthetic probe screenshots carry "SYNTHETIC LAYOUT EVIDENCE, NOT PRODUCT DATA".

Update (second run, rev 3bfafdb7 + probe selector fix): run_b_full.sh complete, serial, single instance.
  part-b-one 168/168, part-b-w403 12/12, part-b-stocked 24/24, part-b-late 130/132 (the 2 are
  opportunity-finding-refused-bad-known-at "same panel count": the refusal frame is the exact-copy
  "Choose a valid evidence cutoff." with no panels by design; the mock claim does not apply).
  Probes: stocked Incidents 479/435, Maintenance 832-865/1123-1205 (selector fix works, 25/25 fields);
  late Scenarios populated 977-1014 / 1337-1424.
  Producer `w403 capture --phase late`: FAILED 7/459, all retired u9c caps (Scenarios 348/391, Incidents 460)
  plus "Scenarios table inner vertical scroll box" (client==scroll height, wrapper is horizontal overflow only).
  Log entry, not a product fault; Q13 retired these caps. Unproved by design: alternatives-stocked/-empty-current (F02 future-dated).
  Note: an earlier launch overlapped three concurrent run_b_full instances (shell backgrounding); all killed, evidence restored from git, rerun once.
Servers stopped, w4rc_b_test dropped.
