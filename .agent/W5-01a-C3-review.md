# W5-01a C3 review: cold Health

Reviewer: fresh independent Claude reviewer, 2026-10-22.
Worktree `AssetOpsV1-review2`, branch `task/W5-01a-cold-selected-depth`, head `100f2bd1`.
C3 commits reviewed: `a374e2d8`, `ef933516`, `56231727`, `f3bf7c6c`, `a9769dd9`, `100f2bd1`. The main merges (`d34e06f8`, `127a117d`, `a23cda93`) were not reviewed.
Spec: `.agent/W5-01-build-spec.md`. I read the C3 card, the C1 Health read tables, the literal ledger, the caps and the capture-method section, "C3 rulings (Q-C3-1..4)", "C3 rulings (Q-C3-5, mock differences)" and the Codex retrospective.

## Verdict: REVISE

The code does what the rulings say. One High finding remains, and it starts in the Q-C3-5 ruling rather than in the build. Rulings 2 and 4 misdescribe the mock for the two neutral cards, so the built page has a user-visible difference from the mock that nobody labelled. The fix is one Architect amendment and a one-line change.

## Findings

### H1 (High): the neutral cards depart from the mock, and the departure is not labelled

**Where:** `frontend/src/sites/ColdHealthDepth.tsx:110` (`assessment` on every card), as directed by Q-C3-5 rulings 2 and 4.

**What is wrong.** In the mock (`frontend/mockups/v69/index.html:181`, line 689), `metric()` adds the `assessment` class only when the card has a tone:

```js
`<div class="metric ${tone?'assessment '+tone:''}">`
```

On `cold-health`, only `Backup generator` has a tone (`amber`). `Cooling plant` and `Temperature sensing` pass `''`, so they are plain `.metric` cards. Their value uses `.metric-value` at **27 px**, and they have **no top border**. `cold-health-1440-mock.png` and `cold-health-390-mock.png` show this: `Unknown` and `Limited` are large, with no border.

Ruling 2 says to apply `assessment` to all three cards "so the neutral cards have the mock's neutral assessment border". Ruling 4 says "the mock's assessment state word is 17 px". Both statements are true only of the Backup card. As a result, every capture (for example `cold-health-failed-start-1440-app.png`) shows:
- a 3 px grey top border on the neutral cards, which the mock does not have;
- 17 px `Unknown` and `Limited` values where the mock has 27 px.

The packet says the page matches the mock ("amber top border only on the Backup card, body-colour 17 px values"). The amber part is accurate, but the packet does not mention the grey border or the 17 px neutral values.

**Why it matters.** Under the ROLE_CONFIG mock-fidelity rule, a user-visible departure that is not labelled `MOCK DEVIATION` is High. This departure changes the cards' prominence: the mock's large neutral words become small.

**Fix.**
1. The Architect amends Q-C3-5 rulings 2 and 4: a card gets `assessment` only when it has a tone.
2. The Implementer passes `assessment={row.condition_state === "NEEDS_INVESTIGATION"}` and leaves out both `assessment` and `word` on the other cards. A plain `MetricCard` already gives the mock's 27 px value and no top border (`primitives.css:4423`).
3. Update `coldHealthDepth.test.tsx` `condition_matrix`, which currently asserts `v69-metric--assessment` on all three cards.
4. Recapture the 10 app PNGs. The card heights grow slightly; recheck them against the 200/430 cap.

If the Architect prefers to keep the current styling, the ruling must instead label it as a `MOCK DEVIATION`, with the reason and the alternatives considered.

### M1 (Medium): at 390 px, the sticky Asset column hides the assessment columns

**Where:** the `primitives.css` block added in `a9769dd9`, which matches the ruling literally.

**What is wrong.** In every 390 capture (for example `cold-health-failed-start-390-app.png` and `cold-health-unknown-390-app.png`), the sticky Asset column fills almost the whole table area. That column is at least 240 px wide and holds a one-line 36-character ID. `Supported assessment` and `Next evidence` are completely off-screen until the user scrolls sideways.

The mock at 390 shows all three columns, because its Asset cell is a short code such as `GEN-CR-01`. The CSS is exactly what the ruling specifies, and the spec does sanction a sticky first column at 390. So this is not an implementation error.

**Why it matters.** The column that carries the page's claim is invisible on a phone until the user scrolls.

**Fix.** This needs an Architect decision, and it is not a blocker for the Implementer. Options:
- a narrower sticky column, such as the name only, with the ID on a smaller wrapped line;
- an Asset cell that leads with `asset_code`, as the mock does;
- labelling it as a `MOCK DEVIATION`.

At minimum, flag it for the owner walkthrough.

### Low

- **L1.** The tests do not cover the in-panel loading line (`Loading the site's gateway contact.`) on the cold page's `SiteHealthSources`. The composition test only waits for it to disappear. It is low risk, because `SourcesPanel` is shared with non-cold Sites.

## Checks against the dispatch list

- **Files on the card.** Every changed file is on the C3 list as the rulings amend it:
  - Q-C3-1 added `SiteHealth.tsx`.
  - Q-C3-3 and Q-C3-4 added `coldDepth.test.tsx` and `coldFoundation.test.tsx`.
  - Q-C3-5 rulings 1 and 3 added `primitives.css` and `ui/V69Layout.tsx`.
  - The shared `MetricCard` `link?: ReactNode` prop is named in Q-C3-5 ruling 3, so it is on the card. It renders `<div className="v69-metric__link">` after the note, and only when a link is given.
  - `operatorSiteRoutes.ts` is listed but needed no change, because `siteHealthHref` already existed.
