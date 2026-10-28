"""Adaptador numérico por ámbito para F3c-R; no inicia trabajo al importar."""
from pathlib import Path
import importlib.util
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd

R = Path(__file__).resolve().parents[1]
s = importlib.util.spec_from_file_location('f3cr_inherited_postprocessing', R / 'herramientas/evaluar_F3c_completo.py')
e = importlib.util.module_from_spec(s); s.loader.exec_module(e)
a = e.a; f = e.f
LINES = ['motor', 'buildings', 'contents']
CELL_ORDER = ['motor_0', 'buildings_0', 'contents_0', 'motor_1', 'buildings_1', 'contents_1']


def scope_name(excluded):
    x = tuple(sorted(set(excluded)))
    if any(k not in range(5) for k in x) or len(x) > 3:
        raise ValueError('Ámbito no registrado')
    return 'all' if not x else 'exclude_' + ''.join(map(str, x))


def train_frame(frame, excluded):
    scope_name(excluded)
    keys = frame.loc[frame.year.eq(2023), ['row_id', 'fold', 'group']]
    assert keys.row_id.is_unique and keys.group.notna().all()
    assert set(keys.fold) == set(range(5)) and keys.groupby('group').fold.nunique().max() == 1
    tr = frame.loc[frame.year.eq(2023) & ~frame.fold.isin(excluded)].copy().reset_index(drop=True)
    assert tr.row_id.is_unique and set(tr.fold).issubset(set(range(5)) - set(excluded))
    assert set(tr.line) == set(LINES) and tr.group.notna().all() and tr.groupby('group').fold.nunique().max() == 1
    # No conversión de los costes retenidos antes del selector.
    tr['y'] = pd.to_numeric(tr.y, errors='raise').astype(float)
    assert np.isfinite(tr.y).all() and tr.y.ge(0).all()
    # Normalizar el tipo DESPUÉS de excluir etiquetas protegidas. Una columna
    # object puede sumar idénticos floats con otro orden y alterar el optimizador.
    for col in [c for c in tr if c.startswith('y_')]:
        tr[col] = pd.to_numeric(tr[col], errors='raise').astype(float)
    for line in LINES:
        mask = tr.line.eq(line)
        for peril in a.PERILS[line]:
            col = 'y_' + peril
            values = pd.to_numeric(tr.loc[mask, col], errors='raise')
            assert np.isfinite(values).all() and values.ge(0).all(), (line, peril)
            tr.loc[mask, col] = values
        assert np.allclose(tr.loc[mask, ['y_' + p for p in a.PERILS[line]]].sum(axis=1), tr.loc[mask, 'y'], rtol=1e-10, atol=1e-7)
    support = tr.groupby(['line', 'new_business']).y.sum()
    assert len(support) == 6 and support.gt(0).all()
    return tr


class RealSource:
    def __init__(self, root):
        self.root = Path(root)
        self.rawT = a.t2b_raw(); self.FT = a.t2b_curves(); self.cache = {}

    def get(self, excluded, train):
        name = scope_name(excluded)
        if name not in self.cache:
            folder = self.root / name
            assert (folder / 'source_complete.json').exists(), f'Fuente pendiente: {name}'
            admission = e.read(folder / 'curves_admission.json')
            assert e.sha(folder / 'curves.json') == admission['curves_sha256']
            assert admission['poison_before_actual_filter_exact']
            self.cache[name] = {'FA': a.parse_curves(e.read(folder / 'curves.json')['full']), 'FT': self.FT,
                'raws': {'T2b': self.rawT}, 'training_ids_digest': admission['target_ids_digest'],
                'curve_receipt': str(folder / 'curves_admission.json'), 'native_receipts': []}
            for family in ['N0', 'F1']:
                all_lines = []
                for line in LINES:
                    seeds = []
                    for seed in [11, 12, 13]:
                        cp = folder / line / f'{family}_{seed}' / 'complete.json'; rec = e.read(cp)
                        assert e.sha(f.ROOT / rec['model']) == rec['model_sha256']
                        assert e.sha(f.ROOT / rec['raw']) == rec['raw_sha256']
                        seeds.append(pd.read_parquet(f.ROOT / rec['raw']).set_index('row_id').raw)
                        self.cache[name]['native_receipts'].append({'path': str(cp), 'sha256': e.sha(cp)})
                    assert all(seeds[0].index.equals(q.index) for q in seeds)
                    all_lines.append(pd.Series(np.mean(np.stack([q.to_numpy() for q in seeds]), axis=0), index=seeds[0].index))
                self.cache[name]['raws'][family] = pd.concat(all_lines)
        out = self.cache[name]
        from preparar_F3c_regularizado import digest
        assert out['training_ids_digest'] == digest(train.row_id.tolist()), 'Ancestro de otro ámbito'
        return out


