"""Blend line-specific components after normalizing their prediction totals.

Each component supplies V23-selection, V24 and 2025 predictions. Normalize to the
weighted total of eligible internal components separately in each cut; weights
then control relativities rather than selecting a single model's level. The
external S08 stack can contribute shape but is excluded from that reference.
Apply the V23 Tweedie factor to reported V24 predictions and the mean of V23/V24
factors to 2025. Optional shape, level and grid settings retain the frozen recipe.
Usage: python mezcla3.py <name> <spec_json> [--rejilla=<line>:<index>]
       [--alfa=<line>:<a>,...] [--forma=<line>:<rate_power>:<exposure_power>,...]
       [--nivel=s17] [--escribir]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from comun import BASE, LINES, WORK, d2, digest

EXTERNAL_STACK = Path("/mnt/user-data/uploads/Hakaton/Preparación/artifacts/verification/improvement_D76")
# External S08 and N01 contents-GAM components do not determine the level reference.
EXTERNOS = {"EXTERNAL_STACK", "GAMC_contents"}
# Neural-network levels were unstable between V24 and production: MLP3_contents had
# a 2025/V24 total ratio of 0.897 versus 1.074-1.078 for trees; use its relativities only.
NIVEL_INESTABLE = {"MLP3_contents", "MLP3_buildings", "MLP3_motor"}
# Since S17, exclude any component whose unlabeled total ratio deviates by more than
# 1.5% from its line anchor between V24 and 2025; this also covers peril-mean severity fits.
# Recorded 18 October against the frozen anchors: CFS motor -4.3%,
# buildings -2.7%, contents -2.9%; CFSS motor -4.4%, household lines -2.0%.
# Earlier motor/buildings CFS values (-3.8%/-2.6%) used another reference; classification is unchanged.
# S19 hybrid GLM/boosting severity: CFSG motor -3.9% and buildings -1.7% are excluded;
# CFSG contents -1.0% remains within the threshold and enters the level reference.
NIVEL_INESTABLE_S17 = NIVEL_INESTABLE | {"CFS_motor", "CFS_motor_4s", "CFSS_motor", "CFS_buildings", "CFSS_buildings", "CFS_contents", "CFSS_contents",
                                          "CFSG5_motor", "CFSG2_motor", "CFSG5_buildings", "CFSG2_buildings", "FSAS_contents",
                                          "FSAS4_contents", "FSAS_motor", "FSAX4_contents", "CFSX_contents", "CFSX_buildings",
                                          "CFSX_motor", "FSAXc4_contents", "CFSXc_contents", "CFSXc_buildings", "CFSXc_motor",
                                          "CFSS4_buildings", "FS2Xc_contents", "FS2S_motor",
                                          "CFSSr_motor", "CFSS4r_buildings", "FSAXc4r_contents",
                                          "CFSS6_motor", "CFSS4v_motor_tmp"}
# Four-seed buildings CFSS (S21): -1.72%, excluded under the same rule.
# Third frequency engine with a severity GLM: buildings FS2S
# -1.46% is included; contents FS2Xc -1.58% and motor FS2S -3.86% are excluded.
# Severity relativities capped at p99.5: motor CFSSr -4.4%, buildings CFSS4r
# -1.75% and contents FSAXc4r -1.55% are excluded; buildings FSAS4r +0.02% is included.
# Additional motor CFSS seeds retain exclusion; CFSS4v_motor_tmp was a V24-only diagnostic.
# Physical-covariate severity (S21): contents FSAX4 -1.52%, CFSX -2.06% and
# buildings CFSX -1.79% are excluded; buildings FSAX4 +0.2% is included.
# Corrected unpenalized-base variant: contents -1.53%/-2.06%, buildings CFSXc -1.86% excluded; FSAXc4 +0.15% included.
# Additive frequency with insured-value severity (S20): buildings FSAS +0.2% enters
# the level reference; contents -1.53% is excluded. Four-seed buildings FSAS4 +0.06%
# remains included; contents -1.57% and motor FSAS -3.85% remain excluded.
SIN_REFERENCIA = EXTERNOS | NIVEL_INESTABLE


def sin_referencia(opts):
    """Exclude components from the level reference; s17 applies the V24-to-2025 stability rule."""
    return EXTERNOS | (NIVEL_INESTABLE_S17 if opts.get("nivel") == "s17" else NIVEL_INESTABLE)
_cx = {}


def ftw(y, mu):
    return float((y / np.sqrt(mu)).sum() / np.sqrt(mu).sum())


def external_stack(split):
    if split not in _cx:
        f = {"v24": "learned_predictions_V24.parquet", "sel": "learned_fit_V23.parquet", "p25": "learned_predictions_PROD.parquet"}[split]
        _cx[split] = pd.read_parquet(EXTERNAL_STACK / f, columns=["row_id", "stack"]).set_index("row_id")["stack"]
    return _cx[split]


def component(run, sel_name, line):
    if run == "EXTERNAL_STACK":
        return external_stack("sel"), external_stack("v24"), external_stack("p25")
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
    """Raise predictions around their geometric mean; a>1 increases dispersion before level calibration."""
    if a == 1.0:
        return mu
    g = np.exp(np.log(mu).mean())
    return g * (mu / g) ** a


def shape_rate(mu, e, a, b):
    """Apply mu=e*(e/e_bar)^(b-1)*g*(r/g)^a with r=mu/e; a changes rate dispersion and b changes exposure proportionality."""
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
        # Use the weighted total of eligible internal components as the reference in each cut;
        # external components have another level basis. Rescale before applying relative-shape weights.
        own = [(w, s, v, p) for run, w, s, v, p in raw if run not in sin_referencia(opts)]
        wo = sum(o[0] for o in own)
        ref = [sum(o[0] * o[j].sum() for o in own) / wo for j in (1, 2, 3)]
        comps = [(s * ref[0] / s.sum(), v * ref[1] / v.sum(), p * ref[2] / p.sum()) for run, w, s, v, p in raw]
        ws = [c[2] for c in spec[line]]
        expos = None
        if line in forma:
            fe = pd.read_parquet(WORK / f"feat_{line}.parquet", columns=["row_id", "e_ef_coste", "exposure"])
            fe["row_id"] = fe.row_id.astype(str); fe = fe.set_index("row_id")
            # V23/V24 use effective exposure; 2025 uses nominal exposure, matching prediction.
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
