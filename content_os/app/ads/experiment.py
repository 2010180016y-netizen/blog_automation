from __future__ import annotations

from typing import Dict


def recommend_ad_experiment(rpm: float, rps: float, ads_per_page: int, bounce_rate: float) -> Dict:
    """
    Guardrail-based recommendation for ad load experiments.
    - Increase only when RPM/RPS are weak and UX risk is acceptable.
    - Hold/decrease when bounce rate or ad density suggests quality risk.
    """
    target_rpm = 12.0
    target_rps = 0.08
    max_ads_per_page = 6

    recommendation = "HOLD"
    reason = "Metrics are within guardrails."

    if bounce_rate >= 0.7:
        recommendation = "DECREASE"
        reason = "High bounce rate indicates UX risk; reduce ad load first."
    elif ads_per_page >= max_ads_per_page:
        recommendation = "HOLD"
        reason = "Ad density already at cap; do not increase."
    elif rpm < target_rpm and rps < target_rps and bounce_rate < 0.6:
        recommendation = "INCREASE_STEP"
        reason = "Low monetization efficiency with acceptable bounce; run +1 ad slot A/B test."

    return {
        "recommendation": recommendation,
        "reason": reason,
        "guardrails": {
            "target_rpm": target_rpm,
            "target_rps": target_rps,
            "max_ads_per_page": max_ads_per_page,
            "bounce_rate_ceiling": 0.7,
        },
    }
