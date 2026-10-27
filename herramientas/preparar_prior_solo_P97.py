"""Prior calibrado P88 sin GLM corrector: camino estándar de menor dimensión."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p97_existing_prior',R/'herramientas/preparar_GLM_prior_calibrado_P87.py')
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
m=p.m;q=p.q;w=p.w;np=p.np;pd=p.pd;BASE=p.BASE
OUT=BASE/'P97_prior_solo_preflight_20261027';OLD=BASE/'P88_validacion_prior_calibrado_20261027'
PLAN=R/'registro/semana2_prior_solo_preflight_plan.json';INDEX=R/'registro/semana2_prior_solo_preflight_actual.json'
DOC=R/'docs/semana2/PRIVADA_P97_PRIOR_SOLO_PREFLIGHT.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)
def frame_for(line,outer):return p.k.frame_for(line,outer)


def learn_levels(frame,line):
    train=frame.loc[~frame.is_held]
    assert set(train.group_id).isdisjoint(set(frame.loc[frame.is_held,'group_id']))
    return {'line':line,'prior_level_calibration':p.calibrate_levels(train,line),
        'kind':'Two_component_same_scope_calibrated_prior_only_no_GLM_or_new_shape'}


def forward(frame,artifact):
    return p.ultimate_offset(frame,artifact['prior_level_calibration'])


def cached(frame,line,outer):
    train=frame.loc[~frame.is_held];old=w.read(OLD/f'{line}_{outer}/learning.json')
    assert old==w.read(OLD/f'{line}_{outer}/adverse_learning.json')
    assert old['fit_row_ids_digest']==m.p.b.digest(sorted(train.row_id))
    assert old['fit_groups_digest']==m.p.b.digest(sorted(set(train.group_id)))
    sources=w.read(R/'registro/semana2_prior_calibrado_GLM_validacion_plan.json')['sources']
    for path in [Path(p.__file__),Path(p.k.__file__),p.r.p.t.t.OUT/f'input_{line}_{outer}.parquet']:
        assert sources[w.rel(path)]==w.sha(path)
    cal=old['prior_level_calibration']
    assert cal['target_learned_parameters']==6 and cal['line']==line
    return {'line':line,'prior_level_calibration':cal,'kind':'Two_component_same_scope_calibrated_prior_only_no_GLM_or_new_shape'}


def synthetic():
    rng=np.random.default_rng(2026102797);n=360;indices=np.arange(n);records=[]
    def reject(*args,**kwargs):raise AssertionError('Prior-only flow must not fit a GLM')
    original=p.r.TweedieRegressor.fit;p.r.TweedieRegressor.fit=reject
    try:
        for line in q.LINES:
            f=pd.DataFrame({'row_id':['s'+str(i) for i in indices],'line':line,'group_id':['g'+str(i) for i in indices],
                'is_held':indices%5==0,'year':2023+(indices//5)%2,'new_business':(indices//10)%2,
                'T0':rng.gamma(2,80,n)*(rng.random(n)<.4),'reserve':0.,'annual_A1S':np.exp(rng.normal(0,.4,n)),
                'annual_T2b':np.exp(rng.normal(5,.5,n)),'exposure_calendar':rng.uniform(.1,1,n),'q_paired':rng.uniform(.3,1,n),
                'ignored_rating':rng.normal(size=n)})
            primary=learn_levels(f,line);bad=f.copy()
            for name in ['T0','reserve','annual_A1S','annual_T2b','exposure_calendar','q_paired','new_business','ignored_rating']:
                bad[name]=bad[name].astype('object');bad.loc[bad.is_held,name]='INVALID_HELD'
            assert learn_levels(bad,line)==primary
            changed=f.copy();changed['ignored_rating']='INVALID_EVERYWHERE'
            assert learn_levels(changed,line)==primary
            math_checks=p.level_math(f.loc[~f.is_held],primary['prior_level_calibration'])
            held=f.loc[f.is_held].drop(columns=['T0','reserve','q_paired','ignored_rating'])
            value=forward(held,primary);stored=json.loads(json.dumps(primary))
            assert np.array_equal(value,forward(held,stored))
            scalar=[];cal=stored['prior_level_calibration']
            for _,row in held.iterrows():
                total=sum(.5*float(row['annual_'+source])*cal['components'][source]['cell_levels'][str(int(row.new_business))] for source in ['A1S','T2b'])
                scalar.append(total*float(row.exposure_calendar))
            assert np.allclose(value,scalar,rtol=3e-15,atol=1e-12)
            order=np.arange(len(held))[::-1];assert np.array_equal(forward(held.iloc[order],stored),value[order])
            subset=np.arange(0,len(held),3);assert np.array_equal(forward(held.iloc[subset],stored),value[subset])
            records.append({'line':line,'full_held_poison_exact':True,'all_rating_payload_ignored_exact':True,
                'level_math':math_checks,'scalar_component_units_and_calendar_match':True,'JSON_subset_permutation_exact':True})
    finally:p.r.TweedieRegressor.fit=original
    return {'author':'Codex','utc':utc(),'records':records,'synthetic_primary_closed_levels':18,'synthetic_adverse_closed_levels_separate':18,
        'new_native_fits':0,'new_real_levels':0,'new_scores':0,'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0}


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    previous=BASE/'P96_validacion_capital_destino_20261027';assert w.read(previous/'completion_receipt.json')['report_sha256']==w.sha(previous/'report.json')
    parent=w.read(p.PLAN);m.check_sources(parent)
    paths=[Path(__file__),Path(p.__file__),Path(p.k.__file__),previous/'report.json',previous/'completion_receipt.json',OLD/'report.json',OLD/'completion_receipt.json',R/'registro/semana2_prior_calibrado_GLM_validacion_plan.json']
    paths += [OLD/f'{line}_{outer}/{name}.json' for line in q.LINES for outer in range(5) for name in ['learning','adverse_learning']]
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'candidate':'Own-training calibrated two-source prior alone, removing the entire GLM correction',
        'need':'P88/P90/P93/P96 whole algorithms fail; P96 direct ordinary capital does not improve P88. The P88 prior itself has not been evaluated as a complete candidate without its final correction. Test lower-dimensional standard transport before adding fields or capacity.',
        'hypothesis':'Broad component/line/business calibration may preserve source allocation with less target-fitting variation than the rejected correction. Unknown gain; not proof every rating effect is harmful.',
        'one_change':'From P88 remove the entire GLM and its preprocessing/source-log/rating coefficients. Keep the exact prior, fixed half mixture, calendar, own reporting and folds.',
        'configuration':{'prior':parent['configuration']['components'],'business_levels':'Same global Tweedie moments and K400 geometric business shrinkage, six parameters per line/fold. No new final mixture normalization or intercept.',
            'application':'Half A1S annual relative*stored target level plus half T2b annual source cost*stored target/source ratio, then calendar. No q, y, rating design or batch normalizer in ultimate.',
            'reuse':'Use all90 P88 same-scope stored level parameters by original code/raw-input/key hashes and adverse equality; no recalibration. Synthetic learns only its own levels for exclusion proof.',
            'distinction':'B12 is constant by line/business without source risk. P18 joint GAM calibration is a different algorithm. P65 has target history/NCB shapes and shared residual stages. None is this unshaped source-risk prior alone.'},
        'preflight_criterion':'All three whole prior learners invariant to all held payload and all unused rating changes; independent scalar moment and component/calendar math, JSON/subset/permutation exact; GLMfit blocked. Fifteen exact same-scope cache bindings, no real output prices.',
        'future_budget':{'new_native_fits':0,'new_real_closed_levels':0,'reused_primary_closed_levels':90,'reused_adverse_closed_levels_separate':90,'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0},
        'future_criterion':'Same complete pooled/cohort/stress/level/influence/family gates; separate own transfer required after pooled pass before CSV. No source weight/K/line rescue or changed criteria.',
        'sources':{**parent['sources'],**{w.rel(path):w.sha(path) for path in paths}},'limits':parent['limits']+['Removing a correction is an adaptive candidate choice after adverse evidence; no pristine validation or private guarantee.'],
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md';body.write_text('Codex. P97 registra una alternativa más simple: prior P88 calibrado por componente/ramo/negocio, mezcla fija50/50, sin GLM corrector, nuevas variables, forma de historial, normalizador o intercepto. Se distingue de B12 constante, P18 conjunto y P65 con formas. La hipótesis es reducir variación de ajuste destino; no hay beneficio probado. Primero fixture integral de momentos, veneno retenido y ratings ignorados, unidades/calendario y replay JSON. Se enlazan los90 niveles existentes en sus ámbitos exactos; cero ajuste real o nuevos precios en este preflight. La evaluación completa tendrá registro propio y las mismas guardas. B00 preservado,2024abierto adaptativo, ceroenvíos. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P97registered_before_prior_only_preflight','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),'forum':q.post(body,'COD-S2-20261027-PRIVADA-P97-PRIOR-PREVIO','P97: prior calibrado sin corrección, preflight registrado')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def run():
    plan=w.read(PLAN);m.check_sources(plan);dump(OUT/'synthetic.json',synthetic())
    records=[]
    for line in q.LINES:
        for outer in range(5):
            f=frame_for(line,outer);a=cached(f,line,outer)
            records.append({'line':line,'outer':outer,'calibration_sha256':m.p.b.digest(a['prior_level_calibration']),'no_real_parameter_reestimation':True})
    m.check_sources(plan);dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P97prior_only_synthetic_and_scope_bindings_complete','records':records,'new_native_fits':0,'new_real_levels':0,'new_predictions':0,'new_scores':0,'new_submissions':0})
    print(json.dumps({'preflight_pass':True,'same_scope_bindings':15,'new_real_learning':0}))


def close():
    m.check_sources(w.read(PLAN));d=w.read(OUT/'report.json')
    next_unit='P98: register complete exact prior-only P97 evaluation with unchanged outer/cohort/scenario/family/level/influence guards; reuse90 same-scope P88 levels, zero new native/closed/source/CDF fits. Full price/observation replay before any transfer/admission. No K/mixture/line tuning.'
    text='# P97: prior calibrado sin GLM\n\nCodex, '+utc()+'.\n\nSe comprobó un camino de menor dimensión: niveles propios por componente/ramo/negocio y mezcla fija de riesgos fuente, sin la corrección GLM. El fixture mantuvo iguales los parámetros al alterar todo el payload retenido y los atributos de tarifa que este camino ignora. Momentos de calibración por otro método; suma escalar de componentes y calendario, JSON, subconjuntos y permutaciones exactos con ajuste GLM bloqueado. No se repitieron suites de fuentes, capital o reporte.\n\nLos quince ámbitos enlazan exactamente los90 parámetros de nivel P88 ya guardados, por claves/código/datos y controles adversos originales. No se generaron nuevos precios reales o scores ni se reestimaron parámetros. Quitar el GLM no prueba una mejora: la evaluación completa es el siguiente paso y conserva todas las guardas. Tampoco equivale a B12 constante o P65 con formas. B00 y todas las alternativas conservadas;2024abierto adaptativo, fuentes/valoración/cola y búsqueda adaptativa siguen limitando generalización. Sin revisión independiente o garantía privada.\n\nPróximo: '+next_unit+'\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'synthetic':w.rel(OUT/'synthetic.json'),'synthetic_sha256':w.sha(OUT/'synthetic.json'),'document':w.rel(DOC),'next_unit':next_unit,'new_native_fits':0,'new_real_levels':0,'new_predictions':0,'new_scores':0,'new_submissions':0,'2024_open':True,'goal_achieved':False,'forum':q.post(body,'COD-S2-20261027-PRIVADA-P97-PRIOR-RESULTADO','P97: prior sin GLM comprobado, evaluación aún pendiente')}
    cut=R/'privado'/('corte_P97_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));cut.mkdir();w.update(INDEX,receipt,cut)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P97'),(R/'registro/semana2_mision_privada_actual.json','P97')]:w.update(path,{key:receipt,'next_unit':next_unit},cut)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P97=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},cut)
    note='\n\n## Privada P97: prior sin GLM, preflight\n\nCodex, '+receipt['utc']+'. Exclusión integral y aritmética del prior comprobadas, quince ámbitos/niveles enlazados sin ajuste o precio real. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,cut)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_prior_only_preflight_index':w.rel(INDEX),'week_2_private_prior_only_preflight_report':w.rel(DOC)},cut)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');a=argparse.ArgumentParser(description=__doc__);a.add_argument('mode',choices=['register','run','close'])
    with m.e.threadpool_limits(limits=2):{'register':register,'run':run,'close':close}[a.parse_args().mode]()
