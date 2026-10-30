"""Figure f12: E14-E22 versus T2b in DEV 2023, HOLD 2024 and developed DES24."""
import json
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from comun import *

E = ENTREGA
fuentes = ["e14_individuales.json", "e14_fs.json", "e15_cb.json", "e21_fsp.json", "e22_mezcla.json"]
boot, des = {}, {}
for f in fuentes:
    r = json.load(open(E / f))
    for k, v in r["bootstrap_vs_T2b"].items():
        nom, cal = k.split("|")
        if cal == "ramo":
            boot[nom] = v
    des.update(r["DES24"])
filas = [("T2x", "T2x  +make_model y tenencia"), ("CB", "CB  CatBoost Tweedie"), ("FSp", "FSp  frec. x sev. por peligro"),
         ("T2o", "T2o  sin occupation"), ("T2c", "T2c  sin historia"), ("T2h", "T2h  historia centrada"),
         ("FS", "FS  frecuencia x severidad"), ("T2b+T2h+FS+T2o_e50", "Mezcla v2 (E22, e50)")]
C = {"bg": "#fcfcfb", "ink": "#0b0b0b", "ink2": "#52514e", "grid": "#e4e3df",
     "s1": "#2a78d6", "s2": "#eb6834", "s3": "#1baf7a"}
plt.rcParams.update({"font.size": 9.5, "axes.edgecolor": C["grid"], "axes.labelcolor": C["ink2"],
                     "xtick.color": C["ink2"], "ytick.color": C["ink"], "font.family": "DejaVu Sans"})
fig, axs = plt.subplots(1, 2, figsize=(12.5, 5.2), facecolor=C["bg"], gridspec_kw={"width_ratios": [1.15, 1]})
y = np.arange(len(filas))[::-1]
ax = axs[0]
for j, (fase, lab, col, mk) in enumerate([("dev", "2023 (DEV, OOF)", C["s1"], "o"), ("hold", "2024 (HOLD)", C["s2"], "s")]):
    for yi, (k, _) in zip(y, filas):
        if k not in boot:
            continue
        b = boot[k][fase]; off = 0.16 if j == 0 else -0.16
        ax.plot(b["ic95"], [yi + off] * 2, color=col, lw=2, solid_capstyle="round")
        ax.plot(b["dif"], yi + off, mk, color=col, ms=7, mec=C["bg"], mew=1.5, label=lab if yi == y[0] else None)
ax.axvline(0, color=C["ink2"], lw=1)
ax.axvspan(0.001, 0.02, color=C["grid"], alpha=0.35, lw=0)
ax.text(0.0012, y[0] + 0.55, "umbral E18: +0,001 en 2023", color=C["ink2"], fontsize=8.5, va="bottom")
ax.set_yticks(y); ax.set_yticklabels([n for _, n in filas])
ax.set_xlim(-0.026, 0.012); ax.set_ylim(-0.7, len(filas) - 0.1)
ax.set_xlabel("Diferencia de D² frente a T2b, calibración C1 (IC95 por cliente)")
ax.set_title("Emergente: 2023 y 2024", loc="left", color=C["ink"], fontsize=11)
ax.legend(loc="lower left", frameon=False)
ax.grid(axis="x", color=C["grid"], lw=0.8); ax.set_axisbelow(True); ax.set_facecolor(C["bg"])
ax = axs[1]
ramos = [("motor", "autos", C["s1"], "o"), ("buildings", "edificios", C["s2"], "s"), ("contents", "contenidos", C["s3"], "^")]
for j, (l, lab, col, mk) in enumerate(ramos):
    for yi, (k, _) in zip(y, filas):
        if k not in des:
            continue
        v = des[k][l] - des["T2b"][l]; off = (1 - j) * 0.2
        ax.plot([0, v], [yi + off] * 2, color=col, lw=1.2, alpha=0.6)
        ax.plot(v, yi + off, mk, color=col, ms=7, mec=C["bg"], mew=1.5, label=lab if yi == y[2] else None)
    if l == "contents":
        for yi, (k, _) in zip(y, filas):
            if k in des and des[k][l] - des["T2b"][l] < -0.012:
                ax.annotate(f"{des[k][l] - des['T2b'][l]:+.3f}".replace(".", ","), (-0.0116, yi - 0.45), color=C["ink2"],
                            fontsize=8, va="center")
ax.axvline(0, color=C["ink2"], lw=1)
ax.set_yticks(y); ax.set_yticklabels([""] * len(filas))
ax.set_xlim(-0.012, 0.009); ax.set_ylim(-0.7, len(filas) - 0.1)
ax.set_xticks([-0.01, -0.005, 0, 0.005])
ax.text(0.0, -0.55, "la mezcla no tiene DES24: es una combinación de troncos", color=C["ink2"], fontsize=8.5, ha="center")
ax.set_xlabel("Diferencia de D² frente a T2b en el desarrollado 2024 (renivelado)")
ax.set_title("DES24: desarrollado 2024, fuera de tiempo", loc="left", color=C["ink"], fontsize=11)
ax.legend(loc="upper right", frameon=False)
ax.grid(axis="x", color=C["grid"], lw=0.8); ax.set_axisbelow(True); ax.set_facecolor(C["bg"])
for a in axs:
    for s in ("top", "right"):
        a.spines[s].set_visible(False)
    a.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:+.3f}".replace(".", ",") if v else "0"))
fig.suptitle("Troncos nuevos frente a T2b: lo que mejora en 2024 y en el desarrollado no mejora en 2023",
             x=0.01, ha="left", fontsize=12.5, color=C["ink"])
fig.tight_layout(rect=(0, 0, 1, 0.95))
out = E / "evolucion" / "f12_troncos.png"; out.parent.mkdir(exist_ok=True)
fig.savefig(out, dpi=150, facecolor=C["bg"])
print(out)
