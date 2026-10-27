"""Centrado G persistido en entrenamiento, sin volver a estimar sus factores.

El nuisance por año/negocio de fit_stage hace los factores invariantes ante una
escala constante de base por celda. Permite conservar los factores P65 al pasar
de normalización por lote a centros de último fijos por negocio. El control
sintético reaprende la cadena alternativa para comprobar esa equivalencia.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import math
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p101_existing_scoped_components',R/'herramientas/preparar_componentes_sin_G_P99.py')
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
k=p.k;h=p.h;m=p.m;q=p.q;w=p.w;np=p.np;pd=p.pd;BASE=p.BASE
OLD=p.OLD;OUT=BASE/'P101_centrado_fijo_preflight_20261027'
PLAN=R/'registro/semana2_centrado_fijo_preflight_plan.json';INDEX=R/'registro/semana2_centrado_fijo_preflight_actual.json'
DOC=R/'docs/semana2/PRIVADA_P101_CENTRADO_FIJO_PREFLIGHT.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)
def frame_for(line,outer):return p.frame_for(line,outer)


def factors(frame,stage):
    labels=k.g.key(frame[stage['variable']])
    return np.array([stage['factors'].get(label,1.) for label in labels])


def centers(train,ultimate,factor):
    nb=train.new_business.to_numpy(int);assert np.isin(nb,[0,1]).all()
    result={}
    for business in [0,1]:
        mask=nb==business;assert mask.any()
        result[str(business)]=float(np.sum(ultimate[mask]*factor[mask])/np.sum(ultimate[mask]))
        assert np.isfinite(result[str(business)]) and result[str(business)]>0
    return result


def apply_fixed(frame,base,stage):
    nb=frame.new_business.to_numpy(int);assert np.isin(nb,[0,1]).all()
    fixed=np.array([stage['frozen_ultimate_business_centers'][str(value)] for value in nb])
    value=base*factors(frame,stage)/fixed
    assert np.isfinite(value).all() and (value>0).all()
    return value


def freeze_centers(frame,original):
    # All transformations are AFTER the training selector; held can be invalid.
    train=frame.loc[~frame.is_held].copy()
    assert set(train.group_id).isdisjoint(set(frame.loc[frame.is_held,'group_id']))
    assert original['fit_row_ids_digest']==m.p.b.digest(sorted(train.row_id))
    assert original['fit_groups_digest']==m.p.b.digest(sorted(set(train.group_id)))
    _,_,ultimate=k.components(train,original,True);stages=[];controls=[]
    for old in original['stages']:
        assert old['training_row_ids_digest']==k.g.digest(sorted(train.row_id))
        assert old['training_groups_digest']==k.g.digest(sorted(set(train.group_id)))
        stage=dict(old);factor=factors(train,stage);fixed=centers(train,ultimate,factor)
        for business in [0,1]:
            mask=train.new_business.to_numpy(int)==business
            scalar=math.fsum((float(u)*float(f) for u,f in zip(ultimate[mask],factor[mask])))/math.fsum(ultimate[mask].tolist())
            assert math.isclose(scalar,fixed[str(business)],rel_tol=3e-14)
        stage['frozen_ultimate_business_centers']=fixed
        changed=apply_fixed(train,ultimate,stage)
        for business in [0,1]:
            mask=train.new_business.to_numpy(int)==business
            assert math.isclose(math.fsum(changed[mask].tolist()),math.fsum(ultimate[mask].tolist()),rel_tol=3e-14)
        controls.append({'variable':stage['variable'],'scalar_centers_match':True,'own_training_ultimate_business_totals_preserved':True})
        ultimate=changed;stages.append(stage)
    return {'line':original['line'],'contract':'Same_P65_components_Gfactors_train_frozen_ultimate_NB_centers',
        'components':original['components'],'stages':stages,'fit_row_ids_digest':original['fit_row_ids_digest'],
        'fit_groups_digest':original['fit_groups_digest'],'center_controls':controls,
        'factor_learning_provenance':'Original P65 stage factors; year/business baseline-scale invariance. No new nuisance or factor estimation.'}


def forward(frame,artifact,ultimate=True):
    assert ultimate
    _,_,value=k.components(frame,artifact,True)
    for stage in artifact['stages']:value=apply_fixed(frame,value,stage)
    return value,{'frozen_centers':{s['variable']:s['frozen_ultimate_business_centers'] for s in artifact['stages']}}


def cached(frame,line,outer):
    # Component ancestry is checked by the unchanged P99 scope binder.
    component=p.cached(frame,line,outer);old=w.read(OLD/f'{line}_{outer}/learning.json')
    assert component['components']==old['components']
    return old


def learn_original_fixture(frame,line):
    # Typed held poison leaves the pandas column dtype as object even after
    # row exclusion. Restore numeric dtype ONLY on selected training rows.
    train=frame.loc[~frame.is_held].copy()
    assert set(train.group_id).isdisjoint(set(frame.loc[frame.is_held,'group_id']))
    train['T0']=pd.to_numeric(train.T0,errors='raise').astype(float)
    return k.learn(train,line)


def synthetic():
    rng=np.random.default_rng(20261027101);n=480;i=np.arange(n)
    f=pd.DataFrame({'row_id':['s'+str(j) for j in i],'group_id':['g'+str(j) for j in i],'is_held':i%5==0,
        'year':2023+(i//5)%2,'new_business':(i//10)%2,'T0':rng.gamma(2,100,n)*(rng.random(n)<.3),'reserve':0.,
        'exposure_calendar':rng.uniform(.2,1,n),'q_paired':rng.uniform(.2,1,n),'annual_A1S':np.exp(rng.normal(0,.4,n)),
        'annual_T2b':np.exp(rng.normal(5,.5,n)),'ncb_years':rng.integers(0,15,n),'prior_claims_5y':rng.integers(0,3,n),
        'gender':rng.choice(['F','M'],n),'works_from_home':rng.integers(0,2,n),'marketing_segment':rng.choice(['a','b','c'],n)})
    records=[]
    for line in q.LINES:
        f['line']=line
        original=learn_original_fixture(f,line);a=freeze_centers(f,original);bad=f.copy()
        for name in ['T0','reserve','annual_A1S','annual_T2b','exposure_calendar','q_paired','new_business','ncb_years','prior_claims_5y','gender','works_from_home','marketing_segment']:
            bad[name]=bad[name].astype('object');bad.loc[bad.is_held,name]='INVALID_HELD'
        adverse_original=learn_original_fixture(bad,line);adverse=freeze_centers(bad,adverse_original)
        assert a==adverse and original==adverse_original
        # Independent fresh alternative chain: learned nuisance cancels each
        # year/business scale change induced by earlier fixed centering.
        train=f.loc[~f.is_held];_,_,u=k.components(train,original,True);observed=u*train.q_paired.to_numpy()
        for stage in a['stages']:
            fresh=k.g.fit_stage(train,observed,stage['variable'])
            assert fresh['positive_period_counts']==stage['positive_period_counts']
            for label,value in stage['factors'].items():
                assert math.isclose(value,fresh['factors'][label],rel_tol=3e-13,abs_tol=1e-14)
            fresh['frozen_ultimate_business_centers']=centers(train,u,factors(train,fresh))
            next_u=apply_fixed(train,u,fresh);next_obs=apply_fixed(train,observed,fresh)
            assert np.allclose(next_obs,next_u*train.q_paired.to_numpy(),rtol=3e-13)
            for business in [0,1]:assert math.isclose(fresh['frozen_ultimate_business_centers'][str(business)],stage['frozen_ultimate_business_centers'][str(business)],rel_tol=3e-13)
            u=next_u;observed=next_obs
        expected=forward(train,a,True)[0];assert np.allclose(u,expected,rtol=3e-13)
        held=f.loc[f.is_held].drop(columns=['T0','reserve','q_paired'])
        value,_=forward(held,a,True);stored=json.loads(json.dumps(a))
        save=(k.g.fit_stage,k.g.apply_stage,k.core.fit_component)
        def reject(*args,**kwargs):raise AssertionError('No learning or application-batch normalization during replay')
        try:
            k.g.fit_stage=reject;k.g.apply_stage=reject;k.core.fit_component=reject
            assert np.array_equal(value,forward(held,stored,True)[0])
            # Singleton/single-business applications used to require a full
            # year/business batch; new quoting must be projective.
            for j in [0,len(held)//2,len(held)-1]:assert math.isclose(forward(held.iloc[[j]],stored,True)[0][0],value[j],rel_tol=3e-14)
            ix=np.arange(0,len(held),3);order=np.arange(len(held))[::-1]
            assert np.allclose(forward(held.iloc[ix],stored,True)[0],value[ix],rtol=3e-14,atol=0)
            assert np.allclose(forward(held.iloc[order],stored,True)[0],value[order],rtol=3e-14,atol=0)
            unknown=held.copy()
            for stage in stored['stages']:
                unknown[stage['variable']]='__UNSEEN__';assert np.array_equal(factors(unknown,stage),np.ones(len(unknown)))
            if stored['stages']:
                base=k.components(unknown,stored,True)[2];manual=base.copy()
                for stage in stored['stages']:manual/=np.array([stage['frozen_ultimate_business_centers'][str(int(nb))] for nb in unknown.new_business])
                assert np.array_equal(forward(unknown,stored,True)[0],manual)
        finally:k.g.fit_stage,k.g.apply_stage,k.core.fit_component=save
        records.append({'line':line,'whole_original_learning_and_center_held_poison_exact':True,
            'fresh_alternative_chain_factors_and_centers_match_reuse':True,'observed_ultimate_q_commutes_with_fixed_centers':True,
            'scalar_centers_and_training_business_totals_checked':True,'JSON_exact_singleton_subset_permutation_rtol3e14':True,
            'unknown_factor_one_before_fixed_center_not_final_identity':True})
    return {'author':'Codex','utc':utc(),'records':records,'synthetic_primary_component_fits':6,'synthetic_adverse_component_fits_separate':6,
        'synthetic_original_primary_G_stage_fits':4,'synthetic_original_adverse_G_stage_fits_separate':4,'synthetic_fresh_alternative_stage_controls':4,
        'new_real_fits':0,'new_real_centers':0,'new_real_predictions':0,'new_scores':0,'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0}


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert phase['P100_execution']['state']=='TERMINAL_SUCCESS'
    assert not phase.get('active_jobs') and not phase.get('active_execution')
    previous=BASE/'P100_validacion_componentes_sin_G_20261027';assert w.read(previous/'completion_receipt.json')['report_sha256']==w.sha(previous/'report.json')
    parent=w.read(p.PLAN);m.check_sources(parent)
    paths=[Path(__file__),Path(k.g.__file__),p.PLAN,p.OUT/'report.json',p.OUT/'synthetic.json',p.OUT/'completion_receipt.json',previous/'report.json',previous/'completion_receipt.json']
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'candidate':'P65 components and G factors with own-training ultimate business centers persisted',
        'need':'P100removing allGstages fails. Original Gapply_stage computes normalizers from every application year/business batch, so a quote depends on other rows and legitimate future mix shifts are normalized away. This is a portability mechanism, not evidence the existing implementation leaks labels.',
        'hypothesis':'Retain the source and residual risk effects but center only with own-training ultimate prices, allowing actual covariate mix changes to alter future mean costs. Private benefit unknown; no normalization to public totals.',
        'one_change':'Replace application-year/business Gbatch centers with persisted own-training ultimate-weighted centers for NB/renewal, sequentially. Keep every component and Gfactor/K/stage order fixed.',
        'configuration':{'formula':'For each Gstage and business b, c_b=sum_train(U_i*f_i)/sum_train(U_i); then U_i<-U_i*f_i/c_b. Learn centers sequentially from previous new-stage U. Pool own-training2023/2024within business; require positive support; no yearkey fallback or future centering.',
            'factor_reuse_proof':'For any positive constant a within year/business, factor fit nuisance k(y,a*base)=k(y,base)/a. Adjusted base is identical, so raw and K300shrunk category factors/positive counts are invariant. Each previous centering change is such a cellwise scale; induction permits all original P65 factors. Original nuisance/base digest is historical provenance, not a claim of a fresh fit under new baseline.',
            'centers':'Two finite positive centers per Gstage, forty primary/fory adverse real constants if evaluated. Derived only from train source/component risks and stage factors; no direct target/q in center calculation, but their learned ancestors are target-trained.',
            'application':'Component ultimate calendar, same Gfactors divided by stored business centers; no grouping by applicationyear or cohort, no live q/target/recalibration. Known unknown-category rule rawfactor1 is retained BEFOREfixedcentering; its final price effect need not be identity.',
            'observation':'Training ultimate and observed prices retain O=qU through every new stage because both use the same fixed centers. Evaluation remains final U*ownq; no new CDF or valuation claim.'},
        'preflight_criterion':'Fresh original primary/adverse synthetic whole component/Glearning and center conversion exact under all held poison; separately refit full alternative sequential Gchain and match factors/centers to reused version. Scalar center math, business-total checks, JSON/singleton/subset/permutation, unknown rawfactor policy and qbridge with batch Gapplication/learning blocked at replay.',
        'future_budget':{'new_native_fits':0,'new_real_G_factor_fits':0,'reused_primary_components':30,'reused_primary_G_stages':20,'new_primary_frozen_centers':40,'adverse_frozen_centers_separate':40,'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0},
        'future_criterion':'All unchanged pooled/cohort/scenario/family16/level/influence gates; separate own transfer after pass before CSV. No choosing NB/years/stages/weights/K or public-total rescaling after outcome.',
        'sources':{**parent['sources'],**{w.rel(path):w.sha(path) for path in paths}},'limits':parent['limits']+['Frozen training mix may also transport poorly; projective quoting and synthetic equivalence are not evidence of predictive gain. Unknown categories keep rawneutral1 before fixed center and can have nonidentity final scaling.'],
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md';body.write_text('Codex. P101 registra una alternativa de normalización: conservar todos los componentes/factores G de P65 y fijar sus centros con precios últimos del entrenamiento propio por negocio, antes de cotizar. Así el precio no depende del lote futuro. Los factores se reutilizan solo si pasa la prueba: el nuisance año/negocio cancela cada cambio de escala de la base; se comprobará reaprendiendo una cadena alternativa completa sintética. No se normaliza al total público, no se cambia K, peso, orden o campo. Se verifican veneno integral, centros escalares, puente q, JSON y cotización individual/subconjuntos con aplicación Gpor lote bloqueada. Desconocidos conservan factor bruto1 antes del centro fijo; no se afirma precio final idéntico. Preflight sin parámetros o precios reales. Evaluación posterior con40centros primarios/40adversos, cero nuevos factores/nativos/CDF y mismas guardas; B00 preservado,2024abierto adaptativo, ceroenvíos. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P101registered_before_fixed_center_synthetic_proof','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P101-CENTROS-PREVIO','P101: centrado de entrenamiento fijo, antes de probar equivalencia')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def run():
    plan=w.read(PLAN);m.check_sources(plan);dump(OUT/'synthetic.json',synthetic());bindings=[]
    for line in q.LINES:
        for outer in range(5):
            f=frame_for(line,outer);a=cached(f,line,outer)
            for stage in a['stages']:
                assert stage['training_row_ids_digest']==k.g.digest(sorted(f.loc[~f.is_held,'row_id']))
                assert stage['training_groups_digest']==k.g.digest(sorted(set(f.loc[~f.is_held,'group_id'])))
            bindings.append({'line':line,'outer':outer,'component_and_factor_scope_exact':True,'stages':len(a['stages']),'no_new_real_center_or_application':True})
    assert sum(z['stages'] for z in bindings)==20
    m.check_sources(plan);dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P101fixed_centers_full_synthetic_equivalence_and_scope_bindings_complete','bindings':bindings,
        'new_real_fits':0,'new_real_centers':0,'new_real_predictions':0,'new_scores':0,'new_submissions':0})
    print(json.dumps({'preflight_pass':True,'same_scope_components':30,'same_scope_Gstages':20,'new_real_parameters':0}))


def close():
    plan=w.read(PLAN);m.check_sources(plan);d=w.read(OUT/'report.json')
    next_unit='P102: separately register complete exact P101fixed own-training ultimate business-center evaluation. Reuse allP65components/Gfactors byscope, learn only40primary/40adverse centers; zero real factor/native/source/CDF fits. All old gates/scenarios, full replay and own transfer before CSV. No source/stage/line/K/centering-scope refinement from outcome.'
    text='# P101: centrado fijo de entrenamiento\n\nCodex, '+utc()+'.\n\nSe comprobó una alternativa que conserva todos los factores de P65 y aprende sus centros de último solo en el entrenamiento propio, por negocio. Al aplicar, cada fila usa constantes guardadas y su precio no depende del lote. Los centros se calculan secuencialmente y conservan los totales últimos de cada negocio en el entrenamiento, sin preservar por obligación un total futuro.\n\nLa reutilización de factores tiene una condición matemática comprobada: el nuisance año/negocio del estimador cancela una escala constante de la base en su celda. Las nuevas normalizaciones anteriores solo introducen ese tipo de escala. El fixture reaprendió la cadena alternativa completa; sus factores y centros coincidieron con la ruta reutilizada dentro de la precisión numérica declarada. No se repitió ningún ajuste real. El nuisance y digest antiguos siguen siendo procedencia histórica, no un nuevo ajuste.\n\nPasaron aprendizaje original completo y conversión con todo el payload retenido alterado, sumas escalares de centros, totales de entrenamiento, puente observado=q por último, JSON y aplicaciones individuales/subconjuntos/permutaciones. El replay bloqueó aprendizaje y Gpor lote. Un valor desconocido mantiene factor bruto1 antes del centro; su precio final puede tener el reescalado fijo.\n\nLos quince ámbitos enlazan treinta componentes y veinte etapas originales por claves/código/datos sin producir centros o precios reales. La mejora predictiva sigue sin probar: requiere registro y evaluación completos con las mismas guardas, luego transferencia si pasa. Cero fuente/CDF/2025/envíos. B00 y alternativas preservadas,2024abierto adaptativo; fuentes/snapshots/valoración/cola/búsqueda siguen limitando la conclusión. Sin revisión profesional independiente.\n\nPróximo: '+next_unit+'\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'synthetic':w.rel(OUT/'synthetic.json'),'synthetic_sha256':w.sha(OUT/'synthetic.json'),'document':w.rel(DOC),'next_unit':next_unit,
        'new_real_fits':0,'new_real_centers':0,'new_real_predictions':0,'new_scores':0,'new_submissions':0,'2024_open':True,'goal_achieved':False,
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P101-CENTROS-RESULTADO','P101: equivalencia secuencial y cotización por fila comprobadas')}
    cut=R/'privado'/('corte_P101_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));cut.mkdir();w.update(INDEX,receipt,cut)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P101'),(R/'registro/semana2_mision_privada_actual.json','P101')]:w.update(path,{key:receipt,'next_unit':next_unit},cut)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P101=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},cut)
    note='\n\n## Privada P101: centrado fijo, preflight\n\nCodex, '+receipt['utc']+'. Equivalencia matemática y cadena alternativa sintética comprobadas; precios por fila/subconjuntos/replay, veinte etapas enlazadas sin aprender centros reales. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,cut)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_fixed_center_preflight_index':w.rel(INDEX),'week_2_private_fixed_center_preflight_report':w.rel(DOC)},cut)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');a=argparse.ArgumentParser(description=__doc__);a.add_argument('mode',choices=['register','run','close'])
    with m.e.threadpool_limits(limits=2):{'register':register,'run':run,'close':close}[a.parse_args().mode]()
