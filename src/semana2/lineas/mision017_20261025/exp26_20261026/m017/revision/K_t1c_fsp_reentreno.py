"""K tarea 1c/3b: reentreno propio de la FSp ligera (desarrollado 2021-2023, mismos hiperparámetros) para
(i) comprobar que las predicciones emergentes del autor salen solo del desarrollado y (ii) medir en el desarrollado 2024 (fuera de tiempo,
en dominio, muestra grande) el valor de mezclar la FSp con T2b por NB/renovación y año completo.
Usa las utilidades de lectura de variables de la línea ML (cargar, matriz, categorias_union) y la completitud por peligro."""
import os, sys, time, json
os.environ["MLIND_RAIZ"] = "/home/claude/ml2"; sys.path.insert(0, "/home/claude/ml2/codigo")
import numpy as np, pandas as pd, lightgbm as lgb
from comun import TRABAJO
from variables import cargar, comunes, matriz, categorias_union, SOLO_EMERGENTE, MARKETING, TARIFA, MAKE
from completitud import por_peligro
OUT = "/home/claude/m017/revision"
def dev(y, m): return 4 * y / np.sqrt(m) + 4 * np.sqrt(m) - 8 * np.sqrt(y)
def kopt(y, m): return np.sum(y / np.sqrt(m)) / np.sum(np.sqrt(m))
PF = dict(objective="poisson", learning_rate=0.08, num_leaves=31, min_data_in_leaf=1000, feature_fraction=0.8, bagging_fraction=0.8,
          bagging_freq=1, lambda_l2=10.0, max_cat_to_onehot=8, cat_smooth=50, verbose=-1, num_threads=2, seed=20261026)
PS = dict(objective="gamma", learning_rate=0.05, num_leaves=15, min_data_in_leaf=200, feature_fraction=0.8, bagging_fraction=0.8,
          bagging_freq=1, lambda_l2=10.0, max_cat_to_onehot=8, cat_smooth=50, verbose=-1, num_threads=2, seed=20261026)
def fit(X, y, off, p, val, w=None):
    dtr = lgb.Dataset(X[~val], y[~val], init_score=off[~val], weight=None if w is None else w[~val], free_raw_data=False)
    dvl = lgb.Dataset(X[val], y[val], init_score=off[val], weight=None if w is None else w[val], reference=dtr)
    b = lgb.train(p, dtr, 2000, valid_sets=[dvl], callbacks=[lgb.early_stopping(50, verbose=False)])
    n = max(b.best_iteration, 1); return lgb.train(p, lgb.Dataset(X, y, init_score=off, weight=w), n), n
