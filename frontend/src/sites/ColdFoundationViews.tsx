import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

import {
  AttentionList,
  Badge,
  Breadcrumbs,
  type Crumb,
  DataTable,
  ExactReferences,
  KeyValues,
  MetricCard,
  MetricCards,
  Panel,
  SITE_SCREEN_DESCRIPTIONS,
  SitePageHeader,
} from "../ui";
import type { ColdBinding, ColdFoundationClient, ColdFoundationRead, ColdFoundationReadModel, ColdTopologyNode } from "./coldFoundationClient";
import { FoundationSubtabs, foundationViewLabel, type FoundationView } from "./FoundationSubtabs";
import { formatInstant } from "./FoundationRevisionPanel";
import type { EvidenceRead } from "./evidenceRead";
import type { GatewayHealth, GatewayHealthClient } from "./gatewayHealthClient";
import type { FoundationVersionsReadModel } from "./siteFoundationClient";
import "./w2-cold-foundation.css";

/*
 * W2-01: the three Foundation views of a COLDCHAIN Site (`cold-foundation`, `cold-readiness`,
 * `cold-sld`), rendered from the selected cold configuration read in the v69 panel slots
 * (`.agent/W2-technical-design-cold.md` section 6 panel map; `D-2026-10-17-mockup-layout-spec`).
 * Configuration only: nothing here is a temperature, equipment-health or evidence claim.
 */

export const COLD_FOUNDATION_LOADING = "Loading the site's cold configuration.";
export const COLD_GATEWAY_LOADING = "Loading the site's gateway contact.";
export const COLD_HEADING_ID = "cold-foundation-page-heading";
export const NO_GATEWAY_SELECTED = "No gateway selected";
export const CONFIGURED = "Configured";
export const NEEDS_A_SOURCE = "Needs a source";
export const NOT_CONFIGURED = "Not configured";
export const NOT_DECLARED = "Not declared";
export const SOURCE_CONTACT_UNAVAILABLE = "Source contact unavailable";
export const CONFIDENCE_NOT_ASSESSED = "Confidence is not assessed";
export const FUNCTION_UNKNOWN = "Function description not recorded";

/** Plain labels of the `cold-roles-1` roles (backend `sites/binding_roles.py`). */
const ROLE_LABEL: Record<string, string> = {
  chamber_temperature: "Chamber temperature",
  cold_policy_low: "Temperature policy low",
  cold_policy_high: "Temperature policy high",
  compressor_state: "Compressor state",
  compressor_power: "Compressor power",
  grid_state: "Grid state",
  backup_start_event: "Generator start request and result",
  generator_state: "Generator state",
  backup_bus_state: "Backup bus state",
  grid_power_event: "Grid power loss and restoration",
  transfer_result: "Transfer result",
  door_event: "Door open and close",
  ambient_temperature: "Ambient temperature",
  manual_temperature: "Manual temperature log",
};

export const roleLabel = (role: string | null): string =>
  role === null ? "Site" : (ROLE_LABEL[role] ?? role.replace(/_/g, " "));

const NODE_ROLE_WORD: Record<string, string> = {
  COLD_ROOM: "Cold room",
  SENSOR: "Sensor",
  COOLING: "Cooling",
  SWITCH: "Switch",
  GENERATION: "Generation",
  BUS: "Power bus",
  METERING: "Metering",
};

const MEDIUM_WORD: Record<string, string> = { AC: "power", THERMAL: "cooling", SIGNAL: "sensing", DC: "DC power", FUEL: "fuel" };

const CONTACT: Record<string, { value: string; tone?: "muted" }> = {
  RECENT: { value: "Recent contact" },
  STALE: { value: "Contact stale", tone: "muted" },
  NEVER: { value: "Never contacted", tone: "muted" },
};

/** Readiness areas: which roles each row of the readiness table answers for. */
const AREAS: { key: string; area: string; roles: string[] }[] = [
  { key: "chamber", area: "Chamber temperature probe", roles: ["chamber_temperature"] },
  { key: "cooling", area: "Compressor", roles: ["compressor_state", "compressor_power"] },
  { key: "grid", area: "Grid supply", roles: ["grid_state", "grid_power_event"] },
  { key: "backup", area: "Backup generator and bus", roles: ["generator_state", "backup_start_event", "backup_bus_state"] },
  { key: "transfer", area: "Transfer switch", roles: ["transfer_result"] },
  { key: "door", area: "Door and loading log", roles: ["door_event", "manual_temperature"] },
  { key: "ambient", area: "Ambient temperature", roles: ["ambient_temperature"] },
];
const DEFINITION_CODES = new Set(["ROOM_MISSING", "POLICY_MISSING"]);
/** The optional `cold-roles-1` channel roles (backend `sites/binding_roles.py`, required flag false). */
const OPTIONAL_ROLES = new Set(["compressor_power", "transfer_result", "door_event", "ambient_temperature", "manual_temperature"]);

/* Frame -------------------------------------------------------------------- */

