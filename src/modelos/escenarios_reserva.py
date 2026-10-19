"""Sensibilidad de las comparaciones a la reserva de caso: etiquetas T1 con la reserva de los siniestros abiertos × 0,75 y × 1,25.

T0 suma, por periodo, incurrido menos recobros de los siniestros aceptados asignados (D67). T1(a) (metodología D35) cambia
solo los abiertos: pagado + a × (incurrido − pagado) − recobros, así que T1(a) = T0 + (a − 1) × R, con R la reserva de
caso de los abiertos aceptados de la fila. Las reservas son escenarios de evaluación, nunca predictores, y las
predicciones no cambian (incluido su factor de año siguiente, estimado con T0). Para cada escenario se informa el D² de
los candidatos de Claude en V23 selección y V24, la diferencia frente al primero de la lista con bootstrap por cliente
(Poisson(1), 1.000 réplicas, denominador fijo) y, en V24, frente a A_G y H de Codex (lectura sin modificar).
Uso: python3 escenarios_reserva.py <salida.json> <ref>=<spec>[@<forma>[@<nivel>]] <cand>=<spec>...
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from comun import BASE, BASESDIR, LINES, WORK, d2, deviance
from mezcla3 import labels
from robustez import blend, parse

C = "/mnt/user-data/uploads/Hakaton/Hackaton/Semana 1/Modelado_codex/nocturna_20261017_N01"
CLAIMS = BASE / "Limpieza" / "runs" / "preaudit_20261016T211816Z_817285a5" / "data" / "claims.parquet"
A = (0.75, 1.0, 1.25)
B = 1000


def reserva_por_fila():
    c = pd.read_parquet(CLAIMS, columns=["claim_id", "status", "paid_to_date", "incurred_to_date", "audit_pre00"])
    a = pd.read_parquet(BASESDIR / "tables" / "asignacion_por_siniestro.parquet", columns=["claim_id", "category", "row_id"])
    m = a.merge(c, on="claim_id", how="left", validate="one_to_one")
    ok = (m.status == "open") & (m.category == "unica") & (~m.audit_pre00.fillna(False).astype(bool)) & m.row_id.notna()
    r = (m.incurred_to_date - m.paid_to_date)[ok].groupby(m.row_id[ok].astype(str)).sum()
    return r


def boot(dif, groups, null, rng):
    codes, inv = np.unique(groups, return_inverse=True)
    d = np.bincount(inv, weights=dif)
    bs = np.concatenate([rng.poisson(1.0, size=(50, len(d))) @ d for _ in range(B // 50)]) / null
    return [round(float(np.quantile(bs, 0.025)), 6), round(float(np.quantile(bs, 0.975)), 6)], round(float((bs > 0).mean()), 3)


def main():
    out = sys.argv[1]
    cands = [parse(x) for x in sys.argv[2:]]
    ref = cands[0][0]
    R = reserva_por_fila()
    ag = pd.read_parquet(f"{C}/crossfit_meta_gam_guard/predictions_V24_crossfit.parquet", columns=["row_id", "meta_gam"]).set_index("row_id").meta_gam
    hh = pd.read_parquet(f"{C}/geometric_meta_nested/V24.parquet", columns=["row_id", "candidate"]).set_index("row_id").candidate
    rng = np.random.default_rng(20261018)
    store = {f: {"y": [], "r": [], "cu": [], "P": {}} for f in ("V23", "V24")}
    for line in LINES:
        ysel, y24, idx25 = labels(line)
        fe = pd.read_parquet(WORK / f"feat_{line}.parquet", columns=["row_id", "customer_id", "e_ef_coste", "exposure"])
        fe["row_id"] = fe.row_id.astype(str); fe = fe.set_index("row_id")
        expos = (fe.e_ef_coste.reindex(ysel.index).values, fe.e_ef_coste.reindex(y24.index).values, fe.exposure.reindex(idx25).values)
        for f, ys in (("V23", ysel), ("V24", y24)):
            store[f]["y"].append(ys.values); store[f]["r"].append(R.reindex(ys.index).fillna(0.0).values)
            store[f]["cu"].append(fe.customer_id.reindex(ys.index).astype(str).values)
        for name, spec, forma in cands:
            _, bsel, b24, _ = blend(spec, forma, line, ysel, y24, idx25, expos)
            store["V23"]["P"].setdefault(name, []).append(bsel); store["V24"]["P"].setdefault(name, []).append(b24)
        store["V24"]["P"].setdefault("A_G", []).append(ag.reindex(y24.index).values)
        store["V24"]["P"].setdefault("H", []).append(hh.reindex(y24.index).values)
        store["V23"].setdefault("line", []).append(np.full(len(ysel), line)); store["V24"].setdefault("line", []).append(np.full(len(y24), line))
    rep = {"referencia": ref, "reserva_abiertos_CU": {f: round(float(np.concatenate(store[f]["r"]).sum()), 0) for f in store}, "escenarios": {}}
    for a in A:
        ra = {}
        for f in ("V23", "V24"):
            y0 = np.concatenate(store[f]["y"]); r = np.concatenate(store[f]["r"]); cu = np.concatenate(store[f]["cu"]); ln = np.concatenate(store[f]["line"])
            y = y0 + (a - 1.0) * r
            P = {k: np.concatenate(v) for k, v in store[f]["P"].items()}
            res = {}
            for scope in LINES + ["agregado"]:
                msk = np.ones(len(y), bool) if scope == "agregado" else (ln == scope)
                ys, cus = y[msk], cu[msk]
                null = deviance(ys, np.full_like(ys, ys.mean())).sum()
                row = {"d2": {k: round(d2(ys, p[msk]), 5) for k, p in P.items()}}
                for k in P:
                    if k == ref:
                        continue
                    dif = deviance(ys, P[ref][msk]) - deviance(ys, P[k][msk])
                    ic, pm = boot(dif, cus, null, rng)
                    row[f"{k}_menos_{ref}"] = {"dif": round(float(dif.sum() / null), 6), "ic95_cliente": ic, "P_mejora": pm}
                res[scope] = row
            ra[f] = res
            print(f"a={a} {f} agregado", {k: v for k, v in res["agregado"]["d2"].items()}, flush=True)
            for scope in LINES + ["agregado"]:
                print("   ", scope, {k: (v["dif"], v["ic95_cliente"]) for k, v in res[scope].items() if k != "d2"}, flush=True)
        rep["escenarios"][str(a)] = ra
    (WORK / out).write_text(json.dumps(rep, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
