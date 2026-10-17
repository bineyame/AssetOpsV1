/**
 * The three Foundation views of a Site imported into the persisted store
 * (S1-03, Architect decision `D-2026-10-08-s1-foundation-organization`).
 *
 * Site model, Single line diagram and Readiness follow the v6.9 mock's
 * organization (`#/foundation`, `#/sld`, `#/readiness`): a concise status
 * strip first, then the primary visual or verdict, then the details, with long
 * audit material kept on the page behind named disclosures. The mock supplies
 * hierarchy, not data: every value here comes from the selected stored
 * Foundation, binding set and registrations. Nothing is an observation, a
 * pending gateway is never shown as connected, and panels the mock fills with
 * gateway status, live flows or commissioning have no counterpart here.
 *
 * All three views read the same selection, because the selection is the `at`
 * value in the URL and the shell passes the one read to whichever view the
 * address names.
 */

import { Fragment, useMemo, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { Badge, Breadcrumbs, DataTable, Disclosure, Fact, FactList, MissingClaim, Panel, SITE_SCREEN_DESCRIPTIONS, SitePageHeader, type Crumb } from "../ui";
import {
  AcquisitionDetailsPanel,
  knownReadiness,
  ReadinessVerdictLead,
  ReadinessVerdictNotes,
  RoleCoveragePanel,
  SignalBindingsPanel,
} from "./FoundationBindingsPanel";
import {
  FoundationControlsPanel,
  FoundationPeriodStrip,
  FoundationRecordDetails,
  RegisteredSourcesPanel,
} from "./FoundationRevisionPanel";
import { FoundationSubtabs, foundationViewLabel, type FoundationView } from "./FoundationSubtabs";
import {
  SITE_CONFIGURATION_HEADING_ID,
  SiteConfigurationComponents,
  SiteControlAssumptions,
  SiteControlProperties,
  SiteControlsTable,
  SiteFoundationDevices,
  SitePhysicalProperties,
  SiteSignalMappings,
  SiteTopologyConnections,
  SiteTopologyNodes,
  type SignalMappingBasis,
} from "./SiteConfiguration";
import { ComponentTypeIcon } from "./componentIcons";
import { ExactRef, UserName } from "./exactValues";
import type { GatewayHealthClient } from "./gatewayHealthClient";
import { GatewayStatusPanel, ReadinessCards, ReadinessEvidenceTable } from "./ReadinessOverview";
import { SITE_SLD_HEADING_ID, SiteSldDetails, SiteSldPrimary } from "./SiteSingleLineDiagram";
import type {
  BindingPublishOutcome,
  FoundationReadModel,
  FoundationVersionsReadModel,
  PublishOutcome,
  SignalBinding,
} from "./siteFoundationClient";
import type { SiteDetailReadModel } from "./siteReadModel";
import { deriveSiteConfigurationView, type SiteConfigurationView } from "./siteViewModel";

export interface StoredFoundationViewsProps {
  view: FoundationView;
  /** The stored read for the selected period. */
  foundation: FoundationReadModel;
  versions: FoundationVersionsReadModel | null;
  selectedAt: string | null;
  onSelectAt: (at: string | null) => void;
  /** The address of a view, carrying the selected period. Built by the shell. */
  viewHref: (view: FoundationView) => string;
  /** Performance › Dispatch for this Site (V-01a round 3 control-table link). */
  dispatchHref?: string;
  /** The Site's Evidence address, where claim readiness lives. */
  evidenceHref: string;
  /** The Site's Health address, where source contact and reporting live (W1-UX-05). */
  healthHref: string;
  snapshotHref: string;
  onPublish: (assetCode: string, value: number, validFrom: string) => Promise<PublishOutcome>;
  onPublishBindings: (validFrom: string, bindings: SignalBinding[], note: string) => Promise<BindingPublishOutcome>;
  /**
   * The selected part's stable component ID, already checked against this
   * period's declared components by the shell (null when none is chosen).
   */
  selectedComponent?: string | null;
  /** A part chosen earlier that this period does not declare; selection was cleared. */
  missingComponent?: string | null;
  onSelectComponent?: (componentId: string | null) => void;
  /** The S2 central gateway-contact read, composed on Readiness (V-01a round 3). */
  gatewayHealth?: GatewayHealthClient;
  /** The operator Site tab row, placed under the page header. */
  tabs?: ReactNode;
  parentTrail: (siteId: string) => Crumb[];
}

/**
 * The stored Site as the shared substrate reads it: the Foundation document of
 * the selected version, with its signal links replaced by the bindings in
 * effect (S1-02), so every table and the diagram show configured links only.
 */
export function storedSiteDetail(foundation: FoundationReadModel): SiteDetailReadModel {
  return {
    ...foundation.detail,
    foundation: {
      ...foundation.detail.foundation,
      signal_mappings: foundation.bindings.mappings.map((binding) => ({
        mapping_id: binding.binding_revision_id,
        device_id: binding.device_id,
        signal_id: binding.signal_id,
        component_id: binding.asset_code ?? "",
      })),
    },
  };
}

export function StoredFoundationViews(props: StoredFoundationViewsProps) {
  const { view, foundation, viewHref, tabs, parentTrail } = props;
  const site = useMemo(() => storedSiteDetail(foundation), [foundation]);
  const configuration = useMemo(() => deriveSiteConfigurationView(site), [site]);
  const trail: Crumb[] =
    view === "model"
      ? [...parentTrail(configuration.siteId), { label: "Foundation" }]
      : [
          ...parentTrail(configuration.siteId),
          { label: "Foundation", to: viewHref("model") },
          { label: foundationViewLabel(view) },
        ];

  return (
    <div className="foundation-views-page" data-foundation-view-page={view}>
      <Breadcrumbs trail={trail} />
      <SitePageHeader
        siteName={configuration.displayName}
        siteId={configuration.siteId}
        mode={configuration.sourceMode}
        description={SITE_SCREEN_DESCRIPTIONS[view === "model" ? "foundation" : view]}
        headingId={SITE_CONFIGURATION_HEADING_ID}
      />
      {tabs}
      <FoundationSubtabs current={view} hrefFor={viewHref} />
      {props.missingComponent ? (
        <p className="notice notice--attention" role="status" data-selected-part-missing={props.missingComponent}>
          <strong>Selected part is not in this Foundation period.</strong> Part{" "}
          <code>{props.missingComponent}</code> is not declared in Foundation v{foundation.revision.version}, so
          the selection was cleared. No other part was chosen in its place.
        </p>
      ) : null}
      {view === "model" ? (
        <SiteModelView {...props} site={site} configuration={configuration} />
      ) : view === "sld" ? (
        <SldView {...props} site={site} configuration={configuration} />
      ) : (
        <ReadinessView {...props} site={site} configuration={configuration} />
      )}
    </div>
  );
}

const READINESS_ADVANCED = "readiness-advanced";

/**
 * The v69 panel slots of a Foundation view when the selected read cannot fill
 * them (`D-2026-10-17-mockup-layout-spec`): each panel keeps its place and states
 * the gap inside it. Nothing configured is shown, and no other period's values
 * stand in. The page-level refusal is stated before these by the shell.
 */
export function FoundationPanelSkeletons({
  view,
  siteName,
  gap,
}: {
  view: FoundationView;
  /** The Site name for the SLD title; the route's Site ID when the name is unknown. */
  siteName: string;
  gap: string;
}) {
  const slot = (title: string, id: string, extra?: ReactNode) => (
    <Panel heading={title} headingId={id}>
      <p className="not-available-yet" data-panel-gap={id}>
        {gap}
      </p>
      {extra}
    </Panel>
  );
  if (view === "model") {
    return (
      <>
        <div className="panel-pair">
          {slot("Configured topology", "foundation-configured-topology-heading")}
          {slot("Identity and operating obligations", "foundation-identity-heading")}
        </div>
        {slot("Time-valid control configuration", "foundation-controls-config-heading")}
      </>
    );
  }
  if (view === "sld") {
    return (
      <>
        {slot(siteName, SITE_SLD_HEADING_ID, <p className="muted">Site type unknown: no stored version was read.</p>)}
        {slot("What each part does", "foundation-sld-parts-heading")}
      </>
    );
  }
  return (
    <>
      {slot("Readiness and commissioning evidence", "foundation-readiness-table-heading")}
      <Panel className="gw-panel" heading="Gateway status · No gateway selected" headingId="foundation-readiness-gateway-heading">
        <p className="not-available-yet" data-panel-gap="foundation-readiness-gateway-heading">
          {gap}
        </p>
        <div className="panel-pair">
          {slot("Connected sources", "readiness-connected-sources-heading")}
          {slot("Effect on readiness and confidence", "readiness-effect-heading")}
        </div>
      </Panel>
    </>
  );
}

interface ViewProps extends StoredFoundationViewsProps {
  site: SiteDetailReadModel;
  configuration: SiteConfigurationView;
}

function strip(
  props: StoredFoundationViewsProps,
  action: ReactNode,
  extraReferences?: { label: string; value: string | null }[],
  lead?: ReactNode,
) {
  return (
    <FoundationPeriodStrip
      lead={lead}
      foundation={props.foundation}
      versions={props.versions}
      selectedAt={props.selectedAt}
      onSelectAt={props.onSelectAt}
      action={action}
      extraReferences={extraReferences}
    />
  );
}

/* Site model ---------------------------------------------------------------- */

function SiteModelView(props: ViewProps) {
  const { foundation, versions, viewHref, configuration, onPublish } = props;
  const gaps = foundation.configuration_gaps;
  const noEffective = gaps.find((gap) => gap.code === "NO_EFFECTIVE_REVISION");
  if (noEffective !== undefined) {
    // Fail closed (W1-F1 review finding 11): a loaded read that resolves no
    // effective version shows nothing as configured. Each v69 panel keeps its
    // slot and states the gap; no other period's values stand in.
    return (
      <>
        {strip(props, <Link to={viewHref("readiness")}>Review configuration readiness →</Link>)}
        <FoundationPanelSkeletons
          view="model"
          siteName={configuration.displayName}
          gap={`No configuration for this period: ${noEffective.message} No equipment or settings are recorded for the selected time.`}
        />
      </>
    );
  }
  return (
    <>
      {strip(props, <Link to={viewHref("readiness")}>Review configuration readiness →</Link>)}
      <div className="panel-pair">
        <ConfiguredTopologyPanel
          site={props.site}
          sldHref={viewHref("sld")}
          selection={{
            selected: props.selectedComponent ?? null,
            onSelect: props.onSelectComponent,
            controls: stripId("model"),
          }}
          strip={<SelectedPartStrip {...props} scope="model" />}
        />
        <IdentityPanel foundation={foundation} configuration={configuration} site={props.site} />
      </div>
      <FoundationControlsPanel
        foundation={foundation}
        versions={versions}
        onPublish={onPublish}
        dispatchHref={props.dispatchHref}
      >
        {gaps.length === 0 ? null : (
          <div className="subsection" data-foundation-gaps="">
            <h3 className="subsection__heading" id="foundation-gaps-heading">
              Configuration gaps
            </h3>
            <ul aria-labelledby="foundation-gaps-heading">
              {gaps.map((gap) => (
                <li key={`${gap.code}-${gap.subject}`} data-gap-code={gap.code}>
                  {gap.message}
                </li>
              ))}
            </ul>
            <p>
              A gap keeps configuration readiness incomplete.{" "}
              <Link to={viewHref("readiness")}>See what is missing in Readiness →</Link>
            </p>
          </div>
        )}
        <Disclosure name="foundation-advanced" summary="Advanced details — Foundation records">
          <p>Record IDs, the import path and its content reference, raw component and property tables, and control assumptions, kept for audit.</p>
          <FoundationRecordDetails foundation={foundation} versions={versions} />
          <Disclosure name="foundation-summary" summary="Configuration document summary">
            <p>
              <UserName>{configuration.foundationSummary}</UserName>
            </p>
          </Disclosure>
          <Disclosure name="foundation-components" summary={`Components and declared ratings (${configuration.components.length})`}>
            <SiteConfigurationComponents components={configuration.components} />
            <SitePhysicalProperties section={configuration.physicalProperties} />
          </Disclosure>
          <Disclosure name="foundation-declared-controls" summary="Declared control properties and operating assumptions">
            <SiteControlProperties section={configuration.controlProperties} />
            <SiteControlsTable section={configuration.siteControls} />
            <SiteControlAssumptions section={configuration.controlAssumptions} />
          </Disclosure>
        </Disclosure>
      </FoundationControlsPanel>
    </>
  );
}

interface TopologyCard {
  key: string;
  parts: { componentId: string; componentType: string; name: string }[];
  ratings: string[];
}

/** Supply chains into the bus and loads off it, from the declared topology. */
function topologyCards(site: SiteDetailReadModel, configuration: SiteConfigurationView) {
  const topology = site.foundation.topology;
  if (topology === null || topology.nodes.length === 0) return null;
  const nodes = new Map(topology.nodes.map((node) => [node.node_id, node]));
  const components = new Map(configuration.components.map((c) => [c.componentId, c]));
  const bus = topology.nodes.find((node) => node.node_role === "BUS");
  if (bus === undefined) return null;
  const name = (nodeId: string) => {
    const node = nodes.get(nodeId);
    return node === undefined ? nodeId : components.get(node.component_id)?.displayName ?? node.component_id;
  };
  const rating = (nodeId: string) => {
    const node = nodes.get(nodeId);
    const component = node === undefined ? undefined : components.get(node.component_id);
    return component === undefined ? null : component.rating;
  };
  const types = new Map(site.foundation.components.map((c) => [c.component_id, c.component_type]));
  const card = (chain: string[]): TopologyCard => ({
    key: chain.join(">"),
    parts: chain.map((nodeId) => {
      const componentId = nodes.get(nodeId)?.component_id ?? nodeId;
      return { componentId, componentType: types.get(componentId) ?? "", name: name(nodeId) };
    }),
    ratings: chain.map(rating).filter((r): r is string => r !== null),
  });
  const supplies: TopologyCard[] = [];
  for (const connection of topology.connections) {
    if (connection.to_node !== bus.node_id) continue;
    const chain = [connection.from_node];
    const seen = new Set(chain);
    for (;;) {
      const upstream = topology.connections.find((c) => c.to_node === chain[0] && !seen.has(c.from_node));
      if (upstream === undefined) break;
      chain.unshift(upstream.from_node);
      seen.add(upstream.from_node);
    }
    supplies.push(card(chain));
  }
  const loads = topology.connections
    .filter((connection) => connection.from_node === bus.node_id)
    .map((connection) => card([connection.to_node]));
  return { busName: name(bus.node_id), busRating: rating(bus.node_id), supplies, loads };
}

interface PartSelection {
  selected: string | null;
  onSelect?: (componentId: string | null) => void;
  /** The id of the selected-part strip region this choice updates. */
  controls?: string;
}

/**
 * A declared part's name as a toggle that chooses it by component ID. Without
 * a selection handler it is the plain name.
 */
function PartChoice({
  componentId,
  name,
  selection,
}: {
  componentId: string;
  name: string;
  selection: PartSelection;
}) {
  if (selection.onSelect === undefined) return <UserName>{name}</UserName>;
  const pressed = selection.selected === componentId;
  return (
    <button
      type="button"
      className="part-choice"
      aria-pressed={pressed}
      aria-controls={selection.controls}
      data-part-choice={componentId}
      onClick={() => selection.onSelect?.(pressed ? null : componentId)}
    >
      <UserName>{name}</UserName>
    </button>
  );
}

function TopologyCards({ cards, selection }: { cards: TopologyCard[]; selection: PartSelection }) {
  return (
    <ul className="plant-cards">
      {cards.map((item) => (
        <li
          className="plant-card"
          key={item.key}
          data-selected={item.parts.some((p) => p.componentId === selection.selected) ? "" : undefined}
        >
          {/* V-01a round 2: one icon per declared part, named by its type. */}
          <span className="plant-card__icons">
            {item.parts.map((part) => (
              <ComponentTypeIcon key={part.componentId} componentType={part.componentType} size={44} />
            ))}
          </span>
          <strong>
            {item.parts.map((part, index) => (
              <span key={part.componentId}>
                {index > 0 ? " → " : null}
                <PartChoice componentId={part.componentId} name={part.name} selection={selection} />
              </span>
            ))}
          </strong>
          <small>{item.ratings.length === 0 ? "No rating declared" : item.ratings.join(" · ")}</small>
        </li>
      ))}
    </ul>
  );
}

function ConfiguredTopologyPanel({
  site,
  sldHref,
  selection,
  strip,
}: {
  site: SiteDetailReadModel;
  sldHref: string;
  selection: PartSelection;
  strip?: ReactNode;
}) {
  const configuration = deriveSiteConfigurationView(site);
  const cards = topologyCards(site, configuration);
  return (
    <Panel
      heading="Configured topology"
      headingId="foundation-configured-topology-heading"
      description="Declared ratings and configured connections; not live energy flows"
      actions={<Link to={sldHref}>Single line diagram →</Link>}
    >
      {cards === null ? (
        <p data-topology="not-declared">
          This Foundation version declares no topology with a bus, so no arrangement is drawn.
        </p>
      ) : (
        <div className="plant-map" data-topology="declared">
          <TopologyCards cards={cards.supplies} selection={selection} />
          <p className="plant-bus" data-topology-bus>
            <UserName>{cards.busName}</UserName>
            {cards.busRating === null ? "" : ` · ${cards.busRating}`} · configured electrical connections
          </p>
          <TopologyCards cards={cards.loads} selection={selection} />
        </div>
      )}
      {strip}
    </Panel>
  );
}

/** The named loads and the first critical-load member, from stored records only. */
export function loadFacts(foundation: FoundationReadModel, site: SiteDetailReadModel) {
  const assetNames = new Map(foundation.assets.map((asset) => [asset.asset_code, asset.display_name]));
  const componentNames = new Map(site.foundation.components.map((c) => [c.component_id, c.display_name]));
  const nameOf = (code: string) => assetNames.get(code) ?? componentNames.get(code) ?? code;
  const members = foundation.controls.critical_load_priority.members ?? [];
  return {
    firstCritical: members.length === 0 ? null : nameOf(members[0]),
    criticalOrder: members.map(nameOf),
    loads: site.foundation.components
      .filter((component) => component.component_type === "LOAD")
      .map((component) => component.display_name),
  };
}

/** Names, each marked as user-owned, joined by `separator`. */
function joined(names: string[], separator: string): ReactNode {
  return names.map((name, index) => (
    <Fragment key={`${index}-${name}`}>
      {index > 0 ? separator : null}
      <UserName>{name}</UserName>
    </Fragment>
  ));
}

export const PRODUCTIVE_USE_NOT_DECLARED = "Not declared";
export const FINANCIAL_ASSUMPTIONS_NOT_AVAILABLE = "Financial assumptions not available here";
export const CRITICAL_LOAD_NOT_CONFIGURED = "Critical service order not configured";

function IdentityPanel({
  foundation,
  configuration,
  site,
}: {
  foundation: FoundationReadModel;
  configuration: SiteConfigurationView;
  site: SiteDetailReadModel;
}) {
  const facts = loadFacts(foundation, site);
  return (
    <Panel heading="Identity and operating obligations" headingId="foundation-identity-heading">
      <FactList>
        <Fact term="Site identity">
          <UserName>{configuration.displayName}</UserName> · <ExactRef>{foundation.site.site_code}</ExactRef>
        </Fact>
        <Fact term="Archetype">{configuration.siteType}</Fact>
        <Fact term="Location">{configuration.location}</Fact>
        <Fact term="Timezone">{configuration.timezone}</Fact>
        <Fact term="Critical service order">
          {facts.firstCritical === null ? (
            <span data-critical-load="not-configured">{CRITICAL_LOAD_NOT_CONFIGURED}</span>
          ) : (
            <span data-critical-load="configured">
              First in critical service order:{" "}
              <strong>
                <UserName>{facts.firstCritical}</UserName>
              </strong>
              {facts.criticalOrder.length > 1 ? (
                <small className="muted">
                  {" "}
                  Order: {joined(facts.criticalOrder, " → ")}. An order, not a service designation.
                </small>
              ) : null}
            </span>
          )}
        </Fact>
        <Fact term="Configured supplied users">
          <span data-configured-loads="">
            {facts.loads.length === 0 ? "No supplied users declared" : joined(facts.loads, ", ")}
          </span>
        </Fact>
        <Fact term="Productive-use designation">
          <span className="not-available-yet" data-productive-use="not-declared">
            <MissingClaim gapId="G-foundation-productive-use" placement="foundation.identity.productive-use">
              {PRODUCTIVE_USE_NOT_DECLARED}
            </MissingClaim>
          </span>
        </Fact>
        <Fact term="Evidence mode">
          <Badge tone="provenance">{configuration.sourceMode}</Badge>
        </Fact>
        <Fact term="Lifecycle status">
          <Badge tone="lifecycle">{configuration.lifecycleStatus}</Badge>
        </Fact>
        <Fact term="Configuration origin">
          <Badge tone="origin">{configuration.configurationOrigin}</Badge>
        </Fact>
      </FactList>
      <p className="not-available-yet" data-financial-assumptions="not-available">
        <MissingClaim gapId="G-foundation-financial-assumptions" placement="foundation.identity.financial-assumptions">
          {FINANCIAL_ASSUMPTIONS_NOT_AVAILABLE}. Physical ratings here are not financial assumptions.
        </MissingClaim>{" "}
        {/* S4-02a: the reviewed Site price read lives on Financials; the gap stays open until this link is accepted. */}
        <span data-financial-assumptions-link>
          The site&apos;s diesel price is on{" "}
          <Link to={`/sites/${encodeURIComponent(site.site_id)}/financials/assumptions`}>Financials › Assumptions</Link>.
        </span>
      </p>
    </Panel>
  );
}

/* Single line diagram -------------------------------------------------------- */

/**
 * The v69 `sld:1` title (approved dynamic rule): the selected Site's name and its
 * configured type. No topology type is invented when the site type is not stated.
 */
export function sldPanelTitle(configuration: SiteConfigurationView): string {
  // W1-F1 fix round 1 (review finding 9): the approved rule is "{site} · {configured
  // topology type, if stated}". The Foundation read states no topology type, and the
  // site archetype is not one, so the title is the site name and the panel
  // description says the type is not stated.
  return configuration.displayName;
}

/**
 * What the drawing can and cannot say, inside the diagram panel (the former W1
 * answer card's supported counts): parts drawn and devices with a linked reading
 * channel. Reporting is never inferred from a link.
 */
function SldDeviceSummary({ foundation, site }: { foundation: FoundationReadModel; site: SiteDetailReadModel }) {
  const devices = site.foundation.devices ?? [];
  const linked = new Set(foundation.bindings.mappings.map((binding) => binding.device_id));
  const withLink = devices.filter((device) => linked.has(device.device_id)).length;
  const parts = site.foundation.components.filter((c) => c.component_type !== "AC_BUS").length;
  return (
    <p className="v69-chart-note" data-sld-summary="">
      {devices.length === 0
        ? `${parts} parts are drawn; no device is recorded, so no part can report.`
        : `${parts} parts are drawn; ${withLink} of ${devices.length} devices have a linked reading channel.`}{" "}
      Whether linked parts are reporting is not assessed here.
    </p>
  );
}

function SldView(props: ViewProps) {
  const { foundation, site, configuration, viewHref } = props;
  const boundDevices = useMemo<ReadonlySet<string>>(
    () => new Set(foundation.bindings.mappings.map((binding) => binding.device_id)),
    [foundation],
  );
  const basis: SignalMappingBasis = {
    bindingSetVersion: foundation.bindings.binding_set?.version ?? null,
    bindingSetRevisionId: foundation.bindings.binding_set?.binding_set_revision_id ?? null,
    foundationVersion: foundation.revision.version,
  };
  return (
    <>
      {strip(props, <Link to={viewHref("readiness")}>Configuration readiness →</Link>)}
      <Panel
        heading={sldPanelTitle(configuration)}
        headingId={SITE_SLD_HEADING_ID}
        description="Topology type not stated in this version · configured equipment and declared connections for the period shown; not live power flow, and not reporting status"
        actions={<Link to={props.evidenceHref}>Site evidence →</Link>}
      >
        <SldDeviceSummary foundation={foundation} site={site} />
        <SiteSldPrimary
          site={site}
          boundDevices={boundDevices}
          headingId={SITE_SLD_HEADING_ID}
          selection={
            props.onSelectComponent === undefined
              ? null
              : { selected: props.selectedComponent ?? null, onSelect: props.onSelectComponent }
          }
          strip={<SelectedPartStrip {...props} scope="sld" />}
        />
        <p className="not-available-yet" data-sld-missing="">
          <MissingClaim gapId="G-sld-protection-metering" placement="sld.diagram.protection-metering">
            {SLD_PROTECTION_METERING_NOT_DECLARED}
          </MissingClaim>{" "}
          <MissingClaim gapId="G-sld-reporting-status" placement="sld.diagram.reporting-status">
            {SLD_REPORTING_STATUS_NOT_ASSESSED}
          </MissingClaim>{" "}
          {SLD_SEE_SITE_EVIDENCE} <Link to={props.evidenceHref}>Site Evidence →</Link>
        </p>
      </Panel>
      <ConfiguredPartsPanel
        foundation={foundation}
        site={site}
        configuration={configuration}
        selection={{
          selected: props.selectedComponent ?? null,
          onSelect: props.onSelectComponent,
          controls: stripId("sld"),
        }}
      >
        <Disclosure name="sld-advanced" summary="Advanced details — diagram records">
          <p>
            The same configuration in rows, kept for audit: each part&apos;s channels, topology node and connection
            IDs, devices and which device channel describes which part.
          </p>
          <Disclosure name="sld-part-channels" summary="Channels of each part">
            <PartChannelsTable foundation={foundation} site={site} configuration={configuration} />
          </Disclosure>
          <Disclosure name="sld-contents" summary="Diagram contents and open review questions">
            <SiteSldDetails site={site} boundDevices={boundDevices} />
          </Disclosure>
          <Disclosure name="sld-topology" summary="Topology nodes and connections">
            <SiteTopologyNodes section={configuration.topologyNodes} />
            <SiteTopologyConnections section={configuration.topologyConnections} />
          </Disclosure>
          <Disclosure name="sld-devices" summary="Devices and the channel-link set's device-to-asset links">
            <SiteFoundationDevices section={configuration.devices} />
            <SiteSignalMappings section={configuration.signalMappings} basis={basis} />
          </Disclosure>
        </Disclosure>
      </ConfiguredPartsPanel>
    </>
  );
}

/*
 * The SLD note beside the drawing (V-01a round-3 Addendum), split per claim (G-02):
 * protection/meter positions and per-part reporting status are separate gaps. The
 * rendered sentence is unchanged.
 */
export const SLD_PROTECTION_METERING_NOT_DECLARED =
  "Protection and meter positions are not declared in this Foundation topology;";
export const SLD_REPORTING_STATUS_NOT_ASSESSED = "monitoring links and reporting status are not assessed on this diagram.";
export const SLD_SEE_SITE_EVIDENCE = "See Site Evidence for reported records.";

/**
 * A part's channels for the selected period: bound channels whose binding names
 * this component as the asset, and declared-but-unbound channels on a device
 * attached to it. Always from the selected effective binding set.
 */
function partChannels(foundation: FoundationReadModel, site: SiteDetailReadModel, componentId: string) {
  const deviceComponent = new Map((site.foundation.devices ?? []).map((device) => [device.device_id, device.component_id]));
  const bound = foundation.bindings.mappings.filter((m) => m.asset_code === componentId);
  const missing = foundation.readiness.channels.filter(
    (c) => c.status !== "BOUND" && deviceComponent.get(c.device_id) === componentId,
  );
  return { bound, missing };
}

function PartChannelList({ bound, missing }: ReturnType<typeof partChannels>) {
  if (bound.length === 0 && missing.length === 0) return <>No channel declared for this part</>;
  return (
    <ul className="plain-list">
      {bound.map((m) => (
        <li key={m.binding_revision_id} data-part-channel="bound">
          {m.role_label}: <ExactRef>{`${m.device_id} / ${m.signal_id}`}</ExactRef>
        </li>
      ))}
      {missing.map((c) => (
        <li key={`${c.device_id}/${c.signal_id}`} data-part-channel="unbound" className="muted">
          Not bound: <ExactRef>{`${c.device_id} / ${c.signal_id}`}</ExactRef>
        </li>
      ))}
    </ul>
  );
}

function stripId(scope: "model" | "sld"): string {
  return `selected-part-strip-${scope}`;
}

function channelCounts({ bound, missing }: ReturnType<typeof partChannels>): string {
  if (bound.length === 0 && missing.length === 0) return "No channel declared";
  return `${bound.length} bound; ${missing.length} not bound`;
}

/**
 * The chosen part beside its drawing (V-01a round 3, item 4): name, declared
 * type and rating, its bound and unbound channel counts for the period shown,
 * Clear, and the full channel list behind an Advanced disclosure. The region
 * is always present and polite, so a changed selection is announced without
 * moving focus.
 */
function SelectedPartStrip(props: ViewProps & { scope: "model" | "sld" }) {
  const { foundation, site, configuration, selectedComponent, onSelectComponent, scope } = props;
  const component =
    selectedComponent == null ? undefined : configuration.components.find((c) => c.componentId === selectedComponent);
  const channels = component === undefined ? null : partChannels(foundation, site, component.componentId);
  const clear = () => {
    if (component === undefined || onSelectComponent === undefined) return;
    const id = component.componentId;
    onSelectComponent(null);
    // Return focus to the part's own choice, a stable control that stays on the page.
    window.setTimeout(() => {
      document.querySelector<HTMLElement>(`[data-part-choice="${id}"]`)?.focus();
    }, 0);
  };
  return (
    <div id={stripId(scope)} className="part-strip-region" aria-live="polite" data-part-strip-region={scope}>
      {component === undefined || channels === null ? null : (
        <div
          className="part-strip"
          role="group"
          aria-labelledby={`${stripId(scope)}-name`}
          data-selected-part={component.componentId}
        >
          <div className="part-strip__summary">
            <strong id={`${stripId(scope)}-name`}>
              Selected: <UserName>{component.displayName}</UserName>
            </strong>
            <span>{`${component.componentType} · ${component.rating}`}</span>
            <span data-part-channel-counts="">{channelCounts(channels)}</span>
            <span className="muted">{`Foundation v${foundation.revision.version}; configuration, not readings`}</span>
            {onSelectComponent ? (
              <button type="button" className="part-clear" onClick={clear}>
                Clear selected part
              </button>
            ) : null}
          </div>
          <Disclosure name={`selected-part-channels-${scope}`} summary="Advanced details — selected part channels">
            <FactList>
              <Fact term="Component ID">
                <ExactRef>{component.componentId}</ExactRef>
              </Fact>
              <Fact term="Channels">
                <PartChannelList {...channels} />
              </Fact>
            </FactList>
          </Disclosure>
        </div>
      )}
    </div>
  );
}

/** What each configured part is, and how many of its channels are bound. */
function ConfiguredPartsPanel({
  foundation,
  site,
  configuration,
  selection,
  children,
}: {
  foundation: FoundationReadModel;
  site: SiteDetailReadModel;
  configuration: SiteConfigurationView;
  selection: PartSelection;
  children?: ReactNode;
}) {
  return (
    <Panel heading="What each part does" headingId="foundation-sld-parts-heading">
      <DataTable labelledBy="foundation-sld-parts-heading">
        <caption>
          Each declared component, its declared rating and how many of its channels are bound for the period
          shown. Configuration, not readings. Choose a part to see it beside the drawing; the channel list is under
          Advanced details.
        </caption>
        <thead>
          <tr>
            <th scope="col">Part</th>
            <th scope="col">Type</th>
            <th scope="col">Declared rating</th>
            <th scope="col">Channels</th>
          </tr>
        </thead>
        <tbody>
          {configuration.components.map((component) => (
            <tr
              key={component.componentId}
              data-sld-part={component.componentId}
              data-selected={selection.selected === component.componentId ? "" : undefined}
            >
              <th scope="row">
                <PartChoice componentId={component.componentId} name={component.displayName} selection={selection} />
              </th>
              <td>{component.componentType}</td>
              <td>{component.rating}</td>
              <td>{channelCounts(partChannels(foundation, site, component.componentId))}</td>
            </tr>
          ))}
        </tbody>
      </DataTable>
      {children}
    </Panel>
  );
}

/** Every part's bound and unbound channels, for audit under Advanced details. */
function PartChannelsTable({
  foundation,
  site,
  configuration,
}: {
  foundation: FoundationReadModel;
  site: SiteDetailReadModel;
  configuration: SiteConfigurationView;
}) {
  return (
    <DataTable labelledBy="foundation-sld-parts-heading">
      <caption>
        A bound channel describes this part: the channel-link set shown names it as the asset. An unbound channel
        (marked Not bound) is only one declared on a device attached to this part; it has no published meaning and
        is not a report from the part.
      </caption>
      <thead>
        <tr>
          <th scope="col">Part</th>
          <th scope="col">Channels</th>
        </tr>
      </thead>
      <tbody>
        {configuration.components.map((component) => (
          <tr key={component.componentId} data-part-channels={component.componentId}>
            <th scope="row">
              <UserName>{component.displayName}</UserName>
            </th>
            <td>
              <PartChannelList {...partChannels(foundation, site, component.componentId)} />
            </td>
          </tr>
        ))}
      </tbody>
    </DataTable>
  );
}

/* Readiness ------------------------------------------------------------------ */

/**
 * What still needs doing for set-up, as one note line at the foot of panel 1
 * (W1-F1 fix round 1: the mock has no separate "What to do next" block).
 * Commissioning is never shown as confirmed.
 */
function ReadinessNextSteps({ foundation }: { foundation: FoundationReadModel }) {
  const missingRoles = foundation.readiness.roles.filter((role) => role.required && role.status !== "CONFIGURED");
  const steps: { key: string; text: string; role?: string }[] = [
    ...missingRoles
      .filter((role) => role.covered_by !== "FOUNDATION_CONTROL")
      .map((role) => ({ key: role.role, role: role.role, text: `Link a reading channel for ${role.label}.` })),
    ...missingRoles
      .filter((role) => role.covered_by === "FOUNDATION_CONTROL")
      .map((role) => ({ key: role.role, role: role.role, text: `Set ${role.label} in the Site model.` })),
    ...foundation.configuration_gaps.map((gap) => ({ key: `${gap.code}:${gap.subject}`, text: gap.message })),
    ...(foundation.gateways.length === 0 ? [{ key: "gateway", text: "Register the site's gateway." }] : []),
  ];
  return (
    <p className="v69-chart-note" data-readiness-next="">
      <strong>Next step: </strong>
      {!knownReadiness(foundation.readiness.state) ? (
        // Fail closed: an unrecognised set-up state never yields "nothing is missing".
        <span data-readiness-next-unrecognised="">
          The set-up state in this read is not recognised, so what is missing cannot be listed here.
        </span>
      ) : steps.length === 0 && foundation.readiness.state === "READY_TO_REPORT" ? (
        <span>Record a commissioning confirmation when one exists; nothing else is missing from the set-up.</span>
      ) : steps.length === 0 ? (
        <span>No missing item is listed in this read; the set-up state above still applies.</span>
      ) : (
        <span data-readiness-next-steps="">
          {steps.map((step, index) => (
            <Fragment key={step.key}>
              {index > 0 ? " " : null}
              <span data-readiness-missing-role={step.role}>{step.text}</span>
            </Fragment>
          ))}
        </span>
      )}
    </p>
  );
}

function ReadinessView(props: ViewProps) {
  const { foundation, viewHref, snapshotHref, onPublishBindings, evidenceHref, configuration } = props;
  const reviewBindings = () => {
    const advanced = document.querySelector<HTMLDetailsElement>(`details[data-disclosure="${READINESS_ADVANCED}"]`);
    if (advanced === null) return;
    advanced.open = true;
    const control =
      advanced.querySelector<HTMLElement>('form[aria-label="Remove a channel link"] select') ??
      advanced.querySelector<HTMLElement>("summary");
    control?.focus();
    control?.scrollIntoView?.({ block: "center" });
  };
  const selected =
    props.selectedComponent == null
      ? undefined
      : configuration.components.find((c) => c.componentId === props.selectedComponent);
  return (
    <>
      {strip(
        props,
        <Link to={viewHref("sld")}>Single line diagram →</Link>,
        [
          { label: "Set-up state (exact)", value: foundation.readiness.state },
          { label: "Required readings list", value: foundation.readiness.role_set },
        ],
        <ReadinessVerdictLead foundation={foundation} />,
      )}
      {selected === undefined ? null : (
        <p className="part-chip" data-selected-part-chip={selected.componentId}>
          Selected part: <strong>{selected.displayName}</strong> · details beside the part in{" "}
          <Link to={viewHref("model")}>Site model</Link> or <Link to={viewHref("sld")}>Single line diagram</Link>
        </p>
      )}
      <ReadinessCards foundation={foundation} />
      <ReadinessEvidenceTable
        foundation={foundation}
        links={{ model: viewHref("model"), sld: viewHref("sld"), evidence: evidenceHref }}
        onReviewBindings={reviewBindings}
      >
        <ReadinessVerdictNotes foundation={foundation} />
        <ReadinessNextSteps foundation={foundation} />
        <Disclosure name={READINESS_ADVANCED} summary="Advanced details — roles, channels and records">
          <p>
            The full role coverage, every channel link and its references, the channel-link change form, source
            registrations and the pinned acquisition snapshot. Kept for configuration work and audit.
          </p>
          <RoleCoveragePanel foundation={foundation} />
          <SignalBindingsPanel foundation={foundation} onPublishBindings={onPublishBindings} />
          <RegisteredSourcesPanel foundation={foundation} evidenceHref={evidenceHref} />
          <AcquisitionDetailsPanel foundation={foundation} snapshotHref={snapshotHref} />
        </Disclosure>
      </ReadinessEvidenceTable>
      <GatewayStatusPanel
        foundation={foundation}
        siteId={configuration.siteId}
        gatewayHealth={props.gatewayHealth}
        evidenceHref={evidenceHref}
        healthHref={props.healthHref}
      />
      <p className="note" data-readiness-scope="">
        This view assesses configuration: roles, channel links, Foundation gaps and registrations. Gateway status
        reports central server contact only. What the readings can support, accepted evidence and source diagnostics are on{" "}
        <Link to={evidenceHref}>Site Evidence</Link>.
      </p>
    </>
  );
}