export interface ColdFoundationFrameProps {
  view: FoundationView;
  siteId: string;
  siteName: string;
  mode: string | null;
  selectedAt: string | null;
  onSelectAt: (at: string | null) => void;
  client: ColdFoundationClient;
  gatewayHealth?: GatewayHealthClient;
  versions: FoundationVersionsReadModel | null;
  viewHref: (target: FoundationView) => string;
  evidenceHref: string;
  healthHref: string;
  tabs: ReactNode;
  parentTrail: Crumb[];
}

const DESCRIPTION: Record<FoundationView, string> = {
  model: SITE_SCREEN_DESCRIPTIONS["cold-foundation"],
  readiness: SITE_SCREEN_DESCRIPTIONS["cold-readiness"],
  sld: SITE_SCREEN_DESCRIPTIONS["cold-sld"],
};

export function ColdFoundationFrame(props: ColdFoundationFrameProps) {
  const { view, siteId, siteName, selectedAt, client, gatewayHealth } = props;
  const [read, setRead] = useState<{ key: string; value: ColdFoundationRead } | null>(null);
  const key = `${siteId}|${selectedAt ?? ""}`;
  useEffect(() => {
    let active = true;
    void client.getColdFoundation(siteId, selectedAt).then((value) => {
      if (active) setRead({ key, value });
    });
    return () => {
      active = false;
    };
  }, [client, siteId, selectedAt, key]);

  const [health, setHealth] = useState<EvidenceRead<GatewayHealth> | null>(null);
  useEffect(() => {
    if (gatewayHealth === undefined) {
      setHealth({ status: "unavailable", message: null });
      return undefined;
    }
    let active = true;
    void gatewayHealth.getGatewayHealth(siteId).then((value) => {
      if (active) setHealth(value);
    });
    return () => {
      active = false;
    };
  }, [gatewayHealth, siteId]);

  const current = read !== null && read.key === key ? read.value : null;
  const gateway = gatewayName(health);
  const trail: Crumb[] =
    view === "model"
      ? [...props.parentTrail, { label: "Foundation" }]
      : [...props.parentTrail, { label: "Foundation", to: props.viewHref("model") }, { label: foundationViewLabel(view) }];

  return (
    <main aria-labelledby={COLD_HEADING_ID} data-cold-foundation-view={view}>
      <Breadcrumbs trail={trail} />
      <SitePageHeader siteName={siteName} siteId={siteId} mode={props.mode} description={DESCRIPTION[view]} headingId={COLD_HEADING_ID} />
      {props.tabs}
      <FoundationSubtabs current={view} hrefFor={props.viewHref} />
      {current === null ? (
        <p>{COLD_FOUNDATION_LOADING}</p>
      ) : current.status === "loaded" ? (
        <ColdViews {...props} read={current.value} health={health} gateway={gateway} />
      ) : (
        <ColdRefusal {...props} read={current} gateway={gateway} />
      )}
    </main>
  );
}

function gatewayName(health: EvidenceRead<GatewayHealth> | null): string {
  if (health !== null && health.status === "loaded" && health.value.gateways.length > 0) {
    return health.value.gateways.map((g) => g.gateway_external_id).join(", ");
  }
  return NO_GATEWAY_SELECTED;
}

/* Refused or unavailable read: the page-level state, then every slot with its gap. */

function ColdRefusal(props: ColdFoundationFrameProps & { read: Exclude<ColdFoundationRead, { status: "loaded" }>; gateway: string }) {
  const { read, selectedAt } = props;
  const noVersion = read.status === "refused" && read.code === "FOUNDATION_REVISION_NOT_FOUND";
  const gap = noVersion
    ? "No configuration is stored for the selected time, so nothing is shown as configured in this panel."
    : "The configuration could not be read, so nothing is shown as configured in this panel.";
  return (
    <>
      <div className="page-refusal" role="status" data-page-refusal={noVersion ? "no-version" : "unavailable"}>
        <p className="page-refusal__title">
          <strong>{noVersion ? "No stored version for this period" : "Configuration unavailable"}</strong>
        </p>
        <p>
          {noVersion
            ? `No configuration of this site is in effect at ${formatInstant(selectedAt)}. The configuration in effect now is not shown in its place.`
            : "The site's configuration could not be read. Nothing is shown as configured until it can be."}
        </p>
        {noVersion && selectedAt !== null ? (
          <button type="button" className="button primary" onClick={() => props.onSelectAt(null)}>
            Show the version in effect now
          </button>
        ) : null}
        <ExactReferences
          name="cold-refusal-references"
          variant="tech"
          references={[
            { label: "Refusal code", value: read.status === "refused" ? read.code : null },
            { label: "Server message", value: read.message },
            { label: "Selected time (exact)", value: selectedAt },
          ]}
        />
      </div>
      <ColdSkeletons view={props.view} siteName={props.siteName} gateway={props.gateway} gap={gap} />
    </>
  );
}

