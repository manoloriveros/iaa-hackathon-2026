"""Mezcla general por ramo: componentes de Claude y el stack S08 de Codex ("CODEX"), con rejilla para un componente.

Cada componente aporta predicciones de V23 selección, V24 y 2025. Antes de mezclar, el total de cada componente se
iguala, en cada corte, a la media ponderada de los totales de los componentes de Claude (solo predicciones), para que los
pesos actúen sobre relatividades y el nivel no dependa de un único modelo. El
factor de año siguiente es la media de los factores Tweedie de la mezcla en V23 selección y V24; V24 se informa con el
factor de V23 (fuera de muestra) y 2025 recibe la media.
Uso: python3 mezcla3.py <nombre> <spec_json> [--rejilla=<ramo>:<indice>] [--alfa=<ramo>:<a>,...] [--forma=<ramo>:<a_tasa>:<b_exposicion>,...] [--nivel=s17] [--escribir]
spec: {"motor": [["CAT_motor", "cat1a", 0.5], ...], "buildings": [["S08h_hogar_F3s2", "hS2", 0.5], ["CODEX", "", 0.5]], ...}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from comun import BASE, LINES, WORK, d2, digest

CODEX = Path("/mnt/user-data/uploads/Hakaton/Preparación/artifacts/verification/improvement_D76")
# componentes de Codex que no entran en la referencia de nivel (el stack S08 y el GAM de contenidos de la carpeta N01)
EXTERNOS = {"CODEX", "GAMC_contents"}
# redes neuronales: su nivel no es estable entre V24 y producción (MLP3_contents: total V24 un 10 % sobre el real y
# razón 2025/V24 de 0,897 frente a 1,074-1,078 de los árboles), así que aportan relatividades pero no nivel
NIVEL_INESTABLE = {"MLP3_contents", "MLP3_buildings", "MLP3_motor"}
# desde S17, regla sin etiquetas: tampoco entran los componentes cuyo total frente al ancla del ramo se mueve más de un
# 1,5 % entre V24 y 2025 (frecuencias con severidad media del peligro, con o sin relatividad por capital). Medido el 18 de
# octubre frente a CAT_motor_4s, S12h_edif_md1000 y S08h_hogar_F3s2: CFS -4,3 % en autos (CFS_motor_4s), -2,7 % en
# edificios y -2,9 % en contenidos; CFSS -4,4 % en autos y -2,0 % en edificios y en contenidos. Al fijar la regla se
# anotó -3,8 % y -2,6 % para CFS en autos y edificios, con otra referencia; la clasificación no cambia
# con la misma regla (S19): la severidad híbrida GLM + boosting (CFSG) se mueve -3,9 % en autos y -1,7 % en edificios,
# fuera; en contenidos -1,0 %, dentro del umbral, así que CFSG*_contents sí entra en la referencia
NIVEL_INESTABLE_S17 = NIVEL_INESTABLE | {"CFS_motor", "CFS_motor_4s", "CFSS_motor", "CFS_buildings", "CFSS_buildings", "CFS_contents", "CFSS_contents",
                                          "CFSG5_motor", "CFSG2_motor", "CFSG5_buildings", "CFSG2_buildings", "FSAS_contents",
                                          "FSAS4_contents", "FSAS_motor", "FSAX4_contents", "CFSX_contents", "CFSX_buildings",
                                          "CFSX_motor", "FSAXc4_contents", "CFSXc_contents", "CFSXc_buildings", "CFSXc_motor",
                                          "CFSS4_buildings", "FS2Xc_contents", "FS2S_motor",
                                          "CFSSr_motor", "CFSS4r_buildings", "FSAXc4r_contents",
                                          "CFSS6_motor", "CFSS4v_motor_tmp"}
# CFSS de edificios con cuatro semillas (S21): -1,72 %, fuera como CFSS
# tercer motor de frecuencia (frecsev2 sin --aditivo, con severidad GLM encima; CLA-20261018-009): FS2S de edificios
# -1,46 % (dentro); FS2Xc de contenidos -1,58 % (fuera); FS2S de autos -3,86 % (fuera; CLA-20261018-011)
# relatividades de severidad acotadas al p99,5 (--tope=0.995, CLA-20261018-018): CFSSr de autos -4,4 %, CFSS4r de edificios
# -1,75 % y FSAXc4r de contenidos -1,55 %: fuera, como sus originales; FSAS4r de edificios +0,02 %: dentro
# CFSS de autos con más semillas (CFSS6_motor; CFSS4v_motor_tmp solo para medir V24, CLA-20261018-021): fuera, como CFSS_motor
# severidad con covariables físicas (severidad_cfs3.py, S21): FSAX4 de contenidos -1,52 % y CFSX -2,06 % (contenidos),
# -1,79 % (edificios): fuera; FSAX4 de edificios +0,2 %: dentro. Versión corregida, que no penaliza las covariables de CFSS
# (FSAXc4/CFSXc): contenidos -1,53 % y -2,06 %, edificios CFSXc -1,86 %: fuera; FSAXc4 de edificios +0,15 %: dentro
# frecuencia aditiva (frecsev2 --aditivo) con severidad GLM por capital (FSAS, S20): edificios +0,2 % (entra en la
# referencia); contenidos -1,53 %, justo por encima del umbral (fuera). Con cuatro semillas (FSAS4): edificios +0,06 %,
# contenidos -1,57 %; la clasificación no cambia. Autos (FSAS_motor): -3,85 %, fuera
SIN_REFERENCIA = EXTERNOS | NIVEL_INESTABLE


def sin_referencia(opts):
    """Conjunto excluido de la referencia de nivel; --nivel=s17 aplica la regla de estabilidad entre V24 y 2025."""
    return EXTERNOS | (NIVEL_INESTABLE_S17 if opts.get("nivel") == "s17" else NIVEL_INESTABLE)
_cx = {}


def ftw(y, mu):
    return float((y / np.sqrt(mu)).sum() / np.sqrt(mu).sum())


def codex(split):
    if split not in _cx:
        f = {"v24": "learned_predictions_V24.parquet", "sel": "learned_fit_V23.parquet", "p25": "learned_predictions_PROD.parquet"}[split]
        _cx[split] = pd.read_parquet(CODEX / f, columns=["row_id", "stack"]).set_index("row_id")["stack"]
    return _cx[split]


def component(run, sel_name, line):
    if run == "CODEX":
        return codex("sel"), codex("v24"), codex("p25")
    s = pd.read_parquet(WORK / f"sel_{sel_name}.parquet"); s = s[s.line == line].set_index("row_id")["mu"]
    v = pd.read_parquet(WORK / run / "v24.parquet"); v = v[v.line == line].set_index("row_id")["mu"]
    p = pd.read_parquet(WORK / run / "prediccion_2025.parquet"); p = p[p.line == line].set_index("row_id")["prediction"]
    return s, v, p


def labels(line):
    ref = pd.read_parquet(WORK / "S04b_lgbm_F0124_F3autos" / "v24.parquet"); ref = ref[ref.line == line].set_index("row_id")["y"]
    sel = pd.read_parquet(WORK / "sel_total_F0124.parquet"); sel = sel[sel.line == line].set_index("row_id")["y"]
    p25 = pd.read_parquet(WORK / "S04b_lgbm_F0124_F3autos" / "prediccion_2025.parquet"); p25 = p25[p25.line == line].set_index("row_id").index
    return sel, ref, p25


def shape(mu, a):
    """Potencia alrededor de la media geométrica: a > 1 abre la dispersión de las predicciones; el nivel lo fija luego el factor."""
    if a == 1.0:
        return mu
    g = np.exp(np.log(mu).mean())
    return g * (mu / g) ** a


def shape_rate(mu, e, a, b):
    """Forma sobre la tasa y elasticidad de la exposición: mu = e (e/ē)^(b-1) g (r/g)^a con r = mu/e y medias geométricas.
    a > 1 abre la dispersión de las tasas; b distinto de 1 deja de suponer coste proporcional a la duración del periodo."""
    if a == 1.0 and b == 1.0:
        return mu
    r = mu / e
    g = np.exp(np.log(r).mean()); eb = np.exp(np.log(e).mean())
    return e * (e / eb) ** (b - 1.0) * g * (r / g) ** a


def evaluate(comps, ws, ysel, y24, a=1.0, forma=None, expos=None):
    ws = np.asarray(ws, float) / np.sum(ws)
    bsel = sum(w * c[0] for w, c in zip(ws, comps)); b24 = sum(w * c[1] for w, c in zip(ws, comps)); b25 = sum(w * c[2] for w, c in zip(ws, comps))
    bsel, b24, b25 = shape(bsel, a), shape(b24, a), shape(b25, a)
    if forma is not None:
        bsel, b24, b25 = (shape_rate(bsel, expos[0], *forma), shape_rate(b24, expos[1], *forma), shape_rate(b25, expos[2], *forma))
    f23, f24 = ftw(ysel, bsel), ftw(y24, b24)
    return {"d2_sel": d2(ysel, bsel), "d2_v24_f23": d2(y24, b24 * f23), "f23": f23, "f24": f24, "f": (f23 + f24) / 2}, bsel, b24 * f23, b25 * (f23 + f24) / 2


def main():
    name, spec_path = sys.argv[1], sys.argv[2]
    opts = dict((a[2:].split("=") + ["1"])[:2] for a in sys.argv[3:] if a.startswith("--"))
    spec = json.loads(open(spec_path).read())
    grid = opts.get("rejilla")
    alfa = {kv.split(":")[0]: float(kv.split(":")[1]) for kv in opts.get("alfa", "").split(",") if kv}
    forma = {kv.split(":")[0]: (float(kv.split(":")[1]), float(kv.split(":")[2])) for kv in opts.get("forma", "").split(",") if kv}
    rep = {"spec": spec, "lines": {}, "alfa": alfa, "forma": {k: list(v) for k, v in forma.items()}}
    ys24, ms24, preds = [], [], []
    for line in LINES:
        ysel, y24, idx25 = labels(line)
        raw = []
        for k, (run, sel_name, w) in enumerate(spec[line]):
            s, v, p = component(run, sel_name, line)
            s = s.reindex(ysel.index).values; v = v.reindex(y24.index).values; p = p.reindex(idx25).values
            assert np.isfinite(s).all() and np.isfinite(v).all() and np.isfinite(p).all(), (line, run)
            raw.append((run, w, s, v, p))
        # nivel de referencia: media ponderada de los totales de los componentes de Claude en cada corte (el de Codex está
        # en otra base de nivel); cada componente se reescala a ese total, así los pesos actúan sobre relatividades
        own = [(w, s, v, p) for run, w, s, v, p in raw if run not in sin_referencia(opts)]
        wo = sum(o[0] for o in own)
        ref = [sum(o[0] * o[j].sum() for o in own) / wo for j in (1, 2, 3)]
        comps = [(s * ref[0] / s.sum(), v * ref[1] / v.sum(), p * ref[2] / p.sum()) for run, w, s, v, p in raw]
        ws = [c[2] for c in spec[line]]
        expos = None
        if line in forma:
            fe = pd.read_parquet(WORK / f"feat_{line}.parquet", columns=["row_id", "e_ef_coste", "exposure"])
            fe["row_id"] = fe.row_id.astype(str); fe = fe.set_index("row_id")
            # V23 selección y V24 con la exposición efectiva del offset; 2025 con la nominal, como en la predicción
            expos = (fe.e_ef_coste.reindex(ysel.index).values, fe.e_ef_coste.reindex(y24.index).values, fe.exposure.reindex(idx25).values)
        res, bsel, b24, b25 = evaluate(comps, ws, ysel.values, y24.values, alfa.get(line, 1.0), forma.get(line), expos)
        rep["lines"][line] = {k: round(v, 5) for k, v in res.items()}
        print(line, rep["lines"][line], flush=True)
        if grid and grid.split(":")[0] == line:
            j = int(grid.split(":")[1])
            others = np.array(ws, float); others[j] = 0; others = others / others.sum()
            for wj in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5):
                w2 = others * (1 - wj); w2[j] = wj
                r2, *_ = evaluate(comps, w2, ysel.values, y24.values, alfa.get(line, 1.0), forma.get(line), expos)
                print("  rejilla", spec[line][j][0], wj, {k: round(v, 5) for k, v in r2.items()}, flush=True)
        ys24.append(y24.values); ms24.append(b24)
        preds.append(pd.DataFrame({"row_id": idx25.values, "line": line, "prediction": b25}))
    rep["d2_v24_global_f23"] = round(d2(np.concatenate(ys24), np.concatenate(ms24)), 5)
    rep["publico_esperado"] = round(0.0099 + 0.8644 * rep["d2_v24_global_f23"], 5)
    print("global V24", rep["d2_v24_global_f23"], "público esperado", rep["publico_esperado"], flush=True)
    if "escribir" in opts:
        pred = pd.concat(preds, ignore_index=True)
        sample = pd.read_parquet(BASE / "Datos" / "sample_submission.parquet", columns=["row_id"])
        sub = sample.merge(pred[["row_id", "prediction"]], on="row_id", how="left", validate="one_to_one")
        assert len(sub) == 626639 and np.isfinite(sub.prediction).all() and (sub.prediction > 0).all()
        out = WORK / name
        out.mkdir(parents=True, exist_ok=True)
        csv = out / f"{name}.csv"
        sub.to_csv(csv, index=False, float_format="%.6f")
        back = pd.read_csv(csv, dtype={"row_id": str})
        assert (back.row_id.values == sample.row_id.values).all()
        rep["file"] = {"path": str(csv), "sha256": digest(csv), "rows": 626639, "total_CU": round(float(back.prediction.sum()), 2),
                       "by_line_CU": {l: round(float(pred[pred.line == l].prediction.sum()), 2) for l in LINES}}
        pred.to_parquet(out / "prediccion_2025.parquet", index=False)
        (out / "resumen.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))
        print(json.dumps(rep["file"], indent=1), flush=True)


if __name__ == "__main__":
    main()
