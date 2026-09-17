/**
 * The brand header that sits at the top of a shell's rail.
 *
 * It renders the product name and a mark, and nothing else. The mockups put a
 * user chip beside it ("BY Bineyame"); that is an identity this build does not
 * have, so it is not rendered. Dressing a screen must not introduce a fact the
 * product cannot source, and a signed-in user is a fact.
 *
 * The mark is drawn in CSS rather than as an inline `<svg>`. That is
 * deliberate: several surfaces assert that no `svg`, `canvas`, `img` or
 * `figure` exists anywhere in the rendered container, because a chart, a
 * diagram or a site photograph would each be a claim this build cannot make.
 * A decorative brand mark is not one of those things, but it should not be the
 * reason that assertion has to be narrowed - the guard is worth more than the
 * glyph.
 *
 * The name is a prop rather than a constant because both shells render this
 * and the workspace shell may name itself differently later. Nothing here
 * knows which shell it is in.
 */
export interface AppHeaderProps {
  /** The product or workspace name shown beside the mark. */
  name: string;
}

export function AppHeader({ name }: AppHeaderProps) {
  return (
    <p className="app-header">
      <span className="app-header__mark" aria-hidden="true" />
      {name}
    </p>
  );
}
