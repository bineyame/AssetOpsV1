/**
 * Post-W6 W6 caps ruling 4: in-cell progressive disclosure for the clamped list cells (WAI-ARIA disclosure pattern;
 * WCAG 2.2 Focus Visible, no hover or focus popover). The value shows as a two-line preview only when the complete
 * value would overflow it; then a visible "Show full" button sits inside the two-line box (over the end of the second
 * line, never a new line) and reveals the complete unchanged value inline, offering "Show less". When the value fits,
 * it shows plainly with no button. The button is a sibling of the value, never nested in a cell link.
 */
import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState, type ReactNode } from "react";

export function CellDisclosure({
  column,
  row,
  children,
  data,
}: {
  /** Column name for the accessible name, e.g. `Owner`. */
  column: string;
  /** Row identity for the accessible name, e.g. the case code. */
  row: string;
  children: ReactNode;
  data?: Record<string, string>;
}) {
  const id = useId();
  const ref = useRef<HTMLDivElement>(null);
  const [overflows, setOverflows] = useState(false);
  const [expanded, setExpanded] = useState(false);

  // Measured only while collapsed: the clamped preview overflows when its content is taller than its two-line box.
  const measure = useCallback(() => {
    const el = ref.current;
    if (el === null || el.dataset.cellDisclosureExpanded === "true") return;
    setOverflows(el.scrollHeight > el.clientHeight + 1);
  }, []);

  useLayoutEffect(() => {
    if (!expanded) measure();
  }, [expanded, measure, children]);

  useEffect(() => {
    const el = ref.current;
    if (el === null) return undefined;
    const resize = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(() => measure());
    resize?.observe(el);
    // A content change that keeps the box at two lines does not resize it, so text changes re-measure too.
    const mutation = typeof MutationObserver === "undefined" ? null : new MutationObserver(() => measure());
    mutation?.observe(el, { childList: true, subtree: true, characterData: true });
    return () => {
      resize?.disconnect();
      mutation?.disconnect();
    };
  }, [measure]);

  const disclosed = overflows || expanded;
  return (
    <div
      className="cell-disclosure"
      data-cell-disclosure=""
      data-cell-disclosure-state={disclosed ? (expanded ? "expanded" : "collapsed") : "fits"}
    >
      <div
        ref={ref}
        id={id}
        className="global-work-clamp global-work-clamp--two cell-disclosure__value"
        data-cell-disclosure-expanded={expanded ? "true" : "false"}
        {...data}
      >
        {children}
      </div>
      {disclosed ? (
        <button
          type="button"
          className="cell-disclosure__toggle"
          data-cell-disclosure-toggle=""
          aria-expanded={expanded}
          aria-controls={id}
          aria-label={`${expanded ? "Show less" : "Show full"} ${column} for ${row}`}
          onClick={() => setExpanded((open) => !open)}
        >
          {expanded ? "Show less" : "Show full"}
        </button>
      ) : null}
    </div>
  );
}
