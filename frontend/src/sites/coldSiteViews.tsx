import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { siteTime } from "./siteTime";

import {
  AttentionList,
  Badge,
  Breadcrumbs,
  type Crumb,
  CausalTimeline,
  DataTable,
  Disclosure,
  KeyValues,
  MetricCard,
  MetricCards,
  Notice,
  Panel,
  SITE_SCREEN_DESCRIPTIONS,
  SitePageHeader,
  StatusBar,
  type TimelineEvent,
} from "../ui";
import {
  type ColdAssessmentClient,
  type ColdBackupRead,
  type ColdRead,
  type ColdStepRead,
  type ColdTemperatureRead,
  type ColdWindowQuery,
  type ColdFindingsRead,
  coldWindowSearch,
} from "./coldAssessmentClient";
import type {
  ColdAnalysisRead,
  ColdAssumptionsRead,
  ColdCapability,
  ColdEvidenceRead,
  ColdOverviewRead,
  ColdSiteClient,
  ColdSource,
} from "./coldSiteClient";
import { ADVERSE, COLD_ASSESSMENT_LOADING, RUNNING, outcomeText, refusalText } from "./ColdAssessmentViews";
import { ColdTemperatureChart } from "./assessmentGraphics";
import { selectedClassification } from "./sourceProvenance";
import { claimWord, classificationWord, plainCode, plainLimitation, reasonWord, STEP_LABELS } from "./coldAssessmentWords";
import { roleLabel } from "./ColdFoundationViews";
import { NOT_ASSESSED, NOT_RECORDED, date, dayHm, decimal, degreeMinutes, hm, windowText } from "./coldFormat";
import "./w2-cold-site.css";

/*
 * W2-04 commit 4: the five cold Site screens of a COLDCHAIN Site in their exact v69 panel slots
 * (`.agent/W2-04-build-spec.md` "v69 panel contract and UI", "Final Run-5 Architect rulings" and its
 * "Commit-4 copy ledger"; `D-2026-10-17-mockup-layout-spec`):
 *
 *   cold                    1 What happened · power → cooling → product conditions, 2 Chamber temperature,
 *                           3 Needs attention, 4 Bounded money consequence, 5 Next step
 *   cold-evidence           1 What we can conclude now, 2 Data sources · data quality, not equipment condition,
 *                           3 Most useful next evidence
 *   cold-evidence-analysis  1 Accepted records behind the conclusions, 2 How a claim limit is set
 *   cold-financials         1 What happened → what it means in money, 2 Assumptions in use, 3 Not included
 *   cold-assumptions        1 Financial assumptions
 *
 * Every visible string is the ledger's; dynamic values come only from the selected read. A refused or
 * unavailable read keeps every panel and states the refusal inside it; no mock value is a fallback.
 */

export type ColdSiteView = "overview" | "evidence" | "analysis" | "financials" | "assumptions";

export const COLD_SITE_HEADING_ID = "cold-site-heading";
export const NO_COLD_ASSESSMENT = "No cold assessment for this window";
export const SOURCE_FORBIDDEN = "Source details are not available for this Site";
export const COLD_SITE_UNAVAILABLE = "Cold Site data is temporarily unavailable";

/** The UI route bases (no query) the cold Site screens link to; the shell builds them. */
export interface ColdSiteRoutes {
  overview: string;
  evidence: string;
  financials: string;
  assumptions: string;
  temperature: string;
  backup: string;
  cooling: string;
  health: string;
  findings: string;
  finding: (findingId: string) => string;
  foundation: string;
  /** post-W6 W2-cold R256: the Foundation single line diagram view. */
  sld: string;
  /** post-W6 W2-cold R254 (Q8): cold Work › Maintenance. */
  workMaintenance: string;
}

/* ---------- words ---------- */

/** Copy-source closure: the source role is the sole source of "What it provides" and of missing-role names. */
const ROLE_PROVIDES: Record<string, string> = {
  chamber_temperature: "Chamber temperature",
  grid_power_event: "Grid event",
  backup_start_event: "Start request and result",
  generator_state: "Generator state",
  transfer_result: "Transfer position",
  backup_bus_state: "Bus voltage",
  compressor_state: "Compressor state",
  door_event: "Door and loading context",
};
const roleName = (role: string) => ROLE_PROVIDES[role] ?? `Configured role: ${roleLabel(role)}`;

const CONTACT_WORDS: Record<string, string> = {
  RECENT: "Recent source contact",
  STALE: "Last source contact is old",
  NEVER: "No source contact recorded",
  UNKNOWN: "Source contact unknown",
};

const STEP_ORDER = ["GRID", "START_REQUEST", "START_RESULT", "GENERATOR", "TRANSFER", "BUS", "COMPRESSOR", "PROBE"];
const STEP_CHIP: Record<string, string> = { OBSERVED: "Observed", MISSING: "Missing", CONTRADICTORY: "Contradictory" };

const CURRENTNESS_SENTENCE: Record<string, string> = {
  PENDING_RECOMPUTE: "New evidence is waiting to be assessed",
  HISTORICAL: "Earlier evidence cutoff",
  STALE_SOURCE: "Latest usable probe is more than 10 minutes before this window ended",
};

/** The four capability rows of `cold-evidence` panel 1, in mock order, with their Q-R1 capability pairs. */
const CAP_ROWS = [
  { key: "temperature", label: "Temperature compliance", claims: ["TEMPERATURE_POINT", "EXCURSION_BOUNDS"], next: "evidence" },
  { key: "backup", label: "Backup response", claims: ["BACKUP_START_RESULT", "TRANSFER_POSITION"], next: "evidence" },
  { key: "cooling", label: "Cooling recovery", claims: ["COOLING_RESPONSE"], next: "evidence" },
  { key: "exposure", label: "Product exposure", claims: ["PRODUCT_EXPOSURE"], next: "financials" },
] as const;
type RowChip = "Full" | "Limited" | "None" | "Contradictory";

const SAY: Record<RowChip, string> = {
  Full: "Selected records support this claim for the covered window.",
  Limited: "Selected records support only part of this claim.",
  None: "This claim is not established from the selected records.",
  Contradictory: "Selected records contradict one another.",
};

/**
 * The six mock source rows of `cold-evidence` panel 2 in mock order (Run-7 exact source-to-mock-row placement).
 * `roles` populate the closed cells; `other` reports appear only in that row's `Source details`, identified by
 * `OTHER_SOURCE_NAME`, and never populate the closed cells or establish the named mock device.
 */
const SOURCE_ROWS: { label: string; roles: string[]; undeclared?: string; other?: { heading: string; roles: string[] } }[] = [
  { label: "Chamber probe", roles: ["chamber_temperature"], other: { heading: "Other temperature context", roles: ["ambient_temperature", "manual_temperature"] } },
  {
    label: "Inverter-charger + battery",
    roles: [],
    undeclared: "No inverter or battery source declared",
    other: { heading: "Other power-path reports", roles: ["grid_state", "grid_power_event", "backup_bus_state"] },
  },
  { label: "Generator controller", roles: ["backup_start_event", "generator_state"] },
  { label: "Compressor meter", roles: ["compressor_state", "compressor_power"] },
  { label: "Transfer switch", roles: ["transfer_result"] },
  { label: "Loading / door log", roles: ["door_event"] },
];
/**
 * Run-8 closed-panel compaction: short navigation labels for the closed `Data sources` table, by mock row. The full
 * role names, quality, contact and every affected capability stay in `Source details`.
 */
const CLOSED_SOURCE: Record<string, { what: string; primary: string[]; affects: string }> = {
  "Chamber probe": { what: "Chamber temperature", primary: ["chamber_temperature"], affects: "Temperature" },
  "Generator controller": { what: "Start result", primary: ["backup_start_event"], affects: "Backup" },
  "Compressor meter": { what: "Compressor state", primary: ["compressor_state"], affects: "Cooling" },
  "Transfer switch": { what: "Transfer position", primary: ["transfer_result"], affects: "Backup" },
  "Loading / door log": { what: "Door/loading context", primary: ["door_event"], affects: "Temperature · cooling" },
};
const OTHER_SOURCE_NAME: Record<string, string> = {
  grid_state: "Grid meter",
  grid_power_event: "Grid meter",
  backup_bus_state: "AC bus",
  ambient_temperature: "Ambient probe",
  manual_temperature: "Manual room log",
};

/** W2-F S1: the product claim's required basis, listed as requirements, never as accepted records. */
const PRODUCT_REQUIRED_BASIS = "Product identity; stock quantity and unit value; currency; reviewed product response rule";

const pad = (n: number) => String(n).padStart(2, "0");
/**
 * The Site-local `Measured` time (`HH:MM:SS`), while data stays UTC. post-W6 W2-EV: takes the Site timezone (shared
 * signature; `siteTime` in `./siteTime` gives the zone label, exact UTC and a cross-day date). The default keeps the
 * earlier East Africa Time behaviour for callers not yet passing a zone.
 */
export function eatTime(value: string | null | undefined, timeZone: string | null = "Africa/Addis_Ababa", reference?: string | null): string | null {
  return siteTime(value, timeZone, reference)?.text ?? null;
}
const utc = (value: string | null | undefined) => (date(value) === null ? NOT_RECORDED : `${dayHm(value)} UTC`);
const limitText = (value: string | null | undefined) => (value ? plainLimitation(value) : null);

