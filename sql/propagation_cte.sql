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
  rec AS (
    WITH RECURSIVE walk AS (
      -- columns: root, current_node, from, to, depth, delta
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
      FROM walk w
      JOIN phase1_edges e
        ON e.buyer_firm_id = w.current_node_id
      JOIN out_degree od
        ON od.firm_id = w.current_node_id
      WHERE w.depth < 4
    )
    SELECT
      path_root_firm_id,
      from_firm_id,
      to_supplier_id,
      depth,
      propagated_delta_usd
    FROM walk
  )
  SELECT *
  FROM rec
  ORDER BY path_root_firm_id, depth, from_firm_id, to_supplier_id
) TO STDOUT WITH CSV HEADER;
