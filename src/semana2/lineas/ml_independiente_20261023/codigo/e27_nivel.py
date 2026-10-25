"""E27: nivel 2025 por ramo y segmento con la siniestralidad esperada sobre la prima escrita (preinscripción
entrega/nivel2025/PREINSCRIPCION_NIVEL.md, SHA 13d2ef2f…). Sin tablero.

Salida: entrega/nivel2025/e27_nivel.json y privado/e27_nivel_2025.csv (base × f_s).
"""
import json, hashlib
import numpy as np, pandas as pd
from comun import *
from scipy.stats import spearmanr

PRE = ENTREGA / "nivel2025" / "PREINSCRIPCION_NIVEL.md"
assert sha256(PRE).startswith("13d2ef2f1596621f"), "la preinscripción cambió"
BASE = RAIZ / "privado" / "mezcla50_designada_mlind_2025.csv"
assert sha256(BASE).startswith("12831ef4a05c1773"), "la base no es la mezcla enviada"
TAU, K, TOPE, B_BOOT, SEM = 0.07, 200.0, (0.85, 1.15), 1000, 20261024

filas = []
for l in LINEAS:
    b = pd.read_parquet(TRABAJO / f"base_emerging_{l}.parquet",
                        columns=["row_id", "customer_id", "year", "conjunto", "y", "n_sin", "c_fila", "exposure",
                                 "written_premium", "new_business"])
    filas.append(b.assign(line=l))
d = pd.concat(filas, ignore_index=True)
d["seg"] = d.line + "|" + np.where(d.new_business, "NB", "REN")
d["P"] = d.written_premium * d.exposure
h = d[(d.conjunto == "train") & d.year.isin([2023, 2024])].reset_index(drop=True)
h["U"] = h.y / h.c_fila
t = d[d.conjunto == "test"].reset_index(drop=True)
base = pd.read_csv(BASE)
t = t.merge(base, on="row_id", how="left"); assert t.prediction.notna().all() and len(t) == 209063
SEGS = sorted(h.seg.unique())


def lr_estrella(hh, w=None, k=K):
    w = np.ones(len(hh)) if w is None else w
    out, raw = {}, {}
    for l in LINEAS:
        il = (hh.line == l).values
        lr_l = np.sum(w[il] * hh.U.values[il]) / np.sum(w[il] * hh.P.values[il])
        for s in ("NB", "REN"):
            m = il & (hh.seg == f"{l}|{s}").values
            lr_s = np.sum(w[m] * hh.U.values[m]) / np.sum(w[m] * hh.P.values[m])
            n = np.sum(w[m] * hh.n_sin.values[m]); z = n / (n + k)
            out[f"{l}|{s}"] = z * lr_s + (1 - z) * lr_l; raw[f"{l}|{s}"] = (lr_s, lr_l, n, z)
    return out, raw


def factores(hh, tt, tau=TAU, k=K, boot=True):
    lrs, raw = lr_estrella(hh, k=k)
    # varianza bootstrap por cliente (pesos de Poisson)
    cli, idx = np.unique(hh.customer_id.values, return_inverse=True)
    rng = np.random.default_rng(SEM)
    sims = {s: [] for s in SEGS}
    if boot:
        for _ in range(B_BOOT):
            w = rng.poisson(1.0, len(cli))[idx].astype(float)
            o, _ = lr_estrella(hh, w, k=k)
            for s in SEGS:
                sims[s].append(np.log(o[s]))
    res = {}
    for s in SEGS:
        l = s.split("|")[0]
        yr = {}
        for a in (2023, 2024):
            m = (hh.seg == s).values & (hh.year == a).values
            yr[a] = hh.U.values[m].sum() / hh.P.values[m].sum()
        var_boot = float(np.var(sims[s])) if boot else np.nan
        var_anio = 0.5 * (np.log(yr[2024]) - np.log(yr[2023])) ** 2
        sig2 = var_boot + var_anio
        mt = (tt.seg == s).values
        P25 = tt.P.values[mt].sum(); Bs = tt.prediction.values[mt].sum()
        E = lrs[s] * P25; g = E / Bs
        z = tau ** 2 / (tau ** 2 + sig2)
        f = float(np.clip(np.exp(z * np.log(g)), *TOPE))
        res[s] = {"LR_segmento": raw[s][0], "LR_ramo": raw[s][1], "siniestros": raw[s][2], "Z_n": raw[s][3],
                  "LR_estrella": lrs[s], "LR_2023": yr[2023], "LR_2024": yr[2024], "var_boot": var_boot,
                  "var_anio": var_anio, "sigma": float(np.sqrt(sig2)), "P25": P25, "base_total": Bs, "E_tarifa": E,
                  "g": g, "Z": z, "f": f, "filas_2025": int(mt.sum())}
    return res


