/*
Phase 1 shock diff
Compares baseline vs shocked "effective import cost" for the scenario in scenarios/tariff_shock_example.json

For Phase 1, we hardcode the shock to HS_A * 1.25.
This is intentional: mechanics first, realism later.
*/

COPY (
  WITH
  baseline AS (
    SELECT
      e.firm_id,
      e.hs_code,
      e.import_value_usd AS base_value_usd
    FROM firm_hs_exposure e
    JOIN phase1_firms f ON f.firm_id = e.firm_id
  ),
  shocked AS (
    SELECT
      firm_id,
      hs_code,
      base_value_usd,
      CASE
        WHEN hs_code = 'HS_A' THEN base_value_usd * 1.25
        ELSE base_value_usd
      END AS shocked_value_usd
    FROM baseline
  )
  SELECT
    firm_id,
    hs_code,
    base_value_usd,
    shocked_value_usd,
    (shocked_value_usd - base_value_usd) AS delta_usd
  FROM shocked
  WHERE shocked_value_usd <> base_value_usd
  ORDER BY firm_id, hs_code
) TO STDOUT WITH CSV HEADER;
