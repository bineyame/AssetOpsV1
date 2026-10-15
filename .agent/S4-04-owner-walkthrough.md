# S4-04 owner walkthrough - Site Findings index (`sitefindings:1#a/#b`)

What you are accepting: Site > Findings for an imported Site lists the persisted Findings that overlap a chosen
UTC window, newest first, each opening its exact version; an assessed empty window says so with its basis; any
window that is not fully assessed says "not known" with no list and no count. No amounts are shown yet.

All commands run from the repository root (PowerShell), with the repository `.venv`, Postgres on 55432 and
`var/sites/kobo-001.yaml` present. Private database `assetops_s404_owner`, work directory `var/s404_owner`,
API 8934, web 5434. Nothing touches the developer database; no schedule is installed.

## 1. Prepare and serve

```powershell
.venv\Scripts\python.exe tools\s404_finding_index_walkthrough.py prepare      # ~4 min; exit 0 = every check passed
.venv\Scripts\python.exe tools\s404_finding_index_walkthrough.py serve        # keep this window open
# second window, from frontend\:
$env:ASSETOPS_API_PORT="8934"; npm.cmd run dev -- --port 5434 --strictPort
```

`serve` prints these addresses (KOBO-001):

| Fixture | Window (UTC) | Address |
| --- | --- | --- |
| Assessed empty (#a) | 2026-10-25 | http://localhost:5434/sites/KOBO-001/findings?from=2026-10-25T00%3A00%3A00Z&to=2026-10-26T00%3A00%3A00Z&domain=mini-grid-dispatch |
| Positive (#b) | 2026-10-15 | http://localhost:5434/sites/KOBO-001/findings?from=2026-10-15T00%3A00%3A00Z&to=2026-10-16T00%3A00%3A00Z&domain=mini-grid-dispatch |
| Positive, 2 per page | 2026-10-15 | same as above plus `&limit=2` |
| Not assessed | 2026-10-30 | from=2026-10-30T00:00:00Z, to=2026-10-31T00:00:00Z |
| Late evidence waiting (stale) | 2026-10-27 | from=2026-10-27T00:00:00Z, to=2026-10-28T00:00:00Z |
| Failed assessment | 2026-11-05 | from=2026-11-05T00:00:00Z, to=2026-11-06T00:00:00Z |

The manifest `var/s404_owner/s404-manifest.json` lists the exact Finding and revision IDs, selection tokens and
statuses each window read at prepare time.

## 2. Look at

1. **Assessed empty.** Heading "No Findings in this window". Open "What this list is based on": days inspected,
   per-day assessment selection and record, Finding matching pass, selection token.
2. **Not assessed / stale / failed.** Heading "Not known", "Not current" or "Not known" with the reason; the page
   says no Findings are listed, no count is given, and that this is not a "no Findings" statement.
3. **Positive.** "3 Findings in this window", newest period first. Each Finding link opens that exact version
   (`?revision_id=`); reload keeps it. Open one, then its History. "Related" links merged/split/recurrence
   Findings. Amount reads "No amount shown" on every row.
4. **Pages.** With `&limit=2`, "Next page" adds a `cursor` to the address; reload keeps page 2.
5. **Date change.** Change From/To and press "Show Findings": the address changes and the list is read again.

## 3. Late evidence, then settle

```powershell
.venv\Scripts\python.exe tools\s404_finding_index_walkthrough.py late     # API may stay up
```

Reload the positive day: "Not current", no list. Reload the old page-2 address: "This list changed" with
"Start again from the first page". Then:

```powershell
.venv\Scripts\python.exe tools\s404_finding_index_walkthrough.py settle   # ticks assessment + Finding matching
```

Reload the positive day: current again, with one more Finding (16:00-16:40). The old page-2 address still
restarts. Reopen the Finding link you opened in step 2.3: the same exact version opens.

## 4. Source gate

```powershell
.venv\Scripts\python.exe tools\s404_finding_index_walkthrough.py gate --close
```

Reload any window: "Findings list closed for this Site", no list, no count. An exact Finding version link still
opens (audit material). Then reopen and settle:

```powershell
.venv\Scripts\python.exe tools\s404_finding_index_walkthrough.py gate --open
.venv\Scripts\python.exe tools\s404_finding_index_walkthrough.py settle
```

## 5. Compare with v6.9 `sitefindings`

Mock `frontend/mockups/v69/index.html` (`sitefindings`). Deliberately omitted: the All/Cost/Risks/Opportunities
chips, "N open" and "Manage in Findings" global link, priority/confidence badges, and sample money (F-108/F-109
are illustrative). The list has no status model of its own beyond the read's current/not-current state.

Screenshots and claims from `tools/s404-finding-index-evidence.mjs` are listed in `.agent/S4-04-review-packet.md`.

## 6. Clean up

```powershell
.venv\Scripts\python.exe tools\s404_finding_index_walkthrough.py drop
```

## Owner record

Record visual/copy acceptance or feedback here (date, verdict, notes). Merge and `sitefindings:1#a/#b`
promotion are held until this record and the slice review.
