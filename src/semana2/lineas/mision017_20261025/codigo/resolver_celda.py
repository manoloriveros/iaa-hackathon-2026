"""Resolutor de la sonda por ramo × nuevo negocio (misma álgebra y paradas que sonda_segmento_resolver.py de la sesión nocturna),
que además construye el final sobre F2 (NCB y siniestros previos, forma 0,9 en renovación de autos). Uso: python resolver_celda.py recibos.json [--forzar]
recibos.json = lista de {"sha256": ..., "d2": ...} con F (42659dbb…) y las cinco sondas."""
import hashlib, json, sys
import numpy as np, pandas as pd
pre = json.load(open("in/preinscripcion.json")); B = pre["base"]; CEL = pre["celdas"]; DED = pre["celda_deducida"]
LO, HI, K = 0.75, 1.33, 1.2
FILES = {B["sha256"]: "F"}; FILES.update({v["sha256"]: v["celda"] for v in pre["sondas"].values()})
args = {}
for r in json.load(open(sys.argv[1])):
    assert r["sha256"] in FILES, r["sha256"][:12]; args[FILES[r["sha256"]]] = float(r["d2"])
need = ["F"] + [s for s in CEL if s != DED]; assert sorted(args) == sorted(need), set(need) - set(args)
bA, bB, g, cg = B["beta_A"], B["beta_B"], B["g"], B["c_optimo_global"]; dF = args["F"]; res = {"d2": args}
lo, hi = pre["d2_F_intervalo_redondeo"]
if dF + 5e-6 < lo - 1e-9 or dF - 5e-6 > hi + 1e-9: res["parada"] = "D2(F) fuera del intervalo previsto"; print(json.dumps(res, indent=1)); sys.exit(2)
b_s = {s: bB * CEL[s]["cuota_raiz_mu"] for s in CEL}; a_s = {}
for s in need[1:]:
    a_s[s] = (dF - args[s] - b_s[s] * ((g * K) ** 0.5 - g ** 0.5)) / ((g * K) ** -0.5 - g ** -0.5)
a_s[DED] = bA - sum(a_s.values())
if any(not (a_s[s] > 0) for s in CEL): res.update({"a_s": a_s, "parada": "a_s no positivo"}); print(json.dumps(res, indent=1)); sys.exit(2)
cstar = {s: a_s[s] / b_s[s] for s in CEL}; fac = {}; grande = []
for s in CEL:
    rel = cstar[s] / cg
    if abs(np.log(rel)) > max(0.7, 3 * CEL[s]["sigma"]): grande.append(s)
    fac[s] = g * float(np.clip(rel ** CEL[s]["Z"], LO, HI))
pleno = {s: float(np.clip(cstar[s], g * LO, g * HI)) for s in CEL}
prev = lambda f: dF - sum(a_s[s] * (f[s] ** -0.5 - g ** -0.5) + b_s[s] * (f[s] ** 0.5 - g ** 0.5) for s in CEL)
res.update({"a_s": a_s, "b_s": b_s, "c_optimo_publico": {s: round(v, 4) for s, v in cstar.items()}, "relativo_global": {s: round(v / cg, 4) for s, v in cstar.items()},
            "factor_credible": {s: round(v, 4) for s, v in fac.items()}, "parada_grande": grande,
            "d2_publico_previsto_F_celda_credible": round(prev(fac), 5), "d2_publico_previsto_F_celda_pleno": round(prev(pleno), 5)})
if grande and "--forzar" not in sys.argv:
    res["parada"] = f"|log(c*_s/c*_g)| > max(0,7; 3 sigma) en {grande}: no se escribe el final (preinscripción)"
    json.dump(res, open("resultado_celda.json", "w"), indent=1, ensure_ascii=False); print(json.dumps(res, indent=1, ensure_ascii=False)); sys.exit(2)
b = pd.read_parquet("base_etiquetas.parquet").set_index("row_id")
for nombre, base_csv, fuente in (("F_celda", "in/final_sonda_global_2025.csv", "F"), ("F2_celda", "F2_ncb_previos_2025.csv", "F2")):
    x = pd.read_csv(base_csv, dtype={"row_id": str}); t = b.loc[x.row_id]
    cel = (t.line + "_" + t.new_business.astype(int).astype(str)).values
    for etiqueta, f in (("credible", fac), ("pleno", pleno)):
        out = x.copy(); out["prediction"] = x.prediction.values * np.array([f[c] / g for c in cel])
        assert len(out) == 209063 and (out.prediction > 0).all()
        p = f"{nombre}_{etiqueta}_2025.csv"; out.to_csv(p, index=False, float_format="%.6f", lineterminator="\n")
        res[p] = {"sha256": hashlib.sha256(open(p, "rb").read()).hexdigest(), "total": round(float(out.prediction.sum()), 2)}
json.dump(res, open("resultado_celda.json", "w"), indent=1, ensure_ascii=False); print(json.dumps(res, indent=1, ensure_ascii=False))
