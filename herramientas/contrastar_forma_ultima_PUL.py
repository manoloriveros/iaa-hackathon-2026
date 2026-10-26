"""Descompone forma última y observación; mezcla fija REN con artefactos guardados."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import importlib.util
import json
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
BASE=R/'privado/semana2/mision017_fase2';PARENT=BASE/'FSp_REN_G3_prod_contraste_20261026_v1'
HET=BASE/'enlace_HET_20261026_v1';OUT=BASE/'forma_ultima_PUL_20261026_v1'
PROPOSAL=R/'registro/semana2_forma_ultima_observacion_propuesta_v0.json'
PLAN=R/'registro/semana2_forma_ultima_PUL_plan_v1.json'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'));sys.stdout.reconfigure(encoding='utf8')
import numpy as np
import pandas as pd
from scipy.special import logsumexp
from threadpoolctl import threadpool_limits


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


d=load('PUL_existing_statistics',R/'herramientas/glm_discrepancia_A1S.py')
w=d.w;WEIGHTS=w.read(PROPOSAL)['fixed_weights_REN']


def dump(p,v):
    assert not p.exists();p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')


def ratio(f,perils,kappa):
    components=np.column_stack([kappa[p]*f['f_'+p].to_numpy(float)*f['s_'+p].to_numpy(float) for p in perils])
    denominator=f.annual_raw_T2b.to_numpy(float)*f.exposure.to_numpy(float)
    assert (components>0).all() and np.isfinite(components).all() and (denominator>0).all()
    r=components.sum(axis=1)/denominator
    assert np.isfinite(r).all() and (r>0).all()
    return r,components


def apply(f,base,r,line,weight=None):
    weight=WEIGHTS[line] if weight is None else weight
    result=base.copy();norms={}
    for year in sorted(f.year.unique()):
        mask=f.year.eq(year).to_numpy()&f.new_business.eq(0).to_numpy();assert mask.any()
        factor=r[mask]**weight
        norm=float(np.sum(base[mask]*factor)/np.sum(base[mask]))
        result[mask]=base[mask]*factor/norm;norms[str(year)]=norm
        assert abs(result[mask].sum()/base[mask].sum()-1)<1e-12
    assert np.array_equal(result[f.new_business.eq(1)],base[f.new_business.eq(1)])
    assert np.isfinite(result).all() and (result>0).all()
    return result,norms


def prepare():
    assert not OUT.exists() and not PLAN.exists();OUT.mkdir()
    hp=w.read(HET/'report.json');assert hp['primary']=='H2'
    assert w.read(R/'registro/semana2_enlace_HET_plan_v1.json')['bootstrap']['seed']==2026102614
    prices=pd.read_parquet(HET/'oof_2023_2024.parquet').set_index('row_id')
    pre=w.read(PARENT/'preflight.json');paths=[Path(__file__),Path(d.__file__),PROPOSAL,HET/'report.json',
        HET/'completion_receipt.json',HET/'oof_2023_2024.parquet',HET/'statistics_H1/bootstrap.npy',
        R/'registro/semana2_enlace_HET_plan_v1.json',PARENT/'preflight.json',PARENT/'report.json']
    cache={};scopes=[];math=[]
    for scope in pre['scopes']:
        line=scope['line'];held=scope['held'];perils=pre['perils'][line]
        inp=ROOT/scope['input'];assert w.sha(inp)==scope['sha256'];paths.append(inp)
        kp=PARENT/f'learning_{line}_fold{held}.json';cp=BASE/f'tanda2_20261025_v1/learning_{line}_fold{held}.json'
        h1p=HET/f'learning_H1_{line}_fold{held}.json';paths += [kp,cp,h1p]
        f=pd.read_parquet(inp);training=f.fold.ne(held);a=w.read(kp);c0=w.read(cp)['artifact']['C0'];h1=w.read(h1p)
        assert sorted(f.loc[training,'row_id'])==a['training_row_ids']==c0['fit_row_ids']
        assert d.c.b.digest(a['training_row_ids'])==h1['training_row_ids_digest']
        assert sorted(set(f.loc[training,'group_id']))==a['training_groups']
        assert not set(f.loc[training,'group_id']).intersection(f.loc[~training,'group_id'])
        if line not in cache:
            rp=BASE/f'linaje_T2b_v1/raw_rates_{line}.parquet';paths.append(rp)
            cache[line]=pd.read_parquet(rp,columns=['row_id','annual_raw_T2b']).set_index('row_id')
        f=f.loc[~training].copy();f['annual_raw_T2b']=cache[line].loc[f.row_id,'annual_raw_T2b'].to_numpy()
        reference=prices.loc[f.row_id]
        for col in ['T0','fold','group_id','year','new_business']:assert np.array_equal(f[col],reference[col])
        assert np.array_equal(f.baseline_G3,reference.G3)
        f['baseline_H1']=reference.H1.to_numpy()
        kappa={p:a['perils'][p]['kappa'] for p in perils};r,components=ratio(f,perils,kappa)
        q=np.column_stack([f['q_'+p].to_numpy() for p in perils])
        qouter=np.sum(components*q,axis=1)/np.sum(components,axis=1)
        qglobal=f.e_cost_scope.to_numpy()/f.exposure.to_numpy()
        old=np.sum(components*q,axis=1)/f.unshaped_T2b.to_numpy()
        decomposition=r*qouter/qglobal
        err=float(np.max(np.abs(old/decomposition-1)));assert err<1e-12
        independent=np.exp(logsumexp(np.log(components),axis=1)-np.log(f.annual_raw_T2b.to_numpy())-np.log(f.exposure.to_numpy()))
        assert np.allclose(r,independent,rtol=1e-13)
        sample=f.iloc[:min(32,len(f))].copy();original=ratio(sample,perils,kappa)[0]
        bad=sample.copy()
        for col in bad:
            if col in ['T0','reserve'] or col.startswith(('q_','n_','y_')):bad[col]=-1e30
        assert np.array_equal(original,ratio(bad,perils,kappa)[0])
        f['ratio_ultimate']=r
        # No new price is computed in preflight; formula-only fixtures.
        fake=pd.DataFrame({'year':[2023]*4+[2024]*4,'new_business':[0,0,1,1]*2})
        base=np.arange(1,9,dtype=float);rat=np.linspace(.5,2.,8)
        zero,_=apply(fake,base,rat,line,weight=0.);assert np.array_equal(zero,base)
        neutral,_=apply(fake,base,np.ones(8),line);assert np.array_equal(neutral,base)
        fp=OUT/f'inputs_{line}_fold{held}.parquet';f.to_parquet(fp,index=False)
        scopes.append({'line':line,'held':held,'input':w.rel(fp),'sha256':w.sha(fp),'held_rows':len(f)})
        math.append({'line':line,'held':held,'source_ancestry_membership_exact':True,
                     'old_ratio_equals_ultimate_ratio_times_completion_ratio_max_relative_error':err,
                     'independent_logmath':True,'ultimate_ratio_cost_count_reserve_q_payload_invariant':True,
                     'zero_weight_and_neutral_ratio_identity_exact':True})
    assert sum(s['held_rows'] for s in scopes)==109296
    dump(OUT/'preflight.json',{'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'scopes':scopes,
        'sources':{w.rel(p):w.sha(p) for p in paths},'controls':math,'new_fits':0,'new_real_prices':0,'new_scores':0})
    print(json.dumps({'preflight':'passed','scopes':15,'real_new_prices':0,'new_fits':0}))


def register():
    assert not PLAN.exists() and not (OUT/'registration.json').exists()
    pre=w.read(OUT/'preflight.json');proposal=w.read(PROPOSAL)
    sources={**pre['sources'],w.rel(OUT/'preflight.json'):w.sha(OUT/'preflight.json'),**{s['input']:s['sha256'] for s in pre['scopes']}}
    assert all(w.sha(ROOT/p)==v for p,v in sources.items())
    plan={**proposal,'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'registered_before_new_price_score',
        'primary_candidate':'PUL2','models':{'PUL1':'G3plus ultimate-only FSpRENshape','PUL2':'H1plus same ultimate-only FSpRENshape'},
        'criterion':w.read(d.PLAN)['criterion'],'bootstrap':{'replicates':2000,'seed':2026102614,'unit':'same global connected component, same paired draws as HET',
            'incremental_vs_H1':'PUL2vsG3bootstrap minus storedH1vsG3bootstrap, paired. Verify source/group/outcome equality; no additional resampling.'},
        'incremental_guard':{'PUL2_vs_H1_point_positive':True,'NB_exact_H1':True},
        'budget':proposal['budget_if_registered'],'sources':sources,
        'limits':['Source costs/peril profiles and reserves remain conditional proxies; no ultimate truth identification',
                  'H1was a declared HETablation; its use here is an explicit adaptive decision, not independent confirmation or formal promotion',
                  'No complete historicF3c comparator; no claim gain against G3equals publicgain',
                  '2024adaptive, weightedESSfailed, no automatic finalprices or upload']}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. Registro PUL2 primario y PUL1 como comparación fija antes de nuevos precios o scores. '
        'La identidad comprobada muestra que RFS mezclaba forma última con razón de completitudes. Ahora se usa solo sum(kappa*f*s)/(T2b_anual*exposición calendario), con exposición una sola vez. '
        'PUL2 aplica esa forma sobre H1; PUL1 sobre G3. H1 sigue siendo una ablation anterior, usada aquí por decisión adaptativa explícita; no se convierte retrospectivamente en primario o ganador confirmado. '
        'Se mantienen pesos .25/.25/.5 solo en renovaciones. NB de PUL2 será exactamente H1; NB de PUL1, G3. '
        'No hay ajuste nuevo, C0, kappa o inferencia fuente. Solo 60 normalizadores de predicciones, sin etiquetas. '
        'Pasaron la identidad algebraica, grupos/ancestros, aritmética logarítmica e invariancia de la forma última a costes/recuentos/reservas/q alterados. '
        'Criterios previos y guardas conservados; sin precios finales de 2025 ni envíos. B00/F3c y alternativas intactos; 2024 abierto. Plan: '+w.rel(PLAN)+'.',encoding='utf8')
    response=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
        '--id','COD-S2-20261026-MISION017-PUL-PREVIO','--asunto','PUL registrado: separar forma última y completitud, sin nuevos ajustes',
        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    dump(OUT/'registration.json',{'plan_sha256':w.sha(PLAN),'forum':json.loads(response.stdout)})
    print(json.dumps({'registered':True,'primary':'PUL2','forum':json.loads(response.stdout)}))


def run():
    assert not (OUT/'report.json').exists() and not (OUT/'started.json').exists()
    plan=w.read(PLAN);assert w.sha(PLAN)==w.read(OUT/'registration.json')['plan_sha256']
    assert all(w.sha(ROOT/p)==v for p,v in plan['sources'].items())
    import os
    dump(OUT/'started.json',{'utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid()})
    p=pd.read_parquet(HET/'oof_2023_2024.parquet');idx=pd.Series(p.index.to_numpy(),index=p.row_id)
    p['PUL1']=np.nan;p['PUL2']=np.nan;checks=[]
    for scope in w.read(OUT/'preflight.json')['scopes']:
        f=pd.read_parquet(ROOT/scope['input']);r=f.ratio_ultimate.to_numpy(float)
        for name,col in [('PUL1','baseline_G3'),('PUL2','baseline_H1')]:
            base=f[col].to_numpy(float);pred,norm=apply(f,base,r,scope['line'])
            altered=f.copy();altered[['T0','reserve']]=-1e30
            other,nn=apply(altered,base,r,scope['line']);assert np.array_equal(pred,other) and norm==nn
            for year in [2023,2024]:
                mask=f.year.eq(year).to_numpy()&f.new_business.eq(0).to_numpy()
                independent=np.exp(np.log(base[mask])+WEIGHTS[scope['line']]*np.log(r[mask]))
                independent*=base[mask].sum()/independent.sum()
                assert np.allclose(independent,pred[mask],rtol=1e-13,atol=1e-9)
            p.loc[idx.loc[f.row_id].to_numpy(),name]=pred
            saved=OUT/f'application_{name}_{scope["line"]}_fold{scope["held"]}.json'
            dump(saved,{'held_normalizers':norm,'held_rows':len(f),'NB_exact_parent':True})
        checks.append({'line':scope['line'],'held':scope['held'],'payload_invariant_new_formula':True,
                       'independent_price_logmath':True,'NB_exact_parents':True})
    assert p[['PUL1','PUL2']].notna().all().all()
    p.to_parquet(OUT/'oof_2023_2024.parquet',index=False);results={}
    with threadpool_limits(limits=2):
        for name in ['PUL1','PUL2']:
            statsout=OUT/f'statistics_{name}';statsout.mkdir();d.OUT=statsout
            result=d.statistics(p[['row_id','line','year','group_id','fold','new_business','T0','N3','G3',name]].rename(columns={name:'D1'}),plan)
            result['scores'][name]=result['scores'].pop('D1');results[name]=result
    parent=pd.read_parquet(HET/'oof_2023_2024.parquet')
    for col in ['row_id','group_id','fold','T0','G3','H1']:assert np.array_equal(parent[col],p[col])
    old=w.read(HET/'report.json')['results']['H1']
    draws=np.load(OUT/'statistics_PUL2/bootstrap.npy')-np.load(HET/'statistics_H1/bootstrap.npy')
    np.save(OUT/'incremental_vs_H1_bootstrap.npy',draws)
    incremental=float(results['PUL2']['delta_vs_G3']-old['delta_vs_G3'])
    yy=p.T0.to_numpy();den=d.unit(yy,np.full(len(yy),yy.mean())).sum()
    direct=float((d.unit(yy,p.H1.to_numpy())-d.unit(yy,p.PUL2.to_numpy())).sum()/den)
    assert abs(direct-incremental)<1e-12
    assert np.array_equal(p.loc[p.new_business.eq(1),'H1'],p.loc[p.new_business.eq(1),'PUL2'])
    assert all(w.sha(ROOT/path)==v for path,v in plan['sources'].items())
    report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'complete_exploratory_no_formal_admission',
        'primary':'PUL2','results':results,'incremental_vs_H1':{'delta':incremental,'paired_bootstrap95':np.quantile(draws,[.025,.975]).tolist(),
            'point_positive':incremental>0,'same_group_outcome_order_and_seed_checked':True},
        'numeric_controls':checks,'new_price_estimator_fits':0,'new_C0_fits':0,'new_kappa_fits':0,
        'new_source_inference':0,'held_prediction_normalizers':60,'new_final_test_prices':0,'new_submissions':0,
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False,'plan_sha256':w.sha(PLAN),'limits':plan['limits']}
    dump(OUT/'report.json',report)
    print(json.dumps({'results':{name:{k:r[k] for k in ['scores','delta_vs_G3','bootstrap95','fold_contributions','year_contributions','post31_delta','gates','weighted2025_sensitivity_delta']} for name,r in results.items()},'incremental_vs_H1':report['incremental_vs_H1']},ensure_ascii=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','register','run']);a=parser.parse_args()
    {'prepare':prepare,'register':register,'run':run}[a.mode]()
