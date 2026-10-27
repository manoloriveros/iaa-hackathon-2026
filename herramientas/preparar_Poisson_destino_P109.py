"""Contrato, flujo sintetico y entradas pareadas para un Poisson destino estandar."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import math
import sys
import warnings

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
sys.path.insert(0,str(R/'herramientas'))
import exportar_pares_fuente_P108 as p108
k=p108.load('p109_existing_rating_bands',R/'herramientas/preparar_GLM_bandas_negocio_P81.py')
q=k.q;w=k.w;pd=k.pd;np=k.np;BASE=k.BASE
from sklearn.linear_model import PoissonRegressor
from sklearn.metrics import mean_poisson_deviance
from sklearn.exceptions import ConvergenceWarning
from scipy.special import xlogy
from threadpoolctl import threadpool_limits
OUT=BASE/'P109_Poisson_destino_preflight_20261027'
PLAN=R/'registro/semana2_Poisson_destino_preflight_plan.json'
INDEX=R/'registro/semana2_Poisson_destino_preflight_actual.json'
DOC=R/'docs/semana2/PRIVADA_P109_POISSON_DESTINO_PREFLIGHT.md'
P64=BASE/'P64_reporte_por_ramo_preflight_20261027'
PARAMS={'fit_intercept':True,'solver':'lbfgs','max_iter':3000,'tol':1e-7,'warm_start':False}
ALPHA=.001
dump=p108.dump;utc=p108.utc


def digest(values):return hashlib.sha256('\n'.join(sorted(map(str,values))).encode()).hexdigest()


def design(frame,line,prep=None):
    # Same previously used raw rating fields/bands, without source cost-rate
    # covariates. Source frequency is an offset, not an estimated feature slope.
    f=k.rating_frame(frame,line);parts=[]
    for name in k.NUM[line]:
        z=pd.to_numeric(f[name],errors='coerce').to_numpy(float)
        parts.append(np.log1p(np.where(np.isfinite(z)&(z>=0),z,np.nan)))
    raw=np.column_stack(parts);missing=~np.isfinite(raw)
    if prep is None:
        med=np.array([np.median(raw[~missing[:,j],j]) if (~missing[:,j]).any() else 0. for j in range(raw.shape[1])])
        filled=np.where(missing,med,raw);scale=filled.std(axis=0);scale=np.where(scale>0,scale,1.)
        prep={'numeric':k.NUM[line],'categorical':k.CAT[line],'median':med.tolist(),'mean':filled.mean(axis=0).tolist(),
            'scale':scale.tolist(),'levels':{name:sorted(f[name].astype('string').fillna('__MISSING__').unique().tolist()) for name in k.CAT[line]}}
    assert prep['numeric']==k.NUM[line] and prep['categorical']==k.CAT[line]
    values=[(np.where(missing,np.asarray(prep['median']),raw)-np.asarray(prep['mean']))/np.asarray(prep['scale']),missing.astype(float)]
    names=k.NUM[line]+[name+'__missing' for name in k.NUM[line]]
    for name,levels in prep['levels'].items():
        z=f[name].astype('string').fillna('__MISSING__').to_numpy(str)
        values.append(np.column_stack([z==level for level in levels]).astype(float));names += [name+'='+v for v in levels]
    matrix=np.ascontiguousarray(np.column_stack(values),dtype=float);assert np.isfinite(matrix).all()
    if 'columns' not in prep:prep['columns']=names
    assert prep['columns']==names
    return matrix,prep


def cost_level(y,base):
    y=np.asarray(y,dtype=float);base=np.asarray(base,dtype=float)
    assert np.isfinite(y).all() and (y>=0).all() and y.sum()>0
    assert np.isfinite(base).all() and (base>0).all()
    value=float(np.sum(y/np.sqrt(base))/np.sum(np.sqrt(base)))
    other=math.fsum((y/np.sqrt(base)).tolist())/math.fsum(np.sqrt(base).tolist())
    assert math.isclose(value,other,rel_tol=3e-13)
    return value


def fit(frame,line,checkpoint=None):
    train=frame.loc[~frame.is_held].copy()
    assert set(train.group_id).isdisjoint(set(frame.loc[frame.is_held,'group_id']))
    n=train.n_accepted.to_numpy(float);base=train.count_offset.to_numpy(float)
    eligible=p108.p107.count_likelihood_domain(n,base)
    assert n.sum()>0 and eligible.any()
    # A zero-exposure/zero-count row has no Poisson likelihood contribution.
    # Preprocessing is also restricted to eligible training rows; original row
    # count is retained in the mean-objective penalty scaling.
    x,prep=design(train.loc[eligible],line);target=n[eligible]/base[eligible];weight=base[eligible]
    adjusted=ALPHA*len(train)/weight.sum()
    estimator=PoissonRegressor(alpha=adjusted,**PARAMS)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always',ConvergenceWarning);estimator.fit(x,target,sample_weight=weight)
    artifact={'line':line,'preprocess':prep,'coef':estimator.coef_.tolist(),'intercept':float(estimator.intercept_),
        'parameters':{**PARAMS,'nominal_alpha_original_row_mean':ALPHA,'adjusted_alpha':float(adjusted)},
        'n_iter':int(estimator.n_iter_),'warnings':[str(z.message) for z in caught],
        'fit_row_ids_digest':digest(train.row_id),'fit_groups_digest':digest(train.group_id.unique()),
        'eligible_count_rows':int(eligible.sum()),'original_training_rows':len(train),'observed_events':int(n.sum())}
    if checkpoint is not None:dump(checkpoint.with_name(checkpoint.stem+'_count_raw.json'),artifact)
    a=np.exp(x@estimator.coef_+estimator.intercept_)
    assert np.allclose(a,estimator.predict(x),rtol=2e-13)
    mu=weight*a
    direct=2*math.fsum((xlogy(n[eligible],n[eligible]/mu)-n[eligible]+mu).tolist())
    converted=mean_poisson_deviance(target,a,sample_weight=weight)*weight.sum()
    assert math.isclose(direct,converted,rel_tol=3e-12,abs_tol=1e-9)
    penalty=float(np.dot(estimator.coef_,estimator.coef_))
    original_objective=.5*direct/len(train)+.5*ALPHA*penalty
    transformed_objective=.5*converted/weight.sum()+.5*adjusted*penalty
    assert math.isclose(transformed_objective,original_objective*len(train)/weight.sum(),rel_tol=3e-12,abs_tol=1e-10)
    score=weight*(a-target)/weight.sum()
    gradient=np.r_[score.sum(),x.T@score+adjusted*estimator.coef_]
    artifact['gradient_inf']=float(np.max(np.abs(gradient)))
    artifact['count_offset_and_penalty_objective_identity']=True
    assert not artifact['warnings'] and artifact['gradient_inf']<1e-5
    # Cost calibration is a second supervised stage; its full T0 ancestry is
    # stored, never described as a pure-source price or frequency-only fit.
    all_x,_=design(train,line,prep);all_a=np.exp(all_x@estimator.coef_+estimator.intercept_)
    source=train.annual_paired_cost.to_numpy(float);e=train.exposure_calendar.to_numpy(float)*train.q_paired.to_numpy(float)
    y=train.T0.to_numpy(float)
    artifact['cost_level']=cost_level(y,source*all_a*e)
    artifact['null_cost_level']=cost_level(y,source*e)
    artifact['null_count_level']=float(n.sum()/base.sum())
    artifact['new_closed_level_parameters']=3
    if checkpoint is not None:dump(checkpoint,artifact)
    return artifact


def forward(frame,artifact):
    x,_=design(frame,artifact['line'],artifact['preprocess'])
    a=np.exp(x@np.asarray(artifact['coef'])+artifact['intercept'])
    source=frame.annual_paired_cost.to_numpy(float);calendar=frame.exposure_calendar.to_numpy(float)
    value=source*a*artifact['cost_level']*calendar
    null=source*artifact['null_cost_level']*calendar
    assert np.isfinite(value).all() and (value>0).all() and np.isfinite(null).all() and (null>0).all()
    return value,null,a


def poison(frame,line):
    f=frame.copy();held=f.is_held
    names=['T0','reserve','n_accepted','count_offset','annual_paired_cost','q_paired','exposure_calendar']+k.BASE_NUM[line]+k.BASE_CAT[line]
    for name in dict.fromkeys(names):f[name]=f[name].astype('object');f.loc[held,name]='INVALID_HELD'
    return f


def synthetic():
    rng=np.random.default_rng(20261027109);records=[];n=720;i=np.arange(n)
    for line in q.LINES:
        base=rng.uniform(.03,.4,n);events=rng.poisson(base*np.exp(.2*(i%2)))
        f=pd.DataFrame({'row_id':['s'+str(j) for j in i],'line':line,'group_id':['g'+str(j) for j in i],
            'is_held':i%5==0,'fold':i%5,'year':2023+(i//5)%2,'new_business':(i//10)%2,
            'n_accepted':events,'count_offset':base,'T0':events*rng.gamma(2,70,n),'reserve':0.,
            'annual_paired_cost':np.exp(rng.normal(5,.3,n)),'exposure_calendar':rng.uniform(.2,1,n),'q_paired':rng.uniform(.3,1,n)})
        for name in k.BASE_NUM[line]:f[name]=rng.choice([0.,1.,10.,np.nan],n)
        for name in k.BASE_CAT[line]:
            if name!='new_business':f[name]=rng.choice(['a','b','c'],n)
        f.loc[1,['n_accepted','T0','count_offset']]=0
        f.loc[2,['n_accepted','T0']]=[2,0]
        folder=OUT/'synthetic'/line;folder.mkdir(parents=True)
        a=fit(f,line,folder/'primary.json');b=fit(poison(f,line),line,folder/'adverse.json')
        assert a==b
        tr=f.loc[~f.is_held];eligible=tr.count_offset.gt(0)
        matrix,_=design(tr.loc[eligible],line,a['preprocess'])
        observed=tr.loc[eligible,'n_accepted'].to_numpy(float);weight=tr.loc[eligible,'count_offset'].to_numpy(float)
        theta=np.r_[a['intercept'],a['coef']];alpha=a['parameters']['adjusted_alpha']
        def objective(value):
            mean=np.exp(value[0]+matrix@value[1:]);target=observed/weight
            dev=2*(xlogy(target,target/mean)-target+mean)
            return .5*math.fsum((weight*dev).tolist())/weight.sum()+.5*alpha*float(value[1:]@value[1:])
        mean=np.exp(theta[0]+matrix@theta[1:]);score=weight*(mean-observed/weight)/weight.sum()
        derivative=np.r_[score.sum(),matrix.T@score+alpha*theta[1:]]
        for j in range(min(4,len(theta))):
            hi=theta.copy();lo=theta.copy();hi[j]+=1e-5;lo[j]-=1e-5
            numerical=(objective(hi)-objective(lo))/(2e-5)
            assert math.isclose(numerical,derivative[j],rel_tol=2e-4,abs_tol=2e-8)
        held=f.loc[f.is_held].copy();value,null,relative=forward(held,a)
        clean=held.drop(columns=['T0','reserve','q_paired','count_offset','n_accepted'])
        other=forward(clean,json.loads(json.dumps(b)))
        assert all(np.array_equal(x,y) for x,y in zip((value,null,relative),other))
        subset=np.arange(0,len(held),7)
        assert all(np.allclose(x[subset],y,rtol=2e-13,atol=1e-13) for x,y in zip((value,null,relative),forward(clean.iloc[subset],a)))
        assert all(np.allclose(x[::-1],y,rtol=2e-13,atol=1e-13) for x,y in zip((value,null,relative),forward(clean.iloc[::-1],a)))
        train=f.loc[~f.is_held];mu=train.annual_paired_cost.to_numpy(float)*train.exposure_calendar.to_numpy(float)*train.q_paired.to_numpy(float)
        # A constant count factor cancels out of the later cost level. The null
        # cost comparator therefore does not need an artificial shape change.
        scaled=cost_level(train.T0,mu*a['null_count_level'])*a['null_count_level']
        assert math.isclose(scaled,a['null_cost_level'],rel_tol=3e-13)
        records.append({'line':line,'whole_count_and_cost_learning_held_poison_exact':True,
            'offset_penalty_objective_and_finite_difference_gradient_match':True,
            'JSON_replay_exact':True,'quote_without_labels_count_offset_or_q':True,
            'subset_permutation_projective':True,'zero_count_exposure_and_accepted_cost0_retained':True,
            'null_constant_count_level_cancels_from_cost_price':True,'gradient_inf':a['gradient_inf']})
    return {'author':'Codex','utc':utc(),'records':records,'synthetic_primary_Poisson_fits':3,
        'synthetic_adverse_Poisson_fits_separate':3,'synthetic_primary_closed_levels':9,
        'synthetic_adverse_closed_levels_separate':9,'new_real_fits':0,'new_scores':0}


def prepare_frame(line,outer):
    raw=k.frame_for(line,outer)
    keep=['row_id','line','year','group_id','fold','is_held','new_business','T0','reserve','period_start','period_end','exposure_calendar']+k.BASE_NUM[line]+k.BASE_CAT[line]
    f=raw[list(dict.fromkeys(keep))].copy()
    paired=pd.read_parquet(p108.OUT/f'paired_source_{line}.parquet').set_index('row_id').loc[f.row_id].reset_index()
    assert np.array_equal(paired.year,f.year) and np.array_equal(paired.T0,f.T0)
    assert np.array_equal(paired.group_id,f.group_id) and np.array_equal(paired.fold,f.fold)
    assert f.row_id.is_unique and np.array_equal(f.is_held,f.fold.eq(outer))
    f['n_accepted']=paired.n_accepted.to_numpy()
    count=np.zeros(len(f));cost=np.zeros(len(f));cost_observed=np.zeros(len(f))
    curves=w.read(P64/f'NOMINAL_outer{outer}'/line/'primary_curves.json')
    for peril in q.PERILS[line]:
        lam=paired['frequency_'+peril].to_numpy(float);mark=paired['mark_'+peril].to_numpy(float)
        count+=lam*paired['E_count_source_'+peril].to_numpy(float)
        cost+=lam*mark
        cost_observed+=lam*mark*q.effective(f,curves['curves'][peril])
    f['count_offset']=count;f['annual_paired_cost']=cost
    f['q_paired']=cost_observed/(cost*f.exposure_calendar.to_numpy(float))
    assert (count>0).all() and (cost>0).all() and np.isfinite(f.q_paired).all() and f.q_paired.between(0,1+1e-12).all()
    assert f.q_paired.gt(0).all()
    return f


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    assert w.read(p108.INDEX)['status']=='P108historical_paired_source_rates_exported_no_target_model'
    original=w.read(R/'registro/semana2_GLM_bandas_negocio_validacion_plan.json')
    paths=[Path(__file__),Path(k.__file__),Path(k.r.__file__),Path(q.__file__),Path(p108.__file__),
        p108.INDEX,p108.OUT/'report.json',P64/'report.json',P64/'completion_receipt.json',
        R/'registro/semana2_GLM_bandas_negocio_validacion_plan.json',R/'registro/semana2_mision_privada_plan_v1.json']
    for line in q.LINES:
        paths += [p108.OUT/f'paired_source_{line}.parquet']
        for outer in range(5):
            paths += [k.r.p.t.t.OUT/f'input_{line}_{outer}.parquet',P64/f'NOMINAL_outer{outer}'/line/'primary_curves.json']
    OUT.mkdir()
    plan={'author':'Codex','utc':utc(),'scope':'New fixed standard count-supervised target kernel: synthetic whole-learning test and15strict numerical scope inputs only. No real target/source/CDFfit or target score in this unit.',
        'need':'Cost-supervised standard shape/capacity/level variants failed. True accepted counts are9102events, not8071positive periods. Test whether a less severity-sensitive response can transfer risk shape; source P30cost transport failure remains.',
        'hypothesis':'A regularized Poisson correction of source accepted-event frequency may transfer shape more stably than cost-only corrections. Source mark allocation stays frozen and a single own-train Tweedie1.5cost level perline preserves the final original T0cost objective.',
        'configuration':{'count_offset':'B_N=sum_peril(lambda_source*E_count_source); source count exposure fixed from P107, no target claim in its CDF.',
            'cost_offset':'S=sum_peril(lambda_source*mark_source); E_Cmix=sum(lambda*mark*E_Cscope)/S, own P64cost curves, same fixed source peril weights in cost scenarios.',
            'frequency_model':'Poisson E[N|x]=B_N*exp(Xbeta+intercept), main effects and existing business-specific history/NCBbands. No source cost covariates or target-learned price/base feature.',
            'numeric':k.NUM,'categorical':k.CAT,'nominal_alpha_original_row_mean':ALPHA,'parameters':PARAMS,
            'weight_and_penalty':'Fit N/B_N with weight B_N on B_N>0, alpha_adjusted=.001*n_original_train/sum(B_N). Zero-exposure zero-count has zero likelihood and stays in n_original. No reweighting or exposure floor.',
            'preprocessing':'Select own training and eligible count rows BEFORE parsing features. Training-only log1p numeric medians/center/scales/missing flags and full onehot existing bands; unknown levels allzero.',
            'cost_level':'kappa=sum(T0/sqrt(S*a*E_Cmix))/sum(sqrt(S*a*E_Cmix)), all own training. Final ultimate period price=calendar*S*a*kappa. No live batch normalization or NB level rescue.',
            'matched_null':'Same source S/E_Cmix and one own-train cost level, with count shape a=1. Store own count level sum(N)/sum(B_N) for count diagnostics; it cancels in cost-level-calibrated null price.',
            'model_ancestry':'Count coefficients and preprocessing learn counts/covariates; cost level learns T0. Full staged algorithm is target learned, never pure-source or an ultimate-frequency identification claim.'},
        'criterion':'3+3synthetic full staged fits with poisoned entire held payload before selection; count objective/scalar cost identity/gradient, JSONlabel-free replay, projectivity, cost0events and zero-exposure handling.15real exact key/group/calendar/label bindings and explicit paired count/cost exposure. No real fit here.',
        'future_validation':{'primary':'Register separately before15primary+15adverse real Poisson fits,45+45closed levels, unchanged all5globalcustomer/addressfolds2023/2024.',
            'comparators':'Primary F3c/A1S reference and all current fixed guards; matched null and P65 secondary mechanism contrasts. No line/weight/alpha/feature rescue.',
            'adverse':'Poison all held cost/count/rating/source/exposure payload before training; numeric qcost own-scope ancestry remains pinned; test full quote flow and replay with ALL count/cost/preprocessing learning blocked.',
            'scenarios':'Same reserve075/125 and tail005/010protocol with own stored cost curves, same nominal source paired weights and final nominal model held fixed; no scenario count/price fit.',
            'staged':'Every unchanged P82predictive/cohort/convergence/level/influence/family16guard. Pooledfailure forbids admission; pooledpass still needs OWN2023-only conditionaltransfer with proper own cost reporting before CSV.'},
        'future_budget':{'primary_Poisson_fits':15,'adverse_Poisson_fits_separate':15,'primary_closed_levels':45,'adverse_closed_levels_separate':45,
            'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0},
        **{name:original[name] for name in ['criteria','bootstrap','cohort_guard','level_sensitivity']},
        'limits':['Frequency, mark and reporting transport can fail; sparse target events do not establish credible peril-specific mark updates.',
            'Retrospective2024-12-31status/reserve/reporting snapshots, unobserved tail, adaptive search and source2024ancestry remain.',
            'No private or public improvement is established; source-derived count shape and fixed severity may still underfit the private mixture.'],
        'sources':{w.rel(path):w.sha(path) for path in paths},'B00_all_alternatives_preserved':True,'2024_open':True,'goal_achieved':False}
    dump(PLAN,plan)
    body=OUT/'forum_previo.md';body.write_text('Codex. P109 registra el preflight de un Poisson estándar por ramo con recuentos aceptados, offset de frecuencia pareada fuente y exposición por número P107. La corrección de frecuencia es común a los perils; las marcas fuente permanecen fijas. Un nivel Tweedie de coste aprende T0 en el propio entrenamiento. Se especifica un comparador emparejado sin corrección de forma, con la misma exposición de coste. Las exposiciones de coste y número siguen separadas. Nominal alpha=.001 en la media por fila original, con reescalado exacto por pesos; no búsqueda de alpha o capacidad. Solo 3+3 ajustes sintéticos y 15 entradas reales sin ajustar en esta unidad. Una evaluación real requiere registro propio y todas las guardas privadas, cohortes, estrés y transferencia; no admisión por punto o mejora pública. B00 y P30 adverso preservados. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P109registered_before_Poisson_synthetic_preflight','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':p108.p107.previous.post(body,'COD-S2-20261027-PRIVADA-P109-POISSON-PREVIO','P109: frecuencia estándar y objetivo de coste, antes de probar')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def run():
    plan=w.read(PLAN);p108.p107.previous.check_sources(plan)
    with threadpool_limits(limits=2):dump(OUT/'synthetic.json',synthetic())
    outputs={};records=[]
    for line in q.LINES:
        for outer in range(5):
            f=prepare_frame(line,outer);path=OUT/f'input_{line}_{outer}.parquet';f.to_parquet(path,index=False)
            outputs[w.rel(path)]=w.sha(path)
            records.append({'line':line,'outer':outer,'rows':len(f),'train_events':int(f.loc[~f.is_held,'n_accepted'].sum()),
                'count_offset_min':float(f.count_offset.min()),'cost_completion_min':float(f.q_paired.min()),
                'training_groups_disjoint':set(f.loc[~f.is_held,'group_id']).isdisjoint(set(f.loc[f.is_held,'group_id']))})
    assert all(record['training_groups_disjoint'] for record in records)
    p108.p107.previous.check_sources(plan)
    dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P109synthetic_staged_Poisson_and15scope_inputs_complete_no_real_fit',
        'records':records,'outputs':outputs,'new_real_Poisson_fits':0,'new_CDF_fits':0,'new_scores':0,'new2025inference':0,'new_submissions':0,
        'synthetic_primary_Poisson_fits':3,'synthetic_adverse_Poisson_fits_separate':3,'synthetic_primary_closed_levels':9,'synthetic_adverse_closed_levels_separate':9})
    print(json.dumps({'synthetic_whole_flows':3,'real_scope_inputs':15,'new_real_fits':0,'new_scores':0}))


def close():
    plan=w.read(PLAN);p108.p107.previous.check_sources(plan);report=w.read(OUT/'report.json')
    assert all(w.sha(ROOT/path)==sha for path,sha in report['outputs'].items())
    next_unit='P110: implement/register real complete validation of EXACT P109staged Poisson-count/cost-level algorithm and matched null. Reuse these15inputs and own P64cost curves, prepare paired-weight scenario q, retain ALL original private guards and raw fit attempt counters before running.15+15Poissonfits/45+45closed levels, no source/CDFfit or capacity rescue. Score only after preregistration; replay ALL learned stages blocked. Transfer remains pending unless pooled guards all pass.'
    text='# P109: Poisson de frecuencia, preflight completo\n\nCodex, '+utc()+'.\n\nQuedó fijada una receta estándar por ramo que aprende la corrección de frecuencia con recuentos aceptados y exposición por número. Las marcas fuente se mantienen; un segundo paso calibra el nivel de coste con T0. Su comparador emparejado mantiene la misma fuente y exposición, sin corrección de forma. Se declaran ambos pasos y su dependencia de etiquetas destino.\n\nPasaron tres flujos sintéticos primarios y tres adversos, con todo el contenido retenido alterado antes de seleccionar entrenamiento. Coincidieron los modelos completos, el objetivo Poisson por otro método, el gradiente, la calibración escalar y el replay JSON sin etiquetas en la consulta. Se conservaron eventos de coste cero y filas de recuento/exposición cero. La predicción por subconjunto y permutación fue coherente. Se prepararon 15 entradas numéricas reales con claves, años, grupos y costes exactos; sus offsets de número y completitud de coste usan pesos fuente pareados y curvas separadas. No se ajustó un modelo real.\n\nLa receta no añade capacidad, nuevas variables o búsqueda de penalización; alpha nominal .001 sigue la convención por fila original y se reescala exactamente por peso. Las curvas de número son fuente fijas; las curvas de coste se reutilizan dentro de su propio ámbito. El transporte fuente-destino, la valoración retrospectiva, reservas y cola siguen limitando la interpretación. Los adversos previos se conservan.\n\nLa evaluación real todavía está pendiente y requiere registro, contadores de intentos, escenarios pareados y todas las guardas predictivas y por cohortes. Un resultado combinado favorable necesitaría además su transferencia propia de 2023 antes de considerar un CSV. No hay evidencia de mejora privada o nuevo envío admisible. B00 intacto, prioridad privada, 2024 abierto como desarrollo adaptativo.\n\nPróximo: '+next_unit+'\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':report['status'],'report':w.rel(OUT/'report.json'),
        'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'outputs':report['outputs'],
        'new_real_fits':0,'new_CDF_fits':0,'new_scores':0,'new2025inference':0,'new_submissions':0,'next_unit':next_unit,'2024_open':True,'goal_achieved':False,
        'forum':p108.p107.previous.post(body,'COD-S2-20261027-PRIVADA-P109-POISSON-RESULTADO','P109: flujo sintético de frecuencia/coste y entradas protegidas')}
    cut=R/'privado'/('corte_P109_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));cut.mkdir();w.update(INDEX,receipt,cut)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P109'),(R/'registro/semana2_mision_privada_actual.json','P109')]:
        w.update(path,{key:receipt,'next_unit':next_unit},cut)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025']
    own.update(private_P109=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},cut)
    note='\n\n## Privada P109: frecuencia y coste\n\nCodex, '+receipt['utc']+'. Receta Poisson estándar con niveles de coste y null emparejado. Pasaron 3+3 flujos sintéticos y 15 entradas reales; cero ajuste real o score. Evaluación completa pendiente. Informe '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,cut)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_target_Poisson_preflight_index':w.rel(INDEX),
        'week_2_private_target_Poisson_preflight_report':w.rel(DOC)},cut)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['register','run','close']);{'register':register,'run':run,'close':close}[parser.parse_args().mode]()
