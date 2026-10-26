"""Prototipo concreto F3c/PUL2. No hay método de envío ni admisión predictiva."""
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal,ROUND_HALF_EVEN,localcontext
import argparse
import importlib.util
import json
import math
import os
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
BASE=R/'privado/semana2/mision017_fase2';HOME=BASE/'A1S_nucleo_20261026_v1'
OLD=BASE/'F3c_FSp_REN_prototipo_20261026_v1';HET=BASE/'enlace_HET_20261026_v1'
PUL=BASE/'forma_ultima_PUL_20261026_v1'
OUT=BASE/'F3c_PUL2_prototipo_20261026_v1';PLAN=R/'registro/semana2_F3c_PUL2_prototipo_plan_v1.json'
RAW=ROOT/'Hackaton/Semana 2/Datos/emerging'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'));sys.stdout.reconfigure(encoding='utf8')
import numpy as np
import pandas as pd
import lightgbm as lgb
from threadpoolctl import threadpool_limits


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


old=load('PUL2_prior_inference_and_rounding',R/'herramientas/preparar_prototipo_F3c_FSp_REN.py')
het=load('PUL2_saved_H1_ultimate_adapter',R/'herramientas/contrastar_enlace_HET.py')
w=old.w;io=old.io;WEIGHTS=old.WEIGHTS


def dump(path,value):
    assert not path.exists(),'Preserve artifact: '+str(path)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')


def G3_future(f,old_n3,stages):
    value=f.annual_raw_T2b.to_numpy(float)*f.exposure.to_numpy(float)
    for shape in old_n3['shape']:value=het.b.shape_apply(f,value,shape)
    value*=np.array([old_n3['cellshape'][str(int(nb))] for nb in f.new_business])
    norms={}
    for stage in stages:
        value,norm=het.g.apply_stage(f,value,stage);norms[stage['variable']]=norm
    return value,norms


def correct_member(f,parent,ratio_link,ratio_ultimate,line,weight=None):
    weight=WEIGHTS[line] if weight is None else weight
    assert np.isfinite(parent).all() and (parent>0).all()
    assert np.isfinite(ratio_link).all() and (ratio_link>0).all()
    adjusted=parent*ratio_link;out=adjusted.copy();ren=f.new_business.eq(0).to_numpy()
    assert ren.any() and np.isfinite(ratio_ultimate[ren]).all() and (ratio_ultimate[ren]>0).all()
    factor=ratio_ultimate[ren]**weight
    norm=float(np.sum(adjusted[ren]*factor)/np.sum(adjusted[ren]))
    out[ren]=adjusted[ren]*factor/norm
    assert abs(out[ren].sum()/adjusted[ren].sum()-1)<1e-12
    assert np.array_equal(out[~ren],adjusted[~ren])
    assert np.isfinite(out).all() and (out>0).all()
    return out,norm


def rounding(values):
    values=np.asarray(values,float);assert np.isfinite(values).all() and (values>0).all()
    ticks=np.empty(len(values),dtype=np.int64)
    for i,x in enumerate(values):
        n,d=float(x).as_integer_ratio();ticks[i]=io.round_ratio_even(n*1000000,d)
    assert (ticks>0).all()
    return ticks


def canonical_metadata(frame,ids,rate):
    assert frame.row_id.is_unique and pd.Index(ids).is_unique and rate.index.is_unique
    result=frame.set_index('row_id').loc[ids].reset_index()
    result['annual_raw_T2b']=rate.loc[ids,'annual_T2b'].to_numpy(float)
    assert np.isfinite(result.annual_raw_T2b).all() and result.annual_raw_T2b.gt(0).all()
    assert result.exposure.gt(0).all()
    # These are adapter markers for observed-at-2024 completion. Ultimate
    # pricing must ignore them and use calendar exposure exactly once.
    result['e_source_mix']=0.;result['e_cost_scope']=0.
    return result


