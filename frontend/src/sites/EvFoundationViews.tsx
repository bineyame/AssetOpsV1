import { useCallback, useEffect, useState, type ReactNode } from "react";
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
import { UnavailableLinkEntry } from "../ui/UnavailableEntry";
import type { EvBinding, EvConnector, EvFoundationClient, EvFoundationRead, EvFoundationReadModel, EvReadinessMessage } from "./evFoundationClient";
import { FoundationSubtabs, foundationViewLabel, type FoundationView } from "./FoundationSubtabs";
import { formatInstant } from "./FoundationRevisionPanel";
import type { EvidenceRead } from "./evidenceRead";
import type { GatewayHealth, GatewayHealthClient } from "./gatewayHealthClient";
import type { FoundationVersionsReadModel } from "./siteFoundationClient";
import { EvSingleLineDiagram } from "./SiteSingleLineDiagram";
import { connectorName, LIMIT_NOT_DECLARED, NO_CONNECTOR_DECLARED, NOT_DECLARED } from "./evWords";
import { COMMISSIONING_RECORD, NOTHING_FURTHER_RECORDED } from "./ColdFoundationViews";
import "./w2-cold-foundation.css";
import "./w2-ev-foundation.css";

/*
 * W2-05a: the three Foundation views of an EV_CHARGING Site (`ev-foundation`, `ev-readiness`, `ev-sld`),
 * rendered from the selected EV Foundation read in the v69 panel slots (`.agent/W2-05a-build-spec.md`
 * "Three routes and fidelity proof"; `D-2026-10-17-mockup-layout-spec`). Configuration only: a configured
 * service window is not observed availability, gateway contact is not charger health, and a mapped status
 * channel is not proof of reporting.
 */

export { LIMIT_NOT_DECLARED, NO_CONNECTOR_DECLARED, NOT_DECLARED };
export const EV_FOUNDATION_LOADING = "Loading the site's EV configuration.";
export const EV_HEADING_ID = "ev-foundation-page-heading";
export const NO_GATEWAY_SELECTED = "No gateway selected";
export const GATEWAY_NOT_READ = "Gateway not read";
export const NEEDS_A_SOURCE = "Needs a source";
export const NO_GATEWAY_CONTACT = "No gateway contact recorded";
export const SOURCE_CONTACT_UNAVAILABLE = "Source contact unavailable";
export const COMMISSIONING_UNCONFIRMED = "Commissioning unconfirmed";
export const NOT_ASSESSED = "Not assessed";
export const FUNCTION_NOT_RECORDED = "Function not recorded";
export const NO_LIVE_FLOW = "Live power flow is not observed here";
export const NO_TARIFF = "No tariff set for estimates";
export const NOT_CONNECTED = "Not connected";
export const EMPTY_SELECTION = "No EV Foundation for this selection";
export const FORBIDDEN = "Source details are not available for this Site";
export const UNAVAILABLE = "EV Foundation is temporarily unavailable";
export const EV_TIMELINE_NO_HISTORY = "No history to draw";

/** Plain labels of the `ev-roles-1` roles (backend `sites/binding_roles.py`). */
const ROLE_LABEL: Record<string, string> = {
  ev_session_event: "Session events",
  ev_connector_fault: "Fault events",
  ev_connector_state: "Connector status",
  ev_connector_energy: "Energy metering",
  ev_connector_power: "Connector power",
  ev_site_import: "Site import power",
  ev_requested_power: "Requested power",
  ev_allocated_limit: "Allocated power limit",
};
export const evRoleLabel = (role: string | null): string => (role === null ? "Site" : (ROLE_LABEL[role] ?? role.replace(/_/g, " ")));

const WEEKDAY: Record<string, string> = {
  MONDAY: "Monday",
  TUESDAY: "Tuesday",
  WEDNESDAY: "Wednesday",
  THURSDAY: "Thursday",
  FRIDAY: "Friday",
  SATURDAY: "Saturday",
  SUNDAY: "Sunday",
};

/* Frame -------------------------------------------------------------------- */

export interface EvFoundationFrameProps {
  view: FoundationView;
  siteId: string;
  siteName: string;
  mode: string | null;
  selectedAt: string | null;
  onSelectAt: (at: string | null) => void;
  client: EvFoundationClient;
  gatewayHealth?: GatewayHealthClient;
  versions: FoundationVersionsReadModel | null;
  viewHref: (target: FoundationView) => string;
  evidenceHref: string;
  healthHref: string;
  financialsHref: string;
  assumptionsHref: string;
  tabs: ReactNode;
  parentTrail: Crumb[];
}

const DESCRIPTION: Record<FoundationView, string> = {
  model: SITE_SCREEN_DESCRIPTIONS["ev-foundation"],
  readiness: SITE_SCREEN_DESCRIPTIONS["ev-readiness"],
  sld: SITE_SCREEN_DESCRIPTIONS["ev-sld"],
};

