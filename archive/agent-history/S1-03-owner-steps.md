# S1-03 owner UI check: Foundation, Single line diagram, Readiness

Branch `task/S1-03-foundation-organization`. Compare each app view with its mock, side by side. Reference captures are in `.agent/S1-03-screens/` (see `INDEX.md`).

## 1. Start the app (PowerShell, from the repository root)

The servers may already be running from the build session: backend on :8010 and frontend on :5183, against the dev database. If http://localhost:5183/sites opens, skip to step 2.

Otherwise:

```powershell
git checkout task/S1-03-foundation-organization
docker compose up -d postgres
$env:DATABASE_URL = "postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/assetops"
.venv\Scripts\python.exe -m uvicorn assetops_backend.main:app --port 8010
```

In a second PowerShell window:

```powershell
cd frontend
$env:ASSETOPS_API_PORT = "8010"
npx vite --port 5183
```

Ports 8010 and 5183 are used because something else on this machine already holds 8000 and 5173. The dev database already holds converted KOBO-001 and the gap Site KOBO-GAP-001, so there is nothing to import.

## 2. Open each pair side by side (two browser windows)

Mock file: `C:\Users\assef\Bineyame\AssetOpsV1\frontend\mockups\v69\index.html`

| View | App | Mock |
|---|---|---|
| Site model | http://localhost:5183/sites/KOBO-001/foundation | `index.html#/foundation` |
| Single line diagram | http://localhost:5183/sites/KOBO-001/foundation/sld | `index.html#/sld` |
| Readiness | http://localhost:5183/sites/KOBO-001/foundation/readiness | `index.html#/readiness` |
| Gap Site | http://localhost:5183/sites/KOBO-GAP-001/foundation and `/foundation/readiness` | (missing-reserve case; no mock) |

Check each pair at full desktop width, then narrow the window to phone width (about 390 px). You can also use DevTools device mode at 390 x 844.

## 3. What to find

### Site model

- [ ] The view row reads *Site model · Single line diagram · Readiness*, in that order, with no *Change & effect* entry.
- [ ] The status strip comes first and shows **Foundation v9**, its effective period, **Binding vN** with the channel count, and "No configuration gap".
- [ ] *Configured topology* sits beside *Identity & operating obligations*.
- [ ] *Time-valid control configuration* shows **Battery reserve 35 %**, and *Change the battery reserve* sits directly under it.
- [ ] Long IDs and digests appear only after you open *Record and inventory details*.
- [ ] On KOBO-GAP-001, a *Configuration gaps* panel says the battery declares no reserve, and the reserve row reads "Not configured".

### Single line diagram

- [ ] The configured diagram is the main visual on the page.
- [ ] In *What each configured part is*, the **Diesel generator** row shows "Generator state: generator-controller / status".
- [ ] In the same table, the **Battery energy storage** row shows "Battery state of charge: battery-pcs-controller / state-of-charge".
- [ ] The node and connection tables are behind *Diagram detail*.
- [ ] Nothing says Online, Reporting or Connected.

### Readiness

- [ ] The verdict comes first: **Ready to report**, with the configuration counts.
- [ ] *Signal bindings* lists `generator-controller / status` (Generator state) and `battery-pcs-controller / state-of-charge` (Battery state of charge), each with its Binding ID.
- [ ] *Change the binding set* is in the same panel.
- [ ] *Acquisition details* shows the **snapshot SHA-256** and a working **Download snapshot** link.
- [ ] On KOBO-GAP-001 the verdict reads **Unknown**.
- [ ] On KOBO-GAP-001 the verdict sentence reads "Not bound: …" followed by "Not configured: Battery reserve".
- [ ] On KOBO-GAP-001, *What is missing* explains each role.

### Across views

- [ ] Choose an earlier period in *Period shown*. The strip turns to a "Historical period" note.
- [ ] Move between the three views. The same period stays selected, and each URL ends in `?at=...`.
- [ ] Reload the page, or copy the URL into a new window. The same view and period reopen.
- [ ] Tab through the page. Each view link shows a focus outline.

## 4. Optional: watch a binding removal

This writes to the database, so try it on a scratch copy if you want to keep the dev data unchanged. The build session did this on a scratch database; the record is `.agent/S1-03-behaviour.txt`.

1. On Readiness, use *Change the binding set* to remove "Battery state of charge" from a future instant, then publish.
2. Choose that period in *Period shown*. Readiness turns **Incomplete** and names Battery state of charge.
3. The Single line diagram at that period lists the SOC channel as "Not bound".
4. Choose *In effect now*. The earlier, complete binding set is back.

## 5. Your verdict

Accept, ask for focused corrections, or decline. The deliberate omissions, and the missing data behind each one, are listed per view in `.agent/S1-03-screens/INDEX.md`.
