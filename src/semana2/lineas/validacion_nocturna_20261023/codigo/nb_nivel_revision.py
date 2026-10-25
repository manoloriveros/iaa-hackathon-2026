"""Revisión antes del envío: ¿hace falta un factor de nivel para el nuevo negocio?

rev5 encontró que, con la receta final y el nivel agrupado 2023-2024, el nuevo negocio sale por encima del modelo
(A/E 1,26 en autos y 1,27 en contenidos). En 2025 el nuevo negocio es el 77 % de la exposición, así que importa.
Prueba fuera de tiempo, la única honesta con dos años: factor estimado en 2023 y medido en 2024 (exploratorio, 2024 ya
abierto), con la receta final sin historia (A1fixb3, relatividades conf 2021-2023) y con historia neutral (A1fixF1b3n).
Variantes del factor por ramo f = A/E(NB) / A/E(ramo) en 2023, reequilibrado para no mover el total 2023 del ramo:
  sin factor; factor bruto; factor con siniestros topados a 100.000 CU (cuerpo); factor con credibilidad
  Z = n / (n + k), n = siniestros NB del ramo, k = 300 (fijado antes de medir).
Después, la misma lectura en 2023-2024 agrupado para 2025 (cuánto movería el total de cada ramo).
Escribe salidas/correccion/nb_nivel_revision.json.
"""
import json, pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import marco as M

R = pathlib.Path('/home/claude/noche'); T = R / 'salidas/transfer'; C = R / 'salidas/conf'; O = R / 'salidas/correccion'
LINES = ['motor', 'buildings', 'contents']; K = 300.0; CAP = 100000.0
SRC = {}  # se toma de evaluar_final.py para usar exactamente las mismas semillas
src_txt = open(R / 'codigo/evaluar_final.py').read()
exec(src_txt[src_txt.index('SRC = {'):src_txt.index('def lg(')])


def lg(tags, line):
    return pd.concat([pd.read_parquet(T / f'lg_{t}_{line}_em.parquet').set_index('row_id').lg_dev for t in tags], axis=1).mean(axis=1)


a = pd.read_parquet(R / 'salidas/s2/asignacion.parquet'); a = a[(a.category == 'unica') & a.accepted]
capd = a.assign(c=np.minimum(a.net, CAP)).groupby('row_id').c.sum(); nclm = a.groupby('row_id').size()
out = {'k_credibilidad': K, 'tope_cuerpo': CAP}
# 1. 2023 -> 2024 con relatividades conf
rows = []
for line in LINES:
    b = pd.read_parquet(C / f'base_s2_{line}.parquet')
    for rec in ('A1fixb3', 'A1fixF1b3'):
        b[f'g_{rec}'] = np.exp(b.row_id.map(lg(SRC[rec]['conf'][line], line)).values)
    b['line'] = line; rows.append(b[['row_id', 'line', 'year', 'customer_id', 'address_id', 'new_business', 't0', 'eef_coste', 'g_A1fixb3', 'g_A1fixF1b3']])
