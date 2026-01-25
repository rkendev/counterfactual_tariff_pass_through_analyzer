/*
Seed candidate firms for event_0003.

This is intentionally conservative:
- exposure flags start as 0
- evidence_note remains "pending review"
- no outcomes are encoded here

You will later update exposed_flag and evidence_note once you have filing quotes.
*/

BEGIN;

DELETE FROM firm_event_exposure
WHERE event_id = 'event_0003';

INSERT INTO firm_event_exposure (
  event_id,
  firm_id,
  exposed_flag,
  exposure_bucket,
  evidence_note
) VALUES
  ('event_0003','AAPL', 0, NULL, 'pending review: add filing quote and period for China sourcing and List 2 exposure'),
  ('event_0003','CSCO', 0, NULL, 'pending review: add filing quote and period for China sourcing and List 2 exposure'),
  ('event_0003','DELL', 0, NULL, 'pending review: add filing quote and period for China sourcing and List 2 exposure'),
  ('event_0003','HPQ',  0, NULL, 'pending review: add filing quote and period for China sourcing and List 2 exposure');

COMMIT;
