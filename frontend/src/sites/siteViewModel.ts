/**
 * The Site view model: the one place a site record becomes display.
 *
 * Vocabulary lives here and nowhere else, because the failure this substrate
 * exists to prevent is two shells labelling the same field differently. Every
 * label, every fallback, and every unavailable state is decided once.
 *
 * The rule this module must not break: configuration origin, source mode, and
 * lifecycle status are independent facts and none is derived from, defaulted
 * from, or rendered as a proxy for another. In M1 every `USER`-origin site
 * also has `SIMULATED` source mode, because the Simulator Lab is the only
 * creation path. They coincide by circumstance, not by definition, so nothing
 * here may compute one from the other: a shipped demo site would be `SHIPPED`
 * plus `SIMULATED`, and a site registered against a real integration would be
 * `USER` plus `LIVE`.
 *
 * `Simulated` is the rendering of `source.mode`. It is provenance, never
 * status, never health, and never an assessment, so it never shares a column
 * or a label with lifecycle status.
 *
 * An unrecognised value is shown as it arrived rather than mapped to a
 * plausible-looking label. Inventing a label for a value this build does not
 * know would be a claim about a site rather than a statement about the record.
 */

import type {
  ControlAssumptionReadModel,
  FoundationDeviceReadModel,
  SignalMappingReadModel,
  SiteComponentReadModel,
  SiteDetailReadModel,
  SiteSummary,
  TopologyConnectionReadModel,
  TopologyNodeReadModel,
} from "./siteReadModel";

/** What the Sites index renders for one site. */
export interface SiteView {
  siteId: string;
  displayName: string;
  siteType: string;
  location: string;
  lifecycleStatus: string;
  sourceMode: string;
  configurationOrigin: string;
  templateProvenance: string;
  /** See `NO_ANALYSIS_IN_WINDOW`. Always that value in M1. */
  lastAnalysed: string;
}

const SITE_TYPE_LABELS: Record<string, string> = {
  MINIGRID: "Mini-grid",
  COLDCHAIN: "Cold chain",
};

const LIFECYCLE_STATUS_LABELS: Record<string, string> = {
  PLANNED: "Planned",
  COMMISSIONED: "Commissioned",
  ACTIVE: "Active",
  DECOMMISSIONED: "Decommissioned",
  ARCHIVED: "Archived",
};

const SOURCE_MODE_LABELS: Record<string, string> = {
  SIMULATED: "Simulated",
  LIVE: "Live",
};

const CONFIGURATION_ORIGIN_LABELS: Record<string, string> = {
  USER: "User",
  SHIPPED: "Shipped",
};

/** What a site with no template provenance shows. It came from no template. */
export const NO_TEMPLATE_PROVENANCE = "Not created from a template";

/**
 * What the `Last analysed` column shows while no evidence has been analysed.
 *
 * This is v6.9's own rendering for a site with no data in the selected window,
 * not a placeholder standing in for a timestamp the product will fill in later.
 * The canonical mockup puts real timestamps in this column; those are evidence
 * the product does not have, and reproducing them would be the clearest case of
 * a mockup literal becoming content.
 *
 * It is a constant rather than a literal in the table so that the day evidence
 * exists, there is one place that stops being true.
 */
export const NO_ANALYSIS_IN_WINDOW = "--";

/**
 * A canonical value rendered in the words a reader sees, or the value itself.
 *
 * Exported because the diagram and the tables must spell a role and a medium
 * the same way. Two label maps for one vocabulary is how a screen comes to
 * call the same thing two things.
 */
export function label(value: string, labels: Record<string, string>): string {
  return labels[value] ?? value;
}

