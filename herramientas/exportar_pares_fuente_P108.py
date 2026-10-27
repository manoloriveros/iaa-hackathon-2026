"""Exporta pares fuente ya ajustados, solo a filas historicas y sin aprender."""
from pathlib import Path
import argparse
import copy
import importlib.util
import json
import math
import sys
from datetime import datetime, timezone

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
p107=load('p108_count_adapter',R/'herramientas/preparar_exposicion_recuento_P107.py')
m=load('p108_frozen_pair_helpers',R/'herramientas/fuente_frecuencia_marca_P28.py')
w=m.w;pd=m.pd;np=m.np;BASE=m.BASE;HOME=m.HOME
SOURCE=BASE/'P29_fuente_frecuencia_completa_20261026'
OUT=BASE/'P108_pares_fuente_historicos_20261027'
PLAN=R/'registro/semana2_pares_fuente_historicos_plan.json'
INDEX=R/'registro/semana2_pares_fuente_historicos_actual.json'
DOC=R/'docs/semana2/PRIVADA_P108_PARES_FUENTE_HISTORICOS.md'
dump=p107.dump;utc=p107.utc


def block_learning(*args,**kwargs):
    raise AssertionError('Learning is forbidden during a frozen source export')


def historical_inputs(rows,x):
    assert len(rows)==len(x) and rows.index.equals(x.index) and rows.row_id.is_unique
    assert rows.is_test.dtype==bool and rows.year.notna().all()
    keep=~rows.is_test
    # Select keys first; never transform or parse excluded future covariates.
    selected=rows.loc[keep,['row_id','year']].reset_index(drop=True)
    assert selected.year.isin([2023,2024]).all() and len(selected)>0
    return selected,x.loc[keep].reset_index(drop=True)


def predict_pairs(rows,x,prep,pairs):
    keys,selected=historical_inputs(rows,x)
    matrix,names=m.p14.transform(selected,prep)
    out=keys.copy();total=np.zeros(len(keys));terms=[]
    for peril,frequency,mark,columns in pairs:
        assert names==columns and len(frequency['coef'])==len(mark['coef'])==len(names)
        f=m.predict(matrix,frequency);s=m.predict(matrix,mark)
        assert np.isfinite(f).all() and np.isfinite(s).all() and (f>0).all() and (s>0).all()
        out['frequency_'+peril]=f;out['mark_'+peril]=s
        value=f*s;assert np.isfinite(value).all() and (value>0).all()
        total+=value;terms.append(value)
    out['raw_log_rate']=np.log(total)
    sample=np.unique(np.linspace(0,len(out)-1,min(32,len(out)),dtype=int))
    scalar=np.array([math.fsum(float(value[i]) for value in terms) for i in sample])
    assert np.allclose(total[sample],scalar,rtol=3e-15,atol=0)
    return out


