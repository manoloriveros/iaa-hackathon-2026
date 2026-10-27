"""Revision de evidencia y politica residual de dominio, sin entrenar fuentes."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import hashlib
import importlib.util
import json
import math
import os
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
spec=importlib.util.spec_from_file_location('doc_review_writer',R/'herramientas/registrar_avance_mision017_fase2.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
BASE=R/'privado/semana2/mision017_fase2'
OUT=BASE/'revision_chat_documento_20261027'
PARENT=R/'privado/validacion_cadena_f3c/20261027T153123Z'
ACTIVE=R/'privado/validacion_cadena_f3c_A1_mezcla/20261027T175434Z'
PLAN=R/'registro/semana2_revision_evaluacion_documento_plan.json'
INDEX=R/'registro/semana2_revision_evaluacion_documento_actual.json'
DOC=R/'docs/semana2/REVISION_EVALUACION_DOCUMENTO_20261027.md'
VIEWS=['T2b','A1','mezcla'];LINES=['motor','buildings','contents']
F3C=R/'privado/semana2/claude_mision017_20261025/F3c_2025.csv'
F3CSHA='5ab5e4e34290cf6ed6a7a792f59e1e55a4f056400bbbdf8401933afd236b3276'
COORD=R/'docs/validacion_cinco_prioridades/20261027T142339Z'
THREAD='01a17a2a-2650-7201-9b42-c688b92ac726'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf8') as f:json.dump(data,f,ensure_ascii=False,indent=2,allow_nan=False)
def post(path,identifier,subject):
    import subprocess
    result=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',identifier,
        '--asunto',subject,'--cuerpo',str(path)],check=True,capture_output=True,text=True,encoding='utf8')
    return json.loads(result.stdout)
def guard(plan):
    for name,sha in plan['sources'].items():assert w.sha(ROOT/name)==sha,name


def neutral_nb(base,factored,new_business):
    base=np.asarray(base);factored=np.asarray(factored);nb=np.asarray(new_business)
    assert base.ndim==factored.ndim==nb.ndim==1 and base.shape==factored.shape==nb.shape
    assert np.isin(nb,[0,1]).all();mask=nb.astype(bool)
    # Read only the actually used branch, including when own factors are absent
    # for NB. No portfolio normalizer, public exponent or level follows this rule.
    result=np.empty(len(nb),dtype=float)
    result[mask]=base[mask].astype(float);result[~mask]=factored[~mask].astype(float)
    assert np.isfinite(result).all() and (result>0).all()
    return result


def groups(t):
    # Independent bipartite customer/address union, canonical smallest customer.
    parent={}
    def find(node):
        parent.setdefault(node,node)
        while parent[node]!=node:
            parent[node]=parent[parent[node]];node=parent[node]
        return node
    for customer,address in t[['customer_id','address_id']].itertuples(index=False,name=None):
        a=find('c:'+str(customer));b=find('a:'+str(address))
        if a!=b:parent[b]=a
    minima={}
    for customer in t.customer_id.astype(str).unique():
        root=find('c:'+customer);minima[root]=min(minima.get(root,customer),customer)
    return np.array([minima[find('c:'+str(customer))] for customer in t.customer_id])


def loss(y,mu):
    y=np.asarray(y,dtype=float);mu=np.asarray(mu,dtype=float)
    assert y.shape==mu.shape and np.isfinite(y).all() and (y>=0).all() and np.isfinite(mu).all() and (mu>0).all()
    return 4*y/np.sqrt(mu)+4*np.sqrt(mu)-8*np.sqrt(y)
def null_loss(y,weight=None):
    weight=np.ones(len(y)) if weight is None else np.asarray(weight,float)
    return 8*(math.sqrt(math.fsum(weight.tolist())*math.fsum((weight*y).tolist()))-math.fsum((weight*np.sqrt(y)).tolist()))


def synthetic():
    base=np.array([10.,20.,30.,40.]);full=np.array([11.,21.,31.,41.]);nb=np.array([1,0,1,0])
    expected=np.array([10.,21.,30.,41.]);assert np.array_equal(neutral_nb(base,full,nb),expected)
    b=base.astype(object);f=full.astype(object);b[nb==0]='UNUSED';f[nb==1]='UNAVAILABLE_OWN_FACTORS'
    assert np.array_equal(neutral_nb(b,f,nb),expected)
    assert np.array_equal(neutral_nb(b[::-1],f[::-1],nb[::-1]),expected[::-1])
    assert np.array_equal(neutral_nb(b[[0,3]],f[[0,3]],nb[[0,3]]),expected[[0,3]])
    for bad in [[0,1,2,0],[0,1,np.nan,0]]:
        try:neutral_nb(base,full,bad)
        except AssertionError:pass
        else:raise AssertionError('Unknown business type accepted')
    t=pd.DataFrame({'customer_id':['c','b','a','d'],'address_id':['x','x','y','y']})
    assert np.array_equal(groups(t),['b','b','a','a'])
    from sklearn.metrics import mean_tweedie_deviance
    y=np.array([0.,1.,3.,50.]);mu=np.array([2.,3.,5.,20.])
    assert math.isclose(math.fsum(loss(y,mu).tolist())/len(y),mean_tweedie_deviance(y,mu,power=1.5),rel_tol=3e-14)
    assert math.isclose(null_loss(y),math.fsum(loss(y,np.full(len(y),y.mean())).tolist()),rel_tol=3e-14)
    return {'author':'Codex','utc':utc(),'NB_exact_baseline_renewal_exact_factored':True,
        'unused_branch_not_parsed':True,'subset_permutation_exact':True,'unknown_business_rejected':True,
        'independent_customer_address_groups':True,'scalar_Tweedie_identity':True,'new_fits':0}


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    paths=[Path(__file__),PARENT/'PLAN.json',PARENT/'freeze.json',PARENT/'fuentes.json',PARENT/'resultados.json',
        PARENT/'baseline_predictions.parquet',PARENT/'target2024_sealed.parquet',PARENT/'verificacion.json',PARENT/'cierre.json',
        ACTIVE/'PLAN.json',ACTIVE/'freeze.json',ACTIVE/'sources.json',ACTIVE/'source_training_complete.json',
        ACTIVE/'prediction_checks.json',ACTIVE/'preopening_verification.json',ACTIVE/'target2024_sealed.parquet',
        R/'herramientas/validar_cadena_f3c.py',R/'herramientas/ampliar_validacion_cadena_f3c.py',F3C,
        R/'registro/validacion_cinco_prioridades_actual.json',COORD/'INFORME_CONJUNTO.md']
    paths += [COORD/f'P{i:02d}.md' for i in range(1,6)]
    for view in VIEWS:paths += [ACTIVE/f'predictions_{view}.parquet',ACTIVE/f'parameters_{view}.json']
    assert all(path.exists() for path in paths),[str(path) for path in paths if not path.exists()]
    assert w.sha(F3C)==F3CSHA
    OUT.mkdir();dump(OUT/'synthetic.json',synthetic())
    plan={'author':'Codex','utc':utc(),'request':'Review completed and ongoing work in Evaluación del documento; decide/model changes for private robustness; submission only if supported. No external message/delegation.',
        'source_chat':{'thread_id':THREAD,'title':'Evaluación del documento','read_only':True,
            'completed_primary_turn':'01a17df7-5e4f-7d11-89e2-489df84b4b8a','ongoing_turn':'01a17e78-989e-7ee1-b609-d0941ee1b8f0'},
        'review_scope':'Evidence integrity, frozen code/data/control receipts, independent point metric/group arithmetic, bootstrap identities, production-vs-validation family and stage scope. Preserve concurrent files and author ownership; no retrain or report rerender.',
        'prior_knowledge':'Primary T2b correction results and adverse NB/influence already known; heartbeat exposed A1/mix completion and mix global delta~.002366. This is exploratory, not blind confirmation; no A1/mix segment choice or weight selection.',
        'candidate':'DOC_R1_NB_baseline_renewal_own_block',
        'hypothesis':'Own residual factors lack stable NB support while NB dominates2025. Applying the block only in renewal may preserve its evidence and avoid adding unsupported NB effects. Baseline itself remains uncertain.',
        'configuration':{'quote_rule':'Every line: new_business=1 returns EXACT sin_factores; renewal returns EXACT F3c_reaprendido, no following level/exponent/normalizer. No re-learning or choosing fields/ramo/weight.',
            'retained':'F2/prior history/commonshape and source predictors remain in sin_factores. This does not establish inception availability of those ancestors.',
            'views':VIEWS,'primary':'T2b fixed; A1 and fixed50/50 mix are sensitivities, no best-view selection.',
            'evaluation':'Same59202historical2024rows/observedT0/paired completion and same customer-address components. Labels/recipes already adaptive.',
            'bootstrap':'Reuse original10000group multiplicities with seed2026102301, compute only new policy statistics; no new seed/search. Global/NB/renewal/ramo intervals, same2025composition weights if available.',
            'family':12,'family_scope':'Six original view comparisons plus six new policy-vs-baseline/full comparisons; conditional percentile bands, does not account for whole historical search.',
            'criteria':{'global_family12_lower_gt':.0005,'broad_segment_floor':-.001,'NB_point_nonnegative':True,
                'NB_lower95_floor':-.001,'motor_NB_floor':-.001,'influence_top': 'max(5,ceil(.001*G))','influence_delta_nonnegative':True,
                'same_quote_NB_and_renewal_exact':True},
            'stress':'Apply same branch rule to BOTH fixed nominal prices and each source scenario target-relearned price pack. Preserve all50scenarios and segments, without new source/target fit. Robustness warning if adverse broad floor-.001.',
            'submission':'No2025quote or submission from retrospective policy pass alone. Require exact validated family implemented/reproduced in production with committed code and whole-flow safeguards. Existing F3c includes F1/3seed/public constants not covered by this single-seed noF1backtest.'},
        'budget':{'new_native_or_closed_fits':0,'new_CDF_fits':0,'new2025_model_inference':0,'new_submissions_in_this_evaluation':0},
        'decision':'Any critical predictive/stress gate failure means research-only/no newCSV. Even pass requires mapped production/provenance and full-file admission; no relaxation for public/private speculation.',
        'sources':{w.rel(path):w.sha(path) for path in paths},
        'late_bound_owner_outputs':'Owner results/composition/scenarios/postverification can finish after registration. Read only completed JSON/NPZ, archive exact hashes at use; require unchanged frozen source code/PLAN and fixed source prediction hashes. Never treat in-progress absence as failure.',
        'B00_F3c_all_alternatives_preserved':True,'2024_open_adaptive':True,'goal_achieved':False}
    dump(PLAN,plan)
    body=OUT/'forum_previo.md';body.write_text('Codex. Reviso el trabajo de «Evaluación del documento» por solicitud directa, leyendo el chat y sus artefactos sin modificar su corrida concurrente. El avance computacional no acredita por sí solo generalización: T2b conserva fallos NB/influencia, y la nueva A1 es la rama histórica de una semilla sin F1, distinta de F3c de producción. Registro antes de calcular una política de control: en todos los ramos NB devuelve exactamente la referencia sin el bloque propio; renovación conserva exactamente el precio con ese bloque. No se reestiman factores, pesos, K o niveles. T2b sigue primario y A1/mezcla sensibilidades; ninguna selección por vista. Bandas de familia12, pisos originales, concentración y todos los escenarios, con los mismos sorteos históricos. Es exploratoria tras conocer los resultados previos. Si falla, no se admite CSV; incluso si pasa, falta la producción de la misma familia, trazabilidad y controles antes de enviar. Cero ajustes o inferencia2025 en esta evaluación. B00/F3c y autoría ajena intactos. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':'registered_before_document_review_policy_evaluation','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':post(body,'COD-S2-20261027-REVISION-DOCUMENTO-PREVIO','Revisión del chat y política conservadora NB, criterios previos')}
    dump(OUT/'registration.json',receipt);dump(INDEX,receipt);print(json.dumps(receipt))


def audit():
    plan=w.read(PLAN);guard(plan);checks={};receipts=[]
    for root,script,manifest in [(PARENT,'validar_cadena_f3c.py','fuentes.json'),(ACTIVE,'ampliar_validacion_cadena_f3c.py','sources.json')]:
        frozen=w.read(root/'freeze.json')
        checks[root.parent.name+'_code_frozen']=frozen['code_sha256']==w.sha(R/'herramientas'/script)
        checks[root.parent.name+'_plan_frozen']=frozen['plan_sha256']==w.sha(root/'PLAN.json')
        checks[root.parent.name+'_manifest_frozen']=frozen['sources_sha256']==w.sha(root/manifest)
    a=w.read(ACTIVE/'source_training_complete.json');checks['all_completed_A1_adversarial_receipts']=a['all_passed'] and all(a['checks'].values())
    checks['A1_actual_native_attempts48']=a['native_fit_attempts']==48 and len((ACTIVE/'fit_attempts.jsonl').read_text().splitlines())==48
    for path in (ACTIVE/'models').glob('*/*_receipt.json'):
        record=w.read(path);model=path.with_name(path.name.replace('_receipt.json','.txt'));raw=path.with_name(path.name.replace('_receipt.json','_raw.parquet'))
        assert record['complete'] and w.sha(model)==record['model_sha256'] and w.sha(raw)==record['raw_file_sha256']
        receipts.append({'path':w.rel(path),'model_sha256':record['model_sha256'],'arguments_sha256':record['arguments_sha256'],'rounds':record['rounds']})
    checks['all24_source_pairs_saved_and_hashed']=len(receipts)==24
    for name in ['preflight.json','prediction_checks.json','preopening_verification.json']:
        data=w.read(ACTIVE/name);checks[name]=data['all_passed']
    labels=pd.read_parquet(ACTIVE/'target2024_sealed.parquet');assert labels.row_id.is_unique
    t=pd.read_parquet(ACTIVE/'predictions_T2b.parquet',columns=['row_id','customer_id','address_id','year','new_business','sin_factores','F3c_reaprendido','constante'])
    y=labels.set_index('row_id').loc[t.row_id,'y'].to_numpy(float)
    original=w.read(PARENT/'resultados.json')
    points={}
    for segment,mask in [('global',np.ones(len(t),bool)),('new_business',t.new_business.to_numpy(bool)),('renewal',~t.new_business.to_numpy(bool))]:
        den=null_loss(y[mask]);points[segment]={name:float(1-math.fsum(loss(y[mask],t.loc[mask,name].to_numpy()).tolist())/den) for name in ['sin_factores','F3c_reaprendido','constante']}
        for name,value in points[segment].items():assert math.isclose(value,original['metrics'][segment]['D2'][name],rel_tol=0,abs_tol=2e-13)
    group=groups(t);checks['independent_2024_components_count']=len(np.unique(group))==original['influence']['groups']
    checks['all59202_rows_and_year2024']=len(t)==59202 and t.year.eq(2024).all()
    checks['F3c_bytes_preserved']=w.sha(F3C)==F3CSHA
    checks['validation_family_not_exact_production']=True
    guard(plan);assert all(checks.values()),checks
    dump(OUT/'audit.json',{'author':'Codex','utc':utc(),'checks':checks,'source_receipts':receipts,'scalar_primary_D2':points,
        'scope':'Completed primary and completed computational A1/mix stages. Owner final scenario verification remains separately checked at close.',
        'professional_independent_review':False,'new_fits':0,'new2025inference':0})
    print(json.dumps({'audit_passed':True,'completed_source_pairs':len(receipts),'computational_primary_not_production_claim':True}))


def evaluate_policy():
    plan=w.read(PLAN);guard(plan);assert (OUT/'audit.json').exists() and not (OUT/'policy_results.json').exists()
    dump(OUT/'policy_started.json',{'author':'Codex','utc':utc(),'pid':os.getpid(),'plan_sha256':w.sha(PLAN)})
    late={};tables={};quotes={}
    cols=['row_id','customer_id','address_id','year','new_business','line','exposure','sin_factores','F3c_reaprendido','constante']
    target=pd.read_parquet(ACTIVE/'target2024_sealed.parquet').set_index('row_id').y
    for view in VIEWS:
        t=pd.read_parquet(ACTIVE/f'predictions_{view}.parquet',columns=cols)
        assert t.row_id.is_unique and len(t)==59202 and t.year.eq(2024).all()
        if tables:
            for name in ['row_id','customer_id','address_id','new_business','line']:assert np.array_equal(t[name],tables['T2b'][name])
        base=t.sin_factores.to_numpy();full=t.F3c_reaprendido.to_numpy();candidate=neutral_nb(base,full,t.new_business.to_numpy())
        nb=t.new_business.to_numpy(bool)
        assert np.array_equal(candidate[nb],base[nb]) and np.array_equal(candidate[~nb],full[~nb])
        z=t[['row_id','line','new_business']].copy();z['baseline']=base;z['full']=full;z['DOC_R1']=candidate
        z.to_parquet(OUT/f'policy_{view}.parquet',index=False);tables[view]=t;quotes[view]=(base,full,candidate)
    t=tables['T2b'];y=target.loc[t.row_id].to_numpy(float);g=groups(t);universe,ix=np.unique(g,return_inverse=True);G=len(universe)
    composition=ACTIVE/'composition_bootstrap_T2b.npz'
    assert composition.exists(),'Owner composition outputs are not complete yet; do not invent them'
    futureweights=np.load(composition)['weights'];assert len(futureweights)==len(t) and np.isfinite(futureweights).all() and (futureweights>=0).all()
    for view in VIEWS:
        path=ACTIVE/f'composition_bootstrap_{view}.npz';assert np.array_equal(np.load(path)['weights'],futureweights);late[w.rel(path)]=w.sha(path)
    nb=t.new_business.to_numpy(bool)
    masks={'global':np.ones(len(t),bool),'new_business':nb,'renewal':~nb,**{line:t.line.eq(line).to_numpy() for line in LINES}}
    names=list(masks)+['mix2025_global','mix2025_new_business']
    weights={name:mask.astype(float) for name,mask in masks.items()}
    weights['mix2025_global']=futureweights;weights['mix2025_new_business']=futureweights*nb
    stats=[];results={};gain_by_view={}
    for view,(base,full,candidate) in quotes.items():
        gain_by_view[view]=(loss(y,base)-loss(y,candidate),loss(y,full)-loss(y,candidate))
        results[view]={'metrics':{},'influence':{}}
        for name,mask in {**masks,**{line+'_'+str(b):t.line.eq(line).to_numpy()&(nb==b) for line in LINES for b in [0,1]}}.items():
            den=null_loss(y[mask]);first,second=gain_by_view[view]
            results[view]['metrics'][name]={'rows':int(mask.sum()),'delta_vs_baseline':float(math.fsum(first[mask].tolist())/den),
                'delta_vs_full':float(math.fsum(second[mask].tolist())/den)}
        for name in ['mix2025_global','mix2025_new_business']:
            ww=weights[name];den=null_loss(y,ww);first,second=gain_by_view[view]
            results[view]['metrics'][name]={'rows':int((ww>0).sum()),'delta_vs_baseline':float(math.fsum((first*ww).tolist())/den),
                'delta_vs_full':float(math.fsum((second*ww).tolist())/den),'descriptive_composition_only':True}
        first=gain_by_view[view][0];gg=np.bincount(ix,weights=first,minlength=G);order=np.argsort(-gg,kind='stable');remove=max(5,int(np.ceil(.001*G)))
        keep=~np.isin(ix,order[:remove]);delta=float(math.fsum(first[keep].tolist())/null_loss(y[keep]))
        erased=np.flatnonzero(np.cumsum(gg[order])>=gg.sum())
        results[view]['influence']={'groups':G,'removed':remove,'delta_without_top':delta,'groups_to_erase':int(erased[0]+1) if len(erased) else None}
    # Same original group multiplicities, new statistics. No bootstrap of a
    # different seed or repeated source/target learning.
    for name in names:
        ww=weights[name]
        block=[np.bincount(ix,weights=ww,minlength=G),np.bincount(ix,weights=ww*y,minlength=G),np.bincount(ix,weights=ww*np.sqrt(y),minlength=G)]
        for view in VIEWS:
            for gain in gain_by_view[view]:block.append(np.bincount(ix,weights=ww*gain,minlength=G))
        stats.append(np.stack(block,axis=1))
    flat=np.stack(stats,axis=1).reshape(G,-1);rng=np.random.default_rng(2026102301);draws=np.empty((10000,len(names),3,2))
    for start in range(0,10000,25):
        size=min(25,10000-start);counts=np.stack([np.bincount(rng.integers(0,G,size=G),minlength=G) for _ in range(size)])
        if start==0:np.save(OUT/'first4_original_group_multiplicities.npy',counts[:4])
        values=(counts@flat).reshape(size,len(names),9)
        den=8*(np.sqrt(values[:,:,0]*values[:,:,1])-values[:,:,2]);assert (den>0).all()
        draws[start:start+size]=(values[:,:,3:]/den[:,:,None]).reshape(size,len(names),3,2)
    np.savez_compressed(OUT/'policy_bootstrap.npz',delta=draws,segments=names,views=VIEWS,comparisons=['baseline','full'])
    for vi,view in enumerate(VIEWS):
        for si,name in enumerate(names):
            record=results[view]['metrics'][name]
            for ci,comparison in enumerate(['baseline','full']):
                record['CI95_vs_'+comparison]=np.quantile(draws[:,si,vi,ci],[.025,.975]).tolist()
                record['family12_vs_'+comparison]=np.quantile(draws[:,si,vi,ci],[.05/24,1-.05/24]).tolist()
        a=results[view]['metrics'];results[view]['guards']={
            'global_family12_lower_gt_margin':a['global']['family12_vs_baseline'][0]>.0005,
            'broad_segment_floor':all(a[name]['delta_vs_baseline']>=-.001 for name in ['motor','buildings','contents','new_business','renewal']),
            'NB_increment_protection':a['new_business']['delta_vs_baseline']>=0 and a['new_business']['CI95_vs_baseline'][0]>=-.001,
            'motor_NB_floor':a['motor_1']['delta_vs_baseline']>=-.001,
            'influence_top_removal_nonnegative':results[view]['influence']['delta_without_top']>=0,
            'NB_quote_exact_baseline':True,'renewal_quote_exact_full':True}
    guard(plan)
    dump(OUT/'policy_results.json',{'author':'Codex','utc':utc(),'candidate':plan['candidate'],'results':results,
        'all_primary_guards_pass':all(results['T2b']['guards'].values()),'family':12,'same_original_group_multiplicities':True,
        'late_bound_sources':late,'new_fits':0,'new2025inference':0,'new_submissions':0,'production_ready':False})
    print(json.dumps({'primary':results['T2b'],'new_fits':0,'production_ready':False}))


def scenarios():
    plan=w.read(PLAN);guard(plan);assert not (OUT/'scenario_review.json').exists()
    source=ACTIVE/'scenario_results.json';assert source.exists(),'Owner50scenarios are still pending'
    items=w.read(source)['scenarios'];assert len(items)==50
    labels=pd.read_parquet(ACTIVE/'target2024_sealed.parquet').set_index('row_id').y
    tables={view:pd.read_parquet(ACTIVE/f'predictions_{view}.parquet',columns=['row_id','line','new_business','sin_factores','F3c_reaprendido']) for view in VIEWS}
    y0=labels.loc[tables['T2b'].row_id].to_numpy(float);records=[];sources={w.rel(source):w.sha(source)}
    for i,item in enumerate(items):
        path=ACTIVE/'scenarios'/f'{i:02d}.npz';pack=np.load(path);prices=pack['predictions'];y=pack['y']
        assert prices.shape==(3,3,59202) and y.shape==y0.shape
        sources[w.rel(path)]=w.sha(path);record={'scenario':item['scenario'],'views':{}}
        for vi,view in enumerate(VIEWS):
            t=tables[view];nb=t.new_business.to_numpy(bool);out={}
            for branch,base,full in [('fixed',t.sin_factores.to_numpy(),t.F3c_reaprendido.to_numpy()),('target_relearned',prices[vi,0],prices[vi,1])]:
                quote=neutral_nb(base,full,nb);gain=loss(y,base)-loss(y,quote)
                masks={'global':np.ones(len(t),bool),'new_business':nb,'renewal':~nb,**{line:t.line.eq(line).to_numpy() for line in LINES}}
                out[branch]={name:float(math.fsum(gain[mask].tolist())/null_loss(y[mask])) for name,mask in masks.items()}
                assert out[branch]['new_business']==0.
            record['views'][view]=out
        records.append(record)
    worst={view:min(record['views'][view][branch][segment] for record in records for branch in ['fixed','target_relearned'] for segment in ['motor','buildings','contents','new_business','renewal']) for view in VIEWS}
    dump(OUT/'scenario_review.json',{'author':'Codex','utc':utc(),'scenarios':records,'worst_broad_segment_delta':worst,
        'all_broad_floors_pass':all(value>=-.001 for value in worst.values()),'sources':sources,
        'scope':'Source trees/CDFs fixed, target nuisance relearnt in original owner artifacts. Overlay only, no refits, no probabilities or ultimate adequacy claim.',
        'new_fits':0,'new2025inference':0,'new_submissions':0})
    print(json.dumps({'scenarios_reviewed':50,'worst_broad_segment_delta':worst,'new_fits':0}))


def close():
    plan=w.read(PLAN);guard(plan);audit=w.read(OUT/'audit.json');policy=w.read(OUT/'policy_results.json');stress=w.read(OUT/'scenario_review.json')
    assert all(w.sha(ROOT/name)==sha for name,sha in policy['late_bound_sources'].items())
    assert all(w.sha(ROOT/name)==sha for name,sha in stress['sources'].items())
    primary=policy['results']['T2b'];ok=policy['all_primary_guards_pass'] and stress['all_broad_floors_pass']
    owner_post=ACTIVE/'post_verification.json';owner_info={'complete':False}
    if owner_post.exists():owner_info={'path':w.rel(owner_post),'sha256':w.sha(owner_post),'content':w.read(owner_post)}
    next_unit=('Production of the EXACT newly validated family still missing, not inherited from old F3c. Require registered full historical source/target refits and whole quote flow, committed producer code, exact-file controls and current Kaggle quota before any submission. Do not map the one-seed noF1proof to old3seed/F1/public-calibrated F3c.' if ok else
        'Retain F3c/B00 and all research alternatives; no new CSV from this policy. Computational scope correction verified, but a robust new model still needs support/transport and predictive evidence. Review completed owner final results without repeating source fits; the climate-mark P113stage remains research and is not automatic priority over full-family validation.')
    a=primary['metrics'];text='# Revisión de «Evaluación del documento»\n\nCodex, '+utc()+'. Revisión propia de IA sobre evidencia compartida, sin revisión profesional independiente. No se modificó la corrida ajena, el PDF, el guion o F3c.\n\n'
    text+='La corrección computacional es un avance real: se cotejaron código y planes congelados, 24 pares fuente A1 guardados con 48 llamadas nativas y sus pruebas adversas, y los controles anteriores a puntuar. Las métricas primarias se reprodujeron con aritmética escalar y los componentes cliente-dirección se reconstruyeron por otro algoritmo. Esto no vuelve independiente a 2024 ni demuestra disponibilidad histórica de datos o coste último.\n\n'
    text+='A1 de esta comprobación es la rama histórica de una semilla, sin F1. La entrega F3c incluye tres semillas, F1 y constantes públicas históricas. La protección del contraste no certifica retrospectivamente todos los ancestros de ese CSV. Las revisiones de soporte NB, disponibilidad y reservas conservan sus límites; no se cierran con una nota editorial o un control de integridad.\n\n'
    text+='Probé una política de control del bloque propio: NB devuelve exactamente la referencia sin ese bloque y renovación conserva el precio completo. No se reestimaron factores, K, pesos, niveles, árboles o curvas. El respaldo estadístico sigue siendo condicional a los modelos ya ajustados y a una búsqueda histórica adaptativa. La igualdad de NB con la referencia evita un incremento de ese bloque, sin probar que la referencia sea adecuada para el broker adquirido.\n\n'
    text+='| Vista | Delta global frente a referencia | Banda familiar12 | Delta NB | Delta tras grupos favorables |\n|---|---:|---|---:|---:|\n'
    for view in VIEWS:
        result=policy['results'][view];z=result['metrics']['global'];band=z['family12_vs_baseline']
        text+=f"| {view} | {z['delta_vs_baseline']:+.7f} | [{band[0]:+.7f}; {band[1]:+.7f}] | {result['metrics']['new_business']['delta_vs_baseline']:+.7f} | {result['influence']['delta_without_top']:+.7f} |\n"
    text+='\nCriterios primarios: '+json.dumps(primary['guards'],ensure_ascii=False)+'. Peor segmento en los escenarios: '+json.dumps(stress['worst_broad_segment_delta'])+'. Se conservaron todos los escenarios de precios fijos y capa destino reaprendida, sin atribuirles probabilidades o un refit fuente completo.\n\n'
    text+=('La investigación supera los controles evaluados, pero falta producir y verificar la misma familia antes de un envío.' if ok else 'La política no supera todos los controles registrados; no se admite para envío.')+' No hay una nueva puntuación privada conocida o pronosticada. No se gastó un cupo de Kaggle.\n\n'
    text+='Los cambios necesarios son proteger la cadena completa del modelo que realmente se vaya a entregar, conservar comparadores sencillos y separar renovación de NB sin decisiones por score público. La disponibilidad al cotizar necesita timestamps reales; las reservas y la cola requieren valoraciones posteriores. Se pueden estudiar ajustes con los datos oficiales actuales, pero no inventar esa evidencia faltante ni aprobar modelos por reproducir su CSV.\n\nPróximo: '+next_unit+'\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':'document_chat_review_and_domain_policy_complete_research_only',
        'report':w.rel(DOC),'policy':w.rel(OUT/'policy_results.json'),'policy_sha256':w.sha(OUT/'policy_results.json'),
        'audit_sha256':w.sha(OUT/'audit.json'),'scenarios_sha256':w.sha(OUT/'scenario_review.json'),
        'research_controls_pass':ok,'production_ready':False,'submission_made':False,'owner_post_verification':owner_info,
        'next_unit':next_unit,'goal_achieved':False,'2024_open_adaptive':True,
        'forum':post(body,'COD-S2-20261027-REVISION-DOCUMENTO-RESULTADO','Auditoría del chat y política NB: resultados y consecuencia')}
    archive=R/'privado'/('corte_DOC_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir();w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','document_review_20261027'),(R/'registro/semana2_mision_privada_actual.json','document_review_20261027')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(document_review_20261027=receipt,next_unit=next_unit)
    w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Revisión del chat Evaluación del documento\n\nCodex, '+receipt['utc']+'. Auditoría computacional y política NB sin nuevos ajustes. Controles de investigación='+str(ok)+', producción no preparada, cero envíos. Fuente F3c/B00 preservados, sin modificar trabajo concurrente. Informe '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_document_chat_review_index':w.rel(INDEX),'week_2_document_chat_review_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'research_controls_pass':ok,'production_ready':False,'submission_made':False}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['register','audit','evaluate','scenarios','close']);args=parser.parse_args()
    with threadpool_limits(limits=2):{'register':register,'audit':audit,'evaluate':evaluate_policy,'scenarios':scenarios,'close':close}[args.mode]()
