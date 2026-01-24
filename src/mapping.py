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


def predicted_margin_sign(cost_delta_usd: float, alpha: float, firm_profile: str | None) -> int:
    """
    Phase 5 mapping gate

    If firm_profile is ip_licensing_dominated, this model does not claim
    that cost deltas map to gross margin sign. Return 0 and let evaluation
    exclude it from the falsification set S.

    Otherwise use the existing sign_from_cost_delta logic unchanged.
    """
    if firm_profile == "ip_licensing_dominated":
        return 0

    return sign_from_cost_delta(cost_delta_usd, alpha)
