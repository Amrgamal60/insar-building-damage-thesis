# Planted-signal check of Test A (AUSTIN_PLAN.md §14)

Datasets per cell: 100 (projection 1.8 h on 64 workers; fallback not applied). Null draws per dataset: 999. Synthetic events per dataset: 1754.

A dataset meets the §11 rule if its change in PR AUC is positive and p < 0.05. Paired bias is the observed change minus the mean of that dataset's null draws; intervals are Student t over datasets. p deciles count (0,.1], ..., (.9,1].

| Cell | Meets §11 rule [95% Wilson] | Mean observed change [95% t] | Mean null change | Paired bias [95% t] | p deciles |
|---|---|---|---|---|---|
| 1. nothing added | 5/100 = 5.0% [2.2, 11.2] | -0.00010 [-0.00016, -0.00003] | -0.00011 | +0.00002 [-0.00003, +0.00006] | [12, 6, 12, 14, 13, 8, 8, 8, 8, 11] |
| 2. 0.65 t (nonlinear soil) | 11/100 = 11.0% [6.3, 18.6] | -0.00026 [-0.00038, -0.00015] | -0.00025 | -0.00001 [-0.00011, +0.00009] | [20, 6, 7, 12, 9, 5, 4, 12, 8, 17] |
| 3. 0.7 H (hidden spatial field) | 5/100 = 5.0% [2.2, 11.2] | -0.00009 [-0.00023, +0.00004] | -0.00008 | -0.00002 [-0.00008, +0.00005] | [11, 10, 12, 7, 8, 7, 11, 12, 9, 13] |
| 4. beta = -0.1 | 34/100 = 34.0% [25.5, 43.7] | +0.00070 [+0.00054, +0.00086] | +0.00033 | +0.00037 [+0.00027, +0.00047] | [47, 13, 4, 6, 7, 6, 3, 5, 4, 5] |
| 5. beta = -0.2 | 75/100 = 75.0% [65.7, 82.5] | +0.00275 [+0.00253, +0.00298] | +0.00132 | +0.00143 [+0.00127, +0.00159] | [83, 8, 1, 4, 2, 1, 0, 1, 0, 0] |
| 6. beta = -0.4 | 100/100 = 100.0% [96.3, 100.0] | +0.00948 [+0.00907, +0.00990] | +0.00406 | +0.00542 [+0.00513, +0.00572] | [100, 0, 0, 0, 0, 0, 0, 0, 0, 0] |

Source hashes: `planted_signal.py` 977f626f1c72ab25e6c3f70b062fe1010252b9027f0e8bba113f4acad882b8f4, `testa_core.py` f4d71575c3179ef2f6ac7aeff8e0a26c14ab515db76ad937e411fae9e6e38430, `nyc_lib.py` 619e4de49415bc2f33cc7e54cd91f26740a37de8c0fcd0d990503a93f4546db1.
Input fingerprints: {"checkpoint1_inputs": {"features": "d02137242303f60380a026b68a73c55bfed5c599840538d90d14dc4a4769db6a", "grid": "c13e637f7e10bc25469e1384d19065cf44e7e0617fbc1c7808e96b14e27fd7bb", "episodes": "ba6898f7887c6aeab5b93c31b86c9314d887583fbb5bb46b78bc305efd5d0ace", "censoring": "0e223f92ef2ad60a3f1124a8e51870b239a9a57afc6ef25c76ae8e8ae7fd4a91"}, "field_npz": "7a9ad77f75b05c4a13d7cc29db07da47c871c8a31e196aae49989a521aa4a4e4", "null_field": "970344870bc083ddbe6d21260d00416e9afba5813b0a9e8a41007e8a5abb7e3e", "coefficients": "2f67ed802968a6992101894724fdfb09489bb3fb2e8054ef277e37a1c98a9c8b", "event_dates": "8bd81249242c48e018b4c16d95c3d5bbb529d998bf4a708dbca4a82b335d495a", "surrogates": "07bf0d54eef4b62389ce81d62732388cbf62c9cc66a22a44e5d67308d556c055", "quantiles": "99d9e71bfbf25dd28d2fb563b159d022de6e402ad6067d5dd834b1ad7d62feff"}.
