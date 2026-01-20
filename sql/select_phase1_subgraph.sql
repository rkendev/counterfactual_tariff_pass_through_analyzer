/*
Phase 1 Subgraph Selection (PostgreSQL)
Creates:
  phase1_firms
  phase1_edges

Base tables:
  firm_hs_exposure(firm_id, hs_code, import_value_usd)
  supplier_edges(buyer_firm_id, supplier_firm_id)

Parameters (edit if needed):
  max_up_depth   = 3
  max_down_depth = 2
  max_firms_cap  = 200
*/

BEGIN;

DROP TABLE IF EXISTS phase1_edges;
DROP TABLE IF EXISTS phase1_firms;

-- Create phase1_firms
CREATE TABLE phase1_firms AS
WITH
hs_scope AS (
  SELECT hs_code
  FROM (VALUES
    ('HS_A'),
    ('HS_B')
  ) v(hs_code)
),
anchor AS (
  SELECT e.firm_id
  FROM firm_hs_exposure e
  JOIN hs_scope h ON h.hs_code = e.hs_code
  GROUP BY e.firm_id
  ORDER BY SUM(e.import_value_usd) DESC, e.firm_id
  LIMIT 1
),
upstream AS (
  WITH RECURSIVE up AS (
    SELECT a.firm_id AS firm_id, 0::int AS depth
    FROM anchor a
    UNION ALL
    SELECT se.supplier_firm_id AS firm_id, up.depth + 1 AS depth
    FROM up
    JOIN supplier_edges se ON se.buyer_firm_id = up.firm_id
    WHERE up.depth < 3
  )
  SELECT firm_id, MIN(depth) AS min_depth
  FROM up
  GROUP BY firm_id
),
first_hop_suppliers AS (
  SELECT firm_id
  FROM upstream
  WHERE min_depth = 1
),
downstream AS (
  WITH RECURSIVE dn AS (
    SELECT fhs.firm_id AS firm_id, 0::int AS depth
    FROM first_hop_suppliers fhs
    UNION ALL
    SELECT se.buyer_firm_id AS firm_id, dn.depth + 1 AS depth
    FROM dn
    JOIN supplier_edges se ON se.supplier_firm_id = dn.firm_id
    WHERE dn.depth < 2
  )
  SELECT firm_id, MIN(depth) AS min_depth
  FROM dn
  GROUP BY firm_id
),
combined_firms AS (
  SELECT firm_id FROM upstream
  UNION
  SELECT firm_id FROM downstream
)
SELECT firm_id
FROM combined_firms
ORDER BY firm_id
LIMIT 200
;

-- Create phase1_edges (induced by phase1_firms)
CREATE TABLE phase1_edges AS
SELECT
  se.buyer_firm_id,
  se.supplier_firm_id
FROM supplier_edges se
JOIN phase1_firms b ON b.firm_id = se.buyer_firm_id
JOIN phase1_firms s ON s.firm_id = se.supplier_firm_id
ORDER BY se.buyer_firm_id, se.supplier_firm_id
;

COMMIT;
