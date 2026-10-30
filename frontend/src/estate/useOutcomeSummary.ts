import { useEffect, useState } from "react";

import type { EstateClient, EstateOutcomeSummaryBody, EstateResult } from "./estateClient";

/**
 * OUT-C U5/U6: the estate outcome summary for one window, for the warning lists and the Maintenance card. `null`
 * while loading; a client without the read (older fakes) answers refused.
 */
export function useOutcomeSummary(
  reads: Pick<EstateClient, "getOutcomeSummary">,
  window: { from: string; to: string; known_at?: string | null } | null,
): EstateResult<EstateOutcomeSummaryBody> | null {
  const key = window === null ? null : `${window.from}|${window.to}|${window.known_at ?? ""}`;
  const [read, setRead] = useState<{ key: string; result: EstateResult<EstateOutcomeSummaryBody> } | null>(null);
  useEffect(() => {
    if (window === null || key === null) return;
    let live = true;
    const pending =
      reads.getOutcomeSummary === undefined
        ? Promise.resolve<EstateResult<EstateOutcomeSummaryBody>>({ status: "refused", httpStatus: 503, code: "ESTATE_STORE_UNAVAILABLE", copy: "" })
        : reads.getOutcomeSummary({ from: window.from, to: window.to, known_at: window.known_at ?? null });
    void pending
      .then((result) => {
        if (live) setRead({ key, result });
      })
      .catch(() => undefined);
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reads, key]);
  return key !== null && read?.key === key ? read.result : null;
}
