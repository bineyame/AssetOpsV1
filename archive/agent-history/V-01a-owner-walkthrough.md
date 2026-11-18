# V-01a owner walkthrough: Sites and Foundation next to the v6.9 mock (round 3)

This round applies your round-2 feedback and the Architect's round-3 rulings. It covers the same four screens: the Sites list, the Foundation Site model, the single line diagram and Readiness. Put each app screen next to its mock screen and decide whether it now looks right.

Some panels in the mock show facts this product does not have yet. As you asked, the app now says so on the screen instead of leaving the space empty. Those notes are listed below under "What you will see that is missing". If you accept a panel that carries one of these notes, the acceptance is for the layout and wording only, and is conditional on those named gaps. A later task has to supply the missing data and be checked again.

The data is a private copy, so nothing here touches your own servers or `var/`.

## Start (four terminals, from the repository root)

1. `.venv/Scripts/python.exe tools/v01a_foundation_walkthrough.py prepare` copies the Kobo database into `assetops_v01awalk` and creates an empty `assetops_v01aempty`. If the S4 fixture output is missing, run `tools/s4_finding_cases.py run` first. Run `prepare` again to pick up this round's code.
2. `.venv/Scripts/python.exe tools/v01a_foundation_walkthrough.py serve` starts the two data services, on 8860 and 8861.
3. From `frontend/`: `$env:ASSETOPS_API_PORT="8860"; npm.cmd run dev -- --port 5360 --strictPort`
4. From `frontend/`: `$env:ASSETOPS_API_PORT="8861"; npm.cmd run dev -- --port 5361 --strictPort`

`tools/v01a_foundation_walkthrough.py links` prints every address. To repeat the measured checks, run `node tools/v01a-foundation-evidence.mjs http://localhost:5360 <folder> http://localhost:5361`. It should print 185/185 (Finding detail is reported as NOT RUN: this copy has no Finding to open). Press Ctrl+C in each terminal to stop.

The mock pages are at `http://localhost:5360/mockups/v69/index.html#/sites`, `#/foundation`, `#/readiness` and `#/sld`.

## What to look at

1. **Sites** (`http://localhost:5360/sites`).
   - Each row has a new **Operating view** column. It says "Not available yet", with "Assessment · top issue · evidence limit · last analysed" underneath. This is one cell, not four empty columns.
   - Under the table, one line gives the number of Sites listed and says the mock's "Needs attention" and "Evidence limited" counts, and setup progress, are not tracked yet.
   - Empty state: `http://localhost:5361/sites` shows "No sites configured".
2. **Site model** (`/sites/KOBO-001/foundation`).
   - Configured topology and Identity & operating obligations sit side by side on a wide screen and stack on a phone.
   - Identity now shows "First in critical-load priority: …" (from the stored priority), "Configured loads: …" (the stored load parts), "Productive-use designation: Not declared" and "Financial assumptions not available here".
   - The control table has an **Evidence / change** column, as in the mock. Each row says what really exists: "Published configuration · Foundation vN", "Open Dispatch; choose an assessed day", or "No proposed-change record here" / "No linked constraint evidence".
   - IDs, digests, the import record and the raw component tables are under **Advanced details — Foundation records**, closed until you open it.
   - Click a part name in a topology card. A small strip appears inside the topology panel with the part's name, type and rating, "N bound; M not bound", and **Clear selected part**. Its full channel list is under **Advanced details — selected part channels**. The big "Selected part" panel at the top of the page is gone.
3. **Single line diagram** (`.../foundation/sld`).
   - Next to the drawing, a note says: "Protection and meter positions are not declared in this Foundation topology; monitoring links and reporting status are not assessed on this diagram. See Site Evidence for reported records." No breakers, meters or status dots are drawn, because they would show equipment this Site does not declare.
   - The parts table shows only channel counts. The full lists, topology IDs and devices are under **Advanced details — diagram records**.
   - Choosing a part (click, or Tab and Enter) shows the same small strip under the drawing. On a phone it stays on screen while the drawing scrolls sideways in its own box.
4. **Readiness** (`.../foundation/readiness`). The order now follows the mock:
   - the overall verdict, then four cards: Definition, Topology, Specifications and Controls, each "Configured" (green, with a tick), "Needs configuration" (amber) or "Unknown" (grey);
   - the **Readiness and commissioning evidence** table (Area, Declared, Confirmed, What is needed, Next step);
   - **Gateway status**: the registered gateway, whether it is enabled, and when the server last heard from it ("Current", "Stale" or "Unknown", in a grey badge). On this copy it says **Stale**, because the last diagnostic is hours old. A note explains that this is checked now on the server clock, even when you are looking at a past or scheduled Foundation period;
   - **Advanced details — roles, channels and records** holds role coverage, signal bindings and the binding form. The "Review or change bindings" link in the table opens it and puts you on the form.
   - With a chosen part in the address, Readiness shows only a small chip linking back to it.
5. **Narrow screens (390 px).** The cards stack, the table and drawing scroll in their own boxes, and the strips and notes stay readable.

## What you will see that is missing

| Screen | Exact words on screen | What is missing and what would fill it |
| --- | --- | --- |
| Sites | "Not available yet" / "Assessment · top issue · evidence limit · last analysed" | A per-Site summary for a chosen time window and a ranking of Findings. Later Sites/Findings work. |
| Sites | "… Needs attention and Evidence limited counts across Sites are not available yet: there is no common window or aggregation contract for them. Setup progress not tracked yet." | A common window and roll-up rule across Sites; onboarding progress (`sites:2`, W6). |
| Site model | "Productive-use designation: Not declared" | A typed productive-use field in the Foundation. A later Foundation contract task. |
| Site model | "Financial assumptions not available here." | A reviewed financial-assumptions page. Later financial work. |
| Site model | "No proposed-change record here", "No linked constraint evidence" | Change proposals (S6) and control-specific evidence. |
| Site model | "Critical-load priority not configured" (only if a period has no priority; Kobo has one) | The Site's own configuration. |
| Readiness | "Not recorded" in every Confirmed cell, and "Commissioning confirmation not recorded" | A commissioning or field-confirmation record. No such record exists yet. |
| Readiness | "Not available yet: uptime trend, expected-versus-delivered completeness, signal strength and firmware. No reviewed source for these fields." | A reviewed source for these gateway figures. |
| Readiness | "Device connection not established here." | Proof that a physical source is connected. Not claimed by this read. |
| Readiness | "Gateway contact unavailable." (only when the gateway read fails) or "Contact unknown — no central diagnostic received." (no diagnostic yet) | Not seen on this copy, which answers "Stale". The evidence tool shows both by answering the read differently in the browser; screenshots `app-readiness-gateway-*`. |
| Single line diagram | the protection and meter sentence quoted above, and "Readings not assessed here" under each part | Declared protection and meter positions in the topology; reporting status (Site Evidence). |

## What to decide

- For each screen, at both widths: does it now look acceptable next to the mock?
- For a panel with a row in the table above, an acceptance would be recorded as: **"Owner visual acceptance conditional on these named data gaps; layout/copy accepted only."** It would not close any technical item or mark a screen as fully real.
- If something still looks wrong, say which screen and what, in your own words.
