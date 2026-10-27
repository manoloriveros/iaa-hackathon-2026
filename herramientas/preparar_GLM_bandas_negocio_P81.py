"""Mismo GLM y prior fijo; representa historia/NCB con bandas por negocio."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import argparse
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p81_fixed_two_source_prior',R/'herramientas/preparar_GLM_prior_dos_fuentes_P76.py')
b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
r=b.r;m=b.m;q=b.q;w=b.w;pd=b.pd;np=b.np;BASE=b.BASE
OUT=BASE/'P81_GLM_bandas_negocio_preflight_20261027'
PLAN=R/'registro/semana2_GLM_bandas_negocio_preflight_plan.json';INDEX=R/'registro/semana2_GLM_bandas_negocio_preflight_actual.json'
DOC=R/'docs/semana2/PRIVADA_P81_GLM_BANDAS_NEGOCIO_PREFLIGHT.md'
BASE_NUM={line:list(r.NUM[line]) for line in q.LINES};BASE_CAT={line:list(r.CAT[line]) for line in q.LINES}
NUM={line:[name for name in BASE_NUM[line] if name not in ['prior_claims_5y','ncb_years']] for line in q.LINES}
CAT={line:BASE_CAT[line]+['history_business_band']+(['ncb_business_band'] if line=='motor' else []) for line in q.LINES}
ORIGINAL_DESIGN=r.design


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)


def rating_frame(frame,line):
    f=frame.copy();nb=f.new_business.to_numpy(dtype=int);assert np.isin(nb,[0,1]).all()
    history=pd.to_numeric(f.prior_claims_5y,errors='coerce').clip(upper=2).fillna(-1).astype(int).astype(str).to_numpy()
    f['history_business_band']=[f'{business}|{label}' for business,label in zip(nb,history)]
    if line=='motor':
        ncb=pd.cut(pd.to_numeric(f.ncb_years,errors='coerce'),[-1,0,2,5,9,np.inf],labels=['0','1-2','3-5','6-9','10+']).astype('string').fillna('missing').to_numpy()
        f['ncb_business_band']=[f'{business}|{label}' for business,label in zip(nb,ncb)]
    return f


def design(frame,line,pre=None):return ORIGINAL_DESIGN(rating_frame(frame,line),line,pre)


def frame_for(line,outer):
    raw=pd.read_parquet(r.p.t.t.OUT/f'input_{line}_{outer}.parquet')
    columns=['row_id','line','year','group_id','fold','new_business','T0','reserve','period_start','period_end','exposure_calendar','annual_A1S','annual_T2b','q_paired','is_held']+BASE_NUM[line]+BASE_CAT[line]
    f=raw[list(dict.fromkeys(columns))].copy()
    assert not any(name.startswith(('baseline_','crossfit_','e_cost')) for name in f)
    assert np.array_equal(f.is_held,f.fold.eq(outer)) and f.year.isin([2023,2024]).all();return f


def poison(frame,line):
    f=frame.copy();held=f.is_held
    columns=list(dict.fromkeys(['T0','reserve','q_paired','annual_A1S','annual_T2b','exposure_calendar']+BASE_NUM[line]+BASE_CAT[line]))
    for name in columns:f[name]=f[name].astype('object');f.loc[held,name]='INVALID_HELD'
    return f


def setup():r.NUM=NUM;r.CAT=CAT;r.design=design


def fit(frame,line,checkpoint=None):
    setup();artifact=b.fit(frame,line,checkpoint)
    artifact['rating_form']='P65existing_history_NCBbands_by_business_as_direct_GLMcategorical_effects';return artifact


def forward(frame,artifact):setup();return b.forward(frame,artifact)
def independent_math(train,artifact):setup();return b.independent_math(train,artifact)


def synthetic():
    setup();rng=np.random.default_rng(2026102781);records=[];n=720;i=np.arange(n)
    for line in q.LINES:
        f=pd.DataFrame({'row_id':['synthetic'+str(j) for j in i],'line':line,'group_id':['g'+str(j) for j in i],'is_held':i%5==0,
            'fold':i%5,'year':2023+(i//5)%2,'new_business':(i//10)%2,'T0':rng.gamma(2,90,n)*(rng.random(n)<.4),'reserve':0.,
            'annual_A1S':np.exp(rng.normal(0,.4,n)),'annual_T2b':np.exp(rng.normal(5,.5,n)),'exposure_calendar':rng.uniform(.1,1,n),'q_paired':rng.uniform(.3,1,n)})
        for name in BASE_NUM[line]:f[name]=rng.choice([0.,10.,100.],n)
        for name in BASE_CAT[line]:
            if name!='new_business':f[name]=rng.choice(['a','b','c'],n)
        f['prior_claims_5y']=rng.choice([0.,1.,2.,3.,np.nan],n)
        if line=='motor':f['ncb_years']=rng.choice([0.,1.,2.,3.,5.,6.,9.,10.,np.nan],n)
        folder=OUT/'synthetic'/line
        primary=m.once(folder,'primary',lambda:fit(f,line,folder/'primary_raw.json'))
        adverse=m.once(folder,'adverse',lambda:fit(poison(f,line),line,folder/'adverse_raw.json'));assert primary==adverse
        assert not primary['warnings'] and primary['gradient_inf']<1e-5
        checks=independent_math(f.loc[~f.is_held],primary)
        held=f.loc[f.is_held].copy();u,relative=forward(held,primary)
        clean=held.drop(columns=['T0','reserve','q_paired']);other,rr=forward(clean,json.loads(json.dumps(adverse)))
        assert np.array_equal(u,other) and np.array_equal(relative,rr)
        subset=np.arange(0,len(held),7);small,_=forward(clean.iloc[subset],primary);assert np.allclose(small,u[subset],rtol=2e-13,atol=1e-13)
        permutation=np.arange(len(held))[::-1];shuffled,_=forward(clean.iloc[permutation],primary);assert np.allclose(shuffled,u[permutation],rtol=2e-13,atol=1e-13)
        # An absent categorical band uses the declared all-zero encoding; no held fit.
        unknown=clean.copy();unknown.loc[unknown.index[0],'prior_claims_5y']=-987
        x,_=design(unknown,line,primary['preprocess']);columns=primary['preprocess']['columns'];indices=[j for j,name in enumerate(columns) if name.startswith('history_business_band=')]
        assert indices and not x[0,indices].any()
        assert 'prior_claims_5y' not in primary['preprocess']['numeric'] and 'ncb_years' not in primary['preprocess']['numeric']
        records.append({'line':line,'all_held_payload_poison_before_band_transform_invariant':True,'objective_gradient':checks,'JSON_replay_exact':True,
            'subset_permutation_projective_given_source_inputs':True,'unknown_band_allzero_no_refit':True,'no_duplicate_ordinal_history_terms':True,'preprocess_columns':columns})
    return {'author':'Codex','utc':utc(),'records':records,'synthetic_primary_GLMfits':3,'synthetic_adverse_GLMfits_separate':3,'new_real_fits':0,'new_source_fits':0,'new_CDF_fits':0,'new_scores':0,'new2025inference':0,'new_submissions':0}


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    previous=BASE/'P80_validacion_formas_momento_20261027';assert w.read(previous/'completion_receipt.json')['report_sha256']==w.sha(previous/'report.json')
    parent=w.read(b.PLAN);m.check_sources(parent)
    paths=[Path(__file__),Path(b.__file__),Path(r.__file__),b.PLAN,b.OUT/'report.json',b.OUT/'completion_receipt.json',previous/'report.json',previous/'completion_receipt.json',
        BASE/'P78_formas_riesgo_20261027/report.json',R/'registro/semana2_GLM_prior_dos_fuentes_validacion_plan.json']
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'scope':'NEWstandard GLMcategorical representation, synthetic full flow and strict15saved input bindings only; no real fit/source/CDF/score.',
        'need':'P78identified that P77direct GLMshared ordinal logslopes cannot represent the P65business-specific history/NCBband functions. P80rawmoment-only change failed with delta-.00005394and did not address that function-space difference. No causal attribution or new sign/field selection.',
        'hypothesis':'A standard direct GLMwith the SAMEalready-used business-specific bands may represent nonlinearity without target-cost-trained base offsets or arbitrary new interactions. Benefit unknown, not a private gain claim.',
        'one_change':'Replace shared log1pprior/ncbnumeric terms by fullonehot of existing P65priorband x business and, motoronly, existing P65NCBband x business. Keep all other existing main effects/source signals, alpha1/preprocessing/prior/objective/inputs unchanged.',
        'configuration':{'numeric':NUM,'categorical':CAT,'parameters':r.PARAMS,'fixed_source_offset':w.read(b.PLAN)['configuration']['offset_change_only'],
            'bands':'Exact original P65NCBcut[-1,0,2,5,9,inf], missing; history min(count,2), missing -1; deterministic provided covariates only, before preprocessing AFTERtrainselector.',
            'preprocessing':'Same training-only numeric median/standardization/missing flags and fullonehot/train levels/unknownallzero. No dual raw history terms, cap, search, field deletion outside this replacement or target-trained base.',
            'interpretation':'Business x band encodes a rating form already present in the structured comparator. It changes function space with fixed regularization, not an isolated test of every interaction or restored holdout.'},
        'criterion':'All held cost/source/calendar/q/rawrating payload poison before trainselection/banding invariant; raw loss/gradient scalar checks, exact JSONreplay, projectivity, unknown band encoding,15strict input joins and deterministic band equality to original P65.',
        'future_budget':{'primary_GLMfits':15,'adverse_GLMfits_separate':15,'new_target_base_fits':0,'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0},
        'future_criterion':'Separate P82registration/commit and EVERYunchanged P77predictive/cohort/scenario/family16/level/influence/convergence guard; pooledpass requires OWN2023-only conditionaltransfer before CSV. No K/alpha/band/field/weight/line rescue.',
        'sources':{**parent['sources'],**{w.rel(path):w.sha(path) for path in paths}},'limits':parent['limits']+['Difference in rating form does not establish a cause of P77loss or need for arbitrary capacity. No new covariates, source fit or target base.'],
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md';body.write_text('Codex. P81registra antes de probar un GLMestándar con el mismo prior fuente50/50yalpha1deP77. Cambia solo representación de historia/NCB: bandas ya presentes enP65separadas por negocio, en lugar de pendienteslog1pcomunes. Resto de campos/objetivo/preproceso/fuentes/qsin cambio, sin añadir datos o elegir signos/variables por validación. P80no resolvió esta diferencia de forma y queda adverso.3+3GLMsintéticos con veneno de payload antes del selector/bandas, matemática/JSON/projectividad y15entradas reales sin ajustar. Nada de ajustes reales/CDF/2025/envíos. Una evaluación realP82requiere registro y todas las guardas/transferencia intactas. B00preservado,2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P81registered_before_band_GLMSynthetic','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P81-BANDAS-PREVIO','P81: mismas bandas por negocio dentro del GLM, antes de probar')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def run():
    assert not (OUT/'report.json').exists();plan=w.read(PLAN);m.check_sources(plan);assert w.read(OUT/'registration.json')['plan_sha256']==w.sha(PLAN)
    dump(OUT/'synthetic.json',synthetic());bindings=[]
    # Equality of NEWnumeric path with established deterministic P65bands, no fit.
    old=r.p.k.core.b
    for line in q.LINES:
        for outer in range(5):
            f=frame_for(line,outer);z=rating_frame(f,line);nb=f.new_business.to_numpy(int)
            expected=[f'{business}|{label}' for business,label in zip(nb,old.bands(f,'prior'))];assert np.array_equal(expected,z.history_business_band)
            if line=='motor':assert np.array_equal([f'{business}|{label}' for business,label in zip(nb,old.bands(f,'ncb'))],z.ncb_business_band)
            bindings.append({'line':line,'outer':outer,'rows':len(f),'rating_band_exactly_original_P65':True,'same_saved_P64_input_sha256':w.sha(r.p.t.t.OUT/f'input_{line}_{outer}.parquet')})
    m.check_sources(plan);dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P81band_GLMprotected_synthetic_and_bindings_passed','bindings':bindings,
        'new_real_fits':0,'new_source_fits':0,'new_CDF_fits':0,'new_scores':0,'new2025inference':0,'new_submissions':0})
    print(json.dumps({'preflight':'passed','bindings':len(bindings),'new_real_fits':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();d=w.read(OUT/'report.json');m.check_sources(w.read(PLAN))
    next_unit='P82: register/commit SAMEP77single directGLMfixedsourceprior with ONLYP81history/NCBbusinessband representation.15primary/15adverseGLMfits, no source/base/CDFfits, all unchanged gates plus convergence; pooledpass requires own2023-only conditionaltransfer before CSV. No alpha/bands/field/weight/line rescue.'
    text='# P81: bandas por negocio dentro del GLM\n\nCodex, '+utc()+'. Se cambia solo la representación de historia/NCBde pendienteslog1pcomunes a las bandas por negocio ya usadas porP65. No se añaden covariables: se retiran los términos ordinales sustituidos. Mismo GLMalpha1, prior fuente50/50, resto de campos y objetivo. La diferencia funcional motivó la prueba; no demuestra la causa de pérdidas ni mejora privada.\n\n'
    text+='Pasaron3GLMprimarios/3adversos sintéticos, veneno de TODOSlos campos retenidos antes de seleccionar entrenamiento o crear bandas, objetivo/gradiente por otra suma, replayJSONexacto, proyección por subconjuntos/permutación y banda desconocida sin ajuste. Las bandas en15entradas reales coinciden exactamente con la función originalP65; cero ajustes o scores reales/CDF/2025/envíos. Todas las guardas y transferencia propia siguen requeridas. B00/F3cyalternativas conservados;2024es desarrollo adaptativo, información fuente/snapshots condicional, sin revisión independiente.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'synthetic.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'next_unit':next_unit,
        'new_real_fits':0,'new_source_fits':0,'new_CDF_fits':0,'new_scores':0,'new_submissions':0,'2024_open':True,'goal_achieved':False,
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P81-BANDAS-RESULTADO','P81: GLM por bandas protegido, preflight completo sin ajuste real')}
    archive=R/'privado'/('corte_P81_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir();w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P81'),(R/'registro/semana2_mision_privada_actual.json','P81')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    cp=R/'registro/semana2_contadores_propios_actual.json';w.update(cp,{'phase2_private_P81_business_band_preflight':{**receipt,'synthetic':w.read(OUT/'synthetic.json')}},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P81=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P81: GLM con bandas por negocio, preflight\n\nCodex, '+receipt['utc']+'.TresGLMprimarios/3adversos sintéticos y15enlaces, cero ajuste real/CDF/scoring/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_business_band_GLM_preflight_index':w.rel(INDEX),'week_2_private_business_band_GLM_preflight_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'new_real_fits':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['register','run','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'register':register,'run':run,'close':close}[args.mode]()
