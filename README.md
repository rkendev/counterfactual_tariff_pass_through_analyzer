# Counterfactual Tariff Pass-Through Analyzer

A counterfactual modeling project that tests whether tariff cost shocks propagate through firm-level supplier networks in ways that explain observed margin changes better than direct exposure alone.

## Structural Hypothesis

> If tariff shocks propagate through firm-level supplier networks in a non-uniform, path-dependent manner, then a counterfactual model with explicit recursive landed-cost propagation will explain post-shock firm margin changes more reliably than headline tariff rates or linear pass-through assumptions.

## What This Project Does

The analyzer takes a real tariff event (e.g., US Section 301 tariffs on Chinese goods), maps which firms are exposed through HS code classifications, then propagates cost shocks recursively through a supplier graph using a PostgreSQL recursive CTE. Each firm receives a **direct delta** (from its own import exposure) and an **incoming delta** (from upstream supplier cost pass-through). The combined cost shock is mapped to a predicted gross margin direction, which is then compared against observed margin changes from public filings.

The project evaluates two real historical events:

| Event | Policy | Enforcement Date | Evaluated Firms | Accuracy |
|-------|--------|-----------------|----------------|----------|
| Section 301 List 1 | 25% tariff on $34B Chinese goods | 2018-07-06 | AAPL, CSCO, DELL | 3/3 correct |
| Section 301 List 2 | 25% tariff on $16B Chinese goods | 2018-08-23 | DELL, HPQ | 2/2 correct |

## Key Findings

**The propagation mechanism works.** After graph enrichment with documented supplier relationships, the network model produces meaningful incoming cost deltas. For example, Dell's total cost impact (36,667) is 3.7x its direct-only exposure (10,000) due to cost pass-through from Foxconn, Broadcom, and Intel.

**The sign-based metric cannot distinguish the models.** Because all cost shocks in these events are positive (tariffs increase costs), both the network model and the direct-only comparator predict the same margin direction (-1) for all manufacturing-linked firms. The network mechanism produces different magnitudes but identical signs.

**Profile gating improves evaluation quality.** Firms where cost-to-margin mapping is structurally implausible (IP-licensing-dominated, services-and-software-weighted) are excluded before evaluation, preventing false negatives from contaminating accuracy metrics.

**Sample sizes are below the pre-committed minimum.** Both events produce evaluated sets of 2-3 firms, below the 5-firm minimum specified in the event selection criteria. Results are directionally consistent but statistically thin.

## Architecture

```
PostgreSQL 16 (Docker) ─── recursive CTE propagation engine
Python 3.12 ──────────────── orchestration, evaluation, mapping
CSV artifacts ────────────── all inputs and outputs inspectable
```

No distributed compute, no feature stores, no dashboards. The entire system runs in a single Docker container plus a Python virtual environment.

## Project Structure

```
├── data/manual_inputs/          # Event-specific CSVs (exposure, margins, profiles)
│   ├── event_0002/
│   ├── event_0003/
│   └── supplier_enrichment.csv
├── docs/                        # Decision logs, postmortems, phase plans
├── outputs/                     # Evaluation artifacts per event
│   ├── event_0002/
│   └── event_0003/
├── scenarios/                   # Event manifest templates
├── sql/                         # Schema, seeds, propagation queries
└── src/                         # Python: loader, evaluator, mapping
```

## How to Run

