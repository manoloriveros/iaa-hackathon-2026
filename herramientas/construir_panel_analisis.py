"""EDA de ambas semanas desde originales. No entrena ni carga modelos.

python herramientas/construir_panel_analisis.py --raiz C:/dev/Hakaton
Las filas de auditoría se escriben solo en privado; el panel recibe agregados.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = REPO.parents[1]
sys.path.insert(0, str(DEFAULT_ROOT / 'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

LINES = ('motor', 'buildings', 'contents')
MONEY = ('paid', 'incurred', 'recoveries', 'reserve', 'T0')


def read_json(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def write_json(p, x):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, ensure_ascii=False, indent=1, allow_nan=False,
        default=lambda v: v.item() if hasattr(v, 'item') else str(v)) + '\n', encoding='utf-8')


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def require(ok, label):
    if not bool(ok):
        raise ValueError(label)


def cents(s):
    a = s.to_numpy(dtype=float)
    require(np.isfinite(a).all(), 'Dinero no finito')
    b = np.rint(a * 100)
    require(np.max(np.abs(a * 100 - b), initial=0) < 1e-5, 'Dinero fuera de centavos')
    return b.astype('int64')


def build(root: Path):
    routes = read_json(root / 'RUTAS_PROYECTO.json')
    output = REPO / 'docs/entrega/analisis'
    output.mkdir(parents=True, exist_ok=True)
    run = REPO / 'privado/panel_analisis' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run.mkdir(parents=True, exist_ok=False)
    sources, controls = [], []

    def check(label, ok, detail=None):
        controls.append({'control': label, 'pasa': bool(ok), 'detalle': detail})
        require(ok, label)

    def source(p, expected=None, role='original'):
        p = Path(p)
        h = sha(p)
        if expected:
            check('SHA ' + p.relative_to(root).as_posix(), h == expected)
        sources.append({'ruta': p.relative_to(root).as_posix(), 'sha256': h, 'rol': role})
        return p

    source(REPO / 'registro/panel_analisis_plan.json', role='plan_previo')
    source(Path(__file__), role='productor')
    rules = read_json(REPO / 'src/datos/n62_codex/rules.json')
    s2_plan = read_json(REPO / 'registro/semana2_preparacion_plan.json')
    manifest_path = source(root / s2_plan['input_manifest_workspace_relative'], role='manifiesto')
    m2 = {x['local_path'].split('/')[-1]: x['sha256'] for x in read_json(manifest_path)['files']}
    bases = {'developed': root / routes['week_1_data'], 'emerging': root / routes['week_2_emerging_data']}
    for market, base in bases.items():
        hashes = rules['originals_sha256'] if market == 'developed' else m2
        for p in sorted(base.glob('*.parquet')):
            require(p.name in hashes, 'Original sin manifiesto: ' + p.name)
            source(p, hashes[p.name])
    # La copia desarrollada de semana 2 es referencia, no un tercer mercado.
    reference = root / routes['week_2_data']
    for name, expected in rules['originals_sha256'].items():
        source(reference / name, expected, 'copia_referencia_desarrollado')

    portfolio, missingness, distributions, perils, quality, schemas = [], [], [], [], [], []
    periods_all, claims_all = [], []
    for market, base in bases.items():
        print('Leyendo', market, flush=True)
        customers = pq.read_table(base / 'customers.parquet').to_pandas()
        addresses = pq.read_table(base / 'addresses.parquet').to_pandas()
        customers['customer_id'] = customers.customer_id.astype('string').str.zfill(8)
        check(market + ': clientes únicos', customers.customer_id.is_unique)
        check(market + ': direcciones únicas', addresses.address_id.is_unique)
        period_parts = []
        for line in LINES:
            line_frames = []
            for kind in ['policies', 'test']:
                table = f'{kind}_{line}'
                f = pq.read_table(base / (table + '.parquet')).to_pandas()
                schemas.append({'market': market, 'table': table, 'fields': list(f.columns)})
                f['customer_id'] = f.customer_id.astype('string').str.zfill(8)
                check(f'{market}/{table}: row_id único', f.row_id.is_unique and f.row_id.notna().all())
                check(f'{market}/{table}: clientes enlazados', f.customer_id.isin(customers.customer_id).all())
                check(f'{market}/{table}: direcciones enlazadas', f.address_id.isin(addresses.address_id).all())
                for col in ['period_start', 'period_end']:
                    f[col] = pd.to_datetime(f[col])
                f['year'] = f.period_start.dt.year
                f['line'] = line
                f['market'] = market
                f['is_test'] = kind == 'test'
                check(f'{market}/{table}: años y cortes', f.year.isin([2025] if kind == 'test' else ([2021, 2022, 2023, 2024] if market == 'developed' else [2023, 2024])).all() and f.period_end.dt.year.eq(f.year).all())
                days = (f.period_end - f.period_start).dt.days + 1
                check(f'{market}/{table}: duraciones', days.between(1, 366).all())
                f['exposure_raw'] = f.exposure
                f['exposure'] = (days / 365).round(4)
                f['exposure_changed'] = ~np.isclose(f.exposure_raw, f.exposure, rtol=0, atol=1e-7)
                # Comparación ponderada por pólizas, no por el padrón de clientes.
                for year, cohort in f.groupby('year', sort=True):
                    for origin, frame in [('policies', cohort), ('customers', customers.reindex(columns=customers.columns).set_index('customer_id').reindex(cohort.customer_id)), ('addresses', addresses.set_index('address_id').reindex(cohort.address_id))]:
                        ignored = {'row_id','policy_id','customer_id','address_id','surname','email_domain','market','line','year','is_test','exposure_raw','exposure_changed'}
                        for field in frame.columns:
                            if field in ignored:
                                continue
                            miss = int(frame[field].isna().sum())
                            missingness.append({'market': market, 'line': line, 'year': int(year), 'table': origin, 'field': field, 'n': len(cohort), 'missing': miss})
                    for feature in ['channel', 'new_business', 'cover_type', 'driver_age_band', 'policyholder_age_band']:
                        if feature not in cohort:
                            continue
                        s = cohort[feature].astype('string').fillna('(ausente)')
                        for category, n in s.value_counts().items():
                            distributions.append({'market': market, 'line': line, 'year': int(year), 'feature': feature, 'category': str(category), 'n': int(n)})
                keep = ['market','line','year','is_test','row_id','policy_id','customer_id','address_id','period_start','period_end','exposure','exposure_raw','exposure_changed','new_business']
                line_frames.append(f[keep].copy())
                del f
                gc.collect()
            lf = pd.concat(line_frames, ignore_index=True)
            order = lf.sort_values(['policy_id','period_start'])
            prior_end = order.groupby('policy_id').period_end.shift()
            check(f'{market}/{line}: periodos sin solapar', not prior_end.ge(order.period_start).any())
            lf['known_customer'] = False
            for year in sorted(lf.year.unique()):
                prior = lf.loc[lf.year.lt(year), 'customer_id']
                mask = lf.year.eq(year)
                lf.loc[mask, 'known_customer'] = lf.loc[mask,'customer_id'].isin(prior)
            period_parts.append(lf)
        p = pd.concat(period_parts, ignore_index=True)
        check(market + ': row_id global único', p.row_id.is_unique)
        expected_sample = pq.read_table(base/'sample_submission.parquet', columns=['row_id']).column('row_id').to_pylist()
        check(market + ': orden y conjunto sample/test', p.loc[p.is_test, 'row_id'].tolist() == expected_sample)
        c_raw = pq.read_table(base/'claims.parquet').to_pandas()
        payload = [x for x in c_raw.columns if x != 'claim_id']
        duplicate_mask = c_raw.duplicated(payload, keep=False)
        if market == 'developed':
            pairs = c_raw.loc[duplicate_mask].groupby(payload, dropna=False, sort=False).claim_id.agg(list)
            excluded, aliases = [], []
            for ids in pairs:
                short = [x for x in ids if len(x) == 10]
                long = [x for x in ids if len(x) == 11]
                require(len(ids) == 2 and len(short) == len(long) == 1, 'DUP01: par fuera del contrato')
                aliases.append((short[0],long[0]))
                excluded.extend(long)
            fingerprint = hashlib.sha256(('\n'.join('|'.join(x) for x in sorted(aliases))+'\n').encode()).hexdigest()
            # Se coteja además la lista efectiva contra la capa histórica más abajo.
            check('DUP01: 604 copias de payload', len(excluded) == rules['DUP01']['count'])
            c = c_raw.loc[~c_raw.claim_id.isin(excluded)].copy()
        else:
            excluded = []
            check('Emergente: sin payload duplicado', not duplicate_mask.any())
            c = c_raw.copy()
        check(market + ': IDs siniestros únicos', c.claim_id.is_unique)
        check(market + ': estados conocidos', c.status.isin(['closed','open','repudiated']).all())
        for field in ['loss_date','report_date']:
            c[field] = pd.to_datetime(c[field])
        check(market + ': fechas reporte', c.report_date.ge(c.loss_date).all() and c.report_date.le(pd.Timestamp('2024-12-31')).all())
        c['_pos'] = np.arange(len(c))
        join = c[['_pos','line','policy_id','loss_date']].merge(p[['line','policy_id','row_id','period_start','period_end']], on=['line','policy_id'], how='left')
        matches = join.loc[join.loss_date.between(join.period_start,join.period_end)]
        check(market + ': asignación sin ambigüedad', matches._pos.is_unique)
        c['row_id'] = c._pos.map(matches.set_index('_pos').row_id)
        first = p.groupby(['line','policy_id']).period_start.min()
        c['first_start'] = pd.MultiIndex.from_frame(c[['line','policy_id']]).map(first)
        c['precoverage'] = c.row_id.isna() & c.loss_date.lt(c.first_start)
        check(market + ': exclusiones explicadas', (c.row_id.notna() | c.precoverage).all())
        c['included'] = c.row_id.notna() & c.status.ne('repudiated')
        c['market'] = market
        c['year'] = c.loss_date.dt.year
        c['delay_days'] = (c.report_date-c.loss_date).dt.days
        for col, raw in [('paid','paid_to_date'),('incurred','incurred_to_date'),('recoveries','recoveries')]:
            c[col+'_cents'] = cents(c[raw])
        c['reserve_cents'] = c.incurred_cents-c.paid_cents
        c['T0_cents'] = c.incurred_cents-c.recoveries_cents
        check(market + ': componentes no negativos', c[[x+'_cents' for x in MONEY]].ge(0).all().all())
        a = c.loc[c.included].copy()
        a['accepted'] = 1
        a['positive'] = a.T0_cents.gt(0).astype('int64')
        a['open'] = a.status.eq('open').astype('int64')
        target = a.groupby('row_id')[[x+'_cents' for x in MONEY]+['accepted','positive','open']].sum()
        t = p.merge(target, left_on='row_id',right_index=True,how='left',validate='one_to_one')
        for col in list(target.columns):
            t[col] = t[col].where(t.is_test, t[col].fillna(0)).astype('Int64')
        check(market + ': etiquetas test ausentes', t.loc[t.is_test,'T0_cents'].isna().all())
        check(market + ': todas las etiquetas train', t.loc[~t.is_test,'T0_cents'].notna().all())
        # Cotejo por fila con el objetivo previo, no solo su gran total.
        if market == 'developed':
            index_path = source(root/'Hackaton/Semana 1/Bases_actuariales_claude/current_run.json',role='indice_objetivo')
            idx = read_json(index_path)
            old_path = root/'Hackaton/Semana 1/Bases_actuariales_claude'/idx['t0']['table']
            old = pq.read_table(source(old_path,role='objetivo_existente')).to_pandas()
            old['T0_cents'] = cents(old.T0)
            old = old[['row_id','T0_cents','exposure']]
            catalog_idx=read_json(root/'Hackaton/Semana 1/Limpieza/current_dataset.json')
            catalog=read_json(root/catalog_idx['catalog_workspace_relative'])
            cp=root/catalog['claims']['workspace_relative_path']
            historic_ids=pq.read_table(source(cp,catalog['claims']['sha256'],'siniestros_preparados'),columns=['claim_id']).column('claim_id').to_pylist()
            check('DUP01: mismos representantes históricos', set(c.claim_id) == set(historic_ids))
        else:
            index_path=source(root/routes['week_2_preparation_index'],role='indice_objetivo')
            idx=read_json(index_path)
            old=pq.read_table(source(root/idx['target'],idx['target_sha256'],'objetivo_existente')).to_pandas()
            old=old.loc[~old.is_test,['row_id','T0_cents','exposure']]
        comparison=t.loc[~t.is_test,['row_id','T0_cents','exposure']].merge(old,on='row_id',suffixes=('_new','_old'),validate='one_to_one')
        check(market+': mismos periodos que objetivo previo',len(comparison)==len(old)==int((~t.is_test).sum()))
        check(market+': T0 idéntico por fila en centavos',comparison.T0_cents_new.eq(comparison.T0_cents_old).all())
        check(market+': exposición idéntica a capa previa',np.allclose(comparison.exposure_new,comparison.exposure_old,rtol=0,atol=1e-12))
        for (line,year),g in t.groupby(['line','year'],sort=True):
            is_test=bool(g.is_test.iloc[0])
            row={'market':market,'line':line,'year':int(year),'is_test':is_test,'rows':len(g),
                 'exposure':float(g.exposure.sum()),'exposure_raw':float(g.exposure_raw.sum()),'exposure_changed':int(g.exposure_changed.sum()),
                 'new_business':int(g.new_business.sum()),'known_customers':int(g.known_customer.sum())}
            for col in [x+'_cents' for x in MONEY]+['accepted','positive','open']:
                row[col]=None if is_test else int(g[col].sum())
            row['positive_periods']=None if is_test else int(g.T0_cents.gt(0).sum())
            portfolio.append(row)
        for (line,year,peril),g in a.groupby(['line','year','peril'],sort=True):
            perils.append({'market':market,'line':line,'year':int(year),'peril':peril,'claims':len(g),
                'T0_cents':int(g.T0_cents.sum()),'reserve_cents':int(g.reserve_cents.sum()),'open':int(g.open.sum()),
                'delay_median':float(g.delay_days.median()),'delay_p90':float(g.delay_days.quantile(.9)),
                'delay_over90':int(g.delay_days.gt(90).sum())})
        quality.append({'market':market,'raw_claims':len(c_raw),'duplicate_copies':len(excluded),'unique_claims':len(c),
            'precoverage':int(c.precoverage.sum()),'repudiated_assigned':int((c.row_id.notna()&c.status.eq('repudiated')).sum()),
            'included':int(c.included.sum()),'open':int(a.open.sum()),'zero_accepted':int(a.T0_cents.eq(0).sum()),
            'excluded_precoverage_T0_cents':int(c.loc[c.precoverage,'T0_cents'].sum()),
            'last_report':str(c.report_date.max().date()),'train_exposure_changes':int(t.loc[~t.is_test,'exposure_changed'].sum()),
            'test_exposure_changes':int(t.loc[t.is_test,'exposure_changed'].sum())})
        periods_all.append(t)
        claims_all.append(c[['market','line','year','claim_id','row_id','peril','status','precoverage','included','delay_days']+[x+'_cents' for x in MONEY]])
        del customers,addresses,p,c,c_raw,a,t,comparison,old
        gc.collect()
    pd.concat(periods_all,ignore_index=True).to_parquet(run/'periodos_auditados.parquet',index=False)
    pd.concat(claims_all,ignore_index=True).to_parquet(run/'siniestros_auditados.parquet',index=False)
    # Esquemas adicionales: ausencia estructural separada de nulos.
    for market,base in bases.items():
        for name in ['customers','addresses','weather']:
            schemas.append({'market':market,'table':name,'fields':pq.ParquetFile(base/(name+'.parquet')).schema_arrow.names})
    expenses=pq.read_table(bases['emerging']/'expenses.parquet').to_pandas()
    expenses=expenses.astype(object).where(expenses.notna(),None).to_dict('records')
    refs=pq.read_table(bases['emerging']/'reference_policies.parquet',columns=['line']).to_pandas().line.value_counts().to_dict()
    d={'version':1,'autor':'Codex','generado_utc':datetime.now(timezone.utc).isoformat(),'corte_valoracion':'2024-12-31',
       'alcance':'EDA local de los dos mercados, sin entrenamiento ni inferencia. T0 observado, no último.',
       'environment':{'python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__,'pyarrow':pa.__version__},
       'portfolio':portfolio,'perils':perils,'missingness':missingness,'distributions':distributions,
       'quality':quality,'schemas':schemas,'expenses':expenses,'reference_policy_counts':refs,'sources':sources,
       'validation':{'controls':len(controls),'failed':0,'same_T0_per_row':True,'independent_professional_review':False},
       'private_run':run.relative_to(root).as_posix()}
    write_json(run/'controles_productor.json',controls)
    write_json(run/'agregados.json',d)
    write_json(output/'datos_panel.json',d)
    template=(REPO/'docs/entrega/web/analisis_plantilla.html').read_text(encoding='utf-8')
    encoded=json.dumps(d,ensure_ascii=False,allow_nan=False).replace('</','<\\/')
    (REPO/'docs/entrega/panel_analisis.html').write_text(template.replace('__ANALYSIS_DATA__',encoded),encoding='utf-8')
    write_json(REPO/'registro/panel_analisis_actual.json',{'id':'PANEL-DATOS-S1-S2-20261026','autor':'Codex','run':run.relative_to(root).as_posix(),
        'panel':'docs/entrega/panel_analisis.html','data':'docs/entrega/analisis/datos_panel.json','data_sha256':sha(output/'datos_panel.json'),
        'estado':'construido_pendiente_validacion_separada','controls':len(controls),'trained':False,'inference':False,'submissions':False})
    print(json.dumps({'run':str(run),'controls':len(controls),'cohorts':len(portfolio),'T0_cents':{m:sum(x['T0_cents'] or 0 for x in portfolio if x['market']==m) for m in bases}},ensure_ascii=False))


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--raiz',type=Path,default=DEFAULT_ROOT)
    build(ap.parse_args().raiz.resolve())
