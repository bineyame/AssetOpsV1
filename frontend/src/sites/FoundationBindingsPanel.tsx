/**
 * Configuration Readiness, the signal binding set in effect and the gateway
 * snapshot for a stored Site (S1-02), as the pieces the S1-03 Readiness view
 * composes: the verdict first, then role coverage, the binding details with
 * the binding-change action, and the acquisition details last.
 *
 * Everything here is configuration. "Set up to report" means the configuration
 * names a bound channel for every required role; it never says a device is
 * connected, reporting or healthy. A role with no channel is "Not bound", and
 * no binding set at all is "Unknown".
 */

import { Fragment, useState, type FormEvent } from "react";

import { Badge, DataTable, Disclosure, Fact, FactList, Panel, type BadgeTone } from "../ui";
import type {
  BindingPublishOutcome,
  ConfigurationReadiness,
  FoundationReadModel,
  ReadinessRole,
  SignalBinding,
} from "./siteFoundationClient";
import { formatInstant, utcInstantFromLocal } from "./FoundationRevisionPanel";

export const FOUNDATION_READINESS_HEADING_ID = "foundation-readiness-heading";
export const FOUNDATION_ROLES_HEADING_ID = "foundation-roles-heading";
export const FOUNDATION_BINDINGS_HEADING_ID = "foundation-bindings-heading";
export const FOUNDATION_ACQUISITION_HEADING_ID = "foundation-acquisition-heading";

const READINESS_WORD: Record<ConfigurationReadiness["state"], string> = {
  READY_TO_REPORT: "Set up to report",
  INCOMPLETE: "Incomplete",
  UNKNOWN: "Unknown",
};

/**
 * Configuration-only colour (D-2026-10-12-v01a-owner-visual-rulings): green
 * when every required role is configured with no Foundation gap, amber for a
 * known configuration gap, neutral when the basis cannot be resolved. Colour
 * never asserts contact, received records, accepted Evidence or health.
 */
const READINESS_TONE: Record<ConfigurationReadiness["state"], BadgeTone> = {
  READY_TO_REPORT: "configured",
  INCOMPLETE: "config-gap",
  UNKNOWN: "neutral",
};

/**
 * A role row's tone. An optional role that is not bound is neutral: it is not
 * a gap, and it must not read amber beside a complete required verdict.
 */
export function roleTone(role: ReadinessRole, state?: ConfigurationReadiness["state"]): BadgeTone {
  // Architect ruling: an absent or unresolvable basis stays neutral.
  if (state === "UNKNOWN") return "neutral";
  if (role.status === "CONFIGURED") return "configured";
  return role.required ? "config-gap" : "neutral";
}

/**
 * The colour scope, as one `v69-chart-note` line under the Readiness table
 * (W1-F1 fix round 1: the three-chip legend and its paragraphs are reduced to
 * this line). The material limit stays visible beside the claim.
 */
export const READINESS_COLOUR_SCOPE =
  "Colours describe configuration of the selected Foundation version only: green configured, amber a missing required role, control or declaration, grey an unresolved basis. Green does not mean a device is connected, records have arrived, Evidence is accepted or equipment is in good condition.";

const ROLE_STATUS_WORD: Record<ReadinessRole["status"], string> = {
  CONFIGURED: "Configured",
  UNBOUND: "Not bound",
  NOT_CONFIGURED: "Not configured",
};

function conversionText(binding: SignalBinding): string {
  const { kind } = binding.conversion;
  return kind === "IDENTITY" ? "Same unit" : "State labels mapped";
}

function roleCoverage(role: ReadinessRole, mappings: SignalBinding[]): string {
  if (role.covered_by === "FOUNDATION_CONTROL") return role.detail ?? "Foundation control";
  if (role.subjects.length === 0) return "No channel is bound to this role.";
  const byId = new Map(mappings.map((m) => [m.binding_revision_id, m]));
  return role.subjects
    .map((subject) => {
      if (subject.status === "UNBOUND") return `${subject.asset_code ?? "Unknown"}: not bound`;
      const channel = subject.binding_revision_ids
        .map((id) => byId.get(id))
        .filter((m): m is SignalBinding => m !== undefined)
        .map((m) => `${m.device_id} / ${m.signal_id}`)
        .join(", ");
      return `${subject.asset_code ?? "Unknown"}: ${channel}`;
    })
    .join("; ");
}

