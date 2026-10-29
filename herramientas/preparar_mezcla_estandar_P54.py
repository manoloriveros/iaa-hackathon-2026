"""Preflight de mezcla fija A1S/T2b con calendario y reporte propios, sin ajuste real."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import argparse
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p54_existing_closed_engines',R/'herramientas/contrastar_fuente_controlada_P53.py')
h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
m=h.m;w=h.w;np=h.np;pd=h.pd;BASE=h.BASE;core=m.e.core;g=m.p.g
OUT=BASE/'P54_mezcla_estandar_preflight_20261027'
PLAN=R/'registro/semana2_mezcla_estandar_preflight_plan.json';INDEX=R/'registro/semana2_mezcla_estandar_preflight_actual.json'
DOC=R/'docs/archivo/semana2/PRIVADA_P54_MEZCLA_ESTANDAR_PREFLIGHT.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(p,v):return m.dump(p,v)


def component_frame(f,key,ultimate=False):
    z=f.copy();z['log_relative_A1S']=np.log(z[key].to_numpy(float))
    z['e_cost_scope']=z.exposure_calendar.to_numpy(float).copy()
    if not ultimate:z['e_cost_scope']*=z.q_paired.to_numpy(float)
    return z


def components(f,a,ultimate=False):
    first=core.apply_component(component_frame(f,'annual_A1S',ultimate),a['components']['A1S'])
    second=core.apply_component(component_frame(f,'annual_T2b',ultimate),a['components']['T2b'])
    mixed=.5*first+.5*second
    assert np.isfinite(mixed).all() and (mixed>0).all()
    return first,second,mixed


def forward(f,a,ultimate=False):
    _,_,value=components(f,a,ultimate);norms={}
    for stage in a['stages']:
        value,norm=g.apply_stage(f,value,stage);norms[stage['variable']]=norm
    return value,norms


def learn(f,line):
    train=f.loc[~f.is_held].copy();held=f.loc[f.is_held]
    assert set(train.group_id).isdisjoint(set(held.group_id)) and train.T0.ge(0).all()
    a={'line':line,'contract':'fixed_half_A1S_T2b_calendar_common_scoped_costq_single_learner',
        'components':{name:core.fit_component(component_frame(train,'annual_'+name),line) for name in ['A1S','T2b']},
        'fit_row_ids_digest':m.p.b.digest(sorted(train.row_id)),'fit_groups_digest':m.p.b.digest(sorted(set(train.group_id)))}
    _,_,value=components(train,a);stages=[];norms={}
    for variable in g.STAGES[line]:
        stage=g.fit_stage(train,value,variable);value,norm=g.apply_stage(train,value,stage)
        stages.append(stage);norms[variable]=norm
    a.update(stages=stages,training_normalizers=norms);return a


def constant_counts(a):
    return {'shape_factors':sum(sum(len(s['factors']) for s in c['shape']) for c in a['components'].values()),
        'level_constants':6,'residual_factors':sum(len(s['factors']) for s in a['stages']),
        'training_nuisance_levels':sum(len(s['nuisance_year_business']) for s in a['stages'])}


def frame_for(line,outer):
    f=pd.read_parquet(m.P1/f'canonical_{line}.parquet');f['is_held']=f.fold.eq(outer)
    q=pd.read_parquet(m.REPORTING/f'outer{outer}/target_{line}.parquet').set_index('row_id')
    raw=pd.read_parquet(h.OLD_SOURCE/f'target_{line}_three_seed_components.parquet',columns=['row_id','log_relative_A1S'])
    raw=raw.loc[raw.row_id.isin(set(f.row_id))].set_index('row_id')
    assert f.row_id.is_unique and raw.index.is_unique and set(f.row_id)==set(raw.index)==set(q.index)
    assert np.array_equal(q.loc[f.row_id,'year'],f.year)
    f['annual_A1S']=np.exp(raw.loc[f.row_id,'log_relative_A1S'].to_numpy())
    f['annual_T2b']=f.annual_raw_T2b.to_numpy(float);f['q_paired']=q.loc[f.row_id,'q_A1R'].to_numpy()
    assert f.year.isin([2023,2024]).all() and f.annual_A1S.gt(0).all() and f.annual_T2b.gt(0).all()
    assert f.q_paired.gt(0).all() and f.q_paired.le(1+1e-10).all()
    return f


def synthetic():
    rng=np.random.default_rng(2026102754);n=480
    f=pd.DataFrame({'row_id':['fake'+str(i) for i in range(n)],'group_id':['g'+str(i) for i in range(n)],
        'is_held':np.arange(n)%5==0,'year':2023+(np.arange(n)//5)%2,'new_business':(np.arange(n)//10)%2,
        'T0':rng.gamma(2,100,n)*(rng.random(n)<.3),'reserve':0.,'exposure_calendar':rng.uniform(.2,1,n),
        'q_paired':rng.uniform(.2,1,n),'annual_A1S':np.exp(rng.normal(0,.4,n)),'annual_T2b':np.exp(rng.normal(5,.5,n)),
        'ncb_years':rng.integers(0,15,n),'prior_claims_5y':rng.integers(0,3,n),
        'gender':rng.choice(['F','M'],n),'works_from_home':rng.integers(0,2,n),'marketing_segment':rng.choice(['a','b','c'],n)})
    records=[]
    for line in m.q.LINES:
        folder=OUT/'synthetic_members'/line
        a=m.once(folder,'primary',lambda:learn(f,line));bad=f.copy();bad.loc[bad.is_held,['T0','reserve']]=-1e30
        adverse=m.once(folder,'adverse',lambda:learn(bad,line));assert a==adverse
        held=f.loc[f.is_held];u,norm=forward(held,a,True)
        bad.loc[bad.is_held,'q_paired']=np.nan
        replay,nn=forward(bad.loc[bad.is_held],json.loads(json.dumps(adverse)),True)
        assert np.array_equal(u,replay) and norm==nn
        one,two,mix=components(held,a,True)
        assert np.array_equal(mix,np.array([.5*float(x)+.5*float(y) for x,y in zip(one,two)]))
        observed,obs_norm=forward(held,a,False)
        # Shared q gives a direct component identity; stage normalizers still belong to the chosen application scale.
        _,_,omix=components(held,a,False)
        assert np.allclose(omix,mix*held.q_paired.to_numpy(),rtol=1e-12)
        assert np.isfinite(u*held.q_paired.to_numpy()).all() and np.isfinite(observed).all()
        records.append({'line':line,'held_label_and_held_q_ultimate_invariance':True,'serialization_exact':True,
            'arithmetic_half_components_scalar_check':True,'observation_bridge_component_identity':True,
            'ultimate_and_observed_normalizers_recorded_separately':{'ultimate':norm,'observed':obs_norm}})
    return {'author':'Codex','utc':utc(),'records':records,'synthetic_primary_whole_learners':3,'synthetic_adverse_whole_learners_separate':3,
        'synthetic_component_calibrations_primary':6,'synthetic_component_calibrations_adverse_separate':6,
        'synthetic_residual_stage_calls_primary':4,'synthetic_residual_stage_calls_adverse_separate':4,'real_price_fits':0,'new_C0_fits':0,'new_scores':0}


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    assert (h.OUT/'completion_receipt.json').exists();OUT.mkdir()
    (OUT/'preflight_code.py').write_bytes(Path(__file__).read_bytes())
    dump(OUT/'synthetic.json',synthetic());bindings=[]
    for line in m.q.LINES:
        for outer in range(5):
            f=frame_for(line,outer);assert set(f.loc[f.is_held,'group_id']).isdisjoint(set(f.loc[~f.is_held,'group_id']))
            bindings.append({'line':line,'outer':outer,'rows':len(f),'held_rows':int(f.is_held.sum()),'row_year_groups_exact':True})
    dump(OUT/'bindings.json',bindings)
    paths=[Path(__file__),Path(h.__file__),Path(m.__file__),Path(core.__file__),Path(core.b.__file__),Path(g.__file__),
        OUT/'synthetic.json',OUT/'bindings.json',h.OUT/'report.json',h.OUT/'completion_receipt.json',m.PLAN,h.PLAN]
    sources=dict(w.read(h.PLAN)['sources']);sources.update({w.rel(p):w.sha(p) for p in paths})
    plan={'author':'Codex','utc':utc(),'need':'P53matched A1Scontrol still trails full reference by.002808D2; replacing source adds only-.000190point. Current evidence does not justify increasing tree capacity. Reference S2uses a fixed arithmetic half A1S/T2b mixture absent from both standalone controls.',
        'hypothesis':'Recover complementary standard T2brisk by separately calibrating two source-only inputs, then applying the original fixed50/50cost mixture and common residual stages. Test the complete new algorithm, not one winning component.',
        'current_scope':'Preflight only: synthetic whole flow and15real historical input joins; ZEROreal price/report fits, scores,2025inference or submissions. A separate full validation registration/commit/forum is required before real fitting.',
        'frozen_recipe':'Source-only saved3seed A1Srelative risk and original developed-only T2bannual_raw. Each gets original NCB/priorK300, line optimum and businessK400under sameP50own outer reporting qand calendar once. Fixed arithmetic weights .5/.5after calibration; original shared gender/WFH/marketing K300stages AFTER mixture. One complete target learner, not nestedH1or5targetmean. No new features, capacity, weights, source trees or C0.',
        'observation':'Common training-only cost-peril mixture qby line/outer is an explicit assumption for BOTHcomponents; no per-row-peril-truth claim. Ultimate applies calendar and ultimate stage normalizers; evaluation multiplies by ownq AFTER that flow. Direct observed-stage application is not substituted for ultimate*q.',
        'future_validation':'Same P52global/scenario/cohort/family16/level/influence gates, no relaxation. All3lines/5folds/bothyears, full production-equivalent algorithm,15primary+15poison whole learners (30+30component calibrations,20+20residual stage calls). No source fits or nominalC0refits. Pooled failure rejects; pooled pass needs OWNconditional-transfer whole validation before production/admission. Scenario branches keep final ultimate prices nominal; no claim of full branch re-training.',
        'future_acceptance':{k:w.read(m.PLAN)[k] for k in ['criteria','bootstrap','cohort_guard','level_sensitivity']},
        'sources':sources,'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False,
        'limits':['P53matched source effect has point estimates, no new interval; source adequacy not established by a small point gap.',
            'Remaining loss includes observation and target architecture, not a causal decomposition.',
            'Adaptive2023/2024and conditional source2024, reporting-tail/reserves and undated master assumptions remain. No private improvement claim.']}
    dump(PLAN,plan);text='# P54: mezcla estándar fija, preflight completo\n\nCodex, '+utc()+'. El control P53conserva una brecha de−0,002808con la fuente A1S. La referencia usa una mezcla aritmética fija50/50con T2b que los dos modelos autónomos omitieron. Se prepara ese mecanismo estándar antes de aumentar capacidad.\n\n'
    text+='Dos componentes con sus propias calibraciones cerradas, costes comparables antes de mezclar, residual común después. El calendario entra una vez y el avance a último usa sus normalizadores propios. El qP50común por ramo es una hipótesis explícita, sin fingir composición por peril por fila. Pasaron3flujos sintéticos primarios/3adversos (6+6componentes,4+4etapas residuales), serialización, etiquetas/qretenidos alterados y suma escalar50/50. Se enlazaron los15ámbitos históricos por claves/años/grupos.\n\n'
    text+='No se ajustaron precios reales, curvas o fuentes ni se puntuó. Antes de hacerlo debe registrarse y versionarse la evaluación completa con todas las guardas P52, incluida la transferencia propia si pasa el combinado. No hay CSV admitido. B00/F3c/adversos conservados,2024abierto adaptativo, privada prioritaria.\n\nPlan: '+w.rel(PLAN)+'; SHA '+w.sha(PLAN)+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':'P54synthetic_and_real_binding_preflight_passed_no_real_learning','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),'document':w.rel(DOC),
        'real_price_fits':0,'new_C0_fits':0,'new_scores':0,'new_submissions':0,'next_unit':'P55: register and commit the exact P54fixed50/50complete target validation, shared P50qand current scenarios; no new source fits. Test all unchanged gates, stage transfer only after pooled pass. Do not replace final ultimate-normalizer mapping by observed forward.',
        'forum':m.q.post(body,'COD-S2-20261027-PRIVADA-P54-MEZCLA-PREFLIGHT','P54: mezcla estándar fija y flujo completo sintético, sin ajuste real')}
    dump(INDEX,receipt);dump(OUT/'completion_receipt.json',receipt)
    archive=R/'privado'/('corte_P54_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir()
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P54'),(R/'registro/semana2_mision_privada_actual.json','P54')]:w.update(path,{key:receipt,'next_unit':receipt['next_unit']},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P54=receipt,next_unit=receipt['next_unit']);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    counts=R/'registro/semana2_contadores_propios_actual.json';w.update(counts,{'phase2_private_P54_mixture_preflight':w.read(OUT/'synthetic.json')},archive)
    note='\n\n## Privada P54: mezcla estándar fija, preflight\n\nCodex, '+receipt['utc']+'.Flujo sintético completo y15enlaces históricos pasaron, cero ajustes reales/C0/scores/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+receipt['next_unit']+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_fixed_mixture_preflight_index':w.rel(INDEX),'week_2_private_fixed_mixture_preflight_report':w.rel(DOC)},archive)
    print(json.dumps({'preflight':'passed','bindings':15,'real_fits':0,'new_scores':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['prepare']);p.parse_args()
    with m.e.threadpool_limits(limits=2):prepare()
