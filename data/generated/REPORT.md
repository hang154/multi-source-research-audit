# Synthetic Temporal Data Audit — Run Report

> **Data status: synthetic only.** This report demonstrates an audit workflow. It is not an empirical market or client result.

## Scope

- Source extracts: 7 files; 5,781 total rows.
- Built decision panel: 267 entity-decision rows.
- Target: any qualified inquiry in the 28 days after each decision timestamp.
- Identity: aliases are resolved using validity intervals at each source observation time.
- Point-in-time rule: both `observed_at` and `available_at` must be at or before the decision cutoff.

## Findings from the generated fixture

- A naive latest-observation join would select 440 source rows before they were available.
- Correctly eligible source rows across entity-cutoffs: 1,138.
- Entity decisions excluded for missing search/crawl coverage: 21.
- Future-event rate for full universe / included panel / excluded decisions: 0.5903 / 0.5993 / 0.4762.
- Mean 28-day outcome rate by entity visibility cohort: high=0.7535, low=0.4479.
- High-minus-low difference=0.3056; entity-cluster bootstrap 95% interval=[0.1779, 0.4384] (2,000 resamples).
- Forward-only test ROC AUC=0.6718, average precision=0.7764, Brier=0.2288.
- Train rows=107; test rows=128; purged overlap gap=28 days.

## Review notes

1. Preserve both observation time and availability time; a corrected historical row is not available to an earlier decision.
2. Resolve changing URL aliases against effective intervals, and fail closed on overlapping identity mappings.
3. Keep the outcome window strictly after the decision cutoff. Purge the full label horizon between train and test periods.
4. Report coverage loss and compare included and excluded entities before generalizing from observed records.
5. The small synthetic panel is useful for exercising code paths, not for claiming a stable model or causal effect.

Reproduce with `python -m temporal_audit_demo --output reports/reproduced` after installing `requirements.txt`.
