"""Inspect unlabeled component level drift: 2025/V24 totals against each line's anchor.

The s17 rule excludes components drifting more than 1.5% from the anchor from
the blend's level reference. Anchors are CAT_motor_4s, S12h_edif_md1000 and
S08h_hogar_F3s2 for motor, buildings and contents respectively.
Usage: python deriva_nivel.py <spec_json> [<output.json>]
"""
import json
import sys

from comun import WORK
from mezcla3 import component, sin_referencia

ANCLA = {"motor": ("CAT_motor_4s", "cat1a"), "buildings": ("S12h_edif_md1000", "hS3"), "contents": ("S08h_hogar_F3s2", "hS2")}


def tot(run, sel, line):
    s, v, p = component(run, sel, line)
    return float(v.sum()), float(p.sum())


def main():
    spec = json.load(open(sys.argv[1]))
    excl = sin_referencia({"nivel": "s17"})
    rep = {}
    for line, comps in spec.items():
        a24, a25 = tot(*ANCLA[line], line)
        rep[line] = {}
        for run, sel, w in comps:
            v24, p25 = tot(run, sel, line)
            der = (p25 / v24) / (a25 / a24) - 1.0
            rep[line][run] = {"peso": w, "deriva": round(der, 4), "fuera_de_la_referencia": run in excl, "regla_coherente": (abs(der) > 0.015) == (run in excl) or run.startswith("MLP")}
            print(line, run, rep[line][run], flush=True)
    if len(sys.argv) > 2:
        (WORK / sys.argv[2]).write_text(json.dumps(rep, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
