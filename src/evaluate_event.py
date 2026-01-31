from __future__ import annotations

import os
import csv
from dataclasses import dataclass
from pathlib import Path

from mapping import predicted_margin_sign, _OUT_OF_SCOPE_PROFILES


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


def _find_firm_profile_file(base: Path) -> Path | None:
    candidates = [
        base / "firm_profile.csv",
        base / "firm_profiles.csv",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def load_firm_profiles(event_id: str) -> dict[str, str]:
    """
    Loads firm profiles from manual inputs if present.
    If the file does not exist, return empty dict and no gating is applied.
    """
    base = Path("data") / "manual_inputs" / event_id
    p = _find_firm_profile_file(base)
    if p is None:
        return {}

    out: dict[str, str] = {}
    with p.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        required = {"event_id", "firm_id", "firm_profile", "evidence_note"}
        missing = required - set(r.fieldnames or [])
        if missing:
            raise ValueError(f"Firm profile CSV missing columns: {sorted(missing)}")

        for row in r:
            firm_id = (row["firm_id"] or "").strip()
            profile = (row["firm_profile"] or "").strip()
            if firm_id and profile:
                out[firm_id] = profile
    return out


def compute_metrics(
    components: dict[str, dict[str, float]],
    observed: dict[str, int],
    firm_profiles: dict[str, str],
    alpha: float,
) -> Metrics:
    rows = []
    for firm, obs_sign in observed.items():
        if obs_sign not in (-1, 0, 1):
            continue

        c = components.get(firm, {"direct": 0.0, "incoming": 0.0, "simulated": 0.0})

        simulated_delta = c["simulated"]
        direct_delta = c["direct"]

        profile = firm_profiles.get(firm)

        predicted_sign = predicted_margin_sign(simulated_delta, alpha, profile)
        comparator_sign = predicted_margin_sign(direct_delta, alpha, profile)

        rows.append((firm, simulated_delta, direct_delta, predicted_sign, comparator_sign, obs_sign, profile))

    def in_scope_row(r: tuple[str, float, float, int, int, int, str | None]) -> bool:
        _, sim_d, _, _, _, obs_s, profile = r
        if obs_s not in (-1, 1):
            return False
        if profile in _OUT_OF_SCOPE_PROFILES:
            return False
        return True

    in_scope = [r for r in rows if in_scope_row(r)]
    n = len(in_scope)
    if n == 0:
        return Metrics(0, 0.0, 0.0, 0.0, 0.0, False)

    matches = sum(1 for (_, _, _, pred_s, _, obs_s, _) in in_scope if pred_s == obs_s)
    accuracy = matches / n

    baseline_sign = 1
    baseline_matches = sum(1 for (_, _, _, _, _, obs_s, _) in in_scope if baseline_sign == obs_s)
    baseline_accuracy = baseline_matches / n

    comparator_matches = sum(1 for (_, _, _, _, comp_s, obs_s, _) in in_scope if comp_s == obs_s)
    comparator_accuracy = comparator_matches / n

    covered = sum(1 for (_, sim_d, _, _, _, _, _) in in_scope if sim_d != 0.0)
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
    firm_profiles = load_firm_profiles(event_id)

    metrics = compute_metrics(components, observed, firm_profiles, alpha)

    results_path = out_dir / "backtest_results.csv"
    with results_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "firm_id",
                "firm_profile",
                "direct_delta_usd",
                "incoming_delta_usd",
                "simulated_delta_usd",
                "alpha",
                "predicted_margin_sign",
                "comparator_margin_sign_direct_only",
                "observed_margin_change_sign",
                "match_flag",
                "in_scope_S",
            ]
        )

        for firm_id in sorted(observed.keys()):
            obs_s = observed[firm_id]
            c = components.get(firm_id, {"direct": 0.0, "incoming": 0.0, "simulated": 0.0})
            profile = firm_profiles.get(firm_id)

            pred_s = predicted_margin_sign(c["simulated"], alpha, profile)
            comp_s = predicted_margin_sign(c["direct"], alpha, profile)

            in_scope = int((obs_s in (-1, 1)) and (profile not in _OUT_OF_SCOPE_PROFILES))

            match = ""
            if in_scope == 1:
                match = str(int(pred_s == obs_s))

            w.writerow(
                [
                    firm_id,
                    profile or "",
                    f"{c['direct']:.6f}",
                    f"{c['incoming']:.6f}",
                    f"{c['simulated']:.6f}",
                    f"{alpha:.6f}",
                    pred_s,
                    comp_s,
                    obs_s,
                    match,
                    in_scope,
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