/** Own keys only (W1-UX-06 phase-1 review L4): `in` would treat inherited names such as `constructor` as known. */
export function knownReadiness(state: string): state is ConfigurationReadiness["state"] {
  return Object.hasOwn(READINESS_WORD, state);
}

function verdictSentence(readiness: ConfigurationReadiness): string {
  if (!knownReadiness(readiness.state)) {
    return "The set-up state in this read is not recognised, so no overall set-up judgment is made here.";
  }
  if (readiness.state === "READY_TO_REPORT") {
    return "Every required role has a configured channel or control, and this Foundation has no configuration gap.";
  }
  if (readiness.missing_roles.length > 0) {
    // A Foundation control (the battery reserve) is configured, not bound:
    // name it apart from the channel roles (S1-02 re-review finding).
    const controls = new Set(
      readiness.roles.filter((role) => role.covered_by === "FOUNDATION_CONTROL").map((role) => role.label),
    );
    const unbound = readiness.missing_roles.filter((label) => !controls.has(label));
    const unconfigured = readiness.missing_roles.filter((label) => controls.has(label));
    return [
      unbound.length > 0 ? `Not bound: ${unbound.join(", ")}.` : null,
      unconfigured.length > 0 ? `Not configured: ${unconfigured.join(", ")}.` : null,
    ]
      .filter((part) => part !== null)
      .join(" ");
  }
  return "Every required role has a configured channel or control, but this Foundation has configuration gaps.";
}

/**
 * The set-up verdict as the lead of the Readiness strip, as the mock's
 * `Needs review · Configuration readiness is distinct from claim readiness`
 * (W1-F1 fix round 1). Configuration only; never connection or condition.
 */
export function ReadinessVerdictLead({ foundation }: { foundation: FoundationReadModel }) {
  const { readiness } = foundation;
  const known = knownReadiness(readiness.state);
  return (
    <span className="readiness-verdict-lead" data-readiness-verdict="" data-readiness-state={readiness.state}>
      <span className="verdict__state">
        {/* W1-UX-06 (`D-2026-10-17-w1-ux-06` Q4): an unrecognised state is neutral and says so, never blank. */}
        <Badge tone={known ? READINESS_TONE[readiness.state] : "neutral"}>
          {known ? READINESS_WORD[readiness.state] : "Set-up state not recognised"}
        </Badge>
      </span>{" "}
      <span>Configuration readiness is distinct from what the readings can support</span>
    </span>
  );
}

/**
 * The verdict's reason and the colour scope, as two `v69-chart-note` lines under
 * the Readiness table: why the verdict is what it is, the Foundation gaps by
 * name (configuration, not channel links), the read's own limit statement, and
 * what the colours do and do not mean. Counts are of configuration, never readings.
 */
export function ReadinessVerdictNotes({ foundation }: { foundation: FoundationReadModel }) {
  const { readiness } = foundation;
  return (
    <>
      <p className="v69-chart-note" data-readiness-verdict-note="">
        <span className="verdict__sentence">{verdictSentence(readiness)}</span>
        {readiness.foundation_gaps.length > 0 ? (
          <span data-readiness-gaps="">
            {" Foundation gaps (configuration, not channel links): "}
            {readiness.foundation_gaps.map((gap, index) => (
              <Fragment key={`${gap.code}:${gap.subject}`}>
                {index > 0 ? "; " : null}
                <span data-readiness-gap={gap.code}>{gap.message}</span>
              </Fragment>
            ))}
            .
          </span>
        ) : null}{" "}
        <span data-readiness-statement="">{readiness.statement}</span>
      </p>
      <p className="v69-chart-note" data-readiness-colour-scope="">
        {READINESS_COLOUR_SCOPE}
      </p>
    </>
  );
}

/** Every role the analysis needs and what in this configuration covers it. */
export function RoleCoveragePanel({ foundation }: { foundation: FoundationReadModel }) {
  const { readiness, bindings } = foundation;
  return (
    <Panel heading="Role coverage" headingId={FOUNDATION_ROLES_HEADING_ID}>
      <DataTable labelledBy={FOUNDATION_ROLES_HEADING_ID}>
        <caption>
          Roles the analysis of this Site needs, and what in this configuration covers each one.
          Configuration only; what the readings can support is on Evidence.
        </caption>
        <thead>
          <tr>
            <th scope="col">Role</th>
            <th scope="col">Required</th>
            <th scope="col">Configuration</th>
            <th scope="col">Covered by</th>
          </tr>
        </thead>
        <tbody>
          {readiness.roles.map((role) => (
            <tr key={role.role} data-readiness-role={role.role}>
              <th scope="row">{role.label}</th>
              <td>{role.required ? "Required" : "Optional"}</td>
              <td data-readiness-status={role.status}>
                <Badge tone={roleTone(role, readiness.state)}>{ROLE_STATUS_WORD[role.status]}</Badge>
              </td>
              <td>{roleCoverage(role, bindings.mappings)}</td>
            </tr>
          ))}
        </tbody>
      </DataTable>
    </Panel>
  );
}

