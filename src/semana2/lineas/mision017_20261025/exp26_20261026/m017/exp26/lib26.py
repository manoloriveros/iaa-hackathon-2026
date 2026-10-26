import numpy as np, pandas as pd, json
exec(open("/home/claude/m017/f3_eval.py").read().split("K = 300")[0])
W = pd.read_parquet("/home/claude/ml2/datos/emerging/weather.parquet").set_index(["address_id", "year"])
def wvar(t, v, year=None):
    a = pol.address_id.reindex(t.index).values; yr = t.year.values.astype(int) if year is None else np.full(len(t), year)
    return W[v].reindex(pd.MultiIndex.from_arrays([a, yr])).values
def d2u(t, m):
    y = t.y.values; return 1 - dev(y, m).sum() / dev(y, np.full(len(y), y.mean())).sum()
def rel_base(t):
    """m llevado al nivel Tweedie-óptimo de su celda"""
    return nivel_celda(t, t.m.values)
def fac_tw(t, clave, lines, k=300, by_nb=False):
    """factor Tweedie-óptimo por nivel, relativo a la celda, con credibilidad n/(n+k) en log"""
    c = celda(t); kk = clave(t); m = rel_base(t); y = t.y.values; f = {}
    for l in lines:
        il = t.line.values == l
        grupos = [("all", il)] if not by_nb else [(nb, il & (t.new_business.values == nb)) for nb in (False, True)]
        for g, i in grupos:
            for v in np.unique(kk[i]):
                j = i & (kk == v); n = (y[j] > 0).sum()
                if n == 0: continue
                kv = np.sum(y[j] / np.sqrt(m[j])) / np.sum(np.sqrt(m[j]))
                f[(l, g, v)] = np.exp(n / (n + k) * np.log(max(kv, 1e-3)))
    return f
def aplica_tw(t, f, clave, m, by_nb=False):
    c = celda(t); kk = clave(t); m0 = m.copy()
    g = t.new_business.values if by_nb else np.array(["all"] * len(t), dtype=object)
    m = m * np.array([f.get((l, gg, v), 1.0) for l, gg, v in zip(t.line.values, g, kk)])
    for cc in np.unique(c): i = c == cc; m[i] *= m0[i].sum() / m[i].sum()
    return m
