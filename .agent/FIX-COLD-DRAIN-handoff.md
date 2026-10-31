# FIX-COLD-DRAIN handoff

Status: built, `in_review`, head after packet commit. U1-U4 done. P1-P4 and T1-T5 pass; check-all 11/11.
Scoped selector run hit the 60-min cap (2031 passed, 1 literal failure fixed in 06189ef67, 7 w601e unrun then passed focused).
Open: `-Tier all` on the coordinator's go (and a clean scoped rerun if wanted) once no other `assetops-ops03-*` run is active.
Packet `.agent/FIX-COLD-DRAIN-packet.md`.