export function deriveSiteView(site: SiteSummary): SiteView {
  return {
    siteId: site.site_id,
    displayName: site.display_name,
    siteType: label(site.site_type, SITE_TYPE_LABELS),
    location: `${site.location.locality}, ${site.location.country}`,
    lifecycleStatus: label(site.lifecycle_status, LIFECYCLE_STATUS_LABELS),
    sourceMode: label(site.source.mode, SOURCE_MODE_LABELS),
    configurationOrigin: label(site.origin, CONFIGURATION_ORIGIN_LABELS),
    templateProvenance:
      site.template === null
        ? NO_TEMPLATE_PROVENANCE
        : `${site.template.template_id} v${site.template.template_version}`,
    lastAnalysed: NO_ANALYSIS_IN_WINDOW,
  };
}

/**
 * A fact the product cannot state for a configuration-only site, and the
 * reason it cannot.
 *
 * The reason is not decoration. "No evidence" without a reason reads as a
 * measurement of zero; with one it reads as what it is, a statement about what
 * has been recorded. Every one of these is written here rather than in a
 * component, so the two shells cannot explain the same absence differently.
 */
export interface SiteUnavailableFact {
  value: string;
  reason: string;
}

/**
 * What a site page renders for one site.
 *
 * The six provenance-and-status concepts appear here as six fields, never as
 * one. Three come straight off the record - configuration origin, source mode,
 * lifecycle status. Three have no field behind them in this build -
 * integration readiness, evidence availability, source health - and each is
 * stated as unavailable with its reason rather than defaulted, zeroed, or
 * derived from one of the other three.
 *
 * Each of those three says what this build records, not what the site has.
 * The record carries no integration field and no source-health field, so a
 * sentence here about how a site is integrated, or about whether its source
 * reports, would be a claim this substrate cannot back for the site in front
 * of it. Source health in particular is not rendered as a health value, and no
 * source-health vocabulary appears here.
 */
export interface SiteDetailView extends SiteView {
  timezone: string;
  foundationVersion: string;
  foundationValidFrom: string;
  /** The summary the foundation document carries, verbatim. */
  foundationSummary: string;
  integrationReadiness: SiteUnavailableFact;
  evidenceAvailability: SiteUnavailableFact;
  sourceHealth: SiteUnavailableFact;
}

/**
 * Integration readiness: a separate concept, with no field behind it.
 *
 * What this states is what the build records, because that is all the record
 * proves. "No integration is configured for this site" would be a claim about
 * the site, and nothing in the record says whether one is: a site registered
 * against a real integration would arrive here with the same fields and be
 * described wrongly by it.
 */
export const INTEGRATION_READINESS_UNAVAILABLE: SiteUnavailableFact = {
  value: "Not recorded",
  reason:
    "This build records no integration readiness for a site, so nothing here " +
    "states whether an integration is configured. Readiness is its own fact: " +
    "it is not lifecycle status, not source mode, and not derived from either.",
};

/** Evidence availability: a statement about evidence, not a measurement. */
export const EVIDENCE_AVAILABILITY_UNAVAILABLE: SiteUnavailableFact = {
  value: "No evidence",
  reason:
    "No evidence has been accepted for this site, so there is nothing to " +
    "show and nothing to analyse. This is a statement about evidence, not a " +
    "reading of zero and not a statement about the site's lifecycle status.",
};

/**
 * Source health: not recorded, because the record carries no health field.
 *
 * Not "not applicable", which would state that this site's source could have
 * no health, and not "no source is expected to report", which would state
 * something about the site's source that the record does not carry. What is
 * true is about the build: it records no source health for any site.
 */
export const SOURCE_HEALTH_UNAVAILABLE: SiteUnavailableFact = {
  value: "Not recorded",
  reason:
    "This build records no source health for a site, and the record carries " +
    "no field that could carry one. Nothing here states whether this site's " +
    "source is reporting, so nothing here is a health value.",
};

export function deriveSiteDetailView(site: SiteDetailReadModel): SiteDetailView {
  return {
    ...deriveSiteView(site),
    timezone: site.timezone,
    foundationVersion: `${site.foundation.version}`,
    foundationValidFrom: site.foundation.valid_from,
    foundationSummary: site.foundation.summary,
    integrationReadiness: INTEGRATION_READINESS_UNAVAILABLE,
    evidenceAvailability: EVIDENCE_AVAILABILITY_UNAVAILABLE,
    sourceHealth: SOURCE_HEALTH_UNAVAILABLE,
  };
}

