# S1-03 side-by-side captures

Captured 2026-10-08 with `.agent/S1-03-screens/capture.mjs`: headless Chrome, 1440x900 and 390x844, first viewport (`-viewport`) and full page (`-full`). The app was served from the dev database (converted KOBO-001; KOBO-GAP-001 imported and not converted, with no reserve), backend :8010, frontend :5183, at HEAD `eabf4ca`. Mock: `frontend/mockups/v69/index.html`. No capture scrolls horizontally: scrollWidth equals clientWidth in all 16 captures.

| Manifest ID | Mock | App (KOBO-001) | Also |
|---|---|---|---|
| `foundation` | `mock-foundation-{1440,390}-{viewport,full}.png` | `app-foundation-…` (`/sites/KOBO-001/foundation`) | `app-gap-foundation-…` (KOBO-GAP-001, missing reserve) |
| `sld` | `mock-sld-…` | `app-sld-…` (`/foundation/sld`) | |
| `readiness` | `mock-readiness-…` | `app-readiness-…` (`/foundation/readiness`) | `app-gap-readiness-…` (Unknown, roles not bound, reserve not configured) |

## `foundation` → Site model

**Supported, in the mock's order:**
1. View row: Site model · Single line diagram · Readiness.
2. Status strip: Foundation vN, its effective period, "immutable stored version", binding vN with the bound-channel count, the configuration-gap count, a link to Readiness, the current or historical label, and the period selector.
3. *Configuration gaps* panel. Only when the version has gaps, e.g. KOBO-GAP-001.
4. *Configured topology* beside *Identity & operating obligations*. Topology is drawn as cards: supply chains into the bus, then the loads, using declared ratings. Identity shows Site code, name, archetype, location, timezone, critical-load priority, lifecycle, evidence mode and configuration origin.
5. *Time-valid control configuration*, with the reserve change under it.
6. *Record and inventory details*, as disclosures: version record IDs, digest and import path, superseded versions, document summary, components and ratings, declared control properties and assumptions.

**Deliberate omissions:**

| Mock content | Why it is omitted |
|---|---|
| Plant icons and the "400 V AC BUS" label | The bus is named from the Foundation; no icon set is in scope. |
| "Evidence / change" column with *Published policy* / *Review proposed change* / *Constraint evidence* / *See actual operation* links | No Evidence or change model exists in S1. |
| *Critical service* / *Productive use* labels | Not modelled. The configured critical-load priority is shown instead. |
| *Financial assumptions* note | There is no Financials surface. |
| *Change & effect* view | No intervention or change model exists. Absent, not disabled. |
| Mock values: MG-DEMO-01, Africa/Nairobi, 35%/90% SOC and other mock numbers | Not copied. Every value comes from the stored version. |

## `sld` → Single line diagram

**Supported:**
1. Status strip.
2. The configured diagram as the main visual. It is scaled to the panel at 1100 px and wider, and scrolls inside its own region when narrower.
3. *What each configured part is*: part, type, declared rating, bound channels with their role, and declared channels that are not bound.
4. *Diagram detail*, as disclosures: the diagram contents table and open review questions; topology nodes and connections; devices and the binding set's device-to-asset links, which is the D5 table.

**Deliberate omissions:**

| Mock content | Why it is omitted |
|---|---|
| Reporting / gap / not-connected dots, the *Monitoring & communication* strip, "What it reports" frequency text | No accepted evidence or source health exists until S2. Node slots read "Awaiting runtime/evidence". |
| Breaker and kWh-meter glyphs | Not declared in the Foundation topology. |
| *Site evidence* link | Moved to Readiness, where claim readiness on Evidence is linked. |

## `readiness` → Readiness

**Supported:**
1. Status strip.
2. *Configuration readiness*: a verdict block (Ready to report / Incomplete / Unknown, with a sentence), four configuration counts (required roles configured, Foundation gaps, binding set, declared channels not bound), *What is missing*, Foundation gaps, and the meaning statement.
3. *Role coverage* table.
4. *Signal bindings*: binding set and period, the channel table with Binding IDs, the binding set record behind a disclosure, unbound channels, and *Change the binding set*.
5. *Registered gateway and sources*: "registered, awaiting credentials, not sending data", with the sources behind a disclosure.
6. *Acquisition details*: snapshot SHA-256, schema, pinned Foundation and binding record IDs, the access statement, and *Download snapshot*.
7. A scope note linking Site Evidence.

**Deliberate omissions:**

| Mock content | Why it is omitted |
|---|---|
| *Gateway status* (Online, availability, completeness, clock and delivery, timeline) | No gateway contact exists until S2. A pending gateway is never shown as connected. |
| *Connected sources* chips | Same reason as *Gateway status*. |
| *Effect on readiness and confidence* | No evidence exists. |
| Readiness and commissioning evidence: *Confirmed* column, field verification, owners, *Raise action* | No commissioning workflow or Work surface exists. |
| *Needs review* verdict wording and mock area cards (Definition / Topology / Specifications / Controls) | Replaced by the S1-02 configuration verdict and configuration counts. |
