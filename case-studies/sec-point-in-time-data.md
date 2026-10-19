# Point-in-Time Financial and SEC Filing Data

**Project type:** Independent quantitative research. This was not a client engagement.

## Data preparation

One research pipeline combined historical prices, reported financial facts, and SEC institutional-ownership filings. It scanned **7,653,159 raw 13F rows**, extracted **11,675 target rows**, and built a **34,776-row comparison panel** for the same 1,242 reporting managers.

## As-of rules

- A fact can enter a decision only when `available_at <= as_of`.
- The daily cutoff is defined explicitly in the market timezone. A filing with only a calendar date is conservatively treated as available at midnight on the following day.
- Later-filed restatements are excluded from earlier snapshots.
- Conflicting same-time versions are treated as unknown instead of being resolved by arbitrary row order.
- Missing values stay missing; they are not silently converted to zero.

## Result and limits

The screening pipeline generated a research watchlist and detailed evidence cards, but the 14-name detailed sample did not pass every full research entry criterion. The 13F comparison panel is not a complete ownership census. The selected equity sample is not a survivorship-free historical universe, so the research does not establish investable alpha.

The original source exports and detailed security-level outputs are intentionally not included here. This public case note documents the point-in-time design and scale without redistributing source data.

The original source exports, detailed security-level outputs, and implementation are not part of this repository. This case note summarizes the methods and aggregate counts from the local research records.
