/** OUT-A: inline `outcome-map/1` wire fixtures (the A1 map test cases F-104, F-118, F-130, F-119). */
import type { OutcomeCategories } from "../outcomeCategories";

export const OPT = "Optimize cost and efficiency";
export const PRO = "Protect asset and capital";
export const GROW = "Grow revenue";

export const F104: OutcomeCategories = {
  policy_version: "outcome-map/1",
  state: "MAPPED",
  items: [
    { category: "OPTIMIZE_COST", label: OPT, role: "MOVES", outcomes: [{ key: "MG-2", label: "Supply cost per kWh" }] },
    {
      category: "PROTECT_ASSET",
      label: PRO,
      role: "CHECKED",
      outcomes: [
        { key: "MG-5", label: "Reliable service" },
        { key: "MG-4", label: "Battery and generator life" },
      ],
    },
  ],
};

export const F118: OutcomeCategories = {
  policy_version: "outcome-map/1",
  state: "MAPPED",
  items: [
    {
      category: "PROTECT_ASSET",
      label: PRO,
      role: "MOVES",
      outcomes: [
        { key: "CC-6", label: "Cooling continuity" },
        { key: "CC-1", label: "Stock kept saleable" },
      ],
    },
    { category: "PROTECT_ASSET", label: PRO, role: "CHECKED", outcomes: [{ key: "CC-5", label: "Compressor life" }] },
    { category: "OPTIMIZE_COST", label: OPT, role: "CHECKED", outcomes: [{ key: "CC-3", label: "Cost per cooling unit" }] },
  ],
};

export const F130: OutcomeCategories = {
  policy_version: "outcome-map/1",
  state: "MAPPED",
  items: [
    { category: "PROTECT_ASSET", label: PRO, role: "MOVES", outcomes: [{ key: "EV-1", label: "Buses ready for service" }] },
    { category: "GROW_REVENUE", label: GROW, role: "MOVES", outcomes: [{ key: "EV-3", label: "Charger use" }] },
    { category: "PROTECT_ASSET", label: PRO, role: "CHECKED", outcomes: [{ key: "EV-4", label: "Charger life" }] },
  ],
};

export const F119: OutcomeCategories = {
  policy_version: "outcome-map/1",
  state: "MAPPED",
  items: [{ category: "PROTECT_ASSET", label: PRO, role: "MOVES", outcomes: [{ key: "CC-1", label: "Stock kept saleable" }] }],
};

export const NOT_MAPPED: OutcomeCategories = { policy_version: "outcome-map/1", state: "NOT_MAPPED", items: [] };
