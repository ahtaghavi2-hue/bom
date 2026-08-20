"""Unit tests for PERT Calculator.

Run: python tests/test_pert.py
"""

import sys
import os
import math

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from services.pert_calculator import (
    pert_time, pert_std_dev, pert_variance, calculate,
    pert_path_statistics, probability_project_complete,
)

PASS = 0
FAIL = 0


def check(name, cond, detail=''):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f'  [PASS] {name}')
    else:
        FAIL += 1
        print(f'  [FAIL] {name} {detail}')


def test_basic_pert():
    """Test basic PERT formula: t_e = (O + 4M + P) / 6"""
    print('\n--- PERT Basic Formulas ---')

    # Simple case: O=2, M=4, P=8
    # t_e = (2 + 16 + 8) / 6 = 26/6 ≈ 4.333
    te = pert_time(2, 4, 8)
    check('pert_time(2,4,8) = 26/6', abs(te - 26/6) < 1e-9, f'got {te}')

    # O=1, M=1, P=1 (certain) -> t_e = 1
    te = pert_time(1, 1, 1)
    check('pert_time(1,1,1) = 1.0', abs(te - 1.0) < 1e-9, f'got {te}')

    # O=0, M=0, P=0 -> t_e = 0
    te = pert_time(0, 0, 0)
    check('pert_time(0,0,0) = 0.0', abs(te - 0.0) < 1e-9, f'got {te}')


def test_std_dev():
    """Test PERT standard deviation: σ = (P - O) / 6"""
    print('\n--- PERT Standard Deviation ---')

    # σ = (8 - 2) / 6 = 1.0
    sd = pert_std_dev(2, 8)
    check('pert_std_dev(2,8) = 1.0', abs(sd - 1.0) < 1e-9, f'got {sd}')

    # σ = (1 - 1) / 6 = 0
    sd = pert_std_dev(1, 1)
    check('pert_std_dev(1,1) = 0.0', abs(sd - 0.0) < 1e-9, f'got {sd}')

    # σ = (20 - 5) / 6 = 2.5
    sd = pert_std_dev(5, 20)
    check('pert_std_dev(5,20) = 2.5', abs(sd - 2.5) < 1e-9, f'got {sd}')


def test_variance():
    """Test PERT variance: σ² = ((P - O) / 6)²"""
    print('\n--- PERT Variance ---')

    var = pert_variance(2, 8)
    check('pert_variance(2,8) = 1.0', abs(var - 1.0) < 1e-9, f'got {var}')

    var = pert_variance(5, 20)
    expected = (2.5) ** 2  # 6.25
    check('pert_variance(5,20) = 6.25', abs(var - expected) < 1e-9, f'got {var}')


def test_calculate():
    """Test the full calculate() function."""
    print('\n--- PERT Calculate ---')

    est = calculate(2, 4, 8)
    check('calculate expected = 26/6', abs(est.expected - 26/6) < 1e-9)
    check('calculate std_dev = 1.0', abs(est.std_dev - 1.0) < 1e-9)
    check('calculate variance = 1.0', abs(est.variance - 1.0) < 1e-9)
    check('calculate preserves O/M/P', est.optimistic == 2 and est.most_likely == 4 and est.pessimistic == 8)


def test_validation():
    """Test that invalid inputs raise ValueError."""
    print('\n--- PERT Validation ---')

    try:
        pert_time(5, 3, 8)  # O > M
        check('O > M raises ValueError', False)
    except ValueError:
        check('O > M raises ValueError', True)

    try:
        pert_time(2, 10, 5)  # M > P
        check('M > P raises ValueError', False)
    except ValueError:
        check('M > P raises ValueError', True)


def test_path_statistics():
    """Test path statistics: sum of expected times + sqrt of sum of variances."""
    print('\n--- PERT Path Statistics ---')

    # Two activities: (2,4,8) and (3,5,10)
    # Activity 1: t_e = 26/6 ≈ 4.333, σ² = 1.0
    # Activity 2: t_e = (3+20+10)/6 = 33/6 = 5.5, σ² = ((10-3)/6)² = (7/6)² ≈ 1.361
    # Path: t_e = 4.333 + 5.5 = 9.833, σ = sqrt(1.0 + 1.361) = sqrt(2.361) ≈ 1.537

    path_e, path_sd = pert_path_statistics([(2, 4, 8), (3, 5, 10)])
    expected_e = 26/6 + 33/6
    expected_sd = math.sqrt(1.0 + (7/6)**2)
    check('path expected ~ 9.833', abs(path_e - expected_e) < 1e-9, f'got {path_e}')
    check('path std_dev ~ 1.537', abs(path_sd - expected_sd) < 1e-9, f'got {path_sd}')


def test_probability():
    """Test probability of completion using normal approximation."""
    print('\n--- PERT Probability ---')

    # If expected = 10, std_dev = 2, target = 12
    # z = (12 - 10) / 2 = 1.0 -> P(Z <= 1) ~ 0.8413
    prob = probability_project_complete(10, 2, 12)
    check('P(t<=12) ~ 0.8413', abs(prob - 0.8413) < 0.01, f'got {prob:.4f}')

    # target = expected -> P ~ 0.5
    prob = probability_project_complete(10, 2, 10)
    check('P(t<=10) ~ 0.5', abs(prob - 0.5) < 0.01, f'got {prob:.4f}')

    # target much less -> P close to 0
    prob = probability_project_complete(10, 2, 2)
    check('P(t<=2) ~ 0', prob < 0.01, f'got {prob:.4f}')

    # target much more -> P close to 1
    prob = probability_project_complete(10, 2, 20)
    check('P(t<=20) ~ 1', prob > 0.99, f'got {prob:.4f}')


if __name__ == '__main__':
    test_basic_pert()
    test_std_dev()
    test_variance()
    test_calculate()
    test_validation()
    test_path_statistics()
    test_probability()

    print(f'\nRESULT: {PASS} passed, {FAIL} failed')
    sys.exit(1 if FAIL else 0)
