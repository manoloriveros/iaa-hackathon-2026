"""Inspect power-1.5 Tweedie calibration with isotonic Murphy decomposition.
Report observed/expected ratios by decile and segment.
Usage: python calibracion.py <dev|pcv> <recipe.json>
"""
import sys, json
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.isotonic import IsotonicRegression
from comun import *
import receta

plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 130})
C = {"motor": "#2a6f97", "buildings": "#c4673b", "contents": "#5b8c5a"}


def murphy(y, m, w):
    """Decompose mean score as S=UNC-DSC+MCB; fit isotonic observed rates with exposure weights."""
    e = w
    r = m / e
    # For power-1.5 amount deviance, optimal isotonic blocks weight rates by e^(2-p)=sqrt(e).
    iso = IsotonicRegression(out_of_bounds="clip").fit(r, y / e, sample_weight=np.sqrt(e))
    mc = np.maximum(iso.predict(r) * e, 1e-9)
    ybar = np.sum(y / np.sqrt(e)) / np.sum(np.sqrt(e)) * e  # Tweedie-optimal constant rate.
    S = desviacion(y, m).mean(); Sc = desviacion(y, mc).mean(); Su = desviacion(y, ybar).mean()
    return {"S": S, "UNC": Su, "DSC": Su - Sc, "MCB": S - Sc, "D2": 1 - S / Su, "D2_recal": 1 - Sc / Su}


if __name__ == "__main__":
    fase = sys.argv[1]; spec = json.load(open(sys.argv[2]))
    t, mu, _ = receta.oof_cruzado(fase, spec["componentes"], spec["calib"])
    m = mu * t.c_fila.values; y = t.y.values
    out = {"murphy": {}, "deciles": {}, "segmentos": {}}
    fig, axs = plt.subplots(1, 3, figsize=(10, 3.2))
    for ax, l in zip(axs, LINEAS):
        i = (t.line == l).values
        out["murphy"][l] = murphy(y[i], m[i], t.exposure.values[i] * t.c_fila.values[i])
        r = m[i] / (t.exposure.values[i] * t.c_fila.values[i])
        dec = pd.qcut(r, 10, labels=False, duplicates="drop")
        g = pd.DataFrame({"d": dec, "y": y[i], "m": m[i], "e": t.exposure.values[i] * t.c_fila.values[i]}).groupby("d").sum()
        g["obs"] = g.y / g.e; g["pred"] = g.m / g.e; g["AE"] = g.y / g.m
        out["deciles"][l] = g[["obs", "pred", "AE"]].round(4).to_dict()
        ax.plot(g.pred, g.obs, "o-", color=C[l], ms=4, label="observado")
        lim = [0, max(g.pred.max(), g.obs.max()) * 1.05]
        ax.plot(lim, lim, color="#999", lw=0.8, ls="--", label="diagonal")
        ax.set_title(f"{l}  (MCB/S = {out['murphy'][l]['MCB'] / out['murphy'][l]['S']:.2%})")
        ax.set_xlabel("tasa predicha (CU por año)"); ax.legend(frameon=False, fontsize=7)
    axs[0].set_ylabel("tasa observada (CU por año)")
    fig.suptitle(f"Calibración por deciles de la predicción, OOF {fase}", fontsize=10)
    fig.tight_layout(); fig.savefig(ENTREGA / "figuras" / f"f05_calibracion_deciles_{fase}.png"); plt.close(fig)
    # Shape diagnostic: transferred-relativity exponent a; a=1 indicates unchanged shape.
    out["forma"] = {}
    for l in LINEAS:
        i = (t.line == l).values; e = t.exposure.values[i] * t.c_fila.values[i]; r = m[i] / e
        g = np.exp(np.average(np.log(r), weights=e))
        mejor = None; curva = {}
        for a in np.round(np.arange(0.6, 1.41, 0.05), 2):
            ma = e * g * (r / g) ** a
            ma *= factor_tweedie(y[i], ma)
            dv_ = desviacion(y[i], ma).sum(); curva[float(a)] = dv_
            if mejor is None or dv_ < mejor[1]:
                mejor = (float(a), dv_)
        base = curva[1.0]; d0 = desviacion(y[i], np.full(i.sum(), y[i].mean())).sum()
        out["forma"][l] = {"a_optimo": mejor[0], "ganancia_D2_en_muestra": (base - mejor[1]) / d0}
    for seg in ["new_business", "year"]:
        g = pd.DataFrame({"line": t.line, "s": t[seg], "y": y, "m": m}).groupby(["line", "s"]).sum()
        g["AE"] = g.y / g.m
        out["segmentos"][seg] = {f"{a}|{b}": round(float(v), 4) for (a, b), v in g.AE.items()}
    guardar_json(out, ENTREGA / f"calibracion_{fase}.json")
    print(json.dumps(out["murphy"], indent=1, default=float)); print(out["segmentos"]); print(out["forma"])
