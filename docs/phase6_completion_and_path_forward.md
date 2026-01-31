# Phase 6 Completion and Path Forward Decision

---

## Status

Phase 6 is complete. Both real events pass the falsification test. Profile gating works correctly. The evaluation framework is sound.

However, the core differentiating claim of the project — that network propagation outperforms direct-only exposure — remains untested due to a supplier graph that does not connect the real firms.

---

## The Decision

You have two defensible paths forward. Both maintain project discipline. Neither involves scope creep.

---

### Path A: Package As-Is (Negative Network Result)

**What you deliver:**
A portfolio project that demonstrates counterfactual economic modeling, falsification discipline, and honest reporting. The narrative is: "I built the mechanism, tested it rigorously, and found that the available supplier graph is too sparse to activate network propagation. The sign mapping works, but the network claim is unvalidated."

**Effort:** Low. Write the final report, clean up the README, commit and tag.

**Portfolio signal:** Strong on methodology, honesty, and engineering discipline. Weaker on demonstrating the actual network mechanism working.

**When to choose this:** If you want to move on to your next project, or if graph enrichment would require data sources outside your constraints.

---

### Path B: Targeted Graph Enrichment (Test the Mechanism)

**What you do:**
Add a small number of supplier edges connecting the real firms so that propagation can activate. This does not mean inventing data — it means encoding known public supply chain relationships.

For example, it is publicly documented that:
- Foxconn (as a supplier entity) supplies AAPL, DELL, and HPQ
- Broadcom supplies AAPL and DELL for components
- Intel supplies DELL and HPQ

Adding even 3-5 such edges with synthetic but directionally plausible HS exposure would allow the propagation engine to produce nonzero `incoming_delta_usd` values, and the cross-event comparison would become meaningful.

**Scope guard:** This is permitted under your existing data boundaries if supplier relationships come from "prior leads" (Step 1, section 1.3). It does not require web scraping or new proprietary datasets. It requires a documented justification for each edge added.

**Effort:** Medium. Define edges, seed them, rerun both events, compare network vs direct-only, write the final report.

**Portfolio signal:** Strongest possible. Demonstrates the full mechanism end-to-end, with honest reporting of where it helps and where it doesn't.

**When to choose this:** If you want the project to demonstrate its core claim, and you can document the supplier relationships from public knowledge.

---

### What I recommend

Path B, done minimally. The project has earned the right to test its core hypothesis. You built the entire evaluation harness correctly. Not testing the one thing it was designed to test would be like building a telescope and never pointing it at the sky.

The key constraint: every edge you add must be documented with an evidence note, just like the firm profiles. No silent enrichment.

---

## If You Choose Path B: Minimal Execution Plan

1. Create `data/manual_inputs/supplier_enrichment.csv` with columns: `buyer_firm_id, supplier_firm_id, evidence_note`
2. Add 3-5 edges based on publicly known supply chain relationships
3. Load into `supplier_edges` table
4. Rebuild `phase1_firms` and `phase1_edges` to include the new firms
5. Rerun simulated components for event_0002 and event_0003
6. Rerun evaluation for both events
7. Compare: does `incoming_delta_usd > 0` for any firm? Does accuracy diverge from comparator?
8. Document results in the final report regardless of outcome
9. Commit, tag `v0.6.0-graph-enrichment`, write README, package

---

## If You Choose Path A: Packaging Steps

1. Write `docs/final_report.md` documenting all findings honestly
2. Create `outputs/multi_event_summary.csv` 
3. Clean up README with project description, results, and limitations
4. Commit, tag `v0.6.0-final`, push
