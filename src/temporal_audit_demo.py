"""Synthetic point-in-time audit for asynchronous research data sources.

The fixture is deliberately small and deterministic. It is a portfolio demo,
not a market-data product or evidence of a prior client engagement.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Iterable

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

UTC = timezone.utc
FEATURES = ("visibility", "content_quality", "referring_domains", "ai_citations")
HORIZON_DAYS = 28
SEED = 20261019


@dataclass(frozen=True)
class AuditRow:
    entity_id: str
    decision_at: str
    visibility: float
    content_quality: float
    referring_domains: float
    ai_citations: float
    visibility_age_days: int
    content_age_days: int
    target_events_28d: int
    target_any_event_28d: int
    feature_sources: str


def iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"Timestamp must include a timezone: {value}")
    return parsed.astimezone(UTC)


def write_csv(path: Path, rows: Iterable[dict]) -> None:
    materialized = list(rows)
    if not materialized:
        raise ValueError(f"Refusing to write empty fixture: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(materialized[0]))
        writer.writeheader()
        writer.writerows(materialized)


def generate_fixture(output: Path) -> dict[str, int]:
    """Create reproducible synthetic source extracts with realistic timing gaps."""
    rng = random.Random(SEED)
    start = datetime(2025, 1, 6, 12, tzinfo=UTC)
    entity_count, week_count = 32, 36
    entities, aliases, search, crawls, backlinks, citations, outcomes = [], [], [], [], [], [], []
    latent: dict[str, tuple[float, float]] = {}

    for number in range(entity_count):
        entity_id = f"ORG-{number:03d}"
        base_visibility = rng.uniform(18, 78)
        quality = rng.uniform(25, 90)
        latent[entity_id] = (base_visibility, quality)
        entities.append({"entity_id": entity_id, "sector": f"sector-{number % 4}", "synthetic_only": "true"})
        old_alias, new_alias = f"site-{number:03d}-old", f"site-{number:03d}-new"
        switch_at = start + timedelta(weeks=18)
        if number % 4 == 0:
            aliases.extend([
                {"alias": old_alias, "entity_id": entity_id, "valid_from": iso(start - timedelta(days=365)), "valid_to": iso(switch_at)},
                {"alias": new_alias, "entity_id": entity_id, "valid_from": iso(switch_at), "valid_to": ""},
            ])
        else:
            aliases.append({"alias": old_alias, "entity_id": entity_id, "valid_from": iso(start - timedelta(days=365)), "valid_to": ""})

        visibility, content = base_visibility, quality
        for week in range(week_count):
            observed = start + timedelta(weeks=week)
            alias = new_alias if number % 4 == 0 and observed >= switch_at else old_alias
            # A few sources observe low-visibility entities less often. This
            # creates a known, measurable missing-not-at-random selection effect.
            visibility = max(1.0, min(100.0, visibility + rng.gauss(0.8, 5.0)))
            content = max(1.0, min(100.0, content + rng.gauss(0.25, 3.2)))
            captured = visibility >= 29 or rng.random() < 0.24
            delay_hours = rng.choice((1, 2, 8, 26, 50))
            available = observed + timedelta(hours=delay_hours)
            row_id = f"{entity_id}-W{week:02d}"
            if captured:
                search.append({"row_id": row_id, "alias": alias, "observed_at": iso(observed), "available_at": iso(available),
                               "visibility": round(visibility, 4), "rank_position": max(1, round(105 - visibility + rng.gauss(0, 7))),
                               "source_version": "original"})
                # A delayed correction makes observation time differ from
                # information-availability time for the same source period.
                if week == 11 and number % 7 == 0:
                    search.append({"row_id": row_id + "-REV", "alias": alias, "observed_at": iso(observed),
                                   "available_at": iso(available + timedelta(days=4)),
                                   "visibility": round(min(100.0, visibility + 18), 4),
                                   "rank_position": max(1, round(87 - visibility)), "source_version": "late_revision"})
            crawls.append({"row_id": row_id, "alias": alias, "observed_at": iso(observed + timedelta(hours=3)),
                           "available_at": iso(observed + timedelta(hours=3 + rng.choice((1, 3, 18, 30)))),
                           "content_quality": round(content, 4), "word_count": max(180, round(420 + content * 31 + rng.gauss(0, 170)))})
            backlinks.append({"row_id": row_id, "alias": alias, "observed_at": iso(observed + timedelta(hours=8)),
                              "available_at": iso(observed + timedelta(hours=8 + rng.choice((2, 12, 32)))),
                              "referring_domains": max(0, round(base_visibility / 4 + week * 0.7 + rng.gauss(0, 4)))})
            citations.append({"row_id": row_id, "alias": alias, "observed_at": iso(observed + timedelta(hours=5)),
                              "available_at": iso(observed + timedelta(hours=5 + rng.choice((1, 7, 27)))),
                              "ai_citations": max(0, round(visibility / 18 + content / 23 + rng.gauss(0, 1.6)))})

            # A synthetic future business outcome with a weak, noisy relationship
            # to the generated features; it is never used as a contemporaneous feature.
            logit = -4.7 + visibility * 0.026 + content * 0.018 + math.log1p(max(0, base_visibility / 4)) * 0.22
            probability = 1 / (1 + math.exp(-logit))
            event = int(rng.random() < probability)
            outcomes.append({"row_id": row_id, "alias": alias, "event_at": iso(observed + timedelta(days=3)),
                             "available_at": iso(observed + timedelta(days=5)), "qualified_inquiries": event})

    paths = {
        "entities.csv": entities,
        "aliases.csv": aliases,
        "search_snapshots.csv": search,
        "crawl_snapshots.csv": crawls,
        "backlink_snapshots.csv": backlinks,
        "ai_citation_snapshots.csv": citations,
        "outcomes.csv": outcomes,
    }
    for name, rows in paths.items():
        write_csv(output / name, rows)
    return {name: len(rows) for name, rows in paths.items()}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def resolve_alias(alias: str, at: datetime, intervals: dict[str, list[dict[str, str]]]) -> str | None:
    matches = []
    for row in intervals.get(alias, []):
        start = parse_time(row["valid_from"])
        end = parse_time(row["valid_to"]) if row.get("valid_to") else None
        if start <= at and (end is None or at < end):
            matches.append(row["entity_id"])
    if len(matches) > 1:
        raise ValueError(f"Overlapping identity intervals for alias {alias} at {iso(at)}")
    return matches[0] if matches else None


def eligible_source_rows(rows: list[dict[str, str]], cutoff: datetime, intervals: dict[str, list[dict[str, str]]]) -> dict[str, dict[str, str]]:
    latest: dict[str, dict[str, str]] = {}
    for row in rows:
        observed, available = parse_time(row["observed_at"]), parse_time(row["available_at"])
        if observed > cutoff or available > cutoff:
            continue
        entity = resolve_alias(row["alias"], observed, intervals)
        if entity is None:
            continue
        previous = latest.get(entity)
        ordering = (observed, available)
        if previous is None or ordering > (parse_time(previous["observed_at"]), parse_time(previous["available_at"])):
            latest[entity] = row
    return latest


def build_panel(data_dir: Path) -> tuple[list[AuditRow], dict[str, int | float]]:
    entities = read_csv(data_dir / "entities.csv")
    aliases: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(data_dir / "aliases.csv"):
        aliases[row["alias"]].append(row)
    search, crawl = read_csv(data_dir / "search_snapshots.csv"), read_csv(data_dir / "crawl_snapshots.csv")
    backlink, citation = read_csv(data_dir / "backlink_snapshots.csv"), read_csv(data_dir / "ai_citation_snapshots.csv")
    outcome_rows = read_csv(data_dir / "outcomes.csv")
    weekly_decisions = sorted({parse_time(row["observed_at"]).date() for row in crawl})
    # Evaluate non-overlapping 28-day outcome windows. Source snapshots remain
    # weekly and are still joined at the exact decision cutoff.
    decisions = weekly_decisions[::4]
    outcomes_by_entity: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in outcome_rows:
        event_at = parse_time(row["event_at"])
        entity = resolve_alias(row["alias"], event_at, aliases)
        if entity:
            outcomes_by_entity[entity].append(row)

    panel: list[AuditRow] = []
    universe_targets: list[int] = []
    included_targets: list[int] = []
    excluded_targets: list[int] = []
    counts = {"late_source_rows_excluded": 0, "unmapped_alias_rows": 0, "incomplete_entity_decisions": 0}
    all_sources = (search, crawl, backlink, citation)
    for decision_date in decisions:
        cutoff = datetime.combine(decision_date, time(23, 59, 59), UTC)
        maps = [eligible_source_rows(rows, cutoff, aliases) for rows in all_sources]
        for rows in all_sources:
            counts["late_source_rows_excluded"] += sum(
                parse_time(row["observed_at"]) <= cutoff < parse_time(row["available_at"]) for row in rows
            )
        for entity in entities:
            entity_id = entity["entity_id"]
            source_records = [mapping.get(entity_id) for mapping in maps]
            end = cutoff + timedelta(days=HORIZON_DAYS)
            future = [row for row in outcomes_by_entity[entity_id]
                      if cutoff < parse_time(row["event_at"]) <= end
                      and parse_time(row["available_at"]) <= end + timedelta(days=2)]
            target = sum(int(row["qualified_inquiries"]) for row in future)
            universe_targets.append(int(target > 0))
            # Keep only entities with a captured search metric and a crawl row;
            # report the excluded population separately for selection-bias review.
            if source_records[0] is None or source_records[1] is None:
                counts["incomplete_entity_decisions"] += 1
                excluded_targets.append(int(target > 0))
                continue
            included_targets.append(int(target > 0))
            search_row, crawl_row, backlink_row, citation_row = source_records
            assert search_row and crawl_row
            cutoff_iso = iso(cutoff)
            panel.append(AuditRow(
                entity_id=entity_id, decision_at=cutoff_iso,
                visibility=float(search_row["visibility"]),
                content_quality=float(crawl_row["content_quality"]),
                referring_domains=float(backlink_row["referring_domains"]) if backlink_row else 0.0,
                ai_citations=float(citation_row["ai_citations"]) if citation_row else 0.0,
                visibility_age_days=(cutoff - parse_time(search_row["observed_at"])).days,
                content_age_days=(cutoff - parse_time(crawl_row["observed_at"])).days,
                target_events_28d=target, target_any_event_28d=int(target > 0),
                feature_sources="|".join(str(index) for index, record in enumerate(source_records) if record),
            ))
    counts["universe_future_event_rate"] = round(sum(universe_targets) / len(universe_targets), 4)
    counts["included_future_event_rate"] = round(sum(included_targets) / len(included_targets), 4) if included_targets else 0.0
    counts["excluded_future_event_rate"] = round(sum(excluded_targets) / len(excluded_targets), 4) if excluded_targets else 0.0
    return panel, counts


def leakage_audit(data_dir: Path) -> dict[str, int]:
    aliases: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(data_dir / "aliases.csv"):
        aliases[row["alias"]].append(row)
    search = read_csv(data_dir / "search_snapshots.csv")
    cutoffs = sorted({parse_time(row["observed_at"]).date() for row in read_csv(data_dir / "crawl_snapshots.csv")})
    violations = []
    for decision in cutoffs:
        cutoff = datetime.combine(decision, time(23, 59, 59), UTC)
        legal = eligible_source_rows(search, cutoff, aliases)
        latest_observed: dict[str, dict[str, str]] = {}
        for row in search:
            observed = parse_time(row["observed_at"])
            if observed > cutoff:
                continue
            entity = resolve_alias(row["alias"], observed, aliases)
            if entity and (entity not in latest_observed or observed > parse_time(latest_observed[entity]["observed_at"])):
                latest_observed[entity] = row
        for entity, row in latest_observed.items():
            if parse_time(row["available_at"]) > cutoff and (entity not in legal or legal[entity]["row_id"] != row["row_id"]):
                violations.append({"entity_id": entity, "decision_at": iso(cutoff), "row_id": row["row_id"]})
    return {"legal_rows_by_cutoff_entity": sum(len(eligible_source_rows(search, datetime.combine(day, time(23, 59, 59), UTC), aliases)) for day in cutoffs),
            "naive_future_availability_violations": len(violations),
            "examples": violations[:5]}


def time_split(panel: list[AuditRow]) -> tuple[list[AuditRow], list[AuditRow], str]:
    decision_dates = sorted({parse_time(row.decision_at) for row in panel})
    boundary = decision_dates[int(len(decision_dates) * 0.65)]
    train_end = boundary - timedelta(days=HORIZON_DAYS)
    train = [row for row in panel if parse_time(row.decision_at) < train_end]
    test = [row for row in panel if parse_time(row.decision_at) >= boundary]
    return train, test, iso(boundary)


def model_metrics(train: list[AuditRow], test: list[AuditRow]) -> dict:
    x_train = np.asarray([[getattr(row, name) for name in FEATURES] for row in train], dtype=float)
    y_train = np.asarray([row.target_any_event_28d for row in train], dtype=int)
    x_test = np.asarray([[getattr(row, name) for name in FEATURES] for row in test], dtype=float)
    y_test = np.asarray([row.target_any_event_28d for row in test], dtype=int)
    if len(set(y_train)) < 2 or len(set(y_test)) < 2:
        raise ValueError("Synthetic fixture did not produce both target classes in train and test; adjust the fixed seed")
    model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, class_weight="balanced", random_state=SEED))
    model.fit(x_train, y_train)
    probabilities = model.predict_proba(x_test)[:, 1]
    coefficients = model.named_steps["logisticregression"].coef_[0]
    return {
        "train_rows": len(train), "test_rows": len(test),
        "train_cutoff_start": min(row.decision_at for row in train),
        "train_cutoff_end": max(row.decision_at for row in train),
        "test_cutoff_start": min(row.decision_at for row in test),
        "test_cutoff_end": max(row.decision_at for row in test),
        "purge_gap_days": HORIZON_DAYS,
        "test_positive_rate": round(float(y_test.mean()), 4),
        "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4),
        "average_precision": round(float(average_precision_score(y_test, probabilities)), 4),
        "brier_score": round(float(brier_score_loss(y_test, probabilities)), 4),
        "coefficients_standardized": {name: round(float(value), 4) for name, value in zip(FEATURES, coefficients)},
        "interpretation": "Synthetic demonstration only; these metrics are not evidence of predictive skill on real search or business data.",
    }


def selection_diagnostics(panel: list[AuditRow], incomplete_decisions: int) -> dict:
    by_entity: dict[str, list[AuditRow]] = defaultdict(list)
    for row in panel:
        by_entity[row.entity_id].append(row)
    entity_means = {entity: sum(row.target_any_event_28d for row in rows) / len(rows) for entity, rows in by_entity.items()}
    visibility_by_entity = {entity: sum(row.visibility for row in rows) / len(rows) for entity, rows in by_entity.items()}
    median_visibility = float(np.median(list(visibility_by_entity.values())))
    high = [entity_means[entity] for entity, value in visibility_by_entity.items() if value >= median_visibility]
    low = [entity_means[entity] for entity, value in visibility_by_entity.items() if value < median_visibility]
    rng = np.random.default_rng(SEED)
    boot_differences = []
    for _ in range(2000):
        high_draw = rng.choice(high, size=len(high), replace=True)
        low_draw = rng.choice(low, size=len(low), replace=True)
        boot_differences.append(float(np.mean(high_draw) - np.mean(low_draw)))
    difference = float(np.mean(high) - np.mean(low)) if high and low else None
    return {
        "entities_in_panel": len(by_entity), "entity_decisions_excluded_for_missing_search_or_crawl": incomplete_decisions,
        "high_visibility_entity_mean_event_rate": round(float(np.mean(high)), 4) if high else None,
        "low_visibility_entity_mean_event_rate": round(float(np.mean(low)), 4) if low else None,
        "high_minus_low_event_rate_difference": round(difference, 4) if difference is not None else None,
        "entity_cluster_bootstrap_95pct_ci": [round(float(np.quantile(boot_differences, 0.025)), 4),
                                               round(float(np.quantile(boot_differences, 0.975)), 4)] if boot_differences else None,
        "bootstrap_resamples": len(boot_differences),
        "warning": "Coverage depends partly on generated visibility. Compare the observed panel with the source universe before generalizing; do not interpret this synthetic gap causally.",
    }


def run(output: Path) -> dict:
    sample_dir = output / "sample"
    counts = generate_fixture(sample_dir)
    panel, panel_counts = build_panel(sample_dir)
    train, test, boundary = time_split(panel)
    leakage = leakage_audit(sample_dir)
    result = {
        "project": "temporal-search-audit-demo",
        "data_status": "synthetic_only",
        "seed": SEED,
        "decision_horizon_days": HORIZON_DAYS,
        "source_rows": counts,
        "panel_rows": len(panel),
        "panel_build_diagnostics": panel_counts,
        "leakage_audit": leakage,
        "temporal_validation": {"test_boundary": boundary, **model_metrics(train, test)},
        "selection_diagnostics": {
            **selection_diagnostics(panel, int(panel_counts["incomplete_entity_decisions"])),
            "universe_future_event_rate": panel_counts["universe_future_event_rate"],
            "included_future_event_rate": panel_counts["included_future_event_rate"],
            "excluded_future_event_rate": panel_counts["excluded_future_event_rate"],
        },
    }
    output.mkdir(parents=True, exist_ok=True)
    with (output / "panel.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(asdict(panel[0])))
        writer.writeheader()
        writer.writerows(asdict(row) for row in panel)
    (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (output / "REPORT.md").write_text(render_report(result), encoding="utf-8")
    return result


def render_report(result: dict) -> str:
    model = result["temporal_validation"]
    leakage = result["leakage_audit"]
    selection = result["selection_diagnostics"]
    return f"""# Synthetic Temporal Data Audit — Run Report

