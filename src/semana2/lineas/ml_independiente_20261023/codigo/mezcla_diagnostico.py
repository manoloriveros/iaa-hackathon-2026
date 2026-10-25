"""Diagnósticos de la combinación 50/50 designada + MLind (PREINSCRIPCION_MEZCLA.md). No cambian el archivo."""
import json
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.isotonic import IsotonicRegression
from comun import *
import receta

OTROS = RAIZ / "comparacion" / "otros"; OUT = RAIZ / "mezcla"
res = {"fuentes": {f: sha256(p) for f, p in {"designada": OTROS / "A1fixF1b3n_2025.csv", "mlind": PRIVADO / "prediccion_2025_mlind.csv",
       "mezcla": PRIVADO / "mezcla50_designada_mlind_2025.csv", "pred2024_noct": OTROS / "predicciones_2024.parquet"}.items()}}
# ------------------------------------------------ 2024
o = pd.read_parquet(OTROS / "predicciones_2024.parquet")
p = receta.parametros("dev", ["T2b"], "ramo"); t, mu = receta.aplicar("hold", p, None)
d = t.merge(o[["row_id", "address_id", "A1"]], on="row_id")
assert len(d) == 59202
d["T2b"] = mu * t.c_fila.values
y = d.y.values; A = d.A1.values; T = d.T2b.values
d["ari"] = 0.5 * A + 0.5 * T; d["geo"] = np.sqrt(A * T)
padre = {}
def f(x):
    while padre.setdefault(x, x) != x:
        padre[x] = padre[padre[x]]; x = padre[x]
    return x
for c, a in zip("C" + d.customer_id, "A" + d.address_id):
    rc, ra = f(c), f(a)
    if rc != ra: padre[ra] = rc
_, gi = np.unique([f("C" + c) for c in d.customer_id], return_inverse=True); G = gi.max() + 1
ws = np.round(np.arange(0, 1.0001, 0.05), 2)
rng = np.random.default_rng(20261024)
res["curva_2024"] = {}
for l in LINEAS + ["todos"]:
    i = np.ones(len(d), bool) if l == "todos" else (d.line == l).values
    Dm = np.column_stack([desviacion(y[i], w * T[i] + (1 - w) * A[i]) for w in ws])
    nulo = desviacion(y[i], np.full(i.sum(), y[i].mean())).sum()
    curva = 1 - Dm.sum(0) / nulo
    gl = gi[i]; _, gl = np.unique(gl, return_inverse=True); Gl = gl.max() + 1
    opt = []
    for s in range(0, 1000, 100):
        Wc = rng.poisson(1.0, size=(100, Gl)).astype(float)
        S = np.zeros((100, len(ws)))
        for j in range(len(ws)):
            S[:, j] = np.bincount(gl, weights=Dm[:, j], minlength=Gl) @ Wc.T
        opt.append(ws[S.argmin(1)])
    opt = np.concatenate(opt)
    res["curva_2024"][l] = {"pesos_MLind": ws.tolist(), "D2": curva.tolist(), "w_optimo": float(ws[curva.argmax()]),
                            "w_optimo_ic95": [float(np.quantile(opt, .025)), float(np.quantile(opt, .975))],
                            "D2_w0": float(curva[0]), "D2_w05": float(curva[10]), "D2_w1": float(curva[-1]), "D2_max": float(curva.max())}
# aritmética frente a geométrica y calibración
def murphy_mcb(yy, mm, ee):
    r = mm / ee
    iso = IsotonicRegression(out_of_bounds="clip").fit(r, yy / ee, sample_weight=np.sqrt(ee))
    mc = np.maximum(iso.predict(r) * ee, 1e-9)
    return float((desviacion(yy, mm).sum() - desviacion(yy, mc).sum()) / desviacion(yy, mm).sum())
res["2024"] = {}
for m in ["A1", "T2b", "ari", "geo"]:
    r = {"D2": d2(y, d[m].values)}
    for l in LINEAS:
        i = (d.line == l).values
        r[l] = {"D2": d2(y[i], d[m].values[i]), "AE": float(y[i].sum() / d[m].values[i].sum()),
                "AE_NB": float(y[i & d.new_business.values].sum() / d[m].values[i & d.new_business.values].sum()),
                "AE_REN": float(y[i & ~d.new_business.values].sum() / d[m].values[i & ~d.new_business.values].sum()),
                "MCB_sobre_S": murphy_mcb(y[i], d[m].values[i], d.exposure.values[i])}
    res["2024"][m] = r
# ------------------------------------------------ 2025
sub = pd.read_parquet(DATOS / "emerging" / "sample_submission.parquet")[["row_id"]]
base = pd.concat([pd.read_parquet(TRABAJO / f"base_emerging_{l}.parquet", columns=["row_id", "policy_id", "exposure", "new_business", "conjunto"]).assign(line=l) for l in LINEAS])
q = sub.merge(base[base.conjunto == "test"], on="row_id", how="left")
for k, fp in {"designada": OTROS / "A1fixF1b3n_2025.csv", "mlind": PRIVADO / "prediccion_2025_mlind.csv", "mezcla": PRIVADO / "mezcla50_designada_mlind_2025.csv"}.items():
    x = pd.read_csv(fp, dtype={"row_id": str}); assert (x.row_id.values == q.row_id.values).all(); q[k] = x.prediction.values
assert np.allclose(q.mezcla, 0.5 * q.designada + 0.5 * q.mlind, rtol=1e-6, atol=1e-5)
res["2025"] = {"controles": {"filas": int(len(q)), "nulos": int(q.mezcla.isna().sum()), "min": float(q.mezcla.min()),
                             "positivas": bool((q.mezcla > 0).all()), "orden_plantilla": True,
                             "max_error_media": float(np.abs(q.mezcla - 0.5 * q.designada - 0.5 * q.mlind).max())}}