export function EvFoundationFrame(props: EvFoundationFrameProps) {
  const { view, siteId, siteName, selectedAt, client, gatewayHealth } = props;
  const [read, setRead] = useState<{ key: string; value: EvFoundationRead } | null>(null);
  const [attempt, setAttempt] = useState(0);
  const key = `${siteId}|${selectedAt ?? ""}|${attempt}`;
  useEffect(() => {
    let active = true;
    void client.getEvFoundation(siteId, selectedAt).then((value) => {
      if (active) setRead({ key, value });
    });
    return () => {
      active = false;
    };
  }, [client, siteId, selectedAt, key]);
  const retry = useCallback(() => setAttempt((n) => n + 1), []);

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
  const trail: Crumb[] =
    view === "model"
      ? [...props.parentTrail, { label: "Foundation" }]
      : [...props.parentTrail, { label: "Foundation", to: props.viewHref("model") }, { label: foundationViewLabel(view) }];

  return (
    <main aria-labelledby={EV_HEADING_ID} data-ev-foundation-view={view}>
      <Breadcrumbs trail={trail} />
      <SitePageHeader siteName={siteName} siteId={siteId} mode={props.mode} description={DESCRIPTION[view]} headingId={EV_HEADING_ID} />
      {props.tabs}
      <FoundationSubtabs current={view} hrefFor={props.viewHref} withChanges={false} />
      {current === null ? (
        <p>{EV_FOUNDATION_LOADING}</p>
      ) : current.status === "loaded" ? (
        <EvViews {...props} read={current.value} health={health} gateway={gatewayName(current.value, health)} />
      ) : (
        <EvRefusal {...props} read={current} onRetry={retry} />
      )}
    </main>
  );
}

/** The selected gateway's registered name from the health read, matched by the EV read's selected gateway. */
function gatewayName(read: EvFoundationReadModel, health: EvidenceRead<GatewayHealth> | null): string {
  if (read.contact.gateway_id === null) return NO_GATEWAY_SELECTED;
  if (health !== null && health.status === "loaded") {
    const match = health.value.gateways.find((g) => g.gateway_id === read.contact.gateway_id);
    if (match !== undefined) return match.gateway_external_id;
  }
  return GATEWAY_NOT_READ;
}

/* Empty, refused or unavailable read: the page-level state, then every slot with its gap. */

type RefusalKind = "empty" | "forbidden" | "unavailable";

function refusalKind(read: Exclude<EvFoundationRead, { status: "loaded" }>): RefusalKind {
  if (read.status === "refused" && read.code === "FOUNDATION_REVISION_NOT_FOUND") return "empty";
  if (read.status === "refused" && read.httpStatus === 403) return "forbidden";
  return "unavailable";
}

function EvRefusal(props: EvFoundationFrameProps & { read: Exclude<EvFoundationRead, { status: "loaded" }>; onRetry: () => void }) {
  const kind = refusalKind(props.read);
  const title = kind === "empty" ? EMPTY_SELECTION : kind === "forbidden" ? FORBIDDEN : UNAVAILABLE;
  const gap =
    kind === "empty"
      ? `${EMPTY_SELECTION}, so nothing is shown as configured in this panel.`
      : kind === "forbidden"
        ? `${FORBIDDEN}, so this panel shows no configuration.`
        : `${UNAVAILABLE}, so nothing is shown as configured in this panel. This is not an empty configuration.`;
  return (
    <>
      <div className="page-refusal" role="status" data-page-refusal={kind}>
        <p className="page-refusal__title">
          <strong>{title}</strong>
        </p>
        {kind === "empty" ? (
          <p>{`No EV configuration of this site is in effect at ${formatInstant(props.selectedAt)}. The configuration in effect now is not shown in its place.`}</p>
        ) : kind === "unavailable" ? (
          <p>The site's EV configuration could not be read. Nothing is shown as configured until it can be.</p>
        ) : null}
        {kind === "empty" && props.selectedAt !== null ? (
          <button type="button" className="button primary" onClick={() => props.onSelectAt(null)}>
            Show the version in effect now
          </button>
        ) : null}
        {kind === "unavailable" ? (
          <button type="button" className="button primary" onClick={props.onRetry}>
            Try again
          </button>
        ) : null}
        {kind === "forbidden" ? null : (
          <ExactReferences
            name="ev-refusal-references"
            variant="tech"
            references={[
              { label: "Refusal code", value: props.read.status === "refused" ? props.read.code : null },
              { label: "Selected time (exact)", value: props.selectedAt },
            ]}
          />
        )}
      </div>
      <EvSkeletons view={props.view} siteName={props.siteName} gateway={GATEWAY_NOT_READ} gap={gap} />
    </>
  );
}

export function EvSkeletons({ view, siteName, gateway, gap }: { view: FoundationView; siteName: string; gateway: string; gap: string }) {
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
        {slot("Physical site", "ev-physical-site-heading")}
        {slot("Operating interpretation", "ev-operating-heading")}
      </div>
    );
  }
  if (view === "sld") {
    return (
      <>
        {slot(siteName, "ev-sld-heading")}
        {slot("What each part does", "ev-sld-parts-heading")}
      </>
    );
  }
  return (
    <>
      {slot("Readiness and commissioning evidence", "ev-readiness-table-heading")}
      <Panel className="gw-panel" heading={`Gateway status · ${gateway}`} headingId="ev-gateway-heading">
        <p className="not-available-yet v69-chart-note" data-panel-gap="ev-gateway-heading">
          {gap}
        </p>
        <div className="panel-pair">
          {slot("Connected sources", "ev-connected-sources-heading")}
          {slot("Effect on readiness and confidence", "ev-effect-heading")}
        </div>
      </Panel>
    </>
  );
}

