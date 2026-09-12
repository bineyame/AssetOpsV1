import appConfig from "../../../config/app-config.json";

/**
 * Serving-boundary feature flags for the UI.
 *
 * `config/app-config.json` at the repository root is the single source of truth
 * and is read by the backend too, so one edit moves both serving boundaries.
 * The file is imported directly rather than copied into a UI-only setting, so
 * the two boundaries cannot drift apart.
 *
 * `simulatorLab.enabled` gates simulator surfaces and execution only. It must
 * never gate Site semantics, evidence, provenance, analytics, or operator
 * routes: operator screens work identically in both states.
 */
export interface FeatureFlags {
  simulatorLab: {
    enabled: boolean;
  };
}

export const featureFlags: FeatureFlags = {
  simulatorLab: {
    enabled: appConfig.simulator_lab.enabled,
  },
};

/** Build an explicit flag set. Used by tests to exercise both gate states. */
export function featureFlagsWith(simulatorLabEnabled: boolean): FeatureFlags {
  return { simulatorLab: { enabled: simulatorLabEnabled } };
}