B = pd.concat(rows, ignore_index=True)
B['t0c'] = B.row_id.map(capd).fillna(0.0).values; B['n'] = B.row_id.map(nclm).fillna(0).values
nb = B.new_business.values.astype(bool); y23 = (B.year == 2023).values; y24 = (B.year == 2024).values
res = {}
for rec in ('A1fixb3', 'A1fixF1b3'):
    m = np.zeros(len(B))
    for line in LINES:
        s = (B.line == line).values
        L = B.t0.values[s & y23].sum() / (B.eef_coste.values[s & y23] * B[f'g_{rec}'].values[s & y23]).sum()
        m[s] = B.eef_coste.values[s] * B[f'g_{rec}'].values[s] * L
    if rec == 'A1fixF1b3':  # neutral: total 2024 por ramo igual al de A1fixb3
        for line in LINES:
            s = (B.line == line).values & y24; m[s] *= res['A1fixb3']['_m'][s].sum() / m[s].sum()
    seg = {}
    for line in LINES:
        s = (B.line == line).values
        for yy, ym in ((2023, y23), (2024, y24)):
            for nm, nn in (('nuevo', nb), ('renov', ~nb)):
                k = s & ym & nn
                seg[f'{line}_{yy}_{nm}'] = {'AE': round(float(B.t0.values[k].sum() / m[k].sum()), 4), 'AE_cuerpo': round(float(B.t0c.values[k].sum() / (m[k].sum() * B.t0c.values[s & ym].sum() / B.t0.values[s & ym].sum())), 4),
                                            'siniestros': int(B.n.values[k].sum()), 'exposicion': round(float(B.eef_coste.values[k].sum()), 1)}
    # factores estimados en 2023
    fac = {}
    for line in LINES:
        s = (B.line == line).values & y23
        ae_nb = B.t0.values[s & nb].sum() / m[s & nb].sum(); ae_all = B.t0.values[s].sum() / m[s].sum()
        aec_nb = B.t0c.values[s & nb].sum() / m[s & nb].sum(); aec_all = B.t0c.values[s].sum() / m[s].sum()
        n = B.n.values[s & nb].sum(); z = n / (n + K)
        fac[line] = {'bruto': ae_nb / ae_all, 'cuerpo': aec_nb / aec_all, 'credibilidad': (ae_nb / ae_all) ** z, 'Z': z, 'siniestros_nb_2023': int(n)}
    variants = {'sin_factor': m.copy()}
    for v in ('bruto', 'cuerpo', 'credibilidad'):
        mv = m.copy()
        for line in LINES:
            s = (B.line == line).values; f = fac[line][v]
            w = np.where(nb, f, 1.0)
            # reequilibrio: el total 2023 del ramo no cambia
            c = m[s & y23].sum() / (m[s & y23] * w[s & y23]).sum()
            mv[s] = m[s] * w[s] * c
        variants[v] = mv
    y = B.t0.values[y24]; comp = M.components(B.customer_id.values[y24], B.address_id.values[y24])
    mus = {k: v[y24] for k, v in variants.items()}
    bs = M.boot_d2_diff(y, mus, comp, n=4000)
    kc = y < np.quantile(y, 0.999)
    d2 = {k: {'D2_2024': round(float(M.d2(y, v)), 6), 'menos_sin_factor': round(float(M.d2(y, v) - M.d2(y, mus['sin_factor'])), 6),
              'IC90': [round(float(np.quantile(bs[k] - bs['sin_factor'], q)), 6) for q in (0.05, 0.95)],
              'cuerpo_menos_sin_factor': round(float(M.d2(y[kc], v[kc]) - M.d2(y[kc], mus['sin_factor'][kc])), 6),
              **{f'D2_{l}': round(float(M.d2(y[(B.line.values[y24] == l)], v[(B.line.values[y24] == l)])), 5) for l in LINES}} for k, v in mus.items()}
    res[rec] = {'segmentos': seg, 'factores_2023': {l: {k: (round(float(v), 4) if isinstance(v, float) else v) for k, v in f.items()} for l, f in fac.items()}, 'pares_2024': d2, '_m': m}
for rec in res: res[rec].pop('_m')
out['fuera_de_tiempo_2023_a_2024'] = res
# 2. agrupado 2023-2024 con la receta de producción (relatividades completas) y efecto en 2025
pr = {}
prod = pd.read_csv(O / 'A1fixF1b3n_2025.csv', dtype={'row_id': str}).set_index('row_id').prediction
for line in LINES:
    b = pd.read_parquet(R / f'salidas/s2/base_{line}.parquet')
    g = np.exp(b.row_id.map(lg(SRC['A1fixb3']['full'][line], line)).values)
    tr = (b.split == 'train').values; te = (b.split == 'test').values; nbb = b.new_business.values.astype(bool)
    L = b.t0.values[tr].sum() / (b.eef_coste.values[tr] * g[tr]).sum(); m = b.eef_coste.values * g * L
    t0c = b.row_id.map(capd).fillna(0.0).values; n = b.row_id.map(nclm).fillna(0).values
    ae_nb = b.t0.values[tr & nbb].sum() / m[tr & nbb].sum(); aec_nb = t0c[tr & nbb].sum() / m[tr & nbb].sum() / (t0c[tr].sum() / b.t0.values[tr].sum())
    nn = n[tr & nbb].sum(); z = nn / (nn + K)
    p = prod.loc[b.row_id.values[te]].values; share = p[nbb[te]].sum() / p.sum()
    ef = {}
    for v, f in (('bruto', ae_nb), ('cuerpo', aec_nb), ('credibilidad', ae_nb ** z)):
        w = np.where(nbb, f, 1.0); c = m[tr].sum() / (m[tr] * w[tr]).sum()  # total 2023-2024 sin cambio
        ef[v] = {'factor_nb': round(float(f * c), 4), 'factor_renov': round(float(c), 4), 'cambio_total_2025': round(float((p * w[te] * c).sum() / p.sum() - 1), 4)}
    pr[line] = {'AE_nb_2023_24': round(float(ae_nb), 4), 'AE_nb_cuerpo_2023_24': round(float(aec_nb), 4), 'siniestros_nb': int(nn), 'Z': round(float(z), 3),
                'peso_nb_en_2025': round(float(share), 4), 'efecto_en_2025': ef}
out['agrupado_2023_24_y_2025'] = pr
json.dump(out, open(O / 'nb_nivel_revision.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
