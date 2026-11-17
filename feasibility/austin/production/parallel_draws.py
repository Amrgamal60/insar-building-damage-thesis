"""Parallel execution of the frozen variogram-null draws with identical arithmetic (AUSTIN_PLAN.md §10, §14).

The frozen generator (nyc_lib.VariogramNull.draws, inherited unchanged by LowMemVariogramNull and by the
calibration's CPU adapter calibration/cpu_null.CPULowMemVariogramNull, and wrapped by
conditional_null.ConditionalVariogramNull) draws in order from one numpy Generator. Per draw it makes exactly
two calls on it: rng.permutation(n), then rng.standard_normal(n). Nothing else touches the generator, and how
much of the bit stream these calls consume does not depend on the field. So the generator's state at the
start of draw d is found by replaying those two calls d times, without computing any field.

ParallelDraws has the engines' draws(n, rng) -> (field, k) interface. It replays the states, then each
worker sets a fresh PCG64 generator to the state of its draw and takes one draw from the unchanged engine
(engine.draws(1, rng)). Draws are yielded in draw order, so testa_core.write_surrogates stores them exactly
as a sequential run of the same engine would. The engine is built once in the parent and reaches the
workers by fork (copy-on-write); it is never modified.

Written on 2026-11-10, before any InSAR file was opened, because the user moved all heavy runs to the
processing server, whose GPU is unusable. Checked by check_parallel_draws.py on synthetic fields.
"""
from __future__ import annotations

import copy
import itertools
import multiprocessing as mp
from collections import deque
from concurrent.futures import ProcessPoolExecutor

import numpy as np

_ENGINE = None


def draw_states(rng, n, draws):
    """Bit-generator state at the start of each draw. Advances rng past all draws, as a sequential run."""
    states = []
    for _ in range(draws):
        states.append(copy.deepcopy(rng.bit_generator.state))
        rng.permutation(n)
        rng.standard_normal(n)
    return states


def _one(state):
    bg = np.random.PCG64()
    bg.state = state
    field, k = next(_ENGINE.draws(1, np.random.Generator(bg)))
    return field, int(k)


class ParallelDraws:
    def __init__(self, engine, workers):
        self.engine, self.workers = engine, int(workers)
        self.n = int(engine.n)

    def draws(self, n_draws, rng):
        global _ENGINE
        assert isinstance(rng.bit_generator, np.random.PCG64), "the frozen seed uses default_rng (PCG64)"
        states = draw_states(rng, self.n, n_draws)
        _ENGINE = self.engine
        try:
            with ProcessPoolExecutor(self.workers, mp_context=mp.get_context("fork")) as ex:
                it = iter(states)
                pending = deque(ex.submit(_one, s) for s in itertools.islice(it, 2 * self.workers))
                while pending:
                    field, k = pending.popleft().result()  # draw order; a dead worker raises here
                    nxt = next(it, None)
                    if nxt is not None:
                        pending.append(ex.submit(_one, nxt))
                    yield field, k
        finally:
            _ENGINE = None
