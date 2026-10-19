/** W2-05a: shared EV Foundation gap words (the views and the single line diagram module both use them). */
export const NO_CONNECTOR_DECLARED = "No connector declared";
export const RATING_NOT_DECLARED = "Rating not declared";
export const LIMIT_NOT_DECLARED = "Site import limit not declared";
export const NOT_DECLARED = "Not declared";

import type { EvConnector } from "./evFoundationClient";

/** The declared connector's name, or its position when the topology names none. */
export function connectorName(connector: EvConnector, names: Map<string, string>, index: number): string {
  return (connector.asset_id === null ? undefined : names.get(connector.asset_id)) ?? `Connector ${index + 1}`;
}
