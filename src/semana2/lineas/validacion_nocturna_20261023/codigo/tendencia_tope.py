"""Índice de nivel del desarrollado con y sin tope de siniestros grandes (conciliación con el revisor rev4).

Mismo índice que tendencia_opciones.json (Σ T0 / Σ e_ef·g por año, relatividades fijas del GBM desarrollado, e_ef con la
completitud de reporte) y una variante con cada siniestro topado a C; el exceso sobre C se trata como carga estable
(promedio 2021-2024 del cociente exceso / topado), así que no entra en la tendencia. También da la tendencia con solo
2021-2023, que no depende del IBNR de 2024, y la sensibilidad de autos a la completitud de lesiones en 2024.
Escribe salidas/produccion/tendencia_tope.json.
"""
import json, pathlib
import numpy as np, pandas as pd

R = pathlib.Path('/home/claude/noche')
YRS = [2021, 2022, 2023, 2024]
a = pd.read_parquet(R / 'salidas/s1/asignacion.parquet'); a = a[(a.category == 'unica') & a.accepted]
out = {}


def slope(idx, yrs):
    x = np.array(yrs, float); y = np.log([idx[k] for k in yrs])
    X = np.c_[np.ones_like(x), x]; b, res, *_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X @ b; se = np.sqrt((r @ r) / max(len(x) - 2, 1) / ((x - x.mean()) @ (x - x.mean())))
    return float(np.expm1(b[1])), float(se)


for line in ['motor', 'buildings', 'contents']:
    b = pd.read_parquet(R / f'salidas/s1/base_{line}.parquet'); b = b[b.split == 'train'].reset_index(drop=True)
    gf = 'lg_dev21222324_v2fixs11_motor_dev' if line == 'motor' else f'lg_dev21222324_m02_{line}_dev'
    g = pd.read_parquet(R / f'salidas/transfer/{gf}.parquet').set_index('row_id').lg_dev
    b['m'] = b.eef_coste * np.exp(b.row_id.map(g).values)
    al = a[a.line == line]
    res = {}
    for C in (None, 250000.0, 100000.0):
        if C is None:
            t = b.t0.values
        else:
            cap = al.assign(c=np.minimum(al.net, C)).groupby('row_id').c.sum()
            t = b.row_id.map(cap).fillna(0.0).values
        lev = {y: t[b.year.values == y].sum() / b.m.values[b.year.values == y].sum() for y in YRS}
        idx = {y: lev[y] / lev[2021] for y in YRS}
        s4, se4 = slope(idx, YRS); s3, se3 = slope(idx, YRS[:3])
        tag = 'sin_tope' if C is None else f'tope_{int(C / 1000)}k'
        res[tag] = {'indice': {str(y): round(idx[y], 4) for y in YRS}, 'tendencia_21_24': round(s4, 4), 'ee_21_24': round(se4, 4),
                    'tendencia_21_23': round(s3, 4), 'ee_21_23': round(se3, 4)}
        if C is not None:
            exc = {y: (b.t0.values[b.year.values == y].sum() / t[b.year.values == y].sum()) for y in YRS}
            res[tag]['exceso_por_anio'] = {str(y): round(exc[y], 4) for y in YRS}
    # mayores siniestros por año
    big = al.sort_values('net', ascending=False).head(5)
    res['mayores'] = [{'anio': int(pd.Timestamp(r.loss_date).year), 'neto': round(float(r.net), 0), 'peligro': str(r.peril)} for r in big.itertuples()]
    res['coste_total_por_anio'] = {str(y): round(float(b.t0.values[b.year.values == y].sum()), 0) for y in YRS}
    out[line] = res
    print(line, json.dumps(res, ensure_ascii=False), flush=True)
json.dump(out, open(R / 'salidas/produccion/tendencia_tope.json', 'w'), indent=1, ensure_ascii=False)
