"""J, tareas 2c, 3 y 4: previsión del D² público de F3, F3 sin factores y final_creible, descompuesta en
nivel (exacto con los recibos), orden de F2 (medido), forma (parábola corregida exacta) y factores (escenarios locales).
D²(X) = D²(F) + Nivel(s_X) + Σ_s G_s(X)/s_s(X)   (ver J_nivel.py)."""
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/m017/revision")
import J_nivel as N
from J_lib import CELS, R, leer_pred, REC

loc = json.load(open(R + "revision/J_local.json")); loc2 = json.load(open(R + "revision/J_local2.json"))
fin = json.load(open(R + "final_salida.txt"))
A3 = 1 + 0.927 * (1.3212 - 1)
AF, BF = N.AF, N.BF

files = {"F": R + "in/final_sonda_global_2025.csv", "F2": R + "F2_ncb_previos_2025.csv", "F3": R + "exp26/F3_2025.csv",
         "F3_sinfac": R + "revision/J_F3_sinfac_2025.csv", "final_creible": R + "revision/J_final_creible_2025.csv",
         "sonda_m1_a14": R + "sonda_F2_motor_1_a14.csv"}
S = {k: N.s_de(N.leer(p)) for k, p in files.items()}
out = {"s_por_celda": S, "nivel": {k: N.nivel(v) for k, v in S.items()},
       "nivel_por_celda": {k: {c: AF[c] * (1 - 1 / v[c]) + BF[c] * (1 - v[c]) for c in CELS} for k, v in S.items()}}

# ---- orden de F2: total medido, reparto por evidencia local ----
GF2 = N.reparto_F2({"motor_1": 0.79, "contents_1": 0.21})
out["G_F2"] = GF2; out["G_F2_total_medido"] = N.GF2_total

# ---- forma: parábolas exactas (ganancia a Σ√μ fijo, unidades de D² público al Σ√μ de F) ----
par = {c: N.forma_celda(c, GF2) for c in ["motor_1", "buildings_1", "contents_1"]}
Gsh = lambda c, a: float(np.polyval(par[c]["coef"], a))
out["vertices_exactos"] = {c: par[c]["vertice"] for c in par}
out["G_forma_F3_m1"] = Gsh("motor_1", A3)
out["G_forma_vertice_m1"] = Gsh("motor_1", par["motor_1"]["vertice"])
aC = {c: fin["forma"][c]["a_cred"] for c in par}
out["G_forma_final_creible"] = {c: Gsh(c, aC[c]) for c in par}

# ---- factores: escenarios ρ (puntos básicos de Q) → G = 2ρA_s(F) ----
fc = ["motor_0", "motor_1", "contents_0", "contents_1"]
esc = {"cero": {c: 0.0 for c in fc},
       "REN_transferido": {"motor_0": 25e-4, "motor_1": 25e-4, "contents_0": 48e-4, "contents_1": 48e-4},
       "CV_en_tiempo": {c: loc2["cv"]["factores"][c] for c in fc},
       "OOT_23a24_T2b": {c: loc["DEV23_T2b->HOLD24_T2b"]["factores"][c] for c in fc},
       "OOT_23a24_mezcla": {c: loc["DEV23_T2b->HOLD24_mezcla"]["factores"][c] for c in fc},
       "OOT_24a23": {c: loc["HOLD24_T2b->DEV23_T2b"]["factores"][c] for c in fc}}
# calibración local → público con F2 (lo único medido en el público con la misma vara)
predF2 = {}
for nm, rr in (("CV_en_tiempo", loc2["cv"]["F2"]), ("OOT_23a24_T2b", loc["DEV23_T2b->HOLD24_T2b"]["F2"]),
               ("OOT_23a24_mezcla", loc["DEV23_T2b->HOLD24_mezcla"]["F2"]), ("OOT_24a23", loc["HOLD24_T2b->DEV23_T2b"]["F2"])):
    predF2[nm] = sum(2 * rr[c] * AF[c] / S["F2"][c] for c in CELS)
out["F2_prevision_local_publico"] = predF2
cal = N.GF2_total / np.mean([predF2["CV_en_tiempo"], predF2["OOT_23a24_T2b"], predF2["OOT_24a23"]])
out["F2_realizado_sobre_previsto"] = cal
esc["REN_transferido_calibrado_F2"] = {c: v * cal for c, v in esc["REN_transferido"].items()}
Gfac = {k: {c: 2 * v[c] * AF[c] for c in fc} for k, v in esc.items()}
se_pub = {c: 2 * loc2["se"][c]["se_rho_pub"] * AF[c] for c in fc}
out["G_factores_escenarios"] = Gfac; out["G_factores_ruido_publico_1sd"] = se_pub
out["G_factores_ruido_publico_total_1sd"] = float(np.sqrt(sum(v ** 2 for v in se_pub.values())))


def pred(nombre, G):
    sv = S[nombre]; parts = {"D2_F": N.dF, "nivel": N.nivel(sv)}
    parts["orden_F2"] = sum(GF2.get(c, 0) / sv[c] for c in CELS)
    parts["forma"] = sum(G.get(("forma", c), 0) / sv[c] for c in CELS)
    parts["factores"] = sum(G.get(("fac", c), 0) / sv[c] for c in CELS)
    parts["total"] = parts["D2_F"] + parts["nivel"] + parts["orden_F2"] + parts["forma"] + parts["factores"]
    return parts


P = {}
P["F2_control"] = pred("F2", {})
P["sonda_m1_a14"] = pred("sonda_m1_a14", {("forma", "motor_1"): Gsh("motor_1", 1.4)})
P["F3_sinfac"] = pred("F3_sinfac", {("forma", "motor_1"): Gsh("motor_1", A3)})
for k, gf in Gfac.items():
    G = {("forma", "motor_1"): Gsh("motor_1", A3)}; G.update({("fac", c): v for c, v in gf.items()})
    P[f"F3|{k}"] = pred("F3", G)