```bash
# Start database
docker compose -f infra/db/docker-compose.yml up -d

# Initialize schema
docker exec -i ctp_postgres psql -U ctp -d ctp < sql/00_schema.sql
docker exec -i ctp_postgres psql -U ctp -d ctp < sql/30_event_inputs_schema.sql
docker exec -i ctp_postgres psql -U ctp -d ctp < sql/34_firm_profile_schema.sql

# Seed supplier graph
docker exec -i ctp_postgres psql -U ctp -d ctp < sql/01_seed_synthetic.sql
docker exec -i ctp_postgres psql -U ctp -d ctp < sql/40_seed_supplier_enrichment.sql

# Seed event data
docker exec -i ctp_postgres psql -U ctp -d ctp < sql/33_seed_synthetic_event_0002_exposure.sql
docker exec -i ctp_postgres psql -U ctp -d ctp < sql/31_seed_event_0002_firm_candidates.sql
docker exec -i ctp_postgres psql -U ctp -d ctp < sql/37_seed_synthetic_event_0003_exposure.sql
docker exec -i ctp_postgres psql -U ctp -d ctp < sql/36_seed_event_0003_firm_candidates.sql

# Build subgraph
docker exec -i ctp_postgres psql -U ctp -d ctp < sql/select_phase1_subgraph.sql

# Load manual inputs and run evaluation
source .venv/bin/activate
export DATABASE_URL="postgresql://ctp:ctp@localhost:5432/ctp"

export EVENT_ID="event_0002"
python3 src/load_manual_inputs.py
docker exec -i ctp_postgres psql -U ctp -d ctp < sql/22_simulated_components_event_0002.sql > outputs/event_0002/simulated_components.csv
python3 src/evaluate_event.py

export EVENT_ID="event_0003"
python3 src/load_manual_inputs.py
docker exec -i ctp_postgres psql -U ctp -d ctp < sql/23_simulated_components_event_0003.sql > outputs/event_0003/simulated_components.csv
python3 src/evaluate_event.py
```

## Evaluation Framework

The project uses a pre-committed falsification framework:

- **Primary metric:** directional accuracy (predicted margin sign vs. observed margin sign)
- **Reference baseline:** naive +1 prediction for all firms
- **Comparator:** direct-only exposure model (no network propagation)
- **Pass condition:** accuracy > baseline accuracy
- **Minimum sample:** ≥5 firms with nonzero outcomes (not met in current events)
- **Profile gating:** firms where cost-to-margin mapping is structurally implausible are excluded before evaluation

The hypothesis would be rejected if the network model showed no directional alignment with observed margin changes, or if network propagation provided no advantage over the reference baseline.

## Limitations

1. **Sign metric saturation:** unidirectional cost shocks produce identical signs for both models. Magnitude-sensitive metrics (rank correlation) would better differentiate.
2. **Synthetic exposure values:** HS_A import values are synthetic, not estimated from real trade data.
3. **Small sample sizes:** 2-3 evaluated firms per event, below the 5-firm pre-committed minimum.
4. **Single tariff type:** only Section 301 tariffs tested. No cross-policy validation.
5. **Binary exposure proxy:** exposed/not-exposed classification limits heterogeneous effect detection.

## Development History

| Phase | Branch | What Happened |
|-------|--------|--------------|
| 1 | phase1-slice1-scaffold | Synthetic subgraph, propagation engine, baseline/shock diff |
| 3 | phase3-mapping-layer | Cost delta to margin sign mapping with pass-through parameter |
| 4 | phase4-event_0002-execution | First real event backtest (Section 301 List 1) |
| 5 | phase5-minimal-extension | Firm profile gating for QCOM |
| 6 | phase6-event_0003-validation | Second real event, CSCO profile refinement, cross-event comparison |
| 7 | phase7-graph-enrichment | Supplier graph enrichment, propagation direction correction |

## What This Project Demonstrates

This is a portfolio project built to demonstrate applied data science judgment, not production deployment. It shows:

- **Structural thinking:** mechanism-based hypothesis with explicit counterfactual design
- **Falsification discipline:** pre-committed evaluation rules, minimum sample sizes, pass/fail criteria defined before execution
- **Honest reporting:** negative results documented (sign metric saturation, small samples), failures investigated (QCOM postmortem), limitations stated upfront
- **Architecture restraint:** no infrastructure beyond what the problem requires
- **Iterative refinement:** each phase builds on the previous one with documented decision rationale