export function ColdSkeletons({ view, siteName, gateway, gap }: { view: FoundationView; siteName: string; gateway: string; gap: string }) {
  const slot = (title: string, id: string) => (
    <Panel heading={title} headingId={id}>
      <p className="not-available-yet v69-chart-note" data-panel-gap={id}>
        {gap}
      </p>
    </Panel>
  );
  if (view === "model") {
    return (
      <div className="panel-pair panel-pair--equal">
        {slot("Physical site", "cold-physical-site-heading")}
        {slot("Operating interpretation", "cold-operating-heading")}
      </div>
    );
  }
  if (view === "sld") {
    return (
      <>
        {slot(siteName, "cold-sld-heading")}
        {slot("What each part does", "cold-sld-parts-heading")}
      </>
    );
  }
  return (
    <>
      {slot("Readiness and commissioning evidence", "cold-readiness-table-heading")}
      <Panel className="gw-panel" heading={`Gateway status · ${gateway}`} headingId="cold-gateway-heading">
        <p className="not-available-yet v69-chart-note" data-panel-gap="cold-gateway-heading">
          {gap}
        </p>
        <div className="panel-pair">
          {slot("Connected sources", "cold-connected-sources-heading")}
          {slot("Effect on readiness and confidence", "cold-effect-heading")}
        </div>
      </Panel>
    </>
  );
}

/* Loaded ------------------------------------------------------------------- */

interface ViewProps extends ColdFoundationFrameProps {
  read: ColdFoundationReadModel;
  health: EvidenceRead<GatewayHealth> | null;
  gateway: string;
}

function ColdViews(props: ViewProps) {
  if (props.view === "model") return <ColdModelView {...props} />;
  if (props.view === "sld") return <SldView {...props} />;
  return <ReadinessView {...props} />;
}

function nodeNames(read: ColdFoundationReadModel): Map<string, string> {
  const names = new Map<string, string>();
  for (const node of read.topology?.nodes ?? []) {
    if (node.asset_id !== null) names.set(node.asset_id, node.display_name ?? node.component_id);
  }
  return names;
}

const bound = (read: ColdFoundationReadModel, role: string) => read.bindings.some((b) => b.role === role);
const allBound = (read: ColdFoundationReadModel, roles: string[]) => roles.every((role) => bound(read, role));

function SourceBadge({ configured }: { configured: boolean }) {
  return configured ? <Badge tone="configured">{CONFIGURED}</Badge> : <Badge tone="config-gap">{NEEDS_A_SOURCE}</Badge>;
}

function policyText(read: ColdFoundationReadModel): string | null {
  const bands = read.rooms.flatMap((room) => (room.policy === null ? [] : [`${room.policy.low}–${room.policy.high} °C`]));
  return bands.length === 0 ? null : Array.from(new Set(bands)).join(", ");
}

function periodText(read: ColdFoundationReadModel): string {
  return `${formatInstant(read.valid_from)} to ${read.valid_to === null ? "no end date" : formatInstant(read.valid_to)}`;
}

/** The mock's one-line status bar: the screen verdict first, the period, then the period selector. */
function ColdStrip(props: ViewProps & { lead: ReactNode; action: ReactNode }) {
  const { read, versions, selectedAt } = props;
  const revision = versions?.revisions.find((r) => r.revision_id === read.foundation_revision_id) ?? null;
  const periods = (versions?.revisions ?? [])
    .filter((r) => r.recorded_state === "CURRENT")
    .sort((a, b) => a.valid_from.localeCompare(b.valid_from));
  const inList = selectedAt !== null && periods.some((r) => r.valid_from === selectedAt);
  return (
    <div className="status-strip status-strip--line" role="group" aria-label="Foundation version" data-cold-strip="">
      <span className="status-strip__lead">{props.lead}</span>
      <span className="status-strip__item">
        <Badge tone="neutral">{revision === null ? "Stored configuration" : `Configuration v${revision.version}`}</Badge>{" "}
        <span>Effective {periodText(read)}</span>
      </span>
      {revision === null ? null : revision.period_state === "CURRENT" ? (
        <span className="status-strip__state">This is the configuration in effect now.</span>
      ) : (
        <span role="note" className="status-strip__state status-strip__state--historical" data-foundation-historical="true">
          {revision.period_state === "FUTURE" ? "Scheduled period" : "Historical period"}: not the configuration in effect now.
        </span>
      )}
      <span className="status-strip__spacer" aria-hidden="true" />
      <select
        className="status-strip__select"
        aria-label="Foundation period"
        value={selectedAt ?? ""}
        onChange={(event) => props.onSelectAt(event.target.value === "" ? null : event.target.value)}
      >
        <option value="">In effect now</option>
        {selectedAt !== null && !inList ? <option value={selectedAt}>{`At ${formatInstant(selectedAt)} (from the address)`}</option> : null}
        {periods.map((r) => (
          <option key={r.revision_id} value={r.valid_from}>{`v${r.version} · from ${formatInstant(r.valid_from)}`}</option>
        ))}
      </select>
      <span className="status-strip__action">{props.action}</span>
      <ExactReferences
        name="cold-strip-references"
        variant="tech"
        references={[
          { label: "Selected time (exact)", value: selectedAt },
          { label: "Foundation version record", value: read.foundation_revision_id },
          { label: "Effective from (exact)", value: read.valid_from },
          { label: "Effective to (exact)", value: read.valid_to },
        ]}
      />
    </div>
  );
}

