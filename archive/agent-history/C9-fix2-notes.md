# C9 fix 2 notes (B1 + C1)
- parseGateQueue now keys discovery on the link target filename (`ID-slug.md`, any label); bare-id link text is the fallback. External URLs skipped.
- packetPhase: anchored `open\b` is not_started (after done/in_review/active); `umbrella` restricted to literal `umbrella/index`.
- Three new fixtures failed before the change (23 pass/3 fail), pass after (26/26): labeled discovery, phase mapping (incl. "opening soon", "umbrella of active work" unknown), labeled V-01a/V-01b open/active/in_review through discovery.
- Real README discovery: 22 packets incl. V-01a, V-01b (both not_started). check-all.ps1: 6/6 pass. Live --next-work: ranked, Decision unchanged (select I-sim-dispatch-cases 3.018 vs A-finding-episode 2.679, gap 11.2%); only packet_status fingerprint changed (8efe64f298668aad), recorded in .agent/W1-first-ranking.md (Decision line at line 896).
- Report does not print the gate list; discovery verified by calling parseGateQueue on tasks/README.md.
