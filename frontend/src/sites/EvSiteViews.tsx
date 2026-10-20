import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

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
import { UnavailableInline, UnavailableLinkEntry } from "../ui/UnavailableEntry";
import { coldWindowSearch } from "./coldAssessmentClient";
import { eatTime } from "./coldSiteViews";
import { date, dayHm, hm } from "./coldFormat";
import { evRefusalText } from "./EvAssessmentViews";
import type { EvEnvelope, EvRead, EvWindowQuery } from "./evAssessmentClient";
import type {
  EvAnalysisItem,
  EvAnalysisRead,
  EvAssumptionsRead,
  EvCapability,
  EvConsequence,
  EvCoverage,
  EvOverviewRead,
  EvSiteClient,
  EvSource,
} from "./evSiteClient";
import { EvPowerChart } from "./assessmentGraphics";
import "./w2-ev-site.css";

/*
 * W2-07 commits 4-5: the five EV Site screens of an EV_CHARGING Site in their exact v69 panel slots
 * (`.agent/W2-07-build-spec.md` "Commits 4-5", closure section 4, "Run 6 rulings (q5)" and "Run 7 rulings (q6)"):
 *
 *   ev                    1 What happened on the service day, 2 Charging activity and site power, 3 Needs attention,
 *                         4 Bounded money consequence, 5 Next step
 *   ev-evidence           1 What we can conclude now, 2 Data sources · data quality, not equipment condition,
 *                         3 Most useful next evidence
 *   ev-evidence-analysis  1 Accepted records behind the conclusions, 2 How a claim limit is set
 *   ev-financials         1 What happened → what it means in money, 2 Assumptions in use, 3 Not included
 *   ev-assumptions        1 Financial assumptions
 *
 * Every visible string is the copy ledger's; dynamic values come only from the selected reads. A refused read keeps
 * every panel and states the typed refusal inside it; no mock value is a fallback, and a null amount is never zero.
 */

export type EvSiteView = "overview" | "evidence" | "analysis" | "financials" | "assumptions";

export const EV_SITE_HEADING_ID = "ev-site-heading";
export const EV_SITE_LOADING = "Loading the site's evidence.";
const NO_LINK = "No linked page for this item";
const NOT_RECORDED = "Not recorded";

export interface EvSiteRoutes {
  overview: string;
  evidence: string;
  analysis: string;
  financials: string;
  assumptions: string;
  sessions: string;
  finding: (findingId: string) => string;
}

/* ---------- words ---------- */

const CLAIM_LABEL: Record<string, string> = {
  SESSION_OUTCOME: "Session outcomes",
  SERVICE_STATE: "Connector availability",
  DELIVERED_ENERGY: "Delivered energy",
  FAULT_ASSOCIATION: "Cause of interruption",
  SITE_POWER_CONTEXT: "Site power context",
  POWER_CONSTRAINT: "Site power constraint",
  GROSS_TARIFF_SCENARIO: "Gross tariff scenario",
};
const CAP_ROWS: { key: string; label: string; claim: string }[] = [
  { key: "sessions", label: "Session outcomes", claim: "SESSION_OUTCOME" },
  { key: "availability", label: "Connector availability", claim: "SERVICE_STATE" },
  { key: "energy", label: "Delivered energy", claim: "DELIVERED_ENERGY" },
  { key: "cause", label: "Cause of interruption", claim: "FAULT_ASSOCIATION" },
];
const ROLE_LABEL: Record<string, string> = {
  session_event: "Session start and end reports",
  session_terminal: "Session end report",
  connector_meter_delta: "Connector meter intervals",
  connector_status: "Connector status reports",
  fault_event: "Connector fault reports",
  site_import: "Site import power",
  requested_power: "Requested vehicle power",
  allocated_limit: "Allocated power limit",
  ev_gross_tariff_per_kwh: "Published EV tariff",
};
const roleLabel = (role: string) => ROLE_LABEL[role] ?? "Configured EV reading";
const CHIP: Record<string, string> = { SUPPORTED: "Full", LIMITED: "Limited", UNAVAILABLE: "None", CONTRADICTORY: "Contradictory" };
const CONTACT: Record<string, string> = { RECENT: "Recent", OLD: "Old", NEVER: "Never", UNKNOWN: "Unknown", MIXED: "Mixed" };
const QUALITY: Record<string, string> = { GOOD: "Good", DEGRADED: "Limited", MIXED: "Mixed", NO_FACT: "No fact" };
const ATTENTION: Record<string, string> = {
  PENDING: "New evidence pending",
  FAULT_ABORT: "Fault-aborted session",
  INCOMPLETE_SESSION: "End record missing",
  METER_OR_SOURCE_GAP: "Meter or source gap",
  TARIFF_MISSING: "No tariff set for estimates",
};
const SLOT_LABEL: Record<string, string> = { CONNECTOR_1: "Connector 1", CONNECTOR_2: "Connector 2", SITE_METER: "Site meter", BILLING: "Billing system" };
const SLOT_AFFECTS: Record<string, string> = { CONNECTOR_1: "Sessions", CONNECTOR_2: "Sessions", SITE_METER: "Site power", BILLING: "Collections not assessed" };
const EVENT_KINDS = ["EV_SESSION_START", "EV_CONNECTOR_FAULT", "EV_SESSION_ABORT", "EV_SESSION_END"];
/** Review r1 L4: the same-instant chronology order (the array order of `EVENT_KINDS`). */
const kindRank = (kind: string | null) => (kind === null ? EVENT_KINDS.length : EVENT_KINDS.indexOf(kind));
const TONE: Record<string, "green" | "amber" | "red"> = {
  Full: "green",
  Good: "green",
  Recent: "green",
  "Evidence supported": "green",
  Limited: "amber",
  Old: "amber",
  Never: "amber",
  Mixed: "amber",
  "Not declared": "amber",
  "Evidence limited": "amber",
  Unpriced: "amber",
  Withheld: "amber",
  Contradictory: "red",
  "Evidence contradictory": "red",
};

function Chip({ word }: { word: string }) {
  const tone = TONE[word];
  return (
    <Badge tone="neutral" className={tone === undefined ? "ev-site-chip" : `ev-site-chip ev-tone--${tone}`}>
      {word}
    </Badge>
  );
}

const short = (id: string | null | undefined) => (id ? id.slice(0, 8) : "Unknown");
const pad = (n: number) => String(n).padStart(2, "0");
function hms(value: string | null | undefined): string {
  const d = date(value);
  return d === null ? NOT_RECORDED : `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())}`;
}
const instant = (value: string | null | undefined) => (value ? `${value}` : NOT_RECORDED);

/** Display rounding of an exact Decimal string to two places, half even on the absolute value, without a float. */
export function money2(value: string): string {
  const negative = value.startsWith("-");
  const [whole, frac = ""] = (negative ? value.slice(1) : value).split(".");
  const padded = frac.padEnd(2, "0");
  let cents = BigInt(whole || "0") * 100n + BigInt(padded.slice(0, 2));
  const rest = padded.slice(2);
  if (/[1-9]/.test(rest)) {
    const half = rest[0] === "5" && !/[1-9]/.test(rest.slice(1));
    if (rest[0] > "5" || (rest[0] === "5" && !half) || (half && cents % 2n === 1n)) cents += 1n;
  }
  const text = `${cents / 100n}.${String(cents % 100n).padStart(2, "0")}`;
  return negative && cents !== 0n ? `-${text}` : text;
}

