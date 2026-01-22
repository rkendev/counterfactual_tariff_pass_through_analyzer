from __future__ import annotations

import os
import csv
from dataclasses import dataclass
from pathlib import Path

from mapping import sign_from_cost_delta


@dataclass(frozen=True)
class Metrics:
    n_in_scope: int
    accuracy: float
    baseline_accuracy: float
    comparator_accuracy: float
    coverage: float
    passed: bool


def load_components(path: Path) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    with path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        required = {"firm_id", "direct_delta_usd", "incoming_delta_usd", "simulated_delta_usd"}
        missing = required - set(r.fieldnames or [])
        if missing:
            raise ValueError(f"Components CSV missing columns: {sorted(missing)}")

        for row in r:
            firm = (row["firm_id"] or "").strip()
            out[firm] = {
                "direct": float((row["direct_delta_usd"] or "0").strip()),
                "incoming": float((row["incoming_delta_usd"] or "0").strip()),
                "simulated": float((row["simulated_delta_usd"] or "0").strip()),
            }
    return out


def load_observed(path: Path) -> dict[str, int]:
    out: dict[str, int] = {}
    with path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        required = {"firm_id", "margin_change_sign"}
        missing = required - set(r.fieldnames or [])
        if missing:
            raise ValueError(f"Observed CSV missing columns: {sorted(missing)}")

        for row in r:
            firm = (row["firm_id"] or "").strip()
            s = int((row["margin_change_sign"] or "0").strip())
            out[firm] = s
    return out


def compute_metrics(
    components: dict[str, dict[str, float]],
    observed: dict[str, int],
    alpha: float,
) -> Metrics:
    rows = []
    for firm, obs_sign in observed.items():
        if obs_sign not in (-1, 0, 1):
            continue

        c = components.get(firm, {"direct": 0.0, "incoming": 0.0, "simulated": 0.0})

        simulated_delta = c["simulated"]
        direct_delta = c["direct"]

        predicted_sign = sign_from_cost_delta(simulated_delta, alpha)
        comparator_sign = sign_from_cost_delta(direct_delta, alpha)

        rows.append((firm, simulated_delta, direct_delta, predicted_sign, comparator_sign, obs_sign))

    in_scope = [r for r in rows if r[5] in (-1, 1)]
    n = len(in_scope)
    if n == 0:
        return Metrics(0, 0.0, 0.0, 0.0, 0.0, False)

    matches = sum(1 for (_, _, _, pred_s, _, obs_s) in in_scope if pred_s == obs_s)
    accuracy = matches / n

    baseline_sign = 1
    baseline_matches = sum(1 for (_, _, _, _, _, obs_s) in in_scope if baseline_sign == obs_s)
    baseline_accuracy = baseline_matches / n

    comparator_matches = sum(1 for (_, _, _, _, comp_s, obs_s) in in_scope if comp_s == obs_s)
    comparator_accuracy = comparator_matches / n

    covered = sum(1 for (_, sim_d, _, _, _, _) in in_scope if sim_d != 0.0)
    coverage = covered / n

    passed = accuracy > baseline_accuracy
    return Metrics(n, accuracy, baseline_accuracy, comparator_accuracy, coverage, passed)


def main() -> None:
    event_id = os.getenv("EVENT_ID", "event_0001")
    alpha = 0.0

    out_dir = Path("outputs") / event_id
    out_dir.mkdir(parents=True, exist_ok=True)

    components_path = out_dir / "simulated_components.csv"
    observed_path = out_dir / "observed_margin_sign.csv"

    if not components_path.exists():
        raise FileNotFoundError(f"Missing {components_path}")

    if not observed_path.exists():
        raise FileNotFoundError(f"Missing {observed_path}")

    components = load_components(components_path)
    observed = load_observed(observed_path)

    metrics = compute_metrics(components, observed, alpha)

    results_path = out_dir / "backtest_results.csv"
    with results_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "firm_id",
                "direct_delta_usd",
                "incoming_delta_usd",
                "simulated_delta_usd",
                "alpha",
                "predicted_margin_sign",
                "comparator_margin_sign_direct_only",
                "observed_margin_change_sign",
                "match_flag",
            ]
        )

        for firm_id in sorted(observed.keys()):
            obs_s = observed[firm_id]
            c = components.get(firm_id, {"direct": 0.0, "incoming": 0.0, "simulated": 0.0})

            pred_s = sign_from_cost_delta(c["simulated"], alpha)
            comp_s = sign_from_cost_delta(c["direct"], alpha)

            match = "" if obs_s == 0 else str(int(pred_s == obs_s))

            w.writerow(
                [
                    firm_id,
                    f"{c['direct']:.6f}",
                    f"{c['incoming']:.6f}",
                    f"{c['simulated']:.6f}",
                    f"{alpha:.6f}",
                    pred_s,
                    comp_s,
                    obs_s,
                    match,
                ]
            )

    readout_path = out_dir / "falsification_readout.txt"
    with readout_path.open("w", encoding="utf-8") as f:
        f.write(f"event_id: {event_id}\n")
        f.write(f"alpha: {alpha:.6f}\n")
        f.write(f"sample_size_S: {metrics.n_in_scope}\n")
        f.write(f"accuracy: {metrics.accuracy:.6f}\n")
        f.write(f"baseline_accuracy: {metrics.baseline_accuracy:.6f}\n")
        f.write(f"comparator_accuracy_direct_only: {metrics.comparator_accuracy:.6f}\n")
        f.write(f"coverage: {metrics.coverage:.6f}\n")
        f.write(f"pass: {str(metrics.passed).lower()}\n")


if __name__ == "__main__":
    main()