/* Loaded: shared helpers ------------------------------------------------------ */

interface ViewProps extends EvFoundationFrameProps {
  read: EvFoundationReadModel;
  health: EvidenceRead<GatewayHealth> | null;
  gateway: string;
}

function EvViews(props: ViewProps) {
  if (props.view === "model") return <EvModelView {...props} />;
  if (props.view === "sld") return <EvSldView {...props} />;
  return <EvReadinessView {...props} />;
}

/** asset_id -> the declared part name (the topology's display name). */
function partNames(read: EvFoundationReadModel): Map<string, string> {
  const names = new Map<string, string>();
  for (const node of read.topology?.nodes ?? []) {
    if (node.asset_id !== null) names.set(node.asset_id, node.display_name ?? node.component_id);
  }
  return names;
}

const allConnectors = (read: EvFoundationReadModel): EvConnector[] => read.chargers.flatMap((c) => c.connectors);

/** Declared connectors that have a binding of `role`, and how many are declared. */
function roleCoverage(read: EvFoundationReadModel, role: string): { bound: number; total: number } {
  const connectors = allConnectors(read);
  const assets = new Set(read.bindings.filter((b) => b.role === role).map((b) => b.asset_id));
  return { bound: connectors.filter((c) => c.asset_id !== null && assets.has(c.asset_id)).length, total: connectors.length };
}

const fullyBound = (read: EvFoundationReadModel, role: string) => {
  const { bound, total } = roleCoverage(read, role);
  return total > 0 && bound === total;
};

function ratingsText(read: EvFoundationReadModel): string | null {
  const connectors = allConnectors(read);
  if (connectors.length === 0) return null;
  const counts = new Map<string, number>();
  for (const c of connectors) {
    const rating = c.max_kw === null ? "rating not declared" : `${c.max_kw} kW`;
    counts.set(rating, (counts.get(rating) ?? 0) + 1);
  }
  return Array.from(counts.entries())
    .map(([rating, n]) => `${n} × ${rating}`)
    .join(", ");
}

function scheduleText(connector: EvConnector): string {
  const s = connector.enabled_schedule;
  if (!s.enabled) return "disabled";
  if (s.weekly.length === 0) return "no service hours configured";
  const hours = s.weekly.map((w) => `${WEEKDAY[w.weekday] ?? w.weekday} ${w.local_start}–${w.local_end}`).join(", ");
  return s.time_zone === null ? hours : `${hours} (${s.time_zone})`;
}

/** One line for every connector's configured service hours; per connector when they differ. */
function schedulesText(read: EvFoundationReadModel, names: Map<string, string>): string | null {
  const connectors = allConnectors(read);
  if (connectors.length === 0) return null;
  const texts = connectors.map(scheduleText);
  if (new Set(texts).size === 1) return texts[0] ?? null;
  return connectors.map((c, i) => `${connectorName(c, names, i)}: ${texts[i]}`).join("; ");
}

/** The configured clock error bound, per connector when the values differ (QI); configuration, not observed sync. */
function clockBoundText(read: EvFoundationReadModel, names: Map<string, string>): string | null {
  const connectors = allConnectors(read);
  const values = connectors.map((c) => c.clock_error_bound_seconds);
  if (values.length === 0 || values.every((v) => v === null)) return null;
  if (new Set(values).size === 1) return `Configured clock error bound: ${values[0]} s`;
  return `Configured clock error bound: ${connectors
    .map((c, i) => `${connectorName(c, names, i)} ${values[i] === null ? NOT_DECLARED.toLowerCase() : `${values[i]} s`}`)
    .join(", ")}`;
}

/** A readiness message in plain words: the missing role and part, never the backend text or code. */
function needText(m: EvReadinessMessage, names: Map<string, string>): string {
  const part = m.asset_id === null ? null : (names.get(m.asset_id) ?? "a declared connector");
  switch (m.code) {
    case "CONNECTOR_NOT_DECLARED":
      return NO_CONNECTOR_DECLARED;
    case "FEED_OR_LIMIT_MISSING":
      return m.asset_id === null ? "No site feed declared" : LIMIT_NOT_DECLARED;
    case "METER_NOT_BOUND":
    case "SESSION_EVENTS_NOT_BOUND":
    case "STATUS_NOT_BOUND":
      return `${NEEDS_A_SOURCE}: ${evRoleLabel(m.role).toLowerCase()} for ${part ?? "a declared connector"}`;
    case "SITE_IMPORT_NOT_BOUND":
      return `${NEEDS_A_SOURCE}: site import power (optional); site power comparison is unavailable`;
    case "SOURCE_NOT_CONTACTED":
      return NO_GATEWAY_CONTACT;
    case "COMMISSIONING_UNCONFIRMED":
      return COMMISSIONING_UNCONFIRMED;
    default:
      return NEEDS_A_SOURCE;
  }
}

