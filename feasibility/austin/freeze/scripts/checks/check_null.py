"""Small synthetic step-0 equivalence check, reproducible from frozen copies."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    upstream = ROOT.parents[1]/'nyc'/'scripts'/'nyc_lib.py'
    timing = ROOT.parent/'step0'/'timing'/'lowmem_null.py'
    result = dict(synthetic_only=True, tolerance=1e-11,
                  frozen_nyc_sha256=sha(ROOT/'nyc_lib.py'), upstream_nyc_sha256=sha(upstream),
                  frozen_lowmem_sha256=sha(ROOT/'lowmem_null.py'), step0_lowmem_sha256=sha(timing))
    assert result['frozen_nyc_sha256'] == result['upstream_nyc_sha256']
    assert result['frozen_lowmem_sha256'] == result['step0_lowmem_sha256']
    try:
        state = subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,memory.free',
                                          '--format=csv,noheader,nounits'],text=True).strip()
        result['nvidia_smi_before'] = state
        free = int(state.splitlines()[0].split(',')[-1].strip())
        if free < 2048:
            raise RuntimeError(f'Only {free} MiB free; 2048 MiB conservative minimum')
    except (OSError, subprocess.CalledProcessError, RuntimeError, ValueError) as e:
        result.update(status='UNVERIFIED', reason=str(e))
    else:
        import nyc_lib as N
        from lowmem_null import LowMemVariogramNull
        rng = np.random.default_rng(5)
        xy = np.unique(np.floor(rng.uniform(0,3000,(4000,2))/30),axis=0)*30+15
        n,W = len(xy),11
        fields = rng.standard_normal(n)[None,:]+.3*rng.standard_normal((W,n))
        fields[rng.random((W,n))<.1] = np.nan
        a = N.VariogramNull(fields,xy,30.,kmax=200)
        b = LowMemVariogramNull(fields,xy,30.,kmax=200,chunk=3)
        identical_counts = np.array_equal(a.cp.asnumpy(a.cnt), b.cp.asnumpy(b.cnt))
        draws = []
        for (sa,ka),(sb,kb) in zip(a.draws(4,np.random.default_rng(2027)),
                                  b.draws(4,np.random.default_rng(2027))):
            delta = float(np.nanmax(np.abs(sa-sb)))
            assert ka==kb and delta<=result['tolerance'] and np.array_equal(np.isnan(sa),np.isnan(sb))
            draws.append(dict(original_k=int(ka), lowmem_k=int(kb), max_abs_difference=delta))
        assert identical_counts
        result.update(status='PASS', cells=n, windows=W, pair_counts_identical=identical_counts,
                      draws=draws, max_abs_difference=max(d['max_abs_difference'] for d in draws))
    (Path(__file__).parent/'null_results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
