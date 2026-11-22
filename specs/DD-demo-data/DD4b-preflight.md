# DD4b pre-flight: DD4.3 (EV writer) and DD4.4 (measured books)

Builder, 2026-11-22, branch `task/DD4b-ev-measured` from main at 98899a948. One batch (`.ai/RULES.md` §4), each
question with the default the builder takes unless the Architect rules otherwise. BLOCKER marks a question that
stops a unit.

Checked against: `packs/ev_charger.py` (ev-charger/1), `observation/transform.py` (`ev_public_records`, read for the
record set only), `world/exports_ev.py` (`roster_rows`, `TICKETS`), `world/books.py`, `M` (`tenants.metro-bus`,
`history.families` line 2179, `disorder_tests` CLOCK-1), the `/2` file `backend/tests/fixtures/on1/metro-bus.onboarding.json`,
`backend/conversions/world/EV-*-bindings.json`, `tools/dd_check.py`, and DD4a's `ColdSiteRun` on
`task/DD4-cold-ev-reality` (D-DD.81's protocol; read only).

Code reality: neither DD3a's frame (`world/telemetry.py`) nor DD4a (`telemetry_cold.py`, D-DD.81) is on main. DD4.3
therefore builds `EvSiteRun` on D-DD.81's protocol and tests it directly, as DD4a did before its join; refusals are
`ValueError`s whose first word is the `TEL_*` code.

## DD4.3

1. **ev-charger/1 admits two sessions per pack instance** (`PLUG_LABELS = ("session-1", "session-2")`). A charger
   over 129 nights needs about 260. *Default:* the label sequence generalises to `session-<n>`, n = plugs + 1, in
   `packs/ev_charger.py`; the first two labels are v1's, so every v1 run (the Lab EV Sites, `host/ev_publication.py`)
   is byte-identical. A test pins a v1 run's `content_digest` before and after. Reach: that one rule.
2. **Enable schedule.** The `/2` file declares `ev-connector-enabled` ENABLED and no schedule. *Default:*
   `enabled_from 00:00`, `enabled_to time.max` (every UTC minute enabled); no pack change.
3. **Id order.** "Lowest-id connector", "(charger, connector) id order" and "the third charger" read string ids
   (`ch-e10` sorts before `ch-e2`). *Default:* the `/2` file's declared component order (ch-e1..ch-e10, c1 before c2).
   CLOCK-1's third charger is `ch-e3`.
4. **Public rows.** ev-charger/1 emits only events and private boundary documents; its public record set is
   ev-publication/1 in `observation/transform.py`, which spec §4.1 keeps off this path. *Default:* `telemetry_ev.py`
   writes ev-publication/1's record set itself: each connector's `state` every minute; `session-event` and
   `fault-event` at their minute; `energy` as 5-minute `INTERVAL_DELTA` of the meter (cumulative kWh rounded
   half-even to 0.001 at both ends) per started session; `power`, `requested-power`, `allocated-limit` and the Site
   `import` as 5-minute `INTERVAL_MEAN`, split at session boundaries. ev-observation/1 (DROP, HOLD, ADD) is not
   applied. A row's `device_id` is the bound asset (`ch-k1-c1`, or `site-meter` for `import`) and its `signal_id`
   the logical channel; the frame maps (asset, channel) to the binding row's `device_id` and `signal_id` at the
   join. *Volume:* about 47,000 rows per Embakasi day (20 connectors); DD6.3 measures.
5. **A session's minutes.** *Default:* `PLUG` and `AUTHORIZE ACCEPT` at the plug-in minute, charging (START) from
   the next minute, `REQUEST_KW` each minute from the depot manager, `REQUEST_KW 0` once `required_kwh` is met (the
   bus stays plugged), `UNPLUG` at departure (END). A bus still waiting at departure leaves without a session.
6. **Depot manager share.** *Default:* a share is capped by the connector rating, by what the charger has left of
   its rating, and by the remaining need × 60 kW (the exact kW that meets it in one minute), so a share may be a
   fraction. Each pack instance's `site_limit_kw` is its charger rating; base load 0. A connector counts as
   CHARGING for the minute if the pack will start it at that boundary.
7. **A fault under a charging bus.** CH-K2 is a charger fault: `FAULT` on both connectors at 2026-11-01 23:40.
   Ruiru CH-R7 c2 faults at 2026-10-06 00:00, when the 14th bus charges on it. *Default:* the aborted bus rejoins the
   queue at that minute with its remaining need and takes the next freed connector (a new session). Assumed, in
   `conditions`.
8. **The November nights.** *Default:* nights 1 to 5 Nov (from the first day after the accounting period to the day
   before `as_of`); the last departures, 6 Nov 05:00 and 05:30, fall inside the span that ends 06:00. With no
   November `kwh`, each November row's `required_kwh` is `kwh_per_bus_night` exactly. The same `roster_rows`
   writes them (D-DD.52); the roster goldens regenerate. *Information:* `M` gives Ruiru `nights: 6` (11,760 kWh =
   6 × 14 × 140) beside Kasarani's 5; the readings will hold 5 November nights at Ruiru.
9. **Kasarani's spare-bus nights.** `M` lists the spare's free nights only from 7 Nov (outside the span) and
   `spare_bus_nights: 3` without dates. *Default:* nights 2, 3 and 4 Nov (the first three short nights after the
   23:40 fault was found), in a module table `SPARE_NIGHTS` with a manifest parity test (count = `spare_bus_nights`,
   each night inside `short_nights_from`..`period_end`, `spare_buses` = 1). The spare is one more roster row: bus
   `EV-KAS-S01`, block `EV-KAS-BLK-S01`, return 22:00, departure 05:00, `required_kwh` 150.000, plugged in after
   B01..B08.
10. **Prediction, for the Architect (nothing tuned).** With CH-K2 out, three 50 kW chargers over 22:01-05:00 give at
    most about 1,047 kWh against 1,200 required (1,350 on a spare night). By the connector rule the shortfall falls
    on the buses that wait, two a night (three on a spare night), where `M` counts one bus short a night. The plant
    run measures it; the readings stand.
11. **Initial state.** *Default:* 1 Jul 00:00 local, every connector UNPLUGGED, no bus at the depot before its
    first roster return (no 30 Jun night). In `conditions`.
12. **CLOCK-1's rows.** *Default:* every row of `ch-e3`'s connectors whose true `end` falls on 2026-10-15 local while
    a session is plugged on that connector carries `start` and `end` 4 minutes later; the row stays in its true
    day's records. The Site `import` is not shifted. In `conditions` with `disorder_tests` as source.
13. **Session tokens.** *Default:* each charger's `scenario_sha256` is `sha256("assetops.world-ev/1|<site>|<charger>")`,
    so tokens are deterministic and distinct per charger. No random stream is used.
14. **p_m source.** *Default:* a module table (0.36, 0.43, 0.49, 0.55; November 0.55) with a parity test against
    `M` (`history.families` peak share line and October `period.actual.peak_share` at Embakasi).
15. **D-DD.87 for EV.** Allocations are 1 kW quanta or need × 60 with milli-kWh needs, so energy denominators divide
    3,000. The test asserts it over 7 days; if they grow, the builder stops and asks.

## DD4.4

16. **BLOCKER for DD4.4.** `measured.json` is written by the frame (DD3a, not on main), the cold bill needs DD4a's
    room meter (not on main), and spec §4.1 gives no `measured.json` schema while the departure log needs each
    bus-night's kWh at departure, not a month total. *Default:* DD4.4 starts after DD3a, DD4a and the join are on
    main, with this schema: `{"schema": "assetops.world-measured/1", "sites": {<code>: {<month>: {"room_kwh"} |
    {"bands": {<band>: kWh}, "demand_kw"}}}, "departures": [{"site_code", "vehicle_ref", "block_ref",
    "service_day", "departure_at", "required_kwh", "kwh_at_departure"}]}`, exact decimal text.
17. **Band kWh and DEMAND.** *Default:* band kWh = Σ 5-minute Site import mean × 5/60 over slots inside the band's
    local hours (bands are whole hours, so no slot straddles one); DEMAND = the largest mean of six consecutive
    5-minute slots aligned to :00 and :30.
18. **Departure.** *Default:* `kwh_at_departure` = the bus's sessions' meter energy at UNPLUG, rounded half-even to
    0.001; `block_met` = `kwh_at_departure` ≥ `required_kwh`; a bus that never got a connector has 0.
19. **C-DD19 in C5 (D-DD.84).** No question; it lands in DD4.4 as ruled.

No question is a BLOCKER for DD4.3. The builder builds DD4.3 on these defaults.
