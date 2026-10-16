/**
 * S7-01b Site Health (`health:2#a`) over S7-01a's source-health and battery
 * entry reads. Layout follows v69 `#/health`; content is limited to what the
 * reads support (`D-2026-10-16-a-s7-health`, `D-2026-10-16-s701-clock`):
 *
 * - The summary is "Gateway contact" with an enabled-gateway count, never Site
 *   or equipment health. Disabled gateways are listed with "Disabled" and are
 *   not counted.
 * - Contact (server receipt), what each gateway last reported (queue, storage,
 *   its clock), device contact reported by gateways and battery condition are
 *   separate sections, each saying what it is not.
 * - An age is shown only when the read states one; otherwise "Unknown age"
 *   with the clock reason. Never a signed age.
 * - Exact IDs, rule and watermark sit in "Technical details", closed by default.
 */
import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { siteAssetHref, siteAssetsHref, siteHealthHref } from "../shell/operatorSiteRoutes";
import { Badge, DataTable, Disclosure, Fact, FactList, Panel } from "../ui";
import type {
  BatteryEntry,
  GatewayHealthRow,
  HealthClient,
  HealthRead,
  HealthRefusal,
  SourceHealthDocument,
} from "./healthClient";

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
  if (age === null) return `Unknown age: ${unknownAgeReason(row)}`;
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

const SUMMARY_WORDS: Record<string, string> = {
  ALL_CURRENT: "all current",
  NOT_ALL_CURRENT: "not all current",
  NO_REGISTERED_SOURCE: "no enabled gateway",
};