> **Data status: synthetic only.** This report demonstrates an audit workflow. It is not an empirical market or client result.

## Scope

- Source extracts: {len(result['source_rows'])} files; {sum(result['source_rows'].values()):,} total rows.
- Built decision panel: {result['panel_rows']:,} entity-decision rows.
- Target: any qualified inquiry in the 28 days after each decision timestamp.
- Identity: aliases are resolved using validity intervals at each source observation time.
- Point-in-time rule: both `observed_at` and `available_at` must be at or before the decision cutoff.

## Findings from the generated fixture

- A naive latest-observation join would select {leakage['naive_future_availability_violations']:,} source rows before they were available.
- Correctly eligible source rows across entity-cutoffs: {leakage['legal_rows_by_cutoff_entity']:,}.
- Entity decisions excluded for missing search/crawl coverage: {selection['entity_decisions_excluded_for_missing_search_or_crawl']:,}.
- Future-event rate for full universe / included panel / excluded decisions: {selection['universe_future_event_rate']} / {selection['included_future_event_rate']} / {selection['excluded_future_event_rate']}.
- Mean 28-day outcome rate by entity visibility cohort: high={selection['high_visibility_entity_mean_event_rate']}, low={selection['low_visibility_entity_mean_event_rate']}.
- High-minus-low difference={selection['high_minus_low_event_rate_difference']}; entity-cluster bootstrap 95% interval={selection['entity_cluster_bootstrap_95pct_ci']} ({selection['bootstrap_resamples']:,} resamples).
- Forward-only test ROC AUC={model['roc_auc']}, average precision={model['average_precision']}, Brier={model['brier_score']}.
- Train rows={model['train_rows']:,}; test rows={model['test_rows']:,}; purged overlap gap={model['purge_gap_days']} days.

## Review notes

1. Preserve both observation time and availability time; a corrected historical row is not available to an earlier decision.
2. Resolve changing URL aliases against effective intervals, and fail closed on overlapping identity mappings.
3. Keep the outcome window strictly after the decision cutoff. Purge the full label horizon between train and test periods.
4. Report coverage loss and compare included and excluded entities before generalizing from observed records.
5. The small synthetic panel is useful for exercising code paths, not for claiming a stable model or causal effect.

Reproduce with `python -m temporal_audit_demo --output reports/reproduced` after installing `requirements.txt`.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a synthetic multi-source temporal audit demonstration.")
    parser.add_argument("--output", type=Path, default=Path("reports/run"), help="Output directory for synthetic extracts, panel, and report")
    args = parser.parse_args()
    result = run(args.output)
    print(json.dumps({"output": str(args.output), "panel_rows": result["panel_rows"],
                      "leakage_violations": result["leakage_audit"]["naive_future_availability_violations"],
                      "test_roc_auc": result["temporal_validation"]["roc_auc"]}, indent=2))


if __name__ == "__main__":
    main()
