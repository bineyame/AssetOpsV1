/**
 * SR-5e (architect rev 9 §9.4, D-SR.10): what every Site page does with the shared date range, per Site type. This is
 * the rev 9 §9.3 table after SR-5 (with rev 10.5, 10a.5/D-SR.30, 10b.4, 10c/D-SR.39 and 10d.3/D-SR.43-44 applied).
 * Plans, packets and reviews cite the row for any Site page they touch. `shell/__tests__/siteRangeMatrix.test.tsx`
 * opens every row in the whole App and fails a route with no row, an R row whose data requests ignore the range, a D
 * row without its honest "Showing … of the range" tag on a drill-in day, and an N row that claims the range.
 *
 * - R: the page follows the range (every data read carries the range's `from`/`to`; the bar says "All pages").
 * - D: one day or hour inside the range (a drill-in); the bar names the day shown.
 * - N: not a period (configuration, a directory, one record at its own period, prices in force now); the bar says so.
 *
 * Site types are the matrix's own keys (`mini` Kobo/Kisiwa, `cold`, `ev`), not the wire values. Later slices flip their
 * own rows: SR-5c mini Dispatch D → R, SR-5d mini Financials N → R, SR-6 mini Health N → R, SR-7/8/10/11 the mini
 * Service, Renewable, Fuel and Backup subtabs D → R (their pages are not on this branch yet).
 */
export type RangeClass = "R" | "D" | "N";
export type MatrixSite = "mini" | "cold" | "ev";

export interface RangeMatrixEntry {
  /** The App route pattern (an `operatorSiteRoutes` constant's value). */
  route: string;
  /** The concrete path below `/sites/{code}` the test opens (route parameters filled). */
  path: string;
  site: MatrixSite;
  class: RangeClass;
  why: string;
  /**
   * Site data reads this page still makes without the range, each with the card that ranges it. The test allows exactly
   * these, so a new unranged read fails and a fixed one is removed from the list.
   */
  knownUnranged?: readonly { read: string; card: string }[];
  /** An N record page that declares "own period" only once its record loads (the matrix fixture refuses every read). */
  declaresOnLoad?: boolean;
  /** A legacy address that forwards to another row's page (whose row applies); the forward drops the range. */
  forwards?: boolean;
  /**
   * An R page whose `?day=` opens one day (SR-5b/5c drill-in): the test checks the bar names that day. "on-load": the
   * page names its day once the day's own read loads (the Overview board, which may serve another day), so under the
   * all-refused fixture the test checks only that the bar never says "now" (named test limit; its own test pins the day).
   */
  drillIn?: "first-render" | "on-load";
}

const ALL: readonly MatrixSite[] = ["mini", "cold", "ev"];
const S = "/sites/:siteId";

function rows(route: string, path: string, sites: readonly MatrixSite[], cls: RangeClass, why: string, extra: Partial<RangeMatrixEntry> = {}): RangeMatrixEntry[] {
  return sites.map((site) => ({ route, path, site, class: cls, why, ...extra }));
}

const EVIDENCE_GAPS = [{ read: "/evidence/rejections", card: "SR-12a" }] as const;
/** An R page whose `?day=` is a one-day drill-in (SR-5b/5c): with a day the bar names it. */
const DRILL_IN = { drillIn: "first-render" } as const;

