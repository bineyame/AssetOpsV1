/**
 * Pieces of the persisted Foundation revision (S1-01), composed by the S1-03
 * views in `StoredFoundationViews`: the period status strip every view opens
 * with, the time-valid controls with the one S1 change (battery reserve), the
 * audit record details, and the registered gateway and sources.
 *
 * Substrate leaf. It states only configuration. Nothing here is an
 * observation: the gateway and its sources are registrations, and contact,
 * credentials and evidence are not assessed here (Site Evidence reports them).
 */

import { useState, type FormEvent, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { Badge, DataTable, Disclosure, Fact, FactList, Panel } from "../ui";
import type {
  FoundationControl,
  FoundationReadModel,
  FoundationRevisionSummary,
  FoundationVersionsReadModel,
  PublishOutcome,
} from "./siteFoundationClient";

export const FOUNDATION_REVISION_HEADING_ID = "foundation-revision-heading";

export function formatInstant(value: string | null): string {
  if (value === null) return "no end";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getUTCFullYear()}-${pad(date.getUTCMonth() + 1)}-${pad(date.getUTCDate())} ${pad(
    date.getUTCHours(),
  )}:${pad(date.getUTCMinutes())} UTC`;
}

function period(revision: FoundationRevisionSummary): string {
  return `${formatInstant(revision.valid_from)} to ${formatInstant(revision.valid_to)}`;
}

const PERIOD_WORD: Record<FoundationRevisionSummary["period_state"], string> = {
  PAST: "past",
  CURRENT: "current",
  FUTURE: "scheduled",
};

export function controlValue(control: FoundationControl, names?: ReadonlyMap<string, string>): string {
  if (control.state === "NOT_CONFIGURED") {
    return control.message ?? "Not configured in this Foundation";
  }
  if (control.members !== undefined) return control.members.map((code) => names?.get(code) ?? code).join(" → ");
  return `${control.value ?? ""} ${control.unit ?? ""}`.trim();
}

/**
 * A `datetime-local` value read as UTC. Browsers emit `HH:mm` or `HH:mm:ss`
 * (and some a fraction); whole seconds are what the API accepts.
 */
export function utcInstantFromLocal(value: string): string | null {
  const match = /^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})(?::(\d{2})(?:\.\d+)?)?$/.exec(value);
  return match === null ? null : `${match[1]}:${match[2] ?? "00"}Z`;
}

/** The periods a reader can select: Foundation versions and binding periods. */
function selectablePeriods(versions: FoundationVersionsReadModel | null) {
  const current = versions?.revisions.filter((row) => row.recorded_state === "CURRENT") ?? [];
  const superseded = versions?.revisions.filter((row) => row.recorded_state === "SUPERSEDED") ?? [];
  // Binding periods are selectable too, so a binding change inside one
  // Foundation period can be inspected before and after (S1-02).
  const foundationStarts = new Set(current.map((row) => row.valid_from));
  const bindingPeriods =
    versions?.binding_sets.filter(
      (row) => row.recorded_state === "CURRENT" && !foundationStarts.has(row.valid_from),
    ) ?? [];
  const selectable = new Set([...foundationStarts, ...bindingPeriods.map((row) => row.valid_from)]);
  return { current, superseded, bindingPeriods, selectable };
}

export interface FoundationPeriodStripProps {
  foundation: FoundationReadModel;
  versions: FoundationVersionsReadModel | null;
  /** The `at` instant carried in the URL, or null for "now". */
  selectedAt: string | null;
  onSelectAt: (at: string | null) => void;
  /** A link placed at the end of the strip (the next useful view). */
  action?: ReactNode;
}

/**
 * The concise status strip every Foundation view opens with (S1-03): which
 * stored version and binding set is shown, for which effective period, whether
 * that is the configuration in effect now, and the period selector. One
 * selection drives all three views, because it lives in the URL.
 */
export function FoundationPeriodStrip({
  foundation,
  versions,
  selectedAt,
  onSelectAt,
  action,
}: FoundationPeriodStripProps) {
  const { revision, bindings } = foundation;
  const { current, bindingPeriods, selectable } = selectablePeriods(versions);
  const gaps = foundation.configuration_gaps.length;
  const bindingPeriod = bindings.binding_set?.period_state ?? null;

  return (
    <section
      className="status-strip"
      aria-labelledby={FOUNDATION_REVISION_HEADING_ID}
      data-foundation-period={revision.period_state}
    >
      <h2 className="visually-hidden" id={FOUNDATION_REVISION_HEADING_ID}>
        Foundation version
      </h2>
      <div className="status-strip__row">
        <p className="status-strip__summary">
          <Badge tone="neutral">{`Foundation v${revision.version}`}</Badge>{" "}
          <span>Effective {period(revision)} · immutable stored version</span>
        </p>
        <p className="status-strip__summary">
          {bindings.binding_set === null ? (
            <span data-strip-bindings="NONE">No signal binding set in effect</span>
          ) : (
            <>
              <Badge tone="neutral">{`Binding v${bindings.binding_set.version}`}</Badge>{" "}
              <span data-strip-bindings="PUBLISHED">
                {`${bindings.mappings.length} bound ${bindings.mappings.length === 1 ? "channel" : "channels"}`}
              </span>
            </>
          )}
          {" · "}
          <span data-strip-gaps={gaps}>
            {gaps === 0 ? "No configuration gap" : `${gaps} configuration ${gaps === 1 ? "gap" : "gaps"}`}
          </span>
        </p>
        {action === undefined ? null : <p className="status-strip__action">{action}</p>}
      </div>
      <div className="status-strip__row">
        {revision.is_current && bindingPeriod !== null && bindingPeriod !== "CURRENT" ? (
          // The Foundation version is the current one, but the binding set
          // shown is not in effect now (a scheduled or past binding period):
          // never call that "the configuration in effect now".
          <p
            role="note"
            className="status-strip__state status-strip__state--historical"
            data-foundation-historical="true"
          >
            {bindingPeriod === "FUTURE" ? "Scheduled binding period" : "Historical binding period"}:
            you are viewing binding v{bindings.binding_set?.version}, effective{" "}
            {formatInstant(bindings.binding_set?.valid_from ?? null)} to{" "}
            {formatInstant(bindings.binding_set?.valid_to ?? null)}, with Foundation v{revision.version}.
            These bindings are not the ones in effect now.
          </p>
        ) : revision.is_current ? (
          <p className="status-strip__state">This is the configuration in effect now.</p>
        ) : (
          <p
            role="note"
            className="status-strip__state status-strip__state--historical"
            data-foundation-historical="true"
          >
            {revision.period_state === "FUTURE" ? "Scheduled period" : "Historical period"}:
            you are viewing Foundation v{revision.version}, effective {period(revision)}. This
            is not the configuration in effect now.
          </p>
        )}
        <label className="status-strip__period">
          <span>Period shown</span>
          <select
            aria-label="Foundation period"
            value={selectedAt ?? ""}
            onChange={(event) => onSelectAt(event.target.value === "" ? null : event.target.value)}
          >
            <option value="">In effect now</option>
            {current.map((row) => (
              <option key={row.revision_id} value={row.valid_from}>
                {`v${row.version} · ${period(row)} (${PERIOD_WORD[row.period_state]})`}
              </option>
            ))}
            {bindingPeriods.map((row) => (
              <option key={row.binding_set_revision_id} value={row.valid_from}>
                {`Binding v${row.version} · from ${formatInstant(row.valid_from)} (${PERIOD_WORD[row.period_state]})`}
              </option>
            ))}
          </select>
        </label>
      </div>
      {selectedAt !== null && !selectable.has(selectedAt) ? (
        <p className="status-strip__state">
          Showing the version in effect at {formatInstant(foundation.resolved.at)}.
        </p>
      ) : null}
    </section>
  );
}

/**
 * The stored version's audit identifiers, kept on the Site model behind a
 * named disclosure: record IDs, the content digest, the import path and the
 * earlier recorded versions kept for audit.
 */
export function FoundationRecordDetails({
  foundation,
  versions,
}: {
  foundation: FoundationReadModel;
  versions: FoundationVersionsReadModel | null;
}) {
  const { revision, site, provenance } = foundation;
  const { superseded } = selectablePeriods(versions);
  return (
    <Disclosure name="foundation-record" summary="Version record, digest and import details">
      <FactList>
        <Fact term="Site code">{site.site_code}</Fact>
        <Fact term="Site record ID">
          <code>{site.site_uuid}</code>
        </Fact>
        <Fact term="Version record ID">
          <code>{revision.revision_id}</code>
        </Fact>
        <Fact term="Content digest (SHA-256)">
          <code>{revision.content_sha256}</code>
        </Fact>
        <Fact term="Recorded">{formatInstant(revision.recorded_at)}</Fact>
        <Fact term="Imported from">
          {provenance.source_path === null ? (
            "No import recorded"
          ) : (
            <>
              <code>{provenance.source_path}</code> (SHA-256{" "}
              <code>{provenance.source_sha256}</code>) as v{provenance.imported_version}
            </>
          )}
        </Fact>
      </FactList>
      {superseded.length > 0 ? (
        <p>
          {superseded.length} earlier recorded{" "}
          {superseded.length === 1 ? "version is" : "versions are"} kept for audit and no longer
          in force: {superseded.map((row) => `v${row.version}`).join(", ")}.
        </p>
      ) : (
        <p>No earlier recorded version has been superseded.</p>
      )}
    </Disclosure>
  );
}

export interface FoundationControlsPanelProps {
  foundation: FoundationReadModel;
  versions: FoundationVersionsReadModel | null;
  onPublish: (assetCode: string, value: number, validFrom: string) => Promise<PublishOutcome>;
}

/** The time-valid controls of the version shown, with the one reserve change. */
export function FoundationControlsPanel({ foundation, versions, onPublish }: FoundationControlsPanelProps) {
  const { revision, controls } = foundation;
  const { current } = selectablePeriods(versions);
  const reserve = controls.battery_reserve;
  // Priorities list asset codes; the table names them as the rest of the view does.
  const assetNames = new Map(foundation.assets.map((asset) => [asset.asset_code, asset.display_name ?? asset.asset_code]));
  // The battery the reserve belongs to, from the registered assets; never a
  // guessed code (review m8).
  const batteryCode =
    reserve.asset_code ?? foundation.assets.find((asset) => asset.asset_type === "BATTERY")?.asset_code ?? null;

  return (
    <Panel heading="Time-valid control configuration" headingId="foundation-controls-config-heading">
      <DataTable labelledBy="foundation-controls-config-heading">
        <caption>
          Configured values in this Foundation version. Configuration, not measurements.
        </caption>
        <thead>
          <tr>
            <th scope="col">Control</th>
            <th scope="col">Configured value</th>
            <th scope="col">Authority</th>
          </tr>
        </thead>
        <tbody>
          {(
            [
              ["Battery reserve", reserve],
              ["Generator start / stop", controls.generator_start_stop],
              ["Minimum generator runtime", controls.generator_minimum_runtime],
              ["Source priority (read-only)", controls.source_priority],
              ["Critical-load priority (read-only)", controls.critical_load_priority],
            ] as const
          ).map(([label, control]) => (
            <tr key={label}>
              <th scope="row">{label}</th>
              <td data-control-state={control.state}>{controlValue(control, assetNames)}</td>
              <td>{control.authority ?? "None"}</td>
            </tr>
          ))}
        </tbody>
      </DataTable>
      {batteryCode === null ? (
        <p data-reserve-change="unavailable">
          No battery is registered for this Site, so there is no reserve to change.
        </p>
      ) : (
        <ReservePublishForm
          assetCode={batteryCode}
          shown={reserve.value ?? null}
          periodIsCurrent={revision.is_current}
          periods={current}
          onPublish={onPublish}
        />
      )}
    </Panel>
  );
}

/**
 * The registered gateway and its sources: registrations only. A pending
 * gateway is never shown as connected; none of these is sending data.
 */
export function RegisteredSourcesPanel({
  foundation,
  evidenceHref,
}: {
  foundation: FoundationReadModel;
  evidenceHref?: string;
}) {
  return (
    <Panel heading="Registered gateway and sources" headingId="foundation-sources-heading">
      {foundation.gateways.map((gateway) => (
        <p key={gateway.gateway_id}>
          Gateway <code>{gateway.gateway_external_id}</code>: registered. Whether it has made
          contact or sent data is not assessed here
          {evidenceHref === undefined ? "." : <>; see <Link to={evidenceHref}>Site Evidence</Link>.</>}
        </p>
      ))}
      <Disclosure name="foundation-sources" summary={`Registered sources (${foundation.sources.length})`}>
        <DataTable labelledBy="foundation-sources-heading">
          <caption>One source per configured device. Registrations only; whether data is arriving is not assessed here.</caption>
          <thead>
            <tr>
              <th scope="col">Source</th>
              <th scope="col">Device</th>
              <th scope="col">Equipment</th>
              <th scope="col">State</th>
            </tr>
          </thead>
          <tbody>
            {foundation.sources.map((source) => (
              <tr key={source.source_id}>
                <th scope="row">
                  <code>{source.source_external_id}</code>
                </th>
                <td>{source.display_name ?? source.device_kind}</td>
                <td>{source.asset_code ?? "Unknown"}</td>
                <td>Registered</td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      </Disclosure>
    </Panel>
  );
}

/**
 * The period a reserve change would apply to (Architect, 2026-10-08): from
 * its effective instant to the end of the currently recorded period that
 * contains it, or with no end when that period is open. Later scheduled
 * periods keep their own values, so a bounded change must not read as
 * permanent.
 */
export function resultingPeriod(
  periods: FoundationRevisionSummary[],
  effectiveFrom: string,
): { from: string; to: string | null; version: number } | null {
  const at = new Date(effectiveFrom).getTime();
  if (Number.isNaN(at)) return null;
  const covering = periods.find(
    (row) =>
      new Date(row.valid_from).getTime() <= at &&
      (row.valid_to === null || at < new Date(row.valid_to).getTime()),
  );
  return covering === undefined
    ? null
    : { from: effectiveFrom, to: covering.valid_to, version: covering.version };
}

function ReservePublishForm({
  assetCode,
  shown,
  periodIsCurrent,
  periods,
  onPublish,
}: {
  assetCode: string;
  shown: number | null;
  periodIsCurrent: boolean;
  periods: FoundationRevisionSummary[];
  onPublish: (assetCode: string, value: number, validFrom: string) => Promise<PublishOutcome>;
}) {
  const [value, setValue] = useState("");
  const [effective, setEffective] = useState("");
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const number = Number(value);
    if (value.trim() === "" || Number.isNaN(number) || effective === "") {
      setMessage("Enter a reserve percentage and the instant it takes effect.");
      return;
    }
    const instant = utcInstantFromLocal(effective);
    if (instant === null) {
      setMessage("Enter the effective time as a date and time.");
      return;
    }
    setPending(true);
    const outcome = await onPublish(assetCode, number, instant);
    setPending(false);
    setMessage(
      outcome.status === "published"
        ? `Published Foundation v${outcome.revision.version}, effective ${period(outcome.revision)}.`
        : `Not published: ${outcome.message}`,
    );
  }

  const instant = effective === "" ? null : utcInstantFromLocal(effective);
  const preview = instant === null ? null : resultingPeriod(periods, instant);

  return (
    <form className="action-form" aria-label="Change battery reserve" onSubmit={submit}>
      <h3 className="action-form__heading">Change the battery reserve</h3>
      <p>
        Change the battery reserve ({assetCode}) from a chosen instant.{" "}
        {periodIsCurrent ? "In effect now, the reserve" : "In the period shown, the reserve"}
        {shown === null ? " is not configured" : ` is ${shown}%`}. Earlier periods keep their
        stored values. A change applies until the end of the period it falls in; later scheduled
        periods keep their own values.
      </p>
      <div className="action-form__fields">
        <label>
          New reserve (%){" "}
          <input
            type="number"
            min={0}
            max={100}
            step="any"
            value={value}
            onChange={(event) => setValue(event.target.value)}
          />
        </label>
        <label>
          Effective from (UTC){" "}
          <input
            type="datetime-local"
            value={effective}
            onChange={(event) => setEffective(event.target.value)}
          />
        </label>
        <button type="submit" disabled={pending}>
          Publish reserve change
        </button>
      </div>
      {effective === "" ? null : (
        <p data-resulting-period={preview === null ? "none" : preview.to === null ? "open" : "bounded"}>
          {preview === null
            ? "No stored period contains this instant, so no change can start there."
            : preview.to === null
              ? `Resulting period: from ${formatInstant(preview.from)}, with no end (the v${preview.version} period is open).`
              : `Resulting period: from ${formatInstant(preview.from)} until ${formatInstant(preview.to)}, when the v${preview.version} period ends. The value after that is unchanged.`}
        </p>
      )}
      {message === null ? null : <p role="status">{message}</p>}
    </form>
  );
}
