BEGIN;

DELETE FROM firm_hs_exposure
WHERE firm_id IN ('AAPL','CSCO','DELL','HPQ');

INSERT INTO firm_hs_exposure (firm_id, hs_code, import_value_usd) VALUES
  ('AAPL','HS_A', 100000),
  ('CSCO','HS_A',  50000),
  ('DELL','HS_A',  40000),
  ('HPQ','HS_A',   30000);

COMMIT;
