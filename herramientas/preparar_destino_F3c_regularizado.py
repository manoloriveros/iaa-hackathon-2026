"""Prerregistro y control sintético del adaptador anidado completo de F3c-R.

No entrena fuente nativa ni produce un CSV del concurso. Las fuentes artificiales
sustituyen exclusivamente a los árboles y RKM; el procesamiento destino es real.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import itertools
import json
import sys
import traceback
from unittest.mock import patch

R = Path(__file__).resolve().parents[1]
ROOT = R.parents[1]
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from sklearn.metrics import mean_tweedie_deviance
import entradas_F3c_regularizado as inp
import calibrador_F3c_regularizado as model
import preparar_F3c_regularizado as io

OUT = R / 'privado/semana2/F3c_regularizado_20261028/target_adapter'
PLAN = R / 'registro/semana2_F3c_regularizado_destino_plan.json'
e = inp.e


def utc(): return datetime.now(timezone.utc).isoformat()
def sha(path): return io.sha(Path(path))
def read(path): return io.read(Path(path))
def dump(path, value): return io.dump(Path(path), value)


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False)


def state(adapter):
    return {'base': adapter.base_parameters, 'recipes': adapter.recipes}


def signature(adapter):
    return hashlib.sha256(canonical(state(adapter)).encode()).hexdigest()


def protected_branch(adapter, fold):
    tr = inp.crossfit_features(adapter, (fold,))
    held = adapter.frame.loc[adapter.frame.year.eq(2023) & adapter.frame.fold.eq(fold)]
    va = adapter.features((fold,), held).sort_values('row_id').reset_index(drop=True)
    return tr, va


def estimate(t, lam):
    return model.fit(t.base, t.signal, t.cell, t.y, lam)


def forward(t, artifact):
    return model.predict(t.base, t.signal, t.cell, artifact)


def bundle(adapter):
    """Mismo selector que se conectará a fuentes reales, sin etiquetas2024."""
    totals = np.zeros(3); models = []; branches = {}
    for fold in range(5):
        tr, va = protected_branch(adapter, fold)
        # Etiqueta exterior solo para evaluar el selector, después del aprendizaje.
        y = va.row_id.map(adapter.frame.set_index('row_id').y).to_numpy(float)
        members = []
        for k, lam in enumerate(model.LAMBDAS):
            fitted = estimate(tr, lam); mu = forward(va, fitted)
            loss = float(np.sum(4 * (y / np.sqrt(mu) + np.sqrt(mu) - 2 * np.sqrt(y))))
            totals[k] += loss
            members.append({'model': fitted, 'held_deviance_sum': loss})
        models.append(members); branches[fold] = (tr, va)
    selection = model.select(totals)
    tr = inp.crossfit_features(adapter, ())
    final = estimate(tr, selection['lambda'])
    held = adapter.frame.loc[adapter.frame.year.eq(2024)]
    va = adapter.features((), held).sort_values('row_id').reset_index(drop=True)
    return {'selection': selection, 'members': models, 'final': final}, tr, va, forward(va, final), branches


def fixture():
    rng = np.random.default_rng(20261028); rows = []
    perils = sorted(set(sum(inp.a.PERILS.values(), [])))
    for year, folds in [(2023, range(5)), (2024, [-1])]:
        for fold, line, nb, j in itertools.product(folds, inp.LINES, [0, 1], range(30)):
            group = f'g{fold}_{nb}_{j}'
            start = pd.Timestamp(f'{year}-01-01') + pd.Timedelta(days=3*j)
            days = 30 + (j*11) % 260
            mean = (100 + 90*inp.LINES.index(line)) * (1+.3*nb) * days/365
            y = float(rng.gamma(2, mean/1.1)) if j % 3 else 0.
            weights = rng.dirichlet(np.ones(len(inp.a.PERILS[line])))
            row = dict(row_id=f'{year}_{fold}_{line}_{nb}_{j}', group=group, fold=fold, year=year,
                line=line, new_business=nb, exposure=days/365, period_start=start,
                period_end=start+pd.Timedelta(days=days-1), y=y, ncb_years=j%12,
                prior_claims_5y=j%4, gender=['F','M','U'][j%3], works_from_home=bool(j%2),
                marketing_segment=['A','B','C','D'][j%4])
            row.update({'y_'+p: np.nan for p in perils})
            row.update({'y_'+p: y*w for p,w in zip(inp.a.PERILS[line], weights)})
            rows.append(row)
    return pd.DataFrame(rows)


class SyntheticSource:
    """Dependencia explícita de los costes permitidos, sin modelos de concurso."""
    def __init__(self, frame):
        self.frame = frame; self.cache = {}

    def get(self, excluded, train):
        name = inp.scope_name(excluded)
        keys = self.frame.loc[self.frame.year.eq(2023) & ~self.frame.fold.isin(excluded), 'row_id']
        assert set(train.row_id) == set(keys), 'Ancestro de otro ámbito'
        if name not in self.cache:
            allowed = inp.train_frame(self.frame, excluded)
            level = float(allowed.y.mean()); variation = np.tanh(level/150)
            days = np.arange(5000)
            FT = {(line,p): 1 - .85*np.exp(-days/(70+9*k)) for line in inp.LINES for k,p in enumerate(inp.a.PERILS[line])}
            FA = {key: 1-(1-val)*(1-.15*variation) for key,val in FT.items()}
            t = self.frame
            offset = np.log(100+90*t.line.map(dict(zip(inp.LINES, range(3)))).to_numpy())
            effect = .12*np.sin(np.arange(len(t))) + .06*t.new_business.to_numpy()
            raws = {'T2b': offset+effect, 'N0': offset+.8*effect+.05*variation,
                    'F1': offset+effect*(1+.3*variation)+.04*variation}
            self.cache[name] = {'FT': FT, 'FA': FA, 'raws': {k: pd.Series(v, index=t.row_id) for k,v in raws.items()}}
        return self.cache[name]


def register():
    assert not PLAN.exists() and not OUT.exists(), 'Prerregistro ya existe'
    OUT.mkdir(parents=True)
    dependencies = [Path(__file__), Path(inp.__file__), Path(model.__file__), Path(io.__file__),
        R/'herramientas/evaluar_F3c_completo.py', R/'herramientas/validar_F3c_completo.py',
        R/'herramientas/ampliar_validacion_cadena_f3c.py', R/'herramientas/validar_cadena_f3c.py',
        R/'herramientas/auditar_evaluacion_documento.py', e.f.PLAN,
        R/'registro/semana2_F3c_regularizado_plan.json', R/'registro/semana2_F3c_regularizado_fuente_plan.json']
    plan = {'author': 'Codex', 'utc': utc(), 'candidate': 'F3c-R', 'phase': 'nested_numeric_target_adapter',
        'hypothesis': 'Regularizar los niveles y la intensidad del bloque propio reduce fragilidad de negocio nuevo sin cambiar las variables ni el tronco F3c; todo aprendizaje del selector excluye sus grupos retenidos.',
        'configuration': {'folds': 'cinco guardados2023', 'base_scopes': 26, 'recipe_scopes': 16,
            'source': '18 pares A1 N0/F1 por ámbito ya preinscritos; T2b desarrollado fijo',
            'target': 'base por ramo; C1/F2/own aprendidos solo con entradas OOF internas; misma normalización por lote histórica',
            'model': 'b*exp(a_cell+gamma_cell*z); 6a,4gamma; gamma edificios0; resto0..1',
            'lambda': model.LAMBDAS, 'selection': 'suma devianza2023 en5folds; empate1e-10 relativo favorece lambda mayor',
            'mixture': [.5,.5], 'historical_A_M1_conditioning_retained': True,
            'inapplicable_peril_NaN': 'Conservar NA fuera de su ramo; validar solo periles aplicables y su suma frente a T0. No imputar un peril aplicable.'},
        'comparators_clarified_before_new_fit_or_score': {
            'controlled': 'matched_trainlevel_full reconstruido con exactamente los mismos26ámbitos y preprocesamiento de F3c-R',
            'practical': 'public_full temporal original congelado en validación completa20261027',
            'old_trainlevel_full': 'Conservado como evidencia histórica; no aísla calibración al cambiar ancestros del tronco.',
            'family': 20, 'new_contrasts': 2, 'thresholds': 'Sin cambio frente al plan F3c-R original; IC condicionales después de búsqueda adaptativa.'},
        'synthetic_controls': ['flujo completo26bases/16recetas/selector', 'costes2024 no numéricos antes del selector',
            'costes de cadafold2023 retenido no numéricos antes de producir su rama', 'control positivo parcial de entrenamiento',
            'replay JSON con estimadores bloqueados', 'extremos gamma0/1 equivalentes a controles completos',
            'devianza por sklearn y solución final por SLSQP', 'rechazo ancestro incorrecto y grupo en2folds',
            'renovación temporal permite grupo2023 repetido2024; exclusión interna sigue estricta'],
        'budget': {'synthetic_calibrator_fits': 49, 'synthetic_native_source_fits': 0,
            'synthetic_target_analytic_levels': '26bases/16recetas por bundle; dosbundles, cinco ramas adversas, un positivo y controles endpoint sin fit; contabilizar llamadas reales.',
            'real_primary_calibrator_fits_when_ready': 16, 'real_adverse_calibrator_fits_reserved': 16,
            'real_base_levels_primary': 234, 'real_C1_levels_primary': 48,
            'recipe_kopt_bound_per_scope': '66+sum(nunique(variable) para líneas elegibles de los3bloques propios); contar real, nunca usar esta cota como ejecución.',
            'new_native_source_or_C0_from_adapter': 0, 'new2025_predictions': 0, 'submissions': 0},
        'real_release_gate': 'No ajustar destino real hasta26recibos fuente, hashes, controles sintéticos y comentario previo. La corrida actual solo habilita el adaptador; no promociona ni envía.',
        'dependencies': [{'path':io.rel(p), 'sha256':sha(p)} for p in dependencies]}
    dump(PLAN, plan)
    body = ('Codex. Registro el adaptador numérico completo de F3c-R antes de probarlo. Mantiene las26bases/16recetas por ámbito y el selector ya propuesto; verifica los costes retenidos antes de cualquier conversión. '
        'Aclaro la comparación: la contracción se medirá contra trainlevel_full del MISMO flujo anidado; F3c public_full temporal original sigue como referencia práctica. Dos contrastes, familia20 y umbrales previos intactos; no hay scores nuevos. '
        'Primero fixture sintético con49ajustes de calibrador como máximo, fuentes artificiales sensibles a costes permitidos, replay sin ajuste y controles de cadafold. No se entrenan árboles ni curvas reales desde este adaptador. '
        'Los entrenamientos fuente registrados siguen su cola, sin duplicarlos. Conservo B00/R1/F3c y adversos; no genero2025 ni envío. Plan: '+io.rel(PLAN)+'; SHA256 '+sha(PLAN)+'.')
    forum = io.post(body, 'COD-S2-20261028-F3CR-DESTINO-PREVIO', 'F3c-R: adaptador anidado y comparadores registrados antes del ajuste')
    dump(OUT/'registration.json', {'utc':utc(), 'plan_sha256':sha(PLAN), 'forum':forum})
    print(json.dumps({'registered':True, 'plan_sha256':sha(PLAN)}), flush=True)


def guard():
    assert read(OUT/'registration.json')['plan_sha256'] == sha(PLAN)
    amendment = read(OUT/'numeric_types_amendment.json') if (OUT/'numeric_types_amendment.json').exists() else {}
    for item in read(PLAN)['dependencies']:
        expected = amendment.get('corrected_dependencies',{}).get(item['path'],item['sha256'])
        assert sha(ROOT/item['path']) == expected, item['path']


def admit_numeric_types():
    assert not (OUT/'numeric_types_amendment.json').exists()
    failed=read(OUT/'synthetic.json'); assert not failed['all_passed']
    expected_changes={io.rel(Path(__file__)),io.rel(Path(inp.__file__))}
    corrected={item['path']:sha(ROOT/item['path']) for item in read(PLAN)['dependencies'] if sha(ROOT/item['path'])!=item['sha256']}
    assert set(corrected)==expected_changes
    body=('Codex. Conservo el preflight sintético fallido: la alteración no numérica de etiquetas retenidas convirtió columnas a object; los mismos floats permitidos se sumaron con diferencias de hasta5.46e-12. '
        'El extremo heredado difirió hasta5.69e-14 por orden de multiplicación. Normalizo a float64 exclusivamente DESPUÉS del selector y restauro el orden heredado nivel×puente. '
        'No cambio tolerancias, fórmulas, particiones ni criterios. Repito49ajustes sintéticos del flujo afectado; se conservan49fallidos anteriores, código y diagnóstico. '
        'No se ha ajustado destino real ni calculado un score nuevo. La cola fuente no cambia. Evidencia: '+io.rel(OUT/'failure_diagnosis.json')+'.')
    forum=io.post(body,'COD-S2-20261028-F3CR-DESTINO-TIPOS','F3c-R: corrección de tipos después del selector y orden aritmético')
    dump(OUT/'numeric_types_amendment.json',{'author':'Codex','utc':utc(),'plan_sha256':sha(PLAN),
        'failed_receipt_sha256':sha(OUT/'synthetic.json'),'diagnosis_sha256':sha(OUT/'failure_diagnosis.json'),
        'corrected_dependencies':corrected,'additional_synthetic_fits':49,'forum':forum,'criteria_unchanged':True})
    print(json.dumps({'numeric_types_correction_admitted':True}),flush=True)


def synthetic():
    guard()
    out = OUT/'corrected_numeric_types' if (OUT/'numeric_types_amendment.json').exists() else OUT
    assert not (out/'synthetic.json').exists()
    out.mkdir(parents=True,exist_ok=True)
    frame = fixture(); adapter = inp.Adapter(frame, SyntheticSource(frame))
    counts_before = dict(e.COUNTS)
    primary, tr, va, mu, branches = bundle(adapter)
    checks = {'base_scopes26':len(adapter.base_parameters)==26, 'recipe_scopes16':len(adapter.recipes)==16,
        'all6cells_and5folds':set(tr.cell)==set(range(6)) and set(tr.fold)==set(range(5)),
        'rows_unique_complete':tr.row_id.is_unique and len(tr)==900 and len(va)==180}
    dump(out/'synthetic_parameters.json', {'adapter':state(adapter), 'calibrator':primary})
    tr.to_parquet(out/'synthetic_training.parquet', index=False)
    va.assign(prediction=mu).to_parquet(out/'synthetic_predictions.parquet', index=False)
    print(json.dumps({'stage':'primary_complete', 'counts':adapter.counts}), flush=True)
    poison = frame.copy()
    cols = ['y']+[c for c in frame if c.startswith('y_')]
    for col in cols:
        poison[col] = poison[col].astype(object)
        poison.loc[poison.year.eq(2024),col] = 'FORBIDDEN_HELD_LABEL'
    pa = inp.Adapter(poison, SyntheticSource(poison)); pb, _, pv, pmu, _ = bundle(pa)
    checks['all2024_poison_parameters_exact'] = signature(adapter)==signature(pa) and canonical(primary)==canonical(pb)
    checks['all2024_poison_inputs_prices_exact'] = va.equals(pv) and np.array_equal(mu,pmu)
    fold_records = []
    for fold in range(5):
        p = frame.copy()
        for col in cols:
            p[col] = p[col].astype(object)
            p.loc[p.year.eq(2023)&p.fold.eq(fold),col] = 'FORBIDDEN_OUTER_FOLD'
        aa = inp.Adapter(p, SyntheticSource(p)); tt,vv = protected_branch(aa,fold)
        expected = {'base': {k:v for k,v in adapter.base_parameters.items() if fold in v['excluded_folds']},
                    'recipes': {k:v for k,v in adapter.recipes.items() if fold in v['excluded_folds']}}
        # La rama solo visita los ámbitos que necesita, todos incluidos en el esperado.
        exact = all(canonical(v)==canonical(expected[k][n]) for k,part in state(aa).items() for n,v in part.items())
        fits = [estimate(tt,lam) for lam in model.LAMBDAS]
        fold_records.append({'fold':fold,'parameters_exact':exact,
            'training_inputs_exact':tt.equals(branches[fold][0]),'held_inputs_exact':vv.equals(branches[fold][1]),
            'calibrator_parameters_exact':all(canonical(m)==canonical(x['model']) for m,x in zip(fits,primary['members'][fold]))})
    checks['five_outer_folds_isolated'] = all(all(v for k,v in z.items() if k!='fold') for z in fold_records)
    print(json.dumps({'stage':'held_controls_complete','checks':checks}), flush=True)
    positive = frame.copy(); mask = positive.year.eq(2023)&(np.arange(len(positive))%7==0)
    for col in cols: positive.loc[mask,col] *= 2
    aa = inp.Adapter(positive,SyntheticSource(positive)); tt = inp.crossfit_features(aa,())
    mm = estimate(tt,primary['selection']['lambda']); pp = aa.features((),positive[positive.year.eq(2024)])
    checks['positive_training_changes_parameters_and_prices'] = signature(aa)!=signature(adapter) and not np.allclose(forward(pp,mm),mu,rtol=1e-9,atol=1e-9)
    saved = read(out/'synthetic_parameters.json'); source = adapter.source.get((),frame[frame.year.eq(2023)])
    def forbidden(*args, **kwargs): raise AssertionError('Aprendizaje durante replay')
    with patch.object(e,'learn_recipe',forbidden), patch.object(e,'kopt',forbidden), patch.object(e.v,'factor_train',forbidden), patch.object(model,'fit',forbidden), patch.object(inp.a,'completion',forbidden):
        replay = inp.apply_features(frame[frame.year.eq(2024)].drop(columns=cols), source,
            saved['adapter']['base']['all'],saved['adapter']['recipes']['all']).sort_values('row_id').reset_index(drop=True)
        replay_mu = forward(replay,saved['calibrator']['final'])
    checks['saved_replay_no_learning_exact'] = replay.equals(va) and np.array_equal(mu,replay_mu)
    recipe = adapter.recipes['all']; raw = inp.apply_base(frame[frame.year.eq(2024)],source,adapter.base_parameters['all'])
    raw['T2b_C1'] = raw.T2b_raw*raw.line.map(recipe['C1']);raw['mix']=.5*(raw.A1_F1*raw.q+raw.T2b_C1)
    inherited = e.apply_recipe(raw,recipe['recipe']); new = inp.from_base(raw,recipe['recipe'])
    checks['endpoint_inherited_exact'] = all(np.array_equal(new['matched_'+k],inherited[k]) for k in ['trainlevel_full','trainlevel_noown'])
    levels = recipe['recipe']['secondary_levels']
    for variant,gamma in [('full',1.),('noown',0.)]:
        beta = np.r_[[np.log(levels[variant][k]) for k in inp.CELL_ORDER],[gamma,0,gamma,gamma,0,gamma]]
        checks['endpoint_gamma_'+variant] = bool(np.allclose(forward(new,{'beta':beta.tolist()}),new['matched_trainlevel_'+variant],rtol=2e-15,atol=1e-12))
    indep = model.fit(tr.base,tr.signal,tr.cell,tr.y,primary['selection']['lambda'],independent=True)
    checks['independent_final_objective'] = abs(indep['loss']-primary['final']['loss'])<1e-10
    fitted_train = forward(tr,primary['final']); manual = np.mean(4*(tr.y/np.sqrt(fitted_train)+np.sqrt(fitted_train)-2*np.sqrt(tr.y)))
    checks['sklearn_deviance'] = bool(np.isclose(manual,mean_tweedie_deviance(tr.y,fitted_train,power=1.5),rtol=1e-12,atol=1e-10))
    bad = frame.copy(); bad.loc[(bad.year.eq(2023))&(bad.fold.eq(1)), 'group'] = 'g0_0_0'
    try: inp.train_frame(bad,()); checks['reject_crossfold_group']=False
    except AssertionError: checks['reject_crossfold_group']=True
    try: adapter.source.get((0,),inp.train_frame(frame,())); checks['reject_wrong_source_scope']=False
    except AssertionError: checks['reject_wrong_source_scope']=True
    # Repetir grupo2023 en una renovación2024 es legítimo temporalmente.
    renewal = frame[frame.year.eq(2024)].copy(); renewal['group'] = frame.loc[frame.year.eq(2023),'group'].iloc[:len(renewal)].to_numpy()
    rr = inp.apply_features(renewal,source,adapter.base_parameters['all'],recipe).sort_values('row_id')
    checks['temporal_group_overlap_allowed'] = np.array_equal(forward(rr,primary['final']),mu)
    counts_after = dict(e.COUNTS)
    result = {'author':'Codex','utc':utc(),'plan_sha256':sha(PLAN),'checks':checks,'all_passed':all(checks.values()),
        'outer_fold_controls':fold_records,'synthetic_rows':len(frame),'synthetic_calibrator_fits':49,
        'primary_adapter_counts':adapter.counts,'actual_kopt_calls_total':sum(counts_after.values())-sum(counts_before.values()),
        'selected_synthetic_lambda':primary['selection']['lambda'],'primary_signature':signature(adapter),
        'independent_objective_difference':abs(indep['loss']-primary['final']['loss']),
        'max_primary_KKT':max([primary['final']['projected_gradient_inf']]+[m['model']['projected_gradient_inf'] for fold in primary['members'] for m in fold]),
        'no_new_real_source_fit_or_C0_or_predictive_score':True,
        'limit':'Valida flujo destino real sobre fixture; fuentes artificiales. No acredita rendimiento privado ni invariancia de entrenamiento nativo. Esas fuentes tienen controles y recibos separados.'}
    guard(); dump(out/'synthetic.json',result)
    assert result['all_passed'], checks
    print(json.dumps({'complete':True,'checks_passed':len(checks),'synthetic_calibrator_fits':49}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['register','synthetic','admit-numeric-types']);args=parser.parse_args()
    try:
        with threadpool_limits(limits=2):
            {'register':register,'synthetic':synthetic,'admit-numeric-types':admit_numeric_types}[args.mode]()
    except Exception:
        if OUT.exists():
            stamp=datetime.now(timezone.utc).strftime('%H%M%S%f')
            (OUT/f'failure_{stamp}.txt').write_text(traceback.format_exc(),encoding='utf-8')
        raise
