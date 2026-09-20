import type {
  SiteDetailReadModel,
  SiteFoundationReadModel,
} from "../siteReadModel";

/**
 * Records for the SLD view-model tests.
 *
 * `HYBRID_MINI_GRID_SITE` mirrors the shipped
 * `config/site-templates/hybrid-mini-grid-100kw.yaml` as a created Site would
 * carry it: the same components, the same nine topology nodes, the same eight
 * connections, the same six devices and thirteen mappings.
 *
 * It mirrors the template rather than importing it because the archetype must
 * bind by canonical type and role. A fixture that was the template would let a
 * binding by identity pass unnoticed; a fixture that says the same thing with
 * its own identities, in its own order, is what makes the difference visible.
 * Every identity below is deliberately NOT the template's, and the node array
 * is deliberately NOT in the template's order.
 */

const FOUNDATION: SiteFoundationReadModel = {
  version: 1,
  valid_from: "2026-09-19T08:00:00Z",
  summary:
    "Solar-plus-storage mini-grid with a diesel generator for backup and a " +
    "metered distribution load.",
  components: [
    {
      component_id: "c-solar",
      component_type: "PV_ARRAY",
      display_name: "Rooftop PV array",
      rating: { value: 100, unit: "kW" },
    },
    {
      component_id: "c-solar-inverter",
      component_type: "INVERTER",
      display_name: "PV inverter",
      rating: { value: 90, unit: "kW" },
    },
    {
      component_id: "c-storage",
      component_type: "BATTERY",
      display_name: "Battery energy storage",
      rating: { value: 215, unit: "kWh" },
    },
    {
      component_id: "c-storage-pcs",
      component_type: "POWER_CONVERSION_SYSTEM",
      display_name: "Battery power conversion system",
      rating: { value: 50, unit: "kW" },
    },
    {
      component_id: "c-genset",
      component_type: "GENERATOR",
      display_name: "Diesel generator",
      rating: { value: 60, unit: "kW" },
    },
    {
      component_id: "c-fuel",
      component_type: "FUEL_TANK",
      display_name: "Generator fuel tank",
      rating: { value: 500, unit: "L" },
    },
    {
      component_id: "c-bus",
      component_type: "AC_BUS",
      display_name: "AC bus",
      rating: { value: 400, unit: "V" },
    },
    {
      component_id: "c-meter",
      component_type: "METER",
      display_name: "Site meter",
      rating: null,
    },
    {
      component_id: "c-load",
      component_type: "LOAD",
      display_name: "Distribution load",
      rating: { value: 80, unit: "kW" },
    },
  ],
  topology: {
    // Deliberately not in lane order, not in connection order, and not in the
    // shipped template's order. Anything the archetype decides from this order
    // is a binding by array position.
    nodes: [
      { node_id: "n-load", component_id: "c-load", node_role: "LOAD" },
      { node_id: "n-bus", component_id: "c-bus", node_role: "BUS" },
      { node_id: "n-fuel", component_id: "c-fuel", node_role: "FUEL_STORAGE" },
      {
        node_id: "n-solar-inverter",
        component_id: "c-solar-inverter",
        node_role: "CONVERSION",
      },
      { node_id: "n-meter", component_id: "c-meter", node_role: "METERING" },
      { node_id: "n-solar", component_id: "c-solar", node_role: "GENERATION" },
      {
        node_id: "n-storage-pcs",
        component_id: "c-storage-pcs",
        node_role: "CONVERSION",
      },
      { node_id: "n-genset", component_id: "c-genset", node_role: "GENERATION" },
      { node_id: "n-storage", component_id: "c-storage", node_role: "STORAGE" },
    ],
    connections: [
      {
        connection_id: "k-solar-dc",
        from_node: "n-solar",
        to_node: "n-solar-inverter",
        medium: "DC",
      },
      {
        connection_id: "k-solar-ac",
        from_node: "n-solar-inverter",
        to_node: "n-bus",
        medium: "AC",
      },
      {
        connection_id: "k-storage-dc",
        from_node: "n-storage",
        to_node: "n-storage-pcs",
        medium: "DC",
      },
      {
        connection_id: "k-storage-ac",
        from_node: "n-storage-pcs",
        to_node: "n-bus",
        medium: "AC",
      },
      {
        connection_id: "k-fuel",
        from_node: "n-fuel",
        to_node: "n-genset",
        medium: "FUEL",
      },
      {
        connection_id: "k-genset-ac",
        from_node: "n-genset",
        to_node: "n-bus",
        medium: "AC",
      },
      {
        connection_id: "k-bus-meter",
        from_node: "n-bus",
        to_node: "n-meter",
        medium: "AC",
      },
      {
        connection_id: "k-meter-load",
        from_node: "n-meter",
        to_node: "n-load",
        medium: "AC",
      },
    ],
  },
  devices: [
    {
      device_id: "d-solar-controller",
      device_type: "CONTROLLER",
      display_name: "PV inverter controller",
      component_id: "c-solar-inverter",
      signals: [
        { signal_id: "ac-power", display_name: "AC output power", unit: "kW" },
        {
          signal_id: "lifetime-energy",
          display_name: "Lifetime energy delivered",
          unit: "kWh",
        },
      ],
    },
    {
      device_id: "d-irradiance",
      device_type: "SENSOR",
      display_name: "Plane-of-array irradiance sensor",
      component_id: "c-solar",
      signals: [
        {
          signal_id: "irradiance",
          display_name: "Plane-of-array irradiance",
          unit: "W/m2",
        },
        {
          signal_id: "module-temperature",
          display_name: "Module temperature",
          unit: "degC",
        },
      ],
    },
    {
      device_id: "d-storage-controller",
      device_type: "CONTROLLER",
      display_name: "Battery PCS controller",
      component_id: "c-storage-pcs",
      signals: [
        { signal_id: "ac-power", display_name: "AC power at the PCS", unit: "kW" },
        {
          signal_id: "state-of-charge",
          display_name: "Battery state of charge",
          unit: "%",
        },
      ],
    },
    {
      device_id: "d-genset-controller",
      device_type: "CONTROLLER",
      display_name: "Generator controller",
      component_id: "c-genset",
      signals: [
        {
          signal_id: "ac-power",
          display_name: "Generator output power",
          unit: "kW",
        },
        {
          signal_id: "output-voltage",
          display_name: "Generator output voltage",
          unit: "V",
        },
      ],
    },
    {
      device_id: "d-fuel-level",
      device_type: "SENSOR",
      display_name: "Fuel level sensor",
      component_id: "c-fuel",
      signals: [{ signal_id: "fuel-level", display_name: "Fuel level", unit: "L" }],
    },
    {
      device_id: "d-meter-unit",
      device_type: "METER",
      display_name: "Site meter",
      component_id: "c-meter",
      signals: [
        {
          signal_id: "active-power",
          display_name: "Active power through the meter",
          unit: "kW",
        },
        {
          signal_id: "throughput-energy",
          display_name: "Energy through the meter",
          unit: "kWh",
        },
        { signal_id: "bus-voltage", display_name: "Bus voltage", unit: "V" },
        { signal_id: "bus-frequency", display_name: "Bus frequency", unit: "Hz" },
      ],
    },
  ],
  // The meter is attached to the metering point and describes the load and the
  // bus. Nothing else in this document says so, which is why a view model that
  // took the device's own component instead would look right on every other
  // row and wrong on these three.
  signal_mappings: [
    {
      mapping_id: "m-inverter-power",
      device_id: "d-solar-controller",
      signal_id: "ac-power",
      component_id: "c-solar-inverter",
    },
    {
      mapping_id: "m-array-energy",
      device_id: "d-solar-controller",
      signal_id: "lifetime-energy",
      component_id: "c-solar",
    },
    {
      mapping_id: "m-array-irradiance",
      device_id: "d-irradiance",
      signal_id: "irradiance",
      component_id: "c-solar",
    },
    {
      mapping_id: "m-array-module-temperature",
      device_id: "d-irradiance",
      signal_id: "module-temperature",
      component_id: "c-solar",
    },
    {
      mapping_id: "m-pcs-power",
      device_id: "d-storage-controller",
      signal_id: "ac-power",
      component_id: "c-storage-pcs",
    },
    {
      mapping_id: "m-storage-state-of-charge",
      device_id: "d-storage-controller",
      signal_id: "state-of-charge",
      component_id: "c-storage",
    },
    {
      mapping_id: "m-genset-power",
      device_id: "d-genset-controller",
      signal_id: "ac-power",
      component_id: "c-genset",
    },
    {
      mapping_id: "m-genset-voltage",
      device_id: "d-genset-controller",
      signal_id: "output-voltage",
      component_id: "c-genset",
    },
    {
      mapping_id: "m-fuel-level",
      device_id: "d-fuel-level",
      signal_id: "fuel-level",
      component_id: "c-fuel",
    },
    {
      mapping_id: "m-load-power",
      device_id: "d-meter-unit",
      signal_id: "active-power",
      component_id: "c-load",
    },
    {
      mapping_id: "m-load-energy",
      device_id: "d-meter-unit",
      signal_id: "throughput-energy",
      component_id: "c-load",
    },
    {
      mapping_id: "m-bus-voltage",
      device_id: "d-meter-unit",
      signal_id: "bus-voltage",
      component_id: "c-bus",
    },
    {
      mapping_id: "m-bus-frequency",
      device_id: "d-meter-unit",
      signal_id: "bus-frequency",
      component_id: "c-bus",
    },
  ],
  control_assumptions: [
    {
      assumption_id: "a-solar-first",
      display_name: "Solar is dispatched before the generator",
      component_id: null,
      basis: "TEMPLATE",
      statement:
        "The archetype assumes photovoltaic output is consumed or stored " +
        "before the diesel generator is called on.",
    },
    {
      assumption_id: "a-reserve",
      display_name: "The battery holds a reserve",
      component_id: "c-storage",
      basis: "TEMPLATE",
      statement:
        "The battery is assumed to retain a reserve for evening supply.",
    },
  ],
};

