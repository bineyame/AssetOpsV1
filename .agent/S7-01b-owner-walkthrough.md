# S7-01b owner walkthrough - Site Health (gateway contact) and the battery page

About 15 minutes. Everything runs on a private copy of the data that is removed at the end.
You need three PowerShell windows. Docker Postgres must be running (it normally is).

## 1. Prepare (window 1, once, about 1 minute)

```powershell
cd C:\Users\assef\Bineyame\AssetOpsV1-review
.\.venv\Scripts\python.exe tools\s701_health_walkthrough.py --db assetops_s701_owner1 --work var/s701_owner1 prepare
```

It ends with `Prepared.` It sets up two sites:

- **KOBO-001** has eight test gateways, one for each situation, plus its original gateway, which is disabled.
- **KOBO-002** has only a disabled gateway and no battery.

## 2. Start the servers

Window 1 (leave it running):

```powershell
.\.venv\Scripts\python.exe tools\s701_health_walkthrough.py --db assetops_s701_owner1 --work var/s701_owner1 serve
```

Window 2 (leave it running):

```powershell
cd C:\Users\assef\Bineyame\AssetOpsV1-review\frontend
$env:ASSETOPS_API_PORT="8947"; npm.cmd run dev -- --port 5447 --strictPort
```

Window 1 prints the exact addresses, including the KOBO-001 battery address (it holds an ID).

## 3. Refresh just before you look (window 3)

```powershell
cd C:\Users\assef\Bineyame\AssetOpsV1-review
.\.venv\Scripts\python.exe tools\s701_health_walkthrough.py --db assetops_s701_owner1 --work var/s701_owner1 deliver
.\.venv\Scripts\python.exe tools\s701_health_walkthrough.py --db assetops_s701_owner1 --work var/s701_owner1 attest
```

`attest` must end with `attest: ok`.

The gateways report every minute, and a gateway counts as stale after 2 minutes with no report. Open the pages within about 2 minutes of `deliver`. If more time passes, run `deliver` again and reload the page.

## 4. What to look at

**http://127.0.0.1:5447/sites/KOBO-001/health**

- The Health tab is selected.
- The strip at the top reads "Gateway contact: not all current", then "8 enabled gateways: 6 current, 1 stale, 1 unknown · 1 disabled, not counted". It never says "Site health" or "healthy".
- **Battery condition** is the first section. It reads "Unknown", with "Open battery".
- **Gateway contact** has one row per gateway:
  - `edge-kobo-001` shows a "Disabled" tag and is not counted.
  - `s7-stale-cadence` reads "Stale: nothing received for N min; when it stopped is not known".
  - `s7-delayed-old` has current contact, but its facts read "Old: observed 6 h ago; it reached the server 6 h after it was observed".
  - `s7-clock-offset` reads "Unknown age: the gateway's clock is off by 95 s, more than the 5 s allowed". It shows no age at all, and no negative age.
  - `s7-never-received` reads "Never received".
- **Queue and storage, as last reported**:
  - `s7-queue-growth` shows 900 waiting, the oldest waiting 1 h 30 min.
  - `s7-disk-stop` reads "Full: collection stopped".
  - `s7-disk-recovery` reads "Normal" and "none waiting".
- **Device contact reported by gateways** gives the device times as each gateway reported them.
- A blue note at the bottom says that a gateway being heard from does not make equipment healthy.
- **Technical details** is closed. Open it to see the IDs, the rule and the selection watermark.
- Click **Details** on `s7-clock-offset`, or Tab to it and press Enter. The address gains `?gateway=...` and a panel shows that gateway's latest report ID. Reload the page: the same gateway stays selected. Press Back: you return to the full list.

**Open battery** (or the battery address printed by `serve`)

- The page shows "Condition: Unknown" and "Capacity: unverified".
- Four tiles:
  - Physical condition: Unknown (3 inputs missing).
  - Declared rating: 200 kWh, "a configuration rating, not a measurement".
  - State of charge: Not shown.
  - Signal channels: 1 connected.
- The table lists the three missing inputs: temperature history, measured usable capacity, and charge and discharge stress history.
- "Not stated on this page" lists degradation, remaining life, warranty and replacement. None of them is claimed.

**http://127.0.0.1:5447/sites/KOBO-002/health**

- The strip reads "Gateway contact: no enabled gateway", then "No gateway is enabled for this site, so nothing is known about contact". There is no "0 current" and no green zero.
- Battery condition reads "Unknown (not configured)".

**http://127.0.0.1:5447/sites/KOBO-002/assets**

- The page reads "No battery configured". It shows no asset ID and no link.

**Refusal check:** open the KOBO-002 battery address with an ID that is not part of its configuration. Window 1 prints one, or reuse the KOBO-001 battery ID with `KOBO-002` in the address. The page reads "Battery not found ... not a battery in this site's current configuration" and shows no condition.

**Compare with the mockup** at 1440 px wide and at phone width (390 px):

- http://127.0.0.1:5447/mockups/v69/index.html#/health
- http://127.0.0.1:5447/mockups/v69/index.html#/asset

Only what the data supports is shown. The mock's illustrative weekly reserve chart, stress counts and warranty date are deliberately absent, because no accepted data exists for them.

## 5. Stop and clean up

1. Press Ctrl+C in windows 1 and 2.
2. In window 3, run:

```powershell
.\.venv\Scripts\python.exe tools\s701_health_walkthrough.py --db assetops_s701_owner1 --work var/s701_owner1 drop
```

It prints `dropped database assetops_s701_owner1` and `removed ...var\s701_owner1`.
