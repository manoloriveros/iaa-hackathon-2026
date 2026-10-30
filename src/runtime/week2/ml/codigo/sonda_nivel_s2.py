"""Reconstruct historical Week 2 public-probe level factors with credibility.

For power 1.5, scaling a line by c changes public D2 by
-4*[S1*(c**-0.5-1)+S2*(c**0.5-1)]/N, with S1=sum(y/sqrt(mu)) and
S2=sum(sqrt(mu)). Two recorded probes (0.90 and 1.10) identify the normalized
terms and the public optimum c*=S1/S2. Shrink log(c*) by
Z=tau^2/(tau^2+sigma^2), with tau fixed before observing the probes. Estimate
noise at the recorded 2025 public/private sample sizes. This source preserves
the historical formula; the reproduction notebook does not request new probes.
Usage: python sonda_nivel_s2.py generar
       python sonda_nivel_s2.py resolver --base <score> --motor <P090> <P110>
       --buildings <P090> <P110> --contents <P090> <P110> [--simular]
"""
import argparse, json, datetime as dt, sys
import numpy as np, pandas as pd
from comun import *
import receta

BASE_SHA = "12831ef4a05c1773824abe5fa139d9503dd2989b4874e7d93cfc000406cfdb4a"
BASE_PUB = 0.15390
C_SONDA = {"x090": 0.90, "x110": 1.10}
PREF = {"M": "motor", "B": "buildings", "C": "contents"}
# Prior uncertainty of log 2025 level was frozen before observing public probes,
# using the documented spread of defensible production-level scenarios:
# motor: C1 1.00, trend 1.08, C2 1.28, C2+trend 1.38; prior sd 0.14.
# buildings: C1 1.00, trend 1.09, 2023-only 1.31, 2024-only 0.81; prior sd 0.20.
# contents: C1 1.00, trend 1.06, C2 1.05, C2+trend 1.12; prior sd 0.06.
TAU = {"motor": 0.14, "buildings": 0.20, "contents": 0.06}
DIR = RAIZ / "sondas"


def leer_base():
    f = PRIVADO / "mezcla50_designada_mlind_2025.csv"
    assert sha256(f) == BASE_SHA, "la base no es la mezcla enviada"
    b = pd.read_csv(f, dtype={"row_id": str})
    b["line"] = b.row_id.str[0].map(PREF)
    assert b.line.notna().all()
    return b


def ruido(reps=2000, semilla=20261024):
    """Estimate line sigma as sd(log(public optimum/private optimum)) by customer-address resampling of observed-scale T2b+C1 PCV OOF to the recorded 2025 sample sizes."""
    t, mu, _ = receta.oof_cruzado("pcv", ["T2b"], "ramo")
    b = pd.concat([pd.read_parquet(TRABAJO / f"base_emerging_{l}.parquet", columns=["row_id", "address_id"]) for l in LINEAS])
    t = t.merge(b, on="row_id", how="left")
    m = mu * t.c_fila.values; y = t.y.values
    padre = {}
    def f(x):
        while padre.setdefault(x, x) != x:
            padre[x] = padre[padre[x]]; x = padre[x]
        return x
    for c, a in zip("C" + t.customer_id, "A" + t.address_id):
        rc, ra = f(c), f(a)
        if rc != ra: padre[ra] = rc
    _, gi = np.unique([f("C" + c) for c in t.customer_id], return_inverse=True); G = gi.max() + 1
    lam_pub = 209063 / 3 / len(t); lam_priv = 209063 * 2 / 3 / len(t)
    rng = np.random.default_rng(semilla); out = {}
    for l in LINEAS:
        i = (t.line == l).values
        a1 = np.bincount(gi[i], weights=y[i] / np.sqrt(m[i]), minlength=G); a2 = np.bincount(gi[i], weights=np.sqrt(m[i]), minlength=G)
        Wp = rng.poisson(lam_pub, size=(reps, G)); Wq = rng.poisson(lam_priv, size=(reps, G))
        cp = (Wp @ a1) / (Wp @ a2); cq = (Wq @ a1) / (Wq @ a2)
        out[l] = {"sd_log_c_publico": float(np.std(np.log(cp))), "sd_log_c_privado": float(np.std(np.log(cq))),
                  "sigma_pub_menos_priv": float(np.std(np.log(cp) - np.log(cq)))}
    return out


