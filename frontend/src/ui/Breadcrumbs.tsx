import { Link } from "react-router-dom";

/**
 * The breadcrumb trail.
 *
 * A crumb without a `to` is the current page and renders as text, not a link
 * to itself. The trail is supplied by whichever shell composes the screen,
 * because where a surface sits in a route hierarchy is a shell's fact about
 * its own routes.
 *
 * The trail names places that exist. It is not a place to announce a parent
 * section the product does not serve.
 */
export interface Crumb {
  label: string;
  /** Omitted for the current page. */
  to?: string;
}

export interface BreadcrumbsProps {
  trail: Crumb[];
}

export function Breadcrumbs({ trail }: BreadcrumbsProps) {
  if (trail.length === 0) {
    return null;
  }

  return (
    <nav className="breadcrumbs" aria-label="Breadcrumb">
      <ol className="breadcrumbs__list">
        {trail.map((crumb) => (
          <li className="breadcrumbs__item" key={`${crumb.label}-${crumb.to ?? "current"}`}>
            {crumb.to === undefined ? (
              <span className="breadcrumbs__current" aria-current="page">
                {crumb.label}
              </span>
            ) : (
              <Link to={crumb.to}>{crumb.label}</Link>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
