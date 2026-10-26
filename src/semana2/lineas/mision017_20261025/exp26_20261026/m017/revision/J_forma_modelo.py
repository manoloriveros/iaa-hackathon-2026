"""J: comprobación de la forma funcional de la parábola de motor_1 (ajustada con a ≤ 1 y usada en a = 1,30).
Modelo autoconsistente sin ruido: μ_i = κ0·e_i·r_i^a0 (r = tasa de F2), filas 2025 de motor_1 a escala del público.
G(a) = A(F2) − A(m̃_a), m̃_a = forma(F2, a) llevada al Σ√μ de F2. Se compara la parábola por (0,6; 0,8; 1,0) con la curva exacta."""
import sys, json, numpy as np
sys.path.insert(0, "/home/claude/m017/revision")
from J_lib import *
import J_nivel as N
F2 = leer_pred(R + "F2_ncb_previos_2025.csv"); t = test_df(F2.row_id.values); c = celda(t); i = c == "motor_1"
m = F2.prediction.values[i]; e = t.exposure.values[i]
B2 = N.BF["motor_1"] * N.s_F2["motor_1"]; esc = B2 / np.sqrt(m).sum()          # 4/D0 por unidad de Σ√ (público)
K2 = (N.AF["motor_1"] - 0.00093) / N.s_F2["motor_1"] / B2                       # óptimo de F2 en la celda (≈ 1,176)
def shp(a):
    mm = e * (m / e) ** a; mm *= m.sum() / mm.sum(); return mm * (np.sqrt(m).sum() / np.sqrt(mm).sum()) ** 2
res = {}
for a0 in (1.2, 1.33, 1.45):
    mu = shp(a0); mu *= K2 * np.sqrt(m).sum() / np.sum(mu / np.sqrt(m))   # c*(F2) = K2 bajo el modelo
    G = lambda a: esc * (np.sum(mu / np.sqrt(m)) - np.sum(mu / np.sqrt(shp(a))))
    pts = [(1.0, 0.0), (0.6, G(0.6)), (0.8, G(0.8))]; cf = np.polyfit([p[0] for p in pts], [p[1] for p in pts], 2)
    grid = np.round(np.arange(0.9, 1.61, 0.01), 2); Gs = np.array([G(a) for a in grid])
    res[a0] = {"G(0.6)": G(0.6), "G(0.8)": G(0.8), "vertice_parabola": -cf[1] / (2 * cf[0]), "vertice_real": float(grid[Gs.argmax()]),
               "G_real_1.30": G(1.2978), "G_parabola_1.30": float(np.polyval(cf, 1.2978)), "G_real_1.40": G(1.4), "G_parabola_1.40": float(np.polyval(cf, 1.4)),
               "G_real_vertice": float(Gs.max())}
print(json.dumps(res, indent=1, default=float))
json.dump(res, open(R + "revision/J_forma_modelo.json", "w"), indent=1, default=float)

# ajuste exacto (a0, escala) a los dos puntos observados de G (J_nivel, reparto local_D)
from scipy.optimize import brentq
par = N.forma_celda("motor_1", N.reparto_F2({"motor_1": 0.79, "contents_1": 0.21}))
obs = dict(par["puntos"])
def curva(a0):
    mu = shp(a0); mu *= K2 * np.sqrt(m).sum() / np.sum(mu / np.sqrt(m))
    return lambda a: esc * (np.sum(mu / np.sqrt(m)) - np.sum(mu / np.sqrt(shp(a))))
f = lambda a0: (lambda G: G(0.6) / G(0.8) - obs[0.6] / obs[0.8])(curva(a0))
a0 = brentq(f, 1.15, 1.6); G = curva(a0); lam = obs[0.8] / G(0.8)
grid = np.round(np.arange(1.0, 1.7, 0.005), 3); Gs = np.array([G(a) for a in grid]) * lam
ajuste = {"a0": a0, "escala_sobre_modelo": lam, "vertice": float(grid[Gs.argmax()]), "G_1.2978": lam * G(1.2978), "G_1.40": lam * G(1.4),
          "G_parabola_1.2978": float(np.polyval(par["coef"], 1.2978)), "G_parabola_1.40": float(np.polyval(par["coef"], 1.4)),
          "a_cred_modelo": 1 + 0.927 * (float(grid[Gs.argmax()]) - 1), "G_a_cred_modelo": float(lam * G(1 + 0.927 * (float(grid[Gs.argmax()]) - 1))),
          "G_1.3715": lam * G(1.3715)}
s14 = N.s_de(N.leer(R + "sonda_F2_motor_1_a14.csv")); GF2 = N.reparto_F2({"motor_1": 0.79, "contents_1": 0.21})
ajuste["D2_sonda_a14_modelo"] = N.dF + N.nivel(s14) + sum(GF2.get(c, 0) / s14[c] for c in CELS) + (ajuste["G_1.40"]) / s14["motor_1"]
ajuste["D2_sonda_a14_parabola_exacta"] = N.dF + N.nivel(s14) + sum(GF2.get(c, 0) / s14[c] for c in CELS) + ajuste["G_parabola_1.40"] / s14["motor_1"]
print(json.dumps(ajuste, indent=1, default=float))
res["ajuste"] = ajuste
json.dump(res, open(R + "revision/J_forma_modelo.json", "w"), indent=1, default=float)
