# Backtest Definition (Phase 2)

This document defines the first falsification backtest for the Counterfactual Tariff Pass Through Analyzer.

The purpose is to test whether simulated counterfactual marginal cost deltas produced by explicit supplier network propagation align directionally with observed firm outcomes for a single historical tariff event.

This definition is written before results are produced and must not be modified in response to outcomes.

## Hypothesis anchor

Structural hypothesis:

If tariff shocks propagate through firm level supplier networks in a non uniform and path dependent manner, then a counterfactual model that explicitly simulates recursive landed cost propagation across those networks will explain observed post shock firm margin changes more reliably than headline tariff rates or linear pass through assumptions.

Falsification condition:

The hypothesis is falsified for the tested event if simulated marginal cost deltas show no directional alignment with realized margin changes and do not outperform a trivial reference baseline under the rules below.

## Backtest scope and constraints

Scope:

One historical tariff event, one scenario, one run.

Constraints:

- No new infrastructure
- PostgreSQL for relational and recursive queries
- Python for scenario logic and artifact production
- Single local execution producing CSV artifacts
- No parameter tuning during the backtest

## Inputs required

### 1 Event definition

An event is defined by:

- event_id
- event_start_date and event_end_date
- HS scope: the affected HS codes for this event
- shock magnitude rule: how tariff change is mapped to an effective cost multiplier

The event definition is stored as a scenario manifest in `scenarios/<event_id>_shock.json`.

### 2 Firm exposure and supplier graph

Required tables:

- firm_hs_exposure: firm_id, hs_code, import_value_usd
- supplier_edges: buyer_firm_id, supplier_firm_id

Both must be restricted to the firms that participate in the backtest sample and must be documented.

### 3 Observed outcome proxy

Observed outcome is defined as a directional proxy for pass through impact.

Minimum requirement:

A table mapping firm_id to an observed margin change over the event window.

Required columns:

- firm_id
- margin_change_sign in {-1, 0, +1}

Where margin_change_sign is computed from a precommitted rule.

If raw margins are available, the sign is computed as:

margin_change_sign = sign( post_event_margin - pre_event_margin )

Windowing rule:

- pre_event_window: the N periods immediately before event_start_date
- post_event_window: the N periods immediately after event_start_date

N must be fixed per event and recorded in the event manifest.

If only a single pre and post observation exists, the sign is computed from that pair.

## Model outputs used for evaluation

Model output for each firm:

- simulated_delta_usd: total marginal cost delta produced by the counterfactual propagation run

Simulated sign:

simulated_sign = sign(simulated_delta_usd)

Zero handling:

- If simulated_delta_usd == 0 then simulated_sign = 0
- If observed margin_change_sign == 0 then the firm is excluded from directional accuracy metrics but still reported

## Primary evaluation metric

Directional agreement on non zero observed outcomes.

Let S be the set of firms with observed margin_change_sign in {-1, +1}.

Directional accuracy:

accuracy = mean( simulated_sign == observed_margin_change_sign ) over S

This is the primary pass fail readout for the backtest.

## Reference baseline

A trivial baseline is used for falsification discipline.

Baseline definition:

- baseline_sign = +1 for all firms in S

This baseline encodes the naive assumption that tariff shocks increase costs and therefore push margins downward uniformly.

Baseline accuracy is computed identically:

baseline_accuracy = mean( baseline_sign == observed_margin_change_sign ) over S

The model is not considered useful for this event if:

accuracy <= baseline_accuracy

This is not a global rejection criterion, but it is sufficient to fail the Phase 2 slice for this event.

## Secondary diagnostics (non gating)

These do not determine pass fail but are recorded:

- Coverage: fraction of S with simulated_delta_usd != 0
- Rank correlation: Spearman correlation between simulated_delta_usd and absolute margin change magnitude, if magnitude is available
- Tier sensitivity: whether firms with greater upstream depth show different alignment

## Outputs required

The run must produce:

1 `outputs/<event_id>/backtest_results.csv`

Required columns:

- firm_id
- simulated_delta_usd
- simulated_sign
- observed_margin_change_sign
- match_flag

2 `outputs/<event_id>/falsification_readout.txt`

Must contain:

- event_id
- sample size |S|
- accuracy
- baseline_accuracy
- coverage
- pass fail statement based on the rule accuracy > baseline_accuracy

## No tuning rule

During Phase 2:

- No changes to propagation mechanics
- No changes to shock mapping
- No changes to evaluation windows
- No changes to inclusion criteria

If the backtest fails, the correct action is to document the failure and decide whether to stop or to proceed to Phase 3 multi event testing with a precommitted change proposal.

## Observed outcome mapping for real events

Observed outcome proxy is gross margin.

gross_margin is (revenue minus cost_of_goods_sold) divided by revenue.

Pre window is the quarter immediately before the enforcement date.
Post window is the quarter immediately after the enforcement date.

margin_change is gross_margin_post minus gross_margin_pre.

margin_change_sign is:
-1 if margin_change < 0
0 if margin_change = 0
+1 if margin_change > 0

No thresholds, smoothing, or discretionary adjustments are permitted.

