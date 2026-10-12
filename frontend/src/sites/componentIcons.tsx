import type { ReactNode } from "react";

import { COMPONENT_TYPE_LABELS, label } from "./siteViewModel";
import { sldSymbolFor, type SldSymbol } from "./sldViewModel";

/**
 * V-01a round 2 (Architect item 4): one semantic icon per declared component
 * type, drawn in the v6.9 single line diagram's visual grammar - a framed
 * symbol block whose frame colour says which family of equipment it is
 * (supply, storage, conversion, network, load). Colour and shape name the
 * TYPE only. Nothing here encodes operating state, a reading or a rating, and
 * no glyph spells a letter or a number.
 *
 * The same shapes are used on the configured drawing and on the Foundation
 * topology cards, so a reader learns one vocabulary.
 */
export const COMPONENT_ICON_WIDTH = 64;
export const COMPONENT_ICON_HEIGHT = 44;

export type ComponentIconFamily = "supply" | "storage" | "conversion" | "network" | "load";

const FAMILY: Record<SldSymbol, ComponentIconFamily> = {
  PV_ARRAY: "supply",
  GENERATOR: "supply",
  FUEL_TANK: "supply",
  BATTERY: "storage",
  INVERTER: "conversion",
  POWER_CONVERSION_SYSTEM: "conversion",
  BUSBAR: "network",
  METER: "network",
  LOAD: "load",
  COLD_ROOM: "load",
};

export function componentIconFamily(symbol: SldSymbol): ComponentIconFamily {
  return FAMILY[symbol];
}

function mark(symbol: SldSymbol): ReactNode {
  switch (symbol) {
    case "PV_ARRAY":
      return [0, 1, 2].flatMap((c) =>
        [0, 1].map((r) => (
          <rect key={`${c}-${r}`} className="component-icon__cell" x={8 + c * 17} y={7 + r * 16} width={14} height={13} />
        )),
      );
    case "GENERATOR":
      return (
        <>
          <circle cx={23} cy={22} r={13} />
          <path d="M14,22 q4.5,-8 9,0 q4.5,8 9,0" />
          <rect x={41} y={13} width={15} height={18} rx={2} />
        </>
      );
    case "FUEL_TANK":
      return (
        <>
          <rect x={13} y={9} width={38} height={27} rx={9} />
          <line x1={13} y1={25} x2={51} y2={25} />
          <path d="M32,13 q-4,6 0,8 q4,-2 0,-8" />
        </>
      );
    case "BATTERY":
      return [0, 1, 2, 3].map((c) => (
        <rect key={c} className="component-icon__cell" x={10 + c * 12} y={10} width={9} height={24} rx={2} />
      ));
    case "INVERTER":
    case "POWER_CONVERSION_SYSTEM":
      return (
        <>
          <rect x={18} y={6} width={28} height={32} rx={2} />
          <line x1={18} y1={38} x2={46} y2={6} />
          <path d="M21,15 q2.5,-4 5,0 q2.5,4 5,0" />
          <line x1={34} y1={29} x2={43} y2={29} />
          <line x1={34} y1={33} x2={43} y2={33} />
          {symbol === "POWER_CONVERSION_SYSTEM" ? (
            <path d="M5,22 h8 M8,19 l-3,3 l3,3 M51,22 h8 M56,19 l3,3 l-3,3" />
          ) : null}
        </>
      );
    case "METER":
      return (
        <>
          <circle cx={32} cy={22} r={13} />
          <path d="M23,26 a10,10 0 0 1 18,0" />
          <line x1={32} y1={25} x2={38} y2={15} />
        </>
      );
    case "LOAD":
      return <path d="M18,36 V20 L32,9 L46,20 V36 Z M28,36 v-8 h8 v8" />;
    case "COLD_ROOM":
      return (
        <path d="M32,9 v26 M20.7,15.5 l22.6,13 M20.7,28.5 l22.6,-13 M29,11 l3,3 l3,-3 M29,33 l3,-3 l3,3" />
      );
    case "BUSBAR":
      return <rect className="component-icon__bar" x={6} y={19} width={52} height={6} rx={2} />;
  }
}

/**
 * The icon's shapes, in a 64 x 44 box at the origin. For use inside an SVG
 * the caller owns (the configured drawing); `frameClassName` lets the drawing
 * keep its own hook on the frame.
 */
export function ComponentIconShape({
  symbol,
  frameClassName,
}: {
  symbol: SldSymbol;
  frameClassName?: string;
}) {
  const family = FAMILY[symbol];
  return (
    <g className={`component-icon__shape component-icon--${family}`} data-component-icon={symbol}>
      <rect
        className={`component-icon__frame${frameClassName === undefined ? "" : ` ${frameClassName}`}`}
        x={0}
        y={0}
        width={COMPONENT_ICON_WIDTH}
        height={COMPONENT_ICON_HEIGHT}
        rx={5}
      />
      <g className="component-icon__mark">{mark(symbol)}</g>
    </g>
  );
}

/**
 * A standalone icon for a declared component type, named by the type in words
 * (`role="img"` with the type label). Returns nothing for a type the archetype
 * has no symbol for: an unknown type is never drawn as some other type.
 */
export function ComponentTypeIcon({ componentType, size = 40 }: { componentType: string; size?: number }) {
  const symbol = sldSymbolFor(componentType);
  if (symbol === null) return null;
  return (
    <svg
      className="component-icon"
      viewBox={`0 0 ${COMPONENT_ICON_WIDTH} ${COMPONENT_ICON_HEIGHT}`}
      width={size}
      height={(size * COMPONENT_ICON_HEIGHT) / COMPONENT_ICON_WIDTH}
      role="img"
      aria-label={label(componentType, COMPONENT_TYPE_LABELS)}
      focusable="false"
    >
      <ComponentIconShape symbol={symbol} />
    </svg>
  );
}
