from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Metrics:
    n_in_scope: int
    accuracy: float
    baseline_accuracy: float
    coverage: float
    passed: bool


def sign(x: float) -> int:
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


def load_simulated(path: Path) -> dict[str, float]:
    out: dict[str, float] = {}
    with path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            firm = (row["firm_id"] or "").strip()
            val = float((row["simulated_delta_usd"] or "0").strip())
            out[firm] = val
    return out


def load_observed_from_psql_dump(path: Path) -> dict[str, int]:
    out: dict[str, int] = {}
    with path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            firm = (row["firm_id"] or "").strip()
            s = int((row["margin_change_sign"] or "0").strip())
            out[firm] = s
    return out


def compute_metrics(sim: dict[str, float], obs: dict[str, int]) -> Metrics:
    rows = []
    for firm, obs_sign in obs.items():
        if obs_sign not in (-1, 0, 1):
            continue
        sim_delta = sim.get(firm, 0.0)
        sim_sign = sign(sim_delta)
        rows.append((firm, sim_delta, sim_sign, obs_sign))

    in_scope = [r for r in rows if r[3] in (-1, 1)]
    n = len(in_scope)
    if n == 0:
        return Metrics(0, 0.0, 0.0, 0.0, False)

    matches = sum(1 for (_, _, sim_s, obs_s) in in_scope if sim_s == obs_s)
    accuracy = matches / n

    baseline_sign = 1
    baseline_matches = sum(1 for (_, _, _, obs_s) in in_scope if baseline_sign == obs_s)
    baseline_accuracy = baseline_matches / n

    covered = sum(1 for (_, sim_d, _, _) in in_scope if sim_d != 0.0)
    coverage = covered / n

    passed = accuracy > baseline_accuracy
    return Metrics(n, accuracy, baseline_accuracy, coverage, passed)


def main() -> None:
    event_id = "event_0001"

    out_dir = Path("outputs") / event_id
    out_dir.mkdir(parents=True, exist_ok=True)

    sim_path = out_dir / "simulated_deltas.csv"
    obs_path = out_dir / "observed_margin_sign.csv"

    if not sim_path.exists():
        raise FileNotFoundError(f"Missing {sim_path}")

    if not obs_path.exists():
        raise FileNotFoundError(
            f"Missing {obs_path}. Export it from Postgres using the command in the instructions."
        )

    sim = load_simulated(sim_path)
    obs = load_observed_from_psql_dump(obs_path)

    metrics = compute_metrics(sim, obs)

    # Write backtest_results.csv
    results_path = out_dir / "backtest_results.csv"
    with results_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["firm_id", "simulated_delta_usd", "simulated_sign", "observed_margin_change_sign", "match_flag"])
        for firm_id in sorted(obs.keys()):
            obs_s = obs[firm_id]
            sim_d = sim.get(firm_id, 0.0)
            sim_s = sign(sim_d)
            match = "" if obs_s == 0 else str(int(sim_s == obs_s))
            w.writerow([firm_id, f"{sim_d:.6f}", sim_s, obs_s, match])

    # Write falsification_readout.txt
    readout_path = out_dir / "falsification_readout.txt"
    with readout_path.open("w", encoding="utf-8") as f:
        f.write(f"event_id: {event_id}\n")
        f.write(f"sample_size_S: {metrics.n_in_scope}\n")
        f.write(f"accuracy: {metrics.accuracy:.6f}\n")
        f.write(f"baseline_accuracy: {metrics.baseline_accuracy:.6f}\n")
        f.write(f"coverage: {metrics.coverage:.6f}\n")
        f.write(f"pass: {str(metrics.passed).lower()}\n")


if __name__ == "__main__":
    main()
