#!/usr/bin/env python3
"""Build model for the Layer 4 pack: the slice list of delivery-plan.md (#6) and every computed table of
two-week-build-plan.md (#6b); also the owner-time tables commercial-plan.md (#9) uses. One source, so the documents
cannot drift.

Design-pack tool, not product code. Python 3 standard library only. Moved from Docs/go-to-market/plan_model.py
(two-week-conversion-plan.md rev 4.3) by pack plan F §5 and rebuilt for the build-only fortnight (owner, 19 Nov:
"recreat tehe two week plan focussed on advancing as much as possible towarfs the new features, not the markting
element"). The selling track, demo days, the offer kit and PIPE-2 are gone. The capacity inputs (memory, observed pace,
rework, reviewer stream) and the owner-time model for #9 are carried over unchanged, with their sources.

Run: python3 plan_model.py                 -> prints every computed table and the prose facts
     python3 plan_model.py --fill F        -> writes each table between <!--table:NAME--> and <!--/table--> in F, then checks
     python3 plan_model.py --check F       -> exit 1 if any table block in F differs from this model, if a table F must
                                              carry is missing, if a prose fact F must state is absent, or if a
                                              must-keep slice does not land by its day
     python3 plan_model.py --check         -> checks every pack document that carries tables from this model

Units. Build effort is in UNITS: one reviewed merge of one to three commits (W4), the unit the git history counts.
Structure pages (W1) are in Architect lane-days. Day 1 is the first build day after the owner approves the recreated
pack; time t is in lane-days from the start of day 1, and day(t) = floor(t) + 1.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent

# ================================================================ 1. capacity inputs (carried over, with their sources)
MEM_AVAILABLE_GB = 14.0   # measured `free -g` "available", 18 Nov, with the walkthrough server, lab_app, Postgres and the coordinator running
MEM_HEADROOM_GB = 2.0     # assumption: no swap, so an out-of-memory kill could hit Postgres or the owner's walkthrough server
AGENT_GB = 0.6            # measured: one Claude agent process, 0.57 GB resident (ps, 18 Nov)
HEAVY_GB = 3.1            # check-all at 4-way: sum of the four largest measured guard peaks (pipeline evaluation §5, P2)
TSC_GB = 1.26             # measured `tsc --noEmit` peak (pipeline evaluation §4.2)
LIGHT_GB = 0.4            # one focused pytest process, 0.34 GB measured (pipeline evaluation P12), rounded up
HEAVY_SLOTS = 2           # at most 2 check-all runs at once (RULES §7, PIPE-1 slot)
DB_JOB_GB = 1.5           # ASSUMPTION, not measured: one heavy database job above the Postgres already counted
DB_JOB_GB_HIGH = 3.1      # pessimistic case: a database job as large as a check-all slot
REVIEWERS, SPEC_AGENTS = 1, 1   # one fresh-review slot; the Architect (no writing pool: the selling track is dropped)


def peak_gb(b, pooled, db=None):
    """Worst-case resident memory with b builders while the one heavy database job runs. Pooled (the heavy-tool slot
    pool, `B03` in the go-to-market numbering): heavy tools and the database job share check-all's two slots."""
    db = DB_JOB_GB if db is None else db
    agents = (b + REVIEWERS + SPEC_AGENTS) * AGENT_GB
    n = b + REVIEWERS
    if pooled:
        return agents + max(HEAVY_SLOTS * HEAVY_GB + max(0, n - HEAVY_SLOTS) * LIGHT_GB,
                            (HEAVY_SLOTS - 1) * HEAVY_GB + db + max(0, n - HEAVY_SLOTS + 1) * LIGHT_GB)
    return agents + HEAVY_SLOTS * HEAVY_GB + db + max(0, n - HEAVY_SLOTS) * TSC_GB


BUDGET_GB = MEM_AVAILABLE_GB - MEM_HEADROOM_GB
LANE_CAP = 4              # W4 as amended by the owner (sitting 1, item 7): four build lanes for this fortnight


def max_lanes(pooled):
    b = 1
    while b < LANE_CAP and peak_gb(b + 1, pooled) <= BUDGET_GB + 1e-9:
        b += 1
    return b


N_POOLED, N_UNPOOLED = max_lanes(True), max_lanes(False)
MARGIN = round(BUDGET_GB - peak_gb(N_POOLED, True), 2)
MARGIN_HIGH = round(BUDGET_GB - peak_gb(N_POOLED, True, DB_JOB_GB_HIGH), 2)

# Observed pace (git, first-parent task merges to main, 18 Oct - 14 Nov)
OBS_MERGES, OBS_SPAN_DAYS, OBS_OPEN = 237, 26.29, 1.88
OBS_PACE = round(OBS_MERGES / OBS_SPAN_DAYS / OBS_OPEN, 2)     # units per lane-day (Little's law)
PACES = {"slip": 2.0, "plan": 3.0, "observed": OBS_PACE}        # plan = about 0.6 of observed: new schema and money work,
                                                                # discovery reviews (W5), checks first (W2), four lanes
REWORK = 0.15             # explicit rework allowance per unit, the low end of the old roadmap's 15-20%
REVIEW_MIN = {"discovery": 45, "standard": 30}                  # W5: discovery for a new schema, mechanism, seam or money figure
REREVIEW_MIN, REREVIEW_SHARE = 15, 0.5
REVIEW_HOURS_A_DAY = 14   # assumption: hours a day the coordinator dispatches agents
COMMIT_BY = 12            # committed = lands by day 12 at the planning pace (two days of reserve)