/* ---------- links ---------- */

function withQuery(base: string, params: URLSearchParams): string {
  const text = params.toString();
  return text === "" ? base : `${base}?${text}`;
}

/** The UI address of a selected read's API link, keeping its exact `from`, `to`, `known_at` (or `at`). */
export function coldUiHref(api: string | null | undefined, routes: ColdSiteRoutes): string | null {
  if (api === null || api === undefined) return null;
  const match = /^\/api\/sites\/[^/?]+\/cold\/([^?]*)(?:\?(.*))?$/.exec(api);
  if (match === null) return null;
  const suffix = match[1];
  const params = new URLSearchParams(match[2] ?? "");
  const finding = /^findings\/([^/]+)$/.exec(suffix);
  if (finding !== null) return withQuery(routes.finding(decodeURIComponent(finding[1])), params);
  const bases: Record<string, string> = {
    overview: routes.overview,
    evidence: routes.evidence,
    financials: routes.financials,
    "financial-assumptions": routes.assumptions,
    temperature: routes.temperature,
    "backup-chain": routes.backup,
    cooling: routes.cooling,
    health: routes.health,
    findings: routes.findings,
    foundation: routes.foundation,
  };
  if (suffix === "evidence/analysis") {
    params.set("view", "analysis");
    return withQuery(routes.evidence, params);
  }
  return suffix in bases ? withQuery(bases[suffix], params) : null;
}

/** A route of this Site at the read's resolved selection. */
export function selected(base: string, window: ColdWindowQuery, view?: "analysis"): string {
  const params = new URLSearchParams(coldWindowSearch(window).slice(1));
  if (view !== undefined) params.set("view", view);
  return withQuery(base, params);
}

function ToLink({ href, children, data }: { href: string | null; children: ReactNode; data?: Record<string, string> }) {
  return href === null ? (
    <span className="cold-site-noop" {...data}>
      No linked page for this item
    </span>
  ) : (
    <Link to={href} {...data}>
      {children}
    </Link>
  );
}

/* ---------- reads ---------- */