R = factores(h, t)
out = {"preinscripcion_sha256": sha256(PRE), "base_sha256": sha256(BASE), "tau": TAU, "K": K, "tope": TOPE, "segmentos": R}
for s, r in R.items():
    print(s, "LR %.3f (2023 %.3f, 2024 %.3f) LR* %.3f | g %.3f sigma %.3f Z %.3f -> f %.4f" % (
        r["LR_segmento"], r["LR_2023"], r["LR_2024"], r["LR_estrella"], r["g"], r["sigma"], r["Z"], r["f"]))

# sensibilidades (sin bootstrap nuevo para K: se reutiliza la varianza del caso central)
sens = {}
for tau in (0.05, 0.10):
    sens[f"tau_{tau}"] = {s: float(np.clip(np.exp(tau ** 2 / (tau ** 2 + R[s]["sigma"] ** 2) * np.log(R[s]["g"])), *TOPE)) for s in SEGS}
for k in (100.0, 400.0):
    Rk = factores(h, t, k=k, boot=True)
    sens[f"K_{int(k)}"] = {s: Rk[s]["f"] for s in SEGS}
out["sensibilidad"] = sens
print("sens", json.dumps({a: {s: round(v, 4) for s, v in b.items()} for a, b in sens.items()}))

# entrega E27: base × f_s
t["f"] = t.seg.map({s: R[s]["f"] for s in SEGS})
sub = pd.read_parquet(DATOS / "emerging" / "sample_submission.parquet")
o = sub[["row_id"]].merge(t[["row_id", "prediction", "f"]], on="row_id", how="left")
o["prediction"] = o.prediction * o.f
o = o[["row_id", "prediction"]]
assert len(o) == 209063 and (o.row_id.values == sub.row_id.values).all() and o.prediction.notna().all() and (o.prediction > 0).all()
f_out = RAIZ / "privado" / "e27_nivel_2025.csv"
o.to_csv(f_out, index=False, float_format="%.6f", lineterminator="\n")
out["entrega"] = {"archivo": f_out.name, "sha256": sha256(f_out), "total": float(o.prediction.sum()),
                  "total_base": float(base.prediction.sum()),
                  "por_ramo": {l: float(o.prediction.values[t.set_index("row_id").loc[o.row_id, "line"].values == l].sum()) for l in LINEAS}}
print("entrega", out["entrega"])

# diagnóstico: orden de riesgo de la tarifa frente a la predicción base, nuevo negocio 2025 y 2023-2024 (T2b OOF pcv)
pcv = pd.concat([pd.read_parquet(TRABAJO / "pred" / "pcv" / f"T2b_{l}.parquet") for l in LINEAS])
hh = h.merge(pcv, on="row_id", how="left")
diag = {}
for l in LINEAS:
    for s in ("NB", "REN"):
        m25 = (t.seg == f"{l}|{s}").values; m23 = (hh.seg == f"{l}|{s}").values
        diag[f"{l}|{s}"] = {
            "spearman_2025": float(spearmanr(t.written_premium.values[m25], t.prediction.values[m25] / t.exposure.values[m25])[0]),
            "spearman_2023_24": float(spearmanr(hh.written_premium.values[m23], hh.mu.values[m23] / hh.exposure.values[m23])[0]),
            "prima_media_2025": float(t.written_premium.values[m25].mean()),
            "prima_media_2023_24": float(hh.written_premium.values[m23].mean()),
            "base_por_exposicion_2025": float(t.prediction.values[m25].sum() / t.exposure.values[m25].sum()),
            "T2b_por_exposicion_2023_24": float(hh.mu.values[m23].sum() / hh.exposure.values[m23].sum())}
out["diagnostico_orden"] = diag
print("orden", json.dumps({s: {k: round(v, 3) for k, v in d_.items()} for s, d_ in diag.items()}))
guardar_json(out, ENTREGA / "nivel2025" / "e27_nivel.json")