# ================================================================ 2. the slices (delivery-plan.md §2) and structure pages
# Each build slice: id, step (Figure 10), construct, what it builds, lane, units (low, high), depends on, structure page,
# flags. Lanes: SRC sources and money (Figure 10 lane A), STR structure and the plan's records (lane B), DEC the recorded
# person, decisions and proof, SCR screens and tooling, ANY a gap-filler (read-only calibration). Units: the old backlog's
# ranges where the work is the same (two-week-conversion-plan rev 4.3 §3.3), the Architect's estimate where it is new
# (marked "new"). Flags: schema (new table or mechanism), money (a money figure), new (estimate is new).
STEP_ORDER = ["T", "0", "1", "2", "3A", "3B", "3C", "4", "5", "6", "7", "8", "9", "W"]
PATH = ["1", "2", "3A", "3B", "3C", "4", "5", "6", "7", "8", "9"]   # Figure 10's steps, in order
STEP_NAME = {"T": "Tooling: the heavy-tool slot pool", "0": "0 Calibration replays K, M, E", "1": "1 Correct the last-day figure",
             "2": "2 Canonical format and leaf factor IDs", "3A": "3A Sources", "3B": "3B Structure", "3C": "3C Recorded person",
             "4": "4 Join at the money leaves", "5": "5 Targets and the bridge", "6": "6 Decisions and options",
             "7": "7 The plan and the Portfolio", "8": "8 Three verdicts", "9": "9 Rights, cold then EV, pilot onboarding", "W": "The day-14 walkthrough database"}
