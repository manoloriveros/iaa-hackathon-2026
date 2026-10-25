"""Figuras de resultados: DEV frente a HOLD, inestabilidad del nuevo negocio, sensibilidad 2025, curvas del transformer."""
import json
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from comun import *
import receta

FIG = ENTREGA / "figuras"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 130})
C = {"motor": "#2a6f97", "buildings": "#c4673b", "contents": "#5b8c5a"}
out = {}

# f04: DEV frente a HOLD (2024, sin tendencia) para la lista congelada
dev = pd.read_csv(ENTREGA / "tabla_dev.csv")
hold = json.load(open(ENTREGA / "resultados_hold.json"))["candidatos"]
filas = []
for k, v in hold.items():
    base, cal = k.rsplit("_", 1)
    cc = {"C1": "ramo", "C2": "ramo_nb"}[cal]
    dv = dev[(dev.cand == base) & (dev.calib == cc)].D2.values
    filas.append({"cand": k, "DEV": float(dv[0]) if len(dv) else np.nan, "HOLD": v["sin_tendencia"]["D2"]})
d = pd.DataFrame(filas).sort_values("HOLD"); out["dev_hold"] = d.round(5).to_dict("records")
fig, ax = plt.subplots(figsize=(7, 4))
y = np.arange(len(d))
ax.hlines(y, d.DEV, d.HOLD, color="#bbb", lw=2)
ax.scatter(d.DEV, y, color="#2a6f97", label="DEV: OOF 2023", zorder=3)
ax.scatter(d.HOLD, y, color="#c4673b", label="HOLD: 2024, abierto una vez", zorder=3)
ax.set_yticks(y, d.cand); ax.set_xlabel("D² Tweedie 1,5")
ax.legend(frameon=False, loc="lower right"); ax.set_title("Los modelos con transferencia ganan en los dos años; el orden entre ellos es ruido", fontsize=9)
fig.tight_layout(); fig.savefig(FIG / "f04_dev_frente_hold.png"); plt.close(fig)

# f06: A/E del nuevo negocio por ramo y año con C1 (OOF 2023-2024)
t, mu, _ = receta.oof_cruzado("pcv", ["T2b"], "ramo")
m = mu * t.c_fila.values
g = pd.DataFrame({"line": t.line, "year": t.year, "nb": t.new_business, "y": t.y, "m": m, "s": t.y > 0}).groupby(["line", "nb", "year"]).agg(
    y=("y", "sum"), m=("m", "sum"), n=("s", "sum"))
g["AE"] = g.y / g.m
out["ae_nb_anio"] = {f"{a}|{b}|{c}": {"AE": round(float(r.AE), 4), "n_sin": int(r.n)} for (a, b, c), r in g.iterrows()}
fig, ax = plt.subplots(figsize=(7, 3.4))
xs = 0
for l in LINEAS:
    for nb in (False, True):
        for yv, mk in ((2023, "o"), (2024, "s")):
            r = g.loc[(l, nb, yv)]
            ax.scatter(xs, r.AE, color=C[l], marker=mk, s=20 + r.n / 8, alpha=0.85)
        ax.text(xs, 0.3, ("NB" if nb else "REN"), ha="center", fontsize=7)
        xs += 1
    xs += 0.6
ax.axhline(1, color="#999", lw=0.8, ls="--")
ax.set_xticks([0.5, 3.1, 5.7], LINEAS); ax.set_ylabel("observado / esperado (C1)")
ax.set_ylim(0.25, 1.9)
ax.set_title("El exceso del nuevo negocio no se repite de un año a otro (círculo 2023, cuadrado 2024; área ∝ siniestros)", fontsize=8.5)
fig.tight_layout(); fig.savefig(FIG / "f06_nuevo_negocio_por_anio.png"); plt.close(fig)

# f07: sensibilidad del total 2025 y tasas frente a la historia
prod = json.load(open(ENTREGA / "produccion_2025.json")); ctx = json.load(open(ENTREGA / "contexto_2025.json"))
fig, axs = plt.subplots(1, 2, figsize=(10, 3.4))
var = ["final_C1", "C1_tendencia", "C2", "preinscrita_C2_tendencia"]
etq = ["final (C1)", "C1 + tendencia", "C2", "preinscrita\n(C2 + tendencia)"]
tot = [prod["variantes"][v]["total"] / 1e6 for v in var]
axs[0].bar(etq, tot, color=["#2a6f97", "#9bb7cc", "#9bb7cc", "#9bb7cc"])
for i, v in enumerate(tot):
    axs[0].text(i, v + 0.5, f"{v:.1f}", ha="center", fontsize=8)
axs[0].set_ylabel("total predicho 2025 (millones de CU)"); axs[0].set_title("Sensibilidad del total a las dos reglas descartadas", fontsize=9)
x = np.arange(3); w = 0.25
for j, (lab, key) in enumerate([("2023 observado último", "2023"), ("2024 observado último", "2024"), ("2025 predicho", "2025")]):
    vals = [ctx[l][key]["tasa_ultima_obs"] if key != "2025" else ctx[l]["2025"]["tasa_predicha"] for l in LINEAS]
    axs[1].bar(x + (j - 1) * w, vals, w, label=lab, color=["#cfcfcf", "#9a9a9a", "#2a6f97"][j])
axs[1].set_xticks(x, LINEAS); axs[1].set_ylabel("CU por año de exposición"); axs[1].legend(frameon=False, fontsize=7)
axs[1].set_title("Tasa por exposición: historia y predicción", fontsize=9)
fig.tight_layout(); fig.savefig(FIG / "f07_sensibilidad_2025.png"); plt.close(fig)

# f08: curvas del transformer (preentrenamiento en el desarrollado)
fig, axs = plt.subplots(1, 3, figsize=(10, 3))
for ax, l in zip(axs, LINEAS):
    h = json.load(open(TRABAJO / "modelos" / "dev" / f"N_pre_{l}.json"))["hist"]
    ep = [r[0] for r in h]; tr = [r[1] for r in h]; vl = [r[2] for r in h]
    ax.plot(ep, tr, "o-", ms=3, color="#999", label="entrenamiento"); ax.plot(ep, vl, "o-", ms=3, color=C[l], label="validación")
    ax.set_title(l); ax.set_xlabel("época"); ax.legend(frameon=False, fontsize=7)
axs[0].set_ylabel("desviación Tweedie media (y con tope)")
fig.suptitle("Preentrenamiento del FT-Transformer en el mercado desarrollado 2021-2023", fontsize=10)
fig.tight_layout(); fig.savefig(FIG / "f08_transformer_preentrenamiento.png"); plt.close(fig)
guardar_json(out, ENTREGA / "figuras_datos.json")
print(json.dumps(out, indent=0)[:3000])
