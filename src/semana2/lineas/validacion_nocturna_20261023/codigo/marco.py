"""Marco común de la escalera de semana 2: particiones, métricas, bootstrap por componentes y modelos estándar.

Particiones propias (fijadas antes de medir, independientes de las de Codex): fold = int(sha256('noche_v1|'+customer_id)[:16],16) % 5.
Métrica: D² Tweedie p=1,5 sobre importes por fila, global (tres ramos concatenados) y por ramo; nulo = media de y del conjunto.
En desarrollo y confirmación el objetivo es T0 y la predicción es la de T0: mu = tasa último * e_ef_coste.
"""
import hashlib, json, pathlib, sys, time
import numpy as np, pandas as pd

R = pathlib.Path('/home/claude/noche')
sys.path.insert(0, str(R / 'codigo'))
P = 1.5


def fold_of(ids, salt='noche_v1', k=5):
    return np.array([int(hashlib.sha256(f'{salt}|{x}'.encode()).hexdigest()[:16], 16) % k for x in ids])


def dev(y, mu, p=P):
    y = np.asarray(y, float); mu = np.asarray(mu, float)
    return 2 * (np.power(y, 2 - p) / ((1 - p) * (2 - p)) - y * np.power(mu, 1 - p) / (1 - p) + np.power(mu, 2 - p) / (2 - p))


def d2(y, mu):
    y = np.asarray(y, float)
    return 1 - dev(y, mu).sum() / dev(y, np.full_like(y, y.mean())).sum()


def components(cust, addr):
    """Componentes conexas cliente-dirección (union-find)."""
    keys = pd.Index(pd.unique(np.concatenate([('c' + pd.Series(cust).astype(str)).values, ('a' + pd.Series(addr).astype(str)).values])))
    par = np.arange(len(keys))
    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    ci = keys.get_indexer('c' + pd.Series(cust).astype(str)); ai = keys.get_indexer('a' + pd.Series(addr).astype(str))
    for x, z in zip(ci, ai):
        rx, rz = find(x), find(z)
        if rx != rz: par[rx] = rz
    roots = np.array([find(i) for i in ci])
    return pd.factorize(roots)[0]


def boot_d2_diff(y, mus, comp, n=10000, seed=2026102301, batch=250):
    """Bootstrap de Poisson por componente. mus: dict nombre->mu. Devuelve dict de arrays de D² por réplica."""
    y = np.asarray(y, float); K = comp.max() + 1
    agg = lambda v: np.bincount(comp, weights=v, minlength=K)
    Sy = agg(y); Sy2 = agg(np.power(y, 2 - P)); Sn = agg(np.ones_like(y))
    Sd = {k: agg(dev(y, m)) for k, m in mus.items()}
    rng = np.random.default_rng(seed); out = {k: [] for k in mus}
    for s in range(0, n, batch):
        W = rng.poisson(1.0, size=(min(batch, n - s), K)).astype(float)
        ny = W @ Sy; nn = W @ Sn; c = ny / nn; ny2 = W @ Sy2
        null = 2 * (ny2 / ((1 - P) * (2 - P)) - ny * np.power(c, 1 - P) / (1 - P) + nn * np.power(c, 2 - P) / (2 - P))
        for k in mus:
            out[k].append(1 - (W @ Sd[k]) / null)
    return {k: np.concatenate(v) for k, v in out.items()}


# ---------------------------------------------------------------- modelos estándar

