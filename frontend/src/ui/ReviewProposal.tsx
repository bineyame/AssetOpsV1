import type { ReactNode } from "react";

/**
 * A provisional proposal, on screen, awaiting a decision.
 *
 * This project runs user-review checkpoints on the screen rather than in a
 * document, and it has learned what a checkpoint region has to do. T016 put a
 * question on screen with candidates the project had considered and not
 * chosen, and no proposal. Accepting the screen therefore settled nothing, and
 * the question had to be answered by an Architect weeks later. A menu is not a
 * proposal.
 *
 * So this region carries four things, and the type requires all four:
 *
 * - `question`: what is being decided, in one line.
 * - `proposal`: what this project proposes. Not options.
 * - `settled`: what is already decided and is deliberately not being asked
 *   about, so accepting the proposal does not look like reopening it.
 * - `onAccepting` / `onRedirecting`: what accepting this screen commits to,
 *   and what redirecting it would mean. A reader has to be able to tell what
 *   their answer does.
 *
 * Provisional is stated in the region's own words rather than only in colour,
 * because a reader who cannot see the tint must still be able to tell that
 * what they are looking at is a proposal and not a decision.
 *
 * It renders no control. A checkpoint is answered by the user in review, not
 * by clicking Accept on a page that has nothing to record the answer in - a
 * button here would be a control with no capability behind it, which is the
 * thing this product does not draw.
 */
export interface ReviewProposalProps {
  /** Distinguishes this proposal's region for tests and for `aria`. */
  id: string;
  /** What is being decided, as a question. */
  question: ReactNode;
  /** What this project proposes. Rendered as the body of the region. */
  proposal: ReactNode;
  /** What is already settled and is not part of the question. */
  settled: ReactNode;
  /** What accepting this screen adopts. */
  onAccepting: ReactNode;
  /** What redirecting it would mean. */
  onRedirecting: ReactNode;
}

export const REVIEW_PROPOSAL_STATUS = "Provisional - awaiting your review";

export function ReviewProposal({
  id,
  question,
  proposal,
  settled,
  onAccepting,
  onRedirecting,
}: ReviewProposalProps) {
  const headingId = `${id}-heading`;

  return (
    <section
      className="review-proposal"
      data-review-proposal={id}
      aria-labelledby={headingId}
    >
      <p className="review-proposal__status">{REVIEW_PROPOSAL_STATUS}</p>
      <h3 className="review-proposal__heading" id={headingId}>
        {question}
      </h3>
      <div className="review-proposal__body">{proposal}</div>
      <dl className="review-proposal__terms">
        <dt>Already settled, and not part of this question</dt>
        <dd>{settled}</dd>
        <dt>Accepting this screen adopts</dt>
        <dd>{onAccepting}</dd>
        <dt>Redirecting it would mean</dt>
        <dd>{onRedirecting}</dd>
      </dl>
    </section>
  );
}
