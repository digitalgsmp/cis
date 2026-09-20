// Static mirror of runtime/card_runner.py's CAPABILITIES / USAGE_REPORTING_VERIFIED /
// DEFAULT_MODEL_* / DEFAULT_TIMEOUT_SECONDS. There is no capabilities API route —
// dispatch() itself enforces these rules and returns a 400 if violated — so this
// file exists only to explain the caps in the UI *before* a dispatch is attempted.
// If runtime/card_runner.py's CAPABILITIES dict changes, this must be updated to match.

export const RUN_TARGETS = ["claude", "codex"];

export const CAPABILITIES = {
  claude: {
    max_turns: {
      enforcement: "observation_only",
      note: "No CLI flag exists to cap turns. The number of turns used is only reported after the run finishes.",
    },
    budget_usd: {
      enforcement: "native",
      note: "Enforced by the CLI's own --max-budget-usd flag.",
    },
  },
  codex: {
    max_turns: {
      enforcement: "unavailable",
      note: "No CLI flag exists for this at all — turns are never capped or reported.",
    },
    budget_usd: {
      enforcement: "unavailable",
      note: "No CLI flag exists for this at all — spend is never capped.",
    },
  },
};

export const USAGE_REPORTING_VERIFIED = { claude: true, codex: false };

export const DEFAULT_MODEL = { claude: "claude-haiku-4-5-20251001", codex: null };

export const DEFAULT_TIMEOUT_SECONDS = 1800;

export function enforcementLabel(enforcement) {
  if (enforcement === "native") return "Enforced";
  if (enforcement === "observation_only") return "Observed only, not enforced";
  return "Unavailable";
}
