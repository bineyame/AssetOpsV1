import type { ReactNode } from "react";

/**
 * W1-F2 (D-2026-10-17-mockup-layout-spec): a part of one v69 panel. Legacy Site Evidence surfaces that used to be
 * panels of their own now sit inside the v69 panel that owns their content; each keeps a small labelled line (its
 * former title, for `aria-labelledby` and table labels) but is not a panel and adds no panel slot.
 * Same props as `Panel`, so the move is mechanical and every existing label id survives.
 */
export function Part({
  heading,
  headingId,
  description,
  children,
}: {
  heading?: ReactNode;
  headingId?: string;
  headingLevel?: 2 | 3;
  description?: ReactNode;
  flush?: boolean;
  children: ReactNode;
}) {
  return (
    <div className="panel-part" aria-labelledby={heading === undefined ? undefined : headingId}>
      {heading === undefined ? null : (
        <p className="panel-part__title" id={headingId}>
          <strong>{heading}</strong>
          {description === undefined ? null : <span className="panel-part__description"> {description}</span>}
        </p>
      )}
      {children}
    </div>
  );
}
