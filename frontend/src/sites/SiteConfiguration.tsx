import type { ReactNode } from "react";

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
import {
  FOUNDATION_CONTROLS_ID,
  FOUNDATION_DEFINITION_ID,
  FOUNDATION_TOPOLOGY_ID,
  FoundationSubtabs,
} from "./FoundationSubtabs";
import type {
  ComponentPropertyView,
  ControlAssumptionView,
  FoundationDeviceView,
  SiteDeclaredSection,
  SiteKeyParameterView,
  SignalMappingView,
  TopologyConnectionView,
  TopologyNodeView,
} from "./siteViewModel";
import type { SiteDetailClient } from "./siteDirectoryClient";
import type { SiteDetailReadModel } from "./siteReadModel";
import { SiteSingleLineDiagram } from "./SiteSingleLineDiagram";
import { useSiteRecord } from "./useSiteRecord";
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
 * Where the new content sits is settled, not incidental. The subtab row names
 * Definition, Topology and Controls, and T013's rule is that no unlinked panel
 * may sit between the sections it names - so the topology, device and mapping
 * tables live INSIDE the Topology panel as subsections, and the components
 * table stays below Controls where T013 put it.
 */
export const SITE_CONFIGURATION_HEADING_ID = "site-configuration-heading";

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
   * The trail above this page, built by the shell from the canonical
   * `site_id`. Foundation sits two levels down, so its parent is the Site
   * itself, and the Site's crumb has to be spelled the way the record spells
   * it rather than the way the address did.
   */
  parentTrail?: (siteId: string) => Crumb[];
}

export function SiteConfiguration({
  siteId,
  detail,
  tabs,
  parentTrail,
}: SiteConfigurationProps) {
  const result = useSiteRecord(siteId, detail);

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
      parentTrail={parentTrail}
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
  /** See `SiteConfigurationProps.parentTrail`. */
  parentTrail?: (siteId: string) => Crumb[];
}

