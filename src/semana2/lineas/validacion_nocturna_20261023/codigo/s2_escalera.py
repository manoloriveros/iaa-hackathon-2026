"""Escalera de desarrollo 2023 del emergente: OOF por cinco folds de cliente.

Uso: python s2_escalera.py SPEC [SPEC ...]   (SPEC en ESPECS); guarda salidas/s2/oof/SPEC.parquet y un resumen.
"""
import json, pathlib, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import marco as M
from variables import features, CATEG, weather_other_year

R = pathlib.Path('/home/claude/noche'); O = R / 'salidas/s2'; (O / 'oof').mkdir(parents=True, exist_ok=True)
LINES = ['motor', 'buildings', 'contents']
_cache = {}


def data(line):
    if line not in _cache:
        b = pd.read_parquet(O / f'base_{line}.parquet')
        X, cols, df = features(b, line, 's2')
        _cache[line] = (b, X, cols, df)
    return _cache[line]


def dev_set(line, years=(2023,)):
    b, X, cols, df = data(line)
    m = (b.split == 'train') & b.year.isin(years)
    return b[m].reset_index(drop=True), X[m].reset_index(drop=True), cols, df[m].reset_index(drop=True)


def lg_dev(line, row_ids, tag='dev21222324'):
    g = pd.read_parquet(R / f'salidas/transfer/lg_{tag}_{line}_em.parquet').set_index('row_id').lg_dev
    return g.reindex(row_ids).values


def run(spec_name, spec, years=(2023,)):
    rows = []
    for line in LINES:
        b, X, cols, df = dev_set(line, years)
        use = spec.get('cols', lambda c, l: c)(cols, line)
        Xu = X[use].copy()
        if spec.get('exposure_feature'):
            Xu['exposure_model'] = b.exposure_model.values
        if spec.get('transfer'):
            b = b.copy(); b['lg'] = lg_dev(line, b.row_id.values, spec['transfer'])
            b['eef_coste'] = b.eef_coste * np.exp(b.lg)  # el offset lleva la relatividad del desarrollado
        if spec.get('weather'):
            Xu = pd.concat([Xu, weather_other_year(df, 's2', spec['weather'], 'otro')], axis=1)
        fold = M.fold_of(b.customer_id.values)
        y = b.t0.values; e = b.eef_coste.values; off = np.log(e)
        e_out = (b.eef_coste / np.exp(b.lg)).values if spec.get('transfer') else e
        mu = np.zeros(len(b))
        for k in range(5):
            tr, te = fold != k, fold == k
            if spec.get('balance', True):  # BAL-N1: nivel del modelo igualado al total del entrenamiento
                both = spec['fit'](line, Xu[tr], y[tr], off[tr], pd.concat([Xu[te], Xu[tr]]), np.concatenate([off[te], off[tr]]), b[tr], pd.concat([b[te], b[tr]]))
                nte = te.sum(); fac = y[tr].sum() / both[nte:].sum()
                mu[te] = both[:nte] * fac
            else:
                mu[te] = spec['fit'](line, Xu[tr], y[tr], off[tr], Xu[te], off[te], b[tr], b[te])
        rows.append(pd.DataFrame({'row_id': b.row_id, 'line': line, 'year': b.year, 'customer_id': b.customer_id,
                                  'address_id': b.address_id, 'new_business': b.new_business, 'y': y, 'eef': e_out,
                                  'exposure': b.exposure_model, 'mu': mu, 'fold': fold}))
    out = pd.concat(rows, ignore_index=True)
    out.to_parquet(O / 'oof' / f'{spec_name}.parquet', index=False)
    return out


def summary(o):
    r = {'D2_global': round(M.d2(o.y, o.mu), 5)}
    for l, g in o.groupby('line'):
        r[f'D2_{l}'] = round(M.d2(g.y, g.mu), 5); r[f'AE_{l}'] = round(g.y.sum() / g.mu.sum(), 4)
    for nb, g in o.groupby('new_business'):
        r[f'AE_nb{int(nb)}'] = round(g.y.sum() / g.mu.sum(), 4)
    return r


# ------------------------------------------------------------------ especificaciones

def f_rate(line, Xtr, y, off, Xte, offte, btr, bte):
    return np.exp(offte) * y.sum() / np.exp(off).sum()


def f_rate_tw(line, Xtr, y, off, Xte, offte, btr, bte):
    m = np.exp(off)  # nivel que minimiza la desviación Tweedie 1,5 en el entrenamiento
    return np.exp(offte) * (y / np.sqrt(m)).sum() / np.sqrt(m).sum()


def mk_glm(alpha, nbins=6):
    def f(line, Xtr, y, off, Xte, offte, btr, bte):
        cols = list(Xtr.columns)
        A, Bm = M.design_glm(Xtr, Xte, cols, CATEG | {c for c in cols if str(Xtr[c].dtype) == 'category'}, nbins=nbins)
        return M.fit_glm_tweedie(A, y, off, Bm, offte, alpha)[0]
    return f


def mk_fs(af, as_, nbins=6):
    def f(line, Xtr, y, off, Xte, offte, btr, bte):
        cols = list(Xtr.columns)
        A, Bm = M.design_glm(Xtr, Xte, cols, CATEG | {c for c in cols if str(Xtr[c].dtype) == 'category'}, nbins=nbins)
        return M.fit_glm_fs(A, btr.n_claims.values, y, off, Bm, offte, af, as_)[0]
    return f


def mk_gbm(params=None):
    def f(line, Xtr, y, off, Xte, offte, btr, bte):
        return M.fit_gbm_tweedie(Xtr, y, off, Xte, offte, btr.customer_id.values, params)[0]
    return f


def few(keep):
    return lambda cols, line: [c for c in cols if c in keep.get(line, keep.get('all', []))]


