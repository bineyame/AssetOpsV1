import { EstateActionsPage } from "../estate/actionIndex";
import type { EstateClient, EstateLens } from "../estate/estateClient";
import { EstateEvidencePage } from "../estate/EstateEvidence";
import type { EstateEvidenceMoneyClient } from "../estate/estateEvidenceMoneyClient";
import { EstateFinancialsPage } from "../estate/EstateFinancials";
import type { EstateFinancialsClient } from "../estate/estateEvidenceMoneyClient";
import { EstateFindingsPage } from "../estate/findingIndex";
import { EstatePortfolioPage } from "../estate/EstatePortfolio";

/**
 * W3-01 commit 3: the operator shell's frames for the estate roots. Each estate page renders its own
 * `PageHeader`; the frame supplies the `<main>` landmark every operator frame owns (Lane B's pages are tested under
 * a local router without one). A lens change remounts the page, so its window and cursor state restart.
 */
export function EstateFindingsFrame({ lens, client }: { lens: EstateLens; client: EstateClient }) {
  return (
    <main aria-label="Findings">
      <EstateFindingsPage key={lens} lens={lens} client={client} />
    </main>
  );
}

export function EstateActionsFrame({ client }: { client: EstateClient }) {
  return (
    <main aria-label="Actions">
      <EstateActionsPage client={client} />
    </main>
  );
}

/** W3-02 commit 2: the estate Evidence root. */
export function EstateEvidenceFrame({ client }: { client: EstateEvidenceMoneyClient }) {
  return (
    <main aria-label="Evidence">
      <EstateEvidencePage client={client} />
    </main>
  );
}

/** W3-02 commit 4: the estate Financials root. */
export function EstateFinancialsFrame({ client }: { client: EstateFinancialsClient }) {
  return (
    <main aria-label="Financials">
      <EstateFinancialsPage client={client} />
    </main>
  );
}

/** W3-03 run 2: the estate Portfolio root. */
export function EstatePortfolioFrame({ client }: { client: EstateClient }) {
  return (
    <main aria-label="Portfolio">
      <EstatePortfolioPage client={client} />
    </main>
  );
}