export function SiteConfigurationFacts({
  site,
  tabs,
  parentTrail,
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

      <FoundationSubtabs />

      {/*
        * Definition, as v6.9 names it. T011A left a panel headed `Foundation`
        * directly under a page titled `Foundation` and said this slice owned
        * the correction; this is it, and the panel now carries what the
        * criterion assigns to Definition: identity, summary, validity and
        * provenance, in one place rather than scattered across three panels
        * the subtab row does not name.
        */}
      <Panel
        heading="Definition"
        headingId={FOUNDATION_DEFINITION_ID}
      >
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
          <Fact term="Created from template">{view.templateProvenance}</Fact>
        </FactList>
        <p>{view.foundationValiditySemantics}</p>
        <p>
          These are separate facts about a site and none is derived from
          another. Configuration origin is where this site&apos;s configuration
          document came from. Mode is where the site&apos;s evidence comes
          from, and it is provenance rather than status, health, or an
          assessment. Lifecycle status is where the site is in its own life.
        </p>
      </Panel>

      <Panel
        heading="Configuration is fixed at creation"
        headingId="site-configuration-fixed-heading"
      >
        <p>{view.configurationFixedAtCreation}</p>
      </Panel>

      <SiteKeyParameters parameters={view.keyParameters} />

      <Panel
        heading="Topology"
        headingId={FOUNDATION_TOPOLOGY_ID}
      >
        <p>
          What this site&apos;s foundation declares about how its components
          are joined, which devices are configured against them, and which
          component each device signal describes. All of it is configuration
          read back. Nothing here is a reading: no device has reported, and no
          value below has ever been measured.
        </p>

        {/*
          * Topology is one declaration, so it is one absence. When a document
          * declares none, the nodes and the connections are not two separate
          * things missing: the statement is made once, under the name the
          * subtab row uses, rather than repeated under two subsection
          * headings that would both give the same reason.
          */}
        {/*
          * The diagram comes first inside Topology, above the tables that say
          * the same thing in rows. It is the same facts in two forms and the
          * drawing is the one a reader looks at first; putting it under six
          * tables would make the section read as though the tables were the
          * subject and the diagram an afterthought.
          *
          * It is a subsection and not a panel of its own. T013's rule is that
          * no unlinked panel may sit between the sections the Foundation row
          * names, and a panel headed for the diagram between Topology and
          * Controls would make the row misleading about where Topology ends.
          */}
        <SiteSingleLineDiagram site={site} />

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
        <SiteSignalMappings section={view.signalMappings} />

        {/*
          * Two device facts this build does not hold, stated once rather than
          * given a column each. `.ai/FEATURE_MAP.md` lists protocol metadata
          * and sample cadence as prerequisites of this feature area; T014's
          * schema carries neither, and the parser refuses a document that
          * declares one. A column of dashes would say the product looked for a
          * protocol and found none, which is a claim about the device.
          */}
        <p className="note">{FOUNDATION_DEVICE_METADATA_LIMITS}</p>
      </Panel>

      <Panel
        heading="Controls"
        headingId={FOUNDATION_CONTROLS_ID}
      >
        {/*
          * Two different kinds of fact under one heading, and the order says
          * which is which. The declared control properties are configured
          * numbers with units; the control assumptions below are statements
          * in words about how the site is intended to be operated. Neither is
          * a control: nothing on this screen issues one, and the note on the
          * properties table says so where a reader meets the numbers.
          */}
        <SiteControlProperties section={view.controlProperties} />
        <SiteControlAssumptions section={view.controlAssumptions} />
      </Panel>

      {/*
        * The components table sits after Controls, not between Topology and
        * Controls where T013 first put it.
        *
        * The row names Topology and Controls and does not name this, and an
        * unnamed panel wedged between two named ones makes the row misleading
        * about where a section ends. It also had a measurable cost: with this
        * table above it, Controls could be reached only by the document
        * clamping at the bottom of the page, so its link landed 336px from the
        * top while every other link landed at 24px.
        */}
      <SiteConfigurationComponents components={view.components} />

      {/*
        * The typed physical properties sit with the components rather than
        * with Controls, because what a tank holds and what a generator burns
        * are facts about what those machines ARE. The control properties are
        * under Controls, beside the assumptions they make concrete.
        */}
      <Panel
        heading="Declared component properties"
        headingId="site-configuration-physical-properties-heading"
        flush
      >
        <SitePhysicalProperties section={view.physicalProperties} />
      </Panel>

      <Panel
        heading="Not available for this site"
        headingId="site-configuration-no-evidence-heading"
      >
        <FactList>
          <SiteConfigurationStatedAbsence
            name="Integration readiness"
            fact={view.integrationReadiness}
          />
          <SiteConfigurationStatedAbsence
            name="Evidence availability"
            fact={view.evidenceAvailability}
          />
          <SiteConfigurationStatedAbsence
            name="Source health"
            fact={view.sourceHealth}
          />
        </FactList>
        <p>
          Nothing below the configuration exists for this site yet. There is no
          accepted evidence, so there is nothing to chart, nothing to analyse,
          nothing to replay, and no finding to draw. Each of those arrives with
          the evidence that fills it rather than as an empty version of itself.
        </p>
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
    <Panel
      heading="Components"
      headingId="site-configuration-components-heading"
      flush
    >
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
              <td>{component.displayName}</td>
              <td>{component.componentType}</td>
              <td>{component.rating}</td>
              <td>{component.componentId}</td>
            </tr>
          ))}
        </tbody>
      </DataTable>
    </Panel>
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
          property.componentName,
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
            property.componentName,
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
  caption: string;
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
        cells: [node.componentName, node.role, node.componentId, node.nodeId],
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
          connection.from,
          connection.to,
          connection.medium,
          connection.connectionId,
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
      caption="The devices this site's foundation declares. These are configured assets awaiting runtime and evidence: none has reported, and nothing here states that any of them is reporting or that any is not."
      columns={["Device", "Type", "Attached to", "Signals it can report", "Device ID"]}
      row={(device) => ({
        key: device.deviceId,
        cells: [
          device.displayName,
          device.deviceType,
          device.attachedTo,
          <ul className="cell-list" key={`${device.deviceId}-signals`}>
            {device.signals.map((signal) => (
              <li key={signal.signalId}>
                {signal.displayName} ({signal.unit})
              </li>
            ))}
          </ul>,
          device.deviceId,
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
}: {
  section: SiteDeclaredSection<SignalMappingView>;
}) {
  return (
    <SiteConfigurationSubsection
      name="Signal mappings"
      headingId="foundation-signal-mappings-heading"
      section={section}
      caption="Which component each declared device signal describes. Every row is a declaration in this site's foundation: none is inferred from a name, a type, or a position in the topology."
      columns={[
        "Signal",
        "Signal ID",
        "Unit",
        "Reported by",
        "Describes",
        "Mapping ID",
      ]}
      row={(mapping) => ({
        key: mapping.mappingId,
        cells: [
          mapping.signalName,
          mapping.signalId,
          mapping.unit,
          mapping.deviceName,
          mapping.describes,
          mapping.mappingId,
        ],
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
      caption="What this site's foundation assumes about how the site is intended to be operated. These are declared assumptions, not control actions, and none of them describes how the site has actually run."
      columns={["Assumption", "Applies to", "Declared by", "What it assumes"]}
      row={(assumption) => ({
        key: assumption.assumptionId,
        cells: [
          assumption.displayName,
          assumption.appliesTo,
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
    <Panel
      heading="Key parameters"
      headingId="site-configuration-key-parameters-heading"
    >
      <FactList>
        {parameters.map((parameter) => (
          <Fact key={`${parameter.label}-${parameter.value}`} term={parameter.label}>
            {parameter.value}
          </Fact>
        ))}
      </FactList>
    </Panel>
  );
}
