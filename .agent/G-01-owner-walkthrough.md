# G-01 owner walkthrough: the gateway firmware missing state

## What changed

The Readiness page has a **Gateway status** panel. Its old closing line named four things the product cannot report yet: uptime trend, expected-versus-delivered completeness, signal strength and firmware. Firmware now has a line of its own:

> Firmware not available yet: no reviewed source reports what firmware a gateway runs.

The other line now names only uptime trend, completeness and signal strength.

The firmware line is the first missing state linked to an entry in the new gap catalogue. That entry is `G-readiness-gateway-firmware`. It records that no source exists for firmware, and that you and the Architect are its owners. The ID is never shown on screen; it is on the line's HTML as `data-gap-id`. No firmware value is invented anywhere.

Behind the scenes:
- The normal checks reject any missing-state line that points at an unknown gap.
- They reject new "not available yet" copy that is not linked to a gap.
- They reject growth in the dated list of 16 older lines that are not linked yet. G-02 to G-05 will link those and shrink the list.
- W1 scoring, K=10 and next-work ranking are unchanged. A test proves the same decision and scores with and without catalogue entries.

## Start (four terminals, from the repository root)

This uses private databases `assetops_g01walk` and `assetops_g01empty` and the owner ports 8864/8865 (data) and 5364/5365 (web). Nothing touches your other servers or `var/`.

1. `.venv/Scripts/python.exe tools/v01a_foundation_walkthrough.py --db assetops_g01walk --empty-db assetops_g01empty --work-name g01-owner prepare`
   - Docker Desktop's Postgres must be running.
   - If the S4 fixture output is missing, run `.venv/Scripts/python.exe tools/s4_finding_cases.py run` first.
2. `.venv/Scripts/python.exe tools/v01a_foundation_walkthrough.py --db assetops_g01walk --empty-db assetops_g01empty --work-name g01-owner serve --port 8864 --web-port 5364 --empty-port 8865 --empty-web-port 5365`
3. From `frontend/`: `$env:ASSETOPS_API_PORT="8864"; npm.cmd run dev -- --port 5364 --strictPort`
4. From `frontend/` (optional, empty store): `$env:ASSETOPS_API_PORT="8865"; npm.cmd run dev -- --port 5365 --strictPort`

To repeat the measured checks at 1440 and 390 pixels, run `node tools/g01-firmware-evidence.mjs http://localhost:5364 <folder>`. It prints `N/M claims passed`.

## What to look at

1. Open `http://localhost:5364/sites/KOBO-001/foundation/readiness` and scroll to **Gateway status**.
   - The contact read shows the registered gateway as **Stale**, because its last diagnostic is hours old.
   - Under the panel body you will see two lines:
     - "Not available yet: uptime trend, expected-versus-delivered completeness and signal strength. No reviewed source for these fields."
     - "Firmware not available yet: no reviewed source reports what firmware a gateway runs."
2. Reload the page. The firmware line stays the same.
3. Narrow the window to phone width, about 390 px. Both lines wrap inside the panel, and the page does not scroll sideways.
4. Optional, to inspect the link: right-click the firmware line and choose Inspect. It carries `data-gap-id="G-readiness-gateway-firmware"` and `data-gap-placement="readiness.gateway.firmware"`.
5. The firmware line appears whatever the contact read returns: current, stale, unknown, failed, or no gateway. The evidence tool shows these states by substituting the browser's response. That proves only what the screen renders for each answer. It says nothing about the gateway itself.

## Your decision

Is the separate, plain firmware line the right missing-state treatment for gateway facts we have no source for? G-02 will apply the same treatment to signal strength, uptime, completeness, commissioning and the other V-01a missing facts.

Accepting it does not make the Gateway status panel or the Readiness screen Real. Firmware stays an unallocated data-source gap, "pending owner review", until you choose a firmware source at the W1-exit gap allocation.

## Stop

- Press Ctrl+C in each terminal.
- Then run `.venv/Scripts/python.exe tools/v01a_foundation_walkthrough.py --db assetops_g01walk --empty-db assetops_g01empty drop`.
