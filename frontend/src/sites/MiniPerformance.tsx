/**
 * W4-02 unit 6: the MINIGRID mini-depth Performance pages. This file holds the shared sibling-tab row
 * (`service, dispatch, fuel, renewable, backup`, S6), the Renewable page (v69 `renewable`), the Service page (v69 `service`)
 * the Fuel page (v69 `fuel`) and the Backup page (v69 `backup`), all from the q9 page dry-read.
 * Every number is the selected read's; a missing value reads `Unknown`, never a mock literal.
 */
import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  Badge,
  ChartNote,
  DataTable,
  MetricCard,
  MetricCards,
  Notice,
  Panel,
  StatusBar,
  ValueBars,
} from "../ui";
import type { PanelProps } from "../ui/Panel";
import { UnavailableInline, UnavailableLinkEntry } from "../ui/UnavailableEntry";
import { sourceQualification } from "../ui/productWords";
import {
  localDateOf,
  localDaysWindow,
  localHourWindow,
  localTimeOf,
  miniWindowSearch,
  type MiniBound,
  type MiniCapability,
  type MiniCoverage,
  type BackupRead,
  type BackupRow,
  type BackupStep,
  type FuelRead,
  type FuelRow,
  renewableDowngraded,
  type MiniDepthClient,
  type MiniRead,
  type MiniWindowQuery,
  type RenewableRead,
  type RenewableRow,
  type ServiceRead,
  type ServiceRow,
} from "./miniDepthClient";
import { performanceSubtabs, type DomainPresentationProfile } from "./presentationProfile";
import { PERFORMANCE_SUBTABS_LABEL } from "./performanceSubtabsLabel";
import "./w4-mini-performance.css";

/* ---------- sibling tabs ---------- */

/**
 * The mini pages this build renders. A served mini tab without its page yet is left out of the row (a new unbuilt
 * in-page entry needs a ruling, navigation-truthfulness guard); pending ruling q10-3.
 */
export const BUILT_MINI_PAGES: ReadonlySet<string> = new Set(["service", "fuel", "renewable", "backup"]);

/** S6: the mini capabilities merged with the served Dispatch, ordered by the presentation profile. */
export function useMiniCapabilities(client: MiniDepthClient | undefined, siteCode: string): MiniCapability[] {
  const [caps, setCaps] = useState<{ code: string; items: MiniCapability[] } | null>(null);
  useEffect(() => {
    if (client === undefined) return undefined;
    let active = true;
    void client.getCapabilities(siteCode).then((read) => {
      if (active) setCaps({ code: siteCode, items: read.status === "loaded" ? read.value : [] });
    });
    return () => {
      active = false;
    };
  }, [client, siteCode]);
  return caps !== null && caps.code === siteCode ? caps.items : [];
}

export function MiniPerformanceSubtabs({
  client,
  siteCode,
  profile,
  current,
  subtabHref,
}: {
  client: MiniDepthClient | undefined;
  siteCode: string;
  profile: DomainPresentationProfile | null;
  current: string;
  subtabHref: (id: string) => string;
}) {
  const mini = useMiniCapabilities(client, siteCode);
  const served = [{ id: "dispatch", display_name: "Dispatch" }, ...mini];
  const subtabs = performanceSubtabs(profile, served);
  return (
    <nav className="site-tabs site-subtabs" aria-label={PERFORMANCE_SUBTABS_LABEL}>
      <ol className="site-tabs__list">
        {subtabs.map((item) =>
          item.id !== "dispatch" && item.known && !BUILT_MINI_PAGES.has(item.id) ? null : (
          <li className="site-tabs__item" key={item.id}>
            <Link
              className="site-tabs__link"
              to={subtabHref(item.id)}
              data-performance-subtab={item.id}
              data-profile-known={item.known}
              aria-current={item.id === current ? "page" : undefined}
            >
              {/* The Dispatch label on this imported-Site row stays as before (handoff Run 15). */}
              {item.id === "dispatch" ? "Dispatch" : item.label}
            </Link>
          </li>
          ),
        )}
      </ol>
    </nav>
  );
}

/* ---------- shared formatting ---------- */

export const UNKNOWN = "Unknown";
export const MINI_UNAVAILABLE = "Mini-grid evidence is unavailable right now. Try again.";

const NUMBER = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });

export function boundText(bound: MiniBound | null, unit: string): string {
  if (bound === null || bound.low === null || bound.high === null) return UNKNOWN;
  return bound.low === bound.high
    ? `${NUMBER.format(bound.low)} ${unit}`
    : `${NUMBER.format(bound.low)}–${NUMBER.format(bound.high)} ${unit}`;
}

/** Renewable constraint copy in its stable order (`mini_depth/rules.py:RENEWABLE_CONSTRAINTS`). */
const CONSTRAINT_COPY: Record<string, string> = {
  CAPABILITY_MISSING: "Available solar power unknown",
  PV_USE_MISSING: "Observed use unknown",
  MARGIN_MISSING: "Retained margin unknown",
  CHARGE_OBLIGATION_MISSING: "Storage obligation unknown",
  CRITICAL_SERVICE_MISSING: "Critical service not established",
  COVERAGE_GAP: "Incomplete hour",
  REQUIRED_INPUT_UNUSABLE: "Required reading could not be used",
  CONFLICT: "Conflicting evidence",
  HEADROOM_NON_POSITIVE: "No positive headroom after retained margin",
  CHARGE_OBLIGATION_ACTIVE: "Storage charging uses the available headroom",
  CRITICAL_SERVICE_DEFICIT: "Critical service has an unresolved deficit",
};

const LIMITATION_COPY: Record<string, string> = {
  SOURCE_CLASS_UNKNOWN: "Source class unknown",
  SOURCE_CLASS_MIXED: "Mixed source classes",
  RECOMPUTE_PENDING: "Recompute pending",
  SOURCE_STALE: "Sources changed since the assessment",
  SITE_ROLE_UNSUPPORTED: "This site type has no mini-grid assessment",
  REQUEST_BASELINE_MISSING: "Requested-service baseline missing",
  DELIVERY_COMPLETENESS_MISSING: "Delivery completeness unconfirmed",
  CLOSING_READING_MISSING: "Closing tank reading missing",
  RECOVERY_TARGET_MISSING: "No pinned critical-service recovery target",
  BACKUP_CHAIN_INCOMPLETE: "No complete outage chain",
};

const plainCode = (code: string): string => CONSTRAINT_COPY[code] ?? LIMITATION_COPY[code] ?? code;

/* ---------- q12-7: bounded regions ---------- */

/**
 * q12-7: a closed disclosure showing an exact count or short conclusion; the full ordered list opens in a
 * keyboard-focusable bounded scroll. `strip` marks it as a status-strip part (the open list overlays the strip).
 */
function MoreList({
  summary,
  label,
  items,
  ids = false,
  strip = false,
  data,
}: {
  summary: ReactNode;
  /** The list's accessible name; defaults to the summary when that is plain text. */
  label?: string;
  items: string[];
  ids?: boolean;
  strip?: boolean;
  data?: Record<string, string>;
}) {
  const list = ["mini-more__list", ids ? "mini-ids" : "", strip ? "status-strip__more" : ""].filter(Boolean).join(" ");
  return (
    <details className={strip ? "mini-more status-strip__item" : "mini-more"} {...data}>
      <summary>{summary}</summary>
      <ul className={list} tabIndex={0} aria-label={label ?? (typeof summary === "string" ? summary : undefined)}>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </details>
  );
}

/**
 * q12-7: the strip's ordered limitations (any claim-limit sentence first) as one short line; the full ordered list
 * sits behind the disclosure. `summary` replaces the count line when the page has its own limitation word.
 */
function StripLimitations({ limits, lead = [], summary }: { limits: string[]; lead?: string[]; summary?: ReactNode }) {
  const items = [...lead, ...limits];
  if (items.length === 0) return null;
  const count = `Limited by ${items.length} condition${items.length === 1 ? "" : "s"}`;
  return <MoreList strip summary={summary ?? count} label={count} items={items} data={{ "data-mini-limitations": "" }} />;
}

/**
 * q12-7: a panel bounded to its mock-derived maximum (the whole panel, heading included). A plain panel's body
 * scrolls inside the budget; a `table` panel scrolls inside its table region under a sticky header.
 */
function BoundedPanel({ bound, table = false, children, ...props }: Omit<PanelProps, "className"> & { bound: string; table?: boolean }) {
  return (
    <Panel {...props} className={`mini-bound mini-max--${bound}${table ? " mini-bound--table" : ""}`}>
      {table ? (
        children
      ) : (
        <div className="mini-scroll" tabIndex={0} role="group" aria-label="Panel content (scrolls)">
          {children}
        </div>
      )}
    </Panel>
  );
}

const DECISION_WORD: Record<string, string> = {
  ELIGIBLE: "Eligible",
  EXCLUDED: "Excluded",
  LIMITED: "Limited",
  CONFLICT: "Conflict",
};

