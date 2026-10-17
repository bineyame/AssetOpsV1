import { Fragment, type ReactNode } from "react";

import {
  Badge,
  Breadcrumbs,
  DataTable,
  Fact,
  FactList,
  PageHeader,
  Panel,
  type Crumb,
} from "../ui";
import type {
  ComponentPropertyView,
  ControlAssumptionView,
  FoundationDeviceView,
  SiteControlView,
  SiteDeclaredSection,
  SiteKeyParameterView,
  SignalMappingView,
  TopologyConnectionView,
  TopologyNodeView,
} from "./siteViewModel";
import type { SiteDetailClient } from "./siteDirectoryClient";
import type { SiteDetailReadModel } from "./siteReadModel";
import { ExactRef, UserName } from "./exactValues";
import { SiteSingleLineDiagram } from "./SiteSingleLineDiagram";
import { useSiteRecord } from "./useSiteRecord";
import {
  useSiteTemplateLineage,
  type SiteTemplateLineageClient,
  type SiteTemplateLineageReadModel,
} from "./siteTemplateLineage";
import { TemplateProvenanceText } from "./TemplateProvenanceText";
import {
  CONTROL_PROPERTIES_ARE_NOT_CONTROLS,
  FOUNDATION_DEVICE_METADATA_LIMITS,
  deriveSiteConfigurationView,
  type SiteComponentView,
  type SiteUnavailableFact,
} from "./siteViewModel";

/**
 * One site's Foundation, presented from the shared substrate.
 *
 * Foundation is the product name of this surface, from v6.9's operator Site
 * tab row. Configuration is the domain word underneath it: the document a site
 * was created from, its configuration origin, and the rule that configuration
 * is fixed at creation. So the heading says Foundation and the content still
 * says configuration where configuration is what it means.
 *
 * The module, the component and the heading id deliberately still say
 * `SiteConfiguration`. T011A renamed what a reader sees and what an address
 * says; renaming these would touch every test in this directory and both
 * single-definition guard patterns without changing one rendered character.
 *
 * This is the same shared-region rule the site page follows. A shell composes
 * it, supplies the landmark around it, and hands it chrome to place; there is
 * no `variant`, `mode`, `shell`, or `isLab` prop and no import of shell code,
 * simulator code, or the feature flag. The one extension slot, `tabs`, is
 * named, optional, and opaque: this component decides where it renders and
 * never what is in it.
 *
 * A site is addressed by `site_id` and by nothing else. Neither the foundation
 * version nor the template a site was created from addresses it, and nothing
 * on this screen changes it.
 *
 * What this surface shows is the configuration document, read back. It is
 * component truth declared by that document and never evidence: that a
 * foundation declares a 100 kW array is not a claim that any array exists, is
 * commissioned, or has ever reported a measurement.
 *
 * What it deliberately does not show:
 *
 * - No tab row of its own. The operator shell hands one in through `tabs`,
 *   and this component decides only where such a row goes: under the page
 *   header, above the facts, and only for a site it actually loaded.
 * - No action control of any kind, in any state, absent from the DOM rather
 *   than rendered disabled. M1 has decided configuration is fixed at creation,
 *   so a greyed-out control would promise a capability the product has
 *   declined to have, and `Version History` would name a future capability
 *   wrongly: no configuration-change model exists, and the eventual shape of
 *   that territory is an auditable intervention record, which is a different
 *   thing.
 * - No signal selector. Signals are declared and listed, and a control that
 *   picks one belongs to the slice that has something to show for the signal a
 *   reader picked. The configured diagram itself now renders, inside the
 *   Topology section: T016 is the causal step that earns it, and it draws only
 *   what `deriveSiteSldView` validated against the archetype - never a partial
 *   arrangement and never an empty frame.
 * - No telemetry, chart, series, gauge, count, source health, or analytics. A
 *   configuration-only site has no evidence, and a zero is a measurement claim
 *   rather than an absence.
 * - No empty table. Topology, devices, signal mappings and control assumptions
 *   render as content when this site's foundation declares them, and as a
 *   stated absence with its reason when it does not. Never as a table with a
 *   header row and no rows: that is a screen saying it looked and found
 *   nothing, which is a claim about the site rather than about its document.
 *
 * This is the legacy (unimported) Site's one page; an imported Site renders
 * the S1-03 views in `StoredFoundationViews` instead. Where the content sits
 * is settled, not incidental. W1-F1 (D-2026-10-17-mockup-layout-spec) gives
 * it the three v69 Foundation panels - Configured topology and Identity and
 * operating obligations side by side, then Time-valid control configuration -
 * and nothing else. Definition, Topology, Controls, Components and the other
 * former panels are subsections (h3) of the panel that owns them.
 */
