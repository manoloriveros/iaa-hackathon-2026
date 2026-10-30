import json
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from comun import *
c1 = json.load(open(RAIZ / "comparacion" / "comparacion_lineas.json")); c2 = json.load(open(RAIZ / "comparacion" / "comparacion_lineas_2.json"))
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 130})
fig, axs = plt.subplots(1, 2, figsize=(10.5, 3.6))
seg = [("todas", "todas las filas"), ("NB", "nuevo negocio"), ("REN", "renovación"), ("pond_2025", "ponderado a 2025")]
mods = [("R0", "Tasa por ramo", "#bbbbbb"), ("A1", "A1 (base de la designada)", "#c4673b"), ("T2b", "MLind T2b (C1)", "#2a6f97"), ("mez50", "mezcla 50/50", "#5b8c5a")]
x = np.arange(len(seg)); w = 0.2
for j, (k, lab, col) in enumerate(mods):
    axs[0].bar(x + (j - 1.5) * w, [c2["D2"][k][s] for s, _ in seg], w, label=lab, color=col)
axs[0].set_xticks(x, [s for _, s in seg]); axs[0].set_ylabel("D² Tweedie 1,5 en 2024")
axs[0].set_ylim(0.05, 0.15); axs[0].legend(frameon=False, fontsize=7, loc="upper center", ncol=2)
axs[0].set_title("2024, mismas 59.202 filas (exploratorio: las dos líneas ya lo habían visto)", fontsize=8.5)
v = c1["2025"]; ks = [("noct_R0", "R0", "#bbbbbb"), ("noct_A1fixF1b3n_designada", "designada A1fixF1b3n", "#c4673b"),
                      ("MLind_final", "MLind final", "#2a6f97"), ("MLind_C2", "MLind con C2", "#9bb7cc")]
x = np.arange(3)
for j, (k, lab, col) in enumerate(ks):
    axs[1].bar(x + (j - 1.5) * w, [v[k][l]["tasa"] for l in LINEAS], w, label=lab, color=col)
axs[1].set_xticks(x, LINEAS); axs[1].set_ylabel("tasa 2025 predicha (CU por año de exposición)")
axs[1].legend(frameon=False, fontsize=7); axs[1].set_title("Producción 2025: el nivel es lo que más separa a las líneas", fontsize=8.5)
fig.tight_layout(); fig.savefig(RAIZ / "comparacion" / "f10_comparacion_lineas.png"); plt.close(fig)
