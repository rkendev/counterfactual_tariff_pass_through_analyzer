BEGIN;

INSERT INTO firm_event_exposure (event_id, firm_id, exposed_flag, exposure_bucket, evidence_note)
VALUES
  ('event_0002','AAPL',0,NULL,'pending review: check 2018 filings for China sourcing and List 1 exposure'),
  ('event_0002','HPQ',0,NULL,'pending review: check 2018 filings for China sourcing and List 1 exposure'),
  ('event_0002','DELL',0,NULL,'pending review: check 2018 filings for China sourcing and List 1 exposure'),
  ('event_0002','CSCO',0,NULL,'pending review: check 2018 filings for China sourcing and List 1 exposure'),
  ('event_0002','QCOM',0,NULL,'pending review: check 2018 filings for China sourcing and List 1 exposure')
ON CONFLICT (event_id, firm_id) DO NOTHING;

COMMIT;
