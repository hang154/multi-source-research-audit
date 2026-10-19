# CRSP Historical Walk-Forward Review

**Project type:** Independent historical-model development study; not a client engagement.

## Dataset and identity policy

A local research snapshot used CRSP daily stock data from **2010-01-04 through 2024-12-31**. The stored extract contained **105,672 rows** for a fixed 28-name convenience panel; the model-ready aligned panel contained **3,774 date rows**. Security identity was held by PERMNO, with ticker aliases retained as metadata. Rows were aligned to observed SPY sessions without forward-fill or backward-fill.

The panel was selected for development convenience. It is not a point-in-time, survivorship-free universe, and the price-return series is not a dividend-inclusive total-return series.

## Evaluation

The historical development run tested 16 chronological folds and used a moving-block bootstrap to assess incremental mean-squared-error gains over a baseline. The work recorded candidate definitions, data hashes, fold boundaries, and evaluation outputs.

**Outcome:** no independent discovery was established. The reported candidate gains were generally small or uncertain, and the run is labeled historical development rather than independent out-of-sample proof. That negative result is retained as part of the research record.

The source extract, full model outputs, and private research database are not included in this repository. This case note summarizes the dataset manifest and completed development-run records.