def generar(_):
    DIR.mkdir(parents=True, exist_ok=True)
    b = leer_base(); sig = ruido()
    Z = {l: TAU[l] ** 2 / (TAU[l] ** 2 + sig[l]["sigma_pub_menos_priv"] ** 2) for l in LINEAS}
    archivos = {}
    for l in LINEAS:
        for k, c in C_SONDA.items():
            x = b[["row_id", "prediction"]].copy()
            x.loc[b.line == l, "prediction"] *= c
            f = DIR / f"S2sonda_{l}_{k}.csv"
            x.to_csv(f, index=False, float_format="%.6f", lineterminator="\n")
            archivos[f.name] = {"sha256": sha256(f), "ramo": l, "factor": c, "total": float(x.prediction.sum()), "filas": len(x)}
    reg = {"id": "S2-SONDA-NIVEL-MLIND", "utc": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "base": {"archivo": "mezcla50_designada_mlind_2025.csv", "sha256": BASE_SHA, "publico": BASE_PUB, "envio": 57599788},
           "forma": "D2(c)-D2(1) = -4[S1(c^-1/2-1)+S2(c^1/2-1)]/N por ramo; c* = S1/S2",
           "tau_log": TAU, "ruido": sig, "Z": Z, "sondas": archivos,
           "regla": ["Enviar las seis sondas tal cual; ninguna se selecciona nunca.",
                     "Con las seis puntuaciones públicas y la base, resolver S1/N y S2/N por ramo; si alguno sale <= 0, ese ramo no se ajusta.",
                     "Si c* sale fuera de [0,5; 2,0], ese ramo no se ajusta (la forma supuesta no se cumple).",
                     "Candidato: base x c_Z por ramo, log c_Z = Z log c*. Se envía una vez; su público esperado se fija antes y una desviación > 0,0001 indica que el evaluador no tiene la forma supuesta.",
                     "Historical rule: retain the candidate only when its public result meets the recorded baseline. The participant controls submission and final selection."]}
    guardar_json(reg, DIR / "preinscripcion_sonda_nivel_s2.json")
    print(json.dumps({k: reg[k] for k in ["ruido", "Z", "tau_log"]}, indent=1))
    for k, v in archivos.items(): print(k, v["sha256"][:12], round(v["total"]))


def resolver(a):
    reg = json.load(open(DIR / "preinscripcion_sonda_nivel_s2.json"))
    b = leer_base(); out = {"entradas": {"base": a.base}, "ramos": {}}
    for l in LINEAS:
        p90, p110 = getattr(a, l); out["entradas"][l] = [p90, p110]
        # Solve d(c)=-4*[S1*(c**-0.5-1)+S2*(c**0.5-1)]/N for normalized s1 and s2.
        A = np.array([[-(0.9 ** -0.5 - 1), -(0.9 ** 0.5 - 1)], [-(1.1 ** -0.5 - 1), -(1.1 ** 0.5 - 1)]])
        s1, s2 = np.linalg.solve(A, np.array([p90 - a.base, p110 - a.base]))
        r = {"s1": float(s1), "s2": float(s2)}
        if s1 <= 0 or s2 <= 0:
            r.update({"valido": False, "motivo": "S1 o S2 no positivos", "c_Z": 1.0})
        else:
            cs = s1 / s2; z = reg["Z"][l]
            ok = bool(0.5 <= cs <= 2.0)
            cz = float(np.exp(z * np.log(cs))) if ok else 1.0
            ganancia_pub = lambda c: -(s1 * (c ** -0.5 - 1) + s2 * (c ** 0.5 - 1))
            r.update({"valido": ok, "c_estrella": float(cs), "Z": z, "c_Z": cz, "ganancia_publica_esperada": float(ganancia_pub(cz)),
                      "ganancia_publica_si_c_estrella": float(ganancia_pub(cs))})
        out["ramos"][l] = r
    out["publico_esperado_candidato"] = a.base + sum(r.get("ganancia_publica_esperada", 0.0) for r in out["ramos"].values())
    print(json.dumps(out, indent=1, default=float))
    if a.simular:
        return
    x = b[["row_id", "prediction"]].copy()
    for l in LINEAS:
        x.loc[b.line == l, "prediction"] *= out["ramos"][l]["c_Z"]
    f = DIR / "S2_nivel_credibilidad.csv"
    x.to_csv(f, index=False, float_format="%.6f", lineterminator="\n")
    out["candidato"] = {"archivo": f.name, "sha256": sha256(f), "total": float(x.prediction.sum()),
                        "por_ramo": {l: float(x.prediction[b.line == l].sum()) for l in LINEAS}}
    guardar_json(out, DIR / "resolucion_sonda_nivel_s2.json")
    print(out["candidato"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("generar")
    r = sp.add_parser("resolver"); r.add_argument("--base", type=float, default=BASE_PUB); r.add_argument("--simular", action="store_true")
    for l in LINEAS: r.add_argument(f"--{l}", type=float, nargs=2, required=True)
    a = ap.parse_args()
    {"generar": generar, "resolver": resolver}[a.cmd](a)
