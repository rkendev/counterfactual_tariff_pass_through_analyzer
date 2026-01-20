DELETE FROM observed_margin_sign WHERE event_id = 'event_0001';

INSERT INTO observed_margin_sign (event_id, firm_id, margin_change_sign) VALUES
  ('event_0001','B1',-1),
  ('event_0001','B2',-1),
  ('event_0001','B3', 0),
  ('event_0001','F0',-1),
  ('event_0001','S1',-1),
  ('event_0001','S2',-1),
  ('event_0001','S3',-1),
  ('event_0001','S4',-1);
