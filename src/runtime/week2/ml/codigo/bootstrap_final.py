"""Customer-bootstrap intervals for the comparisons cited in the report."""
import json
import numpy as np, pandas as pd
from comun import *
from evaluar import bootstrap_dif
import receta

res = {}
t = receta.tabla("dev")
m = {}
for c, cal in [("T2b", "ramo"), ("R0", "ramo"), ("T1wp", "ramo"), ("G1", "ramo"), ("N1", "ramo_nb"), ("N2a", "ramo_nb"), ("T2b", "ramo_nb"), ("N3", "ramo_nb")]:
    _, mu, _ = receta.oof_cruzado("dev", [c], cal); m[(c, cal)] = mu
res["DEV_T2b_C1-R0_C1"] = bootstrap_dif(t, m[("T2b", "ramo")], m[("R0", "ramo")])
res["DEV_T2b_C1-T1wp_C1"] = bootstrap_dif(t, m[("T2b", "ramo")], m[("T1wp", "ramo")])
res["DEV_T2b_C1-G1_C1"] = bootstrap_dif(t, m[("T2b", "ramo")], m[("G1", "ramo")])
res["DEV_N2a_C2-N1_C2"] = bootstrap_dif(t, m[("N2a", "ramo_nb")], m[("N1", "ramo_nb")])
res["DEV_N3_C2-T2b_C2"] = bootstrap_dif(t, m[("N3", "ramo_nb")], m[("T2b", "ramo_nb")])
lista = json.load(open(ENTREGA / "lista_congelada.json"))
th = None; hm = {}
for nom in ["T2b_C1", "R0_C1", "T1wp_C2", "G1_C2", "N1_C2", "N2a_C2", "N3_C2", "T2b_C2"]:
    spec = lista["candidatos"][nom]
    p = receta.parametros("dev", spec["componentes"], spec["calib"])
    th, hm[nom] = receta.aplicar("hold", p, None)
res["HOLD_T2b_C1-R0_C1"] = bootstrap_dif(th, hm["T2b_C1"], hm["R0_C1"])
res["HOLD_T2b_C1-T1wp_C2"] = bootstrap_dif(th, hm["T2b_C1"], hm["T1wp_C2"])
res["HOLD_N2a_C2-N1_C2"] = bootstrap_dif(th, hm["N2a_C2"], hm["N1_C2"])
res["HOLD_N3_C2-T2b_C2"] = bootstrap_dif(th, hm["N3_C2"], hm["T2b_C2"])
res["HOLD_T2b_C2-T2b_C1"] = bootstrap_dif(th, hm["T2b_C2"], hm["T2b_C1"])
guardar_json(res, ENTREGA / "bootstrap_final.json")
for k, v in res.items():
    print(k, round(v["dif"], 4), [round(x, 4) for x in v["ic95"]], v["p_mayor"])
