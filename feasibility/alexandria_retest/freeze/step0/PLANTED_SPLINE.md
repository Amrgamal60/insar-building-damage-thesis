# Planted check of the flexible-baseline secondary (ALEX_RETEST_PLAN.md secondary 14)

Datasets per cell: 500; null c2, 999 draws; the same synthetic datasets as the main check (`step0/planted_20261117/`), so the linear-baseline column is paired. Rejection: p < 0.05, T > 0, beta-hat < 0.

| Cell | flexible baseline: T under c2 | paired bias | linear baseline (main check): T under c2 | mean beta-hat (flexible) |
|---|---|---|---|---|
| 1. nothing added | 2.4% [1.4, 4.1] | +0.130 [-0.105, +0.365] | 4.4% | -0.14 |
| 2. 0.65 t (nonlinear covariate) | 3.0% [1.8, 4.9] ✗ | +0.341 [+0.120, +0.562] | 10.0% | -0.10 |
| 7. beta = observed | 73.0% [68.9, 76.7] | +13.769 [+12.939, +14.599] | 86.0% | -1.35 |

✗ = not acceptable by the §9 criteria (reported only; no rule depends on it).

Sources: {"planted_py": "3528f3d76978a44b6e0a8482cae6a68398e20ad06fa43aaf55e69de43c93ee96", "retest_core": "299076d8acd0b61bdf2653cab9a287bbe328dadf7989099e2cb2adda68e16499", "inputs": "03c0b825a259398df9afc3135bbac4f0e3c6f56e69684d732c62646c02dc66d7", "planted_spline_py": "2149637c89931f9b003d368db59686c05129d583d7a9ef2959f9d33ef9bf6353", "design_sha256": "a9fa95654ea4d6cf66b578e465cb6e6003ff0b7b728de685aa6a515be0ffdad6"}.