export const SITE_CONFIGURATION_HEADING_ID = "site-configuration-heading";

/**
 * The legacy page's in-page section headings. S1-03 removed the
 * `Definition | Topology | Controls` contents row that linked to them: they
 * stay as headings on the one legacy page, and an imported Site uses the
 * Foundation view row (`FoundationSubtabs`) instead.
 */
export const FOUNDATION_DEFINITION_ID = "foundation-definition-heading";
export const FOUNDATION_TOPOLOGY_ID = "foundation-topology-heading";
export const FOUNDATION_CONTROLS_ID = "foundation-controls-heading";

export interface SiteConfigurationProps {
  /** The identity taken from the address. `undefined` names no site. */
  siteId: string | undefined;
  detail: SiteDetailClient;
  /**
   * Chrome the composing shell places under the page header. Nothing renders
   * when it is absent, and nothing here reads what is in it.
   */
  tabs?: ReactNode;
  /**
   * S1-01: the persisted Foundation version panel (period, controls, the one
   * reserve change, registrations and gaps), placed under the tabs and above
   * the subtab row. Absent for a Site still read from its legacy document.
   */
  revision?: ReactNode;
  /**
   * The trail above this page, built by the shell from the canonical
   * `site_id`. Foundation sits two levels down, so its parent is the Site
   * itself, and the Site's crumb has to be spelled the way the record spells
   * it rather than the way the address did.
   */
  parentTrail?: (siteId: string) => Crumb[];
  /**
   * The gated template-lineage read, passed only when the composing shell's
   * gate is open. Absent, "Created from template" shows the recorded lineage
   * alone; present, it adds the advisory note when the record is behind.
   */
  templateLineage?: SiteTemplateLineageClient;
  /**
   * S1-02: the devices with at least one channel bound in the binding set in
   * effect, for an imported Site. The SLD then marks every other attached
   * device as having no bound channel. Absent for a legacy Site.
   */
  sldBoundDevices?: ReadonlySet<string> | null;
  /**
   * S1-02: for an imported Site, the binding set whose device-to-asset links
   * fill the "Signal mappings" table, and the Foundation revision it is
   * aligned to. Absent for a legacy Site, whose table keeps the document's
   * declared mappings and their mapping IDs.
   */
  signalMappingBasis?: SignalMappingBasis | null;
}

/** Which published binding set the stored-Site mapping rows come from. */
export interface SignalMappingBasis {
  /** Null when no binding set is in effect for the period shown. */
  bindingSetVersion: number | null;
  bindingSetRevisionId: string | null;
  foundationVersion: number;
}