/**
 * One component a site's foundation declares, as display.
 *
 * The rating is the archetype's declared design rating, copied from the
 * template when the site was created. It is nameplate intent from a document
 * and never a measurement, so it is never rendered beside, or in the
 * vocabulary of, anything a device has reported.
 */
export interface SiteComponentView {
  componentId: string;
  displayName: string;
  componentType: string;
  rating: string;
}

/**
 * What a component with no declared rating shows.
 *
 * Not `0`, and not an empty cell. A component that declares no rating and a
 * component rated at zero are different facts, and the document states only
 * the first.
 */
export const NO_RATING_DECLARED = "No rating declared";

export const COMPONENT_TYPE_LABELS: Record<string, string> = {
  PV_ARRAY: "PV array",
  INVERTER: "Inverter",
  BATTERY: "Battery",
  POWER_CONVERSION_SYSTEM: "Power conversion system",
  GENERATOR: "Generator",
  FUEL_TANK: "Fuel tank",
  AC_BUS: "AC bus",
  LOAD: "Load",
  COLD_ROOM: "Cold room",
  METER: "Meter",
};

/**
 * The statement that configuration does not change after a site is created.
 *
 * Written once, here, because it is the load-bearing sentence of this surface:
 * it is what makes the absence of every editing control a stated product
 * position rather than something a user has to infer from an empty toolbar.
 *
 * It says what M1 does and does not do. It does not say "not yet", does not
 * name an editing workflow, and does not describe the present arrangement as
 * temporary, because none of those is a promise this product has made.
 */
export const CONFIGURATION_FIXED_AT_CREATION =
  "Configuration is fixed at creation in M1. A site's foundation is copied " +
  "from its template when the site is created, and AssetOps does not edit a " +
  "site's foundation in this milestone.";

/**
 * What the foundation's validity interval means, stated rather than implied.
 *
 * The interval is half-open and open-ended: it includes the instant it starts
 * and has no recorded end. Rendering a start date alone would leave a reader
 * to guess whether the configuration has since stopped applying.
 */
export const FOUNDATION_VALIDITY_SEMANTICS =
  "The interval is half-open: it includes the instant it starts and has no " +
  "recorded end, because a foundation stays valid until a later version " +
  "supersedes it. This is the validity of one configuration document. It is " +
  "not a configuration history, and this build records no change to a " +
  "foundation.";

/**
 * A part of a site's configuration this site's foundation does not declare.
 *
 * T008 wrote these because the M1 schema had nowhere to put a device. T014
 * gives it somewhere, so the reason moved: it is no longer about what a
 * foundation CAN carry, it is about what THIS foundation does carry. The
 * distinction is the whole of why these constants survive the slice that made
 * them look redundant.
 *
 * They are stated rather than omitted, and the reason does the work. Silence
 * about devices on a screen presenting itself as a site's configuration would
 * read as "this site has no devices". What is true is narrower: this site's
 * configuration document declares none, and a document is not the world.
 *
 * None of these is a placeholder for a future panel. There is no empty frame,
 * no heading reserved for content that has not landed, and nothing here names
 * a screen the product does not have. An empty table would be worse than
 * either: a table with a header row and no rows is a screen saying it looked
 * and found nothing.
 */
export const TOPOLOGY_NOT_DECLARED: SiteUnavailableFact = {
  value: "Not declared",
  reason:
    "This site's foundation document declares no topology, so nothing here " +
    "states how its components are joined. The components it declares are " +
    "listed below; how they connect is a separate declaration this document " +
    "does not make.",
};

export const DEVICES_NOT_DECLARED: SiteUnavailableFact = {
  value: "Not declared",
  reason:
    "This site's foundation document declares no device. A foundation can " +
    "carry devices and the signals they are configured to report; this one " +
    "does not. That is a statement about the document, not a statement that " +
    "this site has no devices.",
};

