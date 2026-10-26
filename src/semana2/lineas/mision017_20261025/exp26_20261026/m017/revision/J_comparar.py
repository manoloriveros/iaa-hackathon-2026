"""J, tarea 4 y resumen: F3 frente a final_creible por celda (totales, nivel en Σ√μ, forma, factores) y previsión final."""
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/m017/revision")
import J_nivel as N
from J_lib import CELS, R, leer_pred

pr = json.load(open(R + "revision/J_prediccion.json")); fm = json.load(open(R + "revision/J_forma_modelo.json"))["ajuste"]
fin = json.load(open(R + "final_salida.txt")); f3i = json.load(open(R + "exp26/F3_info.json"))
X = {k: N.leer(p) for k, p in {"F": R + "in/final_sonda_global_2025.csv", "F3": R + "exp26/F3_2025.csv",
                                  "FC": R + "revision/J_final_creible_2025.csv", "F3sf": R + "revision/J_F3_sinfac_2025.csv"}.items()}
C = N.C; S = pr["s_por_celda"]
tab = {}
for c in CELS:
    i = C == c; lr = np.log(X["F3"][i] / X["FC"][i]); lrs = np.log(X["F3sf"][i] / X["FC"][i])
    tab[c] = {"total_F": X["F"][i].sum(), "total_FC": X["FC"][i].sum(), "total_F3": X["F3"][i].sum(),
              "F3/FC_suma": X["F3"][i].sum() / X["FC"][i].sum(), "F3/FC_nivel_raiz2": (S["F3"][c] / S["final_creible"][c]) ** 2,
              "F3sf/FC_nivel_raiz2": (S["F3_sinfac"][c] / S["final_creible"][c]) ** 2,
              "sd_log_F3/FC": float(lr.std()), "sd_log_F3sf/FC": float(lrs.std()),
              "nivel_pub_F3": pr["nivel_por_celda"]["F3"][c], "nivel_pub_FC": pr["nivel_por_celda"]["final_creible"][c],
              "a_F3": f3i["a_motor_1"] if c == "motor_1" else 1.0, "a_FC": fin["forma"][c]["a_cred"] if c in fin["forma"] else 1.0,
              "R_F3": f3i["razon_nivel_local"][c], "cred_rel_F": N.cred[c] / N.g}
# previsiones finales (público): parábola exacta y modelo potencia para la forma
GF2 = pr["G_F2"]; A3 = 1 + 0.927 * (1.3212 - 1)
def total(nombre, Gsh, Gfac):
    sv = S[nombre]
    return N.dF + N.nivel(sv) + sum((GF2.get(c, 0) + Gsh.get(c, 0) + Gfac.get(c, 0)) / sv[c] for c in CELS)
Gfac_c = {"cero": {}, "central": {c: v * 0.5 for c, v in pr["G_factores_escenarios"]["REN_transferido"].items()}}
for c in Gfac_c["central"]: Gfac_c["central"][c] += 0.5 * pr["G_factores_escenarios"]["REN_transferido_calibrado_F2"][c]
pv = {}
for forma_nm, g3, gC in (("parabola", {"motor_1": pr["G_forma_F3_m1"]}, pr["G_forma_final_creible"]),
                         ("potencia", {"motor_1": fm["G_1.2978"]}, {"motor_1": fm["G_1.3715"], "contents_1": pr["G_forma_final_creible"]["contents_1"]})):
    pv[forma_nm] = {"F3_sinfac": total("F3_sinfac", g3, {}), "F3_factores_0": total("F3", g3, {}),
                    "F3_central": total("F3", g3, Gfac_c["central"]), "final_creible": total("final_creible", gC, {}),
                    "F3_factores_REN": total("F3", g3, pr["G_factores_escenarios"]["REN_transferido"]),
                    "F3_factores_calibrado": total("F3", g3, pr["G_factores_escenarios"]["REN_transferido_calibrado_F2"])}
fac_central = pv["parabola"]["F3_central"] - pv["parabola"]["F3_factores_0"]
sd_ruido = pr["G_factores_ruido_publico_total_1sd"]
out = {"tabla_celdas": tab, "previsiones_publico": pv, "factores_central": fac_central,
       "nota_ruido": "sd de ruido público de la parte de factores ≈ 0,0014 con tamaño efectivo (J_local2 + n_eff); la de J_prediccion (0,0039) escala sin n_eff y la sobrestima"}
json.dump(out, open(R + "revision/J_comparar.json", "w"), indent=1, default=float, ensure_ascii=False)
df = pd.DataFrame(tab).T
pd.set_option("display.width", 250)
print(df[["total_F", "total_FC", "total_F3", "F3/FC_suma", "F3/FC_nivel_raiz2", "F3sf/FC_nivel_raiz2", "sd_log_F3/FC", "sd_log_F3sf/FC", "nivel_pub_F3", "nivel_pub_FC", "a_F3", "a_FC"]].round(5).to_string())
print(json.dumps(pv, indent=1)); print("factores central", fac_central)
