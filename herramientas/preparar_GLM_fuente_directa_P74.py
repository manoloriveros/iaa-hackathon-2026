"""Un único GLM destino con offset fuente T2b y señal relativa fuente A1S."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import argparse
import warnings
import math
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p74_fixed_reporting',R/'herramientas/validar_GLM_reporte_actual_P67.py')
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
m=p.m;q=p.q;w=p.w;pd=p.pd;np=p.np;BASE=p.BASE
from sklearn.linear_model import TweedieRegressor
from sklearn.metrics import mean_tweedie_deviance
from sklearn.exceptions import ConvergenceWarning
import sklearn
OUT=BASE/'P74_GLM_fuente_directa_preflight_20261027'
PLAN=R/'registro/semana2_GLM_fuente_directa_preflight_plan.json';INDEX=R/'registro/semana2_GLM_fuente_directa_preflight_actual.json'
DOC=R/'docs/semana2/PRIVADA_P74_GLM_FUENTE_DIRECTA_PREFLIGHT.md'
PARAMS=dict(p.g.PARAMS)
NUM={line:list(p.g.NUM[line])+['prior_claims_5y']+(['ncb_years'] if line=='motor' else []) for line in q.LINES}
CAT={line:list(p.g.CAT[line]) for line in q.LINES}


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)


def frame_for(line,outer):
    raw=pd.read_parquet(p.t.t.OUT/f'input_{line}_{outer}.parquet')
    names=['row_id','line','year','group_id','fold','new_business','T0','reserve','period_start','period_end','exposure_calendar','annual_A1S','annual_T2b','q_paired','is_held']+NUM[line]+CAT[line]
    f=raw[list(dict.fromkeys(names))].copy()
    assert not any(name.startswith(('baseline_','crossfit_','e_cost')) for name in f)
    assert np.array_equal(f.is_held,f.fold.eq(outer)) and f.year.isin([2023,2024]).all()
    return f


def numeric(f,line):
    a=f.annual_A1S.to_numpy(float);b=f.annual_T2b.to_numpy(float)
    assert np.isfinite(a).all() and (a>0).all() and np.isfinite(b).all() and (b>0).all()
    values=[np.log(b),np.log(a)]
    for name in NUM[line]:
        x=pd.to_numeric(f[name],errors='coerce').to_numpy(float);x=np.where(np.isfinite(x)&(x>=0),x,np.nan);values.append(np.log1p(x))
    return np.column_stack(values)


def design(f,line,pre=None):
    raw=numeric(f,line);missing=~np.isfinite(raw);numeric_names=['log_annual_T2b_source','log_relative_A1S_source']+NUM[line]
    if pre is None:
        med=[float(np.median(raw[~missing[:,j],j])) if (~missing[:,j]).any() else 0. for j in range(raw.shape[1])]
        filled=np.where(missing,np.asarray(med),raw);center=filled.mean(axis=0);scale=filled.std(axis=0);scale=np.where(scale>0,scale,1.)
        pre={'line':line,'numeric':numeric_names,'categorical':CAT[line],'median':med,'mean':center.tolist(),'scale':scale.tolist(),
            'levels':{name:sorted(f[name].astype('string').fillna('__MISSING__').unique().tolist()) for name in CAT[line]}}
    assert numeric_names==pre['numeric'];filled=np.where(missing,np.asarray(pre['median']),raw)
    parts=[(filled-np.asarray(pre['mean']))/np.asarray(pre['scale']),missing.astype(float)];names=numeric_names+[name+'__missing' for name in numeric_names]
    for name,levels in pre['levels'].items():
        x=f[name].astype('string').fillna('__MISSING__').to_numpy(str);parts.append(np.column_stack([x==level for level in levels]).astype(float));names.extend(name+'='+level for level in levels)
    x=np.ascontiguousarray(np.column_stack(parts),dtype=np.float64);assert np.isfinite(x).all()
    if 'columns' not in pre:pre['columns']=names
    assert names==pre['columns'];return x,pre


def ultimate_source_offset(f):
    # CU/source-year * calendar-years. qand all target payload are deliberately absent.
    value=f.annual_T2b.to_numpy(float)*f.exposure_calendar.to_numpy(float)
    assert np.isfinite(value).all() and (value>0).all();return value


def fit(f,line,checkpoint=None):
    train=f.loc[~f.is_held].copy();held_groups=set(f.loc[f.is_held,'group_id']);assert set(train.group_id).isdisjoint(held_groups)
    x,pre=design(train,line);y=train.T0.to_numpy(float);base=ultimate_source_offset(train)*train.q_paired.to_numpy(float)
    assert np.isfinite(y).all() and (y>=0).all() and np.isfinite(base).all() and (base>0).all()
    weight=np.sqrt(base);target=y/base;model=TweedieRegressor(**PARAMS)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always',ConvergenceWarning);model.fit(x,target,sample_weight=weight)
    artifact={'line':line,'preprocess':pre,'coef':model.coef_.tolist(),'intercept':float(model.intercept_),'parameters':PARAMS,'sklearn_version':sklearn.__version__,
        'n_iter':int(model.n_iter_),'warnings':[str(z.message) for z in caught],'fit_row_ids_digest':m.p.b.digest(sorted(train.row_id)),
        'fit_groups_digest':m.p.b.digest(sorted(set(train.group_id))),'source_offset':'T2bannual_source_scale*calendar*owntrainingq; no target-trained base risk or batch normalizer'}
    if checkpoint is not None:dump(checkpoint,artifact)
    relative=np.exp(x@model.coef_+model.intercept_);assert np.allclose(relative,model.predict(x),rtol=2e-13)
    direct=float(m.e.unit(y,base*relative).sum());other=mean_tweedie_deviance(target,relative,power=1.5,sample_weight=weight)*weight.sum()
    assert math.isclose(direct,other,rel_tol=2e-12,abs_tol=1e-7)
    score=weight*(np.sqrt(relative)-target/np.sqrt(relative))/weight.sum();gradient=np.r_[score.sum(),x.T@score+PARAMS['alpha']*model.coef_]
    artifact.update(gradient_inf=float(np.max(np.abs(gradient))),offset_homogeneity_loss_match=True,manual_linear_prediction_matches_API=True)
    return artifact


def forward(f,artifact):
    x,_=design(f,artifact['line'],artifact['preprocess']);relative=np.exp(x@np.asarray(artifact['coef'])+artifact['intercept'])
    value=ultimate_source_offset(f)*relative;assert np.isfinite(value).all() and (value>0).all();return value,relative


def poison(f,line):
    z=f.copy();held=z.is_held
    names=list(dict.fromkeys(['T0','reserve','q_paired','annual_A1S','annual_T2b','exposure_calendar']+NUM[line]+CAT[line]))
    for name in names:z[name]=z[name].astype('object');z.loc[held,name]='INVALID_HELD'
    return z


def independent_math(train,artifact):
    x,_=design(train,artifact['line'],artifact['preprocess']);base=ultimate_source_offset(train)*train.q_paired.to_numpy(float)
    y=train.T0.to_numpy(float);relative=np.exp(x@np.asarray(artifact['coef'])+artifact['intercept'])
    direct=math.fsum((4*y/np.sqrt(base*relative)+4*np.sqrt(base*relative)-8*np.sqrt(y)).tolist())
    transformed=math.fsum((np.sqrt(base)*(4*(y/base)/np.sqrt(relative)+4*np.sqrt(relative)-8*np.sqrt(y/base))).tolist())
    assert math.isclose(direct,transformed,rel_tol=2e-12,abs_tol=1e-7)
    weight=np.sqrt(base);score=weight*(np.sqrt(relative)-(y/base)/np.sqrt(relative))/weight.sum();gradient=np.r_[score.sum(),x.T@score+PARAMS['alpha']*np.asarray(artifact['coef'])]
    assert math.isclose(float(np.max(np.abs(gradient))),artifact['gradient_inf'],rel_tol=2e-9,abs_tol=2e-13)
    for j in range(min(3,x.shape[1])):
        scalar=math.fsum((x[:,j]*score).tolist())+PARAMS['alpha']*artifact['coef'][j];assert math.isclose(scalar,gradient[j+1],abs_tol=2e-13)
    return {'original_uncapped_offset_loss_scalar_identity':True,'gradient_scalar_and_vector_match':True,'gradient_inf':artifact['gradient_inf']}


def synthetic():
    rng=np.random.default_rng(2026102774);n=600;records=[]
    for line in q.LINES:
        i=np.arange(n);f=pd.DataFrame({'row_id':['s'+str(j) for j in i],'group_id':['g'+str(j) for j in i],'is_held':i%5==0,'fold':i%5,'year':2023+(i//5)%2,
            'new_business':(i//10)%2,'T0':np.round(rng.gamma(2,90,n)*(rng.random(n)<.4),2),'reserve':0.,'annual_A1S':np.exp(rng.normal(0,.4,n)),
            'annual_T2b':np.exp(rng.normal(4,.5,n)),'exposure_calendar':rng.uniform(.1,1,n),'q_paired':rng.uniform(.3,1,n)})
        for name in NUM[line]:f[name]=rng.choice([0.,10.,100.],n)
        for name in CAT[line]:
            if name!='new_business':f[name]=rng.choice(['a','b','c'],n)
        folder=OUT/'synthetic'/line
        a=m.once(folder,'primary',lambda:fit(f,line,folder/'primary_raw.json'));b=m.once(folder,'adverse',lambda:fit(poison(f,line),line,folder/'adverse_raw.json'));assert a==b
        assert not a['warnings'] and a['gradient_inf']<1e-5
        checks=independent_math(f.loc[~f.is_held],a);held=f.loc[f.is_held].copy();value,relative=forward(held,a)
        no_target=held.drop(columns=['T0','reserve','q_paired']);replay,rr=forward(no_target,json.loads(json.dumps(b)))
        assert np.array_equal(value,replay) and np.array_equal(relative,rr)
        selected=np.arange(0,len(held),7);subset,_=forward(no_target.iloc[selected],a);assert np.allclose(subset,value[selected],rtol=2e-13,atol=1e-13)
        permutation=np.arange(len(held))[::-1];shuffled,_=forward(no_target.iloc[permutation],a);assert np.allclose(shuffled,value[permutation],rtol=2e-13,atol=1e-13)
        # Every fitted source center is frozen; no new row/batch normalization in target GLM.
        records.append({'line':line,'all_held_cost_source_offset_and_covariate_poison_fit_invariant':True,'ultimate_target_q_not_read':True,
            'subset_and_permutation_projective_given_fixed_source_inputs':True,'JSON_replay_exact':True,'independent_math':checks})
    return {'author':'Codex','utc':utc(),'records':records,'synthetic_primary_GLMfits':3,'synthetic_adverse_GLMfits_separate':3,'new_real_fits':0,'new_source_fits':0,'new_CDF_fits':0,'new_scores':0,'new_submissions':0}


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    previous=BASE/'P73_offsets_guardados_20261027';assert w.read(previous/'completion_receipt.json')['report_sha256']==w.sha(previous/'report.json')
    parent=w.read(p.PLAN);m.check_sources(parent)
    paths=[Path(__file__),p.PLAN,previous/'report.json',previous/'completion_receipt.json',R/'registro/semana2_mision017_A1S_fuente_plan_v1.json',R/'herramientas/entrenar_nucleo_A1S.py',
        BASE/'A1S_nucleo_20261026_v1/source_models/report.json',BASE/'P21_cache_T2b_20261026/report.json',BASE/'P41_grafo_fuente_recuperada_20261026/report.json',Path(sklearn.__file__)]
    for line in q.LINES:
        paths += [BASE/f'A1S_nucleo_20261026_v1/source_models/target_{line}_three_seed_components.parquet']
        paths += [p.t.t.OUT/f'input_{line}_{outer}.parquet' for outer in range(5)]
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'scope':'Source-unit/ancestry reuse plus new direct-target GLMsynthetic full flow and strict15input bindings only. ZEROreal target/source/curvefit or score.',
        'need':'P73measured substantial whole-target-base64percent/80percent differences while qdifferences were tiny; residual GLM/robustshape/boosting all fail. Remove target-cost-trained price ancestors entirely from the final risk feature/offset, rather than changing their sample size or increasing residual capacity. The measured spread is not a proved cause.',
        'hypothesis':'A single regularized target GLMusing fixed developed-only source risk and supplied rating covariates may generalize better without target-derived base offset variation. No known improvement or private guarantee.',
        'source_contract':{'annual_A1S':'Dimensionless exp(logrelative); geometric mean of all3saved developed-source seeds. Centers are source exposure-weighted means, NOTtarget or application-batch centers. Coefficients/centers developed2021-2024; target covariates only in these predictions.',
            'annual_T2b':'Original saved total annual monetary-scale source risk proxy, no peril decomposition or emerging-target price calibration. Reused P21raw binding and P41graph; no repeated producer/header/inference suite or claim of identified ultimate truth.',
            'availability':'Source2024conditional and supplied snapshot/history/weather assumptions persist; not an as-of2023quote backtest. T2bdiscount/payment windows and missing2023history remain limitations.'},
        'configuration':{'offset':'annual_T2b_source*calendar_exposure*own_outerP64rowFSpPROXYqfor observed fit. Ultimate uses source_annual_T2b*calendar_exposure ONLY, multiplied by saved GLMexpeta; qand target not read in ultimate.',
            'numeric_source_signals':['log_annual_T2b_source','log_relative_A1S_source'],'numeric_other':NUM,'categorical':CAT,'GLMparameters':PARAMS,
            'fields_reason':'Same already-used rating fields; prior_claims/ncbwere target-base shape inputs and now enter directly as log1pmain effects because that base is removed. Source annual risk signals replace the target-trained base risk, not selected by held coefficient signs.',
            'preprocessing':'Training-only median/log1p/missingflags/standardization and full onehot, unknown levelallzero. No interactions, cap, newfields, targetbasefeatures, nested price learners, foldmean, application normalizers or tuned hyperparameters.',
            'objective':'Original uncappedT0; y/bwith sample_weight=sqrt(b) exactly gives Tweedie1.5offset deviance. Alpha1/intercept/log/lbfgs1000tol1e-7as previous standard GLM.'},
        'new_ancestry':'Only nuisance reporting P64is learned on outertraining target claims; price risk features/offset T2b/A1Sdo NOTdepend on any target-cost-trained base, its qfit, shapes/levels or batch normalizers. All target estimation is ONEGLMperline. No training stacker on in-sample target predictions.',
        'future_budget':{'primary_GLMfits':15,'adverse_GLMfits_separate':15,'new_target_base_fits':0,'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0},
        'preflight_criterion':'Full actual preprocessing/fit with ALLheld cost/source/covariate/exposure/qpayload corrupt before trainselector; objective and gradients by another method; JSONexact; ultimate ignores cost/qand is subset/permutation projective given fixed source inputs. Strict frames exclude inherited baseline/crossfit/e_costfeatures.',
        'future_criterion':'Every original P67predictive/cohort/family16/scenario/level/influence gate plus GLMconvergence. Pooled fail prevents admission; pooled pass requires OWN2023-only conditional-transfer reporting+directGLMbefore CSVadmission. No copied pooled2024target-trained qobjects there.',
        'sources':{**parent['sources'],**{w.rel(path):w.sha(path) for path in paths}},
        'limits':['Changing the entire target learning architecture is a standard alternative, not a causal single-parameter attribution of past losses.','A1S/T2bmodels and source-only report offsets remain fixed/conditional; no independent source2024held-label proof or ultimate identification.',
            'Market/valuation/tail/reserves/undatedmasters and adaptive2023/2024selection persist; no independent professional validation.'],
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. P74registra antes de probar un GLMúnico destino, offset T2banual fuente*calendario*qP64propio, señal A1Srelativa fuente y campos habituales. Se elimina la base de precio ajustada con costes emergentes y sus offsetsOOF; historia/NCBya usados por esa base entran ahora como efectos principales. Un solo GLMalpha1sin búsqueda, no stacking sobre predicciones target in-sample. FuenteA1Scentrada con exposiciones DESARROLLADASy3semillas fijas; T2bes proxyanual monetario total, no verdad última identificada. Preflight3+3GLM, matemática/veneno/projectividad/15entradas, cero ajuste real. Futuro15+15GLMcon TODASlas guardas y transferencia propia si pasa. B00conservado,2024abierto adaptativo; fuente2024/snapshotscondicionales y cero2025/envíos. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P74registered_before_direct_target_GLM_preflight','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P74-DIRECTO-PREVIO','P74: un GLM destino con riesgo fuente puro, antes de probar')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def run():
    assert not (OUT/'report.json').exists();plan=w.read(PLAN);m.check_sources(plan);assert w.read(OUT/'registration.json')['plan_sha256']==w.sha(PLAN)
    dump(OUT/'synthetic.json',synthetic());bindings=[]
    for line in q.LINES:
        source=pd.read_parquet(BASE/f'A1S_nucleo_20261026_v1/source_models/target_{line}_three_seed_components.parquet',columns=['row_id','log_relative_A1S']).set_index('row_id')
        for outer in range(5):
            f=frame_for(line,outer);assert f.row_id.is_unique and set(f.loc[~f.is_held,'group_id']).isdisjoint(set(f.loc[f.is_held,'group_id']))
            assert np.array_equal(np.exp(source.loc[f.row_id,'log_relative_A1S'].to_numpy(float)),f.annual_A1S)
            assert f.annual_T2b.gt(0).all() and f.exposure_calendar.gt(0).all() and f.q_paired.gt(0).all()
            bindings.append({'line':line,'outer':outer,'rows':len(f),'strict_columns':list(f),'source_A1S_seed_geomean_binding_exact':True,
                'original_T2b_annual_already_verified_P21':True,'target_trained_price_ancestors_in_numeric_inputs':False})
    m.check_sources(plan);dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P74direct_source_offset_GLM_synthetic_and_bindings_passed','plan_sha256':w.sha(PLAN),'bindings':bindings,
        'new_real_fits':0,'new_target_base_fits':0,'new_source_fits':0,'new_CDF_fits':0,'new_scores':0,'new2025inference':0,'new_submissions':0})
    print(json.dumps({'preflight':'passed','bindings':15,'new_real_fits':0,'new_scores':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();d=w.read(OUT/'report.json');m.check_sources(w.read(PLAN))
    next_unit='P75: register and commit ONEdirect target GLMperline/outer,15primary+15adverse real fits, current P64qand source-only T2boffset/A1Ssignal. No target-base/OOFprice fits or source/CDFrefits. Every existing predictive/cohort/scenario/family16/level/influence guard and convergence; transfer OWN2023required after pooled pass before CSV.'
    text='# P74: un GLM destino con señales fuente\n\nCodex, '+utc()+'. Se prepara un único GLMcon offset de tasa anual fuenteT2bpor exposición calendario y qpropio del fold, señal relativa fuenteA1Sycampos habituales. Historia/NCBentran directamente porque ya no hay una base de precio ajustada con costes target. Se conserva alpha1yefectos principales; no predicciones target in-samplepara stacking, offsetsOOFde precio o centros por lote.\n\n'
    text+='Las unidades y el linaje se apoyan en contratos/recibos fuente ya comprobados: A1Srelativo sin moneda,3semillas y centros desarrollados fijos; T2btotal anual en escala monetaria fuente, proxy sin identificación de último. Se comprobó de nuevo solo la unión exacta de esta entrada nueva, sin repetir productores o auditorías antiguas. qP64sigue siendo un nuisanceaprendido con los siniestros de entrenamiento exterior, sin su retenido.\n\n'
    text+='TresGLMprimarios/3adversos sintéticos pasaron tras alterar TODOSlos costes, señales fuente, exposiciones, qyatributos retenidos antes de preprocesar/ajustar. Objetivo y gradiente coincidieron por otro cálculo; replayJSONexacto y proyección de filas invariante bajo subconjuntos/permutación dadas señales fuente fijas. Se enlazaron15entradas estrictas reales sin bases/precios/flags heredados. Cero ajustes reales/CDF/scoring/2025/envíos.\n\n'
    text+='Esto no demuestra mejora o causalidad de la variación de offsetsP73. La fuente2024ymaestros/historias/clima siguen siendo información suministrada condicional, con ventanas pendientes; no backtestde cotización2023o último identificado. B00/F3cyalternativas preservados,2024abierto adaptativo; toda guardaanterior y transferencia siguen requeridas, sin revisión independiente.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'synthetic.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'next_unit':next_unit,
        'new_real_fits':0,'new_target_base_fits':0,'new_CDF_fits':0,'new_scores':0,'new_submissions':0,'2024_open':True,'goal_achieved':False,
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P74-DIRECTO-RESULTADO','P74: flujo GLM directo protegido y unidades, sin ajuste real')}
    archive=R/'privado'/('corte_P74_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir();w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P74'),(R/'registro/semana2_mision_privada_actual.json','P74')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    cp=R/'registro/semana2_contadores_propios_actual.json';w.update(cp,{'phase2_private_P74_direct_source_GLM_preflight':{**receipt,'synthetic':w.read(OUT/'synthetic.json')}},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P74=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P74: GLM único con riesgo fuente\n\nCodex, '+receipt['utc']+'.Preflight sintético/unidades/15enlaces estrictos pasaron, cero ajuste real/CDF/scoring/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_direct_source_GLM_preflight_index':w.rel(INDEX),'week_2_private_direct_source_GLM_preflight_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'new_real_fits':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['register','run','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'register':register,'run':run,'close':close}[args.mode]()
