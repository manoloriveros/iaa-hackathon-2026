"""Cambia solo el momento de las bandas NCB/historia; preflight sintético."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import importlib.util
import json
import math
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p79_existing_line_reporting',R/'herramientas/validar_reporte_por_ramo_P65.py')
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
k=p.k;m=p.m;q=p.q;w=p.w;np=p.np;pd=p.pd;BASE=p.BASE
OUT=BASE/'P79_formas_momento_preflight_20261027'
PLAN=R/'registro/semana2_formas_momento_preflight_plan.json';INDEX=R/'registro/semana2_formas_momento_preflight_actual.json'
DOC=R/'docs/semana2/PRIVADA_P79_FORMAS_MOMENTO_PREFLIGHT.md'
ORIGINAL_SHAPE=k.core.b.shape_fit
ORIGINAL_LEARN=k.learn


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)


def shape_fit(frame,mu,which):
    labels=k.core.b.bands(frame,which);business=frame.new_business.to_numpy(dtype=int);y=frame.T0.to_numpy(float)
    assert np.isfinite(y).all() and (y>=0).all() and np.isfinite(mu).all() and (mu>0).all()
    factors={};normalizers={};out=mu.copy()
    for nb in [0,1]:
        cell=business==nb;assert cell.any()
        # Same shape capacity/credibility as P65; only the raw estimating moment changes.
        base=float(np.sum(y[cell]/np.sqrt(mu[cell]))/np.sum(np.sqrt(mu[cell])));assert base>0
        for label in sorted(set(labels[cell])):
            selected=cell&(labels==label);n=int(np.count_nonzero(y[selected]>0));z=n/(n+300)
            own=float(np.sum(y[selected]/np.sqrt(mu[selected]))/np.sum(np.sqrt(mu[selected])))
            raw=own/base;factors[f'{nb}|{label}']=float(1+z*(raw-1))
        g=np.array([factors[f'{nb}|{label}'] for label in labels[cell]])
        norm=float(np.sum(mu[cell]*g)/np.sum(mu[cell]));assert norm>0
        normalizers[str(nb)]=norm;out[cell]*=g/norm
    return {'which':which,'factors':factors,'normalizers':normalizers,'estimator':'relative_withinbusiness_Tweedie15scale_moment'},out


def learn(frame,line):
    artifact=ORIGINAL_LEARN(frame,line)
    artifact['contract']='P79fixed_half_P65_only_history_NCB_Tweedie15moments_K300linearcred'
    assert all(shape['estimator']=='relative_withinbusiness_Tweedie15scale_moment' for component in artifact['components'].values() for shape in component['shape'])
    return artifact


def setup():
    k.core.b.shape_fit=shape_fit;k.learn=learn;k.frame_for=p.frame_for


def independent_shape(frame,mu,which,artifact,out):
    labels=k.core.b.bands(frame,which);y=frame.T0.to_numpy(float);nb=frame.new_business.to_numpy(int)
    derivative_errors=[];zero_bands=0
    expected=mu.copy()
    for business in [0,1]:
        cell=nb==business;indices=np.flatnonzero(cell)
        base=math.fsum(float(y[i])/math.sqrt(float(mu[i])) for i in indices)/math.fsum(math.sqrt(float(mu[i])) for i in indices)
        factors={}
        for label in sorted(set(labels[cell])):
            ids=np.flatnonzero(cell&(labels==label));n=sum(float(y[i])>0 for i in ids)
            moment=math.fsum(float(y[i])/math.sqrt(float(mu[i])) for i in ids)/math.fsum(math.sqrt(float(mu[i])) for i in ids)
            factor=1+n/(n+300)*(moment/base-1);factors[label]=factor
            assert math.isclose(factor,artifact['factors'][f'{business}|{label}'],rel_tol=4e-14,abs_tol=2e-15)
            if n:
                # Raw unshrunk single-band optimum only; no joint optimality claim.
                derivative=math.fsum(math.sqrt(float(mu[i])*moment)-float(y[i])/math.sqrt(float(mu[i])*moment) for i in ids)
                norm=math.fsum(math.sqrt(float(mu[i])*moment) for i in ids)
                assert abs(derivative)<=max(1e-10,4e-14*norm);derivative_errors.append(abs(derivative))
            else:
                assert moment==0 and factor==1;zero_bands+=1
        denominator=math.fsum(float(mu[i]) for i in indices)
        norm=math.fsum(float(mu[i])*factors[labels[i]] for i in indices)/denominator
        assert math.isclose(norm,artifact['normalizers'][str(business)],rel_tol=4e-14)
        for i in indices:expected[i]=float(mu[i])*factors[labels[i]]/norm
        assert math.isclose(math.fsum(float(out[i]) for i in indices),denominator,rel_tol=4e-14)
    assert np.allclose(expected,out,rtol=8e-14,atol=1e-12)
    return {'scalar_factors_and_normalizers_match':True,'raw_unshrunk_logscale_derivative_zero':True,
        'max_absolute_raw_derivative':max(derivative_errors,default=0.),'zero_positive_bands_neutral':zero_bands,'business_base_sum_preserved':True}


def synthetic_frame():
    rng=np.random.default_rng(2026102779);n=840;i=np.arange(n)
    f=pd.DataFrame({'row_id':['syn'+str(j) for j in i],'group_id':['group'+str(j) for j in i],
        'line':'synthetic','is_held':i%5==0,'fold':i%5,'year':2023+(i//5)%2,'new_business':(i//10)%2,
        'T0':rng.gamma(2,100,n)*(rng.random(n)<.35),'reserve':0.,'exposure_calendar':rng.uniform(.1,1,n),
        'q_paired':rng.uniform(.15,1,n),'annual_A1S':np.exp(rng.normal(0,.8,n)),
        'annual_T2b':np.exp(rng.normal(4,.9,n)),'ncb_years':rng.integers(0,15,n),'prior_claims_5y':rng.integers(0,3,n),
        'gender':rng.choice(['F','M'],n),'works_from_home':rng.integers(0,2,n),'marketing_segment':rng.choice(['a','b','c'],n)})
    # Explicit zero-positive band, both businesses; keep rows and exposures.
    f.loc[f.prior_claims_5y.eq(2),'T0']=0.
    f.loc[i%19==0,'ncb_years']=np.nan
    f.loc[i%23==0,'prior_claims_5y']=np.nan
    return f


def poison(frame):
    z=frame.copy();held=z.is_held
    for column in ['T0','reserve','exposure_calendar','q_paired','annual_A1S','annual_T2b','ncb_years','prior_claims_5y']:
        z.loc[held,column]=np.nan
    for column in ['new_business','year','works_from_home']:z.loc[held,column]=-999
    for column in ['gender','marketing_segment']:z.loc[held,column]='__POISON_HELD__'
    return z


def synthetic():
    setup();frame=synthetic_frame();records=[];constant_counts=[]
    train=frame.loc[~frame.is_held].copy();shape_checks=[]
    for name in ['A1S','T2b']:
        z=k.component_frame(train,'annual_'+name);mu=np.exp(z.log_relative_A1S.to_numpy())*z.e_cost_scope.to_numpy()
        for which in ['ncb','prior']:
            artifact,value=shape_fit(z,mu,which)
            shape_checks.append({'source':name,'variable':which,**independent_shape(z,mu,which,artifact,value)})
            mu=value
    old_artifact,old_values=ORIGINAL_SHAPE(z,mu,'prior');new_artifact,new_values=shape_fit(z,mu,'prior')
    assert not np.allclose(old_values,new_values,rtol=1e-8,atol=1e-10)
    for line in q.LINES:
        folder=OUT/'synthetic'/line
        a=m.once(folder,'primary',lambda:learn(frame,line));adverse=m.once(folder,'adverse',lambda:learn(poison(frame),line));assert a==adverse
        held=frame.loc[frame.is_held].copy();held_no_target=held.drop(columns=['T0','reserve']);held_no_target['q_paired']=np.nan
        value,norm=k.forward(held_no_target,a,True)
        replay,nn=k.forward(held_no_target,json.loads(json.dumps(adverse)),True)
        assert np.array_equal(value,replay) and norm==nn
        # Stored production scalar factors, normalizers and source bases, independent order.
        component_math=[]
        for name,obj in a['components'].items():
            z=k.component_frame(train,'annual_'+name);mu=np.exp(z.log_relative_A1S.to_numpy())*z.e_cost_scope.to_numpy()
            for artifact in obj['shape']:
                applied=k.core.b.shape_apply(z,mu,artifact)
                component_math.append(independent_shape(z,mu,artifact['which'],artifact,applied));mu=applied
            scalar=math.fsum((z.T0.to_numpy()/np.sqrt(mu)).tolist())/math.fsum(np.sqrt(mu).tolist())
            assert math.isclose(scalar,obj['level'],rel_tol=3e-13)
        records.append({'line':line,'all_held_payload_poison_before_selector_invariant':True,'serialized_whole_flow_exact':True,
            'ultimate_ignores_held_T0_reserve_q':True,'component_shape_and_level_math':component_math,
            'stage_normalizers_application_scope_preserved':norm})
        constant_counts.append(k.constant_counts(a))
    # Ensure the poison test exercises the selector and prevents parsing bad held fields.
    bad=train.copy();bad.loc[bad.index[0],'T0']=np.nan
    try:learn(bad,'motor')
    except AssertionError:pass
    else:raise AssertionError('Nonfinite TRAINING target must be rejected')
    return {'author':'Codex','utc':utc(),'records':records,'new_shape_scalar_checks':shape_checks,
        'different_from_AE_on_heterogeneous_synthetic_case':True,'invalid_training_target_rejected':True,
        'synthetic_primary_whole_learners':3,'synthetic_adverse_whole_learners_separate':3,
        'synthetic_primary_component_calibrations':6,'synthetic_adverse_component_calibrations_separate':6,
        'synthetic_primary_residual_stages':4,'synthetic_adverse_residual_stages_separate':4,
        'primary_stored_parameter_counts':constant_counts,'new_real_fits':0,'new_CDF_fits':0,'new_scores':0,'new_submissions':0}


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    previous=BASE/'P78_formas_riesgo_20261027';assert w.read(previous/'completion_receipt.json')['report_sha256']==w.sha(previous/'report.json')
    parent=w.read(p.PLAN);m.check_sources(parent)
    paths=[Path(__file__),Path(p.__file__),Path(k.__file__),Path(k.core.__file__),Path(k.core.b.__file__),Path(k.g.__file__),
        p.PLAN,previous/'report.json',previous/'completion_receipt.json',R/'registro/semana2_mision_privada_plan_v1.json']
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'scope':'Only new shape moment and its protected whole-kernel integration, synthetic; zero real learning/prices/scores/source or CDFfits.',
        'need':'P78identified exact rating-form and estimator differences; raw A/Ein P65NCB/prior is the only closed shape step that does not use the current Tweedie15scale moment. No bug or causal attribution established; no field/sign/weight rescue.',
        'hypothesis':'Using relative withinbusiness Tweedie15scale moments in the existing standard bands may improve complete held-group allocation while preserving its credibility and capacity. No future benefit assumed.',
        'one_change':'For each business and shape band, rawrelative = [sum(y/sqrt(mu))/sum(sqrt(mu))]_band / same_moment_business instead of relative aggregateAE. All other operations unchanged.',
        'unchanged':{'bands':'P65existing NCB0/1-2/3-5/6-9/10+/missing and prior0/1/2+/missing, separate business',
            'credibility':'positiveT0periodcount n/(n+300), LINEAR factor1+z*(raw-1); no threshold change',
            'normalization':'Same price-weighted withinbusiness training center; persisted shape normalizers',
            'levels':'Same metric-optimal line level and K400geometric business levels',
            'base_and_residual':'Same A1S/T2bseparately calibrated then fixed arithmetichalf, same already-metric Gresidual stages/nuisances/batch normalizers',
            'inputs':'Exact P64rowFSpPROXYline/perilq/current sources, calendar once, original uncappedT0, same5folds/2023and2024',
            'observation':'Ultimate forward under its normalizers THEN multiply saved ownq; scenario nominalultimateprices fixed'},
        'criterion':'Independent scalar band/business moments, credibility, price-centers and raw unshrunk derivative; neutral zero-positive bands; actual full-kernel held payload poison before selection; exact JSONflow;15real saved bindings only, no real fit.',
        'budget':{'synthetic_primary_whole_learners':3,'synthetic_adverse_whole_learners_separate':3,'new_real_fits':0,'new_source_fits':0,'new_CDF_fits':0,'new_scores':0,'new_resampling':0,'new2025inference':0,'new_submissions':0},
        'future_budget':parent['budget'],'future_criterion':'Separate P80registered whole validation under EVERYunchanged P65global/cohort/scenario/family16/level/influence guard; pooledpass needs OWN2023-only conditionaltransfer before anyCSV. No relaxed thresholds.',
        'limits':parent['limits']+['Raw scalar optimum does not imply shrunk/normalized multi-stage joint optimum or future/private improvement. A/Elegitimately estimates an aggregate mean.'],
        'sources':{**parent['sources'],**{w.rel(path):w.sha(path) for path in paths}},'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. P79registra antes de probar un solo cambio frente aP65: momentoTweedie1,5relativo por banda/negocio en lugar de razónA/E, conservando credibilidad LINEALK300, bandas/normalizadores, nivelK400, mezcla fija50/50yresiduales ya métricos. Preflight sintético3+3aprendices completos, matemática escalar/derivadas, banda sin positivos neutral, veneno de todo payload retenido y replayJSON.15entradas reales solo por unión/SHA; no ajustes ni precios reales, CDF/2025/envíos. No se afirma error deA/E, óptimo conjunto o ganancia privada. Todas las guardas futuras intactas y transferencia propia si pasa. B00/F3cyalternativas conservados,2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P79registered_before_shape_moment_synthetic','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P79-MOMENTO-PREVIO','P79: momento de bandas con credibilidad intacta, preflight antes de ajustar')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def run():
    assert not (OUT/'report.json').exists();plan=w.read(PLAN);m.check_sources(plan);assert w.read(OUT/'registration.json')['plan_sha256']==w.sha(PLAN)
    dump(OUT/'synthetic.json',synthetic());bindings=[]
    for line in q.LINES:
        for outer in range(5):
            frame=p.frame_for(line,outer);assert frame.row_id.is_unique and frame.year.isin([2023,2024]).all()
            assert set(frame.loc[frame.is_held,'group_id']).isdisjoint(set(frame.loc[~frame.is_held,'group_id']))
            bindings.append({'line':line,'outer':outer,'rows':len(frame),'input_sha256':w.sha(p.t.OUT/f'input_{line}_{outer}.parquet'),'same_saved_P64_inputs':True})
    m.check_sources(plan);dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P79shape_moment_whole_synthetic_and_bindings_passed','bindings':bindings,
        'synthetic_report':w.rel(OUT/'synthetic.json'),'synthetic_sha256':w.sha(OUT/'synthetic.json'),**plan['budget']})
    print(json.dumps({'preflight':'passed','bindings':len(bindings),'synthetic_primary_whole_learners':3,'synthetic_adverse_whole_learners_separate':3,'new_real_fits':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();d=w.read(OUT/'report.json');m.check_sources(w.read(PLAN))
    next_unit='P80: register/commit SAMEP65complete fixedhalf model with ONLYP79NCB/prior rawmoment change.15primary/15adverse closedwholelearners, no source/CDF/GLMfits, sameALLpredictive/cohort/scenario/family16/level/influence guards. Pooledpass requires OWN2023-only conditionaltransfer before anyCSV. No band/credibility/weight/line rescue.'
    text='# P79: momento de bandas y flujo protegido\n\nCodex, '+utc()+'. Se sustituyó solo la razón A/Ede cada bandaNCB/historia por el cociente de sus momentos de escalaTweedie1,5dentro del mismo tipo de negocio. Bandas, credibilidad linealK300, centros, K400, fuentes, q, calendario, mezcla50/50yresiduales permanecen iguales.\n\n'
    text+='Pasaron3aprendices completos primarios y3adversos sintéticos:6+6calibraciones y4+4etapas residuales. Factores/centros por sumas escalares, derivada del óptimo crudo de cada banda, conservación de la suma base por negocio y banda sin positivos neutral. Alterar todos los costes, fuentes, atributos, calendario y qretenidos antes del selector no cambió el aprendizaje; el replayJSONdel flujo final fue exacto y no leyó coste/reserva/qen último. Se rechazó un coste de entrenamiento no finito. Las15entradas reales son exactamente las deP64yconservan grupos separados; no se ajustaron.\n\n'
    text+='La derivada valida el momento crudo antes de credibilidad/normalización, no un óptimo conjunto. A/Ees legítimo para otro momento agregado; no se demostró que fuera un error ni que este cambio mejore la privada. Cero ajuste real/CDF/scores/remuestreo/2025/envíos. B00/F3cyalternativas preservados,2024abierto adaptativo, transporte/cola/reservas/maestros/fuente2024condicional persisten; sin revisión independiente.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'synthetic.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'next_unit':next_unit,
        **w.read(PLAN)['budget'],'2024_open':True,'goal_achieved':False,'forum':q.post(body,'COD-S2-20261027-PRIVADA-P79-MOMENTO-RESULTADO','P79: momento de bandas integrado y protegido, sin ajuste real')}
    archive=R/'privado'/('corte_P79_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir();w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P79'),(R/'registro/semana2_mision_privada_actual.json','P79')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    cp=R/'registro/semana2_contadores_propios_actual.json';w.update(cp,{'phase2_private_P79_shape_moment_preflight':{**receipt,'synthetic':w.read(OUT/'synthetic.json')}},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P79=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P79: momento de bandas, preflight\n\nCodex, '+receipt['utc']+'.Flujo completo sintético protegido y15enlaces sin ajustes reales pasaron. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_shape_moment_preflight_index':w.rel(INDEX),'week_2_private_shape_moment_preflight_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'new_real_fits':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['register','run','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'register':register,'run':run,'close':close}[args.mode]()