export interface SignalBindingsPanelProps {
  foundation: FoundationReadModel;
  onPublishBindings: (validFrom: string, bindings: SignalBinding[], note: string) => Promise<BindingPublishOutcome>;
}

/** The binding set in effect, its unbound channels and the binding change. */
export function SignalBindingsPanel({ foundation, onPublishBindings }: SignalBindingsPanelProps) {
  const { readiness, bindings } = foundation;
  const unbound = readiness.channels.filter((channel) => channel.status !== "BOUND");

  return (
    <Panel heading="Reading-channel links" headingId={FOUNDATION_BINDINGS_HEADING_ID}>
      {bindings.binding_set === null ? (
        <p data-bindings-state="NONE">{bindings.statement}</p>
      ) : (
        <>
          <p data-bindings-state="PUBLISHED">
            <Badge tone="neutral">{`Channel links v${bindings.binding_set.version}`}</Badge> Effective{" "}
            {formatInstant(bindings.binding_set.valid_from)} to{" "}
            {formatInstant(bindings.binding_set.valid_to)} · {bindings.statement}
          </p>
          <DataTable labelledBy={FOUNDATION_BINDINGS_HEADING_ID}>
            <caption>
              Each bound channel of the registered gateway: its source, the equipment it describes,
              its role and units. Configuration, not readings.
            </caption>
            <thead>
              <tr>
                <th scope="col">Channel</th>
                <th scope="col">Source</th>
                <th scope="col">Equipment</th>
                <th scope="col">Role</th>
                <th scope="col">Units</th>
                <th scope="col">Conversion</th>
                <th scope="col">Link reference</th>
              </tr>
            </thead>
            <tbody>
              {bindings.mappings.map((binding) => (
                <tr key={binding.binding_revision_id} data-binding-channel={`${binding.device_id}/${binding.signal_id}`}>
                  <th scope="row">
                    <code data-vocabulary-exempt="source-reference">{`${binding.device_id} / ${binding.signal_id}`}</code>
                  </th>
                  <td>
                    <code data-vocabulary-exempt="source-reference">{binding.source_external_id ?? binding.source_id}</code>
                  </td>
                  <td>{binding.asset_code === null ? "Unknown" : <code data-vocabulary-exempt="source-reference">{binding.asset_code}</code>}</td>
                  <td>{binding.role_label}</td>
                  <td>{`${binding.source_unit} → ${binding.canonical_unit}`}</td>
                  <td>{conversionText(binding)}</td>
                  <td>
                    <code data-vocabulary-exempt="source-reference">{binding.binding_revision_id}</code>
                  </td>
                </tr>
              ))}
            </tbody>
          </DataTable>
          <Disclosure name="binding-set-record" summary="Channel-link set record and content reference">
            <FactList>
              <Fact term="Channel-link set reference">
                <code data-vocabulary-exempt="source-reference">{bindings.binding_set.binding_set_id}</code>
              </Fact>
              <Fact term="Channel-link version record reference">
                <code data-vocabulary-exempt="source-reference">{bindings.binding_set.binding_set_revision_id}</code>
              </Fact>
              <Fact term="Channel links content reference (SHA-256)">
                <code data-vocabulary-exempt="source-reference">{bindings.binding_set.bindings_sha256}</code>
              </Fact>
              <Fact term="Role set">
                <code data-vocabulary-exempt="source-reference">{bindings.binding_set.role_set}</code>
              </Fact>
            </FactList>
          </Disclosure>
        </>
      )}
      {unbound.length === 0 ? null : (
        <>
          <p>Declared channels with no channel link (Unknown until bound):</p>
          <ul aria-label="Unbound channels">
            {unbound.map((channel) => (
              <li key={`${channel.device_id}/${channel.signal_id}`} data-channel-status={channel.status}>
                <code data-vocabulary-exempt="source-reference">{`${channel.device_id} / ${channel.signal_id}`}</code> ({channel.unit}):{" "}
                {channel.status === "UNREGISTERED" ? "no registered source" : "not bound"}
              </li>
            ))}
          </ul>
        </>
      )}
      {bindings.binding_set === null || bindings.mappings.length === 0 ? null : (
        <RemoveBindingForm mappings={bindings.mappings} onPublishBindings={onPublishBindings} />
      )}
    </Panel>
  );
}

