"""Evaluacion completa del Poisson de numero y del nivel de coste P109."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import json
import math
import os
import sys
from types import SimpleNamespace

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
sys.path.insert(0,str(R/'herramientas'))
import preparar_Poisson_destino_P109 as k
loader=k.p108.load
m=loader('p110_existing_cost_guards',R/'herramientas/validar_A1R_destino_P52.py')
w=k.w;pd=k.pd;np=k.np;q=k.q;BASE=k.BASE
OUT=BASE/'P110_validacion_Poisson_destino_20261027'
PLAN=R/'registro/semana2_Poisson_destino_validacion_plan.json'
INDEX=R/'registro/semana2_Poisson_destino_validacion_actual.json'
DOC=R/'docs/semana2/PRIVADA_P110_VALIDACION_POISSON_DESTINO.md'
P65=BASE/'P65_validacion_reporte_por_ramo_20261027'
ORIGINAL_FIT=k.PoissonRegressor.fit
ORIGINAL_COST_LEVEL=k.cost_level
ACTIVE=None
PROFILES={}
dump=k.dump;utc=k.utc


def frame_for(line,outer):return pd.read_parquet(k.OUT/f'input_{line}_{outer}.parquet')


def cost_q(frame,line,outer,branch='NOMINAL',tail=0.):
    if line not in PROFILES:
        PROFILES[line]=pd.read_parquet(k.p108.OUT/f'paired_source_{line}.parquet').set_index('row_id')
    source=PROFILES[line].loc[frame.row_id]
    assert np.array_equal(source.year,frame.year)
    curves=w.read(k.P64/f'{branch}_outer{outer}'/line/'primary_curves.json')
    numerator=np.zeros(len(frame));denominator=np.zeros(len(frame))
    for peril in q.PERILS[line]:
        annual=source['frequency_'+peril].to_numpy(float)*source['mark_'+peril].to_numpy(float)
        en=q.effective(frame,curves['curves'][peril])
        numerator+=annual*en*(1-tail*(peril in ['bodily_injury','subsidence']))
        denominator+=annual
    result=numerator/(denominator*frame.exposure_calendar.to_numpy(float))
    assert np.isfinite(result).all() and (result>0).all() and (result<=1+1e-12).all()
    return result


def state(status,session=None):
    index=w.read(INDEX);previous=index.get('execution') or {}
    native=sorted(w.rel(path) for path in OUT.glob('*_*/*_fit_invoked.json'))
    primary_levels=sorted(w.rel(path) for path in OUT.glob('*_*/primary_cost_level*_invoked.json'))
    adverse_levels=sorted(w.rel(path) for path in OUT.glob('*_*/adverse_cost_level*_invoked.json'))
    for name,keys in [('primary',primary_levels),('adverse',adverse_levels)]:
        for path in OUT.glob('*_*/'+name+'_model_raw.json'):
            if 'null_count_level' in w.read(path):keys.append(w.rel(path)+'#null_count_level')
    primary_levels.sort();adverse_levels.sort()
    counter_path=R/'registro/semana2_contadores_propios_actual.json';counter=w.read(counter_path)
    prior=counter.get('phase2_private_P110_count_execution',{})
    oldnative=prior.get('counted_native_keys',[]);oldlevels=prior.get('counted_primary_closed_keys',[])
    assert set(oldnative).issubset(native) and set(oldlevels).issubset(primary_levels)
    delta_native=len(set(native)-set(oldnative));delta_levels=len(set(primary_levels)-set(oldlevels))
    execution=None
    if status=='RUNNING':
        started=w.read(OUT/'started.json')
        execution={'pid':started['pid'],'started_utc':started['utc'],'script':w.rel(Path(__file__)),
            'kind':'P110staged_count_Poisson','exec_session_id':session if session is not None else previous.get('exec_session_id')}
    record={'author':'Codex','utc':utc(),'state':status,'execution':execution,'native_fit_attempts':len(native),
        'primary_native_attempts':sum('/primary_' in key for key in native),
        'adverse_native_attempts_separate':sum('/adverse_' in key for key in native),
        'primary_closed_parameter_invocations':len(primary_levels),'adverse_closed_invocations_separate':len(adverse_levels),
        'committed_members':len(list(OUT.glob('*_*/committed.json'))),'output':w.rel(OUT)}
    archive=R/'privado'/('p110_state_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir()
    w.update(counter_path,{'cumulative_price_base_fits':counter['cumulative_price_base_fits']+delta_native,
        'cumulative_closed_form_constants':counter['cumulative_closed_form_constants']+delta_levels,
        'phase2_private_P110_count_execution':{'counted_native_keys':native,'counted_primary_closed_keys':primary_levels,
            'adverse_closed_keys_separate':adverse_levels,'record':record}},archive)
    w.update(INDEX,{'execution':execution,'execution_record':record},archive)
    phase_path=R/'registro/semana2_mision017_fase2_actual.json';phase=w.read(phase_path)
    values={'P110_execution':record,'active_execution':execution,'active_jobs':[] if execution is None else [execution]}
    if 'new_price_fits' in phase:values['new_price_fits']=phase['new_price_fits']+delta_native
    w.update(phase_path,values,archive)
    path=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(path)['week_2_mission017_phase2_20261025']
    own.update(P110_execution=record,active_execution=execution,active_jobs=[] if execution is None else [execution])
    w.update(path,{'week_2_mission017_phase2_20261025':own},archive)
    return record


def observed_fit(self,*args,**kwargs):
    assert ACTIVE is not None
    path=ACTIVE['folder']/(ACTIVE['name']+'_fit_invoked.json')
    dump(path,{'author':'Codex','utc':utc(),'actual_Poisson_fit_invoked':True,
        'nominal_alpha':k.ALPHA,'adjusted_alpha':self.alpha,'rows':len(args[1]),'pid':os.getpid()})
    return ORIGINAL_FIT(self,*args,**kwargs)


def observed_level(y,base):
    assert ACTIVE is not None
    number=ACTIVE['level_calls'];assert number<2;ACTIVE['level_calls']+=1
    path=ACTIVE['folder']/(ACTIVE['name']+f'_cost_level{number}_invoked.json')
    dump(path,{'author':'Codex','utc':utc(),'kind':'Poisson_shape_cost_level' if number==0 else 'matched_null_cost_level',
        'rows':len(y),'y_sha256':k.p108.m.array_digest(np.asarray(y,dtype=float)),
        'base_sha256':k.p108.m.array_digest(np.asarray(base,dtype=float))})
    return ORIGINAL_COST_LEVEL(y,base)


def learn(frame,line,outer,name):
    global ACTIVE
    folder=OUT/f'{line}_{outer}';ACTIVE={'folder':folder,'name':name,'level_calls':0}
    value=k.fit(frame,line,folder/(name+'_model_raw.json'))
    assert ACTIVE['level_calls']==2;ACTIVE=None
    return value


def independent_math(train,artifact):
    eligible=train.count_offset.to_numpy(float)>0
    x,_=k.design(train.loc[eligible],artifact['line'],artifact['preprocess'])
    beta=np.asarray(artifact['coef']);a=np.exp(x@beta+artifact['intercept'])
    n=train.loc[eligible,'n_accepted'].to_numpy(float);base=train.loc[eligible,'count_offset'].to_numpy(float)
    score=base*(a-n/base)/base.sum();alpha=artifact['parameters']['adjusted_alpha']
    gradient=np.r_[score.sum(),x.T@score+alpha*beta]
    assert math.isclose(float(np.max(np.abs(gradient))),artifact['gradient_inf'],rel_tol=2e-8,abs_tol=2e-13)
    whole,_=k.design(train,artifact['line'],artifact['preprocess']);relative=np.exp(whole@beta+artifact['intercept'])
    source=train.annual_paired_cost.to_numpy(float);e=train.exposure_calendar.to_numpy(float)*train.q_paired.to_numpy(float)
    y=train.T0.to_numpy(float)
    for name,factor in [('cost_level',relative),('null_cost_level',np.ones(len(train)))]:
        mu=source*factor*e
        scalar=math.fsum((y/np.sqrt(mu)).tolist())/math.fsum(np.sqrt(mu).tolist())
        assert math.isclose(scalar,artifact[name],rel_tol=3e-13)
    assert math.isclose(math.fsum(train.n_accepted.to_numpy(float).tolist())/math.fsum(train.count_offset.to_numpy(float).tolist()),artifact['null_count_level'],rel_tol=3e-13)
    return {'gradient_and_three_levels_scalar_match':True,'gradient_inf':artifact['gradient_inf'],
        'limit':'Conditional stationarity and staged levels, not a joint Poisson/Tweedie likelihood optimum.'}


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent=w.read(k.PLAN);m.check_sources(parent)
    assert w.read(k.OUT/'completion_receipt.json')['report_sha256']==w.sha(k.OUT/'report.json')
    pre=w.read(k.OUT/'report.json');assert pre['new_real_Poisson_fits']==0 and len(pre['records'])==15
    assert all(w.sha(ROOT/path)==sha for path,sha in pre['outputs'].items())
    OUT.mkdir();records=[];outputs={}
    source_paths=[Path(__file__),Path(k.__file__),Path(m.__file__),Path(m.e.__file__),k.PLAN,k.INDEX,
        k.OUT/'report.json',k.OUT/'synthetic.json',k.OUT/'completion_receipt.json',
        m.REF,P65/'report.json',BASE/'P19_cohortes_broker_20261026/covariates.parquet',
        BASE/'P19_cohortes_broker_20261026/group_universe.json',BASE/'P19_cohortes_broker_20261026/first4_group_weights.npy',
        BASE/'estimando_cartera2025_v3/weights.parquet']
    curve_report=w.read(k.P64/'report.json')
    for line in q.LINES:
        source_paths += [m.P1/f'canonical_{line}.parquet']
        for outer in range(5):
            f=frame_for(line,outer)
            nominal=cost_q(f,line,outer)
            assert np.array_equal(nominal,f.q_paired.to_numpy())
            for branch in ['NOMINAL','RESERVE075','RESERVE125']:
                path=k.P64/f'{branch}_outer{outer}'/line/'primary_curves.json'
                assert curve_report['outputs'][w.rel(path)]==w.sha(path);source_paths.append(path)
            for name,branch,tail in [('RESERVE075','RESERVE075',0.),('RESERVE125','RESERVE125',0.),
                ('TAIL005','NOMINAL',.05),('TAIL010','NOMINAL',.1)]:
                z=f[['row_id']].copy();z['q']=cost_q(f,line,outer,branch,tail)
                path=OUT/'scenario_inputs'/f'{name}_{line}_{outer}_q.parquet'
                path.parent.mkdir(exist_ok=True);z.to_parquet(path,index=False);outputs[w.rel(path)]=w.sha(path)
            records.append({'line':line,'outer':outer,'actual_nominal_adapter_bitexact_to_P109':True})
    dump(OUT/'scenario_bindings.json',{'author':'Codex','utc':utc(),'records':records,'outputs':outputs,'new_CDF_fits':0})
    sources={**parent['sources'],**pre['outputs'],**outputs,**{w.rel(path):w.sha(path) for path in source_paths}}
    plan={'author':'Codex','utc':utc(),'candidate':'P109standard_count_Poisson_then_own_train_T0level',
        'need':parent['need'],'hypothesis':parent['hypothesis'],'configuration':parent['configuration'],
        **{name:parent[name] for name in ['criteria','bootstrap','cohort_guard','level_sensitivity','future_validation']},
        'budget':parent['future_budget'],'primary_comparator':'Same reproducible original A1S/S2/H1historical algorithm and109296rows as prior evaluations. This is not an exact replay of delivered F3c. F3c remains the preserved live submission.',
        'secondary_comparators':'Matched null uses identical paired-source S/cost q and own train cost level but no count shape. Evaluate both cost and accepted-count losses. P65secondary point contrast only; no line/feature/alpha selection.',
        'scenario_integration':'All15nominal paired-source adapters bitexact to P109.60new qvectors from unchanged own P64reserve/tail curves and nominal lambda*mark weights. Tail mass only BI/subsidence. Final price model nominal fixed; no scenario refit.',
        'adverse':'Actual15second Poisson fits after ALLheld labels/counts/source/rating/exposure/qpayload poisoned before train selection. Stored coefficient and final level snapshots; all staged models must match.',
        'counts':'Actual estimator fit marker before every Poisson invocation; two cost-level markers before their computations, null count constant reconciled from saved full raw model. Native cumulative includes primary/adverse; closed cumulative counts primary, adverse separate as existing convention.',
        'matched_inference':'Secondary cost contrast uses the SAME2000primary group-draw multiplicities/seed and denominator, no separate tuning. Its bands are exploratory and not private-score forecasts.',
        'staged_decision':'Every original global/cell/cohort/level/influence/convergence guard unchanged. Pooledfailure forbids admission; pooledpass requires OWN2023-only conditionaltransfer with own cost reporting before CSV. No public score-driven rescue.',
        'sources':sources,'limits':parent['limits']+['Fixed-source and fixed-CDF bootstrap does not include complete fitting/selection uncertainty. Both target years are adaptive; no clean private labels exist.'],
        'B00_all_alternatives_preserved':True,'2024_open':True,'goal_achieved':False}
    dump(PLAN,plan)
    body=OUT/'forum_previo.md';body.write_text('Codex. P110 registra la evaluación real completa de la receta P109: 15 Poisson primarios y 15 adversos, 45 constantes primarias y 45 adversas separadas. Recuentos aceptados y exposición de número dirigen la forma; T0 conserva el objetivo de coste y su nivel propio. Comparador principal S2/H1 histórico reproducible, sin afirmar réplica exacta de F3c; null emparejado y P65 secundarios. Los 15 adaptadores nominales coinciden exactamente y los 60 vectores de estrés usan pesos fuente pareados, no los FSp antiguos. Se conservan todas las guardas, el control de influencia y los escenarios con precios nominales fijos. Cero fuente/CDF nuevos, 2025 o envíos. La transferencia propia sigue obligatoria antes de admitir. Las llamadas nativas y niveles se contarán por sus marcadores reales; no se repetirá un intento sin conciliar. B00 y adversos preservados, prioridad privada y 2024 adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':'P110registered_before_real_count_and_cost_learning',
        'plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),'execution':None,
        'forum':k.p108.p107.previous.post(body,'COD-S2-20261027-PRIVADA-P110-POISSON-PREVIO','P110: Poisson de número y nivel de coste, evaluación real preinscrita')}
    dump(OUT/'registration.json',receipt);dump(INDEX,receipt);print(json.dumps(receipt))


def matched_summary(f,data,plan):
    codes,groups=pd.factorize(f.group_id,sort=True);count=np.bincount(codes,minlength=len(groups))
    records=[];gains=[];totals=[];roots=[]
    for j,name in enumerate(m.e.NAMES):
        y,_,candidate=data[j]
        null=f.null_new_nominal.to_numpy() if name=='NOMINAL' else f[name+'_null'].to_numpy()
        gain=m.e.unit(y,null)-m.e.unit(y,candidate)
        denominator=m.e.unit(y,np.full(len(y),y.mean())).sum()
        grouped=np.bincount(codes,weights=gain,minlength=len(groups))
        gains.append(grouped);totals.append(np.bincount(codes,weights=y,minlength=len(groups)))
        roots.append(np.bincount(codes,weights=np.sqrt(y),minlength=len(groups)))
        cells=[]
        for (line,year,business),indices in f.groupby(['line','year','new_business']).groups.items():
            ii=np.asarray(list(indices));yy=y[ii]
            den=m.e.unit(yy,np.full(len(ii),yy.mean())).sum()
            cells.append({'line':line,'year':int(year),'NB':int(business),'delta':float(gain[ii].sum()/den)})
        records.append({'scenario':name,'delta_vs_matched_null':float(gain.sum()/denominator),
            'post31_delta':float((grouped.sum()-np.sort(grouped)[::-1][:31].sum())/denominator),
            'cells':cells,'worst_cell_delta':min(record['delta'] for record in cells),
            'folds':{str(fold):float(gain[f.fold.eq(fold)].sum()/denominator) for fold in range(5)}})
    gains=np.column_stack(gains);totals=np.column_stack(totals);roots=np.column_stack(roots)
    rng=np.random.default_rng(plan['bootstrap']['pooled_seed']);draws=[]
    # Exactly the primary group multiplicities and denominator, now applied to
    # a different saved gain statistic. No extra random search or fitted model.
    for _ in range(plan['bootstrap']['replicates']):
        ii=rng.integers(0,len(groups),len(groups))
        den=8*(np.sqrt(count[ii].sum()*totals[ii].sum(axis=0))-roots[ii].sum(axis=0))
        assert (den>0).all();draws.append(gains[ii].sum(axis=0)/den)
    draws=np.asarray(draws);np.save(OUT/'matched_null_joint_bootstrap.npy',draws)
    for j,record in enumerate(records):record['bootstrap95']=np.quantile(draws[:,j],[.025,.975]).tolist()
    count_records=[]
    from sklearn.metrics import mean_poisson_deviance
    for (line,year,business),indices in f.groupby(['line','year','new_business']).groups.items():
        g=f.loc[indices];n=g.n_accepted.to_numpy(float);mu=g.count_prediction.to_numpy(float);null=g.null_count_prediction.to_numpy(float)
        count_records.append({'line':line,'year':int(year),'NB':int(business),'rows':len(g),'accepted_events':int(n.sum()),
            'Poisson_deviance_candidate':float(mean_poisson_deviance(n,mu)),
            'Poisson_deviance_null':float(mean_poisson_deviance(n,null)),
            'AE_count_candidate':float(n.sum()/mu.sum()),'AE_count_null':float(n.sum()/null.sum())})
    result={'author':'Codex','utc':utc(),'cost_comparisons':records,'count_comparisons':count_records,
        'same_primary2000group_multiplicities':True,'secondary_only_no_admission_or_private_claim':True}
    dump(OUT/'matched_null_report.json',result);return result


def run():
    assert not (OUT/'report.json').exists()
    plan=w.read(PLAN);m.check_sources(plan)
    assert w.read(OUT/'registration.json')['plan_sha256']==w.sha(PLAN)
    if not (OUT/'started.json').exists():dump(OUT/'started.json',{'author':'Codex','utc':utc(),'pid':os.getpid(),'plan_sha256':w.sha(PLAN)})
    m.OUT=OUT;m.e.OUT=OUT;k.PoissonRegressor.fit=observed_fit;k.cost_level=observed_level
    state('RUNNING');parts=[]
    try:
        for outer in range(5):
            for line in q.LINES:
                folder=OUT/f'{line}_{outer}';folder.mkdir(exist_ok=True)
                if (folder/'committed.json').exists():
                    committed=w.read(folder/'committed.json')
                    assert all(w.sha(ROOT/path)==sha for path,sha in committed['outputs'].items())
                    parts.append(pd.read_parquet(folder/'prices.parquet'));continue
                f=frame_for(line,outer)
                a=m.once(folder,'learning',lambda:learn(f,line,outer,'primary'))
                adverse=m.once(folder,'adverse_learning',lambda:learn(k.poison(f,line),line,outer,'adverse'))
                assert a==adverse
                held=f.loc[f.is_held].copy();u,null,relative=k.forward(held,a)
                clean=held.drop(columns=['T0','reserve','q_paired','count_offset','n_accepted'])
                check=k.forward(clean,json.loads(json.dumps(adverse)))
                assert all(np.array_equal(x,y) for x,y in zip((u,null,relative),check))
                math_checks=independent_math(f.loc[~f.is_held],a)
                assert np.array_equal(cost_q(held,line,outer),held.q_paired.to_numpy())
                out=held[['row_id','line','year','new_business','fold','group_id','T0','n_accepted']].copy()
                out['ultimate']=u;out['null_ultimate']=null
                out['new_nominal']=u*held.q_paired.to_numpy();out['null_new_nominal']=null*held.q_paired.to_numpy()
                out['count_prediction']=held.count_offset.to_numpy(float)*relative
                out['null_count_prediction']=held.count_offset.to_numpy(float)*a['null_count_level']
                for name in m.e.NAMES[1:]:
                    link=pd.read_parquet(OUT/'scenario_inputs'/f'{name}_{line}_{outer}_q.parquet').set_index('row_id').loc[held.row_id,'q'].to_numpy()
                    out[name+'_new']=u*link;out[name+'_null']=null*link
                out.to_parquet(folder/'prices.parquet',index=False);parts.append(out)
                dump(folder/'committed.json',{'line':line,'outer':outer,'whole_primary_adverse_models_exact':True,
                    'ultimate_quote_without_labels_count_offset_or_q':True,'independent_checks':math_checks,
                    'outputs':{w.rel(path):w.sha(path) for path in folder.iterdir() if path.is_file()}})
                state('RUNNING')
                print(json.dumps({'member_completed':line+'_'+str(outer),'members':len(parts)}),flush=True)
        ref=pd.read_parquet(m.REF);f=pd.concat(parts)
        assert f.row_id.is_unique and set(f.row_id)==set(ref.row_id)
        f=f.set_index('row_id',drop=False).loc[ref.row_id].reset_index(drop=True)
        for name in ['row_id','line','year','new_business','fold','group_id','T0']:assert np.array_equal(f[name],ref[name])
        f['old_nominal']=ref.old_nominal.to_numpy()
        reserve=pd.concat([pd.read_parquet(m.P1/f'canonical_{line}.parquet',columns=['row_id','reserve']) for line in q.LINES]).set_index('row_id').loc[f.row_id,'reserve'].to_numpy()
        y=f.T0.to_numpy(float);ys=[y,y-.25*reserve,y+.25*reserve,y,y]
        data=[(y,f.old_nominal.to_numpy(),f.new_nominal.to_numpy())]
        for j,name in enumerate(m.e.NAMES[1:],1):
            f[name+'_old']=ref[name+'_old'].to_numpy();data.append((ys[j],f[name+'_old'].to_numpy(),f[name+'_new'].to_numpy()))
        f.to_parquet(OUT/'POOLED_prices.parquet',index=False)
        weight=pd.read_parquet(BASE/'estimando_cartera2025_v3/weights.parquet').set_index('row_id').loc[f.row_id]
        assert np.array_equal(weight.group_id,f.group_id)
        metrics=m.e.metrics(f,data,'POOLED',weight.weight.to_numpy(float),plan)
        cohorts=m.cohort_analysis();matched=matched_summary(f,data,plan)
        a=metrics['NOMINAL'];criteria=plan['criteria']
        models=[w.read(path) for path in OUT.glob('*_*/learning.json')];assert len(models)==15
        gates={'pooled_delta_ge002':a['delta']>=criteria['nominal_pooled_delta_min'],
            'pooled_lower95_positive':a['bootstrap95'][0]>0,
            'pooled_atleast4positive_folds':sum(value>0 for value in a['folds'].values())>=4,
            'both_pooled_years_nonnegative':min(a['years'].values())>=0,'pooled_post31_nonnegative':a['post31_delta']>=0,
            'all_nominal_and_stress_cell_floors':all(value['worst_cell_delta']>=-.001 for value in metrics.values()),
            'all_Poisson_convergence_pass':all(not model['warnings'] and model['gradient_inf']<1e-5 for model in models)}
        passed=all(gates.values()) and all(cohorts['gates'].values())
        prior=w.read(P65/'report.json')['results']['POOLED']['NOMINAL']['delta']
        m.check_sources(plan)
        report={'author':'Codex','utc':utc(),'status':'P110staged_Poisson_cost_level_pooled_complete_transfer_unmeasured',
            'plan_sha256':w.sha(PLAN),'results':{'POOLED':metrics,'TRANSFER':None},'pooled_gates':gates,
            'pooled_cohort_gates':cohorts['gates'],'all_pooled_gates_pass':passed,'conditional_transfer_gate':None,
            'all_required_gates_pass':False,'decision':'TRANSFER_REQUIRED_BEFORE_ADMISSION' if passed else 'REJECT_FROM_POOLED_FAILURE_TRANSFER_UNEVALUATED',
            'matched_nominal':matched['cost_comparisons'][0],'P110_minus_P65_point_only':a['delta']-prior,
            'primary_Poisson_fits':15,'adverse_Poisson_fits_separate':15,'primary_closed_levels':45,'adverse_closed_levels_separate':45,
            'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0,
            'primary_comparator_not_exact_F3c':True,'adopted':False,'2024_open':True,'goal_achieved':False}
        dump(OUT/'report.json',report);state('TERMINAL_SUCCESS')
        print(json.dumps({'decision':report['decision'],'nominal':{name:a[name] for name in ['delta','bootstrap95','post31_delta','worst_cell_delta']},
            'matched_null_delta':report['matched_nominal']['delta_vs_matched_null'],'gates':gates,'cohort_gates':cohorts['gates']}),flush=True)
    except Exception as error:
        if not (OUT/'failure.json').exists():dump(OUT/'failure.json',{'author':'Codex','utc':utc(),'type':type(error).__name__,'message':str(error)})
        state('TERMINAL_FAILURE_RECONCILE_NO_BLIND_RESTART');raise


def replay():
    assert not (OUT/'replay_report.json').exists();plan=w.read(PLAN);m.check_sources(plan)
    report=w.read(OUT/'report.json');m.OUT=OUT;m.e.OUT=OUT
    def reject(*args,**kwargs):raise AssertionError('P110replay forbids ALL learning, source and CDF fitting')
    k.fit=reject;k.cost_level=reject;k.PoissonRegressor.fit=reject;q.cost_curves=reject
    original_design=k.design
    def frozen_design(frame,line,prep=None):
        assert prep is not None,'Training preprocessing prohibited during replay'
        return original_design(frame,line,prep)
    k.design=frozen_design
    for outer in range(5):
        for line in q.LINES:
            folder=OUT/f'{line}_{outer}';committed=w.read(folder/'committed.json')
            assert all(w.sha(ROOT/path)==sha for path,sha in committed['outputs'].items())
            frame=frame_for(line,outer);held=frame.loc[frame.is_held].drop(columns=['T0','reserve','q_paired','count_offset','n_accepted'])
            value,null,relative=k.forward(held,w.read(folder/'learning.json'))
            expected=pd.read_parquet(folder/'prices.parquet')
            assert np.array_equal(value,expected.ultimate) and np.array_equal(null,expected.null_ultimate)
            assert np.array_equal(cost_q(frame,line,outer),frame.q_paired.to_numpy())
            for name,branch,tail in [('RESERVE075','RESERVE075',0.),('RESERVE125','RESERVE125',0.),('TAIL005','NOMINAL',.05),('TAIL010','NOMINAL',.1)]:
                expected_link=pd.read_parquet(OUT/'scenario_inputs'/f'{name}_{line}_{outer}_q.parquet')
                assert np.array_equal(cost_q(frame,line,outer,branch,tail),expected_link.q.to_numpy())
    totals,desc,_,_=m.cohort_blocks();weights=np.load(BASE/'P19_cohortes_broker_20261026/first4_group_weights.npy')
    draws=np.load(OUT/'cohort_bootstrap.npy');cohort=w.read(OUT/'cohort_report.json')
    assert np.allclose(m.cohort_scores(weights@totals),draws[:4],rtol=2e-12,atol=2e-13)
    for j,record in enumerate(cohort['comparisons']):
        assert desc[j]['delta']==record['delta'] and np.array_equal(np.quantile(draws[:,j],[.025/16,1-.025/16]),record['family16_band95'])
    draws=np.load(OUT/'POOLED_joint_bootstrap.npy');matched=np.load(OUT/'matched_null_joint_bootstrap.npy');mr=w.read(OUT/'matched_null_report.json')
    for j,name in enumerate(m.e.NAMES):
        assert np.array_equal(np.quantile(draws[:,j],[.025,.975]),report['results']['POOLED'][name]['bootstrap95'])
        assert np.array_equal(np.quantile(matched[:,j],[.025,.975]),mr['cost_comparisons'][j]['bootstrap95'])
    m.check_sources(plan)
    dump(OUT/'replay_report.json',{'author':'Codex','utc':utc(),'report_sha256':w.sha(OUT/'report.json'),
        'all15whole_staged_flows_exact':True,'all15nominal60scenario_links_exact':True,
        'cost_count_GLM_and_preprocessing_learning_blocked':True,'ultimate_quote_labels_and_q_absent':True,
        'saved_intervals_and_first4cohort_weights_replayed':True,'new_fits':0,'new_resampling':0,'new_submissions':0})
    print(json.dumps({'replay':'exact','members':15,'new_fits':0,'new_resampling':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();plan=w.read(PLAN);m.check_sources(plan)
    report=w.read(OUT/'report.json');assert w.read(OUT/'replay_report.json')['report_sha256']==w.sha(OUT/'report.json')
    attempts=state('TERMINAL_SUCCESS')
    assert attempts['primary_native_attempts']==attempts['adverse_native_attempts_separate']==15
    assert attempts['primary_closed_parameter_invocations']==attempts['adverse_closed_invocations_separate']==45
    a=report['results']['POOLED']['NOMINAL'];matched=report['matched_nominal'];passed=report['all_pooled_gates_pass']
    next_unit=('Register OWN2023-only conditionaltransfer of exact P109algorithm and matched null with own2023cost reporting before production. Fixed source count/reporting assumptions remain conditional, no source refit or CSV from pooled alone.' if passed else
        'Review ONLY new saved P110cost/count matched-null loss, coefficients and group/cell influence without fits/resampling. Separate whether observed-count correction transfers but frozen source marks/level fail. Preserve all raw outputs; no alpha/line/feature/weight rescue. Identify a new evidence-backed mechanism before another recipe; no new CSVadmitted.')
    text='# P110: evaluación del Poisson de frecuencia y nivel de coste\n\nCodex, '+utc()+'. '+('El combinado pasa las guardas; falta transferencia propia antes de admitir.' if passed else 'El combinado falla las guardas; no se admite un CSV y la transferencia permanece sin evaluar.')+'\n\n'
    text+=f"Frente al algoritmo histórico S2/H1: delta D2={a['delta']:+.7f}; IC95 por grupos=[{a['bootstrap95'][0]:+.7f}, {a['bootstrap95'][1]:+.7f}]; Post31={a['post31_delta']:+.7f}; peor celda={a['worst_cell_delta']:+.7f}. No es una réplica histórica exacta del CSV F3c enviado.\n\n"
    text+=f"Frente al null emparejado sin corrección de forma: delta={matched['delta_vs_matched_null']:+.7f}; IC95=[{matched['bootstrap95'][0]:+.7f}, {matched['bootstrap95'][1]:+.7f}]. Ambos conservan fuente, mezcla por peril, exposición y nivel de coste propio. La comparación de recuentos por celdas está en matched_null_report.json. Son contrastes exploratorios, sin forecast de score privado.\n\n"
    text+='Quince Poisson primarios y quince adversos reales, con 45 constantes primarias y 45 adversas separadas. La forma aprende de recuentos aceptados con exposición de número; el nivel conserva T0 como objetivo final de coste. Todos los modelos completos coincidieron después de alterar el contenido retenido antes de seleccionar entrenamiento. Los quince replays reprodujeron precios con aprendizaje de Poisson, niveles, preprocesamiento y CDF bloqueado; también coincidieron los 75 enlaces nominales y de estrés. La suma por otro método comprobó gradiente y los tres niveles de cada ámbito.\n\n'
    text+='Guardas globales: '+json.dumps(report['pooled_gates'])+'. Cohortes: '+json.dumps(report['pooled_cohort_gates'])+'. Los escenarios mantienen los modelos nominales fijos, sin refits por escenario. No se repitió fuente o CDF y no hubo inferencias de 2025 o envíos.\n\n'
    text+='La fuente, las curvas, las reservas a valoración y la cola siguen siendo supuestos; ambos años destino son desarrollo adaptativo. La validación condicional no incluye toda la incertidumbre de ajuste/selección ni prueba generalización privada. B00, F3c y todas las alternativas se conservan, sin revisión profesional independiente.\n\nPróximo: '+next_unit+'\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':report['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),
        'document':w.rel(DOC),'decision':report['decision'],'nominal':{name:a[name] for name in ['delta','bootstrap95','post31_delta','worst_cell_delta']},
        'matched_nominal':matched,'all_pooled_gates_pass':passed,'conditional_transfer_gate':None,
        'primary_Poisson_fits':15,'adverse_Poisson_fits_separate':15,'primary_closed_levels':45,'adverse_closed_levels_separate':45,
        'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0,'next_unit':next_unit,'2024_open':True,'goal_achieved':False,
        'forum':k.p108.p107.previous.post(body,'COD-S2-20261027-PRIVADA-P110-POISSON-RESULTADO','P110: resultado completo de frecuencia y coste, guardas privadas')}
    archive=R/'privado'/('corte_P110_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir()
    w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P110'),(R/'registro/semana2_mision_privada_actual.json','P110')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    path=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(path)['week_2_mission017_phase2_20261025'];own.update(private_P110=receipt,next_unit=next_unit)
    w.update(path,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P110: Poisson de número y nivel de coste\n\nCodex, '+receipt['utc']+'. '+receipt['decision']+'. Quince Poisson primarios/15 adversos y45+45 niveles, intentos conciliados y replay exacto. Sin fuente/CDF/2025/envíos. Informe '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_target_Poisson_validation_index':w.rel(INDEX),'week_2_private_target_Poisson_validation_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'decision':report['decision'],'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['prepare','run','replay','close','state']);parser.add_argument('--session',type=int)
    args=parser.parse_args()
    with k.threadpool_limits(limits=2):
        if args.mode=='state':print(json.dumps(state('RUNNING',args.session)))
        else:{'prepare':prepare,'run':run,'replay':replay,'close':close}[args.mode]()
