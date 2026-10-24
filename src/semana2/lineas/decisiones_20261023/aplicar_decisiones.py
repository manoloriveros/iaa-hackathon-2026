"""Aplicación de las cuatro decisiones del participante de semana 2 (Claude, 23 de octubre de 2026).

Sigue la preinscripción preinscripcion_decisiones_20261023.json (CLA-S2-DEC-20261023):
CAPS2-01 (capital entre mil con la prueba de prima por mil), CLIMA-S2-01 (bloque de clima de la dirección
con variables persistentes y 2025 como escenario), NB-CRED-01 (nivel del nuevo negocio con credibilidad
frente al desarrollado) y GASTO-F-01 (gasto fijo según exposición en la prima comercial).

No ajusta modelos de precios ni cambia archivos de Codex. Los GLM de NB-CRED-01 solo estiman la
relatividad del nuevo negocio. Escribe agregados en --out y las tablas por fila o dirección en --privado.

Uso desde C:/dev/Hakaton (necesita pandas, pyarrow, scipy y matplotlib):
    python "Hackaton/Semana 2/Claude/decisiones_20261023/aplicar_decisiones.py"
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import platform
import sys
import time

sys.dont_write_bytecode = True
AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import numpy as np
import pandas as pd
import pyarrow
import pyarrow.parquet as pq
import scipy

import glm_robusto as gr

LINES = ['motor', 'buildings', 'contents']
HOGAR = ['buildings', 'contents']
AGE_BINS = [16, 24, 34, 49, 64, 200]
AGE_LABELS = ['17-24', '25-34', '35-49', '50-64', '65+']
CAP_THRESHOLD = {'buildings': 5_000_000, 'contents': 2_000_000}
WEATHER_VARS = ['hail_days', 'wind_exposure_index', 'freezing_days', 'dry_summer_index', 'wildfire_index',
                'rainfall_mm', 'mean_temperature_c']
PERSISTENCIA_MIN = 0.80
PARES_CLIMA = [('buildings', 'storm', 'wind_exposure_index'), ('buildings', 'fire', 'wildfire_index'),
               ('buildings', 'flood', 'rainfall_mm'), ('contents', 'flood', 'rainfall_mm'),
               ('buildings', 'escape_of_water', 'rainfall_mm'), ('contents', 'escape_of_water', 'rainfall_mm')]
COVS = {
    'motor': dict(cat=['driver_age_band', 'yl_band', 'ncb_band', 'vehicle_value_group', 'vage_band', 'cover_type',
                       'vehicle_use', 'overnight_parking', 'named_young_driver', 'fuel_type', 'body_type',
                       'transmission', 'channel', 'payment_method', 'voluntary_excess', 'urban_density'],
                  cont=[]),
    'buildings': dict(cat=['policyholder_age_band', 'occupancy', 'smoke_alarms', 'accidental_damage_cover', 'mortgage',
                           'voluntary_excess', 'channel', 'payment_method', 'urban_density', 'flood_zone',
                           'property_type', 'roof_type', 'basement', 'soil_type', 'prop_age_band'],
                      cont=['log_si']),
    'contents': dict(cat=['policyholder_age_band', 'tenure', 'security_level', 'high_value_items',
                          'accidental_damage_cover', 'works_from_home', 'lodgers', 'bicycle_cover', 'voluntary_excess',
                          'channel', 'payment_method', 'urban_density', 'property_type', 'flood_zone'],
                     cont=['log_si'])}
MIN_SINIESTROS_TAU = 100
F_EMERGENTE = 85.0
CAT_REASEGURO = 0.12
DENOM_BASE = 1 - 0.15 - 0.08 - 0.08
COMISION = {'direct': 0.0, 'broker': 0.20}


# ----------------------------------------------------------------------------------------------- utilidades
def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def to_py(o):
    if isinstance(o, dict):
        return {str(k): to_py(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [to_py(v) for v in o]
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return None if np.isnan(o) else float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, float) and np.isnan(o):
        return None
    if isinstance(o, (pd.Timestamp, dt.date)):
        return str(o)[:10]
    return o


def read(folder: pathlib.Path, name: str) -> pd.DataFrame:
    return pq.read_table(folder / f'{name}.parquet').to_pandas()


def tweedie_dev(y, mu, w):
    p = 1.5
    d = 2 * (np.power(y, 2 - p) / ((1 - p) * (2 - p)) - y * np.power(mu, 1 - p) / (1 - p) + np.power(mu, 2 - p) / (2 - p))
    return float(np.sum(w * d) / np.sum(w))


def d2(y, mu, w=None):
    y = np.asarray(y, float)
    mu = np.asarray(mu, float)
    w = np.ones_like(y) if w is None else np.asarray(w, float)
    mu0 = np.full_like(y, np.sum(w * y) / np.sum(w))
    return 1 - tweedie_dev(y, mu, w) / tweedie_dev(y, mu0, w)


def bandas(s, cortes, etiquetas):
    return pd.cut(s.astype(float), cortes, labels=etiquetas).astype(str)


# ----------------------------------------------------------------------------------------------- datos
class Mercado:
    """Pólizas con siniestros aceptados asignados por póliza y fecha de ocurrencia (misma regla que la revisión)."""

    def __init__(self, name: str, folder: pathlib.Path, test: bool):
        self.name, self.folder = name, folder
        c = read(folder, 'claims')
        if name == 'developed':
            c = c[c.claim_id.str.len() != 11].copy()          # DUP01 (D41/D42)
        c['loss_date'] = pd.to_datetime(c.loss_date)
        c['net'] = c.incurred_to_date - c.recoveries
        self.addresses = read(folder, 'addresses')
        self.weather = read(folder, 'weather')
        self.pol, self.test, acc = {}, {}, []
        for l in LINES:
            p = self._fechas(read(folder, f'policies_{l}'), l)
            if test:
                self.test[l] = self._fechas(read(folder, f'test_{l}'), l)
            cl = c[c.line == l]
            m = cl.merge(p[['row_id', 'policy_id', 'customer_id', 'period_start', 'period_end']], on='policy_id', how='left')
            m = m[(m.loss_date >= m.period_start) & (m.loss_date <= m.period_end)]
            a = m[(m.status != 'repudiated')].copy()
            a['line'] = l
            acc.append(a)
            pos = a[a.net > 0]
            g = pos.groupby('row_id').agg(n=('claim_id', 'size'), t0p=('net', 'sum'))
            t0 = a.groupby('row_id').net.sum().rename('t0')
            p = p.merge(g, left_on='row_id', right_index=True, how='left').merge(t0, left_on='row_id', right_index=True, how='left')
            p[['n', 't0p', 't0']] = p[['n', 't0p', 't0']].fillna(0)
            self.pol[l] = p
        self.acc = pd.concat(acc, ignore_index=True)

    @staticmethod
    def _fechas(q: pd.DataFrame, l: str) -> pd.DataFrame:
        q['period_start'] = pd.to_datetime(q.period_start)
        q['period_end'] = pd.to_datetime(q.period_end)
        q['dias'] = (q.period_end - q.period_start).dt.days + 1
        q['e'] = q.dias / 365
        q['year'] = q.period_start.dt.year
        q['line'] = l
        return q


def preparar(M: Mercado, l: str, years, si_model: dict | None) -> pd.DataFrame:
    p = M.pol[l]
    p = p[p.year.isin(years)].copy()
    a = M.addresses.set_index('address_id')
    p = p.join(a[['region', 'urban_density', 'flood_zone', 'property_type', 'roof_type', 'basement', 'soil_type',
                  'year_built']], on='address_id')
    if l == 'motor':
        if 'driver_age_band' not in p.columns:
            p['driver_age_band'] = pd.cut(p.driver_age, AGE_BINS, labels=AGE_LABELS).astype(str)
        p['yl_band'] = bandas(p.years_licensed, [-np.inf, 2, 5, 10, 20, np.inf], ['0-2', '3-5', '6-10', '11-20', '21+'])
        p['ncb_band'] = bandas(p.ncb_years, [-np.inf, 0, 2, 4, 8, np.inf], ['0', '1-2', '3-4', '5-8', '9+'])
        p['vage_band'] = bandas(p.vehicle_age, [-np.inf, 2, 5, 9, 14, np.inf], ['0-2', '3-5', '6-9', '10-14', '15+'])
    else:
        if 'policyholder_age_band' not in p.columns:
            p['policyholder_age_band'] = pd.cut(p.policyholder_age, AGE_BINS, labels=AGE_LABELS).astype(str)
        si = p.row_id.map(si_model) if si_model is not None else None
        p['si_model'] = np.where(si.notna(), si, p.sum_insured) if si is not None else p.sum_insured
        p['log_si_raw'] = np.log(p.si_model.astype(float))
        p['prop_age_band'] = bandas(p.year_built, [-np.inf, 1949, 1979, 1999, np.inf], ['<1950', '1950-1979', '1980-1999', '2000+'])
    p['nb'] = p.new_business.astype(bool).astype(float)
    return p


def exposicion_mensual(p: pd.DataFrame, years) -> np.ndarray:
    """Matriz filas x 12 con la exposición (días/365) de cada fila en cada mes calendario, sumando años."""
    s = p.period_start.values.astype('datetime64[D]')
    e = p.period_end.values.astype('datetime64[D]')
    out = np.zeros((len(p), 12))
    for y in years:
        for m in range(12):
            ms = np.datetime64(f'{y}-{m + 1:02d}-01', 'D')
            me = (np.datetime64(f'{y}-{m + 1:02d}', 'M') + np.timedelta64(1, 'M')).astype('datetime64[D]') - np.timedelta64(1, 'D')
            d = (np.minimum(e, me) - np.maximum(s, ms)).astype(int) + 1
            out[:, m] += np.clip(d, 0, None) / 365
    return out


def indice_estacional(M: Mercado, l: str, years) -> np.ndarray:
    p = M.pol[l]
    p = p[p.year.isin(years) & ~p.new_business.astype(bool)]
    ex = exposicion_mensual(p, years).sum(axis=0)
    a = M.acc[(M.acc.line == l) & (M.acc.net > 0) & M.acc.row_id.isin(p.row_id)]
    n = a.groupby(a.loss_date.dt.month).size().reindex(range(1, 13), fill_value=0).values.astype(float)
    return (n / ex) / (n.sum() / ex.sum())


# ----------------------------------------------------------------------------------------------- CAPS2-01
def capital(E: Mercado, ev, priv: pathlib.Path):
    filas, res = [], {}
    for l in HOGAR:
        t = pd.concat([E.pol[l].assign(is_test=False), E.test[l].assign(is_test=True)], ignore_index=True)
        t['ppm'] = 1000 * t.written_premium / t.sum_insured
        normal = t[t.sum_insured <= CAP_THRESHOLD[l]]
        lo, hi, med = normal.ppm.min(), normal.ppm.max(), normal.ppm.median()
        ext = t[t.sum_insured > CAP_THRESHOLD[l]].copy()
        ext['ppm_div'] = 1000 * ext.ppm
        ext['pasa'] = (ext.ppm < lo) & (ext.ppm_div >= lo) & (ext.ppm_div <= hi)
        ext['si_div'] = ext.sum_insured / 1000
        # confirmación por historia: otra fila de la póliza bajo el umbral con capital 0,80-1,25 veces el dividido
        otras = normal[['policy_id', 'row_id', 'sum_insured']].rename(columns={'row_id': 'otra', 'sum_insured': 'si_otra'})
        h = ext[['row_id', 'policy_id', 'si_div']].merge(otras, on='policy_id', how='left')
        h['ok'] = (h.si_div / h.si_otra).between(0.80, 1.25)
        conf = h.groupby('row_id').ok.any()
        hay_otra = h.groupby('row_id').otra.apply(lambda s: s.notna().any())
        ext['confirmada'] = ext.row_id.map(conf).fillna(False).astype(bool)
        ext['con_otra_fila_normal'] = ext.row_id.map(hay_otra).fillna(False).astype(bool)
        brecha_ext = float(lo / ext.ppm.max())
        res[l] = dict(
            umbral=CAP_THRESHOLD[l], filas_normales=len(normal), ppm_normal_min=lo, ppm_normal_max=hi,
            ppm_normal_mediana=med, filas_sobre_umbral=len(ext), pasan=int(ext.pasa.sum()), no_pasan=int((~ext.pasa).sum()),
            pasan_train=int((ext.pasa & ~ext.is_test).sum()), pasan_test=int((ext.pasa & ext.is_test).sum()),
            ppm_bruta_mediana=float(ext.ppm.median()), ppm_bruta_max=float(ext.ppm.max()),
            ppm_dividida_mediana=float(ext.ppm_div.median()), ppm_dividida_min=float(ext.ppm_div.min()),
            ppm_dividida_max=float(ext.ppm_div.max()),
            veces_hueco_min_normal_sobre_max_extrema=brecha_ext,
            confirmadas_por_historia=int(ext.confirmada.sum()), con_otra_fila_normal=int(ext.con_otra_fila_normal.sum()),
            control_hueco_preinscrito=int((normal.ppm < lo / 10).sum()),
            control_hueco_mediana_entre_100=int((normal.ppm < med / 100).sum()),
            capital_dividido_max=float(ext.si_div.max()), capital_normal_max=float(normal.sum_insured.max()),
            por_anio={int(y): int(g.pasa.sum()) for y, g in ext.groupby('year')})
        ext['line'] = l
        filas.append(ext)
    ext = pd.concat(filas, ignore_index=True)
    tabla = pd.DataFrame(dict(
        row_id=ext.row_id, line=ext.line, year=ext.year.astype(int), is_test=ext.is_test, policy_id=ext.policy_id,
        sum_insured_raw=ext.sum_insured, sum_insured_model=np.where(ext.pasa, ext.si_div, np.nan),
        audit_capital_scale_adjusted=ext.pasa, audit_capital_scale_confirmed=ext.pasa & ext.confirmada,
        ppm_raw=ext.ppm, ppm_model=np.where(ext.pasa, ext.ppm_div, np.nan))).sort_values('row_id').reset_index(drop=True)
    ruta = priv / 'capital_caps2_01.parquet'
    pq.write_table(pyarrow.Table.from_pandas(tabla, preserve_index=False), ruta)
    lista = '\n'.join(sorted(tabla.row_id[tabla.audit_capital_scale_adjusted])) + '\n'
    res['total_divididas'] = int(tabla.audit_capital_scale_adjusted.sum())
    res['total_divididas_test'] = int((tabla.audit_capital_scale_adjusted & tabla.is_test).sum())
    res['total_divididas_train'] = int((tabla.audit_capital_scale_adjusted & ~tabla.is_test).sum())
    res['total_no_pasan'] = int((~tabla.audit_capital_scale_adjusted).sum())
    res['lista_sha256'] = hashlib.sha256(lista.encode()).hexdigest()
    res['tabla'] = dict(ruta=ruta.name, filas=len(tabla), sha256=sha256(ruta))
    ev['capital'] = res
    return dict(zip(tabla.row_id[tabla.audit_capital_scale_adjusted], tabla.sum_insured_model[tabla.audit_capital_scale_adjusted])), ext


# ----------------------------------------------------------------------------------------------- CLIMA-S2-01
def clima(E: Mercado, D: Mercado, ev, priv: pathlib.Path, rev_ev: dict):
    w = E.weather
    piv = w.pivot(index='address_id', columns='year', values=WEATHER_VARS)
    pers = {}
    for v in WEATHER_VARS:
        r1 = float(piv[(v, 2023)].corr(piv[(v, 2024)]))
        r2 = float(piv[(v, 2024)].corr(piv[(v, 2025)]))
        pers[v] = dict(r_2023_2024=r1, r_2024_2025=r2, persistente=bool(r1 >= PERSISTENCIA_MIN and r2 >= PERSISTENCIA_MIN))
    vars_p = [v for v in WEATHER_VARS if pers[v]['persistente']]
    filas = []
    for y, otros in [(2023, [2024]), (2024, [2023]), (2025, [2023, 2024])]:
        d = pd.DataFrame({'address_id': piv.index, 'year': y})
        for v in vars_p:
            d[f'x_clima_dir_{v}'] = np.mean([piv[(v, o)].values for o in otros], axis=0)
        filas.append(d)
    bloque = pd.concat(filas, ignore_index=True)
    ruta = priv / 'clima_direccion_s2_01.parquet'
    pq.write_table(pyarrow.Table.from_pandas(bloque, preserve_index=False), ruta)
    # comprobación descriptiva: frecuencia 2023 por terciles del bloque y del clima del propio año
    comp = []
    for M, years, otros_de in [(E, [2023], {2023: [2024]}), (D, [2021, 2022, 2023], None)]:
        wp = M.weather.pivot(index='address_id', columns='year', values=WEATHER_VARS)
        for l, peril, v in PARES_CLIMA:
            p = M.pol[l]
            p = p[p.year.isin(years)][['row_id', 'address_id', 'year', 'e']].copy()
            p['propio'] = np.nan
            for yy in years:
                msk = (p.year == yy).values
                p.loc[msk, 'propio'] = p.address_id[msk].map(wp[(v, yy)]).values
            if M.name == 'emerging':
                p['bloque'] = p.address_id.map(wp[(v, 2024)])
            else:
                # desarrollado: media de los otros años de 2021-2024 (sin 2025), la misma idea con más años
                anios = [2021, 2022, 2023, 2024]
                suma = sum(p.address_id.map(wp[(v, yy)]).values for yy in anios)
                p['bloque'] = (suma - p.propio.values) / (len(anios) - 1)
            n = M.acc[(M.acc.line == l) & (M.acc.peril == peril) & (M.acc.net > 0)].groupby('row_id').size()
            p['n'] = p.row_id.map(n).fillna(0)
            out = dict(mercado=M.name, ramo=l, peligro=peril, variable=v, siniestros=int(p.n.sum()))
            for col in ['bloque', 'propio']:
                q = pd.qcut(p[col].rank(method='first'), 3, labels=['bajo', 'medio', 'alto'])
                f = p.groupby(q, observed=True).apply(lambda g: g.n.sum() / g.e.sum(), include_groups=False)
                out[f'razon_alto_bajo_{col}'] = float(f['alto'] / f['bajo'])
                out[f'frecuencias_{col}'] = {k: float(x) for k, x in f.items()}
            comp.append(out)
    esc = rev_ev['clima']['sensibilidad_2025']
    ev['clima'] = dict(persistencia=pers, umbral=PERSISTENCIA_MIN, variables_bloque=vars_p,
                       regla_anios={'2023': [2024], '2024': [2023], '2025': [2023, 2024]},
                       tabla=dict(ruta=ruta.name, filas=len(bloque), sha256=sha256(ruta)),
                       comprobacion=comp, escenario_2025=esc)


# ----------------------------------------------------------------------------------------------- NB-CRED-01
def referencias(dev_df, cats):
    return {c: pd.Series(gr.txt(dev_df[c])).value_counts().idxmax() for c in cats}


def ajustar_mercado(p: pd.DataFrame, sev: pd.DataFrame, l, refs, centro, region_ref, estacional: np.ndarray | None, years):
    cats = COVS[l]['cat'] + ['region']
    refs = dict(refs, region=region_ref)
    p = p.copy()
    if COVS[l]['cont']:
        p['log_si'] = p.log_si_raw - centro
    exm = exposicion_mensual(p, years)
    p['e_s'] = exm @ estacional if estacional is not None else exm.sum(axis=1)
    p = p[p.e_s > 0]
    X, nombres = gr.disenar(p, cats, refs, COVS[l]['cont'] + ['nb'])
    f = gr.ajustar(X, p.n.values, np.log(p.e_s.values), 'poisson', p.customer_id.values)
    s = sev.merge(p[['row_id'] + cats + COVS[l]['cont'] + ['nb']], on='row_id', how='inner')
    Xs, nombres_s = gr.disenar(s, cats, refs, COVS[l]['cont'] + ['nb'])
    g = gr.ajustar(Xs, s.net.values, None, 'gamma', s.customer_id.values)
    cnt = {}
    for c in cats:
        v = gr.txt(p[c])
        for lv, k in p.n.groupby(v).sum().items():
            cnt[f'{c}={lv}'] = float(k)
    return dict(f=dict(zip(nombres, f['beta'])), fse=dict(zip(nombres, f['se'])), s=dict(zip(nombres_s, g['beta'])),
                sse=dict(zip(nombres_s, g['se'])), conteos=cnt, filas=len(p), siniestros=int(p.n.sum()),
                siniestros_sev=len(s), convergio=bool(f['convergio'] and g['convergio']),
                iteraciones=[f['iteraciones'], g['iteraciones']], clusters=[f['clusters'], g['clusters']])


def tau2(fits_em, fits_dev, comp, excluir_ncb=False):
    filas = []
    for l in LINES:
        fe, fd = fits_em[l], fits_dev[l]
        b, s = (comp, comp + 'se')
        for k, be in fe[b].items():
            if k in ('intercepto', 'nb', 'log_si') or k.startswith('region=') or k not in fd[b]:
                continue
            if excluir_ncb and k.startswith('ncb_band='):
                continue
            if fe['conteos'].get(k, 0) < MIN_SINIESTROS_TAU:
                continue
            filas.append((l, k, be - fd[b][k], fe[s][k], fd[s][k]))
    d = np.array([x[2] for x in filas])
    se_e = np.array([x[3] for x in filas])
    se_d = np.array([x[4] for x in filas])
    t2 = max(0.0, float(np.mean(d ** 2 - se_e ** 2 - se_d ** 2))) if len(d) else 0.0
    return t2, len(filas), filas


def credibilidad(fits_em, fits_dev, excluir_ncb=False):
    t2f, nf, lf = tau2(fits_em, fits_dev, 'f', excluir_ncb)
    t2s, ns, ls = tau2(fits_em, fits_dev, 's', excluir_ncb)
    out = dict(tau_f=float(np.sqrt(t2f)), tau_s=float(np.sqrt(t2s)), niveles_tau_f=nf, niveles_tau_s=ns, ramos={})
    for l in LINES:
        fe, fd = fits_em[l], fits_dev[l]
        tf_e, tf_d, sf_e = fe['f']['nb'], fd['f']['nb'], fe['fse']['nb']
        ts_e, ts_d, ss_e = fe['s']['nb'], fd['s']['nb'], fe['sse']['nb']
        zf = t2f / (t2f + sf_e ** 2) if t2f + sf_e ** 2 > 0 else 0.0
        zs = t2s / (t2s + ss_e ** 2) if t2s + ss_e ** 2 > 0 else 0.0
        th_em = tf_e + ts_e
        th_dev = tf_d + ts_d
        th = zf * tf_e + (1 - zf) * tf_d + zs * ts_e + (1 - zs) * ts_d
        out['ramos'][l] = dict(theta_f_em=tf_e, se_f_em=sf_e, theta_f_dev=tf_d, se_f_dev=fd['fse']['nb'], Z_f=zf,
                               theta_s_em=ts_e, se_s_em=ss_e, theta_s_dev=ts_d, se_s_dev=fd['sse']['nb'], Z_s=zs,
                               theta_em=th_em, theta_dev=th_dev, theta_cred=th,
                               rel_em=float(np.exp(th_em)), rel_dev=float(np.exp(th_dev)), rel_cred=float(np.exp(th)),
                               rel_f_em=float(np.exp(tf_e)), rel_f_dev=float(np.exp(tf_d)),
                               rel_s_em=float(np.exp(ts_e)), rel_s_dev=float(np.exp(ts_d)),
                               c=float(np.exp(th - th_em)), c_solo_desarrollado=float(np.exp(th_dev - th_em)))
    return out


def relatividad_bruta(p):
    nb, re = p[p.nb == 1], p[p.nb == 0]
    fr = (nb.n.sum() / nb.e.sum()) / (re.n.sum() / re.e.sum())
    pp = (nb.t0p.sum() / nb.e.sum()) / (re.t0p.sum() / re.e.sum())
    return dict(frecuencia=float(fr), prima_pura=float(pp), siniestros_nb=int(nb.n.sum()), filas_nb=len(nb))


def concentracion(M: Mercado, l: str, years) -> dict:
    """Descriptivo no preinscrito: peso de los cinco mayores siniestros en el coste NB y REN."""
    p = M.pol[l]
    p = p[p.year.isin(years)]
    nbm = p.set_index('row_id').new_business.astype(bool)
    a = M.acc[(M.acc.line == l) & (M.acc.net > 0) & M.acc.row_id.isin(p.row_id)].copy()
    a['nb'] = a.row_id.map(nbm)
    out = {}
    for nb, g in a.groupby('nb'):
        x = np.sort(g.net.values)
        out['NB' if nb else 'REN'] = dict(siniestros=len(x), media=float(x.mean()), mediana=float(np.median(x)),
                                          media_sin_5_mayores=float(x[:-5].mean()), cuota_5_mayores=float(x[-5:].sum() / x.sum()),
                                          maximo=float(x.max()))
    return out


def nb_credibilidad(E: Mercado, D: Mercado, si_model, oof: pd.DataFrame, ev, log):
    yrs_e, yrs_d = [2023], [2021, 2022, 2023]
    est_dev = {l: indice_estacional(D, l, yrs_d) for l in LINES}
    est_em = {l: indice_estacional(E, l, yrs_e) for l in LINES}
    prep_e = {l: preparar(E, l, yrs_e, si_model) for l in LINES}
    prep_d = {l: preparar(D, l, yrs_d, None) for l in LINES}
    sev_e = {l: E.acc[(E.acc.line == l) & (E.acc.net > 0)][['row_id', 'customer_id', 'net']] for l in LINES}
    sev_d = {l: D.acc[(D.acc.line == l) & (D.acc.net > 0)][['row_id', 'customer_id', 'net']] for l in LINES}
    refs = {l: referencias(prep_d[l], COVS[l]['cat']) for l in LINES}
    centro = {l: float(prep_d[l].log_si_raw.mean()) if l in HOGAR else 0.0 for l in LINES}
    rref = {('e', l): pd.Series(gr.txt(prep_e[l].region)).value_counts().idxmax() for l in LINES}
    rref.update({('d', l): pd.Series(gr.txt(prep_d[l].region)).value_counts().idxmax() for l in LINES})
    bruta = {l: dict(emergente=relatividad_bruta(prep_e[l]), desarrollado=relatividad_bruta(prep_d[l])) for l in LINES}
    variantes = {'principal': (est_dev, False), 'sin_estacionalidad': (None, False), 'estacional_emergente': ('em', False)}
    fits = {}
    for nombre, (est, _) in variantes.items():
        fe, fd = {}, {}
        for l in LINES:
            t = time.time()
            ee = None if est is None else (est_em[l] if est == 'em' else est[l])
            ed = None if est is None else (est_em[l] if est == 'em' else est[l])
            fe[l] = ajustar_mercado(prep_e[l], sev_e[l], l, refs[l], centro[l], rref[('e', l)], ee, yrs_e)
            fd[l] = ajustar_mercado(prep_d[l], sev_d[l], l, refs[l], centro[l], rref[('d', l)], ed, yrs_d)
            log(f'  {nombre} {l}: {time.time() - t:.0f} s')
        fits[nombre] = (fe, fd)
    res = dict(datos=dict(emergente=yrs_e, desarrollado=yrs_d),
               indice_estacional_desarrollado={l: est_dev[l].tolist() for l in LINES},
               indice_estacional_emergente={l: est_em[l].tolist() for l in LINES},
               referencias=refs, relatividad_bruta=bruta, ajustes={}, credibilidad={})
    for nombre, (fe, fd) in fits.items():
        res['ajustes'][nombre] = {l: dict(emergente={k: v for k, v in fe[l].items() if k not in ('f', 'fse', 's', 'sse', 'conteos')},
                                          desarrollado={k: v for k, v in fd[l].items() if k not in ('f', 'fse', 's', 'sse', 'conteos')})
                                  for l in LINES}
        res['credibilidad'][nombre] = credibilidad(fe, fd)
    fe, fd = fits['principal']
    res['credibilidad']['principal_sin_ncb_en_tau'] = credibilidad(fe, fd, excluir_ncb=True)
    _, _, lista_f = tau2(fe, fd, 'f')
    _, _, lista_s = tau2(fe, fd, 's')
    res['niveles_tau'] = dict(frecuencia=[dict(ramo=a, nivel=b, delta=c, se_em=d, se_dev=e) for a, b, c, d, e in lista_f],
                              severidad=[dict(ramo=a, nivel=b, delta=c, se_em=d, se_dev=e) for a, b, c, d, e in lista_s])
    # coeficientes completos de la variante principal (para la tabla de relatividades)
    coef = []
    for l in LINES:
        for comp in ['f', 's']:
            for k, b in fe[l][comp].items():
                coef.append(dict(ramo=l, componente=comp, nivel=k, beta_em=b, se_em=fe[l][comp + 'se'][k],
                                 beta_dev=fd[l][comp].get(k), se_dev=fd[l][comp + 'se'].get(k),
                                 siniestros_em=fe[l]['conteos'].get(k)))
    res['_coeficientes'] = coef
    # diagnóstico por folds sobre los OOF guardados de Codex
    fold_de = oof.drop_duplicates('row_id').set_index('row_id').fold
    cred_k = {}
    for k in sorted(fold_de.unique()):
        fek = {}
        for l in LINES:
            pk = prep_e[l][prep_e[l].row_id.map(fold_de) != k]
            fek[l] = ajustar_mercado(pk, sev_e[l][sev_e[l].row_id.isin(pk.row_id)], l, refs[l], centro[l], rref[('e', l)], est_dev[l], yrs_e)
        cred_k[int(k)] = credibilidad(fek, fd)
        log(f'  fold {k}: listo')
    res['credibilidad_por_fold'] = cred_k
    res['concentracion_severidad'] = {l: dict(emergente=concentracion(E, l, yrs_e), desarrollado=concentracion(D, l, yrs_d))
                                      for l in LINES}
    ev['nuevo_negocio'] = res
    return res, prep_e


def diagnostico_oof(oof: pd.DataFrame, cred_k: dict, E: Mercado, ev):
    t = oof.copy()
    t['T0'] = t.T0.astype(float)
    t['fold'] = t.fold.astype(int)
    cuota25 = {}
    for l in LINES:
        te = E.test[l]
        cuota25[l] = float(te[te.new_business.astype(bool)].exposure.sum() / te.exposure.sum())
    b = t[t.model_id == 'W2-B00']
    pesos = {}
    for l, s in b.groupby('line'):
        enb, ere = s[s.x_new_business == 1].exposure.sum(), s[s.x_new_business == 0].exposure.sum()
        sh = enb / (enb + ere)
        pesos[(l, 1)], pesos[(l, 0)] = cuota25[l] / sh, (1 - cuota25[l]) / (1 - sh)
    t['w25'] = [pesos[(l, int(x))] for l, x in zip(t.line, t.x_new_business)]
    out = dict(cuota_nb_exposicion_test_2025=cuota25, pesos={f'{l}/{"NB" if x else "REN"}': v for (l, x), v in pesos.items()},
               recetas={})
    for m, s in t.groupby('model_id'):
        s = s.copy()
        g = {v: np.ones(len(s)) for v in ['emergente', 'credibilidad', 'desarrollado']}
        for k in sorted(s.fold.unique()):
            for l in LINES:
                fuera = (s.fold != k) & (s.line == l)
                nbm = fuera & (s.x_new_business == 1)
                rem = fuera & (s.x_new_business == 0)
                ratio = (s.T0[nbm].sum() / s.prediction[nbm].sum()) / (s.T0[rem].sum() / s.prediction[rem].sum())
                cr = cred_k[int(k)]['ramos'][l]
                sel = ((s.fold == k) & (s.line == l) & (s.x_new_business == 1)).values
                g['emergente'][sel] = ratio
                g['credibilidad'][sel] = ratio * cr['c']
                g['desarrollado'][sel] = ratio * cr['c_solo_desarrollado']
        o = {}
        nbs = (s.x_new_business == 1).values
        # no preinscrito (declarado): mismas métricas sin el 0,1 % de filas con mayor T0 de cada ramo
        corte = s.groupby('line').T0.transform(lambda x: x.quantile(0.999)).values
        cuerpo = s.T0.values <= corte
        for v, f in [('guardada', np.ones(len(s)))] + list(g.items()):
            pr = s.prediction.values * f
            o[v] = dict(D2_mezcla_2023=d2(s.T0, pr), D2_mezcla_2025=d2(s.T0, pr, s.w25),
                        AE_NB=float(s.T0[nbs].sum() / pr[nbs].sum()), AE_REN=float(s.T0[~nbs].sum() / pr[~nbs].sum()),
                        AE_mezcla_2025=float((s.T0 * s.w25).sum() / (pr * s.w25).sum()),
                        D2_NB=d2(s.T0[nbs], pr[nbs]),
                        D2_mezcla_2023_sin_01=d2(s.T0[cuerpo], pr[cuerpo]),
                        D2_mezcla_2025_sin_01=d2(s.T0[cuerpo], pr[cuerpo], s.w25[cuerpo]),
                        AE_NB_sin_01=float(s.T0[nbs & cuerpo].sum() / pr[nbs & cuerpo].sum()))
        # factor que daría factor_nuevo_negocio.py con todo 2023 (sin cruzar), como ejemplo de aplicación
        o['g_todo_2023'] = {}
        for l in LINES:
            sl = s[s.line == l]
            nb_, re_ = sl[sl.x_new_business == 1], sl[sl.x_new_business == 0]
            razon = (nb_.T0.sum() / nb_.prediction.sum()) / (re_.T0.sum() / re_.prediction.sum())
            c_full = ev['nuevo_negocio']['credibilidad']['principal']['ramos'][l]['c']
            o['g_todo_2023'][l] = dict(razon=float(razon), c=c_full, g_NB=float(razon * c_full))
        out['recetas'][m] = o
    out['filas_excluidas_sin_01'] = int((~cuerpo).sum())
    ev['diagnostico_oof'] = out


def escenario_bloque(E: Mercado, cred: dict, ev):
    out = {}
    for l in LINES:
        te = E.test[l]
        nb = te.new_business.astype(bool)
        ene = nb & (te.period_start.dt.month == 1)
        rel = cred['ramos'][l]['rel_cred']
        base = te.exposure[~nb].sum() + rel * te.exposure[nb].sum()
        esc = te.exposure[~nb].sum() + rel * te.exposure[nb & ~ene].sum() + te.exposure[ene].sum()
        rel_em = cred['ramos'][l]['rel_em']
        em = te.exposure[~nb].sum() + rel_em * te.exposure[nb].sum()
        out[l] = dict(cuota_exposicion_nb_enero=float(te.exposure[ene].sum() / te.exposure.sum()),
                      cuota_exposicion_nb=float(te.exposure[nb].sum() / te.exposure.sum()),
                      relatividad_creible=rel, relatividad_solo_emergente=rel_em,
                      cambio_nivel_si_bloque_como_renovacion=float(esc / base - 1),
                      cambio_nivel_creible_frente_a_solo_emergente=float(base / em - 1))
    ev['escenario_bloque_transferido'] = out


# ----------------------------------------------------------------------------------------------- GASTO-F-01
def gasto_fijo(E: Mercado, ev):
    x = read(E.folder, 'expenses').set_index('item').emerging
    supuestos = dict(F=float(x['fixed_expense_per_policy']), v=float(x['variable_expense']), t=float(x['premium_tax']),
                     m=float(x['target_profit_margin']), r=float(x['cat_reinsurance']),
                     comision_direct=float(x['commission_direct']), comision_broker=float(x['commission_broker']),
                     comision_comparison_site=None if pd.isna(x['commission_comparison_site']) else float(x['commission_comparison_site']))
    esperado = dict(F=F_EMERGENTE, v=0.15, t=0.08, m=0.08, r=CAT_REASEGURO, comision_direct=COMISION['direct'],
                    comision_broker=COMISION['broker'])
    if any(abs(supuestos[k] - v) > 1e-12 for k, v in esperado.items()):
        raise SystemExit(f'expenses.parquet no coincide con las constantes: {supuestos}')
    r = read(E.folder, 'reference_policies')
    tests = pd.concat([E.test[l][['row_id', 'policy_id', 'e', 'exposure', 'period_start', 'period_end']].assign(line=l)
                       for l in LINES], ignore_index=True)
    e_pol = tests.groupby('policy_id').exposure.sum()
    n_pol = tests.groupby('policy_id').size()
    tasa = {}
    for l in LINES:
        p = E.pol[l]
        p = p[p.year == 2023]
        tasa[l] = float(p.t0.sum() / p.e.sum())
    filas = []
    for _, x in r.iterrows():
        d = DENOM_BASE - COMISION[x.channel]
        e = float(x.exposure)
        prop = x.line in HOGAR
        R = tasa[x.line] * e
        reglas = {'F_por_exposicion': F_EMERGENTE * e,
                  'F_por_poliza_y_anio': F_EMERGENTE * e / float(e_pol[x.policy_id]),
                  'F_entero_por_fila': F_EMERGENTE}
        fila = dict(row_id=x.row_id, policy_id=x.policy_id, line=x.line, channel=x.channel, new_business=bool(x.new_business),
                    period_start=str(x.period_start)[:10], period_end=str(x.period_end)[:10], exposure=e,
                    filas_poliza_2025=int(n_pol[x.policy_id]), exposicion_poliza_2025=float(e_pol[x.policy_id]),
                    denominador=d, written_premium=float(x.written_premium), R_ilustrativo=R)
        for k, F in reglas.items():
            P = (R * (1 + CAT_REASEGURO * prop) + F) / d
            fila[f'{k}_F'] = F
            fila[f'{k}_termino_F'] = F / d
            fila[f'{k}_P'] = P
            fila[f'{k}_P_anualizada'] = P / e
        filas.append(fila)
    t = pd.DataFrame(filas).sort_values(['line', 'row_id']).reset_index(drop=True)
    dif = t.F_entero_por_fila_P - t.F_por_exposicion_P
    ev['gasto_fijo'] = dict(
        supuestos_expenses=supuestos,
        tasa_ilustrativa_2023=tasa, denominadores={k: DENOM_BASE - v for k, v in COMISION.items()},
        referencias=t.to_dict(orient='records'),
        filas_con_exposicion_menor_0_99=int((t.exposure < 0.99).sum()),
        diferencia_max_F_entero_menos_exposicion=float(dif.max()),
        fila_diferencia_max=t.row_id[dif.idxmax()],
        diferencia_mediana=float(dif.median()),
        suma_termino_F_exposicion=float(t.F_por_exposicion_termino_F.sum()),
        suma_termino_F_entero=float(t.F_entero_por_fila_termino_F.sum()),
        suma_termino_F_poliza_anio=float(t.F_por_poliza_y_anio_termino_F.sum()))
    return t


# ----------------------------------------------------------------------------------------------- main
def main(a):
    t0 = time.time()
    a.out.mkdir(parents=True, exist_ok=True)
    a.privado.mkdir(parents=True, exist_ok=True)
    (a.out / 'tablas').mkdir(exist_ok=True)

    def log(m):
        print(f'[{time.time() - t0:6.0f} s] {m}', flush=True)

    if a.solo_manifiesto:
        escribir_manifiesto(a, json.loads((a.out / 'evidencia_decisiones.json').read_text(encoding='utf-8'))['entradas'])
        log('manifiesto reescrito')
        return
    pre = json.loads(a.preinscripcion.read_text(encoding='utf-8'))
    man_em = {f['name'].split('/')[-1]: f['sha256'] for f in json.load(open(a.manifest_em, encoding='utf-8'))['files']}
    man_dev = {pathlib.Path(f['path']).name: f['sha256'] for f in json.load(open(a.manifest_dev, encoding='utf-8'))['files']}
    entradas = {}
    for n in ['addresses', 'claims', 'policies_buildings', 'policies_contents', 'policies_motor', 'reference_policies',
              'test_buildings', 'test_contents', 'test_motor', 'weather', 'expenses']:
        h = sha256(a.emerging / f'{n}.parquet')
        entradas[f'emerging/{n}'] = dict(sha256=h, coincide=h == man_em[f'{n}.parquet'])
    for n in ['addresses', 'claims', 'policies_buildings', 'policies_contents', 'policies_motor', 'weather']:
        h = sha256(a.developed / f'{n}.parquet')
        entradas[f'developed/{n}'] = dict(sha256=h, coincide=h == man_dev[f'{n}.parquet'])
    m3 = json.load(open(a.oof.parent / 'manifest.json', encoding='utf-8'))['files']
    h = sha256(a.oof)
    entradas['codex/dev3/oof_2023.parquet'] = dict(sha256=h, coincide=h == [f['sha256'] for f in m3 if f['path'] == 'oof_2023.parquet'][0])
    h = sha256(a.revision)
    entradas['claude/revision_apertura_20261023/evidencia.json'] = dict(sha256=h)
    if not all(v.get('coincide', True) for v in entradas.values()):
        raise SystemExit(f'Huellas distintas: {entradas}')
    ev = dict(autor='Claude (Cowork)', utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
              preinscripcion=dict(id=pre['id'], sha256=sha256(a.preinscripcion), utc=pre['utc']),
              entradas=entradas,
              entorno=dict(python=platform.python_version(), pandas=pd.__version__, numpy=np.__version__,
                           pyarrow=pyarrow.__version__, scipy=scipy.__version__))
    log('cargando mercados')
    E = Mercado('emerging', a.emerging, test=True)
    D = Mercado('developed', a.developed, test=False)
    rev_ev = json.loads(a.revision.read_text(encoding='utf-8'))
    log('CAPS2-01')
    si_model, _ = capital(E, ev, a.privado)
    log('CLIMA-S2-01')
    clima(E, D, ev, a.privado, rev_ev)
    log('NB-CRED-01')
    oof = pq.read_table(a.oof).to_pandas()
    res, _ = nb_credibilidad(E, D, si_model, oof, ev, log)
    diagnostico_oof(oof, res['credibilidad_por_fold'], E, ev)
    escenario_bloque(E, res['credibilidad']['principal'], ev)
    log('GASTO-F-01')
    tg = gasto_fijo(E, ev)
    tg.to_csv(a.out / 'tablas' / 'gasto_fijo_referencias.csv', index=False)
    coef = pd.DataFrame(ev['nuevo_negocio'].pop('_coeficientes'))
    coef.to_csv(a.out / 'tablas' / 'coeficientes_glm_nb.csv', index=False)
    pd.DataFrame(ev['clima']['comprobacion']).drop(columns=['frecuencias_bloque', 'frecuencias_propio']).to_csv(
        a.out / 'tablas' / 'clima_comprobacion.csv', index=False)
    filas = []
    for m, o in ev['diagnostico_oof']['recetas'].items():
        for v, x in o.items():
            filas.append(dict(receta=m, variante=v, **x))
    pd.DataFrame(filas).to_csv(a.out / 'tablas' / 'diagnostico_oof_2023.csv', index=False)
    fac = {l: dict(c=x['c'], relatividad_creible=x['rel_cred'], theta_creible=x['theta_cred'], Z_f=x['Z_f'], Z_s=x['Z_s'])
           for l, x in ev['nuevo_negocio']['credibilidad']['principal']['ramos'].items()}
    (a.out / 'factores_nb_cred.json').write_text(json.dumps(to_py(dict(
        regla='NB-CRED-01', preinscripcion_sha256=ev['preinscripcion']['sha256'],
        uso='g_NB = (A/E_NB / A/E_REN) cruzado de la receta * c; g_REN = 1', ramos=fac)), ensure_ascii=False, indent=1),
        encoding='utf-8')
    ev['segundos'] = round(time.time() - t0)
    (a.out / 'evidencia_decisiones.json').write_text(json.dumps(to_py(ev), ensure_ascii=False, indent=1), encoding='utf-8')
    if not a.sin_figuras:
        import figuras_decisiones
        figuras_decisiones.dibujar(a.out, a.privado, E)
    escribir_manifiesto(a, entradas)
    log('hecho')


def escribir_manifiesto(a, entradas):
    salidas = sorted(x for x in a.out.rglob('*') if x.is_file() and '__pycache__' not in x.parts
                     and not x.name.startswith('verificacion_') and x.name != 'manifiesto.json')
    man = dict(autor='Claude (Cowork)', utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
               scripts={x.name: sha256(x) for x in sorted(AQUI.glob('*.py'))},
               entradas=entradas,
               salidas={str(x.relative_to(a.out)).replace('\\', '/'): sha256(x) for x in salidas},
               privado={x.name: sha256(x) for x in sorted(a.privado.glob('*.parquet'))})
    (a.out / 'manifiesto.json').write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    raiz = AQUI.parents[3] if len(AQUI.parents) > 3 else AQUI
    s2 = raiz / 'Hackaton/Semana 2'
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--emerging', type=pathlib.Path, default=s2 / 'Datos/emerging')
    ap.add_argument('--developed', type=pathlib.Path, default=raiz / 'Hackaton/Semana 1/Datos')
    ap.add_argument('--manifest-em', type=pathlib.Path, default=s2 / 'Codex/fuentes/download_manifest.json')
    ap.add_argument('--manifest-dev', type=pathlib.Path,
                    default=raiz / 'Preparación/artifacts/verification/iaa_launch_20261016/data_manifest.json')
    ap.add_argument('--oof', type=pathlib.Path, default=raiz / 'Hackaton/Repositorio_IAA2026/privado/semana2/desarrollo2023/dev3_20261023T181613Z_24c943a3/oof_2023.parquet')
    ap.add_argument('--revision', type=pathlib.Path, default=s2 / 'Claude/revision_apertura_20261023/evidencia.json')
    ap.add_argument('--preinscripcion', type=pathlib.Path, default=AQUI / 'preinscripcion_decisiones_20261023.json')
    ap.add_argument('--out', type=pathlib.Path, default=AQUI)
    ap.add_argument('--privado', type=pathlib.Path, default=raiz / 'Hackaton/Repositorio_IAA2026/privado/semana2/decisiones_participante_20261023')
    ap.add_argument('--sin-figuras', action='store_true')
    ap.add_argument('--solo-manifiesto', action='store_true', help='Solo reescribe manifiesto.json con los archivos actuales')
    main(ap.parse_args())