export const RANGE_MATRIX: readonly RangeMatrixEntry[] = [
  // Overview
  ...rows(S, "", ["mini"], "R", "SR-5b: range-overview over the range; one day is the ?day= drill-in (D-SR.9)", { drillIn: "on-load" }),
  ...rows(S, "", ["cold"], "R", "the cold Overview reads the window (rev 8 8.1)"),
  ...rows(S, "", ["ev"], "R", "forwards to the EV Overview, which reads the window (rev 8 8.1)"),
  // Foundation: configuration in force (D-SR.39)
  ...rows(`${S}/foundation`, "/foundation", ALL, "N", "configuration in force, not a period (D-SR.39)"),
  ...rows(`${S}/foundation/:foundationView`, "/foundation/sld", ALL, "N", "a drawing of the configuration (D-SR.39)"),
  ...rows(`${S}/foundation/changes`, "/foundation/changes", ALL, "N", "an edit history of configuration; SR-13 OUT (D-SR.39)"),
  ...rows(`${S}/foundation/changes/:changeId`, "/foundation/changes/c1", ALL, "N", "one record (D-SR.30)"),
  ...rows(`${S}/configuration`, "/configuration", ALL, "N", "legacy address; forwards to the Foundation (configuration)", { forwards: true }),
  // Evidence
  ...rows(`${S}/evidence`, "/evidence", ["mini", "ev"], "R", "the evidence ledger reads the range (rev 10.5)", { knownUnranged: EVIDENCE_GAPS }),
  ...rows(`${S}/evidence`, "/evidence", ["cold"], "R", "the cold evidence page reads the window (rev 10.5)"),
  // Performance
  ...rows(`${S}/performance`, "/performance", ["mini"], "R", "SR-5c: Dispatch by day from range-overview; one day is the ?day= drill-in (D-SR.9)", DRILL_IN),
  ...rows(`${S}/performance`, "/performance", ["cold", "ev"], "R", "temperature / sessions read the window (rev 10b.4)"),
  ...rows(`${S}/performance/:capabilityId`, "/performance/dispatch", ["mini"], "R", "SR-5c: Dispatch by day from range-overview; one day is the ?day= drill-in (D-SR.9)", DRILL_IN),
  ...rows(`${S}/performance/:capabilityId`, "/performance/service", ["mini"], "D", "one Site-local hour of the range's last day until the SR-7 page (D-SR.59)"),
  ...rows(`${S}/performance/:capabilityId`, "/performance/renewable", ["mini"], "D", "the last 5 Site-local days of the range until the SR-8 page (D-SR.59)"),
  ...rows(`${S}/performance/:capabilityId`, "/performance/fuel", ["mini"], "D", "one hour (Kisiwa: the fuel-check nights, SR-10k) until the SR-10 page (D-SR.44)"),
  ...rows(`${S}/performance/:capabilityId`, "/performance/backup", ["mini"], "D", "one hour until the SR-11 page (D-SR.44)"),
  ...rows(`${S}/performance/:capabilityId`, "/performance/temperature", ["cold"], "R", "reads the window (rev 10b.4)"),
  ...rows(`${S}/performance/:capabilityId`, "/performance/backup", ["cold"], "R", "reads the window (rev 10b.4)"),
  ...rows(`${S}/performance/:capabilityId`, "/performance/cooling", ["cold"], "R", "reads the window (rev 10b.4)"),
  ...rows(`${S}/performance/:capabilityId`, "/performance/sessions", ["ev"], "R", "reads the window (rev 10b.4)"),
  ...rows(`${S}/performance/:capabilityId`, "/performance/availability", ["ev"], "R", "reads the window (rev 10b.4)"),
  ...rows(`${S}/performance/:capabilityId`, "/performance/energy", ["ev"], "R", "reads the window (rev 10b.4)"),
  // Findings
  ...rows(`${S}/findings`, "/findings", ALL, "R", "the Finding index reads the range (rev 10.5)"),
  ...rows(`${S}/findings/:findingId`, "/findings/f1", ALL, "N", "one Finding at its own episode (D-SR.64)"),
  ...rows(`${S}/findings/:findingId/:findingView`, "/findings/f1/analysis", ALL, "N", "one Finding at its own episode (D-SR.64)"),
  // Financials
  ...rows(`${S}/financials`, "/financials", ["mini"], "N", "prices valid now until SR-5d adds the range money (D-SR.6)"),
  ...rows(`${S}/financials`, "/financials", ["cold"], "R", "the cold Financials read the window (rev 8 8.1)"),
  ...rows(`${S}/financials`, "/financials", ["ev"], "R", "forwards to the EV Financials, which read the window (SR-4c)"),
  ...rows(`${S}/financials/assumptions`, "/financials/assumptions", ["mini", "ev"], "N", "forwards to the Site prices: prices valid now (PR-2a, D-SR.39)"),
  ...rows(`${S}/financials/assumptions`, "/financials/assumptions", ["cold"], "R", "the cold assumptions view shows range content (D-SR.66)"),
  ...rows(`${S}/financials/scenarios`, "/financials/scenarios", ALL, "R", "scenarios are computed over the range's telemetry (D-SR.44)"),
  ...rows(`${S}/financials/prices`, "/financials/prices", ALL, "N", "prices in force now; SR-14 OUT (D-SR.39)"),
  // One record (D-SR.30, D-SR.44)
  ...rows(`${S}/opportunities/:opportunityId`, "/opportunities/o1", ["mini"], "N", "one record with its own five days (D-SR.44)", { declaresOnLoad: true }),
  ...rows(`${S}/actions/:actionId`, "/actions/a1", ALL, "N", "one record (D-SR.30)", { declaresOnLoad: true }),
  ...rows(`${S}/actions/:actionId/:actionView`, "/actions/a1/verification", ALL, "N", "one record (D-SR.30)", { declaresOnLoad: true }),
  ...rows(`${S}/domain-actions/:actionId/verification`, "/domain-actions/a1/verification", ["mini"], "N", "one verification record with its own windows (D-SR.44)", { declaresOnLoad: true }),
  ...rows(`${S}/domain-actions/:actionId/fuel-verification`, "/domain-actions/a1/fuel-verification", ["mini"], "N", "one verification record with its own windows (D-SR.44)", { declaresOnLoad: true }),
  ...rows(`${S}/fuel-findings/:findingId`, "/fuel-findings/f1", ["mini"], "N", "one fuel Finding at its own night (D-SR.44)", { declaresOnLoad: true }),
  // Health
  ...rows(`${S}/health`, "/health", ["mini"], "N", "gateway contact now until the SR-6 page (D-SR.12)"),
  ...rows(`${S}/health`, "/health", ["cold", "ev"], "R", "reads the window (rev 10b.4)"),
  // Assets: configuration (D-SR.43)
  ...rows(`${S}/assets`, "/assets", ALL, "N", "Foundation configuration; condition never invented (D-SR.43)"),
  ...rows(`${S}/assets/:assetId`, "/assets/a1", ALL, "N", "Foundation configuration; condition never invented (D-SR.43)"),
  // Work
  ...rows(`${S}/work`, "/work", ALL, "R", "Actions, incidents and maintenance read the range (rev 10a.5)"),
  ...rows(`${S}/work/incidents`, "/work/incidents", ALL, "R", "reads the range (rev 10a.5)"),
  ...rows(`${S}/work/maintenance`, "/work/maintenance", ALL, "R", "reads the range (D-SR.41c)"),
  // EV pages
  ...rows(`${S}/ev`, "/ev", ["ev"], "R", "every /ev page reads the window (rev 8 8.1)"),
  ...rows(`${S}/ev/evidence`, "/ev/evidence", ["ev"], "R", "telemetry and its consequences (D-SR.44)"),
  ...rows(`${S}/ev/evidence/analysis`, "/ev/evidence/analysis", ["ev"], "R", "telemetry and its consequences (D-SR.44)"),
  ...rows(`${S}/ev/financials`, "/ev/financials", ["ev"], "R", "reads the window (rev 8 8.1)"),
  ...rows(`${S}/ev/financial-assumptions`, "/ev/financial-assumptions", ["ev"], "R", "shows range content, as the cold assumptions (D-SR.66)"),
  ...rows(`${S}/ev/financials/scenarios`, "/ev/financials/scenarios", ["ev"], "R", "scenarios over the range's telemetry (D-SR.44)"),
];
