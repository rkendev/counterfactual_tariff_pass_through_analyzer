# Phase 7: Graph Enrichment and Propagation Correction

## Motivation

After Phase 6, both real events pass the falsification test but reveal a structural limitation: `incoming_delta_usd = 0` for every firm in every event. The network propagation mechanism has never activated because the real firms have no supplier edges connecting them to other firms in the graph.

Additionally, code review during the Phase 6 handoff revealed that the propagation direction in the simulation SQL is inverted relative to the hypothesis. The walk follows buyer to supplier edges (upstream), but the structural hypothesis describes recursive landed cost propagation, which flows downstream from supplier to buyer.

Phase 7 addresses both issues with minimal, documented changes.

## Objectives

1. Add a small set of publicly documented supplier firms and edges to the graph.
2. Correct the propagation direction for real events so cost shocks flow downstream from suppliers to their buyers.
3. Rerun evaluation for events 0002 and 0003 and compare results.

## Propagation Direction Correction

### Current behavior

The walk in `22_simulated_components_event_0002.sql` and `23_simulated_components_event_0003.sql` joins on `buyer_firm_id = current_node` and moves to `supplier_firm_id`. This propagates cost upstream.

### Corrected behavior

The walk joins on `supplier_firm_id = current_node` and moves to `buyer_firm_id`. This propagates cost downstream, matching the hypothesis that a supplier's landed cost increase is passed through to its buyers.

### Scope of change

Only the real event SQL files (22, 23) are modified. The synthetic wiring test (event_0001, files 20, 21) uses `phase1_edges` with its own graph and is not changed.

### Justification

This is a bug fix, not a post hoc tuning. The direction error was not observable in Phase 1 or Phase 2 because the synthetic graph is small and fully connected, making propagation symmetric. The error only becomes visible when real firms are added to the graph with asymmetric buyer-supplier relationships.

## Supplier Enrichment

### Firms added

| Firm ID | Represents | Rationale |
|---------|-----------|-----------|
| FXCN | Foxconn / Hon Hai Precision | Largest electronics contract manufacturer globally. Publicly documented manufacturing partner for Apple, Dell, HP, and Cisco hardware products. |
| AVGO | Broadcom Inc. | Major semiconductor supplier. Publicly documented supplier of wireless, networking, and storage chips to Apple, Dell, and HP. |
| INTC | Intel Corporation | Dominant processor supplier. Publicly documented supplier of CPUs to Dell and HP for PC and server product lines. |

### Edges added

| Buyer | Supplier | Evidence |
|-------|----------|----------|
| AAPL | FXCN | Foxconn manufactures iPhone, iPad, and Mac products for Apple |
| AAPL | AVGO | Broadcom supplies wireless and networking chips to Apple |
| CSCO | FXCN | Foxconn manufactures router and switch hardware for Cisco |
| DELL | FXCN | Foxconn manufactures server and PC hardware for Dell |
| DELL | AVGO | Broadcom supplies networking and storage controller chips to Dell |
| DELL | INTC | Intel supplies processors for Dell PCs and servers |
| HPQ | FXCN | Foxconn manufactures PC and printer hardware for HP |
| HPQ | AVGO | Broadcom supplies networking chips to HP |
| HPQ | INTC | Intel supplies processors for HP PCs and servers |

All relationships are based on publicly available information from company filings, earnings calls, and supply chain disclosures during 2017-2018.

### Exposure values

Supplier firms receive synthetic HS_A exposure values scaled to reflect their relative import intensity as contract manufacturers and component suppliers.

| Firm | HS_A import_value_usd | Rationale |
|------|----------------------|-----------|
| FXCN | 200000 | Highest: contract manufacturing requires massive Chinese component imports |
| AVGO | 80000 | Medium: semiconductor design firm with significant Chinese packaging and test operations |
| INTC | 60000 | Medium: processor manufacturing with Chinese supply chain exposure |

These are synthetic values consistent with the existing framework. They are not estimated from real data.

## Expected Outcome

With the corrected propagation direction, supplier firms' cost deltas will flow downstream to their buyers. The real event firms (AAPL, DELL, HPQ, CSCO) will receive nonzero `incoming_delta_usd` for the first time.

### Known limitation

All direct deltas and incoming deltas are positive (cost increases). At alpha = 0, the predicted margin sign for all manufacturing-cost-linked firms is -1 regardless of magnitude. Therefore, the sign-based evaluation metric cannot distinguish between the network model and the direct-only model for these events.

This is a structural property of unidirectional cost shocks evaluated with sign-based metrics, not a model failure. The network mechanism produces meaningfully different magnitudes that would be captured by magnitude-sensitive metrics such as rank correlation, which the backtest definition lists as a secondary diagnostic.

## Scope Guard

### In scope
- Add 3 supplier firms with documented evidence
- Add 9 buyer-supplier edges with documented evidence
- Add synthetic HS_A exposure for 3 supplier firms
- Correct propagation direction in event SQL for real events
- Rerun evaluation for events 0002 and 0003
- Document results

### Out of scope
- Adding new evaluated firms to the event sets
- Changing evaluation metrics
- Changing alpha or other parameters
- Adding observed gross margins for supplier firms
- Any changes to event_0001 or Phase 1 synthetic tests
