"""Render website-content.md to its HTML twin, after the copy lint and the stage gates pass (plan F #10, rev 2).

Usage: python3 render_website_content_html.py website-content.md website-content.html
       python3 render_website_content_html.py --lint-only FILE   -> run only the copy lint on FILE's copy blocks
       python3 render_website_content_html.py --fixtures         -> run only the planted-violation self-test

Recreated with the document on 19 Nov 2026 (plan F: kept, adapted, "the lint adds the A3 terms"). The copy lint of the
18 Nov brief is carried over and extended with the design's retired terms, imported from check_alignment.py so the two
never drift: "factor key", a Finding as "conditions on", the M1-M5 mechanic names, the system or product as chooser or
approver (C2 class), and "plan" used for a target (the OD-6 naming lint). Also new: a coming construct claimed as available
now, and a legal or insurance conclusion (design Rules, 6).

Checks, run before writing (the build fails on any violation, SystemExit):
- copy lint: every quoted block (lines starting ">") in §2 and §3 is website copy, checked by lint_block();
- stage gates (§4.2): while a trigger's state is "not met", its gated phrase may not appear in any copy block, and
  "available to see in a walkthrough" may not appear until one of the step triggers is met; each trigger's prepared copy
  must carry its gated phrase, pass the lint and hold no figure;
- computed gates T13 and T14: read from the commercial plan's durations table (every owner-time case within the owner's
  C14 and C15 decisions of 19 Nov; rows named "sensitivity ..." are left out);
- planted violations: every line of website-copy-lint-fixtures.txt must FAIL, or the build fails;
- the five stage names equal the commercial plan's;
- rendering is deterministic."""
import json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
L4 = HERE.parent / "demo-sprint/product-direction-layer4"
sys.path.insert(0, str(L4))
sys.path.insert(0, str(HERE))
import check_alignment as CA                     # noqa: E402  the design's retired terms and naming lint (A3)
import render_commercial_plan_html as RC        # noqa: E402  stage names, the durations table, the page renderer

DV = json.loads((L4 / "derived-values.json").read_text(encoding="utf-8"))


def fail(msg):
    raise SystemExit(f"CHECK FAILED: {msg}")


# ---------------------------------------------------------------- copy lint
ALLOWED = ["We do not promise savings", "before anyone calls it a saving", "may have nothing to save", "Coverage is decided by the supplier or insurer"]
FIG = r"(\d[\d,]*(\.\d+)?\s?%|[$€£]\s?\d|\b(US\$|USD|KES|NGN)\b|\b\d[\d,.]*\s?(k|K|m|M|thousand|million)\b|\b\d[\d,.]*\s+(a|per)\s+(month|year|day))"
BANNED = [
    # H1 savings, in any phrasing
    r"\bsav(e|es|ed|ing|ings)\b", r"\bguarantee", r"\bup to\b[^.]{0,30}\d",
    r"\b(cut|cuts|reduc\w*|lower\w*|drop\w*|slash\w*|trim\w*|decreas\w*|improv\w*|increas\w*|boost\w*|rais\w*|grow\w*)\b[^.]{0,60}?" + FIG,
    r"\d[\d,]*(\.\d+)?\s?%\s+(less|lower|cheaper|off|fewer)\b", r"\bROI\b", r"\bpayback\b",
    # H5 proof and customer claims
    r"\bproven (across|in|at|by|with|results|savings|track)", r"\btrack record", r"\bverified\b",
    r"\b(trusted|relied|rely|relies) (by|on)\b", r"\b(used|chosen|backed|adopted) by\b", r"\bleading (operators|companies|developers|providers)\b",
    r"\bour (customers|clients)", r"\b(clients|customers) include", r"\bcase stud", r"\btestimonial",
    r"\b\d[\d,]*\+?\s+(sites|operators|customers|clients|companies|depots|installations|deployments|mini-grids|networks)\b",
    # H4 competitors and products
    r"\b(?!(?:Your|Our|The|This|That|A|An|Each|Every|AssetEcon)\b)[A-Z][\w-]+(?:'s)?\s+(dashboards?|platforms?|portals?|software|systems?)\b",
    r"\b(PowerGen|Odyssey|SparkMeter|Steamaco|Victron|Huawei|FusionSolar|Schneider|Bboxx|Engie|Husk|ChargePoint|BasiGo|ColdHubs|Roam|Ampersand)\b",
    # H9 superlatives and internal words
    r"\bthe only\b", r"\bunlike\b", r"\bbest[- ]in[- ]class", r"\bworld[- ]class", r"\bindustry[- ]leading", r"\bnext[- ]generation",
    r"\bAI[- ]powered", r"\bsmart\b", r"\brevolution", r"\bcutting[- ]edge",
    r"\bFinding", r"\bevaluator", r"\bLayer 4", r"\bfactor bridge", r"\blane\b", r"\bslice\b", r"\bspike\b", r"\bAssetOps\b", r"\bmock-?up",
    r"\bleaf\b", r"\bleaves\b", r"\bdisposition", r"\bcanonical\b", r"\bregistry\b", r"\bstructure observer", r"\bplan item",
    # H8 qualifiers
    r"(?<!possibly )\bavoidable\b",
    # D1 revised (18 Nov): the paid diagnostic is retired
    r"\bdiagnos",
    # the pilot fee's credit (C2) and the deep-dive's terms (C12), decided 19 Nov, are disclosed after the client
    # conversation like the price (D2), so they never appear on the site (website-content.md WC5)
    r"\bcredit(?:ed|s)?\b", r"\b(?:free|no[- ]fee|no charge|at no cost|without charge)\b[^.]{0,60}\bdeep-dive",
    r"\bdeep-dive\b[^.]{0,60}\b(?:is free|for free|free of charge|at no charge|no fee|at no cost|without charge)\b",
    # design rev 16.7, A3 class C2 in public words: the system proposes, people decide
    r"\b(?:decides|chooses|approves|acts)\s+for\s+you\b", r"\bautomatic(?:ally)?\s+(?:fix|act|approv|decid|chang)\w*",
    r"\b(?:we|it|AssetEcon)\s+(?:will\s+)?(?:make|take)s?\s+(?:the\s+)?decisions?\b",
    # design Rules 6: no legal or insurance conclusion
    r"\bliab(?:le|ility)\b", r"\b(?:is|are|will be)\s+covered\b", r"\bwarranty\s+covers\b", r"\binsurer\s+(?:will|must)\s+pay\b",
]
CASED = {r"\bFinding"}
NOW_WORDS = re.compile(r"\b(?:available now|now available|running today|today|live now|in the product now)\b", re.I)
COMING_WORDS = re.compile(r"\b(?:against (?:your )?target|valued against doing nothing|net of (?:its|their) cost|one plan|approved by your executive|"
                          r"did the money follow|money followed|contract rights|contribution|collections|cost to serve|who approved)\b", re.I)
