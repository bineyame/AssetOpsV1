import type { ReactNode } from "react";

/**
 * The one page-header pattern: a level-1 heading and an optional line under it.
 *
 * It has no action slot and no badge slot. The mockups put `+ New Site`,
 * `Edit`, `Version History` and a provenance badge up here, and every one of
 * those belongs to the slice that owns that screen's information architecture:
 * the create action is restyled in T011, the Site identity header and its badge
 * are T012, and two of those controls are never rendered at all. Building the
 * slots now would be machinery nothing in this slice fills, and an empty
 * toolbar is exactly the kind of frame this feature refuses to draw.
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
}

export function PageHeader({ title, headingId, subtitle }: PageHeaderProps) {
  return (
    <header className="page-header">
      <div>
        <h1 className="page-header__heading" id={headingId}>
          {title}
        </h1>
        {subtitle === undefined ? null : (
          <p className="page-header__subtitle">{subtitle}</p>
        )}
      </div>
    </header>
  );
}
