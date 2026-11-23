# Decision index

Decisions by ID. The former `.ai/DECISIONS.md` was split verbatim on 2026-11-18;
at the split commit its four parts concatenate, in this order, to the original
(headers aside; `python tools/check-split-preservation.py`). Since then only
citation paths were rewritten (declutter steps 4 and 5, `specs/CITATION_MAP.md`):

| Part | Holds | Size |
| --- | --- | --- |
| `2026-10-late.md` | 2026-10-07 to 10-22 by heading, newest first (it was prepended), with 10-23 amendments at the top | 83 KB |
| `old-index-2026-10.md` | the old in-file "Decision Index For Agent Context" | 17 KB |
| `2026-09.md` | 2026-09-11 to 09-30, oldest first | 182 KB |
| `2026-10-early.md` | 2026-10-01 to 10-09 by heading, oldest first, plus later decisions (to 10-31) appended under the last `## 2026-10-09` heading | 211 KB |

Find a decision: grep its ID in `index-*.md` (one line each: ID, title, status, file),
then open the file at that ID. Never read a part whole. `live` means no later decision
text supersedes it, not that it applies under the Layer 4 direction (`.ai/START_HERE.md`). 45 early decisions
have no ID; find them by date heading (`## 2026-09-11` ...) in the parts.

