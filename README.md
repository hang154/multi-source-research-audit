# Multi-Source Research Audit

Portfolio material on point-in-time data joins, event-time alignment, leakage review, and statistical validation.

This repository contains concise case studies from my independent quantitative research and a small, reproducible synthetic-data demo for multi-source search intelligence. The case studies describe real research work; they are not client engagements. The runnable demo uses synthetic data only and is not evidence of performance on real data.

## What this demonstrates

- **Point-in-time joins:** retain observation and availability timestamps, respect filing publication times, and keep later revisions out of earlier decisions.
- **Event-time alignment:** join option events, underlying prices, and model outputs on a consistent timezone-aware clock; test whether same-period values were actually observable.
- **Statistical review:** compare conditional findings with the full observable panel, use fixed effects and chronological validation, and report null or negative results with the scope limits.
- **Search-intelligence audit:** inspect changing entity aliases, asynchronous source coverage, delayed revisions, and future-only outcomes in a deterministic fixture.

## Case studies

1. [Options event-time alignment and panel regression](case-studies/options-event-time-regression.md) — an options microstructure study that corrected a timezone join error and removed same-minute close lookahead before evaluating conditional relationships.
2. [Point-in-time financial and SEC filing data](case-studies/sec-point-in-time-data.md) — availability-time filtering and historical 13F panel construction, with explicit restatement and coverage rules.
3. [CRSP historical validation](case-studies/crsp-walk-forward-review.md) — a 2010–2024, 28-name research panel evaluated with chronological folds and block-bootstrap uncertainty; no independent discovery was established.

The examples come from separate projects. Together they show both temporal data handling and statistical evaluation without implying that one study contained every method.

## Reproducible synthetic demo

The demo models asynchronous search snapshots, crawls, backlinks, AI-citation observations, effective-dated URL aliases, and future business outcomes. It builds a point-in-time panel and reports leakage, coverage, selection, and temporal-validation diagnostics.

Requirements: Python 3.10 or later.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
PYTHONPATH=src python -m temporal_audit_demo --output reports/reproduced
```

The checked-in `data/generated/` reference output was generated with seed `20261019`. Its 32 entities and all observations are synthetic. The generated model metrics are workflow diagnostics only; they do not establish real-world predictive skill, causality, or trading performance.

## Repository layout

```text
case-studies/       Public summaries of separate personal research projects
data/generated/     Deterministic synthetic fixture and reference outputs
src/                Synthetic point-in-time panel and audit implementation
```

## Data and disclosure

No private source exports, licensed market-data files, credentials, or full strategy implementation are included. Real-project results are summarized at a level suitable for a portfolio; the source data and original research repositories remain separate. The CRSP study used a fixed convenience panel and is not a survivorship-free universe. The SEC 13F panel was incomplete and was not used as a complete ownership census. Historical research results are not evidence of future performance.

## Scope

The case studies are self-directed research, not paid client work. The synthetic demo is a new portfolio artifact, not a prior client project. A client-specific review would begin by confirming source permissions, data grain, identity keys, timezone semantics, revision behavior, missingness, and target availability.
