# Scoped Agent Contract — model/server

The root `AGENTS.md` remains authoritative. These rules specialize review of `server/` changes.

## Code Review Rules

### Keep metric semantics distinct
Flag any change that treats EWI or Market Risk Score as an empirical probability, or changes the ML crash-probability contract without aligned tests/documentation. The safe path is to preserve the documented metric type and scale explicitly.

### Preserve source time and provenance
Flag payload/model changes that confuse observation period with retrieval time or remove source/status lineage. The safe path is explicit source identity, observation period, retrieval timestamp, and availability/freshness status.

### No synthetic production fallback
Flag any path that replaces unavailable authoritative data with mock/synthetic/proxy values while presenting output as live. The safe path is explicit stale/unavailable/model-unavailable state.
