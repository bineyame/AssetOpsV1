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

import { useMemo, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { Badge, Breadcrumbs, DataTable, Disclosure, Fact, FactList, PageHeader, Panel, type Crumb } from "../ui";
import {
  AcquisitionDetailsPanel,
  ReadinessVerdictPanel,
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
  /** The Site's Evidence address, where claim readiness lives. */
  evidenceHref: string;
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
      <PageHeader
        title="Foundation"
        headingId={SITE_CONFIGURATION_HEADING_ID}
        subtitle={`${configuration.displayName} · ${configuration.siteId}`}
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
      <SelectedPartPanel {...props} site={site} configuration={configuration} />
      {view === "model" ? (
        <SiteModelView {...props} site={site} configuration={configuration} />
      ) : view === "sld" ? (
        <SldView {...props} site={site} configuration={configuration} />
      ) : (
        <ReadinessView {...props} />
      )}
    </div>
  );
}

interface ViewProps extends StoredFoundationViewsProps {
  site: SiteDetailReadModel;
  configuration: SiteConfigurationView;
}

function strip(props: StoredFoundationViewsProps, action: ReactNode) {
  return (
    <FoundationPeriodStrip
      foundation={props.foundation}
      versions={props.versions}
      selectedAt={props.selectedAt}
      onSelectAt={props.onSelectAt}
      action={action}
    />
  );
}

/* Site model ---------------------------------------------------------------- */

function SiteModelView(props: ViewProps) {
  const { foundation, versions, viewHref, configuration, onPublish } = props;
  const gaps = foundation.configuration_gaps;
  return (
    <>
      {strip(props, <Link to={viewHref("readiness")}>Review configuration readiness →</Link>)}
      {gaps.length === 0 ? null : (
        <Panel heading="Configuration gaps" headingId="foundation-gaps-heading">
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
        </Panel>
      )}
      <div className="panel-pair">
        <ConfiguredTopologyPanel
          site={props.site}
          sldHref={viewHref("sld")}
          selection={{ selected: props.selectedComponent ?? null, onSelect: props.onSelectComponent }}
        />
        <IdentityPanel foundation={foundation} configuration={configuration} />
      </div>
      <FoundationControlsPanel foundation={foundation} versions={versions} onPublish={onPublish} />
      <Panel heading="Record and inventory details" headingId="foundation-details-heading">
        <p>Kept for audit. Open a section to see its records.</p>
        <FoundationRecordDetails foundation={foundation} versions={versions} />
        <Disclosure name="foundation-summary" summary="Configuration document summary">
          <p>{configuration.foundationSummary}</p>
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
      </Panel>
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
  if (selection.onSelect === undefined) return <>{name}</>;
  const pressed = selection.selected === componentId;
  return (
    <button
      type="button"
      className="part-choice"
      aria-pressed={pressed}
      data-part-choice={componentId}
      onClick={() => selection.onSelect?.(pressed ? null : componentId)}
    >
      {name}
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
}: {
  site: SiteDetailReadModel;
  sldHref: string;
  selection: PartSelection;
}) {
  const configuration = deriveSiteConfigurationView(site);
  const cards = topologyCards(site, configuration);
  return (
    <Panel
      heading="Configured topology"
      headingId="foundation-configured-topology-heading"
      description={
        <>
          Declared ratings and configured connections; not live energy flows.{" "}
          <Link to={sldHref}>Single line diagram →</Link>
        </>
      }
    >
      {cards === null ? (
        <p data-topology="not-declared">
          This Foundation version declares no topology with a bus, so no arrangement is drawn.
        </p>
      ) : (
        <div className="plant-map" data-topology="declared">
          <TopologyCards cards={cards.supplies} selection={selection} />
          <p className="plant-bus" data-topology-bus>
            {cards.busName}
            {cards.busRating === null ? "" : ` · ${cards.busRating}`} · configured electrical connections
          </p>
          <TopologyCards cards={cards.loads} selection={selection} />
        </div>
      )}
    </Panel>
  );
}

function IdentityPanel({
  foundation,
  configuration,
}: {
  foundation: FoundationReadModel;
  configuration: SiteConfigurationView;
}) {
  const names = new Map(foundation.assets.map((asset) => [asset.asset_code, asset.display_name ?? asset.asset_code]));
  const critical = foundation.controls.critical_load_priority;
  return (
    <Panel heading="Identity & operating obligations" headingId="foundation-identity-heading">
      <FactList>
        <Fact term="Site code">{foundation.site.site_code}</Fact>
        <Fact term="Name">{configuration.displayName}</Fact>
        <Fact term="Archetype">{configuration.siteType}</Fact>
        <Fact term="Location">{configuration.location}</Fact>
        <Fact term="Timezone">{configuration.timezone}</Fact>
        <Fact term="Critical-load priority">
          {critical.members === undefined || critical.members.length === 0
            ? "Not configured in this Foundation"
            : critical.members.map((code) => names.get(code) ?? code).join(" → ")}
        </Fact>
        <Fact term="Lifecycle status">
          <Badge tone="lifecycle">{configuration.lifecycleStatus}</Badge>
        </Fact>
        <Fact term="Evidence mode">
          <Badge tone="provenance">{configuration.sourceMode}</Badge>
        </Fact>
        <Fact term="Configuration origin">
          <Badge tone="origin">{configuration.configurationOrigin}</Badge>
        </Fact>
      </FactList>
    </Panel>
  );
}

/* Single line diagram -------------------------------------------------------- */

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
        heading={`${configuration.displayName} · configured single line diagram`}
        headingId={SITE_SLD_HEADING_ID}
        description="Configured equipment and declared connections for the period shown; not live power flow, and not reporting status."
      >
        <SiteSldPrimary
          site={site}
          boundDevices={boundDevices}
          headingId={SITE_SLD_HEADING_ID}
          selection={
            props.onSelectComponent === undefined
              ? null
              : { selected: props.selectedComponent ?? null, onSelect: props.onSelectComponent }
          }
        />
      </Panel>
      <ConfiguredPartsPanel
        foundation={foundation}
        site={site}
        configuration={configuration}
        selection={{ selected: props.selectedComponent ?? null, onSelect: props.onSelectComponent }}
      />
      <Panel heading="Diagram detail" headingId="foundation-sld-detail-heading">
        <p>The same configuration in rows, kept for audit.</p>
        <Disclosure name="sld-contents" summary="Diagram contents and open review questions">
          <SiteSldDetails site={site} boundDevices={boundDevices} />
        </Disclosure>
        <Disclosure name="sld-topology" summary="Topology nodes and connections">
          <SiteTopologyNodes section={configuration.topologyNodes} />
          <SiteTopologyConnections section={configuration.topologyConnections} />
        </Disclosure>
        <Disclosure name="sld-devices" summary="Devices and the binding set's device-to-asset links">
          <SiteFoundationDevices section={configuration.devices} />
          <SiteSignalMappings section={configuration.signalMappings} basis={basis} />
        </Disclosure>
      </Panel>
    </>
  );
}

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
          {m.role_label}: <code>{`${m.device_id} / ${m.signal_id}`}</code>
        </li>
      ))}
      {missing.map((c) => (
        <li key={`${c.device_id}/${c.signal_id}`} data-part-channel="unbound" className="muted">
          Not bound: <code>{`${c.device_id} / ${c.signal_id}`}</code>
        </li>
      ))}
    </ul>
  );
}

