/*
Phase 7: Supplier graph enrichment

Adds three intermediate supplier firms and nine buyer-supplier edges
based on publicly documented supply chain relationships during 2017-2018.

Also adds synthetic HS_A exposure for the supplier firms so they
participate in cost shock propagation as seeds.

See docs/phase7_graph_enrichment.md for full rationale and evidence.
*/

BEGIN;

-- 1. Add supplier firm HS exposure
INSERT INTO firm_hs_exposure (firm_id, hs_code, import_value_usd) VALUES
  ('FXCN', 'HS_A', 200000),
  ('AVGO', 'HS_A',  80000),
  ('INTC', 'HS_A',  60000)
ON CONFLICT (firm_id, hs_code) DO UPDATE
SET import_value_usd = EXCLUDED.import_value_usd;

-- 2. Add buyer-supplier edges
INSERT INTO supplier_edges (buyer_firm_id, supplier_firm_id) VALUES
  ('AAPL', 'FXCN'),
  ('AAPL', 'AVGO'),
  ('CSCO', 'FXCN'),
  ('DELL', 'FXCN'),
  ('DELL', 'AVGO'),
  ('DELL', 'INTC'),
  ('HPQ',  'FXCN'),
  ('HPQ',  'AVGO'),
  ('HPQ',  'INTC');

COMMIT;
