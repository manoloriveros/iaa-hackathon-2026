"""J, tareas 2 y 4: álgebra de nivel exacta con los recibos.
Parametrización (identidad, no hipótesis): para cada celda s y archivo X,
  s_s(X) = Σ√X_s / Σ√F_s (filas 2025 de la celda; el público es un tercio al azar),
  A_s(X) = [A_s(F) − G_s(X)] / s_s(X),  B_s(X) = B_s(F)·s_s(X),
donde G_s(X) es la reducción de A_s (= ganancia de D²) del orden de X llevado al Σ√μ de F en la celda.
  D²(X) = D²(F) + Nivel(X) + Σ_s G_s(X)/s_s(X),  Nivel(X) = Σ_s [A_s(F)(1 − 1/s_s) + B_s(F)(1 − s_s)]  (exacto con los recibos).
A_s(F) = a_s/√g, B_s(F) = b_s·√g (a_s, b_s del resolutor, relativos a la mezcla)."""
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/m017/revision")
from J_lib import *

g = PRE["base"]["g"]; Kp = 1.2; CEL = PRE["celdas"]
dF = REC[PRE["base"]["sha256"]]
_sc = {v["celda"]: REC[v["sha256"]] for v in PRE["sondas"].values()}
b_s = {s: PRE["base"]["beta_B"] * CEL[s]["cuota_raiz_mu"] for s in CEL}
a_s = {s: (dF - _sc[s] - b_s[s] * ((g * Kp) ** .5 - g ** .5)) / ((g * Kp) ** -.5 - g ** -.5) for s in _sc}
a_s[PRE["celda_deducida"]] = PRE["base"]["beta_A"] - sum(a_s.values())
c_opt = {s: a_s[s] / b_s[s] for s in CEL}
cg = PRE["base"]["c_optimo_global"]
cred = {s: g * float(np.clip((c_opt[s] / cg) ** CEL[s]["Z"], 0.75, 1.33)) for s in CEL}
AF = {s: a_s[s] / g ** .5 for s in CELS}; BF = {s: b_s[s] * g ** .5 for s in CELS}
kapF = {s: AF[s] / BF[s] for s in CELS}            # óptimo de F en la celda, relativo a F

SF = json.load(open(R + "sondas_F2_info.json"))
SHA_F2 = SF["base"]["sha256"]; dF2 = REC[SHA_F2]
SONDAS = {(v["celda"], v["a"]): (R + k, REC.get(v["sha256"])) for k, v in SF["sondas"].items()}
SONDAS[("motor_1", 1.4)] = (R + "sonda_F2_motor_1_a14.csv", None)

F = leer_pred(R + "in/final_sonda_global_2025.csv"); T = test_df(F.row_id.values); C = celda(T)
SQF = {s: np.sqrt(F.prediction.values[C == s]).sum() for s in CELS}


def s_de(m):
    return {s: np.sqrt(m[C == s]).sum() / SQF[s] for s in CELS}


def nivel(sv):
    return sum(AF[s] * (1 - 1 / sv[s]) + BF[s] * (1 - sv[s]) for s in CELS)


def d2(sv, G):
    return dF + nivel(sv) + sum(G.get(s, 0.0) / sv[s] for s in CELS)


def leer(p):
    d = leer_pred(p); assert (d.row_id.values == F.row_id.values).all(); return d.prediction.values


def parabola(pts):
    x = np.array([p[0] for p in pts]); y = np.array([p[1] for p in pts]); c = np.polyfit(x, y, 2)
    return c, (-c[1] / (2 * c[0]) if c[0] < 0 else None)


m_F2 = leer(R + "F2_ncb_previos_2025.csv"); s_F2 = s_de(m_F2)
GF2_total = dF2 - dF - nivel(s_F2)          # = Σ G_s(F2)/s_s(F2)


def reparto_F2(w):
    """G_s(F2) con pesos w (suman 1) sobre Σ G_s/s_s = medido"""
    k = GF2_total / sum(w[s] / s_F2[s] for s in w); return {s: k * w[s] for s in w}