- **Literals.** These match the spec character for character:
  - the condition notice, loading line and empty sentence;
  - the card words (`Needs attention`, `Limited`, `Unknown`, `Not configured`);
  - every C1 tuple in `HEALTH_ROW_LITERALS`;
  - the next-evidence strings;
  - the refusal heading, `Retry`, and the unreachable and malformed sentences, imported from C2;
  - `View detail →`;
  - the registry node, panel-row and ledger JSON;
  - the `cooling:1` and `cooling:2` reasons, which equal the Q-C3-5 ruling 5 literals.
- **DTO validation** (`ColdDepthClient.ts`). Each of these must hold, or the read is malformed:
  - The `health` key set and every row's key set are exact, and the asset key set is `{asset_id, asset_code, display_name}`.
  - The three rows appear in kind order.
  - Each row's `(kind, condition_state, observation, limitation)` is one of the C1 tuples, and `next_evidence` equals its kind's literal.
  - `asset_id`, `link`, `display_name` and `foundation_revision_id` are a string or null, and `evidence_ids` is a string array.

  A malformed read is returned as `unavailable` and renders the refusal. This is correct against the C3 Validation bullet. The tests cover missing, extra, ill-typed, reordered and off-table values.
- **`SiteHealthSources`.** It is exported with the exact signature. It uses the same `health:${siteId}` key, heading ID, description, `SourcesBody` and `HealthGap`, and keeps its loading line inside the panel. It has no battery read, strip, panel or blue notice.
- **Non-cold Sites.** `SiteHealth` keeps its own reads, early loading return, strip, battery panel and blue notice. Only the source panel moved into the shared private `SourcesPanel`, and its markup is identical. `siteHealthBoundary.test.tsx` asserts that a mini-grid Site still gets all four and never calls `getHealth`.
- **Sticky CSS.** It is the Q-C3-5 block verbatim inside `@media (max-width: 480px)`. `--surface-raised` and `--surface-sunken` exist in `tokens.css`.
- **Cards.**
  - The Backup card is `v69-metric--assessment v69-metric--amber`: a 3 px amber top border and a 17 px body-colour value.
  - Every card has a plain label and a separate `View detail →` link from `coldUiHref`. A null destination gives no link.
  - The neutral cards are covered under H1.
- **Test edits.** The `coldDepth` test name and its last assertion equal Q-C3-3 literally. The `coldFoundation` test equals Q-C3-4 literally.

## Captures compared with the v69 `cold-health` mock (1440 and 390, five states)

**What matches.**
- The page has the Site-name h1, with `Health` as the breadcrumb end and the active tab.
- The three cards appear in the mock's order, then `Condition and evidence` with the columns `Asset` / `Supported assessment` / `Next evidence`.
- Every card has `View detail →`, as in the mock.

**Differences that are labelled.**
- the third probe row;
- the asset name plus ID line;
- the amber condition notice;
- the currentness notice;
- the S7 Data sources panel, which comes last.

**Differences that are not labelled.** H1 (the neutral card border and size) and M1 (the 390 column visibility).

**Caps.** I checked these myself in `evidence.json` (revision `a9769dd9`):

| Block | Measured (1440 / 390) | Cap (1440 / 390) |
| --- | --- | --- |
| Cards | 135 / ≤347 | 200 / 430 |
| Condition and evidence | 251–285 / 311–345 | 330 / 430 |
| Data sources | 299 / 505 | 700 / 800 |
| Page | ≤1145 / ≤1784 | 1900 / 2350 |

- `scrollWidth` equals `clientWidth` in every capture, and nothing is ellipsized.
- Every asset ID is on one line and not clipped.

**Clocks and producers.**
- `failed-start` and `unknown` are CURRENT and UNKNOWN on the C1 watermark, and `unknown` uses the 2026-10-05 window.
- `pending` is PENDING_RECOMPUTE.
- `historical` uses `known_at=W0` (12:08:07) and is HISTORICAL.
- `refused` is a live 422 `COLD_WINDOW_INVALID`, showing its code, message and Retry.

## Checks I ran (at `100f2bd1`)

| Check | Result |
| --- | --- |
| `npx.cmd tsc --noEmit` (frontend) | exit 0 |
| `npx.cmd vitest run --minWorkers=1 --maxWorkers=2` on `coldHealthDepth`, `siteHealthBoundary`, `coldDepth`, `coldFoundation`, `coldSiteViews` | 5 files, **151 passed**, 0 failed (58.8 s). Vitest ran in this session. |
| `tools/check-architecture.ps1` | passed |
| `tools/check-agent-workflow.ps1` | passed |
| `node frontend/docs/architecture/check_v69_dependency_registry.cjs` | exit 0. It lists cooling (3 panels) and cold-health (1 panel), with `P-cold-area`. |

## What I did not verify

- **Backend tests:** not run, as instructed (a full suite was running).
- **Full frontend suite and production build:** not run.
- **`tools/check-all.ps1`:** not rerun. The packet reports 11/11 guards passed on `a9769dd9`.
- **Captures:** not regenerated. They need Postgres, `lab_app`, Vite and Chrome. I judged them from the PNGs and `evidence.json`.

## Residual risk

- The validator accepts any string `label`, and it does not check that `link` is null for `NOT_CONFIGURED`. The spec does not require either check; the server owns both.
- If `asset_id` has no match in `assets`, the Asset cell shows the ID alone. C1 guarantees a match, so this should not happen.
