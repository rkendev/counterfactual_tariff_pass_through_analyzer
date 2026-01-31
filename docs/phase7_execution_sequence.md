# Phase 7 Execution Sequence

## Prerequisites
- On branch `phase7-graph-enrichment`
- PostgreSQL container running
- Virtual environment activated
- DATABASE_URL exported

## Step 1: Place files

Copy the following files into your project:

```
docs/phase7_graph_enrichment.md
data/manual_inputs/supplier_enrichment.csv
sql/40_seed_supplier_enrichment.sql
sql/22_simulated_components_event_0002.sql   (replace existing)
sql/23_simulated_components_event_0003.sql   (replace existing)
```

## Step 2: Seed supplier enrichment into database

```bash
docker exec -i ctp_postgres psql -U ctp -d ctp < sql/40_seed_supplier_enrichment.sql
```

Expected: `BEGIN` / `INSERT` / `INSERT` / `COMMIT`

## Step 3: Verify supplier data

```bash
docker exec -i ctp_postgres psql -U ctp -d ctp -c \
"SELECT firm_id, hs_code, import_value_usd FROM firm_hs_exposure WHERE firm_id IN ('FXCN','AVGO','INTC') ORDER BY firm_id;"

docker exec -i ctp_postgres psql -U ctp -d ctp -c \
"SELECT * FROM supplier_edges WHERE supplier_firm_id IN ('FXCN','AVGO','INTC') ORDER BY buyer_firm_id, supplier_firm_id;"
```

Expected: 3 exposure rows, 9 edge rows.

## Step 4: Generate simulated components for event_0002

```bash
mkdir -p outputs/event_0002
docker exec -i ctp_postgres psql -U ctp -d ctp -f sql/22_simulated_components_event_0002.sql > outputs/event_0002/simulated_components.csv
```

Wait — the `COPY ... TO STDOUT` syntax means the output goes to stdout. But when using `-f`, psql sends stdout to the terminal. So pipe it:

```bash
docker exec -i ctp_postgres psql -U ctp -d ctp < sql/22_simulated_components_event_0002.sql > outputs/event_0002/simulated_components.csv
```

Then verify:

```bash
cat outputs/event_0002/simulated_components.csv
```

Expected: AAPL, CSCO, DELL, HPQ, QCOM all present. AAPL/CSCO/DELL/HPQ should have `incoming_delta_usd > 0`. QCOM should have `incoming_delta_usd = 0`.

## Step 5: Generate simulated components for event_0003

```bash
mkdir -p outputs/event_0003
docker exec -i ctp_postgres psql -U ctp -d ctp < sql/23_simulated_components_event_0003.sql > outputs/event_0003/simulated_components.csv
```

Verify:

```bash
cat outputs/event_0003/simulated_components.csv
```

Expected: AAPL, CSCO, DELL, HPQ all present. AAPL/CSCO/DELL/HPQ should have `incoming_delta_usd > 0`.

## Step 6: Run evaluation for event_0002

```bash
export EVENT_ID="event_0002"
python3 src/evaluate_event.py
cat outputs/event_0002/falsification_readout.txt
echo "---"
cat outputs/event_0002/backtest_results.csv
```

## Step 7: Run evaluation for event_0003

```bash
export EVENT_ID="event_0003"
python3 src/evaluate_event.py
cat outputs/event_0003/falsification_readout.txt
echo "---"
cat outputs/event_0003/backtest_results.csv
```

## Step 8: Compare with Phase 6 results

Key things to check:
- `incoming_delta_usd > 0` for firms with supplier edges (AAPL, CSCO, DELL, HPQ)
- `simulated_delta_usd > direct_delta_usd` for those firms
- Accuracy and comparator accuracy values
- Pass/fail status unchanged

## Step 9: Git commit (after verification)

```bash
git add -A
git commit -m "Phase 7: graph enrichment with 3 supplier firms, 9 edges, corrected downstream propagation direction"
git push -u origin phase7-graph-enrichment
```
