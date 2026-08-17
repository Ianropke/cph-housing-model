# Scoped Agent Contract — dashboard

The root `AGENTS.md` remains authoritative. These rules specialize review of the React/Vite dashboard.

## Code Review Rules

### Do not turn indices into probabilities
Flag UI copy, formatting, charts, or labels that present EWI or Market Risk Score as a percentage chance. The safe path is to preserve the documented metric name, scale, and uncertainty semantics.

### Preserve unavailable/stale states
Flag UI changes that replace unavailable, stale, or ML-unavailable states with plausible fallback numbers or hide source status. The safe path is an explicit user-visible state.

### Significant UI changes need rendered acceptance
Do not treat build success as UI acceptance. After deterministic tests/build, verify the actual rendered task flow with browser/E2E tooling and, when available, Codex Computer Use for interaction, responsive behavior, loading/empty/error states, and obvious console/runtime failures.