SLICES = [
    ("T1", "T", "tooling", "Heavy-tool slot pool, enforced: tsc, vitest, Postgres test files, browser captures and the heavy database job take one of check-all's two slots; a hook refuses an unpooled run", "SCR", (2, 3), [], None, ""),
    ("0K", "0", "CH3", "Spike K: the forward replay adapter behind a new port method, and Kobo's stop-threshold replay on the simulated series", "DEC", (5, 9), [], None, ""),
    ("0M", "0", "CH3", "Spike M: Mto's demand-on-headroom replay through the same adapter", "ANY", (2, 5), ["0K"], None, ""),
    ("0E", "0", "CH3", "Spike E: Embakasi's charging-schedule replay through the same adapter", "ANY", (3, 6), ["0K"], None, ""),
    ("1a", "1", "CH5", "Pin the Optimize card's last-day behaviour, then correct it: the period's figure, or the day and scope stated", "SCR", (2, 3), [], "P1", ""),
    ("1b", "1", "CH5", "Render the fields the API already computes on the Portfolio and the site board", "SCR", (3, 5), ["1a"], "P1", ""),
    ("2a", "2", "B3", "Canonical format version 1 per source type, and the leaf factor IDs, as code the store and the registry share", "STR", (1, 2), [], "P2", "schema"),
    ("3A1", "3A", "B3", "Commercial record store: immutable raw payload, source-versioned revisions, every record kind of the three verticals declared", "SRC", (2, 4), ["2a"], "P3A", "schema"),
    ("3A2", "3A", "B3", "File intake on the authenticated site-bound path: dry run, plain-word refusals, late records revise closed periods", "SRC", (2, 4), ["3A1"], "P3A", ""),
    ("3A3", "3A", "B3", "Emulators for billing, collections, fuel purchases and budget lines, and the contract test every real source must pass", "SRC", (2, 4), ["3A2"], "P3A", ""),
    ("3A4", "3A", "B3", "Recorded amounts read by recognition period; a late record marks dependent reads as superseded", "SRC", (1, 3), ["3A1"], "P3A", "money"),
    ("3A5", "3A", "B3", "Evidence labels: Emulated beside Recorded on every figure; no total above its weakest part; benefit only from field records (D14)", "SCR", (2, 3), ["3A1"], "P3A", "money"),
    ("3B1", "3B", "B1", "Structure registry in code: mini-grid in full from leaves to outcomes; Protect and operations measures", "STR", (3, 5), ["2a"], "P3B", "schema"),
    ("3B2", "3B", "CH1", "Findings pinned: one registry row per mechanism today; the outcome map's literal removed only after its parity test", "STR", (2, 3), ["3B1"], "P3B", ""),
    ("3B3", "3B", "B1", "Structure read, Site and portfolio: bottom-up on today's operational leaves, coverage, evidence class, nothing stored as a total", "STR", (2, 4), ["3B1"], "P3B", ""),
    ("3B4", "3B", "CH1", "Structure observer: deviations stored as Findings under the owner's rule and outside the factor's tolerance (OD-3)", "STR", (2, 3), ["3B3", "3C1"], "P3B", "new"),
    ("3B5", "3B", "B1", "Site board: driver lines become factor rows generated from the registry, with their Findings on their factors", "SCR", (3, 5), ["3B2", "3B3"], "P3B", ""),
    ("3B6", "3B", "B1", "Cold-room and captive-EV structures declared and tested from the start (revenue not applicable, never zero)", "STR", (1, 2), ["3B1"], "P3B", ""),
    ("3C1", "3C", "CH2", "An authenticated user recorded on every command: trial, domain action and work case writes accept the person", "DEC", (2, 4), ["1a"], "P1", "schema new"),
    ("3C2", "3C", "CH2", "Every Action records creator, owner and due date; overdue computed as for maintenance schedules", "DEC", (2, 3), ["3C1"], "P1", "schema new"),
    ("3C3", "3C", "CH2", "UI controls for the work routes that exist only in the API: raise, assign, complete and close, under the person's name", "SCR", (3, 5), ["3C2"], "P1", "new"),
    ("4a", "4", "B1", "Energy-to-cash observer: delivered, metered, billed, collected, with named leaks", "SRC", (2, 3), ["3A4", "3B3"], None, "money"),
    ("4b", "4", "B1", "Money leaves from records: revenue, collections, O&M, staff and fuel purchases into the structure read", "SRC", (2, 3), ["3A3", "3A4", "3B3"], None, "money new"),
    ("5a", "5", "B2", "Targets and budget lines at factor level, declared by the operator with the declarer recorded; objectives become factor targets", "SRC", (2, 4), ["4b", "3C1"], "P5", "schema money new"),
    ("5b", "5", "B2", "Attribution: exact for sums, a declared rule for products, a residual only beside an unobserved leaf", "STR", (2, 4), ["5a"], "P5", "money"),
    ("5c", "5", "B2", "The bridge on screen, factor by factor, labelled Emulated until the operator's exports replace the emulators", "SCR", (2, 4), ["5b", "3A5", "3B5"], "P5", "money"),
    ("5d", "5", "CH5", "Relabel the Assure line to Actual against target (OD-6)", "SCR", (1, 1), ["5a"], "P5", ""),
    ("6a", "6", "CH3", "Decision, option and evaluation records on a factor, with the Finding that opened it and the person who chose", "DEC", (2, 4), ["3B3", "3C2"], "P6", "schema"),
    ("6b", "6", "CH3", "Bounds as rows: hard, costed, advisory; guardrails generated from them", "DEC", (2, 3), ["6a"], "P6", "schema"),
    ("6c", "6", "CH3", "Evaluator: options valued against no action, net of their one-off, through the replay port", "DEC", (2, 4), ["6a", "0K"], "P6", "money"),
    ("6d", "6", "CH3", "Stop-threshold carrier as a domain-action apply path, linked to its decision option", "DEC", (2, 3), ["6a"], "P6", "schema"),
    ("6e", "6", "CH4", "Stop-setting verification family (an unknown rule fails closed today)", "DEC", (2, 3), ["6d"], "P6", "schema"),
    ("6f", "6", "CH3", "Decision view from What can be done: options with no action, values, the rejected one's reason; the choice recorded", "SCR", (3, 5), ["6b", "6c", "6d"], "P6", ""),
    ("6g", "6", "CH3", "Mto demand and repair decisions (revenue side, after the join), with the quotes emulator", "SRC", (3, 5), ["6c", "4a", "0M"], "P6", "money"),
    ("7a", "7", "P", "Plan records (portfolio_plan): items, versions, settings; one origin and at most one membership, the origin checks widened in one migration", "STR", (4, 6), ["6a", "3C2"], "P7", "schema"),
    ("7b", "7", "P", "Release: spend and crew-visit thresholds as Site or portfolio settings (OD-2, OD-12); the fit checked at each creation; changes counted since the last version", "STR", (3, 5), ["7a"], "P7", "money new"),
    ("7c", "7", "P", "Proposal: the nearest set that fits budget, crew visits and dates, every exclusion with its reason", "STR", (3, 5), ["7b", "6c"], "P7", "money"),
    ("7d", "7", "P", "Spend steps on the item: planned spend, released spend, and incurred spend from linked expense records, counted once", "SRC", (2, 3), ["7a", "3A4"], "P7", "money new"),
    ("7e", "7", "CH5", "Act first: the Finding triage first, the version awaiting approval beside it; approve or send back with a trade-off", "SCR", (4, 6), ["7b", "7c"], "P7", ""),
    ("7f", "7", "P", "Switches beside the proposal (budget; the letter of intent), recomputed visibly", "SCR", (1, 2), ["7e"], "P7", ""),
    ("7g", "7", "CH5", "Portfolio cards read from their factors against target, with their evidence class", "SCR", (2, 3), ["5c"], "P7", ""),
    ("7h", "7", "P", "Period close: the plan review, predicted against observed factors; unfinished items carried into the next draft (OD-10)", "STR", (2, 3), ["7c", "7d", "5b"], "P7", "new"),
    ("8a", "8", "CH4", "Economic and causal verdicts beside the operational one", "DEC", (3, 5), ["6e"], "P8", "schema money"),
    ("8b", "8", "CH4", "Field evidence admitted with its label; the option's cost replaces 0", "DEC", (1, 3), ["8a"], "P8", "money"),
    ("8c", "8", "CH4", "Three verdicts on What changed, with Actions' owners and the plan review", "SCR", (2, 3), ["8b", "7h"], "P8", ""),
    ("9a", "9", "B3", "Rights rows from contract documents, AI-assisted, a person approving each row; contract-document emulator", "SRC", (3, 5), ["3A3", "6a"], "P9", "schema"),
    ("9b", "9", "B3", "Supplier-claim case and its states", "SRC", (2, 4), ["9a"], "P9", "schema"),
    ("9c", "9", "CH3", "Remedy paths inside decisions, with notice deadlines", "SRC", (3, 4), ["9b", "6c"], "P9", "money"),
    ("9d", "9", "B1", "Cold-room records and observers on emulated data; cold verification", "STR", (5, 8), ["3A3", "3B6", "8a"], "P9", "schema"),
    ("9e", "9", "B1", "EV depot records and observers on emulated data; EV verification", "STR", (6, 9), ["9d"], "P9", "schema"),
    ("WK", "W", "tooling", "Prepare the clean day-14 walkthrough database at main", "SCR", (1, 1), [], "DAY13", "heavy"),
]
# Structure pages (W1): one page and a figure per step, written by the Architect from the pack and approved at a sitting.
# "P1" covers steps 1 and 3C, whose structure the recreated pack already holds (#2, #12): it is approved with the pack
# itself, before day 1 (Architect's call for the owner, two-week-build-plan.md §7). Effort in Architect lane-days.
PAGES = [("P1", "Steps 1 and 3C: the corrected figure; the person on every command (pack #2, #12)", 0.0, True),
         ("P2", "Step 2: canonical format version 1 and the leaf factor IDs", 0.5, False),
         ("P3A", "Step 3A: record kinds, intake, emulator rules, the contract test", 0.25, False),
         ("P3B", "Step 3B: registry rows, parity, the structure read and observer", 0.25, False),
         ("P5", "Step 5: target declaration and the attribution rules", 0.5, False),
         ("P6", "Step 6: decision records, bounds, the evaluator and the carrier", 0.5, False),
         ("P7", "Step 7: plan records, release, versions, the proposal (pack #12)", 0.5, False),
         ("P8", "Step 8: economic and causal verdicts", 0.25, False),
         ("P9", "Step 9: rights rows and the claim case; cold and EV records", 0.75, False)]
