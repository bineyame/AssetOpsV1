/**
 * Client for the gated run setup API.
 *
 * The client is created with its base paths rather than importing them, so
 * this module never spells a simulator URL: `tools/check-architecture.ps1`
 * allows that only in `simulatorLabRoutes.tsx`, which is where the paths live
 * and where this client is constructed.
 *
 * It reads the versioned profiles and it creates one Draft. There is no start,
 * step, pause, commit, stage, ingest, replay, rerun or delete method, so no
 * screen built on it can offer one. That is not a convention: a screen cannot
 * call what the client does not have, and the backend serves no such route.
 *
 * ## The two outcomes are two shapes
 *
 * A refusal and a created Draft are different facts and they arrive
 * differently. `refused` carries the refusal kind and the backend's own copy,
 * and it means no run identity was allocated and nothing was written - there
 * is nothing to go and look at. `created` carries the persisted Draft,
 * whether it is `READY` or `BLOCKED`, because a blocked Draft exists and its
 * frozen inputs are the thing a reader inspects in order to decide what to
 * change.
 *
 * Collapsing them into one "it did not work" would lose exactly that.
 */

/** One state a model profile can model, and in which execution roles. */
export interface RunSupportedState {
  state_key: string;
  supported_roles: string[];
  statement: string;
}

export interface RunModelProfile {
  model_profile_id: string;
  model_profile_version: number;
  display_name: string;
  statement: string;
  supported_states: RunSupportedState[];
}

/**
 * A versioned publication profile.
 *
 * Each of the three values it resolves may be `null`, and `null` is a real
 * answer rather than a gap: it means nobody has declared that input, which is
 * what blocks a run. Nothing in this client or in any screen built on it
 * supplies one.
 */
export interface RunPublicationProfile {
  publication_profile_id: string;
  publication_profile_version: number;
  display_name: string;
  statement: string;
  device_signal_cadence_minutes: number | null;
  simulator_source_id: string | null;
  gateway_id: string | null;
}

/** One frozen value, and who answered for it. */
export interface RunFrozenInput {
  identity_field: string;
  field: string;
  value: string;
  answered_by: string;
  answered_by_detail: string;
}

/** Why a frozen Draft may not execute, and what the reason is about. */
export interface RunBlockingReason {
  kind: string;
  subject: string;
  statement: string;
}

export interface RunUnsupportedOptionalInput {
  state_key: string;
  execution_role: string;
  statement: string;
}

export interface RunSummary {
  run_id: string;
  lifecycle_status: string;
  execution_status: string;
  created_at: string;
  site_id: string;
  scenario_id: string;
  scenario_version: number;
  frozen_inputs: RunFrozenInput[];
  blocking_reasons: RunBlockingReason[];
  unsupported_optional_inputs: RunUnsupportedOptionalInput[];
}

/** One value the run supplies because the scenario says the run owns it. */
export interface RunInputValue {
  parameter_id: string;
  value: number;
  unit: string;
}

export interface RunSetupInput {
  site_id: string;
  foundation_version: number;
  scenario_id: string;
  scenario_version: number;
  interval: { start_time: string; end_time: string };
  timestep_minutes: number;
  seed: number;
  model_profile: { profile_id: string; profile_version: number };
  publication_profile: { profile_id: string; profile_version: number };
  run_inputs: RunInputValue[];
}

export type RunProfilesResult =
  | {
      status: "loaded";
      modelProfiles: RunModelProfile[];
      publicationProfiles: RunPublicationProfile[];
    }
  | { status: "unavailable" };

export type CreateRunResult =
  | { status: "created"; run: RunSummary }
  | {
      status: "refused";
      code: string | null;
      refusalKind: string | null;
      message: string;
    }
  | { status: "unavailable" };

export interface RunSetupClient {
  listProfiles(): Promise<RunProfilesResult>;
  createRun(input: RunSetupInput): Promise<CreateRunResult>;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object";
}

function isNullableNumber(value: unknown): boolean {
  return value === null || typeof value === "number";
}

function isNullableString(value: unknown): boolean {
  return value === null || typeof value === "string";
}

function isSupportedState(value: unknown): value is RunSupportedState {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.state_key === "string" &&
    Array.isArray(value.supported_roles) &&
    value.supported_roles.every((role) => typeof role === "string") &&
    typeof value.statement === "string"
  );
}