/** The chosen part, on every view, with its channels for the period shown. */
function SelectedPartPanel(props: ViewProps) {
  const { foundation, site, configuration, selectedComponent, onSelectComponent } = props;
  if (!selectedComponent) return null;
  const component = configuration.components.find((c) => c.componentId === selectedComponent);
  if (component === undefined) return null;
  const channels = partChannels(foundation, site, component.componentId);
  return (
    <Panel
      heading={`Selected part: ${component.displayName}`}
      headingId="foundation-selected-part-heading"
      description={`Configuration for Foundation v${foundation.revision.version}; channels from the binding set in effect for this period. Not readings.`}
    >
      <div className="selected-part" data-selected-part={component.componentId}>
        <FactList>
          <Fact term="Component ID">
            <code>{component.componentId}</code>
          </Fact>
          <Fact term="Type">{component.componentType}</Fact>
          <Fact term="Declared rating">{component.rating}</Fact>
          <Fact term="Channels">
            <PartChannelList {...channels} />
          </Fact>
        </FactList>
        {onSelectComponent ? (
          <button type="button" className="part-clear" onClick={() => onSelectComponent(null)}>
            Clear selected part
          </button>
        ) : null}
      </div>
    </Panel>
  );
}

/** What each configured part is, and which of its channels are bound. */
function ConfiguredPartsPanel({
  foundation,
  site,
  configuration,
  selection,
}: {
  foundation: FoundationReadModel;
  site: SiteDetailReadModel;
  configuration: SiteConfigurationView;
  selection: PartSelection;
}) {
  return (
    <Panel heading="What each configured part is" headingId="foundation-sld-parts-heading">
      <DataTable labelledBy="foundation-sld-parts-heading">
        <caption>
          Each declared component, its declared rating, and its channels. A bound channel describes this
          part: the binding set shown names it as the asset. An unbound channel (marked Not bound) is only
          one declared on a device attached to this part; it has no published meaning and is not a report
          from the part. Configuration, not readings. Choose a part to keep it selected across views.
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
              <td>
                <PartChannelList {...partChannels(foundation, site, component.componentId)} />
              </td>
            </tr>
          ))}
        </tbody>
      </DataTable>
    </Panel>
  );
}

/* Readiness ------------------------------------------------------------------ */

function ReadinessView(props: StoredFoundationViewsProps) {
  const { foundation, viewHref, snapshotHref, onPublishBindings, evidenceHref } = props;
  return (
    <>
      {strip(props, <Link to={viewHref("sld")}>Single line diagram →</Link>)}
      <ReadinessVerdictPanel foundation={foundation} />
      <RoleCoveragePanel foundation={foundation} />
      <SignalBindingsPanel foundation={foundation} onPublishBindings={onPublishBindings} />
      <RegisteredSourcesPanel foundation={foundation} evidenceHref={evidenceHref} />
      <AcquisitionDetailsPanel foundation={foundation} snapshotHref={snapshotHref} />
      <p className="note" data-readiness-scope="">
        This view assesses configuration only: roles, bindings, Foundation gaps and registrations.{" "}
        {foundation.evidence.statement} Claim readiness, accepted evidence and diagnostics are on{" "}
        <Link to={evidenceHref}>Site Evidence</Link>.
      </p>
    </>
  );
}