W = {"motor": 0.25, "buildings": 0.25, "contents": 0.5}
res = {}
for l in sys.argv[1:] or ["buildings", "contents", "motor"]:
    t0 = time.time()
    em = cargar("emerging", l, "hasta2023"); dva = cargar("developed", l, "hasta2023")
    assert (dva.market == "developed").all() and (em.market == "emerging").all()
    dv = dva[dva.year.isin([2021, 2022, 2023])].reset_index(drop=True); d24 = dva[dva.year == 2024].reset_index(drop=True); del dva
    cn = pd.read_parquet(TRABAJO / f"conteos_developed_{l}.parquet")
    dv = dv.merge(cn, on="row_id", how="left"); d24 = d24.merge(cn, on="row_id", how="left")
    cols = comunes(l)
    cats = categorias_union([dv, em], cols + ["hist_pol_12m", "hist_cli_12m", "new_business", "renewal_count", "prior_claims_5y"])
    Xd, Xe, X24 = matriz(dv, cols, cats), matriz(em, cols, cats), matriz(d24, cols, cats); val = dv.fold.values == 0
    perils = sorted(c[2:] for c in cn.columns if c.startswith("n_"))
    aut = pd.read_parquet(f"{TRABAJO}/pred/fsp/{l}.parquet").set_index("row_id").loc[em.row_id]
    chk = {}; comp24 = np.zeros(len(d24)); comp24_ult = {}
    for p in perils:
        n = dv[f"n_{p}"].values.astype(float); yp = dv[f"y_{p}"].values
        cp = np.maximum(por_peligro(l, p, dv.period_start, dv.period_end), 1e-4)
        off = np.log(dv.exposure.values * cp); b0 = float(np.log(n.sum() / np.exp(off).sum())); off = off + b0
        bf, nf = fit(Xd, n, off, PF, val)
        s = (n > 0) & (yp > 0); msev = float(yp[s].sum() / n[s].sum())
        bs, ns = fit(Xd[s].reset_index(drop=True), yp[s] / n[s], np.full(s.sum(), np.log(msev)), PS, val[s], w=n[s])
        fe = np.exp(bf.predict(Xe, raw_score=True) + b0) * em.exposure.values; se = np.exp(bs.predict(Xe, raw_score=True) + np.log(msev))
        # comprobación del desplazamiento inicial: Σ f·cp en el entrenamiento = Σ n
        ftr = np.exp(bf.predict(Xd, raw_score=True) + off)
        chk[p] = {"rondas_f": nf, "rondas_s": ns, "corr_log_f_autor": round(float(np.corrcoef(np.log(fe), np.log(aut[f"f_{p}"].values))[0, 1]), 5),
                  "ratio_f_autor": round(float(fe.sum() / aut[f"f_{p}"].values.sum()), 5),
                  "corr_log_s_autor": round(float(np.corrcoef(np.log(se), np.log(aut[f"s_{p}"].values))[0, 1]), 5) if np.std(np.log(se)) > 0 else None,
                  "ratio_s_autor": round(float(se.mean() / aut[f"s_{p}"].values.mean()), 5),
                  "sum_f_cp_entren/sum_n": round(float(ftr.sum() / n.sum()), 5)}
        cp24 = por_peligro(l, p, d24.period_start, d24.period_end)
        comp24 += np.exp(bf.predict(X24, raw_score=True) + b0) * d24.exposure.values * cp24 * np.exp(bs.predict(X24, raw_score=True) + np.log(msev))
        print(l, p, chk[p], round(time.time() - t0), flush=True)
    # desarrollado 2024: T2b (modelo guardado, entrenado 2021-2023) frente a mezcla con la FSp
    t2 = lgb.Booster(model_file=str(TRABAJO / "modelos/dev" / f"T2b_{l}.txt"))
    cats2 = categorias_union([dv, em], cols + SOLO_EMERGENTE + MARKETING + TARIFA + MAKE)
    e = d24.exposure.values * d24.c_fila.values; mT = np.exp(t2.predict(matriz(d24, cols, cats2), raw_score=True)) * e
    y = d24.y.values; nb = d24.new_business.values.astype(bool); full = d24.exposure.values >= 0.9
    r = {}
    for seg, msk in (("REN", ~nb), ("NB", nb), ("NB_anio_completo", nb & full), ("NB_parcial", nb & ~full), ("REN_anio_completo", ~nb & full)):
        yy, a, b_ = y[msk], mT[msk], comp24[msk]
        null = dev(yy, np.full(len(yy), yy.mean())).sum()
        def d2(m): return 1 - dev(yy, m * kopt(yy, m)).sum() / null
        base = d2(a); rr = {"n": int(msk.sum()), "pos": int((yy > 0).sum()), "D2_T2b": round(base, 5), "D2_FSp": round(d2(b_), 5)}
        for w in (0.1, 0.25, 0.5, 0.75):
            bb = b_ * a.sum() / b_.sum(); m = np.exp((1 - w) * np.log(a) + w * np.log(bb))
            rr[f"gan_w{w}"] = round(d2(m) - base, 5)
            x = np.log(a / e[msk]); yv = np.log(bb / e[msk]); beta = np.cov(x, yv)[0, 1] / np.var(x, ddof=1)
            mc = e[msk] * (a / e[msk]) ** (1 - w + w * beta); rr[f"gan_comp_w{w}"] = round(d2(mc) - base, 5)
        # bootstrap por cliente de la ganancia a w de la línea
        cid = d24.customer_id.values[msk]; u, inv = np.unique(cid, return_inverse=True); rng = np.random.default_rng(5); bs = []
        w = W[l]; bb = b_ * a.sum() / b_.sum(); m = np.exp((1 - w) * np.log(a) + w * np.log(bb))
        for _ in range(200):
            cw = rng.multinomial(len(u), np.full(len(u), 1 / len(u)))[inv].astype(float)
            def d2w(mm): k = np.sum(cw * yy / np.sqrt(mm)) / np.sum(cw * np.sqrt(mm)); ym = np.sum(cw * yy) / cw.sum(); return 1 - np.sum(cw * dev(yy, k * mm)) / np.sum(cw * dev(yy, np.full(len(yy), ym)))
            bs.append(d2w(m) - d2w(a))
        rr["boot_gan_w_linea"] = [round(float(np.quantile(bs, q)), 5) for q in (0.05, 0.5, 0.95)]
        r[seg] = rr
    res[l] = {"comprobacion": chk, "desarrollado_2024": r}
    print(l, json.dumps(r, indent=0), flush=True)
    json.dump(res, open(f"{OUT}/K_t1c_fsp_reentreno_{'_'.join(sys.argv[1:]) or 'todo'}.json", "w"), indent=1, default=float)
