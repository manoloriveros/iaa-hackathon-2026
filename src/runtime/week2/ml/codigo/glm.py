"""G1: emerging-only log-link power-1.5 Tweedie GLM with binned features and internally selected ridge."""
import sys
import numpy as np, pandas as pd
from comun import *
from variables import *
from adaptacion import ajustar, interno

FASE = sys.argv[1] if len(sys.argv) > 1 else "dev"
CONF = {"dev": ("hasta2023", [2023], None), "hold": ("hasta2023", [2023], 2024), "prod": ("hasta2024", [2023, 2024], 2025),
        "pcv": ("hasta2024", [2023, 2024], None)}[FASE]
OUT = TRABAJO / "pred" / FASE
LAMBDAS = [1e2, 1e3, 1e4, 3e4, 1e5, 3e5, 1e6]


def diseno(df, cols, ref=None):
    """Encode categorical levels and training-based numeric quintiles, with an explicit missing level."""
    ref = {} if ref is None else ref
    bloques = []; nombres = []
    for c in cols:
        if c in CATEGORICAS or df[c].dtype == bool or df[c].nunique() <= 6:
            v = df[c].astype(object).where(df[c].notna(), "NA").astype(str).values
            if c not in ref:
                ref[c] = ("cat", sorted(set(v)))
        else:
            x = pd.to_numeric(df[c], errors="coerce").astype(float).values
            if c not in ref:
                q = np.unique(np.nanquantile(x, [0.2, 0.4, 0.6, 0.8])) if np.isfinite(x).any() else np.array([])
                ref[c] = ("num", q)
            q = ref[c][1]
            v = np.where(np.isnan(x), "NA", np.searchsorted(q, x, side="right").astype(str)).astype(str)
            if ref[c][0] == "num" and len(ref[c]) == 2:
                ref[c] = ("num", q, sorted(set(v)))
        niveles = ref[c][1] if ref[c][0] == "cat" else ref[c][2]
        for n in niveles:
            bloques.append((v == n).astype(np.float32)); nombres.append(f"{c}={n}")
    return np.column_stack(bloques), nombres, ref


for l in LINEAS:
    em = cargar("emerging", l, CONF[0])
    cols = [c for c in comunes(l) + SOLO_EMERGENTE]
    tr = em[(em.conjunto == "train") & em.year.isin(CONF[1])].reset_index(drop=True)
    sets = [(tr[tr.fold != k], tr[tr.fold == k]) for k in range(5)] if CONF[2] is None else [(tr, em[em.year == CONF[2]].reset_index(drop=True))]
    preds = []; lams = []
    for a, b in sets:
        Za, nom, ref = diseno(a, cols); Zb, _, _ = diseno(b, cols, ref)
        offa = np.log(a.exposure.values * a.c_fila.values); offb = np.log(b.exposure.values)
        ya = a.y.values; v = interno(a.customer_id.values)
        best = None
        for lam in LAMBDAS:
            bt = ajustar(Za[~v], ya[~v], offa[~v], lam)
            dv_ = desviacion(ya[v], np.exp(offa[v] + bt[0] + Za[v] @ bt[1:])).sum()
            if best is None or dv_ < best[0]:
                best = (dv_, lam)
        lams.append(best[1])
        bt = ajustar(Za, ya, offa, best[1])
        mu_a = np.exp(offa + bt[0] + Za @ bt[1:])
        kin = factor_tweedie(ya, mu_a)
        preds.append(pd.DataFrame({"row_id": b.row_id.values, "mu": kin * np.exp(offb + bt[0] + Zb @ bt[1:])}))
    pd.concat(preds).to_parquet(OUT / f"G1_{l}.parquet", index=False)
    print(l, "lambdas", lams, flush=True)
