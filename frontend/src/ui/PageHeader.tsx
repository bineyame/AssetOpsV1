import type { ReactNode } from "react";

/**
 * The one page-header pattern: a level-1 heading, an optional line under it,
 * and an optional action opposite them.
 *
 * T009 shipped this without the action slot on purpose, because nothing it
 * dressed had an action to put there and an empty toolbar is the kind of frame
 * this feature refuses to draw. T011 is the slice that fills it, with the
 * gated create entry point the Sites index already had.
 *
 * `badge` is the slot T009 said would belong to T012, and this is T012. The
 * mockups put a provenance badge beside a Site's name, and a Site's identity
 * header is the one place that is a fact rather than decoration: `Simulated`
 * is the rendering of `source.mode`, and it sits beside the identity because
 * it is about where this subject's evidence comes from.
 *
 * It renders nothing when empty, like `actions`. Two of the header controls
 * the mockups draw, `Edit` and `Version History`, are never rendered at all,
 * so the action slot is for what exists rather than for what the mockup
 * shows.
 *
 * `actions` renders nothing when empty, so a screen with no action gets no
 * container and no gap.
 *
 * The heading carries the id so a surrounding landmark can be labelled by it,
 * which is how every screen in this tree already names its `<main>`.
 */
export interface PageHeaderProps {
  /** The level-1 heading text. */
  title: ReactNode;
  /** The id assigned to the heading, for `aria-labelledby`. */
  headingId?: string;
  /** One line under the heading. */
  subtitle?: ReactNode;
  /** Rendered beside the heading. Nothing renders when this is empty. */
  badge?: ReactNode;
  /** Rendered opposite the heading. Nothing renders when this is empty. */
  actions?: ReactNode;
}

/** Whether a slot holds anything worth drawing a container for. */
function isEmpty(slot: ReactNode): boolean {
  return (
    slot === undefined ||
    slot === null ||
    slot === false ||
    (Array.isArray(slot) && slot.length === 0)
  );
}

export function PageHeader({
  title,
  headingId,
  subtitle,
  badge,
  actions,
}: PageHeaderProps) {
  return (
    <header className="page-header">
      <div>
        <div className="page-header__title">
          <h1 className="page-header__heading" id={headingId}>
            {title}
          </h1>
          {isEmpty(badge) ? null : badge}
        </div>
        {subtitle === undefined ? null : (
          <p className="page-header__subtitle">{subtitle}</p>
        )}
      </div>
      {isEmpty(actions) ? null : (
        <div className="page-header__actions">{actions}</div>
      )}
    </header>
  );
}
