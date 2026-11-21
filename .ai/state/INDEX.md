# Built-state index

What completed slices settled in code, and what they left open. This folder replaces
the single `.ai/CODE_STATE.md` (split verbatim by product area on 2026-11-18; since
then: citation path rewrites in declutter steps 4-5, and new entries per RULES §9).

Find a slice: grep its ID in `index-*.md` (one line per slice, original order), then
open the named area file at that `## ` heading. Never read an area file whole.

| File | Area | Sections | Size |
| --- | --- | --- | --- |
| `overview.md` | what the code settles across slices; carried-forward risk | 3 | 15 KB |
| `tools.md` | guards, delivery checker, test turnaround, PIPE-1 | 4 | 7 KB |
| `shell.md` | shared visual vocabulary, shell, mock fidelity, W1 presentation | 16 | 41 KB |
| `lab.md` | Simulator Lab: scenarios, runs, kernel, run store, gateway simulation | 26 | 207 KB |
| `data.md` | ingestion, Site evidence, dispatch, claim limits, provenance, canonical format | 16 | 43 KB |
| `findings-money.md` | Findings, consequence and price, assumption history | 19 | 43 KB |
| `work.md` | Actions, verification, Site and global work; operator accounts | 8 | 22 KB |
| `cold-ev.md` | cold-chain and EV Sites | 8 | 18 KB |
| `estate.md` | Portfolio, outcome board and matrix, coverage | 10 | 21 KB |
| `demo.md` | combined demo dataset, polish passes, add-dates | 10 | 20 KB |
| `sites.md` | Sites, Foundation, SLD, Readiness, Overview, Health | 20 | 77 KB |

Slice lists: `index-1.md`, `index-2.md`, `index-3.md`.

New entries: add a `## <slice ID> - <title>` section to the end of the matching area
file, and one line to the last `index-*.md` (a new part when it passes the 2k-token cap).
A new area gets a new file and a row here. Close an open item in place, naming the slice
that closed it.