/** The mock's one-line status bar: lead, the selected version and period, then the period selector. */
function EvStrip(props: ViewProps & { lead: ReactNode; text?: string; action: ReactNode }) {
  const { read, versions, selectedAt } = props;
  const revision = versions?.revisions.find((r) => r.revision_id === read.foundation_revision_id) ?? null;
  const periods = (versions?.revisions ?? [])
    .filter((r) => r.recorded_state === "CURRENT")
    .sort((a, b) => a.valid_from.localeCompare(b.valid_from));
  const inList = selectedAt !== null && periods.some((r) => r.valid_from === selectedAt);
  return (
    <div className="status-strip status-strip--line" role="group" aria-label="Foundation version" data-ev-strip="">
      {props.lead === null ? null : <span className="status-strip__lead">{props.lead}</span>}
      <span className="status-strip__item">
        <Badge tone="neutral">{revision === null ? "Stored configuration" : `Configuration v${revision.version}`}</Badge>{" "}
        <span>
          {revision === null
            ? `Selected ${formatInstant(read.selected_at)}`
            : `Effective ${formatInstant(revision.valid_from)} to ${revision.valid_to === null ? "no end date" : formatInstant(revision.valid_to)}`}
        </span>
      </span>
      {props.text === undefined ? null : <span className="status-strip__state">{props.text}</span>}
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
        name="ev-strip-references"
        variant="tech"
        references={[
          { label: "Selected time (exact)", value: read.selected_at },
          { label: "Foundation version record", value: read.foundation_revision_id },
          { label: "Reading-source version record", value: read.binding_revision_id },
        ]}
      />
    </div>
  );
}

/* ev-foundation --------------------------------------------------------------- */

function EvModelView(props: ViewProps) {
  const { read } = props;
  const names = partNames(read);
  const connectors = allConnectors(read);
  const ratings = ratingsText(read);
  const schedules = schedulesText(read, names);
  const session = roleCoverage(read, "ev_session_event");
  const nodes = read.topology?.nodes ?? [];
  const feedName = read.feed.asset_id === null ? null : (names.get(read.feed.asset_id) ?? "Site feed");
  const meterName = read.feed.meter_asset_id === null ? null : (names.get(read.feed.meter_asset_id) ?? "Import meter");
  const chargerText = read.chargers
    .map((c, i) => `${(c.asset_id === null ? undefined : names.get(c.asset_id)) ?? `Charger ${i + 1}`} ${c.max_kw === null ? "(rating not declared)" : `${c.max_kw} kW`}`)
    .join(", ");
  const edges = read.topology?.edges.length ?? 0;
  const clock = clockBoundText(read, names);
  const blocking = read.readiness.messages.filter((m) => m.blocking).length;
  return (
    <>
      <EvStrip {...props} lead={null} action={<Link to={props.viewHref("readiness")}>Configuration readiness →</Link>} />
      <div className="panel-pair panel-pair--equal">
        <Panel heading="Physical site" headingId="ev-physical-site-heading">
          <KeyValues
            label="Physical site"
            rows={[
              ["Site ID", read.site_code],
              ["Connectors", ratings === null ? NO_CONNECTOR_DECLARED : ratings],
              ["Site import limit", read.feed.limit_kw === null ? LIMIT_NOT_DECLARED : `${read.feed.limit_kw} kW`],
              ["Stationary storage", NOT_DECLARED],
              [
                "Session source",
                session.bound === 0
                  ? NEEDS_A_SOURCE
                  : `Charger session events · ${session.bound} of ${session.total} connector${session.total === 1 ? "" : "s"}`,
              ],
            ]}
          />
          <p className="v69-chart-note" data-ev-physical-detail="">
            {feedName === null ? "Site feed not declared" : `${feedName}`}
            {" → "}
            {meterName === null ? "import meter not declared" : meterName}
            {" → "}
            {chargerText === "" ? "no charger declared" : chargerText}
            {connectors.length === 0 ? "" : ` → ${connectors.length} connector${connectors.length === 1 ? "" : "s"}`}
            {` · ${edges} declared connection${edges === 1 ? "" : "s"}.`}
            {schedules === null ? "" : ` Configured service hours: ${schedules}; a service window is not observed availability.`}
          </p>
          <ExactReferences
            name="ev-physical-references"
            variant="tech"
            references={[
              { label: "Foundation version record", value: read.foundation_revision_id },
              { label: "Site feed asset", value: read.feed.asset_id },
              { label: "Import meter asset", value: read.feed.meter_asset_id },
              ...nodes.map((n) => ({ label: `${n.display_name ?? n.component_id} part`, value: `${n.component_type}${n.asset_id === null ? "" : ` · asset ${n.asset_id}`}` })),
            ]}
          />
        </Panel>
        <Panel heading="Operating interpretation" headingId="ev-operating-heading">
          <KeyValues
            label="Operating interpretation"
            rows={[
              ["Session identity mapping", fullyBound(read, "ev_session_event") ? <Badge key="s" tone="configured">Configured</Badge> : <Badge key="s" tone="config-gap">{NEEDS_A_SOURCE}</Badge>],
              ["Transaction completeness", <span key="t" className="muted">{NOT_ASSESSED}</span>],
              [
                "Connector status",
                <span key="c">
                  {fullyBound(read, "ev_connector_state") ? <Badge tone="configured">Mapped</Badge> : <Badge tone="config-gap">{NEEDS_A_SOURCE}</Badge>}
                  {clock === null ? null : <span className="cold-readiness__detail muted">{`${clock}; not an observed clock check`}</span>}
                </span>,
              ],
              ["Revenue assumption", NO_TARIFF],
            ]}
          />
          <p className="v69-chart-note" data-ev-operating-note="">
            {blocking === 0
              ? "Every required connector reading has a configured source."
              : `${blocking} required item${blocking === 1 ? "" : "s"} still need${blocking === 1 ? "s" : ""} set-up; see Readiness.`}{" "}
            Declared limits: site import {read.feed.limit_kw === null ? "not declared" : `${read.feed.limit_kw} kW`}
            {chargerText === "" ? "" : `, ${chargerText}`}
            {ratings === null ? "" : `, connectors ${ratings}`}. A configured setting is not proof of energy delivered or charging status.
          </p>
        </Panel>
      </div>
      <p className="note">Configuration changes create a new effective version. A changed setting is not proof of an operational effect.</p>
    </>
  );
}