/* cold-foundation ------------------------------------------------------------ */

function ColdModelView(props: ViewProps) {
  const { read, siteId } = props;
  const names = nodeNames(read);
  const nodes = read.topology?.nodes ?? [];
  const ofRole = (role: string) => nodes.filter((n) => n.node_role === role).map((n) => n.display_name ?? n.component_id);
  const rooms = read.rooms.map((room) => names.get(room.asset_id) ?? "Unnamed cold room");
  const supplies = [...ofRole("METERING"), ...ofRole("GENERATION")];
  const switches = ofRole("SWITCH");
  const compressors = ofRole("COOLING");
  const chamberProbes = read.rooms.flatMap((room) => room.probe_ids.map((id) => names.get(id) ?? "Unnamed probe"));
  const primary = new Set(read.rooms.flatMap((room) => room.probe_ids));
  const otherSensors = nodes.filter((n) => n.node_role === "SENSOR" && (n.asset_id === null || !primary.has(n.asset_id)));
  const edges = read.topology?.edges.length ?? 0;
  const policy = policyText(read);
  const backupRoles = ["backup_start_event", "grid_power_event", "generator_state"];
  const blocking = read.readiness.messages.filter((m) => m.blocking).length;
  const join = (items: string[]) => (items.length === 0 ? NOT_DECLARED : items.join(" · "));
  return (
    <>
      <ColdStrip
        {...props}
        lead={<Badge tone="neutral">Configuration only</Badge>}
        action={<Link to={props.viewHref("readiness")}>Configuration readiness →</Link>}
      />
      <div className="panel-pair panel-pair--equal">
        <Panel heading="Physical site" headingId="cold-physical-site-heading">
          <KeyValues
            label="Physical site"
            rows={[
              ["Site ID", siteId],
              ["Cold rooms", join(rooms)],
              ["Power supply", supplies.length === 0 ? NOT_DECLARED : `${supplies.join(" · ")}${switches.length === 0 ? "" : ` via ${switches.join(", ")}`}`],
              ["Cooling equipment", join(compressors)],
              ["Chamber temperature probe", chamberProbes.length === 0 ? NOT_DECLARED : chamberProbes.join(" · ")],
              ["Other sensors", otherSensors.length === 0 ? "None declared" : otherSensors.map((n) => n.display_name ?? n.component_id).join(" · ")],
              ["Declared connections", read.topology === null ? "No topology declared" : `${edges} connection${edges === 1 ? "" : "s"}`],
              ["Night outage rule", NOT_CONFIGURED],
            ]}
          />
          <p className="v69-chart-note" data-cold-undeclared="">
            Parts and connections not declared in this version are not shown; no live state is implied.
          </p>
          <ExactReferences
            name="cold-physical-references"
            variant="tech"
            references={[
              { label: "Foundation version record", value: read.foundation_revision_id },
              ...read.rooms.map((room, index) => ({ label: `Cold room ${index + 1} asset`, value: room.asset_id })),
            ]}
          />
        </Panel>
        <Panel heading="Operating interpretation" headingId="cold-operating-heading">
          <KeyValues
            label="Operating interpretation"
            rows={[
              ["Temperature policy", policy ?? NOT_CONFIGURED],
              ["Product or stock context", NOT_CONFIGURED],
              ["Door and loading observations", <SourceBadge key="door" configured={bound(read, "door_event")} />],
              ["Temperature probes", <SourceBadge key="probe" configured={bound(read, "chamber_temperature")} />],
              ["Backup sequence", <SourceBadge key="backup" configured={allBound(read, backupRoles)} />],
              ["Effective period", periodText(read)],
            ]}
          />
          <p className="v69-chart-note" data-cold-operating-note="">
            {blocking === 0
              ? "Every required reading has a configured source."
              : `${blocking} required item${blocking === 1 ? "" : "s"} still need${blocking === 1 ? "s" : ""} set-up; see Readiness.`}{" "}
            A configured setting is not proof of performance.
          </p>
          <ExactReferences
            name="cold-operating-references"
            variant="tech"
            references={read.rooms.flatMap((room, index) =>
              room.policy === null ? [] : [{ label: `Policy record, room ${index + 1}`, value: room.policy.revision_id }],
            )}
          />
        </Panel>
      </div>
      <p className="note">Configuration changes create a new effective version. A changed setting is not proof of an operational effect.</p>
    </>
  );
}

/* cold-readiness ------------------------------------------------------------- */

