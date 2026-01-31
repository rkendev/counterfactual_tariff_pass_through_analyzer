# Phase 6 Corrections and Path Forward

**Branch:** `phase6-event_0003-validation`  
**Date:** January 31, 2026

---

## Summary of Required Changes

Three issues must be resolved before event_0003 evaluation can run correctly:

| # | File | Issue | Severity |
|---|------|-------|----------|
| 1 | `23_simulated_components_event_0003.sql` | Copy-paste bug: queries `event_0002` instead of `event_0003` | **Blocking** |
| 2 | `34_firm_profile_schema.sql` + live DB | CHECK constraint only allows two profile values; `services_and_software_weighted` will be rejected on INSERT | **Blocking** |
| 3 | `mapping.py` | Only gates `ip_licensing_dominated`; `services_and_software_weighted` passes through ungated | **Logic error** |
| 4 | `evaluate_event.py` | Two hardcoded checks for `ip_licensing_dominated` ignore the new profile | **Logic error** |

---

## Correction 1: Fix `23_simulated_components_event_0003.sql`

This file was copied from `22_simulated_components_event_0002.sql` and the event reference was never updated.

### Change A — Comment block (line 2)

**Old:**
```
Simulated components for event_0002
```

**New:**
```
Simulated components for event_0003
```

### Change B — CTE filter (line 22)

**Old:**
```sql
    WHERE event_id = 'event_0002'
```

**New:**
```sql
    WHERE event_id = 'event_0003'
```

No other changes in this file.

---

## Correction 2: Update firm profile schema

### 2a — Update the SQL definition file `34_firm_profile_schema.sql`

**Old:**
```sql
  CONSTRAINT firm_profile_allowed_values
    CHECK (firm_profile IN ('manufacturing_cost_linked', 'ip_licensing_dominated'))
```

**New:**
```sql
  CONSTRAINT firm_profile_allowed_values
    CHECK (firm_profile IN ('manufacturing_cost_linked', 'ip_licensing_dominated', 'services_and_software_weighted'))
```

### 2b — Migrate the live database

Run this against the running PostgreSQL instance:

```bash
docker exec -i ctp_postgres psql -U ctp -d ctp -c "
ALTER TABLE firm_profile DROP CONSTRAINT firm_profile_allowed_values;
ALTER TABLE firm_profile ADD CONSTRAINT firm_profile_allowed_values
  CHECK (firm_profile IN ('manufacturing_cost_linked', 'ip_licensing_dominated', 'services_and_software_weighted'));
"
```

**Expected output:**
```
ALTER TABLE
ALTER TABLE
```

---

## Correction 3: Update `mapping.py`

The mapping function must gate `services_and_software_weighted` the same way it gates `ip_licensing_dominated`. Both represent firms where cost-delta-to-margin-sign mapping is structurally implausible.

### Full corrected file:

```python
from __future__ import annotations


_OUT_OF_SCOPE_PROFILES = frozenset({
    "ip_licensing_dominated",
    "services_and_software_weighted",
})


def sign_from_cost_delta(cost_delta_usd: float, alpha: float) -> int:
    if alpha < 0.0 or alpha > 1.0:
        raise ValueError("alpha must be in [0, 1]")

    effective = cost_delta_usd * (1.0 - alpha)

    if effective == 0.0:
        return 0

    if effective > 0.0:
        return -1

    return 1


def predicted_margin_sign(cost_delta_usd: float, alpha: float, firm_profile: str | None) -> int:
    """
    Phase 5+ mapping gate

    If firm_profile is in _OUT_OF_SCOPE_PROFILES, this model does not claim
    that cost deltas map to gross margin sign. Return 0 and let evaluation
    exclude it from the falsification set S.

    Otherwise use the existing sign_from_cost_delta logic unchanged.
    """
    if firm_profile in _OUT_OF_SCOPE_PROFILES:
        return 0

    return sign_from_cost_delta(cost_delta_usd, alpha)
```

### What changed and why:

- Added `_OUT_OF_SCOPE_PROFILES` frozenset containing both `ip_licensing_dominated` and `services_and_software_weighted`
- Replaced `if firm_profile == "ip_licensing_dominated"` with `if firm_profile in _OUT_OF_SCOPE_PROFILES`
- Updated docstring from "Phase 5" to "Phase 5+"
- `sign_from_cost_delta` is unchanged
- Adding future out-of-scope profiles now requires only adding to the set, not touching logic

---

## Correction 4: Update `evaluate_event.py`

Two locations reference `ip_licensing_dominated` by string and must be updated to use the same set-based check.

### Change A — `in_scope_row` inner function (inside `compute_metrics`)

**Old (lines 116-122):**
```python
    def in_scope_row(r: tuple[str, float, float, int, int, int, str | None]) -> bool:
        _, sim_d, _, _, _, obs_s, profile = r
        if obs_s not in (-1, 1):
            return False
        if profile == "ip_licensing_dominated":
            return False
        return True
```

