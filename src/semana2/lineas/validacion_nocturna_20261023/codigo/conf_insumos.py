"""Insumos de la confirmación 2023 -> 2024 sin etiquetas de 2024 de ningún mercado (regla de SEL01).

1. Completitud de reporte F (conteos y coste) con siniestros de ocurrencia <= 2023 de los dos mercados; el truncamiento
   sigue siendo el 31-12-2024 (fecha de valoración común).
2. Participaciones s_p con el emergente 2023 y el desarrollado 2021-2023.
3. e_ef_coste de las filas 2023 (ajuste) y 2024 (vínculo de observación para evaluar) del emergente, y de 2021-2023 del
   desarrollado.
Salida: salidas/conf/base_{mk}_{ramo}.parquet con las columnas de base + eef_* recalculadas.
"""
import json, pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import reporte as RP
from exposicion_efectiva import add_effective, PERILS

R = pathlib.Path('/home/claude/noche'); O = R / 'salidas/conf'; O.mkdir(parents=True, exist_ok=True)
c = pd.concat([RP.load('s1'), RP.load('s2')], ignore_index=True)
c = c[c.ld.dt.year <= 2023]
tmax = int(c.window.max())
Fc = {}
for p, g in c.groupby('peril'):
    cap = g.net.quantile(0.995)
    w = np.minimum(g.net.values, cap)
    db = (g.delay.values // RP.B).astype(int); wb = (g.window.values // RP.B).astype(int); nb = tmax // RP.B + 1
    d = np.bincount(db, weights=w, minlength=nb)[:nb]
    st = np.bincount(db, weights=w, minlength=nb + 1)[:nb]
    en = np.bincount(np.minimum(wb, nb - 1) + 1, weights=w, minlength=nb + 1)[:nb]
    risk = np.cumsum(st) - np.cumsum(en)
    h = np.where(risk > 0, d / np.maximum(risk, 1e-9), 0)
    surv = np.cumprod((1 - h)[::-1])[::-1]
    Fc[p] = np.concatenate([surv[1:], [1.0]]).tolist()
json.dump({'bucket_days': RP.B, 'F_coste': Fc, 'nota': 'ocurrencia <= 2023'}, open(O / 'reporte_F_conf.json', 'w'))
res = {}
for mk, years in (('s2', [2023, 2024]), ('s1', [2021, 2022, 2023])):
    for ln in PERILS:
        b = pd.read_parquet(R / f'salidas/{mk}/base_{ln}.parquet')
        b = b[(b.split == 'train') & b.year.isin(years)].reset_index(drop=True)
        fit_years = [y for y in years if y <= 2023]
        tmp = add_effective(b.copy(), ln, Fc, RP.B, {p: 1.0 for p in PERILS[ln]})
        f = tmp.year.isin(fit_years) if mk == 's1' else tmp.year == 2023
        ult = {p: float(b.loc[f, f't0_{p}'].sum() * tmp.loc[f, 'exposure_model'].sum() / tmp.loc[f, f'eef_{p}'].sum()) for p in PERILS[ln]}
        tot = sum(ult.values()); shares = {p: v / tot for p, v in ult.items()}
        b = add_effective(b, ln, Fc, RP.B, shares)
        b.to_parquet(O / f'base_{mk}_{ln}.parquet', index=False)
        res[f'{mk}_{ln}'] = {'shares': {p: round(v, 4) for p, v in shares.items()},
                             'comp_by_year': b.groupby('year').apply(lambda x: x.eef_coste.sum() / x.exposure_model.sum(), include_groups=False).round(4).to_dict()}
json.dump(res, open(O / 'conf_insumos.json', 'w'), indent=1, default=str)
print(json.dumps(res, indent=1, default=str))
