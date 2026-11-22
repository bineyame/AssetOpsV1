# IA-P3 pre-flight (P4b, P5, P6, P7): spec rev 3 against the code

Implementer (Claude), 2026-11-22. Branch `task/IA-P3-sites-site-inbox` from `main` `8f8b3ad16`.
Spec: `spec.md` rev 3 §2.3, §4, §5, §6 P4b to P7, §7; `spec-period.md` P.8, P.9; `handshake.md` answers R3, R6, R8, I10, I13;
6f1: `specs/6f-decisions-screen/spec.md` §2 G-IAP, §4; `rulings.md` D-P6.78 (Q14, Q17).

One batch for the Architect (`.ai/RULES.md` §4). Each question has a default. The defaults apply now (W3).
**BLOCKER** marks a question that stops its unit until it is answered. **No question blocks P4b**, so P4b is built on its
defaults in this run. Q21 blocks only the P5 alias.

## Where IA-P3 and 6f1 meet, and which merges first

- **The meeting point is one function.** `decisionItems(body, rows)` (`estate/homeLists.tsx:77`) builds the decision rows
  from the placed Findings. 6f1 U2 (§4.4) replaces every caller with `useDecisionItems(range)`, which reads the decision
  records. It also drops `watching` (D-P6.78 Q14) and sets the E0 counts from the records (§4.1).
- IA-P3's P6 inbox (the badge and "In your portfolio") and P7 search (the Decisions entries) are two new callers. P4b's
  Sites "Waiting for a choice" column reads E0 `waiting_by_site`, which 6f1 U2 re-sources on the server with the same
  field names. P4b does not change at the merge.
- **Order.** 6f1 U2 is gated on 6h merging (G-6h), and 6f1 is building U1 now. IA-P3 (4.5 u) is expected to merge
  first. 6f1 U2 then runs §4.4's W6 sweep (`grep -rn "decisionItems(" frontend/src`). The sweep finds the inbox and search
  only if they call `decisionItems(` by that name (Q12).
- If 6f1 U2 merges first, P6 and P7 call `useDecisionItems` instead, and IA-P3 runs the sweep (D-P6.78 Q17).
- One shared file: both lanes append rows to `.agent/mock-departure-register.md` after R789 (Q27).

## Questions

### P4b (none blocks)

1. **The directory read.** §4.1 says the Sites list reads `GET /api/sites`, but its rows come from E1 alone, in E1's
   order. E1's Sites are `registry.imported_sites()`, so a Site that the directory lists and E1 does not (a Lab-created
   or legacy-file Site) would leave `/sites`. *Default:* the rows are E1's. A directory Site that E1 lacks is added after
   them, in directory order. Its title links to `/sites/{site_id}`, and every other cell reads "Not available yet",
   including Group. No new word is used. If the directory read is refused, the E1 rows render alone.
2. **Where `months_text` goes.** `months_text` ("Compared in 1 of 2 months") has no column in §5.2's sites row.
   *Default:* it goes under the Contribution cell as `<small>`, the same form as `gap_word` under Gap.
3. **"Compared" for the target facet.** The facet's `of` is "below" when `below` is true, "on" when the row is compared
   and not below, and none when the row is not compared. E1 has no `compared` key. *Default:* a row is compared when
   `gap_word !== null` (P.8: only compared rows carry a word).
4. **Group scope from E1 rows.** A `group:` scope needs a domain code, and E1 rows carry only the `group` word.
   *Default:* invert `DOMAIN_WORD`, whose equality with E1's words P.8 test 2 pins. No quoted Site-type literal is added,
   so the hard-wiring ratchet is not raised.
5. **The More line.** `HomeList` has no More text, only "Show all {n}". *Default:* a `def.more?(hidden)` hook renders
   "Not shown: {h} Sites." before the link. It is literal for every `h`, including 1 (no new singular string). It is
   reachable only with more than 10 Sites.
6. **The note on the "Waiting for a choice" column** (P.9: "in the header's `<small>`"). *Default:* `HomeListColumn`
   gains an optional `note` that renders as `<small>` inside the `<th>`. It holds `RangePartNote`'s words and shows only
   when the window differs from the range.
7. **Outcomes L3's range note.** P.9 lists Outcomes L3 among the blocks fed by a capped read. IA-P2 did not add it.
   *Default:* P4b puts `RangePartNote` at the head of L3.
8. **Outcomes L1 and the E1 refusals.** *Default:* L1 is E1's `headline.text` with its `evidence` words as `<small>`,
   then `without_target.text` when it is not null. In mode `none`, E1's `notes` sit in L1's place. A refused E1 renders
   the Overview's E2 refusal unchanged: the served `text` (else `DD_COPY.unreadable`), "Try again" unless 422, and
   `DD_COPY.signIn` on 401. This applies on both `/sites` and Outcomes.
9. **The Thika matrix fixtures** (`siteTypeMatrix.test.tsx`, D-IAP.25/26). The E1 fixtures have no Thika: they are
   World A or P plus COLD-001 and EV-001. *Default:* `test_iap_portfolio_sites.py` `_fixture_bodies()` gains
   `sites-g-2026-10.json` (World G) and `sites-g-2026-09-10.json` (`_world_p("G")`), both over `(*REFS, THIKA)`. They
   are written by `IAP_WRITE_FIXTURES=1` and pinned by test 9. This is a backend test change only;
   `backend/assetops_backend` is untouched.
10. **`IA_LANDED` IDs.** The merged code uses part IDs (`"IA-P1"`, `"IA-P2"`), not the unit IDs of §5.1. *Default:* P4b
    adds `"IA-P3"` in its last commit, and P5's `/sites/:id/findings` alias is tagged `unit: "IA-P3"`. The alias stays
    unmounted until P5 adds it, after the parity test.