LABEL = re.compile(r"illustration on demo data|\bdemo data\b|\bdemonstration data\b", re.I)
NUMERIC = re.compile(r"[$€£]\s?\d|\bUSD\b|\bKES\b|\bNGN\b|\d+(\.\d+)?\s?%|\b\d{1,3}(,\d{3})+(\.\d+)?\b|\b\d{4,}\b|\b\d[\d.]*\s?(k|K|m|M|thousand|million)\b")


def design_values():
    """H3: figures that rest on a replay not yet run (options with design values) and the plans that include one."""
    vals, opts = set(), set()
    for k, o in DV["options"].items():
        if o.get("design_values"):
            opts.add(k)
            for f in ("value", "monthly_or_horizon_change"):
                if o.get(f):
                    vals.add(abs(float(o[f])))
    for pl in DV["plans"].values():
        d = pl.get("default", {})
        if set(d.get("valued_options", [])) & opts and d.get("value"):
            vals.add(abs(float(d["value"])))
    return sorted(v for v in vals if v >= 100)


DESIGN = design_values()
NUM = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(k|K|m|M|thousand|million)?\b")


def numbers(t):
    for m in NUM.finditer(t):
        v = float(m.group(1).replace(",", ""))
        u = (m.group(2) or "").lower()
        yield v * (1000 if u in ("k", "thousand") else 1e6 if u in ("m", "million") else 1)


# Durations the commercial plan supports. The first two are gated by T14 and T13 (computed below); any other duration in
# copy is a new delivery promise and fails.
APPROVED_DURATIONS = ["within a few weeks of receiving your files", "about three to ten weeks from the deep-dive's start to the pilot",
                      "one to four months of records", "a pilot of about three months"]
NUMW = r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirty|sixty|ninety|a few|several)"
DURATION = re.compile(r"\b" + NUMW + r"(\s*(-|–|to|or)\s*" + NUMW + r")?[\s-]+(business\s+|working\s+)?(days?|weeks?|months?|quarters?)\b", re.I)
KA = DV["sites"]["lakeside-power/Kobo"]["actual"]["nodes"]
KP = DV["sites"]["lakeside-power/Kobo"]["plan"]["nodes"]
COMMERCIAL_FIGS = [f"{KA['contribution']:,.0f}", f"{KP['contribution']:,.0f}", f"{KP['contribution'] - KA['contribution']:,.2f}"]
COMMERCIAL = re.compile(r"\b(contribution|revenue|income|billed|billing|collections?|tariff)\b[^.]{0,60}?\d|\b(?:plan|target) of\s+\d", re.I)