def design_glm(Xtr, Xte, cols, categ, nbins=6, min_share=0.005, w=None):
    """Numéricas a cuantiles (bordes del entrenamiento) más 'missing'; categorías raras (<0,5 % de filas) a 'otros'."""
    A = {}; B = {}
    for c in cols:
        if c in categ or Xtr[c].nunique(dropna=True) <= 12:  # binarias y discretas cortas como categorías
            s_tr = Xtr[c].astype('string').fillna('missing'); s_te = Xte[c].astype('string').fillna('missing')
            share = s_tr.value_counts(normalize=True)
            keep = set(share[share >= min_share].index)
            A[c] = s_tr.where(s_tr.isin(keep), 'otros'); B[c] = s_te.where(s_te.isin(keep), 'otros')
        else:
            v = Xtr[c].astype(float)
            qs = np.unique(np.nanquantile(v, np.linspace(0, 1, nbins + 1)[1:-1])) if v.notna().any() else np.array([])
            def cut(x):
                x = x.astype(float)
                lab = np.searchsorted(qs, x.values, side='right').astype(str)
                lab = np.where(np.isnan(x.values), 'missing', lab)
                return pd.Series(lab, index=x.index)
            A[c] = cut(Xtr[c]); B[c] = cut(Xte[c])
    A = pd.DataFrame(A); B = pd.DataFrame(B)
    for c in cols:
        cats = sorted(set(A[c]) | {'otros'})
        A[c] = pd.Categorical(A[c], categories=cats); B[c] = pd.Categorical(B[c].where(B[c].isin(cats), 'otros'), categories=cats)
    return A, B


def fit_glm_tweedie(Xtr, ytr, off_tr, Xte, off_te, alpha):
    from glum import GeneralizedLinearRegressor, TweedieDistribution
    m = GeneralizedLinearRegressor(family=TweedieDistribution(P), link='log', alpha=alpha, l1_ratio=0.0,
                                   fit_intercept=True, drop_first=False, max_iter=200)
    m.fit(Xtr, ytr, offset=off_tr)
    return m.predict(Xte, offset=off_te), m


def fit_glm_fs(Xtr, ntr, t0tr, off_tr, Xte, off_te, alpha_f, alpha_s):
    from glum import GeneralizedLinearRegressor
    f = GeneralizedLinearRegressor(family='poisson', link='log', alpha=alpha_f, l1_ratio=0.0, drop_first=False, max_iter=200)
    f.fit(Xtr, ntr, offset=off_tr)
    pos = (ntr > 0) & (t0tr > 0)
    s = GeneralizedLinearRegressor(family='gamma', link='log', alpha=alpha_s, l1_ratio=0.0, drop_first=False, max_iter=200)
    s.fit(Xtr[pos], (t0tr[pos] / ntr[pos]), sample_weight=ntr[pos])
    return f.predict(Xte, offset=off_te) * s.predict(Xte), (f, s)


def fit_gbm_tweedie(Xtr, ytr, off_tr, Xte, off_te, ids_tr, params=None, seed=7):
    import lightgbm as lgb
    p = dict(objective='tweedie', tweedie_variance_power=P, learning_rate=0.02, num_leaves=7, min_data_in_leaf=400,
             feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, min_data_per_group=500,
             cat_smooth=50, max_cat_to_onehot=8, verbose=-1, seed=seed, deterministic=True, force_row_wise=True,
             num_threads=2)
    if params: p.update(params)
    base = np.log(ytr.sum() / np.exp(off_tr).sum())  # punto de partida: tasa media del entrenamiento
    off_tr = off_tr + base; off_te = off_te + base
    inner = fold_of(ids_tr, salt='noche_inner', k=5) == 0
    dtr = lgb.Dataset(Xtr[~inner], ytr[~inner], init_score=off_tr[~inner], free_raw_data=False)
    dva = lgb.Dataset(Xtr[inner], ytr[inner], init_score=off_tr[inner], reference=dtr)
    b = lgb.train(p, dtr, num_boost_round=3000, valid_sets=[dva], callbacks=[lgb.early_stopping(150, verbose=False)])
    nb = b.best_iteration
    full = lgb.train(p, lgb.Dataset(Xtr, ytr, init_score=off_tr), num_boost_round=max(nb, 1))
    return np.exp(full.predict(Xte, raw_score=True) + off_te), (full, nb)
