import type { ReactNode } from "react";

/**
 * The one panel pattern: a bordered card with an optional labelled header.
 *
 * A panel is rendered by a surface that has something to put in it. This slice
 * adds no empty frame to balance a layout, so there is no "empty" state here
 * and no placeholder body: a surface with nothing to show renders no panel.
 *
 * `headingId` labels the section, which keeps the existing
 * `aria-labelledby` pattern every screen in this tree already uses.
 */
export interface PanelProps {
  /** Rendered as the panel's heading. Omitted for an unlabelled card. */
  heading?: ReactNode;
  /** The id assigned to the heading, for `aria-labelledby`. */
  headingId?: string;
  /** Heading level, so a panel nests correctly under its page heading. */
  headingLevel?: 2 | 3;
  /**
   * One plain line under the heading (the v6.9 panel sub-line): what the panel
   * shows and its claim limit. Optional; most panels keep their caption in the body.
   */
  description?: ReactNode;
  /** Removes body padding, for a panel whose body is a table. */
  flush?: boolean;
  /** The v69 panel-head right slot: one link or control beside the title. */
  actions?: ReactNode;
  /** An extra class for a v69 panel variant (for example `gw-panel`). */
  className?: string;
  children: ReactNode;
}

export function Panel({
  heading,
  headingId,
  headingLevel = 2,
  description,
  flush = false,
  actions,
  className,
  children,
}: PanelProps) {
  const Heading = headingLevel === 3 ? "h3" : "h2";

  return (
    <section
      className={["panel", flush ? "panel--flush" : "", className ?? ""].filter(Boolean).join(" ")}
      aria-labelledby={heading === undefined ? undefined : headingId}
    >
      {heading === undefined ? null : (
        <div className="panel__header">
          <div className="panel__header-text">
            <Heading className="panel__heading" id={headingId}>
              {heading}
            </Heading>
            {description === undefined ? null : <p className="panel__description">{description}</p>}
          </div>
          {actions === undefined ? null : <div className="panel__actions">{actions}</div>}
        </div>
      )}
      <div className="panel__body">{children}</div>
    </section>
  );
}