export const SIGNAL_MAPPINGS_NOT_DECLARED: SiteUnavailableFact = {
  value: "Not declared",
  reason:
    "This site's foundation document declares no device-to-signal mapping. " +
    "A mapping is declared and never inferred: nothing derives one from a " +
    "device name, a component type, or a position in the topology, so where " +
    "a document declares none, none is stated.",
};

/**
 * The two device facts a foundation in this build cannot carry.
 *
 * `.ai/FEATURE_MAP.md` names protocol metadata and sample cadence as
 * prerequisites of the topology and device feature area, and T014's schema
 * declares neither: the parser refuses a device that carries a protocol key
 * and refuses a signal that carries a cadence. So this is a statement about
 * what a document in this build can say, made once in words, rather than a
 * column of dashes - which would say the product looked at this device and
 * found no protocol, a claim about the device instead of about the schema.
 */
export const FOUNDATION_DEVICE_METADATA_LIMITS =
  "A foundation in this build declares a device's identity, its type, the " +
  "component it is attached to, and the signals it can report. It carries no " +
  "protocol label and no sampling interval for any device, so neither is " +
  "stated here for any of them. That is a limit of the configuration " +
  "document, not something looked for and missing on these devices.";

/**
 * One typed property a component declares, as display.
 *
 * The value carries the unit the document chose, verbatim: no conversion, no
 * rounding, no unit this screen picked. A number a screen reformatted is a
 * number that screen authored.
 *
 * `declaredBy` is the property's own provenance - which document declared it
 * and at which version - rendered per row rather than per component, because
 * a site may declare one of its own beside one it copied from a template.
 */
export interface ComponentPropertyView {
  key: string;
  componentName: string;
  propertyName: string;
  value: string;
  declaredBy: string;
}

/**
 * What the Foundation says when no component declares a physical property.
 *
 * A statement about the document, as every absence on this screen is. A site
 * created before typed properties existed declares none, and a template that
 * later gains them does not reach back into it: templates copy at creation.
 */
export const PHYSICAL_PROPERTIES_NOT_DECLARED: SiteUnavailableFact = {
  value: "Not declared",
  reason:
    "This site's foundation document declares no typed physical property on " +
    "any component. A component may still carry a nameplate rating above: a " +
    "rating and a typed property are different facts, and this says only " +
    "that no property is declared. It is a statement about the document, not " +
    "a statement that these components have no such properties.",
};

/**
 * What the Foundation says when no component declares a control property.
 *
 * Deliberately worded as configuration. A declared control property is a
 * number a component is configured with; it is not a setpoint anything writes,
 * not a controller, and nothing in this build acts on one.
 */
export const CONTROL_PROPERTIES_NOT_DECLARED: SiteUnavailableFact = {
  value: "Not declared",
  reason:
    "This site's foundation document declares no typed control property on " +
    "any component, so no reserve level or minimum runtime is configured " +
    "here. That is a statement about the document, and it is not a statement " +
    "that this site is operated without limits.",
};

/**
 * What a declared control property is, said once, beside the table.
 *
 * The one thing this screen must not imply. A typed control property is a
 * configured number a reader can inspect: nothing in this build reads one to
 * decide anything and nothing writes one to a machine.
 *
 * Worded without the banned control vocabulary, deliberately. A denial that
 * used the word would put the word on the screen, and the ban is on the word
 * appearing at all - "this is not a X" is exactly the cover the T016
 * restriction refuses.
 */
export const CONTROL_PROPERTIES_ARE_NOT_CONTROLS =
  "These are declared configuration values, not controls. Nothing on this " +
  "screen issues a control action, nothing in this build writes one of these " +
  "values to a machine, and nothing reads one to decide anything.";

