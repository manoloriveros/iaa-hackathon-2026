"""K tarea 1: fuga y corrección de la FSp ligera (lectura de salidas del autor como datos; cálculos propios)."""
import sys; sys.path.insert(0, "/home/claude/m017/revision")
from K_lib import *

res = {}
# --- 1a. entrenamiento solo con desarrollado; años
for l in LINES:
    d = pd.read_parquet(f"{T}/base_developed_{l}.parquet", columns=["row_id", "year", "market", "conjunto"])
    res.setdefault("desarrollado", {})[l] = {"mercados": d.market.unique().tolist(), "anios": sorted(d.year.unique().tolist()),
                                              "conjuntos": d.conjunto.unique().tolist()}
# --- 1b. rondas por peligro (meta del autor)
ron = {}
for suf in ["", "_prod"]:
    for l in LINES:
        m = json.load(open(f"{T}/pred/fsp/{l}{suf}_meta.json"))
        for p, v in m.items():
            ron[f"{l}|{p}|{'dev' if suf == '' else 'prod'}"] = {"rondas_f": v["rondas_f"], "rondas_s": v["rondas_s"], "b0": round(v["b0"], 4), "n_dev": v["n_dev"], "sev_media": round(v["sev_media"], 1)}
res["rondas"] = ron
res["rondas_bajas"] = {k: v for k, v in ron.items() if v["rondas_f"] < 20 or v["rondas_s"] < 5}

FT = fsp_tables(""); FP = fsp_tables("_prod")
# --- 1c. completitud
comp = {}
for l in LINES:
    for nm, F in (("dev", FT), ("prod", FP)):
        f, per, be = F[l]["f"], F[l]["per"], F[l]["be"]
        yr = be.year.reindex(f.index).astype(int).values
        for y_ in (2023, 2024, 2025):
            i = yr == y_
            cps = {p: round(float(np.average(f[f"cp_{p}"].values[i], weights=f[f"f_{p}"].values[i] * f[f"s_{p}"].values[i])), 4) for p in per}
            # completitud de la fila implícita (coste esperado observado / último) frente a c_fila de las etiquetas
            imp = sum(f[f"f_{p}"].values[i] * f[f"cp_{p}"].values[i] * f[f"s_{p}"].values[i] for p in per) / sum(f[f"f_{p}"].values[i] * f[f"s_{p}"].values[i] for p in per)
            cf = LAB.c_fila.reindex(f.index[i]).values
            comp[f"{l}|{nm}|{y_}"] = {"cp_medio_por_peligro": cps, "cp_fila_implicita_media": round(float(imp.mean()), 4),
                                      "c_fila_media": round(float(np.nanmean(cf)), 4),
                                      "corr_cp_impl_c_fila": round(float(np.corrcoef(imp, cf)[0, 1]), 4) if y_ < 2025 else None,
                                      "min_cp": round(float(min(f[f"cp_{p}"].values[i].min() for p in per)), 4),
                                      "max_cp": round(float(max(f[f"cp_{p}"].values[i].max() for p in per)), 4)}
res["completitud"] = comp
# --- 1d. κ: detalle por año, consistencia frecuencia × severidad frente a coste directo, estabilidad entre años
kd = {}
for nm, F in (("dev", FT), ("prod", FP)):
    for l in LINES:
        for yrs in ([2023], [2024], [2023, 2024]):
            kap, det = kappa(F, l, yrs, detail=True)
            kd[f"{l}|{nm}|{'+'.join(map(str, yrs))}"] = {p: {k: round(float(v), 4) for k, v in d.items()} for p, d in det.items()}
