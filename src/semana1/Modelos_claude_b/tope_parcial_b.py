"""Tope de siniestros grandes con crédito parcial y por peligro en la etiqueta de entrenamiento del Tweedie total.

La línea principal acota en autos la etiqueta de entrenamiento a 15.000 CU por fila y devuelve el exceso como recargo
uniforme (produccion.py / experimentos.fit con 'cap'); en hogar no acota. Aquí se prueban etiquetas alternativas y' que
conservan parte de la señal de los siniestros grandes:
  - total:K:lam      y' = min(y, K) + lam (y - K)+                       (lam = 0 es el tope duro vigente)
  - peligro:spec     y' = sum_p [min(y_p, K_p) + lam_p (y_p - K_p)+]     con K_p y lam_p por peligro (spec = p:K:lam,...);
                     los peligros no nombrados no se acotan
En todos los casos el recargo uniforme es sum(y) / sum(y') en el entrenamiento, como en la línea principal, y la
evaluación usa siempre la etiqueta completa. LightGBM con la configuración de cfg_total.json del ramo (sin 'cap'),
V23 con parada temprana y V24 con las rondas x 1,15 (semillas indicadas). Escribe WORK/<nombre>/resumen.json.
Uso: python3 tope_parcial_b.py <nombre> <ramo> <conjunto> --variantes="sin;total:15000:0;total:15000:0.3;peligro:bodily_injury:30000:0,own_damage:20000:0.5" [--semillas=1]
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np

import os as _os
from pathlib import Path as _Path
# código de la línea principal de Claude: carpeta hermana Modelos_claude en el repositorio, o la copia de la nube
_MC = _os.environ.get("MODELOS_CLAUDE") or next((str(p) for p in (_Path(__file__).resolve().parent.parent / "Modelos_claude", _Path("/home/claude/mc")) if p.exists()), "/home/claude/mc")
sys.path.insert(0, _MC)
from comun import PERILS, WORK, d2, to_model_frame  # noqa: E402
from experimentos import features, fit, load, predict  # noqa: E402


def etiqueta(variante, y, perils_y):
    if variante == "sin":
        return y.copy()
    kind, rest = variante.split(":", 1)
    if kind == "total":
        K, lam = float(rest.split(":")[0]), float(rest.split(":")[1])
        return np.minimum(y, K) + lam * np.maximum(y - K, 0.0)
    if kind == "peligro":
        spec = {}
        for item in rest.split(","):
            p, K, lam = item.split(":")
            spec[p] = (float(K), float(lam))
        yn = np.zeros_like(y)
        for p, yp in perils_y.items():
            if p in spec:
                K, lam = spec[p]
                yn += np.minimum(yp, K) + lam * np.maximum(yp - K, 0.0)
            else:
                yn += yp
        # los importes que no están asignados a un peligro (diferencias de redondeo) se conservan
        return yn + (y - sum(perils_y.values()))
    raise SystemExit(variante)


def main():
    name, line, set_name = sys.argv[1:4]
    opts = dict((a[2:].split("=", 1) + ["1"])[:2] for a in sys.argv[4:] if a.startswith("--"))
    variantes = [v for v in opts["variantes"].split(";") if v]
    seeds = int(opts.get("semillas", 1))
    cfg = json.load(open(WORK / "cfg_total.json"))[line]
    params = dict(cfg["params"]); params.pop("cap", None)
    t0 = time.time()
    df = load(line)
    feats = features(line, df, set_name)
    X = to_model_frame(df, feats)
    y = df["T0"].fillna(0).values
    perils_y = {p: df[f"y_{p}"].fillna(0).values for p in PERILS[line]}
    off = df["e_ef_coste"].values
    yr = df.year.values
    tr = yr <= 2022; cal = (yr == 2023) & (df.cal_half.values == 0); sel = (yr == 2023) & (df.cal_half.values == 1)
    tr24 = yr <= 2023; ev24 = yr == 2024
    out = WORK / name
    out.mkdir(parents=True, exist_ok=True)
    rep = {"line": line, "set": set_name, "params": params, "variantes": {}}
    for v in variantes:
        yv = etiqueta(v, y, perils_y)
        r = {"recargo_v23": float(y[tr].sum() / yv[tr].sum()), "recargo_v24": float(y[tr24].sum() / yv[tr24].sum())}
        # V23: la parada temprana mira la etiqueta transformada de la mitad de calibración (como con 'cap')
        b, base = fit(X[tr], yv[tr], off[tr], X[cal], yv[cal], off[cal], params=dict(params))
        bf = b.best_iteration or b.current_iteration()
        mu = predict(b, base, X[sel], off[sel], bf) * r["recargo_v23"]
        r.update({"best": int(bf), "d2_sel": round(d2(y[sel], mu), 5), "balance_sel": round(float(mu.sum() / y[sel].sum()), 4)})
        mu24 = np.zeros(ev24.sum())
        for s in range(seeds):
            b24, base24 = fit(X[tr24], yv[tr24], off[tr24], rounds=int(round(bf * 1.15)), early=None, params=dict(params, seed=20261017 + 101 * s))
            mu24 += predict(b24, base24, X[ev24], off[ev24]) / seeds
        mu24 *= r["recargo_v24"]
        r.update({"d2_v24": round(d2(y[ev24], mu24), 5), "balance_v24": round(float(mu24.sum() / y[ev24].sum()), 4)})
        # sin el 0,1 % superior de la pérdida (cuerpo de la distribución)
        for tag, m, pr in (("sel", sel, mu), ("v24", ev24, mu24)):
            keep = y[m] <= np.quantile(y[m], 0.999)
            r[f"d2_{tag}_sin_top01"] = round(d2(y[m][keep], pr[keep]), 5)
        np.save(out / f"v24_{v.replace(':', '_').replace(',', '-')}.npy", mu24)
        rep["variantes"][v] = r
        (out / "resumen.json").write_text(json.dumps(rep, indent=1))
        print(name, v, r, round(time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
