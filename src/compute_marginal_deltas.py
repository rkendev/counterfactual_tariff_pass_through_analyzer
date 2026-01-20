from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


TRACE_PATH = Path("outputs/propagation_trace.csv")
OUT_PATH = Path("outputs/marginal_cost_deltas.csv")


def main() -> None:
    if not TRACE_PATH.exists():
        raise FileNotFoundError(f"Missing required input: {TRACE_PATH}")

    incoming: dict[str, float] = defaultdict(float)
    direct: dict[str, float] = defaultdict(float)

    with TRACE_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"path_root_firm_id", "from_firm_id", "to_supplier_id", "depth", "propagated_delta_usd"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Trace missing columns: {sorted(missing)}")

        for row in reader:
            root = (row["path_root_firm_id"] or "").strip()
            to_supplier = (row["to_supplier_id"] or "").strip()
            depth = int((row["depth"] or "0").strip())
            delta = float((row["propagated_delta_usd"] or "0").strip())

            # depth 0 rows represent the root firm's direct delta
            if depth == 0:
                direct[root] += delta
                continue

            # for hop rows, attribute delta to the receiving supplier node
            if to_supplier:
                incoming[to_supplier] += delta

    all_firms = sorted(set(direct) | set(incoming))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["firm_id", "direct_delta_usd", "incoming_delta_usd", "total_delta_usd"])
        for firm_id in all_firms:
            d = round(direct.get(firm_id, 0.0), 6)
            inc = round(incoming.get(firm_id, 0.0), 6)
            total = round(d + inc, 6)
            writer.writerow([firm_id, f"{d:.6f}", f"{inc:.6f}", f"{total:.6f}"])


if __name__ == "__main__":
    main()
