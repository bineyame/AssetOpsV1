#!/usr/bin/env python3
"""Alignment check: no recreated pack document may contradict the design (plan F, rules A1-A6; rev 16.7).

Design-pack tool, not product code. Python 3 standard library only. It reads the design source (the three files in
SOURCES) to build its lexicon, then checks every derived document that exists against it. It never edits a file.

  A1 Derivation markers. Every `## ` section of a derived document opens with <!--derives: §2.5; OD-1-->, and every
     cited reference resolves in the design (a heading number, a companion section, a figure, a named part, a decision
     ID, a construct ID) or is an owner record that exists (owner: .agent/owner-....md) or `plan_model`.
  A2 Lexicon. Construct, gap and decision IDs, role names, dispositions and evidence words used in a derived document
     are those the design defines. Buyer titles (CEO, CFO, ...) are allowed only in the go-to-market documents.
  A3 Retired terms. "factor key", a Finding as "conditions on", M1-M5 mechanic names, the system as chooser or approver
     (C2), and "plan" for a target (OD-6: the naming lint, also run on the design itself). C4 words are warnings.
  A4 Decisions. The register's text for each design decision equals the design's Decisions table, and lists all of
     them; any other document cites a decision by ID and never restates it as a table row.
  A5 Figures. Every money or percentage figure carries a fig/figx marker or a rec:PATH marker (a declared input) (checked to the cent by check_manifest.py,
     which adds every derived document present to its anchor scan), or sits in a plan_model table block.
  A6 Coverage. Once every builder document exists, their markers together cite every §2.x section of the design.

Run: python3 check_alignment.py [--doc PATH KIND ...]   -> sources, derived documents present, fixtures self-test
     Exit 1 on any failure. check_manifest.py calls run() so one command checks the pack.
Fixtures: alignment-fixtures/*.md (one planted violation each, or clean), alignment-fixtures/a6-*/ (sets),
          naming-lint-fixtures.txt (review G N1: the 12 planted "plan = target" sentences must fail; construct uses pass).
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]
SOURCES = ("layer4-transformation-design.md", "worked-portfolios.md", "design-appendix.md")
GTM = "../../go-to-market/"          # Docs/go-to-market on task/gtm-documents, once it merges this branch

# Derived documents (plan F §1), path relative to this folder -> kind. Checked when the file exists.
#   register: A1-A5 and the A4 register rules; builder: A1-A5 and counted for A6; derived: A1-A5; gtm: A1-A5 with buyer titles
DERIVED = {
    "decisions-register.md": "register",
    "decision-loop-specification.md": "builder",
    "integration-design.md": "builder",
    "reuse-and-gap-matrix.md": "builder",
    "delivery-plan.md": "builder",
    "plan-and-action-workflow.md": "builder",
    "vertical-factor-map.md": "builder",          # #13, the brief's levers -> registry factors (owner, 19 Nov)
    "two-week-build-plan.md": "derived",
    "product-transition-and-roadmap.md": "derived",   # rev 5 (20 Nov): the short roadmap, owner-roadmap-replace-2026-11-20
    "interactive-mockup-vNEXT/walkthroughs.md": "derived",   # #8, recreated after the mock-up lane (plan F §6 step 7)
    GTM + "commercial-plan.md": "gtm",
    GTM + "website-content.md": "gtm",
}
# Kept documents (not recreated): lexicon and retired-term rules only.
KEPT = {"structure-specification.md": "kept"}
# Recreated later (plan F lane order). Move into DERIVED in the commit that recreates them.
PENDING = ()
RULES = ("A1", "A2", "A3", "A4", "A5", "A6")


# ------------------------------------------------------------------ text helpers
def blank(txt, pattern, flags=0):
    """Replace each match by spaces of the same length, so offsets and line numbers hold."""
    return re.sub(pattern, lambda m: re.sub(r"[^\n]", " ", m.group(0)), txt, flags=flags)


def prose(txt, keep_mermaid=True):
    """Text a reader sees: no HTML comments, no code spans, no non-mermaid code blocks, no bold markers."""
    txt = blank(txt, r"<!--.*?-->", re.S)
    # fences are paired in order (rev 16.12: the old pattern could pair a mermaid block's closing fence with the next
    # block's opening one, so the prose between two diagrams was hidden from every rule)
    txt = re.sub(r"```([^\n]*)\n.*?```", lambda m: m.group(0) if (keep_mermaid and m.group(1).strip() == "mermaid")
                 else re.sub(r"[^\n]", " ", m.group(0)), txt, flags=re.S)
    txt = blank(txt, r"`[^`\n]*`")
    return txt.replace("**", "  ")


def line_of(txt, pos):
    return txt.count("\n", 0, pos) + 1


def sentence(txt, a, b):
    """The sentence (or table cell, list item, clause after ';') around txt[a:b]."""
    s = max(txt.rfind("\n", 0, a), txt.rfind("|", 0, a), txt.rfind(";", 0, a))
    lastdot = None
    for m in re.finditer(r"[.!?](?=\s)", txt[s + 1:a]):
        lastdot = m
    start = s + 1 + (lastdot.end() if lastdot else 0)
    m = re.search(r"[.!?](?=\s|$)|[\n|;]", txt[b:])
    end = b + (m.start() if m else len(txt) - b)
    return start, end


# ------------------------------------------------------------------ the naming lint (OD-6; review G, N1)
# "Plan" means only the new construct. Each use is judged in its own sentence, by the words right next to it, never
# by an allowed phrase somewhere nearby. A deny context always fails; otherwise an allow context must touch the word.
PLAN_WORD = re.compile(r"\bplan(?:s|ned|'s)?\b", re.I)
DET = r"(?:the|a|an|this|its|that|each|every|one|their|our|your|next|new|whole|any)"
QUAL = r"(?:(?:default|period's|portfolio's|month's|approved|proposed|draft|revised|whole|next|current|new|first|same|executive's|Lakeside's|\w+'s)\s+)*"
DENY_LEFT = re.compile(
    r"(?:\b(?:against|over|under|above|below|on|off|versus|vs\.?|beat|beats|missed|exceeds?|exceeded|ahead\s+of|behind|to)\s+"
    r"(?:(?:the|a|its|their|this|our|your)\s+)?(?:\w+'s\s+)?$)"
    r"|(?:\b(?:operational|operating|monthly|weekly|annual|yearly|daily|quarterly|cost|budget|diesel|energy|revenue|sales|"
    r"production|fuel|target|business|maintenance|service|site|kwh)\s+$)", re.I)
DENY_RIGHT = re.compile(
    r"^(?:'s)?\s+(?:figures?|values?|lines?|costs?|sides?|targets?|amounts?|levels?|numbers?|litres|kwh|of\s+\d|of\s+(?:litres|kwh|diesel)"
    r"|for\s+(?:diesel|fuel|litres|kwh|revenue|cost|the\s+month))\b", re.I)
RIGHT_OVERRIDE = re.compile(r"^(?:'s)?\s+(?:items?|membership|versions?)\b", re.I)
ALLOW_RIGHT = re.compile(
    r"^(?:'s)?\s+(?:own\s+)?(?:items?|membership|memberships|review|record|records|construct|check|versions?|approval|approver|owner|"
    r"states?\s+(?:are|and)|state\b|life|period|realised|predicted|spend|budget|totals?|in\s+force|"
    r"(?:is|was|stays|becomes)\s+(?:one|derived|proposed|approved|sent\s+back|revised|closed|opened|reviewed|open|in\s+force|worth|infeasible|feasible|a\b|the\b|not\b)|"
    r"(?:(?:never|always|also|then|only|still|now)\s+)?(?:propos\w*|approv\w*|releas\w*|fits|still\s+fits|leaves|drops|keeps|counts|"
    r"carries|records|holds|commits|trades|shows|covers|includes|assembl\w*|opens|closes)|"
    r"beside|and\s+its\s+limits|among\s+the\s+constructs|and\s+the\s+Portfolio|and\s+Action|as\s+(?:proposed|approved)|"
    r"with\s+(?:crews?|a\s+budget|budget))\b"
    r"|^'s\s+states\b|^-facing\b"
    r"|^-item\b|^\s+(?:changes?|screen)\b|^\s+is\s+where\b|^'s:|^\s+\(Figure\b|^,\s+(?:version\s+number|kind)\b"   # rev 16.12: construct uses the fence bug hid
    r"|^\s*:\s+(?:a|one)\s+portfolio's"
    r"|^\s*:\s+(?:proposed\s+by\s+the\s+system|portfolio\s+and\s+period|the\s+period's)"
    r"|^\s*,?\s+(?:proposed|approved|opened|owned|reviewed)\s+by\b"
    r"|^\s*,\s+a\s+(?:new|first-class)\s+construct", re.I)
ALLOW_LEFT = re.compile(
    r"(?:\b(?:approves?|approved|approving|approval\s+of|choos\w*|checks?|checked|re-?evaluat\w*|evaluat\w*|gives|shows|keeps|by|propose[sd]?|proposing|opens?|opened|joins?|joined|joining|enters?|entered|"
    r"beside|owns?|owned|fits?|left\s+out\s+of|drops?|dropped|leaves?|count(?:s|ed)?\s+in|wait(?:s|ing)?\s+for|review\s+of|"
    r"sends?\s+back|sent\s+back|revises?|revised|closes?|closed|version\s+of|items?\s+of|member\s+of|membership\s+of|"
    r"in|into|from|of|with|for|through|and|within|outside|whether)\s+" + DET + r"\s+" + QUAL + r"$)"
    r"|(?:\bP:\s+the\s+$)|(?:\bThe\s+\w+'s\s+$)", re.I)
PLANNED_OK = re.compile(r"^\*?\s*(?:changes?|spend\b|\(the\s+chosen|,\s+released\b)", re.I)          # the plan's predicted change; an item's planned spend step
RAISED_AGAINST = re.compile(r"\b(?:raised|created|opened|raise|create)\s+against\s+(?:a|the)\s+$", re.I)   # OD-1: "an action be raised against a plan"
ALONE = re.compile(r"^[\s*#>-]*(?:the\s+)?plan[\s*]*$", re.I)               # a heading or label that is just "The plan"
QUOTED = r"[\"“](?:actual\s+against\s+plan|plans?)[\"”]"      # meta mentions and the retired label as a quoted name


def naming_violations(text):
    """Return [(line, sentence)] for every use of "plan" that is not the construct."""
    txt = prose(text)
    txt = blank(txt, QUOTED, re.I)
    bad = []
    for m in PLAN_WORD.finditer(txt):
        a, b = sentence(txt, m.start(), m.end())
        left, right, word = txt[a:m.start()], txt[m.end():b], m.group(0).lower()
        if word.endswith("'s"):
            right, word = "'s" + right, word[:-2]
        if word == "planned":
            ok = bool(PLANNED_OK.match(right)) or "evaluated, planned and proved" in txt[a:b]
        elif DENY_RIGHT.match(right):
            ok = False
        elif DENY_LEFT.search(left) and not RIGHT_OVERRIDE.match(right) and not RAISED_AGAINST.search(left):
            ok = False
        elif ALONE.match(txt[a:b]) or RAISED_AGAINST.search(left):
            ok = True
        else:
            ok = bool(ALLOW_RIGHT.match(right) or ALLOW_LEFT.search(left))
        if not ok:
            bad.append((line_of(txt, m.start()), " ".join(txt[a:b].split())))
    return bad


# ------------------------------------------------------------------ lexicon from the design
def section(txt, start_pat, end_pat):
    a = re.search(start_pat, txt, re.M)
    if not a:
        return ""
    b = re.search(end_pat, txt[a.end():], re.M)
    return txt[a.end():a.end() + b.start()] if b else txt[a.end():]


def lexicon(root=ROOT):
    d = (root / SOURCES[0]).read_text(encoding="utf-8")
    wp = (root / SOURCES[1]).read_text(encoding="utf-8")
    da = (root / SOURCES[2]).read_text(encoding="utf-8")
    lx = {}
    lx["design_sections"] = set(re.findall(r"^###? (\d+\.\d+) ", d, re.M))
    lx["named"] = {"Introduction", "Words", "Rules", "Decisions", "Appendix", "Part 1", "Part 2"}
    lx["wp_sections"] = set(re.findall(r"^#{2,3} (\d+(?:\.\d+)?)\.? ", wp, re.M))
    lx["da_sections"] = set(re.findall(r"^## (\d+)\. ", da, re.M))
    lx["figures"] = set(re.findall(r"<!--Figure (\w+):", d)) | set(re.findall(r"\*Figure (\w+)[ .]", d))
    two0 = section(d, r"^### 2\.0 ", r"^### ")
    lx["constructs"] = set(re.findall(r"^\| \*\*(B\d|P|CH\d)\*\* \|", two0, re.M))
    one5 = section(d, r"^### 1\.5 ", r"^---|^## ")
    lx["gaps"] = set(re.findall(r"^\| \**(L\d|G\d)\** \|", one5, re.M))
    dec = section(d, r"^## Decisions", r"^## ")
    lx["decisions"] = set(re.findall(r"(?<![\w-])(D\d+|OD-\d+|Q-[A-Z]\d+)(?![\w-])", dec))
    lx["decision_text"] = {m.group(1): " ".join(m.group(2).split())
                           for m in re.finditer(r"^\| (OD-\d+|Q-A\d+) \| (.+?) \| .+\|\s*$", dec, re.M)}
    roles = section(d, r"^\*\*Roles\*\*", r"^The system ")
    lx["roles"] = re.findall(r"^\| \*\*([^*]+)\*\* \|", roles, re.M)
    lx["role_words"] = set()
    for r in lx["roles"]:
        lx["role_words"].update(w.lower() for w in re.findall(r"[A-Za-z&]+", r))
    words = section(d, r"^\*\*Words used here", r"^\*\*Rules every figure")
    disp = re.search(r"\*\*Disposition\.\*\*[^:]*:\s*([^.]+)\.", words)
    lx["dispositions"] = {w.strip() for w in re.split(r",\s*|\s+or\s+", disp.group(1))} if disp else set()
    rules = section(d, r"^\*\*Rules every figure", r"^---")
    first = rules.split("\n2.")[0]
    lx["evidence"] = set(re.findall(r"\*([A-Z][^*]+)\*", first))
    return lx


# ------------------------------------------------------------------ rules
ID_RE = re.compile(r"(?<![\w-])(B\d+|CH\d+|L\d+|G\d+|OD-\d+|D\d+|Q-[A-Z]\d+)(?![\w-])")
TITLE_RE = re.compile(r"\b(CEO|CFO|CCO|COO|CTO|CIO)s?\b")
ROLE_RE = re.compile(r"\b([A-Za-z&']+)\s+(manager|lead|director|officer|engineer|technician|contractor|controller|supervisor|administrator)s?\b", re.I)
ROLE_PREFIX_OK = {"own", "the", "a", "an", "each", "every", "their", "its", "one", "any", "accountable", "named", "assigned", "same", "that", "this",
                  "or", "and", "site", "operations", "finance", "commercial", "field", "o&m"}
DISP_CANDIDATES = {"Recommended", "Conditional", "Acceptable", "Deferred", "Rejected", "Preferred", "Approved", "Optional", "Suggested",
                   "Blocked", "Accepted", "Feasible", "Infeasible", "Advised", "Possible", "Favoured", "Viable"}
EVIDENCE_RE = re.compile(r"\b(?:labelled|labeled|evidence\s+class(?:es)?(?:\s+of)?|marked)\s+\*([A-Z][A-Za-z ,]*?)\*")
RETIRED = [
    ("C1 'factor key'", re.compile(r"\bfactor[- ]keys?\b", re.I)),
    ("C1 a Finding as 'conditions on'", re.compile(r"\bFindings?\b[^.\n|]{0,60}\bconditions?\s+on\b|\bconditions?\s+on\s+factor", re.I)),
    ("retired mechanic name M1-M5", re.compile(r"\bM[1-5]\s+(?:Define|Observe|Evaluate|Choose|Prove)\b")),
    ("C2 the system or product as chooser/approver", re.compile(
        r"\b(?:the\s+system|AssetEcon|the\s+product)\s+(?:then\s+|also\s+|now\s+)?(?:chooses|approves|decides|picks|selects|"
        r"creates\s+(?:an?\s+|the\s+)?Actions?|acts\s+(?:on\s+its\s+own|for\s+you)|decides\s+for\s+you)\b", re.I)),
]
C4_WARN = re.compile(r"\b(?:replac\w*|retir\w*|no\s+longer)\b", re.I)
MONEY_RE = re.compile(r"(?<![\w.§/-])(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d{2}|\d+(?:\.\d+)?%)(?![\d])")
MARKER_AFTER = re.compile(r"\**<!--(?:figx?|rec):")   # rec:PATH is checked to the exact manifest value by check_manifest.py


def ref_ok(ref, lx):
    ref = ref.strip()
    if not ref:
        return False
    m = re.fullmatch(r"§(\d+\.\d+)", ref)
    if m: return m.group(1) in lx["design_sections"]
    m = re.fullmatch(r"WP §(\d+(?:\.\d+)?)", ref)
    if m: return m.group(1) in lx["wp_sections"]
    m = re.fullmatch(r"DA §(\d+)", ref)
    if m: return m.group(1) in lx["da_sections"]
    m = re.fullmatch(r"Figure (\w+)", ref)
    if m: return m.group(1) in lx["figures"]
    if ref in lx["named"] or ref in lx["decisions"] or ref in lx["constructs"] or ref in lx["gaps"]: return True
    if ref == "plan_model": return True
    m = re.fullmatch(r"owner:\s*(\S+)", ref)
    if m:                                       # owner files moved from .agent/ to owner/ (declutter step 4; specs/CITATION_MAP.md)
        rel = m.group(1)
        return (REPO / rel).is_file() or (rel.startswith(".agent/owner-") and (REPO / "owner" / rel[len(".agent/"):]).is_file())
    return False


def check_doc(name, text, kind, lx):
    """Return {rule: [messages]} for one derived or kept document."""
    out = {r: [] for r in RULES}
    p = prose(text)
    if kind != "kept":                                                   # A1
        heads = list(re.finditer(r"^## .*$", text, re.M))
        for h in heads:
            nxt = re.search(r"\S.*", text[h.end():])
            mk = re.match(r"<!--derives:\s*(.*?)-->", nxt.group(0)) if nxt else None
            if not mk:
                out["A1"].append(f"{name}:{line_of(text, h.start())}: section without a derives marker: {h.group(0)[:60]}")
                continue
            for ref in re.split(r"[;,]", mk.group(1)):
                if not ref_ok(ref, lx):
                    out["A1"].append(f"{name}:{line_of(text, h.start())}: derives reference not in the design: '{ref.strip()}'")
    for m in ID_RE.finditer(p):                                          # A2
        if m.group(1) not in lx["constructs"] | lx["gaps"] | lx["decisions"]:
            out["A2"].append(f"{name}:{line_of(p, m.start())}: ID not defined in the design: {m.group(1)}")
    if kind != "gtm":
        for m in TITLE_RE.finditer(p):
            out["A2"].append(f"{name}:{line_of(p, m.start())}: buyer title used as a product role: {m.group(1)}")
    for m in ROLE_RE.finditer(p):
        pre = m.group(1).lower()
        if pre not in ROLE_PREFIX_OK and not pre.endswith("'s"):
            out["A2"].append(f"{name}:{line_of(p, m.start())}: role not in the design's roles: '{m.group(0)}'")
    for m in re.finditer(r"[^.\n|]*\bdispositions?\b[^.\n|]*", p, re.I):
        for w in re.findall(r"\b[A-Z][a-z]+\b", m.group(0)):
            if w in DISP_CANDIDATES and w not in lx["dispositions"]:
                out["A2"].append(f"{name}:{line_of(p, m.start())}: disposition not in the design: {w}")
    for m in EVIDENCE_RE.finditer(text.replace("**", "")):
        if m.group(1).strip() not in lx["evidence"]:
            out["A2"].append(f"{name}: evidence word not in the design: *{m.group(1)}*")
    for label, rx in RETIRED:                                            # A3
        for m in rx.finditer(p):
            out["A3"].append(f"{name}:{line_of(p, m.start())}: {label}: '{m.group(0)[:60]}'")
    for ln, s in naming_violations(text):
        out["A3"].append(f"{name}:{ln}: 'plan' not the construct (OD-6): '{s[:90]}'")
    if kind == "register":                                               # A4
        rows = {m.group(1): " ".join(m.group(2).split())
                for m in re.finditer(r"^\| \**(OD-\d+|Q-A\d+)\** \| (.+?) \|", text, re.M)}
        for k, v in lx["decision_text"].items():
            if k not in rows:
                out["A4"].append(f"{name}: design decision missing from the register: {k}")
            elif rows[k] != v:
                out["A4"].append(f"{name}: {k} differs from the design's Decisions table")
    elif kind != "kept":
        for m in re.finditer(r"^\| \**(D\d+|OD-\d+|Q-[A-Z]\d+)\** \|", text, re.M):
            out["A4"].append(f"{name}:{line_of(text, m.start())}: restates decision {m.group(1)} as a table row; cite it by ID")
    if kind != "kept":                                                   # A5
        t = blank(text, r"<!--table:[\w-]+-->.*?<!--/table-->", re.S)
        t = blank(t, r"<!--(?!(?:figx?|rec):).*?-->", re.S)
        t = blank(t, r"`[^`\n]*`")
        t = blank(t, r"^#{1,6} \d+(?:\.\d+)+", re.M)                       # section numbers in headings are not figures
        for m in MONEY_RE.finditer(t):
            if not MARKER_AFTER.match(t, m.end()):
                out["A5"].append(f"{name}:{line_of(t, m.start())}: figure without a checked marker: {m.group(1)}")
    return out


def derives_refs(text):
    refs = set()
    for mk in re.findall(r"<!--derives:\s*(.*?)-->", text):
        refs.update(r.strip() for r in re.split(r"[;,]", mk))
    return refs


def coverage(builder_texts, lx):
    """A6: the builder documents' markers together cite every §2.x section."""
    refs = set().union(*(derives_refs(t) for t in builder_texts)) if builder_texts else set()
    need = sorted(s for s in lx["design_sections"] if s.startswith("2."))
    return [f"§{s} is cited by no builder document" for s in need if f"§{s}" not in refs]


