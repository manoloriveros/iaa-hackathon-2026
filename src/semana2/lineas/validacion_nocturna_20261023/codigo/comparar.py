"""Comparación pareada de OOF con bootstrap de Poisson por componentes cliente-dirección (10.000 réplicas)."""
import sys, json, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import numpy as np, pandas as pd, marco as M
R = pathlib.Path('/home/claude/noche'); O = R / 'salidas/s2/oof'
def compare(names, ref, n=10000, sub=None, oofdir=O):
    oo = {k: pd.read_parquet(oofdir / f'{k}.parquet').set_index('row_id') for k in names}
    base = oo[ref]
    idx = base.index
    if sub is not None: idx = idx[sub(base)]
    y = base.loc[idx, 'y'].values
    comp = M.components(base.loc[idx, 'customer_id'].values, base.loc[idx, 'address_id'].values)
    mus = {k: oo[k].loc[idx, 'mu'].values for k in names}
    bs = M.boot_d2_diff(y, mus, comp, n=n)
    out = {}
    for k in names:
        d = bs[k] - bs[ref]
        out[k] = {'D2': round(M.d2(y, mus[k]), 5), 'diff': round(M.d2(y, mus[k]) - M.d2(y, mus[ref]), 5),
                  'q05': round(float(np.quantile(d, .05)), 5), 'q95': round(float(np.quantile(d, .95)), 5),
                  'P_gt0': round(float((d > 0).mean()), 3)}
    return out
if __name__ == '__main__':
    ref = sys.argv[1]; names = [ref] + sys.argv[2:]
    r = compare(names, ref)
    for k, v in r.items(): print(k, v)
    r2 = compare(names, ref, n=2000, sub=lambda b: b.y.values <= np.quantile(b.y.values, 0.999))
    print('-- sin el 0,1 % de filas más caras')
    for k, v in r2.items(): print(k, v)
