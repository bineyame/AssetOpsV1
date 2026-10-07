import { Panel } from "../ui";

/**
 * S1-01: a Site whose configuration moved to the stored Foundation has no
 * migrated evidence yet. Earlier results are not shown beside the updated
 * configuration; this is a stated transition, not an empty result and not a
 * statement about the site's equipment.
 */
export function AwaitingEvidenceMigration({ surface }: { surface: string }) {
  return (
    <Panel heading="Awaiting evidence migration" headingId="awaiting-evidence-migration-heading">
      <p data-evidence-state="awaiting_migration">
        This site&apos;s configuration has moved to its stored Foundation versions. Its {surface}{" "}
        is awaiting evidence migration, so earlier results are not shown beside the updated
        configuration.
      </p>
    </Panel>
  );
}

export const AWAITING_EVIDENCE_MIGRATION = "AWAITING_EVIDENCE_MIGRATION";