def scalar_forward(f,j,artifact,stages,norms):
    nb=str(int(f.new_business.iloc[j]));pieces=[math.log(float(f.annual_raw_T2b.iloc[j])),math.log(float(f.exposure.iloc[j]))]
    for shape in artifact['shape']:
        label=het.b.bands(f.iloc[[j]],shape['which'])[0]
        pieces += [math.log(shape['factors'].get(nb+'|'+str(label),1.)),-math.log(shape['normalizers'][nb])]
    pieces.append(math.log(artifact['cellshape'][nb]))
    for stage in stages:
        value=f[stage['variable']].iloc[j];label='__MISSING__' if pd.isna(value) else str(value)
        pieces += [math.log(stage['factors'].get(label,1.)),-math.log(norms[stage['variable']]['2025|'+nb])]
    return math.exp(math.fsum(pieces))


def strengthen():
    assert not PLAN.exists() and not (OUT/'registration.json').exists()
    assert not (OUT/'QA_strengthening_receipt.json').exists()
    fixture=pd.DataFrame({'row_id':['b','a','d','c'],'exposure':[1.,.5,.8,1.],'new_business':[0,0,1,1]})
    rates=pd.DataFrame({'row_id':['a','b','c','d'],'annual_T2b':[10.,20.,30.,40.]}).set_index('row_id')
    ids=pd.Series(['a','b','c','d'])
    first=canonical_metadata(fixture,ids,rates)
    second=canonical_metadata(fixture.iloc[::-1],ids,rates.iloc[::-1])
    assert first.equals(second) and first.e_source_mix.eq(0).all()
    for bad in [rates.iloc[1:],pd.concat([rates,rates.iloc[:1]]),rates.assign(annual_T2b=-1.)]:
        try:canonical_metadata(fixture,ids,bad)
        except (AssertionError,KeyError,ValueError):pass
        else:raise AssertionError('Invalid rates accepted')
    try:canonical_metadata(pd.concat([fixture,fixture.iloc[:1]]),ids,rates)
    except (AssertionError,KeyError,ValueError):pass
    else:raise AssertionError('Duplicate metadata accepted')
    before=w.read(OUT/'preflight.json');sources=dict(before['sources'])
    assert sources[w.rel(Path(__file__))]==w.sha(OUT/'code_before_QA_strengthening.py')
    sources[w.rel(Path(__file__))]=w.sha(Path(__file__))
    sources[w.rel(OUT/'code_before_QA_strengthening.py')]=w.sha(OUT/'code_before_QA_strengthening.py')
    sources[w.rel(OUT/'preflight_before_QA_strengthening.json')]=w.sha(OUT/'preflight_before_QA_strengthening.json')
    archive=OUT/'pre_registration_changes';archive.mkdir()
    w.update(OUT/'preflight.json',{'sources':sources,'QA_strengthening_before_any_inference':{
        'canonical_metadata_key_shuffle_exact':True,'missing_duplicate_negative_rate_rejected':True,
        'future_observed_zero_markers_explicit':True,'actual_scalar_G3_H1_forward_check_in_producer':True}},archive)
    dump(OUT/'QA_strengthening_receipt.json',{'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),
        'preflight_sha256':w.sha(OUT/'preflight.json'),'new_inference':0,'new_candidate_prices':0,
        'unregistered_prior_code_and_preflight_preserved':True})
    print(json.dumps({'QA_strengthened_before_registration':True,'source_inference':0,'candidate_prices':0}))