export function SiteConfiguration({
  siteId,
  detail,
  tabs,
  revision,
  parentTrail,
  templateLineage,
  sldBoundDevices = null,
  signalMappingBasis = null,
}: SiteConfigurationProps) {
  const result = useSiteRecord(siteId, detail);
  const lineage = useSiteTemplateLineage(templateLineage);

  if (result === null) {
    return (
      <>
        <PageHeader
          title="Foundation"
          headingId={SITE_CONFIGURATION_HEADING_ID}
        />
        <p>Loading the configured site.</p>
      </>
    );
  }

  if (result.status === "not_found") {
    return (
      <>
        <PageHeader
          title="Site not found"
          headingId={SITE_CONFIGURATION_HEADING_ID}
        />
        <Panel
          heading="No such site"
          headingId="site-configuration-not-found-heading"
        >
          <p>
            No site with that site ID is configured, so there is no
            configuration to read. A site is addressed by its site ID and by
            nothing else, so it cannot be reached by its name or by the
            template it was created from.
          </p>
          <p>
            This is a statement that the site does not exist, not a site with
            nothing configured in it.
          </p>
        </Panel>
      </>
    );
  }

  if (result.status === "unavailable") {
    return (
      <>
        <PageHeader
          title="Foundation"
          headingId={SITE_CONFIGURATION_HEADING_ID}
        />
        <Panel
          heading="Site unavailable"
          headingId="site-configuration-unavailable-heading"
        >
          <p>
            The site store could not be read, so this site&apos;s configuration
            cannot be shown. This is a statement about the store: nothing is
            known about whether the site is configured.
          </p>
        </Panel>
      </>
    );
  }

  return (
    <SiteConfigurationFacts
      site={result.site}
      tabs={tabs}
      revision={revision}
      parentTrail={parentTrail}
      lineage={lineage?.get(result.site.site_id)}
      sldBoundDevices={sldBoundDevices}
      signalMappingBasis={signalMappingBasis}
    />
  );
}

/**
 * The configuration itself, rendered from one record.
 *
 * Split out so the rendering can be exercised directly over records, with no
 * client, no router, and no shell in the way.
 */
export interface SiteConfigurationFactsProps {
  site: SiteDetailReadModel;
  /** See `SiteConfigurationProps.tabs`. */
  tabs?: ReactNode;
  /** See `SiteConfigurationProps.revision`. */
  revision?: ReactNode;
  /** See `SiteConfigurationProps.parentTrail`. */
  parentTrail?: (siteId: string) => Crumb[];
  /** This site's lineage answer, if the shell supplied a lineage read. */
  lineage?: SiteTemplateLineageReadModel;
  /** See `SiteConfigurationProps.sldBoundDevices`. */
  sldBoundDevices?: ReadonlySet<string> | null;
  /** See `SiteConfigurationProps.signalMappingBasis`. */
  signalMappingBasis?: SignalMappingBasis | null;
}

