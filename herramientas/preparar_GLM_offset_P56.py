"""GLM Tweedie con offset P55 y efectos principales; preflight sin precios ajustados reales."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import argparse
import math
import warnings
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p56_complete_fixed_base',R/'herramientas/validar_mezcla_estandar_P55.py')
v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
k=v.k;m=v.m;w=v.w;np=v.np;pd=v.pd;BASE=v.BASE
from sklearn.linear_model import TweedieRegressor
from sklearn.metrics import mean_tweedie_deviance
from sklearn.exceptions import ConvergenceWarning
import sklearn
HOME=BASE/'A1S_nucleo_20261026_v1';OUT=BASE/'P56_GLM_offset_preflight_20261027'
PLAN=R/'registro/semana2_GLM_offset_preflight_plan.json';INDEX=R/'registro/semana2_GLM_offset_preflight_actual.json'
DOC=R/'docs/semana2/PRIVADA_P56_GLM_OFFSET_PREFLIGHT.md'
NUM={'motor':['voluntary_excess','compulsory_excess','vehicle_age','years_licensed','engine_size_cc'],
    'buildings':['voluntary_excess','compulsory_excess','prop_age','bedrooms'],
    'contents':['voluntary_excess','compulsory_excess','prop_age','bedrooms']}
CAT={'motor':['new_business','channel','vehicle_value_group','age_band','cover_type','vehicle_use','overnight_parking','named_young_driver'],
    'buildings':['new_business','channel','construction_type','occupancy','smoke_alarms','accidental_damage_cover','property_type','roof_type'],
    'contents':['new_business','channel','security_level','high_value_items','accidental_damage_cover','bicycle_cover','tenure','property_type']}
PARAMS={'power':1.5,'alpha':1.,'fit_intercept':True,'link':'log','solver':'lbfgs','max_iter':1000,'tol':1e-7,'warm_start':False}


def utc():return datetime.now(timezone.utc).isoformat()
def dump(p,vv):return m.dump(p,vv)


def numeric(f,line):
    assert f.baseline_ultimate.gt(0).all() and f.exposure_calendar.gt(0).all()
    cols=[np.log(f.baseline_ultimate.to_numpy(float)/f.exposure_calendar.to_numpy(float))]
    for name in NUM[line]:
        raw=pd.to_numeric(f[name],errors='coerce').to_numpy(float);raw=np.where(np.isfinite(raw)&(raw>=0),raw,np.nan)
        cols.append(np.log1p(raw))
    return np.column_stack(cols)


def design(f,line,pre=None):
    raw=numeric(f,line);missing=~np.isfinite(raw)
    if pre is None:
        med=[float(np.median(raw[~missing[:,j],j])) if (~missing[:,j]).any() else 0. for j in range(raw.shape[1])]
        filled=np.where(missing,np.asarray(med),raw);mean=filled.mean(axis=0);scale=filled.std(axis=0);scale=np.where(scale>0,scale,1.)
        levels={name:sorted(f[name].astype('string').fillna('__MISSING__').unique().tolist()) for name in CAT[line]}
        pre={'line':line,'median':med,'mean':mean.tolist(),'scale':scale.tolist(),'levels':levels,
            'numeric':['baseline_log_annual_risk']+NUM[line],'categorical':CAT[line]}
    filled=np.where(missing,np.asarray(pre['median']),raw)
    pieces=[(filled-np.asarray(pre['mean']))/np.asarray(pre['scale']),missing.astype(float)]
    names=pre['numeric']+[n+'__missing' for n in pre['numeric']]
    for name,levels in pre['levels'].items():
        values=f[name].astype('string').fillna('__MISSING__').to_numpy(str)
        pieces.append(np.column_stack([values==level for level in levels]).astype(float));names += [name+'='+level for level in levels]
    x=np.ascontiguousarray(np.column_stack(pieces),dtype=np.float64);assert np.isfinite(x).all()
    if 'columns' not in pre:pre['columns']=names
    assert names==pre['columns'];return x,pre


def fit(f,line,checkpoint=None):
    # Select training keys before ANY imputation, category decoding, scaling, label or offset transformation.
    train=f.loc[~f.is_held].copy();held=f.loc[f.is_held,['group_id']]
    assert set(train.group_id).isdisjoint(set(held.group_id)) and train.T0.ge(0).all()
    x,pre=design(train,line);base=train.baseline_observed.to_numpy(float);assert np.isfinite(base).all() and (base>0).all()
    target=train.T0.to_numpy(float)/base;weight=np.sqrt(base)
    model=TweedieRegressor(**PARAMS)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always',ConvergenceWarning);model.fit(x,target,sample_weight=weight)
    if checkpoint is not None:
        dump(checkpoint,{'line':line,'preprocess':pre,'coef':model.coef_.tolist(),'intercept':float(model.intercept_),
            'n_iter':int(model.n_iter_),'parameters':PARAMS,'warnings':[str(vv.message) for vv in caught],
            'sklearn_version':sklearn.__version__,'fit_row_ids_digest':m.p.b.digest(sorted(train.row_id)),
            'fit_groups_digest':m.p.b.digest(sorted(set(train.group_id)))})
    relative=np.exp(x@model.coef_+float(model.intercept_));api=model.predict(x)
    assert np.allclose(relative,api,rtol=2e-13,atol=2e-13)
    direct=float(m.e.unit(train.T0.to_numpy(float),base*relative).sum())
    transformed=mean_tweedie_deviance(target,relative,power=1.5,sample_weight=weight)*weight.sum()
    assert math.isclose(direct,transformed,rel_tol=2e-12,abs_tol=1e-7)
    score=weight*(np.sqrt(relative)-target/np.sqrt(relative))/weight.sum()
    gradient=np.r_[score.sum(),x.T@score+PARAMS['alpha']*model.coef_]
    result={'line':line,'preprocess':pre,'coef':model.coef_.tolist(),'intercept':float(model.intercept_),
        'n_iter':int(model.n_iter_),'gradient_inf':float(np.abs(gradient).max()),'warnings':[str(vv.message) for vv in caught],
        'parameters':PARAMS,'sklearn_version':sklearn.__version__,'fit_row_ids_digest':m.p.b.digest(sorted(train.row_id)),
        'fit_groups_digest':m.p.b.digest(sorted(set(train.group_id))),
        'offset_homogeneity_loss_match':True,'manual_linear_prediction_matches_API':True}
    return result


def forward(f,a):
    x,_=design(f,a['line'],a['preprocess']);relative=np.exp(x@np.asarray(a['coef'])+a['intercept'])
    result=f.baseline_ultimate.to_numpy(float)*relative;assert np.isfinite(result).all() and (result>0).all()
    return result,relative


def poison(f,line):
    bad=f.copy();held=bad.is_held
    for name in ['T0','reserve','baseline_ultimate','baseline_observed']+NUM[line]+CAT[line]:
        bad[name]=bad[name].astype('object');bad.loc[held,name]='INVALID_HELD'
    return bad


def frame_for(line,outer):
    f=k.frame_for(line,outer);folder=v.OUT/f'{line}_{outer}';a=w.read(folder/'learning.json');committed=w.read(folder/'committed.json')
    assert all(w.sha(ROOT/p)==vv for p,vv in committed['outputs'].items())
    assert a['fit_row_ids_digest']==m.p.b.digest(sorted(f.loc[~f.is_held,'row_id']))
    f['baseline_ultimate']=np.nan
    for held in [False,True]:
        selected=f.is_held.eq(held);u,_=k.forward(f.loc[selected],a,True);f.loc[selected,'baseline_ultimate']=u
    assert np.array_equal(f.loc[f.is_held,'baseline_ultimate'],pd.read_parquet(folder/'prices.parquet').ultimate)
    f['baseline_observed']=f.baseline_ultimate.to_numpy()*f.q_paired.to_numpy()
    rows=pd.read_parquet(HOME/f'rows_s2_{line}.parquet',columns=['row_id'])
    assert rows.row_id.is_unique;positions=pd.Series(np.arange(len(rows)),index=rows.row_id).loc[f.row_id].to_numpy()
    columns=sorted(set(NUM[line]+CAT[line])-{'new_business'})
    cov=pd.read_parquet(HOME/f'matrix_s2_{line}.parquet',columns=columns).iloc[positions].reset_index(drop=True)
    assert len(cov)==len(f)
    for name in columns:f[name]=cov[name].to_numpy()
    return f


def synthetic():
    rng=np.random.default_rng(2026102756);n=480
    f=pd.DataFrame({'row_id':['s'+str(i) for i in range(n)],'group_id':['g'+str(i) for i in range(n)],
        'is_held':np.arange(n)%5==0,'exposure_calendar':rng.uniform(.2,1,n),'new_business':np.arange(n)%2})
    f['baseline_ultimate']=np.exp(rng.normal(4,.4,n))*f.exposure_calendar;f['q_paired']=rng.uniform(.5,1,n)
    f['baseline_observed']=f.baseline_ultimate*f.q_paired
    f['T0']=f.baseline_observed*rng.gamma(2,.5,n)*(rng.random(n)<.6);f['reserve']=0.
    records=[]
    for line in m.q.LINES:
        z=f.copy()
        for name in NUM[line]:z[name]=rng.choice([0.,10.,100.,np.nan],n)
        for name in CAT[line]:
            if name!='new_business':z[name]=rng.choice(['a','b','c'],n)
        folder=OUT/'synthetic_members'/line
        a=m.once(folder,'primary',lambda:fit(z,line,folder/'primary_model_raw.json'))
        b=m.once(folder,'adverse',lambda:fit(poison(z,line),line,folder/'adverse_model_raw.json'));assert a==b
        assert not a['warnings'] and a['gradient_inf']<1e-5
        held=z.loc[z.is_held];u,rel=forward(held,a);uu,rr=forward(held,json.loads(json.dumps(a)))
        assert np.array_equal(u,uu) and np.array_equal(rel,rr)
        # Independent scalar predictor and objective at several different monetary scales.
        x,_=design(held,line,a['preprocess'])
        scalar=np.array([math.exp(math.fsum(float(c)*float(xx) for c,xx in zip(a['coef'],row))+a['intercept']) for row in x])
        assert np.allclose(scalar,rel,rtol=2e-13,atol=2e-13)
        for scale in [.01,1.,100.]:
            y=held.T0.to_numpy(float)*scale;base=held.baseline_observed.to_numpy(float)*scale
            assert np.allclose(m.e.unit(y,base*rel),np.sqrt(base)*m.e.unit(y/base,rel),rtol=2e-12,atol=1e-10)
        records.append({'line':line,'held_payload_invariance':True,'serialization_exact':True,'scalar_linear_predictor':True,'gradient_inf':a['gradient_inf']})
    return {'author':'Codex','utc':utc(),'records':records,'homogeneity_three_currency_scales':True,
        'synthetic_primary_GLM_fits':3,'synthetic_adverse_GLM_fits_separate':3,'real_GLM_fits':0,'new_C0_fits':0,'new_scores':0}


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent=w.read(v.PLAN);assert w.read(v.OUT/'completion_receipt.json')['report_sha256']==w.sha(v.OUT/'report.json')
    assert not w.read(v.OUT/'report.json')['all_pooled_gates_pass'];m.check_sources(parent)
    OUT.mkdir();(OUT/'preflight_code.py').write_bytes(Path(__file__).read_bytes())
    dump(OUT/'synthetic.json',synthetic());bindings=[]
    for line in m.q.LINES:
        for outer in range(5):
            f=frame_for(line,outer);f.to_parquet(OUT/f'input_{line}_{outer}.parquet',index=False)
            train=f.loc[~f.is_held];assert set(train.group_id).isdisjoint(set(f.loc[f.is_held,'group_id']))
            bindings.append({'line':line,'outer':outer,'rows':len(f),'training_rows':len(train),'held_rows':int(f.is_held.sum()),
                'input_sha256':w.sha(OUT/f'input_{line}_{outer}.parquet'),'baseline_train_application_separate_from_held_covariates':True})
    dump(OUT/'bindings.json',bindings)
    paths=[Path(__file__),v.PLAN,v.OUT/'report.json',v.OUT/'replay_report.json',v.OUT/'completion_receipt.json',
        OUT/'synthetic.json',OUT/'bindings.json',R/'docs/semana2/F02_SEMANTICA_Y_DISPONIBILIDAD_2023.md']
    paths+=list(OUT.glob('input_*.parquet'))
    for line in m.q.LINES:paths += [HOME/f'rows_s2_{line}.parquet',HOME/f'matrix_s2_{line}.parquet']
    for outer in range(5):
        for line in m.q.LINES:
            folder=v.OUT/f'{line}_{outer}';paths += [folder/'learning.json',folder/'committed.json']
    sources=dict(parent['sources']);sources.update({w.rel(p):w.sha(p) for p in paths})
    plan={'author':'Codex','utc':utc(),'need':'P55fixed mixture remains below reference in all5folds/bothyears, including +/-5percentlevel sensitivity and NBcohorts. Current target rules only adjust NCB/prior,business and a few residual categories. A regularized main-effects GLMtests transport of supplied underwriting attributes without new trees, blending weights or capital repair.',
        'hypothesis':'Training-only penalized main effects and a source-risk slope may correct emerging-vs-developed effects omitted by fixed source transport and existing cell rules. This is a testable hypothesis, not a causal finding or established gain.',
        'base':'Exact saved P55whole fixed-half model with matching outer-training ancestry. Its ultimate train predictions and held application are computed SEPARATELY, so held covariates do not enter training normalizers. The original reference remains comparator. Production would fit this same base and then one GLMperline on all known targettraining, not average5GLMs.',
        'model':PARAMS,'numeric':NUM,'categorical':CAT,'additional_numeric':'log(P55ultimate/calendar), standardized training-only; its coefficient is a relative-risk slope adjustment, never a public-derived exponent.',
        'preprocessing':'Numeric>=0 log1p except logannualrisk; missing values median from training only plus missing flags. Train mean/std, zero std->1. Full onehot categories seen ONLY in training; missing category explicit, unknown->allzero. No interactions, cap, target encoding, field selection or hyperparameter search.',
        'offset_identity':'For Tweedie p=1.5, D(y,b*expeta)=sqrt(b)*D(y/b,expeta). Fit normalizedtarget y/b with weights sqrt(b), using b=P55ultimate*q. This includes calendar/q ONCE. Penalized sklearnobjective uses mean weighted halfdeviance plusalpha/2*||beta||^2; intercept unpenalized. Actual unit-loss identity and independent gradient checked.',
        'convergence':'max_iter1000,tol1e-7, no automatic solver retry. Save coefficients BEFORE controls. Any warning, nonfinite value or gradient_inf>=1e-5prevents admission and requires explicit reconciliation.',
        'availability':'Supplied period underwriting attributes are CONDITIONALcompetition inputs, not certified as-of quote snapshots. Construction/occupancy/smoke alarms/excess inherit F02conditions. No days_unoccupied, dynamic payment/history windows, premium, capitalrepair/log_si, future climate, target proxies or IDs as features. Frozen source ancestors retain their documented availability limits; omission here does not erase them.',
        'current_budget':{'synthetic_primary_GLM_fits':3,'synthetic_adverse_GLM_fits_separate':3,'real_GLM_fits':0,
            'saved_baseline_new_training_applications':15,'saved_baseline_held_replays':15,'new_source_fits':0,'new_C0_fits':0,'new_scores':0,'new2025inference':0,'new_submissions':0},
        'future_validation':'Separate preregistration/commit/forum before15primary+15adverse real GLMfits. Reuse P55/P50scope ancestors and exact scenario branches; same whole global/cohort/family16/scenario/level/influence/transfer guards, no relaxation or point-only admission. No re-fit P55base during outerevaluation. Pooled failure rejects; pooledpass requires own conditional transfer whole learning including new GLM.',
        'acceptance':{q:parent[q] for q in ['criteria','bootstrap','cohort_guard','level_sensitivity']},'sources':sources,
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);text='# P56: GLM estándar sobre offset completo, preflight\n\nCodex, '+utc()+'. Se prepara un GLM Tweedie1,5con enlace log y L2=1, sin búsqueda de hiperparámetros. El objetivo conserva T0y la predicción P55funciona como offset completo. La homogeneidad D(y,b·m)=√b·D(y/b,m) evita duplicar exposición o C0.\n\n'
    text+='Pasaron tres GLM sintéticos primarios y tres adversos, etiquetas y atributos retenidos alterados, serialización, predictor escalar, tres escalas monetarias y gradiente independiente. Los15ámbitos reales se enlazaron sin ajustar precios: la base de entrenamiento se aplica aparte de los retenidos. Se guardaron coeficientes sintéticos antes de controles.\n\n'
    text+='Efectos principales predefinidos de suscripción y pendiente del riesgo fuente; sin interacciones, selección de campos, cambios de peso o árboles. Se excluyen primas, capital reparado, clima futuro y desocupación sin ventana clara. Los atributos suministrados siguen siendo condicionales, sin certificar su disponibilidad en una cotización histórica; los límites de ancestros fuente permanecen.\n\n'
    text+='Cero ajustes GLM reales, C0, scores o envíos. Falta registrar y ejecutar la comparación completa bajo todas las guardas originales y transferencia propia si corresponde. B00/F3c/adversos conservados;2024abierto adaptativo, privada prioritaria.\n\nPlan: '+w.rel(PLAN)+' SHA '+w.sha(PLAN)+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':'P56offset_GLM_synthetic_and_real_input_preflight_passed','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),'document':w.rel(DOC),
        'real_GLM_fits':0,'new_C0_fits':0,'new_scores':0,'new2025inference':0,'new_submissions':0,
        'next_unit':'P57: preregister and commit complete P56offset GLMvalidation,15primary+15adverse fits, same unchanged gates/scenarios and whole conditional transfer requirement. No source/P55base/C0refits or public tuning. Keep convergence controls and actual train-only preprocess/offset ancestry.',
        'forum':m.q.post(body,'COD-S2-20261027-PRIVADA-P56-GLM-PREFLIGHT','P56: GLM estándar con offset, matemática y flujo sintético antes de ajustar')}
    dump(INDEX,receipt);dump(OUT/'completion_receipt.json',receipt)
    archive=R/'privado'/('corte_P56_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir()
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P56'),(R/'registro/semana2_mision_privada_actual.json','P56')]:w.update(path,{key:receipt,'next_unit':receipt['next_unit']},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P56=receipt,next_unit=receipt['next_unit']);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    w.update(R/'registro/semana2_contadores_propios_actual.json',{'phase2_private_P56_offset_preflight':w.read(OUT/'synthetic.json')},archive)
    note='\n\n## Privada P56: GLM estándar con offset, preflight\n\nCodex, '+receipt['utc']+'.3GLMsintéticos primarios/3adversos, homogeneidad/gradiente/replay y15enlaces reales pasaron. Cero GLMreal/C0/score/envío. Informe: '+w.rel(DOC)+'. Próximo: '+receipt['next_unit']+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_offset_GLM_preflight_index':w.rel(INDEX),'week_2_private_offset_GLM_preflight_report':w.rel(DOC)},archive)
    print(json.dumps({'preflight':'passed','real_GLM_fits':0,'bindings':15,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['prepare']);p.parse_args()
    with m.e.threadpool_limits(limits=2):prepare()
