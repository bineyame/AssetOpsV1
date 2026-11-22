/**
 * IA-P (spec §5.1, D-IAP.4): one live `LEGACY_ROUTES` entry, rendered as `<Navigate replace>` to its target with the
 * original search merged (the target's own query first). App.tsx mounts one per live entry, before the target's route.
 */
import { Navigate, useLocation, useParams } from "react-router-dom";

import { mergeLegacySearch, type LegacyRoute } from "./iaRoutes";

export function LegacyRedirect({ route }: { route: LegacyRoute }) {
  const params = useParams();
  const location = useLocation();
  const search = new URLSearchParams(location.search);
  const base = typeof route.to === "function" ? route.to(params, search) : route.to;
  const splat = route.prefix && params["*"] ? `/${params["*"]}` : "";
  const [pathname, query] = base.split("?", 2);
  const target = mergeLegacySearch(query === undefined ? `${pathname}${splat}` : `${pathname}${splat}?${query}`, search);
  return <Navigate to={`${target}${location.hash}`} replace />;
}
