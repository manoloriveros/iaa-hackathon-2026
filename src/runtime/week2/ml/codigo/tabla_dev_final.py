"""Final DEV table: candidates/blends, cross-fitted C1/C2 and intervals versus T2b."""
import json
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from comun import *
from evaluar import metricas, bootstrap_dif
import receta

SIMPLES = ["R0", "G1", "T1wp", "T2", "T2b", "T3bwp", "T3bmk", "T4", "T5", "T6", "N1", "N2a", "N2b", "N3"]
MEZCLAS = {"E1": ["T2b", "T3bwp", "N3"], "E2": ["T2b", "T3bwp", "N3", "T4", "G1"],
           "E3": ["G1", "T1wp", "T2", "T2b", "T3bwp", "T3bmk", "T4", "T5", "T6", "N1", "N2a", "N2b", "N3"]}
t0 = receta.tabla("dev").merge(pd.read_parquet(TRABAJO / "pesos_2025_dev.parquet"), on="row_id", how="left")
filas = []; mus = {}; pesos_mezcla = {}
for nombre in SIMPLES + list(MEZCLAS):
    comps = MEZCLAS.get(nombre, [nombre])
    for calib in ["sin", "ramo", "ramo_nb"]:
        if nombre in MEZCLAS and calib == "sin":
            continue
        t, mu, pesos = receta.oof_cruzado("dev", comps, calib)
        assert (t.row_id.values == t0.row_id.values).all()
        mus[(nombre, calib)] = mu
        if pesos: pesos_mezcla[f"{nombre}|{calib}"] = pesos
        filas.append({"cand": nombre, "calib": calib, **metricas(t0, mu)})
df = pd.DataFrame(filas)
ref = mus[("T2b", "ramo_nb")]
bs = {}
for (n, c), mu in mus.items():
    if c == "ramo_nb" and n != "T2b":
        bs[n] = bootstrap_dif(t0, mu, ref, B=1000)
df["dif_T2b_C2"] = df.apply(lambda r: bs[r.cand]["dif"] if r.calib == "ramo_nb" and r.cand in bs else np.nan, axis=1)
df["ic95_lo"] = df.apply(lambda r: bs[r.cand]["ic95"][0] if r.calib == "ramo_nb" and r.cand in bs else np.nan, axis=1)
df["ic95_hi"] = df.apply(lambda r: bs[r.cand]["ic95"][1] if r.calib == "ramo_nb" and r.cand in bs else np.nan, axis=1)
df.to_csv(ENTREGA / "tabla_dev.csv", index=False)
guardar_json({"pesos_mezcla": pesos_mezcla, "bootstrap_vs_T2b_C2": bs}, ENTREGA / "dev_mezclas_bootstrap.json")
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(df[df.calib != "sin"].sort_values("D2", ascending=False).round(4).to_string())
# Plot candidate C2 D2 with comparison intervals against T2b.
d = df[df.calib == "ramo_nb"].set_index("cand").sort_values("D2")
fig, ax = plt.subplots(figsize=(7.5, 4.2))
col = ["#7a7a7a" if c in ("R0", "G1", "T1wp", "T4") else "#2a6f97" if c.startswith("T") else "#8e5ea2" if c.startswith("N") else "#c4673b" for c in d.index]
ax.barh(d.index, d.D2, color=col)
for i, (c, r) in enumerate(d.iterrows()):
    ax.text(r.D2 + 0.001, i, f"{r.D2:.4f}", va="center", fontsize=7)
ax.set_xlabel("D² Tweedie 1,5, OOF 2023, calibración por ramo y negocio cruzada")
ax.set_title("Desarrollo 2023: gris = solo emergente, azul = árboles con transferencia,\nmorado = redes, naranja = mezclas", fontsize=9)
fig.tight_layout(); fig.savefig(ENTREGA / "figuras" / "f03_dev_candidatos.png"); plt.close(fig)