export function SiteConfigurationFacts({
  site,
  tabs,
  revision,
  parentTrail,
  lineage,
  sldBoundDevices = null,
  signalMappingBasis = null,
}: SiteConfigurationFactsProps) {
  const view = deriveSiteConfigurationView(site);

  return (
    <>
      {parentTrail === undefined ? null : (
        <Breadcrumbs
          trail={[...parentTrail(view.siteId), { label: "Foundation" }]}
        />
      )}

      {/*
        * The page is Foundation and the subtitle says whose. T011A settled
        * that this heading reads `Foundation`, and it still does; what was
        * missing was any statement of which site's foundation this is, which
        * a reader arriving from a bookmark had no way to tell.
        */}
      <PageHeader
        title="Foundation"
        headingId={SITE_CONFIGURATION_HEADING_ID}
        subtitle={`${view.displayName} · ${view.siteId}`}
      />

      {tabs}

      {revision}

      {/*
        * W1-F1 (D-2026-10-17-mockup-layout-spec): the legacy Site model renders
        * the three v69 Foundation panels and nothing else - Configured topology
        * beside Identity and operating obligations, then Time-valid control
        * configuration - the same arrangement as the stored Site model. The
        * panels this page used to stack (Definition, Topology, Controls,
        * Components, Key parameters, ...) are now subsections of the one panel
        * that owns them, under their old names, so their content is still found
        * where a reader looks for it.
        */}
      <div className="panel-pair">
        <Panel
          heading="Configured topology"
          headingId="site-configuration-configured-topology-heading"
        >
          <div className="subsection">
            <h3 className="subsection__heading" id={FOUNDATION_TOPOLOGY_ID}>
              Topology
            </h3>
            <p>
              What this site&apos;s foundation declares about how its components
              are joined, which devices are configured against them, and which
              component each device signal describes. All of it is configuration
              read back. Nothing here is a reading: no device has reported, and no
              value below has ever been measured.
            </p>

            {/*
              * The diagram comes first, above the tables that say the same
              * thing in rows: it is the same facts in two forms and the drawing
              * is the one a reader looks at first. It draws only what
              * `deriveSiteSldView` validated, never a partial arrangement.
              */}
            <SiteSingleLineDiagram site={site} boundDevices={sldBoundDevices} />

            {/*
              * Topology is one declaration, so it is one absence: when a
              * document declares none, the statement is made once rather than
              * repeated under the nodes and the connections headings.
              */}
            {view.topologyNodes.status === "not_declared" ? (
              <FactList>
                <SiteConfigurationStatedAbsence
                  name="Topology"
                  fact={view.topologyNodes.absence}
                />
              </FactList>
            ) : (
              <>
                <SiteTopologyNodes section={view.topologyNodes} />
                <SiteTopologyConnections section={view.topologyConnections} />
              </>
            )}

            <SiteFoundationDevices section={view.devices} />
            <SiteSignalMappings section={view.signalMappings} basis={signalMappingBasis} />

            {/*
              * Two device facts this build does not hold, stated once rather
              * than given a column each: a column of dashes would say the
              * product looked for a protocol and found none.
              */}
            <p className="note">{FOUNDATION_DEVICE_METADATA_LIMITS}</p>
          </div>

          <SiteConfigurationComponents components={view.components} />

          {/*
            * The typed physical properties sit with the components, because
            * what a tank holds and what a generator burns are facts about what
            * those machines ARE.
            */}
          <div className="subsection">
            <h3
              className="subsection__heading"
              id="site-configuration-physical-properties-heading"
            >
              Declared component properties
            </h3>
            <SitePhysicalProperties section={view.physicalProperties} />
          </div>
        </Panel>

        <Panel
          heading="Identity and operating obligations"
          headingId="site-configuration-identity-heading"
        >
          {/*
            * Definition, as v6.9 names it: identity, summary, validity and
            * provenance in one place.
            */}
          <div className="subsection">
            <h3 className="subsection__heading" id={FOUNDATION_DEFINITION_ID}>
              Definition
            </h3>
            <FactList>
              <Fact term="Site ID">{view.siteId}</Fact>
              <Fact term="Name">{view.displayName}</Fact>
              <Fact term="Type">{view.siteType}</Fact>
              <Fact term="Location">{view.location}</Fact>
              <Fact term="Timezone">{view.timezone}</Fact>
              <Fact term="Foundation version">{view.foundationVersion}</Fact>
              <Fact term="Valid from">{view.foundationValidFrom}</Fact>
              <Fact term="Summary">{view.foundationSummary}</Fact>
              {/*
               * Three vocabularies, three tones, never one status pill. Template
               * provenance stays plain text: a site created from no template
               * renders an absence there, and an absence is not a badge value.
               */}
              <Fact term="Lifecycle status">
                <Badge tone="lifecycle">{view.lifecycleStatus}</Badge>
              </Fact>
              <Fact term="Mode">
                <Badge tone="provenance">{view.sourceMode}</Badge>
              </Fact>
              <Fact term="Configuration origin">
                <Badge tone="origin">{view.configurationOrigin}</Badge>
              </Fact>
              <Fact term="Created from template">
                <TemplateProvenanceText
                  site={site}
                  provenance={view.templateProvenance}
                  lineage={lineage}
                />
              </Fact>
            </FactList>
            <p>{view.foundationValiditySemantics}</p>
            <p>
              These are separate facts about a site and none is derived from
              another. Configuration origin is where this site&apos;s configuration
              document came from. Mode is where the site&apos;s evidence comes
              from, and it is provenance rather than status, health, or an
              assessment. Lifecycle status is where the site is in its own life.
            </p>
          </div>

          <div className="subsection">
            <h3 className="subsection__heading" id="site-configuration-fixed-heading">
              Configuration is fixed at creation
            </h3>
            <p>{view.configurationFixedAtCreation}</p>
          </div>

          <SiteKeyParameters parameters={view.keyParameters} />

          <div className="subsection">
            <h3
              className="subsection__heading"
              id="site-configuration-no-evidence-heading"
            >
              Not available for this site
            </h3>
            <FactList>
              <SiteConfigurationStatedAbsence
                name="Integration readiness"
                fact={view.integrationReadiness}
              />
            </FactList>
            <p>
              This tab states the site&apos;s configuration, and nothing on it is
              evidence. What has been accepted for this site, the health of each
              source that delivered it and its coverage are on the Evidence tab.
            </p>
          </div>
        </Panel>
      </div>

      <Panel
        heading="Time-valid control configuration"
        headingId="site-configuration-time-valid-controls-heading"
      >
        {/*
          * Two different kinds of fact under one heading, and the order says
          * which is which. The declared control properties are configured
          * numbers with units; the control assumptions below are statements in
          * words about how the site is intended to be operated. Neither is a
          * control: nothing on this screen issues one.
          */}
        <div className="subsection">
          <h3 className="subsection__heading" id={FOUNDATION_CONTROLS_ID}>
            Controls
          </h3>
          <SiteControlProperties section={view.controlProperties} />
          <SiteControlsTable section={view.siteControls} />
          <SiteControlAssumptions section={view.controlAssumptions} />
        </div>
      </Panel>
    </>
  );
}

