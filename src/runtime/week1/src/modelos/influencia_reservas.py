"""Compare fixed 2024 predictions under nominal and +/-25% case reserves.

Report candidate-minus-reference D2 by line and overall, with 95% paired customer
and address intervals from 1,000 Poisson(1) replicates and a fixed denominator.
Show the ten most favorable customers and the difference without them as an
influence diagnostic, not a removal rule. Attribute the change in the paired
deviance numerator to changing one peril's reserve at a time; this is a row-wise
identity rather than a causal attribution. Keep predictions unchanged.
Usage: python influencia_reservas.py <output.json> <cand>=<spec>@<shape>@<level> <other>=<spec>@<shape>@<level>
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from comun import BASESDIR, LINES, WORK, d2, deviance
from escenarios_reserva import CLAIMS, C
from mezcla3 import labels
from robustez import blend, parse

B = 1000


def reservas():
    c = pd.read_parquet(CLAIMS, columns=["claim_id", "status", "peril", "paid_to_date", "incurred_to_date", "audit_pre00"])
    a = pd.read_parquet(BASESDIR / "tables" / "asignacion_por_siniestro.parquet", columns=["claim_id", "category", "row_id"])
    m = a.merge(c, on="claim_id", how="left", validate="one_to_one")
    ok = (m.status == "open") & (m.category == "unica") & (~m.audit_pre00.fillna(False).astype(bool)) & m.row_id.notna()
    m = m[ok].assign(res=lambda d: d.incurred_to_date - d.paid_to_date, row_id=lambda d: d.row_id.astype(str))
    return m.pivot_table(index="row_id", columns="peril", values="res", aggfunc="sum", fill_value=0.0)


def ic(dif, groups, null, rng):
    codes, inv = np.unique(groups, return_inverse=True)
    d = np.bincount(inv, weights=dif)
    bs = np.concatenate([rng.poisson(1.0, size=(50, len(d))) @ d for _ in range(B // 50)]) / null
    return [round(float(np.quantile(bs, 0.025)), 6), round(float(np.quantile(bs, 0.975)), 6)], d


def main():
    out = sys.argv[1]
    (cn, cspec, cfm), (on, ospec, ofm) = parse(sys.argv[2]), parse(sys.argv[3])
    Rp = reservas()
    ag = pd.read_parquet(f"{C}/crossfit_meta_gam_guard/predictions_V24_crossfit.parquet", columns=["row_id", "meta_gam"]).set_index("row_id").meta_gam
    hh = pd.read_parquet(f"{C}/geometric_meta_nested/V24.parquet", columns=["row_id", "candidate"]).set_index("row_id").candidate
    rng = np.random.default_rng(20261018)
    cols = {"y": [], "cu": [], "ad": [], "ln": [], "R": [], cn: [], on: [], "H": [], "A_G": []}
    for line in LINES:
        ysel, y24, idx25 = labels(line)
        fe = pd.read_parquet(WORK / f"feat_{line}.parquet", columns=["row_id", "customer_id", "address_id", "e_ef_coste", "exposure"])
        fe["row_id"] = fe.row_id.astype(str); fe = fe.set_index("row_id")
        expos = (fe.e_ef_coste.reindex(ysel.index).values, fe.e_ef_coste.reindex(y24.index).values, fe.exposure.reindex(idx25).values)
        cols[cn].append(blend(cspec, cfm, line, ysel, y24, idx25, expos)[2]); cols[on].append(blend(ospec, ofm, line, ysel, y24, idx25, expos)[2])
        cols["H"].append(hh.reindex(y24.index).values); cols["A_G"].append(ag.reindex(y24.index).values)
        cols["y"].append(y24.values); cols["ln"].append(np.full(len(y24), line))
        cols["cu"].append(fe.customer_id.reindex(y24.index).astype(str).values); cols["ad"].append(fe.address_id.reindex(y24.index).astype(str).values)
        cols["R"].append(Rp.reindex(y24.index).fillna(0.0))
    V = {k: (pd.concat(v) if k == "R" else np.concatenate(v)) for k, v in cols.items()}
    R = V["R"]; Rtot = R.sum(axis=1).values
    rep = {"candidato": cn, "comparadores": [on, "H", "A_G"], "escenarios": {}}
    for a in (0.75, 1.0, 1.25):
        y_all = V["y"] + (a - 1.0) * Rtot
        res = {}
        for scope in LINES + ["agregado"]:
            msk = np.ones(len(y_all), bool) if scope == "agregado" else (V["ln"] == scope)
            y = y_all[msk]; null = deviance(y, np.full_like(y, y.mean())).sum()
            row = {"d2": {k: round(d2(y, V[k][msk]), 6) for k in (cn, on, "H", "A_G")}}
            for k in (on, "H", "A_G"):
                dif = deviance(y, V[k][msk]) - deviance(y, V[cn][msk])
                ic_cu, by_cu = ic(dif, V["cu"][msk], null, rng)
                ic_ad, _ = ic(dif, V["ad"][msk], null, rng)
                top = np.sort(by_cu)[::-1][:10]
                row[f"{cn}_menos_{k}"] = {"dif": round(float(dif.sum() / null), 6), "ic95_cliente": ic_cu, "ic95_direccion": ic_ad,
                                          "diez_clientes_mas_favorables": round(float(top.sum() / null), 6),
                                          "dif_sin_esos_diez": round(float((dif.sum() - top.sum()) / null), 6)}
                if a == 1.25:
                    # Row-wise change in paired deviance when increasing only this peril's reserve by 25%.
                    base_num = dif.sum()
                    por_peligro = {}
                    for p in R.columns:
                        rp = R[p].values[msk]
                        if rp.sum() <= 0:
                            continue
                        y0 = V["y"][msk]; yp = y0 + 0.25 * rp
                        d0 = deviance(y0, V[k][msk]) - deviance(y0, V[cn][msk])
                        d1 = deviance(yp, V[k][msk]) - deviance(yp, V[cn][msk])
                        por_peligro[p] = round(float((d1 - d0).sum()), 3)
                    row[f"{cn}_menos_{k}"]["cambio_numerador_por_peligro_a_mas25"] = por_peligro
            res[scope] = row
        rep["escenarios"][str(a)] = res
        print(f"a={a}", flush=True)
        for scope in LINES + ["agregado"]:
            r = res[scope]
            print("  ", scope, "D2", r["d2"], flush=True)
            for k in (on, "H", "A_G"):
                v = r[f"{cn}_menos_{k}"]
                extra = f"  por peligro {v['cambio_numerador_por_peligro_a_mas25']}" if "cambio_numerador_por_peligro_a_mas25" in v else ""
                print(f"     frente a {k}: {v['dif']:+.6f} IC95 cliente {v['ic95_cliente']} dirección {v['ic95_direccion']} diez {v['diez_clientes_mas_favorables']:+.6f} sin ellos {v['dif_sin_esos_diez']:+.6f}{extra}", flush=True)
    (WORK / out).write_text(json.dumps(rep, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