/** q6 R3: the unit-specific coverage wording, or the claim's own limitation when coverage is unproved. */
function coverageText(c: EvCoverage, limitation: string | null): string {
  if (c.unit === "WINDOW_SECONDS" && c.known_seconds !== null && c.expected_seconds !== null) {
    return `${c.known_seconds}/${c.expected_seconds} s of selected window covered`;
  }
  if (c.unit === "SESSION_SECONDS" && c.known_seconds !== null && c.expected_seconds !== null) {
    return `${c.known_seconds}/${c.expected_seconds} session-seconds covered`;
  }
  return limitation ?? "Coverage duration cannot be calculated from the selected records.";
}

/* ---------- links ---------- */

const sel = (base: string, window: EvWindowQuery) => `${base}${coldWindowSearch(window)}`;

/** The UI address of a selected read's link: the five EV Site paths are already UI paths; a W2-06 Finding is an API path. */
export function evSiteUiHref(link: string | null | undefined, routes: EvSiteRoutes): string | null {
  if (link === null || link === undefined) return null;
  const finding = /^\/api\/sites\/[^/?]+\/ev\/findings\/([^/?]+)(\?.*)?$/.exec(link);
  if (finding !== null) return `${routes.finding(decodeURIComponent(finding[1]))}${finding[2] ?? ""}`;
  return /^\/sites\/[^/?]+\/ev(\/|\?|$)/.test(link) ? link : null;
}

function ToLink({ href, children, data }: { href: string | null; children: ReactNode; data?: Record<string, string> }) {
  return href === null ? (
    <span className="ev-site-noop" {...data}>
      {NO_LINK}
    </span>
  ) : (
    <Link to={href} {...data}>
      {children}
    </Link>
  );
}

function linkLabel(link: string | null): string {
  if (link === null) return NO_LINK;
  if (link.includes("/findings/")) return "Open Finding →";
  if (link.includes("/evidence/analysis")) return "Evidence › Analysis →";
  if (link.includes("/financials")) return "Financials →";
  if (link.includes("/evidence")) return "Evidence →";
  return "Open →";
}

/* ---------- reads ---------- */