def lint_block(b):
    """Return the reason a copy block fails, or None."""
    t = re.sub(r"<!--.*?-->", "", b)
    for a in ALLOWED:
        t = t.replace(a, "")
    tl = t
    for a in APPROVED_DURATIONS:
        tl = re.sub(re.escape(a), "", tl, flags=re.I)
    tl = re.sub(r"\b\d+ of \d+ (days|nights|months)\b", "", tl)
    m = DURATION.search(tl)
    if m:
        return f"duration not on the approved list: {m.group(0)!r}"
    for pat in BANNED:
        if re.search(pat, t, 0 if pat in CASED or pat.startswith(r"\b(?!(?:Your") else re.I):
            return f"banned phrase /{pat[:60]}/"
    for label, rx in CA.RETIRED:                                       # design A3, imported
        if rx.search(t):
            return f"retired term (design A3): {label}"
    if CA.naming_violations(t):                                        # OD-6: "plan" only for the construct
        return "'plan' used for a target (OD-6): say 'target'"
    for sent in re.split(r"(?<=[.!?])\s+", t):
        if NOW_WORDS.search(sent) and COMING_WORDS.search(sent):
            return f"a coming construct claimed as available now: {sent[:60]!r}"
    for v in numbers(t):
        for d in DESIGN:
            if abs(v - d) <= 0.05 * d:
                return f"design value {d:g} (as {v:g})"
    if NUMERIC.search(t) and not LABEL.search(t):
        return "a figure without an exact illustration label"
    if (any(re.search(r"(?<![\d,.])" + re.escape(f) + r"(?![\d])", t) for f in COMMERCIAL_FIGS) or COMMERCIAL.search(t)) and not re.search(r"\bemulated\b", t, re.I):
        return "a figure from the demonstration world's commercial records without 'Emulated' (D14)"
    if LABEL.search(t) and re.search(r"\brecorded\b", t, re.I):
        return "a demo figure called 'recorded': no figure is stronger than its weakest part (D14)"
    return None


def t1_walkthrough(b):
    """Before the owner approves the mock-up for clients, a demo walkthrough shows only what runs today."""
    for sent in re.split(r"(?<=[.!?])\s+", b):
        if not re.search(r"\bdemo operator", sent, re.I):
            continue
        rest = re.sub(r"what the product does today|what runs today", "", sent, flags=re.I)
        if re.search(r"\b(?:the|our)\s+(?:full\s+)?(?:product|loop)\b", rest, re.I):
            return f"walkthrough wording before T1 ('{sent[:60]}'): say what the product does today"
    return None


# ---------------------------------------------------------------- stage gates (§4.2)
STEP_ROWS = {"T4", "T5", "T6", "T7", "T8", "T9", "T10", "T11"}


def gates(md):
    m = re.search(r"^### 4\.2 .*?(?=^### 4\.3 )", md, re.S | re.M)
    if not m:
        fail("cannot find §4.2")
    rows = [[c.strip() for c in r.strip().strip("|").split("|")] for r in m.group(0).split("\n") if re.match(r"^\| \**T\d", r)]
    if len(rows) < 14:
        fail(f"§4.2 has {len(rows)} trigger rows; expected the full table")
    gated, step_met = [], False
    for r in rows:
        tid, state, phrase = r[0].strip("*"), r[2].lower(), r[3].strip("*\" ")
        if not (state.startswith("not met") or state.startswith("met:")):
            fail(f"§4.2 {tid}: state must be 'not met' or 'met: <evidence>'")
        if tid in STEP_ROWS and state.startswith("met:"):
            step_met = True
        if phrase not in ("–", "-") and state.startswith("not met"):
            gated.append((tid, phrase))
    if not step_met:
        gated.append(("T4–T11", "available to see in a walkthrough"))
    return gated, rows


def computed_gates(md, rows):
    """T13 and T14 hold only over every owner-time case within the owner's C14 and C15 decisions (rows not named "sensitivity")."""
    cp = (HERE / "commercial-plan.md").read_text(encoding="utf-8")
    bl = RC.blocks(cp)
    if "durations" not in bl:
        fail("the commercial plan's durations table not found")
    cases = []
    for r in RC.rows(bl["durations"]):
        bd, tot = RC.rng(r[2]), RC.rng(r[3])
        if not r[0].strip().lower().startswith("sensitivity"):
            cases.append(dict(name=r[0], bd=bd, tot=tot))
    if not cases:
        fail("no owner-time case within the owner's decisions")
    state = {r[0].strip("*"): r[2].lower() for r in rows}
    t6 = state.get("T6", "").startswith("met:")
    lo, hi = min(c["tot"][0] for c in cases), max(c["tot"][1] for c in cases)
    bd_hi = max(c["bd"][1] for c in cases)
    want = {"T13": round(lo) >= 3 and round(hi) <= 10, "T14": bd_hi <= 6 and t6}
    for t, ok in want.items():
        if t not in state:
            fail(f"§4.2 has no {t} row")
        if state[t].startswith("met:") != ok:
            fail(f"§4.2 {t} says '{state[t]}' but the renderer computes {'met' if ok else 'not met'} "
                 f"(cases within the decisions: deep-dive and pack {lo:g}–{hi:g} weeks, first view up to {bd_hi:g}; T6 {'met' if t6 else 'not met'})")
    return want