export const CONTROL_ASSUMPTIONS_NOT_DECLARED: SiteUnavailableFact = {
  value: "Not declared",
  reason:
    "This site's foundation document declares no control assumption, so " +
    "nothing here states how this site is expected to be operated. That is a " +
    "statement about the document, not a statement that this site is " +
    "uncontrolled.",
};

/**
 * What the read-only Site Configuration surface renders for one site.
 *
 * Everything a site page states about identity and provenance, plus the
 * content of the foundation document: its version, what its validity interval
 * means, its summary, and the components it declares.
 *
 * The six provenance-and-status concepts stay six here exactly as they are on
 * the site page, and for the same reason: this screen is a second place they
 * could be collapsed into one another, and one derivation in one view model
 * would be enough to make the two screens disagree about what a site is.
 */
/**
 * One headline number the foundation actually declares.
 *
 * Derived only from components that carry a rating. A component with no
 * declared rating produces no key parameter at all - not a dash, not a zero,
 * not an empty row. The components table already states that component's
 * absence of a rating in words, which is a statement about the document; a
 * blank line in a parameters list would read as a property of the site.
 */
export interface SiteKeyParameterView {
  /** The component the parameter belongs to. */
  label: string;
  /** The declared value with its canonical unit, exactly as the record has it. */
  value: string;
}

/**
 * One declared topology node, as display.
 *
 * The component's name rather than its identity carries the row, because a
 * reader looking at a topology is looking for the thing, not its key. The
 * identity is still rendered: it is what a later mapping, diagram or evidence
 * record is keyed on, and a table that hid it would leave a reader unable to
 * follow a mapping back to the component it names.
 */
export interface TopologyNodeView {
  nodeId: string;
  componentName: string;
  componentId: string;
  role: string;
}

/**
 * One declared connection, as display.
 *
 * Named by the components at each end, because `pv-inverter to ac-bus` is a
 * fact about two components and a reader should not have to resolve two node
 * identities to see it. The direction is the document's declared direction and
 * is never described as flow: nothing has flowed.
 */
export interface TopologyConnectionView {
  connectionId: string;
  from: string;
  to: string;
  medium: string;
}

/** One signal a device is configured to be able to report, as display. */
export interface DeviceSignalView {
  signalId: string;
  displayName: string;
  unit: string;
}

/**
 * One declared device, as display.
 *
 * `attachedTo` is the component the document attaches it to. There is no
 * status, no health, no last-seen and no reading, because the record carries
 * none: a configured device is awaiting runtime and evidence, and this row
 * says only what was configured.
 */
export interface FoundationDeviceView {
  deviceId: string;
  displayName: string;
  deviceType: string;
  attachedTo: string;
  signals: DeviceSignalView[];
}

/**
 * One declared device-to-signal mapping, as display.
 *
 * Every field traces to the document. The component a signal describes is the
 * mapping's own declaration and is not the device's component: a meter on the
 * bus may describe the load, and only the mapping says so.
 */
export interface SignalMappingView {
  mappingId: string;
  signalId: string;
  signalName: string;
  deviceName: string;
  describes: string;
  unit: string;
}

/**
 * One declared control assumption, as display.
 *
 * `appliesTo` is the component the assumption is about, or the site when the
 * document names no component. That is not a missing value: an assumption
 * about dispatch order is about the site, and naming a component for it would
 * be an invention.
 */
export interface ControlAssumptionView {
  assumptionId: string;
  displayName: string;
  appliesTo: string;
  basis: string;
  statement: string;
}

/**
 * What a site page shows for a section its foundation may or may not declare.
 *
 * Exactly one of the two is present. `entries` is what the document declares;
 * `absence` is the statement that it declares none, with its reason. There is
 * no third state and no empty `entries`, because an empty list rendered as a
 * table would say the product looked and found nothing.
 */
export type SiteDeclaredSection<T> =
  | { status: "declared"; entries: T[] }
  | { status: "not_declared"; absence: SiteUnavailableFact };

