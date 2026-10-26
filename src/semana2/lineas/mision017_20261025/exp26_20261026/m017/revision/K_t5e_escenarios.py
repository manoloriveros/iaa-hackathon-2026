"""K tarea 5e: escenarios de traslado al público del paso FSp (F4 − F3b) y probabilidad de empeorar."""
import sys; sys.path.insert(0, "/home/claude/m017/revision")
from K_lib import *
from math import erf, sqrt
Phi = lambda z: 0.5 * (1 + erf(z / sqrt(2)))
v = json.load(open(OUT + "/K_t5d_variantes.json")); ce = v["celdas_orden_pb"]; chk = json.load(open(OUT + "/K_t4b_checks.json")); A = chk["nivel_publico"]["A"]
s4 = v["F4_elegido"]["s_por_celda_vs_F"]; lvl = v["F4_elegido"]["nivel_vs_F3b"]; comp = v["F4_elegido"]["compresion_publica"]
dv = {l: json.load(open(f"{OUT}/K_t1c_fsp_reentreno_{l}.json"))[l]["desarrollado_2024"] for l in LINES}
W = {"motor": 0.25, "buildings": 0.25, "contents": 0.5}
# cociente NB año completo / renovación año completo de la ganancia de mezcla en el desarrollado 2024 (en dominio)
ratio = {l: dv[l]["NB_anio_completo"][f"gan_w{W[l]}"] / dv[l]["REN_anio_completo"][f"gan_w{W[l]}"] for l in LINES}
def pub(cc, gpb): return gpb * 1e-4 * A[cc] / s4[cc]
ren = sum(pub(c, ce[c]["orto_media"]) for c in CELS if c.endswith("_0"))
esc = {}
esc["1_emergente_ortogonal"] = sum(pub(c, ce[c]["orto_media"]) for c in CELS) + comp + lvl
esc["2_emergente_con_compresion_local"] = sum(pub(c, ce[c]["total_media"]) for c in CELS) + lvl
esc["3_REN_mas_NB_por_cociente_desarrollado"] = ren + sum(pub(f"{l}_1", ce[f"{l}_0"]["orto_media"] * max(ratio[l], 0)) for l in LINES) + comp + lvl
esc["3b_igual_con_traslado_24pc"] = 0.24 * (esc["3_REN_mas_NB_por_cociente_desarrollado"] - comp - lvl) + comp + lvl
centro = float(np.mean([esc["1_emergente_ortogonal"], esc["3b_igual_con_traslado_24pc"], 0.5 * (esc["1_emergente_ortogonal"] + esc["3_REN_mas_NB_por_cociente_desarrollado"])]))
sd = float(np.sqrt(0.0020 ** 2 + v["F4_elegido"]["sd_ruido_publico"] ** 2))
out = {"cociente_NB_REN_desarrollado": {k: round(x, 3) for k, x in ratio.items()}, "escenarios": {k: round(x, 6) for k, x in esc.items()},
       "centro": round(centro, 6), "sd": round(sd, 6), "p10_p90": [round(centro - 1.2816 * sd, 5), round(centro + 1.2816 * sd, 5)],
       "P_empeora": round(Phi(-centro / sd), 3), "P_empeora_por_escenario": {k: round(Phi(-x / sd), 3) for k, x in esc.items()},
       "edificios_NB": {"media_pub": round(pub("buildings_1", ce["buildings_1"]["orto_media"]), 6), "sd_pub": round(pub("buildings_1", ce["buildings_1"]["sd_usada"]), 6),
                        "P_empeora": round(Phi(pub("buildings_1", ce["buildings_1"]["orto_media"]) / pub("buildings_1", ce["buildings_1"]["sd_usada"]) * -1), 3)}}
F3b_pub = 0.15948 + chk["nivel_publico"]["nivel_F3b"] + 0.00117 + 0.00184 / s4["motor_1"] * (s4["motor_1"] / 1.0433) + 0.0014
out["D2_publico_F3b_anclado"] = round(F3b_pub, 5); out["D2_publico_F4_centro"] = round(F3b_pub + centro, 5)
jdump(out, OUT + "/K_t5e_escenarios.json"); print(json.dumps(out, indent=1))
