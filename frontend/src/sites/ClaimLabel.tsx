/**
 * CC-R1 (commercial build spec 0.4, register R500): the claim level and who benefits, stated under a commercial
 * figure. An unknown level or beneficiary says "Evidence level and beneficiary not stated" and never throws.
 */
import { BENEFICIARY_WORDS, CLAIM_LABEL, type Beneficiary, type CommercialClaimLevel } from "./actionPresentation";

export function ClaimLabel({ level, beneficiary }: { level: string; beneficiary: string }) {
  const claim = Object.prototype.hasOwnProperty.call(CLAIM_LABEL, level) ? CLAIM_LABEL[level as CommercialClaimLevel] : null;
  const who = Object.prototype.hasOwnProperty.call(BENEFICIARY_WORDS, beneficiary)
    ? BENEFICIARY_WORDS[beneficiary as Beneficiary]
    : null;
  return (
    <p className="claim-label" data-claim-level={level} data-beneficiary={beneficiary}>
      {claim !== null && who !== null ? `${claim} · benefits: ${who}` : "Evidence level and beneficiary not stated"}
    </p>
  );
}
