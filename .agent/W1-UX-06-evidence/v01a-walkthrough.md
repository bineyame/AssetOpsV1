# Walkthrough: Sites, Foundation, Readiness, single line diagram (`v01a_foundation_walkthrough.py`)

## 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432.
- `var/sites/kobo-001.yaml` copied from the main checkout into this folder (`var/` is ignored by git).
- The shared test database `assetops_s4cases` must exist. If `docker exec assetopsv1-postgres-1 psql -U assetops -lqt` does not list it, run once:
```
.venv\Scripts\python.exe tools\s4_finding_cases.py run
```

## 2. Commands (PowerShell, in order)
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3
$wt="C:\Users\assef\Bineyame\AssetOpsV1-review3"; $env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--db","assetops_v01awalk_w1ux06","--empty-db","assetops_v01aempty_w1ux06","--work-name","v01a-w1ux06"
.venv\Scripts\python.exe tools\v01a_foundation_walkthrough.py @T prepare
.venv\Scripts\python.exe tools\v01a_foundation_walkthrough.py @T links --web-port 5460 --empty-web-port 5461
.venv\Scripts\python.exe tools\v01a_foundation_walkthrough.py @T serve --port 8960 --web-port 5460 --empty-port 8961 --empty-web-port 5461
```
Second window (stocked site):
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3\frontend; $env:ASSETOPS_API_PORT="8960"; npm.cmd run dev -- --port 5460 --strictPort
```
Third window (no site stored):
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3\frontend; $env:ASSETOPS_API_PORT="8961"; npm.cmd run dev -- --port 5461 --strictPort
```

## 3. Ports and addresses
APIs 8960 (stocked) and 8961 (empty); web 5460 and 5461. Mock: `http://localhost:5460/mockups/v69/index.html#/<id>`.

| Screen | Address | Mock |
| --- | --- | --- |
| Sites | http://localhost:5460/sites | `#/sites` |
| Sites, none stored | http://localhost:5461/sites | `#/sites` |
| Site model, in effect now | http://localhost:5460/sites/KOBO-001/foundation | `#/foundation` |
| Site model, scheduled | http://localhost:5460/sites/KOBO-001/foundation?at=2026-10-22T00:00:00Z | `#/foundation` |
| Site model, before any stored version | http://localhost:5460/sites/KOBO-001/foundation?at=2026-09-01T00:00:00Z | `#/foundation` |
| Readiness, now | http://localhost:5460/sites/KOBO-001/foundation/readiness | `#/readiness` |
| Readiness, imported period | http://localhost:5460/sites/KOBO-001/foundation/readiness?at=2026-09-30T00:00:00Z | `#/readiness` |
| Diagram, now | http://localhost:5460/sites/KOBO-001/foundation/sld | `#/sld` |
| Diagram, battery chosen | http://localhost:5460/sites/KOBO-001/foundation/sld?at=2026-10-22T00:00:00Z&component=battery | `#/sld` |

## 4. What to look for
- The bold first sentence of the top card answers the question in plain words (for example "9 pieces of equipment and 4 of 5 operating settings are recorded").
- Under it, with "How this was worked out" still closed, the state box shows the state, the site and version, and an "As of" time. On Sites it says "As of: time not recorded" (the list has no read time).
- The small picture (bars or setting tiles) is beside the answer; Sites has none by design.
- The link under the card goes to the next place (Readiness, Single line diagram, Health).
- Scheduled view: a yellow line says this is not the configuration in effect now.
- Before any stored version: only the state line shows, no card (by design). Look by eye only.
- Battery chosen: the battery is highlighted and stays chosen after a reload.
- Keyboard: press Tab from the top of the page; it reaches "How this was worked out".
- Exact link: paste the address in a new tab; the same view opens. Reload: nothing changes.

## 5. Data label
Authored test configuration of KOBO-001 (imported and published Foundation versions). Not field readings.

## 6. Stop and clean up
Ctrl+C in all three windows, then:
```
.venv\Scripts\python.exe tools\v01a_foundation_walkthrough.py @T drop
```
`drop` removes both databases and the work folder `%LOCALAPPDATA%\AssetOps\v01a-w1ux06`.

## 7. Captured in final run (code `b7d75daf`)
| Screen | Case | Address (localhost) | 1440 | 390 | App vs mock |
| --- | --- | --- | --- | --- | --- |
| sites | stocked | 5460/sites | 17/17 (both cases) | 19/19 (both cases) | mock counts (needs attention, evidence limited), assessment/top-issue columns and "In setup" table not built; shown as "Not available yet" |
| sites | empty | 5461/sites | pass | pass | no "How this was worked out" in this state (nothing to reference) |
| foundation | now, scheduled | 5460/.../foundation[?at=2026-10-22...] | pass | pass | |
| foundation | before any version | ?at=2026-09-01... | **not run** | **not run** | no card by design; manual look only |
| readiness | now, imported | .../readiness[?at=2026-09-30...] | pass | pass | stale gateway contact shows only in the panel below the card |
| sld | now, battery | .../sld[?at=2026-10-22...&component=battery] | pass | pass | at 390 the diagram is cut at the right edge and scrolls inside its own box |

Totals: `w1-ux-02` 36/36 (`v01a-w1-ux-02.txt`); `w1-ux-05` 108/108, 54 at 1440 and 54 at 390 (`v01a-w1-ux-05.txt`). Screenshots: `%TEMP%\w1ux06-final\v01a` (not in git).
