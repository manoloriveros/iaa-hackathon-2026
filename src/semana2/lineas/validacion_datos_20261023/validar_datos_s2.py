"""Validación exhaustiva de los datos de la semana 2 (mercado emergente) con código propio (Claude, 23-10-2026).

Recorre un catálogo de controles VE01–VE75 sobre los trece Parquet emergentes, sus relaciones con el mercado
desarrollado, las capas derivadas de Codex (base, T0, particiones, F0 y OOF de 2023) y las tablas de las decisiones
del participante. No cambia datos ni archivos de Codex. Escribe agregados en --out (evidencia, tabla de controles,
figuras, manifiesto) y los casos por fila en --privado.

Uso desde C:/dev/Hakaton (pandas, pyarrow, scipy, matplotlib):
    python "Hackaton/Semana 2/Claude/validacion_datos_20261023/validar_datos_s2.py"
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import platform
import re
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
from scipy import stats

LINES = ['motor', 'buildings', 'contents']
HOGAR = ['buildings', 'contents']
VAL = pd.Timestamp('2024-12-31')
EM_FILES = ['addresses', 'claims', 'customers', 'expenses', 'policies_buildings', 'policies_contents', 'policies_motor',
            'reference_policies', 'sample_submission', 'test_buildings', 'test_contents', 'test_motor', 'weather']
DEV_FILES = ['addresses', 'claims', 'customers', 'policies_buildings', 'policies_contents', 'policies_motor', 'weather',
             'test_buildings', 'test_contents', 'test_motor', 'sample_submission']
PERILS = {'motor': ['own_damage', 'third_party_prop', 'bodily_injury', 'theft', 'glass_hail'],
          'buildings': ['storm', 'flood', 'escape_of_water', 'subsidence', 'fire', 'accidental_damage'],
          'contents': ['theft', 'escape_of_water', 'accidental_damage', 'flood']}
DOMINIOS = {  # del diccionario de la página de datos
    'customers': {'gender': ['M', 'F'], 'marital_status': ['single', 'married', 'divorced', 'widowed'],
                  'document_preference': ['email', 'post', 'app']},
    'addresses': {'region': [f'E0{i}' for i in range(1, 7)], 'urban_density': ['rural', 'suburban', 'urban', 'dense_urban'],
                  'soil_type': ['clay', 'sand', 'loam', 'chalk', 'rock'],
                  'property_type': ['detached', 'semi_detached', 'terraced', 'flat'], 'roof_type': ['pitched', 'flat'],
                  'energy_rating': list('ABCDEFG')},
    'policies': {'voluntary_excess': [0, 250, 500, 1000], 'channel': ['direct', 'comparison_site', 'broker'],
                 'payment_method': ['annual', 'monthly'],
                 'renewal_decision': ['renewed', 'lapsed_by_customer', 'cancelled', 'declined_by_insurer', 'mid_term_change']},
    'motor': {'driver_age_band': ['17-24', '25-34', '35-49', '50-64', '65+'],
              'body_type': ['hatchback', 'saloon', 'estate', 'suv', 'coupe'], 'transmission': ['manual', 'automatic'],
              'fuel_type': ['petrol', 'diesel', 'hybrid', 'electric'],
              'cover_type': ['comprehensive', 'third_party_fire_theft', 'third_party_only'],
              'overnight_parking': ['garage', 'driveway', 'street'], 'vehicle_use': ['social', 'commuting', 'business']},
    'buildings': {'policyholder_age_band': ['17-24', '25-34', '35-49', '50-64', '65+'],
                  'construction_type': ['BRK', 'STN', 'WOD', 'MIX'], 'occupancy': ['owner_occupied', 'let']},
    'contents': {'policyholder_age_band': ['17-24', '25-34', '35-49', '50-64', '65+'], 'tenure': ['owner', 'renter'],
                 'security_level': ['standard', 'locks', 'alarm_and_locks']},
    'claims': {'status': ['closed', 'open', 'repudiated'], 'line': LINES}}
RANGOS = {'weather': {'hail_days': (0, 366), 'wind_exposure_index': (0, 10), 'freezing_days': (0, 366),
                      'dry_summer_index': (0, 1), 'wildfire_index': (0, 1), 'rainfall_mm': (0, None), 'mean_temperature_c': (-30, 50)},
          'addresses': {'flood_zone': (1, 5), 'distance_to_river_km': (0, None), 'elevation_m': (0, None), 'year_built': (1500, 2025),
                        'trees_within_5m': (0, None), 'bedrooms': (1, None)},
          'motor': {'years_licensed': (0, 90), 'ncb_years': (0, None), 'vehicle_value_group': (1, 20), 'vehicle_age': (0, None),
                    'engine_size_cc': (1, None), 'seats': (1, None)},
          'buildings': {'sum_insured': (1, None), 'days_unoccupied': (0, 365)}, 'contents': {'sum_insured': (1, None), 'high_value_items': (0, None)},
          'policies': {'compulsory_excess': (0, None), 'missed_payments_12m': (0, 12), 'renewal_count': (0, None),
                       'days_quote_to_inception': (0, None), 'discount_applied': (0, 1), 'written_premium': (0.01, None),
                       'customer_service_contacts': (0, None), 'exposure': (0.0001, None)},
          'customers': {'household_size': (1, None), 'prior_claims_5y': (0, None), 'licence_points': (0, None), 'years_at_address': (0, None),
                        'customer_since_year': (1900, 2025)}}
CASOS_MAX = 20000


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
    if isinstance(o, (list, tuple, set)):
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
    if isinstance(o, pd.Series):
        return to_py(o.to_dict())
    return o


def txt(s: pd.Series) -> pd.Series:
    return s.astype(object).where(s.notna(), None).map(lambda x: None if x is None else str(x))


def psi(a: pd.Series, b: pd.Series, bins: int = 10) -> float:
    a, b = a.dropna(), b.dropna()
    if len(a) == 0 or len(b) == 0:
        return float('nan')
    if a.dtype.kind in 'fi' and a.nunique() > 12:
        qs = np.unique(np.nanquantile(a, np.linspace(0, 1, bins + 1)))
        if len(qs) < 3:
            return 0.0
        qs[0], qs[-1] = -np.inf, np.inf
        ca, cb = pd.cut(a, qs).astype(str), pd.cut(b, qs).astype(str)
    else:
        ca, cb = txt(a), txt(b)
    pa, pb = ca.value_counts(normalize=True), cb.value_counts(normalize=True)
    idx = pa.index.union(pb.index)
    pa = pa.reindex(idx).fillna(0) + 1e-4
    pb = pb.reindex(idx).fillna(0) + 1e-4
    return float(((pb - pa) * np.log(pb / pa)).sum())


class Registro:
    """Acumula los controles, sus cifras y los casos por fila."""

    def __init__(self, privado: pathlib.Path):
        self.controles, self.ev, self.privado = [], {}, privado
        privado.mkdir(parents=True, exist_ok=True)

    def add(self, id_, area, titulo, resultado, observado, esperado='', severidad='', detalle=None, vd='', casos=None):
        assert resultado in ('pasa', 'hallazgo', 'limite', 'informativo')
        if resultado in ('pasa', 'informativo'):
            severidad = ''
        c = dict(id=id_, area=area, titulo=titulo, resultado=resultado, severidad=severidad, observado=str(observado)[:600],
                 esperado=str(esperado)[:300], vd_semana1=vd, casos='', n_casos=0)
        if casos is not None and len(casos):
            ruta = self.privado / f'casos_{id_}.parquet'
            tabla = casos.head(CASOS_MAX).reset_index(drop=True)
            for col in tabla.columns:
                if tabla[col].dtype == object:
                    tabla[col] = txt(tabla[col])
            pq.write_table(pyarrow.Table.from_pandas(tabla, preserve_index=False), ruta)
            c['casos'], c['n_casos'] = ruta.name, int(len(casos))
        self.controles.append(c)
        if detalle is not None:
            self.ev[id_] = to_py(detalle)
        return c


# ----------------------------------------------------------------------------------------------- datos
def read(folder: pathlib.Path, name: str, cols=None) -> pd.DataFrame:
    return pq.read_table(folder / f'{name}.parquet', columns=cols).to_pandas()


def dias(p):
    return (pd.to_datetime(p.period_end) - pd.to_datetime(p.period_start)).dt.days + 1


class Emergente:
    def __init__(self, folder: pathlib.Path):
        self.folder = folder
        self.raw = {n: read(folder, n) for n in EM_FILES}
        self.pol, self.test = {}, {}
        for l in LINES:
            for kind, name in [('pol', f'policies_{l}'), ('test', f'test_{l}')]:
                q = self.raw[name].copy()
                q['period_start'] = pd.to_datetime(q.period_start)
                q['period_end'] = pd.to_datetime(q.period_end)
                q['dias'] = dias(q)
                q['e365'] = q.dias / 365
                q['year'] = q.period_start.dt.year
                q['line'] = l
                (self.pol if kind == 'pol' else self.test)[l] = q
        c = self.raw['claims'].copy()
        c['loss_date'] = pd.to_datetime(c.loss_date)
        c['report_date'] = pd.to_datetime(c.report_date)
        c['net'] = c.incurred_to_date - c.recoveries
        c['delay'] = (c.report_date - c.loss_date).dt.days
        self.claims = c
        self.customers, self.addresses, self.weather = self.raw['customers'], self.raw['addresses'], self.raw['weather']
        self.todas = pd.concat([pd.concat([self.pol[l].assign(is_test=False), self.test[l].assign(is_test=True)]) for l in LINES],
                               ignore_index=True, sort=False)
        # asignación de siniestros por póliza y fecha de ocurrencia
        asig = []
        for l in LINES:
            p = self.pol[l]
            cl = c[c.line == l]
            m = cl.merge(p[['row_id', 'policy_id', 'period_start', 'period_end', 'year']], on='policy_id', how='left')
            m['dentro'] = (m.loss_date >= m.period_start) & (m.loss_date <= m.period_end)
            k = m.groupby('claim_id').dentro.sum()
            a = m[m.dentro].drop(columns='dentro')
            asig.append(a)
            cl2 = cl.copy()
            cl2['n_periodos'] = cl2.claim_id.map(k).fillna(0).astype(int)
            cl2['tiene_poliza'] = cl2.policy_id.isin(p.policy_id)
            first = p.groupby('policy_id').period_start.min()
            last = p.groupby('policy_id').period_end.max()
            cl2['primer_inicio'] = cl2.policy_id.map(first)
            cl2['ultimo_fin'] = cl2.policy_id.map(last)
            self.claims.loc[cl2.index, ['n_periodos', 'tiene_poliza', 'primer_inicio', 'ultimo_fin']] = cl2[['n_periodos', 'tiene_poliza', 'primer_inicio', 'ultimo_fin']]
        self.asig = pd.concat(asig, ignore_index=True)
        self.acc = self.asig[self.asig.status != 'repudiated'].copy()


class Desarrollado:
    """Solo lo necesario para comparar: esquemas, dominios, IDs solapados y distribuciones de maestros y clima."""

    def __init__(self, folder: pathlib.Path):
        self.folder = folder
        self.schemas = {n: pq.read_schema(folder / f'{n}.parquet') for n in DEV_FILES}
        self.customers = read(folder, 'customers')
        self.addresses = read(folder, 'addresses')
        self.weather = read(folder, 'weather', ['address_id', 'year', 'hail_days', 'wind_exposure_index', 'freezing_days',
                                                'dry_summer_index', 'wildfire_index', 'rainfall_mm', 'mean_temperature_c'])
        cols = {'motor': ['row_id', 'policy_id', 'customer_id', 'address_id', 'period_start', 'period_end', 'exposure', 'driver_age',
                          'years_licensed', 'ncb_years', 'vehicle_value_group', 'vehicle_age', 'make_model', 'engine_size_cc', 'body_type',
                          'transmission', 'seats', 'vehicle_colour', 'fuel_type', 'driver_assist', 'cover_type', 'overnight_parking',
                          'vehicle_use', 'named_young_driver', 'voluntary_excess', 'compulsory_excess', 'channel', 'payment_method',
                          'missed_payments_12m', 'new_business', 'renewal_count', 'days_quote_to_inception', 'discount_applied',
                          'written_premium', 'customer_service_contacts', 'renewal_decision'],
                'buildings': None, 'contents': None}
        self.pol = {l: read(folder, f'policies_{l}', cols[l]) for l in LINES}
        for l in LINES:
            p = self.pol[l]
            p['period_start'] = pd.to_datetime(p.period_start)
            p['year'] = p.period_start.dt.year


# ----------------------------------------------------------------------------------------------- A. integridad
def a_integridad(E: Emergente, D: Desarrollado, args, R: Registro):
    man = {f['name'].split('/')[-1]: f for f in json.load(open(args.manifest_em, encoding='utf-8'))['files']}
    lst = json.load(open(args.listado_kaggle, encoding='utf-8'))
    tam = {}
    def walk(o):
        if isinstance(o, dict):
            if 'name' in o and ('totalBytes' in o or 'size' in o):
                tam[str(o['name']).split('/')[-1]] = o.get('totalBytes', o.get('size'))
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(lst)
    det, ok = {}, 0
    for n in EM_FILES:
        p = E.folder / f'{n}.parquet'
        h, b = sha256(p), p.stat().st_size
        ref = man[f'{n}.parquet']
        det[n] = dict(sha256=h, bytes=b, coincide_manifiesto=h == ref['sha256'], bytes_manifiesto=ref['size'],
                      bytes_listado_kaggle=tam.get(f'{n}.parquet'), filas=pq.ParquetFile(p).metadata.num_rows)
        ok += det[n]['coincide_manifiesto'] and b == ref['size'] and (tam.get(f'{n}.parquet') in (None, b))
    R.add('VE01', 'Integridad', 'Huellas y tamaños de los trece Parquet frente al manifiesto de descarga y al listado de Kaggle',
          'pasa' if ok == 13 else 'hallazgo', f'{ok} de 13 coinciden', '13 de 13', 'P0' if ok < 13 else '', det, 'VD01')
    # VE02 esquema frente al diccionario
    s = json.load(open(args.pagina, encoding='utf-8'))['value']['content'][0]['text'].replace('\\n', '\n').replace('\\"', '"')
    dic = {}
    secciones = [('customers', '### customers', '### addresses'), ('addresses', '### addresses', '### weather'),
                 ('weather', '### weather', '### Columns in all policy'), ('policies', '### Columns in all policy', '### Motor columns'),
                 ('motor', '### Motor columns', '### Buildings columns'), ('buildings', '### Buildings columns', '### Contents columns'),
                 ('contents', '### Contents columns', '### claims'), ('claims', '### claims', '### expenses'),
                 ('expenses', '### expenses', '### reference_policies'), ('reference_policies', '### reference_policies', '### sample_submission'),
                 ('sample_submission', '### sample_submission', '## Glossary')]
    for nombre, ini, fin in secciones:
        bloque = s[s.index(ini):s.index(fin)]
        filas = [l for l in bloque.splitlines() if l.startswith('| `')]
        cols = {}
        for l in filas:
            celdas = [x.strip() for x in l.strip('|').split('|')]
            nombres = re.findall(r'`([a-z_0-9]+)`', celdas[0])
            mercado = celdas[1] if len(celdas) >= 3 else ''
            for nm in nombres:
                cols[nm] = mercado
        dic[nombre] = cols
    comp = {}
    fallos = 0
    for tabla in EM_FILES:
        reales = set(E.raw[tabla].columns)
        if tabla.startswith('policies_') or tabla.startswith('test_'):
            l = tabla.split('_', 1)[1]
            esperadas = {c for c, m in dic['policies'].items() if 'developed only' not in m} | {c for c, m in dic[l].items() if 'developed only' not in m}
            if tabla.startswith('test_'):
                esperadas -= {'renewal_decision'}
        elif tabla == 'reference_policies':
            esperadas = None
        else:
            esperadas = {c for c, m in dic[tabla].items() if 'developed only' not in m}
        if esperadas is None:
            union = set()
            for l in LINES:
                union |= {c for c, m in dic['policies'].items() if 'developed only' not in m} | {c for c, m in dic[l].items() if 'developed only' not in m}
            esperadas = (union - {'renewal_decision'}) | {'line'}
        solo_datos, solo_dic = sorted(reales - esperadas), sorted(esperadas - reales)
        comp[tabla] = dict(columnas=len(reales), no_documentadas=solo_datos, documentadas_ausentes=solo_dic)
        fallos += len(solo_datos) + len(solo_dic)
    R.add('VE02', 'Integridad', 'Columnas de cada tabla frente al diccionario de la página de datos (marcando las de un solo mercado)',
          'pasa' if fallos == 0 else 'hallazgo', f'{fallos} diferencias', '0', 'P1' if fallos else '', comp, 'VD02')
    # VE03 tipos frente al desarrollado
    dif = {}
    for n in EM_FILES:
        if n in D.schemas:
            se, sd = pq.read_schema(E.folder / f'{n}.parquet'), D.schemas[n]
            for c in se.names:
                if c in sd.names and str(se.field(c).type) != str(sd.field(c).type):
                    dif[f'{n}.{c}'] = (str(se.field(c).type), str(sd.field(c).type))
    R.add('VE03', 'Integridad', 'Tipos de las columnas comunes iguales a los del mercado desarrollado',
          'pasa' if not dif else 'hallazgo', f'{len(dif)} columnas con tipo distinto', '0', 'P1' if dif else '', dif, 'VD02')
    # VE04 filas, duplicados, claves
    det = {}
    for n in EM_FILES:
        t = E.raw[n]
        det[n] = dict(filas=len(t), duplicados_exactos=int(t.duplicated().sum()))
    claves = dict(customer_id=E.customers.customer_id.is_unique, address_id=E.addresses.address_id.is_unique,
                  claim_id=E.claims.claim_id.is_unique, weather_address_year=not E.weather.duplicated(['address_id', 'year']).any(),
                  row_id_global=E.todas.row_id.is_unique, sample_row_id=E.raw['sample_submission'].row_id.is_unique,
                  reference_row_id=E.raw['reference_policies'].row_id.is_unique, expenses_item=E.raw['expenses'].item.is_unique)
    det['claves_unicas'] = claves
    ok = all(claves.values()) and all(v['duplicados_exactos'] == 0 for v in det.values() if isinstance(v, dict) and 'duplicados_exactos' in v)
    R.add('VE04', 'Integridad', 'Filas, duplicados exactos y unicidad de claves en las trece tablas', 'pasa' if ok else 'hallazgo',
          'claves únicas y sin duplicados exactos' if ok else 'ver detalle', 'sin duplicados', 'P0' if not ok else '', det, 'VD02')
    # VE05 cadenas
    det, n_prob = {}, 0
    for n in EM_FILES:
        t = E.raw[n]
        for c in t.columns:
            if t[c].dtype == object or str(t[c].dtype).startswith('str'):
                v = txt(t[c]).dropna()
                if len(v) == 0:
                    continue
                esp = int((v != v.str.strip()).sum())
                vac = int((v.str.strip() == '').sum())
                low = v.str.strip().str.lower()
                variantes = int(low.nunique() < v.nunique())
                nvar = int(v.nunique() - low.nunique())
                if esp or vac or nvar:
                    det[f'{n}.{c}'] = dict(con_espacios=esp, vacias=vac, valores=int(v.nunique()), valores_tras_normalizar=int(low.nunique()))
                    n_prob += 1
    R.add('VE05', 'Integridad', 'Columnas de texto con espacios, cadenas vacías o variantes de mayúsculas',
          'hallazgo' if n_prob else 'pasa', f'{n_prob} columnas con variantes', '0', 'P2' if n_prob else '', det, 'VD02')
    # VE06 nulos
    det = {}
    for n in EM_FILES:
        t = E.raw[n]
        nul = t.isna().mean()
        det[n] = {c: round(float(v), 5) for c, v in nul.items() if v > 0}
    claves_nulas = {f'{n}.{c}': int(E.raw[n][c].isna().sum()) for n in EM_FILES for c in E.raw[n].columns
                    if c in ('row_id', 'policy_id', 'customer_id', 'address_id', 'claim_id', 'period_start', 'period_end', 'exposure', 'loss_date', 'report_date', 'year')
                    and E.raw[n][c].isna().any()}
    # nulos train frente a test por columna de pólizas
    shift = {}
    for l in LINES:
        a, b = E.pol[l], E.test[l]
        for c in b.columns:
            if c in a.columns and (a[c].isna().any() or b[c].isna().any()):
                shift[f'{l}.{c}'] = dict(train=round(float(a[c].isna().mean()), 4), test=round(float(b[c].isna().mean()), 4))
    det['nulos_train_test'] = shift
    det['claves_o_fechas_nulas'] = claves_nulas
    R.add('VE06', 'Integridad', 'Perfil de nulos por tabla; claves, fechas y exposición sin nulos; nulos de pólizas en train frente a test',
          'pasa' if not claves_nulas else 'hallazgo', f'{len(claves_nulas)} claves o fechas con nulos', '0', 'P0' if claves_nulas else '', det, 'VD41')
    # VE07 rangos numéricos frente al diccionario
    det, fallos = {}, {}
    def rango(tabla, df, reglas):
        for c, (lo, hi) in reglas.items():
            if c not in df.columns:
                continue
            v = pd.to_numeric(df[c], errors='coerce').astype(float)
            bad = ((v < lo) if lo is not None else False) | ((v > hi) if hi is not None else False)
            n_inf = int(np.isinf(v.fillna(0)).sum())
            det[f'{tabla}.{c}'] = dict(min=float(v.min()), p01=float(v.quantile(0.01)), mediana=float(v.median()), p99=float(v.quantile(0.99)),
                                       max=float(v.max()), fuera_de_rango=int(bad.sum()), infinitos=n_inf, nulos=int(v.isna().sum()))
            if bad.sum() or n_inf:
                fallos[f'{tabla}.{c}'] = int(bad.sum() + n_inf)
    rango('weather', E.weather, RANGOS['weather'])
    rango('addresses', E.addresses, RANGOS['addresses'])
    rango('customers', E.customers, RANGOS['customers'])
    for l in LINES:
        for kind, df in [('policies', E.pol[l]), ('test', E.test[l])]:
            rango(f'{kind}_{l}', df, {**RANGOS['policies'], **RANGOS.get(l, {})})
    R.add('VE07', 'Integridad', 'Rangos numéricos frente al diccionario (índices 0–10 y 0–1, días 0–366, capitales y primas positivos)',
          'pasa' if not fallos else 'hallazgo', f'{len(fallos)} columnas fuera de rango' if fallos else 'todo dentro de rango', '0',
          'P1' if fallos else '', dict(fuera=fallos, perfil=det), 'VD02')


# ----------------------------------------------------------------------------------------------- B. relaciones
def b_relaciones(E: Emergente, D: Desarrollado, R: Registro):
    det, bad = {}, 0
    cust, addr = set(E.customers.customer_id), set(E.addresses.address_id)
    for l in LINES:
        for kind, df in [('train', E.pol[l]), ('test', E.test[l])]:
            det[f'{l}_{kind}'] = dict(clientes_sin_maestro=int(~df.customer_id.isin(cust).sum() if False else (~df.customer_id.isin(cust)).sum()),
                                      direcciones_sin_maestro=int((~df.address_id.isin(addr)).sum()))
            bad += det[f'{l}_{kind}']['clientes_sin_maestro'] + det[f'{l}_{kind}']['direcciones_sin_maestro']
    usados_c = set(E.todas.customer_id)
    usados_a = set(E.todas.address_id)
    det['clientes_sin_poliza'] = len(cust - usados_c)
    det['direcciones_sin_poliza'] = len(addr - usados_a)
    det['clientes_solo_test'] = len(usados_c - set(pd.concat([E.pol[l].customer_id for l in LINES])))
    R.add('VE08', 'Relaciones', 'Claves de pólizas y test en los maestros de clientes y direcciones; maestros sin uso',
          'pasa' if bad == 0 else 'hallazgo', f'{bad} claves sin maestro; {det["clientes_sin_poliza"]} clientes y {det["direcciones_sin_poliza"]} direcciones sin póliza',
          '0 claves sin maestro', 'P0' if bad else '', det, 'VD03')
    w = E.weather
    por_anio = w.groupby('year').address_id.nunique().to_dict()
    det = dict(direcciones_maestro=len(addr), direcciones_clima=int(w.address_id.nunique()), por_anio=por_anio,
               clima_sin_maestro=int((~w.address_id.isin(addr)).sum()), maestro_sin_clima=len(addr - set(w.address_id)),
               completo=all(v == len(addr) for v in por_anio.values()) and set(por_anio) == {2023, 2024, 2025})
    R.add('VE09', 'Relaciones', 'Clima: cada dirección del maestro exactamente una vez en 2023, 2024 y 2025',
          'pasa' if det['completo'] and det['clima_sin_maestro'] == 0 else 'hallazgo', f'{por_anio}', 'tres años completos', 'P1' if not det['completo'] else '', det, 'VD40')
    # VE10 formatos de identificadores
    det, fallos = {}, 0
    pref = {'motor': 'M', 'buildings': 'B', 'contents': 'C'}
    for l in LINES:
        t = pd.concat([E.pol[l], E.test[l]])
        det[l] = dict(row_id_formato=bool(t.row_id.str.fullmatch(pref[l] + r'\d{8}').all()),
                      policy_id_formato=bool(t.policy_id.str.fullmatch(pref[l] + r'\d{8}').all()),
                      policy_id_distintos=int(t.policy_id.nunique()))
        fallos += (not det[l]['row_id_formato']) + (not det[l]['policy_id_formato'])
    pols = {l: set(pd.concat([E.pol[l].policy_id, E.test[l].policy_id])) for l in LINES}
    det['policy_id_en_dos_ramos'] = len((pols['motor'] & pols['buildings']) | (pols['motor'] & pols['contents']) | (pols['buildings'] & pols['contents']))
    det['customer_id_longitudes'] = {int(k): int(v) for k, v in E.customers.customer_id.str.len().value_counts().items()}
    det['address_id_longitudes'] = {int(k): int(v) for k, v in E.addresses.address_id.str.len().value_counts().items()}
    det['customer_id_en_polizas_longitudes'] = {int(k): int(v) for k, v in E.todas.customer_id.str.len().value_counts().items()}
    det['claim_id_longitudes'] = {int(k): int(v) for k, v in E.claims.claim_id.str.len().value_counts().items()}
    det['customer_id_numericos_con_ceros_iniciales'] = int(E.customers.customer_id.str.startswith('0').sum())
    fallos += det['policy_id_en_dos_ramos'] + (len(det['customer_id_en_polizas_longitudes']) > 1)
    R.add('VE10', 'Relaciones', 'Formato de identificadores: prefijo de ramo, ocho dígitos, longitudes uniformes (sin ceros perdidos como ID01)',
          'pasa' if fallos == 0 else 'hallazgo', f'{fallos} anomalías', '0', 'P1' if fallos else '', det, 'VD49')
    # VE11 siniestros frente a pólizas
    c = E.claims
    det = dict(policy_sin_poliza_del_ramo=int((~c.tiene_poliza.astype(bool)).sum()),
               prefijo_poliza_igual_ramo=bool((c.policy_id.str[0] == c.line.map(pref)).all()),
               peril_fuera_del_ramo=int(sum((~c[c.line == l].peril.isin(PERILS[l])).sum() for l in LINES)),
               policy_en_test_sin_train=int((~c.policy_id.isin(set(pd.concat([E.pol[l].policy_id for l in LINES])))).sum()))
    ok = det['policy_sin_poliza_del_ramo'] == 0 and det['prefijo_poliza_igual_ramo'] and det['peril_fuera_del_ramo'] == 0
    R.add('VE11', 'Relaciones', 'Siniestros: póliza existente en su ramo, prefijo coherente y peligro dentro del catálogo del ramo',
          'pasa' if ok else 'hallazgo', det, 'todo coherente', 'P0' if not ok else '', det, 'VD03')
    # VE12 IDs compartidos entre mercados
    cc = E.customers.merge(D.customers, on='customer_id', suffixes=('_em', '_dev'))
    aa = E.addresses.merge(D.addresses, on='address_id', suffixes=('_em', '_dev'))
    def iguales(df, cols):
        return {c: float((txt(df[c + '_em']).fillna('NA') == txt(df[c + '_dev']).fillna('NA')).mean()) for c in cols}
    det = dict(clientes_compartidos=len(cc), direcciones_compartidas=len(aa),
               clientes_atributos_iguales=iguales(cc, ['surname', 'occupation', 'marital_status', 'household_size', 'customer_since_year', 'email_domain']),
               direcciones_atributos_iguales=iguales(aa, ['urban_density', 'flood_zone', 'soil_type', 'year_built', 'property_type', 'bedrooms', 'energy_rating']),
               clientes_compartidos_con_poliza_emergente=int(cc.customer_id.isin(usados_c).sum()))
    dev_test = {l: read(D.folder, f'test_{l}', ['row_id', 'policy_id']) for l in LINES}
    dev_claims = read(D.folder, 'claims', ['claim_id'])
    det['colisiones_de_identificadores_entre_mercados'] = {
        l: dict(row_id_entrenamiento=int(E.pol[l].row_id.isin(set(D.pol[l].row_id)).sum()), row_id_entrenamiento_filas=len(E.pol[l]),
                row_id_test=int(E.test[l].row_id.isin(set(dev_test[l].row_id)).sum()), row_id_test_filas=len(E.test[l]),
                policy_id=len(set(pd.concat([E.pol[l].policy_id, E.test[l].policy_id])) & set(pd.concat([D.pol[l].policy_id, dev_test[l].policy_id]))),
                policy_id_emergentes=int(pd.concat([E.pol[l].policy_id, E.test[l].policy_id]).nunique()))
        for l in LINES}
    det['colisiones_de_identificadores_entre_mercados']['claim_id'] = int(E.claims.claim_id.isin(set(dev_claims.claim_id)).sum())
    det['colisiones_de_identificadores_entre_mercados']['claim_id_emergentes'] = len(E.claims)
    det['uso_cruzado_de_estas_claves_en_esta_validacion'] = 'ninguno: las claves solo se cruzan dentro de cada mercado; entre mercados solo se comparan atributos de clientes y direcciones con el mismo identificador'
    R.add('VE12', 'Relaciones', 'Los 752 clientes y 8.046 direcciones con el mismo identificador en los dos mercados no comparten atributos',
          'informativo', f"apellido igual en {det['clientes_atributos_iguales']['surname']:.1%}; tipo de vivienda igual en {det['direcciones_atributos_iguales']['property_type']:.1%}",
          'identificadores reutilizados, no las mismas entidades', '', det, 'VD49')
    # VE13 estructura cliente-dirección y coherencia entre ramos
    t = E.todas
    cli_dir = t.groupby('customer_id').address_id.nunique()
    dir_cli = t.groupby('address_id').customer_id.nunique()
    det = dict(clientes_con_varias_direcciones=int((cli_dir > 1).sum()), direcciones_con_varios_clientes=int((dir_cli > 1).sum()),
               max_clientes_por_direccion=int(dir_cli.max()),
               clientes_por_numero_de_ramos={int(k): int(v) for k, v in t.groupby('customer_id').line.nunique().value_counts().sort_index().items()})
    b = pd.concat([E.pol['buildings'], E.test['buildings']])[['customer_id', 'address_id', 'year', 'policyholder_age_band', 'channel', 'period_start', 'mortgage']]
    k = pd.concat([E.pol['contents'], E.test['contents']])[['customer_id', 'address_id', 'year', 'policyholder_age_band', 'channel', 'period_start', 'tenure']]
    m = b.merge(k, on=['customer_id', 'address_id', 'year'], suffixes=('_b', '_c'))
    det['hogares_con_edificios_y_contenidos_mismo_anio'] = len(m)
    orden = {'17-24': 0, '25-34': 1, '35-49': 2, '50-64': 3, '65+': 4}
    ob, oc = m.policyholder_age_band_b.map(orden), m.policyholder_age_band_c.map(orden)
    det['banda_distinta_total'] = int((ob != oc).sum())
    det['banda_sube_con_inicio_posterior'] = int((((oc > ob) & (m.period_start_c > m.period_start_b)) | ((ob > oc) & (m.period_start_b > m.period_start_c))).sum())
    det['banda_de_edad_distinta_entre_ramos'] = det['banda_distinta_total'] - det['banda_sube_con_inicio_posterior']
    det['canal_distinto_entre_ramos'] = int((m.channel_b != m.channel_c).sum())
    det['inicio_distinto_entre_ramos'] = int((m.period_start_b != m.period_start_c).sum())
    det['inquilino_con_poliza_de_edificios'] = int((m.tenure == 'renter').sum())
    det['inquilino_con_hipoteca_en_edificios'] = int(((m.tenure == 'renter') & (m.mortgage.astype(bool))).sum())
    cas = m[(ob != oc) | (m.tenure == 'renter')]
    R.add('VE13', 'Relaciones', 'Hogares con edificios y contenidos el mismo año: banda de edad (salvo cumpleaños entre inicios distintos), canal e inicio; inquilinos con póliza de edificios',
          'hallazgo' if det['banda_de_edad_distinta_entre_ramos'] or det['inquilino_con_poliza_de_edificios'] else 'pasa',
          f"{det['banda_distinta_total']} bandas distintas, todas explicadas por un inicio posterior ({det['banda_sube_con_inicio_posterior']}); {det['inquilino_con_poliza_de_edificios']} inquilinos con edificios de {len(m)} hogares",
          '0', 'P2', det, 'VD38', cas)


# ----------------------------------------------------------------------------------------------- C. calendario y exposición
def c_calendario(E: Emergente, R: Registro):
    det, fallos = {}, 0
    for l in LINES:
        for kind, df in [('train', E.pol[l]), ('test', E.test[l])]:
            d = dict(inicio_min=df.period_start.min(), inicio_max=df.period_start.max(), fin_min=df.period_end.min(), fin_max=df.period_end.max(),
                     inicio_despues_de_fin=int((df.period_start > df.period_end).sum()), dias_min=int(df.dias.min()), dias_max=int(df.dias.max()),
                     cruzan_anio=int((df.period_start.dt.year != df.period_end.dt.year).sum()),
                     anios={int(k): int(v) for k, v in df.year.value_counts().sort_index().items()},
                     fin_30_12_2024=int((df.period_end == '2024-12-30').sum()), fin_31_12_2024=int((df.period_end == '2024-12-31').sum()),
                     cubren_31_12_2024=int(((df.period_start <= '2024-12-31') & (df.period_end >= '2024-12-31')).sum()),
                     fin_31_12=int((df.period_end.dt.strftime('%m-%d') == '12-31').sum()), fin_30_12=int((df.period_end.dt.strftime('%m-%d') == '12-30').sum()))
            det[f'{l}_{kind}'] = d
            fallos += d['inicio_despues_de_fin'] + d['cruzan_anio'] + (d['dias_max'] > 366)
    R.add('VE14', 'Calendario', 'Fechas: inicio ≤ fin, ningún periodo cruza el año natural, 1–365 días; 2024 termina el 30-12 y 2025 el 31-12',
          'hallazgo' if fallos else 'pasa', f'{fallos} anomalías de fechas; 2024 sin ningún periodo que cubra el 31-12', '0', 'P1' if fallos else '', det, 'VD15')
    # VE15 solapes y huecos dentro de póliza
    det, sol_tot = {}, 0
    casos = []
    for l in LINES:
        t = pd.concat([E.pol[l], E.test[l]]).sort_values(['policy_id', 'period_start']).reset_index(drop=True)
        t['fin_prev'] = t.groupby('policy_id').period_end.shift()
        t['hueco'] = (t.period_start - t.fin_prev).dt.days - 1
        sol = t[t.hueco < 0]
        sol_tot += len(sol)
        h = t.hueco.dropna()
        det[l] = dict(solapes=len(sol), continuidades=int(len(h)), hueco_0=int((h == 0).sum()), hueco_1=int((h == 1).sum()),
                      hueco_2_30=int(((h >= 2) & (h <= 30)).sum()), hueco_mas_30=int((h > 30).sum()), hueco_max=int(h.max()),
                      hueco_1_en_2024_2025=int(((t.hueco == 1) & (t.period_start.dt.year == 2025)).sum()))
        casos.append(sol[['row_id', 'policy_id', 'period_start', 'period_end', 'fin_prev', 'hueco']].assign(line=l))
    R.add('VE15', 'Calendario', 'Solapes dentro de la misma póliza y huecos entre periodos consecutivos (incluido el día 31-12-2024)',
          'hallazgo' if sol_tot else 'pasa', f'{sol_tot} solapes; huecos de un día en la transición 2024→2025: ' + str({l: det[l]['hueco_1_en_2024_2025'] for l in LINES}),
          '0 solapes', 'P1' if sol_tot else '', det, 'VD16', pd.concat(casos))
    # VE16 convención de exposición
    det, otras = {}, 0
    casos = []
    for l in LINES:
        for kind, df in [('train', E.pol[l]), ('test', E.test[l])]:
            e, d = df.exposure, df.dias
            m365 = np.isclose(e, np.round(d / 365, 4), atol=5e-5)
            m360 = np.isclose(e, np.round(d / 360, 4), atol=5e-5)
            mdd = np.isclose(e, d)
            conv = np.select([m365, m360, mdd], ['ACT365', 'ACT360', 'DIAS'], 'OTRA')
            vc = pd.Series(conv).value_counts().to_dict()
            det[f'{l}_{kind}'] = dict(convencion=vc, ambiguas=int(((m365 & m360) | (m365 & mdd) | (m360 & mdd)).sum()),
                                      no_positivas=int((e <= 0).sum()), mayores_que_uno=int((e > 1).sum()), min=float(e.min()), max=float(e.max()))
            otras += vc.get('OTRA', 0)
            if kind == 'train':
                casos.append(df.loc[conv != 'ACT365', ['row_id', 'policy_id', 'period_start', 'period_end', 'dias', 'exposure']].assign(line=l, convencion=conv[conv != 'ACT365']))
    n_fix = sum(sum(v for k, v in det[f'{l}_train']['convencion'].items() if k != 'ACT365') for l in LINES)
    R.add('VE16', 'Calendario', 'Convención de exposición por fila: días/365 (normal), días/360 y número de días; ninguna sin explicar; test todo días/365',
          'hallazgo' if otras == 0 and n_fix else ('pasa' if otras == 0 else 'hallazgo'),
          f'{n_fix} filas de entrenamiento en otra convención (495 en días/360 y 114 en días), {otras} sin explicar; test 100 % días/365',
          'una sola convención', 'P0', det, 'VD15', pd.concat(casos))
    # VE17 new_business, renewal_count, customer_since_year
    det, casos = {}, []
    cs = E.customers.set_index('customer_id').customer_since_year
    for l in LINES:
        t = pd.concat([E.pol[l].assign(is_test=False), E.test[l].assign(is_test=True)]).sort_values(['policy_id', 'period_start'])
        t['csy'] = t.customer_id.map(cs)
        nb = t.new_business.astype(bool)
        t['rc_prev'] = t.groupby('policy_id').renewal_count.shift()
        t['anio_prev'] = t.groupby('policy_id').year.shift()
        primera = ~t.policy_id.duplicated()
        primer_anio = t.groupby('policy_id').year.transform('min')
        d = dict(nb_sin_renewal_0=int((nb & (t.renewal_count != 0)).sum()), renewal_0_sin_nb=int((~nb & (t.renewal_count == 0)).sum()),
                 renewal_igual_anio_menos_since=float(((t.year - t.csy) == t.renewal_count).mean()),
                 nb_con_since_distinto_del_anio=int((nb & (t.csy != t.year)).sum()),
                 nb_en_tramo_posterior_del_primer_anio=int((nb & ~primera & (t.year == primer_anio)).sum()),
                 nb_en_anio_posterior_al_primero_de_la_poliza=int((nb & (t.year > primer_anio)).sum()),
                 renovacion_sin_periodo_previo_en_datos=int((~nb & primera & (t.year > 2023)).sum()),
                 renewal_count_salto_distinto_de_1_entre_anios=int(((t.year - t.anio_prev == 1) & (t.renewal_count - t.rc_prev != 1)).sum()),
                 renewal_count_cambia_dentro_del_anio=int(((t.year == t.anio_prev) & (t.renewal_count != t.rc_prev)).sum()),
                 since_posterior_al_periodo=int((t.csy > t.year).sum()))
        det[l] = d
        casos.append(t.loc[(nb & (t.csy != t.year)) | (nb & (t.year > primer_anio)) | (t.csy > t.year), ['row_id', 'policy_id', 'customer_id', 'year', 'new_business', 'renewal_count', 'csy', 'is_test']].assign(line=l))
    hall = sum(d['nb_sin_renewal_0'] + d['renewal_0_sin_nb'] + d['nb_en_anio_posterior_al_primero_de_la_poliza'] + d['since_posterior_al_periodo'] + d['nb_con_since_distinto_del_anio'] for d in det.values())
    R.add('VE17', 'Calendario', 'new_business ⇔ renewal_count = 0; renewal_count = año − customer_since_year; NB solo en el primer año de la póliza (también en sus tramos); sin año de ingreso posterior',
          'hallazgo' if hall else 'pasa', f'{hall} incoherencias', '0', 'P1' if hall else '', det, 'VD17', pd.concat(casos))
    # VE18 days_quote_to_inception y renewal_decision
    det = {}
    for l in LINES:
        a, b = E.pol[l], E.test[l]
        det[l] = dict(train=dict(min=int(a.days_quote_to_inception.min()), mediana=float(a.days_quote_to_inception.median()), max=int(a.days_quote_to_inception.max()),
                                 nb_mediana=float(a[a.new_business.astype(bool)].days_quote_to_inception.median()),
                                 ren_mediana=float(a[~a.new_business.astype(bool)].days_quote_to_inception.median())),
                      test=dict(min=int(b.days_quote_to_inception.min()), mediana=float(b.days_quote_to_inception.median()), max=int(b.days_quote_to_inception.max()),
                                nb_mediana=float(b[b.new_business.astype(bool)].days_quote_to_inception.median())),
                      renewal_decision=txt(a.renewal_decision).value_counts(dropna=False).to_dict())
        det[l]['renewal_decision_fuera_de_dominio'] = sorted(set(txt(a.renewal_decision).dropna()) - set(DOMINIOS['policies']['renewal_decision']))
    neg = sum(min(det[l]['train']['min'], det[l]['test']['min']) < 0 for l in LINES)
    R.add('VE18', 'Calendario', 'Días entre cotización e inicio no negativos; dominio de renewal_decision; distribución en nuevo negocio y renovación',
          'pasa' if neg == 0 and not any(det[l]['renewal_decision_fuera_de_dominio'] for l in LINES) else 'hallazgo',
          f'min {min(det[l]["train"]["min"] for l in LINES)} días; valores de renewal_decision dentro del diccionario', 'sin negativos', 'P1' if neg else '', det, 'VD17')
    # VE19 varios periodos por póliza y año
    det, casos = {}, []
    for l in LINES:
        t = pd.concat([E.pol[l].assign(is_test=False), E.test[l].assign(is_test=True)]).sort_values(['policy_id', 'period_start'])
        n = t.groupby(['policy_id', 'year']).size()
        multi = n[n > 1]
        tt = t[t.set_index(['policy_id', 'year']).index.isin(multi.index)].copy()
        cambios = {}
        if len(tt):
            cols = [c for c in tt.columns if c not in ('row_id', 'period_start', 'period_end', 'exposure', 'dias', 'e365', 'is_test', 'renewal_decision', 'customer_service_contacts', 'written_premium', 'days_quote_to_inception')]
            g = tt.groupby(['policy_id', 'year'])
            for c in cols:
                k = g[c].nunique(dropna=False)
                cambios[c] = int((k > 1).sum())
        det[l] = dict(polizas_anio_con_varios_periodos=int(len(multi)), max_periodos=int(n.max()),
                      por_anio={int(k): int(v) for k, v in multi.reset_index().year.value_counts().sort_index().items()},
                      atributos_que_cambian={k: v for k, v in sorted(cambios.items(), key=lambda x: -x[1]) if v > 0},
                      renewal_decision_del_primer_tramo=txt(tt[~tt.is_test].groupby(['policy_id', 'year']).renewal_decision.first()).value_counts().to_dict() if len(tt) else {})
        casos.append(tt[['row_id', 'policy_id', 'year', 'period_start', 'period_end', 'exposure', 'is_test']].assign(line=l))
    R.add('VE19', 'Calendario', 'Pólizas con varios periodos en el mismo año (cambios a mitad de año): cuántos y qué atributos cambian',
          'informativo', {l: det[l]['polizas_anio_con_varios_periodos'] for l in LINES}, '', '', det, 'VD17', pd.concat(casos))


# ----------------------------------------------------------------------------------------------- D. clientes
def d_clientes(E: Emergente, D: Desarrollado, R: Registro):
    c = E.customers
    det, fuera = {}, {}
    for col, dom in DOMINIOS['customers'].items():
        v = txt(c[col]).dropna()
        extra = sorted(set(v) - set(dom))
        det[col] = dict(valores=v.value_counts().to_dict(), fuera_de_dominio=extra)
        if extra:
            fuera[col] = extra
    for col in ['household_size', 'prior_claims_5y', 'licence_points', 'years_at_address', 'customer_since_year', 'email_domain', 'marketing_consent',
                'document_preference', 'previous_insurer', 'campaign_code', 'branch_id', 'marketing_segment']:
        v = c[col]
        det[col] = dict(nulos=int(v.isna().sum()), distintos=int(v.nunique()),
                        valores=(txt(v).value_counts().head(12).to_dict() if v.nunique() <= 60 else dict(min=float(pd.to_numeric(v, errors='coerce').min()), max=float(pd.to_numeric(v, errors='coerce').max()))))
    R.add('VE20', 'Clientes', 'Dominios y perfiles de las 17 columnas del maestro de clientes (género, estado civil, preferencias, campañas, sucursales)',
          'hallazgo' if fuera else 'pasa', f'{len(fuera)} columnas fuera de dominio' if fuera else 'dominios del diccionario', '0', 'P1' if fuera else '', det, 'VD56')
    # VE21 ocupación
    occ = txt(c.occupation)
    n1 = occ.dropna().nunique()
    norm = occ.dropna().str.strip().str.lower()
    n2 = norm.nunique()
    sin_self = norm.str.replace(r'^self-employed\s+', '', regex=True)
    n3 = sin_self.nunique()
    dev_occ = set(txt(D.customers.occupation).dropna().str.strip().str.lower())
    det = dict(valores_crudos=int(n1), tras_normalizar_espacios_y_mayusculas=int(n2), tras_quitar_prefijo_self_employed=int(n3),
               vocabulario_desarrollado=len(dev_occ), coinciden_con_desarrollado=len(set(sin_self) & dev_occ), fuera_del_desarrollado=sorted(set(sin_self) - dev_occ)[:20],
               nulos=int(occ.isna().sum()), con_prefijo_self_employed=int(norm.str.startswith('self-employed').sum()),
               self_employed_retired=int((norm == 'self-employed retired').sum()),
               variantes_por_base=norm.groupby(sin_self).nunique().sort_values(ascending=False).head(10).to_dict())
    R.add('VE21', 'Clientes', 'Ocupación: texto libre con variantes de escritura y prefijo «self-employed»; vocabulario frente al desarrollado',
          'hallazgo', f'{n1} valores crudos → {n2} normalizados → {n3} sin prefijo; {len(set(sin_self) & dev_occ)} coinciden con las {len(dev_occ)} del desarrollado',
          'un vocabulario', 'P2', det, 'VD55')
    # VE22 antigüedad y años en la dirección
    t = E.todas
    first = t.groupby('customer_id').year.min()
    cc = c.set_index('customer_id')
    cmp = pd.DataFrame(dict(primer_anio=first, since=cc.customer_since_year.reindex(first.index), yaa=cc.years_at_address.reindex(first.index)))
    nb_test = t[t.is_test & t.new_business.astype(bool)]
    det = dict(since_mayor_que_primer_anio_observado=int((cmp.since > cmp.primer_anio).sum()),
               since_menor_que_2023_en_clientes_de_train=int((cmp.since < 2023).sum()),
               distribucion_since={int(k): int(v) for k, v in cc.customer_since_year.value_counts().sort_index().items()},
               nb_test_con_since_2025=float((nb_test.customer_id.map(cc.customer_since_year) == 2025).mean()),
               years_at_address_mayor_que_edad_maxima_banda=None)
    # years_at_address frente a la banda de edad del tomador en hogar
    h = pd.concat([E.pol['buildings'], E.test['buildings'], E.pol['contents'], E.test['contents']])[['customer_id', 'policyholder_age_band']]
    h['yaa'] = h.customer_id.map(cc.years_at_address)
    tope = h.policyholder_age_band.map({'17-24': 24, '25-34': 34, '35-49': 49, '50-64': 64, '65+': 120})
    det['years_at_address_mayor_que_edad_maxima_banda'] = int((h.yaa > tope).sum())
    R.add('VE22', 'Clientes', 'Año de ingreso frente al primer periodo observado; nuevo negocio del test con ingreso 2025; años en la dirección frente a la edad',
          'hallazgo' if det['since_mayor_que_primer_anio_observado'] or det['years_at_address_mayor_que_edad_maxima_banda'] else 'pasa',
          f"{det['since_mayor_que_primer_anio_observado']} ingresos posteriores al primer periodo; {det['years_at_address_mayor_que_edad_maxima_banda']} años en la dirección por encima de la edad",
          '0', 'P2', det, 'VD56')
    # VE23 prior_claims_5y frente a los siniestros observados
    det = {}
    for l in LINES:
        p = E.pol[l].copy()
        p['pc'] = p.customer_id.map(cc.prior_claims_5y)
        a = E.acc[E.acc.line == l]
        n = a.groupby('row_id').size()
        p['n'] = p.row_id.map(n).fillna(0)
        g = p.groupby('pc').apply(lambda x: x.n.sum() / x.e365.sum(), include_groups=False)
        base = p.n.sum() / p.e365.sum()
        det[l] = dict(frecuencia_relativa_por_prior_claims={str(k): round(float(v / base), 3) for k, v in g.items()},
                      filas_por_prior_claims={str(k): int(v) for k, v in p.pc.value_counts().sort_index().items()})
    R.add('VE23', 'Clientes', 'prior_claims_5y (declarado al ingresar) frente a la frecuencia observada: relatividad plausible, sin salto que delate fuga',
          'informativo', {l: det[l]['frecuencia_relativa_por_prior_claims'] for l in LINES}, 'relatividad moderada y creciente', '', det, 'VD47')
    # VE24 nulos de clientes por segmento
    det = {}
    nulcols = [col for col in c.columns if c[col].isna().any()]
    for l in LINES:
        t = pd.concat([E.pol[l].assign(is_test=False), E.test[l].assign(is_test=True)])
        t = t.merge(c[['customer_id'] + nulcols], on='customer_id', how='left')
        seg = {}
        for nombre, msk in [('train_renovacion', ~t.is_test & ~t.new_business.astype(bool)), ('train_nb', ~t.is_test & t.new_business.astype(bool)),
                            ('test_renovacion', t.is_test & ~t.new_business.astype(bool)), ('test_nb', t.is_test & t.new_business.astype(bool))]:
            seg[nombre] = {col: round(float(t.loc[msk, col].isna().mean()), 4) for col in nulcols}
        det[l] = seg
    R.add('VE24', 'Clientes', 'Nulos del maestro de clientes por segmento (renovación y nuevo negocio, train y test): ¿estructurales o desplazados?',
          'informativo', {col: det['motor']['train_renovacion'][col] for col in nulcols[:6]}, '', '', det, 'VD41')


# ----------------------------------------------------------------------------------------------- E. direcciones y clima
def e_direcciones_clima(E: Emergente, D: Desarrollado, R: Registro):
    a = E.addresses
    det, fuera = {}, {}
    for col, dom in DOMINIOS['addresses'].items():
        v = txt(a[col]).dropna()
        extra = sorted(set(v) - set(dom))
        det[col] = dict(valores=v.value_counts().to_dict(), fuera_de_dominio=extra)
        if extra:
            fuera[col] = extra
    for col in ['flood_zone', 'basement', 'listed_building', 'solar_panels', 'bedrooms', 'trees_within_5m']:
        det[col] = txt(a[col]).value_counts().sort_index().to_dict()
    R.add('VE25', 'Direcciones', 'Dominios del maestro de direcciones (región E01–E06, densidad, zona de inundación 1–5, suelo, tipo, tejado, energía)',
          'hallazgo' if fuera else 'pasa', f'{len(fuera)} columnas fuera de dominio' if fuera else 'dominios del diccionario', '0', 'P1' if fuera else '', det, 'VD39')
    # VE26 coherencia física
    anio_pol = E.todas.groupby('address_id').year.min()
    aa = a.set_index('address_id')
    det = dict(distancia_mediana_por_zona={int(k): float(v) for k, v in a.groupby('flood_zone').distance_to_river_km.median().items()},
               elevacion_mediana_por_zona={int(k): float(v) for k, v in a.groupby('flood_zone').elevation_m.median().items()},
               elevacion_negativa=int((a.elevation_m < 0).sum()), distancia_negativa=int((a.distance_to_river_km < 0).sum()),
               construida_despues_del_primer_periodo=int((aa.year_built.reindex(anio_pol.index) > anio_pol).sum()),
               construida_despues_de_2025=int((a.year_built > 2025).sum()),
               listed_por_tramo_de_construccion={str(k): float(v) for k, v in a.groupby(pd.cut(a.year_built, [0, 1900, 1950, 2000, 2100]), observed=True).listed_building.mean().items()},
               dormitorios_por_tipo={str(k): float(v) for k, v in a.groupby('property_type').bedrooms.median().items()},
               sotano_en_pisos=float(a[a.property_type == 'flat'].basement.mean()) if 'flat' in set(a.property_type) else None,
               year_built_min=int(a.year_built.min()), year_built_max=int(a.year_built.max()))
    mono = all(det['distancia_mediana_por_zona'][k] >= det['distancia_mediana_por_zona'][k + 1] for k in range(1, 5) if k + 1 in det['distancia_mediana_por_zona'])
    det['distancia_decrece_con_la_zona'] = mono
    hall = det['construida_despues_del_primer_periodo'] + det['elevacion_negativa'] + det['distancia_negativa'] + det['construida_despues_de_2025']
    R.add('VE26', 'Direcciones', 'Coherencia física: la distancia al río baja con la zona de inundación, sin elevaciones negativas, ninguna vivienda construida después de su primer periodo',
          'hallazgo' if hall else 'pasa', f"{hall} incoherencias; distancia decrece con la zona: {mono}", '0', 'P2' if hall else '', det, 'VD20')
    # VE27 comparación con el desarrollado
    det = {}
    for col in ['urban_density', 'flood_zone', 'soil_type', 'year_built', 'property_type', 'roof_type', 'basement', 'trees_within_5m', 'listed_building', 'bedrooms', 'energy_rating', 'solar_panels', 'distance_to_river_km', 'elevation_m']:
        det[col] = round(psi(D.addresses[col], a[col]), 4)
    R.add('VE27', 'Direcciones', 'Desplazamiento de las direcciones frente al desarrollado (PSI por columna)', 'informativo',
          {k: v for k, v in sorted(det.items(), key=lambda x: -x[1])[:5]}, '', '', det, 'VD43')
    # VE28 clima físico
    w = E.weather
    piv = w.pivot(index='address_id', columns='year', values=[c for c in w.columns if c not in ('address_id', 'year')])
    det = dict(filas_identicas_2024_2025=int((piv.xs(2024, axis=1, level=1) == piv.xs(2025, axis=1, level=1)).all(axis=1).sum()),
               filas_identicas_2023_2024=int((piv.xs(2023, axis=1, level=1) == piv.xs(2024, axis=1, level=1)).all(axis=1).sum()),
               medias_por_anio={int(y): {c: round(float(v), 3) for c, v in g.drop(columns='address_id').mean().items()} for y, g in w.groupby('year')},
               correlacion_interanual={c: dict(r_2023_2024=round(float(piv[(c, 2023)].corr(piv[(c, 2024)])), 3), r_2024_2025=round(float(piv[(c, 2024)].corr(piv[(c, 2025)])), 3))
                                       for c in w.columns if c not in ('address_id', 'year')},
               helada_vs_temperatura_corr=round(float(w.freezing_days.corr(w.mean_temperature_c)), 3),
               sequia_vs_lluvia_corr=round(float(w.dry_summer_index.corr(w.rainfall_mm)), 3),
               variables_con_r_2023_2024_de_0_80_o_mas=[c for c in w.columns if c not in ('address_id', 'year') and piv[(c, 2023)].corr(piv[(c, 2024)]) >= 0.80],
               variables_con_r_en_los_dos_pares_de_0_80_o_mas=[c for c in w.columns if c not in ('address_id', 'year') and piv[(c, 2023)].corr(piv[(c, 2024)]) >= 0.80 and piv[(c, 2024)].corr(piv[(c, 2025)]) >= 0.80],
               medias_por_region={r: {c: round(float(v), 3) for c, v in g.items()} for r, g in w.merge(a[['address_id', 'region']], on='address_id').groupby('region')[['hail_days', 'wind_exposure_index', 'freezing_days', 'rainfall_mm', 'mean_temperature_c']].mean().iterrows()})
    R.add('VE28', 'Clima', 'Clima: 2025 no es copia de 2024, signos físicos coherentes (heladas frente a temperatura, sequía frente a lluvia), medias por región',
          'pasa' if det['filas_identicas_2024_2025'] == 0 and det['helada_vs_temperatura_corr'] < 0 else 'hallazgo',
          f"copias 2024→2025: {det['filas_identicas_2024_2025']}; r(heladas, temperatura) {det['helada_vs_temperatura_corr']}; r(sequía, lluvia) {det['sequia_vs_lluvia_corr']}",
          'sin copias y signos físicos', 'P2', det, 'VD40')
    # VE29 clima frente al desarrollado
    det = {}
    dw = D.weather[D.weather.year.isin([2023, 2024])]
    ew = w[w.year.isin([2023, 2024])]
    for col in ['hail_days', 'wind_exposure_index', 'freezing_days', 'dry_summer_index', 'wildfire_index', 'rainfall_mm', 'mean_temperature_c']:
        det[col] = dict(media_desarrollado=round(float(dw[col].mean()), 3), media_emergente=round(float(ew[col].mean()), 3), psi=round(psi(dw[col], ew[col]), 4),
                        emergente_fuera_del_rango_desarrollado=int(((ew[col] < dw[col].min()) | (ew[col] > dw[col].max())).sum()))
    R.add('VE29', 'Clima', 'Clima emergente 2023–2024 frente al desarrollado: medias, PSI y valores fuera del rango observado en el desarrollado', 'informativo',
          {c: det[c]['psi'] for c in det}, '', '', det, 'VD44')


# ----------------------------------------------------------------------------------------------- F. pólizas por ramo
def f_polizas(E: Emergente, D: Desarrollado, R: Registro, args=None):
    def dominios(l, cols_dom):
        det, fuera = {}, {}
        t = pd.concat([E.pol[l], E.test[l]])
        for col, dom in cols_dom.items():
            v = txt(t[col]).dropna() if col != 'voluntary_excess' else t[col].dropna()
            extra = sorted(set(v) - set(dom if col != 'voluntary_excess' else [float(x) for x in dom] + dom))
            det[col] = dict(valores=(v.value_counts().to_dict() if v.nunique() <= 25 else int(v.nunique())), fuera_de_dominio=[str(x) for x in extra])
            if extra:
                fuera[col] = [str(x) for x in extra]
        return det, fuera
    # VE30 autos
    cd = {**DOMINIOS['policies'], **DOMINIOS['motor']}
    cd.pop('renewal_decision')
    det, fuera = dominios('motor', cd)
    t = pd.concat([E.pol['motor'], E.test['motor']])
    det['make_model_niveles'] = int(t.make_model.nunique())
    mm = t.groupby('make_model').agg(body=('body_type', 'nunique'), fuel=('fuel_type', 'nunique'), seats=('seats', 'nunique'), trans=('transmission', 'nunique'), filas=('row_id', 'size'))
    det['make_model_con_varios_body_type'] = int((mm.body > 1).sum())
    det['make_model_con_varios_fuel_type'] = int((mm.fuel > 1).sum())
    det['make_model_con_varios_seats'] = int((mm.seats > 1).sum())
    det['vehicle_age_min'] = int(t.vehicle_age.min())
    det['vehicle_age_min_desarrollado'] = int(D.pol['motor'].vehicle_age.min())
    det['electricos_con_cilindrada'] = int(((t.fuel_type == 'electric') & t.engine_size_cc.notna() & (t.engine_size_cc > 0)).sum())
    det['electricos_sin_cilindrada'] = int(((t.fuel_type == 'electric') & t.engine_size_cc.isna()).sum())
    det['no_electricos_sin_cilindrada'] = int(((t.fuel_type != 'electric') & t.engine_size_cc.isna()).sum())
    det['compulsory_excess_valores'] = t.compulsory_excess.value_counts().head(8).to_dict()
    det['compulsory_excess_constante'] = bool(t.compulsory_excess.nunique() == 1)
    det['compulsory_excess_constante_en_hogar'] = {l2: int(pd.concat([E.pol[l2], E.test[l2]]).compulsory_excess.nunique()) for l2 in HOGAR}
    det['compulsory_excess_constante_en_desarrollado'] = bool(D.pol['motor'].compulsory_excess.nunique() == 1)
    det['compulsory_excess_valor_por_ramo'] = {l2: sorted(float(x) for x in pd.concat([E.pol[l2], E.test[l2]]).compulsory_excess.unique()) for l2 in LINES}
    det['compulsory_excess_valor_desarrollado_autos'] = sorted(float(x) for x in D.pol['motor'].compulsory_excess.unique())
    det['discount_applied_valores'] = t.discount_applied.round(3).value_counts().head(8).to_dict()
    R.add('VE30', 'Autos', 'Dominios de autos (bandas, carrocería, combustible, cobertura, uso, aparcamiento, franquicias, canal, pago); make_model coherente; eléctricos con cilindrada',
          'hallazgo' if fuera or det['electricos_con_cilindrada'] else 'pasa',
          f"{len(fuera)} columnas fuera de dominio; {det['electricos_con_cilindrada']} eléctricos con cilindrada; vehicle_age mínimo {det['vehicle_age_min']} (desarrollado {det['vehicle_age_min_desarrollado']})",
          'dominios del diccionario', 'P2', det, 'VD35')
    # VE75 make_model: coherencia física y señal transferible
    pm = E.pol['motor'].copy()
    acc = E.acc[E.acc.line == 'motor'].groupby('row_id').size()
    pm['n'] = pm.row_id.map(acc).fillna(0)
    def dispersion(df, col, ecol):
        g = df.groupby(col).agg(n=('n', 'sum'), e=(ecol, 'sum'))
        lam = g.n.sum() / g.e.sum()
        g['esp'] = lam * g.e
        chi = float(((g.n - g.esp) ** 2 / g.esp).sum())
        return g, dict(chi2=round(chi, 1), gl=int(len(g) - 1), p=float(stats.chi2.sf(chi, len(g) - 1)), dispersion=round(chi / (len(g) - 1), 3))
    g_em, d_em = dispersion(pm, 'make_model', 'e365')
    _, d_vvg = dispersion(pm, 'vehicle_value_group', 'e365')
    _, d_band = dispersion(pm, 'driver_age_band', 'e365')
    dm = D.pol['motor'][['row_id', 'policy_id', 'period_start', 'make_model', 'body_type', 'fuel_type', 'seats']].copy()
    dmm = dm.groupby('make_model').agg(body=('body_type', 'nunique'), fuel=('fuel_type', 'nunique'), seats=('seats', 'nunique'))
    det = dict(niveles_emergente=int(t.make_model.nunique()), niveles_desarrollado=int(dm.make_model.nunique()), codigos_comunes=len(set(t.make_model) & set(dm.make_model)),
               codigos_con_varias_carrocerias_emergente=int((mm.body > 1).sum()), codigos_con_varias_carrocerias_desarrollado=int((dmm.body > 1).sum()),
               codigos_con_varios_combustibles_emergente=int((mm.fuel > 1).sum()), filas_por_codigo_emergente=dict(min=int(mm.filas.min()), mediana=float(mm.filas.median()), max=int(mm.filas.max())),
               dispersion_frecuencia_por_codigo_emergente=d_em, dispersion_vehicle_value_group=d_vvg, dispersion_driver_age_band=d_band,
               correlacion_frecuencia_por_codigo_con_desarrollado=None)
    if args is not None and getattr(args, 'developed', None) is not None:
        dc = read(args.developed, 'claims', ['claim_id', 'policy_id', 'line', 'loss_date', 'status'])
        dc = dc[(dc.line == 'motor') & (dc.status != 'repudiated') & (dc.claim_id.str.len() != 11)].copy()
        dc['loss_date'] = pd.to_datetime(dc.loss_date)
        dm2 = read(args.developed, 'policies_motor', ['row_id', 'policy_id', 'period_start', 'period_end', 'make_model'])
        dm2['period_start'] = pd.to_datetime(dm2.period_start)
        dm2['period_end'] = pd.to_datetime(dm2.period_end)
        mj = dc.merge(dm2[['row_id', 'policy_id', 'period_start', 'period_end']], on='policy_id')
        mj = mj[(mj.loss_date >= mj.period_start) & (mj.loss_date <= mj.period_end)]
        dm2['n'] = dm2.row_id.map(mj.groupby('row_id').size()).fillna(0)
        dm2['e'] = ((dm2.period_end - dm2.period_start).dt.days + 1) / 365
        g_dev, d_dev = dispersion(dm2, 'make_model', 'e')
        det['dispersion_frecuencia_por_codigo_desarrollado'] = d_dev
        r = pd.DataFrame(dict(em=g_em.n / g_em.e, dev=g_dev.n / g_dev.e)).dropna()
        det['correlacion_frecuencia_por_codigo_con_desarrollado'] = round(float(r.em.corr(r.dev)), 3)
        det['correlacion_frecuencia_por_codigo_con_desarrollado_filas'] = len(r)
    R.add('VE75', 'Autos', 'make_model: 300 códigos que no describen el vehículo (cada uno con varias carrocerías y combustibles); sobredispersión de la frecuencia por código en los dos mercados, pero las frecuencias por código no se correlacionan entre mercados',
          'hallazgo', f"{det['codigos_con_varias_carrocerias_emergente']} de {det['niveles_emergente']} códigos con varias carrocerías; dispersión {d_em['dispersion']} (p {d_em['p']:.1e}); correlación entre mercados {det['correlacion_frecuencia_por_codigo_con_desarrollado']}",
          'un código describe un vehículo', 'P1', det, 'VD44')
    # VE31 coherencia de autos
    tope = t.driver_age_band.map({'17-24': 24, '25-34': 34, '35-49': 49, '50-64': 64, '65+': 120})
    piso = t.driver_age_band.map({'17-24': 17, '25-34': 25, '35-49': 35, '50-64': 50, '65+': 65})
    det = dict(carnet_antes_de_los_16=int((tope - t.years_licensed < 16).sum()), carnet_antes_de_los_17_con_edad_minima=int((piso - t.years_licensed < 0).sum()),
               ncb_mayor_que_carnet=int((t.ncb_years > t.years_licensed).sum()), ncb_mayor_que_carnet_train=int((E.pol['motor'].ncb_years > E.pol['motor'].years_licensed).sum()),
               ncb_mayor_que_carnet_test=int((E.test['motor'].ncb_years > E.test['motor'].years_licensed).sum()),
               ncb_mayor_que_carnet_cuota=float((t.ncb_years > t.years_licensed).mean()),
               ncb_mayor_que_carnet_desarrollado_cuota=float((D.pol['motor'].ncb_years > D.pol['motor'].years_licensed).mean()),
               joven_nombrado_con_banda_17_24=int(((t.driver_age_band == '17-24') & t.named_young_driver.astype(bool)).sum()),
               joven_nombrado_por_banda={k: float(v) for k, v in t.groupby('driver_age_band').named_young_driver.mean().items()},
               seats_fuera_2_9=int(((t.seats < 2) | (t.seats > 9)).sum()), engine_cc_min=float(t.engine_size_cc.min()), engine_cc_max=float(t.engine_size_cc.max()))
    cas = t.loc[(tope - t.years_licensed < 16) | (t.ncb_years > t.years_licensed), ['row_id', 'policy_id', 'driver_age_band', 'years_licensed', 'ncb_years']]
    R.add('VE31', 'Autos', 'Coherencia: edad implícita al obtener el carnet, NCB frente a años de carnet, conductor joven nombrado frente a banda del titular',
          'hallazgo' if det['carnet_antes_de_los_16'] or det['ncb_mayor_que_carnet'] else 'pasa',
          f"{det['carnet_antes_de_los_16']} carnets antes de los 16 (cota superior de la banda); {det['ncb_mayor_que_carnet']} NCB mayor que carnet",
          '0', 'P2', det, 'VD33', cas)
    # VE32 evolución dentro de póliza (autos)
    t = pd.concat([E.pol['motor'].assign(is_test=False), E.test['motor'].assign(is_test=True)]).sort_values(['policy_id', 'period_start'])
    g = t.groupby('policy_id')
    t['dy'] = t.year - g.year.shift()
    for c in ['years_licensed', 'vehicle_age', 'ncb_years', 'make_model', 'driver_age_band', 'customer_id', 'address_id']:
        t[c + '_prev'] = g[c].shift()
    a = t[t.dy == 1]
    orden = {'17-24': 0, '25-34': 1, '35-49': 2, '50-64': 3, '65+': 4}
    det = dict(pares_anio_siguiente=len(a), carnet_no_sube_1=int((a.years_licensed - a.years_licensed_prev != 1).sum()),
               vehiculo_mismo_modelo=int((a.make_model == a.make_model_prev).sum()),
               edad_vehiculo_no_sube_1_mismo_modelo=int(((a.make_model == a.make_model_prev) & (a.vehicle_age - a.vehicle_age_prev != 1)).sum()),
               cambio_de_vehiculo=int((a.make_model != a.make_model_prev).sum()),
               ncb_salto_fuera_de_menos2_a_mas1=int((~(a.ncb_years - a.ncb_years_prev).between(-2, 1)).sum()),
               ncb_distribucion_de_saltos={str(k): int(v) for k, v in (a.ncb_years - a.ncb_years_prev).value_counts().sort_index().items()},
               banda_retrocede=int((a.driver_age_band.map(orden) < a.driver_age_band_prev.map(orden)).sum()),
               cambio_de_cliente=int((a.customer_id != a.customer_id_prev).sum()), cambio_de_direccion=int((a.address_id != a.address_id_prev).sum()))
    cas = a.loc[(a.years_licensed - a.years_licensed_prev != 1) | (a.driver_age_band.map(orden) < a.driver_age_band_prev.map(orden)),
                ['row_id', 'policy_id', 'year', 'years_licensed', 'years_licensed_prev', 'driver_age_band', 'driver_age_band_prev', 'vehicle_age', 'vehicle_age_prev', 'make_model', 'make_model_prev', 'is_test']]
    R.add('VE32', 'Autos', 'Evolución de la póliza de un año al siguiente: carnet +1, edad del vehículo +1 si es el mismo modelo, NCB en −2…+1, banda de edad sin retroceder, mismo cliente',
          'hallazgo' if det['carnet_no_sube_1'] or det['banda_retrocede'] or det['cambio_de_cliente'] else 'pasa',
          f"{det['carnet_no_sube_1']} carnets que no suben 1; {det['banda_retrocede']} bandas que retroceden; {det['cambio_de_cliente']} cambios de cliente en {len(a)} pares",
          '0', 'P2', det, 'VD36', cas)
    # VE33 edificios
    cd = {**DOMINIOS['policies'], **DOMINIOS['buildings']}
    cd.pop('renewal_decision')
    det, fuera = dominios('buildings', cd)
    t = pd.concat([E.pol['buildings'], E.test['buildings']])
    det['desocupacion_por_ocupacion'] = {k: dict(mediana=float(g.median()), p90=float(g.quantile(0.9)), mayor_de_30=int((g > 30).sum())) for k, g in t.groupby('occupancy').days_unoccupied}
    det['desocupados_todo_el_anio'] = int((t.days_unoccupied >= 365).sum())
    det['construccion_desarrollado'] = txt(D.pol['buildings'].construction_type).str.lower().value_counts().to_dict()
    det['construccion_emergente'] = txt(t.construction_type).value_counts().to_dict()
    R.add('VE33', 'Edificios', 'Dominios de edificios; códigos de construcción BRK/STN/WOD/MIX frente a brick/stone/timber/non-standard (y los alias t/w del desarrollado); desocupación frente a ocupación',
          'hallazgo' if fuera else 'pasa', f"{len(fuera)} columnas fuera de dominio; códigos {list(det['construccion_emergente'])}", 'dominios del diccionario', 'P2', det, 'VD31')
    # VE34 contenidos
    cd = {**DOMINIOS['policies'], **DOMINIOS['contents']}
    cd.pop('renewal_decision')
    det, fuera = dominios('contents', cd)
    t = pd.concat([E.pol['contents'], E.test['contents']])
    bld = pd.concat([E.pol['buildings'], E.test['buildings']])[['customer_id', 'address_id', 'year', 'mortgage', 'occupancy']]
    m = t.merge(bld, on=['customer_id', 'address_id', 'year'], how='left', indicator=True)
    det['contenidos_con_edificios_mismo_cliente_anio'] = int((m._merge == 'both').sum())
    det['inquilinos_con_edificios'] = int(((m._merge == 'both') & (m.tenure == 'renter')).sum())
    det['propietarios_sin_edificios'] = int(((m._merge == 'left_only') & (m.tenure == 'owner')).sum())
    det['high_value_items_valores'] = t.high_value_items.value_counts().sort_index().to_dict()
    R.add('VE34', 'Contenidos', 'Dominios de contenidos (tenencia, seguridad, objetos de valor, teletrabajo, inquilinos, bicicletas); cruce con edificios del mismo hogar',
          'hallazgo' if fuera else 'pasa', f"{len(fuera)} columnas fuera de dominio; {det['inquilinos_con_edificios']} inquilinos con edificios del mismo hogar", 'dominios del diccionario', 'P2', det, 'VD38')
    # VE35 evolución de hogar dentro de póliza
    det, casos = {}, []
    for l in HOGAR:
        t = pd.concat([E.pol[l].assign(is_test=False), E.test[l].assign(is_test=True)]).sort_values(['policy_id', 'period_start'])
        g = t.groupby('policy_id')
        t['dy'] = t.year - g.year.shift()
        t['si_prev'] = g.sum_insured.shift()
        t['band_prev'] = g.policyholder_age_band.shift()
        t['addr_prev'] = g.address_id.shift()
        t['cust_prev'] = g.customer_id.shift()
        a = t[t.dy == 1].copy()
        a['ratio'] = a.sum_insured / a.si_prev
        orden = {'17-24': 0, '25-34': 1, '35-49': 2, '50-64': 3, '65+': 4}
        det[l] = dict(pares=len(a), ratio_mediana=float(a.ratio.median()), ratio_p10=float(a.ratio.quantile(0.1)), ratio_p90=float(a.ratio.quantile(0.9)),
                      saltos_x1000=int(a.ratio.between(900, 1100).sum()), caidas_x1000=int(a.ratio.between(1 / 1100, 1 / 900).sum()),
                      ratio_fuera_0_7_1_5=int((~a.ratio.between(0.7, 1.5) & ~a.ratio.between(900, 1100) & ~a.ratio.between(1 / 1100, 1 / 900)).sum()),
                      banda_retrocede=int((a.policyholder_age_band.map(orden) < a.band_prev.map(orden)).sum()),
                      cambio_de_direccion=int((a.address_id != a.addr_prev).sum()), cambio_de_cliente=int((a.customer_id != a.cust_prev).sum()))
        casos.append(a.loc[(a.policyholder_age_band.map(orden) < a.band_prev.map(orden)) | (a.customer_id != a.cust_prev) | (~a.ratio.between(0.7, 1.5) & ~a.ratio.between(900, 1100) & ~a.ratio.between(1 / 1100, 1 / 900)),
                           ['row_id', 'policy_id', 'year', 'sum_insured', 'si_prev', 'ratio', 'policyholder_age_band', 'band_prev', 'address_id', 'addr_prev', 'is_test']].assign(line=l))
    hall = sum(det[l]['banda_retrocede'] + det[l]['cambio_de_cliente'] for l in HOGAR)
    R.add('VE35', 'Hogar', 'Evolución de hogar de un año al siguiente: capital indexado (razón año a año), banda de edad sin retroceder, mismo cliente; saltos ×1000',
          'hallazgo' if hall else 'pasa', f"razón mediana {det['buildings']['ratio_mediana']:.3f} / {det['contents']['ratio_mediana']:.3f}; saltos ×1000: {det['buildings']['saltos_x1000'] + det['contents']['saltos_x1000']}; bandas que retroceden: {hall}",
          '0 retrocesos', 'P2', det, 'VD30', pd.concat(casos))
    # VE36 capital: nubes, prueba de prima, plausibilidad
    det = {}
    for l in HOGAR:
        t = pd.concat([E.pol[l].assign(is_test=False), E.test[l].assign(is_test=True)])
        umbral = {'buildings': 5e6, 'contents': 2e6}[l]
        normal, ext = t[t.sum_insured <= umbral], t[t.sum_insured > umbral]
        ppm_n = 1000 * normal.written_premium / normal.sum_insured
        ppm_e = 1000 * ext.written_premium / ext.sum_insured
        det[l] = dict(filas_sobre_umbral=len(ext), umbral=umbral, capital_normal_max=float(normal.sum_insured.max()), capital_extremo_min=float(ext.sum_insured.min()),
                      hueco_veces=float(ext.sum_insured.min() / normal.sum_insured.max()), ppm_normal=dict(min=float(ppm_n.min()), mediana=float(ppm_n.median()), max=float(ppm_n.max())),
                      ppm_extrema_max=float(ppm_e.max()), ppm_extrema_x1000_dentro=int((((1000 * ppm_e) >= ppm_n.min()) & ((1000 * ppm_e) <= ppm_n.max())).sum()) if len(ext) else 0,
                      capital_cero_o_negativo=int((t.sum_insured <= 0).sum()),
                      capital_mediano_por_dormitorios={str(k): float(v) for k, v in t.merge(E.addresses[['address_id', 'bedrooms']], on='address_id').groupby('bedrooms').sum_insured.median().items()} if l == 'buildings' else None)
    R.add('VE36', 'Hogar', 'Capital asegurado: dos nubes separadas por un hueco, prueba de prima por mil en la nube extrema (CAPS2-01), capital frente a dormitorios',
          'hallazgo', f"{det['buildings']['filas_sobre_umbral']} + {det['contents']['filas_sobre_umbral']} filas en la nube extrema; hueco {det['buildings']['hueco_veces']:.0f}× y {det['contents']['hueco_veces']:.0f}×",
          'una sola escala', 'P1', det, 'VD30')
    # VE37 prima escrita
    det = {}
    for l in LINES:
        t = pd.concat([E.pol[l].assign(is_test=False), E.test[l].assign(is_test=True)])
        tramo = pd.cut(t.e365, [0, 0.25, 0.5, 0.75, 0.99, 1.01], labels=['≤0,25', '0,25–0,5', '0,5–0,75', '0,75–0,99', '≈1'])
        det[l] = dict(prima_min=float(t.written_premium.min()), prima_mediana=float(t.written_premium.median()), prima_max=float(t.written_premium.max()),
                      mediana_por_tramo_de_exposicion={str(k): float(v) for k, v in t.groupby(tramo, observed=True).written_premium.median().items()},
                      mediana_por_anio={int(k): float(v) for k, v in t.groupby('year').written_premium.median().items()},
                      mediana_nb_vs_ren_2025={('NB' if k else 'REN'): float(v) for k, v in t[t.is_test].groupby(t[t.is_test].new_business.astype(bool)).written_premium.median().items()},
                      descuento_fuera_0_1=int((~t.discount_applied.between(0, 1)).sum()), descuento_valores=t.discount_applied.round(2).value_counts().head(6).to_dict(),
                      prima_por_cobertura=({k: float(v) for k, v in t.groupby('cover_type').written_premium.median().items()} if l == 'motor' else None))
    plana = all(max(det[l]['mediana_por_tramo_de_exposicion'].values()) / min(det[l]['mediana_por_tramo_de_exposicion'].values()) < 1.15 for l in LINES)
    R.add('VE37', 'Pólizas', 'Prima escrita: positiva, anual (mediana plana por tramo de exposición), por año, nuevo negocio frente a renovación en 2025, descuento en [0, 1]',
          'pasa' if plana and all(det[l]['descuento_fuera_0_1'] == 0 for l in LINES) else 'hallazgo',
          f'prima anual: medianas por tramo de exposición planas en los tres ramos ({plana})', 'anual', 'P2', det, 'VD25')
    # VE38 contactos e impagos
    det = {}
    for l in LINES:
        a, b = E.pol[l], E.test[l]
        acc = E.acc[E.acc.line == l].groupby('row_id').size()
        a = a.assign(n=a.row_id.map(acc).fillna(0))
        det[l] = dict(frecuencia_por_contactos={str(k): round(float(g.n.sum() / g.e365.sum()), 4) for k, g in a.groupby(a.customer_service_contacts.clip(upper=3))},
                      cuota_3_o_mas_train=float((a.customer_service_contacts >= 3).mean()), cuota_3_o_mas_test=float((b.customer_service_contacts >= 3).mean()),
                      impagos_train={str(k): float(v) for k, v in a.missed_payments_12m.value_counts(normalize=True).sort_index().head(5).items()},
                      impagos_test={str(k): float(v) for k, v in b.missed_payments_12m.value_counts(normalize=True).sort_index().head(5).items()},
                      impagos_en_pago_anual_train=float((a[a.payment_method == 'annual'].missed_payments_12m > 0).mean()))
    R.add('VE38', 'Pólizas', 'customer_service_contacts mide el siniestro del propio periodo y cambia en el test; impagos coherentes con el método de pago',
          'hallazgo', f"frecuencia con 3+ contactos {det['motor']['frecuencia_por_contactos'].get('3')} frente a {det['motor']['frecuencia_por_contactos'].get('0')} con 0; 3+ en {det['motor']['cuota_3_o_mas_train']:.1%} del train y {det['motor']['cuota_3_o_mas_test']:.1%} del test",
          'fuera de los predictores', 'P0', det, 'VD23')


# ----------------------------------------------------------------------------------------------- G. siniestros
def g_siniestros(E: Emergente, R: Registro):
    c = E.claims
    det = dict(estado=c.status.value_counts().to_dict(), ramo=c.line.value_counts().to_dict(),
               fuera_de_dominio={k: sorted(set(txt(c[k]).dropna()) - set(v)) for k, v in DOMINIOS['claims'].items()},
               loss_min=c.loss_date.min(), loss_max=c.loss_date.max(), report_min=c.report_date.min(), report_max=c.report_date.max(),
               report_antes_de_loss=int((c.report_date < c.loss_date).sum()), report_despues_del_corte=int((c.report_date > VAL).sum()),
               loss_despues_del_corte=int((c.loss_date > VAL).sum()), loss_antes_de_2023=int((c.loss_date < '2023-01-01').sum()),
               claim_id_formato_CL_8_digitos=bool(c.claim_id.str.fullmatch(r'CL\d{8}').all()), claim_id_longitudes={int(k): int(v) for k, v in c.claim_id.str.len().value_counts().items()},
               repairer_por_peligro={k: float(v) for k, v in c.groupby('peril').repairer_id.apply(lambda s: s.notna().mean()).items()},
               tercero_por_peligro={k: float(v) for k, v in c.groupby('peril').third_party_id.apply(lambda s: s.notna().mean()).items()},
               reportes_el_31_12_2024=int((c.report_date == VAL).sum()), por_anio_de_perdida={int(k): int(v) for k, v in c.loss_date.dt.year.value_counts().sort_index().items()},
               tercero_fuera_de_peligros_de_terceros=int((c.third_party_id.notna() & ~c.peril.isin(['third_party_prop', 'bodily_injury'])).sum()),
               reparador_fuera_de_autos=int((c.repairer_id.notna() & (c.line != 'motor')).sum()),
               reparador_en_danos_propios=float(c[c.peril == 'own_damage'].repairer_id.notna().mean()))
    hall = det['report_antes_de_loss'] + det['report_despues_del_corte'] + det['loss_despues_del_corte'] + sum(len(v) for v in det['fuera_de_dominio'].values()) + det['tercero_fuera_de_peligros_de_terceros'] + det['reparador_fuera_de_autos']
    R.add('VE39', 'Siniestros', 'Dominios y fechas: estado, peligro, ocurrencia ≤ reporte ≤ 31-12-2024; formato de claim_id; reparador y tercero por peligro',
          'hallazgo' if hall else 'pasa', f"{hall} anomalías; {det['loss_antes_de_2023']} ocurrencias anteriores a 2023", '0', 'P0' if hall else '', det, 'VD07')
    # VE40 importes
    cl, op, rp = c[c.status == 'closed'], c[c.status == 'open'], c[c.status == 'repudiated']
    det = dict(pagado_mayor_que_incurrido=int((c.paid_to_date > c.incurred_to_date + 0.005).sum()), recuperaciones_negativas=int((c.recoveries < 0).sum()),
               recuperaciones_mayores_que_incurrido=int((c.recoveries > c.incurred_to_date + 0.005).sum()), pagos_negativos=int((c.paid_to_date < 0).sum()),
               neto_negativo=int((c.net < -0.005).sum()), cerrados_con_reserva=int((cl.incurred_to_date - cl.paid_to_date > 0.005).sum()),
               abiertos_sin_reserva=int((op.incurred_to_date - op.paid_to_date <= 0.005).sum()), abiertos_con_recuperacion=int((op.recoveries > 0).sum()),
               cerrados_con_recuperacion=float((cl.recoveries > 0).mean()), repudiados_con_pago=int((rp.paid_to_date > 0).sum()), repudiados_con_incurrido=int((rp.incurred_to_date > 0).sum()),
               aceptados_con_neto_cero=int(((c.status != 'repudiated') & (c.net.abs() <= 0.005)).sum()),
               recuperacion_cuota_por_peligro={k: round(float(v), 4) for k, v in c[c.status == 'closed'].groupby('peril').apply(lambda g: g.recoveries.sum() / max(g.incurred_to_date.sum(), 1e-9), include_groups=False).items()},
               reserva_de_caso_total=float((op.incurred_to_date - op.paid_to_date).sum()), decimales_mas_de_2=int(((c.incurred_to_date * 100).round(6) % 1 != 0).sum()))
    hall = det['pagado_mayor_que_incurrido'] + det['recuperaciones_negativas'] + det['neto_negativo'] + det['pagos_negativos'] + det['cerrados_con_reserva'] + det['repudiados_con_pago']
    R.add('VE40', 'Siniestros', 'Importes: pagado ≤ incurrido, recuperaciones en [0, incurrido], neto ≥ 0, cerrados sin reserva, abiertos con reserva, rechazados sin pago; recuperaciones solo en cerrados',
          'hallazgo' if hall or det['aceptados_con_neto_cero'] else 'pasa', f"{hall} anomalías de importes; {det['aceptados_con_neto_cero']} aceptados con neto cero; {det['abiertos_con_recuperacion']} abiertos con recuperación",
          '0', 'P1' if hall else 'P2', det, 'VD07', c[((c.status != 'repudiated') & (c.net.abs() <= 0.005)) | (c.paid_to_date > c.incurred_to_date + 0.005)])
    # VE41 asignación
    det = dict(un_periodo=int((c.n_periodos == 1).sum()), ninguno=int((c.n_periodos == 0).sum()), ambiguos=int((c.n_periodos > 1).sum()))
    u = c[c.n_periodos == 0].copy()
    u['dias_antes_del_primer_inicio'] = (u.primer_inicio - u.loss_date).dt.days
    u['despues_del_ultimo_fin'] = u.loss_date > u.ultimo_fin
    # ¿cae en un hueco entre periodos de la misma póliza?
    hueco = []
    for _, r in u.iterrows():
        p = E.pol[r.line]
        pp = p[p.policy_id == r.policy_id].sort_values('period_start')
        en_hueco = bool(((pp.period_end < r.loss_date).any()) and ((pp.period_start > r.loss_date).any()))
        hueco.append(en_hueco)
    u['en_hueco_entre_periodos'] = hueco
    det.update(no_asignados_antes_del_primer_inicio=int((u.dias_antes_del_primer_inicio > 0).sum()), no_asignados_despues_del_ultimo_fin=int(u.despues_del_ultimo_fin.sum()),
               no_asignados_en_hueco=int(sum(hueco)), dias_antes_min=int(u.dias_antes_del_primer_inicio.min()), dias_antes_max=int(u.dias_antes_del_primer_inicio.max()),
               no_asignados_por_estado=u.status.value_counts().to_dict(), no_asignados_neto=float(u.net.sum()),
               reporte_dentro_de_un_periodo_observado=int(sum(((E.pol[r.line].policy_id == r.policy_id) & (E.pol[r.line].period_start <= r.report_date) & (E.pol[r.line].period_end >= r.report_date)).any() for _, r in u.iterrows())))
    # siniestros del 31-12-2024 (día sin cobertura) y de huecos de un día
    det['siniestros_el_31_12_2024'] = int((c.loss_date == VAL).sum())
    ok = det['ambiguos'] == 0 and det['no_asignados_en_hueco'] == 0 and det['no_asignados_despues_del_ultimo_fin'] == 0 and det['ninguno'] == det['no_asignados_antes_del_primer_inicio']
    R.add('VE41', 'Siniestros', 'Asignación por póliza y fecha de ocurrencia: único, ninguno o ambiguo; los no asignados son todos anteriores al primer periodo (ninguno en un hueco ni después del último)',
          'pasa' if ok else 'hallazgo', f"{det['un_periodo']} únicos, {det['ninguno']} ninguno (todos anteriores al primer inicio), {det['ambiguos']} ambiguos", '0 ambiguos', 'P0' if not ok else '', det, 'VD05', u)
    # VE42 peligro frente a cobertura y capital
    a = E.acc
    m = E.pol['motor'][['row_id', 'cover_type']]
    am = a[a.line == 'motor'].merge(m, on='row_id')
    fuera_cover = am[(am.peril.isin(['own_damage', 'theft', 'glass_hail']) & (am.cover_type == 'third_party_only')) | ((am.peril == 'own_damage') & (am.cover_type == 'third_party_fire_theft'))]
    det = dict(autos_peligro_fuera_de_cobertura=len(fuera_cover), autos_fuera_por_combinacion=fuera_cover.groupby(['peril', 'cover_type']).size().to_dict())
    casos = [fuera_cover[['claim_id', 'row_id', 'peril', 'cover_type', 'status', 'net']]]
    for l in HOGAR:
        h = E.pol[l][['row_id', 'accidental_damage_cover', 'sum_insured'] + (['flood_zone'] if False else [])]
        ah = a[a.line == l].merge(h, on='row_id')
        sin_ad = ah[(ah.peril == 'accidental_damage') & ~ah.accidental_damage_cover.astype(bool)]
        sobre = ah[ah.net > ah.sum_insured]
        det[f'{l}_accidental_damage_sin_cobertura'] = len(sin_ad)
        det[f'{l}_accidental_damage_total'] = int((ah.peril == 'accidental_damage').sum())
        det[f'{l}_neto_mayor_que_capital'] = len(sobre)
        det[f'{l}_netos_sobre_el_capital'] = [dict(peligro=str(r.peril), estado=str(r.status), neto=round(float(r.net), 2), capital=float(r.sum_insured))
                                             for r in sobre.sort_values('net', ascending=False).itertuples()]
        ext = ah[ah.sum_insured > {'buildings': 5e6, 'contents': 2e6}[l]]
        det[f'{l}_siniestros_en_filas_de_capital_extremo'] = len(ext)
        det[f'{l}_neto_mayor_que_capital_entre_mil_en_filas_extremas'] = int((ext.net > ext.sum_insured / 1000).sum())
        casos.append(sin_ad[['claim_id', 'row_id', 'peril', 'status', 'net']].assign(line=l))
        casos.append(sobre[['claim_id', 'row_id', 'peril', 'status', 'net', 'sum_insured']].assign(line=l))
    fz = E.addresses.set_index('address_id').flood_zone
    ab = a[a.line == 'buildings'].merge(E.pol['buildings'][['row_id', 'address_id']], on='row_id')
    det['inundacion_por_zona'] = {int(k): int(v) for k, v in ab[ab.peril == 'flood'].address_id.map(fz).value_counts().sort_index().items()}
    hall = det['autos_peligro_fuera_de_cobertura'] + det['buildings_accidental_damage_sin_cobertura'] + det['contents_accidental_damage_sin_cobertura'] + det['buildings_neto_mayor_que_capital'] + det['contents_neto_mayor_que_capital']
    R.add('VE42', 'Siniestros', 'Peligro frente a cobertura: daños propios/robo/lunas sin cobertura completa; daño accidental sin la cobertura opcional; neto mayor que el capital',
          'hallazgo' if hall else 'pasa', f"{det['autos_peligro_fuera_de_cobertura']} autos fuera de cobertura; {det['buildings_accidental_damage_sin_cobertura']} + {det['contents_accidental_damage_sin_cobertura']} daños accidentales sin cobertura; {det['buildings_neto_mayor_que_capital'] + det['contents_neto_mayor_que_capital']} netos sobre el capital",
          '0', 'P1', det, 'VD09', pd.concat(casos))
    # VE43 duplicados de siniestros
    cols = [x for x in c.columns if x not in ('claim_id', 'net', 'delay', 'n_periodos', 'tiene_poliza', 'primer_inicio', 'ultimo_fin')]
    det = dict(iguales_salvo_claim_id=int(c.duplicated(cols).sum()), misma_poliza_peligro_fecha=int(c.duplicated(['policy_id', 'line', 'peril', 'loss_date']).sum()),
               misma_poliza_fecha=int(c.duplicated(['policy_id', 'loss_date']).sum()), claim_id_once_caracteres=int((c.claim_id.str.len() == 11).sum()),
               mismo_importe_y_fecha_distinta_poliza=int(c[c.incurred_to_date > 0].duplicated(['line', 'peril', 'loss_date', 'incurred_to_date']).sum()))
    R.add('VE43', 'Siniestros', 'Duplicados: iguales salvo claim_id (DUP01), misma póliza-peligro-fecha, identificadores de once caracteres',
          'hallazgo' if det['iguales_salvo_claim_id'] or det['misma_poliza_peligro_fecha'] else 'pasa', det, '0', 'P1' if det['iguales_salvo_claim_id'] else '', det, 'VD04',
          c[c.duplicated(['policy_id', 'loss_date'], keep=False)].sort_values(['policy_id', 'loss_date']))
    # VE44 retrasos
    a = E.acc
    det = {}
    for l in LINES:
        s = a[a.line == l]
        det[l] = dict(retraso_mediana=float(s.delay.median()), p90=float(s.delay.quantile(0.9)), max=int(s.delay.max()), mas_de_365=int((s.delay > 365).sum()),
                      mas_de_365_neto=float(s.net[s.delay > 365].sum()),
                      por_peligro={k: dict(n=int(len(g)), mediana=float(g.delay.median()), p90=float(g.delay.quantile(0.9)), max=int(g.delay.max())) for k, g in s.groupby('peril')},
                      mediana_2023=float(s[s.year == 2023].delay.median()), mediana_2024=float(s[s.year == 2024].delay.median()),
                      reportados_ultima_semana_2024=int((s.report_date >= '2024-12-25').sum()), negativos=int((s.delay < 0).sum()))
    R.add('VE44', 'Siniestros', 'Retraso de reporte por ramo y peligro; más de 365 días; truncamiento de 2024 (medianas menores por falta de seguimiento, no por rapidez)',
          'informativo', {l: dict(mediana=det[l]['retraso_mediana'], mas_de_365=det[l]['mas_de_365']) for l in LINES}, '', '', det, 'VD13')
    # VE45 concentración y reservas
    det = {}
    for l in LINES:
        s = a[a.line == l].sort_values('net', ascending=False)
        tot = s.net.sum()
        det[l] = dict(siniestros=len(s), coste=float(tot), top1=float(s.net.iloc[0] / tot), top10=float(s.net.head(10).sum() / tot), top1pct=float(s.net.head(max(1, len(s) // 100)).sum() / tot),
                      abiertos=int((s.status == 'open').sum()), cuota_abiertos_por_peligro={k: round(float(v), 3) for k, v in s.groupby('peril').apply(lambda g: (g.status == 'open').mean(), include_groups=False).items()},
                      reserva_sobre_incurrido={k: round(float(v), 3) for k, v in s.groupby('peril').apply(lambda g: (g.incurred_to_date - g.paid_to_date).sum() / max(g.incurred_to_date.sum(), 1e-9), include_groups=False).items()},
                      maximo=float(s.net.iloc[0]), p999=float(s.net.quantile(0.999)))
    R.add('VE45', 'Siniestros', 'Concentración del coste (mayor siniestro, diez mayores, 1 % superior) y peso de la reserva de caso por peligro',
          'informativo', {l: dict(top10=round(det[l]['top10'], 3), abiertos=det[l]['abiertos']) for l in LINES}, '', '', det, 'VD45')
    # VE46 decisión de renovación y sucesor
    det = {}
    for l in LINES:
        t = pd.concat([E.pol[l].assign(is_test=False), E.test[l].assign(is_test=True)]).sort_values(['policy_id', 'period_start'])
        t['sig'] = t.groupby('policy_id').period_start.shift(-1)
        tr = t[~t.is_test]
        det[l] = {k: dict(filas=int(len(g)), con_periodo_posterior=float(g.sig.notna().mean())) for k, g in tr.groupby(txt(tr.renewal_decision).fillna('NA'))}
        n24 = tr[tr.year == 2024]
        det[l]['2024_con_fila_en_test'] = {k: float(g.sig.notna().mean()) for k, g in n24.groupby(txt(n24.renewal_decision).fillna('NA'))}
    R.add('VE46', 'Pólizas', 'renewal_decision frente a la existencia de un periodo posterior: declined_by_insurer con sucesor, lapsed y cancelled sin él',
          'hallazgo', {l: {k: round(v['con_periodo_posterior'], 3) for k, v in det[l].items() if isinstance(v, dict) and 'con_periodo_posterior' in v} for l in LINES},
          'declined sin sucesor', 'P2', det, 'VD17')


# ----------------------------------------------------------------------------------------------- H. test frente a train
def h_test(E: Emergente, R: Registro):
    det, nuevas = {}, {}
    for l in LINES:
        a, b = E.pol[l], E.test[l]
        d = dict(columnas_solo_train=sorted(set(a.columns) - set(b.columns)), columnas_solo_test=sorted(set(b.columns) - set(a.columns)), categorias_nuevas={}, fuera_de_soporte={})
        for c in b.columns:
            if c in ('row_id', 'policy_id', 'customer_id', 'address_id', 'period_start', 'period_end', 'dias', 'e365', 'year', 'line'):
                continue
            if b[c].dtype == object or str(b[c].dtype).startswith('str'):
                extra = sorted(set(txt(b[c]).dropna()) - set(txt(a[c]).dropna()))
                if extra:
                    d['categorias_nuevas'][c] = extra[:10] + ([f'… {len(extra)} en total'] if len(extra) > 10 else [])
            elif b[c].dtype.kind in 'fi':
                lo, hi = a[c].min(), a[c].max()
                n = int(((b[c] < lo) | (b[c] > hi)).sum())
                if n:
                    d['fuera_de_soporte'][c] = dict(filas=n, min_test=float(b[c].min()), max_test=float(b[c].max()), min_train=float(lo), max_train=float(hi))
        det[l] = d
        nuevas[l] = len(d['categorias_nuevas']) + len(d['fuera_de_soporte'])
    R.add('VE47', 'Test', 'Esquema del test = train sin renewal_decision; categorías del test ausentes en el train; numéricos fuera del soporte del train (renewal_count 17 es estructural)',
          'informativo' if any(nuevas.values()) else 'pasa', {l: dict(categorias_nuevas=list(det[l]['categorias_nuevas']), fuera_de_soporte=list(det[l]['fuera_de_soporte'])) for l in LINES}, '0', 'P1', det, 'VD44')
    # VE48 PSI
    det = {}
    for l in LINES:
        a23, a24, b = E.pol[l][E.pol[l].year == 2023], E.pol[l][E.pol[l].year == 2024], E.test[l]
        cols = [c for c in b.columns if c not in ('row_id', 'policy_id', 'customer_id', 'address_id', 'period_start', 'period_end', 'dias', 'e365', 'year', 'line', 'make_model')]
        det[l] = {c: dict(psi_2023_2024=round(psi(a23[c], a24[c]), 4), psi_2024_2025=round(psi(a24[c], b[c]), 4)) for c in cols}
        # dentro del nuevo negocio: NB 2023-2024 frente a NB 2025
        nb_tr = E.pol[l][E.pol[l].new_business.astype(bool)]
        nb_te = b[b.new_business.astype(bool)]
        det[l]['_nb_2023_2024_vs_nb_2025'] = {c: round(psi(nb_tr[c], nb_te[c]), 4) for c in cols}
    top = {l: sorted(((c, v['psi_2024_2025']) for c, v in det[l].items() if not c.startswith('_')), key=lambda x: -x[1])[:5] for l in LINES}
    R.add('VE48', 'Test', 'Desplazamiento 2024→2025 por columna (PSI) y dentro del nuevo negocio (orgánico 2023–2024 frente a 2025)', 'informativo',
          {l: top[l] for l in LINES}, 'PSI alto solo en lo que explica la cartera nueva', '', det, 'VD43')
    # VE49 nuevo negocio y cartera de enero
    det = {}
    for l in LINES:
        a, b = E.pol[l], E.test[l]
        nb = b.new_business.astype(bool)
        det[l] = dict(nb_filas=float(nb.mean()), nb_exposicion=float(b.exposure[nb].sum() / b.exposure.sum()), nb_enero=float((b.period_start[nb].dt.month == 1).mean()),
                      nb_train_enero=float((a.period_start[a.new_business.astype(bool)].dt.month == 1).mean()),
                      clientes_nuevos=float((~b.customer_id.isin(a.customer_id)).mean()), direcciones_nuevas=float((~b.address_id.isin(a.address_id)).mean()),
                      canal_nb_2025=txt(b[nb].channel).value_counts(normalize=True).round(3).to_dict(), canal_nb_train=txt(a[a.new_business.astype(bool)].channel).value_counts(normalize=True).round(3).to_dict(),
                      renovaciones_test_sin_fila_en_2024=int((~nb & ~b.policy_id.isin(a[a.year == 2024].policy_id)).sum()),
                      nb_con_cliente_ya_visto=int((nb & b.customer_id.isin(a.customer_id)).sum()))
    R.add('VE49', 'Test', 'Nuevo negocio de 2025: cuota, concentración en enero, clientes y direcciones nuevas, canal; renovaciones del test con fila en 2024',
          'informativo', {l: dict(nb=round(det[l]['nb_filas'], 3), enero=round(det[l]['nb_enero'], 3), ren_sin_2024=det[l]['renovaciones_test_sin_fila_en_2024']) for l in LINES}, '', '', det, 'VD43')
    # VE50 plantilla
    s = E.raw['sample_submission']
    cat = pd.concat([E.test[l].row_id for l in LINES], ignore_index=True)
    det = dict(filas=len(s), unicos=bool(s.row_id.is_unique), mismo_conjunto=set(s.row_id) == set(cat), mismo_orden=bool((s.row_id.values == cat.values).all()),
               prediccion_valores=s.prediction.describe().round(4).to_dict(), prediccion_negativas=int((s.prediction < 0).sum()), prediccion_no_finitas=int((~np.isfinite(s.prediction)).sum()))
    ok = det['unicos'] and det['mismo_conjunto'] and det['mismo_orden'] and det['prediccion_negativas'] == 0
    R.add('VE50', 'Entrega', 'Plantilla de envío: 209.063 filas únicas, mismo conjunto y orden que los tres test concatenados, predicciones finitas y no negativas',
          'pasa' if ok else 'hallazgo', det, 'coincide', 'P0' if not ok else '', det, 'VD51')
    # VE51 referencias
    r = E.raw['reference_policies']
    det = dict(filas=len(r), en_test=int(r.row_id.isin(cat).sum()), linea_coherente=bool((r.line == r.row_id.str[0].map({'M': 'motor', 'B': 'buildings', 'C': 'contents'})).all()),
               canal=txt(r.channel).value_counts().to_dict(), nb=int(r.new_business.astype(bool).sum()), exposicion_min=float(r.exposure.min()), menores_de_0_99=int((r.exposure < 0.99).sum()), menores_de_1=int((r.exposure < 1).sum()))
    dif = {}
    for _, x in r.iterrows():
        t = E.test[x.line]
        fila = t[t.row_id == x.row_id]
        if len(fila) != 1:
            dif[x.row_id] = 'no está en el test'
            continue
        fila = fila.iloc[0]
        for col in t.columns:
            if col in r.columns and col not in ('dias', 'e365', 'year', 'line'):
                v1, v2 = x[col], fila[col]
                if col in ('period_start', 'period_end'):
                    v1, v2 = pd.Timestamp(v1), pd.Timestamp(v2)
                if not ((pd.isna(v1) and pd.isna(v2)) or v1 == v2 or (isinstance(v1, float) and isinstance(v2, float) and abs(v1 - v2) < 1e-9)):
                    dif.setdefault(x.row_id, []).append(col)
    det['diferencias_con_el_test'] = dif
    pol_test = E.todas[E.todas.is_test].groupby('policy_id').size()
    det['polizas_con_otra_fila_en_2025'] = {x: int(pol_test[x]) for x in r.policy_id if pol_test.get(x, 0) > 1}
    ok = det['en_test'] == 20 and det['linea_coherente'] and not dif
    R.add('VE51', 'Entrega', 'Veinte referencias: todas en el test con los mismos valores en todas las columnas, ramo coherente con el identificador, canales y exposiciones',
          'pasa' if ok else 'hallazgo', f"{det['en_test']} en test, {len(dif)} con diferencias, {len(det['polizas_con_otra_fila_en_2025'])} pólizas con otra fila en 2025", 'iguales al test', 'P1' if not ok else '', det, 'VD57')
    # VE52 gastos
    x = E.raw['expenses']
    det = dict(items=txt(x.item).tolist(), unidades=txt(x.unit).value_counts().to_dict(), emergente_nulos=txt(x.item)[x.emerging.isna()].tolist(),
               comparison_site_cuota_train=float(sum((E.pol[l].channel == 'comparison_site').sum() for l in LINES) / sum(len(E.pol[l]) for l in LINES)),
               comparison_site_cuota_test=float(sum((E.test[l].channel == 'comparison_site').sum() for l in LINES) / sum(len(E.test[l]) for l in LINES)),
               comparison_site_en_referencias=int((r.channel == 'comparison_site').sum()),
               valores={k: (None if pd.isna(v) else float(v)) for k, v in zip(txt(x.item), x.emerging)})
    R.add('VE52', 'Entrega', 'Tabla de gastos: ocho ítems, unidades, comisión de comparison_site vacía aunque el canal tiene alrededor del 5 % de las filas',
          'hallazgo', f"comparison_site sin comisión; {det['comparison_site_cuota_train']:.1%} del train y {det['comparison_site_cuota_test']:.1%} del test por ese canal; {det['comparison_site_en_referencias']} referencias",
          'todos los canales con valor', 'P2', det, 'VD57')


# ----------------------------------------------------------------------------------------------- I. capas derivadas
def i_derivadas(E: Emergente, args, R: Registro):
    B = args.base
    man = json.load(open(B / 'manifest.json', encoding='utf-8'))
    det, ok, tot = {}, 0, 0
    for f in man['files']:
        p = B / f['path']
        if p.exists():
            tot += 1
            h = sha256(p)
            ok += h == f['sha256']
            det[f['path']] = h == f['sha256']
    ent = {}
    for k, v in man['input_sha256'].items():
        n = k.split('/')[-1].replace('.parquet', '')
        if n in EM_FILES:
            ent[n] = sha256(E.folder / f'{n}.parquet') == v
    R.add('VE53', 'Capas derivadas', 'Corrida base de Codex: huellas de los archivos copiados frente a su manifiesto y de sus entradas frente a los originales',
          'pasa' if ok == tot and all(ent.values()) else 'hallazgo', f'{ok} de {tot} archivos; entradas iguales: {sum(ent.values())} de {len(ent)}', 'todas', 'P0' if ok < tot else '', dict(archivos=det, entradas=ent))
    # VE54 periods
    det, fallos = {}, 0
    fix = pq.read_table(B / 'exposure_changes_609.parquet').to_pandas()
    for l in LINES:
        for kind, orig, name in [('train', E.pol[l], f'periods_policies_{l}'), ('test', E.test[l], f'periods_test_{l}')]:
            per = pq.read_table(B / f'{name}.parquet').to_pandas()
            m = orig.merge(per, on='row_id', suffixes=('', '_c'))
            d = dict(filas=len(per), filas_iguales=len(m) == len(orig) == len(per), columnas_cambiadas=[])
            for c in orig.columns:
                if c in ('dias', 'e365', 'year', 'line', 'exposure'):
                    continue
                cc = c + '_c' if c + '_c' in m.columns else c
                if cc not in m.columns:
                    continue
                v1, v2 = m[c], m[cc]
                if c in ('period_start', 'period_end'):
                    v2 = pd.to_datetime(v2)
                dif = int((~((v1 == v2) | (v1.isna() & v2.isna()))).sum())
                if dif:
                    d['columnas_cambiadas'].append((c, dif))
            d['exposure_original_igual'] = bool(np.allclose(m.exposure, m.exposure_original))
            d['cambios_de_exposicion'] = int((~np.isclose(m.exposure, m.exposure_c)).sum())
            # mi clasificación
            e, dd = orig.exposure, orig.dias
            m365 = np.isclose(e, np.round(dd / 365, 4), atol=5e-5)
            d['mis_filas_fuera_de_365'] = int((~m365).sum())
            d['corregida_igual_a_dias_365'] = bool(np.allclose(m.exposure_c, np.round(m.dias / 365, 4), atol=5e-5))
            if kind == 'train':
                f = fix[fix.line == l]
                d['exposure_changes_coincide_con_mi_lista'] = set(f.row_id) == set(orig.row_id[~m365])
            det[f'{l}_{kind}'] = d
            fallos += len(d['columnas_cambiadas']) + (not d['corregida_igual_a_dias_365']) + (not d.get('exposure_changes_coincide_con_mi_lista', True))
    R.add('VE54', 'Capas derivadas', 'Tablas de periodos de la base: idénticas a los originales salvo la exposición; los 609 cambios son exactamente mis filas fuera de días/365 y quedan en días/365',
          'pasa' if fallos == 0 else 'hallazgo', f'{fallos} discrepancias', '0', 'P0' if fallos else '', det)
    # VE55 T0 por fila
    t0 = pq.read_table(B / 'target_T0_and_stresses.parquet').to_pandas()
    tr = t0[~t0.is_test.astype(bool)].copy()
    te = t0[t0.is_test.astype(bool)]
    mine = E.acc.copy()
    mine['paid_c'] = np.round(mine.paid_to_date * 100).astype(np.int64)
    mine['inc_c'] = np.round(mine.incurred_to_date * 100).astype(np.int64)
    mine['rec_c'] = np.round(mine.recoveries * 100).astype(np.int64)
    g = mine.groupby('row_id').agg(m_paid=('paid_c', 'sum'), m_inc=('inc_c', 'sum'), m_rec=('rec_c', 'sum'), m_n=('claim_id', 'size'),
                                   m_npos=('net', lambda s: int((s > 0.005).sum())), m_nopen=('status', lambda s: int((s == 'open').sum())))
    tr = tr.merge(g, left_on='row_id', right_index=True, how='left').fillna({'m_paid': 0, 'm_inc': 0, 'm_rec': 0, 'm_n': 0, 'm_npos': 0, 'm_nopen': 0})
    tr['inc'], tr['rec'] = tr.m_inc, tr.m_rec
    det = dict(filas_train=len(tr), filas_test=len(te), test_T0_nulo=int(te.T0.isna().sum()) == len(te),
               T0_cents_iguales=int((tr.T0_cents == tr.m_inc - tr.m_rec).sum()), paid_iguales=int((tr.paid_cents == tr.m_paid).sum()), inc_iguales=int((tr.incurred_cents == tr.m_inc).sum()),
               rec_iguales=int((tr.recoveries_cents == tr.m_rec).sum()), n_accepted_iguales=int((tr.n_accepted == tr.m_n).sum()), n_positive_iguales=int((tr.n_positive == tr.m_npos).sum()),
               n_open_iguales=int((tr.n_open == tr.m_nopen).sum()), T0_total=float(tr.T0.sum()), T0_total_mio=float((tr.m_inc - tr.m_rec).sum() / 100),
               T1_075_formula=bool(np.allclose(tr.T1_reserve075, tr.T0 - 0.25 * tr.reserve, atol=0.011)), T1_125_formula=bool(np.allclose(tr.T1_reserve125, tr.T0 + 0.25 * tr.reserve, atol=0.011)),
               T0_igual_a_cents=bool(np.allclose(tr.T0, tr.T0_cents / 100, atol=0.0051)), exposure_igual_a_dias_365=None, filas_con_T0_positivo=int((tr.T0 > 0).sum()),
               estado=txt(t0.target_status).value_counts().to_dict())
    ex = pd.concat([E.pol[l][['row_id', 'dias']] for l in LINES])
    tr2 = tr.merge(ex, on='row_id')
    det['exposure_igual_a_dias_365'] = bool(np.allclose(tr2.exposure, np.round(tr2.dias / 365, 4), atol=5e-5))
    ok = det['T0_cents_iguales'] == len(tr) and det['paid_iguales'] == len(tr) and det['rec_iguales'] == len(tr) and det['n_accepted_iguales'] == len(tr) and det['test_T0_nulo'] and det['T1_075_formula'] and det['exposure_igual_a_dias_365']
    R.add('VE55', 'Capas derivadas', 'T0 de Codex recalculado fila a fila desde los originales (centavos exactos), componentes, conteos, test sin etiquetas, fórmulas T1 y exposición',
          'pasa' if ok else 'hallazgo', f"{det['T0_cents_iguales']} de {len(tr)} filas con T0 idéntico; total {det['T0_total']:,.2f} CU", 'todas iguales', 'P0' if not ok else '', det, 'VD06',
          tr.loc[tr.T0_cents != tr.m_inc - tr.m_rec, ['row_id', 'T0_cents', 'm_inc', 'm_rec']])
    # VE56 36 y auditoría de asignación
    pre = pq.read_table(B / 'precoverage_claims_36.parquet').to_pandas()
    aud = pq.read_table(B / 'claim_assignment_audit.parquet').to_pandas()
    mios = set(E.claims.claim_id[E.claims.n_periodos == 0])
    det = dict(precobertura_coincide=set(pre.claim_id) == mios, n_codex=len(pre), n_mios=len(mios),
               auditoria_filas=len(aud), incluidos_en_T0=int(aud.included_in_T0.astype(bool).sum()), incluidos_esperados=int(((E.claims.n_periodos == 1) & (E.claims.status != 'repudiated')).sum()),
               categorias=txt(aud.audit_assignment).value_counts().to_dict(),
               row_id_coincide=None)
    m = aud[aud.included_in_T0.astype(bool)].merge(E.acc[['claim_id', 'row_id']], on='claim_id', suffixes=('', '_mio'))
    det['row_id_coincide'] = int((m.row_id == m.row_id_mio).sum()) == len(m) == det['incluidos_esperados']
    ok = det['precobertura_coincide'] and det['incluidos_en_T0'] == det['incluidos_esperados'] and det['row_id_coincide']
    R.add('VE56', 'Capas derivadas', 'Los 36 siniestros anteriores a la cobertura y la auditoría de asignación coinciden con mi asignación (mismos claim_id y mismo periodo)',
          'pasa' if ok else 'hallazgo', det, 'coincide', 'P0' if not ok else '', det, 'VD05')
    # VE57 particiones y grupos
    part = pq.read_table(B / 'partitions.parquet').to_pandas()
    ptr = part[~part.is_test.astype(bool)]
    # componentes conexos propios con union-find sobre cliente-dirección en train
    nodos = {}
    def find(x):
        while nodos[x] != x:
            nodos[x] = nodos[nodos[x]]
            x = nodos[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            nodos[rb] = ra
    for cu, ad in zip(ptr.customer_id.values, ptr.address_id.values):
        a_, b_ = 'c:' + cu, 'a:' + ad
        nodos.setdefault(a_, a_)
        nodos.setdefault(b_, b_)
        union(a_, b_)
    comp = pd.Series([find('c:' + cu) for cu in ptr.customer_id.values], index=ptr.index)
    pares = pd.DataFrame(dict(mio=comp.values, codex=ptr.group_id.values))
    det = dict(grupos_codex=int(ptr.group_id.nunique()), grupos_mios=int(comp.nunique()), particion_equivalente=bool(pares.groupby('mio').codex.nunique().max() == 1 and pares.groupby('codex').mio.nunique().max() == 1),
               folds=sorted(ptr.fold.unique().tolist()), filas_por_fold={int(k): int(v) for k, v in ptr.fold.value_counts().sort_index().items()},
               cliente_en_varios_folds=int((ptr.groupby('customer_id').fold.nunique() > 1).sum()), direccion_en_varios_folds=int((ptr.groupby('address_id').fold.nunique() > 1).sum()),
               max_periodos_por_grupo=int(ptr.groupby('group_id').size().max()), test_con_fold=int(part[part.is_test.astype(bool)].fold.notna().sum()),
               roles_temporales=txt(part.temporal_role).value_counts().to_dict())
    pos = E.acc.groupby('row_id').size()
    ptr2 = ptr.assign(pos=ptr.row_id.map(pos).fillna(0) > 0)
    cruce = ptr2.groupby(['line', 'year', 'fold']).pos.sum()
    det['positivos_por_cruce_min'] = int(cruce.min())
    det['positivos_por_cruce_max'] = int(cruce.max())
    # banderas de cliente visto el año anterior
    # banderas de entidad vista el año anterior (todas las filas, incluido el test)
    flags, flags_estricto = {}, {}
    for col, key, same in [('customer_seen_prior_year_same_line', 'customer_id', True), ('address_seen_prior_year_same_line', 'address_id', True),
                           ('customer_seen_prior_year_any_line', 'customer_id', False), ('address_seen_prior_year_any_line', 'address_id', False)]:
        calc_any, calc_prev = np.zeros(len(part), bool), np.zeros(len(part), bool)
        for y in [2024, 2025]:
            prev_any = E.todas[(E.todas.year < y) & ~E.todas.is_test]
            prev_1 = E.todas[(E.todas.year == y - 1) & ~E.todas.is_test]
            for l in LINES:
                msk = ((part.year == y) & (part.line == l)).values
                v_any = set(prev_any[prev_any.line == l][key]) if same else set(prev_any[key])
                v_1 = set(prev_1[prev_1.line == l][key]) if same else set(prev_1[key])
                calc_any[msk] = part.loc[msk, key].isin(v_any).values
                calc_prev[msk] = part.loc[msk, key].isin(v_1).values
        flags[col] = float((calc_any == part[col].astype(bool).values).mean())
        flags_estricto[col] = float((calc_prev == part[col].astype(bool).values).mean())
    det['banderas_vistas_coinciden_con_cualquier_anio_anterior'] = flags
    det['banderas_vistas_coinciden_con_el_anio_inmediatamente_anterior'] = flags_estricto
    det['lectura'] = 'prior_year significa cualquier año anterior de entrenamiento (2023 cuenta para 2025 aunque la entidad falte en 2024)'
    ok = det['particion_equivalente'] and det['cliente_en_varios_folds'] == 0 and det['direccion_en_varios_folds'] == 0 and det['test_con_fold'] == 0 and all(v == 1.0 for v in flags.values())
    R.add('VE57', 'Capas derivadas', 'Particiones: los grupos son los componentes conexos cliente–dirección (recalculados), ningún cliente ni dirección en dos folds, test sin fold, banderas de entidad vista coherentes (vista en cualquier año anterior)',
          'pasa' if ok else 'hallazgo', f"{det['grupos_codex']} grupos (míos {det['grupos_mios']}), equivalentes: {det['particion_equivalente']}; positivos por cruce entre {det['positivos_por_cruce_min']} y {det['positivos_por_cruce_max']}",
          'equivalentes', 'P0' if not ok else '', det, 'VD27')
    # VE58 splits
    det = {}
    pmap = part.set_index('row_id')
    dev_eval_rows, cold_eval_rows = [], []
    for k in range(5):
        dev = pq.read_table(B / f'splits/development_2023_fold{k}.parquet').to_pandas()
        cold = pq.read_table(B / f'splits/cold_2024_fold{k}.parquet').to_pandas()
        es_eval = lambda df: df.role.str.contains('eval|valid|holdout', case=False)
        dv, df_ = dev[es_eval(dev)], dev[~es_eval(dev)]
        cv, cf = cold[es_eval(cold)], cold[~es_eval(cold)]
        dev_eval_rows.append(set(dv.row_id))
        cold_eval_rows.append(set(cv.row_id))
        det[f'development_fold{k}'] = dict(filas=len(dev), ajuste=len(df_), evaluacion=len(dv), anios=sorted(dev.year.unique().tolist()), eval_es_fold_k=bool((dv.fold == k).all()),
                                           ajuste_sin_fold_k=bool((df_.fold != k).all()),
                                           clientes_compartidos=len(set(pmap.loc[dv.row_id].customer_id) & set(pmap.loc[df_.row_id].customer_id)),
                                           direcciones_compartidas=len(set(pmap.loc[dv.row_id].address_id) & set(pmap.loc[df_.row_id].address_id)))
        det[f'cold_fold{k}'] = dict(filas=len(cold), ajuste=len(cf), evaluacion=len(cv), eval_anios=sorted(cv.year.unique().tolist()), fit_anios=sorted(cf.year.unique().tolist()),
                                    eval_es_fold_k=bool((cv.fold == k).all()), ajuste_sin_fold_k=bool((cf.fold != k).all()),
                                    clientes_compartidos=len(set(pmap.loc[cv.row_id].customer_id) & set(pmap.loc[cf.row_id].customer_id)),
                                    direcciones_compartidas=len(set(pmap.loc[cv.row_id].address_id) & set(pmap.loc[cf.row_id].address_id)))
    det['desarrollo_cada_fila_2023_una_vez_en_evaluacion'] = bool(sum(len(s) for s in dev_eval_rows) == len(set().union(*dev_eval_rows)) == int((ptr.year == 2023).sum()))
    det['poblacion_nueva_cada_fila_2024_una_vez_en_evaluacion'] = bool(sum(len(s) for s in cold_eval_rows) == len(set().union(*cold_eval_rows)) == int((ptr.year == 2024).sum()))
    temp = pq.read_table(B / 'splits/temporal_2024.parquet').to_pandas()
    prod = pq.read_table(B / 'splits/production_2025.parquet').to_pandas()
    det['temporal'] = dict(filas=len(temp), roles_por_anio={int(k): txt(g.role).value_counts().to_dict() for k, g in temp.groupby('year')})
    det['production'] = dict(filas=len(prod), roles_por_anio={int(k): txt(g.role).value_counts().to_dict() for k, g in prod.groupby('year')})
    ok = all(det[f'cold_fold{k}']['clientes_compartidos'] == 0 and det[f'cold_fold{k}']['direcciones_compartidas'] == 0 and det[f'development_fold{k}']['clientes_compartidos'] == 0
             and det[f'development_fold{k}']['eval_es_fold_k'] and det[f'cold_fold{k}']['eval_es_fold_k'] and det[f'development_fold{k}']['ajuste_sin_fold_k'] for k in range(5)) \
        and det['desarrollo_cada_fila_2023_una_vez_en_evaluacion'] and det['poblacion_nueva_cada_fila_2024_una_vez_en_evaluacion']
    R.add('VE58', 'Capas derivadas', 'Splits: en los cinco folds de desarrollo y de población nueva la evaluación es el fold k, el ajuste no lo contiene y no comparten clientes ni direcciones; cada fila se evalúa una vez; contraste temporal y producción con sus roles',
          'pasa' if ok else 'hallazgo', f"folds correctos: {ok}; filas de 2023 evaluadas una vez: {det['desarrollo_cada_fila_2023_una_vez_en_evaluacion']}; de 2024: {det['poblacion_nueva_cada_fila_2024_una_vez_en_evaluacion']}", 'sin fugas de identidad', 'P0' if not ok else '', det, 'VD26')
    # VE59 F0
    F = args.f0
    con = json.load(open(F / 'availability_contract.json', encoding='utf-8'))
    det, fallos = {}, 0
    cs = E.customers.set_index('customer_id').customer_since_year
    yb = E.addresses.set_index('address_id').year_built
    prohibidas = {'renewal_decision', 'customer_service_contacts', 'written_premium', 'discount_applied', 'T0', 'prediction', 'claims', 'occupation', 'gender', 'surname'}
    MISSING = '__MISSING__'
    CONSTR = {'BRK': 'brick', 'STN': 'stone', 'WOD': 'timber', 'MIX': 'mixed_or_nonstandard'}
    for l in LINES:
        f0 = pq.read_table(F / f'F0_{l}.parquet').to_pandas()
        orig = pd.concat([E.pol[l].assign(is_test=False), E.test[l].assign(is_test=True)])
        m = orig.merge(f0, on='row_id', suffixes=('', '_f'))
        d = dict(filas=len(f0), filas_coinciden=len(m) == len(orig) == len(f0), predictores=con['blocks'][l]['all'], columnas_x=[c for c in f0.columns if c.startswith('x_')],
                 prohibidas_presentes=sorted({c.replace('x_', '') for c in f0.columns if c.startswith('x_')} & prohibidas), columnas_distintas=[])
        d['contrato_igual_a_columnas'] = set(con['blocks'][l]['all']) == set(d['columnas_x'])
        for c in d['columnas_x']:
            src = c[2:]
            if src in orig.columns:
                v1, v2 = m[src], m[c]
                if v2.dtype.kind in 'fi' and v1.dtype.kind in 'fi':
                    dif = int((~(np.isclose(v1.astype(float), v2.astype(float), equal_nan=True))).sum())
                elif v2.dtype.kind in 'fi':
                    dif = int((~(np.isclose(v1.astype(float), v2.astype(float), equal_nan=True))).sum())
                else:
                    a_, b_ = txt(v1).fillna(MISSING), txt(v2).fillna(MISSING)
                    if src == 'construction_type':
                        a_ = a_.map(lambda s: CONSTR.get(s, s))
                        d['construction_type_mapa'] = CONSTR
                    dif = int((a_ != b_).sum())
                if dif:
                    d['columnas_distintas'].append((c, dif))
            elif src in ('region', 'urban_density', 'flood_zone', 'distance_to_river_km', 'elevation_m', 'bedrooms', 'basement', 'trees_within_5m', 'listed_building', 'solar_panels', 'soil_type', 'property_type', 'roof_type', 'energy_rating'):
                ref = m.address_id.map(E.addresses.set_index('address_id')[src])
                a_, b_ = txt(ref).fillna(MISSING), txt(m[c]).fillna(MISSING)
                if m[c].dtype.kind in 'fi':
                    dif = int((~np.isclose(pd.to_numeric(ref, errors='coerce').astype(float), m[c].astype(float), equal_nan=True)).sum())
                else:
                    dif = int((a_ != b_).sum())
                if dif:
                    d['columnas_distintas'].append((c, dif))
        d['tenure_igual_anio_menos_since'] = bool((m.x_customer_tenure_years == (m.year - m.customer_id.map(cs))).all())
        d['renewal_count_igual_tenure'] = float((m.x_renewal_count == m.x_customer_tenure_years).mean())
        d['start_month_igual'] = bool((m.x_start_month == m.period_start.dt.month).all())
        d['property_age_igual'] = bool(np.allclose(m.x_property_age, m.year - m.address_id.map(yb), equal_nan=True))
        if l in HOGAR:
            nul = m.x_log_sum_insured.isna()
            umbral = {'buildings': 10e6, 'contents': 1e6}[l]
            d['log_capital_nulo'] = int(nul.sum())
            d['log_capital_nulo_es_sobre_filtro'] = bool((nul == (m.sum_insured > umbral)).all())
            d['log_capital_igual_log'] = bool(np.allclose(m.x_log_sum_insured[~nul], np.log(m.sum_insured[~nul])))
        d['categorias_missing'] = {c: int((txt(f0[c]) == MISSING).sum()) for c in d['columnas_x'] if f0[c].dtype == object or str(f0[c].dtype).startswith('str')}
        d['categorias_missing'] = {k: v for k, v in d['categorias_missing'].items() if v}
        d['numericos_nulos'] = {c: int(f0[c].isna().sum()) for c in d['columnas_x'] if f0[c].dtype.kind in 'fi' and f0[c].isna().any()}
        d['predictores_constantes'] = [c for c in d['columnas_x'] if f0[c].nunique(dropna=False) == 1]
        d['predictores_casi_constantes_99'] = {c: float(txt(f0[c]).value_counts(normalize=True, dropna=False).iloc[0]) for c in d['columnas_x'] if txt(f0[c]).value_counts(normalize=True, dropna=False).iloc[0] > 0.99 and c not in d['predictores_constantes']}
        fallos += len(d['columnas_distintas']) + len(d['prohibidas_presentes']) + (not d['contrato_igual_a_columnas']) + (not d['tenure_igual_anio_menos_since']) + (not d['start_month_igual']) + (not d['property_age_igual']) + (not d.get('log_capital_nulo_es_sobre_filtro', True)) + (not d.get('log_capital_igual_log', True))
        det[l] = d
    constantes = {l: det[l]['predictores_constantes'] for l in LINES if det[l]['predictores_constantes']}
    R.add('VE59', 'Capas derivadas', 'Matrices F0: cada predictor igual a su columna de origen (pólizas y direcciones), derivados correctos (antigüedad, mes, edad de la vivienda, log del capital con la máscara), sin columnas excluidas, contrato = columnas; predictores constantes o duplicados',
          'hallazgo' if fallos or constantes else 'pasa', f"{fallos} discrepancias de valores; predictores constantes: {constantes}; x_renewal_count = x_customer_tenure_years en el {det['motor']['renewal_count_igual_tenure']:.0%}",
          'sin discrepancias ni constantes', 'P0' if fallos else ('P2' if constantes else ''), det, 'VD18')
    # VE60 OOF
    oof = pq.read_table(args.oof).to_pandas()
    b00 = oof[oof.model_id == 'W2-B00']
    pm = part.set_index('row_id')
    tm = t0.set_index('row_id')
    det = dict(modelos=sorted(oof.model_id.unique().tolist()), filas_por_modelo=int(len(b00)), filas_2023_train=int((ptr.year == 2023).sum()),
               mismo_conjunto_que_2023=set(b00.row_id) == set(ptr.row_id[ptr.year == 2023]), fold_coincide=bool((b00.fold.values == pm.loc[b00.row_id].fold.values).all()),
               T0_coincide=bool(np.allclose(b00.T0.values, tm.loc[b00.row_id].T0.values, atol=0.0051)), exposure_coincide=bool(np.allclose(b00.exposure.values, tm.loc[b00.row_id].exposure.values)),
               nb_coincide=bool((b00.x_new_business.values == pd.concat([E.pol[l] for l in LINES]).set_index('row_id').loc[b00.row_id].new_business.astype(float).values).all()),
               e_cost_entre_0_y_e=bool(((oof['e_cost_mix_1.0'] >= 0) & (oof['e_cost_mix_1.0'] <= oof.exposure + 1e-9)).all()),
               e_cost_mix_1_sobre_e_min=float((oof['e_cost_mix_1.0'] / oof.exposure).min()), e_cost_mix_1_sobre_e_mediana=float((oof['e_cost_mix_1.0'] / oof.exposure).median()),
               predicciones_positivas_finitas=bool(np.isfinite(oof.prediction).all() and (oof.prediction > 0).all()),
               prediccion_igual_tasa_por_e_cost=float(np.isclose(oof.prediction, oof.annual_rate * oof['e_cost_mix_1.0'], rtol=1e-6).mean()),
               reserve_coincide=bool(np.allclose(b00.reserve.values, tm.loc[b00.row_id].reserve.values, atol=0.0051)))
    ok = det['mismo_conjunto_que_2023'] and det['fold_coincide'] and det['T0_coincide'] and det['exposure_coincide'] and det['nb_coincide'] and det['e_cost_entre_0_y_e'] and det['predicciones_positivas_finitas']
    R.add('VE60', 'Capas derivadas', 'OOF de 2023 (dev3): mismas filas, folds, T0, exposición y nuevo negocio que la base; exposición efectiva C0 en [0, e]; predicciones positivas y finitas',
          'pasa' if ok else 'hallazgo', f"prediction = tasa × e_cost en el {det['prediccion_igual_tasa_por_e_cost']:.1%} de las filas; C0/e mediana {det['e_cost_mix_1_sobre_e_mediana']:.3f}", 'coherente', 'P1' if not ok else '', det)
    # VE61 tablas propias
    cap = pq.read_table(args.capital).to_pandas()
    cua = pq.read_table(F / 'capital_uncertainty_audit.parquet').to_pandas()
    cl = pq.read_table(args.clima).to_pandas()
    w = E.weather.pivot(index='address_id', columns='year', values=['wind_exposure_index', 'wildfire_index', 'rainfall_mm'])
    c25 = cl[cl.year == 2025].set_index('address_id')
    det = dict(capital_filas=len(cap), capital_mismo_conjunto_que_codex=set(cap.row_id) == set(cua.row_id), capital_dividido_x1000=bool(np.allclose(cap.sum_insured_model * 1000, cap.sum_insured_raw)),
               clima_filas=len(cl), clima_direcciones=int(cl.address_id.nunique()), clima_anios=sorted(cl.year.unique().tolist()),
               clima_2025_es_media=bool(np.allclose(c25.x_clima_dir_rainfall_mm, (w[('rainfall_mm', 2023)] + w[('rainfall_mm', 2024)]).reindex(c25.index) / 2)),
               clima_2023_toma_2024=bool(np.allclose(cl[cl.year == 2023].set_index('address_id').x_clima_dir_wind_exposure_index, w[('wind_exposure_index', 2024)].reindex(cl[cl.year == 2023].address_id))))
    ok = all(v for v in det.values() if isinstance(v, bool))
    R.add('VE61', 'Capas derivadas', 'Tablas de las decisiones del participante: los 349 capitales coinciden con la auditoría de Codex; el bloque de clima toma el otro año y la media en 2025',
          'pasa' if ok else 'hallazgo', det, 'coherente', 'P1' if not ok else '', det)


# ----------------------------------------------------------------------------------------------- J. semántica, métrica y límites
def j_limites(E: Emergente, R: Registro):
    t = E.todas
    cs = E.customers.set_index('customer_id').customer_since_year
    nb_test = t[t.is_test & t.new_business.astype(bool)]
    det = dict(nb_test_since_2025=float((nb_test.customer_id.map(cs) == 2025).mean()), previous_insurer_nulo_nb=float(nb_test.customer_id.map(E.customers.set_index('customer_id').previous_insurer).isna().mean()),
               previous_insurer_nulo_renovacion=float(t[~t.new_business.astype(bool)].customer_id.map(E.customers.set_index('customer_id').previous_insurer).isna().mean()),
               campaign_code_nulo=float(E.customers.campaign_code.isna().mean()), years_at_address_distribucion=E.customers.years_at_address.describe().round(2).to_dict())
    R.add('VE62', 'Disponibilidad', 'Maestros sin fecha de versión: la copia actual se asume estable (customer_since_year 2025 en todo el nuevo negocio del test; previous_insurer y campaña sin fecha)',
          'limite', f"ingreso 2025 en el {det['nb_test_since_2025']:.1%} del nuevo negocio del test", 'supuesto declarado', 'P1', det, 'VD19')
    w = E.weather
    det = dict(anios=sorted(w.year.unique().tolist()), diccionario_anuncia='2023–2024 (texto de la página); el archivo trae 2025',
               filas_2025=int((w.year == 2025).sum()))
    R.add('VE63', 'Disponibilidad', 'El clima de 2025 está en el archivo aunque la página anuncia 2023–2024: no es información conocida al cotizar; queda como escenario (CLIMA-S2-01)',
          'limite', det, 'fuera de la base', 'P1', det, 'VD21')
    det = {}
    for l in LINES:
        a = E.pol[l]
        acc = E.acc[E.acc.line == l].groupby('row_id').size()
        a = a.assign(n=a.row_id.map(acc).fillna(0))
        det[l] = dict(frecuencia_por_impagos={str(k): round(float(g.n.sum() / g.e365.sum()), 4) for k, g in a.groupby(a.missed_payments_12m.clip(upper=3))})
        if l == 'buildings':
            det[l]['frecuencia_por_desocupacion'] = {str(k): round(float(g.n.sum() / g.e365.sum()), 4) for k, g in a.groupby(pd.cut(a.days_unoccupied, [-1, 0, 30, 90, 366]), observed=True)}
    R.add('VE64', 'Disponibilidad', 'Contactos, impagos y desocupación no tienen anclaje temporal: contactos fuera (VE38); impagos y desocupación con frecuencia por nivel para decidir',
          'limite', {l: det[l]['frecuencia_por_impagos'] for l in LINES}, 'bloque condicional declarado', 'P1', det, 'VD23')
    det = {l: dict(train_tiene_renewal_decision='renewal_decision' in E.pol[l].columns, test_tiene='renewal_decision' in E.test[l].columns,
                   mid_term_change_filas=int((txt(E.pol[l].renewal_decision) == 'mid_term_change').sum())) for l in LINES}
    R.add('VE65', 'Disponibilidad', 'renewal_decision solo existe en el entrenamiento y describe el final del periodo: nunca predictor (F0 la excluye)',
          'pasa', det, 'excluida', '', det, 'VD24')
    # VE66 prima escrita anual y siniestralidad
    det = {}
    for l in LINES:
        a = E.pol[l]
        a = a.assign(t0=a.row_id.map(E.acc[E.acc.line == l].groupby('row_id').net.sum()).fillna(0))
        det[l] = dict(siniestralidad_sobre_prima_anualizada_por_exposicion={int(y): round(float(g.t0.sum() / (g.written_premium * g.e365).sum()), 3) for y, g in a.groupby('year')},
                      prima_media_por_exposicion={int(y): round(float((g.written_premium * g.e365).sum() / g.e365.sum()), 2) for y, g in a.groupby('year')})
    R.add('VE66', 'Comercial', 'Prima escrita: base anual respaldada por los datos (VE37); siniestralidad observada sobre prima prorrateada por año, sin convertirla en ancla de suficiencia',
          'informativo', {l: det[l]['siniestralidad_sobre_prima_anualizada_por_exposicion'] for l in LINES}, '', '', det, 'VD25')
    # VE67 historial propio dentro de los datos
    det = {}
    for l in LINES:
        a = E.pol[l].sort_values(['policy_id', 'period_start'])
        acc = E.acc[E.acc.line == l].groupby('row_id').size()
        a = a.assign(n=a.row_id.map(acc).fillna(0))
        prev = a.groupby('policy_id').n.shift()
        s24 = a[(a.year == 2024) & prev.notna()]
        pv = prev[s24.index]
        det[l] = dict(filas_2024_con_2023=len(s24), frecuencia_sin_siniestro_previo=round(float(s24[pv == 0].n.sum() / s24[pv == 0].e365.sum()), 4),
                      frecuencia_con_siniestro_previo=round(float(s24[pv > 0].n.sum() / max(s24[pv > 0].e365.sum(), 1e-9)), 4), filas_con_siniestro_previo=int((pv > 0).sum()))
    R.add('VE67', 'Historia', 'Historial propio observable: frecuencia de 2024 según hubiera o no siniestro en 2023 (solo pólizas con los dos años); prior_claims_5y es declaración al ingresar',
          'informativo', {l: dict(sin=det[l]['frecuencia_sin_siniestro_previo'], con=det[l]['frecuencia_con_siniestro_previo']) for l in LINES}, '', '', det, 'VD47')
    # VE68 valoración única
    c = E.claims
    det = dict(valoracion='31-12-2024 única', abiertos=int((c.status == 'open').sum()), abiertos_en_T0=int((E.acc.status == 'open').sum()),
               reserva_de_caso_en_T0=float((E.acc.incurred_to_date - E.acc.paid_to_date).sum()), cuota_reserva_sobre_T0=float((E.acc.incurred_to_date - E.acc.paid_to_date).sum() / E.acc.net.sum()),
               abiertos_por_anio={int(k): int(v) for k, v in E.acc[E.acc.status == 'open'].year.value_counts().sort_index().items()},
               abiertos_sin_pago=int(((E.acc.status == 'open') & (E.acc.paid_to_date == 0)).sum()))
    R.add('VE68', 'Objetivo', 'Una sola valoración al 31-12-2024: reserva de caso dentro de T0, abiertos por año, sin triángulo; el último no está identificado',
          'limite', f"{det['abiertos_en_T0']} abiertos en T0; reserva de caso {det['cuota_reserva_sobre_T0']:.1%} de T0", 'limitación declarada', 'P0', det, 'VD12')
    # VE69 métrica y entrega
    rng = np.random.default_rng(1)
    y = np.concatenate([np.zeros(900), rng.gamma(1.2, 800, 100)])
    mu = rng.gamma(2, 300, 1000)
    p = 1.5
    def dev(y, mu):
        return 2 * (np.power(y, 2 - p) / ((1 - p) * (2 - p)) - y * np.power(mu, 1 - p) / (1 - p) + np.power(mu, 2 - p) / (2 - p))
    d2 = 1 - dev(y, mu).sum() / dev(y, np.full_like(y, y.mean())).sum()
    try:
        from sklearn.metrics import d2_tweedie_score
        d2_sk = float(d2_tweedie_score(y, mu, power=1.5))
    except Exception:
        d2_sk = None
    det = dict(d2_formula_propia=float(d2), d2_sklearn=d2_sk, coincide=(d2_sk is None) or abs(d2 - d2_sk) < 1e-9,
               identidad_escala_e=bool(np.isclose(dev(2 * y, 2 * mu).sum(), 2 ** (2 - p) * dev(y, mu).sum())))
    R.add('VE69', 'Métrica', 'Métrica: la fórmula propia de D² Tweedie 1,5 coincide con scikit-learn; identidad de escala d(e·r, e·q) = e^(2−p) d(r, q); entrega en CU por fila ≥ 0',
          'pasa' if det['coincide'] and det['identidad_escala_e'] else 'hallazgo', det, 'coincide', '', det, 'VD50')
    # VE70 tendencia por año
    det = {}
    for l in LINES:
        a = E.pol[l]
        acc = E.acc[E.acc.line == l]
        det[l] = {int(y): dict(frecuencia=round(float(acc[acc.year == y].shape[0] / a[a.year == y].e365.sum()), 4), severidad_media=round(float(acc[acc.year == y].net.mean()), 1),
                               severidad_mediana=round(float(acc[acc.year == y].net.median()), 1), prima_pura=round(float(acc[acc.year == y].net.sum() / a[a.year == y].e365.sum()), 2)) for y in [2023, 2024]}
    R.add('VE70', 'Tendencia', 'Frecuencia, severidad y prima pura observadas por año (2024 truncado por reporte y desarrollo): sin estimar inflación como pendiente',
          'informativo', {l: {y: det[l][y]['prima_pura'] for y in det[l]} for l in LINES}, '', '', det, 'VD46')
    # VE72 nulos del 12 % por segmento
    det = {}
    a = E.addresses
    nulcols_a = [c for c in a.columns if a[c].isna().any()]
    det['direcciones_nulos_por_columna'] = {c: round(float(a[c].isna().mean()), 4) for c in nulcols_a}
    det['direcciones_nulos_por_region'] = {r: {c: round(float(g[c].isna().mean()), 4) for c in nulcols_a[:4]} for r, g in a.groupby('region')}
    det['direcciones_filas_con_algun_nulo'] = float(a[nulcols_a].isna().any(axis=1).mean()) if nulcols_a else 0.0
    det['direcciones_nulos_independientes'] = {f'{c1}~{c2}': round(float(a[c1].isna().corr(a[c2].isna())), 3) for i, c1 in enumerate(nulcols_a[:5]) for c2 in nulcols_a[i + 1:5]}
    seg = {}
    for l in LINES:
        tt = pd.concat([E.pol[l].assign(is_test=False), E.test[l].assign(is_test=True)])
        tt = tt.merge(a[['address_id'] + nulcols_a], on='address_id', how='left')
        nulcols_p = [c for c in tt.columns if tt[c].isna().any() and c not in ('renewal_decision',)]
        seg[l] = {}
        for nombre, msk in [('2023', (tt.year == 2023)), ('2024', (tt.year == 2024)), ('2025_renovacion', tt.is_test & ~tt.new_business.astype(bool)), ('2025_nb', tt.is_test & tt.new_business.astype(bool))]:
            seg[l][nombre] = {c: round(float(tt.loc[msk, c].isna().mean()), 4) for c in nulcols_p}
    det['polizas_y_direcciones_por_segmento'] = seg
    maxdif = max(abs(seg[l]['2025_nb'][c] - seg[l]['2024'][c]) for l in LINES for c in seg[l]['2024'])
    det['max_diferencia_nb_2025_frente_a_2024'] = float(maxdif)
    R.add('VE72', 'Faltantes', 'Los nulos del 12 % en direcciones y pólizas: por región, por año y en la cartera nueva de 2025; correlación entre ausencias (¿estructurales, aleatorias o desplazadas?)',
          'informativo' if maxdif < 0.03 else 'hallazgo', f"filas de direcciones con algún nulo: {det['direcciones_filas_con_algun_nulo']:.1%}; mayor cambio de la cuota de nulos en el nuevo negocio de 2025 frente a 2024: {maxdif:.3f}",
          'misma cuota en todos los segmentos', 'P1' if maxdif >= 0.03 else '', det, 'VD41')
    # VE73 mezcla por región y densidad en 2024 frente a 2025
    det = {}
    reg = E.addresses.set_index('address_id')
    for l in LINES:
        a24, b = E.pol[l][E.pol[l].year == 2024], E.test[l]
        det[l] = dict(region_2024=txt(a24.address_id.map(reg.region)).value_counts(normalize=True).round(3).to_dict(), region_2025=txt(b.address_id.map(reg.region)).value_counts(normalize=True).round(3).to_dict(),
                      psi_region=round(psi(txt(a24.address_id.map(reg.region)), txt(b.address_id.map(reg.region))), 4),
                      psi_densidad=round(psi(txt(a24.address_id.map(reg.urban_density)), txt(b.address_id.map(reg.urban_density))), 4),
                      psi_zona_inundacion=round(psi(a24.address_id.map(reg.flood_zone), b.address_id.map(reg.flood_zone)), 4))
    R.add('VE73', 'Test', 'Mezcla geográfica 2024→2025: región, densidad urbana y zona de inundación de las direcciones aseguradas', 'informativo',
          {l: dict(psi_region=det[l]['psi_region'], psi_densidad=det[l]['psi_densidad']) for l in LINES}, '', '', det, 'VD43')
    R.add('VE74', 'Revisión', 'Alcance: controles propios de IA sobre copias con huella; no son revisión profesional independiente ni aprobación de la base',
          'limite', 'revisión de IA', 'revisión humana pendiente', 'P1', {}, 'VD54')


# ----------------------------------------------------------------------------------------------- main
def main(a):
    t0 = time.time()
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / 'tablas').mkdir(exist_ok=True)
    R = Registro(a.privado)

    def log(m):
        print(f'[{time.time() - t0:6.0f} s] {m}', flush=True)

    log('cargando emergente')
    E = Emergente(a.emerging)
    log('cargando desarrollado (parcial)')
    D = Desarrollado(a.developed)
    for nombre, fn in [('A integridad', lambda: a_integridad(E, D, a, R)), ('B relaciones', lambda: b_relaciones(E, D, R)),
                       ('C calendario', lambda: c_calendario(E, R)), ('D clientes', lambda: d_clientes(E, D, R)),
                       ('E direcciones y clima', lambda: e_direcciones_clima(E, D, R)), ('F pólizas', lambda: f_polizas(E, D, R, a)),
                       ('G siniestros', lambda: g_siniestros(E, R)), ('H test', lambda: h_test(E, R)),
                       ('I capas derivadas', lambda: i_derivadas(E, a, R)), ('J límites', lambda: j_limites(E, R))]:
        log(nombre)
        fn()
    tabla = pd.DataFrame(R.controles)
    tabla.to_csv(a.out / 'tablas' / 'controles.csv', index=False)
    resumen = dict(controles=len(tabla), por_resultado=tabla.resultado.value_counts().to_dict(), por_area=tabla.groupby('area').resultado.value_counts().unstack(fill_value=0).to_dict(orient='index'),
                   hallazgos=[dict(id=r.id, severidad=r.severidad, titulo=r.titulo, observado=r.observado, n_casos=r.n_casos) for r in tabla[tabla.resultado == 'hallazgo'].itertuples()],
                   limites=[dict(id=r.id, titulo=r.titulo) for r in tabla[tabla.resultado == 'limite'].itertuples()])
    ev = dict(autor='Claude (Cowork)', utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
              entorno=dict(python=platform.python_version(), pandas=pd.__version__, numpy=np.__version__, pyarrow=pyarrow.__version__, scipy=scipy.__version__),
              resumen=resumen, controles=R.controles, detalle=R.ev, segundos=round(time.time() - t0))
    (a.out / 'evidencia_validacion.json').write_text(json.dumps(to_py(ev), ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    log(f'{len(tabla)} controles: {resumen["por_resultado"]}')
    if not a.sin_figuras:
        import figuras_validacion
        figuras_validacion.dibujar(a.out, E, a.developed)
    salidas = sorted(x for x in a.out.rglob('*') if x.is_file() and '__pycache__' not in x.parts and not x.name.startswith('verificacion_') and x.name != 'manifiesto.json')
    man = dict(autor='Claude (Cowork)', utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
               scripts={x.name: sha256(x) for x in sorted(AQUI.glob('*.py'))},
               entradas={**{f'emerging/{n}': sha256(a.emerging / f'{n}.parquet') for n in EM_FILES}, **{f'developed/{n}': sha256(a.developed / f'{n}.parquet') for n in DEV_FILES},
                         'codex/base/manifest.json': sha256(a.base / 'manifest.json'), 'codex/f0/availability_contract.json': sha256(a.f0 / 'availability_contract.json'), 'codex/dev3/oof_2023.parquet': sha256(a.oof)},
               salidas={str(x.relative_to(a.out)).replace('\\', '/'): sha256(x) for x in salidas},
               privado={x.name: sha256(x) for x in sorted(a.privado.glob('*.parquet'))})
    (a.out / 'manifiesto.json').write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding='utf-8')
    log('hecho')


if __name__ == '__main__':
    raiz = AQUI.parents[3] if len(AQUI.parents) > 3 else AQUI
    s2 = raiz / 'Hackaton/Semana 2'
    rep = raiz / 'Hackaton/Repositorio_IAA2026'
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--emerging', type=pathlib.Path, default=s2 / 'Datos/emerging')
    ap.add_argument('--developed', type=pathlib.Path, default=raiz / 'Hackaton/Semana 1/Datos')
    ap.add_argument('--manifest-em', type=pathlib.Path, default=s2 / 'Codex/fuentes/download_manifest.json')
    ap.add_argument('--listado-kaggle', type=pathlib.Path, default=s2 / 'Codex/fuentes/file_listing.json')
    ap.add_argument('--pagina', type=pathlib.Path, default=s2 / 'Codex/fuentes/pages_response.json')
    ap.add_argument('--base', type=pathlib.Path, default=rep / 'privado/semana2/preparacion/base_20261023T164102Z_b3e6c2a3')
    ap.add_argument('--f0', type=pathlib.Path, default=rep / 'privado/semana2/ultimo/f0_ultimo_20261023T170841Z_82038766')
    ap.add_argument('--oof', type=pathlib.Path, default=rep / 'privado/semana2/desarrollo2023/dev3_20261023T181613Z_24c943a3/oof_2023.parquet')
    ap.add_argument('--capital', type=pathlib.Path, default=rep / 'privado/semana2/decisiones_participante_20261023/capital_caps2_01.parquet')
    ap.add_argument('--clima', type=pathlib.Path, default=rep / 'privado/semana2/decisiones_participante_20261023/clima_direccion_s2_01.parquet')
    ap.add_argument('--out', type=pathlib.Path, default=AQUI)
    ap.add_argument('--privado', type=pathlib.Path, default=rep / 'privado/semana2/validacion_datos_claude_20261023')
    ap.add_argument('--sin-figuras', action='store_true')
    main(ap.parse_args())
