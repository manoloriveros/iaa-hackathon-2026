"""K tarea 1b: mezcla de peligros emergente/desarrollado por año (2023 y 2024), frecuencia y severidad con completitud por peligro."""
import sys, os; sys.path.insert(0, "/home/claude/m017/revision")
from K_lib import *
os.environ["MLIND_RAIZ"] = "/home/claude/ml2"; sys.path.insert(0, "/home/claude/ml2/codigo")
from completitud import por_peligro
FT = fsp_tables("")
res = {}
for l in LINES:
    per = FT[l]["per"]
    d0 = pd.read_parquet(f"{T}/base_developed_{l}.parquet", columns=["row_id", "year", "exposure", "period_start", "period_end"] + [f"y_{p}" for p in per])
    d0 = d0.merge(pd.read_parquet(f"{T}/conteos_developed_{l}.parquet"), on="row_id")
    be = FT[l]["be"]; f = FT[l]["f"]; cn = FT[l]["cn"]
    for yr in (2023, 2024):
        d = d0[d0.year == yr]; e = be[(be.conjunto == "train") & (be.year.astype(int) == yr)].index
        out = {}
        for p in per:
            cpd = por_peligro(l, p, d.period_start, d.period_end); ed = (d.exposure * cpd).sum()
            ee = (LAB.exposure.reindex(e).values * f.loc[e, f"cp_{p}"].values).sum()
            fd, fe = d[f"n_{p}"].sum() / ed, cn.loc[e, f"n_{p}"].sum() / ee
            cd, ce = d[f"y_{p}"].sum() / ed, be.loc[e, f"y_{p}"].sum() / ee
            out[p] = {"N_E": int(cn.loc[e, f"n_{p}"].sum()), "frec_E_D": round(fe / fd, 3), "sev_E_D": round((ce / fe) / (cd / fd), 3) if fe > 0 else None, "cD": cd, "cE": ce}
        sd, se = sum(v["cD"] for v in out.values()), sum(v["cE"] for v in out.values())
        for p in out:
            out[p]["cuota_D"] = round(out[p].pop("cD") / sd, 3); out[p]["cuota_E"] = round(out[p].pop("cE") / se, 3)
        res[f"{l}|{yr}"] = out
        print(l, yr, out)
jdump(res, OUT + "/K_t1b_mezcla.json")
