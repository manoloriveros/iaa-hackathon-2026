"""K tarea 5d: previsión pública de F4 y variantes frente a F3b: nivel exacto (archivos) + orden por celda (parte ortogonal local,
media de direcciones) + coste público de la compresión (parábolas de las sondas) + ruido del tercio público."""
import sys; sys.path.insert(0, "/home/claude/m017/revision")
from K_lib import *
from math import erf, sqrt
chk = json.load(open(OUT + "/K_t4b_checks.json")); A = chk["nivel_publico"]["A"]; B = chk["nivel_publico"]["B"]
orto = json.load(open(OUT + "/K_t5c_ortogonal.json")); gb = json.load(open(OUT + "/K_t5b_g_noponderado.json"))
pub = json.load(open(OUT + "/K_t5_public.json"))
F = pd.read_csv(R + "/in/final_sonda_global_2025.csv", dtype={"row_id": str}); t = LAB.loc[F.row_id]; c = celda(t)
sF = {cc: np.sqrt(F.prediction.values[c == cc]).sum() for cc in CELS}
def s_of(p):
    x = pd.read_csv(p, dtype={"row_id": str}).prediction.values; return {cc: np.sqrt(x[c == cc]).sum() / sF[cc] for cc in CELS}
def nivel(sv): return sum(A[s] * (1 - 1 / sv[s]) + B[s] * (1 - sv[s]) for s in CELS)
s3 = s_of(R + "/exp26/F3b_2025.csv")
G3 = {"motor_0": 0.0004, "motor_1": 0.0030, "buildings_0": 0.0001, "buildings_1": 0.0003, "contents_0": 0.0002, "contents_1": 0.0006}
D23 = ["DEV23->HOLD24_T2b", "DEV23->HOLD24_mezcla", "DEV23->HOLD24_A1"]; D24 = "HOLD2->DEV23_T2b"
cellest = {}
for cc in CELS:
    o23 = np.mean([orto[f"{d}|{cc}|u"]["g_ortogonal_pb"] for d in D23]); o24 = orto[f"{D24}|{cc}|u"]["g_ortogonal_pb"]
    t23 = np.mean([orto[f"{d}|{cc}|u"]["g_total_pb"] for d in D23]); t24 = orto[f"{D24}|{cc}|u"]["g_total_pb"]
    sd23 = gb[f"DEV23->HOLD24_T2b|{cc}|todas"]["sd_pb"]; sd24 = gb[f"{D24}|{cc}|todas"]["sd_pb"]
    sdm = 0.5 * np.sqrt(sd23 ** 2 + sd24 ** 2); het = abs(o23 - o24) / 2
    cellest[cc] = {"orto_23": round(o23, 1), "orto_24": round(o24, 1), "orto_media": round(0.5 * (o23 + o24), 1), "total_media": round(0.5 * (t23 + t24), 1),
                   "sd_media_boot": round(sdm, 1), "semi_dif_direcciones": round(het, 1), "sd_usada": round(max(sdm, het), 1)}
par = chk["parabola_publica"]
VARS = {"F4_elegido": (R + "/exp26/F4_2025.csv", {cc: 1 for cc in CELS}),
        "sin_edif": (OUT + "/K_F4_sinedif_2025.csv", {cc: (0 if cc.startswith("buildings") else 1) for cc in CELS}),
        "solo_REN": (OUT + "/K_F4_soloREN_2025.csv", {cc: (1 if cc.endswith("_0") else 0) for cc in CELS}),
        "solo_REN_sin_edif": (OUT + "/K_F4_soloREN_sinedif_2025.csv", {cc: (1 if cc in ("motor_0", "contents_0") else 0) for cc in CELS})}
noise = {"F4_elegido": pub["ruido"]["elegido"]["sd_publico_realizacion"], "sin_edif": pub["ruido"]["sin_edif"]["sd_publico_realizacion"],
         "solo_REN": pub["ruido"]["solo_REN"]["sd_publico_realizacion"], "solo_REN_sin_edif": pub["ruido"]["solo_REN"]["sd_publico_realizacion"]}
Phi = lambda z: 0.5 * (1 + erf(z / sqrt(2)))
out = {"celdas_orden_pb": cellest}
for vn, (p, on) in VARS.items():
    sv = s_of(p)
    lvl = nivel(sv) - nivel(s3) + sum(G3[cc] * (1 / sv[cc] - 1 / s3[cc]) for cc in CELS)
    ordm = sum(on[cc] * cellest[cc]["orto_media"] * 1e-4 * A[cc] * (1 - G3[cc] / A[cc]) / sv[cc] for cc in CELS)
    ordt = sum(on[cc] * cellest[cc]["total_media"] * 1e-4 * A[cc] * (1 - G3[cc] / A[cc]) / sv[cc] for cc in CELS)
    comp = sum(on[cc] * par[cc]["coste_publico_compresion"] for cc in ("motor_1", "buildings_1", "contents_1"))
    sd_est = np.sqrt(sum((on[cc] * cellest[cc]["sd_usada"] * 1e-4 * A[cc] / sv[cc]) ** 2 for cc in CELS))
    mu = lvl + ordm + comp; sd_pub = np.sqrt(sd_est ** 2 + noise[vn] ** 2); sd_priv = np.sqrt(sd_est ** 2 + noise[vn] ** 2 / 2)
    mu_half = lvl + 0.5 * ordm + comp   # traslado a la mitad (precedente de F2: 24 % de la evidencia local)
    out[vn] = {"s_por_celda_vs_F": {k: round(v, 5) for k, v in sv.items()}, "nivel_vs_F3b": round(lvl, 6), "orden_ortogonal": round(ordm, 6),
               "orden_total_local_con_compresion": round(ordt, 6), "compresion_publica": round(comp, 6),
               "media": round(mu, 6), "media_traslado_mitad": round(mu_half, 6), "sd_estimacion": round(float(sd_est), 6), "sd_ruido_publico": noise[vn],
               "p10_p90_publico": [round(mu - 1.2816 * sd_pub, 5), round(mu + 1.2816 * sd_pub, 5)],
               "P_empeora_publico": round(Phi(-mu / sd_pub), 3), "P_empeora_privado": round(Phi(-mu / sd_priv), 3),
               "P_empeora_publico_traslado_mitad": round(Phi(-mu_half / sd_pub), 3)}
d2F3b_J = 0.1665   # previsión central de J para F3 (F3b difiere de F3 en forma/factores; ver informe)
jdump(out, OUT + "/K_t5d_variantes.json")
print(json.dumps(out, indent=1))