res["kappa_detalle"] = kd
# --- 1e. severidad: media predicha (ponderada por siniestros esperados) frente a observada en el emergente; dispersión
sev = {}
for l in LINES:
    f, per, cn, be = FT[l]["f"], FT[l]["per"], FT[l]["cn"], FT[l]["be"]
    tr = be[be.conjunto == "train"].index
    for p in per:
        n = cn.loc[tr, f"n_{p}"].values; s = f.loc[tr, f"s_{p}"].values; yy = be.loc[tr, f"y_{p}"].values
        sev[f"{l}|{p}"] = {"sev_obs_emerg": round(float(yy.sum() / max(n.sum(), 1)), 1), "sev_pred_en_siniestros": round(float((n * s).sum() / max(n.sum(), 1)), 1),
                           "ratio_obs_pred": round(float(yy.sum() / max((n * s).sum(), 1e-9)), 3), "sd_log_s": round(float(np.std(np.log(f[f"s_{p}"].values))), 4),
                           "sd_log_f_tasa": round(float(np.std(np.log(f[f"f_{p}"].values / LAB.exposure.reindex(f.index).values))), 4), "n_emerg": int(n.sum())}
res["severidad"] = sev
# --- 1f. mezcla de peligros: desarrollado frente a emergente (2023), frecuencia y severidad (último)
mix = {}
for l in LINES:
    per = FT[l]["per"]
    d = pd.read_parquet(f"{T}/base_developed_{l}.parquet", columns=["row_id", "year", "exposure", "period_start", "period_end"] + [f"y_{p}" for p in per])
    cd = pd.read_parquet(f"{T}/conteos_developed_{l}.parquet")
    d = d.merge(cd, on="row_id"); d = d[d.year == 2023]
    import importlib, os
    os.environ["MLIND_RAIZ"] = "/home/claude/ml2"; sys.path.insert(0, "/home/claude/ml2/codigo")
    from completitud import por_peligro   # solo para la completitud del desarrollado, que no está en disco
    be = FT[l]["be"]; f = FT[l]["f"]; cn = FT[l]["cn"]
    e23 = be[(be.conjunto == "train") & (be.year.astype(int) == 2023)].index
    out = {}
    for p in per:
        cpd = por_peligro(l, p, d.period_start, d.period_end)
        fr_d = d[f"n_{p}"].sum() / (d.exposure * cpd).sum(); cost_d = d[f"y_{p}"].sum() / (d.exposure * cpd).sum()
        ee = LAB.exposure.reindex(e23).values * f.loc[e23, f"cp_{p}"].values
        fr_e = cn.loc[e23, f"n_{p}"].sum() / ee.sum(); cost_e = be.loc[e23, f"y_{p}"].sum() / ee.sum()
        out[p] = {"frec_ratio_E_D": round(fr_e / fr_d, 3), "sev_ratio_E_D": round((cost_e / fr_e) / (cost_d / fr_d), 3) if fr_e > 0 else None,
                  "coste_ratio_E_D": round(cost_e / cost_d, 3), "cuota_coste_D": cost_d, "cuota_coste_E": cost_e}
    td = sum(v["cuota_coste_D"] for v in out.values()); te_ = sum(v["cuota_coste_E"] for v in out.values())
    for p in out:
        out[p]["cuota_coste_D"] = round(out[p]["cuota_coste_D"] / td, 3); out[p]["cuota_coste_E"] = round(out[p]["cuota_coste_E"] / te_, 3)
    mix[l] = out