function isModelProfile(value: unknown): value is RunModelProfile {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.model_profile_id === "string" &&
    typeof value.model_profile_version === "number" &&
    typeof value.display_name === "string" &&
    typeof value.statement === "string" &&
    Array.isArray(value.supported_states) &&
    value.supported_states.every(isSupportedState)
  );
}

function isPublicationProfile(value: unknown): value is RunPublicationProfile {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.publication_profile_id === "string" &&
    typeof value.publication_profile_version === "number" &&
    typeof value.display_name === "string" &&
    typeof value.statement === "string" &&
    isNullableNumber(value.device_signal_cadence_minutes) &&
    isNullableString(value.simulator_source_id) &&
    isNullableString(value.gateway_id)
  );
}

function isFrozenInput(value: unknown): value is RunFrozenInput {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.identity_field === "string" &&
    typeof value.field === "string" &&
    typeof value.value === "string" &&
    typeof value.answered_by === "string" &&
    typeof value.answered_by_detail === "string"
  );
}

function isBlockingReason(value: unknown): value is RunBlockingReason {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.kind === "string" &&
    typeof value.subject === "string" &&
    typeof value.statement === "string"
  );
}

function isUnsupportedOptional(
  value: unknown,
): value is RunUnsupportedOptionalInput {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.state_key === "string" &&
    typeof value.execution_role === "string" &&
    typeof value.statement === "string"
  );
}

export function isRunSummary(value: unknown): value is RunSummary {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.run_id === "string" &&
    typeof value.lifecycle_status === "string" &&
    typeof value.execution_status === "string" &&
    typeof value.created_at === "string" &&
    typeof value.site_id === "string" &&
    typeof value.scenario_id === "string" &&
    typeof value.scenario_version === "number" &&
    Array.isArray(value.frozen_inputs) &&
    value.frozen_inputs.every(isFrozenInput) &&
    Array.isArray(value.blocking_reasons) &&
    value.blocking_reasons.every(isBlockingReason) &&
    Array.isArray(value.unsupported_optional_inputs) &&
    value.unsupported_optional_inputs.every(isUnsupportedOptional)
  );
}

/**
 * Build a run setup client over the two API paths.
 *
 * A response that does not match the expected shape is `unavailable`, not a
 * partially rendered run: a screen must not display half a frozen identity
 * and let a reader believe the rest was frozen too.
 */
export function createRunSetupClient(
  profilesPath: string,
  runsPath: string,
): RunSetupClient {
  return {
    async listProfiles(): Promise<RunProfilesResult> {
      try {
        const response = await fetch(profilesPath);
        if (!response.ok) {
          return { status: "unavailable" };
        }
        const body = (await response.json()) as Record<string, unknown>;
        const models = body?.model_profiles;
        const publications = body?.publication_profiles;
        if (
          !Array.isArray(models) ||
          !models.every(isModelProfile) ||
          !Array.isArray(publications) ||
          !publications.every(isPublicationProfile)
        ) {
          return { status: "unavailable" };
        }
        return {
          status: "loaded",
          modelProfiles: models,
          publicationProfiles: publications,
        };
      } catch {
        return { status: "unavailable" };
      }
    },

    async createRun(input: RunSetupInput): Promise<CreateRunResult> {
      try {
        const response = await fetch(runsPath, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(input),
        });

        const body = (await response.json()) as Record<string, unknown>;

        if (response.status === 201) {
          const run = body?.run;
          if (!isRunSummary(run)) {
            return { status: "unavailable" };
          }
          return { status: "created", run };
        }

        // The backend's own refusal copy, placed rather than restated. A
        // second copy of the rules in the browser is a second copy to keep in
        // agreement, and the one in the browser is the one that drifts.
        const detail = body?.detail;
        if (response.status === 422 && isRecord(detail)) {
          return {
            status: "refused",
            code: typeof detail.code === "string" ? detail.code : null,
            refusalKind:
              typeof detail.refusal_kind === "string"
                ? detail.refusal_kind
                : null,
            message:
              typeof detail.message === "string"
                ? detail.message
                : "The run setup request was refused.",
          };
        }

        return { status: "unavailable" };
      } catch {
        return { status: "unavailable" };
      }
    },
  };
}
