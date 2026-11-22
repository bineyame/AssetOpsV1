import { ActionsListPage, DecisionsListPage, FindingsListPage } from "../estate/homeLists";
import type { PortfolioSitesClient } from "../estate/portfolioSitesClient";
import type { SiteDirectoryClient } from "../sites/siteDirectoryClient";
import type { EstateClient } from "../estate/estateClient";
import { EstateEvidencePage } from "../estate/EstateEvidence";
import type { EstateEvidenceMoneyClient } from "../estate/estateEvidenceMoneyClient";
import { EstateFinancialsPage } from "../estate/EstateFinancials";
import type { EstateFinancialsClient } from "../estate/estateEvidenceMoneyClient";
import { EstatePortfolioPage } from "../estate/EstatePortfolio";

/**
 * W3-01 commit 3: the operator shell's frames for the estate roots. Each estate page renders its own
 * `PageHeader`; the frame supplies the `<main>` landmark every operator frame owns (Lane B's pages are tested under
 * a local router without one).
 */
export function EstateFindingsFrame({ client }: { client: EstateClient }) {
  return (
    <main aria-label="Findings">
      <FindingsListPage client={client} />
    </main>
  );
}

export function EstateActionsFrame({ client }: { client: EstateClient }) {
  return (
    <main aria-label="Actions">
      <ActionsListPage client={client} />
    </main>
  );
}

/** IA-P P2: the Decisions list (D-IAP.3): one row per placed Finding. */
export function EstateDecisionsFrame({ client }: { client: EstateClient }) {
  return (
    <main aria-label="Decisions">
      <DecisionsListPage client={client} />
    </main>
  );
}

/** W3-02 commit 2: the estate Evidence root. */
export function EstateEvidenceFrame({ client, estate }: { client: EstateEvidenceMoneyClient; estate?: EstateClient }) {
  return (
    <main aria-label="Evidence">
      <EstateEvidencePage client={client} estate={estate} />
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
export function EstatePortfolioFrame({ client, sites, directory }: { client: EstateClient; sites?: PortfolioSitesClient; directory?: SiteDirectoryClient }) {
  return (
    <main aria-label="Portfolio">
      <EstatePortfolioPage client={client} sites={sites} directory={directory} />
    </main>
  );
}
