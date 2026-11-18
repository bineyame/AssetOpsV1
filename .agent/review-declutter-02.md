# Review: declutter step 2 (indexes; DECISIONS and CODE_STATE split)

Reviewer: fresh Claude reviewer (did not author the work), 2026-11-18.
Branch `task/declutter-02-indexes` at `909cc1df1` (7 commits over `main` `e0b911b45`), worktree
`/opt/assetecon/AssetOpsV1-declutter`. Discovery review (W5): all of the diff was read; I formed my own view before
reading the packet.

## Verdict: REVISE

The split preserves every byte, and the indexes resolve. The router changes are correct. Three things block the
merge. check-all is red at the branch tip. The guard's "drifted pointer is a note" path can hide a deleted ID. Two
standing owner rules are marked historical, and O4 will build on that status column. All three are small fixes.

## Findings (ranked)

### F1 High: check-all fails at the branch tip
`.agent/packet-declutter-02.md:48-49`. The packet commit (`909cc1df1`) cites the two planted IDs from the author's
manual test (the SR-9999 ruling and the 2026-12-01 "no-such-decision" ID). The guard scans all tracked text, so
check-all fails: `Check failed: 1 of 34 blocking guards`, `FAIL unresolved decision ID ... cited in
.agent/packet-declutter-02.md` (x2). The packet's "All 34 guards passed" is true at `3326c4d85` but not at HEAD.
Merging this would turn `main` red.
Fix: reword those lines without a `D-` token, then rerun check-all at the final commit. The same thing will catch any
packet or review that names an example ID, so a sentence in RULES §9 or the INDEX would help ("example IDs in prose:
drop the `D-` prefix").

### F2 Medium: the line-pointer relaxation can hide a deleted ruling
`tools/check-decision-index.py:84-93`. `held` and the fallback `ident not in text and stem not in text` are plain
substring tests. `D-SR.2` is a substring of `D-SR.20`..`D-SR.29`, `D-SR.1` of `D-SR.10`.., and the same holds for
every family. Planted in a scratch clone: I removed every `D-SR.2` token (not followed by a digit) from
`build-sheet-OWN-GAPS-2026-11-08.md`. The guard printed only `note ... D-SR.2 moved off ...:4777` and exited OK. So
a ruling that really vanished passes as a drifted pointer. The relaxation is acceptable for a live sheet that grows,
but only with an exact-token match.
Fix: match `re.escape(ident) + r"(?![0-9A-Za-z])"` (and likewise for the stem) in both the line and the whole-file
tests. Also add a self-test case: an ID that occurs only as a prefix of a longer ID must fail.

### F3 Medium: two standing owner rules are marked historical
O4 says the concise summary will be built from this status column, so these two rows matter.
- `owner/index-1.md:50` `owner-autonomy-2026-10-14.md`: "historical — window closed". The file's last section is
  "Owner confirmation of the standing owner-absent rule": the owner says, verbatim, "keep the owner-absent rule,
  continue". The rule is: build and fresh-review USER_REVIEW_REQUIRED slices and hold the merge for a walkthrough;
  the Architect decides only when delegated. That is a standing rule. It should be current (standing owner-absent
  rule), or split as "window historical; the rule is current".
- `owner/index-2.md:9` `owner-autonomy-2026-10-15.md`: "historical — window closed". It holds the owner's
  "If there is a internet discconnection, try in a given interval", the origin of the standing network-reconnect
  rule. It should be current for that rule.

Lower-confidence rows of the same kind, for the human read the packet already asks for:
- `owner/index-1.md:44` `owner-next-work-2026-10-13c.md` ("pay attetion to the priortization workflow") is marked
  historical, but it reads as a standing instruction.
- `owner/index-3.md:5` `owner-local-servers-authorization-2026-10-26.md`: its addendum says "From now on: start Vite
  directly ... never with `-ExecutionPolicy Bypass` or any other policy/safety override". That outlives the recapture
  batches. Mark it "historical, except the no-safety-override rule".

The other standing rules I checked are current and justified:
- DB authorization: `owner-test-db-authorization-2026-10-18`, `owner-producer-scratch-db-authorization-2026-10-24`.
- Walkthrough DB: `owner-clean-walkthrough-over-time-2026-11-13`.
- Testing: `owner-overnight-2026-11-10` (targeted tests, heavy operations batched; the Docker-restart authority).
- Review routing and fresh reviewer: `owner-review-routing-and-merge-2026-10-11`.
- Token efficiency: `owner-efficiency-2026-11-05`.
- Mechanics first: `owner-layer4-direction-feedback-2026-11-17`.
- Deferred work is a queue: `owner-deferred-is-queued-2026-11-13`.

Port 5490 appears only in coordinator text (`owner-walkthrough-in-6h-2026-11-13.md`) and is not an owner rule in any
owner file. Its "historical" status is fine. The superseded chains I followed are coherent:
- walkthrough policy, then after-W6;
- test-suite policy, then tiered, then overnight;
- claude-architect, then default-architect-claude;
- scope-backlog, then deferred-is-queued.

No owner file was edited by the branch. `git diff main -- .agent/owner-*` shows only `944b0d4fb`, the coordinator's
verbatim append of "go ahead with declutter step 2".

### F4 Low: the decision INDEX misdescribes what the parts hold
`.ai/decisions/INDEX.md:11` says `2026-10-early.md` holds "2026-10-01 to 10-09". It also holds decisions dated up to
2026-10-31, appended under the last `## 2026-10-09` heading. For example, `D-2026-10-31-scn-kobo-reserve-matters` is
at its line 911. Line 8 also omits the 10-23 amendments in `2026-10-late.md`. An agent that browses by date (as the
45 unnamed decisions require) would open the wrong file for late October.
Fix: say "2026-10-01 to 10-09 by heading, plus later decisions appended up to 10-31".

### F5 Low: range headings produce garbled index rows
In 15 `index-rulings-*` rows, a group heading such as `## D-SR.1-8 ...` was parsed as the first ID of the range. The
title then starts with the range end ("`D-SR.1` 8 Site pages on the shared date range"), and the pointer lands on the
group heading, not on the ID's own `### D-SR.1 Three classes of Site page.` (OWN-GAPS:4771). The affected IDs are
`D-SR.1`, .9, .19, .31, .40, .51, .64, .70; `D-MB.1`; `D-WARM.1`; `D-UP.1`; `D-UQFI.6`, .11, .13; `D-DATA.1`
(grep ``^- `D-[A-Z][^`]*` [0-9]``). The lookup still lands within a few lines, so this is cosmetic, but the titles
are wrong. Smaller cosmetic issues:
- a stripped-underscore title, `ARCHITECTDEMORECOMMENDATION` (`D-2026-10-02-demo-led-recommendation`);
- truncated status notes in `specs/INDEX.md:48` and `:58` ("K8c unmerge", "D-P").

### F6 Low: one partial supersession is not recorded
`2026-09.md:938` says, "This supersedes the forward-looking parts of the 2026-09-13 canonical-fidelity decision".
`.ai/decisions/index-2026-09-1.md:8` lists `D-2026-09-13-canonical-fidelity` as `live`. It should read "superseded in
part? see 2026-09.md:938". The other supersessions I followed are recorded correctly:
`D-2026-09-17-client-demo-readiness`, `D-2026-09-24-queue-resequenced-for-demo`,
`D-2026-10-11-w1-loop-and-mapping-boundaries` and the property-absent amendment.
Separately, the header's "Status is `live` unless the text says otherwise" means "not superseded by a later decision
text". It does not mean "applies under the Layer 4 direction". One sentence saying so would stop agents reading
S1-era decisions as current direction.

### F7 Low: the guards do not enforce index completeness or caps
- `tools/check-agent-workflow.ps1:24-29` requires the decisions and state INDEX files, but not `specs/INDEX.md` or
  `owner/INDEX.md`, although START_HERE and AGENTS route to both.
- Nothing fails when a new `.agent/owner-*.md` or build sheet is added without an index row. All 187 owner files and
  all 54 build sheets and specs are indexed today.
- Nothing fails when an index passes the 2k-token cap.
§5.5 places the caps in a later step, so these are notes, not gaps in this step.

### F8 Note: accepted deviations and router staleness
- The Layer 4 pack README from §4.2 step 2 is deferred because the pack is not on `main`. Recorded in the packet's
  follow-ups; accepted.
- `specs/INDEX.md` lists only `build-sheet-*` and `*-build-spec*` files. The live declutter spec
  (`repo-declutter-recommendation-2026-11-18.md`) is reached through NOW, not through the specs index.
- `.ai/NOW.md:56-58` still lists PIPE-1 as active for re-review, but `main` records it merged. This predates the
  branch, but the branch edits NOW.
- The packet's family counts (D-SR 97, D-E5 52) differ from the index (92, 51). The total of 470 matches.

## Checks run (output seen)

- `python tools/check-split-preservation.py`: `OK decisions: 4 parts, 504986 bytes vs original 504986` and
  `OK state: 138 sections in 11 area files, 525239 bytes vs original 525239`.
- My own check, independent of the author's script (ordered by each header's "part N of M"; strips line 1 plus the
  blank line 2):
  - DECISIONS: the concatenation is byte-equal to `git show 916d317f2^:.ai/DECISIONS.md` (504,986 bytes).
  - CODE_STATE: the multiset of `## ` sections equals the original's (138), with no extras, and order is preserved
    within every area file.
- Area assignment: all 138 state index rows resolve to a `## <ID>` heading in the named file. The grouping is by
  product area and wave and is sensible (for example, all W1-UX in `shell.md`; post-W6 Site-screen fixes in
  `sites.md` or `cold-ev.md`). I found no slice whose file would mislead.
- Decision index: 40 IDs sampled across every family, read at the pointer:
  - dated 2026-09 and 2026-10;
  - D-SR, D-E2, D-E3, D-E4, D-E5, D-MONEY, D-ANY (including `D-ANY.6a`), D-AW, D-DATA, D-F05, D-HON, D-I18N, D-MB,
    D-OPEN, D-PRICE, D-R3, D-R4, D-R5, D-R6, D-UI and D-UP.

  All land on the ID's text, except the range headings in F5 and the D-AW rows, which honestly point at the
  demo-plan handoff because the away log is untracked.
- State index: 15 rows spot-checked, and all 138 checked by script.
- Specs index: 15 rows checked against the sheet headers. OWN-GAPS live (NOW names it as the demo-sprint rulings
  file) and DIESEL-1 live (the handoff cites rulings through §9v and the unmerged K8c captures) are justified. 3
  tracked `.agent/*buildspec*` files are not indexed; they are requests or logs, not specs.
- Owner index: 187 of 187 owner files indexed, none twice, and 48 current, matching the INDEX list. 20+ rows read
  against their files (F3).
- Guard:
  - `python tools/check-decision-index.py` at HEAD: exit 1, F1.
  - In a scratch clone: a planted citation of two unindexed IDs in `.ai/NOW.md` gave exit 1 with both reported; a
    `git mv` of the OWN-GAPS sheet gave exit 1, `names a missing file` (250 problems).
  - Prefix-hiding plant: exit 0, F2.
  - A 2-line insert at the top of a live sheet gives 243 notes and exit 0, as designed.
  - Runtime 1.9 s, read-only (`git grep`; the self-test writes nothing). Registered blocking in
    `tools/check-all.ps1:283-285` with its self-test.
  - The decision tokens on the three active lane branches (`task/product-direction-layer4-design`,
    `task/gtm-documents`, `task/WALK-1113-build`) all resolve against these indexes, so no false block for them
    today.
- Caps (bytes/4): AGENTS 468, START_HERE 947, NOW 813 (each under 1.5k); RULES 3,141 (under 4k); implementer brief
  848; ROLE_CONFIG 1,161. Largest index parts: decisions 1,643, state 1,569, specs 1,628, owner 1,592 (each under
  2k). START_HERE, AGENTS, RULES §9 and the implementer brief point at the indexes correctly.
- Readers: no code, test or guard reads the content of `.ai/DECISIONS.md` or `.ai/CODE_STATE.md`.
  `check-agent-workflow.ps1` only requires that the files exist, and the stubs remain. The 21 registry anchors cover
  20 distinct IDs, all of which resolve in the index; `check_v69_dependency_registry.cjs` only checks that evidence
  is non-empty. `public_provenance.py:3` is a docstring.
- `pwsh -NoProfile -File tools/check-all.ps1` (with a temporary `frontend/node_modules` symlink, removed
  afterwards): 43.2 s; `Check failed: 1 of 34 blocking guards (3 advisory, 0 warned)`, only the index guard (F1).
  Every other guard passed.
- `pwsh -NoProfile -File tools/check-agent-workflow.ps1`: `Agent workflow check passed.`
- No test suite, DB, Docker or port touched. No process left running. The scratch clone is deleted.

## Residual risk not named in the packet

- The guard scans every tracked file, including `.agent/` history and reviews. Any future packet or review that
  quotes an example or typo ID blocks check-all for that lane (F1 is the first instance).
- The `file:line` pointers into OWN-GAPS, which is live, will drift into notes quickly. Without F2's fix, notes are
  exactly where a lost ID would hide.
