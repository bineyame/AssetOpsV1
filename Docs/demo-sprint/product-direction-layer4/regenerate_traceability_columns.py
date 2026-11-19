#!/usr/bin/env python3
"""Regenerate two columns of outcome-lever-capability-traceability.csv from the design (regeneration F, #7).

Design-pack tool, not product code. Python 3 standard library only. The 454 rows stay; only two columns change:

  mechanic            -> constructs   the rev 13 mechanics M1-M5 become the design's construct IDs (design §2.0)
  executive_question  -> roles        buyer titles become the design's five roles (design §2.6)

The mapping (for review):
  M1 Define                      -> B1
  M2 Observe                     -> B1, plus B3 when the row's text names a source record, plus B2 when it names a
                                    target, budget or attribution, plus CH1 when it names a Finding
  M3 Evaluate                    -> CH3
  M4 Choose                      -> P
  M5 Prove                       -> CH4
  "reader of M1-M5"              -> CH5 (the screens read every construct)
  any row of kind workforce-execution also gets CH2 (the recorded person who does the work)
  CEO -> Operator executive; COO -> Operations or site manager; CFO and CCO -> Finance and commercial lead; "—" stays.

Run: python3 regenerate_traceability_columns.py          rewrite the file in place (idempotent)
     python3 regenerate_traceability_columns.py --check  exit 1 if the file is not already regenerated
"""
import csv, io, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent
CSV = ROOT / "outcome-lever-capability-traceability.csv"
ORDER = ["B1", "B2", "B3", "P", "CH1", "CH2", "CH3", "CH4", "CH5"]
ROLES = ["Operator executive", "Finance and commercial lead", "Operations or site manager"]
TITLE = {"CEO": ROLES[0], "CFO": ROLES[1], "CCO": ROLES[1], "COO": ROLES[2]}
SOURCE = re.compile(r"\b(source|sources|record|records|intake|export|invoice|invoices|ledger|roster|receipt|receipts|billing|settlement|meter register|contract document)\b", re.I)
TARGET = re.compile(r"\b(target|targets|budget|attribution|bridge|plan value|plan values|planned)\b", re.I)
FINDING = re.compile(r"\bFindings?\b")
TEXT = ("factor", "declared_measure", "model_or_algorithm", "notes")


def constructs(row):
    m = row["mechanic"].strip()
    if m.startswith("reader of"):
        out = {"CH5"}
    else:
        out = set()
        text = " ".join(row[k] for k in TEXT)
        for tok in m.split():
            out |= {"M1": {"B1"}, "M3": {"CH3"}, "M4": {"P"}, "M5": {"CH4"}}.get(tok, set())
            if tok == "M2":
                out.add("B1")
                if SOURCE.search(text): out.add("B3")
                if TARGET.search(text): out.add("B2")
                if FINDING.search(text): out.add("CH1")
            if tok not in ("M1", "M2", "M3", "M4", "M5"):
                raise SystemExit(f"{row['row_id']}: unknown mechanic {tok!r}")
    if row["row_kind"] == "workforce-execution":
        out.add("CH2")
    return " ".join(c for c in ORDER if c in out)


def roles(row):
    q = row["executive_question"].strip()
    if q == "—":
        return q
    got = set()
    for t in q.split():
        if t not in TITLE:
            raise SystemExit(f"{row['row_id']}: unknown title {t!r}")
        got.add(TITLE[t])
    return "; ".join(r for r in ROLES if r in got)


def regenerate(text):
    rows = list(csv.DictReader(io.StringIO(text)))
    head = next(csv.reader(io.StringIO(text)))
    if "constructs" in head:            # already regenerated: nothing to map
        return text
    new_head = ["constructs" if h == "mechanic" else "roles" if h == "executive_question" else h for h in head]
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(new_head)
    for r in rows:
        r2 = dict(r, mechanic=constructs(r), executive_question=roles(r))
        w.writerow([r2[h] for h in head])
    return buf.getvalue()


def main(argv):
    text = CSV.read_text(encoding="utf-8")
    head = next(csv.reader(io.StringIO(text)))
    if "--check" in argv:
        ok = "constructs" in head and "roles" in head and not re.search(r"\bM[1-5]\b|\b(CEO|CFO|CCO|COO)\b",
                                                                          "\n".join(f"{r['constructs']} {r['roles']}" for r in csv.DictReader(io.StringIO(text))))
        print("traceability columns regenerated" if ok else "traceability columns NOT regenerated")
        return 0 if ok else 1
    out = regenerate(text)
    n = len(list(csv.DictReader(io.StringIO(out))))
    CSV.write_text(out, encoding="utf-8")
    print(f"{n} rows written")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