11. **The demo's prebuilt responses** (IA-P2 risk 1, carried). `/sites` now reads `/api/portfolio/sites`, which
    `tools/demo_combined.py` does not prebuild. *Default:* not in IA-P3. The coordinator rules on it before the next demo
    build.

### P6

12. **Builder name for the 6f1 sweep.** *Default:* the inbox and search take their rows from
    `decisionItems(loaded.first, loaded.rows)` through `useEstateRead(…, "portfolio", …)`, and from no other builder, so
    §4.4's grep finds them.
13. **The badge under truncation.** The spec says the badge is "the count of the Decisions read's `waiting` rows". The
    tile shows `summary.waiting_count` when the read is truncated. *Default:* the badge uses `decisionsDef`'s tile rule,
    from one shared function, so badge = tile in every case (W1, the `badge` plant).
14. **The dialog.** No reusable dialog exists. The only focus-trapping one is the private `Drawer` in
    `estate/DeepDiveMonth.tsx:154`. *Default:* move it to `ui/Drawer.tsx` unchanged, with DeepDiveMonth importing it.
    The inbox uses it.
15. **"Since you last looked" words.** `ProgressPanel` shows its rows only inside the "Inspect basis" disclosure, as
    "Action {code} · {outcome words}". *Default:* each line is that exact string (`displayCode`,
    `progressOutcomeWords`). "No change recorded in this range" is the spec's own new string.
16. **When 6f1 drops `watching`** (D-P6.78 Q14), the badge rule is unchanged: it counts `waiting`. *Default:* no action in
    IA-P3.

### P5

17. **Order, not only labels.** Today's tabs are Overview, Foundation, Health, Performance, Findings, Work, Financials,
    Evidence. §2.3 orders them Overview, Operations, Performance, Financials, Evidence, Setup. *Default:* §2.3's order.
    The tests that pin the old eight are migrated as (b).
18. **`/assets` and `/uploads` today.** Assets lights Health (`SiteHealthFrames.tsx:222,272`). Uploads draws no tab row,
    and its crumb goes through Health. *Default:* as §2.3: Assets lights Setup, and Uploads gains the tab row and lights
    Evidence. The Uploads crumb drops "Health" and becomes Sites › Site › Upload readings.
19. **The mini Finding views' tab row (R383).** `CanonicalMiniFinding` keeps a tab row on views other than recommendation
    and alternatives, under MOCK DEVIATION R383. *Default:* P5 retires R383, since every Finding page is an object page,
    and marks the register row closed by P5.
20. **The crumb's Site link.** The Action and mini Finding crumbs read "Actions › {code} › {view} · site:" today.
    *Default:* every object page uses `ui/Breadcrumbs` with three parts, as §2.3 sets out. The view name and the
    "· site:" suffix go.
21. **BLOCKER (P5 alias only): parity across three reads.** Mini reads `/{site}/finding-index?domain&from&to`, and cold
    and EV read `…/findings?from&to&known_at`. The Findings list reads `/api/estate/findings`, capped at 1,000 rows. No
    fixture is shared: the Site index fixtures use `site_id: "s"`, and the cold and EV fixtures are inline.
    *Default:* the parity test uses one new aligned fixture set per vertical. Each is a Site index body and an estate
    findings body for the same Site code and window, made from the same Finding ids. "Same window" means the address's
    `from` and `to`, with `readWindow` applied to both. The test compares `finding_id` sets. If a vertical's index lists a
    Finding the estate read cannot hold (another `known_at` rule, or a `domain` filter), that vertical stops with
    `SPEC_AMBIGUITY` (§6 P5), and MD-IAP-15 applies. The Architect confirms that fixture-level parity is the intended
    proof. A live-read parity test would need a database world.
22. **T1 and T2 fixtures.** The gates answer only the three `/api/estate/*` lists, so `/api/sites/*` gives 404.
    *Default:* T1 and T2 add a Site detail fixture per vertical to `fixtures/iap/` from the existing frontend fixtures
    (`sites/__tests__/sldFixtures` and the cold and EV test bodies). Their sources go in the packet (I11). Any Site panel
    with no fixture shows its existing unavailable state. T1 counts the tab row and T2 counts the crumb, so neither needs
    the panels' content.

### P7

23. **Scope on a Site page or hub.** "A group or all keeps `scope=` in the address" on a hub, but no hub reads `scope`.
    *Default:* the switch writes `scope=` (all removes it). The Overview and Demand & capacity then show the chip "This
    page shows every Site" (MD-IAP-5). Other hubs and Site pages keep the parameter and show nothing more.
24. **The domains present for the scope menu.** *Default:* from `/api/sites` `site_type`, mapped through `DOMAIN_WORD`
    with no quoted literal (as in Q4). The entries come in `DOMAIN_WORD` order, then the Sites in directory order.
25. **Search entries' targets.** *Default:* Decisions use `decisionsDef().target`, Findings use the Findings def's
    target, and Actions use `link_refs.action`. An entry whose target is null is not indexed, because "only live
    targets" applies to it as it does to rail items.
26. **The walk test** (I13). `test_t11_smoke_pages` pins the 8 pages. *Default:* P7 adds `/decisions`, `/results`,
    `/portfolio/outcomes` and `/portfolio/demand-and-capacity` to the JSON and to the test's literal, in one commit.

### All units

27. **The register numbers.** 6f1 also appends after R789. *Default:* IA-P3 takes R790 onward. Whoever merges second
    renumbers its rows at the merge. Rows are named by MD ID, so citations do not move.
28. **The P5 to P7 gates.** `tools/iap_gates.cjs` has no per-unit switch, and every check always runs. *Default:* each
    unit's checks are added to the always-run set, as IA-P1 and IA-P2 did.
