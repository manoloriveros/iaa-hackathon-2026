"""Construye el final de la misión 0,17 a partir de las puntuaciones públicas (recibos por SHA).
Uso: python construir_final.py recibos.json [--prueba]
- Nivel por celda: sonda por celda sobre F (álgebra de resolver_celda.py, paradas preinscritas).
- Forma por celda (motor_1, buildings_1, contents_1): parábola en a por (a_bajo, a_alto y 1,0 = F2); a_final = 1 + Z (a* − 1) si es cóncava
  y a* ∈ [0,3; 1,8]; si no, 1. Z de sigma_forma.json (τ 0,25).
- Final = F2 con la forma de cada celda (razón de nivel Tweedie local) × factor de nivel de la celda relativo a F (f_s / g).
Escribe final_creible_2025.csv (selección) y final_pleno_2025.csv (información), y final_info.json."""
import sys, json, hashlib
import numpy as np, pandas as pd
exec(open("construir_F2.py").read().split("F = pd.read_csv")[0])
pre = json.load(open("in/preinscripcion.json")); B = pre["base"]; CEL = pre["celdas"]; DED = pre["celda_deducida"]
SF = json.load(open("sondas_F2_info.json")); SIG = json.load(open("sigma_forma.json"))
K, LO, HI = 1.2, 0.75, 1.33
nombre_sha = {B["sha256"]: ("F", None)}; nombre_sha.update({v["sha256"]: ("celda", v["celda"]) for v in pre["sondas"].values()})
nombre_sha[SF["base"]["sha256"]] = ("F2", None); nombre_sha.update({v["sha256"]: ("forma", (v["celda"], v["a"])) for v in SF["sondas"].values()})
def resolver(sc):
    bA, bB, g, cg = B["beta_A"], B["beta_B"], B["g"], B["c_optimo_global"]; dF = sc["F"]
    b_s = {s: bB * CEL[s]["cuota_raiz_mu"] for s in CEL}; a_s = {}
    for s in CEL:
        if s != DED: a_s[s] = (dF - sc[("celda", s)] - b_s[s] * ((g * K) ** 0.5 - g ** 0.5)) / ((g * K) ** -0.5 - g ** -0.5)
    a_s[DED] = bA - sum(a_s.values())
    assert all(v > 0 for v in a_s.values()), ("a_s no positivo", a_s)
    cs = {s: a_s[s] / b_s[s] for s in CEL}
    grande = [s for s in CEL if abs(np.log(cs[s] / cg)) > max(0.7, 3 * CEL[s]["sigma"])]
    cred = {s: float(np.clip((cs[s] / cg) ** CEL[s]["Z"], LO, HI)) * g for s in CEL}
    pleno = {s: float(np.clip(cs[s], g * LO, g * HI)) for s in CEL}
    prev = lambda f: dF - sum(a_s[s] * (f[s] ** -0.5 - g ** -0.5) + b_s[s] * (f[s] ** 0.5 - g ** 0.5) for s in CEL)
    return {"c_opt": cs, "rel_global": {s: cs[s] / cg for s in CEL}, "cred": cred, "pleno": pleno, "grande": grande,
            "d2_F_celda_cred": prev(cred), "d2_F_celda_pleno": prev(pleno), "g": g}
def parabola(pts):
    a = np.array([p[0] for p in pts]); d = np.array([p[1] for p in pts]); c2, c1, c0 = np.polyfit(a, d, 2)
    if c2 >= 0: return None, (c2, c1, c0)
    v = -c1 / (2 * c2); return (v if 0.3 <= v <= 1.8 else None), (c2, c1, c0)
