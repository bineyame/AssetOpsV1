# Lane-T: split map

`.agent/build-spec-telemetry-2026-10-27.md` (134 KB, 963 lines, sha256 `1ac12e37b886dd4e`) moved here on 2026-11-18 (declutter step 4) and was split by its own headings, verbatim and in order, into `spec.md` 57 KB, `spec-2.md` 23 KB, `spec-3.md` 52 KB, `rulings.md` 0 KB. Open the part a citation names; an old `file:line` citation maps through the table (old lines -> part lines). Proof: `python tools/declutter/split_specs.py --verify`.

| # | Old lines | Part | Part lines | Section |
| --- | --- | --- | --- | --- |
| 1 | 1-12 | `spec.md` | 1-12 | Build spec, telemetry lane (Lane T), 2026-10-27 |
| 2 | 13-216 | `spec.md` | 13-216 | 0. Lane rules (every task) |
| 3 | 217-226 | `rulings.md` | 1-10 | TEL-00 · Pre-flight and card corrections (no code) · 0.25 d |
| 4 | 227-370 | `spec.md` | 217-360 | TEL-01 · Shared core: profile, decode, clock, aggregate, report, pu... |
| 5 | 371-419 | `spec.md` | 361-409 | TEL-02 · Read-only Modbus TCP client · 0.5 d |
| 6 | 420-468 | `spec.md` | 410-458 | TEL-03 · GX-shaped emulator, profile `-1` and pinned JSONL · 0.75 d |
| 7 | 469-522 | `spec.md` | 459-512 | TEL-04 · Poller and focused end-to-end through a real gateway proce... |
| 8 | 523-541 | `spec-2.md` | 1-19 | TEL-05 · Postgres acceptance, profile `-1` · 0.5 d · run alone |
| 9 | 542-571 | `spec-2.md` | 20-49 | TEL-08 · BeagleBone Black repeat (stage 2, TCP only) · 0.75 d (+ ow... |
| 10 | 572-607 | `spec-2.md` | 50-85 | TEL-05b · Finding proof, profile `-2` · 0.75 d (focused parts can b... |
| 11 | 608-629 | `spec-2.md` | 86-107 | TEL-07 · Claim records and demo runbook · 0.25 d |
| 12 | 630-658 | `spec-2.md` | 108-136 | TEL-06 · Minimal generic CSV collector (B1) · 0.5 d + 0.25 d · afte... |
| 13 | 659-963 | `spec-3.md` | 1-305 | Implementer questions and resolutions |