def synthetic():
    rows=pd.DataFrame({'row_id':['a','future','b','c'],'year':[2023,2025,2024,2024],'is_test':[False,True,False,False]})
    x=pd.DataFrame({'x':[0.,'EXCLUDED_FUTURE',np.nan,1.], 'category':['a','EXCLUDED_FUTURE','rare','a']})
    prep={'columns':['x','category'],
        'numeric':{'x':{'median':0.,'lo':-2.,'hi':2.,'mean':0.,'scale':1.}},
        'categorical':{'category':['a',m.p14.old.OTHER]},
        'numeric_missing_indicators':{'x':{'mean':.2,'scale':.4}}}
    names=['x','category='+m.p14.old.OTHER,'x__is_missing']
    pairs=[('p0',{'coef':[.1,.2,-.1],'intercept':-2.}, {'coef':[.3,-.1,.2],'intercept':4.},names),
        ('p1',{'coef':[-.2,.1,.1],'intercept':-1.}, {'coef':[.2,.2,.1],'intercept':3.},names)]
    original=predict_pairs(rows,x,prep,pairs)
    poison=x.copy();poison.loc[rows.is_test,:]='__OTHER__'
    poisoned=predict_pairs(rows,poison,prep,pairs)
    assert original.equals(poisoned)
    reversed_result=predict_pairs(rows.iloc[::-1].reset_index(drop=True),x.iloc[::-1].reset_index(drop=True),prep,pairs)
    assert original.equals(reversed_result.iloc[::-1].reset_index(drop=True))
    sub=predict_pairs(rows.iloc[[0]].reset_index(drop=True),x.iloc[[0]].reset_index(drop=True),prep,pairs)
    assert original.iloc[[0]].reset_index(drop=True).equals(sub)
    assert original.equals(predict_pairs(rows,x,json.loads(json.dumps(prep)),json.loads(json.dumps(pairs))))
    # Independent dense scalar predictor for all three historical rows/2perils.
    matrix,_=m.p14.transform(x.loc[~rows.is_test].reset_index(drop=True),prep)
    dense=matrix.toarray()
    for peril,f,s,_ in pairs:
        for family,model in [('frequency',f),('mark',s)]:
            scalar=np.array([math.exp(math.fsum(float(a)*b for a,b in zip(row,model['coef']))+model['intercept']) for row in dense])
            assert np.allclose(original[family+'_'+peril],scalar,rtol=3e-15,atol=0)
    bad=rows.copy();bad.loc[1,'is_test']=False
    try:predict_pairs(bad,x,prep,pairs)
    except AssertionError:pass
    else:raise AssertionError('Future non-test record passed')
    try:historical_inputs(rows,x.iloc[::-1])
    except AssertionError:pass
    else:raise AssertionError('Misaligned input indexes passed')
    return {'author':'Codex','utc':utc(),'frozen_preprocess_predict_full_flow':True,
        'future_payload_excluded_before_transform':True,'scalar_predictors_and_peril_sum_match':True,
        'JSON_permutation_singleton_exact':True,'future_non_test_and_misaligned_inputs_rejected':True,
        'new_synthetic_or_real_model_fits':0}


