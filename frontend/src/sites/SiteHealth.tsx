/**
 * S7-01b Site Health (`health:2#a`) over S7-01a's source-health and battery
 * entry reads, rebuilt by W1-F5a to the v69 `health` panels
 * (`D-2026-10-17-mockup-layout-spec`): a status strip about physical asset
 * condition, then "Physical asset condition" and "Data sources · data quality,
 * not equipment condition". Content is limited to what the reads support
 * (`D-2026-10-16-a-s7-health`, `D-2026-10-16-s701-clock`):
 *
 * - Condition comes only from the battery entry read (Unknown). Gateway
 *   contact never decides it and sits in the data-sources panel.
 * - Contact (server receipt), what each gateway last reported (age, queue,
 *   storage) and device contact reported by gateways are separate columns or
 *   rows. Disabled gateways are listed with "Disabled" and are not counted.
 * - An age is shown only when the read states one; otherwise "Unknown age"
 *   with the clock reason. Never a signed age.
 * - Exact IDs, rule and watermark sit in "Technical details", closed by default.
 */
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

import {
  Badge,
  ChartNote,
  DataTable,
  Disclosure,
  ExactReferences,
  Fact,
  FactList,
  KeyValues,
  MissingClaim,
  Panel,
  ProductStatus,
  readResultWords,
  StatusBar,
  V69Notice,
  type ProductWords,
} from "../ui";
import { contactSummaryWords, gatewayContactWords, siteConditionWords } from "./healthHeadlines";
import type {
  BatteryEntry,
  GatewayHealthRow,
  HealthClient,
  HealthRead,
  HealthRefusal,
  SourceHealthDocument,
} from "./healthClient";

/** Addresses the Health and battery screens link to, supplied by the shell frames (the substrate is a leaf). */
export interface HealthLinks {
  health(siteId: string, gatewayId?: string | null): string;
  assets(siteId: string): string;
  asset(siteId: string, assetId: string): string;
}

export const HealthLinksContext = createContext<HealthLinks | null>(null);

export function useHealthLinks(): HealthLinks {
  const links = useContext(HealthLinksContext);
  if (links === null) throw new Error("HealthLinksContext is not provided");
  return links;
}

/** An exact source-owned value, exempt from the plain-language scan. */
export function HealthRef({ value }: { value: string | number | null | undefined }) {
  return (
    <code className="health-ref" data-vocabulary-exempt="source-reference">
      {value === null || value === undefined ? "none" : String(value)}
    </code>
  );
}

/** "7 s", "10 min", "6 h 0 min", "2 d 3 h". Never signed: callers pass only stated, non-negative ages. */
export function formatAge(seconds: number): string {
  if (seconds < 60) return `${seconds} s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)} min`;
  if (seconds < 86400) {
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${Math.floor(seconds / 3600)} h${minutes ? ` ${minutes} min` : ""}`;
  }
  const hours = Math.floor((seconds % 86400) / 3600);
  return `${Math.floor(seconds / 86400)} d${hours ? ` ${hours} h` : ""}`;
}

/** `2026-10-16 09:10:05 UTC` from the read's UTC instant. */
export function formatInstant(value: string | null | undefined): string {
  if (!value) return "none";
  const match = /^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}:\d{2})/.exec(value);
  return match ? `${match[1]} ${match[2]} UTC` : value;
}

const CONTACT_WORDS: Record<string, string> = { CURRENT: "Current", STALE: "Stale", UNKNOWN: "Unknown" };

function contactText(row: GatewayHealthRow): string {
  const c = row.contact;
  if (c.reason === "NEVER_RECEIVED") return "Never received";
  if (c.status === "STALE") {
    return `Stale: nothing received for ${formatAge(c.since_last_receipt_seconds ?? 0)} (limit ${formatAge(
      c.threshold_seconds,
    )}); when it stopped is not known`;
  }
  if (c.status === "CURRENT") return `Current: received ${formatAge(c.since_last_receipt_seconds ?? 0)} ago`;
  return CONTACT_WORDS[c.status] ?? c.status;
}

/** Why a gateway-reported age is not stated. */
function unknownAgeReason(row: GatewayHealthRow): string {
  const f = row.reported_facts;
  if (f.reason === "NEVER_RECEIVED") return "nothing received yet";
  if (f.clock.trust === "UNTRUSTED") {
    const offset = f.clock.offset_ms === null ? "" : ` is off by ${Math.round(Math.abs(f.clock.offset_ms) / 1000)} s,`;
    return `the gateway's clock${offset} more than the ${Math.round(f.clock.tolerance_ms / 1000)} s allowed, so its times are not trusted`;
  }
  if (f.reason === "OBSERVED_AFTER_RECEIPT") return "its reported time is later than the server received it";
  return "its reported time is later than this read";
}

