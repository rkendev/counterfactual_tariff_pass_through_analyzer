# Phase 5 Minimal Extension Plan
Firm Profile Gating for Pass Through Mapping

## Motivation
Event 0002 validation identified a systematic failure mode: firms with IP and licensing dominated economics can exhibit gross margin movements that are weakly coupled to manufacturing cost shocks. Treating these firms as predictable under the same mapping overstates model validity.

Phase 5 introduces a minimal structural boundary that makes the model explicit about where it applies.

## Objective
Condition the cost delta to margin sign mapping on a simple firm profile label so evaluation reports signal only in the regime where the mechanism is plausible.

## Minimal Extension
Add a firm profile flag with two values.

- manufacturing_cost_linked
- ip_licensing_dominated

Mapping behavior.
- manufacturing_cost_linked uses the current sign mapping unchanged
- ip_licensing_dominated returns 0 by default, meaning out of scope for directional prediction under this mechanism

## Scope
In scope
1 Add schema for firm profile labels
2 Add manual input CSV per event for firm profiles
3 Load firm profiles into the database alongside exposure and observed outcomes
4 Update mapping function to incorporate profile
5 Update evaluation to report metrics for
   overall set
   applicable set where predicted sign is non zero

Out of scope
- Any numeric estimation of pass through parameters
- Any scraping or automated filing NLP
- Any new datasets or infra
- Any changes to propagation mechanics

## Artifacts
New
- sql 34 firm_profile_schema sql
- data manual_inputs event_0002 firm_profiles csv
- src loader update to ingest firm profiles
- src mapping update to gate on profile
- docs phase_5_plan md

Modified
- src evaluate_event py to compute applicable metrics

## Acceptance Checklist
- Event 0002 includes a firm profile label for each candidate firm
- QCOM is labeled ip_licensing_dominated in event 0002
- Running the standard evaluation produces
  overall metrics unchanged in structure
  applicable set S metrics where ip_licensing_dominated firms and firms with observed margin change sign = 0 are excluded
- No new dependencies or services are introduced
- A single end to end run from a fresh database is documented and works

## Falsification and Interpretation
Phase 5 does not aim to increase accuracy by tuning. It aims to prevent false generalization by making model scope explicit. The primary success criterion is clarity and reproducibility of the boundary.

## Next Steps
1 Implement schema and loader for firm profiles
2 Add event 0002 firm profile file
3 Wire mapping gating and update evaluation readout
4 Run smoke test for event 0002 and compare to v0.4.0 behavior
5 Commit and tag v0.5.0 firm-profile-gating