export interface SiteConfigurationView extends SiteDetailView {
  foundationSummary: string;
  foundationValiditySemantics: string;
  configurationFixedAtCreation: string;
  components: SiteComponentView[];
  keyParameters: SiteKeyParameterView[];
  physicalProperties: SiteDeclaredSection<ComponentPropertyView>;
  controlProperties: SiteDeclaredSection<ComponentPropertyView>;
  topologyNodes: SiteDeclaredSection<TopologyNodeView>;
  topologyConnections: SiteDeclaredSection<TopologyConnectionView>;
  devices: SiteDeclaredSection<FoundationDeviceView>;
  signalMappings: SiteDeclaredSection<SignalMappingView>;
  controlAssumptions: SiteDeclaredSection<ControlAssumptionView>;
}

/** What a topology node's role is called on screen. */
export const TOPOLOGY_NODE_ROLE_LABELS: Record<string, string> = {
  GENERATION: "Generation",
  CONVERSION: "Conversion",
  STORAGE: "Storage",
  BUS: "Bus",
  METERING: "Metering",
  LOAD: "Load",
  FUEL_STORAGE: "Fuel storage",
};

/** What a connection carries, as the document declares it. */
export const CONNECTION_MEDIUM_LABELS: Record<string, string> = {
  AC: "AC",
  DC: "DC",
  FUEL: "Fuel",
};

const DEVICE_TYPE_LABELS: Record<string, string> = {
  METER: "Meter",
  SENSOR: "Sensor",
  CONTROLLER: "Controller",
};

/** Where a control assumption was declared. Provenance, not a control value. */
const CONTROL_ASSUMPTION_BASIS_LABELS: Record<string, string> = {
  TEMPLATE: "Template",
  SITE: "Site",
};

/** What a control assumption that names no component applies to. */
export const ASSUMPTION_APPLIES_TO_SITE = "The whole site";

/**
 * A component's display name, by identity.
 *
 * The parser refuses a document whose references do not resolve, so every
 * lookup below finds one. The fallback is the identity itself rather than a
 * blank or an invented label: if a reference ever did dangle, the screen shows
 * what the document said and does not pretend to know more.
 */
function nameComponents(
  components: SiteComponentReadModel[],
): Record<string, string> {
  const names: Record<string, string> = {};
  for (const component of components) {
    names[component.component_id] = component.display_name;
  }
  return names;
}

function declared<T>(entries: T[]): SiteDeclaredSection<T> {
  return { status: "declared", entries };
}

function notDeclared<T>(absence: SiteUnavailableFact): SiteDeclaredSection<T> {
  return { status: "not_declared", absence };
}

export function deriveSiteComponentView(
  component: SiteComponentReadModel,
): SiteComponentView {
  return {
    componentId: component.component_id,
    displayName: component.display_name,
    componentType: label(component.component_type, COMPONENT_TYPE_LABELS),
    rating:
      component.rating === null
        ? NO_RATING_DECLARED
        : `${component.rating.value} ${component.rating.unit}`,
  };
}

export function deriveSiteConfigurationView(
  site: SiteDetailReadModel,
): SiteConfigurationView {
  return {
    ...deriveSiteDetailView(site),
    foundationSummary: site.foundation.summary,
    foundationValiditySemantics: FOUNDATION_VALIDITY_SEMANTICS,
    configurationFixedAtCreation: CONFIGURATION_FIXED_AT_CREATION,
    components: site.foundation.components.map(deriveSiteComponentView),
    // Filtered on the record, not on the rendered string. A component whose
    // rating is absent is dropped here rather than rendered as an absence,
    // because a parameters list is a list of what the foundation declares and
    // an entry that declares nothing does not belong in one.
    keyParameters: [
      ...site.foundation.components
        .filter((component) => component.rating !== null)
        .map((component) => ({
          label: label(component.component_type, COMPONENT_TYPE_LABELS),
          value: `${component.rating?.value} ${component.rating?.unit}`,
        })),
      // The declared physical properties sit beside the ratings, because
      // they are the same kind of thing to a reader: a headline number the
      // foundation states. They are listed after rather than merged into the
      // ratings, so a rating and a property of the same component stay two
      // rows and neither has to stand for the other.
      ...site.foundation.components.flatMap((component) =>
        (component.properties ?? [])
          .filter((property) => property.kind === "PHYSICAL")
          .map((property) => ({
            label: `${component.display_name} ${property.display_name.toLowerCase()}`,
            value: `${property.value} ${property.unit}`,
          })),
      ),
    ],
    physicalProperties: deriveComponentProperties(site, "PHYSICAL"),
    controlProperties: deriveComponentProperties(site, "CONTROL"),
    topologyNodes: deriveTopologyNodes(site),
    topologyConnections: deriveTopologyConnections(site),
    devices: deriveDevices(site),
    signalMappings: deriveSignalMappings(site),
    controlAssumptions: deriveControlAssumptions(site),
  };
}