**New:**
```python
    def in_scope_row(r: tuple[str, float, float, int, int, int, str | None]) -> bool:
        _, sim_d, _, _, _, obs_s, profile = r
        if obs_s not in (-1, 1):
            return False
        if profile in _OUT_OF_SCOPE_PROFILES:
            return False
        return True
```

### Change B — `in_scope` calculation in `main()` 

**Old (line 195):**
```python
            in_scope = int((obs_s in (-1, 1)) and (profile != "ip_licensing_dominated"))
```

**New:**
```python
            in_scope = int((obs_s in (-1, 1)) and (profile not in _OUT_OF_SCOPE_PROFILES))
```

### Change C — Add import at top of file

Add after the existing import from mapping (line 8):

**Old:**
```python
from mapping import predicted_margin_sign
```

**New:**
```python
from mapping import predicted_margin_sign, _OUT_OF_SCOPE_PROFILES
```

---

## Correction 5: Confirm `firm_profiles.csv` for event_0003

The file at `data/manual_inputs/event_0003/firm_profiles.csv` should contain:

```
event_id,firm_id,firm_profile,evidence_note
event_0003,AAPL,manufacturing_cost_linked,hardware manufacturing and global supply chain exposure
event_0003,CSCO,services_and_software_weighted,increasing services and software mix reduces direct tariff pass-through
event_0003,DELL,manufacturing_cost_linked,pc manufacturing and hardware sourcing exposure
event_0003,HPQ,manufacturing_cost_linked,pc and printing hardware manufacturing exposure
```

If your existing file already matches this, no change needed. If not, replace it.

---

## Execution Sequence

Run all steps from the project root directory.

### Step 1: Apply all file edits

Apply corrections 1 through 4 to the source files using your editor.

### Step 2: Migrate live database schema

```bash
docker exec -i ctp_postgres psql -U ctp -d ctp -c "
ALTER TABLE firm_profile DROP CONSTRAINT firm_profile_allowed_values;
ALTER TABLE firm_profile ADD CONSTRAINT firm_profile_allowed_values
  CHECK (firm_profile IN ('manufacturing_cost_linked', 'ip_licensing_dominated', 'services_and_software_weighted'));
"
```

### Step 3: Load event_0003 manual inputs

```bash
source .venv/bin/activate
export DATABASE_URL="postgresql://ctp:ctp@localhost:5432/ctp"
export EVENT_ID="event_0003"

python3 src/load_manual_inputs.py
```

**Expected output:**
```
Loaded exposure labels. Firm profiles loaded. Observed outcomes loaded.
```

### Step 4: Verify firm profiles in database

```bash
docker exec -i ctp_postgres psql -U ctp -d ctp -c \
"SELECT firm_id, firm_profile
 FROM firm_profile
 WHERE event_id='event_0003'
 ORDER BY firm_id;"
```

**Expected output:**
```
 firm_id | firm_profile
---------+----------------------------------
 AAPL    | manufacturing_cost_linked
 CSCO    | services_and_software_weighted
 DELL    | manufacturing_cost_linked
 HPQ     | manufacturing_cost_linked
(4 rows)
```

### Step 5: Generate simulated components (if not already present)

Check if `outputs/event_0003/simulated_components.csv` exists. If not, run:

```bash
docker exec -i ctp_postgres psql -U ctp -d ctp \
  -f sql/23_simulated_components_event_0003.sql \
  > outputs/event_0003/simulated_components.csv
```

(Adjust the path to the SQL file based on your project structure.)

### Step 6: Run evaluation

```bash
export EVENT_ID="event_0003"
python3 src/evaluate_event.py
```

### Step 7: Inspect results

```bash
cat outputs/event_0003/falsification_readout.txt
echo "---"
head -n 20 outputs/event_0003/backtest_results.csv
```

**What to look for:**
- `sample_size_S` should be reduced by 1 (CSCO excluded)
- CSCO should show `in_scope_S = 0` in backtest_results.csv
- `accuracy` should be stable or improved
- `comparator_accuracy_direct_only` should no longer dominate

### Step 8: Git commit (only after verification)

```bash
git add -A
git status
```

Review what's staged, then:

```bash
git commit -m "Phase 6: fix event_0003 SQL reference, extend firm profile schema for services_and_software_weighted, update mapping and evaluation gating"
git push
```

---

## What Comes Next After Step 8

1. **Draft `docs/event_0003_post_profile_readout.md`** — document what changed, why, and what the results show
2. **Compare event_0002 vs event_0003** — are both events showing the same pattern (network model outperforms direct-only after profile gating)?
3. **Decide Phase 6 completion** — if both events show consistent behavior, Phase 6 is done
4. **If complete** — begin portfolio packaging (multi-event summary, final report, README)
