"""Productor A1 por ámbito de entrenamiento; etapas reanudables y sin scoring."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import gc
import importlib.util
import json
import os
import sys
import time

R = Path(__file__).resolve().parents[1]; ROOT = R.parents[1]
sys.path.insert(0, str(R / 'herramientas'))
import preparar_F3c_regularizado as p
spec = importlib.util.spec_from_file_location('f3cr_original_source', R / 'herramientas/validar_F3c_completo.py')
f = importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
np = f.np; pd = f.pd; a = f.a; lgb = f.lgb
OUT = p.OUT.parent / 'source_scoped'
PLAN = R / 'registro/semana2_F3c_regularizado_fuente_plan.json'


def dump(path, value): return p.dump(path, value)
def read(path): return p.read(path)
def sha(path): return p.sha(path)
def utc(): return datetime.now(timezone.utc).isoformat()


def event(kind, **data):
    value = {'utc': utc(), 'pid': os.getpid(), 'event': kind, **data}
    with (OUT / 'events.jsonl').open('a', encoding='utf-8') as h: h.write(json.dumps(value) + '\n')
    print(json.dumps(value), flush=True)


def register():
    p.guard(); inv = read(p.OUT / 'scope_inventory.json'); syn = read(p.OUT / 'synthetic_optimizer.json')
    assert inv['scope_membership_passed'] and syn['all_passed']
    assert not PLAN.exists() and not OUT.exists(); OUT.mkdir()
    paths = [Path(__file__), p.OUT / 'scope_inventory.json', p.OUT / 'synthetic_optimizer.json',
        R / 'herramientas/validar_F3c_completo.py', R / 'herramientas/ampliar_validacion_cadena_f3c.py',
        f.ACTIVE / 'prepared/developed_claims.parquet', f.ACTIVE / 'prepared/emerging_claims.parquet']
    paths += [f.ACTIVE / 'prepared' / f'{market}_{line}.parquet' for market in ['developed', 'emerging'] for line in f.LINES]
    paths += [f.LEGACY / 'noche/salidas' / market / 'asignacion.parquet' for market in ['s1', 's2']]
    plan = {'author': 'Codex', 'utc': utc(), 'purpose': 'Produce strict upstream inputs required by admitted F3c-R design, no evaluation yet',
        'scopes': [{'scope': s['scope'], 'excluded_folds': s['excluded_folds']} for s in inv['scopes']],
        'source_recipe': 'Original full F3c N0/F1 three seeds11/12/13; same fields/params/source2021-23, source fold0 early stopping; only eligible emerging claims in pooled RKM. Full source and single-fold N0seed11 reused only if arguments/model/raw match.',
        'scope_filter': 'Filter assigned accepted claim pools by exact admitted source/target row keys before RKM; source-inner excludes developed fold0, target excludes every named fold. No filtering solely by one legacy excluded_fold attribute.',
        'RKM_definition_unchanged': 'Original per-peril pooled reverseKM weekly curve; same historical .995cost-weight cap belongs only to reporting learner, no removal/cap of price targetT0.',
        'budget': {'source_scopes': 26, 'model_pairs_per_scope': 18, 'new_primary_native_calls_upper': 900,
            'new_primary_native_calls_if15singlefold_pairs_exact': 870, 'primary_RKM_bundles_max': 52,
            'adverse_RKM_bundles_max_separate': 52, 'source_adverse_native_refits_this_stage': 0,
            'adverse_scope': 'held claims poisoned before actual scope filter; rebuild curves and native fit inputs, use exact argument-hash memoization for fixed training. No new native replay claimed.',
            'synthetic_reporting_fits': 0, 'target_calibrator_real_fits': 0, 'scores': 0, '2025_inference': 0, 'submissions': 0},
        'checkpoints': 'Every early-stop selection and full native fit journals before invocation; completed same-argument artifacts verified and reused, never overwritten. Sequential source scopes/lines,2threads/native.',
        'admission': 'Full-scope curve parity and protected-claim poison invariance in all26 scopes required before source fits. Do not borrow full-scope source model into protected scope.',
        'source_pair_budget_is_not_runtime_estimate': True,
        'sources': {p.rel(q): sha(q) for q in paths}}
    dump(PLAN, plan)
    forum = p.post('Codex. Registro productor estricto de fuente F3c-R tras conciliar26ambitos. Mantengo A1N0/F1,tres semillas,campos,parametros,fold fuente y mezcla. La unica diferencia upstream es excluir de las curvas agrupadas todos los grupos emergentes protegidos. Primero exijo paridad del ambito completo y veneno antes del filtro de cada ambito; luego ajusto/reutilizo por argumentos exactos. Presupuesto maximo900invocaciones nativas primarias nuevas (870si los15pares N0de fold son identicos),52bundles RKMprimarios y52adversos separados; es coste,no tiempo ni ajustes ya realizados. Cero calibrador real,score,2025oenvio en esta etapa. Replays fuente nativos no incluidos ni afirmados: verificacion de entradas adversas y memoizacion exacta. Se conserva todo fallo y checkpoint. Plan '+p.rel(PLAN)+' SHA '+sha(PLAN)+'.',
        'COD-S2-20261028-F3CR-FUENTE-ESTRICTA-PREVIO', 'F3c-R: productor de fuente por ambito y presupuesto previo')
    dump(OUT / 'registration.json', {'plan_sha256': sha(PLAN), 'forum': forum})
    event('registered', budget=plan['budget'])


def guard():
    assert sha(PLAN) == read(OUT / 'registration.json')['plan_sha256']
    for q, h in read(PLAN)['sources'].items(): assert sha(ROOT / q) == h, q


def curve_bundle(asg, source_ids, target_ids, inner_ids):
    s = asg['developed']; e = asg['emerging']
    ee = e.loc[e.row_id.isin(target_ids)].copy()
    result = {}
    for name, ids in [('inner', inner_ids), ('full', source_ids)]:
        dd = s.loc[s.row_id.isin(ids)].copy()
        dummy = pd.DataFrame()
        cost, count, receipt = a.rkm({'developed': dd, 'emerging': ee}, dummy, dummy)
        result[name] = a.curves_json(cost); result[name + '_count'] = a.curves_json(count)
        result[name + '_receipt'] = receipt
    return result


def prepare():
    guard()
    src = pd.concat([pd.read_parquet(f.ACTIVE / 'prepared' / f'developed_{line}.parquet',
        columns=['row_id', 'year', 'fold'], filters=[('year', '<=', 2023)]) for line in f.LINES], ignore_index=True)
    em = pd.concat([pd.read_parquet(f.ACTIVE / 'prepared' / f'emerging_{line}.parquet',
        columns=['row_id', 'year', 'fold'], filters=[('year', '==', 2023)]) for line in f.LINES], ignore_index=True)
    asg = {market: pd.read_parquet(f.ACTIVE / 'prepared' / f'{market}_claims.parquet') for market in ['developed', 'emerging']}
    source_ids = set(src.row_id); inner_ids = set(src.loc[src.fold != 0, 'row_id'])
    receipts = []
    for scope in read(PLAN)['scopes']:
        folder = OUT / scope['scope']; folder.mkdir(exist_ok=True)
        path = folder / 'curves.json'
        if path.exists(): receipts.append(read(folder / 'curves_admission.json')); continue
        ids = set(em.loc[~em.fold.isin(scope['excluded_folds']), 'row_id'])
        primary = curve_bundle(asg, source_ids, ids, inner_ids)
        poison = {market: table.copy() for market, table in asg.items()}
        protected = ~poison['emerging'].row_id.isin(ids)
        poison['emerging'].loc[protected, 'net'] = -987654.
        adverse = curve_bundle(poison, source_ids, ids, inner_ids)
        exact = primary == adverse
        assert exact, scope
        parity = None
        if scope['scope'] == 'all':
            old = read(f.ACTIVE / 'curves_full.json')
            parity = all(primary[key] == old[key] for key in ['inner', 'full', 'inner_count', 'full_count'])
            assert parity, 'Full source curve mismatch'
        dump(path, primary)
        rec = {'scope': scope, 'target_rows': len(ids), 'protected_claim_rows_altered': int(protected.sum()),
            'target_ids_digest': p.digest(ids), 'curves_sha256': sha(path),
            'poison_before_actual_filter_exact': exact, 'full_scope_legacy_curve_parity': parity,
            'primary_RKM_bundles': 2, 'adverse_RKM_bundles_separate': 2}
        dump(folder / 'curves_admission.json', rec); receipts.append(rec)
        event('curves_complete', scope=scope['scope'], target_rows=len(ids))
    dump(OUT / 'curves_complete.json', {'utc': utc(), 'all_passed': True, 'scopes': receipts,
        'primary_RKM_bundles': 52, 'adverse_RKM_bundles_separate': 52, 'native_fits': 0})
    event('all_curves_admitted', scopes=len(receipts))


def journal(scope, line, family, seed, stage):
    with (OUT / 'native_attempts.jsonl').open('a', encoding='utf-8') as h:
        h.write(json.dumps({'utc': utc(), 'scope': scope, 'line': line, 'family': family, 'seed': seed, 'stage': stage}) + '\n')


def run_scope(scope_name):
    guard(); assert read(OUT / 'curves_complete.json')['all_passed']
    names = {s['scope'] for s in read(PLAN)['scopes']}; assert scope_name in names
    folder = OUT / scope_name
    if (folder / 'source_complete.json').exists():
        for line in f.LINES:
            for family in ['N0', 'F1']:
                for seed in f.SEEDS:
                    rec = read(folder / line / f'{family}_{seed}' / 'complete.json')
                    assert sha(ROOT / rec['model']) == rec['model_sha256'] and sha(ROOT / rec['raw']) == rec['raw_sha256']
        event('completed_scope_reused', scope=scope_name); return
    assert sha(folder / 'curves.json') == read(folder / 'curves_admission.json')['curves_sha256']
    curves = read(folder / 'curves.json'); F = {k: a.parse_curves(curves[k]) for k in ['inner', 'full']}
    for line in f.LINES:
        src, em, _, _ = f.source_inputs(line)
        inner = src.fold.ne(0).to_numpy(); di = src[inner].reset_index(drop=True); dv = src[~inner].reset_index(drop=True)
        qi, qv, wi = a.completion(di, dv, line, F['inner'], 'A1')
        qf, _, wf = a.completion(src, em, line, F['full'], 'A1')
        yi = di.y.to_numpy(float); yv = dv.y.to_numpy(float); yf = src.y.to_numpy(float)
        oi = np.log(di.exposure.to_numpy().round(4) * qi); ov = np.log(dv.exposure.to_numpy().round(4) * qv)
        of = np.log(src.exposure.to_numpy().round(4) * qf)
        bi = float(np.log(yi.sum() / np.exp(oi).sum())); bf = float(np.log(yf.sum() / np.exp(of).sum()))
        for family in ['N0', 'F1']:
            feat = a.a1_features(src, line); ev = a.a1_features(em, line)
            if family == 'F1':
                for col in ['f1_siniestros_previos', 'f1_anios_observados']:
                    feat[col] = src[col].to_numpy(); ev[col] = em[col].to_numpy()
            ci = {c: sorted(feat.loc[inner, c].unique().tolist()) for c in feat if c in a.CAT}
            cf = {c: sorted(feat[c].unique().tolist()) for c in feat if c in a.CAT}
            Xi = a.matrix(feat[inner].reset_index(drop=True), ci); Xv = a.matrix(feat[~inner].reset_index(drop=True), ci)
            Xf = a.matrix(feat, cf); Xe = a.matrix(ev, cf); del feat, ev; gc.collect()
            baseparams = read(f.ACTIVE / 'models/full' / f'{line}_receipt.json')['params']
            for seed in f.SEEDS:
                pp = {**baseparams, 'seed': seed}; dest = folder / line / f'{family}_{seed}'; dest.mkdir(parents=True, exist_ok=True)
                ah = f.v.digest(Xi, yi, oi + bi, Xv, yv, ov + bi, Xf, yf, of + bf, Xe, ci, cf, pp, wi, wf)
                done = dest / 'complete.json'
                if done.exists():
                    rec = read(done); assert rec['arguments_sha256'] == ah
                    assert sha(ROOT / rec['model']) == rec['model_sha256'] and sha(ROOT / rec['raw']) == rec['raw_sha256']; continue
                cache = None
                if scope_name == 'all': cache = read(f.source_folder(line, 'baseline', family, seed) / 'complete.json')
                elif len(scope_name.removeprefix('exclude_')) == 1 and family == 'N0' and seed == 11:
                    old = f.ACTIVE / 'models' / ('fold' + scope_name[-1]); oldrec = read(old / f'{line}_receipt.json')
                    if oldrec['arguments_sha256'] == ah:
                        cache = {'arguments_sha256': ah, 'model': p.rel(old / f'{line}.txt'), 'raw': p.rel(old / f'{line}_raw.parquet'),
                            'model_sha256': oldrec['model_sha256'], 'raw_sha256': oldrec['raw_file_sha256'],
                            'rounds': oldrec['rounds'], 'source_center': oldrec['source_center']}
                if cache:
                    assert cache['arguments_sha256'] == ah
                    assert sha(ROOT / cache['model']) == cache['model_sha256'] and sha(ROOT / cache['raw']) == cache['raw_sha256']
                    dump(done, {**cache, 'reused_exact': True, 'scope': scope_name}); event('reused', scope=scope_name, line=line, family=family, seed=seed); continue
                rc = dest / 'inner_complete.json'
                if rc.exists():
                    rr = read(rc); assert rr['arguments_sha256'] == ah; rounds = rr['rounds']
                else:
                    event('native_start', scope=scope_name, line=line, family=family, seed=seed, stage='inner')
                    journal(scope_name, line, family, seed, 'inner')
                    bst = lgb.train(pp, lgb.Dataset(Xi, label=yi, init_score=oi + bi), 4000,
                        valid_sets=[lgb.Dataset(Xv, label=yv, init_score=ov + bi)], callbacks=[lgb.early_stopping(400, verbose=False)])
                    rounds = max(1, bst.best_iteration); dump(rc, {'arguments_sha256': ah, 'rounds': rounds}); del bst; gc.collect()
                assert f.psutil.virtual_memory().available > 500 * 2**20
                event('native_start', scope=scope_name, line=line, family=family, seed=seed, stage='full')
                journal(scope_name, line, family, seed, 'full')
                bst = lgb.train(pp, lgb.Dataset(Xf, label=yf, init_score=of + bf), rounds)
                center = float(np.log(np.average(np.exp(bst.predict(Xf, raw_score=True, num_threads=2)), weights=src.exposure.to_numpy().round(4))))
                raw = bst.predict(Xe, raw_score=True, num_threads=2) - center
                mp = dest / 'model.txt'; rp = dest / 'raw.parquet'; bst.save_model(str(mp))
                pd.DataFrame({'row_id': em.row_id.to_numpy(), 'raw': raw}).to_parquet(rp, index=False)
                dump(done, {'utc': utc(), 'scope': scope_name, 'arguments_sha256': ah, 'model': p.rel(mp), 'raw': p.rel(rp),
                    'model_sha256': sha(mp), 'raw_sha256': sha(rp), 'rounds': rounds, 'source_center': center, 'reused_exact': False})
                event('native_pair_complete', scope=scope_name, line=line, family=family, seed=seed); del bst, raw; gc.collect()
            del Xi, Xv, Xf, Xe; gc.collect()
        del src, em, di, dv; gc.collect()
    dump(folder / 'source_complete.json', {'utc': utc(), 'scope': scope_name, 'model_pairs': 18, 'scores': 0})
    event('source_scope_complete', scope=scope_name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['register', 'prepare', 'run'])
    parser.add_argument('--scope'); args = parser.parse_args()
    if args.mode == 'run':
        lease = OUT / 'source_worker_lease.json'
        owner = {'pid': os.getpid(), 'process_created': f.psutil.Process().create_time(), 'scope': args.scope, 'utc': utc()}
        dump(lease, owner)
        try:
            run_scope(args.scope)
        finally:
            if read(lease) == owner: lease.unlink()
    else: globals()[args.mode]()
