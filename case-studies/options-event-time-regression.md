# Options Event-Time Alignment and Panel Regression

**Project type:** Independent quantitative research. This was not a client engagement.

## Question

Did model confidence and option/underlying relative-value measures contain information about the next-minute state in selected 0DTE options events? The review also checked whether the apparent relationship survived correct timestamp alignment and a broader observable panel.

## Data and joins

The analysis combined option-event records, underlying spot observations, model prediction outputs, and quote/Greek data. The event and prediction files represented minutes in different clock conventions: prediction timestamps were UTC minutes while the event key was a New York local-minute index. Converting both keys to the same timezone-aware minute basis restored prediction coverage from about 7% to 100%.

The review also found that joining a same-minute spot close to an option quote could use spot information from later within that minute. The corrected analysis used the same-minute spot open for the parity comparison. Close-based outputs were retained as lookahead-contaminated diagnostics and excluded from the accepted interpretation.

## Statistical review and result

- A full observable minute panel contained **262,474 rows**. In that broad panel, the documented confidence-to-next-minute-parity relationship was effectively zero.
- In the narrower out-of-sample, action-conditioned event sample (**899 usable rows**), the relationship was stronger (Spearman correlation approximately **−0.445**).
- A panel-style OLS compared parity and confidence while controlling for spread, convexity-gap proxy, time-of-day, option type, and date. Parity remained strong in the reported specification (coefficient **0.3213**, p **4.49×10⁻³⁹**); confidence added little after parity (p **0.252**, incremental R² approximately **0.0005**).

The result is conditional on the event-selection process. It does not show that confidence predicts the next-minute state across the overall market. The full-panel result is the key limitation, and adjacent minute observations are serially dependent.

## What this demonstrates

- Diagnosing a broken multi-source join from its unexpectedly low coverage.
- Treating UTC/local time and within-bar observability as data-model requirements.
- Re-running the analysis after removing a lookahead path.
- Comparing a selected event sample with the broader observable panel and reporting the loss of generality.

The underlying quote data, prediction files, original reports, and strategy implementation are not part of this repository. This case note summarizes results from the original local research records.
