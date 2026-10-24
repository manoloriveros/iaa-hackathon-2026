"""Aplica NB-CRED-01 a las predicciones de cualquier receta (Claude, 23-10-2026).

Entrada: un Parquet con, por fila, line, x_new_business, T0 y prediction (predicciones cruzadas de la receta en
sus filas de ajuste; opcionales model_id y fold) y factores_nb_cred.json de aplicar_decisiones.py.
Salida: por ramo, A/E de nuevo negocio y renovación, su razón y el factor g_NB = razón * c que se multiplica a las
filas de nuevo negocio de esa receta (las renovaciones quedan igual). No ajusta nada.

    python factor_nuevo_negocio.py --oof predicciones.parquet --factores factores_nb_cred.json [--modelo W2-B06]

c sale de theta_em estimado con el emergente 2023. Si la receta se entrena con otros años, conviene repetir
aplicar_decisiones.py con esa ventana para que theta_em y Z correspondan a los mismos datos.
"""
from __future__ import annotations

import argparse
import json
import pathlib

import pandas as pd
import pyarrow.parquet as pq


def factores(t: pd.DataFrame, c: dict) -> dict:
    out = {}
    for l, s in t.groupby('line'):
        nb, re = s[s.x_new_business == 1], s[s.x_new_business == 0]
        ae_nb, ae_re = nb.T0.sum() / nb.prediction.sum(), re.T0.sum() / re.prediction.sum()
        out[l] = dict(filas_nb=len(nb), filas_ren=len(re), AE_NB=float(ae_nb), AE_REN=float(ae_re),
                      razon=float(ae_nb / ae_re), c=c[l]['c'], g_NB=float(ae_nb / ae_re * c[l]['c']))
    return out


def main(a):
    t = pq.read_table(a.oof).to_pandas()
    if a.modelo:
        t = t[t.model_id == a.modelo]
    c = json.loads(a.factores.read_text(encoding='utf-8'))['ramos']
    res = dict(oof=str(a.oof), modelo=a.modelo, factores=factores(t, c))
    if 'fold' in t.columns:
        res['por_fold_cruzado'] = {int(k): factores(t[t.fold != k], c) for k in sorted(t.fold.unique())}
    texto = json.dumps(res, ensure_ascii=False, indent=1)
    if a.out:
        a.out.write_text(texto, encoding='utf-8')
    for l, x in res['factores'].items():
        print(f"{l:10s} A/E NB {x['AE_NB']:.3f}  A/E REN {x['AE_REN']:.3f}  razón {x['razon']:.3f}  c {x['c']:.3f}  g_NB {x['g_NB']:.3f}")


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--oof', type=pathlib.Path, required=True)
    ap.add_argument('--factores', type=pathlib.Path, default=pathlib.Path(__file__).resolve().parent / 'factores_nb_cred.json')
    ap.add_argument('--modelo')
    ap.add_argument('--out', type=pathlib.Path)
    main(ap.parse_args())
