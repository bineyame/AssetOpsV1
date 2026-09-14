import { act } from "@testing-library/react";
import { afterEach } from "vitest";

import "@testing-library/jest-dom/vitest";

/**
 * Settle promise-driven state updates before React Testing Library unmounts.
 *
 * Screens that read a store start a fetch on mount. A test that asserts a
 * frame concern - a heading, a navigation item - does not await that read, so
 * the promise resolved after the test body finished and React reported "an
 * update was not wrapped in act(...)". The warning was correct: the update was
 * real and unawaited, and every one of them printed a component stack, which
 * was most of the noise in a suite run.
 *
 * Flushing here fixes the cause rather than hiding it. The pending microtasks
 * run inside `act` while the tree is still mounted, so the update is applied
 * and asserted-against state is the settled state.
 *
 * This runs before RTL's own cleanup: Vitest calls `afterEach` hooks in
 * reverse registration order, and importing `@testing-library/react` above
 * registers its cleanup first. If that ever changes, the act warnings come
 * back rather than anything failing silently, which is the right failure mode.
 */
afterEach(async () => {
  await act(async () => {});
});

/**
 * React Router prints two v7 migration notices on every router mount. They are
 * advisory and say nothing about this code.
 *
 * They are filtered rather than opted into. Passing
 * `future={{ v7_startTransition, v7_relativeSplatPath }}` would silence them
 * by adopting v7 state-update and splat-resolution semantics, which is a
 * change to how the app behaves at runtime and a technical-contract decision
 * for the Architect, not a test-hygiene change.
 *
 * Only these exact notices are dropped, and only on `console.warn`. Everything
 * else still reaches the console - React's act warnings come through
 * `console.error` and are deliberately untouched. This exists to keep real
 * signal findable, never to hide it.
 */
const FILTERED_WARNINGS = [/React Router Future Flag Warning/];

const passThroughWarn = console.warn;
console.warn = (...args: unknown[]) => {
  const first = args[0];
  if (
    typeof first === "string" &&
    FILTERED_WARNINGS.some((pattern) => pattern.test(first))
  ) {
    return;
  }
  passThroughWarn(...args);
};