/** A typed refusal of one read: HTTP status and server code kept; never an empty result. */
export function HealthRefusalPanel({
  refusal,
  subject,
  headingId,
  texts = {},
  children,
}: {
  refusal: HealthRefusal;
  subject: string;
  headingId: string;
  texts?: Record<string, string>;
  children?: ReactNode;
}) {
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
  return (
    <Panel heading={heading} headingId={headingId}>
      <p data-health-read="refused" data-health-http={refusal.http ?? "none"} data-health-code={refusal.code ?? ""}>
        {text}
      </p>
      {children}
      {refusal.code ? (
        <Disclosure name={`${headingId}-code`} summary="Technical details">
          <p>
            Code: <HealthRef value={refusal.code} />
          </p>
        </Disclosure>
      ) : null}
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

export function SiteHealth({
  siteId,
  client,
  selectedGateway,
}: {
  siteId: string;
  client: HealthClient;
  selectedGateway: string | null;
}) {
  const health = useRead(() => client.getSourceHealth(siteId), `health:${siteId}`);
  const battery = useRead(() => client.getBatteryEntry(siteId), `battery:${siteId}`);
  if (health === null) {
    return <p>Loading the site's gateway contact.</p>;
  }
  return (
    <div className="site-health" data-health-site={siteId}>
      {health.status === "refused" ? (
        <HealthRefusalPanel
          refusal={health}
          subject="Gateway contact"
          headingId="site-health-refused-heading"
          texts={HEALTH_TEXTS}
        />
      ) : (
        <HealthBody
          siteId={siteId}
          doc={health.value}
          selectedGateway={selectedGateway}
          battery={<BatterySection siteId={siteId} read={battery} />}
        />
      )}
      {health.status === "refused" ? <BatterySection siteId={siteId} read={battery} /> : null}
      <div className="notice notice--info" role="note">
        A gateway being heard from does not make equipment healthy. Gateway contact, what gateways report about
        themselves, and battery condition are separate, and none of them is a statement about equipment condition.
      </div>
      {health.status === "loaded" ? <HealthTechnical doc={health.value} /> : null}
    </div>
  );
}

function HealthBody({
  siteId,
  doc,
  selectedGateway,
  battery,
}: {
  siteId: string;
  doc: SourceHealthDocument;
  selectedGateway: string | null;
  /** v69 order: the asset condition summary sits right under the status strip. */
  battery: ReactNode;
}) {
  const s = doc.summary;
  const enabled = doc.gateways.filter((g) => g.registration === "ENABLED");
  const reported = enabled.filter((g) => g.diagnostic !== null);
  const noEnabled = s.status === "NO_REGISTERED_SOURCE";
  const selected = selectedGateway === null ? null : doc.gateways.find((g) => g.gateway_id === selectedGateway) ?? null;
  return (
    <>
      <div className="evidence-statusbar" data-health-summary={s.status} data-health-summary-reason={s.reason ?? ""}>
        <Badge tone="neutral">{`Gateway contact: ${SUMMARY_WORDS[s.status] ?? s.status}`}</Badge>
        <span className="evidence-statusbar__facts" data-health-counts>
          {noEnabled
            ? s.reason === "NO_REGISTERED_GATEWAY"
              ? "No gateway is registered for this site, so nothing is known about contact."
              : "No gateway is enabled for this site, so nothing is known about contact."
            : `${s.enabled_gateway_count} enabled ${s.enabled_gateway_count === 1 ? "gateway" : "gateways"}: ${
                s.contact_counts.CURRENT
              } current, ${s.contact_counts.STALE} stale, ${s.contact_counts.UNKNOWN} unknown`}
          {s.disabled_gateway_count > 0 ? ` · ${s.disabled_gateway_count} disabled, not counted` : ""}
          {` · read ${formatInstant(doc.read_at)}`}
        </span>
      </div>
      {selectedGateway !== null ? (
        selected === null ? (
          <Panel heading="No such gateway" headingId="site-health-selected-heading">
            <p data-health-selected="not-found">
              This site has no gateway with that ID. <Link to={siteHealthHref(siteId)}>Show all gateways</Link>
            </p>
          </Panel>
        ) : (
          <SelectedGateway siteId={siteId} row={selected} />
        )
      ) : null}
      {battery}
      <Panel
        heading="Gateway contact"
        headingId="site-health-contact-heading"
        description="When the server last received each gateway's report, against the reporting interval the gateway declared. Contact means the gateway reached the server; it says nothing about the equipment."
        flush
      >
        {doc.gateways.length === 0 ? (
          <p className="panel__note">No gateway is registered for this site.</p>
        ) : (
          <DataTable labelledBy="site-health-contact-heading">
            <thead>
              <tr>
                <th scope="col">Gateway</th>
                <th scope="col">Contact</th>
                <th scope="col">Last received (server clock)</th>
                <th scope="col">Reporting interval</th>
                <th scope="col">What it last reported</th>
                <th scope="col">Open</th>
              </tr>
            </thead>
            <tbody>
              {doc.gateways.map((g) => (
                <tr
                  key={g.gateway_id}
                  data-health-gateway={g.gateway_external_id}
                  data-health-contact={g.contact.status}
                  data-health-registration={g.registration}
                  aria-current={g.gateway_id === selectedGateway ? "true" : undefined}
                >
                  <th scope="row">
                    <HealthRef value={g.gateway_external_id} />
                    {g.registration === "DISABLED" ? (
                      <>
                        {" "}
                        <Badge tone="neutral">Disabled</Badge>
                      </>
                    ) : null}
                  </th>
                  <td>
                    {g.registration === "DISABLED" ? "Disabled, not counted. " : ""}
                    {contactText(g)}
                  </td>
                  <td>{formatInstant(g.contact.last_received_at)}</td>
                  <td>every {formatAge(g.declared_cadence_seconds)}</td>
                  <td data-health-facts={g.reported_facts.status}>{reportedText(g)}</td>
                  <td>
                    <Link to={siteHealthHref(siteId, g.gateway_id)} data-health-open={g.gateway_external_id}>
                      Details
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        )}
      </Panel>
      <Panel
        heading="Queue and storage, as last reported"
        headingId="site-health-queue-heading"
        description="What each enabled gateway said about its own queue and storage in its latest report. This is the last reported state, not the hardware's state now."
        flush
      >
        {reported.length === 0 ? (
          <p className="panel__note" data-health-queue="none">
            No enabled gateway has reported yet, so nothing is known about queues or storage.
          </p>
        ) : (
          <DataTable labelledBy="site-health-queue-heading">
            <thead>
              <tr>
                <th scope="col">Gateway</th>
                <th scope="col">Readings waiting</th>
                <th scope="col">Oldest waiting</th>
                <th scope="col">Storage</th>
                <th scope="col">Reported age</th>
              </tr>
            </thead>
            <tbody>
              {reported.map((g) => {
                const f = g.reported_facts;
                return (
                  <tr key={g.gateway_id} data-health-queue-row={g.gateway_external_id}>
                    <th scope="row">
                      <HealthRef value={g.gateway_external_id} />
                    </th>
                    <td>{f.queue ? f.queue.count : "not reported"}</td>
                    <td>
                      {f.queue === null
                        ? "not reported"
                        : f.queue.oldest_age_seconds === null
                          ? "none waiting"
                          : formatAge(f.queue.oldest_age_seconds)}
                    </td>
                    <td data-health-disk={f.disk_pressure?.value ?? ""}>
                      {f.disk_pressure ? DISK_WORDS[f.disk_pressure.value] ?? f.disk_pressure.value : "not reported"}
                    </td>
                    <td>
                      {f.fact_age_seconds === null
                        ? `Unknown age: ${unknownAgeReason(g)}`
                        : `${formatAge(f.fact_age_seconds)} ago`}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </DataTable>
        )}
      </Panel>
      <Panel
        heading="Device contact reported by gateways"
        headingId="site-health-devices-heading"
        description="When each enabled gateway says it last heard from a device. A gateway reaching the server does not show that its devices are connected."
        flush
      >
        {enabled.length === 0 ? (
          <p className="panel__note">No gateway is enabled, so no device contact is reported.</p>
        ) : (
          <DataTable labelledBy="site-health-devices-heading">
            <thead>
              <tr>
                <th scope="col">Gateway</th>
                <th scope="col">Device source</th>
                <th scope="col">Last heard, as reported</th>
                <th scope="col">Age</th>
              </tr>
            </thead>
            <tbody>
              {enabled.flatMap((g) =>
                g.sources.map((source) => (
                  <tr key={source.source_id} data-health-source={source.source_external_id}>
                    <td>
                      <HealthRef value={g.gateway_external_id} />
                    </td>
                    <th scope="row">
                      <HealthRef value={source.source_external_id} />
                    </th>
                    <td>
                      {source.reported_contact_status === "REPORTED"
                        ? formatInstant(source.reported_contact)
                        : source.reported_contact_status === "REPORTED_NEVER_HEARD"
                          ? "The gateway reports never hearing from it"
                          : "Not in the gateway's latest report"}
                    </td>
                    <td>
                      {source.reported_contact_age_seconds !== null
                        ? `${formatAge(source.reported_contact_age_seconds)} ago`
                        : source.reported_contact_status === "REPORTED"
                          ? `Unknown age: ${unknownAgeReason(g)}`
                          : "Unknown"}
                    </td>
                  </tr>
                )),
              )}
            </tbody>
          </DataTable>
        )}
      </Panel>
    </>
  );
}

function SelectedGateway({ siteId, row }: { siteId: string; row: GatewayHealthRow }) {
  const f = row.reported_facts;
  const d = row.diagnostic;
  return (
    <Panel
      heading={`Gateway ${row.gateway_external_id}`}
      headingId="site-health-selected-heading"
      description="This gateway's contact and its latest report, with the exact records they come from."
    >
      <FactList>
        <Fact term="Registration">{row.registration === "DISABLED" ? "Disabled (not counted)" : "Enabled"}</Fact>
        <Fact term="Contact">{contactText(row)}</Fact>
        <Fact term="Last received (server clock)">{formatInstant(row.contact.last_received_at)}</Fact>
        <Fact term="Stale after">{formatAge(row.contact.threshold_seconds)} without a report</Fact>
        <Fact term="Observed (gateway clock)">{formatInstant(f.observed_at)}</Fact>
        <Fact term="What it last reported">{reportedText(row)}</Fact>
        <Fact term="Gateway clock">
          {f.clock.offset_ms === null
            ? "Offset not reported"
            : `Off by ${(f.clock.offset_ms / 1000).toFixed(1)} s; ${
                f.clock.trust === "UNTRUSTED" ? "not trusted" : "within the allowed range"
              }`}
        </Fact>
        <Fact term="Gateway ID">
          <HealthRef value={row.gateway_id} />
        </Fact>
        <Fact term="Latest report ID">
          <span data-health-selected-diagnostic={d?.diagnostic_id ?? ""}>
            <HealthRef value={d?.diagnostic_id ?? null} />
          </span>
        </Fact>
        <Fact term="Report sequence">
          {d ? (
            <>
              <HealthRef value={d.sequence_epoch} /> #{d.diagnostic_sequence}
            </>
          ) : (
            "none"
          )}
        </Fact>
      </FactList>
      <p>
        <Link to={siteHealthHref(siteId)}>Show all gateways</Link>
      </p>
    </Panel>
  );
}

const BATTERY_TEXTS: Record<string, string> = {
  ASSET_BOUNDARY_UNAVAILABLE: "The site's configuration could not be read, so nothing is stated about its battery.",
  FOUNDATION_BASIS_UNAVAILABLE:
    "The site's configuration could not be read consistently, so nothing is stated about its battery.",
};

export { BATTERY_TEXTS };

function BatterySection({ siteId, read }: { siteId: string; read: HealthRead<BatteryEntry> | null }) {
  if (read === null) {
    return <p>Loading the site's battery.</p>;
  }
  if (read.status === "refused") {
    return (
      <HealthRefusalPanel
        refusal={read}
        subject="Battery condition"
        headingId="site-health-battery-refused-heading"
        texts={BATTERY_TEXTS}
      />
    );
  }
  const entry = read.value;
  return (
    <Panel
      heading="Battery condition"
      headingId="site-health-battery-heading"
      description="Physical condition of the configured battery. Gateway contact never decides it."
      flush
    >
      {entry.configuration === "NOT_CONFIGURED" ? (
        <p className="panel__note" data-health-battery="NOT_CONFIGURED">
          No battery is part of this site's configuration. Battery condition: Unknown (not configured).{" "}
          <Link to={siteAssetsHref(siteId)}>Battery page</Link>
        </p>
      ) : (
        <DataTable labelledBy="site-health-battery-heading">
          <thead>
            <tr>
              <th scope="col">Asset</th>
              <th scope="col">Condition</th>
              <th scope="col">Why</th>
              <th scope="col">Open</th>
            </tr>
          </thead>
          <tbody>
            {entry.batteries.map((b) => (
              <tr key={b.asset_id} data-health-battery={b.asset_id}>
                <th scope="row">
                  <span data-vocabulary-exempt="user-owned">{b.display_name ?? b.asset_code}</span>
                </th>
                <td>Unknown</td>
                <td>The inputs needed to judge battery condition are missing</td>
                <td>
                  <Link to={siteAssetHref(siteId, b.asset_id)}>Open battery</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      )}
    </Panel>
  );
}

function HealthTechnical({ doc }: { doc: SourceHealthDocument }) {
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
        <Fact term="Selected report IDs digest">
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
            <tr key={g.gateway_id} data-health-technical={g.gateway_external_id}>
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
