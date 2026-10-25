"""Figura f13: nivel 2025 por segmento según la tarifa (E27) frente al tablero (sondeos globales)."""
import json
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from comun import *

r = json.load(open(ENTREGA / "nivel2025" / "e27_nivel.json"))["segmentos"]
SEG = ["motor|NB", "motor|REN", "buildings|NB", "buildings|REN", "contents|NB", "contents|REN"]
ET = {"motor|NB": "Autos\nnuevo", "motor|REN": "Autos\nrenov.", "buildings|NB": "Edificios\nnuevo",
      "buildings|REN": "Edificios\nrenov.", "contents|NB": "Contenidos\nnuevo", "contents|REN": "Contenidos\nrenov."}
C = {"bg": "#fcfcfb", "ink": "#0b0b0b", "ink2": "#52514e", "grid": "#e4e3df", "s1": "#2a78d6", "s2": "#eb6834", "s3": "#1baf7a"}
plt.rcParams.update({"font.size": 9.5, "axes.edgecolor": C["grid"], "axes.labelcolor": C["ink2"], "xtick.color": C["ink"],
                     "ytick.color": C["ink2"], "font.family": "DejaVu Sans"})
fig, axs = plt.subplots(1, 2, figsize=(12.5, 4.9), facecolor=C["bg"], gridspec_kw={"width_ratios": [1.25, 1]})
x = np.arange(len(SEG))
ax = axs[0]
g = np.array([r[s]["g"] for s in SEG]); sg = np.array([r[s]["sigma"] for s in SEG]); f = np.array([r[s]["f"] for s in SEG])
ax.vlines(x - 0.12, g * np.exp(-sg), g * np.exp(sg), color=C["s2"], lw=2)
ax.plot(x - 0.12, g, "o", color=C["s2"], ms=7, mec=C["bg"], mew=1.5, label="Tarifa × siniestralidad 2023-24 (±1 σ)")
ax.plot(x + 0.12, f, "s", color=C["s1"], ms=7, mec=C["bg"], mew=1.5, label="Factor E27 con credibilidad")
for yv, txt, ls, va in [(1.0, "mezcla enviada (1,000)", "-", "top"), (1.1877, "tablero, nivel creíble 1,188", "--", "top"),
                        (1.2231, "tablero, óptimo público 1,223", ":", "bottom")]:
    ax.axhline(yv, color=C["ink2"], lw=1, ls=ls)
    ax.text(-0.45, yv * (0.995 if va == "top" else 1.005), txt, color=C["ink2"], fontsize=8, va=va, ha="left")
ax.set_xticks(x); ax.set_xticklabels([ET[s] for s in SEG])
ax.set_ylabel("Factor sobre la mezcla enviada")
ax.set_ylim(0.45, 2.15); ax.set_yscale("log"); ax.set_yticks([0.5, 0.7, 1.0, 1.4, 2.0])
ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter()); ax.set_xlim(-0.5, len(SEG) - 0.5)
ax.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.1f}".replace(".", ",")))
ax.set_title("Nivel 2025 que sugiere la tarifa y factor que se aplica", loc="left", color=C["ink"], fontsize=11)
ax.legend(loc="upper right", frameon=False, fontsize=8.5)
ax = axs[1]
l23 = [r[s]["LR_2023"] for s in SEG]; l24 = [r[s]["LR_2024"] for s in SEG]
ax.vlines(x, np.minimum(l23, l24), np.maximum(l23, l24), color=C["grid"], lw=3)
ax.plot(x, l23, "o", color=C["s1"], ms=7, mec=C["bg"], mew=1.5, label="2023")
ax.plot(x, l24, "s", color=C["s2"], ms=7, mec=C["bg"], mew=1.5, label="2024")
ax.set_xticks(x); ax.set_xticklabels([ET[s] for s in SEG])
ax.set_ylabel("Coste último / prima devengada")
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.1f}".replace(".", ",")))
ax.set_title("La siniestralidad cambia mucho de un año a otro", loc="left", color=C["ink"], fontsize=11)
ax.legend(loc="upper right", frameon=False)
for a in axs:
    a.set_facecolor(C["bg"]); a.grid(axis="y", color=C["grid"], lw=0.8); a.set_axisbelow(True)
    for s in ("top", "right"):
        a.spines[s].set_visible(False)
fig.suptitle("La tarifa apunta en la misma dirección que el tablero, pero es demasiado inestable para fijar el nivel",
             x=0.01, ha="left", fontsize=12.5, color=C["ink"])
fig.tight_layout(rect=(0, 0, 1, 0.94))
out = ENTREGA / "nivel2025" / "f13_nivel_2025.png"
fig.savefig(out, dpi=150, facecolor=C["bg"]); print(out)