function useEvRead<T>(load: () => Promise<EvRead<T>>, key: string): EvRead<T> | null {
  const [state, setState] = useState<{ key: string; value: EvRead<T> } | null>(null);
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

const loaded = <T,>(read: EvRead<T> | null): T | null => (read !== null && read.status === "loaded" ? read.value : null);
const refusal = (read: EvRead<unknown> | null): string | null => (read === null || read.status === "loaded" ? null : evRefusalText(read));

/** q5 copy ledger: the chart needs every selected Analysis page, so the cursor is followed (200 per page). */
export async function loadAllAnalysis(client: EvSiteClient, siteId: string, window: EvWindowQuery): Promise<EvRead<EvAnalysisRead>> {
  const first = await client.getAnalysis(siteId, window, { limit: 200 });
  if (first.status !== "loaded") return first;
  const items = [...first.value.items];
  let cursor = first.value.next_cursor;
  for (let page = 0; cursor !== null && page < 50; page += 1) {
    const next = await client.getAnalysis(siteId, window, { cursor, limit: 200 });
    if (next.status !== "loaded") return next;
    items.push(...next.value.items);
    cursor = next.value.next_cursor;
  }
  return { status: "loaded", value: { ...first.value, items, next_cursor: null } };
}

function Gap({ id, children }: { id: string; children: ReactNode }) {
  return (
    <p className="not-available-yet v69-chart-note" data-panel-gap={id}>
      {children}
    </p>
  );
}

/* ---------- shared strip pieces ---------- */

/** Evidence aggregate over the four mock-visible capabilities (review r1 L2; copy ledger "Shared strip"). */
export function evidenceAggregate(caps: EvCapability[]): "Evidence supported" | "Evidence limited" | "Evidence contradictory" | "Evidence unknown" {
  const states = CAP_ROWS.map((r) => caps.find((c) => c.claim === r.claim)?.state ?? "UNAVAILABLE");
  if (states.length === 0 || states.every((s) => s === "UNAVAILABLE")) return "Evidence unknown";
  if (states.includes("CONTRADICTORY")) return "Evidence contradictory";
  if (states.every((s) => s === "SUPPORTED")) return "Evidence supported";
  return "Evidence limited";
}

function stateLine(env: EvEnvelope): string | null {
  if (env.currentness.state === "PENDING_RECOMPUTE") return "New evidence is being assessed";
  if (env.currentness.state === "HISTORICAL") return `Historical selection · ${dayHm(env.window.known_at)} UTC`;
  return null;
}

function Provenance({ env }: { env: EvEnvelope }) {
  if (env.source_provenance.classification !== "REGISTERED_SIMULATION") return null;
  return (
    <>
      {" "}
      <Badge tone="provenance">Generated test data</Badge>
      <span className="ev-site-strip-note" data-ev-provenance-note>
        Registered test reports; not physical charger observations.
      </span>
    </>
  );
}

function StateNote({ env }: { env: EvEnvelope }) {
  const line = stateLine(env);
  return line === null ? null : (
    <span className="ev-site-strip-note" data-ev-state-line>
      {line}
    </span>
  );
}

/** The selected window and cutoff (copy ledger: `{from}–{to} UTC · known at {known_at} UTC`). */
function WindowBar({ env, extra }: { env: EvEnvelope | null; extra?: string | null }) {
  if (env === null) return null;
  const w = env.window;
  const text = w.from === null || w.to === null ? "No window selected" : `${dayHm(w.from)}–${dayHm(w.to)} UTC · known at ${dayHm(w.known_at)} UTC`;
  return (
    <p className="site-date-bar" data-ev-window>
      <span className="site-date-bar__window">{text}</span>
      {extra ? <span className="site-date-bar__cutoff">{extra}</span> : null}
    </p>
  );
}

/* ---------- frame ---------- */

export interface EvSiteFrameProps {
  view: EvSiteView;
  siteId: string;
  siteName: string;
  mode: string | null;
  window: EvWindowQuery;
  client: EvSiteClient;
  routes: EvSiteRoutes;
  tabs: ReactNode;
  parentTrail: Crumb[];
}

const SCREEN: Record<EvSiteView, string> = {
  overview: "ev",
  evidence: "ev-evidence",
  analysis: "ev-evidence-analysis",
  financials: "ev-financials",
  assumptions: "ev-assumptions",
};
const DESCRIPTION: Record<EvSiteView, string> = {
  overview: SITE_SCREEN_DESCRIPTIONS.mini,
  evidence: SITE_SCREEN_DESCRIPTIONS.evidence,
  analysis: SITE_SCREEN_DESCRIPTIONS["evidence-analysis"],
  financials: SITE_SCREEN_DESCRIPTIONS.financials,
  assumptions: SITE_SCREEN_DESCRIPTIONS.assumptions,
};
const CRUMB: Record<EvSiteView, Crumb[]> = {
  overview: [],
  evidence: [{ label: "Evidence" }],
  analysis: [{ label: "Evidence" }, { label: "Analysis" }],
  financials: [{ label: "Financials" }],
  assumptions: [{ label: "Financials" }, { label: "Assumptions" }],
};

/** Route-local tabs, all live: Evidence `Overview | Analysis`, Financials `Overview | Assumptions` (q5; +0 unavailable). */
function Subtabs({ view, routes, window }: { view: EvSiteView; routes: EvSiteRoutes; window: EvWindowQuery }) {
  const evidence = view === "evidence" || view === "analysis";
  const financial = view === "financials" || view === "assumptions";
  if (!evidence && !financial) return null;
  const items: [EvSiteView, string, string][] = evidence
    ? [
        ["evidence", "Overview", sel(routes.evidence, window)],
        ["analysis", "Analysis", sel(routes.analysis, window)],
      ]
    : [
        ["financials", "Overview", sel(routes.financials, window)],
        ["assumptions", "Assumptions", sel(routes.assumptions, window)],
      ];
  return (
    <nav className="site-tabs site-subtabs" aria-label={evidence ? "Evidence sections" : "Financials sections"}>
      <ol className="site-tabs__list">
        {items.map(([id, label, href]) => (
          <li className="site-tabs__item" key={id}>
            <Link className="site-tabs__link" to={href} data-ev-subtab={id} aria-current={id === view ? "page" : undefined}>
              {label}
            </Link>
          </li>
        ))}
      </ol>
    </nav>
  );
}

export function EvSiteFrame(props: EvSiteFrameProps) {
  const { view } = props;
  return (
    <main aria-labelledby={EV_SITE_HEADING_ID} data-ev-site-view={SCREEN[view]}>
      <Breadcrumbs trail={[...props.parentTrail, ...CRUMB[view]]} />
      <SitePageHeader siteName={props.siteName} siteId={props.siteId} mode={props.mode} description={DESCRIPTION[view]} headingId={EV_SITE_HEADING_ID} />
      {props.tabs}
      <Subtabs view={view} routes={props.routes} window={props.window} />
      {view === "overview" ? (
        <OverviewScreen {...props} />
      ) : view === "evidence" ? (
        <EvidenceScreen {...props} />
      ) : view === "analysis" ? (
        <AnalysisScreen {...props} />
      ) : view === "financials" ? (
        <FinancialsScreen {...props} />
      ) : (
        <AssumptionsScreen {...props} />
      )}
    </main>
  );
}

const keyOf = (p: EvSiteFrameProps, name: string) => `${name}|${p.siteId}|${p.window.from ?? ""}|${p.window.to ?? ""}|${p.window.known_at ?? ""}`;

/* ---------- ev (Overview) ---------- */

function objectiveHours(o: EvOverviewRead): string {
  const obj = o.objective;
  if (!obj.service_schedule_declared) return "Service window not declared";
  if (obj.configured_service_windows.length === 0) return "No configured service hours overlap this selection";
  if (obj.configured_service_window !== null && obj.configured_service_windows.length === 1) {
    return `Configured service hours ${hm(obj.configured_service_window.from)}–${hm(obj.configured_service_window.to)} UTC`;
  }
  return "Configured service hours vary by connector";
}

function sessionWord(o: EvOverviewRead): string {
  if (o.currentness.state === "PENDING_RECOMPUTE") return "Evidence pending";
  switch (o.status.state) {
    case "OBSERVED_SESSIONS":
      return "Sessions observed";
    case "NO_SESSIONS_OBSERVED":
      return "No sessions observed";
    case "CONTRADICTORY":
      return "Records disagree";
    default:
      return "Unknown";
  }
}

function OverviewCards({ o, caps, routes }: { o: EvOverviewRead; caps: EvCapability[]; routes: EvSiteRoutes }) {
  const d = o.denominator;
  const sessionNote =
    d.started === null
      ? "Session outcomes not assessed"
      : `${d.completed ?? "Unknown"} completed · ${d.observed_abort ?? "Unknown"} observed aborts · ${d.incomplete ?? "Unknown"} incomplete · of ${d.started} attempts`;
  const p = o.site_power;
  const peak = p.observed_peak_kw === null ? "Unknown" : `${p.observed_peak_kw} kW observed peak`;
  const powerNote = p.observed_peak_kw === null ? (p.limitation ?? "No accepted Site import report") : coverageText(p.coverage, p.limitation);
  const word = evidenceAggregate(caps);
  const window = o.window;
  return (
    <MetricCards columns={5} label="EV charging conditions">
      <MetricCard label={<Link to={sel(routes.sessions, window)}>Session service</Link>} value={sessionWord(o)} note={sessionNote} tone="muted" assessment data={{ "data-ev-card": "sessions" }} />
      <MetricCard label="Availability" value="Not assessed" note="Connector availability is not assessed" tone="muted" assessment data={{ "data-ev-card": "availability" }} />
      <MetricCard label="Site power" value={peak} note={powerNote} tone="muted" assessment data={{ "data-ev-card": "power" }} />
      <MetricCard label="Charger condition" value="Not assessed" note="Source reporting is not equipment condition" tone="muted" assessment data={{ "data-ev-card": "charger" }} />
      <MetricCard
        label={<Link to={sel(routes.evidence, window)}>Evidence</Link>}
        value={word.replace("Evidence ", "").replace(/^./, (c) => c.toUpperCase())}
        note={caps.length === 0 ? "Evidence coverage not assessed" : `${CAP_ROWS.length} capabilities · no single score`}
        tone="muted"
        assessment
        data={{ "data-ev-card": "evidence" }}
      />
    </MetricCards>
  );
}

const CHRONOLOGY_SLOTS = 7;

function chronology(items: EvAnalysisItem[], incomplete: boolean): { events: TimelineEvent[]; extra: EvAnalysisItem[] } {
  const accepted = items
    .filter((i) => i.record_kind !== null && EVENT_KINDS.includes(i.record_kind) && i.use !== "EXCLUDED")
    .sort(
      (a, b) =>
        (a.source_time ?? "").localeCompare(b.source_time ?? "") ||
        kindRank(a.record_kind) - kindRank(b.record_kind) ||
        a.evidence_id.localeCompare(b.evidence_id),
    );
  const room = incomplete ? CHRONOLOGY_SLOTS - 1 : CHRONOLOGY_SLOTS;
  const shown = accepted.slice(0, room);
  const events: TimelineEvent[] = shown.map((i) => ({
    key: i.evidence_id,
    time: `${hm(i.source_time)} UTC`,
    title: (
      <>
        {`${i.value_display ?? "Accepted event"} · `}
        <span aria-label={`Record ${i.evidence_id}`}>{`Record ${short(i.evidence_id)}`}</span>
      </>
    ),
    tone: i.record_kind === "EV_CONNECTOR_FAULT" || i.record_kind === "EV_SESSION_ABORT" ? "danger" : undefined,
  }));
  if (incomplete) events.push({ key: "end-missing", time: "—", title: "End record missing", tone: "gap" });
  while (events.length < CHRONOLOGY_SLOTS) events.push({ key: `empty-${events.length}`, time: "—", title: "No accepted event", tone: "gap" });
  return { events, extra: accepted };
}

function OverviewScreen(p: EvSiteFrameProps) {
  const overview = useEvRead(() => p.client.getOverview(p.siteId, p.window), keyOf(p, "o"));
  const evidence = useEvRead(() => p.client.getEvidence(p.siteId, p.window), keyOf(p, "e"));
  const analysis = useEvRead(() => loadAllAnalysis(p.client, p.siteId, p.window), keyOf(p, "a"));
  const financials = useEvRead(() => p.client.getFinancials(p.siteId, p.window), keyOf(p, "f"));
  if (overview === null || evidence === null || analysis === null || financials === null) return <p>{EV_SITE_LOADING}</p>;
  const o = loaded(overview);
  const refused = refusal(overview);
  const e = loaded(evidence);
  const caps = e?.capabilities ?? [];
  const a = loaded(analysis);
  const f = loaded(financials);
  const routes = p.routes;
  const incomplete = o?.needs_attention.some((n) => n.code === "INCOMPLETE_SESSION") ?? false;
  const chron = chronology(a?.items ?? [], incomplete);
  const money = o?.consequence_summary;
  const next = e?.next_evidence[0] ?? null;
  const limit = o?.objective.site_import_limit_kw ?? null;
  return (
    <>
      {o === null ? null : (
        <>
          <WindowBar env={o} />
          <StatusBar label="EV Site state" action={<Link to={sel(routes.evidence, o.window)}>Inspect evidence</Link>}>
            <Chip word={evidenceAggregate(caps)} />
            <Provenance env={o} />
            <StateNote env={o} />
          </StatusBar>
          <p className="v69-objective" data-ev-objective>
            {`${o.objective.text} ${objectiveHours(o)} · ${limit === null ? "Site limit not declared" : `Site import limit ${limit} kW`}`}
          </p>
          <OverviewCards o={o} caps={caps} routes={routes} />
        </>
      )}
      <Panel
        heading="What happened on the service day"
        headingId="ev-site-day-heading"
        description="Plain sequence from accepted charger and meter records"
        actions={o === null ? undefined : <Link to={sel(routes.sessions, o.window)}>Review sessions →</Link>}
      >
        {refused !== null ? (
          <Gap id="ev-site-day">{refused}</Gap>
        ) : (
          <>
            <CausalTimeline events={chron.events} label="Service day sequence" />
            <p className="prose" data-ev-day-limit>
              {o!.status.limitation ?? "Only accepted records are shown; the cause of an interruption is not established."}
            </p>
            <Disclosure summary="Event details" name="ev-site-event-details" variant="tech">
              {chron.extra.length === 0 ? (
                <p>No accepted event in this window</p>
              ) : (
                <ul className="ev-site-list">
                  {chron.extra.map((i) => (
                    <li key={i.evidence_id} data-ev-event={i.evidence_id}>
                      <code data-vocabulary-exempt="source-reference">{i.evidence_id}</code>
                      {` · ${i.value_display ?? "Accepted event"} · ${i.source_label} · source ${instant(i.source_time)} · received ${instant(i.received_at)} · use ${i.use ?? NOT_RECORDED}${i.reason ? ` · ${i.reason}` : ""}`}
                    </li>
                  ))}
                </ul>
              )}
            </Disclosure>
          </>
        )}
      </Panel>
      <div className="panel-pair ev-site-pair">
        <Panel
          heading="Charging activity and site power"
          headingId="ev-site-power-heading"
          description="Power is operating context, not proof of charger condition or cause."
        >
          {refused !== null ? (
            <Gap id="ev-site-power">{refused}</Gap>
          ) : refusal(analysis) !== null ? (
            <Gap id="ev-site-power">{refusal(analysis)}</Gap>
          ) : o!.window.from === null || o!.window.to === null ? (
            <Gap id="ev-site-power">No accepted report</Gap>
          ) : (
            <>
              <EvPowerChart items={a!.items} from={o!.window.from} to={o!.window.to} limitKw={o!.site_power.configured_limit_kw} />
              <Disclosure summary="Chart details" name="ev-site-chart-details" variant="tech">
                <p>{`Site import: ${coverageText(o!.site_power.coverage, o!.site_power.limitation)}`}</p>
                {(["connector_meter_delta", "site_import"] as const).map((role) => {
                  const rows = a!.items.filter((i) => i.role === role);
                  return (
                    <div key={role} data-ev-series={role}>
                      <p>
                        <strong>{role === "site_import" ? "Site import" : "Connector energy"}</strong>
                      </p>
                      {rows.length === 0 ? (
                        <p>No accepted report</p>
                      ) : (
                        <ul className="ev-site-list">
                          {rows.map((i) => (
                            <li key={i.evidence_id}>
                              <code data-vocabulary-exempt="source-reference">{i.evidence_id}</code>
                              {` · ${instant(i.interval_start)} to ${instant(i.interval_end)} · ${i.value_display ?? NOT_RECORDED}${i.unit ? ` ${i.unit}` : ""}`}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  );
                })}
              </Disclosure>
            </>
          )}
          <p className="ev-site-link">
            <UnavailableInline label="Open single line diagram" />
          </p>
        </Panel>
        <Panel heading="Needs attention" headingId="ev-site-attention-heading">
          {refused !== null ? (
            <Gap id="ev-site-attention">{refused}</Gap>
          ) : o!.needs_attention.length === 0 ? (
            <Gap id="ev-site-attention">No recorded attention item for this window</Gap>
          ) : (
            <>
              <AttentionList
                label="Needs attention"
                items={o!.needs_attention.slice(0, 3).map((n) => ({
                  key: n.code,
                  title: ATTENTION[n.code] ?? "Attention item",
                  body: n.text,
                  action: (
                    <p className="ev-site-link">
                      <ToLink href={evSiteUiHref(n.link, routes)} data={{ "data-attention-link": n.code }}>
                        {linkLabel(n.link)}
                      </ToLink>
                    </p>
                  ),
                }))}
              />
              {o!.needs_attention.length > 3 ? (
                <Disclosure summary="Attention details" name="ev-site-attention-details" variant="tech">
                  <ul className="ev-site-list">
                    {o!.needs_attention.slice(3).map((n) => (
                      <li key={n.code}>
                        {`${ATTENTION[n.code] ?? "Attention item"} · ${n.text} · `}
                        <ToLink href={evSiteUiHref(n.link, routes)}>{linkLabel(n.link)}</ToLink>
                      </li>
                    ))}
                  </ul>
                </Disclosure>
              ) : null}
            </>
          )}
        </Panel>
      </div>
      <div className="panel-pair ev-site-pair">
        <Panel heading="Bounded money consequence" headingId="ev-site-money-heading">
          {refused !== null ? (
            <Gap id="ev-site-money">{refused}</Gap>
          ) : (
            <>
              <div className="metric-value v69-metric__value ev-site-amount" data-ev-money={money!.state ?? "none"}>
                {money!.state === "ESTIMATED" && money!.amount !== null && money!.currency !== null
                  ? `${money!.currency} ${money2(money!.amount)} gross tariff estimate`
                  : money!.state === "UNPRICED"
                    ? "Unpriced"
                    : money!.state === "WITHHELD"
                      ? "Withheld"
                      : "No gross tariff scenario assessed"}
              </div>
              <p className="prose">
                {money!.state === "ESTIMATED"
                  ? `Gross tariff estimate for ${money!.quantity_kwh} kWh delivered with complete coverage. Not cash collected.`
                  : (money!.limitation ?? "No gross tariff scenario assessed.")}
              </p>
              {f !== null && f.consequence !== null ? <ScenarioDetails c={f.consequence} /> : null}
              <p className="ev-site-link">
                <ToLink href={evSiteUiHref(o!.links.financials, routes)}>Open financial bridge →</ToLink>
              </p>
            </>
          )}
        </Panel>
        <Panel heading="Next step" headingId="ev-site-next-heading">
          {refused !== null ? (
            <Gap id="ev-site-next">{refused}</Gap>
          ) : next === null ? (
            <Gap id="ev-site-next">No recorded next step</Gap>
          ) : (
            <div data-ev-next={next.code}>
              <h3>{next.text}</h3>
              <p className="prose">{next.why}</p>
            </div>
          )}
          {refused !== null ? null : <UnavailableLinkEntry label="Review recommendation" />}
        </Panel>
      </div>
    </>
  );
}

function ScenarioDetails({ c }: { c: EvConsequence }) {
  return (
    <Disclosure summary="Scenario details" name="ev-site-scenario-details" variant="tech">
      <ul className="ev-site-list">
        <li>{`Exact amount: ${c.amount === null ? "Not assessed" : `${c.currency ?? ""} ${c.amount}`.trim()}`}</li>
        <li>
          Tariff revision: <code data-vocabulary-exempt="source-reference">{c.tariff_revision_id ?? "Not declared"}</code>
        </li>
        <li>{`Source gate: ${c.source_gate ?? NOT_RECORDED}`}</li>
        <li>
          Overlap group: <code data-vocabulary-exempt="source-reference">{c.overlap_group ?? NOT_RECORDED}</code>
        </li>
        {c.reason === "HISTORICAL_CURRENT_CLAIM" || c.label !== undefined ? <li>Historical scenario</li> : null}
      </ul>
    </Disclosure>
  );
}

/* ---------- ev-evidence ---------- */

function capOf(caps: EvCapability[], claim: string): EvCapability | null {
  return caps.find((c) => c.claim === claim) ?? null;
}

function chipOf(cap: EvCapability | null): string {
  return cap === null ? "None" : (CHIP[cap.state] ?? "None");
}

function canSay(row: string, cap: EvCapability | null, o: EvOverviewRead | null): string {
  if (row === "availability") return "Not assessed";
  if (row === "sessions") {
    const d = o?.denominator;
    if (d === undefined || d.started === null) return "Session outcomes not assessed";
    return `${d.completed ?? "Unknown"} completed · ${d.observed_abort ?? "Unknown"} observed aborts · ${d.incomplete ?? "Unknown"} incomplete`;
  }
  if (row === "energy") {
    const kwh = o?.energy.complete_kwh ?? null;
    return kwh === null ? "Complete delivered energy not established" : `${kwh} kWh with complete meter coverage`;
  }
  return (o?.findings.count ?? 0) > 0 && cap !== null && cap.state !== "UNAVAILABLE" ? "Interruption observed; cause not established" : "Cause not established";
}

function contactDetail(state: string): string {
  return state === "MIXED" ? "Source contacts differ" : state === "UNKNOWN" ? "No source-specific record" : CONTACT[state] ?? "Unknown";
}

function EvidenceScreen(p: EvSiteFrameProps) {
  const evidence = useEvRead(() => p.client.getEvidence(p.siteId, p.window), keyOf(p, "e"));
  const overview = useEvRead(() => p.client.getOverview(p.siteId, p.window), keyOf(p, "o"));
  if (evidence === null || overview === null) return <p>{EV_SITE_LOADING}</p>;
  const e = loaded(evidence);
  const refused = refusal(evidence);
  const o = loaded(overview);
  const caps = e?.capabilities ?? [];
  const routes = p.routes;
  const analysisHref = e === null ? null : evSiteUiHref(e.links.analysis, routes);
  const financialsHref = e === null ? null : evSiteUiHref(e.links.financials, routes);
  const sessionsHref = e === null ? null : sel(routes.sessions, e.window);
  const word = evidenceAggregate(caps);
  const rowChips = CAP_ROWS.map((r) => chipOf(capOf(caps, r.claim)));
  const count = (w: string) => rowChips.filter((c) => c === w).length;
  const checked = e?.sources.find((s) => s.contact.checked_at !== null)?.contact.checked_at ?? null;
  return (
    <>
      <WindowBar env={e} />
      {e === null ? null : (
        <StatusBar label="Evidence state" action={<UnavailableInline label="Portfolio evidence" />}>
          <Chip word={word} />
          {` ${CAP_ROWS.length} capabilities · ${count("Full")} full · ${count("Limited")} limited · ${count("None")} none${count("Contradictory") > 0 ? ` · ${count("Contradictory")} contradictory` : ""} · no single score`}
          <Provenance env={e} />
          <StateNote env={e} />
        </StatusBar>
      )}
      <Panel heading="What we can conclude now" headingId="ev-site-conclude-heading" description="Evidence readiness is not equipment condition">
        {refused !== null ? (
          <Gap id="ev-site-conclude">{refused}</Gap>
        ) : (
          <>
            <DataTable labelledBy="ev-site-conclude-heading">
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
                  const cap = capOf(caps, row.claim);
                  const missing = cap?.missing_roles ?? [];
                  const nextHref = row.key === "sessions" ? sessionsHref : row.key === "energy" ? financialsHref : null;
                  return (
                    <tr key={row.key} data-capability-row={row.key}>
                      <th scope="row">{row.label}</th>
                      <td>
                        <Chip word={chipOf(cap)} />
                      </td>
                      <td>{canSay(row.key, cap, o)}</td>
                      <td>{missing.length === 0 ? "No required role missing" : missing.map(roleLabel).join(", ")}</td>
                      <td>
                        {nextHref === null ? (
                          <UnavailableInline label={row.key === "availability" ? "Availability" : "Work"} />
                        ) : (
                          <Link to={nextHref}>{row.key === "sessions" ? "Review sessions" : "Review financials"}</Link>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </DataTable>
            <Disclosure summary="Capability details" name="ev-site-capability-details" variant="tech">
              {caps.length === 0 ? (
                <p>Claim limit not assessed</p>
              ) : (
                <ul className="ev-site-list">
                  {caps.map((c) => (
                    <li key={c.claim} data-capability-detail={c.claim}>
                      {`${CLAIM_LABEL[c.claim] ?? "Claim"}: ${chipOf(c)} · ${coverageText(c.coverage, c.limitation)} · requires ${c.required_roles.map(roleLabel).join(", ")}${c.missing_roles.length > 0 ? ` · missing ${c.missing_roles.map(roleLabel).join(", ")}` : ""} · ${c.accepted_evidence_ids.length} accepted records · source ${e!.source_provenance.classification ?? "Unknown"} · known at ${instant(c.as_of)}${c.limitation ? ` · ${c.limitation}` : ""}`}
                    </li>
                  ))}
                </ul>
              )}
            </Disclosure>
          </>
        )}
      </Panel>
      <div className="panel-pair ev-site-pair">
        <Panel heading="Data sources · data quality, not equipment condition" headingId="ev-site-sources-heading">
          {refused !== null ? (
            <Gap id="ev-site-sources">{refused}</Gap>
          ) : (
            <>
              <p className="v69-chart-note" data-ev-contact-checked>
                {`Contact checked at ${checked === null ? NOT_RECORDED : dayHm(checked)} UTC`}
              </p>
              <DataTable labelledBy="ev-site-sources-heading">
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
                  {e!.sources.map((s) => (
                    <SourceRow key={s.slot} s={s} />
                  ))}
                </tbody>
              </DataTable>
              <Disclosure summary="Source details" name="ev-site-source-details" variant="tech">
                {e!.sources.map((s) => (
                  <div className="ev-site-group" key={s.slot} data-source-detail={s.slot}>
                    <p>
                      <strong>{`${SLOT_LABEL[s.slot] ?? s.display_name} · ${s.display_name}`}</strong>
                    </p>
                    <p>{`Contact ${CONTACT[s.contact.state] ?? "Unknown"} · ${contactDetail(s.contact.state)}`}</p>
                    {s.contact.by_source.length === 0 ? (
                      <p>No source-specific record</p>
                    ) : (
                      <ul className="ev-site-list">
                        {s.contact.by_source.map((b) => (
                          <li key={b.source_id} data-source-contact={b.source_id}>
                            Source <code data-vocabulary-exempt="source-reference">{b.source_id}</code>
                            {` · ${CONTACT[b.state] ?? "Unknown"} · diagnostic ${b.diagnostic_id ?? "No source-specific record"} · received ${b.diagnostic_received_at ?? "No source-specific record"} · cadence ${b.cadence_seconds === null ? "No source-specific record" : `${b.cadence_seconds} s`} · contact ${b.last_seen_at ?? "No source-specific record"} · age ${b.age_seconds === null ? "No source-specific record" : `${b.age_seconds} s`}`}
                          </li>
                        ))}
                      </ul>
                    )}
                    <p>{`${s.quality.accepted_count} accepted · ${QUALITY[s.quality.state] ?? "No fact"}${s.roles.length > 0 ? ` · ${s.roles.map(roleLabel).join(", ")}` : ""}`}</p>
                    {s.limitation === null ? null : <p>{s.limitation}</p>}
                  </div>
                ))}
              </Disclosure>
            </>
          )}
        </Panel>
        <Panel heading="Most useful next evidence" headingId="ev-site-next-evidence-heading">
          {refused !== null ? (
            <Gap id="ev-site-next-evidence">{refused}</Gap>
          ) : (
            <>
              <AttentionList
                label="Most useful next evidence"
                items={[0, 1, 2].map((i) => {
                  const n = e!.next_evidence[i];
                  return n === undefined
                    ? { key: `none-${i}`, title: "No further evidence request recorded", body: "" }
                    : {
                        key: n.code,
                        title: n.text,
                        body: n.why,
                        action: (
                          <p className="ev-site-link">
                            <ToLink href={evSiteUiHref(n.link, routes)}>{linkLabel(n.link)}</ToLink>
                          </p>
                        ),
                      };
                })}
              />
              <Disclosure summary="Evidence request details" name="ev-site-request-details" variant="tech">
                {caps.every((c) => c.missing_roles.length === 0) ? (
                  <p>No required role missing</p>
                ) : (
                  <ul className="ev-site-list">
                    {caps
                      .filter((c) => c.missing_roles.length > 0)
                      .map((c) => (
                        <li key={c.claim}>{`${c.missing_roles.map(roleLabel).join(", ")} · limits ${CLAIM_LABEL[c.claim] ?? "a claim"} to ${chipOf(c)}`}</li>
                      ))}
                  </ul>
                )}
              </Disclosure>
            </>
          )}
        </Panel>
      </div>
      {e === null ? null : (
        <Notice tone="blue" data={{ "data-ev-notice": "analysis" }}>
          Record-level detail and each claim limit are in <ToLink href={analysisHref}>Evidence › Analysis</ToLink>.
        </Notice>
      )}
    </>
  );
}

function SourceRow({ s }: { s: EvSource }) {
  const accepted = s.quality.accepted_count > 0;
  const what =
    s.slot === "BILLING"
      ? "No payment feed"
      : s.slot === "SITE_METER"
        ? accepted && s.roles.includes("site_import")
          ? "Import power"
          : "No accepted report for this role"
        : accepted
          ? "Sessions and status"
          : "No accepted report for this role";
  const label = SLOT_LABEL[s.slot] ?? s.display_name;
  return (
    <tr data-source-row={s.slot}>
      <th scope="row">
        {label}
        {s.display_name !== label ? <span className="ev-site-detail">{s.display_name}</span> : null}
      </th>
      <td>
        <Chip word={CONTACT[s.contact.state] ?? "Unknown"} />
      </td>
      <td>
        <Chip word={QUALITY[s.quality.state] ?? "No fact"} />
      </td>
      <td>{what}</td>
      <td>{SLOT_AFFECTS[s.slot] ?? "Claim effect not assessed"}</td>
    </tr>
  );
}

/* ---------- ev-evidence-analysis ---------- */

function valueText(i: EvAnalysisItem): string {
  if (i.value_display === null) return NOT_RECORDED;
  return i.unit === null ? i.value_display : `${i.value_display} ${i.unit}`;
}

function AnalysisScreen(p: EvSiteFrameProps) {
  const first = useEvRead(() => p.client.getAnalysis(p.siteId, p.window), keyOf(p, "a"));
  const [more, setMore] = useState<{ key: string; items: EvAnalysisItem[]; cursor: string | null } | null>(null);
  if (first === null) return <p>{EV_SITE_LOADING}</p>;
  const a = loaded(first);
  const refused = refusal(first);
  const key = keyOf(p, "a");
  const extra = more !== null && more.key === key ? more : null;
  const items = a === null ? [] : [...a.items, ...(extra?.items ?? [])];
  const cursor = extra !== null ? extra.cursor : (a?.next_cursor ?? null);
  const loadMore = () => {
    if (a === null || cursor === null) return;
    void p.client.getAnalysis(p.siteId, a.window, { cursor }).then((r) => {
      if (r.status === "loaded") setMore({ key, items: [...(extra?.items ?? []), ...r.value.items], cursor: r.value.next_cursor });
    });
  };
  const unverified = a?.excluded_records.filter((x) => x.reason === "SOURCE_UNVERIFIED") ?? [];
  return (
    <>
      <WindowBar env={a} />
      {a === null ? null : (
        <StatusBar label="Analysis state">
          <Badge tone="neutral" className="ev-site-chip">
            Evidence · Analysis
          </Badge>
          {` ${a.total_count} accepted records · timing and how each limit is set`}
          <Provenance env={a} />
          <StateNote env={a} />
        </StatusBar>
      )}
      <Panel heading="Accepted records behind the conclusions" headingId="ev-site-records-heading" description="Measured time is kept even when a report arrives late">
        {refused !== null ? (
          <Gap id="ev-site-records">{refused}</Gap>
        ) : items.length === 0 ? (
          <Gap id="ev-site-records">No accepted EV records in this window</Gap>
        ) : (
          <>
            <DataTable labelledBy="ev-site-records-heading">
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
                {items.slice(0, 3).map((i) => (
                  <tr key={i.evidence_id} data-record-row={i.evidence_id} data-record-use={i.use ?? ""} data-record-reason={i.reason ?? ""}>
                    <th scope="row">{i.source_label}</th>
                    <td>{valueText(i)}</td>
                    <td className="ev-site-nowrap">{eatTime(i.source_time) ?? NOT_RECORDED}</td>
                    <td className="ev-site-nowrap">{hms(i.sent_at)}</td>
                    <td className="ev-site-nowrap">{hms(i.received_at)}</td>
                    <td>
                      <span aria-label={`Record ${i.evidence_id}`}>{`Record ${short(i.evidence_id)}`}</span>
                      {i.record_target_state === "UNAVAILABLE" ? " · No analysis link" : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </DataTable>
            <Disclosure summary="Record details" name="ev-site-record-details" variant="tech">
              <p data-ev-record-selection>{`Site ${p.siteId} · ${a!.window.from ?? "No window"} to ${a!.window.to ?? "No window"} · known at ${a!.window.known_at ?? NOT_RECORDED}`}</p>
              <ul className="ev-site-list">
                {items.map((i) => (
                  <li key={i.evidence_id} data-record-detail={i.evidence_id}>
                    <code data-vocabulary-exempt="source-reference">{i.evidence_id}</code>
                    {i.note !== null && i.use === "EXCLUDED" && i.reason === "SOURCE_UNVERIFIED" ? <span data-ev-record-note> {i.note}</span> : null}
                    <span className="ev-site-line">{`${i.source_label} · ${valueText(i)} · measured ${instant(i.source_time)} · sent ${instant(i.sent_at)} · received ${instant(i.received_at)}`}</span>
                    <span className="ev-site-line">{`Quality ${i.quality ?? NOT_RECORDED} · use ${i.use ?? NOT_RECORDED}${i.reason ? ` · ${i.reason}` : ""} · source ${a!.source_provenance.classification ?? "Unknown"}`}</span>
                    {i.record_target_state === "UNAVAILABLE" ? <span className="ev-site-line">Analysis view not available for this EV record</span> : null}
                  </li>
                ))}
              </ul>
              {unverified.filter((x) => !items.some((i) => i.evidence_id === x.evidence_id)).length > 0 ? (
                <ul className="ev-site-list" data-ev-excluded-records>
                  {unverified
                    .filter((x) => !items.some((i) => i.evidence_id === x.evidence_id))
                    .map((x) => (
                      <li key={x.evidence_id}>
                        <code data-vocabulary-exempt="source-reference">{x.evidence_id}</code> Source or binding unverified for this record.
                        <span className="ev-site-line">Analysis view not available for this EV record</span>
                      </li>
                    ))}
                </ul>
              ) : null}
              {cursor === null ? null : (
                <p>
                  <button type="button" className="button" onClick={loadMore} data-ev-load-more>
                    {`Load more accepted records (${items.length} of ${a!.total_count})`}
                  </button>
                </p>
              )}
            </Disclosure>
          </>
        )}
      </Panel>
      <Panel heading="How a claim limit is set" headingId="ev-site-claim-heading">
        {refused !== null ? (
          <Gap id="ev-site-claim">{refused}</Gap>
        ) : a!.claim_rules.length === 0 ? (
          <Gap id="ev-site-claim">Claim limit not assessed</Gap>
        ) : (
          <>
            <div className="prose" data-claim-prose>
              <p>Each capability lists the readings it needs. Missing readings narrow the conclusion to covered periods; gaps are shown.</p>
              <p>Source reporting is not equipment condition.</p>
            </div>
            <Disclosure summary="Claim details" name="ev-site-claim-details" variant="tech">
              <ul className="ev-site-list">
                {a!.claim_rules.map((r) => (
                  <li key={r.claim} data-claim-rule={r.claim}>
                    {`${CLAIM_LABEL[r.claim] ?? "Claim"}: ${CHIP[r.result] ?? "None"} · ${coverageText(r.coverage, r.limitation)}`}
                    <span className="ev-site-line">{`Requires ${r.required_roles.map(roleLabel).join(", ")} · observed ${r.observed_roles.length === 0 ? "none" : r.observed_roles.map(roleLabel).join(", ")} · missing ${r.missing_roles.length === 0 ? "none" : r.missing_roles.map(roleLabel).join(", ")}`}</span>
                    <span className="ev-site-line">{`${r.accepted_evidence_ids.length} accepted records · source ${r.source_class ?? "Unknown"} · known at ${instant(r.known_at)}${r.limitation ? ` · ${r.limitation}` : ""}`}</span>
                  </li>
                ))}
              </ul>
            </Disclosure>
          </>
        )}
      </Panel>
    </>
  );
}

/* ---------- ev-financials ---------- */

/** Review r1 M1: the stored tariff basis in plain words; an unrecognised basis is not shown as a code. */
const BASIS_TEXT: Record<string, string> = { AUTHORED_ESTIMATE: "Authored estimate" };
const basisText = (basis: string) => BASIS_TEXT[basis] ?? "Basis not recognised";
const NO_SCENARIO = "No gross tariff scenario assessed";

function tariffText(t: EvAssumptionsRead["tariff"]): string {
  return t === null ? "Not declared" : `${t.value} ${t.currency}/kWh${t.basis ? ` · ${basisText(t.basis)}` : ""}`;
}
const billingText = (state: string | undefined) => (state === "NOT_CONNECTED" ? "Not connected" : "No record");

function consequenceWord(c: EvConsequence | null): string {
  if (c === null) return NO_SCENARIO;
  if (c.state === "ESTIMATED" && c.amount !== null && c.currency !== null) return `${c.currency} ${money2(c.amount)} gross estimate`;
  return c.state === "WITHHELD" ? "Withheld" : "Unpriced";
}

function FinancialsScreen(p: EvSiteFrameProps) {
  const financials = useEvRead(() => p.client.getFinancials(p.siteId, p.window), keyOf(p, "f"));
  const overview = useEvRead(() => p.client.getOverview(p.siteId, p.window), keyOf(p, "o"));
  const evidence = useEvRead(() => p.client.getEvidence(p.siteId, p.window), keyOf(p, "e"));
  const assumptions = useEvRead(() => p.client.getAssumptions(p.siteId, p.window), keyOf(p, "s"));
  if (financials === null || overview === null || evidence === null || assumptions === null) return <p>{EV_SITE_LOADING}</p>;
  const f = loaded(financials);
  const refused = refusal(financials);
  const o = loaded(overview);
  const s = loaded(assumptions);
  const gross = capOf(loaded(evidence)?.capabilities ?? [], "GROSS_TARIFF_SCENARIO");
  const c = f?.consequence ?? null;
  const routes = p.routes;
  const lines = c !== null && c.revision_id !== null ? 1 : 0;
  const currency = c?.currency ?? s?.tariff?.currency ?? null;
  const proved = gross !== null && gross.coverage.ratio === "1";
  const confidence = proved ? "Metered with complete coverage" : (gross?.limitation ?? "Coverage limited");
  const sessionsHref = f === null ? null : sel(routes.sessions, f.window);
  const finding = o?.findings.items[0] ?? null;
  const findingHref = finding === null ? null : evSiteUiHref(finding.links.self, routes);
  const interrupted = (o?.findings.count ?? 0) > 0;
  const estimated = c !== null && c.state === "ESTIMATED";
  const energyKwh = o?.energy.complete_kwh ?? null;
  return (
    <>
      <WindowBar env={f} />
      {f === null ? null : (
        <StatusBar label="Financials state" action={<UnavailableInline label="Portfolio roll-up" />}>
          <Badge tone="neutral" className="ev-site-chip">{`${lines} consequence ${lines === 1 ? "line" : "lines"}`}</Badge>
          {` ${currency ?? "Currency not declared"} · selected window · gross scenario only`}
          <Provenance env={f} />
          <StateNote env={f} />
        </StatusBar>
      )}
      {f === null ? null : (
        <MetricCards columns={4} label="EV money translation">
          <MetricCard label="Delivered energy" value={energyKwh === null ? "Unknown" : `${energyKwh} kWh`} note="Metered, complete sessions" data={{ "data-ev-fin-card": "energy" }} />
          <MetricCard label="Gross tariff estimate" value={estimated ? `${c!.currency} ${money2(c!.amount!)}` : c === null ? NO_SCENARIO : c.state === "WITHHELD" ? "Withheld" : "Unpriced"} note="Gross scenario · not cash collected" data={{ "data-ev-fin-card": "gross" }} />
          <MetricCard label="Lost revenue" value="Unknown" note="Unmet demand not established" data={{ "data-ev-fin-card": "lost" }} />
          <MetricCard label="Collections" value="Not recorded" note="No accepted payment record" data={{ "data-ev-fin-card": "collections" }} />
        </MetricCards>
      )}
      <Panel
        heading="What happened → what it means in money"
        headingId="ev-site-bridge-heading"
        description={(estimated && sessionsHref !== null) || findingHref !== null ? "Select a source to inspect its exact evidence" : undefined}
      >
        {refused !== null ? (
          <Gap id="ev-site-bridge">{refused}</Gap>
        ) : (
          <>
            <DataTable labelledBy="ev-site-bridge-heading">
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
                {c === null ? (
                  <tr data-bridge-row="none">
                    <th scope="row">No eligible delivered-energy consequence</th>
                    <td>Tariff not declared</td>
                    <td>
                      <Chip word={NO_SCENARIO} />
                    </td>
                    <td>Not assessed</td>
                    <td>Not assessed</td>
                    <td>
                      <span className="ev-site-noop">{NO_LINK}</span>
                    </td>
                  </tr>
                ) : (
                  <tr data-bridge-row="scenario">
                    <th scope="row">{c.quantity_kwh === null ? "Delivered energy not established" : `${c.quantity_kwh} kWh delivered with complete coverage`}</th>
                    <td>{c.quantity_kwh !== null && c.tariff_value !== null && c.currency !== null ? `${c.quantity_kwh} kWh × ${c.tariff_value} ${c.currency}/kWh` : "Tariff not declared"}</td>
                    <td className="ev-site-nowrap">{estimated ? consequenceWord(c) : <Chip word={consequenceWord(c)} />}</td>
                    <td>{estimated ? <Badge tone="neutral" className="ev-site-chip">Scenario</Badge> : <Chip word={c.state === "WITHHELD" ? "Withheld" : "Unpriced"} />}</td>
                    <td>{estimated ? confidence : (c.limitation ?? confidence)}</td>
                    <td>
                      <ToLink href={estimated ? sessionsHref : null}>Sessions ↗</ToLink>
                    </td>
                  </tr>
                )}
                {interrupted ? (
                  <tr data-bridge-row="interruption">
                    <th scope="row">Lost demand not established</th>
                    <td>Unmet demand × tariff</td>
                    <td>Not established</td>
                    <td>Not assessed</td>
                    <td>Not assessed</td>
                    <td>
                      <ToLink href={findingHref}>Finding ↗</ToLink>
                    </td>
                  </tr>
                ) : null}
                {interrupted ? (
                  <tr data-bridge-row="repair">
                    <th scope="row">No accepted repair or warranty cost record</th>
                    <td>Warranty claim or local repair</td>
                    <td>Not recorded</td>
                    <td>Not assessed</td>
                    <td>Not assessed</td>
                    <td>
                      <span className="ev-site-noop">{NO_LINK}</span>
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </DataTable>
            <Disclosure summary="Basis details" name="ev-site-basis-details" variant="tech">
              {c === null ? (
                <p>No gross tariff scenario assessed</p>
              ) : (
                <ul className="ev-site-list">
                  <li>{`Unrounded amount: ${c.amount === null ? "Not assessed" : `${c.currency ?? ""} ${c.amount}`.trim()} · state ${c.state}${c.reason ? ` · ${c.reason}` : ""}`}</li>
                  <li>{`Meter records: ${c.evidence_ids.length === 0 ? "none" : c.evidence_ids.join(", ")}`}</li>
                  <li>{`Session revisions: ${c.session_revision_ids.length === 0 ? "none" : c.session_revision_ids.join(", ")}`}</li>
                  <li>{`Tariff revision: ${c.tariff_revision_id ?? "Not declared"} · source gate ${c.source_gate ?? NOT_RECORDED} · source ${f!.source_provenance.classification ?? "Unknown"}`}</li>
                  {c.limitation ? <li>{c.limitation}</li> : null}
                  {f!.history.map((h) => (
                    <li key={h.revision_id ?? h.recorded_at ?? "history"} data-ev-history={h.revision_id ?? ""}>
                      {`Historical scenario · revision ${h.revision_no ?? NOT_RECORDED} · ${h.amount === null ? (h.state === "WITHHELD" ? "Withheld" : "Unpriced") : `${h.currency ?? ""} ${h.amount}`.trim()} · recorded ${instant(h.recorded_at)}`}
                    </li>
                  ))}
                </ul>
              )}
            </Disclosure>
          </>
        )}
      </Panel>
      <div className="panel-pair ev-site-pair">
        <Panel heading="Assumptions in use" headingId="ev-site-assumptions-heading">
          {refused !== null ? (
            <Gap id="ev-site-assumptions">{refused}</Gap>
          ) : (
            <>
              <KeyValues
                label="Assumptions in use"
                rows={[
                  ["Tariff", s === null ? (refusal(assumptions) ?? "Not declared") : s.tariff === null ? <Chip word="Not declared" /> : tariffText(s.tariff)],
                  ["Billing / collections", billingText(s?.billing_state)],
                  ["Currency", s?.tariff?.currency ?? (s === null ? "Not declared" : <Chip word="Not declared" />)],
                ]}
              />
              <p className="ev-site-link">
                <Link className="button" to={sel(routes.assumptions, f!.window)}>
                  Review assumptions
                </Link>
              </p>
              <Disclosure summary="Assumption details" name="ev-site-assumption-details" variant="tech">
                <AssumptionDetails s={s} />
              </Disclosure>
            </>
          )}
        </Panel>
        <Panel heading="Not included" headingId="ev-site-excluded-heading">
          {refused !== null ? (
            <Gap id="ev-site-excluded">{refused}</Gap>
          ) : ["lost_sales", "collections", "margin", "repair", "warranty"].every((k) => f!.not_included.includes(k)) ? (
            <p className="prose">Lost sales, collections, margin, repair and warranty are not included in this gross tariff scenario.</p>
          ) : (
            <Gap id="ev-site-excluded">Exclusions not recorded</Gap>
          )}
        </Panel>
      </div>
    </>
  );
}

function AssumptionDetails({ s }: { s: EvAssumptionsRead | null }) {
  if (s === null || s.tariff === null) return <p>Tariff not declared · no published EV tariff revision</p>;
  const t = s.tariff;
  return (
    <ul className="ev-site-list">
      <li>
        Tariff revision <code data-vocabulary-exempt="source-reference">{t.revision_id}</code>
        {` · ${t.unit} · ${t.basis ? basisText(t.basis) : "Basis not recorded"}`}
      </li>
      <li>{`Valid ${instant(t.valid_from)} to ${t.valid_to ?? "open"} · recorded ${instant(t.recorded_at)} · ${s.tariff_revision_count} published revisions`}</li>
      {s.publication_note === null ? null : <li data-ev-assumption-publication-note>{s.publication_note}</li>}
      <li>{`Billing / collections: ${billingText(s.billing_state)} · source: published Site financial assumption`}</li>
    </ul>
  );
}

/* ---------- ev-assumptions ---------- */

function AssumptionsScreen(p: EvSiteFrameProps) {
  const assumptions = useEvRead(() => p.client.getAssumptions(p.siteId, p.window), keyOf(p, "s"));
  if (assumptions === null) return <p>{EV_SITE_LOADING}</p>;
  const s = loaded(assumptions);
  const refused = refusal(assumptions);
  const extra = s === null ? null : [s.source_provenance.classification === "REGISTERED_SIMULATION" ? "Generated test data" : null, stateLine(s)].filter(Boolean).join(" · ");
  return (
    <>
      <WindowBar env={s} extra={extra} />
      <Panel heading="Financial assumptions" headingId="ev-site-fin-assumptions-heading" description="Site-scoped business context · changes keep the earlier version">
        {refused !== null ? (
          <Gap id="ev-site-fin-assumptions">{refused}</Gap>
        ) : (
          <>
            <DataTable labelledBy="ev-site-fin-assumptions-heading">
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
                <tr data-assumption-row="tariff">
                  <th scope="row">Tariff</th>
                  <td>{s!.tariff === null ? <Chip word="Not declared" /> : tariffText(s!.tariff)}</td>
                  <td>Translating metered energy</td>
                </tr>
                <tr data-assumption-row="billing">
                  <th scope="row">Billing / collections</th>
                  <td>{billingText(s!.billing_state)}</td>
                  <td>Cash collection not assessed</td>
                </tr>
                <tr data-assumption-row="currency">
                  <th scope="row">Currency</th>
                  <td className="ev-site-nowrap">{s!.tariff === null ? <Chip word="Not declared" /> : s!.tariff.currency}</td>
                  <td>Scenario display currency</td>
                </tr>
              </tbody>
            </DataTable>
            {s!.publication_note === null ? null : (
              <p className="v69-chart-note" data-ev-publication-note>
                {s!.publication_note}
              </p>
            )}
            <Disclosure summary="Assumption details" name="ev-site-assumption-details" variant="tech">
              <AssumptionDetails s={s} />
            </Disclosure>
          </>
        )}
      </Panel>
      <Notice tone="blue" data={{ "data-ev-notice": "assumptions" }}>
        Changing the tariff re-translates the same metered energy. It does not change what was measured.
      </Notice>
    </>
  );
}
