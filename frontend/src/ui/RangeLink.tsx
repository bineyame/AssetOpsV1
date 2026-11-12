/**
 * SR-4a (D-SR.2, architect rev 8 §8.2): the one link component of the app. It renders react-router's `Link` with the
 * address's shared range carried onto every Site target (`carryRange`), so a Site page never opens without the range
 * the user is looking at. Every non-test `.tsx` imports it instead of `Link` (`RangeLink as Link` is allowed); the guard
 * `tools/checks/site-links-carry-range.ps1` keeps it that way.
 */
import { forwardRef } from "react";
import { Link, useSearchParams, type LinkProps } from "react-router-dom";

import { carryRange } from "./sharedRange";

export const RangeLink = forwardRef<HTMLAnchorElement, LinkProps>(function RangeLink({ to, ...rest }, ref) {
  const [params] = useSearchParams();
  return <Link ref={ref} to={carryRange(to, params)} {...rest} />;
});
