import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

import {
  AttentionList,
  Badge,
  Breadcrumbs,
  type Crumb,
  CausalTimeline,
  DataTable,
  ExactReferences,
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
import { UnavailableTab } from "../ui/UnavailableEntry";
import { type ColdAssessmentClient, type ColdRead, type ColdTemperatureRead, type ColdWindowQuery, type ColdFindingsRead, coldWindowSearch } from "./coldAssessmentClient";
import type {
  ColdAnalysisRead,
  ColdAssumptionsRead,
  ColdCapability,
  ColdEvidenceRead,
  ColdOverviewRead,
  ColdSiteClient,
  ColdSource,
} from "./coldSiteClient";
import { COLD_ASSESSMENT_LOADING, refusalText } from "./ColdAssessmentViews";
import { ColdTemperatureChart } from "./assessmentGraphics";
import { claimWord, classificationWord, plainCode, plainLimitation, reasonWord, STEP_LABELS } from "./coldAssessmentWords";
import { roleLabel } from "./ColdFoundationViews";
import { NOT_ASSESSED, NOT_RECORDED, date, dayHm, decimal, windowText } from "./coldFormat";
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
  findings: string;
  finding: (findingId: string) => string;
  foundation: string;
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

/** The six grouped source rows of `cold-evidence` panel 2 in mock order, and the `cold-roles-1` roles each groups. */
const SOURCE_ROWS: { label: string; roles: string[] }[] = [
  { label: "Chamber probe", roles: ["chamber_temperature", "ambient_temperature", "manual_temperature"] },
  { label: "Inverter-charger + battery", roles: ["grid_state", "grid_power_event", "backup_bus_state"] },
  { label: "Generator controller", roles: ["backup_start_event", "generator_state"] },
  { label: "Compressor meter", roles: ["compressor_state", "compressor_power"] },
  { label: "Transfer switch", roles: ["transfer_result"] },
  { label: "Loading / door log", roles: ["door_event"] },
];

const ASSUMPTION_ROWS: [string, string][] = [
  ["cold_stock_quantity", "Stock quantity in chamber"],
  ["cold_stock_unit_value", "Stock unit value"],
  ["cold_exposure_rule", "Product exposure rule"],
];

const pad = (n: number) => String(n).padStart(2, "0");
/** The mock's `Measured (EAT)` time: East Africa Time (UTC+3, no daylight saving), while data stays UTC. */
export function eatTime(value: string | null | undefined): string | null {
  const d = date(value);
  if (d === null) return null;
  const e = new Date(d.getTime() + 3 * 3600 * 1000);
  return `${pad(e.getUTCHours())}:${pad(e.getUTCMinutes())}:${pad(e.getUTCSeconds())}`;
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
function selected(base: string, window: ColdWindowQuery, view?: "analysis"): string {
  const params = new URLSearchParams(coldWindowSearch(window).slice(1));
  if (view !== undefined) params.set("view", view);
  return withQuery(base, params);
}

function ToLink({ href, children, data }: { href: string | null; children: ReactNode; data?: Record<string, string> }) {
  return href === null ? (
    <span className="cold-site-noop" {...data}>
      Not available yet
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
interface Refusal {
  sentence: string;
  retry: boolean;
  key: string;
}
function refusalOf(read: ColdRead<unknown> | null): Refusal | null {
  if (read === null || read.status === "loaded") return null;
  if (read.status === "refused" && read.httpStatus === 403) return { sentence: SOURCE_FORBIDDEN, retry: false, key: "forbidden" };
  if (read.status === "unavailable" || read.httpStatus === 503) return { sentence: COLD_SITE_UNAVAILABLE, retry: true, key: "unavailable" };
  return { sentence: refusalText(read).body, retry: false, key: refusalText(read).key };
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
  if (view === "overview") return null;
  const evidence = view === "evidence" || view === "analysis";
  const items: [string, string, string][] = evidence
    ? [
        ["evidence", "Overview", selected(routes.evidence, window)],
        ["analysis", "Analysis", selected(routes.evidence, window, "analysis")],
      ]
    : [
        ["financials", "Overview", selected(routes.financials, window)],
        ["assumptions", "Assumptions", selected(routes.assumptions, window)],
      ];
  return (
    <nav className="site-tabs site-subtabs" aria-label={evidence ? "Evidence sections" : "Financials sections"}>
      <ol className="site-tabs__list">
        {items.map(([id, label, href]) => (
          <li className="site-tabs__item" key={id}>
            <Link className="site-tabs__link" to={href} data-cold-subtab={id} aria-current={id === view ? "page" : undefined}>
              {label}
            </Link>
          </li>
        ))}
        {evidence ? null : <UnavailableTab label="Scenarios" />}
      </ol>
    </nav>
  );
}

/** The selected window and evidence cutoff (the mock's date bar), with any pending, historical or stale sentence. */
function selectionLine(read: { window: ColdWindowQuery; currentness: { state: string } } | null, withCutoff: boolean): string | null {
  if (read === null) return null;
  const parts = [windowText(read.window.from, read.window.to)];
  if (withCutoff) parts.push(`Selected evidence through ${utc(read.window.known_at)}`);
  return parts.join(" · ");
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
  const coverage = t.coverage.known_points === null ? null : `coverage ${t.coverage.known_points} / ${t.coverage.expected_points ?? "?"} readings`;
  const tempNote =
    t.latest_deg_c === null
      ? "No chamber reading for this window"
      : [`${t.episode_count} ${t.episode_count === 1 ? "excursion" : "excursions"}`, `latest ${decimal(t.latest_deg_c)} °C`, policy, coverage].filter(Boolean).join(" · ");
  const b = o.backup_summary;
  const backupChip = b.observed_failure > 0 ? "Degraded" : b.observed_success > 0 ? "Observed start" : "Unknown";
  const backupNote =
    b.observed_failure + b.observed_success === 0
      ? "Backup result not observed"
      : `${b.attempts} ${b.attempts === 1 ? "start attempt" : "start attempts"} · ${b.observed_success} started · ${b.observed_failure} failed`;
  const coolingChip = { SUPPORTED: "Supported", LIMITED: "Limited", CONTRADICTORY: "Contradictory" }[o.cooling.state] ?? "Unknown";
  const caps = evidence?.capabilities ?? [];
  const counts = chipCounts(caps);
  const evidenceChip = caps.length === 0 ? "Unknown" : counts.limited > 0 ? "Limited" : counts.contradictory > 0 ? "Contradictory" : counts.full === counts.n ? "Supported" : "Unknown";
  const card = (label: string, href: string | null) => (href === null ? label : <Link to={href}>{label}</Link>);
  return (
    <MetricCards columns={5} label="Cold room conditions">
      <MetricCard label={card("Temperature", coldUiHref(o.links.temperature, routes))} value={tempChip} note={tempNote} tone={proved ? "amber" : "muted"} assessment data={{ "data-cold-card": "temperature" }} />
      <MetricCard label={card("Backup", coldUiHref(o.links.backup, routes))} value={backupChip} note={backupNote} tone={b.observed_failure > 0 ? "red" : "muted"} assessment data={{ "data-cold-card": "backup" }} />
      <MetricCard
        label="Cooling"
        value={coolingChip}
        note={`${o.cooling.text} · Recovery comparison not assessed · Not available yet`}
        tone="muted"
        assessment
        data={{ "data-cold-card": "cooling" }}
      />
      <MetricCard label="Maintenance" value="Not recorded" note={`${o.maintenance.text} · Work record not available`} tone="muted" assessment data={{ "data-cold-card": "maintenance" }} />
      <MetricCard
        label={card("Evidence", coldUiHref(o.links.evidence, routes))}
        value={evidenceChip}
        note={caps.length === 0 ? "Evidence coverage not assessed" : countSentence(caps)}
        tone="muted"
        assessment
        data={{ "data-cold-card": "evidence" }}
      />
    </MetricCards>
  );
}

function stripEvents(o: ColdOverviewRead): TimelineEvent[] {
  const steps = [...o.causal_strip].sort((a, b) => STEP_ORDER.indexOf(a.step) - STEP_ORDER.indexOf(b.step));
  return steps.map((s) => {
    const name = STEP_LABELS[s.step] ?? plainCode(s.step);
    return {
      key: s.step,
      time: s.at === null ? "—" : `${eatTime(s.at)?.slice(0, 5)} EAT`,
      title: `${name} · ${STEP_CHIP[s.state] ?? plainCode(s.state)}`,
      detail: s.state === "MISSING" ? `No accepted ${name.toLowerCase()} report for this chain` : (limitText(s.limitation) ?? undefined),
      tone: s.state === "OBSERVED" ? undefined : s.state === "CONTRADICTORY" ? "danger" : "gap",
    };
  });
}

function OverviewScreen(p: ScreenProps) {
  const overview = useColdRead(() => p.client.getOverview(p.siteId, p.window), keyOf(p, "o"));
  const evidence = useColdRead(() => p.client.getEvidence(p.siteId, p.window), keyOf(p, "e"));
  const temperature = useColdRead(() => p.assessment.getTemperature(p.siteId, p.window), keyOf(p, "t"));
  if (overview === null || evidence === null || temperature === null) return <p>{COLD_ASSESSMENT_LOADING}</p>;
  const o = value(overview);
  const refused = refusalOf(overview);
  const none = o !== null && !isSelected(o);
  const firstFinding = o?.findings.items.find((f) => f.link !== null) ?? null;
  const next = o?.needs_attention.find((n) => n.link !== null) ?? null;
  const policyNote =
    o !== null && o.objective.policy_low_deg_c !== null && o.objective.policy_high_deg_c !== null
      ? `Policy band ${decimal(o.objective.policy_low_deg_c)}–${decimal(o.objective.policy_high_deg_c)}°C. Gaps between accepted readings remain unmeasured.`
      : "Chamber temperature policy not declared for this window";
  const temp: ColdTemperatureRead | null = value(temperature);
  const tempRefused = refusalOf(temperature);
  const money = o?.consequence_summary;
  const attentionLabel = (link: string): string =>
    link.includes("/cold/findings/") ? "Open Finding →" : link.includes("/cold/backup-chain") ? "Performance › Backup →" : "Evidence →";
  return (
    <>
      {o === null ? null : (
        <>
          <StatusBar
            label="Cold room state"
            other={selectionLine(o, false)}
            action={<ToLink href={coldUiHref(o.links.evidence, p.routes)}>Inspect evidence</ToLink>}
          >
            <Badge tone="neutral">{overviewStateChip(o)}</Badge>{" "}
            <Badge tone="neutral">{o.status.claim_level === null ? "Confidence: Unknown" : `Confidence: ${claimWord(o.status.claim_level)}`}</Badge>{" "}
            <Badge tone="neutral">{o.consequence_summary.overlap_group !== null ? "Potential product exposure" : "Product exposure not established"}</Badge>{" "}
            {stateSentence(o) === null ? `Selected evidence through ${utc(o.window.known_at)}` : `${stateSentence(o)} · Selected evidence through ${utc(o.window.known_at)}`}
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
        actions={firstFinding === null ? undefined : <ToLink href={coldUiHref(firstFinding.link, p.routes)}>Open Finding</ToLink>}
      >
        {refused !== null ? (
          <RefusedGap id="cold-site-what-happened" refusal={refused} onRetry={p.retry} />
        ) : none ? (
          <Gap id="cold-site-what-happened">{NO_COLD_ASSESSMENT}</Gap>
        ) : o!.causal_strip.length === 0 ? (
          <p className="prose">The power-to-cooling sequence is not established for this window.</p>
        ) : (
          <>
            <CausalTimeline events={stripEvents(o!)} label="Power to cooling sequence" />
            <p className="prose">The steps below are based on the selected accepted records. Missing steps remain unobserved.</p>
          </>
        )}
      </Panel>
      <div className="panel-pair">
        <Panel heading="Chamber temperature" headingId="cold-site-temperature-heading" description="Operating conditions, not an inventory-loss model">
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
              items={o!.needs_attention.map((n) => ({
                key: n.code,
                title: n.text,
                body: limitText(n.limitation) ?? "",
                action:
                  n.link === null ? undefined : (
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
            <p className="cold-panel-link" data-cold-next={next.code}>
              <ToLink href={coldUiHref(next.link, p.routes)}>{next.text} →</ToLink>
            </p>
          )}
        </Panel>
      </div>
    </>
  );
}

/* ---------- cold-evidence ---------- */

function evidenceChip(caps: ColdCapability[]): string {
  const states = caps.map((c) => c.state);
  if (states.includes("LIMITED")) return "Evidence limited";
  if (states.includes("CONTRADICTORY")) return "Evidence contradictory";
  if (states.length > 0 && states.every((s) => s === "SUPPORTED")) return "Evidence supported";
  return "Evidence unknown";
}

function qualityText(sources: ColdSource[]): string {
  const good = sources.reduce((n, s) => n + s.quality.good_count, 0);
  const other = sources.reduce((n, s) => n + s.quality.other_count, 0);
  if (good + other === 0) return "No accepted fact";
  if (other === 0) return "Accepted facts · good quality";
  if (good === 0) return "Accepted facts · limited quality";
  return "Accepted facts · mixed quality";
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
  const exposureConsidered = ["LIMITED", "SUPPORTED", "CONTRADICTORY"].includes(caps.find((c) => c.claim === "PRODUCT_EXPOSURE")?.state ?? "UNAVAILABLE");
  const channels = e?.sources ?? [];
  return (
    <>
      {e === null ? null : (
        <StatusBar
          label="Evidence state"
          other={selectionLine(e, true)}
          action={foundation === null ? <span>Configuration link not available</span> : <Link to={foundation}>Configuration at window end</Link>}
        >
          <Badge tone="neutral">{evidenceChip(caps)}</Badge> {countSentence(caps)}
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
                const missText = miss.length > 0 ? miss.join(", ") : chip === "Full" ? "Nothing required for this claim" : "Coverage or claim basis incomplete";
                return (
                  <tr key={row.key} data-capability-row={row.key}>
                    <th scope="row">{row.label}</th>
                    <td>
                      <Badge tone="neutral">{chip}</Badge>
                    </td>
                    <td>{row.key === "exposure" ? `${SAY[chip]} Thermal exposure does not prove product loss.` : SAY[chip]}</td>
                    <td>{row.key === "exposure" ? `${missText} · Stock identity and value are not declared` : missText}</td>
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
              <DataTable labelledBy="cold-site-sources-heading">
                <thead>
                  <tr>
                    {["Source", "Status at window end", "Quality", "What it provides", "Affects"].map((h) => (
                      <th key={h} scope="col">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {SOURCE_ROWS.map((row) => {
                    const bound = channels.filter((s) => row.roles.includes(s.role));
                    if (bound.length === 0) {
                      return (
                        <tr key={row.label} data-source-row={row.label}>
                          <th scope="row">
                            {row.label}
                            <small className="cold-site-detail">No source-specific record</small>
                          </th>
                          <td>No source-specific record</td>
                          <td>No accepted fact</td>
                          <td>No accepted report for this role</td>
                          <td>Claim effect not assessed</td>
                        </tr>
                      );
                    }
                    const provides = bound.filter((s) => s.accepted_count > 0).map((s) => roleName(s.role));
                    return (
                      <tr key={row.label} data-source-row={row.label}>
                        <th scope="row">
                          {row.label}
                          {bound.map((s) => (
                            <small className="cold-site-detail" key={`${s.id}|${s.role}`}>
                              {roleLabel(s.role)}
                            </small>
                          ))}
                        </th>
                        <td>
                          {bound.map((s) => (
                            <span className="cold-site-line" key={`${s.id}|${s.role}`} data-source-contact={s.contact}>
                              {CONTACT_WORDS[s.contact] ?? CONTACT_WORDS.UNKNOWN}
                              {s.contact_at === null ? null : ` at ${utc(s.contact_at)}`}
                              {s.limitation === null ? null : <small className="cold-site-detail">{s.limitation}</small>}
                            </span>
                          ))}
                          <small className="cold-site-detail">Contact checked at window end {utc(e!.window.to)}</small>
                        </td>
                        <td>
                          {qualityText(bound)}
                          {bound.map((s) => (
                            <small className="cold-site-detail" key={`${s.id}|${s.role}`}>
                              {s.last_accepted_at === null ? "No accepted fact in this window" : `Last accepted fact ${utc(s.last_accepted_at)} · ${s.fact_age ?? "?"} s old`}
                            </small>
                          ))}
                        </td>
                        <td>{provides.length === 0 ? "No accepted report for this role" : provides.join(", ")}</td>
                        <td>{affects(caps, bound.map((s) => s.role))}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </DataTable>
              <ExactReferences
                name="cold-site-source-references"
                references={channels.map((s, i) => ({ label: `${roleLabel(s.role)} source ${i + 1}`, value: s.id }))}
              />
            </>
          )}
        </Panel>
        <Panel heading="Most useful next evidence" headingId="cold-site-next-evidence-heading">
          {refused !== null ? (
            <RefusedGap id="cold-site-next-evidence" refusal={refused} />
          ) : none ? (
            <Gap id="cold-site-next-evidence">{NO_COLD_ASSESSMENT}</Gap>
          ) : missing.length === 0 && !exposureConsidered ? (
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
                ...(exposureConsidered
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
      <Notice tone="blue">
        Record-level detail and claim limits are on <ToLink href={analysis}>Evidence › Analysis</ToLink>.
      </Notice>
    </>
  );
}

/* ---------- cold-evidence-analysis ---------- */

function AnalysisScreen(p: ScreenProps) {
  const first = useColdRead(() => p.client.getAnalysis(p.siteId, p.window, null), keyOf(p, "a"));
  const [more, setMore] = useState<{ key: string; pages: ColdAnalysisRead[] }>({ key: "", pages: [] });
  if (first === null) return <p>{COLD_ASSESSMENT_LOADING}</p>;
  const a = value(first);
  const refused = refusalOf(first);
  const none = a !== null && !isSelected(a);
  const key = keyOf(p, "a");
  const pages = more.key === key ? more.pages : [];
  const rows = a === null ? [] : [a, ...pages].flatMap((x) => x.accepted_records.items);
  const cursor = a === null ? null : (pages.length > 0 ? pages[pages.length - 1] : a).accepted_records.next_cursor;
  const loadMore = () => {
    if (cursor === null) return;
    void p.client.getAnalysis(p.siteId, p.window, cursor).then((next) => {
      if (next.status === "loaded") setMore({ key, pages: [...pages, next.value] });
    });
  };
  return (
    <>
      {a === null ? null : (
        <StatusBar label="Evidence analysis" other={selectionLine(a, true)}>
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
                  {["Source · reading", "Value", "Measured (EAT)", "Sent", "Received", "Record"].map((h) => (
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
                  rows.map((r) => (
                    <tr key={r.evidence_id} data-accepted-record={r.evidence_id}>
                      <th scope="row">
                        {r.role === null ? NOT_RECORDED : roleLabel(r.role)}
                        <small className="cold-site-detail">
                          Quality: {r.quality === null ? NOT_RECORDED : plainCode(r.quality)} · Use: {r.exclusion === null ? "Not classified" : reasonWord(r.exclusion)} · Assessment:{" "}
                          <code data-vocabulary-exempt="source-reference">{r.assessment_revision_id ?? NOT_RECORDED}</code>
                        </small>
                      </th>
                      <td>{r.value_display === null ? NOT_RECORDED : `${r.value_display}${r.unit === null ? "" : ` ${r.unit}`}`}</td>
                      <td>{eatTime(r.source_time) ?? NOT_RECORDED}</td>
                      <td>{eatTime(r.sent_at) ?? NOT_RECORDED}</td>
                      <td>{eatTime(r.received_at) ?? NOT_RECORDED}</td>
                      <td>
                        {r.record_target_state === "PROVED" && r.link !== null ? (
                          <ToLink href={coldUiHref(r.link, p.routes) ?? r.link}>Open record</ToLink>
                        ) : (
                          <span data-record-target="unavailable">
                            Record <code data-vocabulary-exempt="source-reference">{r.evidence_id}</code> · Analysis view not available for this cold record
                          </span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </DataTable>
            {cursor === null ? null : (
              <p className="cold-panel-link">
                <button type="button" className="button" onClick={loadMore} data-cold-more>
                  Show more accepted records
                </button>
              </p>
            )}
          </>
        )}
      </Panel>
      <Panel heading="How a claim limit is set" headingId="cold-site-limit-heading" description="Source reporting describes data availability, not equipment condition.">
        {refused !== null ? (
          <RefusedGap id="cold-site-limit" refusal={refused} />
        ) : none || a!.claim_rules.length === 0 ? (
          <Gap id="cold-site-limit">Claim limit not assessed</Gap>
        ) : (
          a!.claim_rules.map((rule) => (
            <div className="cold-site-rule" key={rule.rule_id} data-claim-rule={rule.rule_id}>
              <p className="prose">{rule.requirement}</p>
              <KeyValues
                label={rule.requirement}
                rows={[
                  ["Observed", rule.observed_roles.length === 0 ? "None" : rule.observed_roles.map(roleName).join(", "), "observed"],
                  ["Missing", rule.missing_roles.length === 0 ? "None" : rule.missing_roles.map(roleName).join(", "), "missing"],
                  ["Coverage", decimal(rule.coverage.ratio) ?? NOT_ASSESSED, "coverage"],
                  ["Result", rule.result === null ? NOT_ASSESSED : plainCode(rule.result), "result"],
                  ["Source", a!.source_provenance.classification === null ? "Unknown" : classificationWord(a!.source_provenance.classification), "source"],
                  ["Evidence cutoff", utc(a!.window.known_at), "cutoff"],
                  ...(rule.limitation === null ? [] : ([["Limit", plainLimitation(rule.limitation), "limit"]] as [string, string, string][])),
                ]}
              />
            </div>
          ))
        )}
      </Panel>
    </>
  );
}

/* ---------- cold-financials ---------- */

function boundText(v: string | null): string {
  return decimal(v) ?? "Unknown bound";
}

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
  const count = f?.consequences.length ?? 0;
  const first = exposures[0];
  const s = value(assumptions);
  const sRefused = refusalOf(assumptions);
  return (
    <>
      {f === null ? null : (
        <>
          <StatusBar label="Financial consequence" other={selectionLine(f, true)}>
            <Badge tone="neutral">{`${count} consequence ${count === 1 ? "line" : "lines"}`}</Badge> selected window · no financial status here
            {stateSentence(f) === null ? null : ` · ${stateSentence(f)}`}
          </StatusBar>
          <MetricCards label="Money consequence">
            <MetricCard
              label="Product exposure"
              value={first === undefined ? NOT_ASSESSED : first.state === "WITHHELD" ? "Withheld" : first.state === "UNPRICED" ? "Unpriced" : NOT_ASSESSED}
              note={
                first !== undefined && first.state === "UNPRICED"
                  ? `${boundText(first.quantity_bounds.low)}–${boundText(first.quantity_bounds.high)} degC_min`
                  : first !== undefined && first.state === "WITHHELD"
                    ? (limitText(first.reason) ?? NOT_RECORDED)
                    : "No product exposure consequence assessed"
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
                      <th scope="row">
                        {`Bounded chamber temperature exposure: ${boundText(c.quantity_bounds.low)}–${boundText(c.quantity_bounds.high)} degC_min`}
                        {[c.reason, c.limitation].filter(Boolean).map((t) => (
                          <small className="cold-site-detail" key={t}>
                            {plainLimitation(t!)}
                          </small>
                        ))}
                      </th>
                      <td>Stock value × product response rule — not declared</td>
                      <td>{withheld ? "Withheld" : "Not priced"}</td>
                      <td>
                        <Badge tone="neutral">{withheld ? "Withheld" : "Unpriced"}</Badge>
                      </td>
                      <td>{finding === null ? NOT_ASSESSED : claimWord(finding.claim_level)}</td>
                      <td>{finding === null ? "Finding link not available" : <Link to={findingLink(finding.finding_id)}>{finding.title}</Link>}</td>
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
            <ExactReferences
              name="cold-site-basis-references"
              references={exposures.flatMap((c, i) => {
                const b = c.exact_basis;
                const n = exposures.length > 1 ? ` ${i + 1}` : "";
                return [
                  { label: `Finding version${n}`, value: b.finding_revision_id },
                  { label: `Episode version${n}`, value: b.episode_revision_id },
                  { label: `Assessment version${n}`, value: b.assessment_revision_id },
                  { label: `Accepted records${n}`, value: b.evidence_ids.length === 0 ? null : b.evidence_ids.join(", ") },
                  { label: `Source check${n}`, value: b.source_gate_sha256 },
                  { label: `Assumption versions${n}`, value: b.assumption_revision_ids.length === 0 ? null : b.assumption_revision_ids.join(", ") },
                  { label: `Consequence basis${n}`, value: b.consequence_basis_sha256 },
                ];
              })}
            />
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
              <p className="v69-chart-note">No assumption in use · Cold stock and exposure assumptions have not been declared</p>
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

function AssumptionValues({ read }: { read: ColdAssumptionsRead }) {
  return (
    <KeyValues
      label="Assumptions in use"
      rows={[
        ...ASSUMPTION_ROWS.map(([key, label]) => [label, assumptionValue(read, key), key] as [string, string, string]),
        ["Currency", read.currency_state === "UNDECLARED" ? "Not declared" : NOT_RECORDED, "currency"],
      ]}
    />
  );
}

/* ---------- cold-assumptions ---------- */

function AssumptionsScreen(p: ScreenProps) {
  const read = useColdRead(() => p.client.getAssumptions(p.siteId, p.window), keyOf(p, "s"));
  if (read === null) return <p>{COLD_ASSESSMENT_LOADING}</p>;
  const s = value(read);
  const refused = refusalOf(read);
  const stock = s === null ? "Not declared" : assumptionValue(s, "cold_stock_quantity") === "Not declared" || assumptionValue(s, "cold_stock_unit_value") === "Not declared" ? "Not declared" : `${assumptionValue(s, "cold_stock_quantity")} × ${assumptionValue(s, "cold_stock_unit_value")}`;
  const rows: [string, string, string][] = [
    ["Stock value in chamber", stock, "Pricing product exposure"],
    ["Product exposure rule", s === null ? "Not declared" : assumptionValue(s, "cold_exposure_rule"), "Translating thermal exposure"],
    ["Currency", s === null || s.currency_state === "UNDECLARED" ? "Not declared" : NOT_RECORDED, "Displaying a priced consequence"],
  ];
  return (
    <>
      {s === null ? null : (
        <StatusBar label="Selected window">
          {stateSentence(s) === null ? selectionLine(s, true) : `${selectionLine(s, true)} · ${stateSentence(s)}`}
        </StatusBar>
      )}
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
              {rows.map(([label, v, used]) => (
                <tr key={label} data-assumption-row={label}>
                  <th scope="row">{label}</th>
                  <td>{v === "Not declared" ? <Badge tone="neutral">{v}</Badge> : v}</td>
                  <td>{used}</td>
                </tr>
              ))}
            </tbody>
          </DataTable>
          <p className="v69-chart-note">No assumption in use · Cold stock and exposure assumptions have not been declared</p>
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
