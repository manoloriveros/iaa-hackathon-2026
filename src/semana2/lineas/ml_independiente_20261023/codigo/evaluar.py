"""Métricas de la línea ML independiente sobre predicciones guardadas."""
from __future__ import annotations
import sys
import numpy as np, pandas as pd
from comun import *

def tabla_eval(fase, anio):
    filas = []
    for l in LINEAS:
        b = pd.read_parquet(TRABAJO / f"base_emerging_{l}.parquet",
                            columns=["row_id", "y", "c_fila", "exposure", "customer_id", "year", "new_business", "conjunto"])
        b = b[(b.conjunto == "train") & (b.year == anio)]
        filas.append(b.assign(line=l))
    return pd.concat(filas, ignore_index=True)


def cargar_pred(fase, cand):
    out = []
    for l in LINEAS:
        f = TRABAJO / "pred" / fase / f"{cand}_{l}.parquet"
        if not f.exists():
            return None
        out.append(pd.read_parquet(f))
    return pd.concat(out, ignore_index=True)


def cuerpo_mask(t, q=0.995):
    m = np.ones(len(t), bool)
    for l in LINEAS:
        i = (t.line == l).values & (t.y.values > 0)
        thr = np.quantile(t.y.values[i], q)
        m &= ~((t.line == l).values & (t.y.values > thr))
    return m


def metricas(t, mu, w=None):
    y = t.y.values; m = mu * t.c_fila.values
    r = {"D2": d2(y, m, w)}
    if "w2025" in t:
        r["D2_w2025"] = d2(y, m, t.w2025.values)
    for l in LINEAS:
        i = (t.line == l).values
        r[f"D2_{l}"] = d2(y[i], m[i], None if w is None else w[i])
        r[f"AE_{l}"] = float(y[i].sum() / m[i].sum())
    cm = cuerpo_mask(t)
    mb = m.copy()
    for l in LINEAS:
        i = cm & (t.line == l).values
        mb[i] *= y[i].sum() / m[i].sum()
    r["D2_cuerpo"] = d2(y[cm], mb[cm])
    for nb in (True, False):
        i = t.new_business.values == nb
        r[f"AE_{'NB' if nb else 'REN'}"] = float(y[i].sum() / m[i].sum())
    return r


if __name__ == "__main__":
    fase = sys.argv[1]; anio = 2023 if fase == "dev" else 2024
    t = tabla_eval(fase, anio)
    filas = []
    for f in sorted((TRABAJO / "pred" / fase).glob("*_motor.parquet")):
        cand = f.name.replace("_motor.parquet", "")
        p = cargar_pred(fase, cand)
        if p is None: continue
        mu = t[["row_id"]].merge(p, on="row_id", how="left").mu.values
        if np.isnan(mu).any(): continue
        filas.append({"cand": cand, **metricas(t, mu)})
    df = pd.DataFrame(filas).set_index("cand").sort_values("D2", ascending=False)
    pd.set_option("display.width", 250)
    print(df.round(4))


def calibrar_cruzado(t, mu, folds, por_nb=False, K=200.0):
    """A01/E04: factor Tweedie por ramo (y opcionalmente por ramo x nuevo negocio con credibilidad),
    estimado en los otros pliegues y aplicado al pliegue retenido."""
    m = mu * t.c_fila.values; y = t.y.values
    out = mu.copy()
    for k in np.unique(folds):
        te = folds == k; trm = ~te
        for l in LINEAS:
            il = (t.line == l).values
            kl = factor_tweedie(y[trm & il], m[trm & il])
            if not por_nb:
                out[te & il] = mu[te & il] * kl
            else:
                for nb in (True, False):
                    s = (t.new_business.values == nb)
                    ks = factor_tweedie(y[trm & il & s], m[trm & il & s] * kl)
                    nsin = np.sum((y[trm & il & s] > 0))
                    z = nsin / (nsin + K)
                    out[te & il & s] = mu[te & il & s] * kl * (z * ks + (1 - z))
    return out


