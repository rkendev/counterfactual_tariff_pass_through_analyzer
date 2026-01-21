# Event Selection Criteria

This document defines the minimum criteria required to introduce a real historical tariff event into the Counterfactual Tariff Pass Through Analyzer.

Its purpose is to prevent premature modeling, post hoc rationalization, and scope creep by forcing explicit data sufficiency checks before any new event is added.

No code changes are permitted for a new event until all criteria in this document are satisfied.

## Definition of a valid tariff event

A valid tariff event for this project must satisfy all of the following conditions.

1 The event represents a discrete policy action that changes tariff rates for identifiable HS codes.
2 The event has a clearly documented start date that can be used to define pre and post windows.
3 The event scope is narrow enough to be expressed as a finite set of HS codes.
4 The event is externally documented by an authoritative source.

Events that evolve gradually, lack a clear start date, or cannot be tied to specific HS codes are not valid for this project.

## Required HS scope data

For an event to be eligible, the following must be available.

1 A list of affected HS codes at a consistent digit level.
2 A documented tariff change magnitude or rule that can be mapped to an effective cost multiplier.
3 Public or reproducible documentation of the HS scope.

If HS scope cannot be expressed deterministically, the event is rejected.

## Required firm level exposure proxy

The project does not require exact firm import costs, but it does require a defensible exposure proxy.

Minimum requirements are:

1 Firm level mapping to HS codes affected by the event.
2 A nonzero exposure signal per firm such as import value, trade share, or input cost proxy.
3 Consistent firm identifiers across exposure and supplier graph data.

If firm exposure is inferred indirectly, the inference rule must be documented before execution.

If fewer than a meaningful fraction of firms in the supplier graph have exposure to the event HS codes, the event is rejected.

## Required supplier graph coverage

The supplier graph must satisfy the following.

1 A connected subgraph exists that includes both exposed firms and upstream suppliers.
2 Graph depth is sufficient to allow at least one non trivial propagation path.
3 The graph construction method is documented and reproducible.

Events where exposure firms are mostly isolated nodes do not provide meaningful propagation tests and are rejected.

## Required observed outcome proxy

Observed outcomes are required to evaluate directional alignment.

Minimum requirements are:

1 A firm level outcome proxy measured before and after the event.
2 A deterministic rule to map raw outcomes to margin_change_sign values.
3 A fixed pre and post window definition that is recorded in the event manifest.

Observed outcomes may be noisy, but the mapping rule must be defined before any model results are inspected.

If no defensible outcome proxy exists, the event is rejected.

## Minimum sample size

The evaluated set S must satisfy:

1 At least five firms with nonzero observed outcomes.
2 At least two firms with upstream propagation paths.

If this condition is not met, the event is rejected as uninformative.

## Rejection criteria summary

An event must be rejected if any of the following are true.

1 HS scope cannot be deterministically defined.
2 Firm exposure cannot be mapped to HS codes.
3 Supplier graph coverage is too sparse to allow propagation.
4 Observed outcomes cannot be mapped to directional signs.
5 Sample size is below the minimum threshold.

Rejection is a valid and expected outcome and must be documented.

## Enforcement rule

No scenario manifest for a real event may be created unless all criteria above are satisfied.

If an event fails these criteria, the correct action is to document the failure and select a different event.

This document may not be modified in response to a specific event.
