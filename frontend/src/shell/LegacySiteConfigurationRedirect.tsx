import { Navigate, useParams } from "react-router-dom";

import { SITES_PATH, siteFoundationHref } from "./operatorSiteRoutes";

/**
 * The address T008 served the Foundation surface at, forwarded to its name.
 *
 * This renders no surface of its own, which is the whole point. A rename that
 * left the old address rendering the same screen would have produced two
 * product surfaces for one thing, and the second one would keep its old name
 * in bookmarks, in links people had already shared, and eventually in someone's
 * mental model of what this product calls that screen.
 *
 * The identity is carried across verbatim: whoever opened a site's old
 * configuration address was asking about that site, and they arrive at that
 * site's Foundation. It is a `replace` so the old address does not sit in the
 * history stack waiting for a Back button to bounce off it.
 *
 * The address itself is spelled in exactly two places, and neither is here:
 * `operatorSiteRoutes.ts` declares it and the route table registers it. The
 * navigation-truthfulness guard holds that line, which is why this comment
 * describes the address rather than writing it out.
 *
 * `siteId` cannot be absent here, because the only route registered against
 * this component carries the parameter. The fallback is the Sites index rather
 * than a thrown error: an address that somehow named no site is a request to
 * look at sites.
 */
export function LegacySiteConfigurationRedirect() {
  const { siteId } = useParams<{ siteId: string }>();

  return (
    <Navigate
      replace
      to={siteId === undefined ? SITES_PATH : siteFoundationHref(siteId)}
    />
  );
}