/**
 * The components the foundation declares.
 *
 * A rating here is the archetype's declared design rating, copied from
 * the template at creation. It is nameplate intent from a document, so the
 * column says declared and never shares a column with anything a device could
 * report.
 */
export interface SiteConfigurationComponentsProps {
  components: SiteComponentView[];
}

export function SiteConfigurationComponents({
  components,
}: SiteConfigurationComponentsProps) {
  return (
    <div className="subsection">
      <h3 className="subsection__heading" id="site-configuration-components-heading">
        Components
      </h3>
      <DataTable labelledBy="site-configuration-components-heading">
        <caption>
          The components this site&apos;s foundation declares, with the design
          ratings declared for them. These are configuration, not measurements:
          nothing here states that a device exists, is commissioned, or has
          ever reported.
        </caption>
        <thead>
          <tr>
            <th scope="col">Component</th>
            <th scope="col">Type</th>
            <th scope="col">Declared rating</th>
            <th scope="col">Component ID</th>
          </tr>
        </thead>
        <tbody>
          {components.map((component) => (
            <tr key={component.componentId}>
              <td>
                <UserName>{component.displayName}</UserName>
              </td>
              <td>{component.componentType}</td>
              <td>{component.rating}</td>
              <td>
                <ExactRef>{component.componentId}</ExactRef>
              </td>
            </tr>
          ))}
        </tbody>
      </DataTable>
    </div>
  );
}

/**
 * The typed physical properties the foundation declares.
 *
 * A rating is the one nameplate magnitude a component was sold with; these are
 * named facts about what the machine IS, each with its own unit and its own
 * provenance, and a component may declare several. That is the difference
 * between a rating column and this table: a profile looking for "the rating in
 * litres" can only ever find one thing per component, and a profile looking
 * for `tank-capacity` finds the thing it meant.
 *
 * Declared configuration, never evidence. Nothing here states that a
 * measurement was taken.
 */
export function SitePhysicalProperties({
  section,
}: {
  section: SiteDeclaredSection<ComponentPropertyView>;
}) {
  return (
    <SiteConfigurationSubsection
      name="Declared physical properties"
      headingId="foundation-physical-properties-heading"
      section={section}
      caption="Typed physical properties this site's foundation declares about its components, each with the unit it is declared in and the document and version that declared it. These are configuration copied at creation, not measurements."
      columns={["Component", "Property", "Declared quantity", "Declared by"]}
      row={(property) => ({
        key: property.key,
        cells: [
          <UserName key="component">{property.componentName}</UserName>,
          property.propertyName,
          property.value,
          property.declaredBy,
        ],
      })}
    />
  );
}

/**
 * The typed control properties the foundation declares.
 *
 * The same carrier as the physical properties above, and deliberately the same
 * shape: a control property is a configured number with a unit, not a control
 * model. There is no setpoint anything writes, no switching position, no
 * operating mode, and no controller - the first thing that CONSUMES one of
 * these arrives with a later slice, and this screen implies no capability to
 * act.
 *
 * The note is rendered beside the numbers rather than in a docstring, because
 * a reader meeting a column of numbers beside the word Controls is exactly the
 * reader who might take one for a control.
 */
