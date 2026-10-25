"""T6 (E05): transferencia por peligro con nivel emergente por peligro y credibilidad.

Uso: python peligros.py fase
"""
from __future__ import annotations
import sys, time
import numpy as np, pandas as pd, lightgbm as lgb
from comun import *
from variables import *
from completitud import por_peligro
from gbm import P_DEV, ajustar, CONF, MOD, OUT

PELIGROS = {"motor": ["bodily_injury", "glass_hail", "own_damage", "theft", "third_party_prop"],
            "buildings": ["accidental_damage", "escape_of_water", "fire", "flood", "storm", "subsidence"],
            "contents": ["accidental_damage", "escape_of_water", "flood", "theft"]}
KCRED = 100.0
FASE = sys.argv[1] if len(sys.argv) > 1 else "dev"

for l in LINEAS:
    t0 = time.time()
    em = cargar("emerging", l, CONF["clima"]); dv = cargar("developed", l, CONF["clima"])
    dv = dv[dv.year.isin(CONF["dev_years"])].reset_index(drop=True)
    cols = comunes(l); cats = categorias_union([dv, em], cols + SOLO_EMERGENTE + MARKETING + TARIFA + MAKE)
    Xd = matriz(dv, cols, cats); Xe = matriz(em, cols, cats)
    raw = {}; rondas = {}; kdevs = {}
    for p in PELIGROS[l]:
        f = MOD / f"T6_{l}_{p}.txt"
        cd = por_peligro(l, p, dv.period_start, dv.period_end)
        offd = np.log(dv.exposure.values * np.maximum(cd, 1e-4))
        if f.exists():
            b = lgb.Booster(model_file=str(f)); n = b.current_iteration()
        else:
            b, n = ajustar(Xd, dv[f"y_{p}"].values, offd, P_DEV, 4000, es=100, val=dv.fold.values == 0)
            b.save_model(str(f))
        rondas[p] = n
        # reajuste del nivel de cada peligro en el propio desarrollado (la L2 con Tweedie lo sesga a la baja)
        kdev = factor_tweedie(dv[f"y_{p}"].values, np.exp(b.predict(Xd, raw_score=True) + offd))
        kdevs[p] = kdev
        raw[p] = b.predict(Xe, raw_score=True) + np.log(kdev)
        em[f"c_{p}"] = np.where(em.conjunto == "test", 1.0, por_peligro(l, p, em.period_start, em.period_end))
    for p in PELIGROS[l]:
        em[f"raw_{p}"] = raw[p]
    em[[c for c in em.columns if c.startswith("raw_") or c == "row_id"]].to_parquet(OUT / f"T6raw_{l}.parquet", index=False)
    tr = em[(em.conjunto == "train") & em.year.isin(CONF["em_train"])].reset_index(drop=True)
    sets = [(tr[tr.fold != k], tr[tr.fold == k]) for k in range(5)] if CONF["em_eval"] is None else \
        [(tr, em[em.year == CONF["em_eval"]].reset_index(drop=True))]
    preds = []; niveles = []
    for a, b in sets:
        # nivel común del ramo
        mu_a = sum(np.exp(a[f"raw_{p}"].values) * a.exposure.values * a[f"c_{p}"].values for p in PELIGROS[l])
        kl = factor_tweedie(a.y.values, mu_a)
        kp = {}
        for p in PELIGROS[l]:
            m = np.exp(a[f"raw_{p}"].values) * a.exposure.values * a[f"c_{p}"].values * kl
            kem = factor_tweedie(a[f"y_{p}"].values, m)
            n = int((a[f"y_{p}"].values > 0).sum()); z = n / (n + KCRED)
            kp[p] = kl * (z * kem + (1 - z))
        niveles.append({"k_ramo": kl, **{p: kp[p] for p in kp}})
        mu = sum(kp[p] * np.exp(b[f"raw_{p}"].values) for p in PELIGROS[l]) * b.exposure.values
        preds.append(pd.DataFrame({"row_id": b.row_id.values, "mu": mu}))
    pd.concat(preds).to_parquet(OUT / f"T6_{l}.parquet", index=False)
    guardar_json({"rondas": rondas, "k_desarrollado": kdevs, "niveles": niveles, "s": round(time.time() - t0)}, OUT / f"T6_{l}_meta.json")
    print(l, rondas, [{k: round(v, 3) for k, v in n.items()} for n in niveles][:2], round(time.time() - t0), "s", flush=True)
