-- Read-only aggregate audit. No account IDs, quantities or monetary values in output.
BEGIN READ ONLY;

WITH latest AS (
    SELECT account_id, max(report_date) AS report_date
    FROM position GROUP BY account_id
), held AS (
    SELECT DISTINCT p.instrument_id
    FROM position p JOIN latest l USING (account_id, report_date)
    WHERE p.quantity <> 0
), targets AS (
    SELECT instrument_id, bool_or(population = 'portfolio') AS held,
           bool_or(population = 'watchlist') AS watched
    FROM (
        SELECT instrument_id, 'portfolio' AS population FROM held
        UNION ALL
        SELECT instrument_id, 'watchlist' FROM watchlist_item
    ) populations GROUP BY instrument_id
)
SELECT CASE WHEN t.held AND t.watched THEN 'both'
            WHEN t.held THEN 'portfolio' ELSE 'watchlist' END AS population,
       i.kind, count(*) AS target_count,
       count(f.instrument_id) AS fundamentals_count,
       count(*) FILTER (WHERE f.fetched_at >= now() - interval '8 days') AS fresh_fundamentals,
       count(*) FILTER (WHERE i.kind = 'unknown' OR i.exchange IS NULL OR i.currency IS NULL) AS unknown_identity_count,
       count(i.currency) AS currency_count,
       count(b.instrument_id) AS daily_bars_count,
       count(*) FILTER (WHERE b.n >= 2) AS daily_change_count,
       count(*) FILTER (WHERE b.last_day >= current_date - 4) AS fresh_bars_count,
       count(w.target_price) AS user_target_count,
       count(e.instrument_id) AS etf_profile_count,
       max(b.last_day) AS last_bar,
       max(f.fetched_at) AS fundamentals_fetched_at,
       now() AS checked_at
FROM targets t JOIN instrument i ON i.id = t.instrument_id
LEFT JOIN fundamentals f ON f.instrument_id = i.id
LEFT JOIN watchlist_item w ON w.instrument_id = i.id
LEFT JOIN etf_profile e ON e.instrument_id = i.id
LEFT JOIN LATERAL (
    SELECT instrument_id, count(*) AS n, max(day) AS last_day
    FROM bar WHERE instrument_id = i.id AND interval = '1d' GROUP BY instrument_id
) b ON true
GROUP BY t.held, t.watched, i.kind;

SELECT kv.key AS metric,
       count(*) FILTER (WHERE kv.value <> 'null'::jsonb) AS nonnull_count,
       min(f.as_of) AS as_of_min, max(f.fetched_at) AS fetched_at_max
FROM fundamentals f CROSS JOIN LATERAL jsonb_each(f.metrics) kv GROUP BY kv.key;

SELECT count(*) AS profile_count, count(ter) AS ter_count, count(index_name) AS index_count,
       count(*) FILTER (WHERE distribution = 'acc') AS acc_count,
       count(*) FILTER (WHERE distribution = 'dist') AS dist_count
FROM etf_profile;
COMMIT;