def paths():
    result=[Path(__file__),Path(m.__file__),Path(m.p14.__file__),Path(m.p14.old.__file__),Path(p107.__file__),
        p107.INDEX,p107.OUT/'report.json',SOURCE/'report.json',SOURCE/'completion_receipt.json',m.P27/'report.json',
        R/'registro/semana2_prioridad_privada_reafirmada_20261027.json']
    for line in p107.PERILS:
        result += [HOME/f'rows_s2_{line}.parquet',HOME/f'matrix_s2_{line}.parquet',
            SOURCE/line/'preprocessor.json',SOURCE/line/'application.json',
            SOURCE/f'historical_{line}_three_seed.parquet',p107.OUT/f'count_exposure_{line}.parquet']
        for peril in p107.PERILS[line]:
            for family in ['frequency','mark']:
                result += [SOURCE/line/f'{line}_{peril}_{family}'/'model.json',
                    SOURCE/line/f'{line}_{peril}_{family}'/'fit_record.json']
    return result


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json')
    assert not phase.get('active_jobs') and not phase.get('active_execution')
    closed=w.read(SOURCE/'completion_receipt.json')
    assert closed['report_sha256']==w.sha(SOURCE/'report.json')
    assert all(w.sha(ROOT/path)==sha for path,sha in closed['model_hashes'].items())
    OUT.mkdir();fixture=synthetic();dump(OUT/'synthetic.json',fixture)
    plan={'author':'Codex','utc':utc(),
        'need':'Target count path now has accepted counts and fixed source count exposure; it lacks explicit paired source frequency and mark rates. Native FSp frequency fitted on cost exposure is not a replacement.',
        'configuration':{'source_recipe':'Unchanged P29:30stored GLMs, source-only P14preprocessing,15perils, same annual lambda*mark sum and source normalizers.',
            'destination':'Only emerging historical2023/2024; filter test before transform/predict. Matrix and metadata are positionally bound by original source hashes.',
            'output':'Annual lambda and paired mean mark per peril, original raw log cost rate, exact canonical row order. Count exposure and all labels/costs/groups unchanged.',
            'no_future':'No2025transformation or inference; excluded payload poisoning in synthetic actual export flow.',
            'no_learning':'Block model and preprocessor learning in the export process; no recalibration, new level/normalizer, exposure fit or score.',
            'order':'Exact original P27peril order used by P29 to preserve floating sum ordering.'},
        'criterion':'Synthetic frozen preprocess->pairedpredict->sum agrees with scalar predictors, JSON/permutation/singleton; future/test rejected before transform. Real sum reproduces all P29saved raw and normalized log rates; all canonical keys and original columns unchanged.',
        'budget':{'new_model_fits':0,'new_CDF_fits':0,'new_normalizers':0,'historical_source_component_models_reused':30,
            'new_scores':0,'new2025inference':0,'new_final_prices':0,'new_submissions':0},
        'limits':['These are source model outputs, not identified true ultimate frequency or severity.',
            'Target transfer recipe still pending; source-only completion does not establish predictive or private improvement.',
            'P30failed target transfer retained; adaptive2023/2024search and reporting/reserve uncertainty remain.'],
        'sources':{w.rel(path):w.sha(path) for path in paths()},'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan)
    body=OUT/'forum_previo.md';body.write_text('Codex. P108 registra la exportación histórica de frecuencia y marca por peril desde los 30 GLM fuente P29 ya ajustados. Se conserva su preprocesamiento fuente y el orden original de suma; no hay refit o normalizador nuevo. El filtro de 2023/2024 se aplica antes de transformar o inferir; no se toca 2025. La prueba sintética del flujo completo verifica exclusión de datos futuros, predictor escalar, JSON, orden y consulta individual. Se exigirá reproducir el agregado histórico guardado y conservar todas las columnas originales de P107. No se confunde f FSp con este contrato pareado ni se afirma frecuencia última identificada. La receta de destino y su contraste siguen pendientes; P30 adverso se conserva. Cero scores, precios finales o envíos. Prioridad privada, B00 preservado. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P108registered_before_historical_pair_export','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':p107.previous.post(body,'COD-S2-20261027-PRIVADA-P108-PARES-PREVIO','P108: pares fuente históricos, sin refit o inferencia futura')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def run():
    plan=w.read(PLAN);p107.previous.check_sources(plan)
    for owner,names in [(m,['fit','coefficients']),(m.p14,['fit_preprocessor']),(m.p14.old,['fit_preprocessor','fit_source'])]:
        for name in names:setattr(owner,name,block_learning)
    fixture=synthetic();dump(OUT/'synthetic_run.json',fixture)
    records=[];outputs={};total=0
    perils=w.read(m.P27/'report.json')['by_line_peril']
    for line in p107.PERILS:
        prep_path=SOURCE/line/'preprocessor.json';prep=w.read(prep_path);pairs=[]
        for peril in [record['peril'] for record in perils if record['line']==line]:
            models=[];columns=None
            for family in ['frequency','mark']:
                folder=SOURCE/line/f'{line}_{peril}_{family}';record=w.read(folder/'fit_record.json')
                assert record['model_sha256']==w.sha(folder/'model.json') and record['preprocessor_sha256']==w.sha(prep_path)
                assert columns is None or columns==record['columns'];columns=record['columns']
                models.append(w.read(folder/'model.json'))
            pairs.append((peril,*models,columns))
        rows=pd.read_parquet(HOME/f'rows_s2_{line}.parquet',columns=['row_id','year','is_test'])
        x=pd.read_parquet(HOME/f'matrix_s2_{line}.parquet')
        prediction=predict_pairs(rows,x,prep,pairs)
        old=pd.read_parquet(SOURCE/f'historical_{line}_three_seed.parquet')
        assert old.row_id.tolist()==prediction.row_id.tolist() and old.year.equals(prediction.year)
        error=float(np.max(np.abs(old.raw_log_rate-prediction.raw_log_rate)))
        assert np.array_equal(old.raw_log_rate.to_numpy(),prediction.raw_log_rate.to_numpy())
        center=w.read(SOURCE/line/'application.json')['source_center']
        assert np.array_equal(old.log_relative_A1S.to_numpy(),prediction.raw_log_rate.to_numpy()-center)
        canonical=pd.read_parquet(p107.OUT/f'count_exposure_{line}.parquet')
        assert set(canonical.row_id)==set(prediction.row_id) and prediction.row_id.is_unique
        prediction=prediction.set_index('row_id').loc[canonical.row_id].reset_index()
        assert np.array_equal(canonical.year,prediction.year)
        newcols=[name for name in prediction if name not in ['row_id','year']]
        out=canonical.copy()
        for name in newcols:out[name]=prediction[name].to_numpy()
        assert out.drop(columns=newcols).equals(canonical)
        path=OUT/f'paired_source_{line}.parquet';out.to_parquet(path,index=False)
        outputs[w.rel(path)]=w.sha(path);total+=len(out)
        records.append({'line':line,'rows':len(out),'perils':len(pairs),'raw_log_aggregate_max_error':error,
            'all_P29_raw_and_normalized_rates_bitexact':True,'canonical_original_columns_unchanged':True})
    assert total==109296;p107.previous.check_sources(plan)
    dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P108historical_paired_source_rates_exported_no_target_model',
        'rows':total,'records':records,'outputs':outputs,'learning_blocked_during_export':True,**plan['budget']})
    print(json.dumps({'rows':total,'models_reused':30,'all_P29_aggregates_exact':True,'new_fits':0,'new_scores':0}))