/**
 * The topology nodes, or the statement that the document declares none.
 *
 * Derived from `foundation.topology` alone. Nothing here infers a node from a
 * component: a site whose foundation lists nine components and no topology has
 * no topology, and saying otherwise would invent nine positions the document
 * never declared.
 */
export function deriveTopologyNodes(
  site: SiteDetailReadModel,
): SiteDeclaredSection<TopologyNodeView> {
  const topology = site.foundation.topology;
  if (topology === null) {
    return notDeclared(TOPOLOGY_NOT_DECLARED);
  }

  const names = nameComponents(site.foundation.components);

  return declared(
    topology.nodes.map((node: TopologyNodeReadModel) => ({
      nodeId: node.node_id,
      componentName: names[node.component_id] ?? node.component_id,
      componentId: node.component_id,
      role: label(node.node_role, TOPOLOGY_NODE_ROLE_LABELS),
    })),
  );
}

export function deriveTopologyConnections(
  site: SiteDetailReadModel,
): SiteDeclaredSection<TopologyConnectionView> {
  const topology = site.foundation.topology;
  if (topology === null) {
    return notDeclared(TOPOLOGY_NOT_DECLARED);
  }

  const names = nameComponents(site.foundation.components);
  const nodeNames: Record<string, string> = {};
  for (const node of topology.nodes) {
    nodeNames[node.node_id] = names[node.component_id] ?? node.component_id;
  }

  return declared(
    topology.connections.map((connection: TopologyConnectionReadModel) => ({
      connectionId: connection.connection_id,
      from: nodeNames[connection.from_node] ?? connection.from_node,
      to: nodeNames[connection.to_node] ?? connection.to_node,
      medium: label(connection.medium, CONNECTION_MEDIUM_LABELS),
    })),
  );
}

export function deriveDevices(
  site: SiteDetailReadModel,
): SiteDeclaredSection<FoundationDeviceView> {
  const devices = site.foundation.devices;
  if (devices === null) {
    return notDeclared(DEVICES_NOT_DECLARED);
  }

  const names = nameComponents(site.foundation.components);

  return declared(
    devices.map((device: FoundationDeviceReadModel) => ({
      deviceId: device.device_id,
      displayName: device.display_name,
      deviceType: label(device.device_type, DEVICE_TYPE_LABELS),
      attachedTo: names[device.component_id] ?? device.component_id,
      signals: device.signals.map((signal) => ({
        signalId: signal.signal_id,
        displayName: signal.display_name,
        unit: signal.unit,
      })),
    })),
  );
}

/**
 * The declared mappings, resolved to the names a reader can follow.
 *
 * The signal's name and unit come from the device that declares it, which is
 * the only place they exist. Resolving them here rather than in a component
 * keeps the rule in one place: a mapping names a device and a signal, and the
 * device is what says what that signal is.
 */
