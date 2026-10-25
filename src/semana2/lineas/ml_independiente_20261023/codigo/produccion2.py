"""Producción 2025 de MLind v2 (E14-E21): mezcla convexa por ramo de troncos transferidos, nivel C1, sin tendencia.

Uso: python3 produccion2.py <nombre> <encoge> comp1 [comp2 ...]
- Pesos por ramo con el OOF de 2023-2024 (fase pcv), encogidos hacia pesos iguales en la fracción <encoge>.
- Nivel C1: factor Tweedie por ramo de la mezcla en el OOF pcv (igual que produccion.py).
- Escribe privado/prediccion_2025_<nombre>.csv, la combinación 50/50 con la designada y entrega/produccion_<nombre>.json.
"""
import sys
import numpy as np, pandas as pd
from comun import *
from evaluar import mezcla_pesos, metricas
import receta

NOM, ENC, COMPS = sys.argv[1], float(sys.argv[2]), sys.argv[3:]
PRIV = RAIZ / "privado"
DESIGNADA = RAIZ / "comparacion" / "otros" / "A1fixF1b3n_2025.csv"
SHA_DESIGNADA = "f786deb3"


def pesos(t, P, il):
    M = np.column_stack([P[c][il] * t.c_fila.values[il] for c in COMPS])
    w = mezcla_pesos(t.y.values[il], M) if len(COMPS) > 1 else np.ones(1)
    return (1 - ENC) * w + ENC / len(COMPS)


def controles(out, sub):
    c = {"filas": int(len(out)), "orden_igual_plantilla": bool((out.row_id.values == sub.row_id.values).all()),
         "nulos": int(out.prediction.isna().sum()), "min": float(out.prediction.min()),
         "positivas_estrictas": bool((out.prediction > 0).all()), "ids_unicos": bool(out.row_id.is_unique)}
    assert c["filas"] == 209063 and c["nulos"] == 0 and c["positivas_estrictas"] and c["orden_igual_plantilla"], c
    return c


tp = receta.tabla("pcv"); Pp = receta.componentes("pcv", COMPS, tp)
tt = receta.tabla("prod"); Pt = receta.componentes("prod", COMPS, tt)
mu = np.zeros(len(tt)); params = {}
# OOF cruzado de la receta en 2023-2024 (pesos y nivel fuera del pliegue) para medir y para el balance
folds = pliegue(tp.customer_id.values); oof = np.zeros(len(tp))
for l in LINEAS:
    il = (tp.line == l).values; it = (tt.line == l).values
    w = pesos(tp, Pp, il)
    b = np.column_stack([Pp[c][il] for c in COMPS]) @ w
    k = factor_tweedie(tp.y.values[il], b * tp.c_fila.values[il])
    mu[it] = (np.column_stack([Pt[c][it] for c in COMPS]) @ w) * k
    params[l] = {"pesos": dict(zip(COMPS, np.round(w, 4).tolist())), "k_ramo": k}
    for f in range(5):
        te = folds == f
        tr_ = tp[~te].reset_index(drop=True)
        wf = pesos(tr_, {c: Pp[c][~te] for c in COMPS}, il[~te])
        bf = np.column_stack([Pp[c] for c in COMPS]) @ wf
        kf = factor_tweedie(tp.y.values[~te & il], bf[~te & il] * tp.c_fila.values[~te & il])
        oof[te & il] = bf[te & il] * kf
sub = pd.read_parquet(DATOS / "emerging" / "sample_submission.parquet")
out = sub[["row_id"]].merge(pd.DataFrame({"row_id": tt.row_id.values, "prediction": mu}), on="row_id", how="left")
res = {"componentes": COMPS, "encoge": ENC, "params": params, "controles": controles(out, sub)}
f = PRIV / f"prediccion_2025_{NOM}.csv"
out.to_csv(f, index=False, float_format="%.6f", lineterminator="\n")
res["controles"]["sha256"] = sha256(f); res["controles"]["archivo"] = f.name
tot = {}
for l in LINEAS:
    i = (tt.line == l).values; e = tt.exposure.values[i]; nb = tt.new_business.values[i]
    tot[l] = {"total": float(mu[i].sum()), "tasa": float(mu[i].sum() / e.sum()),
              "tasa_NB": float(mu[i][nb].sum() / e[nb].sum()), "tasa_REN": float(mu[i][~nb].sum() / e[~nb].sum())}
res["totales"] = tot; res["total"] = float(mu.sum())
res["oof_pcv"] = metricas(tp, oof)
res["balance_oof_pcv"] = {l: float(tp.y[(tp.line == l).values].sum() / (oof * tp.c_fila.values)[(tp.line == l).values].sum()) for l in LINEAS}
# combinación 50/50 con la designada (misma regla que MEZCLA.md)
assert sha256(DESIGNADA).startswith(SHA_DESIGNADA)
d = pd.read_csv(DESIGNADA)
assert (d.row_id.values == sub.row_id.values).all()
m50 = pd.DataFrame({"row_id": sub.row_id.values, "prediction": 0.5 * d.prediction.values + 0.5 * out.prediction.values})
f50 = PRIV / f"mezcla50_designada_{NOM}_2025.csv"
m50.to_csv(f50, index=False, float_format="%.6f", lineterminator="\n")
res["mezcla50"] = {**controles(m50, sub), "sha256": sha256(f50), "archivo": f50.name, "total": float(m50.prediction.sum())}
lm = np.log(out.prediction.values); ld = np.log(d.prediction.values)
res["frente_designada"] = {"corr_log": float(np.corrcoef(lm, ld)[0, 1]), "cociente_p01_p99": [
    float(np.quantile(np.exp(lm - ld), 0.01)), float(np.quantile(np.exp(lm - ld), 0.99))]}
v1 = pd.read_csv(PRIV / "prediccion_2025_mlind.csv")
lv = np.log(v1.prediction.values)
res["frente_mlind_v1"] = {"corr_log": float(np.corrcoef(lm, lv)[0, 1]), "total_v1": float(v1.prediction.sum())}
guardar_json(res, ENTREGA / f"produccion_{NOM}.json")
print(NOM, round(res["total"]), {l: round(v["tasa"], 1) for l, v in tot.items()}, res["controles"]["sha256"][:12],
      "OOF pcv D2 %.4f" % res["oof_pcv"]["D2"], "corr designada %.4f v1 %.4f" % (res["frente_designada"]["corr_log"], res["frente_mlind_v1"]["corr_log"]))
