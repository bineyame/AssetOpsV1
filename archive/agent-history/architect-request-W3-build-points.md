# Architect request: W3-estate build-time points

You are the AssetOps Architect. The W3-estate builder finished code to your rulings (`.agent/post-W6-W3-estate-rulings.md`), on branch `task/post-W6-W3-estate` at e4e1042d; inspect it with `git show`/`git diff main...task/post-W6-W3-estate`. It raised six points. Rule each in `.agent/post-W6-W3-estate-build-rulings.md`: accept as built, or say exactly what to change.

1. **Index Finding links are never null.** `EstateFindingRow.links.finding` is a non-nullable string, and no type change was made. Unprovable cold/EV index rows still carry the old `?revision_id=` string. The frontend renders a link only when the string carries from/to/known_at; otherwise it shows plain text with "Finding detail unavailable". Portfolio `links.finding` is nullable and is null in this case. Should the index DTO become nullable, as a contract change, or is the frontend gate acceptable?
2. **No "Window cannot be read" title** on the estate roots, because they have no refusal title element. The sentence and the "Window not valid" bar are present. Add a title, or accept?
3. **Stale test.** `estateFinancials.test.tsx` `meetsMeasuredNarrowLayoutWithoutDocumentOverflow` reads old W3-02 capture JSON that includes the now-removed inner-scroll cap. The builder plans to regenerate the JSON from the recapture and revise the assertions. Confirm.
4. **Matrix cell windows.** Service and Health cells link with no window. Cold/EV Cost and Evidence cells use the Site's latest proven Evidence-row window, or the Site home if there is none. Accept, or specify?
5. **Q7 plural.** "its rows are held until then" is kept verbatim even when several Sites are named. Give the plural form.
6. **Q14 fallback.** The generic fallback in both estate refusal tables is now "The selected window is invalid." Confirm this is in scope.

Also say whether the scope_snapshot Postgres test's assumption (the fixture's cold Site has a proven Evidence window and a selected cold Finding row) is valid. Read the W3-03 fixture. Do not edit product code. Keep it tight.
