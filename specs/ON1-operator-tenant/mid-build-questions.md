# ON1 mid-build questions (RULES §4 item 7)

A question about something the spec did not fix stops only the affected part. Write it here (Q1, Q2 ...): the
section, what is stopped, what is built, and what you ask. The Architect rules in `rulings.md`. Record the count in
the packet; a count above zero is a spec-template defect to fix.

Count: **2** (reset at spec rev 2, 2026-11-20).

## Q1 (spec §2): the code for a structural refusal (answered: D-ON1.18, `ONBOARD_STRUCTURE`)

- **Section.** §2 says "an unknown or missing key is refused" at every level and gives `sites` 1 to 50, `people` 1 to
  50, `roles` 1 to 5, but names no code for an unknown or missing key, a container of the wrong JSON type, or a list
  outside its bounds. (Duplicate keys and unparsable JSON are `ONBOARD_FILE`, as built.)
- **Stopped.** Nothing: the default below is small and reversible (one code in `operator_file._strict`/`_list`).
- **Built (default).** `ONBOARD_FORMAT` ("This is not an onboarding file of version 1.") with `where` the path of
  the object or list concerned (`sites[0]`, `people[2].roles[0]`, `sites`; none at the top level). A Site field of the
  wrong type inside a well-formed Site entry is `ONBOARD_SITE_INVALID` (the Site parser judges it).
- **Ask.** Confirm `ONBOARD_FORMAT`, or name another code (for example a new `ONBOARD_STRUCTURE`).

## Q2 (spec §3.3, §7): `onboarding_open` trips the persistence guard (answered: D-ON1.17, renamed `onboarding_may_grant`)

- **Section.** §3.3 names `AccountService.onboarding_open`; §7 says `tools/checks/configuration-persistence.ps1` is not
  changed. The guard's "storage technology above the adapter layer" list holds the bare pattern `open\(`, so the line
  `def onboarding_open(self, tenant_slug: str) -> bool:` in `accounts/service.py` (a configuration package, outside
  its adapters) fails it: a false positive (no file is opened), the guard's only failure on this branch.
- **Stopped.** Only that guard result: the method keeps the spec's name, the guard is not edited, and no spacing
  trick (`def onboarding_open (`) is used to pass it (owner: never work around a safety check).
- **Built.** Everything else; the three planted violations of §7 each add their own failure to the guard.
- **Ask.** Either (a) rename the method (for example `AccountService.onboarding_grants_open`, store
  `person_grant_exists` unchanged), or (b) narrow the guard's pattern to a call not preceded by an identifier
  character (`(?<![A-Za-z0-9_])open\(`, which still catches `open(`, `os.open(` and `Path(...).open(`), a guard
  change outside §4's list. Builder's lean: (a), one line in service, its two callers and the tests.
