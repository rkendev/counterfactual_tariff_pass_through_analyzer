# Phase 2 Failure Note: event_0001

## What was tested
A fully wired counterfactual loop was executed end to end on a synthetic event manifest (event_0001) using HS_A multiplier shock mapping, recursive upstream propagation on the supplier graph, aggregation to per firm simulated_delta_usd, and a precommitted directional accuracy backtest against observed margin_change_sign.

## What happened
Directional accuracy on the evaluated set S was zero and did not outperform the trivial baseline. This is expected given the wiring test design: simulated deltas were strictly positive for all firms with nonzero observed outcomes, while observed margin_change_sign values were all negative. Under the current evaluation mapping, simulated_sign and observed_sign disagree for all firms in S.

## Why this does not invalidate the project
This run validates the engineering spine and the falsification harness, not the economics. The pipeline produced interpretable artifacts and enforced a precommitted evaluation rule without post hoc changes. The correct conclusion is that the current shock to outcome sign mapping is not a meaningful test of pass through in this synthetic setup.

## Most likely root cause
The synthetic observed outcome proxy does not encode a realistic or logically consistent mapping between higher simulated marginal costs and the observed margin sign. In real data, higher costs could reduce margins, increase prices, or be absorbed heterogeneously. Without a principled mapping, directional agreement is not informative.

## Phase 3 change proposal (precommitted)
Introduce an explicit mapping layer from simulated cost delta to an expected margin sign with a documented assumption, then rerun the exact same evaluation harness without changing metrics.

The Phase 3 change is limited to adding:
1 a deterministic transformation from simulated_delta_usd to predicted_margin_sign based on a fixed pass through assumption parameter alpha in [0,1]
2 a reference baseline that uses the same mapping without network propagation for comparison

No changes to propagation mechanics, depth caps, or evaluation rules are permitted in Phase 3 beyond the addition of this mapping layer.