PAGE = {p: dict(id=p, name=n, eff=e, with_pack=w) for p, n, e, w in PAGES}
KEYS = ("id", "step", "construct", "name", "lane", "rng", "deps", "gate", "flags")
IT = [dict(zip(KEYS, r)) for r in SLICES]
BY = {i["id"]: i for i in IT}
for i in IT:
    i["flags"] = set(i["flags"].split())
assert all(d in BY for i in IT for d in i["deps"]), "unknown dependency"
assert all(i["gate"] in PAGE or i["gate"] in (None, "DAY13") for i in IT), "unknown structure page"
BUILD_LANES = ("SRC", "STR", "DEC", "SCR")
LANE_NAME = {"SRC": "Lane 1 · sources and money", "STR": "Lane 2 · structure and the plan's records",
             "DEC": "Lane 3 · person, decisions and proof", "SCR": "Lane 4 · screens and tooling", "ANY": "any lane's gaps"}
MUST_KEEP = {"T1", "1a", "1b", "2a", "3A1", "3A2", "3A3", "3A4", "3B1", "3B2", "3B3", "3C1", "3C2", "WK"}   # land by day 12 (WK by 14)


def units(i):
    lo, hi = i["rng"]
    return max(1.0, round((lo + hi) / 2 * 2) / 2)


def rank(i):
    return STEP_ORDER.index(i["step"])


def dependents(x, seen=None):
    out = set()
    for j in IT:
        if x in j["deps"]:
            out.add(j["id"]); out |= dependents(j["id"])
    return out


def chain(x, memo={}):
    """Units on the longest path from x to the end (x included): a slice that unlocks more waits less."""
    if x not in memo:
        memo[x] = units(BY[x]) + max([chain(j["id"]) for j in IT if x in j["deps"]] + [0])
    return memo[x]


# The fortnight's aim (owner): advance as far as possible along Figure 10. Priority is delivery order first, then the
# work a slice unlocks; the heavy-tool pool is first of all (W4 as amended), since lanes 3 and 4 open only once it merges.
def prio(i):
    if i["id"] == "WK":                 # the owner's rule: the walkthrough runs only on a clean, good database; first once released
        return (1, 0)
    return (-rank(i), chain(i["id"]))


def review_minutes_per_unit():
    bs = [i for i in IT]
    disc = sum(units(i) for i in bs if i["flags"] & {"schema", "money"}) / sum(units(i) for i in bs)
    return disc * REVIEW_MIN["discovery"] + (1 - disc) * REVIEW_MIN["standard"] + REREVIEW_SHARE * REREVIEW_MIN, disc


REV_MIN, DISC_SHARE = review_minutes_per_unit()
REVIEW_CAP = REVIEWERS * REVIEW_HOURS_A_DAY * 60 / REV_MIN    # units a day one review slot carries


# ================================================================ 3. structure pages and sittings (W1)
def page_schedule():
    """The Architect writes the pages one after another, in delivery order, from the start of day 1."""
    t, out = 0.0, {}
    for p in PAGES:
        if PAGE[p[0]]["with_pack"]:
            out[p[0]] = (0.0, 0.0)
            continue
        out[p[0]] = (t, t + PAGE[p[0]]["eff"]); t += PAGE[p[0]]["eff"]
    return out


PAGE_T = page_schedule()


def approval_day(p, sittings):
    """Approved with the pack (day 0), or at the first sitting on a day after it is finished (the owner reads it the day before)."""
    if PAGE[p]["with_pack"]:
        return 0
    f = PAGE_T[p][1]
    ks = [k for k in sorted(sittings) if f <= k - 1 + 1e-9]
    return ks[0] if ks else None


# ================================================================ 4. the schedule (list scheduling)
def run(pace, sittings, n_build=4, rework=None):
    rework = REWORK if rework is None else rework
    lanes = list(BUILD_LANES[:n_build])
    remap = {"DEC": "SRC", "SCR": "STR"} if n_build == 2 else {}
    eff = min(pace, REVIEW_CAP / n_build)
    rel = {}
    for i in IT:
        g = i["gate"]
        if g is None: r = 0.0
        elif g == "DAY13": r = 12.0
        else:
            k = approval_day(g, sittings); r = float(k) if k is not None else 99.0
        rel[i["id"]] = r
    start, fin, where = {}, {}, {}
    lane_of = lambda i: remap.get(i["lane"], i["lane"])  # noqa: E731
    dur = lambda i: units(i) * (1 + rework) / eff         # noqa: E731
    free = {l: 0.0 for l in lanes}
    pend = list(IT)
    pool_gate = n_build > N_UNPOOLED

    def avail(i):
        if any(d not in fin for d in i["deps"]): return None
        a = max([rel[i["id"]]] + [fin[d] for d in i["deps"]])
        if pool_gate and lane_of(i) in ("DEC", "SCR") and i["id"] != "T1":
            a = max(a, fin.get("T1", 99.0))
        return a
    guard = 0
    while pend and guard < 5000:
        guard += 1
        l = min(lanes, key=lambda l: (free[l], l)); t = free[l]
        if t > 40: break
        own = [i for i in pend if lane_of(i) == l or i["id"] == "WK"]     # the walkthrough database goes to the first free lane
        rdy = [i for i in own if avail(i) is not None and avail(i) <= t + 1e-9]
        if rdy:
            i = max(rdy, key=lambda i: (prio(i), i["id"]))
        else:
            nxt = [avail(i) for i in own if avail(i) is not None]
            gap_end = min(nxt) if nxt else 99.0
            anys = [i for i in pend if i["lane"] == "ANY" and avail(i) is not None and avail(i) <= t + 1e-9
                    and (t + dur(i) <= gap_end + 1e-9 or not own)
                    and not (pool_gate and l in ("DEC", "SCR") and fin.get("T1", 99.0) > t + 1e-9)]
            if anys:
                i = max(anys, key=lambda i: (prio(i), i["id"]))
            else:
                # idle: wait for the next event (a slice finishing, another lane freeing, a structure page's approval)
                later = [f for f in fin.values() if f > t + 1e-9] + [free[x] for x in lanes if free[x] > t + 1e-9]
                later += [v for v in rel.values() if t + 1e-9 < v < 99] + ([gap_end] if gap_end < 99 else [])
                free[l] = min(later) if later else 99.0
                continue
        d = dur(i)
        start[i["id"]], fin[i["id"]], where[i["id"]] = t, t + d, l
        free[l] = t + d; pend.remove(i)
    return {"start": start, "fin": fin, "where": where, "eff": eff, "rel": rel, "pace": pace, "sittings": sittings, "n": n_build}