def prepare():
    assert not OUT.exists() and not PLAN.exists();OUT.mkdir()
    parent=pd.read_csv(old.PARENT,dtype=str);sample=pd.read_csv(old.SAMPLE,dtype=str)
    assert w.sha(old.PARENT)=='5ab5e4e34290cf6ed6a7a792f59e1e55a4f056400bbbdf8401933afd236b3276'
    assert len(parent)==209063 and np.array_equal(parent.row_id,sample.row_id);io.ticks(parent)
    cohort=pd.read_parquet(old.COHORT).set_index('row_id').loc[parent.row_id]
    assert cohort.index.is_unique and set(cohort.index)==set(parent.row_id)
    old_plan=w.read(old.PLAN);history_plan=R/'registro/semana2_mision017_FSp_historia_compatibilidad_plan_v1.json'
    cached_rates=OLD/'annual_T2b_REN_2025.parquet'
    assert w.sha(cached_rates)==w.read(history_plan)['sources'][w.rel(cached_rates)]
    assert w.sha(Path(old.__file__))==old_plan['sources'][w.rel(Path(old.__file__))]
    sources=[Path(__file__),Path(old.__file__),Path(io.__file__),Path(het.__file__),old.PARENT,old.SAMPLE,old.COHORT,
        old.PLAN,OLD/'report.json',history_plan,cached_rates,HET/'report.json',HET/'completion_receipt.json',
        PUL/'report.json',PUL/'completion_receipt.json',R/'herramientas/mision017_fase2_tanda2.py',
        R/'herramientas/mision017_fase2_tanda10_factores.py',RAW/'customers.parquet']
    customers=pd.read_parquet(RAW/'customers.parquet',columns=['customer_id','gender','marketing_segment']).set_index('customer_id')
    assert customers.index.is_unique
    cached=pd.read_parquet(cached_rates).set_index('row_id')
    lineage=[];inputs={};nbtotal=0
    for line in WEIGHTS:
        ids=parent.loc[cohort.line.to_numpy()==line,'row_id']
        rp=HOME/f'rows_s2_{line}.parquet';xp=HOME/f'matrix_s2_{line}.parquet'
        tp=RAW/f'test_{line}.parquet';sources += [rp,xp,tp]
        rows=pd.read_parquet(rp);x=pd.read_parquet(xp)
        assert len(rows)==len(x)
        mask=rows.is_test.to_numpy(bool);future=rows.loc[mask].set_index('row_id').loc[ids].reset_index()
        assert future.year.eq(2025).all() and len(future)==len(ids)
        assert np.array_equal(future.new_business.astype(int),cohort.loc[ids,'new_business'].astype(int))
        cols=['prior_claims_5y']+(['ncb_years'] if line=='motor' else [])
        ix=pd.Series(np.arange(len(rows)),index=rows.row_id);assert ix.index.is_unique
        for col in cols:future[col]=x.iloc[ix.loc[ids].to_numpy()][col].to_numpy()
        future['exposure']=future.exposure_calendar.to_numpy(float)
        day=((pd.to_datetime(future.period_end)-pd.to_datetime(future.period_start)).dt.days+1)/365.
        assert np.array_equal(future.exposure,day) and future.exposure.gt(0).all()
        future['line']=line
        future['gender']=customers.loc[future.customer_id,'gender'].to_numpy()
        future['marketing_segment']=customers.loc[future.customer_id,'marketing_segment'].to_numpy()
        assert future.gender.notna().all() and future.marketing_segment.notna().all()
        if line=='contents':
            # Keep the original bool representation: source matrix uses0/1
            # while the learned G3/H1 factor keys are "False"/"True".
            telework=pd.read_parquet(tp,columns=['row_id','works_from_home']).set_index('row_id')
            future['works_from_home']=telework.loc[ids,'works_from_home'].to_numpy()
            assert str(future.works_from_home.dtype)=='bool'
        else:future['works_from_home']='__NOT_USED__'
        metadata=OUT/f'future_{line}.parquet';future.to_parquet(metadata,index=False)
        matrixp,modelrows,componentp=old.locations(line)
        modelp=BASE/f'linaje_T2b_v1/modelos/prod/T2b_{line}.txt'
        sources += [matrixp,modelrows,componentp,modelp]
        source_rows=pd.read_parquet(modelrows)
        nb=source_rows.is_test & source_rows.new_business.eq(1)
        expected_nb=future.loc[future.new_business.eq(1),'row_id']
        assert set(source_rows.loc[nb,'row_id'])==set(expected_nb)
        nbtotal+=int(nb.sum())
        bst=lgb.Booster(model_file=str(modelp))
        old.align_matrix(pd.read_parquet(matrixp).loc[nb].iloc[:2],bst)  # No predict.
        renids=future.loc[future.new_business.eq(0),'row_id']
        assert set(cached.loc[cached.line.eq(line)].index)==set(renids)
        kernelp=OLD/f'annual_FSp_kernel_REN_{line}.parquet';sources.append(kernelp)
        kernel=pd.read_parquet(kernelp);assert kernel.index.is_unique and set(kernel.index)==set(renids)
        component=pd.read_parquet(componentp).set_index('row_id').loc[renids]
        for peril in kernel:
            expected=component['f_'+peril].to_numpy()/component.exposure.to_numpy()*component['s_'+peril].to_numpy()
            assert np.array_equal(kernel.loc[renids,peril],expected)
        # Verify the covariate contract underlying old and new shape rules.
        histp=HET/f'inputs_{line}_fold0.parquet';rawp=BASE/f'linaje_T2b_v1/features_{line}.parquet'
        sources += [histp,rawp]
        hist=pd.read_parquet(histp);original=pd.read_parquet(rawp).set_index('row_id').loc[hist.row_id].reset_index()
        assert np.array_equal(het.b.bands(hist,'prior'),het.b.bands(original,'prior'))
        if line=='motor':assert np.array_equal(het.b.bands(hist,'ncb'),het.b.bands(original,'ncb'))
        for held in range(5):
            cp=BASE/f'tanda2_20261025_v1/learning_{line}_fold{held}.json'
            hp=HET/f'learning_H1_{line}_fold{held}.json'
            kp=old.CV/f'learning_{line}_fold{held}.json';sources += [cp,hp,kp]
            c0=w.read(cp)['artifact']['C0'];h1=w.read(hp);kappa=w.read(kp)
            assert het.b.digest(c0['fit_row_ids'])==h1['training_row_ids_digest']
            assert c0['fit_row_ids']==kappa['training_row_ids'] and c0['excluded_fold']==held
            if line!='buildings':sources.append(BASE/f'tanda10_factores_20261026_v1/learning_{line}_fold{held}.json')
        inputs[line]={'future_metadata':w.rel(metadata),'metadata_sha256':w.sha(metadata),
            'T2b_matrix':w.rel(matrixp),'T2b_rows':w.rel(modelrows),'T2b_model':w.rel(modelp),
            'kernel':w.rel(kernelp),'new_T2b_NB_rows':int(nb.sum()),'cached_T2b_REN_rows':len(renids)}
        lineage.append({'line':line,'future_rows':len(future),'historic_prior_NCB_bands_match':True,
            'future_WFH_bool_kept_if_contents':True,'cached_REN_rates_pinned_by_prior_plan':True,
            'cached_FSp_kernel_exact_source_component_algebra':True})
    assert nbtotal==158980
    # New arithmetic adapter fixture, without a source inference or candidate price.
    f=pd.DataFrame({'new_business':[0,0,1,1]});base=np.array([100.,200.,30.,50.])
    same,norm=correct_member(f,base,np.ones(4),np.ones(4),'motor',weight=0.)
    assert np.array_equal(same,base) and norm==1.
    ignored=np.array([1.2,.8,-1e30,np.nan])
    val,_=correct_member(f,base,np.ones(4),ignored,'motor')
    assert np.array_equal(val[2:],base[2:])
    dump(OUT/'preflight.json',{'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'inputs':inputs,'lineage':lineage,
        'sources':{w.rel(p):w.sha(p) for p in sources},'new_source_inference':0,'new_candidate_prices':0,'new_fits':0,
        'new_arithmetic_adapter_identity_and_NB_scope_fixture':True})
    print(json.dumps({'preflight':'passed','new_NB_inference_rows_if_registered':nbtotal,'cached_REN_rows':50083,'new_inference':0,'new_prices':0}))


