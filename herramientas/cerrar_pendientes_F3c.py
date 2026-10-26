"""Batería local de los doce pendientes. No envía, publica ni selecciona.

Los contrastes trasladan la receta de factores, no las predicciones de producción
F3c que se ajustaron con ambos años. Todo 2024 sigue siendo exploratorio.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import shutil
import sys
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP, localcontext
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parents[1]
DATA = ROOT / 'Hackaton/Semana 2/Datos/emerging'
SRC = REPO / 'src/semana2/lineas/mision017_20261025'
WORK = REPO / 'privado/reproduccion_m017/20261026 entorno nuevo'
PLAN = REPO / 'registro/pendientes_F3c_plan.json'
L = ('motor', 'buildings', 'contents')
SEQ = (('gender', ('motor', 'contents')), ('works_from_home', ('contents',)),
       ('marketing_segment', ('contents',)))
NAMES = ('sin_factores', 'F3c_transferido', 'constante')


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def clean(x):
    if isinstance(x, dict):
        return {str(k): clean(v) for k, v in x.items()}
    if isinstance(x, (tuple, list)):
        return [clean(v) for v in x]
    if isinstance(x, np.ndarray):
        return clean(x.tolist())
    if isinstance(x, np.generic):
        return clean(x.item())
    if isinstance(x, float) and not math.isfinite(x):
        return None
    return x


def save(p, x):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(clean(x), ensure_ascii=False, indent=2,
                                 allow_nan=False) + '\n', encoding='utf-8')


def rel(p):
    return Path(p).relative_to(ROOT).as_posix()


def dev(y, m):
    y, m = np.asarray(y), np.asarray(m)
    assert np.isfinite(y).all() and (y >= 0).all()
    assert np.isfinite(m).all() and (m > 0).all()
    return 4 * (y / np.sqrt(m) + np.sqrt(m) - 2 * np.sqrt(y))


def kopt(y, m):
    return float(np.sum(y / np.sqrt(m)) / np.sqrt(m).sum())


def cells(t):
    return (t.line + '_' + t.new_business.astype(int).astype(str)).to_numpy()


def band(e):
    return np.where(e < .5, 'c', np.where(e < .9, 'm', 'l'))


def renorm(t, m, old):
    out = m.copy()
    c = cells(t)
    for cc in np.unique(c):
        i = c == cc
        out[i] *= old[i].sum() / out[i].sum()
    return out


def shape(t, m, powers):
    out = m.copy()
    c = cells(t)
    for cc, a in powers.items():
        i = c == cc
        if not i.any():
            continue
        e = (t.exposure * t.c_fila).to_numpy()[i]
        gm = m[i].sum() / e.sum()
        mm = e * gm * (m[i] / e / gm) ** a
        out[i] = mm * m[i].sum() / mm.sum()
    return out


def fit_ae(t, m, key):
    c, y = cells(t), t.y.to_numpy()
    factors = {}
    for cc in np.unique(c):
        i = c == cc
        base = y[i].sum() / m[i].sum()
        for v in np.unique(key[i]):
            j = i & (key == v)
            n = (y[j] > 0).sum()
            factors[(cc, v)] = 1 + n / (n + 300) * (y[j].sum() / m[j].sum() / base - 1)
    return factors


def apply_ae(t, m, key, f):
    return renorm(t, m * np.array([f.get((c, v), 1.) for c, v in zip(cells(t), key)]), m)


def fit_tw(t, m, key, lines):
    c, y = cells(t), t.y.to_numpy()
    ref = m.copy()
    for cc in np.unique(c):
        i = c == cc
        ref[i] *= kopt(y[i], ref[i])
    factors = {}
    for l in lines:
        il = t.line.to_numpy() == l
        for v in np.unique(key[il]):
            j = il & (key == v)
            n = int((y[j] > 0).sum())
            if n:
                factors[(l, v)] = math.exp(n / (n + 300) * math.log(max(kopt(y[j], ref[j]), 1e-3)))
    return factors


def apply_tw(t, m, key, f):
    return renorm(t, m * np.array([f.get((l, v), 1.) for l, v in zip(t.line, key)]), m)


def freeze(run, reuse=None):
    if run.exists():
        raise RuntimeError('Use carpeta nueva; no se sobrescriben corridas.')
    run.mkdir(parents=True)
    files = [PLAN, Path(__file__), WORK / 'base_etiquetas.parquet',
             WORK / 'in/predicciones_2024.parquet',
             SRC / 'final_info_3puntos.json',
             SRC / 'exp26_20261026/m017/exp26/fuga_celdas.json',
             SRC / 'sigma_forma.json', REPO / 'registro/reproduccion_m017_actual.json',
             REPO / 'registro/semana2_politica_seleccion_v1.json',
             REPO / 'registro/semana2_politica_desarrollo2024_v2.json']
    files += list(DATA.glob('*.parquet'))
    files += [ROOT / 'Hackaton/Semana 1/Datos/claims.parquet']
    files += list((WORK / 'oof/pred').rglob('*.parquet'))
    files += list((SRC / 'codigo').glob('*.py'))
    files += [SRC / 'exp26_20261026/m017/construir_F3b.py',
              SRC / 'exp26_20261026/m017/exp26/lib26.py',
              SRC / 'exp26_20261026_v2/m017/construir_F3c.py']
    files += [REPO / 'privado/semana2/claude_mision017_20261025' / (n + '_2025.csv')
              for n in ('F2_ncb_previos', 'F3c', 'F3d', 'F4c', 'F3b_sinfac')]
    files += [REPO / 'privado/semana2/mision017_fase2/calibracion_F2_creible_20261025_v1/final_creible_2025.csv']
    files = sorted(set(files))
    assert all(p.is_file() for p in files)
    manifest = {'utc': datetime.now(timezone.utc).isoformat(), 'author': 'Codex',
                'plan': read(PLAN), 'files': [{'path': rel(p), 'sha256': sha(p)} for p in files],
                'environment': {'python': sys.version, 'executable': sys.executable,
                    'platform': platform.platform(), 'prefix': sys.prefix,
                    'packages': {n: importlib.metadata.version(n) for n in ('numpy', 'pandas', 'pyarrow')}}}
    save(run / 'frozen.json', manifest)
    if reuse is not None:
        reused = []
        for pattern in ('*_to_*.parquet', '*_parameters.json', 'bootstrap_*.npz'):
            for source in sorted(reuse.glob(pattern)):
                shutil.copyfile(source, run / source.name)
                reused.append({'path': rel(source), 'sha256': sha(source), 'target': source.name})
        save(run / 'reused_artifacts.json', {'source_run': rel(reuse), 'files': reused,
            'reason': 'Recuperar cálculos guardados tras fallo de precisión de exposición; sin nuevas remuestras o factores.'})
    # Inventario documental de uso de 2024. No se abren resultados por fila aquí.
    inventory = []
    for folder in ('registro', 'docs/semana2'):
        for p in sorted((REPO / folder).rglob('*')):
            if p.suffix.lower() in ('.json', '.md') and p.is_file():
                text = p.read_text(encoding='utf-8-sig', errors='replace')
                if '2024' in text:
                    inventory.append({'path': rel(p), 'sha256': sha(p), 'mentions_2024': text.count('2024')})
    save(run / 'inventario_2024.json', {'documents': inventory, 'scope': 'Referencias documentales, no registro exhaustivo de cada lectura humana o consulta histórica.'})
    print(json.dumps({'frozen': rel(run), 'inputs': len(files), 'documents2024': len(inventory), 'sha256': sha(run / 'frozen.json')}))


def verify_inputs(run):
    for entry in read(run / 'frozen.json')['files']:
        assert sha(ROOT / entry['path']) == entry['sha256'], entry['path']


def load():
    b = pd.read_parquet(WORK / 'base_etiquetas.parquet').set_index('row_id')
    parts = []
    for kind in ('policies', 'test'):
        for line in L:
            p = pd.read_parquet(DATA / f'{kind}_{line}.parquet')
            p['line'] = line
            parts.append(p)
    pol = pd.concat(parts, ignore_index=True).set_index('row_id')
    assert pol.index.is_unique and b.index.is_unique and set(pol.index) == set(b.index)
    b['address_id'] = pol.address_id.reindex(b.index)
    b['policy_id'] = pol.policy_id.reindex(b.index)
    b['channel'] = pol.channel.reindex(b.index)
    cu = pd.read_parquet(DATA / 'customers.parquet').set_index('customer_id')
    assert cu.index.is_unique
    for key in ('gender', 'prior_claims_5y', 'marketing_segment'):
        b[key] = cu[key].reindex(b.customer_id).to_numpy()
    b['works_from_home'] = pol.works_from_home.reindex(b.index)
    b['ncb'] = pd.cut(pol.ncb_years.reindex(b.index).fillna(0),
                      [-1, 0, 2, 5, 9, 99], labels=['0', '1-2', '3-5', '6-9', '10+']).astype(str)
    b.loc[b.line != 'motor', 'ncb'] = 'x'
    b['prior'] = np.minimum(b.prior_claims_5y.fillna(0).to_numpy(), 2).astype(int).astype(str)
    # Componente conexa cliente-dirección, construido sin etiquetas.
    parent = {}
    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for customer, address in zip(b.customer_id, b.address_id):
        a = find('c:' + str(customer))
        if pd.notna(address):
            d = find('a:' + str(address))
            if a != d:
                parent[d] = a
    b['group'] = [find('c:' + str(c)) for c in b.customer_id]
    sets = {}
    for name, scope in (('DEV23_T2b', 'dev'), ('HOLD24_T2b', 'hold')):
        p = pd.concat([pd.read_parquet(WORK / f'oof/pred/{scope}/T2b_{l}.parquet') for l in L]).set_index('row_id')
        assert p.index.is_unique
        t = b.loc[p.index].copy()
        t['m'] = p.mu.to_numpy() * t.c_fila.to_numpy()
        sets[name] = t
    p24 = pd.read_parquet(WORK / 'in/predicciones_2024.parquet').set_index('row_id')
    for n in ('A1', 'R0'):
        t = b.loc[p24.index].copy()
        t['m'] = p24[n].to_numpy()
        sets['HOLD24_' + n] = t
    h = sets['HOLD24_T2b'].copy()
    a1 = sets['HOLD24_A1'].m.reindex(h.index)
    tot = h.groupby('line').m.transform('sum') / a1.groupby(h.line).transform('sum')
    h['m'] = .5 * h.m + .5 * a1 * tot
    sets['HOLD24_mezcla'] = h
    for t in sets.values():
        assert np.isfinite(t.m).all() and (t.m > 0).all()
    return b, pol, sets


def keys(t, v):
    # Semántica original: valores de atributos convertidos a texto.
    return t[v].astype(str).to_numpy()


def fit_recipe(tr, te, powers):
    mtr, mte = tr.m.to_numpy().copy(), te.m.to_numpy().copy()
    params = {'F2': [], 'own': [], 'levels': {}}
    for v in ('ncb', 'prior'):
        f = fit_ae(tr, mtr, keys(tr, v))
        mtr = apply_ae(tr, mtr, keys(tr, v), f)
        mte = apply_ae(te, mte, keys(te, v), f)
        params['F2'].append({'variable': v, 'factors': {str(k): x for k, x in f.items()}})
    mtr = shape(tr, mtr, {'motor_0': .9})
    mte = shape(te, mte, {'motor_0': .9})
    # F3c aprende sus residuales en la forma local F3b y los aplica a final_creible.
    sigma = read(SRC / 'sigma_forma.json')
    fuga = read(SRC / 'exp26_20261026/m017/exp26/fuga_celdas.json')
    am1 = 1 + sigma['motor_1']['Z_tau0.25'] * (fuga['motor_1']['sin_nivel']['vertice'] - 1)
    own_tr = shape(tr, mtr, {'motor_1': am1})
    steps = []
    for v, lines in SEQ:
        f = fit_tw(tr, own_tr, keys(tr, v), lines)
        own_tr = apply_tw(tr, own_tr, keys(tr, v), f)
        support_rows = []
        for (line, level), factor in f.items():
            for nb in (False, True):
                j = (tr.line.to_numpy() == line) & (keys(tr, v) == level) & (tr.new_business.to_numpy() == nb)
                support_rows.append({'line': line, 'level': level, 'new_business': nb,
                    'factor': factor, 'rows': int(j.sum()), 'exposure': float(tr.exposure.to_numpy()[j].sum()),
                    'positive_groups': int(tr.loc[j & (tr.y.to_numpy() > 0), 'group'].nunique())})
        params['own'].append({'variable': v, 'factors': {str(k): x for k, x in f.items()}, 'support': support_rows})
        steps.append((v, f))
    base_tr, base_te = shape(tr, mtr, powers), shape(te, mte, powers)
    cand_tr, cand_te = base_tr.copy(), base_te.copy()
    stage_predictions = []
    for v, f in steps:
        cand_tr = apply_tw(tr, cand_tr, keys(tr, v), f)
        cand_te = apply_tw(te, cand_te, keys(te, v), f)
        stage_predictions.append((v, cand_te.copy()))
    c, ce = cells(tr), cells(te)
    preds, train_preds = {}, {}
    for name, mt, me in [('sin_factores', base_tr, base_te), ('F3c_transferido', cand_tr, cand_te)]:
        ks = {}
        for cc in np.unique(c):
            i, j = c == cc, ce == cc
            k = kopt(tr.y.to_numpy()[i], mt[i])
            ks[cc] = k
            mt[i] *= k
            me[j] *= k
        params['levels'][name] = ks
        preds[name], train_preds[name] = me, mt
    params['stage_contributions'] = []
    old = preds['sin_factores'].copy()
    for v, stage in stage_predictions:
        stage = stage * np.array([params['levels']['sin_factores'][cc] for cc in ce])
        params['stage_contributions'].append({'variable': v,
            'evaluation': evaluate(te, {'sin_factores': old, 'F3c_transferido': stage}),
            'limit': 'Incremento de forma con el nivel de la base fijo; niveles de entrenamiento, sin recalibrar retenidos.'})
        old = stage
    const, ct = np.empty(len(te)), np.empty(len(tr))
    for cc in np.unique(c):
        i, j = c == cc, ce == cc
        e = (tr.exposure * tr.c_fila).to_numpy()[i]
        rate = kopt(tr.y.to_numpy()[i], e)
        ct[i] = rate * e
        const[j] = rate * (te.exposure * te.c_fila).to_numpy()[j]
        params.setdefault('constant_rates', {})[cc] = rate
    preds['constante'], train_preds['constante'] = const, ct
    return preds, params, train_preds


def apply_saved(tr, te, params, powers, relevel=False):
    mt, me = tr.m.to_numpy().copy(), te.m.to_numpy().copy()
    for step in params['F2']:
        f = {ast.literal_eval(k): v for k, v in step['factors'].items()}
        v = step['variable']
        mt, me = apply_ae(tr, mt, keys(tr, v), f), apply_ae(te, me, keys(te, v), f)
    mt, me = shape(tr, mt, {'motor_0': .9}), shape(te, me, {'motor_0': .9})
    bt, be = shape(tr, mt, powers), shape(te, me, powers)
    ct, ce = bt.copy(), be.copy()
    for step in params['own']:
        f = {ast.literal_eval(k): v for k, v in step['factors'].items()}
        v = step['variable']
        ct, ce = apply_tw(tr, ct, keys(tr, v), f), apply_tw(te, ce, keys(te, v), f)
    out, trainout = {}, {}
    for name, train, test in [('sin_factores', bt, be), ('F3c_transferido', ct, ce)]:
        for cc in np.unique(cells(tr)):
            i, j = cells(tr) == cc, cells(te) == cc
            k = kopt(tr.y.to_numpy()[i], train[i]) if relevel else params['levels'][name][cc]
            train[i] *= k
            test[j] *= k
        out[name], trainout[name] = test, train
    trconst, teconst = np.empty(len(tr)), np.empty(len(te))
    for cc, rate in params['constant_rates'].items():
        i, j = cells(tr) == cc, cells(te) == cc
        trconst[i] = rate * (tr.exposure * tr.c_fila).to_numpy()[i]
        teconst[j] = rate * (te.exposure * te.c_fila).to_numpy()[j]
    out['constante'], trainout['constante'] = teconst, trconst
    return out, trainout


def metric(y, m, w=None):
    w = np.ones(len(y)) if w is None else w
    avg = np.average(y, weights=w)
    denominator = float((dev(y, np.full(len(y), max(avg, 1e-30))) * w).sum())
    return {'D2': 1 - float((dev(y, m) * w).sum()) / denominator if denominator > 0 else None,
            'A_over_E': float((y * w).sum() / (m * w).sum()),
            'observed': float((y * w).sum()), 'expected': float((m * w).sum()),
            'null_deviance': denominator}


def evaluate(t, preds, weights=None):
    y = t.y.to_numpy()
    masks = {'all': np.ones(len(t), bool), 'new_business': t.new_business.to_numpy(),
             'renewal': ~t.new_business.to_numpy()}
    masks.update({l: t.line.to_numpy() == l for l in L})
    masks.update({l + '_' + str(int(nb)): (t.line.to_numpy() == l) & (t.new_business.to_numpy() == nb)
                  for l in L for nb in (False, True)})
    out = {}
    for seg, i in masks.items():
        if not i.any():
            continue
        w = None if weights is None else weights[i]
        row = {'rows': int(i.sum()), 'exposure': float(t.exposure.to_numpy()[i].sum()),
               'groups': int(t.group[i].nunique()), 'positive_groups': int(t.loc[i & (y > 0), 'group'].nunique()),
               'models': {n: metric(y[i], p[i], w) for n, p in preds.items()}}
        row['delta_F3c_minus_sin_factores'] = row['models']['F3c_transferido']['D2'] - row['models']['sin_factores']['D2']
        out[seg] = row
    return out


def bootstrap(t, preds, run, label, weights=None):
    """Suficientes por grupo; nulo recalculado en cada réplica, pares comunes."""
    y = t.y.to_numpy()
    w = np.ones(len(t)) if weights is None else weights
    group, unique = pd.factorize(t.group, sort=True)
    ng = len(unique)
    segments = {'all': np.ones(len(t), bool), 'new_business': t.new_business.to_numpy(),
                'renewal': ~t.new_business.to_numpy()}
    segments.update({l: t.line.to_numpy() == l for l in L})
    existing = run / ('bootstrap_' + label + '.npz')
    if existing.exists():
        saved = np.load(existing)
        assert list(saved['segments']) == list(segments) and list(saved['models']) == list(NAMES)
        draws = saved['scores']
        assert draws.shape == (10000, len(segments), 3)
        result = {}
        for j, s in enumerate(segments):
            diff = draws[:, j, 1] - draws[:, j, 0]
            result[s] = {'delta_CI95': np.quantile(diff, [.025, .975]).tolist(),
                         'delta_CI_family6': np.quantile(diff, [1 / 240, 239 / 240]).tolist()}
        return {'groups': ng, 'replicates': 10000, 'seed': 2026102607,
                'same_draws_all_models': True, 'intervals': result, 'reused_saved_draws': True}
    mats = []
    for mask in segments.values():
        z = w * mask
        stats = [np.bincount(group, weights=a, minlength=ng) for a in
                 (z, z * y, z * np.sqrt(y))]
        stats += [np.bincount(group, weights=z * dev(y, preds[n]), minlength=ng) for n in NAMES]
        mats.extend(stats)
    matrix = np.array(mats).T
    draws = np.empty((10000, len(segments), 3))
    rng = np.random.default_rng(2026102607)
    for start in range(0, 10000, 20):
        mult = rng.multinomial(ng, np.full(ng, 1 / ng), size=min(20, 10000 - start))
        stats = (mult @ matrix).reshape(len(mult), len(segments), 6)
        den = 8 * (np.sqrt(stats[:, :, 0] * stats[:, :, 1]) - stats[:, :, 2])
        score = 1 - stats[:, :, 3:] / np.maximum(den[:, :, None], 1e-30)
        draws[start:start + len(mult)] = score
    np.savez_compressed(run / ('bootstrap_' + label + '.npz'), scores=draws,
                        segments=np.array(list(segments)), models=np.array(NAMES))
    result = {}
    for j, s in enumerate(segments):
        diff = draws[:, j, 1] - draws[:, j, 0]
        result[s] = {'delta_CI95': np.quantile(diff, [.025, .975]).tolist(),
                     'delta_CI_family6': np.quantile(diff, [1 / 240, 239 / 240]).tolist()}
    return {'groups': ng, 'replicates': 10000, 'seed': 2026102607,
            'same_draws_all_models': True, 'intervals': result}


def influence(t, preds):
    y = t.y.to_numpy()
    c = dev(y, preds['sin_factores']) - dev(y, preds['F3c_transferido'])
    contribution = pd.Series(c).groupby(t.group.to_numpy()).sum().sort_values(ascending=False)
    null = metric(y, preds['sin_factores'])['null_deviance']
    rows = []
    for k in sorted(set((max(5, math.ceil(.001 * len(contribution))), 31))):
        keep = ~t.group.isin(contribution.head(k).index).to_numpy()
        rows.append({'scenario': 'remove_top_' + str(k), 'groups_removed': k,
                     'models': {n: metric(y[keep], p[keep]) for n, p in preds.items()},
                     'delta_fixed_original_null': float(c[keep].sum() / null)})
    threshold = np.quantile(y[y > 0], .99)
    keep = y < threshold
    rows.append({'scenario': 'remove_top1pct_positive_cost_periods', 'threshold': threshold,
                 'rows_removed': int((~keep).sum()),
                 'models': {n: metric(y[keep], p[keep]) for n, p in preds.items()}})
    rng = np.random.default_rng(2026102608)
    gs = np.array(sorted(t.group.unique()))
    random_deltas = []
    random_scores = {n: [] for n in preds}
    for _ in range(100):
        selected = rng.choice(gs, max(1, math.ceil(.01 * len(gs))), replace=False)
        keep = ~t.group.isin(selected).to_numpy()
        ms = {n: metric(y[keep], p[keep])['D2'] for n, p in preds.items()}
        for n in preds:
            random_scores[n].append(ms[n])
        random_deltas.append(ms['F3c_transferido'] - ms['sin_factores'])
    return {'top_contribution': {'top5_share_positive_gain': float(contribution.head(5).sum() / contribution.clip(lower=0).sum()),
                                 'top31_share_positive_gain': float(contribution.head(31).sum() / contribution.clip(lower=0).sum())},
            'scenarios': rows, 'random_1pct_100': {'delta_min': min(random_deltas), 'delta_max': max(random_deltas),
                'positive_fraction': np.mean(np.array(random_deltas) > 0), 'model_D2_ranges': {n: [min(v), max(v)] for n, v in random_scores.items()}}}


def matched_claims(pol):
    c = pd.read_parquet(DATA / 'claims.parquet')
    for col in ('loss_date', 'report_date'):
        c[col] = pd.to_datetime(c[col])
    p = pol.reset_index()[['row_id', 'line', 'policy_id', 'period_start', 'period_end']].copy()
    for col in ('period_start', 'period_end'):
        p[col] = pd.to_datetime(p[col])
    m = c.merge(p, on=['line', 'policy_id'])
    m = m[(m.loss_date >= m.period_start) & (m.loss_date <= m.period_end)].copy()
    assert m.claim_id.is_unique
    unmatched = c[~c.claim_id.isin(m.claim_id)].copy()
    m.attrs['unmatched'] = unmatched
    m['year'] = m.period_start.dt.year
    m['net'] = m.incurred_to_date - m.recoveries
    m['reserve'] = np.where(m.status != 'repudiated', m.incurred_to_date - m.paid_to_date, 0)
    return m


def support(b):
    out = []
    t25 = b[b.conjunto == 'test']
    total_exposure = t25.exposure.sum()
    for year in (2023, 2024):
        hist = b[(b.conjunto == 'train') & (b.year == year)]
        for l in L:
            for nb in (False, True):
                h = hist[(hist.line == l) & (hist.new_business == nb)]
                f = t25[(t25.line == l) & (t25.new_business == nb)]
                counts = h.groupby(pd.Series(band(h.exposure.to_numpy()), index=h.index)).size()
                fn = pd.Series(band(f.exposure.to_numpy())).value_counts(normalize=True)
                hn = pd.Series(band(h.exposure.to_numpy())).value_counts(normalize=True)
                w = pd.Series(band(h.exposure.to_numpy())).map(fn / hn).fillna(0).to_numpy()
                ess = w.sum() ** 2 / (w @ w) if (w @ w) else 0
                # Conservar tamaño por grupo, además del n_eff de filas.
                wg = pd.Series(w).groupby(h.group.to_numpy()).sum().to_numpy()
                ge = wg.sum() ** 2 / (wg @ wg) if len(wg) and (wg @ wg) else 0
                positive = int(h.loc[h.y > 0, 'group'].nunique())
                out.append({'year': year, 'line': l, 'new_business': nb,
                    'historical_rows': len(h), 'historical_exposure': h.exposure.sum(),
                    'future_rows': len(f), 'future_exposure': f.exposure.sum(),
                    'future_portfolio_exposure_share': f.exposure.sum() / total_exposure,
                    'full_year_historical': int((h.exposure >= .9).sum()),
                    'full_year_future': int((f.exposure >= .9).sum()),
                    'positive_groups': positive, 'row_ESS_composition': ess, 'group_ESS_composition': ge,
                    'support_pass': bool(ess >= 100 and ge >= 100 and positive >= 30),
                    'bands_historical': counts.to_dict()})
    variables = []
    for v, lines in SEQ:
        for l in lines:
            for nb in (False, True):
                h = b[(b.conjunto == 'train') & (b.line == l) & (b.new_business == nb)]
                f = t25[(t25.line == l) & (t25.new_business == nb)]
                hv, fv = keys(h, v), keys(f, v)
                seen = set(hv)
                new = ~np.isin(fv, list(seen))
                variables.append({'variable': v, 'line': l, 'new_business': nb,
                    'future_rows': len(f), 'missing_future': int(f[v].isna().sum()),
                    'unseen_future_rows': int(new.sum()),
                    'unseen_future_exposure': f.exposure.to_numpy()[new].sum(),
                    'historical_distribution': pd.Series(hv).value_counts(normalize=True).to_dict(),
                    'future_distribution': pd.Series(fv).value_counts(normalize=True).to_dict(),
                    'availability': 'maestro sin snapshot fechado' if v in ('gender', 'marketing_segment') else 'campo de póliza; fecha de extracción no prueba disponibilidad al cotizar'})
    return {'cells': out, 'variables': variables,
            'business_by_year': b.groupby(['conjunto', 'year', 'new_business']).agg(rows=('line', 'size'), exposure=('exposure', 'sum')).reset_index().to_dict('records')}


def reporting(claims):
    cd = pd.read_parquet(ROOT / 'Hackaton/Semana 1/Datos/claims.parquet')
    cols = [c for c in cd if c != 'claim_id']
    cd = cd[~(cd.duplicated(cols, keep=False) & (cd.claim_id.str.len() == 11))].copy()
    cd['loss_date'], cd['report_date'] = pd.to_datetime(cd.loss_date), pd.to_datetime(cd.report_date)
    cd['net'] = cd.incurred_to_date - cd.recoveries
    mature = cd[(cd.status != 'repudiated') & ((pd.Timestamp('2024-12-31') - cd.loss_date).dt.days >= 1095)]
    curves = {}
    for (l, p), g in mature.groupby(['line', 'peril']):
        delay = (g.report_date - g.loss_date).dt.days.to_numpy()
        ok = delay <= 1095
        delay, cost = delay[ok], g.net.to_numpy()[ok]
        curves[(l, p)] = (np.bincount(delay, minlength=1096).cumsum() / len(delay),
                          np.bincount(delay, weights=cost, minlength=1096).cumsum() / cost.sum())
    out = []
    cc = claims[(claims.status != 'repudiated') & (claims.loss_date.dt.year == 2023)]
    for (l, p), g in cc.groupby(['line', 'peril']):
        delay1 = np.clip((pd.Timestamp('2023-12-31') - g.loss_date).dt.days.to_numpy(), 0, 1095)
        delay2 = np.clip((pd.Timestamp('2024-12-31') - g.loss_date).dt.days.to_numpy(), 0, 1095)
        cn, co = curves[(l, p)]
        pn, pc = cn[delay1] / cn[delay2], co[delay1] / co[delay2]
        late = (g.report_date > pd.Timestamp('2023-12-31')).to_numpy()
        positive = g.net.to_numpy() > 0
        # Incluir marcas cero en conteos; medias de severidad neta con todos aceptados.
        early_mean = float(g.net.to_numpy()[~late].mean()) if (~late).any() else None
        late_mean = float(g.net.to_numpy()[late].mean()) if late.any() else None
        out.append({'line': l, 'peril': p, 'claims': len(g), 'positive': int(positive.sum()),
                    'late_count': int(late.sum()), 'late_cost': float(g.net.to_numpy()[late].sum()),
                    'early_mean': early_mean, 'late_mean': late_mean,
                    'severity_late_over_early': late_mean / early_mean if early_mean and late_mean is not None else None,
                    'expected_late_count_count_curve': float((1 - pn).sum()),
                    'expected_late_count_using_cost_curve_incorrect': float((1 - pc).sum()),
                    'expected_late_cost_cost_curve': float((g.net.to_numpy() * (1 - pc)).sum()),
                    'cost_completion': float(g.net.to_numpy()[~late].sum() / g.net.sum()),
                    'count_completion': float((~late).mean()),
                    'single_valuation': True})
    return out


def scenarios(claims):
    specs = [('reserve075', .75, None, None), ('reserve125', 1.25, None, None)]
    specs += [(f'reserve_{l}_{k}', k, l, None) for l in L for k in (.75, 1.25)]
    specs += [(f'reserve_{l}_{p}_{k}', k, l, p) for l, p in sorted(set(zip(claims.line, claims.peril))) for k in (.75, 1.25)]
    records = []
    for name, k, l, p in specs:
        mask = claims.status != 'repudiated'
        if l:
            mask &= claims.line == l
        if p:
            mask &= claims.peril == p
        # Todo incurrido-pagado es reserva de caso; registrar estados no abiertos.
        delta = claims.reserve.to_numpy() * mask.to_numpy() * (k - 1)
        records.append((name, delta))
    bi = claims.peril.isin(['bodily_injury'])
    for name, bi_factor, other in [('opposed_BI125_rest075', 1.25, .75), ('opposed_BI075_rest125', .75, 1.25)]:
        factor = np.where(bi, bi_factor, other)
        records.append((name, claims.reserve.to_numpy() * (factor - 1)))
    # Riesgo de severidad tardía, aplicado solo a lo observado con retraso>90d.
    delay = (claims.report_date - claims.loss_date).dt.days.to_numpy()
    accepted = (claims.status != 'repudiated').to_numpy()
    for k in (.5, 1.5, 2.):
        records.append((f'late_observed_severity_x{k}', claims.net.to_numpy() * (delay > 90) * accepted * (k - 1)))
    for k in (.05, .10):
        mask = claims.peril.isin(['bodily_injury', 'subsidence']).to_numpy() * accepted
        records.append((f'BI_subsidence_cost_tail_{k}', claims.net.to_numpy() * mask * k))
    return [(n, pd.Series(d).groupby(claims.row_id.to_numpy()).sum()) for n, d in records]


def completion_stress(tr, te, pol, claims, preds, trpred, overlay):
    """Curva de conteo distinta de coste y severidad de la porción no reportada.

    Estructuras guardadas congeladas; mezcla por peligro aprende solo en tr.
    Fuente madura tiene una valoración y no es desarrollo de pagos últimos.
    """
    cd = pd.read_parquet(ROOT / 'Hackaton/Semana 1/Datos/claims.parquet')
    columns = [c for c in cd if c != 'claim_id']
    cd = cd[~(cd.duplicated(columns, keep=False) & (cd.claim_id.str.len() == 11))].copy()
    cd['loss_date'], cd['report_date'] = pd.to_datetime(cd.loss_date), pd.to_datetime(cd.report_date)
    valuation = np.datetime64('2024-12-31')
    age = (pd.Timestamp('2024-12-31') - cd.loss_date).dt.days
    cd = cd[(cd.status != 'repudiated') & (age >= 1095)]
    curves = {}
    for (line, peril), group in cd.groupby(['line', 'peril']):
        delay = (group.report_date - group.loss_date).dt.days.to_numpy()
        net = (group.incurred_to_date - group.recoveries).to_numpy()
        ok = delay <= 1095
        count = np.bincount(delay[ok], minlength=1096).cumsum().astype(float)
        cost = np.bincount(delay[ok], weights=net[ok], minlength=1096).cumsum()
        curves[(line, peril)] = (count / count[-1], cost / cost[-1])
    def perrow(t, curve):
        cdf = np.r_[curve, np.ones(4000 - len(curve))]
        accum = np.r_[0., np.cumsum(cdf)]
        pp = pol.loc[t.index]
        start = pd.to_datetime(pp.period_start).to_numpy().astype('datetime64[D]')
        end = pd.to_datetime(pp.period_end).to_numpy().astype('datetime64[D]')
        a = np.maximum((valuation - end).astype(int), 0)
        z = np.maximum((valuation - start).astype(int), 0)
        return (accum[z + 1] - accum[a]) / (z - a + 1)
    names = ['count_curve', 'cost_curve_train_peril_mix', 'unreported_severity_x0.5',
             'unreported_severity_x1.5', 'unreported_severity_x2.0']
    cf = {n: {'tr': np.ones(len(tr)), 'te': np.ones(len(te))} for n in names}
    mix_records = []
    for line in L:
        it, ie = tr.line.to_numpy() == line, te.line.to_numpy() == line
        tt, ee = tr[it], te[ie]
        perils = sorted(p for l, p in curves if l == line)
        cost_cp = {p: perrow(tt, curves[(line, p)][1]) for p in perils}
        source = claims[(claims.status != 'repudiated') & claims.row_id.isin(tt.index)]
        weights = {p: source.loc[source.peril == p, 'net'].sum() /
                      max(np.average(cost_cp[p], weights=tt.exposure.to_numpy()), 1e-9) for p in perils}
        total = sum(weights.values())
        weights = {p: value / total for p, value in weights.items()}
        mix_records += [{'line': line, 'peril': p, 'train_ultimate_cost_share': v} for p, v in weights.items()]
        for name in names:
            for scope, t, mask in [('tr', tt, it), ('te', ee, ie)]:
                combined = np.zeros(len(t))
                for p in perils:
                    curve = curves[(line, p)][0 if name == 'count_curve' else 1]
                    if name.startswith('unreported_severity_'):
                        factor = float(name.split('x')[-1])
                        curve = curve / np.maximum(curve + factor * (1 - curve), 1e-30)
                    combined += weights[p] * perrow(t, curve)
                cf[name][scope][mask] = combined
    result, transfer = [], {}
    for name, values in cf.items():
        prices, levels = {}, {}
        for n in preds:
            mt = trpred[n] * values['tr'] / tr.c_fila.to_numpy()
            me = preds[n] * values['te'] / te.c_fila.to_numpy()
            levels[n] = {}
            for cc in np.unique(cells(tr)):
                i, j = cells(tr) == cc, cells(te) == cc
                k = kopt(tr.y.to_numpy()[i], mt[i])
                me[j] *= k
                levels[n][cc] = k
            prices[n] = me
        with_public = {n: p * np.array([overlay[c] for c in cells(te)]) for n, p in prices.items()}
        result.append({'scenario': name, 'mean_completion_tr': values['tr'].mean(),
            'mean_completion_te': values['te'].mean(), 'level_ratios_ultimate': levels,
            'before_public': evaluate(te, prices), 'after_frozen_public_overlay': evaluate(te, with_public)})
        transfer['completion_' + name] = levels
    return {'peril_mix': mix_records, 'scenarios': result,
        'limit': 'Mezcla por ramo entrenada en2023, no mezcla por riesgo identificada. No reentrena árboles ni estima pagos futuros de abiertos. Overlay público fijo; recalibración con sondas nuevas no identificada.'}, transfer


def commercial(b, run, stress_levels):
    references = pd.read_parquet(DATA / 'reference_policies.parquet')
    expenses = pd.read_parquet(DATA / 'expenses.parquet').set_index('item').emerging
    paths = {'F3c': REPO / 'privado/semana2/claude_mision017_20261025/F3c_2025.csv',
             'sin_factores_final_creible': REPO / 'privado/semana2/mision017_fase2/calibracion_F2_creible_20261025_v1/final_creible_2025.csv',
             'F3d_no_admitido': REPO / 'privado/semana2/claude_mision017_20261025/F3d_2025.csv',
             'F4c_no_reproducido': REPO / 'privado/semana2/claude_mision017_20261025/F4c_2025.csv',
             'F2': REPO / 'privado/semana2/claude_mision017_20261025/F2_ncb_previos_2025.csv'}
    refs = references.set_index('row_id')
    assert len(refs) == 20 and refs.index.is_unique
    predictions = {n: pd.read_csv(p, dtype={'row_id': str, 'prediction': str}).set_index('row_id') for n, p in paths.items()}
    for p in predictions.values():
        assert len(p) == 209063 and p.index.is_unique and refs.index.isin(p.index).all()
    output = []
    D = lambda x: Decimal(str(x))
    E = lambda x: D(expenses[x])
    cents = Decimal('.01')
    with localcontext() as ctx:
        ctx.prec = 45
        for n, p in predictions.items():
            for idx, r in refs.iterrows():
                e = D(r.exposure)
                calendar = D((pd.Timestamp(r.period_end) - pd.Timestamp(r.period_start)).days + 1) / D(365)
                # El archivo oficial redondea exposure a cuatro decimales.
                assert abs(e - calendar) <= D('.00005000001')
                risk = D(p.loc[idx, 'prediction'])
                commission = E('commission_' + r.channel)
                cat = E('cat_reinsurance') if r.line in ('buildings', 'contents') else D(0)
                denominator = 1 - E('variable_expense') - commission - E('premium_tax') - E('target_profit_margin')
                assert denominator > 0
                cc = str(r.line) + '_' + str(int(r.new_business))
                cases = {'nominal': D(1)}
                if n in ('F3c', 'sin_factores_final_creible'):
                    model = 'F3c_transferido' if n == 'F3c' else 'sin_factores'
                    for scenario, vals in stress_levels.items():
                        cases[scenario] = D(vals[model][cc])
                for scenario, multiplier in cases.items():
                    rr = risk * multiplier
                    fixed = E('fixed_expense_per_policy') * e
                    pp = (rr * (1 + cat) + fixed) / denominator
                    identity = rr * (1 + cat) + fixed + pp * (1 - denominator)
                    assert abs(pp - identity) < D('1e-30')
                    float_check = (float(rr) * (1 + float(cat)) + float(fixed)) / float(denominator)
                    assert abs(float_check - float(pp)) < 1e-8
                    output.append({'row_id': idx, 'model': n, 'scenario': scenario, 'line': r.line,
                        'exposure': str(e), 'channel': r.channel, 'risk_period': str(rr),
                        'annual_risk': str(rr / e), 'commercial_unrounded': str(pp),
                        'commercial': str(pp.quantize(cents, rounding=ROUND_HALF_UP)),
                        'denominator': str(denominator), 'multiplier': str(multiplier)})
    save(run / 'veinte_primas_privadas.json', output)
    pd.DataFrame(output).to_csv(run / 'veinte_primas_privadas.csv', index=False)
    baseline = {x['row_id']: float(x['commercial_unrounded']) for x in output if x['model'] == 'F3c' and x['scenario'] == 'nominal'}
    summary = []
    for (model, scenario), group in pd.DataFrame(output).groupby(['model', 'scenario']):
        values = group.commercial_unrounded.astype(float).to_numpy()
        ratios = values / group.row_id.map(baseline).to_numpy() - 1
        nominal_values = {x['row_id']: float(x['commercial_unrounded']) for x in output if x['model'] == model and x['scenario'] == 'nominal'}
        own_ratios = values / group.row_id.map(nominal_values).to_numpy() - 1
        summary.append({'model': model, 'scenario': scenario, 'count': len(group),
            'total_rounded': str(sum((D(v) for v in group.commercial), D(0))),
            'total_unrounded': float(values.sum()), 'total_change_from_F3c': values.sum() / sum(baseline.values()) - 1,
            'material_refs_vs_F3c_10pct': int((abs(ratios) >= .1).sum()),
            'material_refs_vs_own_nominal_10pct': int((abs(own_ratios) >= .1).sum()),
            'min_change': ratios.min(), 'max_change': ratios.max(),
            'max_scenario_change_own': abs(own_ratios).max()})
    save(run / 'comerciales_resumen.json', summary)
    return {'references': len(refs), 'records': len(output), 'summary': summary,
            'scenario_method': 'Transferencia de razones de nivel histórico por celda a precios de producción congelados. No refit completo ni IC de prima individual.',
            'rounding': 'Decimal precision45, HALF_UP por fila; suma de filas distinta de redondear suma exacta',
            'profit_margin_is_uncertainty_buffer': False}


def analyze(run):
    verify_inputs(run)
    assert not (run / 'results.json').exists(), 'No repetir resultados ya completados.'
    b, pol, sets = load()
    claims = matched_claims(pol)
    unmatched = claims.attrs['unmatched']
    unmatched.to_parquet(run / 'siniestros_sin_periodo_privados.parquet', index=False)
    accepted = claims[claims.status != 'repudiated']
    raw_y = accepted.groupby('row_id').net.sum().reindex(b.index).fillna(0)
    hist = b.conjunto == 'train'
    assert np.max(abs(raw_y[hist].to_numpy() - b.y[hist].to_numpy())) < 1e-8
    assert round(raw_y.sum(), 2) == 27997991.57
    assert b.y[~hist].isna().all()
    final = read(SRC / 'final_info_3puntos.json')
    powers = {c: v['a_cred'] for c, v in final['forma'].items()}
    overlay = {c: v / final['nivel']['g'] for c, v in final['nivel']['cred'].items()}
    result = {'author': 'Codex', 'utc_start': datetime.now(timezone.utc).isoformat(),
        'class': 'adaptive_diagnostic_not_intact_confirmation',
        'raw_label_checks': {'all_historical_rows_equal': True, 'T0_total': raw_y.sum(), 'test_y_null': True,
            'matched_claims': len(claims), 'unmatched_claims': len(unmatched),
            'unmatched_loss2023_2024': int(unmatched.loss_date.dt.year.isin([2023, 2024]).sum()),
            'unmatched_net_total': float((unmatched.incurred_to_date - unmatched.recoveries).sum()),
            'limit': 'Base histórica conserva el enlace original exacto. Siniestros sin periodo no se borran ni reasignan; evidencia privada separada.'},
        'fixed_public_shape': powers, 'fixed_public_level_relative': overlay,
        'comparisons': {}, 'factor_stability': [], 'support': support(b)}
    pairs = [('DEV23_T2b', 'HOLD24_T2b'), ('DEV23_T2b', 'HOLD24_A1'),
             ('DEV23_T2b', 'HOLD24_mezcla'), ('HOLD24_T2b', 'DEV23_T2b')]
    t25 = b[b.conjunto == 'test']
    future_keys = pd.Series(cells(t25) + '_' + band(t25.exposure.to_numpy())).value_counts(normalize=True)
    saved_primary = None
    for trname, tename in pairs:
        label = trname + '_to_' + tename
        print('Compare', label, flush=True)
        tr, te = sets[trname].copy(), sets[tename].copy()
        reused = (run / (label + '_parameters.json')).exists()
        if reused:
            params = read(run / (label + '_parameters.json'))
            saved = pd.read_parquet(run / (label + '.parquet'))
            assert saved.index.equals(te.index)
            preds = {n: saved[n].to_numpy() for n in NAMES}
            replay_preds, trpred = apply_saved(tr, te, params, powers)
            assert all(np.array_equal(preds[n], replay_preds[n]) for n in preds)
        else:
            preds, params, trpred = fit_recipe(tr, te, powers)
        frame = te[['line', 'year', 'new_business', 'exposure', 'customer_id', 'address_id', 'group', 'y']].copy()
        for n, v in preds.items():
            frame[n] = v
        frame.to_parquet(run / (label + '.parquet'))
        save(run / (label + '_parameters.json'), params)
        weight_keys = cells(te) + '_' + band(te.exposure.to_numpy())
        freq = pd.Series(weight_keys).value_counts(normalize=True)
        weights = pd.Series(weight_keys).map(future_keys / freq).fillna(0).to_numpy()
        assert len(preds['sin_factores']) == len(preds['F3c_transferido']) == len(te)
        poisoned = te.copy()
        poisoned['y'] = np.arange(len(te)) * 1001. + 7.
        if reused:
            poison_preds, _ = apply_saved(tr, poisoned, params, powers)
            assert all(np.array_equal(preds[n], poison_preds[n]) for n in preds)
        else:
            poison_preds, poison_params, _ = fit_recipe(tr, poisoned, powers)
            learned = {k: v for k, v in params.items() if k != 'stage_contributions'}
            poison_learned = {k: v for k, v in poison_params.items() if k != 'stage_contributions'}
            assert learned == poison_learned and all(np.array_equal(preds[n], poison_preds[n]) for n in preds)
        cold = ~te.group.isin(tr.group).to_numpy()
        overlap = {'customer_overlap': int(te.customer_id.isin(tr.customer_id).sum()),
                   'address_overlap': int(te.address_id.isin(tr.address_id).sum()),
                   'policy_overlap': int(te.policy_id.isin(tr.policy_id).sum()),
                   'group_overlap': int((~cold).sum()), 'cold_rows': int(cold.sum())}
        current = {'training_year': int(tr.year.iloc[0]), 'evaluation_year': int(te.year.iloc[0]),
            'metrics': evaluate(te, preds), 'metrics_composition2025': evaluate(te, preds, weights),
            'bootstrap': bootstrap(te, preds, run, label),
            'influence': influence(te, preds), 'overlap': overlap,
            'held_target_poison_parameters_and_prices_exact': True}
        current['factor_stages'] = params['stage_contributions']
        if cold.any():
            current['cold_group_metrics'] = evaluate(te[cold], {n: p[cold] for n, p in preds.items()})
        # Overlay de nivel público idéntico en las tres recetas; no es una sonda de la constante.
        public = {n: p * np.array([overlay[c] for c in cells(te)]) for n, p in preds.items()}
        current['common_public_overlay_metrics'] = evaluate(te, public)
        current['common_public_overlay_limit'] = 'Mismo multiplicador recibido, no óptimo público ni calibración propia de cada candidato.'
        # Diagnóstico oráculo que permite cotejar el alcance de B05, separado del principal.
        oracle = {}
        for n, p in preds.items():
            p = p.copy()
            for cc in np.unique(cells(te)):
                i = cells(te) == cc
                p[i] *= kopt(te.y.to_numpy()[i], p[i])
            oracle[n] = p
        current['oracle_same_evaluation_year_level'] = evaluate(te, oracle, weights)
        result['comparisons'][label] = current
        if saved_primary is None:
            saved_primary = (tr, te, preds, params, trpred)
            current['bootstrap_composition2025'] = bootstrap(te, preds, run, label + '_composition2025', weights)
            if reused:
                without_public_shape, _ = apply_saved(tr, te, params, {}, relevel=True)
            else:
                without_public_shape, _, _ = fit_recipe(tr, te, {})
            current['no_public_extra_shape_metrics'] = evaluate(te, without_public_shape)
        # Factores y contribución por paso, ramo y NB/REN sin seleccionar niveles.
        for step in params['own']:
            for key, factor in step['factors'].items():
                result['factor_stability'].append({'training_year': int(tr.year.iloc[0]),
                    'view': label, 'variable': step['variable'], 'key': key,
                    'factor': factor, 'log_factor': math.log(factor)})
        save(run / (label + '_comparison.json'), current)
    save(run / 'comparisons_checkpoint.json', result)
    tr, te, preds, params, trpred = saved_primary
    stress = []
    stress_levels = {}
    for name, delta in scenarios(claims):
        ts, es = tr.copy(), te.copy()
        ts['y'] = tr.y.to_numpy() + delta.reindex(tr.index).fillna(0).to_numpy()
        es['y'] = te.y.to_numpy() + delta.reindex(te.index).fillna(0).to_numpy()
        assert (ts.y >= 0).all() and (es.y >= 0).all()
        # Predicciones/estructura congeladas; reaprender únicamente nivel con entrenamiento.
        variants, levels = {}, {}
        for n in preds:
            out = preds[n].copy()
            levels[n] = {}
            for cc in np.unique(cells(tr)):
                i, j = cells(tr) == cc, cells(te) == cc
                newk = kopt(ts.y.to_numpy()[i], trpred[n][i])
                out[j] *= newk
                levels[n][cc] = newk
            variants[n] = out
        fixed_public = {n: p * np.array([overlay[c] for c in cells(te)]) for n, p in variants.items()}
        # Comparar orden por tasa y cambios absolutos, sin recalibrar en retenidos.
        e = (te.exposure * te.c_fila).to_numpy()
        ranks = {n: float(pd.Series(preds[n] / e).rank().corr(pd.Series(variants[n] / e).rank())) for n in preds}
        stress.append({'scenario': name, 'metrics_frozen_prices_stressed_target': evaluate(es, preds),
                       'metrics_training_level_relearned': evaluate(es, variants),
                       'metrics_with_frozen_public_overlay': evaluate(es, fixed_public),
                       'level_ratios': levels, 'rank_correlation_annual_observed_rate': ranks})
        stress_levels[name] = levels
    result['scenarios'] = stress
    result['completion_stress'], completion_levels = completion_stress(tr, te, pol, claims, preds, trpred, overlay)
    stress_levels.update(completion_levels)
    all_claims = pd.concat([claims, unmatched], ignore_index=True)
    all_claims['net'] = all_claims.incurred_to_date - all_claims.recoveries
    result['reporting_count_cost'] = reporting(all_claims)
    save(run / 'before_commercial_checkpoint.json', result)
    result['commercial'] = commercial(b, run, stress_levels)
    result['reserves'] = {'accepted_claims': len(accepted),
        'nonopen_claims_with_reserve': int(((accepted.status != 'open') & (accepted.reserve.abs() > 1e-8)).sum()),
        'by_line_peril': accepted.groupby(['line', 'peril']).agg(net=('net', 'sum'), reserve=('reserve', 'sum'), claims=('net', 'size')).reset_index().to_dict('records')}
    result['recipe_limit'] = 'Factores/calibración nuevos limitados a entrenamiento; ancestros T2b, A1, c_fila y selección de covariables conservan sus límites históricos. No prueba integral libre de fugas.'
    verify_inputs(run)
    result['utc_end'] = datetime.now(timezone.utc).isoformat()
    save(run / 'results.json', result)
    print(json.dumps({'results': rel(run / 'results.json'), 'comparisons': len(pairs), 'scenarios': len(stress), 'commercial_records': result['commercial']['records']}))


def check(run):
    verify_inputs(run)
    r = read(run / 'results.json')
    checks = []
    for p in sorted(run.glob('*_to_*.parquet')):
        t = pd.read_parquet(p)
        y = t.y.to_numpy()
        # Otra expresión de p=1.5, nulo por suma frente a media explícita.
        for n in NAMES:
            m = t[n].to_numpy()
            generic = 2 * (y ** .5 / (-.5 * .5) - y * m ** -.5 / -.5 + m ** .5 / .5)
            assert np.allclose(generic, dev(y, m), atol=1e-9, rtol=1e-12)
            den = 8 * (math.sqrt(len(y) * y.sum()) - np.sqrt(y).sum())
            score = 1 - generic.sum() / den
            label = p.stem
            recorded = r['comparisons'][label]['metrics']['all']['models'][n]['D2']
            assert abs(score - recorded) < 1e-12
            checks.append({'view': label, 'model': n, 'metric_independent_expression': True})
        z = np.load(run / ('bootstrap_' + p.stem + '.npz'))
        q = np.quantile(z['scores'][:, 0, 1] - z['scores'][:, 0, 0], [1 / 240, 239 / 240])
        assert np.array_equal(q, r['comparisons'][p.stem]['bootstrap']['intervals']['all']['delta_CI_family6'])
        checks.append({'view': p.stem, 'saved_draw_quantiles_exact': True})
    commercial_rows = read(run / 'veinte_primas_privadas.json')
    assert all(int(n) == 20 for n in pd.DataFrame(commercial_rows).groupby(['model', 'scenario']).size())
    assert all(c['held_target_poison_parameters_and_prices_exact'] for c in r['comparisons'].values())
    receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'author': 'Codex', 'self_review': True,
               'checks': checks, 'inputs_unchanged': True, 'commercial_all_groups_20': True,
               'result_sha256': sha(run / 'results.json'), 'new_bootstrap_or_fits': 0}
    save(run / 'verification.json', receipt)
    print(json.dumps({'verification': rel(run / 'verification.json'), 'checks': len(checks), 'success': True}))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('mode', choices=('freeze', 'analyze', 'check'))
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--reuse', type=Path)
    a = p.parse_args()
    run = a.run.resolve()
    assert run.is_relative_to(REPO / 'privado'), 'Salidas restringidas solo en privado.'
    if a.mode == 'freeze':
        freeze(run, a.reuse.resolve() if a.reuse else None)
    else:
        {'analyze': analyze, 'check': check}[a.mode](run)


if __name__ == '__main__':
    main()