def day(t, end=False):
    if end:
        return max(1, int(-(-round(t, 6) // 1)))
    return int(t // 1) + 1


def landed(r, by=14):
    return {x for x, f in r["fin"].items() if f <= by + 1e-9}


def landed_units(r, by=14):
    return sum(units(BY[x]) for x in landed(r, by))


def step_done(r, s, by=14):
    xs = [i["id"] for i in IT if i["step"] == s]
    return all(x in r["fin"] and r["fin"][x] <= by + 1e-9 for x in xs)


def step_day(r, s):
    xs = [i["id"] for i in IT if i["step"] == s]
    if all(x in r["fin"] for x in xs):
        return day(max(r["fin"][x] for x in xs), True)
    return None


def furthest(r, by=14):
    """The furthest Figure 10 step whose slices, and every earlier step's, have all landed."""
    last = None
    for s in PATH:                    # calibration, tooling and the walkthrough database are not on the path
        if step_done(r, s, by): last = s
        else: break
    return last


def best_sittings():
    """Search the sitting days: two or three sittings after the pack's own approval. The most units landed by day 14 wins,
    then the furthest step, then fewer sittings (the owner's time), then earlier days."""
    best = None
    combos = [(a, b) for a in range(2, 6) for b in range(a + 2, 13)] + \
             [(a, b, c) for a in range(2, 6) for b in range(a + 2, 11) for c in range(b + 2, 13)]
    for c in combos:
        r = run(PACES["plan"], c)
        f = furthest(r)
        k = (landed_units(r), STEP_ORDER.index(f) if f else -1, -len(c), tuple(-x for x in c))
        if best is None or k > best[0]:
            best = (k, c, r)
    return best[1], best[2]


SIT, PLAN = best_sittings()
SLIP = run(PACES["slip"], SIT)
OBS = run(PACES["observed"], SIT)
TWO = run(PACES["plan"], SIT, n_build=N_UNPOOLED)
NO_REWORK = run(PACES["plan"], SIT, rework=0.0)
LAND, LAND_SLIP, LAND_OBS = landed(PLAN), landed(SLIP), landed(OBS)
COMMITTED = landed(PLAN, COMMIT_BY)
STRETCH = sorted(LAND_OBS - LAND, key=lambda x: (rank(BY[x]), x))
DROP_ORDER = sorted([x for x in LAND if x not in MUST_KEEP and x not in LAND_SLIP],
                    key=lambda x: (-rank(BY[x]), -PLAN["fin"][x], x))


def status(x):
    if x in COMMITTED: return "committed"
    if x in LAND: return "lands, no reserve"
    if x in LAND_OBS: return "stretch"
    if x in PLAN["start"] and PLAN["start"][x] < 14: return "in progress"
    return "next fortnight"


# ================================================================ 5. owner time in the fortnight (TW11: 240 minutes a day)
OWNER_DAY_CAP = 240


def owner_load(r):
    load = {d: 0 for d in range(1, 15)}
    notes = {d: [] for d in range(1, 15)}
    for n, k in enumerate(r["sittings"], 1):
        pages = [p for p in PAGE if approval_day(p, r["sittings"]) == k and not PAGE[p]["with_pack"]]
        load[k - 1 if k > 1 else k] += 20 * len(pages); notes[k - 1 if k > 1 else k].append(f"reads {len(pages)} pages for sitting {n}")
        load[k] += 30 + 15 * len(pages); notes[k].append(f"sitting {n}")
    load[13] += 30; notes[13].append("reads the day-14 pack")
    load[14] += 120; notes[14].append("walkthrough of the built screens and the next ranked list")
    return load, notes


OWN_LOAD, OWN_NOTES = owner_load(PLAN)


# ================================================================ 6. owner-time model for commercial-plan.md (#9), carried over
# unchanged from the go-to-market model (commercial plan rev 4 §4.1, §6.1; TW11, TW25, TW26 open). Lane C owns its wording.
ENGAGE = {"low": dict(align=1.0, dd=4.5, pack=1.5, to_bd=2.5, chk=0.5), "mid": dict(align=1.5, dd=7.0, pack=2.25, to_bd=4.0, chk=0.75),
          "high": dict(align=2.0, dd=9.5, pack=3.0, to_bd=5.5, chk=1.0)}
DD_FLOOR, PACK_FLOOR, BD_FLOOR = {"low": 2.0, "mid": 2.5, "high": 3.0}, 1.0, 1.0
WORK_DAYS_MONTH, BASE_MIN, PEAK_MIN, PEAK_DAYS_MONTH, OWNER_DAY_MIN = 18, 240, 480, 8, 480
PRODUCT_RESERVE, CALL_FLOOR, CALL_MIN, WEEKS_MONTH = 2, 4, 180, 4.33
DEEP_DIVE_START = (4, 8)
RESERVE_ALT = 4
PROOF_WEEKS = 2 * WEEKS_MONTH


def delivery_cap(peak_days, reserve=None):
    reserve = PRODUCT_RESERVE if reserve is None else reserve
    return ((WORK_DAYS_MONTH - peak_days) * BASE_MIN + peak_days * PEAK_MIN) / OWNER_DAY_MIN - reserve - CALL_FLOOR * CALL_MIN / OWNER_DAY_MIN


DELIVERY_CAP, DELIVERY_CAP_BASE = delivery_cap(PEAK_DAYS_MONTH), delivery_cap(0)


def engage(cap):
    out = {}
    for c, e in ENGAGE.items():
        w = lambda d, floor: max(round(d / cap * WEEKS_MONTH, 1), floor)  # noqa: E731
        bd, dd, pk = w(e["to_bd"], BD_FLOOR), w(e["dd"], DD_FLOOR[c]), w(e["pack"], PACK_FLOOR)
        tot = round(dd + pk, 1)
        out[c] = dict(own=e["align"] + e["dd"] + e["pack"], chk=e["chk"], bd=bd, dd=dd, pack=pk, tot=tot,
                      commit=(int(DEEP_DIVE_START[0] + tot + 0.5), int(DEEP_DIVE_START[1] + tot + 0.5)))
    return out


ENG1, ENG1_BASE = engage(DELIVERY_CAP), engage(DELIVERY_CAP_BASE)
span = lambda E: (min(v["commit"][0] for v in E.values()), max(v["commit"][1] for v in E.values()))  # noqa: E731
OWNER_CASES = [("planning case (the defaults)", PEAK_DAYS_MONTH, PRODUCT_RESERVE), ("no peak days", 0, PRODUCT_RESERVE),
               (f"{RESERVE_ALT}-day product reserve", PEAK_DAYS_MONTH, RESERVE_ALT), (f"no peak days and a {RESERVE_ALT}-day reserve", 0, RESERVE_ALT)]


def owner_case(pk, rv):
    cap = delivery_cap(pk, rv); E = engage(cap); c0, c1 = span(E)
    proved = tuple(round(int(c + PROOF_WEEKS + 0.5) / WEEKS_MONTH) for c in (c0, c1))
    return dict(cap=cap, bd=(E["low"]["bd"], E["high"]["bd"]), tot=(E["low"]["tot"], E["high"]["tot"]), commit=(c0, c1), proved=proved)


OWN_CASES = {n: owner_case(pk, rv) for n, pk, rv in OWNER_CASES}


# ================================================================ 7. tables
def fmt(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def table_capacity():
    rows = [("Machine", "measured, 18 Nov", f"{fmt(MEM_AVAILABLE_GB)} GB available of 22 GB with the walkthrough server, lab_app, Postgres and the coordinator running; no swap"),
            ("Memory budget for agents and tools", f"available less {fmt(MEM_HEADROOM_GB)} GB headroom (assumption)", f"{fmt(BUDGET_GB)} GB"),
            ("One heavy database job", "assumption, not measured; measured on the first live build before lanes 3 and 4 open", f"{fmt(DB_JOB_GB)} GB (pessimistic case {fmt(DB_JOB_GB_HIGH)} GB)"),
            (f"Worst case, {N_POOLED} build lanes, heavy tools pooled", f"every agent resident; the two heavy slots full", f"{fmt(peak_gb(N_POOLED, True))} GB: margin {fmt(MARGIN)} GB to the budget ({fmt(MARGIN_HIGH)} GB in the pessimistic case)"),
            (f"Worst case, {N_UNPOOLED + 1} build lanes, not pooled", "check-all's two slots full, the database job beside them, every other agent running tsc", f"{fmt(peak_gb(N_UNPOOLED + 1, False))} GB: does not fit"),
            ("**Build lanes**", "the largest count that fits, capped by W4 as amended", f"**{N_POOLED}** with the slot pool (lanes 3 and 4 open when it merges); {N_UNPOOLED} without"),
            ("Observed pace", f"{OBS_MERGES} task merges in {fmt(OBS_SPAN_DAYS)} days, {fmt(OBS_OPEN)} branches open on average", f"{fmt(OBS_PACE)} units per lane-day"),
            ("Planning pace", "about 0.6 of observed: new schema and money, discovery reviews, checks first, four lanes merging", f"{fmt(PACES['plan'])} units per lane-day (slip case {fmt(PACES['slip'])})"),
            ("Rework allowance", "explicit, on top of the pace", f"every unit takes {fmt(1 + REWORK)} units of lane time"),
            ("Reviewer stream", f"one fresh-review slot, {REVIEW_HOURS_A_DAY} h a day; {round(DISC_SHARE * 100)} in 100 units need a discovery review", f"{fmt(round(REVIEW_CAP, 1))} units a day; {round(PACES['plan'] * N_POOLED / REVIEW_CAP * 100)} in 100 busy at the planning pace"),
            ("Build capacity in 14 days", f"{N_POOLED} lanes at the planning pace, less rework", f"about {round(N_POOLED * 14 * PLAN['eff'] / (1 + REWORK))} units")]
    out = ["| Resource | Basis | Figure |", "|---|---|---|"]
    out += [f"| {a} | {b} | {c} |" for a, b, c in rows]
    return "\n".join(out)


def table_slices():
    out = ["| Slice | Step | Construct | What it builds | Lane | Units | Depends on | Structure page |", "|---|---|---|---|---|---:|---|---|"]
    for i in IT:
        g = i["gate"] or "none"
        out.append(f"| `{i['id']}` | {i['step']} | {i['construct']} | {i['name']} | {LANE_NAME[i['lane']].split(' · ')[0]} | {fmt(units(i))}{' (new)' if 'new' in i['flags'] else ''} | {', '.join('`' + d + '`' for d in i['deps']) or 'none'} | {g} |")
    tot = sum(units(i) for i in IT)
    out.append(f"| **All** | | | | | **{fmt(tot)}** | | |")
    return "\n".join(out)


def table_steps():
    out = ["| Step | Slices | Units | Done by day (planning pace) | Done by day 14 at slip · planning · observed pace |", "|---|---:|---:|---|---|"]
    for s in STEP_ORDER:
        xs = [i for i in IT if i["step"] == s]
        u = sum(units(i) for i in xs)
        d = step_day(PLAN, s)
        marks = " · ".join("yes" if step_done(r, s) else f"{round(sum(units(BY[x['id']]) for x in xs if x['id'] in landed(r)) / u * 100)} in 100 units" for r in (SLIP, PLAN, OBS))
        out.append(f"| {STEP_NAME[s]} | {len(xs)} | {fmt(u)} | {('day ' + str(d)) if d and d <= 14 else 'after day 14'} | {marks} |")
    return "\n".join(out)


def table_pages():
    out = ["| Page | Covers | Architect lane-days | Approved |", "|---|---|---:|---|"]
    for p, n, e, w in PAGES:
        k = approval_day(p, SIT)
        out.append(f"| {p} | {n} | {fmt(e)} | {'with the pack, before day 1' if w else ('sitting ' + str(SIT.index(k) + 1) + ', day ' + str(k)) if k else 'after day 14'} |")
    return "\n".join(out)


def table_days():
    out = ["| Day | " + " | ".join(LANE_NAME[l] for l in BUILD_LANES) + " | Owner |", "|---|" + "---|" * len(BUILD_LANES) + "---|"]
    for d in range(1, 15):
        cells = []
        for l in BUILD_LANES:
            xs = [x for x, w in PLAN["where"].items() if w == l and PLAN["start"][x] < d - 1e-9 + 1 and PLAN["fin"][x] > d - 1 + 1e-9]
            xs = sorted(xs, key=lambda x: PLAN["start"][x])
            cells.append(", ".join(f"`{x}`" + (" ✓" if day(PLAN["fin"][x], True) == d else "") for x in xs) or "—")
        own = "; ".join(OWN_NOTES[d]) or "—"
        out.append(f"| {d} | " + " | ".join(cells) + f" | {own} |")
    return "\n".join(out)


def table_pace():
    out = ["| Case | Units landed by day 14 | Furthest step complete | Slices landed |", "|---|---:|---|---:|"]
    for n, r in (("slip pace (2 units a lane-day)", SLIP), ("**planning pace (3)**", PLAN), (f"observed pace ({fmt(OBS_PACE)})", OBS),
                 (f"planning pace, {N_UNPOOLED} lanes (no slot pool)", TWO), ("planning pace, no rework allowance", NO_REWORK)):
        f = furthest(r)
        out.append(f"| {n} | {fmt(landed_units(r))} | {STEP_NAME[f] if f else 'none'} | {len(landed(r))} of {len(IT)} |")
    return "\n".join(out)


def table_stretch():
    out = ["| Slice | Step | Lands at the observed pace on day |", "|---|---|---:|"]
    out += [f"| `{x}` {BY[x]['name'].split(':')[0]} | {BY[x]['step']} | {day(OBS['fin'][x], True)} |" for x in STRETCH]
    return "\n".join(out)


def table_drop():
    out = ["| Order | Slice | Step | Lands at the planning pace on day |", "|---:|---|---|---:|"]
    out += [f"| {k} | `{x}` {BY[x]['name'].split(':')[0]} | {BY[x]['step']} | {day(PLAN['fin'][x], True)} |" for k, x in enumerate(DROP_ORDER, 1)]
    return "\n".join(out)


def table_gantt():
    out = ["```mermaid", "gantt", "  title The fortnight at the planning pace (days from day 1)", "  dateFormat X", "  axisFormat %s"]
    for l in BUILD_LANES:
        out.append(f"  section {LANE_NAME[l].split(' · ')[1].capitalize()}")
        for x in sorted([x for x, w in PLAN["where"].items() if w == l and PLAN["start"][x] < 14], key=lambda x: PLAN["start"][x]):
            s, f = PLAN["start"][x], min(PLAN["fin"][x], 14.0)
            out.append(f"  {x} {BY[x]['construct']} :{'crit, ' if x in COMMITTED else ''}g{x}, {round(s, 2)}, {round(f, 2)}")
    out.append("  section Owner")
    for n, k in enumerate(SIT, 1):
        out.append(f"  Sitting {n} :milestone, s{n}, {k - 1}, {k - 1}")
    out.append("  Walkthrough :milestone, s9, 13.5, 13.5")
    out.append("```")
    return "\n".join(out)


def table_owner():
    out = ["| Day | Owner minutes | What |", "|---:|---:|---|"]
    out += [f"| {d} | {OWN_LOAD[d]} | {'; '.join(OWN_NOTES[d])} |" for d in range(1, 15) if OWN_LOAD[d]]
    out.append(f"| **14 days** | **{sum(OWN_LOAD.values())}** | busiest day {max(OWN_LOAD.values())} minutes, within the {OWNER_DAY_CAP}-minute day |")
    return "\n".join(out)


def table_ownertime():
    out = ["| Case | Peak days a month (TW25) | Product reserve, owner-days a month (TW26) | Delivery limit (owner-days a month) | First breakdown (weeks into the deep-dive) | Deep-dive and pack (weeks) | Commitment (weeks from approval) | First proved change |",
           "|---|---:|---:|---:|---:|---:|---|---|"]
    for n, pk, rv in OWNER_CASES:
        c = OWN_CASES[n]
        out.append(f"| {n} | {pk} | {rv} | {fmt(c['cap'])} | {fmt(c['bd'][0])}–{fmt(c['bd'][1])} | {fmt(c['tot'][0])}–{fmt(c['tot'][1])} | weeks {c['commit'][0]}-{c['commit'][1]} | about M{c['proved'][0]}–M{c['proved'][1]} |")
    return "\n".join(out)


def table_diagnostic():
    out = [f"| Effort case (commercial plan §6.1) | Owner-days up to the pilot | Second-person days | At {fmt(DELIVERY_CAP)} owner-days a month: first breakdown (weeks into the deep-dive) | deep-dive (weeks) | integration pack (weeks) | commitment, deep-dive starting weeks {DEEP_DIVE_START[0]}-{DEEP_DIVE_START[1]} | At the 240-minute baseline ({fmt(DELIVERY_CAP_BASE)} a month): first breakdown | deep-dive and pack (weeks) | commitment |",
           "|---|---:|---:|---:|---:|---:|---|---:|---:|---|"]
    for c in ENGAGE:
        a, z = ENG1[c], ENG1_BASE[c]
        out.append(f"| {c} | {fmt(a['own'])} | {fmt(a['chk'])} | {fmt(a['bd'])} | {fmt(a['dd'])} | {fmt(a['pack'])} | weeks {a['commit'][0]}-{a['commit'][1]} | {fmt(z['bd'])} | {fmt(z['tot'])} | weeks {z['commit'][0]}-{z['commit'][1]} |")
    return "\n".join(out)


TABLES = {"capacity": table_capacity, "slices": table_slices, "steps": table_steps, "pages": table_pages, "days": table_days,
          "pace": table_pace, "stretch": table_stretch, "drop": table_drop, "gantt": table_gantt, "owner": table_owner,
          "ownertime": table_ownertime, "diagnostic": table_diagnostic}


def prose_facts():
    f = furthest(PLAN)
    return [f"**{N_POOLED} build lanes**", f"{fmt(PACES['plan'])} units per lane-day", f"{fmt(OBS_PACE)} units per lane-day",
            "sittings on days " + ", ".join(map(str, SIT[:-1])) + " and " + str(SIT[-1]),
            f"{fmt(landed_units(PLAN))} units", f"{len(LAND)} slices", f"{len(COMMITTED)} slices committed",
            f"through step {f}" if f else "no step complete",
            f"{sum(OWN_LOAD.values())} owner minutes",
            f"the furthest complete step moves from step {furthest(PLAN)} to step {furthest(NO_REWORK)}",
            f"the stretch line reaches step {furthest(OBS)}", f"At the slip pace the fortnight still completes step {furthest(SLIP)}"]


# Which documents carry which tables and facts. A table block present anywhere must match; these must be present.
DOCS = {"two-week-build-plan.md": dict(tables={"capacity", "steps", "pages", "days", "pace", "stretch", "drop", "gantt", "owner"}, facts=True),
        "delivery-plan.md": dict(tables={"slices"}, facts=False)}
# The commercial plan's tables are owned by ../../go-to-market/render_commercial_plan_html.py (it computes and checks them
# from the input tables inside that document); plan_model does not generate them, so it does not compare them.


def blocks(text):
    """{name: body} for every <!--table:NAME-->\\n...\\n<!--/table--> block."""
    out, k, L = {}, 0, text.split("\n")
    while k < len(L):
        s = L[k].strip()
        if s.startswith("<!--table:") and s.endswith("-->"):
            name, body, k = s[len("<!--table:"):-3], [], k + 1
            while k < len(L) and L[k].strip() != "<!--/table-->":
                body.append(L[k]); k += 1
            out[name] = "\n".join(body)
        k += 1
    return out


def check(path):
    p = pathlib.Path(path)
    text = p.read_text(encoding="utf-8")
    found = blocks(text)
    want = DOCS.get(p.name, DOCS.get(str(p.relative_to(ROOT)) if p.is_absolute() and ROOT in p.parents else p.name, dict(tables=set(), facts=False)))
    for k, v in DOCS.items():
        if (ROOT / k).resolve() == p.resolve():
            want = v
    bad = sorted(n for n, body in found.items() if n not in TABLES or body != TABLES[n]())
    missing = sorted(want["tables"] - set(found))
    facts = [f for f in prose_facts() if f not in text] if want["facts"] else []
    late = sorted(x for x in MUST_KEEP if x not in (LAND if x == "WK" else COMMITTED))
    if bad or missing or facts or late:
        print(f"MISMATCH {p.name}: tables differ {bad}; tables missing {missing}; prose facts missing {facts}; must-keep slices late {late}")
        return 1
    print(f"ok {p.name}: {len(found)} table blocks match the model{'; ' + str(len(prose_facts())) + ' prose facts stated' if want['facts'] else ''}; "
          f"every must-keep slice lands by day {COMMIT_BY}")
    return 0


def fill(path):
    p = pathlib.Path(path)
    L, out, k = p.read_text(encoding="utf-8").split("\n"), [], 0
    while k < len(L):
        out.append(L[k]); s = L[k].strip(); k += 1
        if s.startswith("<!--table:") and s.endswith("-->"):
            name = s[len("<!--table:"):-3]
            while k < len(L) and L[k].strip() != "<!--/table-->":
                k += 1
            out.extend(TABLES[name]().split("\n"))
    p.write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--check"]:
        paths = a[1:] or [str(ROOT / k) for k in DOCS if (ROOT / k).is_file()]
        sys.exit(max([check(x) for x in paths] or [0]))
    if a[:1] == ["--fill"] and len(a) == 2:
        fill(a[1]); sys.exit(check(a[1]))
    for n, fn in TABLES.items():
        print(f"<!-- {n} -->"); print(fn()); print()
    print("sittings:", SIT, "eff:", round(PLAN["eff"], 2), "furthest:", furthest(PLAN), furthest(SLIP), furthest(OBS))
    print("prose facts:", prose_facts())
    print("must-keep late:", sorted(x for x in MUST_KEEP if x not in (LAND if x == "WK" else COMMITTED)))