function useColdRead<T>(load: () => Promise<ColdRead<T>>, key: string): ColdRead<T> | null {
  const [state, setState] = useState<{ key: string; value: ColdRead<T> } | null>(null);
  useEffect(() => {
    let active = true;
    void load().then((value) => {
      if (active) setState({ key, value });
    });
    return () => {
      active = false;
    };
    // `load` is rebuilt every render; the key names what it reads.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  return state !== null && state.key === key ? state.value : null;
}

const value = <T,>(read: ColdRead<T> | null): T | null => (read !== null && read.status === "loaded" ? read.value : null);
const isSelected = (read: { currentness: { watermark?: { assessment_revision_ids?: string[] } } }) =>
  (read.currentness.watermark?.assessment_revision_ids?.length ?? 0) > 0;

/** The in-panel statement for a read that did not load, or null when it loaded. */
export interface Refusal {
  sentence: string;
  retry: boolean;
  key: string;
  /** Ruling 5: the strip chip names the refusal (a 403/404/503 is never called a window error). */
  title?: string;
}
function refusalOf(read: ColdRead<unknown> | null): Refusal | null {
  if (read === null || read.status === "loaded") return null;
  const title = refusalText(read).title;
  if (read.status === "refused" && read.httpStatus === 403) return { sentence: SOURCE_FORBIDDEN, retry: false, key: "forbidden", title };
  if (read.status === "unavailable" || read.httpStatus === 503) return { sentence: COLD_SITE_UNAVAILABLE, retry: true, key: "unavailable", title };
  return { sentence: refusalText(read).body, retry: false, key: refusalText(read).key, title };
}

function Gap({ id, children }: { id: string; children: ReactNode }) {
  return (
    <p className="not-available-yet v69-chart-note" data-panel-gap={id}>
      {children}
    </p>
  );
}

function RefusedGap({ id, refusal, onRetry }: { id: string; refusal: Refusal; onRetry?: () => void }) {
  return (
    <>
      <Gap id={id}>{refusal.sentence}</Gap>
      {refusal.retry && onRetry !== undefined ? (
        <p className="cold-panel-link">
          <button type="button" className="button" onClick={onRetry} data-cold-retry>
            Retry
          </button>
        </p>
      ) : null}
    </>
  );
}

/* ---------- capability rows ---------- */

function rowChip(caps: ColdCapability[], claims: readonly string[]): RowChip {
  const states = claims.map((c) => caps.find((x) => x.claim === c)?.state ?? "UNAVAILABLE");
  if (states.includes("CONTRADICTORY")) return "Contradictory";
  if (states.every((s) => s === "SUPPORTED")) return "Full";
  if (states.every((s) => s === "UNAVAILABLE")) return "None";
  return "Limited";
}

function rowMissing(caps: ColdCapability[], claims: readonly string[]): string[] {
  const out: string[] = [];
  for (const claim of claims) for (const r of caps.find((x) => x.claim === claim)?.missing_roles ?? []) if (!out.includes(r)) out.push(r);
  return out;
}

function chipCounts(caps: ColdCapability[]) {
  const chips = CAP_ROWS.map((r) => rowChip(caps, r.claims));
  const count = (c: RowChip) => chips.filter((x) => x === c).length;
  return { n: CAP_ROWS.length, full: count("Full"), limited: count("Limited"), none: count("None"), contradictory: count("Contradictory") };
}

function countSentence(caps: ColdCapability[]): string {
  const c = chipCounts(caps);
  return `${c.n} capabilities · ${c.full} full · ${c.limited} limited · ${c.none} none${c.contradictory > 0 ? ` · ${c.contradictory} contradictory` : ""} · no single score`;
}

/* ---------- shared frame ---------- */

export interface ColdSiteFrameProps {
  view: ColdSiteView;
  siteId: string;
  siteName: string;
  mode: string | null;
  window: ColdWindowQuery;
  client: ColdSiteClient;
  assessment: ColdAssessmentClient;
  routes: ColdSiteRoutes;
  tabs: ReactNode;
  /** The Financials subtab row for `financials` / `assumptions`, from the shell. */
  sections?: ReactNode;
  parentTrail: Crumb[];
}

const DESCRIPTION: Record<ColdSiteView, string> = {
  overview: SITE_SCREEN_DESCRIPTIONS.mini,
  evidence: SITE_SCREEN_DESCRIPTIONS.evidence,
  analysis: SITE_SCREEN_DESCRIPTIONS["evidence-analysis"],
  financials: SITE_SCREEN_DESCRIPTIONS.financials,
  assumptions: SITE_SCREEN_DESCRIPTIONS.assumptions,
};
const SCREEN: Record<ColdSiteView, string> = {
  overview: "cold",
  evidence: "cold-evidence",
  analysis: "cold-evidence-analysis",
  financials: "cold-financials",
  assumptions: "cold-assumptions",
};
const CRUMB: Record<ColdSiteView, Crumb[]> = {
  overview: [],
  evidence: [{ label: "Evidence" }],
  analysis: [{ label: "Evidence" }, { label: "Analysis" }],
  financials: [{ label: "Financials" }],
  assumptions: [{ label: "Financials" }, { label: "Assumptions" }],
};

function Subtabs({ view, routes, window }: { view: ColdSiteView; routes: ColdSiteRoutes; window: ColdWindowQuery }) {
  if (view !== "evidence" && view !== "analysis") return null;
  const items: [string, string, string][] = [
    ["evidence", "Overview", selected(routes.evidence, window)],
    ["analysis", "Analysis", selected(routes.evidence, window, "analysis")],
  ];
  return (
    <nav className="site-tabs site-subtabs" aria-label="Evidence sections">
      <ol className="site-tabs__list">
        {items.map(([id, label, href]) => (
          <li className="site-tabs__item" key={id}>
            <Link className="site-tabs__link" to={href} data-cold-subtab={id} aria-current={id === view ? "page" : undefined}>
              {label}
            </Link>
          </li>
        ))}
      </ol>
    </nav>
  );
}

/**
 * Run-7 status/date ruling: the selected half-open UTC window and the evidence cutoff in the Site date-bar slot,
 * immediately below the tabs (no shared date-bar component exists to carry a sub-day window and cutoff).
 * `extra` carries the pending/historical sentence on `cold-assumptions`, which has no status strip.
 */
export function SelectedWindowBar({ read, extra }: { read: { window: ColdWindowQuery } | null; extra?: string | null }) {
  if (read === null) return null;
  return (
    <p className="site-date-bar" data-cold-date-bar>
      <span className="site-date-bar__window">Selected window {windowText(read.window.from, read.window.to)}</span>
      <span className="site-date-bar__cutoff">
        Selected evidence through {utc(read.window.known_at)}
        {extra ? ` · ${extra}` : null}
      </span>
    </p>
  );
}
/**
 * W2-F M3/N7: a refused read keeps the date line from the requested window, unless the window itself is invalid
 * (malformed dates are not echoed). The cutoff is shown only when one was requested.
 */
export function RequestedWindowBar({ window, refusal }: { window: ColdWindowQuery; refusal: Refusal }) {
  if (refusal.key === "invalid-window" || date(window.from) === null || date(window.to) === null) return null;
  return (
    <p className="site-date-bar" data-cold-date-bar data-cold-date-bar-requested>
      <span className="site-date-bar__window">Selected window {windowText(window.from, window.to)}</span>
      {date(window.known_at) === null ? null : <span className="site-date-bar__cutoff">Selected evidence through {utc(window.known_at)}</span>}
    </p>
  );
}
export const WINDOW_CANNOT_BE_READ = "Window cannot be read";
/**
 * W2-F M3: the refused-window status strip; `chip` fills the strip's own chip slot where the screen has one.
 * Ruling 5: `title` names a non-window refusal (403/404/503) by its own title; the default is the window title.
 */
export function RefusedStrip({ label, chip, title }: { label: string; chip?: string; title?: string }) {
  return (
    <StatusBar label={label} data={{ "data-cold-refused-strip": "" }}>
      {chip === undefined ? null : (
        <>
          <Badge tone="neutral">{chip}</Badge>{" "}
        </>
      )}
      <Badge tone="neutral">{title ?? WINDOW_CANNOT_BE_READ}</Badge>
    </StatusBar>
  );
}
/** W2-F M3: the screen's tile slots, each `Not assessed`, so a refusal is never read as a zero. */
export function RefusedTiles({ label, cards, columns }: { label: string; cards: string[]; columns?: 5 }) {
  return (
    <MetricCards columns={columns} label={label}>
      {cards.map((c) => (
        <MetricCard key={c} label={c} value={NOT_ASSESSED} tone="muted" word data={{ "data-cold-refused-card": c }} />
      ))}
    </MetricCards>
  );
}
const stateSentence = (read: { currentness: { state: string } } | null) =>
  read === null ? null : (CURRENTNESS_SENTENCE[read.currentness.state] ?? null);

export function ColdSiteFrame(props: ColdSiteFrameProps) {
  const { view, siteId, window } = props;
  const [attempt, setAttempt] = useState(0);
  const retry = () => setAttempt((n) => n + 1);
  return (
    <main aria-labelledby={COLD_SITE_HEADING_ID} data-cold-view={SCREEN[view]}>
      <Breadcrumbs trail={[...props.parentTrail, ...CRUMB[view]]} />
      <SitePageHeader siteName={props.siteName} siteId={siteId} mode={props.mode} description={DESCRIPTION[view]} headingId={COLD_SITE_HEADING_ID} />
      {props.tabs}
      <Subtabs view={view} routes={props.routes} window={window} />
      {view === "financials" || view === "assumptions" ? (props.sections ?? null) : null}
      {view === "overview" ? (
        <OverviewScreen {...props} attempt={attempt} retry={retry} />
      ) : view === "evidence" ? (
        <EvidenceScreen {...props} attempt={attempt} retry={retry} />
      ) : view === "analysis" ? (
        <AnalysisScreen {...props} attempt={attempt} retry={retry} />
      ) : view === "financials" ? (
        <FinancialsScreen {...props} attempt={attempt} retry={retry} />
      ) : (
        <AssumptionsScreen {...props} attempt={attempt} retry={retry} />
      )}
    </main>
  );
}

type ScreenProps = ColdSiteFrameProps & { attempt: number; retry: () => void };
const keyOf = (p: ScreenProps, name: string) => `${name}|${p.siteId}|${p.window.from ?? ""}|${p.window.to ?? ""}|${p.window.known_at ?? ""}|${p.attempt}`;

/* ---------- cold (Overview) ---------- */

function overviewStateChip(o: ColdOverviewRead): string {
  if (o.status.state === "OBSERVED_EXCURSION" || o.backup_summary.observed_failure > 0) return "Degraded";
  if (o.status.state === "CONTRADICTORY") return "Contradictory";
  if (o.status.state === "NO_EXCURSION_OBSERVED") return "No excursion observed";
  return "Unknown";
}

function OverviewCards({ o, evidence, routes }: { o: ColdOverviewRead; evidence: ColdEvidenceRead | null; routes: ColdSiteRoutes }) {
  const t = o.temperature_summary;
  const proved = o.status.state === "OBSERVED_EXCURSION" && (o.status.claim_level === "OBSERVED" || o.status.claim_level === "BOUNDED");
  const gap = o.needs_attention.some((n) => n.code === "COLD_PROBE_GAP");
  const tempChip = proved ? "Needs attention" : gap ? "Limited" : o.status.state === "NO_EXCURSION_OBSERVED" ? "No excursion observed" : "Unknown";
  const policy =
    o.objective.policy_low_deg_c !== null && o.objective.policy_high_deg_c !== null
      ? `policy ${decimal(o.objective.policy_low_deg_c)}–${decimal(o.objective.policy_high_deg_c)} °C`
      : null;
  // Run-7 card copy: each unavailable clause is omitted rather than rendered as null, zero or a placeholder.
  const coverage =
    t.coverage.known_points === null || t.coverage.expected_points === null ? null : `coverage ${t.coverage.known_points} / ${t.coverage.expected_points} readings`;
  const tempNote =
    t.latest_deg_c === null
      ? "No chamber reading for this window"
      : [`${t.episode_count} ${t.episode_count === 1 ? "excursion" : "excursions"}`, `latest ${decimal(t.latest_deg_c)} °C`, policy, coverage].filter(Boolean).join(" · ");
  const b = o.backup_summary;
  const backupChip = b.observed_failure > 0 ? "Degraded" : b.observed_success > 0 ? "Observed start" : "Unknown";
  // Run-7 card copy: actual zero counts only from an assessed selected summary.
  const backupAssessed = isSelected(o) && b.as_of !== null;
  const backupNote = !backupAssessed
      ? "Backup result not observed"
      : `${b.attempts} ${b.attempts === 1 ? "start attempt" : "start attempts"} · ${b.observed_success} started · ${b.observed_failure} failed`;
  // W2-F S2: cooling recovery is never supported in W2 (no ordered-recovery assessment), so no supported chip exists.
  const coolingChip = ({ LIMITED: "Limited", CONTRADICTORY: "Contradictory" } as Record<string, string>)[o.cooling.state] ?? "Unknown";
  const caps = evidence?.capabilities ?? [];
  // The same row-based rule as the Evidence status chip (Run-7), so Overview and Evidence agree.
  const evidenceChip = evidenceState(caps);
  // R254: plain labels; each card's own `View detail →` link (mock 539), at the read's selected window.
  const detail = (key: string, href: string | null) =>
    href === null ? undefined : (
      <Link to={href} data-cold-card-link={key}>
        View detail →
      </Link>
    );
  return (
    <MetricCards columns={5} label="Cold room conditions">
      <MetricCard label="Temperature" value={tempChip} note={tempNote} tone={proved ? "amber" : "muted"} assessment data={{ "data-cold-card": "temperature" }} link={detail("temperature", coldUiHref(o.links.temperature, routes))} />
      <MetricCard label="Backup" value={backupChip} note={backupNote} tone={b.observed_failure > 0 ? "red" : "muted"} assessment data={{ "data-cold-card": "backup" }} link={detail("backup", coldUiHref(o.links.backup, routes))} />
      <MetricCard
        label="Cooling"
        value={coolingChip}
        note={`${o.cooling.text} · Recovery comparison not assessed`}
        tone="muted"
        assessment
        data={{ "data-cold-card": "cooling" }}
        link={detail("cooling", selected(routes.cooling, o.window))}
      />
      {/* Q8: the overview read carries no maintenance summary; the cases are listed under Work. */}
      <MetricCard
        label="Maintenance"
        value="Not summarised here"
        note="Maintenance cases are listed under Work"
        tone="muted"
        assessment
        data={{ "data-cold-card": "maintenance" }}
        link={detail("maintenance", selected(routes.workMaintenance, o.window))}
      />
      <MetricCard
        label="Evidence"
        link={detail("evidence", coldUiHref(o.links.evidence, routes))}
        value={evidenceChip}
        note={caps.length === 0 ? "Evidence coverage not assessed" : countSentence(caps)}
        tone="muted"
        assessment
        data={{ "data-cold-card": "evidence" }}
      />
    </MetricCards>
  );
}

/**
 * R255 (Q9): the overview strip omits each step's outcome, so an observed step is joined to the selected backup-chain
 * step with the same accepted record (`evidence_id`): `{stepLabel} · {outcomeText}`, danger on an adverse outcome and
 * ok on a running one. An unmatched step keeps its state label and neutral tone.
 */
function stripEvents(o: ColdOverviewRead, backup: ColdBackupRead | null): TimelineEvent[] {
  const steps = [...o.causal_strip].sort((a, b) => STEP_ORDER.indexOf(a.step) - STEP_ORDER.indexOf(b.step));
  const byEvidence = new Map<string, ColdStepRead>();
  for (const chain of backup?.chains ?? []) for (const step of chain.steps) if (step.evidence_id !== null && !byEvidence.has(step.evidence_id)) byEvidence.set(step.evidence_id, step);
  return steps.map((s) => {
    const name = STEP_LABELS[s.step] ?? plainCode(s.step);
    const match = s.state === "OBSERVED" && s.evidence_id !== null ? byEvidence.get(s.evidence_id) : undefined;
    const outcome = match === undefined ? null : outcomeText(match);
    const known = match?.outcome ?? null;
    return {
      key: s.step,
      // UTC like the chamber chart beside it; only the Analysis `Measured` column is in the Site timezone.
      time: s.at === null ? "—" : `${hm(s.at)} UTC`,
      title: outcome !== null ? `${name} · ${outcome}` : `${name} · ${STEP_CHIP[s.state] ?? plainCode(s.state)}`,
      detail: s.state === "MISSING" ? `No accepted ${name.toLowerCase()} report for this chain` : (limitText(s.limitation) ?? undefined),
      tone:
        s.state === "OBSERVED"
          ? known !== null && ADVERSE.test(known)
            ? "danger"
            : known !== null && RUNNING.test(known)
              ? "ok"
              : undefined
          : s.state === "CONTRADICTORY"
            ? "danger"
            : "gap",
    };
  });
}

function OverviewScreen(p: ScreenProps) {
  const overview = useColdRead(() => p.client.getOverview(p.siteId, p.window), keyOf(p, "o"));
  const evidence = useColdRead(() => p.client.getEvidence(p.siteId, p.window), keyOf(p, "e"));
  const temperature = useColdRead(() => p.assessment.getTemperature(p.siteId, p.window), keyOf(p, "t"));
  const backupChain = useColdRead(() => p.assessment.getBackupChain(p.siteId, p.window), keyOf(p, "b"));
  if (overview === null || evidence === null || temperature === null || backupChain === null) return <p>{COLD_ASSESSMENT_LOADING}</p>;
  const o = value(overview);
  const refused = refusalOf(overview);
  const none = o !== null && !isSelected(o);
  const firstFinding = o?.findings.items.find((f) => f.link !== null) ?? null;
  // Run-7: the Next step is the first ordered attention item with a real destination, with that destination's label.
  const next = o?.needs_attention.find((n) => coldUiHref(n.link, p.routes) !== null) ?? null;
  const policyNote =
    o !== null && o.objective.policy_low_deg_c !== null && o.objective.policy_high_deg_c !== null
      ? `Policy band ${decimal(o.objective.policy_low_deg_c)}–${decimal(o.objective.policy_high_deg_c)}°C. Gaps between accepted readings remain unmeasured.`
      : "Chamber temperature policy not declared for this window";
  const temp: ColdTemperatureRead | null = value(temperature);
  const tempRefused = refusalOf(temperature);
  const money = o?.consequence_summary;
  const attentionLabel = (link: string | null): string =>
    link === null ? "No linked page for this item" : link.includes("/cold/findings/") ? "Open Finding →" : link.includes("/cold/backup-chain") ? "Performance › Backup →" : "Evidence →";
  return (
    <>
      {o === null ? (
        refused === null ? null : (
          <>
            <RequestedWindowBar window={p.window} refusal={refused} />
            <RefusedStrip label="Cold room state" title={refused.title} />
            <RefusedTiles label="Cold room conditions" columns={5} cards={["Temperature", "Backup", "Cooling", "Maintenance", "Evidence"]} />
          </>
        )
      ) : (
        <>
          <SelectedWindowBar read={o} />
          <StatusBar label="Cold room state" action={<ToLink href={coldUiHref(o.links.evidence, p.routes)}>Inspect evidence</ToLink>}>
            <Badge tone="neutral">{overviewStateChip(o)}</Badge>{" "}
            <Badge tone="neutral">{o.status.claim_level === null ? "Confidence: Unknown" : `Confidence: ${claimWord(o.status.claim_level)}`}</Badge>{" "}
            <Badge tone="neutral">{o.consequence_summary.overlap_group !== null ? "Potential product exposure" : "Product exposure not established"}</Badge>
            {stateSentence(o) === null ? null : ` ${stateSentence(o)}`}
          </StatusBar>
          <p className="v69-objective" data-cold-objective>
            {o.objective.text}
          </p>
          <OverviewCards o={o} evidence={value(evidence)} routes={p.routes} />
        </>
      )}
      <Panel
        heading="What happened · power → cooling → product conditions"
        headingId="cold-site-what-happened-heading"
        description={o === null ? undefined : "No incident recorded"}
        actions={firstFinding === null ? undefined : <ToLink href={coldUiHref(firstFinding.link, p.routes)}>Open Finding →</ToLink>}
      >
        {refused !== null ? (
          <RefusedGap id="cold-site-what-happened" refusal={refused} onRetry={p.retry} />
        ) : none ? (
          <Gap id="cold-site-what-happened">{NO_COLD_ASSESSMENT}</Gap>
        ) : o!.causal_strip.length === 0 ? (
          <p className="prose">The power-to-cooling sequence is not established for this window.</p>
        ) : (
          <>
            <CausalTimeline events={stripEvents(o!, value(backupChain))} label="Power to cooling sequence" />
            <p className="prose">The steps above are based on the selected accepted records. Missing steps remain unobserved.</p>
          </>
        )}
      </Panel>
      <div className="panel-pair">
        <Panel
          heading="Chamber temperature"
          headingId="cold-site-temperature-heading"
          description="Operating conditions, not an inventory-loss model"
          actions={
            <Link to={p.routes.sld} data-cold-sld-link>
              Single line diagram →
            </Link>
          }
        >
          {refused !== null ? (
            <RefusedGap id="cold-site-temperature" refusal={refused} />
          ) : none ? (
            <Gap id="cold-site-temperature">{NO_COLD_ASSESSMENT}</Gap>
          ) : tempRefused !== null ? (
            <RefusedGap id="cold-site-temperature" refusal={tempRefused} />
          ) : temp === null || temp.points.length === 0 ? (
            <Gap id="cold-site-temperature">No chamber readings for this window</Gap>
          ) : (
            <>
              <ColdTemperatureChart read={temp} label={`Chamber temperature, ${windowText(temp.window.from, temp.window.to)}, with the policy band`} />
              <p className="v69-chart-note">{policyNote}</p>
            </>
          )}
        </Panel>
        <Panel heading="Needs attention" headingId="cold-site-attention-heading">
          {refused !== null ? (
            <RefusedGap id="cold-site-attention" refusal={refused} />
          ) : none ? (
            <Gap id="cold-site-attention">{NO_COLD_ASSESSMENT}</Gap>
          ) : o!.needs_attention.length === 0 ? (
            <Gap id="cold-site-attention">No recorded need for attention in this window</Gap>
          ) : (
            <AttentionList
              label="Needs attention"
              items={o!.needs_attention.map((n, i, all) => ({
                key: n.code,
                title: n.text,
                // R256: a limitation shared by several items is shown once, on the first item that carries it.
                body: all.slice(0, i).some((m) => limitText(m.limitation) === limitText(n.limitation)) ? "" : (limitText(n.limitation) ?? ""),
                // Run-7: a null destination shows noninteractive "No linked page for this item".
                action: (
                  <p className="cold-panel-link">
                    <ToLink href={coldUiHref(n.link, p.routes)} data={{ "data-attention-link": n.code }}>
                      {attentionLabel(n.link)}
                    </ToLink>
                  </p>
                ),
              }))}
            />
          )}
        </Panel>
      </div>
      <div className="panel-pair">
        <Panel heading="Bounded money consequence" headingId="cold-site-money-heading">
          {refused !== null ? (
            <RefusedGap id="cold-site-money" refusal={refused} />
          ) : money!.state === "WITHHELD" ? (
            <>
              <div className="metric-value v69-metric__value" data-cold-money="withheld">
                Money consequence withheld
              </div>
              <p className="prose">{limitText(money!.limitation) ?? NOT_RECORDED}</p>
            </>
          ) : money!.state === "UNPRICED" ? (
            <>
              <div className="metric-value v69-metric__value" data-cold-money="unpriced">
                Not priced
              </div>
              <p className="prose" data-cold-money-basis>{quantityPhrase(money!.quantity)}</p>
              <p className="prose">Potential product exposure. Stock value and product response are not declared, so no loss figure is stated.</p>
            </>
          ) : (
            <Gap id="cold-site-money">No product exposure consequence assessed</Gap>
          )}
          {o === null ? null : (
            <p className="cold-panel-link">
              <ToLink href={coldUiHref(o.links.financials, p.routes)}>Open financial bridge →</ToLink>
            </p>
          )}
        </Panel>
        <Panel heading="Next step" headingId="cold-site-next-heading">
          {refused !== null ? (
            <RefusedGap id="cold-site-next" refusal={refused} />
          ) : next === null ? (
            <Gap id="cold-site-next">No recorded next step</Gap>
          ) : (
            <div data-cold-next={next.code}>
              <h3>{next.text}</h3>
              <p className="cold-panel-link">
                <ToLink href={coldUiHref(next.link, p.routes)}>{attentionLabel(next.link)}</ToLink>
              </p>
            </div>
          )}
        </Panel>
      </div>
    </>
  );
}

/* ---------- cold-evidence ---------- */

/**
 * Run-7 Evidence status chip: computed from the four panel-1 row chips. Contradictory if any row is; else limited
 * if any row is; else unknown if any row is None or there is no assessment; else supported (all four Full).
 */
function evidenceState(caps: ColdCapability[]): "Contradictory" | "Limited" | "Unknown" | "Supported" {
  if (caps.length === 0) return "Unknown";
  const c = chipCounts(caps);
  if (c.contradictory > 0) return "Contradictory";
  if (c.limited > 0) return "Limited";
  if (c.none > 0) return "Unknown";
  return "Supported";
}
const evidenceChip = (caps: ColdCapability[]) => `Evidence ${evidenceState(caps).toLowerCase()}`;

/** Run-9 M5: presentation tone for the mapped cold chip words only (the word stays visible; neutral adds no class). */
const COLD_TONE: Record<string, string> = {
  Recent: "green",
  Old: "amber",
  Never: "amber",
  Mixed: "amber",
  "Not declared": "amber",
  Good: "green",
  Limited: "amber",
  Full: "green",
  Contradictory: "red",
  "Evidence supported": "green",
  "Evidence limited": "amber",
  "Evidence contradictory": "red",
};
const toneClass = (word: string): string | undefined => (COLD_TONE[word] === undefined ? undefined : `cold-tone--${COLD_TONE[word]}`);

/** Run-9 L1 / W2-F S8: the selected consequence's stored quantity bounds, labelled as the consequence basis. */
function quantityPhrase(b: { low: string | null; high: string | null }): string {
  return `Consequence basis: ${degreeMinutes(b.low, b.high)}`;
}

function qualityText(sources: ColdSource[]): string {
  const good = sources.reduce((n, s) => n + s.quality.good_count, 0);
  const other = sources.reduce((n, s) => n + s.quality.other_count, 0);
  if (good + other === 0) return "No accepted fact";
  if (other === 0) return "Accepted facts · good quality";
  if (good === 0) return "Accepted facts · limited quality";
  return "Accepted facts · mixed quality";
}

/** Run-7: several channels in one closed row are summarized only when their states agree. */
const CONTACT_CHIP: Record<string, string> = { RECENT: "Recent", STALE: "Old", NEVER: "Never", UNKNOWN: "Unknown" };
function contactChip(sources: ColdSource[]): string {
  const words = new Set(sources.map((s) => CONTACT_CHIP[s.contact] ?? CONTACT_CHIP.UNKNOWN));
  return words.size === 1 ? [...words][0] : "Mixed";
}
/** Run-9 D1: table summary only; Source details keeps the full quality wording. */
function qualityChip(sources: ColdSource[]): string {
  const good = sources.reduce((n, s) => n + s.quality.good_count, 0);
  const other = sources.reduce((n, s) => n + s.quality.other_count, 0);
  if (good + other === 0) return "No fact";
  if (other === 0) return "Good";
  if (good === 0) return "Limited";
  return "Mixed";
}

/** One `(source_id, role)` channel inside `Source details` (Run-7 density ruling). */
function SourceChannel({ source: s, name, caps }: { source: ColdSource; name: string; caps: ColdCapability[] }) {
  const word = CONTACT_WORDS[s.contact] ?? CONTACT_WORDS.UNKNOWN;
  const at = s.contact_at === null ? CONTACT_WORDS.NEVER : utc(s.contact_at);
  return (
    <li data-source-channel={s.role}>
      <span className="cold-site-line">
        {name} · {roleLabel(s.role)} · Source <code data-vocabulary-exempt="source-reference">{s.id}</code>
      </span>
      <span className="cold-site-line">{word === at ? word : `${word} · ${at}`}</span>
      {s.limitation === null ? null : <span className="cold-site-line">{s.limitation}</span>}
      <span className="cold-site-line">
        {s.accepted_count === 0 ? "Configured source, no accepted report" : `${s.accepted_count} accepted · ${qualityText([s])}`}
      </span>
      <span className="cold-site-line">
        {s.last_accepted_at === null
          ? "No accepted fact in this window"
          : `Last accepted fact ${utc(s.last_accepted_at)}${s.fact_age === null ? "" : ` · ${s.fact_age} s old`}`}
      </span>
      <span className="cold-site-line">What it provides: {roleName(s.role)}</span>
      <span className="cold-site-line">Affects: {affects(caps, [s.role])}</span>
    </li>
  );
}

function affects(caps: ColdCapability[], roles: string[]): string {
  const labels = CAP_ROWS.filter((row) => row.claims.some((claim) => caps.find((c) => c.claim === claim)?.required_roles.some((r) => roles.includes(r))));
  return labels.length === 0 ? "Claim effect not assessed" : labels.map((r) => r.label).join(", ");
}

function EvidenceScreen(p: ScreenProps) {
  const evidence = useColdRead(() => p.client.getEvidence(p.siteId, p.window), keyOf(p, "e"));
  if (evidence === null) return <p>{COLD_ASSESSMENT_LOADING}</p>;
  const e = value(evidence);
  const refused = refusalOf(evidence);
  const none = e !== null && !isSelected(e);
  const caps = e?.capabilities ?? [];
  const analysis = e === null ? null : coldUiHref(e.links.analysis, p.routes);
  const financials = e === null ? null : selected(p.routes.financials, e.window);
  const foundation = e === null ? null : coldUiHref(e.links.foundation, p.routes);
  const missing: { role: string; label: string }[] = [];
  for (const row of CAP_ROWS) for (const role of rowMissing(caps, row.claims)) if (!missing.some((m) => m.role === role)) missing.push({ role, label: row.label });
  // W2-F S5: the stock prompt follows a selected excursion (basis presence), never the product capability chip.
  const excursionPresent = e?.selected_excursion_present === true;
  const channels = e?.sources ?? [];
  return (
    <>
      <SelectedWindowBar read={e} />
      {e === null ? (
        refused === null ? null : (
          <>
            <RequestedWindowBar window={p.window} refusal={refused} />
            <RefusedStrip label="Evidence state" title={refused.title} />
          </>
        )
      ) : (
        <StatusBar
          label="Evidence state"
          action={foundation === null ? <span>Configuration link not available</span> : <Link to={foundation}>Configuration at window end</Link>}
        >
          <Badge tone="neutral" className={toneClass(evidenceChip(caps))}>{evidenceChip(caps)}</Badge> {countSentence(caps)}
          {stateSentence(e) === null ? null : ` · ${stateSentence(e)}`}
        </StatusBar>
      )}
      <Panel heading="What we can conclude now" headingId="cold-site-conclude-heading" description="Evidence readiness is not equipment condition">
        {refused !== null ? (
          <RefusedGap id="cold-site-conclude" refusal={refused} onRetry={p.retry} />
        ) : none ? (
          <Gap id="cold-site-conclude">{NO_COLD_ASSESSMENT}</Gap>
        ) : (
          <DataTable labelledBy="cold-site-conclude-heading">
            <thead>
              <tr>
                {["Capability", "Evidence", "What we can say", "What is missing", "Next step"].map((h) => (
                  <th key={h} scope="col">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {CAP_ROWS.map((row) => {
                const chip = rowChip(caps, row.claims);
                const miss = rowMissing(caps, row.claims).map(roleName);
                // W2-F S1: the cooling and product claims show their missing roles first, then the selected capability's
                // claim limitation; they never fall back to `Nothing required for this claim`.
                const claimRow = row.key === "cooling" || row.key === "exposure";
                const limits = claimRow ? row.claims.flatMap((c) => limitText(caps.find((x) => x.claim === c)?.limitation) ?? []) : [];
                const parts = [...(miss.length > 0 ? [miss.join(", ")] : []), ...limits];
                const missText =
                  parts.length > 0 ? parts.join(" · ") : chip === "Full" && !claimRow ? "Nothing required for this claim" : "Coverage or claim basis incomplete";
                return (
                  <tr key={row.key} data-capability-row={row.key}>
                    <th scope="row">{row.label}</th>
                    <td>
                      <Badge tone="neutral" className={toneClass(chip)}>{chip}</Badge>
                    </td>
                    <td>{row.key === "exposure" ? `${SAY[chip]} Thermal exposure does not prove product loss.` : SAY[chip]}</td>
                    <td>{row.key === "exposure" ? `${missText} · Required basis: ${PRODUCT_REQUIRED_BASIS}` : missText}</td>
                    <td>
                      {row.next === "financials" ? <ToLink href={financials}>Review financials</ToLink> : <ToLink href={analysis}>Review evidence</ToLink>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </DataTable>
        )}
      </Panel>
      <div className="panel-pair">
        <Panel
          heading="Data sources · data quality, not equipment condition"
          headingId="cold-site-sources-heading"
          description="Source contact and accepted facts are separate; neither establishes equipment condition."
        >
          {refused !== null ? (
            <RefusedGap id="cold-site-sources" refusal={refused} />
          ) : none ? (
            <Gap id="cold-site-sources">{NO_COLD_ASSESSMENT}</Gap>
          ) : (
            <>
              <p className="v69-chart-note" data-cold-contact-checked>
                Contact checked at window end {utc(e!.window.to)}
              </p>
              <DataTable labelledBy="cold-site-sources-heading">
                <thead>
                  <tr>
                    {["Source", "Contact at window end", "Accepted quality", "What it provides", "Affects"].map((h) => (
                      <th key={h} scope="col">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {SOURCE_ROWS.map((row) => {
                    if (row.undeclared !== undefined) {
                      return (
                        <tr key={row.label} data-source-row={row.label}>
                          <th scope="row">{row.label}</th>
                          <td>
                            <Badge tone="neutral" className={toneClass("Not declared")}>Not declared</Badge>
                          </td>
                          <td>
                            <Badge tone="neutral">No fact</Badge>
                          </td>
                          <td>No inverter or battery feed</td>
                          <td>Claim effect not assessed</td>
                        </tr>
                      );
                    }
                    const bound = channels.filter((s) => row.roles.includes(s.role));
                    if (bound.length === 0) {
                      return (
                        <tr key={row.label} data-source-row={row.label}>
                          <th scope="row">{row.label}</th>
                          <td>No source-specific record</td>
                          <td>
                            <Badge tone="neutral">No fact</Badge>
                          </td>
                          <td>No accepted report for this role</td>
                          <td>{CLOSED_SOURCE[row.label].affects}</td>
                        </tr>
                      );
                    }
                    const closed = CLOSED_SOURCE[row.label];
                    const provided = bound.filter((s) => s.accepted_count > 0).map((s) => s.role);
                    const others = [...new Set(provided.filter((r) => !closed.primary.includes(r)))];
                    const closedWhat =
                      provided.length === 0
                        ? "No accepted report for this role"
                        : provided.some((r) => closed.primary.includes(r))
                          ? closed.what
                          : others.length === 1
                            ? roleName(others[0])
                            : "Other recorded roles";
                    return (
                      <tr key={row.label} data-source-row={row.label}>
                        <th scope="row">{row.label}</th>
                        <td>
                          <Badge tone="neutral" className={toneClass(contactChip(bound))}>{contactChip(bound)}</Badge>
                        </td>
                        <td>
                          <Badge tone="neutral" className={toneClass(qualityChip(bound))}>{qualityChip(bound)}</Badge>
                        </td>
                        <td>{closedWhat}</td>
                        <td>{closed.affects}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </DataTable>
              <Disclosure summary="Source details" name="cold-site-source-details">
                {SOURCE_ROWS.map((row) => {
                  const owned = channels.filter((s) => row.roles.includes(s.role));
                  const others = row.other === undefined ? [] : channels.filter((s) => row.other!.roles.includes(s.role));
                  return (
                    <div className="cold-site-group" key={row.label} data-source-detail={row.label}>
                      <p>
                        <strong>{row.label}</strong>
                      </p>
                      {row.undeclared !== undefined ? (
                        <p>{row.undeclared}</p>
                      ) : owned.length === 0 ? (
                        <p>No source-specific record</p>
                      ) : (
                        <ul className="cold-site-list">
                          {owned.map((s) => (
                            <SourceChannel key={`${s.id}|${s.role}`} source={s} name={row.label} caps={caps} />
                          ))}
                        </ul>
                      )}
                      {row.other === undefined ? null : (
                        <>
                          <p>{row.other.heading}</p>
                          {others.length === 0 ? (
                            <p>No source-specific record</p>
                          ) : (
                            <ul className="cold-site-list">
                              {others.map((s) => (
                                <SourceChannel key={`${s.id}|${s.role}`} source={s} name={OTHER_SOURCE_NAME[s.role]} caps={caps} />
                              ))}
                            </ul>
                          )}
                        </>
                      )}
                    </div>
                  );
                })}
              </Disclosure>
            </>
          )}
        </Panel>
        <Panel heading="Most useful next evidence" headingId="cold-site-next-evidence-heading">
          {refused !== null ? (
            <RefusedGap id="cold-site-next-evidence" refusal={refused} />
          ) : none ? (
            <Gap id="cold-site-next-evidence">{NO_COLD_ASSESSMENT}</Gap>
          ) : missing.length === 0 && !excursionPresent ? (
            <Gap id="cold-site-next-evidence">Next evidence not identified</Gap>
          ) : (
            <AttentionList
              label="Most useful next evidence"
              items={[
                ...missing.map((m) => ({
                  key: m.role,
                  title: `Record ${roleName(m.role)}`,
                  body: `Needed to assess ${m.label}`,
                  action: (
                    <p className="cold-panel-link">
                      <ToLink href={analysis}>Review evidence</ToLink>
                    </p>
                  ),
                })),
                ...(excursionPresent
                  ? [
                      {
                        key: "stock",
                        title: "Declare stock identity and value",
                        body: "Needed before thermal exposure can be priced",
                        action: (
                          <p className="cold-panel-link">
                            <ToLink href={financials}>Review financials</ToLink>
                          </p>
                        ),
                      },
                    ]
                  : []),
              ]}
            />
          )}
        </Panel>
      </div>
      {/* W2-F M3 + q1 ruling: refused -> one plain sentence, no link; loaded with no Analysis target -> the null-link copy is its own sentence. */}
      <Notice tone="blue">
        {e === null ? (
          <span data-cold-evidence-footer="refused">Record-level detail and how each limit is set cannot be read for this window.</span>
        ) : analysis === null ? (
          <span data-cold-evidence-footer="no-link">
            <span>Record-level detail and how each limit is set are on Evidence › Analysis.</span>{" "}
            <span data-cold-evidence-footer-target="none">
              <ToLink href={null}>{null}</ToLink>.
            </span>
          </span>
        ) : (
          <span data-cold-evidence-footer="link">
            Record-level detail and how each limit is set are on <ToLink href={analysis}>Evidence › Analysis</ToLink>.
          </span>
        )}
      </Notice>
    </>
  );
}

/* ---------- cold-evidence-analysis ---------- */

/** A state or event outcome (e.g. `LOST`) in plain words; a number is shown as recorded. */
const recordValue = (v: string) => (/^[A-Z][A-Z0-9_]*$/.test(v) ? plainCode(v) : v);

/** Run-7 density ruling: the first three selected accepted records, as the mock table shows three. */
const RECORDS_SHOWN = 3;

/** Run-8 time copy: `Sent (UTC)` and `Received (UTC)` headers over bare `HH:MM:SS` UTC clock cells. */
export function utcClock(value: string | null | undefined): string {
  const d = date(value);
  return d === null ? NOT_RECORDED : `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())}`;
}

/** Shortest truthful first-cell label; the bound source name and kind stay in Record details. */
const RECORD_LABEL: Record<string, string> = {
  chamber_temperature: "Chamber temperature",
  backup_start_event: "Generator start result",
  compressor_state: "Compressor running",
};
export const recordLabel = (role: string): string => RECORD_LABEL[role] ?? roleLabel(role);

const CLAIM_SENTENCES = [
  "Each claim needs accepted readings and enough coverage for the selected window. A missing or conflicting input limits what can be concluded.",
  "Source reporting describes data availability, not equipment condition.",
];

function AnalysisScreen(p: ScreenProps) {
  const first = useColdRead(() => p.client.getAnalysis(p.siteId, p.window, null), keyOf(p, "a"));
  const [more, setMore] = useState<{ key: string; pages: ColdAnalysisRead[] }>({ key: "", pages: [] });
  const [expanded, setExpanded] = useState(false);
  if (first === null) return <p>{COLD_ASSESSMENT_LOADING}</p>;
  const a = value(first);
  const refused = refusalOf(first);
  const none = a !== null && !isSelected(a);
  const key = keyOf(p, "a");
  const pages = more.key === key ? more.pages : [];
  const rows = a === null ? [] : [a, ...pages].flatMap((x) => x.accepted_records.items);
  const cursor = a === null ? null : (pages.length > 0 ? pages[pages.length - 1] : a).accepted_records.next_cursor;
  const total = a === null ? 0 : a.accepted_records.total_count;
  const shown = expanded ? rows : rows.slice(0, RECORDS_SHOWN);
  const loadMore = () => {
    if (cursor === null) return;
    void p.client.getAnalysis(p.siteId, p.window, cursor).then((next) => {
      if (next.status === "loaded") setMore({ key, pages: [...pages, next.value] });
    });
  };
  return (
    <>
      <SelectedWindowBar read={a} />
      {a === null ? null : (
        <StatusBar label="Evidence analysis">
          <Badge tone="neutral">Evidence · Analysis</Badge> Accepted records, timing and how each limit is set
          {stateSentence(a) === null ? null : ` · ${stateSentence(a)}`}
        </StatusBar>
      )}
      <Panel heading="Accepted records behind the conclusions" headingId="cold-site-records-heading" description="Measured time is kept even when a report arrives late">
        {refused !== null ? (
          <RefusedGap id="cold-site-records" refusal={refused} onRetry={p.retry} />
        ) : (
          <>
            <DataTable labelledBy="cold-site-records-heading">
              <thead>
                <tr>
                  {["Source · reading", "Value", "Measured (EAT)", "Sent (UTC)", "Received (UTC)", "Record"].map((h) => (
                    <th key={h} scope="col">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.length === 0 ? (
                  <tr>
                    <td colSpan={6}>
                      <Gap id="cold-site-records">No accepted records for this window</Gap>
                    </td>
                  </tr>
                ) : (
                  rows.map((r, index) => (
                    <tr key={r.evidence_id} data-accepted-record={r.evidence_id} hidden={!expanded && index >= RECORDS_SHOWN}>
                      <th scope="row">{r.role === null ? NOT_RECORDED : recordLabel(r.role)}</th>
                      <td>{r.value_display === null ? NOT_RECORDED : `${recordValue(r.value_display)}${r.unit === null ? "" : ` ${r.unit}`}`}</td>
                      <td>{eatTime(r.source_time) ?? NOT_RECORDED}</td>
                      <td>{utcClock(r.sent_at)}</td>
                      <td>{utcClock(r.received_at)}</td>
                      <td>
                        {/* W5-F1 F1-3 (R38): a labelled reference to the selected accepted record, never an anchor.
                            No exact record route is integrated; a wire link, even PROVED, is not a record destination. */}
                        <span data-record-target="unavailable">
                          <code className="cold-site-id" title={r.evidence_id} aria-label={r.evidence_id} data-record-id={r.evidence_id} data-vocabulary-exempt="source-reference">{`REC ${r.evidence_id}`}</code>
                          <span className="cold-site-line">Record page unavailable</span>
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </DataTable>
            {expanded || total <= RECORDS_SHOWN ? null : (
              <p className="cold-panel-link">
                <button type="button" className="button" onClick={() => setExpanded(true)} aria-expanded={false} data-cold-all-records>
                  {`Show all ${total} accepted records`}
                </button>
              </p>
            )}
            {cursor === null || !expanded ? null : (
              <p className="cold-panel-link">
                <button type="button" className="button" onClick={loadMore} data-cold-more>
                  Show more accepted records
                </button>
              </p>
            )}
            {shown.length === 0 ? null : (
              <Disclosure summary="Record details" name="cold-site-record-details">
                <ul className="cold-site-list">
                  {shown.map((r) => (
                    <li key={r.evidence_id} data-record-detail={r.evidence_id}>
                      <span className="cold-site-line">
                        Record <code data-vocabulary-exempt="source-reference">{r.evidence_id}</code>
                        {r.role === null ? null : ` · ${roleLabel(r.role)}`}
                        {` · Kind: ${r.kind}`}
                        {` · Target: ${plainCode(r.record_target_state)}`}
                      </span>
                      <span className="cold-site-line">
                        Quality: {r.quality === null ? NOT_RECORDED : plainCode(r.quality)} · Use: {r.exclusion === null ? "Not classified" : reasonWord(r.exclusion)} · Assessment:{" "}
                        <code data-vocabulary-exempt="source-reference">{r.assessment_revision_id ?? NOT_RECORDED}</code>
                      </span>
                      <span className="cold-site-line">
                        Source <code data-vocabulary-exempt="source-reference">{r.source_id ?? NOT_RECORDED}</code> ·{" "}
                        {selectedClassification(a!) === null ? "Source classification unknown" : classificationWord(selectedClassification(a!))}
                      </span>
                      {r.limitation === null ? null : <span className="cold-site-line">{plainLimitation(r.limitation)}</span>}
                    </li>
                  ))}
                </ul>
              </Disclosure>
            )}
          </>
        )}
      </Panel>
      <Panel heading="How a claim limit is set" headingId="cold-site-limit-heading">
        {refused !== null ? (
          <RefusedGap id="cold-site-limit" refusal={refused} />
        ) : none || a!.claim_rules.length === 0 ? (
          <Gap id="cold-site-limit">Claim limit not assessed</Gap>
        ) : (
          <>
            <div className="prose" data-claim-prose>
              {CLAIM_SENTENCES.map((t) => (
                <p key={t}>{t}</p>
              ))}
            </div>
            <Disclosure summary="Claim details" name="cold-site-claim-details">
              {a!.accepted_records.items.length === 0 ? null : (<p className="prose" data-claim-record-pointer>Accepted record IDs for this assessment are in Record details.</p>)}
              {a!.claim_rules.map((rule) => (
                <div className="cold-site-rule" key={rule.rule_id} data-claim-rule={rule.rule_id}>
                  <p className="prose">
                    <code data-vocabulary-exempt="source-reference">{rule.rule_id}</code> · {rule.result === null ? NOT_ASSESSED : plainCode(rule.result)}
                  </p>
                  <KeyValues
                    label={`${rule.rule_id} details`}
                    rows={[
                      ["Requirement", rule.requirement, "requirement"],
                      ["Observed", rule.observed_roles.length === 0 ? "None" : rule.observed_roles.map(roleName).join(", "), "observed"],
                      ["Missing", rule.missing_roles.length === 0 ? "None" : rule.missing_roles.map(roleName).join(", "), "missing"],
                      ["Coverage", decimal(rule.coverage.ratio) ?? NOT_ASSESSED, "coverage"],
                      ["Result", rule.result === null ? NOT_ASSESSED : plainCode(rule.result), "result"],
                      ["Source", selectedClassification(a!) === null ? "Unknown" : classificationWord(selectedClassification(a!)), "source"],
                      ["Evidence cutoff", utc(a!.window.known_at), "cutoff"],
                      ...(rule.limitation === null ? [] : ([["Limit", plainLimitation(rule.limitation), "limit"]] as [string, string, string][])),
                    ]}
                  />
                </div>
              ))}
            </Disclosure>
          </>
        )}
      </Panel>
    </>
  );
}

/* ---------- cold-financials ---------- */

function FinancialsScreen(p: ScreenProps) {
  const fin = useColdRead(() => p.client.getFinancials(p.siteId, p.window), keyOf(p, "f"));
  const assumptions = useColdRead(() => p.client.getAssumptions(p.siteId, p.window), keyOf(p, "s"));
  const findingsRead = useColdRead(() => p.assessment.listFindings(p.siteId, p.window), keyOf(p, "l"));
  if (fin === null || assumptions === null || findingsRead === null) return <p>{COLD_ASSESSMENT_LOADING}</p>;
  const f = value(fin);
  const refused = refusalOf(fin);
  const findings: ColdFindingsRead | null = value(findingsRead);
  const exposures = (f?.consequences ?? []).filter((c) => c.kind === "PRODUCT_EXPOSURE");
  const start = findings?.items.find((i) => i.kind === "START_RESPONSE") ?? null;
  const findingOf = (revisionId: string) => findings?.items.find((i) => i.revision_id === revisionId) ?? null;
  const findingLink = (id: string) => selected(p.routes.finding(id), f!.window);
  const anyLink = exposures.some((c) => findingOf(c.exact_basis.finding_revision_id) !== null) || start !== null;
  // W2-F M5/N9: the chip counts the bridge rows actually displayed from the selected responses (consequence rows from
  // Financials, the start-response context row from Findings), so the chip and the table always agree.
  const count = exposures.length + (start === null ? 0 : 1);
  const startUnread = findings === null;
  const first = exposures[0];
  const s = value(assumptions);
  const sRefused = refusalOf(assumptions);
  return (
    <>
      {f === null ? (
        refused === null ? null : (
          <>
            <RequestedWindowBar window={p.window} refusal={refused} />
            <RefusedStrip label="Financial consequence" chip={NOT_ASSESSED} title={refused.title} />
            <RefusedTiles label="Money consequence" cards={["Chamber thermal exposure", "Confirmed loss", "Repair and call-out", "Verified savings"]} />
          </>
        )
      ) : (
        <>
          <SelectedWindowBar read={f} />
          <StatusBar label="Financial consequence">
            <Badge tone="neutral">
              <span data-cold-line-count={count}>{`${count} consequence ${count === 1 ? "line" : "lines"}`}</span>
            </Badge>{" "}
            selected window · no financial status here · Displayed rows include unpriced context
            {stateSentence(f) === null ? null : ` · ${stateSentence(f)}`}
          </StatusBar>
          <MetricCards label="Money consequence">
            <MetricCard
              label="Chamber thermal exposure"
              value={first === undefined ? NOT_ASSESSED : first.state === "WITHHELD" ? "Withheld" : first.state === "UNPRICED" ? "Unpriced" : NOT_ASSESSED}
              note={
                first !== undefined && first.state === "UNPRICED"
                  ? quantityPhrase(first.quantity_bounds)
                  : first !== undefined && first.state === "WITHHELD"
                    ? (limitText(first.reason) ?? NOT_RECORDED)
                    : "No chamber thermal exposure consequence assessed"
              }
              word
              data={{ "data-cold-card": "exposure" }}
            />
            <MetricCard label="Confirmed loss" value="Unknown" note="Temperature exposure does not prove spoilage" word />
            <MetricCard label="Repair and call-out" value="Not recorded" note="No accepted repair cost record" word />
            <MetricCard label="Verified savings" value="None" note="No verified outcome recorded" word />
          </MetricCards>
        </>
      )}
      <Panel
        heading="What happened → what it means in money"
        headingId="cold-site-bridge-heading"
        description={refused === null && anyLink ? "Select a source to return to its Finding" : undefined}
      >
        {refused !== null ? (
          <RefusedGap id="cold-site-bridge" refusal={refused} onRetry={p.retry} />
        ) : (
          <>
            <DataTable labelledBy="cold-site-bridge-heading">
              <thead>
                <tr>
                  {["What happened", "How it becomes money", "Consequence", "Basis", "Confidence", "Source"].map((h) => (
                    <th key={h} scope="col">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {exposures.length === 0 && start === null ? (
                  <tr>
                    <td colSpan={6}>
                      <Gap id="cold-site-bridge">No financial consequence assessed for this window</Gap>
                    </td>
                  </tr>
                ) : null}
                {exposures.map((c) => {
                  const finding = findingOf(c.exact_basis.finding_revision_id);
                  const withheld = c.state === "WITHHELD";
                  return (
                    <tr key={c.id} data-consequence-row={c.kind}>
                      <th scope="row">{`Chamber thermal exposure · ${quantityPhrase(c.quantity_bounds)}`}</th>
                      <td>Stock value × product response rule — not declared</td>
                      <td>{withheld ? "Withheld" : "Not priced"}</td>
                      <td>
                        <Badge tone="neutral">{withheld ? "Withheld" : "Unpriced"}</Badge>
                      </td>
                      <td>{finding === null ? NOT_ASSESSED : claimWord(finding.claim_level)}</td>
                      <td>{finding === null ? "No linked page for this item" : <Link to={findingLink(finding.finding_id)}>{finding.title}</Link>}</td>
                    </tr>
                  );
                })}
                {start === null ? null : (
                  <tr data-consequence-row="BACKUP_GAP">
                    <th scope="row">Observed backup start failure</th>
                    <td>Repair and call-out cost not recorded</td>
                    <td>Not recorded</td>
                    <td>No accepted cost basis</td>
                    <td>Not assessed</td>
                    <td>
                      <Link to={findingLink(start.finding_id)}>{start.title}</Link>
                    </td>
                  </tr>
                )}
              </tbody>
            </DataTable>
            {startUnread ? (
              <p className="prose" data-cold-start-context="unread">
                Start-response context cannot be read for this window
              </p>
            ) : null}
            {exposures.length === 0 && start === null ? null : (
              <Disclosure summary="Basis details" name="cold-site-basis-details">
                {exposures.length === 0 ? null : (
                  <p className="prose" data-cold-thermal-basis-note>
                    Thermal exposure does not establish product damage or loss. The consequence bound may be wider than the observed excursion estimate.
                  </p>
                )}
                {exposures.map((c, i) => {
                  const bs = c.exact_basis;
                  const code = (v: string | null) => (v === null ? NOT_RECORDED : <code data-vocabulary-exempt="source-reference">{v}</code>);
                  const rows: [string, ReactNode][] = [
                    ["Quantity bounds", quantityPhrase(c.quantity_bounds)],
                    ["Reason", c.reason === null ? NOT_RECORDED : plainLimitation(c.reason)],
                    ["Limitation", c.limitation === null ? NOT_RECORDED : plainLimitation(c.limitation)],
                    ["Finding version", code(bs.finding_revision_id)],
                    ["Episode version", code(bs.episode_revision_id)],
                    ["Assessment version", code(bs.assessment_revision_id)],
                    ["Accepted records", bs.evidence_ids.length === 0 ? NOT_RECORDED : code(bs.evidence_ids.join(", "))],
                    ["Source gate", code(bs.source_gate_sha256)],
                    ["Assumption versions", bs.assumption_revision_ids.length === 0 ? NOT_RECORDED : code(bs.assumption_revision_ids.join(", "))],
                    ["Consequence basis", code(bs.consequence_basis_sha256)],
                  ];
                  return (
                    <div className="cold-site-group" key={c.id} data-basis-detail={c.id}>
                      <p>
                        <strong>{exposures.length > 1 ? `Chamber thermal exposure ${i + 1}` : "Chamber thermal exposure"}</strong>
                      </p>
                      <dl className="exact-references__list">
                        {rows.map(([label, v]) => (
                          <div className="exact-references__row" key={label}>
                            <dt>{label}</dt>
                            <dd>{v}</dd>
                          </div>
                        ))}
                      </dl>
                    </div>
                  );
                })}
                {start === null ? null : (
                  <div className="cold-site-group" data-basis-detail="BACKUP_GAP">
                    <p>
                      <strong>Observed backup start failure</strong>
                    </p>
                    <p>No stored consequence or exact cost basis for this row.</p>
                  </div>
                )}
              </Disclosure>
            )}
          </>
        )}
      </Panel>
      <div className="panel-pair">
        <Panel heading="Assumptions in use" headingId="cold-site-in-use-heading">
          {sRefused !== null ? (
            <RefusedGap id="cold-site-in-use" refusal={sRefused} />
          ) : (
            <>
              <AssumptionValues read={s!} />
              <p className="cold-panel-link">
                <ToLink href={coldUiHref(f?.links.assumptions, p.routes) ?? selected(p.routes.assumptions, s!.window)}>Review assumptions</ToLink>
              </p>
            </>
          )}
        </Panel>
        <Panel heading="Not included" headingId="cold-site-not-included-heading">
          {refused !== null ? (
            <RefusedGap id="cold-site-not-included" refusal={refused} />
          ) : f!.not_included.length === 0 ? (
            <Gap id="cold-site-not-included">No exclusion reason recorded</Gap>
          ) : (
            <ul className="cold-site-list">
              {f!.not_included.map((n) => (
                <li key={n.code} data-not-included={n.code}>
                  {n.text}
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>
    </>
  );
}

function assumptionValue(read: ColdAssumptionsRead, key: string): string {
  const item = read.items.find((i) => i.key === key);
  if (item === undefined || read.missing_keys.includes(key) || item.value === null) return "Not declared";
  return `${item.value}${item.unit === null ? "" : ` ${item.unit}`}`;
}

const NOT_DECLARED = "Not declared";

/**
 * W2-F M7/N6: the one assumption projection shared by Financials `Assumptions in use` and the Assumptions table, in
 * mock order. Stock value is shown as `{quantity} × {unit value} {currency}` only when both inputs are declared in
 * the selected read; it is never multiplied, and undeclared inputs give `Not declared`.
 */
function coldAssumptionRows(read: ColdAssumptionsRead | null): { key: string; label: string; value: string; used: string }[] {
  const declared = (key: string) => {
    const item = read?.items.find((i) => i.key === key);
    return item === undefined || item.value === null || read!.missing_keys.includes(key) ? null : item;
  };
  const quantity = declared("cold_stock_quantity");
  const unitValue = declared("cold_stock_unit_value");
  const currency = unitValue?.currency ?? read?.items.find((i) => i.currency !== null)?.currency ?? null;
  const stock =
    quantity === null || unitValue === null
      ? NOT_DECLARED
      : `${assumptionValue(read!, "cold_stock_quantity")} × ${unitValue.value}${currency === null ? "" : ` ${currency}`}`;
  return [
    { key: "stock", label: "Stock value in chamber", value: stock, used: "Pricing product exposure" },
    { key: "rule", label: "Product exposure rule", value: read === null ? NOT_DECLARED : assumptionValue(read, "cold_exposure_rule"), used: "Translating thermal exposure" },
    {
      key: "currency",
      label: "Currency",
      value: currency !== null ? currency : read === null || read.currency_state === "UNDECLARED" ? NOT_DECLARED : NOT_RECORDED,
      used: "Displaying a priced consequence",
    },
  ];
}

const noneDeclared = (rows: { value: string }[]) => rows.every((r) => r.value === NOT_DECLARED);

function AssumptionValues({ read }: { read: ColdAssumptionsRead }) {
  const rows = coldAssumptionRows(read);
  return (
    <>
      <KeyValues label="Assumptions in use" rows={rows.map((r) => [r.label, r.value, r.key] as [string, string, string])} />
      {noneDeclared(rows) ? <p className="v69-chart-note">No assumption in use · Cold stock and exposure assumptions have not been declared</p> : null}
    </>
  );
}

/* ---------- cold-assumptions ---------- */

function AssumptionsScreen(p: ScreenProps) {
  const read = useColdRead(() => p.client.getAssumptions(p.siteId, p.window), keyOf(p, "s"));
  if (read === null) return <p>{COLD_ASSESSMENT_LOADING}</p>;
  const s = value(read);
  const refused = refusalOf(read);
  const rows = coldAssumptionRows(s);
  return (
    <>
      <SelectedWindowBar read={s} extra={stateSentence(s)} />
      <Panel heading="Financial assumptions" headingId="cold-site-assumptions-heading" description="Site-scoped business context · no cold assumption publication is available in W2">
        {refused !== null ? (
          <RefusedGap id="cold-site-assumptions" refusal={refused} onRetry={p.retry} />
        ) : (
          <>
          <DataTable labelledBy="cold-site-assumptions-heading">
            <thead>
              <tr>
                {["Assumption", "Value", "Used for"].map((h) => (
                  <th key={h} scope="col">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map(({ label, value: v, used }) => (
                <tr key={label} data-assumption-row={label}>
                  <th scope="row">{label}</th>
                  <td>{v === "Not declared" ? <Badge tone="neutral">{v}</Badge> : v}</td>
                  <td>{used}</td>
                </tr>
              ))}
            </tbody>
          </DataTable>
          {noneDeclared(rows) ? <p className="v69-chart-note">No assumption in use · Cold stock and exposure assumptions have not been declared</p> : null}
          </>
        )}
      </Panel>
      <Notice tone="blue">
        Without declared stock quantity, unit value, currency and a reviewed exposure rule, product exposure stays unpriced. A future reviewed assumption may
        re-translate the same evidence; it does not change the temperature record.
      </Notice>
    </>
  );
}
