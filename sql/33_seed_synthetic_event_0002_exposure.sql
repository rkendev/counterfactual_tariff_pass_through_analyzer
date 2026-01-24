BEGIN;

INSERT INTO firm_hs_exposure (firm_id, hs_code, import_value_usd)
VALUES
  ('AAPL','HS_A', 100000),
  ('CSCO','HS_A',  50000),
  ('DELL','HS_A',  40000),
  ('HPQ','HS_A',   30000),
  ('QCOM','HS_A',  20000)
ON CONFLICT (firm_id, hs_code) DO UPDATE
SET import_value_usd = EXCLUDED.import_value_usd;

COMMIT;