def register():
    assert not PLAN.exists() and not (OUT/'registration.json').exists()
    pre=w.read(OUT/'preflight.json');p=w.read(PUL/'report.json')['results']['PUL2']
    sources={**pre['sources'],w.rel(OUT/'preflight.json'):w.sha(OUT/'preflight.json'),
        **{a['future_metadata']:a['metadata_sha256'] for a in pre['inputs'].values()}}
    assert all(w.sha(ROOT/path)==v for path,v in sources.items())
    plan={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'registered_numeric_prototype_only',
        'parent':{'path':w.rel(old.PARENT),'sha256':w.sha(old.PARENT),'public_score':.16914,'recipe_author':'Claude','composition_QA_author':'Codex'},
        'hypothesis':'Inspect real2025production plumbing and level/cohort effects of PUL2correction on the actualF3cfile before any external admission. Not a claim that post31passed.',
        'formula':'For each line/frozen outer member k, reconstruct oldG3and H1ultimate period prices on2025 using q=1/calendar exposure and same T2bannual rates. First multiply F3cby(H1_k/G3_k), then apply pure ultimate FSp/T2bshape on REN only with weights. Normalize FsRENshape to the already corrected F3cRENtotal. NBonly gets H1/G3. Equal arithmetic mean of all5member costs; no learned ensemble weights.',
        'shape_weights_REN':WEIGHTS,'age_effect':False,
        'H1_G3':'Closed historical shapes/levels/factors already stored, no recalibration. Future gender/marketing official customer snapshot; contents telework remainsboolto match learned keys. Never apply observedq2025=0.',
        'source_history':'Same explicit historia2 cutoff and restored T2bprod matrices as prior tested wrapper; no extension of report availability, source2021-2024and targetclimatemean2023-2024. Official undated payment/discount/master snapshot features in inheritedT2b remain conditional, not proven known at quote time.',
        'ensemble':'Each of5members was validated singly on its held groups. This future mean is not a nested held-ensemble evaluation. No full historicF3c numerical replay exists; transferring G3/H1ratios to F3cis a new conditional production composition, not proven identical validation.',
        'local_evidence':{'PUL2_delta_vs_G3':p['delta_vs_G3'],'CI95':p['bootstrap95'],'gates':p['gates'],
            'weighted2025_sensitivity':p['weighted2025_sensitivity_delta'],'weightedESSfailed':True,
            'post31_failed':True,'not_statistical_admission':True},
        'budget':{'new_model_fits':0,'new_C0_fits':0,'new_kappa_fits':0,'new_calibration_parameters':0,
            'primary_T2b_NB_inference_calls':3,'primary_T2b_NB_rows':158980,'cached_T2b_REN_rows':50083,
            'new_NB_order_check_calls':3,'new_NB_order_check_rows':96,
            'forward_G3_H1_price_rows':2*5*209063,'forward_own_PUL2_component_price_rows':5*209063,
            'wrapped_member_price_rows':5*209063,'prediction_only_normalizers':110,
            'normalizer_breakdown':{'G3_H1_future':80,'wrapped_FSp_REN':15,'own_PUL2_component':15},
            'new_candidate_CSVs':1,'new_final_candidate_rows':209063,'new_submissions':0},
        'QA':['Official keys/order209063positivefiniteprices and canonicalprecision6',
            'Source/kernel/ratecache pins and exactsource algebra; code/category representations checked',
            'New NBsource wrapper order check; every new inference checkpoint saved',
            'Separate G3/H1forward source of q=1/calendar once, H1/G3and Fsratio scalar/log calculations',
            'FSshape preserves already exposure-corrected RENtotal; NBgets only exposurecorrection',
            'No-correction/zero-weight identity; canonicalkeyshuffling and invalidinputs rejected',
            'ExactIEEErational microCUties-even, independentDecimal256rows; readbackSHAand before/aftercell totals'],
        'submission_allowed':False,'submission_ready':False,'predictive_admission':False,'formal_promotion':False,
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False,'sources':sources}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. Registro un prototipo concreto F3c/PUL2 de 2025, sin vía de envío y sin cambiar el fallo post31. '
        'Se aplicará el cociente H1/G3 de los cinco ámbitos guardados a F3c; luego la forma última FSp solo REN, con los pesos ya fijados y normalización al total REN corregido. NB recibe solo el cambio H1/G3, sin edad. '
        'Media aritmética de cinco miembros, no evaluada como ensemble anidado; transferir la corrección a F3c no reproduce su histórico completo. '
        'Se reutilizan las 50.083 tasas REN verificadas y los kernels FSp; faltan tres inferencias T2b para 158.980 NB, más 96 filas de control de orden. '
        'Se cotejaron bandas históricas, claves, ancestros y representación bool de teletrabajo, que difiere del 0/1 de la matriz. '
        'Para último 2025 se usa exposición calendario y q=1, no la completitud observada cero. Cero ajustes, C0, kappas o parámetros nuevos; 110 normalizadores (80 de G3/H1, 15 de la composición y 15 del componente propio de contraste) y un CSV revisable. '
        'El prototipo seguirá sin admisión estadística o de upload. B00/F3c/PUL2 y todas las alternativas intactos; 2024 abierto. Plan: '+w.rel(PLAN)+'.',encoding='utf8')
    response=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
        '--id','COD-S2-20261026-MISION017-F3C-PUL2-PROTO-PREVIO','--asunto','Prototipo F3c/PUL2 registrado: producción real sin upload',
        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    dump(OUT/'registration.json',{'plan_sha256':w.sha(PLAN),'forum':json.loads(response.stdout)})
    print(json.dumps({'registered':True,'submission_allowed':False,'forum':json.loads(response.stdout)}))