const CURRENTNESS_WORD: Record<string, string> = {
  CURRENT: "Current selection",
  HISTORICAL: "Historical selection",
  PENDING_RECOMPUTE: "Recompute pending",
  STALE_SOURCE: "Sources changed since the assessment",
  UNKNOWN: "No selected assessment",
};

/* ---------- reads ---------- */

function useMiniRead<T>(load: () => Promise<MiniRead<T>>, key: string, attempt: number): MiniRead<T> | null {
  const [state, setState] = useState<{ key: string; value: MiniRead<T> } | null>(null);
  const fullKey = `${key}#${attempt}`;
  useEffect(() => {
    let active = true;
    void load().then((value) => {
      if (active) setState({ key: fullKey, value });
    });
    return () => {
      active = false;
    };
    // `load` is rebuilt every render; the key names what it reads.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fullKey]);
  return state !== null && state.key === fullKey ? state.value : null;
}

function refusalCopy(read: Exclude<MiniRead<unknown>, { status: "loaded" }>): { key: string; title: string; body: string } {
  const http = read.status === "refused" ? read.httpStatus : null;
  if (http === 401) return { key: "unauthenticated", title: "Sign in required", body: "Sign in to read this site's mini-grid assessment." };
  if (http === 403) return { key: "forbidden", title: "Access refused", body: "You do not have access to this site." };
  if (http === 404) return { key: "not-found", title: "Not found", body: "This page was not found." };
  if (http === 422) {
    return {
      key: "invalid-window",
      title: "Period cannot be read",
      body: read.message ?? "Select a valid complete site-local hour or one to five site-local days.",
    };
  }
  return { key: "unavailable", title: "Assessment unavailable", body: MINI_UNAVAILABLE };
}

function MiniRefusal({ read, onRetry }: { read: Exclude<MiniRead<unknown>, { status: "loaded" }>; onRetry: () => void }) {
  const copy = refusalCopy(read);
  return (
    <div className="page-refusal" role="status" data-page-refusal={copy.key}>
      <p className="page-refusal__title">
        <strong>{copy.title}</strong>
      </p>
      <p>{copy.body}</p>
      {copy.key === "unavailable" ? (
        <button type="button" className="v69-claim-button" onClick={onRetry} data-mini-retry>
          Try again
        </button>
      ) : null}
    </div>
  );
}

/* ---------- period selector (Q5, q9-1: site-local days, sent as UTC bounds) ---------- */

function MiniPeriodBar({
  timeZone,
  window,
  maxDays,
  onApply,
}: {
  timeZone: string;
  window: MiniWindowQuery;
  maxDays: number;
  onApply: (next: MiniWindowQuery) => void;
}) {
  const fromMs = window.from === null ? Number.NaN : Date.parse(window.from);
  const toMs = window.to === null ? Number.NaN : Date.parse(window.to);
  const firstDay = Number.isNaN(fromMs) ? "" : localDateOf(timeZone, fromMs);
  const lastDay = Number.isNaN(toMs) ? "" : localDateOf(timeZone, toMs - 1);
  const span = firstDay && lastDay ? Math.round((Date.parse(lastDay) - Date.parse(firstDay)) / 86_400_000) + 1 : 1;
  const [first, setFirst] = useState(firstDay);
  const [days, setDays] = useState(String(Math.min(Math.max(span, 1), maxDays)));
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!first) return;
    onApply({ ...localDaysWindow(timeZone, first, Number(days)), known_at: window.known_at });
  };
  return (
    <form className="site-date-bar mini-period-bar" onSubmit={submit} data-mini-period>
      <span className="site-date-bar__window" data-mini-local-period>
        {firstDay && lastDay
          ? `Site-local ${firstDay === lastDay ? `day ${firstDay}` : `days ${firstDay} to ${lastDay}`} (${timeZone})`
          : "No period selected"}
      </span>
      <span className="site-date-bar__cutoff" data-mini-utc-bounds>
        {`UTC ${window.from ?? UNKNOWN} to ${window.to ?? UNKNOWN}`}
        {window.known_at === null ? "" : ` · evidence cutoff ${window.known_at}`}
      </span>
      <label className="v69-chip-field">
        First day{" "}
        <input className="v69-chip-control" type="date" value={first} onChange={(e) => setFirst(e.target.value)} />
      </label>
      <label className="v69-chip-field">
        Days{" "}
        <select className="v69-chip-control" value={days} onChange={(e) => setDays(e.target.value)}>
          {Array.from({ length: maxDays }, (_, i) => String(i + 1)).map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </select>
      </label>
      <button type="submit" className="v69-chip-control">
        Apply
      </button>
    </form>
  );
}

/* ---------- Renewable page ---------- */

export const RENEWABLE_MARGIN_GAP =
  "The retained-margin value is not available in this read; inspect the pinned Foundation basis before using this breakdown.";
export const RENEWABLE_NOTICE =
  "Opportunity is an evidence-backed capacity estimate. A paired load-addition comparison and local demand validation are required before an investment or revenue claim.";


/** q10-3: the currentness/provenance downgrade runs before the label mapping, so a downgraded read never gets `Watch`. */
function statusWord(read: RenewableRead): { word: string; tone: string } {
  const headroom = read.cards?.headroom_kw ?? null;
  if (read.status === "LIMITED") return { word: "Evidence limited", tone: "amber" };
  if (read.status !== "SUPPORTED" || headroom === null || headroom.low === null) {
    return { word: "Not assessed", tone: "muted" };
  }
  if (headroom.low <= 0) return { word: "No usable headroom", tone: "muted" };
  if (renewableDowngraded(read)) return { word: "Evidence limited", tone: "amber" };
  return { word: "Watch", tone: "amber" };
}

function provenanceChips(read: Pick<RenewableRead, "selected_source_provenance" | "pending_source_provenance">): string[] {
  const selected = read.selected_source_provenance?.classification ?? null;
  const pending = read.pending_source_provenance?.classification ?? null;
  const chips: string[] = [];
  if (selected !== null) chips.push(`Selected sources: ${sourceQualification(selected).label}`);
  if (pending !== null) chips.push(`Pending sources: ${sourceQualification(pending).label}`);
  return chips;
}

function RenewableStatus({ read }: { read: RenewableRead }) {
  const { word, tone } = statusWord(read);
  const cards = read.cards;
  const fact =
    cards !== null && cards.eligible_days !== null && cards.assessed_days !== null
      ? `Solar headroom on ${cards.eligible_days} of ${cards.assessed_days} assessed days`
      : "Days with usable solar headroom: Unknown";
  const limits = Array.from(new Set(read.limitations.map((l) => plainCode(l.code))));
  return (
    <StatusBar
      label="Renewable assessment"
      items
      data={{ "data-mini-status": read.status }}
    >
      <span className="status-strip__item">
        <Badge tone="neutral" className={`mini-tone--${tone}`}>
          {word}
        </Badge>
      </span>
      <span className="status-strip__item">
        <Badge tone="neutral">Lens: Opportunity</Badge>
      </span>
      {provenanceChips(read).map((chip) => (
        <span className="status-strip__item" key={chip} data-mini-provenance>
          <Badge tone="neutral">{chip}</Badge>
        </span>
      ))}
      <span className="status-strip__item" data-mini-currentness={read.currentness.state}>
        <Badge tone="neutral">{CURRENTNESS_WORD[read.currentness.state] ?? read.currentness.state}</Badge>
      </span>
      <StripLimitations limits={limits} />
      <span className="status-strip__item">{fact}</span>
      {read.currentness.state === "HISTORICAL" ? (
        <span className="status-strip__item" data-mini-historical>
          Historical selection; job state reflects the retained job record
        </span>
      ) : null}
      <span className="status-strip__spacer" aria-hidden="true" />
      <span className="status-strip__action" data-mini-dispatch-link>
        {read.links.dispatch === null ? (
          <UnavailableInline label="Compare with Dispatch evidence" />
        ) : (
          <Link to={read.links.dispatch}>Compare with Dispatch evidence →</Link>
        )}
      </span>
    </StatusBar>
  );
}

function RenewableCardsRow({ read }: { read: RenewableRead }) {
  const cards = read.cards;
  const coverage = read.coverage;
  const days =
    cards !== null && cards.eligible_days !== null && cards.assessed_days !== null
      ? `${cards.eligible_days} / ${cards.assessed_days} days`
      : UNKNOWN;
  const usedNote =
    coverage === null || coverage.required_seconds === 0
      ? "Accepted power"
      : `Accepted power over ${Math.floor(coverage.observed_seconds / 60)}/${Math.floor(coverage.required_seconds / 60)} min`;
  return (
    <MetricCards label="Renewable summary" data={{ "data-mini-cards": "renewable" }}>
      <MetricCard label="PV capability" value={boundText(cards?.capability_kw ?? null, "kW")} note="Reported PV capability and selected uncertainty" />
      <MetricCard label="PV used" value={boundText(cards?.used_kw ?? null, "kW")} note={usedNote} />
      <MetricCard label="Usable headroom" value={boundText(cards?.headroom_kw ?? null, "kW")} note="After retained margin and service checks" />
      <MetricCard label="Recurring opportunity" value={days} note="Eligible complete days / assessed complete days" />
    </MetricCards>
  );
}

const high = (bound: MiniBound | null | undefined): number | null => (bound === null || bound === undefined ? null : bound.high);

function coverageComplete(read: RenewableRead): boolean {
  const c = read.coverage;
  return c !== null && c.required_seconds > 0 && c.observed_seconds >= c.required_seconds && c.gaps.length === 0;
}

function HeadroomPanel({ read }: { read: RenewableRead }) {
  const cards = read.cards;
  const coverage = read.coverage;
  return (
    <BoundedPanel
      bound="renewable-headroom"
      heading="From physical headroom to an opportunity"
      headingId="mini-renewable-headroom-heading"
      description={coverageComplete(read) ? "Actual accepted interval means cover each eligible one-hour window" : "Accepted coverage is incomplete"}
    >
      <ValueBars
        title="Solar power in the assessed hours"
        items={[
          { key: "capability", label: "Available PV", value: high(cards?.capability_kw), valueText: boundText(cards?.capability_kw ?? null, "kW") },
          { key: "used", label: "Observed use", value: high(cards?.used_kw), valueText: boundText(cards?.used_kw ?? null, "kW") },
          { key: "margin", label: "Retained margin", value: null, valueText: UNKNOWN },
          { key: "headroom", label: "After retained margin", value: high(cards?.headroom_kw), valueText: boundText(cards?.headroom_kw ?? null, "kW") },
        ]}
      />
      {/* q12-7: the retained-margin and coverage explanation sit behind one disclosure; its open body scrolls in the panel. */}
      <details className="mini-more" data-mini-basis>
        <summary>Basis and coverage</summary>
        <div className="mini-more__list" tabIndex={0} role="group" aria-label="Basis and coverage">
          <ChartNote data={{ "data-mini-margin-gap": "" }}>
            {`Retained margin: ${UNKNOWN}. ${RENEWABLE_MARGIN_GAP}`}
          </ChartNote>
          <ChartNote data={{ "data-mini-coverage": "" }}>
            {coverage === null
              ? "Accepted coverage: Unknown."
              : `Accepted coverage: ${Math.floor(coverage.observed_seconds / 60)} of ${Math.floor(coverage.required_seconds / 60)} minutes in the assessed hours. Maximum sources in one assessed hour: ${coverage.source_count}.`}
          </ChartNote>
        </div>
      </details>
    </BoundedPanel>
  );
}

function OpportunityDrawer({ read, timeZone, onClose }: { read: RenewableRead; timeZone: string; onClose: () => void }) {
  return (
    <div className="mini-drawer mini-shrink" role="region" tabIndex={0} aria-labelledby="mini-opportunity-drawer-heading" data-mini-drawer="opportunity">
      <h3 id="mini-opportunity-drawer-heading">Productive-use opportunity evidence</h3>
      <h4>Eligible-window basis</h4>
      {read.rows.length === 0 ? (
        <p>No selected renewable hour is cited for this period.</p>
      ) : (
        <DataTable>
          <thead>
            <tr>
              <th scope="col">Hour</th>
              <th scope="col">Decision</th>
              <th scope="col">Cited accepted records</th>
            </tr>
          </thead>
          <tbody>
            {read.rows.map((row) => (
              <tr key={`${row.day}-${row.from}`}>
                <td>{hourLabel(row.day, row.from, row.to, timeZone)}</td>
                <td>{DECISION_WORD[row.decision] ?? row.decision}</td>
                <td className="mini-ids">{row.evidence_ids.length === 0 ? "None" : row.evidence_ids.join(", ")}</td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      )}
      <h4>Bounded translation</h4>
      <ul className="mini-drawer__list">
        {read.rows
          .filter((row) => row.decision === "ELIGIBLE")
          .map((row) => (
            <li key={`t-${row.day}-${row.from}`}>{`${hourLabel(row.day, row.from, row.to, timeZone)}: ${boundText(row.opportunity_kwh, "kWh")} for one hour of usable headroom`}</li>
          ))}
        <li>Customer demand: Not assessed</li>
        <li>Energy sale: Not assessed</li>
        <li>Tariff: Not assessed</li>
      </ul>
      <button type="button" className="v69-claim-button" onClick={onClose}>
        Close
      </button>
    </div>
  );
}

function ProductiveUsePanel({ read, timeZone }: { read: RenewableRead; timeZone: string }) {
  const [open, setOpen] = useState(false);
  return (
    <BoundedPanel
      bound="renewable-productive"
      table
      heading="Productive-use evaluation"
      headingId="mini-renewable-productive-heading"
      description="Electrical feasibility does not establish customer demand"
    >
      <p className="prose" data-mini-productive-gap>
        No productive-use scenario has been assessed.
      </p>
      <p className="prose">Electrical capacity does not establish customer demand.</p>
      <UnavailableLinkEntry label="Opportunity decision" />
      <p>
        <button
          type="button"
          className="v69-claim-button"
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
          data-mini-drawer-open="opportunity"
        >
          Inspect opportunity constraints
        </button>
      </p>
      {open ? <OpportunityDrawer read={read} timeZone={timeZone} onClose={() => setOpen(false)} /> : null}
    </BoundedPanel>
  );
}

function hourLabel(day: string, from: string, to: string, timeZone: string): string {
  return `${day} · ${localTimeOf(timeZone, Date.parse(from))}–${localTimeOf(timeZone, Date.parse(to))}`;
}

type WindowRow = { kind: "assessed"; row: RenewableRow } | { kind: "not-assessed"; day: string; from: string; to: string };

/** Stored rows plus an honest `Not assessed` row for each requested hour without a selection (q9-6). */
function windowRows(read: RenewableRead): WindowRow[] {
  const out: WindowRow[] = [];
  for (const hour of read.currentness.windows) {
    const stored = read.rows.filter((row) => row.day === hour.local_day);
    if (stored.length > 0) stored.forEach((row) => out.push({ kind: "assessed", row }));
    else out.push({ kind: "not-assessed", day: hour.local_day, from: hour.window_start, to: hour.window_end });
  }
  for (const row of read.rows) {
    if (!read.currentness.windows.some((hour) => hour.local_day === row.day)) out.push({ kind: "assessed", row });
  }
  return out;
}

function recurrenceText(read: RenewableRead): string {
  const hours = read.currentness.windows;
  const complete = hours.length === 5 && hours.every((h) => h.selection_id !== null) && read.cards?.assessed_days === 5;
  return complete && read.cards?.eligible_days !== null && read.cards?.eligible_days !== undefined
    ? `Usable headroom recurred on ${read.cards.eligible_days} of 5 completely assessed days.`
    : "Recurrence is not established for this selection.";
}

function WindowsPanel({ read, timeZone, evidenceHref }: { read: RenewableRead; timeZone: string; evidenceHref: string | null }) {
  const rows = windowRows(read);
  return (
    <BoundedPanel bound="renewable-windows" table heading="Eligible and excluded windows" headingId="mini-renewable-windows-heading" flush>
      {rows.length === 0 ? (
        <p className="not-available-yet v69-chart-note" data-panel-gap="renewable-windows">
          No renewable window has been assessed for this period.
        </p>
      ) : (
        <DataTable labelledBy="mini-renewable-windows-heading">
          <thead>
            <tr>
              <th scope="col">Day / period</th>
              <th scope="col">Opportunity</th>
              <th scope="col">Constraint check</th>
              <th scope="col">Decision</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((item) =>
              item.kind === "assessed" ? (
                <tr key={`a-${item.row.day}-${item.row.from}`} data-mini-row="assessed">
                  <td>{hourLabel(item.row.day, item.row.from, item.row.to, timeZone)}</td>
                  <td>{item.row.opportunity_kwh === null ? "—" : boundText(item.row.opportunity_kwh, "kWh")}</td>
                  <td>
                    {item.row.constraints.length === 0
                      ? "All required evidence present"
                      : item.row.constraints.map((code) => CONSTRAINT_COPY[code] ?? code).join("; ")}
                    <span className="mini-cited">
                      {` · ${item.row.evidence_ids.length} cited record${item.row.evidence_ids.length === 1 ? "" : "s"}`}
                      {evidenceHref === null ? null : (
                        <>
                          {" · "}
                          <Link to={evidenceHref}>Evidence</Link>
                        </>
                      )}
                    </span>
                  </td>
                  <td>
                    <Badge tone="neutral" className={`mini-decision--${item.row.decision.toLowerCase()}`}>
                      {DECISION_WORD[item.row.decision] ?? item.row.decision}
                    </Badge>
                  </td>
                </tr>
              ) : (
                <tr key={`n-${item.day}`} data-mini-row="not-assessed">
                  <td>{hourLabel(item.day, item.from, item.to, timeZone)}</td>
                  <td>—</td>
                  <td>No selected assessment for this hour</td>
                  <td>
                    <Badge tone="neutral">Not assessed</Badge>
                  </td>
                </tr>
              ),
            )}
          </tbody>
        </DataTable>
      )}
      <ChartNote data={{ "data-mini-recurrence": "" }}>{recurrenceText(read)}</ChartNote>
    </BoundedPanel>
  );
}

export function MiniRenewablePage({
  read,
  timeZone,
}: {
  read: RenewableRead;
  timeZone: string;
}) {
  return (
    <>
      <RenewableStatus read={read} />
      <RenewableCardsRow read={read} />
      <div className="panel-pair">
        <HeadroomPanel read={read} />
        <ProductiveUsePanel read={read} timeZone={timeZone} />
      </div>
      <WindowsPanel read={read} timeZone={timeZone} evidenceHref={read.links.evidence} />
      <Notice tone="blue" data={{ "data-mini-notice": "renewable" }}>
        {RENEWABLE_NOTICE}
      </Notice>
    </>
  );
}

export const MINI_LOADING = "Loading the site's mini-grid assessment.";

/** The Renewable page body: the period bar, then the selected read or its refusal. */
export function MiniRenewable({
  client,
  siteCode,
  timeZone,
  window,
  pageHref,
}: {
  client: MiniDepthClient;
  siteCode: string;
  timeZone: string | null;
  window: MiniWindowQuery | null;
  /** The page address for a new window (search included). */
  pageHref: (search: string) => string;
}): ReactNode {
  const navigate = useNavigate();
  const [attempt, setAttempt] = useState(0);
  const key = `${siteCode}|${window?.from ?? ""}|${window?.to ?? ""}|${window?.known_at ?? ""}`;
  const read = useMiniRead<RenewableRead>(
    () => (window === null ? Promise.resolve({ status: "unavailable", message: null }) : client.getRenewable(siteCode, window)),
    key,
    attempt,
  );
  if (timeZone === null || window === null) return <NoTimeZone />;
  return (
    <>
      <MiniPeriodBar
        key={key}
        timeZone={timeZone}
        window={window}
        maxDays={5}
        onApply={(next) => navigate(pageHref(miniWindowSearch(next)))}
      />
      {read === null ? (
        <p role="status">{MINI_LOADING}</p>
      ) : read.status !== "loaded" ? (
        <MiniRefusal read={read} onRetry={() => setAttempt((n) => n + 1)} />
      ) : (
        <MiniRenewablePage read={read.value} timeZone={read.value.site.timezone ?? timeZone} />
      )}
    </>
  );
}


function NoTimeZone() {
  return (
    <div className="page-refusal" role="status" data-page-refusal="no-timezone">
      <p>The site time zone is not recorded, so no site-local day can be selected.</p>
    </div>
  );
}

/* ---------- Service page (v69 `service`, q9 page dry-read, copy ledger, Q20) ---------- */

export const SERVICE_SUPPORTED_COPY =
  "These readings show delivered power where measured. They do not establish what customers required.";
export const SERVICE_EMPTY = "No addressed-load readings were accepted for this period.";
export const SERVICE_REQUEST_MISSING = "Delivered power is observed; requested-service baseline is incomplete";

const SERVICE_STATUS_WORD: Record<string, string> = { SUPPORTED: "Supported", LIMITED: "Limited" };
const ROLE_WORD: Record<string, string> = { CRITICAL: "Critical service", UNCLASSIFIED: "Unclassified load" };
const REQUEST_WORD: Record<string, string> = {
  ACCEPTED: "Accepted requested-power record",
  MISSING: "No accepted requested-power record",
  CONFLICT: "Conflicting requested-power records",
};

const minutes = (coverage: MiniCoverage | null): string =>
  coverage === null || coverage.required_seconds === 0
    ? "Measured minutes: Unknown"
    : `Measured ${Math.floor(coverage.observed_seconds / 60)} of ${Math.floor(coverage.required_seconds / 60)} minutes`;

const kw = (value: number | null, unit = "kW"): string => (value === null ? UNKNOWN : `${NUMBER.format(value)} ${unit}`);

const requestMissing = (read: ServiceRead): boolean =>
  read.limitations.some((l) => l.code === "REQUEST_BASELINE_MISSING") ||
  read.rows.some((row) => row.requested_evidence_state !== "ACCEPTED");

const loadName = (row: ServiceRow): string => (row.role === "CRITICAL" ? `${row.load_label} (critical)` : row.load_label);

/** Final review ruling 2 (M2): the clinic bar and row name the feeder series, never the critical-service record. */
export const CLINIC_FEEDER_LABEL = "Clinic feeder delivered power";
const feederName = (row: ServiceRow): string => (row.role === "CRITICAL" ? CLINIC_FEEDER_LABEL : row.load_label);

/** Ruling 2: the critical card's note names its own record and its own coverage; never the feeder's. */
const CRITICAL_RECORD = "Critical-service delivered power record";
function criticalNote(coverage: MiniCoverage | null | undefined): string {
  if (coverage === null || coverage === undefined || coverage.required_seconds <= 0) return `${CRITICAL_RECORD} · Coverage unknown`;
  return `${CRITICAL_RECORD} · ${minutes(coverage)}`;
}
function criticalComplete(coverage: MiniCoverage | null | undefined): boolean {
  return (
    coverage !== null &&
    coverage !== undefined &&
    coverage.required_seconds > 0 &&
    coverage.observed_seconds >= coverage.required_seconds &&
    coverage.gaps.length === 0
  );
}

/** The hour bar: one Site-local clock hour (Q4/Q5), sent as UTC bounds. */
function MiniHourBar({
  timeZone,
  window,
  onApply,
}: {
  timeZone: string;
  window: MiniWindowQuery;
  onApply: (next: MiniWindowQuery) => void;
}) {
  const fromMs = window.from === null ? Number.NaN : Date.parse(window.from);
  const toMs = window.to === null ? Number.NaN : Date.parse(window.to);
  const known = !Number.isNaN(fromMs) && !Number.isNaN(toMs);
  const day0 = known ? localDateOf(timeZone, fromMs) : "";
  const hour0 = known ? localTimeOf(timeZone, fromMs).slice(0, 2) : "12";
  const [day, setDay] = useState(day0);
  const [hour, setHour] = useState(hour0);
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!day) return;
    onApply({ ...localHourWindow(timeZone, day, Number(hour)), known_at: window.known_at });
  };
  return (
    <form className="site-date-bar mini-period-bar" onSubmit={submit} data-mini-period>
      <span className="site-date-bar__window" data-mini-local-period>
        {known
          ? `Site-local hour ${day0} ${localTimeOf(timeZone, fromMs)}–${localTimeOf(timeZone, toMs)} (${timeZone})`
          : "No period selected"}
      </span>
      <span className="site-date-bar__cutoff" data-mini-utc-bounds>
        {`UTC ${window.from ?? UNKNOWN} to ${window.to ?? UNKNOWN}`}
        {window.known_at === null ? "" : ` · evidence cutoff ${window.known_at}`}
      </span>
      <label className="v69-chip-field">
        Day{" "}
        <input className="v69-chip-control" type="date" value={day} onChange={(e) => setDay(e.target.value)} />
      </label>
      <label className="v69-chip-field">
        Hour{" "}
        <select className="v69-chip-control" value={hour} onChange={(e) => setHour(e.target.value)}>
          {Array.from({ length: 24 }, (_, i) => String(i).padStart(2, "0")).map((h) => (
            <option key={h} value={h}>
              {`${h}:00`}
            </option>
          ))}
        </select>
      </label>
      <button type="submit" className="v69-chip-control">
        Apply
      </button>
    </form>
  );
}

function ServiceStatus({ read }: { read: ServiceRead }) {
  const word = SERVICE_STATUS_WORD[read.status] ?? UNKNOWN;
  const limits = Array.from(new Set(read.limitations.map((l) => plainCode(l.code))));
  return (
    <StatusBar label="Service assessment" items data={{ "data-mini-status": read.status }}>
      <span className="status-strip__item">
        <Badge tone="neutral" className={read.status === "LIMITED" ? "mini-tone--amber" : undefined}>
          {`Service assessment: ${word}`}
        </Badge>
      </span>
      <span className="status-strip__item" data-mini-currentness={read.currentness.state}>
        <Badge tone="neutral">{CURRENTNESS_WORD[read.currentness.state] ?? read.currentness.state}</Badge>
      </span>
      {provenanceChips(read).map((chip) => (
        <span className="status-strip__item" key={chip} data-mini-provenance>
          <Badge tone="neutral">{chip}</Badge>
        </span>
      ))}
      <StripLimitations lead={requestMissing(read) ? [SERVICE_REQUEST_MISSING] : []} limits={limits} />
      {read.currentness.state === "HISTORICAL" ? (
        <span className="status-strip__item" data-mini-historical>
          Historical selection; job state reflects the retained job record
        </span>
      ) : null}
    </StatusBar>
  );
}

function ServiceCardsRow({ read }: { read: ServiceRead }) {
  const cards = read.cards;
  const critical = read.rows.find((row) => row.role === "CRITICAL") ?? null;
  const interruptions = cards?.interruptions_seen ?? null;
  const delivered = cards?.delivered_load_kw ?? null;
  const criticalCoverage = read.critical_delivered_coverage ?? null;
  const criticalValue = cards?.critical_delivered_kw ?? null;
  // Ruling 2: a numeric critical card needs a value and its own complete coverage for the selected hour.
  const criticalKw = criticalValue !== null && criticalComplete(criticalCoverage) ? criticalValue : null;
  const unserved = cards?.unserved_kwh ?? null;
  return (
    <MetricCards label="Service summary" data={{ "data-mini-cards": "service" }} boundClass="mini-cards-bound mini-max--service-cards">
      <MetricCard
        label="Delivered load"
        value={kw(delivered)}
        note={delivered === null ? "Delivered power is not measured for the whole hour" : minutes(read.coverage)}
      />
      <MetricCard
        label="Interruptions seen"
        value={interruptions === null ? UNKNOWN : interruptions === 0 ? "None seen in measured intervals" : String(interruptions)}
        note={interruptions === null ? "Needs delivered and requested power for every load" : minutes(read.coverage)}
      />
      <MetricCard
        label={critical === null ? "Critical load" : `${critical.load_label} (critical)`}
        value={kw(criticalKw)}
        note={criticalNote(criticalCoverage)}
      />
      <MetricCard
        label="Unserved energy"
        value={kw(unserved, "kWh")}
        note={unserved === null ? "Needs demand or request evidence" : minutes(read.coverage)}
      />
    </MetricCards>
  );
}

function PowerPanel({ read }: { read: ServiceRead }) {
  return (
    <BoundedPanel
      bound="service-power"
      heading="Where the power went"
      headingId="mini-service-power-heading"
      description={requestMissing(read) ? "Delivered is measured · needed is not" : "Delivered and requested power use the same accepted hour"}
    >
      {read.rows.length === 0 ? (
        <p className="not-available-yet v69-chart-note" data-panel-gap="service-power">
          {SERVICE_EMPTY}
        </p>
      ) : (
        <ValueBars
          title="Delivered power by addressed load"
          items={[
            ...read.rows.map((row) => ({ key: row.asset_id, label: feederName(row), value: row.delivered_kw, valueText: kw(row.delivered_kw) })),
            { key: "needed", label: "What was needed", value: null, valueText: UNKNOWN },
          ]}
        />
      )}
      <MoreList
        summary="Coverage"
        items={[`Delivered power per addressed load, average of the selected hour. ${minutes(read.coverage)}. The hatched bar is the missing half of a service judgement.`]}
        data={{ "data-mini-coverage": "" }}
      />
    </BoundedPanel>
  );
}

function LoadTablePanel({ read, evidenceHref }: { read: ServiceRead; evidenceHref: string | null }) {
  return (
    <BoundedPanel bound="service-loads" table heading="Delivered power by addressed load" headingId="mini-service-loads-heading" flush>
      {read.rows.length === 0 ? (
        <p className="not-available-yet v69-chart-note" data-panel-gap="service-loads">
          {SERVICE_EMPTY}
        </p>
      ) : (
        <div className="mini-service-table mini-table-wrap">
          <DataTable labelledBy="mini-service-loads-heading">
            <thead>
              <tr>
                <th scope="col">Load</th>
                <th scope="col">Role</th>
                <th scope="col">Observed power</th>
                <th scope="col">Required-service evidence</th>
                <th scope="col">Assessment</th>
              </tr>
            </thead>
            <tbody>
              {read.rows.map((row) => (
                <tr key={row.asset_id} data-mini-row={row.assessment.toLowerCase()}>
                  <td>
                    {feederName(row)}
                    <span className="mini-cited">{` · ${row.asset_code}`}</span>
                  </td>
                  <td>{ROLE_WORD[row.role] ?? row.role}</td>
                  <td>
                    {kw(row.delivered_kw)}
                    <span className="mini-cited">{` · ${minutes(row.coverage).toLowerCase()}`}</span>
                  </td>
                  <td>
                    {REQUEST_WORD[row.requested_evidence_state] ?? row.requested_evidence_state}
                    <span className="mini-cited">
                      {` · ${row.evidence_ids.length} cited record${row.evidence_ids.length === 1 ? "" : "s"}`}
                      {evidenceHref === null ? null : (
                        <>
                          {" · "}
                          <Link to={evidenceHref}>Evidence</Link>
                        </>
                      )}
                    </span>
                  </td>
                  <td>
                    <Badge tone="neutral" className={`mini-decision--${row.assessment.toLowerCase()}`}>
                      {SERVICE_STATUS_WORD[row.assessment] ?? UNKNOWN}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        </div>
      )}
    </BoundedPanel>
  );
}

/** The evidence that would unlock a service conclusion, from the read's missing request rows and limitation codes. */
function unlockItems(read: ServiceRead): string[] {
  const items = read.rows
    .filter((row) => row.requested_evidence_state === "MISSING")
    .map((row) => `${loadName(row)}: an accepted requested-power record for the same hour`);
  const codes = new Set(read.limitations.map((l) => l.code));
  if (read.rows.length === 0 && codes.has("REQUEST_BASELINE_MISSING")) {
    items.push("Accepted delivered and requested power for each addressed load");
  }
  if (codes.has("COVERAGE_GAP")) items.push("Readings that cover the whole hour");
  if (codes.has("CONFLICT")) items.push("One accepted value where records conflict");
  if (codes.has("REQUIRED_INPUT_UNUSABLE")) items.push("A usable replacement for each unusable reading");
  return items;
}

function ServiceConclusionPanels({ read }: { read: ServiceRead }) {
  const unlocks = unlockItems(read);
  return (
    <div className="panel-pair">
      <BoundedPanel bound="service-supported" heading="What is supported" headingId="mini-service-supported-heading">
        <p className="prose" data-mini-supported>
          {SERVICE_SUPPORTED_COPY}
        </p>
      </BoundedPanel>
      <BoundedPanel bound="service-unlock" table heading="What unlocks a service conclusion" headingId="mini-service-unlock-heading">
        {unlocks.length === 0 ? (
          <p className="prose">No further evidence is listed for this hour.</p>
        ) : (
          <>
            <p className="prose" data-mini-unlock-summary>
              {`${unlocks.length} piece${unlocks.length === 1 ? "" : "s"} of evidence would unlock a conclusion:`}
            </p>
            <ul className="mini-drawer__list mini-shrink" tabIndex={0} aria-label="Evidence that would unlock a service conclusion" data-mini-unlocks>
              {unlocks.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </>
        )}
        <UnavailableLinkEntry label="See effect on verification" />
      </BoundedPanel>
    </div>
  );
}

export function MiniServicePage({ read }: { read: ServiceRead }) {
  return (
    <>
      <ServiceStatus read={read} />
      <ServiceCardsRow read={read} />
      <PowerPanel read={read} />
      <LoadTablePanel read={read} evidenceHref={read.links.evidence} />
      <ServiceConclusionPanels read={read} />
    </>
  );
}

/** The Service page body: the hour bar, then the selected read or its refusal. */
export function MiniService({
  client,
  siteCode,
  timeZone,
  window,
  pageHref,
}: {
  client: MiniDepthClient;
  siteCode: string;
  timeZone: string | null;
  window: MiniWindowQuery | null;
  pageHref: (search: string) => string;
}): ReactNode {
  const navigate = useNavigate();
  const [attempt, setAttempt] = useState(0);
  const key = `${siteCode}|${window?.from ?? ""}|${window?.to ?? ""}|${window?.known_at ?? ""}`;
  const read = useMiniRead<ServiceRead>(
    () => (window === null ? Promise.resolve({ status: "unavailable", message: null }) : client.getService(siteCode, window)),
    key,
    attempt,
  );
  if (timeZone === null || window === null) return <NoTimeZone />;
  return (
    <>
      <MiniHourBar key={key} timeZone={timeZone} window={window} onApply={(next) => navigate(pageHref(miniWindowSearch(next)))} />
      {read === null ? (
        <p role="status">{MINI_LOADING}</p>
      ) : read.status !== "loaded" ? (
        <MiniRefusal read={read} onRetry={() => setAttempt((n) => n + 1)} />
      ) : (
        <MiniServicePage read={read.value} />
      )}
    </>
  );
}

/* ---------- Fuel page (v69 `fuel`, q3-3 state table, q9 page dry-read, copy ledger, Q20) ---------- */

export const FUEL_NOTICE =
  "A fuel residual is unexplained inventory movement with uncertainty. It cannot establish theft or be added to dispatch fuel exposure.";
export const FUEL_SECONDARY = "A complete inventory balance needs deliveries and closing evidence.";
export const FUEL_INTERPRETATION =
  "Dispatch may have a separate modelled fuel quantity for a selected Finding. It is not a complete inventory balance.";
export const FUEL_DELIVERY_GAP = "Delivery completeness unconfirmed";
export const FUEL_RESIDUAL_GAP = "Cannot compute";

const FUEL_TERM_WORD: Record<string, string> = {
  OPENING: "Opening inventory",
  DELIVERIES: "Plus deliveries",
  USE: "Less generator consumption",
  CLOSING: "Less closing inventory",
  RESIDUAL: "Unexplained residual",
};

const FUEL_BASIS_WORD: Record<string, string> = {
  ACCEPTED_READING: "Accepted tank reading",
  AUTHORED_EVIDENCE_UNAVAILABLE: "No attested delivery record",
  FOUNDATION_MODEL: "Generator output × selected fuel coefficient",
  MISSING: "Missing",
};

/** The row's typed treatment in plain words; a tank reading without a registered bound stays Unknown (q3-2). */
function fuelTreatment(row: FuelRow): string {
  if (row.treatment === "MODELLED") return "Modelled range, not a fuel-meter reading";
  if (row.treatment === "COMPLETENESS_UNCONFIRMED") return FUEL_DELIVERY_GAP;
  if (row.treatment === "CONFLICT") return "Conflicting records";
  if (row.basis === "ACCEPTED_READING") {
    // q11-2: only a supported bound earns the bounded-reading words.
    const bounded = row.value !== null && row.value.low !== null && row.value.high !== null;
    return bounded ? "Accepted tank reading with bounded uncertainty" : "No bounded tank uncertainty is registered";
  }
  if (row.term === "RESIDUAL") return "Needs every term with a supported range; never infers theft";
  return "Missing";
}

/** A term's displayed amount: never `0 L` for a missing term (q9 dry-read). */
/** q12-7: a gap word (no bounded range) is set at the mock's word size so the card row keeps its budget. */
const fuelWord = (bound: MiniBound | null): boolean => bound === null || bound.low === null || bound.high === null;

function fuelValue(term: string, bound: MiniBound | null): string {
  if (bound !== null && bound.low !== null && bound.high !== null) return boundText(bound, "L");
  if (term === "DELIVERIES") return FUEL_DELIVERY_GAP;
  if (term === "RESIDUAL") return FUEL_RESIDUAL_GAP;
  return UNKNOWN;
}

const fuelRow = (read: FuelRead, term: string): FuelRow | null => read.rows.find((row) => row.term === term) ?? null;

function basisIds(read: FuelRead, key: string): string[] {
  const value = read.basis?.[key];
  return Array.isArray(value) ? value.filter((v): v is string => typeof v === "string") : [];
}

function FuelStatus({ read }: { read: FuelRead }) {
  const limited = read.status === "LIMITED";
  // q11-2: SUPPORTED is only reachable with accepted delivery completeness; never label it Unknown.
  const word = limited ? "Fuel balance: evidence limited" : read.status === "SUPPORTED" ? "Fuel balance: Supported" : "Fuel balance: Unknown";
  const limits = Array.from(new Set(read.limitations.map((l) => plainCode(l.code))));
  return (
    <StatusBar label="Fuel balance" items data={{ "data-mini-status": read.status }}>
      <span className="status-strip__item">
        <Badge tone="neutral" className={limited ? "mini-tone--amber" : undefined}>
          {word}
        </Badge>
      </span>
      {provenanceChips(read).map((chip) => (
        <span className="status-strip__item" key={chip} data-mini-provenance>
          <Badge tone="neutral">{chip}</Badge>
        </span>
      ))}
      <span className="status-strip__item" data-mini-currentness={read.currentness.state}>
        <Badge tone="neutral">{CURRENTNESS_WORD[read.currentness.state] ?? read.currentness.state}</Badge>
      </span>
      <StripLimitations lead={[FUEL_SECONDARY]} limits={limits} />
      {read.currentness.state === "HISTORICAL" ? (
        <span className="status-strip__item" data-mini-historical>
          Historical selection; job state reflects the retained job record
        </span>
      ) : null}
    </StatusBar>
  );
}

function FuelCardsRow({ read }: { read: FuelRead }) {
  const cards = read.cards;
  const use = fuelRow(read, "USE");
  const expected = cards?.expected_use_l ?? null;
  const useKnown = expected !== null && expected.low !== null && expected.high !== null;
  // q12-5: observed USE time exists only for a non-null USE coverage with observed_seconds > 0 and a bounded
  // expected use; minutes come from those seconds, and under a minute the seconds are stated (never `for 0 min`).
  const useSeconds =
    useKnown && use !== null && use.coverage !== null && use.coverage.observed_seconds > 0 ? use.coverage.observed_seconds : null;
  const useSpan =
    useSeconds === null ? null : useSeconds < 60 ? `${useSeconds} s` : `${NUMBER.format(useSeconds / 60)} min`;
  return (
    <MetricCards label="Fuel balance summary" data={{ "data-mini-cards": "fuel" }} boundClass="mini-cards-bound mini-max--fuel-cards">
      <MetricCard label="Opening evidence" value={fuelValue("OPENING", cards?.opening_l ?? null)} word={fuelWord(cards?.opening_l ?? null)} note="Accepted tank opening or Unknown" />
      <MetricCard
        label="Recorded deliveries"
        value={fuelValue("DELIVERIES", cards?.deliveries_l ?? null)}
        word={fuelWord(cards?.deliveries_l ?? null)}
        note="Complete delivery record unavailable"
      />
      <MetricCard
        label="Modelled expected use"
        value={fuelValue("USE", expected)}
        word={fuelWord(expected)}
        note={
          // q11-2: the note needs both a bounded value and observed USE minutes; no guessed numbers.
          // q12-7: two short visible lines at most; the full modelling explanation sits behind the card-note disclosure.
          useSpan !== null ? (
            <>
              <MoreList
                summary="Modelled from generator output"
                items={[`Modelled: generator output for ${useSpan} × selected fuel coefficient with selected bound`]}
                data={{ "data-mini-use-basis": "" }}
              />
            </>
          ) : (
            "Modelled quantity unavailable"
          )
        }
      />
      <MetricCard label="Residual" value={fuelValue("RESIDUAL", cards?.residual_l ?? null)} word={fuelWord(cards?.residual_l ?? null)} note="Cannot compute without complete deliveries" />
    </MetricCards>
  );
}

function FuelGlancePanel({ read }: { read: FuelRead }) {
  const cards = read.cards;
  const bar = (key: string, label: string, term: string, bound: MiniBound | null) => ({
    key,
    label,
    value: bound === null || bound.low === null || bound.high === null ? null : bound.high,
    valueText: fuelValue(term, bound),
  });
  return (
    <Panel heading="Fuel balance at a glance" headingId="mini-fuel-glance-heading" description="Opening + deliveries − use − closing">
      <ValueBars
        title="Fuel balance terms"
        items={[
          bar("opening", "Opening tank", "OPENING", cards?.opening_l ?? null),
          bar("deliveries", "+ Deliveries", "DELIVERIES", cards?.deliveries_l ?? null),
          bar("use", "− Modelled generator use", "USE", cards?.expected_use_l ?? null),
          bar("closing", "− Closing tank", "CLOSING", cards?.closing_l ?? null),
          bar("residual", "= Unexplained", "RESIDUAL", cards?.residual_l ?? null),
        ]}
      />
      <ChartNote data={{ "data-mini-coverage": "" }}>
        Hatched bars are missing evidence. A residual is shown only when every term has a supported range.
      </ChartNote>
    </Panel>
  );
}

function FuelBridgePanel({ read, evidenceHref }: { read: FuelRead; evidenceHref: string | null }) {
  return (
    <BoundedPanel bound="fuel-bridge" table heading="Balance bridge" headingId="mini-fuel-bridge-heading" flush>
      {read.rows.length === 0 ? (
        <p className="not-available-yet v69-chart-note" data-panel-gap="fuel-bridge">
          No fuel hour has been assessed for this period.
        </p>
      ) : (
        <DataTable labelledBy="mini-fuel-bridge-heading">
          <thead>
            <tr>
              <th scope="col">Term</th>
              <th scope="col">Evidence basis</th>
              <th scope="col">Treatment</th>
            </tr>
          </thead>
          <tbody>
            {read.rows.map((row) => (
              <tr key={row.term} data-mini-term={row.term}>
                <td>
                  {FUEL_TERM_WORD[row.term] ?? row.term}
                  <span className="mini-cited">{` · ${fuelValue(row.term, row.value)}`}</span>
                </td>
                <td>
                  {FUEL_BASIS_WORD[row.basis] ?? row.basis}
                  <span className="mini-cited">
                    {` · ${row.evidence_ids.length} cited record${row.evidence_ids.length === 1 ? "" : "s"}`}
                    {evidenceHref === null || row.evidence_ids.length === 0 ? null : (
                      <>
                        {" · "}
                        <Link to={evidenceHref}>Evidence</Link>
                      </>
                    )}
                  </span>
                </td>
                <td>{fuelTreatment(row)}</td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      )}
    </BoundedPanel>
  );
}

function FuelBasisDrawer({ read, onClose }: { read: FuelRead; onClose: () => void }) {
  const sfc = basisIds(read, "specific_fuel_consumption_property_revision_ids");
  const power = basisIds(read, "generator_power_evidence_ids");
  return (
    <div className="mini-drawer mini-shrink" role="region" tabIndex={0} aria-labelledby="mini-fuel-drawer-heading" data-mini-drawer="fuel">
      <h3 id="mini-fuel-drawer-heading">Fuel basis</h3>
      <h4>Modelled generator use</h4>
      <ul className="mini-drawer__list">
        <li>{`Treatment: Modelled · ${fuelValue("USE", read.cards?.expected_use_l ?? null)}`}</li>
        <li className="mini-ids">{`Fuel coefficient revisions: ${sfc.length === 0 ? "None selected" : sfc.join(", ")}`}</li>
        <li className="mini-ids">{`Generator power records: ${power.length === 0 ? "None cited" : power.join(", ")}`}</li>
      </ul>
      <h4>Cited records by term</h4>
      <ul className="mini-drawer__list">
        {read.rows.map((row) => (
          <li key={row.term} className="mini-ids">
            {`${FUEL_TERM_WORD[row.term] ?? row.term}: ${row.evidence_ids.length === 0 ? "None" : row.evidence_ids.join(", ")}`}
          </li>
        ))}
      </ul>
      <button type="button" className="v69-claim-button" onClick={onClose}>
        Close
      </button>
    </div>
  );
}

function FuelInterpretationPanel({ read }: { read: FuelRead }) {
  const [open, setOpen] = useState(false);
  return (
    <BoundedPanel bound="fuel-interpretation" table heading="Inspect existing generator fuel interpretation" headingId="mini-fuel-interpretation-heading">
      <p className="prose">{FUEL_INTERPRETATION}</p>
      <p>
        {/* q9 dry-read: `links.financials` is null in W4-02, so no dispatch consequence is linked. */}
        <span className="v69-unavailable-inline" data-link-unavailable="dispatch-consequence">
          No linked dispatch consequence
        </span>{" "}
        <button
          type="button"
          className="v69-claim-button"
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
          data-mini-drawer-open="fuel"
        >
          Inspect fuel basis
        </button>
      </p>
      {open ? <FuelBasisDrawer read={read} onClose={() => setOpen(false)} /> : null}
    </BoundedPanel>
  );
}

export function MiniFuelPage({ read }: { read: FuelRead }) {
  return (
    <>
      <FuelStatus read={read} />
      <FuelCardsRow read={read} />
      <FuelGlancePanel read={read} />
      <FuelBridgePanel read={read} evidenceHref={read.links.evidence} />
      <Notice data={{ "data-mini-notice": "fuel" }}>{FUEL_NOTICE}</Notice>
      <FuelInterpretationPanel read={read} />
    </>
  );
}

/** The Fuel page body: the hour bar, then the selected read or its refusal. */
export function MiniFuel({
  client,
  siteCode,
  timeZone,
  window,
  pageHref,
}: {
  client: MiniDepthClient;
  siteCode: string;
  timeZone: string | null;
  window: MiniWindowQuery | null;
  pageHref: (search: string) => string;
}): ReactNode {
  const navigate = useNavigate();
  const [attempt, setAttempt] = useState(0);
  const key = `${siteCode}|${window?.from ?? ""}|${window?.to ?? ""}|${window?.known_at ?? ""}`;
  const read = useMiniRead<FuelRead>(
    () => (window === null ? Promise.resolve({ status: "unavailable", message: null }) : client.getFuel(siteCode, window)),
    key,
    attempt,
  );
  if (timeZone === null || window === null) return <NoTimeZone />;
  return (
    <>
      <MiniHourBar key={key} timeZone={timeZone} window={window} onApply={(next) => navigate(pageHref(miniWindowSearch(next)))} />
      {read === null ? (
        <p role="status">{MINI_LOADING}</p>
      ) : read.status !== "loaded" ? (
        <MiniRefusal read={read} onRetry={() => setAttempt((n) => n + 1)} />
      ) : (
        <MiniFuelPage read={read.value} />
      )}
    </>
  );
}

/* ---------- Backup page (v69 `backup`, Q22, q3-8, q5-2/3/4, q9 page dry-read, copy ledger) ---------- */

export const BACKUP_SECONDARY = "Generator operation alone is not a witnessed start-and-recovery test";
export const BACKUP_NO_CHAIN = "No complete outage chain can be assessed";
export const BACKUP_NO_OUTAGE = "No outage in the selected hour";
export const BACKUP_OPERATING =
  "Generator operation supports runtime reconstruction. It does not establish automatic backup readiness.";
export const BACKUP_NEXT =
  "Record a witnessed start-to-service test with command, state, power path and critical-service observations.";
const NO_ACCEPTED_RECORD = "No accepted record";

const BACKUP_RESULT_WORD: Record<string, string> = { PASS: "Pass", FAIL: "Fail", INCOMPLETE: "Incomplete" };
const BACKUP_OUTCOME_WORD: Record<string, string> = {
  RECOVERED: "Recovered",
  MISSED_TARGET: "Missed recovery target",
  UNKNOWN: "Unknown",
};

/** Q22: the four fixed readiness rows and the stored steps each one reads. */
const READINESS_ROWS: { label: string; steps: string[] }[] = [
  { label: "Supply interruption", steps: ["LOSS"] },
  { label: "Start command and state", steps: ["REQUEST", "START"] },
  { label: "Power restored to critical service", steps: ["POWER", "LOAD", "SERVICE"] },
  { label: "Witnessed outcome", steps: [] },
];

const chainStep = (row: BackupRow, code: string): BackupStep | null => row.steps.find((step) => step.code === code) ?? null;

function stepCell(step: BackupStep | null, timeZone: string): string {
  if (step === null || step.state === "MISSING") return NO_ACCEPTED_RECORD;
  const at = step.at === null ? "" : ` ${localTimeOf(timeZone, Date.parse(step.at))}`;
  return step.state === "CONFLICT" ? `Conflicting records${at}` : `Observed${at}`;
}

const minutesOf = (seconds: number | null): string => (seconds === null ? UNKNOWN : `${NUMBER.format(seconds / 60)} min`);

/** q11-3(a): the displayed sample, one per shown chain whose REQUEST and START are both OBSERVED. */
const witnessedPairs = (read: BackupRead): number =>
  read.rows.filter((row) => chainStep(row, "REQUEST")?.state === "OBSERVED" && chainStep(row, "START")?.state === "OBSERVED")
    .length;

/** Shown chains in `(outage_start, chain_id)` order, so the latest chain and the cited-ID order are deterministic (q11-4). */
const chainsInOrder = (read: BackupRead): BackupRow[] =>
  [...read.rows].sort((a, b) =>
    a.outage_start === b.outage_start ? a.chain_id.localeCompare(b.chain_id) : Date.parse(a.outage_start) - Date.parse(b.outage_start),
  );

/** q11-3(a): `Start success` is a count of witnessed successes, never a rate or readiness claim. */
function startSuccessNote(starts: number | null, pairs: number): string {
  if (starts === null) return "No witnessed start request and result";
  if (pairs > 0 && starts <= pairs) return `Of ${pairs} witnessed request/result pair${pairs === 1 ? "" : "s"} in shown chains`;
  return "Witnessed pair count unavailable";
}

function BackupStatus({ read }: { read: BackupRead }) {
  const limited = read.status === "LIMITED";
  const limits = Array.from(new Set(read.limitations.map((l) => plainCode(l.code))));
  return (
    <StatusBar label="Backup readiness" items data={{ "data-mini-status": read.status }}>
      <span className="status-strip__item">
        <Badge tone="neutral">Backup readiness: Unknown</Badge>
      </span>
      {provenanceChips(read).map((chip) => (
        <span className="status-strip__item" key={chip} data-mini-provenance>
          <Badge tone="neutral">{chip}</Badge>
        </span>
      ))}
      <span className="status-strip__item" data-mini-currentness={read.currentness.state}>
        <Badge tone="neutral">{CURRENTNESS_WORD[read.currentness.state] ?? read.currentness.state}</Badge>
      </span>
      <StripLimitations
        lead={[BACKUP_SECONDARY]}
        limits={limits}
        summary={
          limited ? (
            <span data-mini-chain-status>
              <Badge tone="neutral" className="mini-tone--amber">
                Outage-chain assessment: evidence limited
              </Badge>
            </span>
          ) : undefined
        }
      />
      {read.currentness.state === "HISTORICAL" ? (
        <span className="status-strip__item" data-mini-historical>
          Historical selection; job state reflects the retained job record
        </span>
      ) : null}
    </StatusBar>
  );
}

function BackupCardsRow({ read, timeZone }: { read: BackupRead; timeZone: string }) {
  const cards = read.cards;
  const outages = cards?.outage_count ?? null;
  const starts = cards?.start_success_count ?? null;
  const test = cards?.last_witnessed_test_at ?? null;
  const recovery = cards?.critical_recovery ?? null;
  const pairs = witnessedPairs(read);
  return (
    <MetricCards label="Backup summary" data={{ "data-mini-cards": "backup" }} boundClass="mini-cards-bound mini-max--backup-cards">
      <MetricCard
        label="Outages in window"
        value={outages === null ? UNKNOWN : String(outages)}
        word={outages === null}
        note={outages === null ? "Supply reports do not cover the whole hour" : "Supply interruptions seen"}
      />
      <MetricCard
        label="Start success"
        value={starts === null ? UNKNOWN : `${starts} witnessed success${starts === 1 ? "" : "es"}`}
        word
        note={startSuccessNote(starts, pairs)}
      />
      <MetricCard
        label="Last witnessed test"
        value={test === null ? "No record" : localDateOf(timeZone, Date.parse(test))}
        word={test === null}
        note={test === null ? "No accepted witnessed test record" : "Accepted witnessed test record"}
      />
      <MetricCard
        label="Critical service recovery"
        value={recovery === null ? UNKNOWN : minutesOf(recovery.seconds)}
        word={recovery === null}
        note={
          recovery === null
            ? "Needs requested and delivered critical-service power"
            : `Target ${minutesOf(recovery.target_seconds)} · latest valid chain`
        }
      />
    </MetricCards>
  );
}

const CHAIN_COLUMNS = ["When", "Grid", "Start requested", "Generator", "Power to load", "Load response", "Outcome for service", "Result"];

function BackupChainsPanel({ read, timeZone }: { read: BackupRead; timeZone: string }) {
  // q11-3(d): a non-null zero `outage_count` is the projection's proof of complete supply-hour coverage; W4-02's
  // instant reports never reach it (q3-8), so the empty copy is the incomplete-chain line.
  const empty = read.cards?.outage_count === 0 ? BACKUP_NO_OUTAGE : BACKUP_NO_CHAIN;
  return (
    <Panel
      heading="Backup event chains"
      headingId="mini-backup-chains-heading"
      description="Grid → start → generator → power → load → service"
      flush
    >
      <div className="mini-backup-chains">
        <DataTable labelledBy="mini-backup-chains-heading">
          <thead>
            <tr>
              {CHAIN_COLUMNS.map((h) => (
                <th scope="col" key={h}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {read.rows.length === 0 ? (
              <tr data-mini-chain="none">
                <td data-panel-gap="backup-chains">
                  <span className="not-available-yet">{empty}</span>
                </td>
                {Array.from({ length: 6 }, (_, i) => (
                  <td key={i}>—</td>
                ))}
                <td>
                  <Badge tone="neutral">No event</Badge>
                </td>
              </tr>
            ) : (
              read.rows.map((row) => {
                const start = Date.parse(row.outage_start);
                return (
                  <tr key={row.chain_id} data-mini-chain={row.result.toLowerCase()}>
                    <td>{`${localDateOf(timeZone, start)} ${localTimeOf(timeZone, start)}`}</td>
                    <td>{stepCell(chainStep(row, "LOSS"), timeZone)}</td>
                    <td>{stepCell(chainStep(row, "REQUEST"), timeZone)}</td>
                    <td>{stepCell(chainStep(row, "START"), timeZone)}</td>
                    <td>{stepCell(chainStep(row, "POWER"), timeZone)}</td>
                    <td>{stepCell(chainStep(row, "LOAD"), timeZone)}</td>
                    <td>
                      {stepCell(chainStep(row, "SERVICE"), timeZone)}
                      <span className="mini-cited">{` · ${BACKUP_OUTCOME_WORD[row.service_outcome] ?? UNKNOWN}`}</span>
                    </td>
                    <td>
                      <Badge tone="neutral" className={`mini-decision--${row.result.toLowerCase()}`}>
                        {BACKUP_RESULT_WORD[row.result] ?? row.result}
                      </Badge>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </DataTable>
      </div>
    </Panel>
  );
}

/** One readiness row: the cited IDs of its non-MISSING steps across the shown chains (conflicting ones included), and
 * the latest chain's step words; `Witnessed outcome` needs a separately accepted test, which W4-02 never has (q11-4). */
function readinessCells(read: BackupRead, steps: string[]): { ids: string[]; claim: string } {
  if (steps.length === 0) return { ids: [], claim: "Readiness remains unverified" };
  const chains = chainsInOrder(read);
  const latest = chains.length === 0 ? null : chains[chains.length - 1];
  if (latest === null) return { ids: [], claim: "No outage-chain assessment" };
  const ids = Array.from(
    new Set(
      chains.flatMap((row) =>
        steps.flatMap((code) => {
          const step = chainStep(row, code);
          return step === null || step.state === "MISSING" ? [] : step.evidence_ids;
        }),
      ),
    ),
  );
  const states = steps.map((code) => chainStep(latest, code)?.state ?? "MISSING");
  const word = states.every((x) => x === "OBSERVED")
    ? "Observed"
    : states.includes("CONFLICT")
      ? "Conflicting records"
      : states.every((x) => x === "MISSING")
        ? NO_ACCEPTED_RECORD
        : "Partly observed";
  return {
    ids,
    claim: `${word} · chain result ${BACKUP_RESULT_WORD[latest.result] ?? latest.result}`,
  };
}

function BackupReadinessPanel({ read }: { read: BackupRead }) {
  return (
    <BoundedPanel bound="backup-readiness" table heading="Backup readiness evidence" headingId="mini-backup-readiness-heading" flush>
      <div className="mini-backup-readiness mini-table-wrap">
        <DataTable labelledBy="mini-backup-readiness-heading">
          <thead>
            <tr>
              <th scope="col">Required step</th>
              <th scope="col">Available evidence</th>
              <th scope="col">Current claim (latest observed outage chain)</th>
            </tr>
          </thead>
          <tbody>
            {READINESS_ROWS.map(({ label, steps }) => {
              const cells = readinessCells(read, steps);
              return (
                <tr key={label} data-mini-readiness={label}>
                  <td>{label}</td>
                  <td data-mini-evidence-count={cells.ids.length}>
                    {cells.ids.length === 0 ? (
                      NO_ACCEPTED_RECORD
                    ) : (
                      <>
                        {`${cells.ids.length} cited record${cells.ids.length === 1 ? "" : "s"}`}
                        <MoreList summary="Inspect IDs" items={cells.ids} ids data={{ "data-mini-ids": label }} />
                      </>
                    )}
                  </td>
                  <td>{cells.claim}</td>
                </tr>
              );
            })}
          </tbody>
        </DataTable>
      </div>
    </BoundedPanel>
  );
}

function BackupEvidencePanels({ read }: { read: BackupRead }) {
  return (
    <div className="panel-pair">
      <Panel heading="Operating evidence" headingId="mini-backup-operating-heading">
        <p className="prose">{BACKUP_OPERATING}</p>
        <p>
          {read.links.dispatch === null ? (
            <UnavailableInline label="Open Dispatch" />
          ) : (
            <Link to={read.links.dispatch}>Open Dispatch →</Link>
          )}
        </p>
      </Panel>
      <Panel heading="Next evidence" headingId="mini-backup-next-heading">
        <p className="prose">{BACKUP_NEXT}</p>
        <p>
          {read.links.actions === null ? (
            <UnavailableInline label="Browse Actions" />
          ) : (
            <Link to={read.links.actions}>Browse Actions →</Link>
          )}
        </p>
      </Panel>
    </div>
  );
}

export function MiniBackupPage({ read, timeZone }: { read: BackupRead; timeZone: string }) {
  return (
    <>
      <BackupStatus read={read} />
      <BackupCardsRow read={read} timeZone={timeZone} />
      <BackupChainsPanel read={read} timeZone={timeZone} />
      <BackupReadinessPanel read={read} />
      <BackupEvidencePanels read={read} />
    </>
  );
}

/** The Backup page body: the hour bar, then the selected read or its refusal. */
export function MiniBackup({
  client,
  siteCode,
  timeZone,
  window,
  pageHref,
}: {
  client: MiniDepthClient;
  siteCode: string;
  timeZone: string | null;
  window: MiniWindowQuery | null;
  pageHref: (search: string) => string;
}): ReactNode {
  const navigate = useNavigate();
  const [attempt, setAttempt] = useState(0);
  const key = `${siteCode}|${window?.from ?? ""}|${window?.to ?? ""}|${window?.known_at ?? ""}`;
  const read = useMiniRead<BackupRead>(
    () => (window === null ? Promise.resolve({ status: "unavailable", message: null }) : client.getBackup(siteCode, window)),
    key,
    attempt,
  );
  if (timeZone === null || window === null) return <NoTimeZone />;
  return (
    <>
      <MiniHourBar key={key} timeZone={timeZone} window={window} onApply={(next) => navigate(pageHref(miniWindowSearch(next)))} />
      {read === null ? (
        <p role="status">{MINI_LOADING}</p>
      ) : read.status !== "loaded" ? (
        <MiniRefusal read={read} onRetry={() => setAttempt((n) => n + 1)} />
      ) : (
        <MiniBackupPage read={read.value} timeZone={timeZone} />
      )}
    </>
  );
}