/**
 * The pinned gateway snapshot for the period shown, in its own labelled
 * acquisition-details area: availability, hash, the records it pins and the
 * download. Never a claim that the gateway has authenticated or connected.
 */
export function AcquisitionDetailsPanel({
  foundation,
  snapshotHref,
}: {
  foundation: FoundationReadModel;
  snapshotHref: string;
}) {
  const snapshot = foundation.acquisition_snapshot;
  return (
    <Panel heading="Acquisition details" headingId={FOUNDATION_ACQUISITION_HEADING_ID}>
      {snapshot.available ? (
        <div data-snapshot-available="true">
          <p>
            Gateway snapshot pinned at publication for the period shown.{" "}
            <a href={snapshotHref} download>
              Download snapshot
            </a>
          </p>
          <FactList>
            <Fact term="Snapshot SHA-256">
              <code data-vocabulary-exempt="source-reference">{snapshot.sha256}</code>
            </Fact>
            <Fact term="Schema">
              <code data-vocabulary-exempt="source-reference">{snapshot.schema}</code>
            </Fact>
            <Fact term="Foundation version record">
              <code data-vocabulary-exempt="source-reference">{snapshot.foundation_revision_id}</code>
            </Fact>
            <Fact term="Channel-link version record">
              <code data-vocabulary-exempt="source-reference">{snapshot.binding_set_revision_id}</code>
            </Fact>
            <Fact term="Access">{snapshot.access}</Fact>
          </FactList>
        </div>
      ) : (
        <p data-snapshot-available="false">
          Gateway snapshot: not available.{" "}
          {snapshot.reason}
        </p>
      )}
    </Panel>
  );
}

function RemoveBindingForm({
  mappings,
  onPublishBindings,
}: {
  mappings: SignalBinding[];
  onPublishBindings: SignalBindingsPanelProps["onPublishBindings"];
}) {
  const [selected, setSelected] = useState("");
  const [effective, setEffective] = useState("");
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const instant = effective === "" ? null : utcInstantFromLocal(effective);
    if (selected === "" || instant === null) {
      setMessage("Choose a channel link and the instant its removal takes effect.");
      return;
    }
    const removed = mappings.find((m) => m.binding_revision_id === selected);
    const remaining = mappings.filter((m) => m.binding_revision_id !== selected);
    setPending(true);
    const outcome = await onPublishBindings(
      instant,
      remaining,
      `Removed ${removed?.device_id ?? ""} / ${removed?.signal_id ?? ""}`,
    );
    setPending(false);
    setMessage(
      outcome.status === "published"
        ? `Published channel links v${outcome.binding_set.version}, effective ${formatInstant(
            outcome.binding_set.valid_from,
          )} ${
            outcome.applies_until == null
              ? "with no end"
              : `only until ${formatInstant(outcome.applies_until)}${
                  outcome.stopped_by_binding_version == null
                    ? ""
                    : `, where channel links v${outcome.stopped_by_binding_version} (a later, separately published change) takes over`
                }`
          }.`
        : `Not published: ${outcome.message}`,
    );
  }

  return (
    <form className="action-form" aria-label="Remove a channel link" onSubmit={submit}>
      <h3 className="action-form__heading">Change the channel links</h3>
      <p>
        Remove one channel link from a chosen instant. This publishes a new channel-link version;
        earlier periods keep their stored channel links.
      </p>
      <div className="action-form__fields">
        <label>
          Channel link{" "}
          <select value={selected} onChange={(event) => setSelected(event.target.value)}>
            <option value="">Choose a channel link</option>
            {mappings.map((m) => (
              <option key={m.binding_revision_id} value={m.binding_revision_id}>
                {`${m.role_label} · ${m.device_id} / ${m.signal_id}`}
              </option>
            ))}
          </select>
        </label>
        <label>
          Effective from (UTC){" "}
          <input type="datetime-local" value={effective} onChange={(event) => setEffective(event.target.value)} />
        </label>
        <button type="submit" disabled={pending}>
          Publish channel-link change
        </button>
      </div>
      {message === null ? null : <p role="status">{message}</p>}
    </form>
  );
}