export function SiteControlProperties({
  section,
}: {
  section: SiteDeclaredSection<ComponentPropertyView>;
}) {
  return (
    <>
      <SiteConfigurationSubsection
        name="Declared control properties"
        headingId="foundation-control-properties-heading"
        section={section}
        caption="Typed control properties this site's foundation declares about its components, each with the unit it is declared in and the document and version that declared it."
        columns={["Component", "Property", "Declared quantity", "Declared by"]}
        row={(property) => ({
          key: property.key,
          cells: [
            <UserName key="component">{property.componentName}</UserName>,
            property.propertyName,
            property.value,
            property.declaredBy,
          ],
        })}
      />
      <p className="note">{CONTROL_PROPERTIES_ARE_NOT_CONTROLS}</p>
    </>
  );
}

/**
 * One thing this screen does not state, with the reason it does not.
 *
 * The reason is rendered next to the value every time. "Not declared" on its
 * own reads as a fact about the site; with its reason it reads as what it is,
 * a statement about what the configuration document carries.
 */
export interface SiteConfigurationStatedAbsenceProps {
  name: string;
  fact: SiteUnavailableFact;
}

export function SiteConfigurationStatedAbsence({
  name,
  fact,
}: SiteConfigurationStatedAbsenceProps) {
  return (
    <Fact term={name}>
      {fact.value}. {fact.reason}
    </Fact>
  );
}

/**
 * One subsection inside a panel: a heading, and either a table or the
 * statement that this site&apos;s foundation declares nothing to put in it.
 *
 * The two branches are the point. A section with declared content renders its
 * table through `DataTable`, which supplies the region that owns the table&apos;s
 * horizontal overflow so a wide relationship table scrolls inside itself
 * rather than pushing the shell sideways. A section with nothing declared
 * renders words - the absence and the reason for it - and no table at all,
 * because a header row over an empty body would state that this site has no
 * devices, which is a claim about the site and not about its document.
 *
 * The heading is an `h3`. The Foundation subtab row names sections by their
 * panel headings, and T013 holds that no unlinked panel may sit between the
 * sections the row names, so these are subsections of Topology rather than
 * panels of their own.
 */
export interface SiteConfigurationSubsectionProps<T> {
  name: string;
  headingId: string;
  section: SiteDeclaredSection<T>;
  /** What the declared content means, rendered above the table. */
  caption: ReactNode;
  columns: string[];
  row: (entry: T) => { key: string; cells: ReactNode[] };
}

