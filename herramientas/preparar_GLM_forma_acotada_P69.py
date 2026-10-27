"""Preflight: GLM de forma con respuesta acotada y nivel con coste íntegro."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import argparse
import math
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p69_existing_current_GLM',R/'herramientas/validar_GLM_reporte_actual_P67.py')
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
g=p.g;m=p.m;q=p.q;w=p.w;pd=p.pd;np=p.np;BASE=p.BASE
ORIGINAL_FIT=g.fit;ORIGINAL_FORWARD=g.forward;ORIGINAL_MATH=p.driver.independent_math
OUT=BASE/'P69_GLM_forma_acotada_preflight_20261027'
PLAN=R/'registro/semana2_GLM_forma_acotada_preflight_plan.json';INDEX=R/'registro/semana2_GLM_forma_acotada_preflight_actual.json'
DOC=R/'docs/semana2/PRIVADA_P69_GLM_FORMA_ACOTADA_PREFLIGHT.md'
CAP_QUANTILE=.995


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)


def fit(frame,line,checkpoint=None):
    # Select training keys BEFORE reading any target or supplied raw/offset payload.
    mask=~frame.is_held;train=frame.loc[mask].copy();y=train.T0.to_numpy(float)
    assert np.isfinite(y).all() and (y>=0).all() and (y>0).any()
    cap=float(np.quantile(y[y>0],CAP_QUANTILE));assert cap>0
    shaped=frame.copy();shaped.loc[mask,'T0']=np.minimum(y,cap)
    artifact=ORIGINAL_FIT(shaped,line,checkpoint=checkpoint)
    ultimate,_=ORIGINAL_FORWARD(train,artifact);observed=ultimate*train.q_paired.to_numpy(float)
    numerator=float(np.sum(y/np.sqrt(observed)));denominator=float(np.sum(np.sqrt(observed)));level=numerator/denominator
    assert math.isfinite(level) and level>0
    result={**artifact,'response_shape_contract':'T0 capped ONLYin shape fitting at training-positiveT0p995; all original rows retained. Evaluation and final level use original uncappedT0.',
        'shape_cap_quantile':CAP_QUANTILE,'shape_cap_value':cap,'shape_clipped_rows':int((y>cap).sum()),'shape_training_rows':len(y),
        'uncapped_level':level,'uncapped_level_numerator':numerator,'uncapped_level_denominator':denominator,
        'uncapped_training_target_digest':m.p.b.digest(y.tolist()),'source_base_and_reporting_uncapped':True}
    if checkpoint is not None:dump(checkpoint.with_name(checkpoint.stem+'_shape_level.json'),{key:result[key] for key in result if key not in ['coef','preprocess']})
    return result


def forward(frame,artifact):
    ultimate,relative=ORIGINAL_FORWARD(frame,artifact);level=artifact['uncapped_level']
    return ultimate*level,relative*level


def independent_math(train,artifact):
    shaped=train.copy();shaped['T0']=np.minimum(train.T0.to_numpy(float),artifact['shape_cap_value'])
    raw=ORIGINAL_MATH(shaped,artifact)
    ultimate,_=ORIGINAL_FORWARD(train,artifact);mu=ultimate*train.q_paired.to_numpy(float);y=train.T0.to_numpy(float)
    top=math.fsum((y/np.sqrt(mu)).tolist());bottom=math.fsum(np.sqrt(mu).tolist());scalar=top/bottom
    assert math.isclose(scalar,artifact['uncapped_level'],rel_tol=3e-12)
    final=mu*artifact['uncapped_level'];derivative=math.fsum((np.sqrt(final)-y/np.sqrt(final)).tolist())
    assert abs(derivative)<=1e-11*math.fsum(np.sqrt(final).tolist())
    value,_=forward(train,artifact);assert np.array_equal(value,ultimate*artifact['uncapped_level'])
    return {'shape_objective_gradient_checks':raw,'uncapped_level_independent_scalar':scalar,'uncapped_level_log_derivative':derivative,
        'uncapped_objective_level_optimal_for_fixed_shape':True,'does_not_claim_uncapped_joint_GLM_gradient_optimum':True}


def synthetic():
    rng=np.random.default_rng(2026102769);n=600;records=[]
    for line in q.LINES:
        i=np.arange(n);base=np.exp(rng.normal(5,.4,n));y=np.round(rng.gamma(2,120,n)*(rng.random(n)<.35),2)
        y[7]=100000.;y[37]=50000.
        f=pd.DataFrame({'row_id':['s'+str(j) for j in i],'group_id':['g'+str(j) for j in i],'is_held':i%5==0,'fold':i%5,'year':2023+(i//5)%2,
            'new_business':(i//10)%2,'T0':y,'reserve':0.,'baseline_ultimate':base,'baseline_observed':base*.8,'q_paired':.8,'exposure_calendar':1.})
        for name in g.NUM[line]:f[name]=rng.choice([0.,10.,100.],n)
        for name in g.CAT[line]:
            if name!='new_business':f[name]=rng.choice(['a','b','c'],n)
        folder=OUT/'synthetic'/line
        a=m.once(folder,'primary',lambda:fit(f,line,folder/'primary_raw.json'));b=m.once(folder,'adverse',lambda:fit(g.poison(f,line),line,folder/'adverse_raw.json'));assert a==b
        assert a['shape_clipped_rows']>0 and not a['warnings'] and a['gradient_inf']<1e-5
        checks=independent_math(f.loc[~f.is_held],a);held=f.loc[f.is_held].copy();value,relative=forward(held,a)
        poisoned=held.copy();poisoned[['T0','reserve','baseline_observed','q_paired']]=np.nan
        replay,rr=forward(poisoned,json.loads(json.dumps(b)));assert np.array_equal(value,replay) and np.array_equal(relative,rr)
        # Preserve the original training target separately from the shape response.
        assert a['uncapped_training_target_digest']==m.p.b.digest(f.loc[~f.is_held,'T0'].to_numpy(float).tolist())
        records.append({'line':line,'shape_cap':a['shape_cap_value'],'shape_clipped_rows':a['shape_clipped_rows'],'uncapped_level':a['uncapped_level'],
            'held_all_payload_poison_fit_invariant':True,'held_labels_q_observed_offset_not_used_by_ultimate':True,'JSON_replay_exact':True,'independent_math':checks})
    return {'author':'Codex','utc':utc(),'records':records,'synthetic_primary_GLMfits':3,'synthetic_adverse_GLMfits_separate':3,
        'synthetic_primary_positive_quantiles':3,'synthetic_adverse_positive_quantiles_separate':3,'synthetic_primary_uncapped_levels':3,'synthetic_adverse_uncapped_levels_separate':3,
        'new_real_fits':0,'new_scores':0,'new_submissions':0}


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    diag=BASE/'P68_GLM_actual_guardado_20261027';assert w.read(diag/'completion_receipt.json')['report_sha256']==w.sha(diag/'report.json')
    parent=w.read(p.PLAN);m.check_sources(parent);inputs=p.verify_inputs()
    paths=[Path(__file__),Path(g.__file__),Path(p.driver.__file__),p.PLAN,p.OUT/'report.json',p.OUT/'input_report.json',p.OUT/'completion_receipt.json',
        diag/'report.json',diag/'completion_receipt.json',R/'registro/semana2_mision_privada_plan_v1.json']
    sources={**parent['sources'],**inputs['outputs']};sources.update({w.rel(path):w.sha(path) for path in paths})
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'scope':'Synthetic shape/uncapped-level preflight plus exact15existing P67input bindings. ZEROnew real base/report/GLMfit or price score.',
        'need':'P68shows current GLMimproves15/15OOFtraining scopes but6/15held; buildings positive-cost top.5percent carries16-20percent training cost. Contributions are descriptive and do NOTestablish a causal explanation or the success of truncating shape responses.',
        'hypothesis':'A response-bounded GLMshape may learn less from extreme training cost marks, while a separate exact uncapped Tweedie-optimal level retains all original cost information. Test uniformly across3lines, no chosen peril/cell, field pruning, alpha search or public-score tuning.',
        'configuration':{'shape_response':'min(originalT0,positive training originalT0p995), computed after training key exclusion, all rows kept; qand OOFoffsets unchanged.',
            'cap_quantile':CAP_QUANTILE,'quantile_scope':'Each actual outer-training GLMscope only; no held targets or pooled-outer cap borrowing. Source/base/CDFfits remain original uncapped objects.',
            'fields_numeric':g.NUM,'fields_categorical':g.CAT,'GLMparameters':g.PARAMS,
            'uncapped_level':'With shape observed mu0=b*exp(Xbeta), c=sum(originaly/sqrt(mu0))/sum(sqrt(mu0)). Final ultimate=baseultimate*exp(Xbeta)*c; nominal observed=ultimate*ownq. Same level also applies to held/prod, no held recalibration.',
            'evaluation':'Original uncappedT0and every previous scenario/cohort/global guard. Quantile affects only shape estimation; no changed official target, prices capped at prediction, deleting large claims, clipping validation labels or complete-model bounded-influence theorem.'},
        'future_budget':{'primary_GLMshape_fits':15,'adverse_GLMshape_fits_separate':15,'primary_shape_quantiles':15,'adverse_shape_quantiles_separate':15,
            'primary_uncapped_closed_levels':15,'adverse_uncapped_closed_levels_separate':15,'new_base_fits':0,'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0},
        'future_flow':'Reuse exact P67protected crossfit numeric inputs/inner report/base artifacts: those ancestors do not depend on final GLMshape rule. Fit only new final GLMshapes and uncapped levels. Full production would retain own five inner folds, own reports/bases and this final learner. Pooled pass still needs OWNconditional transfer before admission.',
        'preflight_criterion':'Actual primary/adverse fit equality after ALLheld payload corruption before preprocessing/quantile, saved raw shape before controls, raw-shape objective/gradient by scalar method, independent uncapped-level sums and zero scalar derivative, ultimate ignores held labels/q/observedoffset, JSONexact, no changed real inputs.',
        'future_criterion':'All unchanged P67gates including raw-shape convergence plus uncapped-level math. Failed gates remain failed, no per-line/cell rescue. No joint uncapped GLMstationary-point claim after two-stage estimation.',
        'limits':['The final scalar level remains sensitive to all uncapped costs by design; parent base/reporting also remain sensitive. This only limits final shape response contribution for fixed covariates/offsets, not all leverage or whole pipeline influence.',
            'Finite-tail sample, fixedp995heuristic and level/shape tradeoff may lose useful information. No expected improvement guaranteed.',
            'Adaptive2023/2024, source2024conditional, proxy/market/valuation/ultimate-tail and training-size/normalizer limitations persist.'],
        'sources':sources,'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. P69registra antes de ajustar una propuesta sencilla frente al falloP67: misma forma GLM/campos/alpha1, solo respuesta de AJUSTEde forma acotada ap995de costes positivos de su entrenamiento; después nivel óptimo Tweediecon TODOel T0original sin acotar. Todas las filas, objetivos de evaluación y precios finales íntegros. Elq/baseOOFse reutiliza P67por SHAporque no depende del GLMfinal. P68motiva revisar la cola pero no prueba causalidad o mejora; se aplica uniformemente, sin rescatar ramos. Preflight sintético3+3GLM/3+3cuantiles/3+3niveles y15entradas reales sin nuevo ajuste real. El nivel y los ancestros siguen sensibles a la cola; no se afirma robustez global acotada. Antes de probar real habrá otra inscripción con todas las guardas intactas. B00conservado,2024abierto adaptativo y cero2025/envíos. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P69registered_before_response_bounded_shape_preflight','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P69-FORMA-PREVIO','P69: forma con respuesta acotada y nivel íntegro, antes de probar')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def run():
    assert not (OUT/'report.json').exists();plan=w.read(PLAN);m.check_sources(plan);assert w.read(OUT/'registration.json')['plan_sha256']==w.sha(PLAN)
    dump(OUT/'synthetic.json',synthetic());bindings=[]
    for line in q.LINES:
        for outer in range(5):
            f=p.frame_for(line,outer);assert f.year.isin([2023,2024]).all() and np.array_equal(f.is_held,f.fold.eq(outer))
            assert set(f.loc[~f.is_held,'group_id']).isdisjoint(set(f.loc[f.is_held,'group_id']))
            assert f.baseline_ultimate.gt(0).all() and f.baseline_observed.gt(0).all() and f.q_paired.gt(0).all()
            bindings.append({'line':line,'outer':outer,'rows':len(f),'input_sha256':w.sha(p.OUT/f'input_{line}_{outer}.parquet'),'unchanged_original_T0_and_OOFoffsets':True})
    m.check_sources(plan);dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P69shape_uncapped_level_synthetic_and_bindings_passed','plan_sha256':w.sha(PLAN),'bindings':bindings,
        'new_real_fits':0,'new_base_fits':0,'new_source_fits':0,'new_CDF_fits':0,'new_scores':0,'new2025inference':0,'new_submissions':0})
    print(json.dumps({'preflight':'passed','bindings':15,'new_real_fits':0,'new_scores':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();d=w.read(OUT/'report.json');m.check_sources(w.read(PLAN))
    next_unit='P70: register and commit exact P69two-stage GLMshape/uncapped level,15primary+15adverse GLMshape/quantile/level calls, using byte-identical P67OOFinputs. ZEROnew base/report/source fits. Every original gate plus raw-shape convergence/uncapped-level math, no target or threshold rescue; pooled pass requires OWNconditional transfer before CSV.'
    text='# P69: forma con respuesta acotada y nivel íntegro\n\nCodex, '+utc()+'. La propuesta conserva el GLM/campos/alpha1yacota únicamente la respuesta del ajuste de forma al percentil99,5de costes positivos de su entrenamiento. Después calcula un nivel óptimo Tweediecon todos los costes originales. El objetivo de evaluación, todas las filas y los precios finales quedan íntegros. No se atribuye la pérdidaP67causalmente a la cola ni se garantiza mejorar.\n\n'
    text+='Pasaron3GLMprimarios/3adversos sintéticos, con cuantiles y niveles propios, después de alterar TODOSlos datos/offsets/covariables retenidos. La forma se contrastó por objetivo/gradiente escalar; el nivel por otras sumas y derivada cero del objetivo íntegro con forma fija. ReplayJSONexacto, sin usar etiquetas/q/offsetobservado retenidos en último. Se enlazaron las15entradas realesP67sin cambiarlas ni ajustar sobre ellas.\n\n'
    text+='El nivel final y los ancestros base/reporte conservan sensibilidad al coste íntegro; no es un estimador global de influencia acotada. Se reutilizan los controlesP67de sus ancestros, no se repiten curvas o bases. Cero ajustes reales, puntuaciones nuevas,2025o envíos. B00/F3cyalternativas conservados;2024abierto adaptativo, privada prioritaria y sin validación independiente.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'synthetic.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'next_unit':next_unit,
        'new_real_fits':0,'new_base_fits':0,'new_CDF_fits':0,'new_scores':0,'new_submissions':0,'2024_open':True,'goal_achieved':False,
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P69-FORMA-RESULTADO','P69: forma acotada y nivel íntegro, preflight sin ajuste real')}
    archive=R/'privado'/('corte_P69_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir();w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P69'),(R/'registro/semana2_mision_privada_actual.json','P69')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    cp=R/'registro/semana2_contadores_propios_actual.json';w.update(cp,{'phase2_private_P69_bounded_response_preflight':{**receipt,'synthetic':w.read(OUT/'synthetic.json')}},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P69=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P69: forma acotada y nivel íntegro\n\nCodex, '+receipt['utc']+'.Preflight sintético y15enlaces existentes pasaron; cero ajuste real/scoring/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_bounded_shape_GLM_preflight_index':w.rel(INDEX),'week_2_private_bounded_shape_GLM_preflight_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'new_real_fits':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['register','run','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'register':register,'run':run,'close':close}[args.mode]()