res["mezcla_peligros_2023"] = mix
# --- 1g. totales 2025 de la FSp de producción (κ 2023+2024, último) frente a la experiencia 2023/2024 por peligro
tot = {}
for l in LINES:
    f, per, cn, be = FP[l]["f"], FP[l]["per"], FP[l]["cn"], FP[l]["be"]
    kap = kappa(FP, l, [2023, 2024])
    i25 = be[be.conjunto == "test"].index; e25 = LAB.exposure.reindex(i25).values
    r = {}
    for p in per:
        r25 = kap[p] * (f.loc[i25, f"f_{p}"].values * f.loc[i25, f"s_{p}"].values).sum() / e25.sum()
        r25_sin = (f.loc[i25, f"f_{p}"].values * f.loc[i25, f"s_{p}"].values).sum() / e25.sum()
        exp_ = {}
        for y_ in (2023, 2024):
            ii = be[(be.conjunto == "train") & (be.year.astype(int) == y_)].index
            ee = (LAB.exposure.reindex(ii).values * f.loc[ii, f"cp_{p}"].values).sum()
            exp_[y_] = be.loc[ii, f"y_{p}"].sum() / ee
            exp_[f"fsp_{y_}"] = kap[p] * (f.loc[ii, f"f_{p}"].values * f.loc[ii, f"s_{p}"].values).sum() / LAB.exposure.reindex(ii).values.sum()
        r[p] = {"fsp25_por_expo_sin_kappa": r25_sin, "fsp25_por_expo": r25, "exp23_ultimo_por_expo": exp_[2023], "exp24_ultimo_por_expo": exp_[2024],
                "fsp23": exp_["fsp_2023"], "fsp24": exp_["fsp_2024"]}
    tt = {k: sum(v[k] for v in r.values()) for k in ["fsp25_por_expo_sin_kappa", "fsp25_por_expo", "exp23_ultimo_por_expo", "exp24_ultimo_por_expo", "fsp23", "fsp24"]}
    for p in r:
        r[p]["cuota_fsp25"] = round(r[p]["fsp25_por_expo"] / tt["fsp25_por_expo"], 3)
        r[p]["cuota_fsp25_sin_kappa"] = round(r[p]["fsp25_por_expo_sin_kappa"] / tt["fsp25_por_expo_sin_kappa"], 3)
        r[p]["cuota_exp23"] = round(r[p]["exp23_ultimo_por_expo"] / tt["exp23_ultimo_por_expo"], 3)
        r[p]["cuota_exp24"] = round(r[p]["exp24_ultimo_por_expo"] / tt["exp24_ultimo_por_expo"], 3)
        r[p]["cuota_fsp_filas23"] = round(r[p]["fsp23"] / tt["fsp23"], 3); r[p]["cuota_fsp_filas24"] = round(r[p]["fsp24"] / tt["fsp24"], 3)
        for k in ["fsp25_por_expo_sin_kappa", "fsp25_por_expo", "exp23_ultimo_por_expo", "exp24_ultimo_por_expo", "fsp23", "fsp24"]: r[p][k] = round(r[p][k], 2)
    r["_total"] = {k: round(v, 2) for k, v in tt.items()}
    r["_kappa_prod"] = {p: round(v, 3) for p, v in kap.items()}
    tot[l] = r
res["totales_2025"] = tot
# --- 1h. coherencia dev frente a prod en las filas 2025 y en 2023/2024
coh = {}
for l in LINES:
    fd, fp_, per, be = FT[l]["f"], FP[l]["f"], FT[l]["per"], FT[l]["be"]
    for y_ in (2023, 2024, 2025):
        ii = be[be.year.astype(int) == y_].index
        a = sum(fd.loc[ii, f"f_{p}"].values * fd.loc[ii, f"s_{p}"].values for p in per); b_ = sum(fp_.loc[ii, f"f_{p}"].values * fp_.loc[ii, f"s_{p}"].values for p in per)
        coh[f"{l}|{y_}"] = {"corr_log": round(float(np.corrcoef(np.log(a), np.log(b_))[0, 1]), 4), "ratio_tot_prod_dev": round(float(b_.sum() / a.sum()), 4)}
res["dev_vs_prod"] = coh
jdump(res, OUT + "/K_t1_fsp.json")
print(json.dumps({k: res[k] for k in ["desarrollado", "rondas_bajas", "dev_vs_prod"]}, indent=1))
for l in LINES:
    print(l, "κ prod", tot[l]["_kappa_prod"])
    for p, v in tot[l].items():
        if not p.startswith("_"): print("  ", p, {k: v[k] for k in ["cuota_fsp25_sin_kappa", "cuota_fsp25", "cuota_exp23", "cuota_exp24", "cuota_fsp_filas23", "cuota_fsp_filas24"]})
    print("  ", tot[l]["_total"])
for k, v in mix.items(): print("mezcla", k, v)
for k, v in comp.items(): print("comp", k, {kk: vv for kk, vv in v.items() if kk != "cp_medio_por_peligro"})
for k, v in sev.items(): print("sev", k, v)
for k, v in kd.items():
    print("kappa", k, {p: (d["N"], d["raw"], round(d["kf"] * d["ks"], 3), d["cost_direct"], d["kap"]) for p, d in v.items()})