class Adapter:
    def __init__(self, frame, source):
        self.frame = frame
        self.source = source
        self.base_parameters = {}; self.recipes = {}; self.counts = {'base_Tweedie_levels': 0, 'base_balance_levels': 0, 'C1_levels': 0, 'recipe_kopt_calls': 0}

    def learn_base(self, excluded):
        name = scope_name(excluded)
        if name in self.base_parameters:
            assert self.base_parameters[name]['excluded_folds'] == list(excluded)
            return self.base_parameters[name]
        tr = train_frame(self.frame, excluded)
        src = self.source.get(excluded, tr)
        params = {'excluded_folds': list(excluded), 'training_ids': sorted(tr.row_id.tolist()), 'training_groups': sorted(set(tr.group)), 'lines': {}}
        for line in LINES:
            t = tr.loc[tr.line.eq(line)].copy()
            qt, _, wt = a.completion(t, t, line, src['FT'], 'T2b')
            qa, _, wa = a.completion(t, t, line, src['FA'], 'A1')
            ee = t.exposure.to_numpy(float); yy = t.y.to_numpy(float)
            raw = {k: t.row_id.map(v).to_numpy(float) for k, v in src['raws'].items()}
            assert all(np.isfinite(q).all() for q in raw.values())
            levels = {'T2b': e.kopt(yy, np.exp(raw['T2b']) * ee * qt)}
            for family in ['N0', 'F1']:
                levels[family] = float(yy.sum() / np.sum(np.exp(raw[family]) * ee.round(4) * qa))
            params['lines'][line] = {'levels': levels, 'T2b_weights': wt, 'A1_weights': wa}
        self.counts['base_Tweedie_levels'] += 3; self.counts['base_balance_levels'] += 6
        self.base_parameters[name] = params
        return params

    def base(self, excluded, apply):
        params = self.learn_base(excluded)
        tr = train_frame(self.frame, excluded)
        src = self.source.get(excluded, tr)
        return apply_base(apply, src, params)

    def learn_recipe(self, excluded):
        name = scope_name(excluded)
        if name in self.recipes:
            assert self.recipes[name]['excluded_folds'] == list(excluded)
            return self.recipes[name]
        assert len(excluded) <= 2
        tr = train_frame(self.frame, excluded)
        pieces = []
        for fold in sorted(set(range(5)) - set(excluded)):
            held = tr.loc[tr.fold.eq(fold)].copy()
            z = self.base(tuple(sorted((*excluded, fold))), held)
            # Solo etiquetas de entrenamiento: se reponen después del forward protegido.
            ycols = ['y'] + [c for c in held if c.startswith('y_')]
            for col in ycols: z[col] = z.row_id.map(held.set_index('row_id')[col])
            pieces.append(z)
        oof = pd.concat(pieces, ignore_index=True).sort_values('row_id').reset_index(drop=True)
        assert set(oof.row_id) == set(tr.row_id)
        C1 = {line: e.kopt(oof.loc[oof.line.eq(line), 'y'].to_numpy(), oof.loc[oof.line.eq(line), 'T2b_raw'].to_numpy()) for line in LINES}
        self.counts['C1_levels'] += 3
        oof['T2b_C1'] = oof.T2b_raw * oof.line.map(C1)
        oof['mix'] = .5 * (oof.A1_F1 * oof.q + oof.T2b_C1)
        before = sum(e.COUNTS.values()); recipe = e.learn_recipe(oof)
        self.counts['recipe_kopt_calls'] += sum(e.COUNTS.values()) - before
        value = {'excluded_folds': list(excluded), 'training_ids': sorted(tr.row_id.tolist()),
            'training_groups': sorted(set(tr.group)), 'C1': C1, 'recipe': recipe}
        self.recipes[name] = value
        return value

    def features(self, excluded, apply):
        params = self.learn_recipe(excluded)
        ev = self.base(excluded, apply)
        ev['T2b_C1'] = ev.T2b_raw * ev.line.map(params['C1'])
        ev['mix'] = .5 * (ev.A1_F1 * ev.q + ev.T2b_C1)
        return from_base(ev, params['recipe'])