export function deriveSignalMappings(
  site: SiteDetailReadModel,
): SiteDeclaredSection<SignalMappingView> {
  const mappings = site.foundation.signal_mappings;
  if (mappings === null) {
    return notDeclared(SIGNAL_MAPPINGS_NOT_DECLARED);
  }

  const componentNames = nameComponents(site.foundation.components);
  const devices = site.foundation.devices ?? [];
  const deviceNames: Record<string, string> = {};
  const signals: Record<string, DeviceSignalView> = {};
  for (const device of devices) {
    deviceNames[device.device_id] = device.display_name;
    for (const signal of device.signals) {
      signals[`${device.device_id}/${signal.signal_id}`] = {
        signalId: signal.signal_id,
        displayName: signal.display_name,
        unit: signal.unit,
      };
    }
  }

  return declared(
    mappings.map((mapping: SignalMappingReadModel) => {
      const signal = signals[`${mapping.device_id}/${mapping.signal_id}`];
      return {
        mappingId: mapping.mapping_id,
        // The mapping's own signal identity, not the device's display name for
        // it. A signal id is unique within its device only, so the row carries
        // both: the id the document binds by and the device that declares it.
        signalId: mapping.signal_id,
        signalName: signal?.displayName ?? mapping.signal_id,
        deviceName: deviceNames[mapping.device_id] ?? mapping.device_id,
        describes:
          componentNames[mapping.component_id] ?? mapping.component_id,
        unit: signal?.unit ?? "",
      };
    }),
  );
}

/**
 * The typed properties of one kind, or the statement that none is declared.
 *
 * Derived from what the components declare and nothing else. Nothing here
 * infers a property from a component type, from a rating that happens to
 * carry the same unit, or from a display name: a property is declared or the
 * foundation does not have one.
 *
 * Split by kind rather than rendered in one table with a kind column. A tank
 * capacity and a reserve level are different kinds of fact - one is what the
 * machine IS, the other is how it is configured to be operated - and a shared
 * table would put the second under whatever heading the first earned.
 */
export function deriveComponentProperties(
  site: SiteDetailReadModel,
  kind: string,
): SiteDeclaredSection<ComponentPropertyView> {
  const names = nameComponents(site.foundation.components);

  const rows = site.foundation.components.flatMap((component) =>
    (component.properties ?? [])
      .filter((property) => property.kind === kind)
      .map((property) => ({
        key: `${component.component_id}/${property.property_key}`,
        componentName:
          names[component.component_id] ?? component.component_id,
        propertyName: property.display_name,
        value: `${property.value} ${property.unit}`,
        declaredBy: `${label(
          property.source,
          COMPONENT_PROPERTY_SOURCE_LABELS,
        )} version ${property.source_version}`,
      })),
  );

  if (rows.length === 0) {
    return notDeclared(
      kind === "CONTROL"
        ? CONTROL_PROPERTIES_NOT_DECLARED
        : PHYSICAL_PROPERTIES_NOT_DECLARED,
    );
  }

  return declared(rows);
}

/** Which document declared a property, as display. */
export const COMPONENT_PROPERTY_SOURCE_LABELS: Record<string, string> = {
  TEMPLATE: "Template",
  SITE: "This site",
};

export function deriveControlAssumptions(
  site: SiteDetailReadModel,
): SiteDeclaredSection<ControlAssumptionView> {
  const assumptions = site.foundation.control_assumptions;
  if (assumptions === null) {
    return notDeclared(CONTROL_ASSUMPTIONS_NOT_DECLARED);
  }

  const names = nameComponents(site.foundation.components);

  return declared(
    assumptions.map((assumption: ControlAssumptionReadModel) => ({
      assumptionId: assumption.assumption_id,
      displayName: assumption.display_name,
      // An assumption about the site names no component, and that is a
      // declaration rather than a gap. A dash here would read as a missing
      // value; naming a component would be an invention.
      appliesTo:
        assumption.component_id === null
          ? ASSUMPTION_APPLIES_TO_SITE
          : names[assumption.component_id] ?? assumption.component_id,
      basis: label(assumption.basis, CONTROL_ASSUMPTION_BASIS_LABELS),
      statement: assumption.statement,
    })),
  );
}