function reportedText(row: GatewayHealthRow): string {
  const f = row.reported_facts;
  if (f.reason === "NEVER_RECEIVED") return "Nothing received yet";
  const age = f.fact_age_seconds;
  // S7-01b L1: a time observed after the server received it has no stated age, whatever the read's number.
  if (age === null || f.reason === "OBSERVED_AFTER_RECEIPT") return `Unknown age: ${unknownAgeReason(row)}`;
  if (f.status === "OLD") {
    const lag =
      f.receipt_lag_seconds !== null && f.receipt_lag_seconds >= 60
        ? `; it reached the server ${formatAge(f.receipt_lag_seconds)} after it was observed`
        : "";
    return `Old: observed ${formatAge(age)} ago${lag}`;
  }
  if (f.status === "CURRENT") return `Current: observed ${formatAge(age)} ago`;
  return `Unknown: observed ${formatAge(age)} ago`;
}

const DISK_WORDS: Record<string, string> = {
  OK: "Normal",
  WARN: "Warning",
  STOP: "Full: collection stopped",
};

/** The plain heading and sentence for a refused read (HTTP status and server code kept by the caller). */
export function refusalText(
  refusal: HealthRefusal,
  subject: string,
  texts: Record<string, string> = {},
): { heading: string; text: string } {
  const byCode = refusal.code ? texts[refusal.code] : undefined;
  const heading =
    refusal.http === 401
      ? "Sign in required"
      : refusal.http === 403
        ? "No access"
        : refusal.http === 404
          ? `${subject} not found`
          : `${subject} unavailable`;
  const text =
    byCode ??
    (refusal.http === null
      ? "The server could not be reached, so nothing is known right now."
      : refusal.http === 401
        ? `Sign in to read this site's ${subject.toLowerCase()}.`
        : refusal.http === 403
          ? "Your account has no access to this site."
          : refusal.http === 404
            ? "This site is not configured, so it has nothing to show."
            : `The ${subject.toLowerCase()} could not be read (HTTP ${refusal.http}), so nothing is stated.`);
  return { heading, text };
}

/** The shared read-result words for a refused read; a refused read has no read time. */
export function refusalWords(refusal: HealthRefusal): ProductWords {
  return readResultWords(
    refusal.http === 401 || refusal.http === 403 ? "refused" : refusal.http === 404 ? "not-found" : "unavailable",
  );
}

/**
 * W1-F5a: a refused read stated inside the v69 panel that owns it (never a
 * replacement panel). The HTTP status and server code stay on the element and
 * in the small exact-reference disclosure.
 */
export function HealthGap({
  refusal,
  subject,
  name,
  texts = {},
  children,
}: {
  refusal: HealthRefusal;
  subject: string;
  /** Names the exact-reference disclosure. */
  name: string;
  texts?: Record<string, string>;
  children?: ReactNode;
}) {
  const { heading, text } = refusalText(refusal, subject, texts);
  return (
    <div
      className="health-gap"
      data-health-read="refused"
      data-health-http={refusal.http ?? "none"}
      data-health-code={refusal.code ?? ""}
    >
      <p>
        <strong data-health-gap-label>{heading}.</strong> {text} {refusalWords(refusal).label}; this is not an empty
        result.
      </p>
      {children}
      <ExactReferences
        name={name}
        variant="tech"
        references={[
          { label: "Server answer code", value: refusal.code },
          { label: "Web status", value: refusal.http === null ? null : String(refusal.http) },
        ]}
      />
    </div>
  );
}