for k in ["designada", "mlind", "mezcla"]:
    r = {"total": float(q[k].sum())}
    for l in LINEAS:
        i = (q.line == l).values; e = q.exposure.values[i]; nb = q.new_business.values[i]
        r[l] = {"total": float(q[k].values[i].sum()), "tasa": float(q[k].values[i].sum() / e.sum()),
                "tasa_NB": float(q[k].values[i][nb].sum() / e[nb].sum()), "tasa_REN": float(q[k].values[i][~nb].sum() / e[~nb].sum())}
    res["2025"][k] = r
# ------------------------------------------------ prima comercial de las 20 referencias
ex = pd.read_parquet(DATOS / "emerging" / "expenses.parquet").set_index("item").emerging
ref = pd.read_parquet(DATOS / "emerging" / "reference_policies.parquet")
com = {"direct": ex["commission_direct"], "broker": ex["commission_broker"], "comparison_site": ex["commission_comparison_site"]}
exp_pol = q.groupby("policy_id").exposure.sum()
filas = []
for _, r in ref.iterrows():
    R = float(q.loc[q.row_id == r.row_id, "mezcla"].iloc[0]); e = r.exposure
    cat = ex["cat_reinsurance"] * R if r.line in ("buildings", "contents") else 0.0
    den = 1 - ex["variable_expense"] - com[r.channel] - ex["premium_tax"] - ex["target_profit_margin"]
    F = ex["fixed_expense_per_policy"] * e
    P = (R + cat + F) / den
    Fpol = ex["fixed_expense_per_policy"] * e / exp_pol[r.policy_id]  # 85 por póliza repartidos entre sus filas de 2025
    filas.append({"row_id": r.row_id, "ramo": r.line, "canal": r.channel, "nuevo_negocio": bool(r.new_business), "exposicion": e,
                  "riesgo_designada": float(q.loc[q.row_id == r.row_id, "designada"].iloc[0]),
                  "riesgo_mlind": float(q.loc[q.row_id == r.row_id, "mlind"].iloc[0]), "riesgo_mezcla": R,
                  "reaseguro_cat": cat, "gasto_fijo": F, "gasto_variable": P * ex["variable_expense"], "comision": P * com[r.channel],
                  "impuesto": P * ex["premium_tax"], "margen": P * ex["target_profit_margin"], "denominador": den,
                  "prima_comercial": P, "prima_comercial_F_por_poliza": (R + cat + Fpol) / den, "prima_escrita": r.written_premium})
pc = pd.DataFrame(filas); pc.round(2).to_csv(OUT / "prima_comercial_20_mezcla.csv", index=False)
res["prima_comercial"] = {"media_por_ramo": pc.groupby("ramo")[["riesgo_mezcla", "prima_comercial", "prima_escrita"]].mean().round(2).to_dict(),
                          "suma_componentes_ok": bool(np.allclose(pc.riesgo_mezcla + pc.reaseguro_cat + pc.gasto_fijo + pc.gasto_variable + pc.comision + pc.impuesto + pc.margen, pc.prima_comercial))}
guardar_json(res, OUT / "diagnostico_mezcla.json")
# ------------------------------------------------ figura
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 130})
C = {"motor": "#2a6f97", "buildings": "#c4673b", "contents": "#5b8c5a", "todos": "#333333"}
fig, axs = plt.subplots(1, 2, figsize=(10.5, 3.6))
for l in LINEAS + ["todos"]:
    c = res["curva_2024"][l]; base = c["D2"][0]
    axs[0].plot(ws, np.array(c["D2"]) - base, color=C[l], lw=2 if l == "todos" else 1.2, label=f"{l} (óptimo {c['w_optimo']:.2f}, IC95 {c['w_optimo_ic95'][0]:.2f}-{c['w_optimo_ic95'][1]:.2f})")
axs[0].axvline(0.5, color="#999", ls="--", lw=0.8); axs[0].axhline(0, color="#ccc", lw=0.6)
axs[0].set_xlabel("peso de MLind (el resto, A1)"); axs[0].set_ylabel("D² 2024 menos D² de A1 sola")
axs[0].legend(frameon=False, fontsize=6.8); axs[0].set_title("2024 (ya visto por las dos líneas): autos y contenidos admiten 0,5; edificios prefiere MLind", fontsize=8)
x = np.arange(3); w = 0.26
for j, (k, lab, col) in enumerate([("designada", "designada A1fixF1b3n", "#c4673b"), ("mezcla", "mezcla 50/50", "#5b8c5a"), ("mlind", "MLind", "#2a6f97")]):
    vals = [res["2025"][k][l]["tasa"] for l in LINEAS]
    axs[1].bar(x + (j - 1) * w, vals, w, label=lab, color=col)
    for xi, v in zip(x + (j - 1) * w, vals):
        axs[1].text(xi, v + 5, f"{v:.0f}", ha="center", fontsize=7)
axs[1].set_xticks(x, LINEAS); axs[1].set_ylabel("tasa 2025 (CU por año de exposición)"); axs[1].legend(frameon=False, fontsize=7)
axs[1].set_title("Producción 2025 de la combinación", fontsize=8.5)
fig.tight_layout(); fig.savefig(OUT / "f11_mezcla.png"); plt.close(fig)
print(json.dumps({k: v for k, v in res.items() if k not in ("fuentes",)}, indent=1, default=float)[:7000])