def close():
    plan=w.read(PLAN);p107.previous.check_sources(plan);report=w.read(OUT/'report.json')
    assert all(w.sha(ROOT/path)==sha for path,sha in report['outputs'].items())
    next_unit='P109: design and freeze a standard target Poisson frequency correction using actual accepted-event counts, source-paired annual frequency offset and count-weighted completion from P107/P108. Keep original T0cost for final price-level calibration, keep source mark allocation and cost completion distinct. Specify all training normalizers, scope exclusions, penalty rescaling, comparator and whole-pipeline synthetic invariance before any real fit. Do not repeat P30 full source transfer or treat this export as predictive improvement.'
    text='# P108: pares fuente históricos preparados\n\nCodex, '+utc()+'.\n\nSe exportaron las frecuencias y marcas medias pareadas de los 30 GLM fuente P29 ya guardados a las 109.296 filas históricas de 2023 y 2024. El preprocesamiento, los coeficientes y los normalizadores son los originales. La suma por peril reproduce exactamente, bit a bit, los logaritmos brutos y relativos guardados por P29 en todas las filas. También se conserva cada columna original de P107 y el orden canónico.\n\nEl proceso bloqueó las funciones de aprendizaje. La prueba sintética recorrió el filtro histórico, el preprocesamiento congelado y los predictores pareados; la alteración del contenido excluido de 2025 no cambió ninguna salida histórica. Los predictores y la suma coincidieron con cálculos escalares y pasaron las consultas individuales, permutación y recarga JSON. Se rechazaron entradas desalineadas o un año futuro marcado como histórico.\n\nEstas salidas son tasas estimadas del mercado fuente bajo los supuestos de observación y cola ya documentados. No prueban frecuencia o severidad última identificadas, transporte al mercado emergente ni mejora privada. El contraste adverso anterior P30 sigue vigente. Falta diseñar la corrección de frecuencia destino con sus comparadores y validación completa; no se ajustó ese modelo ni se recalibraron precios. Cero refits, nuevos normalizadores, scores, precios finales, inferencia de 2025 o envíos. B00 y alternativas preservados, prioridad privada y 2024 abierto como desarrollo adaptativo.\n\nPróximo: '+next_unit+'\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':report['status'],'report':w.rel(OUT/'report.json'),
        'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'outputs':report['outputs'],**plan['budget'],
        'next_unit':next_unit,'2024_open':True,'goal_achieved':False,
        'forum':p107.previous.post(body,'COD-S2-20261027-PRIVADA-P108-PARES-RESULTADO','P108: pares históricos reproducidos, receta de frecuencia destino pendiente')}
    cut=R/'privado'/('corte_P108_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));cut.mkdir();w.update(INDEX,receipt,cut)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P108'),(R/'registro/semana2_mision_privada_actual.json','P108')]:
        w.update(path,{key:receipt,'next_unit':next_unit},cut)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025']
    own.update(private_P108=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},cut)
    note='\n\n## Privada P108: pares fuente históricos\n\nCodex, '+receipt['utc']+'. Exportación sin refit de 30 GLM fuente a 109.296 filas históricas; agregado P29 exacto y columnas P107 intactas. Aprendizaje bloqueado y filtro futuro probado con datos sintéticos. No es mejora predictiva o privada. Informe '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,cut)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_historical_paired_source_index':w.rel(INDEX),
        'week_2_private_historical_paired_source_report':w.rel(DOC)},cut)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['register','synthetic','run','close']);mode=parser.parse_args().mode
    if mode=='synthetic':print(json.dumps(synthetic()))
    else:{'register':register,'run':run,'close':close}[mode]()
