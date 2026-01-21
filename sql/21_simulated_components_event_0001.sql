/*
Simulated components for event_0001

Outputs per firm components needed for Phase 3 mapping and comparator.
direct_delta_usd comes from exposure shock mapping.
incoming_delta_usd comes from network propagation.
simulated_delta_usd is the sum.

This keeps propagation mechanics unchanged.
*/

COPY (
  WITH
  direct_delta AS (
    SELECT
      e.firm_id,
      SUM(
        CASE
          WHEN e.hs_code = 'HS_A' THEN e.import_value_usd * 0.25
          ELSE 0
        END
      ) AS direct_delta_usd
    FROM firm_hs_exposure e
    JOIN phase1_firms f ON f.firm_id = e.firm_id
    GROUP BY e.firm_id
  ),
  out_degree AS (
    SELECT
      buyer_firm_id AS firm_id,
      COUNT(*)::numeric AS out_deg
    FROM phase1_edges
    GROUP BY buyer_firm_id
  ),
  seeds AS (
    SELECT
      d.firm_id AS path_root_firm_id,
      d.firm_id AS current_node_id,
      0::int AS depth,
      d.direct_delta_usd AS delta_usd
    FROM direct_delta d
    WHERE d.direct_delta_usd <> 0
  ),
  walk AS (
    WITH RECURSIVE w AS (
      SELECT
        s.path_root_firm_id,
        s.current_node_id,
        s.current_node_id AS from_firm_id,
        NULL::text AS to_supplier_id,
        s.depth,
        s.delta_usd AS propagated_delta_usd
      FROM seeds s

      UNION ALL

      SELECT
        w.path_root_firm_id,
        e.supplier_firm_id AS current_node_id,
        w.current_node_id AS from_firm_id,
        e.supplier_firm_id AS to_supplier_id,
        w.depth + 1 AS depth,
        (w.propagated_delta_usd / od.out_deg) AS propagated_delta_usd
      FROM w
      JOIN phase1_edges e ON e.buyer_firm_id = w.current_node_id
      JOIN out_degree od ON od.firm_id = w.current_node_id
      WHERE w.depth < 4
    )
    SELECT * FROM w
  ),
  incoming AS (
    SELECT
      to_supplier_id AS firm_id,
      SUM(propagated_delta_usd) AS incoming_delta_usd
    FROM walk
    WHERE depth >= 1 AND to_supplier_id IS NOT NULL
    GROUP BY to_supplier_id
  )
  SELECT
    f.firm_id,
    COALESCE(d.direct_delta_usd, 0) AS direct_delta_usd,
    COALESCE(i.incoming_delta_usd, 0) AS incoming_delta_usd,
    (COALESCE(d.direct_delta_usd, 0) + COALESCE(i.incoming_delta_usd, 0)) AS simulated_delta_usd
  FROM phase1_firms f
  LEFT JOIN direct_delta d ON d.firm_id = f.firm_id
  LEFT JOIN incoming i ON i.firm_id = f.firm_id
  ORDER BY f.firm_id
) TO STDOUT WITH CSV HEADER;
