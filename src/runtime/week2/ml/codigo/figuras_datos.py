"""Plot peril reporting completeness and portfolio shift from 2023 to 2025."""
import json
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from comun import *

FIG = ENTREGA / "figuras"; FIG.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 130})
C = {"motor": "#2a6f97", "buildings": "#c4673b", "contents": "#5b8c5a"}
info = json.load(open(TRABAJO / "preparacion.json"))

# Peril cost-weighted completeness in developed data and emerging-market contrast.
cdf = info["cdf_coste_desarrollado"]; con = info["contraste_reporte_emergente_2023"]
fig, axs = plt.subplots(1, 3, figsize=(10, 3.2), sharey=True)
for ax, l in zip(axs, LINEAS):
    for k, v in cdf.items():
        ll, p = k.split("|")
        if ll != l: continue
        xs = [0, 30, 90, 180, 365, 730]
        ax.plot(xs, [v[str(x)] if str(x) in v else v[x] for x in xs], marker="o", ms=3, label=p)
    ax.set_title(l); ax.set_xlabel("días desde la ocurrencia"); ax.axvline(365, color="#999", lw=0.6, ls=":")
    ax.legend(fontsize=7, frameon=False)
axs[0].set_ylabel("fracción del coste ya reportada")
fig.suptitle("Completitud de reporte ponderada por coste (desarrollado, cohorte 2021)", fontsize=10)
fig.tight_layout(); fig.savefig(FIG / "f01_completitud_reporte.png"); plt.close(fig)

# Portfolio shift: new business and policy-start month, 2023/2024 versus 2025.
fig, axs = plt.subplots(1, 2, figsize=(9, 3.2))
filas = []
for l in LINEAS:
    b = pd.read_parquet(TRABAJO / f"base_emerging_{l}.parquet", columns=["year", "new_business", "start_month", "exposure"])
    for y, g in b.groupby("year"):
        filas.append({"ramo": l, "año": y, "nb": np.average(g.new_business, weights=g.exposure),
                      "enero": np.average(g.start_month == 1, weights=g.exposure)})
d = pd.DataFrame(filas)
x = np.arange(3); w = 0.25
for i, l in enumerate(LINEAS):
    s = d[d.ramo == l]
    axs[0].bar(x + (i - 1) * w, s.nb.values, w, color=C[l], label=l)
axs[0].set_xticks(x, ["2023", "2024", "2025 (test)"]); axs[0].set_ylabel("nuevo negocio (% de exposición)")
axs[0].yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1)); axs[0].legend(frameon=False)
axs[0].set_title("La cartera de 2025 es casi toda nueva")
pes = json.load(open(TRABAJO / "pesos_2025_dev.json"))
imp = pd.DataFrame({l: pes[l]["importancia_top"] for l in LINEAS}).fillna(0)
imp = imp.loc[imp.mean(1).sort_values().index]
yy = np.arange(len(imp))
for i, l in enumerate(LINEAS):
    axs[1].barh(yy + (i - 1) * 0.25, imp[l].values, 0.25, color=C[l], label=f"{l} (AUC {pes[l]['auc']:.2f})")
axs[1].set_yticks(yy, imp.index); axs[1].set_xlabel("ganancia relativa del clasificador 2023 frente a 2025")
axs[1].legend(frameon=False, fontsize=7); axs[1].set_title("Qué distingue la cartera 2025")
fig.tight_layout(); fig.savefig(FIG / "f02_desplazamiento_cartera.png"); plt.close(fig)
print(d.round(3))
