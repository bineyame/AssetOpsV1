"""Compact text summary of a batch-17 evidence.json (read-only)."""
import json, sys
full = "-v" in sys.argv
for part in [a for a in sys.argv[1:] if a != "-v"]:
    ev = json.load(open(f"{part}/evidence.json", encoding="utf8"))
    for p in ev["pairs"]:
        a, m = p["app"], p["mock"]
        print(f"=== {p['screen']} {p['case']} {p['viewport']} pageH app/mock {a['pageH']}/{m['pageH']} ovX {a['overflowX']} "
              f"hdr {a['header'] and a['header']['h']} mainTop {a['mainTop']}/{m['mainTop']} cerr {a['consoleErrors']}")
        mp = {pn["title"]: pn for pn in m["panels"]}
        for pn in a["panels"]:
            mm = mp.get(pn["title"])
            r = f"{pn['h']}/{mm['h']} ({pn['h']/mm['h']:.2f})" if mm else f"{pn['h']}/-"
            print(f"  P {pn['title']!r} {r} w={pn['w']}/{mm and mm['w']} rows={pn['rows']}/{mm and mm['rows']} cols={pn['columns']} | {mm and mm['columns']}")
            if full:
                print(f"     chips {pn['chips'][:8]} links={pn['links']}/{mm and mm['links']} details={pn['details']}/{mm and mm['details']} h3={pn['h3']}")
                for r_ in pn["rowText"][:6]: print("     row", r_)
        missing = [t for t in mp if t not in [x["title"] for x in a["panels"]]]
        if missing: print("  MISSING vs mock:", missing)
        if [x["title"] for x in a["panels"]] != [x["title"] for x in m["panels"]] and not missing:
            print("  ORDER app", [x["title"] for x in a["panels"]], "mock", [x["title"] for x in m["panels"]])
        mi = a["mini"]
        print("  strip:", mi["strip"][:260])
        print("  cards A:", [c[:70] for c in mi["cards"]], "| M:", [c["t"][:50] for c in m["cardsDom"]])
        print("  cardsH A/M:", [c["h"] for c in a["cardsDom"]][:5], [c["h"] for c in m["cardsDom"]][:5])
        print(f"  refusal[{mi['refusalKey']}]: {mi['refusal'][:200]}  notice: {[n[:120] for n in mi['notice']]}")
        print(f"  NotRecorded {mi['notRecorded']} NAY {mi['notAvailableYet']} prepared {mi['prepared']} enums {mi['enums']} uuids {mi['uuids']} Zcount {mi['utc']} details {mi['details']}")
        print("  fonts prose", a["fonts"]["prose"] and a["fonts"]["prose"]["size"], a["fonts"]["proseSizes"], "pSizes", a["pSizes"], "| M", m["fonts"]["prose"] and m["fonts"]["prose"]["size"], m["pSizes"])
        print("  tabs", a["tabRows"], "| M", m["tabRows"])
        print("  clip", a["clipped"][:3], "hscroll", a["hscroll"][:4], "dark", a["dark"][:1])
        if full:
            print("  links", a["mainLinks"][:40])
            print("  objective", mi["objective"])
        c = a.get("cold") or {}
        print("  cold:", {k: c.get(k) for k in ("plural1", "evConnector", "rawConnector", "backticks", "windowForm", "alerts", "svg", "readFull", "detailsOpen", "vscroll")})
        if full:
            print("  cardLinks", c.get("cardLinks"))
        x = a.get("extra") or {}
        print("  crumb:", x.get("crumb"), "| sub:", x.get("sub"), "| M crumb:", (m.get("extra") or {}).get("crumb"), "| M sub:", (m.get("extra") or {}).get("sub"))
        print("  buttons:", x.get("buttons"), "| M:", (m.get("extra") or {}).get("buttons"))
        if full:
            print("  TEXT:", x.get("mainText", "")[:1800])
            print("  MTEXT:", (m.get("extra") or {}).get("mainText", "")[:1200])
