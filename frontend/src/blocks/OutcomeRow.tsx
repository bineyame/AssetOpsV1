import type { ReactNode } from "react";
import "./blocks.css";

/**
 * CH-5b3 (SCOPE-1, CH5b-R R9): the shared outcome value line, used by the board row (`ob-head`) (UQ-FI-3: the
 * Portfolio card's "Why?" now sits in its top line), with the "Why?" button beside the value as the mock places it.
 *
 * The three slots (earnings, KPI, potential) are filled by CH-6. MOCK DEVIATION MD-CH5b-2: until then no caller passes
 * a slot and the row shows the CH-5a2 headline.
 * MOCK DEVIATION MD-CH5b-4 (CH5b3-R Q3): the mock's `ob-days` / `oc-pfdays` line under the value is not rendered; the
 * days line shows only in the "Why?" dialog's "Days used" (backlog BL-13).
 */

export interface OutcomeSlots {
  earnings?: ReactNode;
  kpi?: ReactNode;
  potential?: ReactNode;
}

const SLOT_ORDER = ["earnings", "kpi", "potential"] as const;

function filled(slots: OutcomeSlots | undefined): boolean {
  return slots !== undefined && SLOT_ORDER.some((k) => slots[k] !== undefined && slots[k] !== null);
}

/** The board row's head: `span.ob-head > span.ob-val + why-btn` (mock row, `index.html:461`). */
export function OutcomeRowHead({
  headline,
  slots,
  why,
}: {
  headline: ReactNode;
  slots?: OutcomeSlots;
  why?: ReactNode;
}) {
  return (
    <span className="ob-head">
      <span className="ob-val">
        {filled(slots)
          ? SLOT_ORDER.map((k) =>
              slots?.[k] === undefined || slots?.[k] === null ? null : (
                <span key={k} className="ob-slot" data-outcome-slot={k}>
                  {slots[k]}
                </span>
              ),
            )
          : headline}
      </span>
      {why}
    </span>
  );
}