def c4_warnings(name, text):
    p = prose(text)
    return [f"{name}:{line_of(p, m.start())}: C4 word for the reviewer: '{m.group(0)}'" for m in C4_WARN.finditer(p)]


# ------------------------------------------------------------------ self-test on the fixtures
def self_test(lx, root=ROOT):
    """Every plant must fail its rule and only its rule; the clean fixture must pass. Returns [(label, ok, detail)]."""
    res = []
    fx = root / "alignment-fixtures"
    for f in sorted(fx.glob("*.md")):
        t = f.read_text(encoding="utf-8")
        h = re.search(r"<!--fixture\s+expect=(\w+)\s+kind=(\w+)-->", t)
        expect, kind = h.group(1), h.group(2)
        failed = {r for r, msgs in check_doc(f.name, t, kind, lx).items() if msgs}
        want = set() if expect == "pass" else {expect}
        res.append((f"fixture {f.name}: expected {expect or 'pass'}, failed {sorted(failed) or 'none'}", failed == want, ""))
    for d in sorted(p for p in fx.glob("a6-*") if p.is_dir()):
        texts = [p.read_text(encoding="utf-8") for p in sorted(d.glob("*.md"))]
        expect = (d / "EXPECT").read_text(encoding="utf-8").strip()
        missing = coverage(texts, lx)
        res.append((f"fixture set {d.name}: expected {expect}, A6 {'fails' if missing else 'passes'} {missing[:2]}",
                    bool(missing) == (expect == "A6"), ""))
    # A4 on a register built from the design itself: whole and exact must pass; one altered row must fail A4 only
    rows = "".join(f"| {k} | {v} |\n" for k, v in sorted(lx["decision_text"].items()))
    reg = "## 1. Owner decisions\n<!--derives: Decisions-->\n\n| ID | Decision |\n|---|---|\n" + rows
    good = {r for r, msgs in check_doc("register (built)", reg, "register", lx).items() if msgs}
    k0 = sorted(lx["decision_text"])[0]
    bent = reg.replace(f"| {k0} | {lx['decision_text'][k0]} |", f"| {k0} | {lx['decision_text'][k0]} (reworded) |")
    badr = {r for r, msgs in check_doc("register (one row altered)", bent, "register", lx).items() if msgs}
    short = reg.replace(f"| {k0} | {lx['decision_text'][k0]} |\n", "")
    shortr = {r for r, msgs in check_doc("register (one row missing)", short, "register", lx).items() if msgs}
    res.append((f"A4 register built from the design passes (failed {sorted(good) or 'none'})", not good, ""))
    res.append((f"A4 register with {k0} reworded fails A4 only (failed {sorted(badr)})", badr == {"A4"}, ""))
    res.append((f"A4 register missing {k0} fails A4 only (failed {sorted(shortr)})", shortr == {"A4"}, ""))
    nf = (root / "naming-lint-fixtures.txt").read_text(encoding="utf-8")
    must_fail = re.findall(r"^FAIL: (.+)$", nf, re.M)
    must_pass = re.findall(r"^PASS: (.+)$", nf, re.M)
    caught = [s for s in must_fail if naming_violations(s)]
    passed = [s for s in must_pass if not naming_violations(s)]
    res.append((f"naming lint: {len(caught)} of {len(must_fail)} planted target uses fail", len(caught) == len(must_fail) and must_fail,
                [s for s in must_fail if s not in caught]))
    res.append((f"naming lint: {len(passed)} of {len(must_pass)} construct uses pass", len(passed) == len(must_pass) and must_pass,
                [s for s in must_pass if s not in passed]))
    return res


