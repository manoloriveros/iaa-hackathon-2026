"""Diagrama del flujo (f00) e importancia de variables del modelo final (f09)."""
import json
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from comun import *

FIG = ENTREGA / "figuras"
plt.rcParams.update({"font.size": 9, "figure.dpi": 130})

# f00: flujo de la receta final
fig, ax = plt.subplots(figsize=(10, 3.6)); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 3.6)
cajas = [
    (0.1, 2.2, "Desarrollado 2021-2024\n2,4 M periodos\n(datos, etiquetas T0,\ncompletitud por peligro)", "#dce8f1"),
    (2.6, 2.2, "T2b: LightGBM Tweedie 1,5\nesquema común de variables\ndesplazamiento log(e·c)\nhiperparámetros por E07", "#2a6f97"),
    (5.1, 2.2, "Transferencia al emergente\nrelatividades del desarrollado\n× nivel por ramo (factor\nTweedie con 2023-2024)", "#c4673b"),
    (7.6, 2.2, "Calibración C1\nfactor por ramo del OOF\ncruzado 2023-2024\nsin tendencia (A03, A04)", "#5b8c5a"),
    (5.1, 0.25, "Emergente 2023-2024\n109.296 periodos, 9.258 siniestros\nOOF por cliente (DEV, PCV) y 2024 (HOLD)", "#f3e3d6"),
    (7.6, 0.25, "Producción 2025\n209.063 filas, 70,8 M CU\nprima comercial de 20 pólizas", "#e3efe2"),
]
for x, y, txt, col in cajas:
    oscuro = col in ("#2a6f97", "#c4673b", "#5b8c5a")
    ax.add_patch(FancyBboxPatch((x, y), 2.25, 1.25, boxstyle="round,pad=0.05", fc=col, ec="#555", lw=0.6))
    ax.text(x + 1.125, y + 0.62, txt, ha="center", va="center", fontsize=7.6, color="white" if oscuro else "#222")
for (x0, y0, x1, y1) in [(2.4, 2.82, 2.6, 2.82), (4.9, 2.82, 5.1, 2.82), (7.4, 2.82, 7.6, 2.82), (6.22, 1.55, 6.22, 2.15), (8.72, 2.15, 8.72, 1.55)]:
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="->", color="#444", lw=1))
ax.text(0.1, 1.2, "Alternativas probadas y no elegidas:\nsolo emergente (R0, G1, T1), ajuste fino por boosting (T3),\nmodelo conjunto (T4), GLM de adaptación (T5), por peligro (T6),\nFT-Transformer desde cero (N1), preentrenado y ajustado (N2a, N2b),\nresidual sobre T2b (N3) y mezclas (E1-E3).", fontsize=7.4, va="center", color="#333")
fig.tight_layout(); fig.savefig(FIG / "f00_flujo_receta.png"); plt.close(fig)

# f09: importancia (ganancia) del T2b de producción
fig, axs = plt.subplots(1, 3, figsize=(10.5, 3.6))
imp_out = {}
for ax, l in zip(axs, LINEAS):
    imp = pd.read_csv(TRABAJO / "modelos" / "prod" / f"T2b_{l}_importancia.csv", index_col=0).iloc[:, 0]
    imp = (imp / imp.sum()).sort_values(ascending=False).head(10)[::-1]
    imp_out[l] = imp[::-1].round(4).to_dict()
    ax.barh(imp.index, imp.values, color={"motor": "#2a6f97", "buildings": "#c4673b", "contents": "#5b8c5a"}[l])
    ax.set_title(l); ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1))
    for s in ("top", "right"): ax.spines[s].set_visible(False)
fig.suptitle("Variables con más ganancia en el modelo del desarrollado (T2b de producción)", fontsize=10)
fig.tight_layout(); fig.savefig(FIG / "f09_importancia_T2b.png"); plt.close(fig)
guardar_json(imp_out, ENTREGA / "importancia_T2b_prod.json"); print(json.dumps(imp_out, indent=0))
