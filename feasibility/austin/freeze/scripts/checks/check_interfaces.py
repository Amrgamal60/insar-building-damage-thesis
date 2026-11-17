"""Synthetic interface, validation, sample-accounting and CLI checks."""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_test_b import panel
from test_b import fit_panel, null_test
from deep_model import oof_scores
from check_deep import make_synthetic


def must_fail(fn, error=ValueError):
    try:
        fn()
    except error:
        return True
    raise AssertionError('Invalid input accepted')


def main():
    d = panel(48,8,901)
    results = {}
    for name, bad in [('nonpositive_exposure',d.assign(n=0)), ('negative_count',d.assign(y=-1)),
                      ('nonfinite_velocity',d.assign(v=np.nan)), ('duplicate_cell_quarter',d.iloc[np.r_[np.arange(len(d)),0]]),
                      ('cell_crosses_blocks',d.assign(block=np.arange(len(d))))]:
        results[name] = must_fail(lambda:fit_panel(bad))
    f = d.pivot(index='quarter',columns='cell',values='v').to_numpy()
    badfield = f.copy(); badfield[0,0] = np.nan
    results['nonfinite_surrogate'] = must_fail(lambda:null_test(d,[badfield],np.arange(8),np.arange(48),expected_draws=1))
    results['missing_null_draw'] = must_fail(lambda:null_test(d,[f],np.arange(8),np.arange(48),expected_draws=2))
    z = np.zeros((10,61),np.float32)
    results['block_split_rejected'] = must_fail(lambda:oof_scores(np.zeros((10,2)),z,z.astype(bool),np.tile([0,1],5),np.zeros(10),np.arange(10)%5))
    with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as name:
        tmp = Path(name)
        d.to_csv(tmp/'panel.csv',index=False)
        subprocess.run([sys.executable,'-I',str(ROOT/'test_b.py'),str(tmp/'panel.csv'),str(tmp/'fit.json')],check=True)
        report = json.loads((tmp/'fit.json').read_text())
        results['test_b_cli'] = len(report['used_row_positions']) == report['rows_used']
    data = make_synthetic(5100, True, 910)
    observed, audit = oof_scores(*data)
    cached, _ = oof_scores(*data, comparison_scores=observed['comparison'])
    results['cached_comparison_identity'] = all(np.array_equal(observed[k],cached[k]) for k in observed)
    results['inner_outer_block_disjoint'] = all(not (set(a['training_blocks']) & set(a['validation_blocks']) or
                                                    set(a['training_blocks']) & set(a['test_blocks']) or
                                                    set(a['validation_blocks']) & set(a['test_blocks'])) for a in audit)
    with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as name:
        tmp = Path(name)
        np.savez(tmp/'rows.npz',baseline=data[0],series=data[1],mask=data[2],y=data[3],block=data[4],fold=data[5])
        subprocess.run([sys.executable,'-I',str(ROOT/'deep_model.py'),str(tmp/'rows.npz'),str(tmp/'oof.npz')],check=True)
        with np.load(tmp/'oof.npz') as out:
            results['deep_cli_scores_exact'] = all(np.array_equal(out[k],observed[k]) for k in observed)
            results['deep_cli_row_ids'] = np.array_equal(out['row_id'],np.arange(5100))
    assert all(results.values()), results
    (Path(__file__).parent/'interface_results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))


if __name__ == '__main__':
    main()