P["final_creible"] = pred("final_creible", {("forma", c): Gsh(c, aC[c]) for c in par})
out["previsiones"] = P

# ---- 2c: nivel de motor_1 en F3 frente al objetivo con Σ√μ fijo y frente al óptimo ----
cred_rel = {c: N.cred[c] / N.g for c in CELS}
tgt = {c: cred_rel[c] ** .5 for c in CELS}
out["s_F3_sobre_objetivo"] = {c: S["F3"][c] / tgt[c] for c in CELS}
out["s_F3sf_sobre_objetivo"] = {c: S["F3_sinfac"][c] / tgt[c] for c in CELS}
out["s_final_creible_sobre_objetivo"] = {c: S["final_creible"][c] / tgt[c] for c in CELS}
# descomposición en motor_1 del salto de Σ√μ: paso F2, paso forma (Σμ fijo + R), paso factores
out["m1_pasos_sqrt"] = {"F2": S["F2"]["motor_1"], "forma_con_R": S["F3_sinfac"]["motor_1"] / tgt["motor_1"] / S["F2"]["motor_1"],
                        "factores_con_R3": S["F3"]["motor_1"] / S["F3_sinfac"]["motor_1"]}
coste = {}
for esc_k in ["cero", "REN_transferido", "CV_en_tiempo"]:
    Gm = GF2.get("motor_1", 0) + Gsh("motor_1", A3) + Gfac[esc_k]["motor_1"]
    f = lambda s: -(AF["motor_1"] - Gm) / s - BF["motor_1"] * s
    s_opt = ((AF["motor_1"] - Gm) / BF["motor_1"]) ** .5
    coste[esc_k] = {"G_m1": Gm, "s_F3": S["F3"]["motor_1"], "s_objetivo": tgt["motor_1"], "s_optimo_publico": s_opt,
                    "nivel_F3_sobre_objetivo": (S["F3"]["motor_1"] / tgt["motor_1"]) ** 2, "nivel_optimo_sobre_objetivo": (s_opt / tgt["motor_1"]) ** 2,
                    "D2_F3_menos_objetivo": f(S["F3"]["motor_1"]) - f(tgt["motor_1"]),
                    "D2_optimo_menos_F3": f(s_opt) - f(S["F3"]["motor_1"])}
out["coste_nivel_motor_1"] = coste
# todas las celdas: F3 con su s frente a s objetivo (Σ√μ fijo) con G de escenario REN_transferido
G_all = {c: GF2.get(c, 0) + (Gsh("motor_1", A3) if c == "motor_1" else 0) + Gfac["REN_transferido"].get(c, 0) for c in CELS}
out["coste_nivel_celdas_F3_vs_objetivo"] = {c: (-(AF[c] - G_all[c]) / S["F3"][c] - BF[c] * S["F3"][c]) - (-(AF[c] - G_all[c]) / tgt[c] - BF[c] * tgt[c]) for c in CELS}
out["coste_nivel_total_F3_vs_objetivo"] = sum(out["coste_nivel_celdas_F3_vs_objetivo"].values())
# interacción nivel × orden: lo que sobrestima sumar «ganancia de nivel sobre F» + «ganancias de orden» sin dividir por s
out["interaccion_F3_REN"] = sum(G_all[c] * (1 / S["F3"][c] - 1) for c in CELS)
# factor de R3 atribuible a los factores (ajuste dentro de muestra) y su efecto de nivel
out["paso_factores_s"] = {c: S["F3"][c] / S["F3_sinfac"][c] for c in CELS}
sv_alt = {c: S["F3"][c] * (S["F3_sinfac"][c] / S["F3"][c] if c in fc else 1) * 1 for c in CELS}
# variante: factores aplicados sin el componente de R3 (Σ√μ casi fijo): s = s_F3sf × (Σ√ factor puro ≈ 1 − 0,0005)
json.dump(out, open(R + "revision/J_prediccion.json", "w"), indent=1, default=float, ensure_ascii=False)
for k, v in P.items(): print(f"{k:38s}", {kk: round(vv, 5) for kk, vv in v.items()})
print("vértices exactos", {c: round(v, 4) for c, v in out["vertices_exactos"].items()})
print("G forma m1 F3", round(out["G_forma_F3_m1"], 6), "vértice", round(out["G_forma_vertice_m1"], 6), "creíble", {c: round(v, 6) for c, v in out["G_forma_final_creible"].items()})
print("F2 local→público", {k: round(v, 5) for k, v in predF2.items()}, "medido", round(N.GF2_total, 5), "cal", round(cal, 3))
print("ruido público factores 1sd", {c: round(v, 5) for c, v in se_pub.items()}, round(out["G_factores_ruido_publico_total_1sd"], 5))
print("s/objetivo F3", {c: round(v, 5) for c, v in out["s_F3_sobre_objetivo"].items()})
print("s/objetivo FC", {c: round(v, 5) for c, v in out["s_final_creible_sobre_objetivo"].items()})
print("m1 pasos", out["m1_pasos_sqrt"])
print(json.dumps(coste, indent=1))
print("coste nivel celdas F3 vs objetivo", {c: round(v, 7) for c, v in out["coste_nivel_celdas_F3_vs_objetivo"].items()}, round(out["coste_nivel_total_F3_vs_objetivo"], 6))
print("interacción", out["interaccion_F3_REN"])
print("nivel por celda", {k: {c: round(x, 6) for c, x in v.items()} for k, v in out["nivel_por_celda"].items() if k in ("F2", "F3", "F3_sinfac", "final_creible")})
