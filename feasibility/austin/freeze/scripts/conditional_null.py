"""Conditional pixel-field variogram null; synthetic calibration and production API.

Fit each window's velocity on pixel means of the baseline covariates, EXCLUDING
coordinates. Fit is in-sample and outcome-blind. The fixed HGB specification is
not selected from outcomes. Randomize residuals using the unchanged memory-lean
NYC generator, then add the fitted mean back. This estimates a conditional null;
it does not guarantee conditional exchangeability or correct residual covariance.
"""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

from lowmem_null import LowMemVariogramNull
import nyc_lib as N


HGB_SETTINGS = dict(learning_rate=0.1, max_iter=100, max_leaf_nodes=15,
                    max_depth=None, min_samples_leaf=20, l2_regularization=1.0,
                    max_bins=255, early_stopping=False, random_state=0,
                    loss="squared_error", categorical_features=None)


class ConditionalVariogramNull:
    """Same ``draws(n_draws, rng) -> (W-by-pixel field, k)`` API as VariogramNull.

    ``covariates`` is pixel-by-feature, already averaged over the parcels sharing
    each pixel. Do not pass coordinates or outcomes. No parcel weighting is used
    in this regression. Missing velocity masks are preserved. Missing covariates
    are rejected so production must establish the common baseline population.
    ``null_factory`` is an optional compatible backend (default LowMemVariogramNull),
    useful for arithmetic-equivalent CPU execution and small identity unit checks.
    """

    def __init__(self, fields, xy, res, covariates, *, feature_names=None,
                 kmax=1000, max_lag=N.MAX_LAG, chunk=8, null_factory=None):
        fields = np.asarray(fields, dtype=float)
        xy = np.asarray(xy, dtype=float)
        covariates = np.asarray(covariates, dtype=float)
        if fields.ndim != 2 or fields.shape[1] < 3:
            raise ValueError("fields must be (windows, pixels), with at least three pixels")
        if xy.shape != (fields.shape[1], 2) or not np.isfinite(xy).all():
            raise ValueError("xy must be finite (pixels, 2)")
        if (covariates.ndim != 2 or covariates.shape[0] != fields.shape[1]
                or covariates.shape[1] < 1 or not np.isfinite(covariates).all()):
            raise ValueError("covariates must be finite (pixels, baseline features)")
        if feature_names is not None:
            if len(feature_names) != covariates.shape[1]:
                raise ValueError("feature_names length must match covariates")
            forbidden = {"x", "y", "x_km", "y_km", "latitude", "longitude", "easting", "northing"}
            if forbidden.intersection(str(s).lower() for s in feature_names):
                raise ValueError("Coordinates must be excluded from the conditional regression")
        if not np.isfinite(res) or res <= 0:
            raise ValueError("res must be positive and finite")
        self.valid = np.isfinite(fields)
        if (self.valid.sum(axis=1) < 3).any():
            raise ValueError("Every window needs at least three finite velocities")
        self.n, self.W = fields.shape[1], fields.shape[0]
        self.fitted = np.full_like(fields, np.nan)
        self.regressors = []
        self.explained_variance = []
        for w, valid in enumerate(self.valid):
            reg = HistGradientBoostingRegressor(**HGB_SETTINGS)
            reg.fit(covariates[valid], fields[w, valid])
            self.fitted[w, valid] = reg.predict(covariates[valid])
            self.regressors.append(reg)
            residual = fields[w, valid] - self.fitted[w, valid]
            var = np.var(fields[w, valid])
            self.explained_variance.append(float(1 - np.var(residual) / var) if var > 0 else 0.0)
        self.residuals = np.where(self.valid, fields - self.fitted, np.nan)
        factory = LowMemVariogramNull if null_factory is None else null_factory
        self.residual_null = factory(self.residuals, xy, res, kmax=kmax,
                                     max_lag=max_lag, chunk=chunk)

    def draws(self, n_draws, rng):
        for residual, k in self.residual_null.draws(n_draws, rng):
            yield np.where(self.valid, self.fitted + residual, np.nan), k
