from __future__ import annotations


def sign_from_cost_delta(cost_delta_usd: float, alpha: float) -> int:
    if alpha < 0.0 or alpha > 1.0:
        raise ValueError("alpha must be in [0, 1]")

    effective = cost_delta_usd * (1.0 - alpha)

    if effective == 0.0:
        return 0

    if effective > 0.0:
        return -1

    return 1
