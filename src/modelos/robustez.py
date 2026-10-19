"""Robustez pareada de candidatos de mezcla frente a una referencia, por ramo y global, en V23 selección y V24.

Cada candidato se reconstruye igual que en mezcla3.py (componentes reescalados al nivel de los de Claude, forma por ramo y
factor de V23 en V24) y se compara con la referencia con tres medidas:
- diferencia de D² (V23 selección sin factor; V24 con el factor de V23, como informa mezcla3),
- bootstrap pareado por cliente (Poisson(1) por cliente, 1000 réplicas) de la diferencia de devianza: P(mejora > 0) e
  intervalo del 90 %; en el global el cliente agrupa sus filas de los tres ramos,
- sensibilidad sin el 0,1 % superior de la pérdida observada de cada ramo y corte (el filtro que usa Codex).
Uso: python3 robustez.py <salida.json> <ref>=<spec>[@<forma>] <cand>=<spec>[@<forma>] ...
forma con el formato de mezcla3: motor:1.09:0.95,buildings:1.08:1.14,contents:1.07:1
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from comun import LINES, WORK, d2, deviance
from mezcla3 import component, evaluate, ftw, labels, sin_referencia

B = 1000


def parse(arg):
    """<nombre>=<spec>[@<forma>[@<regla_de_nivel>]]; la regla s17 saca de la referencia de nivel los componentes inestables."""
    name, rest = arg.split("=", 1)
    spec, _, rest2 = rest.partition("@")
    forma, _, nivel = rest2.partition("@")
    fm = {kv.split(":")[0]: (float(kv.split(":")[1]), float(kv.split(":")[2])) for kv in forma.split(",") if kv}
    if nivel:
        fm["_nivel"] = nivel
    return name, json.loads(open(spec).read()), fm


def blend(spec, forma, line, ysel, y24, idx25, expos):
    raw = []
    for run, sel_name, w in spec[line]:
        s, v, p = component(run, sel_name, line)
        raw.append((run, w, s.reindex(ysel.index).values, v.reindex(y24.index).values, p.reindex(idx25).values))
    own = [(w, s, v, p) for run, w, s, v, p in raw if run not in sin_referencia({"nivel": forma.get("_nivel")})]
    wo = sum(o[0] for o in own)
    ref = [sum(o[0] * o[j].sum() for o in own) / wo for j in (1, 2, 3)]
    comps = [(s * ref[0] / s.sum(), v * ref[1] / v.sum(), p * ref[2] / p.sum()) for run, w, s, v, p in raw]
    res, bsel, b24, b25 = evaluate(comps, [c[2] for c in spec[line]], ysel.values, y24.values, 1.0, forma.get(line), expos)
    return res, bsel, b24, b25


def boot(dif_by_c, null_total, rng):
    # el denominador se fija en la devianza nula total: la réplica solo mueve el numerador; bloques de 50 réplicas por memoria
    d = dif_by_c.astype(np.float64)
    out = [rng.poisson(1.0, size=(50, len(d))).astype(np.float64) @ d for _ in range(B // 50)]
    return np.concatenate(out) / null_total


def main():
    out_path = sys.argv[1]
    cands = [parse(a) for a in sys.argv[2:]]
    rng = np.random.default_rng(20261018)
    data = {}
    for line in LINES:
        ysel, y24, idx25 = labels(line)
        fe = pd.read_parquet(WORK / f"feat_{line}.parquet", columns=["row_id", "customer_id", "e_ef_coste", "exposure"])
        fe["row_id"] = fe.row_id.astype(str); fe = fe.set_index("row_id")
        expos = (fe.e_ef_coste.reindex(ysel.index).values, fe.e_ef_coste.reindex(y24.index).values, fe.exposure.reindex(idx25).values)
        cust = {"V23": fe.customer_id.reindex(ysel.index).astype(str).values, "V24": fe.customer_id.reindex(y24.index).astype(str).values}
        preds = {}
        for name, spec, forma in cands:
            res, bsel, b24, b25 = blend(spec, forma, line, ysel, y24, idx25, expos)
            preds[name] = {"V23": bsel, "V24": b24, "tot25": float(b25.sum()), "res": res}
        data[line] = {"y": {"V23": ysel.values, "V24": y24.values}, "cust": cust, "preds": preds}
    ref = cands[0][0]
    rep = {"referencia": ref, "candidatos": {}}
    for name, _, _ in cands[1:]:
        r = {}
        for fold in ("V23", "V24"):
            rows = {}
            ally, allr, allc, allcu, keep_all = [], [], [], [], []
            for line in LINES:
                y = data[line]["y"][fold]; pr = data[line]["preds"][ref][fold]; pc = data[line]["preds"][name][fold]
                cu = data[line]["cust"][fold]
                dr, dc = deviance(y, pr), deviance(y, pc)
                null = deviance(y, np.full_like(y, y.mean())).sum()
                codes, inv = np.unique(cu, return_inverse=True)
                dif_c = np.bincount(inv, weights=dr - dc)
                bs = boot(dif_c, null, rng)
                keep = y <= np.quantile(y, 0.999)
                rows[line] = {"d2_ref": round(d2(y, pr), 5), "d2_cand": round(d2(y, pc), 5), "dif": round(float((dr - dc).sum() / null), 6),
                              "P_mejora": round(float((bs > 0).mean()), 3), "ic90": [round(float(np.quantile(bs, 0.05)), 6), round(float(np.quantile(bs, 0.95)), 6)],
                              "dif_sin_top01": round(d2(y[keep], pc[keep]) - d2(y[keep], pr[keep]), 6),
                              # mismo filtro, con cada predicción llevada a su nivel óptimo en el subconjunto: separa forma de nivel
                              "dif_sin_top01_renivelado": round(d2(y[keep], pc[keep] * ftw(y[keep], pc[keep])) - d2(y[keep], pr[keep] * ftw(y[keep], pr[keep])), 6),
                              "dif_renivelado": round(d2(y, pc * ftw(y, pc)) - d2(y, pr * ftw(y, pr)), 6),
                              "nivel_cand_sobre_ref": round(float(pc.sum() / pr.sum()), 4)}
                ally.append(y); allr.append(pr); allc.append(pc); allcu.append(cu); keep_all.append(keep)
            y = np.concatenate(ally); pr = np.concatenate(allr); pc = np.concatenate(allc); cu = np.concatenate(allcu); keep = np.concatenate(keep_all)
            dr, dc = deviance(y, pr), deviance(y, pc)
            null = deviance(y, np.full_like(y, y.mean())).sum()
            codes, inv = np.unique(cu, return_inverse=True)
            bs = boot(np.bincount(inv, weights=dr - dc), null, rng)
            rows["global"] = {"d2_ref": round(d2(y, pr), 5), "d2_cand": round(d2(y, pc), 5), "dif": round(float((dr - dc).sum() / null), 6),
                              "P_mejora": round(float((bs > 0).mean()), 3), "ic90": [round(float(np.quantile(bs, 0.05)), 6), round(float(np.quantile(bs, 0.95)), 6)],
                              "dif_sin_top01": round(d2(y[keep], pc[keep]) - d2(y[keep], pr[keep]), 6)}
            r[fold] = rows
        r["total_2025"] = {line: {"ref": round(data[line]["preds"][ref]["tot25"], 0), "cand": round(data[line]["preds"][name]["tot25"], 0)} for line in LINES}
        rep["candidatos"][name] = r
        print("==", name, "frente a", ref, flush=True)
        for fold in ("V23", "V24"):
            for k, v in r[fold].items():
                extra = f"  renivelado {v['dif_renivelado']:+.5f}  sin top renivelado {v['dif_sin_top01_renivelado']:+.5f}  nivel {v['nivel_cand_sobre_ref']}" if k != "global" else ""
                print(f"  {fold} {k:9s} dif {v['dif']:+.5f}  P>0 {v['P_mejora']:.3f}  IC90 [{v['ic90'][0]:+.5f}, {v['ic90'][1]:+.5f}]  sin top 0,1 % {v['dif_sin_top01']:+.5f}{extra}", flush=True)
    (WORK / out_path).write_text(json.dumps(rep, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
