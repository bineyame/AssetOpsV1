import { waitFor } from "@testing-library/react";

/**
 * The loading sentences of the screens that read a store or a run. Each screen
 * renders one of these per read in flight, and none of them afterwards, in any
 * settled state.
 *
 * The run detail screen makes TWO reads since T022 - the persisted Draft and its
 * execution - so it has two sentences here and a test settles only when both are
 * gone. A screen whose second read was not listed would settle on the first, and
 * an assertion about a reading would then be made against a screen that has not
 * got one yet. That is the same race this helper exists for, one read along.
 *
 * T023 added a THIRD read, the Draft's staged source envelopes, and its
 * sentence is listed for the same reason.
 *
 * T027 adds the run screen's Commit read, Site > Evidence's read and the
 * record inspector's list and detail reads. T028 adds the analytics reads:
 * Performance, Dispatch, Finding detail and both Findings indexes.
 *
 * S6-01b adds the Recommendation read and the Action screens' two reads (the
 * Action and its events), each with its own sentence, and the Foundation
 * change read with its application-attempts read.
 */
const LOADING =
  /Loading (?:configured sites|the configured sites|the configured site|the chosen site|the site's Foundation version|the site's Foundation revision|shipped site templates|the shipped site template|saved scenarios|the saved scenario|the run setup inputs|the persisted runs|the persisted run|the execution of the persisted run|the staged source envelopes|the recorded history|the commit status|the site's evidence|the site's overview|the inspected records|the inspected record|the site's analytics|the site's assessments|the assessment|the findings|the site's findings|the publication schedule|the gateway diagnostics|the site's gateway contact|the refused readings|the Finding|the Finding's evidence|the Finding's history|the site's prices|the finding's money view|the fuel cost versions|the recommendation|the Action|the Action's events|the Foundation change|the Action's application attempts)./;

/**
 * Await a screen whose store read has settled, whatever it settled to.
 *
 * A screen that reads the store starts its read on mount. A test that asserts
 * something else - a heading, a navigation item, the absence of a control -
 * finishes before that read resolves, and the resulting state update lands
 * outside `act`. React is right to warn about it: the update is real and
 * unawaited, and asserting before it means asserting against a screen that is
 * still loading.
 *
 * This waits for the state the assertions are about. It is deliberately keyed
 * on the loading state going away rather than on any settled content, so it
 * works for a loaded record, an empty index, a not-found refusal, and an
 * unreadable store alike.
 *
 * Do not settle by awaiting a level-1 heading. The loading states render one
 * too, so it resolves against the placeholder and leaves the race in place.
 */
export async function settledScreen(
  scope: HTMLElement = document.body,
): Promise<void> {
  await waitFor(() => {
    if (LOADING.test(scope.textContent ?? "")) {
      throw new Error("the store read has not settled");
    }
  });
}
