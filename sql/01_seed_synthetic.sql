TRUNCATE firm_hs_exposure;
TRUNCATE supplier_edges;

INSERT INTO firm_hs_exposure (firm_id, hs_code, import_value_usd) VALUES
  ('F0','HS_A', 100000),
  ('F0','HS_B',  10000),

  ('S1','HS_A',  30000),
  ('S2','HS_A',  20000),
  ('S3','HS_A',  15000),
  ('S4','HS_A',  10000),

  ('B1','HS_A',   5000),
  ('B2','HS_A',   5000),
  ('B3','HS_B',   5000);

INSERT INTO supplier_edges (buyer_firm_id, supplier_firm_id) VALUES
  ('F0','S1'),
  ('F0','S2'),
  ('S1','S3'),
  ('S3','S4'),
  ('S2','S4'),
  ('B1','S1'),
  ('B2','S1'),
  ('B3','S2');
