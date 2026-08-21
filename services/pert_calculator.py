"""PERT (Program Evaluation and Review Technique) Calculator.

Standard formulas:
  Expected Time:  t_e = (O + 4M + P) / 6
  Std Deviation:  σ   = (P - O) / 6
  Variance:       σ²  = ((P - O) / 6)²

Where:
  O = Optimistic time
  M = Most Likely time
  P = Pessimistic time
"""

import math
from typing import Optional, Tuple, List
from dataclasses import dataclass


@dataclass
class PertEstimate:
    """Result of a PERT calculation for a single activity."""
    optimistic: float
    most_likely: float
    pessimistic: float
    expected: float
    std_dev: float
    variance: float

    def __post_init__(self):
        if self.optimistic > self.most_likely:
            raise ValueError(
                f"Optimistic ({self.optimistic}) must be <= Most Likely ({self.most_likely})"
            )
        if self.most_likely > self.pessimistic:
            raise ValueError(
                f"Most Likely ({self.most_likely}) must be <= Pessimistic ({self.pessimistic})"
            )


def pert_time(optimistic: float, most_likely: float, pessimistic: float) -> float:
    """Calculate PERT expected time: t_e = (O + 4M + P) / 6."""
    if optimistic > most_likely:
        raise ValueError(f"O={optimistic} must be <= M={most_likely}")
    if most_likely > pessimistic:
        raise ValueError(f"M={most_likely} must be <= P={pessimistic}")
    return (optimistic + 4 * most_likely + pessimistic) / 6.0


def pert_std_dev(optimistic: float, pessimistic: float) -> float:
    """Calculate PERT standard deviation: σ = (P - O) / 6."""
    return (pessimistic - optimistic) / 6.0


def pert_variance(optimistic: float, pessimistic: float) -> float:
    """Calculate PERT variance: σ² = ((P - O) / 6)²."""
    return pert_std_dev(optimistic, pessimistic) ** 2


def calculate(optimistic: float, most_likely: float, pessimistic: float) -> PertEstimate:
    """Full PERT calculation returning a PertEstimate dataclass."""
    te = pert_time(optimistic, most_likely, pessimistic)
    sd = pert_std_dev(optimistic, pessimistic)
    var = sd ** 2
    return PertEstimate(
        optimistic=optimistic,
        most_likely=most_likely,
        pessimistic=pessimistic,
        expected=te,
        std_dev=sd,
        variance=var,
    )


def pert_path_statistics(
    activities: List[Tuple[float, float, float]],
) -> Tuple[float, float]:
    """Calculate expected time and std dev for a path of independent activities.

    Args:
        activities: List of (optimistic, most_likely, pessimistic) tuples.

    Returns:
        (path_expected, path_std_dev) where:
            path_expected = Σ t_e_i
            path_std_dev  = sqrt(Σ σ²_i)
    """
    total_expected = 0.0
    total_variance = 0.0

    for o, m, p in activities:
        total_expected += pert_time(o, m, p)
        total_variance += pert_variance(o, p)

    return total_expected, math.sqrt(total_variance)


def probability_project_complete(
    path_expected: float,
    path_std_dev: float,
    target_time: float,
) -> float:
    """Estimate probability of completing a path within target_time using normal approximation.

    Returns a value between 0 and 1.
    """
    if path_std_dev == 0:
        return 1.0 if target_time >= path_expected else 0.0

    z = (target_time - path_expected) / path_std_dev
    # Approximation of the standard normal CDF (Abramowitz & Stegun)
    return _norm_cdf(z)


def _norm_cdf(z: float) -> float:
    """Approximation of the standard normal cumulative distribution function."""
    if z < -8:
        return 0.0
    if z > 8:
        return 1.0

    a1 = 0.254829592
    a2 = -0.284496736
    a3 = 1.421413741
    a4 = -1.453152027
    a5 = 1.061405429
    p = 0.3275911

    sign = 1 if z >= 0 else -1
    x = abs(z) / math.sqrt(2)
    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x)
    return 0.5 * (1.0 + sign * y)
