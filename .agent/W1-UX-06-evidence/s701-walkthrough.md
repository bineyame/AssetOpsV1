# Walkthrough: Health and battery (`s701_health_walkthrough.py`)

## 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432.
- `var/sites/kobo-001.yaml` copied from the main checkout into this folder (`var/` is ignored by git).

## 2. Commands (PowerShell, in order)
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3
$wt="C:\Users\assef\Bineyame\AssetOpsV1-review3"; $env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--db","assetops_s701_owner_w1ux06","--work","var/s701_owner_w1ux06"
.venv\Scripts\python.exe tools\s701_health_walkthrough.py @T prepare
.venv\Scripts\python.exe tools\s701_health_walkthrough.py @T serve --port 8970 --web-port 5470
```
Second window:
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3\frontend; $env:ASSETOPS_API_PORT="8970"; npm.cmd run dev -- --port 5470 --strictPort
```
Third window, once the API is up (prints the battery address), then right before looking (fresh contacts last about 2 minutes), then the self-check:
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3
$wt="C:\Users\assef\Bineyame\AssetOpsV1-review3"; $env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--db","assetops_s701_owner_w1ux06","--work","var/s701_owner_w1ux06"
.venv\Scripts\python.exe tools\s701_health_walkthrough.py @T links --port 8970 --web-port 5470
.venv\Scripts\python.exe tools\s701_health_walkthrough.py @T deliver
.venv\Scripts\python.exe tools\s701_health_walkthrough.py @T attest --port 8970
```
`attest` should end with `attest: ok`.

## 3. Ports and addresses
API 8970, web 5470. The tool prints `127.0.0.1`; open the same port and path on `localhost`. Mock: `http://localhost:5470/mockups/v69/index.html#/<id>`.

| Screen | Address | Mock |
| --- | --- | --- |
| Health, KOBO-001 | http://localhost:5470/sites/KOBO-001/health | `#/health` |
| Health, KOBO-002 (no gateway) | http://localhost:5470/sites/KOBO-002/health | `#/health` |
| Battery, KOBO-001 | http://localhost:5470/sites/KOBO-001/assets/<id printed by links> (this run `61e5e895-c41a-4ef4-b3e8-6df022af4053`; it changes every prepare) | `#/asset` |
| Battery refusal | http://localhost:5470/sites/KOBO-002/assets/00000000-0000-4000-8000-000000000000 | `#/asset` |

## 4. What to look for
- Health KOBO-001: the bold answer reads "4 of 8 enabled gateways need attention"; the yellow box says some gateways are not in contact, with site and "As of" time, while "How this was worked out" is closed.
- Two bar groups: contact (in contact / out of contact / never heard) and how old the reports are. "What to do" links open each gateway.
- The battery link goes to the battery page.
- KOBO-002: says there is no gateway to read from, with no empty bars pretending to be zero.
- Battery: says its condition cannot be judged yet and lists the missing inputs.
- Refusal address: a plain refusal panel (no card).
- Keyboard: Tab reaches "How this was worked out". Exact link: paste in a new tab, same view. Reload: same view (after about 2 minutes, contacts turn old; run `deliver` again).

## 5. Data label
Generated test data: eight test gateways on KOBO-001 with made-up reports; KOBO-002 has no enabled gateway. Not field readings.

## 6. Stop and clean up
Ctrl+C in both windows, then:
```
.venv\Scripts\python.exe tools\s701_health_walkthrough.py @T drop
```

## 7. Captured in final run (code `7350857f`, after `deliver`, `attest: ok`)
| Screen | Case | Address (localhost:5470) | 1440 | 390 | App vs mock |
| --- | --- | --- | --- | --- | --- |
| health | KOBO-001 | /sites/KOBO-001/health | pass | pass | both bar groups use the same colour; meaning is in words |
| health | KOBO-002 no source | /sites/KOBO-002/health | pass | pass | |
| health | selected gateway | `?gateway=<id>` | **not run** | **not run** | neither `links`, `serve` nor `deliver` prints a gateway ID |
| asset | KOBO-001 battery | /sites/KOBO-001/assets/61e5e895-... | pass | pass | |
| asset | refusal | /sites/KOBO-002/assets/0000... | **not run** | **not run** | refusal panel has no card |

Totals: `w1-ux-05` 56/56, 28 at 1440 and 28 at 390 (`s701-w1-ux-05.txt`). Screenshots: `%TEMP%\w1ux06-final\s701` (not in git).
