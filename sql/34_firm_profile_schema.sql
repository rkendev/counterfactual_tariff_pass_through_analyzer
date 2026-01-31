/*
Phase 5+: firm profile gating schema

Purpose
Store a minimal per event per firm profile label that determines whether
cost delta to margin sign mapping is in scope for that firm.

Profiles
- manufacturing_cost_linked
- ip_licensing_dominated
- services_and_software_weighted

Notes
- Keep as TEXT with a CHECK constraint for simplicity and portability.
- evidence_note is required so every label remains auditable.
*/

BEGIN;

CREATE TABLE IF NOT EXISTS firm_profile (
  event_id TEXT NOT NULL,
  firm_id TEXT NOT NULL,
  firm_profile TEXT NOT NULL,
  evidence_note TEXT NOT NULL,
  PRIMARY KEY (event_id, firm_id),
  CONSTRAINT firm_profile_allowed_values
    CHECK (firm_profile IN ('manufacturing_cost_linked', 'ip_licensing_dominated', 'services_and_software_weighted'))
);

CREATE INDEX IF NOT EXISTS idx_firm_profile_event
  ON firm_profile (event_id);

CREATE INDEX IF NOT EXISTS idx_firm_profile_profile
  ON firm_profile (firm_profile);

COMMIT;
