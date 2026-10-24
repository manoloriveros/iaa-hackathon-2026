"""Revision independiente de la apertura de semana 2 (Claude, 23 de octubre de 2026).

Recalcula desde los Parquet originales, con codigo propio, las cifras del diagnostico de Codex
(COD-S2-20261023-001, Codex/DIAGNOSTICO_INICIAL.md) y anade comprobaciones descriptivas que
condicionan el plan de trabajo. No entrena modelos, no modifica datos y no escribe nada por fila:
la salida son agregados (evidencia.json y tablas CSV) con un manifiesto de huellas.

Uso desde la raiz C:/dev/Hakaton con el Python del laboratorio:
    python "Hackaton/Semana 2/Claude/revision_apertura_20261023/revisar_apertura.py" --out <carpeta>
Sin argumentos de datos toma las rutas del proyecto (Semana 2/Datos/emerging y Semana 1/Datos).
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

import numpy as np
import pandas as pd
import pyarrow
import pyarrow.parquet as pq
from scipy import stats

LINES = ['motor', 'buildings', 'contents']
EM_FILES = ['addresses', 'claims', 'customers', 'expenses', 'policies_buildings', 'policies_contents',
            'policies_motor', 'reference_policies', 'sample_submission', 'test_buildings', 'test_contents',
            'test_motor', 'weather']
DEV_FILES = ['addresses', 'claims', 'customers', 'policies_buildings', 'policies_contents', 'policies_motor',
             'weather']
VAL_DATE = pd.Timestamp('2024-12-31')
AGE_BINS = [16, 24, 34, 49, 64, 200]
AGE_LABELS = ['17-24', '25-34', '35-49', '50-64', '65+']
# Umbral de capital para separar la nube extrema (huecos observados: 0,81-0,89 M frente a 60-73 M en
# edificios; 0,24-0,28 M frente a 7,6-9,2 M en contenidos). Cualquier valor dentro del hueco da lo mismo.
CAP_THRESHOLD = {'buildings': 5_000_000, 'contents': 2_000_000}
CLIMA_PARES = [('motor', 'glass_hail', 'hail_days'),
               ('buildings', 'escape_of_water', 'freezing_days'),
               ('contents', 'escape_of_water', 'freezing_days'),
               ('buildings', 'subsidence', 'dry_summer_index'),
               ('buildings', 'storm', 'wind_exposure_index')]
WEATHER_VARS = ['hail_days', 'wind_exposure_index', 'freezing_days', 'dry_summer_index', 'wildfire_index',
                'rainfall_mm', 'mean_temperature_c']
FACTORES = {'motor': ['driver_age_band', 'ncb_g', 'cover_type', 'vehicle_use', 'overnight_parking',
                      'payment_method', 'channel', 'new_business', 'named_young_driver', 'urban_density'],
            'buildings': ['flood_zone', 'property_type', 'policyholder_age_band', 'occupancy', 'roof_type',
                          'new_business'],
            'contents': ['tenure', 'security_level', 'urban_density', 'policyholder_age_band', 'new_business']}


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
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if np.isnan(o) else float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, float) and np.isnan(o):
        return None
    if isinstance(o, (pd.Timestamp, dt.date)):
        return str(o)[:10]
    return o


def read(folder: pathlib.Path, name: str) -> pd.DataFrame:
    return pq.read_table(folder / f'{name}.parquet').to_pandas()


def dias(p: pd.DataFrame) -> pd.Series:
    return (pd.to_datetime(p.period_end) - pd.to_datetime(p.period_start)).dt.days + 1


def psi(a: pd.Series, b: pd.Series, bins: int = 10) -> float:
    if a.dtype.kind in 'fi' and a.nunique() > 12:
        qs = np.unique(np.nanquantile(a.dropna(), np.linspace(0, 1, bins + 1)))
        qs[0], qs[-1] = -np.inf, np.inf
        ca = pd.cut(a, qs, duplicates='drop').astype(str)
        cb = pd.cut(b, qs, duplicates='drop').astype(str)
    else:
        ca, cb = a.astype(str), b.astype(str)
    pa, pb = ca.value_counts(normalize=True), cb.value_counts(normalize=True)
    idx = pa.index.union(pb.index)
    pa = pa.reindex(idx).fillna(0) + 1e-4
    pb = pb.reindex(idx).fillna(0) + 1e-4
    return float(((pb - pa) * np.log(pb / pa)).sum())


class Mercado:
    """Tablas de un mercado con la etiqueta diagnostica T0 por fila (no es la base del proyecto)."""

    def __init__(self, name: str, folder: pathlib.Path):
        self.name = name
        self.folder = folder
        self.claims = read(folder, 'claims')
        if name == 'developed':
            # DUP01 de semana 1 (D41/D42): las 604 copias son los claim_id de once caracteres.
            self.claims = self.claims[self.claims.claim_id.str.len() != 11].copy()
        self.claims['loss_date'] = pd.to_datetime(self.claims.loss_date)
        self.claims['report_date'] = pd.to_datetime(self.claims.report_date)
        self.claims['net'] = self.claims.incurred_to_date - self.claims.recoveries
        self.customers = read(folder, 'customers')
        self.addresses = read(folder, 'addresses')
        self.weather = read(folder, 'weather')
        self.pol, self.asig, self.unassigned = {}, [], []
        for l in LINES:
            p = read(folder, f'policies_{l}')
            p['period_start'] = pd.to_datetime(p.period_start)
            p['period_end'] = pd.to_datetime(p.period_end)
            p['dias'] = dias(p)
            p['exp365'] = p.dias / 365
            p['year'] = p.period_start.dt.year
            cl = self.claims[self.claims.line == l]
            m = cl.merge(p[['row_id', 'policy_id', 'period_start', 'period_end']], on='policy_id', how='left')
            m['dentro'] = (m.loss_date >= m.period_start) & (m.loss_date <= m.period_end)
            k = m.groupby('claim_id').dentro.sum()
            if (k > 1).any():
                raise RuntimeError(f'{name} {l}: siniestros con mas de un periodo')
            a = m[m.dentro].drop(columns='dentro').copy()
            a['line'] = l
            self.asig.append(a)
            self.unassigned.append(cl[cl.claim_id.isin(k[k == 0].index)].assign(line=l))
            acc = a[a.status != 'repudiated']
            g = acc.groupby('row_id').agg(n=('claim_id', 'size'), t0=('net', 'sum'),
                                          n_open=('status', lambda s: int((s == 'open').sum())))
            p = p.merge(g, left_on='row_id', right_index=True, how='left')
            p[['n', 't0', 'n_open']] = p[['n', 't0', 'n_open']].fillna(0)
            p['line'] = l
            self.pol[l] = p
        self.asig = pd.concat(self.asig, ignore_index=True)
        self.unassigned = pd.concat(self.unassigned, ignore_index=True)
        self.acc = self.asig[self.asig.status != 'repudiated'].copy()
        self.acc['ay'] = self.acc.period_start.dt.year
        self.acc['delay'] = (self.acc.report_date - self.acc.loss_date).dt.days


def integridad(args, ev):
    man_em = {f['name'].split('/')[-1]: f for f in json.load(open(args.manifest_em, encoding='utf-8'))['files']}
    man_dev = {pathlib.Path(f['path']).name: f for f in json.load(open(args.manifest_dev, encoding='utf-8'))['files']}
    res = {'emerging': {}, 'developed': {}}
    for n in EM_FILES:
        p = args.emerging / f'{n}.parquet'
        h = sha256(p)
        ref = man_em[f'{n}.parquet']
        res['emerging'][n] = dict(bytes=p.stat().st_size, sha256=h, coincide_manifiesto_codex=h == ref['sha256'],
                                  bytes_remotos=ref['size'], coincide_bytes=p.stat().st_size == ref['size'],
                                  filas=pq.ParquetFile(p).metadata.num_rows)
    for n in DEV_FILES:
        p = args.developed / f'{n}.parquet'
        h = sha256(p)
        res['developed'][n] = dict(bytes=p.stat().st_size, sha256=h,
                                   coincide_manifiesto_oficial=h == man_dev[f'{n}.parquet']['sha256'])
    res['todas_coinciden'] = all(v['coincide_manifiesto_codex'] and v['coincide_bytes'] for v in res['emerging'].values()) \
        and all(v['coincide_manifiesto_oficial'] for v in res['developed'].values())
    res['archivos_comprobados'] = len(res['emerging']) + len(res['developed'])
    res['archivos_coinciden'] = sum(v['coincide_manifiesto_codex'] and v['coincide_bytes'] for v in res['emerging'].values()) \
        + sum(v['coincide_manifiesto_oficial'] for v in res['developed'].values())
    ev['integridad'] = res


def escala(E, D, args, ev):
    tests = {l: read(args.emerging, f'test_{l}') for l in LINES}
    s = read(args.emerging, 'sample_submission')
    cat = pd.concat([tests[l].row_id for l in LINES], ignore_index=True)
    ev['escala'] = dict(
        ids_coincidentes_entre_mercados=dict(
            clientes=len(set(E.customers.customer_id) & set(D.customers.customer_id)),
            direcciones=len(set(E.addresses.address_id) & set(D.addresses.address_id))),
        filas_train={l: len(E.pol[l]) for l in LINES}, filas_train_total=sum(len(E.pol[l]) for l in LINES),
        filas_test={l: len(tests[l]) for l in LINES}, filas_test_total=sum(len(tests[l]) for l in LINES),
        clientes=len(E.customers), direcciones=len(E.addresses),
        plantilla_filas=len(s), plantilla_ids_unicos=bool(s.row_id.is_unique),
        plantilla_mismo_orden_motor_buildings_contents=bool((s.row_id.values == cat.values).all()),
        claves_cliente_en_maestro=all(E.pol[l].customer_id.isin(E.customers.customer_id).all() and
                                      tests[l].customer_id.isin(E.customers.customer_id).all() for l in LINES),
        claves_direccion_en_maestro=all(E.pol[l].address_id.isin(E.addresses.address_id).all() and
                                        tests[l].address_id.isin(E.addresses.address_id).all() for l in LINES))
    return tests


def exposicion(E, tests, ev):
    out = {}
    tot = dict(cruda=0.0, dias_365=0.0, dias_36525=0.0)
    for l in LINES:
        p = E.pol[l]
        d, e = p.dias, p.exposure
        m365 = np.isclose(e, np.round(d / 365, 4), atol=5e-5)
        m360 = np.isclose(e, np.round(d / 360, 4), atol=5e-5)
        mdd = np.isclose(e, d)
        conv = np.select([m365, m360, mdd], ['ACT365', 'ACT360', 'DIAS'], 'OTRA')
        gt1 = e > 1
        y = p.year
        out[l] = dict(
            filas=len(p), mayores_que_uno=int(gt1.sum()), maximo=float(e.max()), dias_max=int(d.max()),
            convencion=pd.Series(conv).value_counts().to_dict(),
            ambiguas=int((m365 & m360).sum() + (m365 & mdd).sum() + (m360 & mdd).sum()),
            mayores_que_uno_por_convencion=pd.Series(conv[gt1.values]).value_counts().to_dict(),
            act360_hasta_360_dias=int(((conv == 'ACT360') & (d.values <= 360)).sum()),
            suma_cruda=float(e.sum()), suma_dias_365=float((d / 365).sum()), suma_dias_36525=float((d / 365.25).sum()),
            filas_que_cambian_con_dias_365=int((~m365).sum()),
            fin_31_12_2024=int(((p.period_end == '2024-12-31')).sum()),
            fin_30_12_2024=int(((p.period_end == '2024-12-30')).sum()),
            filas_que_cubren_31_12_2024=int(((p.period_start <= '2024-12-31') & (p.period_end >= '2024-12-31')).sum()),
            filas_2024=int((y == 2024).sum()), periodos_de_366_dias=int((d == 366).sum()))
        tot['cruda'] += e.sum(); tot['dias_365'] += (d / 365).sum(); tot['dias_36525'] += (d / 365.25).sum()
        t = tests[l]
        dt_ = dias(t)
        out[l]['test'] = dict(filas=len(t), act365=int(np.isclose(t.exposure, np.round(dt_ / 365, 4), atol=5e-5).sum()),
                              mayores_que_uno=int((t.exposure > 1).sum()), maximo=float(t.exposure.max()))
    out['total'] = tot
    out['total_convenciones'] = pd.Series(
        {k: sum(out[l]['convencion'].get(k, 0) for l in LINES) for k in ['ACT365', 'ACT360', 'DIAS', 'OTRA']}).to_dict()
    out['total_mayores_que_uno'] = sum(out[l]['mayores_que_uno'] for l in LINES)
    ev['exposicion'] = out


def siniestros(E, ev):
    c = E.claims
    out = dict(filas=len(c), ids_distintos=int(c.claim_id.nunique()), estado=c.status.value_counts().to_dict(),
               por_ramo=c.line.value_counts().to_dict(),
               perdida_min=c.loss_date.min(), perdida_max=c.loss_date.max(),
               reporte_min=c.report_date.min(), reporte_max=c.report_date.max(),
               perdidas_31_12_2024=int((c.loss_date == '2024-12-31').sum()),
               reportes_antes_de_perdida=int((c.report_date < c.loss_date).sum()))
    cols = [x for x in c.columns if x not in ('claim_id', 'net')]
    out['duplicados_exactos_salvo_claim_id'] = int(c.duplicated(cols).sum())
    out['duplicados_poliza_ramo_peligro_fecha'] = int(c.duplicated(['policy_id', 'line', 'peril', 'loss_date']).sum())
    asg = {}
    for l in LINES:
        n_l = int((c.line == l).sum())
        n_a = int((E.asig.line == l).sum())
        asg[l] = dict(siniestros=n_l, un_periodo=n_a, ninguno=n_l - n_a)
    out['asignacion'] = asg
    u = E.unassigned
    rows = []
    for l in LINES:
        p = E.pol[l]
        first = p.groupby('policy_id').period_start.min()
        ul = u[u.line == l].copy()
        ul['primer_inicio'] = ul.policy_id.map(first)
        ul['dias_antes'] = (ul.primer_inicio - ul.loss_date).dt.days
        rep = ul[['claim_id', 'policy_id', 'report_date']].merge(p[['policy_id', 'period_start', 'period_end']], on='policy_id')
        rep['dentro'] = (rep.report_date >= rep.period_start) & (rep.report_date <= rep.period_end)
        ul['reporte_en_periodo'] = ul.claim_id.map(rep.groupby('claim_id').dentro.any()).fillna(False)
        rows.append(ul)
    u2 = pd.concat(rows)
    out['sin_periodo'] = dict(
        total=len(u2), por_ramo=u2.line.value_counts().to_dict(),
        por_anio_perdida=u2.loss_date.dt.year.value_counts().sort_index().to_dict(),
        con_poliza_en_train=int(u2.primer_inicio.notna().sum()),
        todos_antes_del_primer_periodo=bool((u2.dias_antes > 0).all()),
        dias_antes_min=int(u2.dias_antes.min()), dias_antes_max=int(u2.dias_antes.max()),
        dias_antes_mediana=float(u2.dias_antes.median()),
        reportados_dentro_de_un_periodo_observado=int(u2.reporte_en_periodo.sum()),
        estado=u2.status.value_counts().to_dict(),
        neto_todos=float(u2.net.sum()), neto_aceptados=float(u2[u2.status != 'repudiated'].net.sum()),
        de_2023=u2[u2.loss_date.dt.year == 2023][['claim_id', 'policy_id', 'loss_date', 'primer_inicio', 'dias_antes', 'status']]
        .to_dict(orient='records'))
    ev['siniestros'] = out


def nuevo_negocio(E, D, tests, ev):
    out = {}
    for l in LINES:
        tr, te = E.pol[l], tests[l].copy()
        te['exp365'] = dias(te) / 365
        otros = pd.concat([E.pol[o].customer_id for o in LINES if o != l]).unique()
        nuevo_cli = ~te.customer_id.isin(tr.customer_id)
        nuevo_pol = ~te.policy_id.isin(tr.policy_id)
        mes = pd.to_datetime(te.period_start).dt.month
        a = pd.concat([tr.assign(y=tr.year), te.assign(y=2025)])
        a['mes'] = pd.to_datetime(a.period_start).dt.month
        nb = a[a.new_business]
        ene = nb.groupby('y').mes.apply(lambda s: float((s == 1).mean())).to_dict()
        s24 = tr[tr.year == 2024].groupby('new_business').exp365.sum()
        s25 = te.groupby('new_business').exp365.sum()
        a['grupo'] = np.where(a.new_business, 'NB', 'REN') + np.where(a.y == 2025, '_2025', '_2023_2024')
        canal = {g: s.channel.value_counts(normalize=True).to_dict() for g, s in a.groupby('grupo')}
        cs = te.merge(E.customers[['customer_id', 'customer_since_year']], on='customer_id', how='left')
        o = dict(canal_por_grupo=canal,
                 nb_2025_con_customer_since_2025=float((cs[cs.new_business].customer_since_year == 2025).mean()),
                 customer_since_year_max_train=int(tr.merge(E.customers[['customer_id', 'customer_since_year']],
                                                            on='customer_id', how='left').customer_since_year.max()),
                 test_cliente_nuevo_en_ramo=float(nuevo_cli.mean()), test_cliente_nuevo_n=int(nuevo_cli.sum()),
                 test_poliza_nueva=float(nuevo_pol.mean()),
                 cliente_nuevo_igual_new_business=bool((nuevo_cli == te.new_business).all()),
                 poliza_nueva_igual_new_business=bool((nuevo_pol == te.new_business).all()),
                 clientes_nuevos_con_otro_ramo_en_train=int((nuevo_cli & te.customer_id.isin(otros)).sum()),
                 cuota_nb_filas={int(y): float(g.new_business.mean()) for y, g in a.groupby('y')},
                 filas_por_anio={int(y): int(len(g)) for y, g in a.groupby('y')},
                 nb_inicio_en_enero=ene,
                 cuota_nb_exposicion_2024=float(s24[True] / s24.sum()), cuota_nb_exposicion_2025=float(s25[True] / s25.sum()))
        # relatividad bruta de nuevo negocio (2023-2024) en ambos mercados
        for mk, M in (('emerging', E), ('developed', D)):
            p = M.pol[l][M.pol[l].year.isin([2023, 2024])]
            g = p.groupby('new_business').agg(exp=('exp365', 'sum'), n=('n', 'sum'), t0=('t0', 'sum'))
            f = g.n / g.exp
            lc = g.t0 / g.exp
            o[f'rel_nb_{mk}'] = dict(frecuencia=float(f[True] / f[False]), coste=float(lc[True] / lc[False]),
                                     siniestros_nb=int(g.n[True]), exposicion_nb=float(g.exp[True]))
            o[f'rel_nb_{mk}_por_anio'] = {}
            for y in (2023, 2024):
                gy = p[p.year == y].groupby('new_business').agg(exp=('exp365', 'sum'), n=('n', 'sum'))
                fy = gy.n / gy.exp
                o[f'rel_nb_{mk}_por_anio'][y] = float(fy[True] / fy[False])
        sh24, sh25 = o['cuota_nb_exposicion_2024'], o['cuota_nb_exposicion_2025']
        mezcla = lambda r: ((1 - sh25) + sh25 * r) / ((1 - sh24) + sh24 * r)
        o['efecto_mezcla_2025_sobre_2024'] = {f'{r:.3f}': mezcla(r) for r in
                                              [0.8, 1.0, 1.2, o['rel_nb_emerging']['frecuencia'],
                                               o['rel_nb_developed']['frecuencia'], 1.5]}
        # desplazamiento de covariables: PSI 2024 frente a 2025 y NB de train frente a NB de 2025
        trc = tr.merge(E.customers, on='customer_id', how='left').merge(E.addresses, on='address_id', how='left')
        tec = te.merge(E.customers, on='customer_id', how='left').merge(E.addresses, on='address_id', how='left')
        skip = {'row_id', 'policy_id', 'customer_id', 'address_id', 'period_start', 'period_end', 'renewal_decision',
                'surname', 'year', 'new_business', 'dias', 'exp365', 'n', 't0', 'n_open', 'line'}
        ps = []
        for col in tec.columns:
            if col in skip or col not in trc.columns:
                continue
            ps.append(dict(variable=col, psi_2024_vs_2025=psi(trc[trc.year == 2024][col], tec[col]),
                           psi_nb_train_vs_nb_2025=psi(trc[trc.new_business][col], tec[tec.new_business][col])))
        ps = pd.DataFrame(ps).sort_values('psi_2024_vs_2025', ascending=False)
        o['psi'] = ps.to_dict(orient='records')
        tiempo = {'customer_since_year', 'renewal_count', 'exposure', 'customer_service_contacts'}
        o['psi_max_nb_sin_antiguedad_exposicion_ni_contactos'] = float(
            ps[~ps.variable.isin(tiempo)].psi_nb_train_vs_nb_2025.max())
        o['psi_variable_max_nb_sin_antiguedad_exposicion_ni_contactos'] = ps[~ps.variable.isin(tiempo)].sort_values(
            'psi_nb_train_vs_nb_2025').variable.iloc[-1]
        out[l] = o
    ev['nuevo_negocio'] = out


def historia(E, ev):
    out = {}
    for l in LINES:
        p = E.pol[l].merge(E.customers[['customer_id', 'customer_since_year']], on='customer_id', how='left')
        r23 = p[(p.year == 2023) & (~p.new_business)]
        out[l] = dict(renovaciones_2023=len(r23), cuota_renovaciones_2023=float(len(r23) / (p.year == 2023).sum()),
                      renewal_count_2023_min=int(r23.renewal_count.min()), renewal_count_2023_max=int(r23.renewal_count.max()),
                      renewal_count_igual_anio_menos_customer_since=float((p.renewal_count == p.year - p.customer_since_year).mean()))
    ev['historia'] = out


def capital(E, tests, ev):
    out = {}
    for l in ['buildings', 'contents']:
        o = {}
        for nm, t in (('train', E.pol[l]), ('test', tests[l])):
            ext = t.sum_insured > CAP_THRESHOLD[l]
            nor, ex = t[~ext], t[ext]
            srt = np.sort(t.sum_insured.unique())
            gaps = srt[1:] / srt[:-1]
            i = int(gaps.argmax())
            ppm_n = nor.written_premium / (nor.sum_insured / 1000)
            ppm_e = ex.written_premium / (ex.sum_insured / 1000)
            ppm_e1000 = ex.written_premium / (ex.sum_insured / 1e6)
            o[nm] = dict(extremas=int(ext.sum()), hueco_desde=float(srt[i]), hueco_hasta=float(srt[i + 1]),
                         hueco_razon=float(gaps[i]),
                         mediana_capital_normal=float(nor.sum_insured.median()),
                         mediana_extremas_entre_mil=float((ex.sum_insured / 1000).median()),
                         prima_por_mil_normal_mediana=float(ppm_n.median()), prima_por_mil_normal_min=float(ppm_n.min()),
                         prima_por_mil_extremas_mediana=float(ppm_e.median()), prima_por_mil_extremas_max=float(ppm_e.max()),
                         prima_por_mil_extremas_entre_mil_mediana=float(ppm_e1000.median()),
                         max_extremas_entre_mil=float((ex.sum_insured / 1000).max()), max_normal=float(nor.sum_insured.max()),
                         extremas_multiplo_de_mil=float((ex.sum_insured % 1000 == 0).mean()))
        out[l] = o
    out['total_extremas'] = sum(out[l][k]['extremas'] for l in ['buildings', 'contents'] for k in ('train', 'test'))
    out['total_extremas_test'] = sum(out[l]['test']['extremas'] for l in ['buildings', 'contents'])
    ev['capital'] = out


def peculiaridades(E, tests, ev):
    out = {'contactos': {}, 'declinadas_con_sucesor': {}, 'danos_accidentales_sin_cobertura': {}}
    for l in LINES:
        p = E.pol[l].copy()
        p['csc'] = p.customer_service_contacts.clip(upper=3)
        g = p.groupby('csc').agg(exp=('exp365', 'sum'), n=('n', 'sum'), filas=('row_id', 'size'))
        te = tests[l]
        out['contactos'][l] = dict(frecuencia={int(k): float(v) for k, v in (g.n / g.exp).items()},
                                   cuota_train={int(k): float(v) for k, v in (g.filas / g.filas.sum()).items()},
                                   cuota_test={int(k): float(v) for k, v in
                                               te.customer_service_contacts.clip(upper=3).value_counts(normalize=True).sort_index().items()})
        a = pd.concat([E.pol[l][['policy_id', 'period_start', 'renewal_decision']],
                       te[['policy_id', 'period_start']].assign(period_start=lambda x: pd.to_datetime(x.period_start))])
        a = a.sort_values(['policy_id', 'period_start'])
        a['sucesor'] = a.groupby('policy_id').period_start.shift(-1).notna()
        out['declinadas_con_sucesor'][l] = {dec: dict(filas=int((a.renewal_decision == dec).sum()),
                                                      con_sucesor=float(a[a.renewal_decision == dec].sucesor.mean()))
                                            for dec in ['declined_by_insurer', 'lapsed_by_customer', 'cancelled']}
        if l != 'motor':
            h = E.acc[(E.acc.line == l)].merge(E.pol[l][['row_id', 'accidental_damage_cover', 'sum_insured']], on='row_id')
            ad = h[h.peril == 'accidental_damage']
            out['danos_accidentales_sin_cobertura'][l] = dict(aceptados=len(ad), sin_cobertura=int((~ad.accidental_damage_cover).sum()),
                                                              netos_sobre_capital=int((h.net > h.sum_insured).sum()))
    m = E.pol['motor']
    out['ncb_mayor_que_anios_carnet'] = dict(train=int((m.ncb_years > m.years_licensed).sum()),
                                            test=int((tests['motor'].ncb_years > tests['motor'].years_licensed).sum()))
    mm = E.acc[E.acc.line == 'motor'].merge(m[['row_id', 'cover_type']], on='row_id')
    out['danos_propios_o_lunas_fuera_de_todo_riesgo'] = int(
        (mm.peril.isin(['own_damage', 'glass_hail']) & (mm.cover_type != 'comprehensive')).sum())
    occ = E.customers.occupation.dropna()
    norm = occ.str.strip().str.lower().str.replace(r'\s+', ' ', regex=True)
    base = norm.str.replace('self-employed ', '', regex=False)
    dev_occ = set(read(ARGS.developed, 'customers').occupation.dropna().str.lower().unique())
    out['ocupacion'] = dict(distintos_crudos=int(occ.nunique()), nulos=int(E.customers.occupation.isna().sum()),
                            distintos_tras_espacios_y_mayusculas=int(norm.nunique()),
                            distintos_base_sin_self_employed=int(base.nunique()),
                            base_igual_vocabulario_desarrollado=set(base.unique()) == dev_occ,
                            cuota_self_employed=float(norm.str.startswith('self-employed').mean()),
                            self_employed_incoherentes={k: int((norm == f'self-employed {k}').sum())
                                                        for k in ['retired', 'student', 'unemployed']})
    ev['peculiaridades'] = out


CURVAS = [('motor', 'glass_hail', 'hail_days', [0, 4, 8, 12, 16, 20, 25, 30, 40, 200]),
          ('buildings', 'storm', 'wind_exposure_index', [0, 2, 3, 4, 5, 6, 7, 8, 11]),
          ('buildings', 'escape_of_water', 'freezing_days', [0, 10, 20, 30, 40, 50, 60, 400])]


def curvas_clima(E, D, tablas):
    """Frecuencia por peligro y tramo de la variable de clima del mismo ano, ocurrencias de 2023 (descriptivo)."""
    out = []
    for mk, M in (('emerging', E), ('developed', D)):
        for line, peril, var, bins in CURVAS:
            p = M.pol[line][M.pol[line].year == 2023].merge(M.weather[M.weather.year == 2023][['address_id', var]],
                                                             on='address_id', how='left')
            k = M.acc[(M.acc.line == line) & (M.acc.peril == peril)].groupby('row_id').size()
            p['k'] = p.row_id.map(k).fillna(0)
            p['tramo'] = pd.cut(p[var], bins, right=False)
            g = p.groupby('tramo', observed=True).agg(exposicion=('exp365', 'sum'), siniestros=('k', 'sum'))
            for b, r in g.iterrows():
                out.append(dict(mercado=mk, ramo=line, peligro=peril, variable=var, tramo=str(b), exposicion=r.exposicion,
                                siniestros=r.siniestros, frecuencia=r.siniestros / r.exposicion))
    d = pd.DataFrame(out)
    tablas['curvas_clima_2023'] = d
    return d


def clima(E, D, tests, ev, tablas):
    w, wd = E.weather, D.weather
    cv = curvas_clima(E, D, tablas)
    g = cv[(cv.peligro == 'glass_hail')].pivot_table(index='tramo', columns='mercado', values=['frecuencia', 'siniestros'],
                                                       sort=False)
    g = g[(g[('siniestros', 'emerging')] >= 50) & (g[('siniestros', 'developed')] >= 50)]
    lunas_solape = [dict(tramo=t, frecuencia_emergente=float(r[('frecuencia', 'emerging')]),
                         frecuencia_desarrollada=float(r[('frecuencia', 'developed')]),
                         razon=float(r[('frecuencia', 'emerging')] / r[('frecuencia', 'developed')]))
                    for t, r in g.iterrows()]
    out = dict(anios_emergente=w.year.value_counts().sort_index().to_dict(),
               duplicados_direccion_anio=int(w.duplicated(['address_id', 'year']).sum()),
               medias_emergente={int(y): g[WEATHER_VARS].mean().to_dict() for y, g in w.groupby('year')},
               medias_2023_2024={'emerging': w[w.year.isin([2023, 2024])][WEATHER_VARS].mean().to_dict(),
                                 'developed': wd[wd.year.isin([2023, 2024])][WEATHER_VARS].mean().to_dict()})
    corr = {}
    for v in WEATHER_VARS:
        pv = w.pivot(index='address_id', columns='year', values=v)
        corr[v] = {'2023_2024': float(pv[2023].corr(pv[2024])), '2024_2025': float(pv[2024].corr(pv[2025]))}
    out['correlacion_entre_anios'] = corr
    # soporte: exposicion emergente fuera del rango desarrollado (2023)
    sop = {}
    for line, var, cut in [('motor', 'hail_days', 30), ('buildings', 'wildfire_index', 0.6)]:
        r = {}
        for mk, M in (('emerging', E), ('developed', D)):
            p = M.pol[line][M.pol[line].year == 2023].merge(M.weather[M.weather.year == 2023][['address_id', var]],
                                                             on='address_id', how='left')
            r[mk] = float(p[p[var] >= cut].exp365.sum())
        sop[f'{line}_{var}_desde_{cut}'] = r
    out['exposicion_2023_fuera_de_soporte'] = sop
    # sensibilidad descriptiva al clima de 2025: estandarizacion directa por tramos
    sens = []
    for line, peril, var in CLIMA_PARES:
        p = E.pol[line][E.pol[line].year.isin([2023, 2024])].merge(w[['address_id', 'year', var]],
                                                                   on=['address_id', 'year'], how='left')
        k = E.acc[(E.acc.line == line) & (E.acc.peril == peril)].groupby('row_id').size()
        p['k'] = p.row_id.map(k).fillna(0)
        edges = np.unique(np.quantile(w[var], np.linspace(0, 1, 9)))
        edges[0], edges[-1] = -np.inf, np.inf
        p['bin'] = pd.cut(p[var], edges)
        g = p.groupby('bin', observed=False).agg(exp=('exp365', 'sum'), k=('k', 'sum'))
        g['freq'] = (g.k / g.exp).fillna(0)
        t = tests[line].copy()
        t['exp365'] = dias(t) / 365
        res = {}
        for y in (2024, 2025):
            tt = t.merge(w[w.year == y][['address_id', var]], on='address_id', how='left')
            res[y] = float((pd.cut(tt[var], edges).map(g.freq).astype(float) * tt.exp365).sum())
        acc_l = E.acc[E.acc.line == line]
        share = float(acc_l[acc_l.peril == peril].net.sum() / acc_l.net.sum())
        sens.append(dict(ramo=line, peligro=peril, variable=var, siniestros_2023_2024=int(g.k.sum()),
                         media_2024=float(w[w.year == 2024][var].mean()), media_2025=float(w[w.year == 2025][var].mean()),
                         esperados_con_clima_2024=res[2024], esperados_con_clima_2025=res[2025],
                         razon=res[2025] / res[2024], cuota_coste_del_peligro=share,
                         efecto_aprox_en_coste_del_ramo=(res[2025] / res[2024] - 1) * share))
    out['sensibilidad_2025'] = sens
    out['lunas_por_granizo_tramos_con_50_siniestros_en_ambos'] = lunas_solape
    ev['clima'] = out


def mercados(E, D, ev, tablas):
    agg = []
    for mk, M in (('emerging', E), ('developed', D)):
        for l in LINES:
            for y, s in M.pol[l].groupby('year'):
                agg.append(dict(mercado=mk, ramo=l, anio=int(y), filas=len(s), exposicion=s.exp365.sum(),
                                siniestros=s.n.sum(), t0=s.t0.sum(), frecuencia=s.n.sum() / s.exp365.sum(),
                                severidad=s.t0.sum() / max(s.n.sum(), 1), coste_por_anio=s.t0.sum() / s.exp365.sum(),
                                cuota_abiertos=s.n_open.sum() / max(s.n.sum(), 1),
                                siniestralidad_prima_escrita=s.t0.sum() / (s.written_premium * s.exp365).sum()))
    agg = pd.DataFrame(agg)
    tablas['mercados_ramo_anio'] = agg
    per = []
    for mk, M in (('emerging', E), ('developed', D)):
        exp = {(l, y): M.pol[l][M.pol[l].year == y].exp365.sum() for l in LINES for y in (2023, 2024)}
        a = M.acc[M.acc.ay.isin([2023, 2024])]
        for (l, pe, y), g in a.groupby(['line', 'peril', 'ay']):
            per.append(dict(mercado=mk, ramo=l, peligro=pe, anio=int(y), siniestros=len(g), frecuencia=len(g) / exp[(l, y)],
                            severidad=g.net.mean(), cv=g.net.std() / g.net.mean(), maximo=g.net.max(),
                            cuota_abiertos=(g.status == 'open').mean(), retraso_mediana=g.delay.median(),
                            retraso_p90=g.delay.quantile(.9)))
    per = pd.DataFrame(per)
    tablas['peligros_mercados'] = per
    pv = per.pivot_table(index=['ramo', 'peligro', 'anio'], columns='mercado', values=['frecuencia', 'severidad', 'siniestros'])
    ratios = pd.DataFrame({'razon_frecuencia': pv[('frecuencia', 'emerging')] / pv[('frecuencia', 'developed')],
                           'razon_severidad': pv[('severidad', 'emerging')] / pv[('severidad', 'developed')],
                           'siniestros_emergente': pv[('siniestros', 'emerging')],
                           'siniestros_desarrollado': pv[('siniestros', 'developed')]}).reset_index()
    tablas['razones_peligro'] = ratios
    r23 = ratios[ratios.anio == 2023]
    ks = []
    for (l, pe), g in E.acc[E.acc.ay == 2023].groupby(['line', 'peril']):
        d = D.acc[(D.acc.ay == 2023) & (D.acc.line == l) & (D.acc.peril == pe)]
        r = stats.ks_2samp(g.delay, d.delay)
        ks.append(dict(ramo=l, peligro=pe, n_emergente=len(g), n_desarrollado=len(d), mediana_emergente=g.delay.median(),
                       mediana_desarrollado=d.delay.median(), p90_emergente=g.delay.quantile(.9),
                       p90_desarrollado=d.delay.quantile(.9), ks=r.statistic, p_valor=r.pvalue))
    ks = pd.DataFrame(ks)
    tablas['retrasos_ks_2023'] = ks
    # Cola de reporte que el emergente no puede observar (ventana de dos años): el desarrollado la ve en
    # las ocurrencias de 2021, observadas entre tres y cuatro años al 31-12-2024.
    cola = {}
    for line, per in [('motor', 'bodily_injury'), ('buildings', 'subsidence')]:
        for mk, M, ay in (('developed', D, 2021), ('developed', D, 2022), ('emerging', E, 2023)):
            g = M.acc[(M.acc.ay == ay) & (M.acc.line == line) & (M.acc.peril == per)]
            r = dict(siniestros=len(g), retraso_max=int(g.delay.max()))
            for dd in (365, 730, 1095):
                r[f'cuota_conteo_mas_de_{dd}'] = float((g.delay > dd).mean())
                r[f'cuota_coste_mas_de_{dd}'] = float(g[g.delay > dd].net.sum() / g.net.sum())
            cola[f'{line}/{per}/{mk}/{ay}'] = r
    ev['mercados'] = dict(
        cola_reporte=cola,
        ramo_anio=agg[agg.anio.isin([2023, 2024])].to_dict(orient='records'),
        razon_frecuencia_2023=dict(zip(r23.ramo + '/' + r23.peligro, r23.razon_frecuencia)),
        razon_severidad_2023=dict(zip(r23.ramo + '/' + r23.peligro, r23.razon_severidad)),
        siniestros_emergentes_2023=dict(zip(r23.ramo + '/' + r23.peligro, r23.siniestros_emergente)),
        retrasos=dict(p_valor_min=float(ks.p_valor.min()), ks_max=float(ks.ks.max()), peligros=len(ks),
                      por_peligro=ks.to_dict(orient='records')),
        concentracion_top10={mk: {l: float(M.acc[(M.acc.line == l) & M.acc.ay.isin([2023, 2024])].net.nlargest(10).sum() /
                                          M.acc[(M.acc.line == l) & M.acc.ay.isin([2023, 2024])].net.sum()) for l in LINES}
                             for mk, M in (('emerging', E), ('developed', D))})


def relatividades(E, D, ev, tablas):
    out = []
    for mk, M in (('emerging', E), ('developed', D)):
        for l, facs in FACTORES.items():
            p = M.pol[l][M.pol[l].year.isin([2023, 2024])].merge(M.addresses, on='address_id', how='left')
            cust = M.customers.copy()
            if mk == 'developed' and l == 'motor':
                p['customer_id'] = p.customer_id.str.zfill(8)  # ID01 de semana 1
            p = p.merge(cust, on='customer_id', how='left', suffixes=('', '_c'))
            if mk == 'developed':
                col = 'driver_age' if l == 'motor' else 'policyholder_age'
                band = 'driver_age_band' if l == 'motor' else 'policyholder_age_band'
                p[band] = pd.cut(p[col], AGE_BINS, labels=AGE_LABELS).astype(str)
            if l == 'motor':
                p['ncb_g'] = pd.cut(p.ncb_years, [-1, 0, 2, 5, 9, 99], labels=['0', '1-2', '3-5', '6-9', '10+']).astype(str)
            base = p.n.sum() / p.exp365.sum()
            for f in facs:
                g = p.groupby(p[f].astype(str)).agg(exp=('exp365', 'sum'), n=('n', 'sum'))
                for lev, r in g.iterrows():
                    out.append(dict(mercado=mk, ramo=l, factor=f, nivel=lev, exposicion=r.exp, siniestros=r.n,
                                    relatividad=(r.n / r.exp) / base))
    d = pd.DataFrame(out)
    tablas['relatividades_oneway'] = d
    pv = d.pivot_table(index=['ramo', 'factor', 'nivel'], columns='mercado', values=['relatividad', 'siniestros']).dropna()
    pv.columns = [f'{a}_{b}' for a, b in pv.columns]
    pv = pv.reset_index()
    pv['dif_log'] = np.log(pv.relatividad_emerging / pv.relatividad_developed)
    fiables = pv[pv.siniestros_emerging >= 100]
    sin_ncb = fiables[fiables.factor != 'ncb_g']
    rel_dif = (np.exp(sin_ncb.dif_log) - 1).abs()
    ev['relatividades'] = dict(
        niveles_comparados=len(pv), niveles_con_100_siniestros_emergentes=len(fiables),
        niveles_con_100_siniestros_sin_ncb=len(sin_ncb),
        mediana_abs_dif_log_sin_ncb=float(sin_ncb.dif_log.abs().median()),
        p90_abs_dif_log_sin_ncb=float(sin_ncb.dif_log.abs().quantile(.9)),
        mediana_abs_dif_relativa_sin_ncb=float(rel_dif.median()),
        p90_abs_dif_relativa_sin_ncb=float(rel_dif.quantile(.9)),
        ncb=pv[pv.factor == 'ncb_g'][['nivel', 'relatividad_emerging', 'relatividad_developed']].to_dict(orient='records'),
        mayores_diferencias=fiables.reindex(fiables.dif_log.abs().sort_values(ascending=False).index)
        .head(6)[['ramo', 'factor', 'nivel', 'relatividad_emerging', 'relatividad_developed', 'siniestros_emerging']]
        .to_dict(orient='records'))


def prima_comercial(E, tests, ev):
    x = read(ARGS.emerging, 'expenses').set_index('item')
    r = read(ARGS.emerging, 'reference_policies')
    allt = pd.concat([tests[l].assign(line=l) for l in LINES])
    sib = []
    for _, row in r.iterrows():
        s = allt[allt.policy_id == row.policy_id].sort_values('period_start')
        if len(s) > 1:
            sib.append(dict(referencia=row.row_id, poliza=row.policy_id,
                            filas=s[['row_id', 'period_start', 'period_end', 'exposure']].to_dict(orient='records')))
    e = x['emerging']
    den = {ch: float(1 - e['variable_expense'] - e[f'commission_{ch}'] - e['premium_tax'] - e['target_profit_margin'])
           for ch in ['direct', 'broker']}
    flat = {}
    for l in LINES:
        p = E.pol[l].copy()
        p['tramo'] = pd.cut(p.exp365, [0, .25, .5, .75, .99, 1.01])
        flat[l] = {str(k): float(v) for k, v in p.groupby('tramo', observed=True).written_premium.median().items()}
    lc = {}
    for l in LINES:
        p = E.pol[l][E.pol[l].year.isin([2023, 2024])]
        cost = p.t0.sum() / p.exp365.sum()
        rr = e['cat_reinsurance'] if l != 'motor' else 0.0
        lc[l] = dict(coste_medio_por_anio=float(cost), prima_escrita_media=float(p.written_premium.mean()),
                     prima_comercial_anual_directa=float((cost * (1 + rr) + e['fixed_expense_per_policy']) / den['direct']),
                     prima_comercial_anual_broker=float((cost * (1 + rr) + e['fixed_expense_per_policy']) / den['broker']))
        lc[l]['razon_broker_sobre_prima_escrita'] = lc[l]['prima_comercial_anual_broker'] / lc[l]['prima_escrita_media']
        lc[l]['razon_directa_sobre_prima_escrita'] = lc[l]['prima_comercial_anual_directa'] / lc[l]['prima_escrita_media']
    ev['prima_comercial'] = dict(
        gastos=x.reset_index().to_dict(orient='records'), denominadores=den,
        referencias=dict(filas=len(r), por_ramo=r.line.value_counts().to_dict(), canal=r.channel.value_counts().to_dict(),
                         en_test=int(r.row_id.isin(allt.row_id).sum()), parciales_menos_0_99=int((r.exposure < 0.99).sum()),
                         parciales_menos_de_1=int((r.exposure < 1).sum()),
                         exposicion_min=float(r.exposure.min()),
                         inicio_despues_1_enero=int((pd.to_datetime(r.period_start) > '2025-01-01').sum()),
                         fin_antes_31_dic=int((pd.to_datetime(r.period_end) < '2025-12-31').sum()),
                         nuevo_negocio=int(r.new_business.sum()), polizas_con_otra_fila_2025=sib),
        prima_escrita_mediana_por_tramo_exposicion=flat,
        orden_de_magnitud_con_coste_observado=lc,
        canal_comparison_site_cuota_filas={l: float((tests[l].channel == 'comparison_site').mean()) for l in LINES})


def main():
    t_start = time.time()
    ev = {'autor': 'Claude', 'inicio_utc': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
          'alcance': 'Revision descriptiva; sin entrenamiento, sin cambios de datos, sin salidas por fila.',
          'entorno': dict(python=sys.version.split()[0], plataforma=platform.platform(), pandas=pd.__version__,
                          numpy=np.__version__, pyarrow=pyarrow.__version__, scipy=__import__('scipy').__version__)}
    integridad(ARGS, ev)
    if not ev['integridad']['todas_coinciden']:
        raise SystemExit('Las huellas no coinciden con los manifiestos: se detiene sin calcular.')
    E = Mercado('emerging', ARGS.emerging)
    D = Mercado('developed', ARGS.developed)
    tablas = {}
    tests = escala(E, D, ARGS, ev)
    exposicion(E, tests, ev)
    siniestros(E, ev)
    nuevo_negocio(E, D, tests, ev)
    historia(E, ev)
    capital(E, tests, ev)
    peculiaridades(E, tests, ev)
    clima(E, D, tests, ev, tablas)
    mercados(E, D, ev, tablas)
    relatividades(E, D, ev, tablas)
    prima_comercial(E, tests, ev)
    ev['fin_utc'] = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    ev['segundos'] = round(time.time() - t_start, 1)
    out = ARGS.out
    (out / 'tablas').mkdir(parents=True, exist_ok=True)
    for k, t in tablas.items():
        t.to_csv(out / 'tablas' / f'{k}.csv', index=False, float_format='%.6g')
    (out / 'evidencia.json').write_text(json.dumps(to_py(ev), ensure_ascii=False, indent=1), encoding='utf-8')
    if not ARGS.sin_figuras:
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        import figuras  # mismo directorio; solo lee evidencia.json y tablas/
        figuras.fig1(out); figuras.fig2(out); figuras.fig3(out)
    here = pathlib.Path(__file__).resolve().parent
    man = {'autor': 'Claude', 'utc': ev['fin_utc'], 'script_sha256': sha256(pathlib.Path(__file__)),
           'scripts': {p.name: sha256(p) for p in sorted(here.glob('*.py'))},
           'entradas': {**{f'emerging/{k}': v['sha256'] for k, v in ev['integridad']['emerging'].items()},
                        **{f'developed/{k}': v['sha256'] for k, v in ev['integridad']['developed'].items()}},
           'salidas': {str(p.relative_to(out)).replace('\\', '/'): sha256(p)
                       for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'manifiesto.json'
                       and '__pycache__' not in p.parts and not p.name.startswith('verificacion_')}}
    (out / 'manifiesto.json').write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps({'segundos': ev['segundos'], 'salidas': len(man['salidas'])}))


if __name__ == '__main__':
    here = pathlib.Path(__file__).resolve()
    root = here.parents[4] if len(here.parents) > 4 else here.parent
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--emerging', type=pathlib.Path, default=root / 'Hackaton/Semana 2/Datos/emerging')
    ap.add_argument('--developed', type=pathlib.Path, default=root / 'Hackaton/Semana 1/Datos')
    ap.add_argument('--manifest-em', type=pathlib.Path, default=root / 'Hackaton/Semana 2/Codex/fuentes/download_manifest.json')
    ap.add_argument('--manifest-dev', type=pathlib.Path,
                    default=root / 'Preparación/artifacts/verification/iaa_launch_20261016/data_manifest.json')
    ap.add_argument('--out', type=pathlib.Path, required=True)
    ap.add_argument('--sin-figuras', action='store_true', help='no regenera los PNG (requiere matplotlib)')
    ARGS = ap.parse_args()
    main()
