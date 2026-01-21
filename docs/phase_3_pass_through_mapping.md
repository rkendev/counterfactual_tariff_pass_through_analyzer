# Pass Through Mapping (Phase 3)

This document defines the deterministic mapping from simulated marginal cost delta to a predicted margin sign.

Purpose

The counterfactual engine produces cost deltas. The backtest compares predicted sign to observed margin sign. A mapping layer is required to avoid an implicit and inconsistent sign convention.

Mapping parameter

alpha in [0, 1] is a fixed pass through assumption.

alpha meaning

alpha is the fraction of incremental cost that is passed through to customers as higher prices within the event window.

Mapping rule

Given a cost delta c for a firm.

If c > 0 then the predicted margin sign is

-1 if alpha < 1
0 if alpha = 1

If c = 0 then predicted margin sign is 0.

If c < 0 then predicted margin sign is +1 if alpha < 1 else 0.

Interpretation

If costs rise and pass through is incomplete, margins are expected to fall. If pass through is complete, short run margin direction is indeterminate from cost alone, so the mapping outputs 0.

Phase 3 constraints

- alpha is fixed per run and must be recorded
- no tuning during the backtest
- propagation mechanics are unchanged
- evaluation metrics remain unchanged

Comparator baseline for Phase 3

A comparator baseline is computed using the same mapping but with direct delta only and no network propagation. This comparator is reported to quantify the incremental value of the network mechanism.

The primary pass fail rule remains the rule defined in backtest_definition.md.