export function SiteConfigurationSubsection<T>({
  name,
  headingId,
  section,
  caption,
  columns,
  row,
}: SiteConfigurationSubsectionProps<T>) {
  if (section.status === "not_declared") {
    return (
      <div className="subsection">
        <h3 className="subsection__heading" id={headingId}>
          {name}
        </h3>
        <FactList>
          <SiteConfigurationStatedAbsence
            name={name}
            fact={section.absence}
          />
        </FactList>
      </div>
    );
  }

  return (
    <div className="subsection">
      <h3 className="subsection__heading" id={headingId}>
        {name}
      </h3>
      <DataTable labelledBy={headingId}>
        <caption>{caption}</caption>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column} scope="col">
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {section.entries.map((entry) => {
            const { key, cells } = row(entry);
            return (
              <tr key={key}>
                {cells.map((cell, index) => (
                  <td key={`${key}-${columns[index]}`}>{cell}</td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </DataTable>
    </div>
  );
}

/** Where each component sits in the declared topology. */
export function SiteTopologyNodes({
  section,
}: {
  section: SiteDeclaredSection<TopologyNodeView>;
}) {
  return (
    <SiteConfigurationSubsection
      name="Topology nodes"
      headingId="foundation-topology-nodes-heading"
      section={section}
      caption="Where each declared component sits in this site's topology. The role is its position in the topology, not its condition and not what it is doing."
      columns={["Component", "Role in topology", "Component ID", "Node ID"]}
      row={(node) => ({
        key: node.nodeId,
        cells: [
          <UserName key="component">{node.componentName}</UserName>,
          node.role,
          <ExactRef key="component-id">{node.componentId}</ExactRef>,
          <ExactRef key="node-id">{node.nodeId}</ExactRef>,
        ],
      })}
    />
  );
}

/** What the document declares is joined to what. */
export function SiteTopologyConnections({
  section,
}: {
  section: SiteDeclaredSection<TopologyConnectionView>;
}) {
  return (
    <SiteConfigurationSubsection
      name="Connections"
      headingId="foundation-topology-connections-heading"
      section={section}
      caption="The connections this site's foundation declares. The direction is the one the document declares; nothing here says anything has flowed."
      columns={["From", "To", "Carries", "Connection ID"]}
      row={(connection) => ({
        key: connection.connectionId,
        cells: [
          <UserName key="from">{connection.from}</UserName>,
          <UserName key="to">{connection.to}</UserName>,
          connection.medium,
          <ExactRef key="connection-id">{connection.connectionId}</ExactRef>,
        ],
      })}
    />
  );
}

/**
 * The devices the foundation declares, and what each can report.
 *
 * The signals column is availability: what this device is configured to be
 * able to send. There is no column for a value, an instant, or a condition,
 * because the record carries none - a configured device is awaiting runtime
 * and evidence, and a column here would have to invent what to put in it.
 */
export function SiteFoundationDevices({
  section,
}: {
  section: SiteDeclaredSection<FoundationDeviceView>;
}) {
  return (
    <SiteConfigurationSubsection
      name="Devices"
      headingId="foundation-devices-heading"
      section={section}
      caption="The devices this site's foundation declares. These are configured assets, not reports from them: whether any of them is reporting is not assessed here."
      columns={["Device", "Type", "Attached to", "Signals it can report", "Device ID"]}
      row={(device) => ({
        key: device.deviceId,
        cells: [
          <UserName key="device">{device.displayName}</UserName>,
          device.deviceType,
          <UserName key="attached-to">{device.attachedTo}</UserName>,
          <ul className="cell-list" key={`${device.deviceId}-signals`}>
            {device.signals.map((signal) => (
              <li key={signal.signalId}>
                <UserName>{signal.displayName}</UserName> ({signal.unit})
              </li>
            ))}
          </ul>,
          <ExactRef key="device-id">{device.deviceId}</ExactRef>,
        ],
      })}
    />
  );
}

/**
 * Which component each declared device signal describes.
 *
 * Declared, never inferred. A device attached to one component may describe
 * another - a meter on the bus describing the load it feeds - and only these
 * rows say so.
 */
export function SiteSignalMappings({
  section,
  basis = null,
}: {
  section: SiteDeclaredSection<SignalMappingView>;
  /** S1-02: set for an imported Site, whose rows are published bindings. */
  basis?: SignalMappingBasis | null;
}) {
  return (
    <SiteConfigurationSubsection
      name="Signal mappings"
      headingId="foundation-signal-mappings-heading"
      section={section}
      caption={basis === null ? LEGACY_SIGNAL_MAPPINGS_CAPTION : storedSignalMappingsCaption(basis)}
      columns={[
        "Signal",
        "Signal ID",
        "Unit",
        "Reported by",
        "Describes",
        basis === null ? "Mapping ID" : "Link reference",
      ]}
      row={(mapping) => ({
        key: mapping.mappingId,
        cells: [
          <UserName key="signal">{mapping.signalName}</UserName>,
          <ExactRef key="signal-id">{mapping.signalId}</ExactRef>,
          mapping.unit,
          <UserName key="device">{mapping.deviceName}</UserName>,
          <UserName key="describes">{mapping.describes}</UserName>,
          <ExactRef key="link-id">{mapping.mappingId}</ExactRef>,
        ],
      })}
    />
  );
}

const LEGACY_SIGNAL_MAPPINGS_CAPTION =
  "Which component each declared device signal describes. Every row is a declaration in this site's foundation: none is inferred from a name, a type, or a position in the topology.";

/**
 * S1-02 (Architect ruling D5): a stored Site's rows are the device-to-asset
 * links of the selected signal binding set, not declarations in the imported
 * document, whose mappings stay legacy comparison data and are not mixed in.
 */
function storedSignalMappingsCaption(basis: SignalMappingBasis): ReactNode {
  if (basis.bindingSetVersion === null) {
    return `No channel-link set is in effect for the period shown (Foundation v${basis.foundationVersion}), so this table lists no device-to-asset link. The imported document's signal links are legacy comparison data and are not shown here.`;
  }
  return (
    <>
      {`The device-to-asset links of the selected channel-link set: channel links v${basis.bindingSetVersion} (record `}
      <ExactRef>{basis.bindingSetRevisionId ?? ""}</ExactRef>
      {`), aligned to Foundation v${basis.foundationVersion}. Each row is a published channel link, identified by its link reference; the imported document's signal links are legacy comparison data and are not shown here.`}
    </>
  );
}

/**
 * The typed Site Controls the foundation declares (T024).
 *
 * Ordered lists of the site's own components - which source serves load first,
 * which load is protected first. Configured values a simulated run reads as
 * frozen inputs, and nothing on this screen changes one.
 */
export function SiteControlsTable({
  section,
}: {
  section: SiteDeclaredSection<SiteControlView>;
}) {
  return (
    <SiteConfigurationSubsection
      name="Site Controls"
      headingId="foundation-site-controls-heading"
      section={section}
      caption="Typed Site-scoped controls this site's foundation declares, each an ordered list of its components, first to last, with the document and version that declared it."
      columns={["Control", "Order", "Declared by"]}
      row={(control) => ({
        key: control.controlKey,
        cells: [control.displayName, <Fragment key="order">
            {control.orderNames.map((name, index) => (
              <Fragment key={`${index}-${name}`}>
                {index > 0 ? ", then " : null}
                <UserName>{name}</UserName>
              </Fragment>
            ))}
          </Fragment>, control.declaredBy],
      })}
    />
  );
}

/**
 * What the foundation assumes about how this site is operated.
 *
 * Assumptions in words, with what each is about and where it was declared.
 * There is no control state, no setpoint and no breaker position here: that
 * vocabulary is not decided, and a column for it would decide it.
 */
export function SiteControlAssumptions({
  section,
}: {
  section: SiteDeclaredSection<ControlAssumptionView>;
}) {
  return (
    <SiteConfigurationSubsection
      name="Control assumptions"
      headingId="foundation-control-assumptions-heading"
      section={section}
      caption="What this site's foundation assumes about how the site is intended to be operated. These are declared assumptions, not control actions, and none of them describes how the site has actually operated."
      columns={["Assumption", "Applies to", "Declared by", "What it assumes"]}
      row={(assumption) => ({
        key: assumption.assumptionId,
        cells: [
          <UserName key="assumption">{assumption.displayName}</UserName>,
          <UserName key="applies-to">{assumption.appliesTo}</UserName>,
          assumption.basis,
          assumption.statement,
        ],
      })}
    />
  );
}

/**
 * The headline numbers the foundation declares.
 *
 * Only what is there. A component with no declared rating produces no row -
 * not a dash, not a zero, not a greyed entry - because this panel is a list of
 * what the document states, and a blank line in it would read as a property of
 * the site rather than a gap in the document. The components table says which
 * components declare no rating, in words, which is the honest place for that.
 *
 * The panel does not render at all when the foundation declares no rated
 * component. An empty card headed `Key parameters` would be chrome claiming
 * content, which is the one thing every panel in this tree refuses.
 *
 * The value is the record's, verbatim, with the unit the record carries. No
 * conversion, no rounding, no unit the document did not choose: a number this
 * screen reformatted would be a number this screen authored.
 */
export interface SiteKeyParametersProps {
  parameters: SiteKeyParameterView[];
}

export function SiteKeyParameters({ parameters }: SiteKeyParametersProps) {
  if (parameters.length === 0) {
    return null;
  }

  return (
    <div className="subsection">
      <h3 className="subsection__heading" id="site-configuration-key-parameters-heading">
        Key parameters
      </h3>
      <FactList>
        {parameters.map((parameter) => (
          <Fact key={`${parameter.label}-${parameter.value}`} term={parameter.label}>
            {parameter.value}
          </Fact>
        ))}
      </FactList>
    </div>
  );
}