# ------------------------------------------------------------------ run
def run(root=ROOT, extra=()):
    """Return (results, warnings, notes). results: [(label, ok)]. extra: [(path, kind)] outside the pack."""
    lx = lexicon(root)
    results, warnings, notes = [], [], []
    for k in ("design_sections", "constructs", "gaps", "decisions", "roles", "dispositions", "evidence", "figures"):
        results.append((f"lexicon: design defines {k} ({len(lx[k])})", bool(lx[k])))
    for fn in SOURCES:                                                    # A3 on the design itself
        txt = (root / fn).read_text(encoding="utf-8")
        if fn == SOURCES[0]:   # the owner-approved Introduction is kept verbatim
            a, b = txt.index("## Introduction"), txt.index("## How to read")
            txt = txt[:a] + re.sub(r"[^\n]", " ", txt[a:b]) + txt[b:]
        bad = naming_violations(txt)
        results.append((f"A3 naming lint (OD-6) on {fn} (violations: {bad[:4]} x{len(bad)})", not bad))
        p = prose(txt)
        hits = [f"{label} l.{line_of(p, m.start())}" for label, rx in RETIRED for m in rx.finditer(p)]
        results.append((f"A3 retired terms on {fn} ({hits[:4]})", not hits))
    docs = [(fn, kind) for fn, kind in {**DERIVED, **KEPT}.items() if (root / fn).is_file()] + list(extra)
    builders = []
    for fn, kind in docs:
        path = pathlib.Path(fn) if pathlib.Path(fn).is_absolute() else root / fn
        t = path.read_text(encoding="utf-8")
        for rule, msgs in check_doc(path.name, t, kind, lx).items():
            results.append((f"{rule} {path.name} ({msgs[:3]} x{len(msgs)})", not msgs))
        warnings += c4_warnings(path.name, t)
        if kind == "builder":
            builders.append(t)
    nb = sum(1 for k in DERIVED.values() if k == "builder")
    if len(builders) == nb:
        miss = coverage(builders, lx)
        results.append((f"A6 coverage of §2.x by the builder documents ({miss})", not miss))
    else:
        notes.append(f"A6 pending: {len(builders)} of {nb} builder documents written")
    unwritten = [fn for fn in DERIVED if not (root / fn).is_file()]
    if unwritten:
        notes.append("not yet written: " + ", ".join(unwritten))
    if PENDING:
        notes.append("pending recreation (not checked): " + ", ".join(PENDING))
    for label, ok, detail in self_test(lx, root):
        results.append((label + (f" (missed: {detail})" if detail else ""), ok))
    return results, warnings, notes


def derived_present(root=ROOT):
    """Derived documents that exist, for check_manifest.py's anchor scan (A5: every figure keeps a checked home)."""
    return [fn for fn in DERIVED if (root / fn).is_file()]


def main(argv):
    extra, i = [], 0
    while i < len(argv):
        if argv[i] == "--doc":
            extra.append((argv[i + 1], argv[i + 2])); i += 3
        else:
            raise SystemExit(f"unknown argument {argv[i]}")
    results, warnings, notes = run(ROOT, extra)
    fails = [l for l, ok in results if not ok]
    for l in fails:
        print("FAIL", l)
    for n in notes:
        print("note:", n)
    for w in warnings:
        print("C4 word for the reviewer:", w)
    print(f"C4 words for the reviewer: {len(warnings)}")
    print(f"alignment: {len(results) - len(fails)} checks passed, {len(fails)} failed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
