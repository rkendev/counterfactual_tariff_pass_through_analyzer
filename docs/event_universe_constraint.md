# Event Universe Constraint

This document constrains the universe of admissible tariff events for this project.

Its purpose is to reduce the event search space so that candidate evaluation is feasible and deterministic.

This constraint is binding for all future event selection.

## Geographic scope

The project will consider tariff events initiated by the United States federal government.

Rationale:

- US tariff actions are well documented
- HS code mappings are publicly available
- Firm exposure proxies are more feasible for US listed firms
- Supplier network data is more likely to exist or be approximated

Non US initiated tariff events are excluded.

## Temporal scope

The project will consider tariff events occurring between 2016 and 2020 inclusive.

Rationale:

- Major discrete tariff actions occurred in this period
- Financial statement data is available
- Supplier network structures are more stable than in earlier decades
- Avoids pandemic induced confounding effects after 2020

Events outside this window are excluded.

## Tariff type scope

The project will consider tariff events that meet all of the following:

- Discrete announcement or enforcement date
- Explicit HS code lists
- Non zero tariff rate change

Gradual policy shifts or quota based measures are excluded.

## Firm universe constraint

The firm universe is constrained to publicly listed firms with available financial statements.

Private firms may appear in the supplier graph but cannot be used for observed outcome evaluation.

## Outcome proxy commitment

The observed outcome proxy is committed as:

Public company gross margin change

Alternative proxies are excluded for this project iteration.

## Enforcement rule

No event candidate may be proposed unless it satisfies all constraints above.

This document may not be modified once an admissible event candidate has been selected.
