"""Selección interna finita de regularización para el mismo GLM P82."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import argparse
import math
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p84_same_band_GLM',R/'herramientas/preparar_GLM_bandas_negocio_P81.py')
k=importlib.util.module_from_spec(s);s.loader.exec_module(k)
m=k.m;q=k.q;w=k.w;pd=k.pd;np=k.np;BASE=k.BASE
OUT=BASE/'P84_seleccion_GLM_preflight_20261027'
PLAN=R/'registro/semana2_seleccion_GLM_interna_preflight_plan.json';INDEX=R/'registro/semana2_seleccion_GLM_interna_preflight_actual.json'
DOC=R/'docs/semana2/PRIVADA_P84_SELECCION_GLM_INTERNA_PREFLIGHT.md'
INNER=BASE/'P67_validacion_GLM_reporte_actual_20261027'
PROXY=BASE/'P61_proxy_observacion_20261027'
GRID=[1.,.1,.01]
ORIGINAL_NATIVE_FIT=k.r.TweedieRegressor.fit


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)


def fit_alpha(frame,line,alpha,folder):
    folder.mkdir(parents=True,exist_ok=True)
    def produce():
        params=k.r.PARAMS;k.r.PARAMS={**params,'alpha':alpha}
        def native(self,*args,**kwargs):
            marker=folder/'actual_fit_invoked.json';assert not marker.exists()
            dump(marker,{'author':'Codex','utc':utc(),'alpha':alpha,'actual_native_fit':True})
            return ORIGINAL_NATIVE_FIT(self,*args,**kwargs)
        k.r.TweedieRegressor.fit=native
        try:
            artifact=k.fit(frame,line,folder/'raw.json')
            artifact['independent_math']=k.independent_math(frame.loc[~frame.is_held],artifact)
            return artifact
        finally:k.r.PARAMS=params;k.r.TweedieRegressor.fit=ORIGINAL_NATIVE_FIT
    artifact=m.once(folder,'artifact',produce)
    assert artifact['parameters']['alpha']==alpha
    assert artifact['fit_row_ids_digest']==m.p.b.digest(sorted(frame.loc[~frame.is_held,'row_id']))
    return artifact


def inner_frames(frames,tables):
    result={}
    for line,raw in frames.items():
        # Exclude outer protected payload BEFORE numeric/type conversion or inner banding.
        f=raw.loc[~raw.is_held].copy().reset_index(drop=True);table=tables[line].set_index('row_id')
        assert table.index.is_unique and set(table.index)==set(f.row_id)
        z=table.loc[f.row_id];assert np.array_equal(z.year,f.year) and np.array_equal(z.group_id,f.group_id)
        f['q_paired']=z.q_paired.to_numpy(float);f['is_held']=z.is_held.to_numpy(bool)
        assert set(f.loc[f.is_held,'group_id']).isdisjoint(set(f.loc[~f.is_held,'group_id']))
        assert f.q_paired.gt(0).all() and f.q_paired.le(1+1e-10).all();result[line]=f
    return result


def choose(losses):
    assert len(losses)==len(GRID) and np.isfinite(losses).all()
    best=min(losses);tolerance=1e-12*max(1.,abs(best))
    # GRIDdescending: exact/roundoff ties favor the stronger regularization.
    index=next(j for j,value in enumerate(losses) if value<=best+tolerance)
    return {'index':index,'alpha':GRID[index],'losses':list(losses),'tie_tolerance':tolerance,'criterion':'minimum total original-T0 Tweedie15deviance over ALLinner-held rows/lines, common alpha'}


def validation_loss(frame,artifact):
    held=frame.loc[frame.is_held];clean=held.drop(columns=['T0','reserve','q_paired'])
    ultimate,_=k.forward(clean,artifact);pred=ultimate*held.q_paired.to_numpy(float);y=held.T0.to_numpy(float)
    vector=float(m.e.unit(y,pred).sum())
    scalar=math.fsum((4*y/np.sqrt(pred)+4*np.sqrt(pred)-8*np.sqrt(y)).tolist())
    assert math.isclose(vector,scalar,rel_tol=4e-12,abs_tol=1e-7)
    return scalar


def train_bundle(frames,scope_tables,folder):
    totals=[0.]*len(GRID);inner_models={};fits=[]
    for member in range(5):
        scoped=inner_frames(frames,scope_tables[member]);inner_models[str(member)]={}
        for line in q.LINES:
            models=[]
            for j,alpha in enumerate(GRID):
                model=fit_alpha(scoped[line],line,alpha,folder/f'i{member}'/f'a{j}'/line)
                totals[j]+=validation_loss(scoped[line],model);models.append(model);fits.append(model)
            inner_models[str(member)][line]=models
    selection=choose(totals);final={}
    for line in q.LINES:
        final[line]=fit_alpha(frames[line],line,selection['alpha'],folder/'final'/line);fits.append(final[line])
    return {'selection':selection,'inner_models':inner_models,'models':final,
        'all_native_fits_converged':all(not a['warnings'] and a['gradient_inf']<1e-5 for a in fits),
        'actual_GLMfit_count':len(fits),'contract':'P84five-inner-common-alpha-selection_then_one_GLMperline_sameP82fields_prior'}


def replay_bundle(frames,tables,bundle):
    totals=[0.]*len(GRID)
    for member in range(5):
        scoped=inner_frames(frames,tables[member])
        for line in q.LINES:
            for j in range(len(GRID)):totals[j]+=validation_loss(scoped[line],bundle['inner_models'][str(member)][line][j])
    assert choose(totals)==bundle['selection']
    return {line:k.forward(frames[line].loc[frames[line].is_held].drop(columns=['T0','reserve','q_paired']),bundle['models'][line])[0] for line in q.LINES}


def synthetic_inputs():
    rng=np.random.default_rng(2026102784);frames={};tables={member:{} for member in range(5)};n=600;i=np.arange(n)
    for line in q.LINES:
        f=pd.DataFrame({'row_id':[line+'s'+str(j) for j in i],'line':line,'group_id':['sharedgroup'+str(j) for j in i],
            'is_held':i%5==0,'fold':i%5,'year':2023+(i//5)%2,'new_business':(i//10)%2,
            'T0':rng.gamma(2,80,n)*(rng.random(n)<.4),'reserve':0.,'exposure_calendar':rng.uniform(.1,1,n),'q_paired':rng.uniform(.3,1,n),
            'annual_A1S':np.exp(rng.normal(0,.4,n)),'annual_T2b':np.exp(rng.normal(5,.5,n))})
        for name in k.BASE_NUM[line]:f[name]=rng.choice([0.,10.,100.],n)
        for name in k.BASE_CAT[line]:
            if name!='new_business':f[name]=rng.choice(['a','b','c'],n)
        f['prior_claims_5y']=rng.choice([0.,1.,2.,np.nan],n)
        if line=='motor':f['ncb_years']=rng.choice([0.,1.,2.,3.,5.,6.,9.,10.,np.nan],n)
        for member in range(5):
            z=f.loc[~f.is_held,['row_id','year','group_id','q_paired']].copy();z['is_held']=((i[~f.is_held]//5)%5)==member
            z['q_paired']*=.95+.01*member;tables[member][line]=z
        frames[line]=f
    return frames,tables


def synthetic():
    frames,tables=synthetic_inputs();folder=OUT/'synthetic'
    primary=m.once(folder,'primary',lambda:train_bundle(frames,tables,folder/'primary_fits'))
    poisoned={line:k.poison(frame,line) for line,frame in frames.items()}
    adverse=m.once(folder,'adverse',lambda:train_bundle(poisoned,tables,folder/'adverse_fits'))
    assert primary==adverse and primary['actual_GLMfit_count']==48 and primary['all_native_fits_converged']
    before=k.r.TweedieRegressor.fit
    def reject(*args,**kwargs):raise AssertionError('P84synthetic replay prohibits all native GLMfits')
    k.r.TweedieRegressor.fit=reject
    try:
        first=replay_bundle(frames,tables,primary);second=replay_bundle(frames,tables,json.loads(json.dumps(adverse)))
        assert all(np.array_equal(first[line],second[line]) for line in q.LINES)
    finally:k.r.TweedieRegressor.fit=before
    assert choose([10.,10.+1e-13,10.])['alpha']==1. and choose([12.,10.,11.])['alpha']==.1
    return {'author':'Codex','utc':utc(),'selected_alpha_synthetic_only':primary['selection']['alpha'],'all_outer_payload_poison_selection_and_models_exact':True,
        'all45inner_losses_and_selector_replayed_exact_without_fitting':True,'JSONfinal_predictions_exact':True,'ties_choose_larger_alpha':True,
        'synthetic_primary_GLMfits':48,'synthetic_adverse_GLMfits_separate':48,
        'reporting_limit':'Synthetic qtables are fixed scope fixtures, not newly learned RPLcurves. Actual75bindings separately use pinned protected P67inner numeric CDFobjects and existing ancestry evidence. No claim that this synthetic fixture revalidates all reporting learning.',
        'new_real_fits':0,'new_CDF_fits':0,'new_scores':0,'new2025inference':0,'new_submissions':0}


def bind_real_inputs():
    records=[];outputs={};profiles={line:pd.read_parquet(PROXY/f'FSp_proxy_{line}.parquet').set_index('row_id') for line in q.LINES}
    engine=k.r.p.u
    for outer in range(5):
        frames={line:k.frame_for(line,outer) for line in q.LINES}
        partition_path=m.P1/f'inner_groups_outer{outer}.parquet';partition=pd.read_parquet(partition_path).set_index('group_id').inner_fold
        manifest=w.read(INNER/f'outer{outer}/inputs_committed.json')['outputs']
        previous={}
        for line in q.LINES:
            path=INNER/f'input_{line}_{outer}.parquet';assert manifest[w.rel(path)]==w.sha(path)
            previous[line]=pd.read_parquet(path,columns=['row_id','q_paired']).set_index('row_id')
        for member in range(5):
            report_path=INNER/f'outer{outer}/inner{member}/report_primary.json';assert manifest[w.rel(report_path)]==w.sha(report_path)
            report=w.read(report_path)
            ids={rid for f in frames.values() for rid in f.loc[~f.is_held&f.group_id.map(partition).ne(member),'row_id']}
            assert report['training_row_ids_digest']==m.p.b.digest(sorted(ids))
            for line,raw in frames.items():
                f=raw.loc[~raw.is_held].copy().reset_index(drop=True);assert f.group_id.isin(partition.index).all()
                f['is_held']=f.group_id.map(partition).eq(member)
                proxy=profiles[line].loc[f.row_id];assert np.array_equal(proxy.year,f.year)
                for name in engine.proxy_columns(line):f[name]=proxy[name].to_numpy(float)
                z=engine.with_q(f,line,report)
                check=previous[line].loc[z.loc[z.is_held,'row_id'],'q_paired'].to_numpy(float)
                assert np.allclose(check,z.loc[z.is_held,'q_paired'],rtol=2e-13,atol=1e-14)
                table=z[['row_id','line','year','group_id','q_paired','is_held']].copy()
                path=OUT/'inputs'/f'o{outer}_i{member}_{line}.parquet';path.parent.mkdir(exist_ok=True);table.to_parquet(path,index=False);outputs[w.rel(path)]=w.sha(path)
                records.append({'outer':outer,'member':member,'line':line,'rows':len(table),'report':w.rel(report_path),'report_sha256':w.sha(report_path),
                    'report_training_ids_digest':report['training_row_ids_digest'],'expected_training_ids_digest':m.p.b.digest(sorted(ids)),
                    'new_numeric_q_matches_old_inner_held':True,'all_outer_held_excluded_before_numeric_apply':True,'table':w.rel(path),'table_sha256':w.sha(path)})
    return {'author':'Codex','utc':utc(),'records':records,'outputs':outputs,'new_real_fits':0,'new_CDF_fits':0,'existing_inner_reports_reused':25,'numeric_scope_tables':75}


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    previous=BASE/'P83_penalizacion_guardada_20261027';assert w.read(previous/'completion_receipt.json')['report_sha256']==w.sha(previous/'report.json')
    assert w.read(INNER/'completion_receipt.json')['report_sha256']==w.sha(INNER/'report.json')
    assert w.read(INNER/'replay_report.json')['report_sha256']==w.sha(INNER/'report.json')
    parent=w.read(k.PLAN);m.check_sources(parent)
    paths=[Path(__file__),Path(k.__file__),k.PLAN,previous/'report.json',previous/'completion_receipt.json',k.r.p.PLAN,k.r.p.u.PLAN,Path(k.r.p.u.__file__),
        INNER/'input_report.json',INNER/'report.json',INNER/'replay_report.json',INNER/'completion_receipt.json',R/'registro/semana2_mision_privada_plan_v1.json']
    for outer in range(5):
        paths += [m.P1/f'inner_groups_outer{outer}.parquet',INNER/f'outer{outer}/inputs_committed.json']
        paths += [INNER/f'outer{outer}/inner{member}/report_primary.json' for member in range(5)]
        paths += [INNER/f'input_{line}_{outer}.parquet' for line in q.LINES]
    paths += [PROXY/f'FSp_proxy_{line}.parquet' for line in q.LINES]
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'scope':'New finite train-only selection composition/synthetic whole flow and75strict inner report numeric bindings, no real learning.',
        'need':'P83quantified strong ridge contribution relative to likelihood curvature in the SAMEP82standard GLM; a fixed alpha1may underadapt. Neither diagonal diagnostic nor outer failures identify the best alpha. Learn regularization within training only, instead of choosing it from outer/public scores.',
        'hypothesis':'A bounded common-alpha inner-validation algorithm may balance source-prior adaptation and variance better than one arbitrary fixed penalty, under the same GLM/rating fields/source/target/exposure. No known gain.',
        'configuration':{'grid':GRID,'grid_reason':'Three fixed orders of magnitude including existing alpha1, common for all3lines. No expansion/refinement after inner or outer results.',
            'selector':'Within each outertrain, use all5saved inner globalgroupfolds. Fit each of3alphas perline/inner, minimize TOTALoriginaluncappedT0Tweedie15deviance across all innerheld rows and lines. Single shared alpha perouter. Ties within1e-12*max(1,abs(minloss))choose larger alpha. No weights or alpha perline.',
            'final_learning':'Refit ONEsameP82GLMperline on alloutertraining at chosen commonalpha, own current P64outerreportq. Whole delivered algorithm would repeat internal selection on all admitted training; not a mean of targetfold models.',
            'preprocessing':'Every innerGLMlearns medians/scales/levels on its OWNtrain via unchanged P81kernel AFTERselector; no outerfeaturematrix, price base, labels or preprocess reused.',
            'reporting':'Reuse ONLY25pinned P67inner report objects with own cap/RPLline/peril curves and matched train-IDs. Numerically reapply fixed sourceFSpPROXYprofiles to alloutertrain rows, overwrite outerq before any innerfit. Existing reporting ancestry/poison proofs reused by hash, no claim of new curve fitting or whole source certification.',
            'unchanged':'P82fields/businessbands, source-only monetary halfprior/all3A1Sseeds/persisted anchors, originalT0/calendar, objective, all GLMsettings except training-selected alpha; adaptive2023/2024/sourceconditional limits remain.'},
        'criterion':'Full synthetic48primary/48adverse native fits including45inner+3final perbundle, outerpayloadpoison beforeselector, exact model/selector equality, all45losses replayed from JSONwith native fitting blocked, scalar deviance/tie checks.75actual strict qtables match saved P67heldinner numeric path and exact reporting trainingkeydigest. No metadata-only selector claim.',
        'budget':{'synthetic_primary_GLMfits':48,'synthetic_adverse_GLMfits_separate':48,'new_real_fits':0,'new_source_fits':0,'new_CDF_fits':0,'new_held_outer_scores':0,'new2025inference':0,'new_submissions':0},
        'future_budget':{'primary_inner_GLMfits':225,'primary_final_GLMfits':15,'adverse_inner_GLMfits_separate':225,'adverse_final_GLMfits_separate':15,'new_source_fits':0,'new_target_base_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0},
        'future_criterion':'Separate P85registration/commit before real fits, EVERYunchanged P82outerpredictive/cohort/scenario/family16/level/influence/convergence guard, plus every candidate innerfit convergence. Pooledpass requires OWN2023-only conditionaltransfer with matching own innerreporting before anyCSVadmission. No grid/field/band/line rescue.',
        'sources':{**parent['sources'],**{w.rel(path):w.sha(path) for path in paths}},'limits':parent['limits']+['Finite grid selection uncertainty is part of the whole outer algorithm; cached reporting remains conditional and bootstrap does not integrate all model/search uncertainty.','No best-alpha/private improvement can be inferred from P83curvature. Synthetic qfixtures do not revalidate reporting learning.'],
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md';body.write_text('Codex. P84registra selección interna finita para el MISMOGLMP82: alpha[1,.1,.01], uno común a los3ramos por entrenamiento, elegido con TODOSlos5folds internos guardados por devianceTweedie original; empate numérico favorece mayoralpha. No valor por ramo ni elección por validación exterior/público. Cada ajuste interno rehace preproceso en su train; qinterno usa SOLOobjetosP67concap/CDFpropios y grupos exactos, nunca qexterior. Preflight48+48GLMsintéticos completos (45internos+3finales porbundle), veneno exterior y replay de TODOSlos45objetivos sin ajustar;75enlaces numéricos reales sin fits/CDF. Futura evaluación requeriría240+240GLMreales y todas las guardas originales/transferencia. Sin refinargrid o cambiarcampos tras resultados; B00adversos preservados,2024abierto adaptativo, ceroenvíos. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P84registered_before_inner_selection_synthetic','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P84-SELECTOR-PREVIO','P84: regularización aprendida solo dentro del entrenamiento, antes de probar')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def run():
    assert not (OUT/'report.json').exists();plan=w.read(PLAN);m.check_sources(plan);assert w.read(OUT/'registration.json')['plan_sha256']==w.sha(PLAN)
    dump(OUT/'synthetic.json',synthetic());bindings=bind_real_inputs();dump(OUT/'bindings.json',bindings)
    m.check_sources(plan);dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P84whole_inner_selection_synthetic_and75numeric_bindings_passed',
        'bindings':w.rel(OUT/'bindings.json'),'bindings_sha256':w.sha(OUT/'bindings.json'),'synthetic':w.rel(OUT/'synthetic.json'),'synthetic_sha256':w.sha(OUT/'synthetic.json'),
        'outputs':bindings['outputs'],'new_real_fits':0,'new_CDF_fits':0,'new_scores':0,'new2025inference':0,'new_submissions':0})
    print(json.dumps({'preflight':'passed','inner_numeric_bindings':len(bindings['records']),'synthetic_primary_GLMfits':48,'synthetic_adverse_GLMfits_separate':48,'new_real_fits':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();d=w.read(OUT/'report.json');m.check_sources(w.read(PLAN))
    next_unit='P85: register/commit EXACTP84inner-selected common-alpha whole algorithm,225inner+15finalGLMprimary and sameadverse, no new source/base/CDFfits. All existing outerguards plus inner/final convergence, exact whole selector/model replay. Pooledpass still needs own2023-only conditionaltransfer before CSV. No grid refinement or perline alpha/field/band rescue.'
    text='# P84: selección interna finita de regularización\n\nCodex, '+utc()+'. Se prepara un algoritmo que elige unalpha común para todos los ramos entre1/0,1/0,01usando exclusivamente los cincofolds internos del entrenamiento. Minimiza la suma de devianceTweedie sobre todos los retenidos internos; empates numéricos favorecen mayor penalización. Luego ajusta un GLMpor ramo con todo ese entrenamiento. Se mantienen campos, bandas por negocio, prior fuente, objetivo y calendario; no elección por resultados exteriores o públicos.\n\n'
    text+='Pasaron48ajustes sintéticos primarios/48adversos,45internos y3finales porbundle. Alterar TODOel payload exterior antes del selector no cambió selección o modelos; JSONreprodujo los45objetivos internos, el selector y predicciones finales con aprendizaje nativo bloqueado. Cada preproceso se aprende en su propio entrenamiento. Los q sintéticos son fixtures fijos, no curvas RPLreestimadas.\n\n'
    text+='Se prepararon75tablas de q internas desde25objetosP67pinnados, cotejando los grupos exactos de aprendizaje del reporte y el enlace numérico completo con los retenidos internos guardados. Nunca se reutilizó qexterior para elegiralpha; no se cargaron bases de precio P67o modelos nuevos de fuente. La prueba de aprendizaje del reporte es evidencia histórica porSHA, no una nueva auditoría completa. Cero ajustes reales/CDF/scores exteriores/2025/envíos.\n\n'
    text+='La futura evaluación cuesta240GLMprimarios/240adversos y conserva todas las guardas, incluida convergencia de cada candidato interno y transferencia propia si pasa combinado. No hay mejoralpha real, mejora privada o CSVadmitido. B00/F3cyalternativas preservados,2024abierto adaptativo; fuente/snapshots/cola/reservas y búsqueda adaptativa limitan la interpretación, sin revisión independiente.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'synthetic.json')+'; '+w.rel(OUT/'bindings.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'next_unit':next_unit,
        'new_real_fits':0,'new_source_fits':0,'new_CDF_fits':0,'new_scores':0,'new_submissions':0,'2024_open':True,'goal_achieved':False,
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P84-SELECTOR-RESULTADO','P84: selector numérico protegido y entradas internas, sin ajuste real')}
    archive=R/'privado'/('corte_P84_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir();w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P84'),(R/'registro/semana2_mision_privada_actual.json','P84')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    cp=R/'registro/semana2_contadores_propios_actual.json';w.update(cp,{'phase2_private_P84_inner_selection_preflight':{**receipt,'synthetic':w.read(OUT/'synthetic.json')}},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P84=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P84: selección interna de regularización, preflight\n\nCodex, '+receipt['utc']+'.48+48GLMsintéticos,75enlaces numéricos internos, cero ajustes reales/CDF/scoring exterior/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_inner_selection_preflight_index':w.rel(INDEX),'week_2_private_inner_selection_preflight_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'new_real_fits':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['register','run','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'register':register,'run':run,'close':close}[args.mode]()
