import { waitFor } from "@testing-library/react";

/**
 * The loading sentences of the screens that read the site store. Each screen
 * renders exactly one of these while its read is in flight, and none of them
 * afterwards, in any settled state.
 */
const LOADING =
  /Loading (?:configured sites|the configured site|shipped site templates|the shipped site template|saved scenarios|the saved scenario)\./;

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
