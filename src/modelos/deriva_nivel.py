"""Deriva de nivel sin etiquetas de cada componente de una mezcla: total 2025 / total V24 frente al del ancla del ramo.

La regla s17 de mezcla3.py deja fuera de la referencia de nivel los componentes que se apartan más de un 1,5 %.
Anclas: CatBoost Tweedie de autos (CAT_motor_4s), LightGBM de edificios (S12h_edif_md1000) y de contenidos (S08h_hogar_F3s2).
Uso: python3 deriva_nivel.py <spec_json> [<salida.json>]
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