def forma_celda(cel, GF2, redondeo=None):
    """ganancia de forma a Σ√μ fijo (G(sonda) − G(F2)) en cada a sondeada; redondeo: dict de perturbaciones de las puntuaciones"""
    pts = [(1.0, 0.0)]; info = {}
    d_f2 = dF2 + (redondeo or {}).get("F2", 0.0)
    for (cc, a), (p, sc) in SONDAS.items():
        if cc != cel or sc is None: continue
        sc = sc + (redondeo or {}).get((cc, a), 0.0)
        sv = dict(s_F2); sv[cel] = s_de(leer(p))[cel] if (cc, a) not in _cache else _cache[(cc, a)]
        _cache[(cc, a)] = sv[cel]
        # D²(p) − D²(F2) = [Nivel(p) − Nivel(F2)] + G_p/s_p − G_F2/s_F2   (solo cambia la celda)
        Gp = sv[cel] * (sc - d_f2 - (nivel(sv) - nivel(s_F2)) + GF2.get(cel, 0.0) / s_F2[cel])
        pts.append((a, Gp - GF2.get(cel, 0.0))); info[a] = {"s": sv[cel], "s_rel_F2": sv[cel] / s_F2[cel], "G_forma": Gp - GF2.get(cel, 0.0)}
    c, v = parabola(pts)
    return {"puntos": pts, "coef": c.tolist(), "vertice": v, "info": info}


_cache = {}

if __name__ == "__main__":
    out = {"nivel_F": {"A_F": AF, "B_F": BF, "kappa_F": kapF, "c_opt": c_opt, "cred_rel_F": {s: cred[s] / g for s in CELS}},
           "comprobacion_final_salida": {}}
    fin = json.load(open(R + "final_salida.txt"))
    out["comprobacion_final_salida"] = {s: [c_opt[s] - fin["nivel"]["c_opt"][s], cred[s] - fin["nivel"]["cred"][s]] for s in CELS}
    out["prevision_cred_sobre_F"] = dF + nivel({s: (cred[s] / g) ** .5 for s in CELS})
    out["prevision_cred_sobre_F_autor"] = fin["nivel"]["d2_F_celda_cred"]
    out["s_F2"] = s_F2; out["nivel_F2"] = nivel(s_F2); out["G_F2_total_medido"] = GF2_total
    # reparto de la ganancia de orden de F2 por celda: evidencia local (revisor D: 23→24 motor_1 +0,0026, contents_1 +0,0007, buildings_0 −0,0001)
    W = {"local_D": {"motor_1": 0.79, "contents_1": 0.21}, "todo_motor_1": {"motor_1": 1.0},
         "proporcional_A": {s: AF[s] / sum(AF.values()) for s in CELS}}
    out["forma"] = {}
    for nm, w in W.items():
        GF2 = reparto_F2(w); o = {"G_F2": GF2}
        for cel in ["motor_1", "buildings_1", "contents_1"]:
            o[cel] = forma_celda(cel, GF2)
        out["forma"][nm] = o
    # aproximación de H (K* constante, sin interacción) para comparar
    fug = json.load(open(R + "exp26/fuga_celdas.json"))
    out["vertice_H"] = {c: fug[c]["sin_nivel"]["vertice"] for c in fug}; out["vertice_original"] = {c: fug[c]["original"]["vertice"] for c in fug}
    # sensibilidad del vértice de motor_1 al redondeo (±5e-6 uniforme en las tres puntuaciones)
    rng = np.random.default_rng(7); vs = []
    GF2 = reparto_F2(W["local_D"])
    for _ in range(4000):
        r = {"F2": rng.uniform(-5e-6, 5e-6), ("motor_1", 0.6): rng.uniform(-5e-6, 5e-6), ("motor_1", 0.8): rng.uniform(-5e-6, 5e-6)}
        vs.append(forma_celda("motor_1", GF2, r)["vertice"])
    vs = np.array([v for v in vs if v is not None])
    out["vertice_motor_1_redondeo"] = {"p05": float(np.quantile(vs, .05)), "p50": float(np.median(vs)), "p95": float(np.quantile(vs, .95)), "sd": float(vs.std())}
    json.dump(out, open(R + "revision/J_nivel.json", "w"), indent=1, default=float, ensure_ascii=False)
    print(json.dumps(out, indent=1, default=float, ensure_ascii=False))