def construir(sc, base_df, t, sets_eval=None):
    lv = resolver(sc); out = {"nivel": lv, "forma": {}}
    for cc in ["motor_1", "buildings_1", "contents_1"]:
        pts = [(1.0, sc["F2"])] + [(a, sc[("forma", (cc, a))]) for (c_, a) in [k[1] for k in sc if isinstance(k, tuple) and k[0] == "forma"] if c_ == cc]
        if len(pts) < 3: out["forma"][cc] = {"a_final": 1.0, "nota": "faltan puntos"}; continue
        v, coef = parabola(pts); Z = SIG[cc]["Z_tau0.25"]
        out["forma"][cc] = {"puntos": pts, "vertice": v, "coef": coef, "Z": Z,
                            "a_cred": 1.0 if v is None else 1 + Z * (v - 1), "a_pleno": 1.0 if v is None else v,
                            "d2_vertice": None if v is None else float(np.polyval(coef, v))}
    res = {}
    for modo in ("cred", "pleno"):
        m = base_df.prediction.values.copy(); c = celda(t)
        for cc, fz in out["forma"].items():
            a = fz.get(f"a_{modo}", 1.0)
            if a != 1.0:
                tt = t.copy(); tt["m"] = m; m2 = aplicar(tt, {cc: a}); i = c == cc
                rs = []
                for k_, s_ in ser.items():
                    cs_ = celda(s_); j = cs_ == cc; mm = aplicar(s_, {cc: a}); rs.append(kopt(s_.y.values[j], mm[j]) / kopt(s_.y.values[j], s_.m.values[j]))
                m[i] = m2[i] * float(np.mean(rs)); fz[f"razon_{modo}"] = float(np.mean(rs))
        f = lv[modo]
        for cc in CEL: m[c == cc] *= f[cc] / lv["g"]
        res[modo] = m
    return out, res
ser = {}
for k_ in ["DEV23_T2b", "HOLD24_T2b", "HOLD24_A1", "HOLD24_mezcla"]:
    s_ = sets[k_].copy(); s_["m"] = transformar(s_); ser[k_] = s_
if __name__ == "__main__" and "--prueba" not in sys.argv:
    sc = {}
    for r in json.load(open(sys.argv[1])):
        if r["sha256"] not in nombre_sha: print("AVISO: SHA desconocido, se ignora:", r["sha256"][:12]); continue
        tipo, cual = nombre_sha[r["sha256"]]; sc[tipo if cual is None else (tipo, cual)] = float(r["d2"])
    falta = ({"F", "F2"} | {("celda", s) for s in CEL if s != DED}) - set(sc)
    if falta: sys.exit(f"PARADA: faltan puntuaciones obligatorias {falta}")
    falta_forma = {("forma", (v["celda"], v["a"])) for v in SF["sondas"].values()} - set(sc)
    if falta_forma: print("AVISO: faltan sondas de forma (esa celda queda con a = 1):", falta_forma)
    lo, hi = pre["d2_F_intervalo_redondeo"]
    if sc["F"] + 5e-6 < lo - 1e-9 or sc["F"] - 5e-6 > hi + 1e-9: sys.exit(f"PARADA preinscrita: D2(F) = {sc['F']} fuera de [{lo}, {hi}]")
    assert hashlib.sha256(open("F2_ncb_previos_2025.csv", "rb").read()).hexdigest() == SF["base"]["sha256"], "F2 en disco distinto del F2 de las sondas"
    for v in SF["sondas"].values():
        cc_, a_ = v["celda"], v["a"]; rs_ = [kopt(s_.y.values[celda(s_) == cc_], aplicar(s_, {cc_: a_})[celda(s_) == cc_]) / kopt(s_.y.values[celda(s_) == cc_], s_.m.values[celda(s_) == cc_]) for s_ in ser.values()]
        assert abs(np.mean(rs_) - v["razon_nivel"]) < 6e-5, ("razón de forma distinta de la de las sondas", cc_, a_, np.mean(rs_))
    F2 = pd.read_csv("F2_ncb_previos_2025.csv", dtype={"row_id": str}); t = b.loc[F2.row_id].copy(); t["m"] = F2.prediction.values; t["c_fila"] = 1.0
    info, res = construir(sc, F2, t)
    if info["nivel"]["grande"] and "--forzar" not in sys.argv:
        print(json.dumps(info, indent=1, default=str)); sys.exit("PARADA preinscrita de nivel en " + str(info["nivel"]["grande"]))
    for modo, m in res.items():
        out = F2.copy(); out["prediction"] = m; assert len(out) == 209063 and np.isfinite(m).all() and (m > 0).all()
        p = f"final_{'creible' if modo == 'cred' else 'pleno'}_2025.csv"; out.to_csv(p, index=False, float_format="%.6f", lineterminator="\n")
        info[p] = {"sha256": hashlib.sha256(open(p, "rb").read()).hexdigest(), "total": round(float(m.sum()), 2)}
    json.dump(info, open("final_info.json", "w"), indent=1, default=str, ensure_ascii=False); print(json.dumps(info, indent=1, default=str, ensure_ascii=False))
