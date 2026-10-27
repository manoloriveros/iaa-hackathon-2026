"""P65 sin etapas G compartidas, conservando íntegros sus componentes propios."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p99_existing_components',R/'herramientas/validar_reporte_por_ramo_P65.py')
h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
k=h.k;m=h.m;q=h.q;w=h.w;np=h.np;pd=h.pd;BASE=h.BASE
OLD=h.OUT;OUT=BASE/'P99_componentes_sin_G_preflight_20261027'
PLAN=R/'registro/semana2_componentes_sin_G_preflight_plan.json';INDEX=R/'registro/semana2_componentes_sin_G_preflight_actual.json'
DOC=R/'docs/semana2/PRIVADA_P99_COMPONENTES_SIN_G_PREFLIGHT.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)
def frame_for(line,outer):return h.frame_for(line,outer)


def learn_components(frame,line):
    train=frame.loc[~frame.is_held].copy()
    assert set(train.group_id).isdisjoint(set(frame.loc[frame.is_held,'group_id']))
    return {'line':line,'contract':'P65_components_only_no_shared_G',
        'components':{name:k.core.fit_component(k.component_frame(train,'annual_'+name),line) for name in ['A1S','T2b']},
        'fit_row_ids_digest':m.p.b.digest(sorted(train.row_id)),'fit_groups_digest':m.p.b.digest(sorted(set(train.group_id))),
        'stages':[],'training_normalizers':{}}


def cached(frame,line,outer):
    train=frame.loc[~frame.is_held];old=w.read(OLD/f'{line}_{outer}/learning.json')
    assert old==w.read(OLD/f'{line}_{outer}/adverse_learning.json')
    assert old['fit_row_ids_digest']==m.p.b.digest(sorted(train.row_id))
    assert old['fit_groups_digest']==m.p.b.digest(sorted(set(train.group_id)))
    parent=w.read(h.PLAN)
    for path in [Path(k.__file__),h.t.OUT/f'input_{line}_{outer}.parquet']:
        assert parent['sources'][w.rel(path)]==w.sha(path)
    return {'line':line,'contract':'P65_components_only_no_shared_G','components':old['components'],
        'fit_row_ids_digest':old['fit_row_ids_digest'],'fit_groups_digest':old['fit_groups_digest'],
        'stages':[],'training_normalizers':{}}


def forward(frame,artifact,ultimate=True):
    assert artifact['stages']==[] and artifact['training_normalizers']=={}
    _,_,value=k.components(frame,artifact,ultimate)
    return value,{}


def independent_math(train,artifact):return h.v.component_level_math(train,artifact)


def synthetic():
    rng=np.random.default_rng(2026102799);n=480;i=np.arange(n)
    f=pd.DataFrame({'row_id':['s'+str(j) for j in i],'group_id':['g'+str(j) for j in i],'is_held':i%5==0,
        'year':2023+(i//5)%2,'new_business':(i//10)%2,'T0':rng.gamma(2,100,n)*(rng.random(n)<.3),'reserve':0.,
        'exposure_calendar':rng.uniform(.2,1,n),'q_paired':rng.uniform(.2,1,n),'annual_A1S':np.exp(rng.normal(0,.4,n)),
        'annual_T2b':np.exp(rng.normal(5,.5,n)),'ncb_years':rng.integers(0,15,n),'prior_claims_5y':rng.integers(0,3,n),
        'gender':rng.choice(['F','M'],n),'works_from_home':rng.integers(0,2,n),'marketing_segment':rng.choice(['a','b','c'],n)})
    records=[]
    def reject(*args,**kwargs):raise AssertionError('No shared G stage may fit or apply')
    originals=(k.g.fit_stage,k.g.apply_stage);k.g.fit_stage=reject;k.g.apply_stage=reject
    try:
        for line in q.LINES:
            f['line']=line
            a=learn_components(f,line);bad=f.copy()
            for name in ['T0','reserve','q_paired','exposure_calendar','annual_A1S','annual_T2b','new_business','ncb_years','prior_claims_5y','gender','works_from_home','marketing_segment']:
                bad[name]=bad[name].astype('object');bad.loc[bad.is_held,name]='INVALID_HELD'
            assert a==learn_components(bad,line)
            no_G=f.copy();no_G[['gender','works_from_home','marketing_segment']]='INVALID_EVERYWHERE'
            assert a==learn_components(no_G,line)
            checks=independent_math(f.loc[~f.is_held],a)
            held=f.loc[f.is_held].drop(columns=['T0','reserve','gender','works_from_home','marketing_segment'])
            u,norm=forward(held,a,True);one,two,_=k.components(held,a,True)
            assert np.array_equal(u,np.array([.5*float(x)+.5*float(y) for x,y in zip(one,two)])) and norm=={}
            observed,_=forward(held,a,False);assert np.allclose(observed,u*held.q_paired.to_numpy(),rtol=2e-13)
            clean=held.drop(columns='q_paired');stored=json.loads(json.dumps(a));assert np.array_equal(u,forward(clean,stored,True)[0])
            ix=np.arange(0,len(clean),3);order=np.arange(len(clean))[::-1]
            assert np.array_equal(forward(clean.iloc[ix],stored,True)[0],u[ix])
            assert np.array_equal(forward(clean.iloc[order],stored,True)[0],u[order])
            records.append({'line':line,'whole_component_held_poison_exact':True,'all_removed_G_payload_ignored_exact':True,
                'G_fit_and_apply_blocked':True,'independent_component_level_math':checks,'half_mixture_scalar_exact':True,
                'own_observation_bridge_matches_without_batch_normalizers':True,'JSON_subset_permutation_exact':True})
    finally:k.g.fit_stage,k.g.apply_stage=originals
    return {'author':'Codex','utc':utc(),'records':records,'synthetic_primary_components':6,'synthetic_adverse_components_separate':6,
        'synthetic_additional_ignored_G_controls_components':6,'new_real_fits':0,'new_real_levels':0,'new_real_predictions':0,
        'new_scores':0,'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0}


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert phase['P98_execution']['state']=='TERMINAL_SUCCESS'
    assert not phase.get('active_jobs') and not phase.get('active_execution')
    previous=BASE/'P98_validacion_prior_solo_20261027';assert w.read(previous/'completion_receipt.json')['report_sha256']==w.sha(previous/'report.json')
    parent=w.read(h.PLAN);m.check_sources(parent)
    inventory=[];inventory_paths=[];current_prefix=w.rel(h.t.OUT)+'/'
    for path in sorted((R/'registro').glob('*plan*.json')):
        d=w.read(path)
        source_values=d.get('sources',{})
        source_paths=list(source_values) if isinstance(source_values,dict) else [x if isinstance(x,str) else x.get('path',x.get('file','')) for x in source_values]
        if d.get('author')=='Codex' and any(name.startswith(current_prefix) for name in source_paths):
            inventory.append({'plan':w.rel(path),'sha256':w.sha(path),'candidate':d.get('candidate'),
                'one_change':d.get('one_change',d.get('change',d.get('single_change'))),'configuration':d.get('configuration',{})})
            inventory_paths.append(path)
    assert h.PLAN in inventory_paths
    stages=[]
    for line in q.LINES:
        for outer in range(5):
            a=w.read(OLD/f'{line}_{outer}/learning.json');stages.append({'line':line,'outer':outer,'variables':[z['variable'] for z in a['stages']],
                'component_shape_variables':{name:[z.get('variable',z.get('name')) for z in obj['shape']] for name,obj in a['components'].items()}})
    assert sum(len(z['variables']) for z in stages)==20
    OUT.mkdir();dump(OUT/'recipe_inventory.json',{'author':'Codex','utc':utc(),'current_reporting':w.rel(h.t.PLAN),'current_reporting_sha256':w.sha(h.t.PLAN),
        'scope':'Own registered recipes inspected for identical current-P64 component-only candidate; no identical registered candidate identified. Not a claim about other authors/chats.',
        'recipes':inventory,'P65_stages':stages,'P98_difference':'Prior-only has no P65 NCB/history component shapes; it is not the proposed ablation.'})
    paths=[Path(__file__),Path(h.__file__),Path(k.__file__),OLD/'report.json',OLD/'completion_receipt.json',h.PLAN,
        previous/'report.json',previous/'completion_receipt.json',OUT/'recipe_inventory.json']
    paths += [OLD/f'{line}_{outer}/{name}.json' for line in q.LINES for outer in range(5) for name in ['learning','adverse_learning']]
    paths += inventory_paths
    plan={'author':'Codex','utc':utc(),'candidate':'P65 complete source-shaped components with all final shared G stages omitted',
        'need':'P98 unshaped prior-only improves rejected GLM variants but remains below reference; it removed both history shapes and shared stages relative to P65. Isolate the final stage instead of adding capacity.',
        'hypothesis':'Component-specific history/NCB/business calibration may supply enough target adaptation; removing shared residual stages may reduce target variance and application-batch dependence. Unknown benefit, not proof a particular covariate is harmful.',
        'one_change':'Remove ALL20 shared residual G stages and their training/application normalizers from P65 across all lines/folds. Preserve exact component shape factors/normalizers, levels, business shrinkage, fixed50/50, sources, q, target and calendar.',
        'configuration':{'components':'Original P65 A/E history/NCB K300 shape rules and Tweedie line/business K400 levels, fully reused by own scope; not P80 metric-moment shapes or P98 unshaped prior.',
            'shared_stages':'No G fit/apply; gender, works_from_home and marketing_segment ignored by the target component-only path. Frozen source functions retain their original fields.',
            'application':'Apply stored components on ultimate calendar, then half mixture; no target batch normalization. Multiply by own q only for observed evaluation.',
            'reuse':'All30 P65 own-scope component objects by model/adverse/code/input/key hashes. Their learning precedes shared G and does not depend on it. No shared-stage constants counted as reused price parameters.'},
        'preflight_criterion':'Full synthetic component learning with all held payload poisoned before selection, all removed G payload corrupted even in train, G fit/apply blocked, scalar levels/half mixture, observation bridge and JSON/subset/permutation.15cached scopes key/code/data checked without real forward.',
        'future_budget':{'new_native_fits':0,'new_real_closed_levels':0,'reused_primary_component_objects':30,'reused_adverse_component_objects_separate':30,
            'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0},
        'future_criterion':'Same complete outer pooled/cohort/scenario/family16/level/influence gates, separate own transfer after pooled pass before anyCSV. No G subset/ramo/weight/K changes selected from held/public results.',
        'sources':{**parent['sources'],**{w.rel(path):w.sha(path) for path in paths}},'limits':parent['limits']+['Adaptive global stage ablation; no pristine validation or proof removed fields fail prospectively.'],
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md';body.write_text('Codex. P99 registra una separación global: conservar todos los componentes P65 con sus formas de historial/NCB, niveles y negocio, y omitir las veinte etapas G compartidas. Se distingue de P98, que también quitó las formas. El inventario de recetas propias con el reporte actual no identifica una combinación idéntica ya evaluada. La hipótesis es reducir variación/normalización de la etapa final, sin elegir un campo o ramo por score. Primero flujo sintético integral con veneno retenido y todos los campos G alterados incluso en train, G bloqueado, momentos/mezcla/calendario y replay. Treinta componentes reales se enlazarán por ámbito sin aplicar a datos reales. Evaluación real con registro posterior y mismas guardas; cero ajustes reales/fuentes/CDF/2025/envíos. B00 preservado,2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P99registered_before_component_only_preflight','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P99-COMPONENTES-PREVIO','P99: componentes intactos sin etapas compartidas, preflight')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def run():
    plan=w.read(PLAN);m.check_sources(plan);dump(OUT/'synthetic.json',synthetic());bindings=[]
    for line in q.LINES:
        for outer in range(5):
            a=cached(frame_for(line,outer),line,outer)
            assert a['components']==w.read(OLD/f'{line}_{outer}/learning.json')['components']
            bindings.append({'line':line,'outer':outer,'component_objects_exact_P65':True,'shared_stages_empty':True,'component_digest':m.p.b.digest(a['components'])})
    m.check_sources(plan);dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P99component_only_full_synthetic_and_scope_bindings_complete','bindings':bindings,
        'new_real_fits':0,'new_real_levels':0,'new_real_predictions':0,'new_scores':0,'new_submissions':0})
    print(json.dumps({'preflight_pass':True,'same_scope_component_objects':30,'new_real_fits':0}))


def close():
    plan=w.read(PLAN);m.check_sources(plan);d=w.read(OUT/'report.json')
    next_unit='P100: preregister exact global P65 component-only/no-G evaluation, all30own-scope component objects reused, zero new native/closed/source/CDF learning. Same P64row-q/scenarios and all fixed outer/cohort/family/level/influence gates; complete replay and own transfer required before any CSV. No field/stage/line subset or K/weight rescue.'
    text='# P99: componentes sin correcciones compartidas\n\nCodex, '+utc()+'.\n\nEl inventario de recetas propias con el reporte actual no encontró esta combinación exacta. Se mantienen las formas y niveles de los componentes P65; se retiran juntas sus veinte etapas compartidas. P98 también retiraba las formas de historial, por lo que sus resultados no aislaban esta etapa. No se cambia un peso, umbral o factor individual.\n\nEl flujo sintético aprendió sus componentes después de excluir el retenido. Alterar todo el payload retenido o los campos G en todas las filas conservó los parámetros. Se bloquearon ajuste y aplicación de G. Momentos por otra suma, mezcla50/50 escalar, puente de observación y replay JSON/subconjuntos/permutaciones exactos. Los quince ámbitos reales enlazan sus treinta componentes intactos por claves/código/datos sin producir precios reales.\n\nCero nuevos parámetros reales, score, fuente/CDF/2025/envío. Sigue pendiente la evaluación completa con las mismas guardas y, solo si pasa, transferencia propia antes del CSV. La hipótesis de menor variación no demuestra un beneficio o efecto causal de género/teletrabajo/marketing; las funciones fuente congeladas conservan sus atributos. B00 y alternativas preservadas,2024abierto adaptativo. Fuente, snapshots, valoración, cola y búsqueda adaptativa siguen limitando generalización; sin revisión independiente.\n\nPróximo: '+next_unit+'\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),
        'synthetic':w.rel(OUT/'synthetic.json'),'synthetic_sha256':w.sha(OUT/'synthetic.json'),'document':w.rel(DOC),'next_unit':next_unit,
        'new_real_fits':0,'new_real_levels':0,'new_real_predictions':0,'new_scores':0,'new_submissions':0,'2024_open':True,'goal_achieved':False,
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P99-COMPONENTES-RESULTADO','P99: separación de etapas comprobada antes de precios reales')}
    cut=R/'privado'/('corte_P99_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));cut.mkdir();w.update(INDEX,receipt,cut)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P99'),(R/'registro/semana2_mision_privada_actual.json','P99')]:w.update(path,{key:receipt,'next_unit':next_unit},cut)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P99=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},cut)
    note='\n\n## Privada P99: componentes sin G, preflight\n\nCodex, '+receipt['utc']+'. Componentes propios intactos, G omitido globalmente; veneno integral, matemática y replay sintéticos pasaron. Treinta componentes enlazados sin precio real o ajuste. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,cut)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_component_only_preflight_index':w.rel(INDEX),'week_2_private_component_only_preflight_report':w.rel(DOC)},cut)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');a=argparse.ArgumentParser(description=__doc__);a.add_argument('mode',choices=['register','run','close'])
    with m.e.threadpool_limits(limits=2):{'register':register,'run':run,'close':close}[a.parse_args().mode]()