| Index | Covers | IDs |
| --- | --- | --- |
| `index-2026-09-1.md` | Dated decisions 2026-09 | `D-2026-09-11-simulator-gate` to `D-2026-09-24-codex-spend-before-the-limit` (41) |
| `index-2026-09-2.md` | Dated decisions 2026-09 | `D-2026-09-24-hardening-gates-nothing` to `D-2026-09-30-t025e-live-follow` (14) |
| `index-2026-10-1.md` | Dated decisions 2026-10 | `D-2026-10-01-run-binds-scenario-to-site` to `D-2026-10-11-s3-dispatch-interval-assessment` (38) |
| `index-2026-10-2.md` | Dated decisions 2026-10 | `D-2026-10-11-s3-phase-1-fixture-and-late-evidence` to `D-2026-10-16-s602-closure` (40) |
| `index-2026-10-3.md` | Dated decisions 2026-10 | `D-2026-10-16-s602-questions` to `D-2026-10-31-scn-kobo-reserve-matters` (41) |
| `index-rulings-1.md` | Demo-sprint and later rulings | `D-SR.1` to `D-SR.52` (59) |
| `index-rulings-2.md` | Demo-sprint and later rulings | `D-SR.53` to `D-AW-4` (50) |
| `index-rulings-3.md` | Demo-sprint and later rulings | `D-AW-5` to `D-E5.13` (55) |
| `index-rulings-4.md` | Demo-sprint and later rulings | `D-E5.14` to `D-PRICE.4` (54) |
| `index-rulings-5.md` | Demo-sprint and later rulings | `D-R3.7` to `D-W1-9` (56) |
| `index-rulings-6.md` | Demo-sprint and later rulings | `D-W1-10` to `D-DS1.14` (55) |
| `index-rulings-7.md` | Demo-sprint and later rulings | `D-BW1.1` to `D-2A.12` (49) |
| `index-rulings-8.md` | Demo-sprint and later rulings | `D-3A1.1` to `D-IA.14` (63) |
| `index-rulings-9.md` | Demo-sprint and later rulings | `D-3A2.1` to `D-3A3.8` (51) |
| `index-rulings-10.md` | Demo-sprint and later rulings | `D-4B.1` to `D-IA.31` (51) |
| `index-rulings-11.md` | Demo-sprint and later rulings | `D-ON1.9` to `D-5B.14` (49) |
| `index-rulings-12.md` | Demo-sprint and later rulings | `D-5B.15` to `D-IA.48` (44) |
| `index-rulings-13.md` | Demo-sprint and later rulings | `D-4D.1` to `D-3C2.13` (56) |
| `index-rulings-14.md` | Demo-sprint and later rulings | `D-IA.49` to `D-IA.60`, `D-3C2.15` (13) |
| `index-rulings-15.md` | Demo-sprint and later rulings | `D-SC1.1` to `D-SC1.28`, `D-3C2.14` (29) |
| `index-rulings-16.md` | Demo-sprint and later rulings | `D-0K1.10` to `D-0K1.18`, `D-DS3.9` to `D-DS3.19` (20) |
| `index-rulings-17.md` | Demo-sprint and later rulings | `D-4A.1` to `D-4A.26`, `D-3B6.1` to `D-3B6.12` (38) |
| `index-rulings-18.md` | Demo-sprint and later rulings | `D-3B4.1` to `D-3B4.26`, `D-DS4.1` to `D-DS4.15`, `D-0K2.1` to `D-0K2.16` (57) |
| `index-rulings-19.md` | Demo-sprint and later rulings | `D-0M.1` to `D-0M.22`, `D-DS4.16` to `D-DS4.27`, `D-0K2.17` to `D-0K2.29`, `D-ENV1.1` to `D-ENV1.7` (54) |
| `index-rulings-20.md` | Demo-sprint and later rulings | `D-0K3.1` to `D-0K3.9` (9) |
| `index-rulings-21.md` | Demo-sprint and later rulings | `D-SC1.32` to `D-SC1.39`, `D-3A7.14` to `D-3A7.15`, `D-DS4.28` to `D-DS4.33`, `D-SC1F.1` to `D-SC1F.6`, `D-1A.1` to `D-1A.11`, `D-WK.1` to `D-WK.9` (42) |
| `index-rulings-22.md` | Demo-sprint and later rulings | `D-0K4.1` to `D-0K4.30`, `D-5C.19` to `D-5C.25` (37) |
| `index-rulings-23.md` | Demo-sprint and later rulings | `D-DDR.11` to `D-DDR.16`, `D-WK.10` to `D-WK.16`, `D-3C2.16`, `D-5C.26` to `D-5C.29`, `D-0K4.31` to `D-0K4.44` (32) |
| `index-rulings-24.md` | Demo-sprint and later rulings | `D-0K4.45` to `D-0K4.56` (12) |
| `index-rulings-25.md` | Demo-sprint and later rulings | `D-IAP.1` to `D-IAP.23`, `D-P6.1` to `D-P6.19` (42) |
| `index-rulings-26.md` | Demo-sprint and later rulings | `D-P6.20` to `D-P6.33`, `D-IAP.24` to `D-IAP.33`, `D-DD.1` to `D-DD.16` (40) |
| `index-rulings-27.md` | Demo-sprint and later rulings | `D-DD.17` to `D-DD.47`, `D-P6.34` to `D-P6.41` (39) |
| `index-rulings-28.md` | Demo-sprint and later rulings | `D-P6.42` to `D-P6.67`, `D-DD.48` to `D-DD.66` (46) |
| `index-rulings-29.md` | Demo-sprint and later rulings | `D-DD.67` to `D-DD.96` (30) |
| `index-rulings-30.md` | Demo-sprint and later rulings | `D-IA.61` to `D-IA.81`, `D-P6.68` to `D-P6.81`, `D-IAP.34`, `D-DD.97` to `D-DD.107` (47) |
| `index-rulings-31.md` | Demo-sprint and later rulings | `D-IAP.35` to `D-IAP.51`, `D-P6.82` to `D-P6.99` (35) |
| `index-rulings-32.md` | Demo-sprint and later rulings | `D-DD.108` to `D-DD.145`, `D-T1.19` to `D-T1.26` (46) |
| `index-rulings-33.md` | Demo-sprint and later rulings | `D-DD.146` to `D-DD.180` (35) |
| `index-rulings-34.md` | Demo-sprint and later rulings | `D-DD.181` to `D-DD.185` (5) |

The `index-rulings-*` lines are index-only: demo-sprint and later rulings
(D-SR, D-E5, D-ANY, D-AW, D-W1, D-MONEY and the rest) whose text is in the
rulings parts of `specs/<ID>/` (most in `specs/OWN-GAPS/`) and in Architect files
in `archive/agent-history/` (declutter step 4); each line names its file.

New decisions: append to `<YYYY-MM>.md` of the month (create it if absent; the
first is 2026-11.md) with a `Decision: \`D-YYYY-MM-DD-slug\`` line, or record a
family ruling in its rulings file; add one line to the last matching `index-*.md`
in the same commit. `python tools/check-decision-index.py` checks that every cited
ID resolves and every indexed file exists.