/* ev-readiness ---------------------------------------------------------------- */

/** Row 1 (Connectors and site limit): connector, Site feed, import meter and limit gaps. Every other gap is row 2 detail. */
const CONNECTOR_AREA_CODES = new Set(["CONNECTOR_NOT_DECLARED", "FEED_OR_LIMIT_MISSING", "METER_NOT_BOUND", "SITE_IMPORT_NOT_BOUND"]);
/** Notices shown in their own slots (gateway status, Confirmed column), not as table rows. */
const NOTICE_CODES = new Set(["SOURCE_NOT_CONTACTED", "COMMISSIONING_UNCONFIRMED"]);

function EvReadinessView(props: ViewProps) {
  const { read, health } = props;
  const names = partNames(read);
  const messages = read.readiness.messages;
  const ready = read.readiness.state === "READY_TO_REPORT";
  const ratings = ratingsText(read);
  const unconfirmed = read.commissioning.evidence_ids.length === 0;
  const confirmed = <Badge tone="neutral">{unconfirmed ? "Unconfirmed" : `${read.commissioning.evidence_ids.length} records`}</Badge>;
  // W2-F M2/N3: the selected readiness messages first (deduped), then `Commissioning record` while no commissioning
  // evidence is stored; `Nothing further recorded` only for a configured row with nothing left to record.
  const needed = (items: string[], configured: boolean) => {
    const list = Array.from(new Set([...items, ...(unconfirmed ? [COMMISSIONING_RECORD] : [])]));
    if (list.length === 0) return configured ? NOTHING_FURTHER_RECORDED : "—";
    return (
      <ul className="plain-list">
        {list.map((text) => (
          <li key={text}>{text}</li>
        ))}
      </ul>
    );
  };
  const connectorNeeds = messages.filter((m) => CONNECTOR_AREA_CODES.has(m.code)).map((m) => needText(m, names));
  const statusNeeds = messages.filter((m) => !CONNECTOR_AREA_CODES.has(m.code) && !NOTICE_CODES.has(m.code)).map((m) => needText(m, names));
  const statusMapped = fullyBound(read, "ev_connector_state");

  const contact = read.contact;
  const contactWord =
    contact.state === "RECENT" ? "Recent contact" : contact.state === "STALE" ? "Stale contact" : NO_GATEWAY_CONTACT;
  const checked = contact.checked_at === null ? "Contact check time not recorded" : `Contact checked ${formatInstant(contact.checked_at)}`;
  const contactNote = contact.as_of === null ? checked : `Last contact ${formatInstant(contact.as_of)} · ${checked}`;
  const clock = clockBoundText(read, names);
  const notContacted = messages.some((m) => m.code === "SOURCE_NOT_CONTACTED");

  return (
    <>
      <EvStrip
        {...props}
        lead={ready ? <Badge tone="configured">Set up to report</Badge> : <Badge tone="config-gap">Set-up incomplete</Badge>}
        text="Configuration readiness is separate from what the records can support."
        action={<Link to={props.viewHref("sld")}>Single line diagram →</Link>}
      />
      <Panel className="cold-readiness-panel" heading="Readiness and commissioning evidence" headingId="ev-readiness-table-heading">
        <DataTable labelledBy="ev-readiness-table-heading">
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
            <tr data-ev-readiness-row="connectors">
              <th scope="row">Connectors and site limit</th>
              <td>
                {ratings === null ? NO_CONNECTOR_DECLARED : ratings}
                {" · "}
                {read.feed.limit_kw === null ? LIMIT_NOT_DECLARED : `${read.feed.limit_kw} kW`}
              </td>
              <td>{confirmed}</td>
              <td>{needed(connectorNeeds, ratings !== null && read.feed.limit_kw !== null)}</td>
              <td>
                <Link to={props.viewHref("model")}>Site model →</Link>
              </td>
            </tr>
            <tr data-ev-readiness-row="status">
              <th scope="row">Connector status points</th>
              <td>{statusMapped ? <Badge tone="configured">Mapped</Badge> : <Badge tone="config-gap">{NEEDS_A_SOURCE}</Badge>}</td>
              <td>{confirmed}</td>
              <td>{needed(statusNeeds, statusMapped)}</td>
              <td>
                <Link to={props.evidenceHref}>Evidence →</Link>
              </td>
            </tr>
            <tr data-ev-readiness-row="billing">
              <th scope="row">Billing integration</th>
              <td>{NOT_CONNECTED}</td>
              <td>
                <Badge tone="neutral">{NOT_CONNECTED}</Badge>
              </td>
              <td>Payment records feed</td>
              <td>
                <UnavailableLinkEntry label="Financials" />
              </td>
            </tr>
            <tr data-ev-readiness-row="tariff">
              <th scope="row">Tariff</th>
              <td>{NO_TARIFF}</td>
              <td>
                <Badge tone="neutral">{NOT_ASSESSED}</Badge>
              </td>
              <td>Confirmed tariff</td>
              <td>
                <UnavailableLinkEntry label="Assumptions" />
              </td>
            </tr>
          </tbody>
        </DataTable>
        <p className="v69-chart-note" data-ev-commissioning="">
          {unconfirmed ? `${COMMISSIONING_UNCONFIRMED}: no commissioning record is stored, so nothing is confirmed.` : "Commissioning records are stored."}{" "}
          Billing and tariff are not read here.
        </p>
        <ExactReferences
          name="ev-readiness-references"
          variant="tech"
          references={[
            { label: "Set-up state (exact)", value: read.readiness.state },
            { label: "Commissioning state (exact)", value: read.commissioning.state },
            ...messages.map((m, i) => ({ label: `Message ${i + 1} code`, value: `${m.code}${m.asset_id === null ? "" : ` · asset ${m.asset_id}`}` })),
          ]}
        />
      </Panel>
      <Panel
        className="gw-panel"
        heading={`Gateway status · ${props.gateway}`}
        headingId="ev-gateway-heading"
        description={`How site data reaches AssetOps · configuration selected ${formatInstant(read.selected_at)} · gateway contact only, not charger health`}
        actions={<UnavailableLinkEntry label="Health › Data sources" />}
      >
        {health === null ? <p>Loading the site's gateway contact.</p> : null}
        <MetricCards label="Gateway contact" data={{ "data-ev-gateway-metrics": "" }}>
          <MetricCard word label="Status" value={contactWord} note={contactNote} tone={contact.state === "RECENT" ? undefined : "muted"} data={{ "data-ev-gateway-metric": "status" }} />
          <MetricCard word tone="muted" label="Availability" value={NOT_ASSESSED} note="No availability history is read here" data={{ "data-ev-gateway-metric": "availability" }} />
          <MetricCard word tone="muted" label="Data completeness" value={NOT_ASSESSED} note="Expected, received and late reading counts are not read here" data={{ "data-ev-gateway-metric": "completeness" }} />
          <MetricCard
            word
            tone="muted"
            label="Clock and delivery"
            value={NOT_ASSESSED}
            note={`${clock === null ? "No clock error bound configured" : clock} · observed sync and delivery speed not assessed`}
            data={{ "data-ev-gateway-metric": "clock" }}
          />
        </MetricCards>
        <div className="cold-gw-timeline" data-ev-gateway-timeline="">
          <div className="cold-gw-track" role="img" aria-label="Gateway availability timeline: no history to draw">
            <span data-ev-timeline-gap="">{EV_TIMELINE_NO_HISTORY}</span>
          </div>
          <div className="cold-gw-legend">
            <span><span className="cold-gw-key cold-gw-key--up" aria-hidden="true" />Online</span>
            <span><span className="cold-gw-key cold-gw-key--part" aria-hidden="true" />Short outage or missing readings</span>
            <span><span className="cold-gw-key cold-gw-key--down" aria-hidden="true" />Offline 1 h or more</span>
            <span><span className="cold-gw-key" aria-hidden="true" />No history</span>
          </div>
        </div>
        <p className="v69-chart-note" data-ev-contact-note="">
          {contact.state === "STALE"
            ? "Gateway contact is stale: the last diagnostic is older than its expected cadence. That is not a charger failure."
            : notContacted
              ? `${NO_GATEWAY_CONTACT}. This does not block set-up to report.`
              : "Gateway diagnostics reach the server."}{" "}
          Contact is checked at request time on the server clock, separately from the selected configuration time.
        </p>
        <div className="panel-pair">
          <Panel heading="Connected sources" headingId="ev-connected-sources-heading">
            <p className="v69-chart-note" data-ev-gateway-identity="">
              Gateway identity · connection not recorded · firmware {NOT_ASSESSED.toLowerCase()} · point list version {NOT_ASSESSED.toLowerCase()}
            </p>
            <ul className="gw-sources" data-ev-sources="">
              {read.bindings.map((b) => (
                <li className="gw-src" key={`${b.role}|${b.asset_id}|${b.device_id}|${b.signal_id}`} data-ev-source={b.role}>
                  <span className="gw-dot gw-dot--none" aria-hidden="true" />
                  <strong>{evRoleLabel(b.role)}</strong> · {(b.asset_id === null ? undefined : names.get(b.asset_id)) ?? "Unnamed part"}
                </li>
              ))}
              <li className="gw-src" data-ev-source="billing">
                <span className="gw-dot gw-dot--none" aria-hidden="true" />
                <strong>Billing system</strong> · {NOT_CONNECTED}
              </li>
            </ul>
            {read.bindings.length === 0 ? <p className="v69-chart-note">No reading source is configured in this version.</p> : null}
            <p className="not-available-yet v69-chart-note" data-ev-source-contact="">
              {SOURCE_CONTACT_UNAVAILABLE}: no per-source contact is read, so no source is shown as reporting.
            </p>
            <div className="v69-chart-note">
              <Link to={props.viewHref("sld")}>Single line diagram →</Link> <UnavailableLinkEntry label="Health › Data sources" />
            </div>
            <ExactReferences
              name="ev-source-references"
              variant="tech"
              references={read.bindings.map((b) => ({ label: `${evRoleLabel(b.role)} source`, value: `${b.device_id} · ${b.signal_id} · ${cadence(b)} · ${b.source_id}` }))}
            />
          </Panel>
          <Panel heading="Effect on readiness and confidence" headingId="ev-effect-heading">
            <AttentionList
              label="Effect on readiness and confidence"
              items={[
                {
                  key: "status-history",
                  title: `Connector status history: ${NOT_ASSESSED}`,
                  body: `Whether status reports arrived from each connector needs accepted records, which this view does not read. Gateway contact is not charger health.`,
                  action: <Link to={props.evidenceHref}>Site Evidence →</Link>,
                },
                {
                  key: "session-records",
                  title: `Session records: ${NOT_ASSESSED}`,
                  body: "Whether each session has its start and end records needs an accepted session assessment, which this view does not read.",
                  action: (
                    <>
                      <Link to={props.evidenceHref}>Site Evidence →</Link>
                      <UnavailableLinkEntry label="Investigation action" />
                    </>
                  ),
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

function cadence(binding: EvBinding): string {
  return binding.cadence_seconds === null ? "on event" : `at most every ${binding.cadence_seconds} s`;
}

/* ev-sld ---------------------------------------------------------------------- */

function EvSldView(props: ViewProps) {
  const { read, siteName } = props;
  const names = partNames(read);
  const rolesFor = (assetId: string | null) => (assetId === null ? [] : read.bindings.filter((b) => b.asset_id === assetId));
  const mapped = (assetId: string | null) => {
    const roles = Array.from(new Set(rolesFor(assetId).map((b) => evRoleLabel(b.role).toLowerCase())));
    return roles.length === 0 ? NOT_DECLARED : `Mapped: ${roles.join(", ")}`;
  };
  const roleCount = (charger: EvCharger) =>
    new Set([charger.asset_id, ...charger.connectors.map((c) => c.asset_id)].flatMap((id) => rolesFor(id).map((b) => b.role))).size;
  const clockBound = (c: EvConnector) => {
    const v = c.clock_error_bound_seconds;
    return v === null ? NOT_DECLARED.toLowerCase() : `${v} s`;
  };
  const feedName = read.feed.asset_id === null ? null : (names.get(read.feed.asset_id) ?? "Site feed");
  const siteImport = read.bindings.filter((b) => b.role === "ev_site_import");
  const nodes = read.topology?.nodes ?? [];
  return (
    <>
      <EvStrip
        {...props}
        lead={<Badge tone="neutral">Configured site</Badge>}
        text="Single line diagram · what is connected to what"
        action={<Link to={props.evidenceHref}>Site evidence →</Link>}
      />
      <Panel
        heading={siteName}
        headingId="ev-sld-heading"
        description={`Topology type not stated in this version · configured equipment, protection and metering · ${NO_LIVE_FLOW}`}
      >
        <EvSingleLineDiagram read={read} names={names} />
      </Panel>
      <Panel heading="What each part does" headingId="ev-sld-parts-heading">
        <DataTable labelledBy="ev-sld-parts-heading">
          <thead>
            <tr>
              <th scope="col">Part</th>
              <th scope="col">Role at this site</th>
              <th scope="col">What it reports</th>
            </tr>
          </thead>
          <tbody>
            <tr data-ev-part="feed">
              <th scope="row">Grid supply + load manager</th>
              <td>
                {`${feedName === null ? `Grid supply · ${NOT_DECLARED}` : `${feedName} · ${read.feed.limit_kw === null ? LIMIT_NOT_DECLARED : `Site import limit ${read.feed.limit_kw} kW`}`}; Load manager · ${NOT_DECLARED}`}
              </td>
              <td>{siteImport.length === 0 ? NOT_DECLARED : "Mapped: site import power"}</td>
            </tr>
            {[0, 1].map((slot) => (
              <ChargerRow key={slot} slot={slot} chargers={slot === 1 ? read.chargers.slice(1) : read.chargers.slice(0, 1)} names={names} roleCount={roleCount} mapped={mapped} clockBound={clockBound} />
            ))}
            <tr data-ev-part="auxiliary">
              <th scope="row">Depot auxiliary</th>
              <td>{NOT_DECLARED}</td>
              <td>{NOT_DECLARED}</td>
            </tr>
          </tbody>
        </DataTable>
        <p className="v69-chart-note" data-ev-parts-note="">
          A mapped channel is configuration, not proof of reporting; configured service hours never mark a part as reporting.
        </p>
        <ExactReferences
          name="ev-parts-references"
          variant="tech"
          references={[
            ...nodes.map((node) => ({ label: `${node.display_name ?? node.component_id} node`, value: `${node.node_id} · ${node.component_type}${node.asset_id === null ? "" : ` · asset ${node.asset_id}`}` })),
            ...(read.topology?.edges ?? []).map((e) => ({ label: `Connection ${e.connection_id}`, value: `${e.from_node} → ${e.to_node} · ${e.medium}` })),
          ]}
        />
      </Panel>
      <p className="note">
        This is the configured site, not a live view. Ratings come from the site model; reporting dots stay unknown because no accepted evidence is read here. Configured
        service hours are not observed availability.
      </p>
    </>
  );
}

type EvCharger = EvFoundationReadModel["chargers"][number];

/** The closed-state schedule word for a charger's connectors. */
function scheduleState(connectors: EvConnector[]): string {
  if (connectors.length === 0) return "no schedule declared";
  const states = new Set(connectors.map((c) => (!c.enabled_schedule.enabled ? "disabled" : c.enabled_schedule.weekly.length === 0 ? "no service hours" : "service hours set")));
  return states.size === 1 ? Array.from(states)[0]! : "mixed schedules";
}

/**
 * One of the mock's two charger rows. Closed, each charger is two lines (name and rating; connector count, schedule state and
 * mapped role count); every connector's name, rating, schedule, clock bound and mapped roles sit in a closed in-cell disclosure.
 * More than two chargers: the second row says how many additional chargers there are and its disclosure lists them all.
 */
function ChargerRow({ slot, chargers, names, roleCount, mapped, clockBound }: { slot: number; chargers: EvFoundationReadModel["chargers"]; names: Map<string, string>; roleCount: (c: EvCharger) => number; mapped: (id: string | null) => string; clockBound: (c: EvConnector) => string }) {
  const label = (charger: EvCharger | undefined, k: number) =>
    charger === undefined ? `Charger ${slot + 1}` : ((charger.asset_id === null ? undefined : names.get(charger.asset_id)) ?? `Charger ${slot + k + 1}`);
  if (chargers.length === 0) {
    return (
      <tr data-ev-part="charger">
        <th scope="row">{`${label(undefined, 0)} · ${NOT_DECLARED}`}</th>
        <td>{NOT_DECLARED}</td>
        <td>{NOT_DECLARED}</td>
      </tr>
    );
  }
  const lead = chargers[0]!;
  const extra = slot === 1 && chargers.length > 1;
  const rolesTotal = chargers.reduce((n, c) => n + roleCount(c), 0);
  const count = (n: number, noun: string) => `${n} ${noun}${n === 1 ? "" : "s"}`;
  return (
    <tr data-ev-part="charger">
      <th scope="row">{label(lead, 0)}</th>
      <td>
        {extra ? (
          <div data-ev-charger-summary="">{count(chargers.length, "additional charger")}</div>
        ) : (
          <>
            <div data-ev-charger-summary="">{`${label(lead, 0)} · ${lead.max_kw === null ? "Rating not declared" : `${lead.max_kw} kW`}`}</div>
            <div className="muted">
              {`${count(lead.connectors.length, "connector")} · ${scheduleState(lead.connectors)} · ${rolesTotal === 0 ? "No mapped source roles" : count(rolesTotal, "mapped source role")}`}
            </div>
          </>
        )}
        <details className="ev-connector-details" data-ev-connector-details="">
          <summary>Connector details</summary>
          {chargers.map((charger, k) => (
            <div key={charger.asset_id ?? k} data-ev-charger-detail="">
              {extra || chargers.length > 1 ? <strong>{`${label(charger, k)} · ${charger.max_kw === null ? "Rating not declared" : `${charger.max_kw} kW`}`}</strong> : null}
              {charger.connectors.map((c, i) => (
                <div key={c.asset_id ?? i} className="muted" data-ev-part="connector">
                  {`${connectorName(c, names, i)} · ${c.max_kw === null ? "rating not declared" : `${c.max_kw} kW`} · service hours ${scheduleText(c)} · clock bound ${clockBound(c)} · Configured source roles: ${mapped(c.asset_id).replace(/^Mapped: /, "").replace(NOT_DECLARED, "none")}`}
                </div>
              ))}
            </div>
          ))}
        </details>
      </td>
      <td>{rolesTotal === 0 ? "No configured source roles" : count(rolesTotal, "configured source role")}</td>
    </tr>
  );
}
