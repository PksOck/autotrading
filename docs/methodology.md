# Data Methodology

Milestones 1 and 2 use a deterministic illustrative AMZN fixture so search, chart, and financial results remain reproducible. Each snapshot and financial series contains source, ISO-8601 UTC `asOf`, currency, and unit metadata. Missing observations are `null` and render as “Not available”; they are never treated as zero.

Price ranges are calculated from the newest available observation: 1M, 6M, 1Y, and 5Y retain observations within the corresponding month window, while MAX retains all available history. The selected native button exposes its state with `aria-pressed`, and the chart publishes a text summary of its observation count, start/end prices, and change. Volume appears only when the selected series contains volume; otherwise the interface explicitly reports that it is unavailable. Financial charts mark gaps rather than interpolating or treating missing values as zero.

Freshness is calculated from `asOf` against an explicit maximum age. The UI labels stale data. Values support product research and testing only and are not financial advice, trading instructions, recommendations, or target prices.

Valuation scenarios use a two-stage discounted cash flow: an explicit forecast horizon plus a terminal value, both discounted to present, minus net debt, divided by diluted shares. Normalized free cash flow is prefilled from the latest available annual figure with its period shown; net debt starts at an explicit editable zero assumption. Terminal growth must stay below the discount rate or the section refuses to estimate; extreme but computable inputs estimate with a visible warning.

The watchlist is stored only in the visitor's browser local storage and never leaves the device.