def run():
    assert not (OUT/'started.json').exists() and not (OUT/'report.json').exists()
    plan=w.read(PLAN);assert w.sha(PLAN)==w.read(OUT/'registration.json')['plan_sha256']
    assert all(w.sha(ROOT/p)==v for p,v in plan['sources'].items())
    dump(OUT/'started.json',{'utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid(),'plan_sha256':w.sha(PLAN)})
    parent=pd.read_csv(old.PARENT,dtype=str);parent_ticks=io.ticks(parent);base=parent_ticks/1e6
    cohort=pd.read_parquet(old.COHORT).set_index('row_id').loc[parent.row_id]
    cached=pd.read_parquet(OLD/'annual_T2b_REN_2025.parquet').set_index('row_id')
    members=np.full((len(parent),5),np.nan);component_frames=[];normalizers={};inference=[];controls=[]
    pre=w.read(OUT/'preflight.json')
    with threadpool_limits(limits=2):
        for line,meta in pre['inputs'].items():
            source_rows=pd.read_parquet(ROOT/meta['T2b_rows']);matrix=pd.read_parquet(ROOT/meta['T2b_matrix'])
            mask=source_rows.is_test&source_rows.new_business.eq(1)
            model=lgb.Booster(model_file=str(ROOT/meta['T2b_model']))
            X=old.align_matrix(matrix.loc[mask],model)
            annual=np.exp(model.predict(X,raw_score=True,num_threads=2))
            assert np.isfinite(annual).all() and (annual>0).all()
            nb=pd.DataFrame({'row_id':source_rows.loc[mask,'row_id'].to_numpy(),'annual_T2b':annual})
            rp=OUT/f'annual_T2b_NB_{line}.parquet';nb.to_parquet(rp,index=False)
            dump(OUT/f'inference_{line}.json',{'utc':datetime.now(timezone.utc).isoformat(),'rows':len(nb),'model_sha256':w.sha(ROOT/meta['T2b_model']),
                'rate_sha256':w.sha(rp),'new_primary_inference_calls':1})
            sample=np.linspace(0,len(X)-1,32,dtype=int)[::-1]
            replay=np.exp(model.predict(X.iloc[sample],raw_score=True,num_threads=2))
            assert np.array_equal(replay,annual[sample])
            rate=pd.concat([nb.set_index('row_id'),cached.loc[cached.line.eq(line),['annual_T2b']]])
            assert rate.index.is_unique
            source_metadata=pd.read_parquet(ROOT/meta['future_metadata']);ids=source_metadata.row_id.copy()
            f=canonical_metadata(source_metadata,ids,rate)
            assert f.equals(canonical_metadata(source_metadata.iloc[::-1],ids,rate.iloc[::-1]))
            for invalid in [rate.drop(index=ids.iloc[0]),pd.concat([rate,rate.iloc[:1]]),rate.assign(annual_T2b=-1.)]:
                try:canonical_metadata(source_metadata,ids,invalid)
                except (AssertionError,KeyError,ValueError):pass
                else:raise AssertionError('Invalid future rates accepted')
            kernel=pd.read_parquet(ROOT/meta['kernel']);ren=f.new_business.eq(0).to_numpy()
            indices=np.flatnonzero(cohort.line.eq(line).to_numpy());assert np.array_equal(parent.row_id.iloc[indices],ids)
            line_base=base[indices];frame=f[['row_id','line','year','new_business','exposure','annual_raw_T2b']].copy()
            for held in range(5):
                n3=w.read(BASE/f'tanda2_20261025_v1/learning_{line}_fold{held}.json')['artifact']
                stages=[] if line=='buildings' else w.read(BASE/f'tanda10_factores_20261026_v1/learning_{line}_fold{held}.json')['stages']
                h1a=w.read(HET/f'learning_H1_{line}_fold{held}.json')
                g3,ng=G3_future(f,n3,stages);h1,nh=het.replay(f,h1a,ultimate=True)
                assert (g3>0).all() and (h1>0).all() and np.isfinite(g3).all() and np.isfinite(h1).all()
                ratio_link=h1/g3
                ka=w.read(old.CV/f'learning_{line}_fold{held}.json')['perils']
                r=np.ones(len(f));risk=sum(ka[p]['kappa']*kernel.loc[ids[ren],p].to_numpy() for p in kernel)
                r[ren]=risk/f.annual_raw_T2b.to_numpy()[ren]
                corrected,norm=correct_member(f,line_base,ratio_link,r,line)
                own,_=correct_member(f,g3,ratio_link,r,line)
                # Independent scalar path and expected exposure-only NB.
                for j in np.unique(np.linspace(0,len(f)-1,16,dtype=int)):
                    assert np.isclose(scalar_forward(f,j,n3,stages,ng),g3[j],rtol=2e-12,atol=1e-9)
                    assert np.isclose(scalar_forward(f,j,h1a,h1a['stages'],nh),h1[j],rtol=2e-12,atol=1e-9)
                    expected=math.exp(math.log(float(line_base[j]))+math.log(float(h1[j]))-math.log(float(g3[j])))
                    if ren[j]:expected*=math.exp(WEIGHTS[line]*math.log(float(r[j]))-math.log(norm))
                    assert np.isclose(expected,corrected[j],rtol=2e-12,atol=1e-9)
                assert np.array_equal(corrected[~ren],(line_base*ratio_link)[~ren])
                identity,_=correct_member(f,line_base,np.ones(len(f)),np.ones(len(f)),line,weight=0.)
                assert np.array_equal(identity,line_base)
                members[indices,held]=corrected
                frame[f'G3_{held}']=g3;frame[f'H1_{held}']=h1;frame[f'own_PUL2_{held}']=own
                frame[f'ratio_H1_G3_{held}']=ratio_link;frame[f'ratio_ultimate_{held}']=r
                normalizers[f'{line}|{held}']={'G3_future':ng,'H1_future':nh,'FSp_REN':norm,
                    'base_REN_total_after_link':float((line_base*ratio_link)[ren].sum()),'final_REN_total':float(corrected[ren].sum())}
            frame.to_parquet(OUT/f'component_forward_{line}.parquet',index=False);component_frames.append(frame)
            inference.append({'line':line,'new_NB_rows':len(nb),'cached_REN_rows':int(ren.sum()),'new_order_check_rows':32,'new_order_check_exact':True})
            controls.append({'line':line,'NB_only_observation_correction_exact':True,'REN_shape_total_preserved':True,
                'zero_correction_identity_exact':True,'independent_scalar_log_price_math':True,
                'independent_G3_H1_ultimate_forward_exposure_once':True,'canonical_key_shuffle_exact':True,
                'missing_duplicate_negative_future_rate_rejected':True,'observed_zero_markers_ignored_by_ultimate':True})
            print(json.dumps({'line':line,'NB_inferred':len(nb),'future_price_members':5,'complete':True}),flush=True)
    assert np.isfinite(members).all() and (members>0).all()
    values=members.mean(axis=1);ticks=rounding(values)
    for i in np.unique(np.linspace(0,len(ticks)-1,256,dtype=int)):
        with localcontext() as ctx:
            ctx.prec=100
            expected=int((Decimal.from_float(float(values[i]))*Decimal(1000000)).quantize(Decimal(1),rounding=ROUND_HALF_EVEN))
        assert expected==int(ticks[i])
    csvpath=OUT/'F3c_PUL2_prototipo_2025.csv';io.write_csv(csvpath,parent.row_id,ticks)
    back=pd.read_csv(csvpath,dtype=str);assert np.array_equal(back.row_id,parent.row_id) and np.array_equal(io.ticks(back),ticks)
    pd.DataFrame({'row_id':parent.row_id,**{f'member{k}':members[:,k] for k in range(5)},'unrounded_mean':values}).to_parquet(OUT/'member_prices_2025.parquet',index=False)
    dump(OUT/'normalizers.json',normalizers)
    cells=[]
    for (line,nb),ii in cohort.reset_index().groupby(['line','new_business']).groups.items():
        ii=np.asarray(list(ii));ratio=ticks[ii]/parent_ticks[ii]
        cells.append({'line':line,'new_business':int(nb),'rows':len(ii),'changed_rows':int(np.count_nonzero(ticks[ii]!=parent_ticks[ii])),
            'parent_total_CU':float(parent_ticks[ii].sum()/1e6),'new_total_CU':float(ticks[ii].sum()/1e6),
            'ratio_quantiles':np.quantile(ratio,[0,.01,.5,.99,1]).tolist()})
    assert all(w.sha(ROOT/p)==v for p,v in plan['sources'].items())
    report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'numeric_prototype_complete_not_submission_ready',
        'CSV':{'path':w.rel(csvpath),'sha256':w.sha(csvpath),'bytes':csvpath.stat().st_size,'rows':len(back),'total_CU':int(ticks.sum())/1e6},
        'cells':cells,'inferences':inference,'numeric_controls':controls,'new_model_fits':0,'new_C0_fits':0,'new_kappa_fits':0,
        'primary_T2b_new_NB_calls':3,'primary_T2b_new_NB_rows':158980,'new_order_check_calls':3,'new_order_check_rows':96,
        'cached_T2b_REN_rows_reused':50083,'prediction_only_normalizers':110,
        'normalizer_breakdown':{'G3_H1_future':80,'wrapped_FSp_REN':15,'own_PUL2_component':15},
        'zero_identity_control_normalizers_separate':15,'new_CSVs':1,'new_submissions':0,
        'independent_Decimal_rounding_and_readback_exact':True,'official209063order_exact':True,
        'parent_F3c_unchanged':True,'submission_allowed':False,'submission_ready':False,'predictive_admission':False,'formal_promotion':False,
        'post31_failure_preserved':True,'fold_mean_not_nested_validated':True,'full_historic_F3c_transfer_not_validated':True,
        'plan_sha256':w.sha(PLAN),'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(OUT/'report.json',report)
    print(json.dumps({k:report[k] for k in ['status','CSV','cells','new_model_fits','new_C0_fits','new_submissions','submission_allowed']},ensure_ascii=True))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','strengthen','register','run']);a=p.parse_args()
    {'prepare':prepare,'strengthen':strengthen,'register':register,'run':run}[a.mode]()