def tabla_dev(cands, por_nb=False):
    t = tabla_eval("dev", 2023)
    t = t.merge(pd.read_parquet(TRABAJO / "pesos_2025_dev.parquet"), on="row_id", how="left")
    from comun import pliegue
    folds = pliegue(t.customer_id.values)
    filas = []
    for c in cands:
        p = cargar_pred("dev", c)
        if p is None: continue
        mu = t[["row_id"]].merge(p, on="row_id", how="left").mu.values
        filas.append({"cand": c, "calib": "sin", **metricas(t, mu)})
        filas.append({"cand": c, "calib": "ramo", **metricas(t, calibrar_cruzado(t, mu, folds))})
        if por_nb:
            filas.append({"cand": c, "calib": "ramo_nb", **metricas(t, calibrar_cruzado(t, mu, folds, True))})
    return pd.DataFrame(filas)


def mezcla_pesos(Y, M):
    """Pesos convexos que minimizan la desviación Tweedie 1,5 de M @ w (M: n x k ya en escala observada)."""
    from scipy.optimize import minimize
    k = M.shape[1]
    if k == 1:
        return np.ones(1)
    def f(w):
        mu = np.maximum(M @ w, 1e-9)
        return np.sum(2 * (2 * Y / np.sqrt(mu) + 2 * np.sqrt(mu))), M.T @ (2 * (-Y / mu ** 1.5 + 1 / np.sqrt(mu)))
    cons = ({"type": "eq", "fun": lambda w: w.sum() - 1, "jac": lambda w: np.ones(k)},)
    r = minimize(f, np.ones(k) / k, jac=True, method="SLSQP", bounds=[(0, 1)] * k, constraints=cons)
    return np.clip(r.x, 0, 1) / np.clip(r.x, 0, 1).sum()


def mezcla_cruzada(t, preds, folds):
    """Pesos por ramo estimados en cuatro pliegues y aplicados al quinto. preds: dict cand -> mu (alineado con t)."""
    nombres = list(preds)
    M = np.column_stack([preds[c] * t.c_fila.values for c in nombres])
    U = np.column_stack([preds[c] for c in nombres])
    y = t.y.values; out = np.zeros(len(t)); pesos = []
    for k in np.unique(folds):
        te = folds == k
        for l in LINEAS:
            il = (t.line == l).values
            w = mezcla_pesos(y[~te & il], M[~te & il])
            out[te & il] = U[te & il] @ w
            pesos.append({"pliegue": int(k), "ramo": l, **dict(zip(nombres, np.round(w, 4)))})
    return out, pesos


def bootstrap_dif(t, mu_a, mu_b, B=1000, semilla=2026, w=None):
    """Diferencia de D2 (a - b) con remuestreo de clientes (pesos de Poisson). Devuelve media, IC95 y P(a>b)."""
    rng = np.random.default_rng(semilla)
    cli, idx = np.unique(t.customer_id.values, return_inverse=True)
    y = t.y.values; ma = mu_a * t.c_fila.values; mb = mu_b * t.c_fila.values
    base = np.ones(len(y)) if w is None else w
    da = desviacion(y, ma); db = desviacion(y, mb)
    sy = np.sqrt(y)
    res = []
    for s in range(0, B, 100):
        Wc = rng.poisson(1.0, size=(min(100, B - s), len(cli))).astype(float)
        W = Wc[:, idx] * base
        ybar = (W @ y) / W.sum(1)
        dn = 2 * ((W @ sy) / (-0.25) - (W @ y) * ybar ** -0.5 / (-0.5) + W.sum(1) * ybar ** 0.5 / 0.5)
        res.append((1 - (W @ da) / dn) - (1 - (W @ db) / dn))
    r = np.concatenate(res)
    return {"dif": float(d2(y, ma, w) - d2(y, mb, w)), "ic95": [float(np.quantile(r, 0.025)), float(np.quantile(r, 0.975))],
            "p_mayor": float(np.mean(r > 0))}
