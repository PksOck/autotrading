# Data Methodology

Milestone 1 uses illustrative fixture data. Each snapshot and financial series contains source, ISO-8601 UTC `asOf`, currency, and unit metadata. Missing observations are `null` and render as “Not available”; they are never treated as zero.

Freshness is calculated from `asOf` against an explicit maximum age. The UI labels stale data. Values support product research and testing only and are not financial advice, trading instructions, recommendations, or target prices.