export const HYBRID_MINI_GRID_SITE: SiteDetailReadModel = {
  site_id: "KLG-014",
  display_name: "Kalangala Mini-Grid",
  site_type: "MINIGRID",
  location: { country: "Uganda", locality: "Kalangala" },
  timezone: "Africa/Kampala",
  lifecycle_status: "PLANNED",
  origin: "USER",
  source: { mode: "SIMULATED" },
  template: { template_id: "hybrid-mini-grid-100kw", template_version: 1 },
  foundation: FOUNDATION,
};

/** The same site with every section below the component list undeclared. */
export const UNDECLARED_TOPOLOGY_SITE: SiteDetailReadModel = {
  ...HYBRID_MINI_GRID_SITE,
  foundation: {
    ...FOUNDATION,
    topology: null,
    devices: null,
    signal_mappings: null,
    control_assumptions: null,
  },
};

/**
 * A deep copy with the foundation's lists reordered by the given rule.
 *
 * Used to prove the archetype decides nothing from array position.
 */
export function withReorderedTopology(
  site: SiteDetailReadModel,
): SiteDetailReadModel {
  const topology = site.foundation.topology;
  if (topology === null) return site;

  return {
    ...site,
    foundation: {
      ...site.foundation,
      components: [...site.foundation.components].reverse(),
      topology: {
        nodes: [...topology.nodes].reverse(),
        connections: [...topology.connections].reverse(),
      },
      devices:
        site.foundation.devices === null
          ? null
          : [...site.foundation.devices].reverse(),
      signal_mappings:
        site.foundation.signal_mappings === null
          ? null
          : [...site.foundation.signal_mappings].reverse(),
    },
  };
}
