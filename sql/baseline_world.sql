/*
Baseline world extraction for Phase 1
Outputs a normalized baseline input view restricted to the Phase 1 subgraph.

Result columns are intentionally minimal and inspectable.
*/

COPY (
  WITH
  exp AS (
    SELECT
      e.firm_id,
      e.hs_code,
      e.import_value_usd
    FROM firm_hs_exposure e
    JOIN phase1_firms f ON f.firm_id = e.firm_id
  ),
  edges AS (
    SELECT
      e.buyer_firm_id,
      e.supplier_firm_id
    FROM phase1_edges e
  )
  SELECT
    exp.firm_id,
    exp.hs_code,
    exp.import_value_usd,
    edges.buyer_firm_id,
    edges.supplier_firm_id
  FROM exp
  LEFT JOIN edges
    ON edges.buyer_firm_id = exp.firm_id
  ORDER BY exp.firm_id, exp.hs_code, edges.supplier_firm_id
) TO STDOUT WITH CSV HEADER;