def apply_base(apply, src, params):
    # Pura aplicación: no lee costes de entrenamiento ni estimadores.
    assert not set(params['training_groups']) & set(apply.loc[apply.year.eq(2023), 'group']), 'Grupo retenido usado por base'
    ev = apply.copy().reset_index(drop=True)
    for col in ['y'] + [c for c in ev if c.startswith('y_')]: ev[col] = np.nan
    for col in ['q', 'T2b_raw', 'A1_N0', 'A1_F1']: ev[col] = np.nan
    for line in LINES:
        mask = ev.line.eq(line); t = ev.loc[mask]
        if not mask.any(): continue
        pp = params['lines'][line]
        qt = sum(weight * a.curve_q(t, src['FT'][(line, peril)], 'T2b') for peril, weight in pp['T2b_weights'].items())
        ev.loc[mask, 'q'] = qt
        ee = t.exposure.to_numpy(float)
        vals = {k: np.exp(t.row_id.map(v).to_numpy(float)) * pp['levels'][k] for k, v in src['raws'].items()}
        n = vals['N0'] * ee.round(4); h = vals['F1'] * ee.round(4)
        h *= float(n.sum() / h.sum())
        ev.loc[mask, 'A1_N0'] = n; ev.loc[mask, 'A1_F1'] = h
        ev.loc[mask, 'T2b_raw'] = vals['T2b'] * ee * qt
    assert np.isfinite(ev[['q', 'T2b_raw', 'A1_N0', 'A1_F1']]).all().all()
    return ev


def apply_features(apply, src, base_params, recipe_params):
    ev = apply_base(apply, src, base_params)
    ev['T2b_C1'] = ev.T2b_raw * ev.line.map(recipe_params['C1'])
    ev['mix'] = .5 * (ev.A1_F1 * ev.q + ev.T2b_C1)
    return from_base(ev, recipe_params['recipe'])


def from_base(ev, recipe):
    bridge = ev.q.to_numpy(float)
    t = ev.copy(); t['q'] = 1.; t['mix'] = ev['mix'].to_numpy() / bridge
    base = e.bycell_mult(t, e.transform_f2(t, t['mix'].to_numpy(), recipe), recipe['F2_ratio'])
    own = e.bycell_mult(t, e.transform_own(t, base, recipe), recipe['own_ratio'])
    out = ev[['row_id', 'group', 'fold', 'year', 'line', 'new_business', 'exposure']].copy()
    out['base'] = base * bridge
    out['signal'] = np.log(own / base)
    cells = e.v.cells(ev)
    out['cell'] = [CELL_ORDER.index(c) for c in cells]
    out['matched_trainlevel_full'] = own * np.array([recipe['secondary_levels']['full'][c] for c in cells]) * bridge
    out['matched_trainlevel_noown'] = base * np.array([recipe['secondary_levels']['noown'][c] for c in cells]) * bridge
    assert np.isfinite(out[['base', 'signal', 'matched_trainlevel_full', 'matched_trainlevel_noown']]).all().all()
    assert (out.base > 0).all() and np.all(out.loc[out.line.eq('buildings'), 'signal'] == 0)
    return out


def crossfit_features(adapter, excluded):
    tr = train_frame(adapter.frame, excluded)
    pieces = []
    for fold in sorted(set(range(5)) - set(excluded)):
        held = tr.loc[tr.fold.eq(fold)]
        part = adapter.features(tuple(sorted((*excluded, fold))), held)
        part['y'] = part.row_id.map(held.set_index('row_id').y)
        pieces.append(part)
    out = pd.concat(pieces, ignore_index=True).sort_values('row_id').reset_index(drop=True)
    assert set(out.row_id) == set(tr.row_id)
    return out
