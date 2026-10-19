# Portfolio case study: temporal joins and leakage review

**Project type:** New synthetic-data demonstration; no external client or production system.

## Problem represented

Multi-source research systems often combine observations with different grains, update schedules, aliases, and publication delays. Joining on observation date alone can make a later correction appear available before a historical decision. Changing URL identities and incomplete source coverage can also distort the sample used for statistical modeling.

## What this demo implements

1. Generated deterministic, synthetic extracts for ranking, crawl, backlink, AI-citation, identity, and future-outcome sources.
2. Resolved changing aliases against effective-dated mappings.
3. Joined each feature only when its observation and availability timestamps were no later than the decision cutoff.
4. Counted cases where a latest-observation join would introduce information unavailable at the cutoff.
5. Built a forward 28-day target, used non-overlapping decision windows, and purged the target horizon between training and evaluation.
6. Reported a logistic-regression baseline and entity-cluster bootstrap interval for a descriptive selection-bias diagnostic.

## What the result means

The project demonstrates an auditable method and repeatable implementation on synthetic data. It does not establish predictive accuracy on real data, causality, or a result from prior client work. A client-specific review would require access to the real data contracts and source vintages before making substantive recommendations.

## Reproduce

```bash
python -m pip install -r requirements.txt
PYTHONPATH=src python -m temporal_audit_demo --output data/generated
```
