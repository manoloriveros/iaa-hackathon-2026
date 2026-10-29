"""GLM estándar P88 con capital ordinario directo: preflight sintético y claves.

La reparación de capital y sus primas quedan fuera de este camino. El importe
incierto se imputa con la mediana propia, sin indicador de calidad en el precio.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import math
import sys
import warnings

R = Path(__file__).resolve().parents[1]
ROOT = R.parents[1]
spec = importlib.util.spec_from_file_location('p95_existing_calibrated_GLM', R/'herramientas/preparar_GLM_prior_calibrado_P87.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
k=p.k; r=p.r; m=p.m; q=p.q; w=p.w; np=p.np; pd=p.pd; BASE=p.BASE
OUT=BASE/'P95_capital_destino_preflight_20261027'
PLAN=R/'registro/semana2_capital_destino_preflight_plan.json'
INDEX=R/'registro/semana2_capital_destino_preflight_actual.json'
DOC=R/'docs/archivo/semana2/PRIVADA_P95_CAPITAL_DESTINO_PREFLIGHT.md'
FIELD='capital_original_ordinary'
UPPER={'buildings':10000000.,'contents':1000000.}
NUM={line:list(k.NUM[line])+([FIELD] if line in UPPER else []) for line in q.LINES}
CAT={line:list(k.CAT[line]) for line in q.LINES}
BASE_DESIGN=k.ORIGINAL_DESIGN


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)


def ordinary(values,line):
    values=pd.to_numeric(values,errors='coerce').to_numpy(float)
    return np.where(np.isfinite(values)&(values>0)&(values<=UPPER[line]),values,np.nan)


def setup():
    r.NUM=NUM; r.CAT=CAT
    k.design=design; k.setup=setup


def design(frame,line,pre=None):
    # BASE_DESIGN uses r.NUM; all fitted medians/scales/levels see only train.
    setup()
    rating=k.rating_frame(frame,line)
    if line not in UPPER:
        return BASE_DESIGN(rating,line,pre)
    matrix,base=BASE_DESIGN(rating,line,None if pre is None else pre['base'])
    columns=base['columns']
    omit=FIELD+'__missing'
    assert columns.count(omit)==1
    keep=[j for j,name in enumerate(columns) if name!=omit]
    selected=[columns[j] for j in keep]
    if pre is None:
        pre={'base':base,'columns':selected,'capital_missing_flag_excluded':True,
            'capital_contract':'Official positive ordinary capital; fixed F0 uncertainty bounds; own-train median; no premium or repaired value.'}
    assert selected==pre['columns'] and omit not in selected
    return np.ascontiguousarray(matrix[:,keep]),pre


def frame_for(line,outer):
    frame=k.frame_for(line,outer)
    if line in UPPER:
        binding=w.read(OUT/'bindings.json')
        path=OUT/f'capital_{line}.parquet'
        assert w.sha(path)==binding['outputs'][w.rel(path)]
        extra=pd.read_parquet(path)
        ids=frame.row_id.tolist()
        frame=frame.merge(extra,on=['row_id','year'],how='left',validate='one_to_one',sort=False,indicator='_capital_join')
        assert frame._capital_join.eq('both').all() and frame.row_id.tolist()==ids
        frame=frame.drop(columns='_capital_join')
    return frame


def poison(frame,line):
    bad=k.poison(frame,line)
    if line in UPPER:
        bad[FIELD]=bad[FIELD].astype('object')
        bad.loc[bad.is_held,FIELD]='INVALID_HELD_CAPITAL'
    return bad


def fit(frame,line,checkpoint=None,calibration=None):
    setup()
    train=frame.loc[~frame.is_held].copy()
    assert set(train.group_id).isdisjoint(set(frame.loc[frame.is_held,'group_id']))
    if calibration is None:
        calibration=p.calibrate_levels(train,line)
    assert calibration['line']==line
    assert calibration['fit_row_ids_digest']==m.p.b.digest(sorted(train.row_id))
    assert calibration['fit_groups_digest']==m.p.b.digest(sorted(set(train.group_id)))
    if checkpoint is not None:dump(checkpoint.with_name(checkpoint.stem+'_levels.json'),calibration)
    matrix,pre=design(train,line)
    target=train.T0.to_numpy(float)
    base=p.ultimate_offset(train,calibration)*train.q_paired.to_numpy(float)
    weight=np.sqrt(base)
    model=r.TweedieRegressor(**r.PARAMS)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always',r.ConvergenceWarning)
        model.fit(matrix,target/base,sample_weight=weight)
    artifact={'line':line,'preprocess':pre,'coef':model.coef_.tolist(),'intercept':float(model.intercept_),
        'parameters':dict(r.PARAMS),'sklearn_version':r.sklearn.__version__,'n_iter':int(model.n_iter_),
        'warnings':[str(z.message) for z in caught],'prior_level_calibration':calibration,
        'fit_row_ids_digest':calibration['fit_row_ids_digest'],'fit_groups_digest':calibration['fit_groups_digest'],
        'source_offset':'Same P88 own-training calibrated half-prior times calendar, own q only for training.',
        'rating_form':'Same P88 main effects plus ordinary capital; missing-quality flag omitted.'}
    if checkpoint is not None:dump(checkpoint,artifact)
    relative=np.exp(matrix@model.coef_+model.intercept_)
    assert np.allclose(relative,model.predict(matrix),rtol=2e-13)
    direct=float(m.e.unit(target,base*relative).sum())
    alternate=r.mean_tweedie_deviance(target/base,relative,power=1.5,sample_weight=weight)*weight.sum()
    assert math.isclose(direct,alternate,rel_tol=3e-12,abs_tol=1e-7)
    score=weight*(np.sqrt(relative)-(target/base)/np.sqrt(relative))/weight.sum()
    gradient=np.r_[score.sum(),matrix.T@score+r.PARAMS['alpha']*model.coef_]
    artifact.update(gradient_inf=float(np.max(np.abs(gradient))),conditional_GLM_offset_loss_identity=True,
        manual_linear_prediction_matches_API=True)
    return artifact


def forward(frame,artifact):
    matrix,_=design(frame,artifact['line'],artifact['preprocess'])
    relative=np.exp(matrix@np.asarray(artifact['coef'])+artifact['intercept'])
    value=p.ultimate_offset(frame,artifact['prior_level_calibration'])*relative
    assert np.isfinite(value).all() and (value>0).all()
    return value,relative


def independent_math(train,artifact):
    setup()
    return p.independent_math(train,artifact)


def bind():
    # Never call historical producers: read just three official policy fields.
    manifest=w.read(BASE/'A1S_nucleo_20261026_v1/report.json')
    records=[];outputs={}
    for line in UPPER:
        path=ROOT/f'Hackaton/Semana 2/Datos/emerging/policies_{line}.parquet'
        assert manifest['sources'][w.rel(path)]==w.sha(path)
        raw=pd.read_parquet(path,columns=['row_id','period_start','sum_insured'])
        raw['year']=pd.to_datetime(raw.period_start).dt.year
        raw=raw.loc[raw.year.isin([2023,2024])].copy()
        assert raw.row_id.is_unique
        extra=raw[['row_id','year']].copy();extra[FIELD]=ordinary(raw.sum_insured,line)
        reference=k.frame_for(line,0)
        assert set(extra.row_id)==set(reference.row_id)
        check=reference[['row_id','year']].merge(extra,on=['row_id','year'],how='left',validate='one_to_one',indicator=True)
        assert check._merge.eq('both').all()
        table=OUT/f'capital_{line}.parquet';extra.to_parquet(table,index=False)
        outputs[w.rel(table)]=w.sha(table)
        records.append({'line':line,'source':w.rel(path),'source_sha256':w.sha(path),'columns_read':['row_id','period_start','sum_insured'],
            'rows':len(extra),'years':[2023,2024],'key_year_coverage_exact':True,'ordinary_capital_rows':int(extra[FIELD].notna().sum()),
            'uncertain_or_absent_rows':int(extra[FIELD].isna().sum()),'raw_amounts_not_repaired':True,'no_premium_or_claim_read':True})
    dump(OUT/'bindings.json',{'author':'Codex','utc':utc(),'records':records,'outputs':outputs})
    for line in q.LINES:
        for outer in range(5):
            f=frame_for(line,outer)
            assert np.array_equal(f.is_held,f.fold.eq(outer)) and f.year.isin([2023,2024]).all()
    return records


def synthetic():
    rng=np.random.default_rng(2026102795);n=720;indices=np.arange(n);records=[]
    for line in q.LINES:
        f=pd.DataFrame({'row_id':['s'+str(i) for i in indices],'line':line,'group_id':['g'+str(i) for i in indices],
            'is_held':indices%5==0,'fold':indices%5,'year':2023+(indices//5)%2,'new_business':(indices//10)%2,
            'T0':rng.gamma(2,80,n)*(rng.random(n)<.4),'reserve':0.,'annual_A1S':np.exp(rng.normal(0,.4,n)),
            'annual_T2b':np.exp(rng.normal(5,.5,n)),'exposure_calendar':rng.uniform(.1,1,n),'q_paired':rng.uniform(.3,1,n)})
        for name in k.BASE_NUM[line]:f[name]=rng.choice([0.,10.,100.],n)
        for name in k.BASE_CAT[line]:
            if name!='new_business':f[name]=rng.choice(['a','b','c'],n)
        f['prior_claims_5y']=rng.choice([0.,1.,2.,np.nan],n)
        if line=='motor':f['ncb_years']=rng.choice([0.,1.,2.,3.,5.,6.,9.,10.,np.nan],n)
        else:
            raw=pd.Series(rng.choice([np.nan,0.,-1.,1000.,20000.,100000.,UPPER[line],UPPER[line]+1.,np.inf],n))
            f[FIELD]=ordinary(raw,line)
            assert np.isnan(ordinary(pd.Series([np.nan,0,-1,UPPER[line]+1,np.inf]),line)).all()
            assert ordinary(pd.Series([UPPER[line]]),line)[0]==UPPER[line]
        folder=OUT/'synthetic'/line
        primary=m.once(folder,'primary',lambda:fit(f,line,folder/'primary_raw.json'))
        adverse=m.once(folder,'adverse',lambda:fit(poison(f,line),line,folder/'adverse_raw.json'))
        assert primary==adverse and primary['gradient_inf']<1e-5 and not primary['warnings']
        math_check=independent_math(f.loc[~f.is_held],primary)
        if line in UPPER:
            pre=primary['preprocess'];base=pre['base'];j=base['numeric'].index(FIELD)
            values=np.log1p(f.loc[~f.is_held,FIELD].to_numpy(float));expected=float(np.median(values[np.isfinite(values)]))
            assert base['median'][j]==expected and FIELD+'__missing' not in pre['columns']
        clean=f.loc[f.is_held].drop(columns=['T0','reserve','q_paired']).copy()
        value,_=forward(clean,primary)
        saved_fit=r.TweedieRegressor.fit;saved_levels=p.calibrate_levels
        def reject(*args,**kwargs):raise AssertionError('No learning allowed during replay')
        try:
            r.TweedieRegressor.fit=reject;p.calibrate_levels=reject
            replay,_=forward(clean,json.loads(json.dumps(primary)));assert np.array_equal(value,replay)
            subset=np.arange(0,len(clean),3);part,_=forward(clean.iloc[subset],primary)
            order=np.arange(len(clean))[::-1];permuted,_=forward(clean.iloc[order],primary)
            assert np.allclose(part,value[subset],rtol=2e-13,atol=1e-13)
            assert np.allclose(permuted,value[order],rtol=2e-13,atol=1e-13)
        finally:r.TweedieRegressor.fit=saved_fit;p.calibrate_levels=saved_levels
        records.append({'line':line,'all_held_payload_including_capital_poison_exact':True,'math':math_check,
            'no_capital_quality_predictor':True,'JSON_replay_exact_with_learning_blocked':True,'subset_permutation_projective':True})
    return {'author':'Codex','utc':utc(),'records':records,'synthetic_primary_GLMfits':3,'synthetic_adverse_GLMfits_separate':3,
        'synthetic_primary_closed_levels':18,'synthetic_adverse_closed_levels_separate':18,'new_real_fits':0,
        'new_source_fits':0,'new_CDF_fits':0,'new_scores':0,'new2025inference':0,'new_submissions':0}


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json')
    assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent_path=R/'registro/semana2_capital_destino_revision_plan.json';parent=w.read(parent_path)
    previous=BASE/'P94_contrato_capital_destino_20261027'
    assert w.read(previous/'completion_receipt.json')['report_sha256']==w.sha(previous/'report.json')
    baseline=w.read(p.PLAN)
    paths=[Path(__file__),Path(p.__file__),Path(k.__file__),Path(r.__file__),parent_path,previous/'report.json',previous/'completion_receipt.json']
    paths += [ROOT/f'Hackaton/Semana 2/Datos/emerging/policies_{line}.parquet' for line in UPPER]
    OUT.mkdir()
    plan={'author':'Codex','utc':utc(),'scope':'Standard GLM with direct ordinary capital; synthetic complete learning and strict official historical policy binding, no real fitting.',
        'need':parent['hypothesis'],'hypothesis':'A single log-capital main effect can adapt ordinary insured-amount response to the emerging market beyond frozen source risks, without estimating a noisy target risk base.',
        'one_change':'Add capital_original_ordinary to buildings/contents P88 main effects; omit its missing flag. Motor unchanged. No source, q, target, exposure or prior rule changes.',
        'configuration':{'capital':parent['future_contract'],'GLM_parameters':dict(r.PARAMS),'features_NUM':NUM,'features_CAT':CAT,
            'capital_design':'log1p once; own-train median/center/scale. Drop capital __missing column before fitting and applying. Other existing numeric missing flags unchanged.',
            'source_level_reuse':'Full evaluation may reuse exact same-scope P88 level objects and motor model after matching code/data/keys/parameters. No new C0 or source learning.'},
        'preflight_criterion':'All three primary/adverse synthetic whole learners equal; capital included in held poison before selection; scalar offset objective/gradient checks, train-only median and no quality flag, JSON replay with learning blocked, boundary conversion and subset/permutation. Fifteen historical inputs with exact policy row/year coverage.',
        'future_budget':{'primary_GLMfits':10,'adverse_GLMfits_separate':10,'reused_primary_motor_models':5,'reused_adverse_motor_models_separate':5,
            'reused_primary_closed_levels':90,'new_primary_closed_levels':0,'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0},
        'future_criterion':'Unchanged complete five-fold 2023/2024 adaptive evaluation and all global/cohort/scenario/level/influence/family/convergence gates; if pooled passes, separate transfer check before any CSV. No tuning thresholds, alpha or lines from held/public outcomes.',
        'sources':{**baseline['sources'],**{w.rel(path):w.sha(path) for path in paths}},'runtime_sources':baseline.get('runtime_sources',{}),
        'limits':baseline['limits']+['Ordinary capital selection is a historical uncertainty filter, not official scale validation; uncertain cells receive only own-training median without a quality predictor.','Supplied snapshot capital is not timestamp-certified at quote; a new direct feature does not remove source ancestry/valuation/adaptive search limits.'],
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan)
    body=OUT/'forum_previo.md';body.write_text('Codex. P95 registra antes de probar el flujo sintético el mismo GLM P88 con un efecto principal de capital ordinario en edificios y contenidos. Se mantienen potencia1,5, alpha1, prior, exposición, reporte y demás variables. Capital positivo original hasta filtros F0 de10M/1M; casos dudosos con mediana propia, sin bandera de calidad como predictor, prima o división por1000. Motor sin cambio. Se enlazarán solo row_id, period_start y sum_insured de pólizas oficiales2023/2024. Primero seis GLM sintéticos, veneno integral retenido, matemática y replay bloqueando aprendizaje; cero ajuste real o envíos. Cualquier evaluación real necesita registro posterior, con20ajustes máximo y reutilización exacta de niveles/motor. B00 preservado,2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P95registered_before_synthetic_and_binding','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P95-CAPITAL-PREVIO','P95: GLM con capital ordinario, antes del preflight')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def run():
    plan=w.read(PLAN);m.check_sources(plan)
    assert w.read(OUT/'registration.json')['plan_sha256']==w.sha(PLAN)
    dump(OUT/'synthetic.json',synthetic());records=bind();m.check_sources(plan)
    dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P95capital_main_effect_synthetic_and_historical_bindings_complete',
        'bindings':records,'all_preflight_pass':True,'new_real_fits':0,'new_source_fits':0,'new_CDF_fits':0,'new_scores':0,'new2025inference':0,'new_submissions':0})
    print(json.dumps({'preflight_pass':True,'historical_rows':sum(z['rows'] for z in records),'new_real_fits':0}))


def close():
    plan=w.read(PLAN);m.check_sources(plan);report=w.read(OUT/'report.json')
    next_unit='P96: separately register and freeze complete same-P88 standard GLM plus direct ordinary capital. Reuse all90 same-scope P88 prior levels and five motor models by code/data/keys; fit only10+10 property models. All old pooled/cohort/scenario/family/convergence/level/influence gates unchanged; whole poison includes capital; replay blocks fits and level estimators. No threshold/alpha/line rescue or 2025/upload before complete admission and transfer.'
    text='# P95: capital ordinario en el GLM directo\n\nCodex, '+utc()+'.\n\nEl flujo sintético pasó con tres ajustes primarios y tres adversos. Corromper todo el payload retenido, incluido el capital, conserva exactamente los parámetros; mediana, categorías y escalas se aprenden dentro del entrenamiento. El capital se transforma una vez con log1p; su indicador de ausencia queda fuera del precio. Se comprobó la pérdida con offset y el gradiente por otro cálculo. El replay JSON, con ajuste y estimación de niveles bloqueados, conserva las predicciones y su aplicación por subconjuntos/permutaciones.\n\n'
    text+='| Ramo | Pólizas históricas enlazadas | Capital ordinario | Dudoso o ausente |\n|---|---:|---:|---:|\n'
    for z in report['bindings']:text+=f"|{z['line']}|{z['rows']}|{z['ordinary_capital_rows']}|{z['uncertain_or_absent_rows']}|\n"
    text+='\nLa unión por fila y año cubre exactamente las entradas 2023/2024; las quince vistas conservan sus folds. Solo se leyeron row_id, period_start y sum_insured de las pólizas. No se leyó prima ni siniestros para construir capital, ni se reparó una escala dudosa. Los filtros de 10 millones y un millón vienen de F0 y siguen siendo una decisión de incertidumbre; no son límites oficiales. Disponibilidad condicional de instantánea, sin historia transaccional que certifique cotización.\n\nCero ajuste real, nuevo score, CDF, inferencia2025 o envío. La evaluación real aún no está hecha: necesita registro separado. Se conserva P88 como comparador completo, B00 y todos los adversos.2024abierto adaptativo; no validación independiente ni evidencia de mejora privada.\n\nPróximo: '+next_unit+'\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':report['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),
        'document':w.rel(DOC),'synthetic':w.rel(OUT/'synthetic.json'),'synthetic_sha256':w.sha(OUT/'synthetic.json'),
        'bindings':w.rel(OUT/'bindings.json'),'bindings_sha256':w.sha(OUT/'bindings.json'),'next_unit':next_unit,
        'new_real_fits':0,'new_source_fits':0,'new_CDF_fits':0,'new_scores':0,'new2025inference':0,'new_submissions':0,
        '2024_open':True,'goal_achieved':False,'forum':q.post(body,'COD-S2-20261027-PRIVADA-P95-CAPITAL-RESULTADO','P95: capital enlazado y flujo sintético comprobado')}
    cut=R/'privado'/('corte_P95_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));cut.mkdir();w.update(INDEX,receipt,cut)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P95'),(R/'registro/semana2_mision_privada_actual.json','P95')]:w.update(path,{key:receipt,'next_unit':next_unit},cut)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P95=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},cut)
    note='\n\n## Privada P95: capital directo, preflight\n\nCodex, '+receipt['utc']+'. Seis ajustes sintéticos, veneno integral, matemática y replay exactos; capital oficial enlazado por fila/año en2023/2024sin prima o reparación. Cero ajuste real/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,cut)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_direct_capital_preflight_index':w.rel(INDEX),'week_2_private_direct_capital_preflight_report':w.rel(DOC)},cut)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');a=argparse.ArgumentParser(description=__doc__);a.add_argument('mode',choices=['register','run','close'])
    with m.e.threadpool_limits(limits=2):{'register':register,'run':run,'close':close}[a.parse_args().mode]()