def copy_blocks(md):
    m = re.search(r"^## 2\. .*?(?=^## 4\. )", md, re.S | re.M)
    if not m:
        fail("cannot find §2–§3")
    blocks, cur = [], []
    for ln in m.group(0).split("\n"):
        if ln.startswith(">"):
            cur.append(ln[1:].strip())
        elif cur:
            blocks.append(" ".join(cur))
            cur = []
    if cur:
        blocks.append(" ".join(cur))
    return blocks


def fixtures(rows):
    """Every planted violation must fail, with every trigger forced to 'not met', or the lint has weakened."""
    gated_all = [(r[0].strip("*"), r[3].strip("*\" ")) for r in rows if r[3].strip("*\" ") not in ("–", "-")] + [("T4–T11", "available to see in a walkthrough")]
    lines = [l.strip() for l in (HERE / "website-copy-lint-fixtures.txt").read_text(encoding="utf-8").split("\n") if l.strip() and not l.startswith("#")]
    if len(lines) < 40:
        fail("lint fixtures missing")
    for l in lines:
        why = lint_block(l) or t1_walkthrough(l)
        if not why:
            why = next((f"gated {tid}" for tid, ph in gated_all if ph.lower() in l.lower()), None)
        if why is None:
            fail(f"lint no longer catches the planted violation: {l}")
    return len(lines)


def run(md, lint_only=False):
    gated, rows = gates(md)
    t1_gated = any(tid == "T1" for tid, _ in gated)

    def check(b):
        why = lint_block(b)
        if why:
            return why
        if t1_gated:
            why = t1_walkthrough(b)
            if why:
                return why
        for tid, ph in gated:
            if ph.lower() in b.lower():
                return f"stage claim '{ph}' before its trigger {tid} is met (§4.2)"
        return None

    blocks = copy_blocks(md)
    for b in blocks:
        why = check(b)
        if why:
            fail(f"copy fails ({why}) in: {b[:120]}")
    if lint_only:
        return len(blocks), 0, 0
    if len(blocks) < 30:
        fail(f"only {len(blocks)} copy blocks found; expected the full deck")
    n_trig = 0
    for r in rows:
        tid, phrase, copy = r[0].strip("*"), r[3].strip("*\" "), r[4]
        if phrase in ("–", "-"):
            continue
        q = re.findall(r"\"([^\"]+)\"", copy)
        if not q:
            fail(f"§4.2 {tid}: no quoted copy")
        for c in q:
            if phrase.lower() not in c.lower():
                fail(f"§4.2 {tid}: prepared copy does not carry its gated phrase '{phrase}'")
            why = lint_block(c)
            if why:
                fail(f"§4.2 {tid} prepared copy fails ({why}): {c[:100]}")
            if re.search(r"\d", c):
                fail(f"§4.2 {tid} prepared copy holds a figure; money stays out of trigger copy")
            n_trig += 1
    computed_gates(md, rows)
    n_fix = fixtures(rows)
    for s in RC.STAGES:
        if s not in md:
            fail(f"stage name '{s}' missing")
    return len(blocks), n_trig, n_fix


def main(argv):
    if argv and argv[0] == "--fixtures":
        md = (HERE / "website-content.md").read_text(encoding="utf-8")
        _, rows = gates(md)
        print(f"ok: {fixtures(rows)} planted violations caught")
        return 0
    if argv and argv[0] == "--lint-only":
        md = pathlib.Path(argv[1]).read_text(encoding="utf-8")
        n, _, _ = run(md, lint_only=True)
        print(f"lint ok: {n} copy blocks")
        return 0
    src, out = pathlib.Path(argv[0]), pathlib.Path(argv[1])
    md = src.read_text(encoding="utf-8")
    n, n_trig, n_fix = run(md)
    page = RC.to_html(md, "Website Content", src.name)
    if RC.to_html(md, "Website Content", src.name) != page:
        fail("rendering is not deterministic")
    out.write_text(page, encoding="utf-8")
    print(f"ok: {n} copy blocks pass the lint; {n_trig} prepared trigger lines pass; {n_fix} planted violations caught; "
          f"T13 and T14 computed; wrote {out.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
