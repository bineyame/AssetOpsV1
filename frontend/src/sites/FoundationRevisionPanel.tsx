/**
 * The persisted Foundation revision: which version and period is shown, how
 * to choose another, the time-valid controls, the one S1 change (battery
 * reserve), registrations and configuration gaps (S1-01).
 *
 * Substrate leaf: rendered beside the shared Foundation screen as a slot. It
 * states only configuration. Nothing here is an observation: the gateway and
 * its sources are registrations awaiting credentials, and no evidence is
 * linked to this Foundation yet. S1-02 adds configuration Readiness, the
 * binding set in effect and the gateway snapshot (`FoundationBindingsPanel`),
 * and binding periods in the period selector.
 */

import { useState, type FormEvent } from "react";

import { Badge, DataTable, Fact, FactList, Panel } from "../ui";
import { FOUNDATION_READINESS_HEADING_ID, FoundationBindingsPanel } from "./FoundationBindingsPanel";
import type {
  BindingPublishOutcome,
  SignalBinding,
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

function controlValue(control: FoundationControl): string {
  if (control.state === "NOT_CONFIGURED") {
    return control.message ?? "Not configured in this Foundation";
  }
  if (control.members !== undefined) return control.members.join(" → ");
  return `${control.value ?? ""} ${control.unit ?? ""}`.trim();
}

export interface FoundationRevisionPanelProps {
  foundation: FoundationReadModel;
  versions: FoundationVersionsReadModel | null;
  /** The `at` instant carried in the URL, or null for "now". */
  selectedAt: string | null;
  onSelectAt: (at: string | null) => void;
  onPublish: (assetCode: string, value: number, validFrom: string) => Promise<PublishOutcome>;
  /** S1-02: where the snapshot for the instant shown downloads from. */
  snapshotHref: string;
  /** S1-02: publish a complete replacement binding set from an instant. */
  onPublishBindings: (validFrom: string, bindings: SignalBinding[], note: string) => Promise<BindingPublishOutcome>;
}

/**
 * A `datetime-local` value read as UTC. Browsers emit `HH:mm` or `HH:mm:ss`
 * (and some a fraction); whole seconds are what the API accepts.
 */
export function utcInstantFromLocal(value: string): string | null {
  const match = /^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})(?::(\d{2})(?:\.\d+)?)?$/.exec(value);
  return match === null ? null : `${match[1]}:${match[2] ?? "00"}Z`;
}

export function FoundationRevisionPanel({
  foundation,
  versions,
  selectedAt,
  onSelectAt,
  onPublish,
  snapshotHref,
  onPublishBindings,
}: FoundationRevisionPanelProps) {
  const { revision, site, provenance, controls } = foundation;
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
  const reserve = controls.battery_reserve;
  // The battery the reserve belongs to, from the registered assets; never a
  // guessed code (review m8).
  const batteryCode =
    reserve.asset_code ?? foundation.assets.find((asset) => asset.asset_type === "BATTERY")?.asset_code ?? null;

  return (
    <div className="foundation-revision">
      <Panel heading="Foundation version" headingId={FOUNDATION_REVISION_HEADING_ID}>
        <p data-foundation-period={revision.period_state}>
          <Badge tone="neutral">{`Foundation v${revision.version}`}</Badge>{" "}
          Effective {period(revision)} · immutable stored version
        </p>
        {revision.is_current ? (
          <p>This is the configuration in effect now.</p>
        ) : (
          <p role="note" data-foundation-historical="true">
            {revision.period_state === "FUTURE" ? "Scheduled period" : "Historical period"}:
            you are viewing Foundation v{revision.version}, effective {period(revision)}. This
            is not the configuration in effect now.
          </p>
        )}
        <label>
          Period shown{" "}
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
        {selectedAt !== null && !selectable.has(selectedAt) ? (
          <p>Showing the version in effect at {formatInstant(foundation.resolved.at)}.</p>
        ) : null}
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
        ) : null}
        <p>
          <a href={`#${FOUNDATION_READINESS_HEADING_ID}`}>Review configuration readiness</a>
        </p>
      </Panel>

      <FoundationBindingsPanel
        foundation={foundation}
        snapshotHref={snapshotHref}
        onPublishBindings={onPublishBindings}
      />

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
                <td data-control-state={control.state}>{controlValue(control)}</td>
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

      <Panel heading="Configuration gaps" headingId="foundation-gaps-heading">
        {foundation.configuration_gaps.length === 0 ? (
          <p>No configuration gap in this Foundation version.</p>
        ) : (
          <ul aria-labelledby="foundation-gaps-heading">
            {foundation.configuration_gaps.map((gap) => (
              <li key={`${gap.code}-${gap.subject}`} data-gap-code={gap.code}>
                {gap.message}
              </li>
            ))}
          </ul>
        )}
        <p>{foundation.evidence.statement}</p>
      </Panel>

      <Panel heading="Registered data sources" headingId="foundation-sources-heading">
        {foundation.gateways.map((gateway) => (
          <p key={gateway.gateway_id}>
            Gateway <code>{gateway.gateway_external_id}</code>: registered, awaiting credentials,
            not sending data.
          </p>
        ))}
        <DataTable labelledBy="foundation-sources-heading">
          <caption>One source per configured device. Registrations only; none is sending data.</caption>
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
                <td>Awaiting credentials</td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      </Panel>
    </div>
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
    <form aria-label="Change battery reserve" onSubmit={submit}>
      <p>
        Change the battery reserve ({assetCode}) from a chosen instant.{" "}
        {periodIsCurrent ? "In effect now, the reserve" : "In the period shown, the reserve"}
        {shown === null ? " is not configured" : ` is ${shown}%`}. Earlier periods keep their
        stored values. A change applies until the end of the period it falls in; later scheduled
        periods keep their own values.
      </p>
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
      </label>{" "}
      <label>
        Effective from (UTC){" "}
        <input
          type="datetime-local"
          value={effective}
          onChange={(event) => setEffective(event.target.value)}
        />
      </label>{" "}
      <button type="submit" disabled={pending}>
        Publish reserve change
      </button>
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