/** A typed refusal of one read as its own panel (the battery entry page, which is not a v69 screen). */
export function HealthRefusalPanel({
  refusal,
  subject,
  headingId,
  texts = {},
  children,
  scope,
}: {
  refusal: HealthRefusal;
  subject: string;
  /** What the refused read was about, in plain words (W1-UX-05 state line). */
  scope?: ReactNode;
  headingId: string;
  texts?: Record<string, string>;
  children?: ReactNode;
}) {
  const { heading, text } = refusalText(refusal, subject, texts);
  return (
    <Panel heading={heading} headingId={headingId}>
      {/* W1-UX-05: the plain state line; a refused read has no read time, so "as of" says so. */}
      <ProductStatus words={refusalWords(refusal)} scope={scope ?? subject} asOf={null} />
      <p data-health-read="refused" data-health-http={refusal.http ?? "none"} data-health-code={refusal.code ?? ""}>
        {text}
      </p>
      {children}
      <ExactReferences
        name={`${headingId}-code`}
        references={[
          { label: "Server answer code", value: refusal.code },
          { label: "Web status", value: refusal.http === null ? null : String(refusal.http) },
        ]}
      />
    </Panel>
  );
}

function useRead<T>(load: () => Promise<HealthRead<T>>, key: string): HealthRead<T> | null {
  const [state, setState] = useState<{ key: string; read: HealthRead<T> } | null>(null);
  useEffect(() => {
    let live = true;
    load().then((read) => {
      if (live) setState({ key, read });
    });
    return () => {
      live = false;
    };
    // `key` names the read; `load` is recreated every render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  return state && state.key === key ? state.read : null;
}

export { useRead as useHealthRead };


const HEALTH_TEXTS: Record<string, string> = {
  SOURCE_HEALTH_UNAVAILABLE:
    "The gateway contact store could not be read, so nothing is known about gateway contact right now.",
  SOURCE_HEALTH_SELECTION_INCONSISTENT:
    "Gateway registrations and their reports did not agree when they were read, so no contact is stated. Reload to read again.",
};

const BATTERY_TEXTS: Record<string, string> = {
  ASSET_BOUNDARY_UNAVAILABLE: "The site's configuration could not be read, so nothing is stated about its battery.",
  FOUNDATION_BASIS_UNAVAILABLE:
    "The site's configuration could not be read consistently, so nothing is stated about its battery.",
};

export { BATTERY_TEXTS };

const CONDITION_HEADING = "Physical asset condition";
const SOURCES_HEADING = "Data sources · data quality, not equipment condition";

/** `09:10 UTC` from the read's UTC instant, for the mock's "Status at" column. */
function clockTime(value: string): string {
  const match = /T(\d{2}:\d{2})/.exec(value);
  return match ? `${match[1]} UTC` : formatInstant(value);
}

export function SiteHealth({
  siteId,
  siteName,
  client,
  selectedGateway,
}: {
  siteId: string;
  /** The site's display name, for the status strip's scope. */
  siteName: string;
  client: HealthClient;
  selectedGateway: string | null;
}) {
  const links = useHealthLinks();
  const health = useRead(() => client.getSourceHealth(siteId), `health:${siteId}`);
  const battery = useRead(() => client.getBatteryEntry(siteId), `battery:${siteId}`);
  if (health === null || battery === null) {
    return <p>Loading the site's gateway contact.</p>;
  }
  return (
    <div className="site-health" data-health-site={siteId}>
      <ConditionStrip siteName={siteName} read={battery} batteryHref={links.assets(siteId)} />
      <Panel
        heading={CONDITION_HEADING}
        headingId="site-health-condition-heading"
        description="Opening an asset moves you to the battery page; the breadcrumb keeps this site"
      >
        <ConditionBody siteId={siteId} read={battery} />
      </Panel>
      <Panel
        heading={SOURCES_HEADING}
        headingId="site-health-sources-heading"
        description="Current · Stale · Never received · Disabled. Contact means the server received a gateway's report; it says nothing about the equipment."
      >
        {health.status === "refused" ? (
          <HealthGap refusal={health} subject="Gateway contact" name="site-health-refused-code" texts={HEALTH_TEXTS} />
        ) : (
          <SourcesBody siteId={siteId} doc={health.value} selectedGateway={selectedGateway} />
        )}
      </Panel>
      <V69Notice tone="blue">
        A gateway being heard from does not make equipment healthy. Gateway contact, what gateways report about
        themselves, and battery condition are separate, and none of them is a statement about equipment condition.
      </V69Notice>
    </div>
  );
}

/** The mock's status line: physical asset condition only, said once. */
function ConditionStrip({
  siteName,
  read,
  batteryHref,
}: {
  siteName: string;
  read: HealthRead<BatteryEntry>;
  batteryHref: string;
}) {
  if (read.status === "refused") {
    return (
      <StatusBar data={{ "data-health-strip": "refused" }}>
        <ProductStatus inline words={refusalWords(read)} scope={`${siteName} · asset condition`} asOf={null} />
      </StatusBar>
    );
  }
  const entry = read.value;
  const count = entry.configuration === "CONFIGURED" ? entry.batteries.length : 0;
  const scope =
    count === 0
      ? `${siteName} · no configured battery · summary only`
      : `${siteName} · ${count} configured ${count === 1 ? "battery" : "batteries"} · summary only; detail on the battery page`;
  return (
    <StatusBar
      data={{ "data-health-strip": entry.configuration }}
      action={count === 0 ? undefined : <Link to={batteryHref}>Battery page →</Link>}
    >
      <ProductStatus inline words={siteConditionWords(entry)} scope={scope} asOf={entry.read_at} />
    </StatusBar>
  );
}

/** v69 `health:1`: the configured battery's condition (Unknown) and the asset rows no read supplies. */
function ConditionBody({ siteId, read }: { siteId: string; read: HealthRead<BatteryEntry> }) {
  const links = useHealthLinks();
  if (read.status === "refused") {
    return (
      <HealthGap refusal={read} subject="Battery condition" name="site-health-battery-refused-code" texts={BATTERY_TEXTS} />
    );
  }
  const entry = read.value;
  return (
    <>
      <p className="health-condition-lead" data-health-condition-lead>
        <strong>Condition cannot yet be judged.</strong>{" "}
        {entry.configuration === "NOT_CONFIGURED"
          ? "No battery is part of this site's configuration, so there is no battery condition to judge."
          : "The inputs needed to judge battery condition are missing. Gateway contact never decides it."}
      </p>
      {entry.configuration === "NOT_CONFIGURED" ? (
        <p data-health-battery="NOT_CONFIGURED">
          <Link to={links.assets(siteId)}>Battery page</Link>
        </p>
      ) : (
        <DataTable labelledBy="site-health-condition-heading">
          <thead>
            <tr>
              <th scope="col">Asset</th>
              <th scope="col">Assessment</th>
              <th scope="col">Evidence</th>
              <th scope="col">Main reason</th>
              <th scope="col">Open findings</th>
              <th scope="col">Open work</th>
              {/* A visible header: a visually hidden one is absolutely positioned and escapes the table's scroller. */}
              <th scope="col">Open</th>
            </tr>
          </thead>
          <tbody>
            {entry.batteries.map((b) => (
              <tr key={b.asset_id} data-health-battery={b.asset_id}>
                <th scope="row">
                  Battery · <span data-vocabulary-exempt="user-owned">{b.display_name ?? b.asset_code}</span>
                </th>
                <td>
                  <Badge tone="neutral">Unknown</Badge>
                </td>
                <td>Inputs missing</td>
                <td>See battery page</td>
                <td>Not recorded</td>
                <td>Not recorded</td>
                <td>
                  <Link to={links.asset(siteId, b.asset_id)}>Open battery →</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      )}
      <ChartNote>
        <MissingClaim gapId="G-health-asset-inventory" placement="health.condition.other-assets">
          Other assets, such as the generator and inverters: condition not available yet
        </MissingClaim>
        . No read lists them with a condition, so none is shown.
      </ChartNote>
    </>
  );
}

/** Short status word with its age: "Current · 3 s ago", "Stale · 16 min", "Never received", "Disabled". */
function statusShort(row: GatewayHealthRow): string {
  if (row.registration === "DISABLED") return "Disabled";
  const c = row.contact;
  if (c.reason === "NEVER_RECEIVED") return "Never received";
  const age =
    c.since_last_receipt_seconds === null
      ? ""
      : ` · ${formatAge(c.since_last_receipt_seconds)}${c.status === "CURRENT" ? " ago" : ""}`;
  return `${CONTACT_WORDS[c.status] ?? c.status}${age}`;
}

/** The quality chip: Current, Old, Unknown age or Nothing received. An untrusted clock is never "Old". */
function qualityWord(row: GatewayHealthRow): string {
  const f = row.reported_facts;
  if (f.reason === "NEVER_RECEIVED") return "Nothing received";
  if (f.fact_age_seconds === null || f.reason === "OBSERVED_AFTER_RECEIPT") return "Unknown age";
  if (f.status === "OLD") return "Old";
  if (f.status === "CURRENT") return "Current";
  return "Unknown age";
}

function needsAttention(row: GatewayHealthRow): boolean {
  return row.registration === "ENABLED" && (row.contact.status !== "CURRENT" || qualityWord(row) !== "Current");
}

/** Queue as last reported (not the hardware now). */
function queueText(row: GatewayHealthRow): string {
  const q = row.reported_facts.queue;
  if (q === null) return "not reported";
  return `${q.count} waiting${q.oldest_age_seconds === null ? ", none waiting" : `, oldest ${formatAge(q.oldest_age_seconds)}`}`;
}

function deviceContactText(source: GatewayHealthRow["sources"][number]): string {
  return source.reported_contact_status === "REPORTED"
    ? `Last heard ${formatInstant(source.reported_contact)}`
    : source.reported_contact_status === "REPORTED_NEVER_HEARD"
      ? "The gateway reports never hearing from it"
      : "Not in the gateway's latest report";
}

/** v69 `health:2`: one row per gateway; queue, storage and device contact sit in Technical details. */
function SourcesBody({
  siteId,
  doc,
  selectedGateway,
}: {
  siteId: string;
  doc: SourceHealthDocument;
  selectedGateway: string | null;
}) {
  const links = useHealthLinks();
  const s = doc.summary;
  const words = contactSummaryWords(doc);
  const enabled = doc.gateways.filter((g) => g.registration === "ENABLED");
  const reported = enabled.filter((g) => g.diagnostic !== null);
  const noEnabled = s.status === "NO_REGISTERED_SOURCE";
  const selected = selectedGateway === null ? null : doc.gateways.find((g) => g.gateway_id === selectedGateway) ?? null;
  const ordered = [
    ...doc.gateways.filter((g) => needsAttention(g)),
    ...doc.gateways.filter((g) => g.registration === "ENABLED" && !needsAttention(g)),
    ...doc.gateways.filter((g) => g.registration === "DISABLED"),
  ];
  return (
    <>
      <p
        className="health-contact-summary"
        data-health-summary={s.status}
        data-health-summary-reason={s.reason ?? ""}
        data-health-contact-tone={words.tone}
      >
        <strong data-health-contact-label>{words.label}.</strong>
        {enabled.length === 0 ? ` ${words.sentence}${words.next ? ` ${words.next}` : ""}` : null}{" "}
        <span data-health-counts>
          {noEnabled
            ? ""
            : `${s.enabled_gateway_count} enabled ${s.enabled_gateway_count === 1 ? "gateway" : "gateways"}: ${
                s.contact_counts.CURRENT
              } current, ${s.contact_counts.STALE} stale, ${s.contact_counts.UNKNOWN} unknown`}
          {s.disabled_gateway_count > 0 ? `${noEnabled ? "" : " · "}${s.disabled_gateway_count} disabled, not counted` : ""}
          {noEnabled && s.disabled_gateway_count === 0 ? "" : " · "}
          {`read ${formatInstant(doc.read_at)}`}
        </span>
      </p>
      {selectedGateway !== null ? (
        selected === null ? (
          <p className="health-selected" data-health-selected="not-found">
            This site has no gateway with that ID. <Link to={links.health(siteId)}>Show all gateways</Link>
          </p>
        ) : (
          <SelectedGateway siteId={siteId} row={selected} />
        )
      ) : null}
      {doc.gateways.length === 0 ? (
        <p data-health-sources="none">No gateway is registered for this site.</p>
      ) : (
        <DataTable labelledBy="site-health-sources-heading">
          <thead>
            <tr>
              <th scope="col">Source</th>
              <th scope="col">Status at {clockTime(doc.read_at)}</th>
              <th scope="col">Quality</th>
              <th scope="col">Affects</th>
              <th scope="col">Open</th>
            </tr>
          </thead>
          <tbody>
            {ordered.map((g) => (
              <tr
                key={g.gateway_id}
                data-health-gateway={g.gateway_external_id}
                data-health-contact={g.contact.status}
                data-health-registration={g.registration}
                aria-current={g.gateway_id === selectedGateway ? "true" : undefined}
              >
                <th scope="row">
                  Gateway <HealthRef value={g.gateway_external_id} />
                  {g.registration === "DISABLED" ? (
                    <>
                      {" "}
                      <Badge tone="neutral">Disabled</Badge>
                    </>
                  ) : (
                    <small className="health-cell-note">
                      {g.sources.length} {g.sources.length === 1 ? "device" : "devices"}
                    </small>
                  )}
                </th>
                <td data-health-status>{statusShort(g)}</td>
                <td data-health-quality>
                  <Badge tone="neutral">{qualityWord(g)}</Badge>
                </td>
                <td className="health-nowrap">Not recorded</td>
                <td>
                  <Link to={links.health(siteId, g.gateway_id)} data-health-open={g.gateway_external_id}>
                    Details
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      )}
      {reported.length === 0 ? (
        <ChartNote data={{ "data-health-queue": "none" }}>
          No enabled gateway has reported yet, so nothing is known about queues or storage.
        </ChartNote>
      ) : null}
      <HealthTechnical doc={doc} selectedGateway={selected?.gateway_id ?? null} />
    </>
  );
}

/** What each enabled gateway last reported, with its queue, storage and device contact (Technical details). */
function HealthReportedDetail({ doc, selectedGateway }: { doc: SourceHealthDocument; selectedGateway: string | null }) {
  const enabled = doc.gateways.filter((g) => g.registration === "ENABLED");
  if (enabled.length === 0) return null;
  return (
    <DataTable>
      <thead>
        <tr>
          <th scope="col">Gateway or device</th>
          <th scope="col">What it last reported</th>
          <th scope="col">Queue and storage, as last reported</th>
        </tr>
      </thead>
      <tbody>
        {enabled.flatMap((g) => {
          const f = g.reported_facts;
          return [
            <tr
              key={g.gateway_id}
              data-health-reported={g.gateway_external_id}
              {...(g.diagnostic !== null ? { "data-health-queue-row": g.gateway_external_id } : {})}
              aria-current={g.gateway_id === selectedGateway ? "true" : undefined}
            >
              <th scope="row">
                Gateway <HealthRef value={g.gateway_external_id} />
              </th>
              <td data-health-facts={f.status}>{reportedText(g)}</td>
              <td>
                {g.diagnostic === null ? (
                  "Nothing received yet"
                ) : (
                  <>
                    Queue, as last reported: {queueText(g)}
                    {" · Storage: "}
                    <span data-health-disk={f.disk_pressure?.value ?? ""}>
                      {f.disk_pressure ? DISK_WORDS[f.disk_pressure.value] ?? "not recognised" : "not reported"}
                    </span>
                  </>
                )}
              </td>
            </tr>,
            ...g.sources.map((source) => (
              <tr key={source.source_id} data-health-source={source.source_external_id}>
                <th scope="row">
                  Device <HealthRef value={source.source_external_id} />
                  <small className="health-cell-note">as its gateway reports</small>
                </th>
                <td>{deviceContactText(source)}</td>
                <td>
                  {source.reported_contact_age_seconds !== null
                    ? `${formatAge(source.reported_contact_age_seconds)} ago`
                    : source.reported_contact_status === "REPORTED"
                      ? `Unknown age: ${unknownAgeReason(g)}`
                      : "Unknown"}
                </td>
              </tr>
            )),
          ];
        })}
      </tbody>
    </DataTable>
  );
}

/** The gateway chosen by `?gateway=`: its contact and latest report, inside the data-sources panel. */
function SelectedGateway({ siteId, row }: { siteId: string; row: GatewayHealthRow }) {
  const links = useHealthLinks();
  const f = row.reported_facts;
  const d = row.diagnostic;
  const words = gatewayContactWords(row);
  return (
    <div
      className="health-selected"
      data-health-selected="found"
      data-health-selected-diagnostic={d?.diagnostic_id ?? ""}
      data-health-selected-tone={words.tone}
    >
      <p>
        <strong>
          Gateway <HealthRef value={row.gateway_external_id} />
        </strong>
        {" · "}
        <strong data-health-selected-state>{words.label}</strong>
        {". "}
        <span data-health-selected-sentence>{words.sentence}</span>
        {words.next ? ` ${words.next}` : ""}
      </p>
      <KeyValues
        label={`Gateway ${row.gateway_external_id}`}
        rows={[
          ["Registration", row.registration === "DISABLED" ? "Disabled (not counted)" : "Enabled", "registration"],
          ["Contact", contactText(row), "contact"],
          ["Last received (server clock)", formatInstant(row.contact.last_received_at), "received"],
          ["Reports every", formatAge(row.declared_cadence_seconds), "cadence"],
          ["Stale after", `${formatAge(row.contact.threshold_seconds)} without a report`, "threshold"],
          ["Observed (gateway clock)", formatInstant(f.observed_at), "observed"],
          ["What it last reported", reportedText(row), "reported"],
          ["Queue, as last reported", row.diagnostic === null ? "not reported" : queueText(row), "queue"],
          [
            "Gateway clock",
            f.clock.offset_ms === null
              ? "Offset not reported"
              : `Off by ${(f.clock.offset_ms / 1000).toFixed(1)} s; ${
                  f.clock.trust === "UNTRUSTED" ? "not trusted" : "within the allowed range"
                }`,
            "clock",
          ],
        ]}
      />
      <p>
        <Link to={links.health(siteId)}>Show all gateways</Link>
      </p>
    </div>
  );
}

function HealthTechnical({ doc, selectedGateway }: { doc: SourceHealthDocument; selectedGateway: string | null }) {
  const w = doc.summary.source_watermark;
  return (
    <Disclosure name="site-health-technical" summary="Technical details">
      <FactList>
        <Fact term="Read at (server clock)">
          <HealthRef value={doc.read_at} />
        </Fact>
        <Fact term="Rule">
          <HealthRef value={doc.rule_id} />
        </Fact>
        <Fact term="Read version">
          <HealthRef value={`${doc.schema.id} v${doc.schema.version}`} />
        </Fact>
        <Fact term="Summary">
          <HealthRef value={doc.summary.status} /> <HealthRef value={doc.summary.reason ?? null} />
        </Fact>
        <Fact term="Snapshot">
          <HealthRef value={`${doc.snapshot.isolation} ${doc.snapshot.selection}`} />
        </Fact>
        <Fact term="Latest reports selected">{w.selected_diagnostic_count}</Fact>
        <Fact term="Latest receipt among them">
          <HealthRef value={w.latest_received_at} />
        </Fact>
        <Fact term="Selected report IDs reference">
          <span data-health-watermark={w.selected_diagnostic_ids_sha256}>
            <HealthRef value={w.selected_diagnostic_ids_sha256} />
          </span>
        </Fact>
        <Fact term="Not stated by this page">
          {doc.not_claimed.map((item) => (
            <span key={item}>
              <HealthRef value={item} />{" "}
            </span>
          ))}
        </Fact>
      </FactList>
      <HealthReportedDetail doc={doc} selectedGateway={selectedGateway} />
      <DataTable>
        <thead>
          <tr>
            <th scope="col">Gateway</th>
            <th scope="col">Gateway ID</th>
            <th scope="col">Latest report ID</th>
            <th scope="col">Sequence</th>
            <th scope="col">Received</th>
            <th scope="col">Observed</th>
            <th scope="col">Clock offset (ms)</th>
            <th scope="col">Reasons</th>
          </tr>
        </thead>
        <tbody>
          {doc.gateways.map((g) => (
            <tr
              key={g.gateway_id}
              data-health-technical={g.gateway_external_id}
              aria-current={g.gateway_id === selectedGateway ? "true" : undefined}
            >
              <th scope="row">
                <HealthRef value={g.gateway_external_id} />
              </th>
              <td>
                <HealthRef value={g.gateway_id} />
              </td>
              <td>
                <HealthRef value={g.diagnostic?.diagnostic_id ?? null} />
              </td>
              <td>
                <HealthRef value={g.diagnostic ? `${g.diagnostic.sequence_epoch}#${g.diagnostic.diagnostic_sequence}` : null} />
              </td>
              <td>
                <HealthRef value={g.diagnostic?.received_at ?? null} />
              </td>
              <td>
                <HealthRef value={g.diagnostic?.observed_at ?? null} />
              </td>
              <td>
                <HealthRef value={g.reported_facts.clock.offset_ms} />
              </td>
              <td>
                <HealthRef value={g.contact.reason} /> <HealthRef value={g.reported_facts.reason} />{" "}
                <HealthRef value={g.reported_facts.clock.reason} />
              </td>
            </tr>
          ))}
        </tbody>
      </DataTable>
    </Disclosure>
  );
}