NONE = {'all': []}
ESPECS = {
    'T1_dev_nivel': {'fit': f_rate, 'transfer': 'dev21222324'},
    'T2_dev_glm_nb_reg_a10': {'fit': mk_glm(10.0), 'transfer': 'dev21222324', 'cols': few({'all': ['new_business', 'region']})},
    'T2_dev_glm_nb_reg_a100': {'fit': mk_glm(100.0), 'transfer': 'dev21222324', 'cols': few({'all': ['new_business', 'region']})},
    'T2_dev_nb_a0.01': {'fit': mk_glm(0.01), 'transfer': 'dev21222324', 'cols': few({'all': ['new_business']})},
    'T2_dev_nb_a1': {'fit': mk_glm(1.0), 'transfer': 'dev21222324', 'cols': few({'all': ['new_business']})},
    'T2_dev_nbreg_a1': {'fit': mk_glm(1.0), 'transfer': 'dev21222324', 'cols': few({'all': ['new_business', 'region']})},
    'T2_dev_nbexp_a1': {'fit': mk_glm(1.0), 'transfer': 'dev21222324', 'cols': few({'all': ['new_business']}), 'exposure_feature': True},
    'T1v2_nivel': {'fit': f_rate, 'transfer': 'v2'},
    'T1v2s12_nivel': {'fit': f_rate, 'transfer': 'v2s12'},
    'T1v2s13_nivel': {'fit': f_rate, 'transfer': 'v2s13'},
    'T1v2b3_nivel': {'fit': f_rate, 'transfer': 'v2b3'},
    'A1fix_nivel': {'fit': f_rate, 'transfer': 'A1fix'},
    'A1fixb3_nivel': {'fit': f_rate, 'transfer': 'A1fixb3'},
    'A1fixF1_nivel': {'fit': f_rate, 'transfer': 'A1fixF1'},
    'A1fixF1b3_nivel': {'fit': f_rate, 'transfer': 'A1fixF1b3'},
    'ROBcap_nivel': {'fit': f_rate, 'transfer': 'robcapb3'},
    'ROBreg_nivel': {'fit': f_rate, 'transfer': 'robregb3'},
    'ROBcapreg_nivel': {'fit': f_rate, 'transfer': 'robcapregb3'},
    'ROBglmgbm_nivel': {'fit': f_rate, 'transfer': 'robglmgbmb3'},
    'ROBrej_nivel': {'fit': f_rate, 'transfer': 'robrejb3'},
    'T1v3_clima_nivel': {'fit': f_rate, 'transfer': 'v3'},
    'T1v2_nivel_tw': {'fit': f_rate_tw, 'transfer': 'v2', 'balance': False},
    'L0_tasa_tw': {'fit': f_rate_tw, 'balance': False},
    'T2v2_nbreg_a1': {'fit': mk_glm(1.0), 'transfer': 'v2', 'cols': few({'all': ['new_business', 'region']})},
    'T2v2_reg_a1': {'fit': mk_glm(1.0), 'transfer': 'v2', 'cols': few({'all': ['region']})},
    'T1_glm_nivel': {'fit': f_rate, 'transfer': 'glm1'},
    'T2_glm_reg_a1': {'fit': mk_glm(1.0), 'transfer': 'glm1', 'cols': few({'all': ['region']})},
    'T2_dev_reg_a1': {'fit': mk_glm(1.0), 'transfer': 'dev21222324', 'cols': few({'all': ['region']})},
    'T2_glm_nbreg_a1': {'fit': mk_glm(1.0), 'transfer': 'glm1', 'cols': few({'all': ['new_business', 'region']})},
    'T2_dev_glm_todo_a100': {'fit': mk_glm(100.0), 'transfer': 'dev21222324'},
    'T2_dev_glm_todo_a1000': {'fit': mk_glm(1000.0), 'transfer': 'dev21222324'},
    'T3_dev_gbm': {'fit': mk_gbm({'num_leaves': 4, 'min_data_in_leaf': 800, 'learning_rate': 0.01}), 'transfer': 'dev21222324', 'exposure_feature': True},
    'L0_tasa': {'fit': f_rate},
    'L1_glm_a1e-4': {'fit': mk_glm(1e-4)},
    'L1_glm_a1e-3': {'fit': mk_glm(1e-3)},
    'L1_glm_a1e-2': {'fit': mk_glm(1e-2)},
    'L1_glm_a1e-1': {'fit': mk_glm(1e-1)},
    'L1_glm_a1': {'fit': mk_glm(1.0)},
    'L1_glm_a10': {'fit': mk_glm(10.0)},
    'L1_glm_a100': {'fit': mk_glm(100.0)},
    'L2_fs_a1e-3': {'fit': mk_fs(1e-3, 1e-2)},
    'L2_fs_a1e-2': {'fit': mk_fs(1e-2, 1e-1)},
    'L3_gbm': {'fit': mk_gbm()},
    'L1_glm_a10_nobal': {'fit': mk_glm(10.0), 'balance': False},
    'L1_glm_a30': {'fit': mk_glm(30.0)},
    'L1_glm_a300': {'fit': mk_glm(300.0)},
    'L3_gbm_lento': {'fit': mk_gbm({'num_leaves': 4, 'min_data_in_leaf': 800, 'learning_rate': 0.01})},
}

if __name__ == '__main__':
    res = {}
    rf = O / 'escalera_resumen.json'
    if rf.exists(): res = json.load(open(rf))
    for s in sys.argv[1:]:
        t = time.time(); o = run(s, ESPECS[s]); r = summary(o); r['segundos'] = round(time.time() - t, 1)
        res[s] = r; print(s, r, flush=True)
        json.dump(res, open(rf, 'w'), indent=1)