function ReadinessView(props: ViewProps) {
  const { read, health, gateway } = props;
  const ready = read.readiness.state === "READY_TO_REPORT";
  const names = nodeNames(read);
  const messages = read.readiness.messages;
  const policy = policyText(read);
  const unconfirmed = read.commissioning.evidence_ids.length === 0;
  const confirmed = (
    <Badge tone="neutral">{unconfirmed ? "Unconfirmed" : `${read.commissioning.evidence_ids.length} records`}</Badge>
  );
  const needed = (items: string[]) =>
    items.length === 0 ? "—" : (
      <ul className="plain-list">
        {items.map((text) => (
          <li key={text}>{text}</li>
        ))}
      </ul>
    );
  const matched = new Set<string>();
  const forRoles = (roles: string[]) =>
    messages.filter((m) => m.role !== null && roles.includes(m.role)).map((m) => {
      matched.add(`${m.code}|${m.role}|${m.component_id}`);
      return m.message;
    });
  const definitionNeeds = messages.filter((m) => DEFINITION_CODES.has(m.code)).map((m) => {
    matched.add(`${m.code}|${m.role}|${m.component_id}`);
    return m.message;
  });
  const rows = AREAS.map((area) => {
    const missing = area.roles.filter((role) => !bound(read, role));
    const missingRequired = missing.filter((role) => !OPTIONAL_ROLES.has(role));
    // Needs a source: a required reading has none, or no reading of the area has one.
    const configured = missingRequired.length === 0 && missing.length < area.roles.length;
    const shown = missing.length === area.roles.length ? [] : missing;
    return {
      key: area.key,
      area: area.area,
      declared: (
        <>
          <SourceBadge configured={configured} />
          {shown.length === 0 ? null : (
            <span className="muted">
              {" "}
              No source: {shown.map((role) => `${roleLabel(role)}${OPTIONAL_ROLES.has(role) ? " (optional)" : ""}`).join(", ")}
            </span>
          )}
          {missing.length === area.roles.length && area.roles.every((role) => OPTIONAL_ROLES.has(role)) ? (
            <span className="muted"> Optional</span>
          ) : null}
        </>
      ),
      needed: needed(forRoles(area.roles)),
      next: <Link to={props.viewHref("sld")}>Single line diagram →</Link>,
    };
  });
  const other = messages.filter((m) => !matched.has(`${m.code}|${m.role}|${m.component_id}`));
  const blocking = messages.filter((m) => m.blocking);

  const contact = read.contact;
  const word = contact.state === null ? { value: "Contact unknown", tone: "muted" as const } : (CONTACT[contact.state] ?? { value: contact.state, tone: "muted" as const });
  const limitations = contact.limitations ?? [];
  const contactNote =
    contact.as_of !== null
      ? `Last contact ${formatInstant(contact.as_of)}`
      : contact.state === "NEVER"
        ? "No gateway diagnostic has been received"
        : (limitations[0] ?? "No contact time is recorded");

  return (
    <>
      <ColdStrip
        {...props}
        lead={ready ? <Badge tone="configured">Set up to report</Badge> : <Badge tone="config-gap">Set-up incomplete</Badge>}
        action={<Link to={props.viewHref("sld")}>Single line diagram →</Link>}
      />
      <Panel
        heading="Readiness and commissioning evidence"
        headingId="cold-readiness-table-heading"
        description="Declared means configured in the selected version. Confirmed needs a commissioning record; none is stored."
      >
        <DataTable labelledBy="cold-readiness-table-heading">
          <thead>
            <tr>
              <th scope="col">Area</th>
              <th scope="col">Declared</th>
              <th scope="col">Confirmed</th>
              <th scope="col">What is needed</th>
              <th scope="col">Next step</th>
            </tr>
          </thead>
          <tbody>
            <tr data-cold-readiness-row="definition">
              <th scope="row">Site definition</th>
              <td>
                {policy === null ? <Badge tone="config-gap">{NOT_CONFIGURED}</Badge> : <Badge tone="configured">{CONFIGURED}</Badge>}{" "}
                <span className="muted">
                  {read.rooms.length === 0 ? "No cold room" : `Cold room${read.rooms.length === 1 ? "" : "s"}`}
                  {policy === null ? "" : ` · ${policy} policy`}
                </span>
              </td>
              <td>{confirmed}</td>
              <td>{needed(definitionNeeds)}</td>
              <td>
                <Link to={props.viewHref("model")}>Site model →</Link>
              </td>
            </tr>
            {rows.map((row) => (
              <tr key={row.key} data-cold-readiness-row={row.key}>
                <th scope="row">{row.area}</th>
                <td>{row.declared}</td>
                <td>{confirmed}</td>
                <td>{row.needed}</td>
                <td>{row.next}</td>
              </tr>
            ))}
            {other.map((m) => (
              <tr key={`${m.code}|${m.role}|${m.component_id}`} data-cold-readiness-row="other">
                <th scope="row">{roleLabel(m.role)}</th>
                <td>
                  <SourceBadge configured={false} />
                </td>
                <td>{confirmed}</td>
                <td>{m.message}</td>
                <td>
                  <Link to={props.viewHref("sld")}>Single line diagram →</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </DataTable>
        <p className="v69-chart-note" data-cold-readiness-verdict={read.readiness.state}>
          {ready
            ? "Set up to report: every required reading has a configured source. This describes configuration only."
            : `Set-up incomplete: ${blocking.length} required item${blocking.length === 1 ? "" : "s"} need${blocking.length === 1 ? "s" : ""} attention before the site is set up to report.`}
        </p>
        <ExactReferences
          name="cold-readiness-references"
          variant="tech"
          references={[
            { label: "Set-up state (exact)", value: read.readiness.state },
            { label: "Commissioning state (exact)", value: read.commissioning.state },
            { label: "Commissioning records", value: read.commissioning.evidence_ids.length === 0 ? null : read.commissioning.evidence_ids.join(", ") },
            ...messages.map((m, i) => ({ label: `Message ${i + 1} code`, value: `${m.code}${m.asset_id === null ? "" : ` · asset ${m.asset_id}`}` })),
          ]}
        />
      </Panel>
      <Panel
        className="gw-panel"
        heading={`Gateway status · ${gateway}`}
        headingId="cold-gateway-heading"
        description="How site data reaches AssetOps: gateway contact only, not equipment condition"
        actions={<Link to={props.healthHref}>Health › Data sources →</Link>}
      >
        {health === null ? <p>{COLD_GATEWAY_LOADING}</p> : null}
        <MetricCards label="Gateway contact" data={{ "data-cold-gateway-metrics": "" }}>
          <MetricCard word label="Status" value={word.value} note={contactNote} tone={word.tone} data={{ "data-cold-gateway-metric": "status" }} />
          <MetricCard word tone="muted" label="Availability" value="Not available" note="No availability history is stored for this gateway" data={{ "data-cold-gateway-metric": "availability" }} />
          <MetricCard word tone="muted" label="Data completeness" value="Not available" note="Completeness needs accepted records, which this view does not read" data={{ "data-cold-gateway-metric": "completeness" }} />
          <MetricCard word tone="muted" label="Clock and delivery" value="Unknown" note="No gateway clock report is read here" data={{ "data-cold-gateway-metric": "clock" }} />
        </MetricCards>
        <p className="v69-chart-note" data-cold-contact-note="">
          Contact is checked now on the server clock, not at the selected time. It shows that diagnostics reach the server, never that equipment works.
          {limitations.length === 0 ? null : ` ${limitations.join(". ")}.`}
        </p>
        <div className="panel-pair">
          <Panel heading="Connected sources" headingId="cold-connected-sources-heading" description="Configured reading sources in the selected version">
            {read.bindings.length === 0 ? (
              <p className="v69-chart-note">No reading source is configured in this version.</p>
            ) : (
              <ul className="gw-sources" data-cold-sources="">
                {read.bindings.map((b) => (
                  <li className="gw-src" key={`${b.role}|${b.asset_id}`} data-cold-source={b.role}>
                    <span className="gw-dot gw-dot--none" aria-hidden="true" />
                    <strong>{roleLabel(b.role)}</strong> · {names.get(b.asset_id) ?? "Unnamed part"}
                  </li>
                ))}
              </ul>
            )}
            <p className="not-available-yet v69-chart-note" data-cold-source-contact="">
              {SOURCE_CONTACT_UNAVAILABLE}: no per-source contact is read for this site, so no source is shown as reporting.
            </p>
            <ExactReferences
              name="cold-source-references"
              variant="tech"
              references={read.bindings.map((b) => ({ label: `${roleLabel(b.role)} source`, value: `${b.source_id} · ${cadence(b)}` }))}
            />
          </Panel>
          <Panel heading="Effect on readiness and confidence" headingId="cold-effect-heading">
            <AttentionList
              label="Effect on readiness and confidence"
              items={[
                ...messages.map((m) => ({
                  key: `${m.code}|${m.role}|${m.component_id}`,
                  title: m.message,
                  body: m.blocking
                    ? "Blocks set-up to report until it is configured."
                    : "Does not block set-up; what it would show stays unknown.",
                })),
                {
                  key: "confidence",
                  title: CONFIDENCE_NOT_ASSESSED,
                  body: "What the records can support is judged on Site Evidence; configuration and contact alone cannot set it.",
                  action: <Link to={props.evidenceHref}>Site Evidence →</Link>,
                },
                {
                  key: "contact",
                  title: "Contact is not condition",
                  body: "Gateway contact proves no temperature, cooling or backup condition.",
                },
              ]}
            />
          </Panel>
        </div>
      </Panel>
      <p className="note">This view assesses configuration, commissioning and the gateway. What the records can support belongs to Site Evidence.</p>
    </>
  );
}

function cadence(binding: ColdBinding): string {
  return binding.cadence_seconds === null ? `${binding.publication_mode} · on change` : `${binding.publication_mode} · every ${binding.cadence_seconds} s`;
}

/* cold-sld ------------------------------------------------------------------ */

function SldView(props: ViewProps) {
  const { read, siteName } = props;
  const nodes = read.topology?.nodes ?? [];
  const byAsset = new Map<string, ColdBinding[]>();
  for (const b of read.bindings) byAsset.set(b.asset_id, [...(byAsset.get(b.asset_id) ?? []), b]);
  const undeclared = undeclaredParts(read);
  return (
    <>
      <ColdStrip
        {...props}
        lead={<Badge tone="neutral">Configured site</Badge>}
        action={<Link to={props.evidenceHref}>Site evidence →</Link>}
      />
      <Panel
        heading={siteName}
        headingId="cold-sld-heading"
        description="Topology type not stated in this version · configured equipment and declared connections; not live power flow"
        actions={<Link to={props.viewHref("readiness")}>Readiness →</Link>}
      >
        <p className="v69-chart-note" data-cold-sld-summary="">
          {nodes.length} part{nodes.length === 1 ? " is" : "s are"} drawn; {read.bindings.length} reading
          {read.bindings.length === 1 ? " has" : "s have"} a configured source. Whether any part is reporting is unknown here.
        </p>
        {read.topology === null || nodes.length === 0 ? (
          <p className="not-available-yet v69-chart-note" data-panel-gap="cold-sld-heading">
            No topology is declared in this version, so there is nothing to draw.
          </p>
        ) : (
          <ColdDiagram read={read} byAsset={byAsset} />
        )}
        <p className="not-available-yet v69-chart-note" data-cold-sld-undeclared="">
          {undeclared.length === 0 ? "Every cold-chain part is declared." : `Undeclared in this version: ${undeclared.join(", ")}.`} Live state is unknown: this is the
          configured site, not a live view.
        </p>
      </Panel>
      <Panel heading="What each part does" headingId="cold-sld-parts-heading">
        <DataTable labelledBy="cold-sld-parts-heading">
          <thead>
            <tr>
              <th scope="col">Part</th>
              <th scope="col">Role at this site</th>
              <th scope="col">What it reports</th>
            </tr>
          </thead>
          <tbody>
            {nodes.map((node) => {
              const readings = node.asset_id === null ? [] : (byAsset.get(node.asset_id) ?? []);
              return (
                <tr key={node.node_id} data-cold-part={node.component_id}>
                  <th scope="row">{node.display_name ?? node.component_id}</th>
                  <td>
                    {NODE_ROLE_WORD[node.node_role] ?? node.node_role} (configured)
                    <span className="muted"> · {FUNCTION_UNKNOWN}</span>
                  </td>
                  <td>
                    {readings.length === 0 ? (
                      <span className="muted">No reading configured</span>
                    ) : (
                      readings.map((b) => roleLabel(b.role)).join(" · ")
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </DataTable>
        <p className="v69-chart-note" data-cold-parts-note="">
          Roles come from the configuration only. What each part does in operation is not recorded, and no row is a reading or a state.
        </p>
        <ExactReferences
          name="cold-parts-references"
          variant="tech"
          references={[
            ...nodes.map((node) => ({ label: `${node.display_name ?? node.component_id} node`, value: `${node.node_id} · ${node.component_type}${node.asset_id === null ? "" : ` · asset ${node.asset_id}`}` })),
            ...(read.topology?.edges ?? []).map((e) => ({ label: `Connection ${e.connection_id}`, value: `${e.from_node} → ${e.to_node} · ${e.medium}` })),
          ]}
        />
      </Panel>
      <p className="note">This is the configured site, not a live view. Opening Readiness shows which readings still need a source.</p>
    </>
  );
}

/** Cold-chain parts the panel map expects that this version does not declare. */
export function undeclaredParts(read: ColdFoundationReadModel): string[] {
  const nodes = read.topology?.nodes ?? [];
  const has = (type: string) => nodes.some((n) => n.component_type === type);
  const out: string[] = [];
  if (!has("COLD_ROOM")) out.push("cold room");
  if (read.rooms.length > 0 && read.rooms.some((r) => r.probe_ids.length === 0)) out.push("chamber temperature probe");
  if (!has("COMPRESSOR")) out.push("compressor");
  if (!has("METER")) out.push("grid supply meter");
  if (!has("GENERATOR")) out.push("backup generator");
  if (!has("TRANSFER_SWITCH")) out.push("transfer switch");
  if (!has("AC_BUS")) out.push("power bus");
  if (!has("PV_ARRAY")) out.push("solar array");
  if (!has("BATTERY")) out.push("battery");
  return out;
}

/* The configured drawing: columns by connection depth, boxes per part, one line per declared connection. */

const BOX_W = 170;
const BOX_H = 74;
const COL_W = 204;
const ROW_H = 132;

function ColdDiagram({ read, byAsset }: { read: ColdFoundationReadModel; byAsset: Map<string, ColdBinding[]> }) {
  const layout = useMemo(() => diagramLayout(read.topology?.nodes ?? [], read.topology?.edges ?? []), [read]);
  const width = layout.columns * COL_W - (COL_W - BOX_W) + 16;
  const height = layout.rows * ROW_H - (ROW_H - BOX_H) + 16;
  const at = (id: string) => layout.position.get(id);
  return (
    <figure className="cold-sld" data-cold-diagram="">
      <div className="cold-sld__scroll" role="region" aria-label="Configured single line diagram" tabIndex={0}>
      <svg
        className="cold-sld__svg"
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={`Configured single line diagram: ${layout.nodes.length} parts and ${layout.edges.length} declared connections`}
      >
        {layout.edges.map((edge) => {
          const from = at(edge.from_node);
          const to = at(edge.to_node);
          if (from === undefined || to === undefined) return null;
          const x1 = from.x + BOX_W;
          const y1 = from.y + BOX_H / 2;
          const x2 = to.x;
          const y2 = to.y + BOX_H / 2;
          const mid = (x1 + x2) / 2;
          return (
            <path
              key={edge.connection_id}
              className={`cold-sld__edge cold-sld__edge--${edge.medium.toLowerCase()}`}
              d={`M ${x1} ${y1} H ${mid} V ${y2} H ${x2}`}
              data-cold-edge={edge.connection_id}
            >
              <title>{`${edge.from_node} to ${edge.to_node} (${MEDIUM_WORD[edge.medium] ?? edge.medium})`}</title>
            </path>
          );
        })}
        {layout.nodes.map((node) => {
          const p = at(node.node_id);
          if (p === undefined) return null;
          const readings = node.asset_id === null ? 0 : (byAsset.get(node.asset_id)?.length ?? 0);
          const name = node.display_name ?? node.component_id;
          return (
            <g key={node.node_id} transform={`translate(${p.x} ${p.y})`} data-cold-node={node.component_id}>
              <rect className={`cold-sld__box cold-sld__box--${family(node.node_role)}`} width={BOX_W} height={BOX_H} rx={6} />
              <text className="cold-sld__label" x={10} y={26}>
                {name.length > 24 ? `${name.slice(0, 23)}…` : name}
              </text>
              <text className="cold-sld__small" x={10} y={46}>
                {NODE_ROLE_WORD[node.node_role] ?? node.node_role}
              </text>
              <text className="cold-sld__small" x={10} y={63}>
                {readings === 0 ? "No reading configured" : `${readings} reading${readings === 1 ? "" : "s"} configured`}
              </text>
            </g>
          );
        })}
      </svg>
      </div>
      <figcaption className="cold-sld__legend">
        <span><span className="cold-sld__key cold-sld__key--ac" aria-hidden="true" />Power</span>
        <span><span className="cold-sld__key cold-sld__key--thermal" aria-hidden="true" />Cooling</span>
        <span><span className="cold-sld__key cold-sld__key--signal" aria-hidden="true" />Sensing</span>
      </figcaption>
    </figure>
  );
}

function family(role: string): string {
  if (role === "GENERATION" || role === "METERING") return "supply";
  if (role === "COLD_ROOM" || role === "COOLING") return "load";
  if (role === "SENSOR") return "sensor";
  return "network";
}

export function diagramLayout(nodes: ColdTopologyNode[], edges: { connection_id: string; from_node: string; to_node: string; medium: string }[]) {
  const depth = new Map(nodes.map((n) => [n.node_id, 0]));
  // Longest path from any source; the configuration is a directed acyclic graph, so this settles in |nodes| passes.
  for (let pass = 0; pass < nodes.length; pass += 1) {
    for (const edge of edges) {
      const from = depth.get(edge.from_node);
      const to = depth.get(edge.to_node);
      if (from !== undefined && to !== undefined && to < from + 1) depth.set(edge.to_node, from + 1);
    }
  }
  const columns = new Map<number, ColdTopologyNode[]>();
  for (const node of nodes) {
    const d = depth.get(node.node_id) ?? 0;
    columns.set(d, [...(columns.get(d) ?? []), node]);
  }
  const position = new Map<string, { x: number; y: number }>();
  let rows = 1;
  for (const [d, list] of columns) {
    rows = Math.max(rows, list.length);
    list.forEach((node, i) => position.set(node.node_id, { x: 8 + d * COL_W, y: 8 + i * ROW_H }));
  }
  // Centre each column on the tallest one, so a chain reads as one line across the drawing.
  for (const list of columns.values()) {
    const offset = ((rows - list.length) * ROW_H) / 2;
    for (const node of list) {
      const p = position.get(node.node_id);
      if (p !== undefined) p.y += offset;
    }
  }
  return { nodes, edges, position, columns: Math.max(1, columns.size === 0 ? 1 : Math.max(...columns.keys()) + 1), rows };
}
