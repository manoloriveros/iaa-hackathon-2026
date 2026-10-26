"""Diagnóstico de mezcla de perils, con artefactos guardados y cero aprendizaje."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import importlib.util
import json
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
BASE=R/'privado/semana2/mision017_fase2'
PARENT=BASE/'FSp_REN_G3_prod_contraste_20261026_v1'
PREVIOUS=BASE/'completitud_por_riesgo_diagnostico_20261026_v1'
OUT=BASE/'completitud_por_riesgo_diagnostico_20261026_v2'
PLAN=R/'registro/semana2_completitud_por_riesgo_diagnostico_plan_v2.json'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'));sys.stdout.reconfigure(encoding='utf8')
import numpy as np
import pandas as pd
from scipy.special import logsumexp

sp=importlib.util.spec_from_file_location('risk_completion_writer',R/'herramientas/registrar_avance_mision017_fase2.py')
w=importlib.util.module_from_spec(sp);sp.loader.exec_module(w)


def dump(path,value):
    assert not path.exists();path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')


def conditional_q(f,perils,kappa):
    # No response, reserve, count or observed-cost field is accessed here.
    r=np.column_stack([f['f_'+p].to_numpy(float)*f['s_'+p].to_numpy(float)*kappa[p] for p in perils])
    q=np.column_stack([f['q_'+p].to_numpy(float) for p in perils])
    assert np.isfinite(r).all() and (r>0).all()
    assert np.isfinite(q).all() and (q>=0).all() and (q<=1+1e-10).all()
    result=np.sum(r*q,axis=1)/np.sum(r,axis=1)
    assert np.all(result>=q.min(axis=1)-1e-12) and np.all(result<=q.max(axis=1)+1e-12)
    return result,r,q


def register():
    assert not PLAN.exists() and not OUT.exists();OUT.mkdir()
    pre=w.read(PARENT/'preflight.json')
    failure=w.read(PREVIOUS/'failure_receipt.json')
    assert len(failure['completed_scope_outputs'])==8
    sources=[Path(__file__),R/'herramientas/diagnosticar_completitud_por_riesgo.py',
             R/'registro/semana2_completitud_por_riesgo_diagnostico_plan_v1.json',PREVIOUS/'failure_receipt.json',
             PARENT/'preflight.json',PARENT/'report.json',BASE/'residuo_aditivo_DT1_20261026_v1/report.json']
    for name,value in failure['completed_scope_outputs'].items():
        path=PREVIOUS/name;assert w.sha(path)==value;sources.append(path)
    for a in pre['scopes']:
        assert w.sha(ROOT/a['input'])==a['sha256']
        sources+=[ROOT/a['input'],PARENT/f'learning_{a["line"]}_fold{a["held"]}.json',
                  BASE/f'tanda2_20261025_v1/learning_{a["line"]}_fold{a["held"]}.json']
    plan={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'registered_diagnostic_only_no_new_fit_score',
        'question':'Does the existing global peril mixture in effective cost exposure differ materially from per-risk mixtures implied by saved source f*s and separately by frozen outer-scope shrunk kappa*f*s?',
        'mathematics':'Conditional on ultimate risk components r_ip and known peril completion q_ip, E(observed_i)=exposure_i*sum_p r_ip*q_ip and q_risk_i=sum_p(r_ip*q_ip)/sum_p(r_ip). Global fixed mixture is exact only under appropriate common composition or equal peril completions. These are modeling assumptions, not an identified ultimate truth.',
        'two_profiles':'Source-only f*s; and the existing frozen outer-scope kappa*f*s. No per-peril or total recalibration, count/mark/C0 estimation, curve fitting or parameter search.',
        'repair':{'previous_failure':w.rel(PREVIOUS/'failure_receipt.json'),
                  'change':'Accept legitimate per-perilq=0with log(0)=-infinity in logsumexp; do not floor, refit or change original completions.',
                  'completed_scope_outputs_reused_without_recomputing':failure['completed_scope_outputs'],
                  'only_7_pending_scopes_run_new_numeric_controls':True,'criteria_parameters_profiles_unchanged':True},
        'scope':'Same109296historical emerging2023/2024rows and five stored global component folds; summarize held portions only. No2025prices or new model inference.',
        'measure':'Dimensionless q_risk/q_global quantiles and fraction with >5percent multiplicative difference, by line/year/business; completion itself and math identities. Do not price, score or rank candidates.',
        'materiality_screen_fixed_before_readout':{'multiplicative_difference_threshold':1.05,'fraction_in_cell_threshold':.05,
           'meaning':'A descriptive need-for-investigation screen only; not an acceptance rule, significance test or proof of a better model.'},
        'controls':['Parent pinned input hashes','Outer kappa/C0 train row/group membership and held exclusion',
            'Existing q_global equals saved C0mixture of peril completions','Equivalent log-sum-exp ratio arithmetic',
            'Invariance to common risk scaling and poisoned observed T0/reserve/count/cost fields',
            'Equal-peril completion reduces to common q; fixed C0mixture reduces to global q; invalid inputs rejected'],
        'budget':{'new_model_fits':0,'new_C0_fits':0,'new_calibrations':0,'new_model_inference':0,'new_price_scores':0,'new_final_test_prices':0,'new_submissions':0},
        'limits':['f*s with original cost-completion count offset is a cost proxy, not separately identified ultimate frequency/severity',
            'Frozen target kappa is conditional and exploratory; no independent inner validation or causal mix identification',
            'Risk-dependent completion does not resolve tail/reserve adequacy or master vintages',
            'Source2024and target climate2023/24information conditional on the supplied snapshot;2024adaptive development',
            'No change to target/exposure, submission or model adoption follows from this diagnostic alone'],
        '2024_open':True,'B00_all_alternatives_preserved':True,'sources':{w.rel(p):w.sha(p) for p in sources}}
    dump(PLAN,plan)
    body=OUT/'forum_previo.md'
    body.write_text('Codex. Enmienda técnica antes de continuar el diagnóstico: una completitud de subsidencia es exactamente cero, legítima en su ámbito; v1 exigía positividad estricta y se detuvo. Se acepta cero con log(0)=-infinito, sin sustituirlo por un mínimo ni cambiar curvas. Los ocho ámbitos completos se reutilizan por hash y solo se calculan los siete pendientes. Se conservan ambas versiones y el fallo, sin cambios de perfiles o filtro descriptivo. Registro un diagnóstico distinto del enlace de observación, sin nuevos ajustes o scores. '
        'Compararé la completitud global por mezcla constante con la que implican los perfiles por peril f*s ya guardados y, aparte, sus kappas exteriores ya estimadas. '
        'Solo se medirán diferencias de completitud en los folds retenidos de 2023/2024, con matemáticas y procedencia comprobadas. '
        'La fórmula es una media de completitudes por pesos de riesgo, condicionada a que esos pesos representen el coste de último; este supuesto no queda identificado por el diagnóstico. '
        'Se fija antes de leer el resultado un filtro descriptivo de diferencias multiplicativas mayores del 5% en al menos el 5% de una celda, sin usarlo como aprobación predictiva. '
        'No se reestima C0, momentos o precios, no se puntúa ni modifica el objetivo. B00/F3c y alternativas intactos; 2024 abierto. Plan: '+w.rel(PLAN)+'.',encoding='utf8')
    response=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
        '--id','COD-S2-20261026-MISION017-COMPLETITUD-RIESGO-V2-PREVIO','--asunto','Completitud por riesgo: cero legítimo y reutilización de ocho ámbitos',
        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    dump(OUT/'registration.json',{'plan_sha256':w.sha(PLAN),'forum':json.loads(response.stdout)})
    print(json.dumps({'registered':True,'new_fits':0,'forum':json.loads(response.stdout)}))


def run():
    assert not (OUT/'report.json').exists()
    plan=w.read(PLAN);assert w.sha(PLAN)==w.read(OUT/'registration.json')['plan_sha256']
    assert all(w.sha(ROOT/p)==v for p,v in plan['sources'].items())
    pre=w.read(PARENT/'preflight.json');results=[];checks=[];outputs=[]
    for scope in pre['scopes']:
        line=scope['line'];held=scope['held'];perils=pre['perils'][line]
        f=pd.read_parquet(ROOT/scope['input']);train=f.fold.ne(held)
        c0=w.read(BASE/f'tanda2_20261025_v1/learning_{line}_fold{held}.json')['artifact']['C0']
        saved=w.read(PARENT/f'learning_{line}_fold{held}.json')
        assert sorted(f.loc[train,'row_id'])==c0['fit_row_ids']==saved['training_row_ids']
        assert sorted(set(f.loc[train,'group_id']))==saved['training_groups']
        assert c0['excluded_fold']==held and not set(f.loc[train,'group_id']).intersection(f.loc[~train,'group_id'])
        valid=f.loc[~train].copy()
        qglobal=valid.e_cost_scope.to_numpy(float)/valid.exposure.to_numpy(float)
        previous=PREVIOUS/f'held_completion_{line}_fold{held}.parquet'
        if previous.exists():
            assert w.sha(previous)==plan['repair']['completed_scope_outputs_reused_without_recomputing'][previous.name]
            record=pd.read_parquet(previous)
            assert np.array_equal(record.row_id,valid.row_id) and np.array_equal(record.q_global,qglobal)
            for profile in ['source','outer_saved']:
                ratio=record['ratio_'+profile].to_numpy();value=record['q_'+profile].to_numpy()
                for (year,nb),ix in record.groupby(['year','new_business']).groups.items():
                    local=record.index.get_indexer(ix);rr=ratio[local]
                    fraction=float(np.mean(np.abs(np.log(rr))>np.log(1.05)))
                    results.append({'line':line,'held':held,'profile':profile,'year':int(year),'new_business':int(nb),'rows':len(local),
                        'ratio_quantiles':np.quantile(rr,[0,.01,.5,.99,1]).tolist(),'fraction_factor_difference_gt_1_05':fraction,
                        'materiality_screen':fraction>=.05,'completion_mean':float(value[local].mean()),'global_completion_mean':float(qglobal[local].mean()),
                        'reused_complete_v1_output':True})
            outputs.append({'path':w.rel(previous),'sha256':w.sha(previous),'rows':len(record),'reused_without_q_recalculation':True})
            checks.append({'line':line,'held':held,'C0_and_kappa_group_membership_exact':True,
                'reused_v1_complete_flow_controls_before_output_commit':True,'completed_output_hash_exact':True})
            continue
        qm=sum(c0['mixture'][p]*valid['q_'+p].to_numpy(float) for p in perils)
        assert np.allclose(qglobal,qm,rtol=2e-13,atol=1e-14)
        record=valid[['row_id','line','year','new_business','fold','group_id']].copy();record['q_global']=qglobal
        for profile,kappa in [('source',{p:1. for p in perils}),('outer_saved',{p:saved['perils'][p]['kappa'] for p in perils})]:
            value,r,q=conditional_q(valid,perils,kappa)
            logq=np.full(q.shape,-np.inf);np.log(q,out=logq,where=q>0)
            alternate=np.exp(logsumexp(np.log(r)+logq,axis=1)-logsumexp(np.log(r),axis=1))
            assert np.allclose(value,alternate,rtol=3e-14,atol=1e-14)
            ratio=value/qglobal;record['q_'+profile]=value;record['ratio_'+profile]=ratio
            for (year,nb),ix in valid.groupby(['year','new_business']).groups.items():
                local=valid.index.get_indexer(ix);rr=ratio[local]
                fraction=float(np.mean(np.abs(np.log(rr))>np.log(1.05)))
                results.append({'line':line,'held':held,'profile':profile,'year':int(year),'new_business':int(nb),'rows':len(local),
                    'ratio_quantiles':np.quantile(rr,[0,.01,.5,.99,1]).tolist(),'fraction_factor_difference_gt_1_05':fraction,
                    'materiality_screen':fraction>=.05,'completion_mean':float(value[local].mean()),'global_completion_mean':float(qglobal[local].mean())})
            # Controls change only the diagnostic inputs, not any learned model.
            sample=valid.iloc[:min(32,len(valid))].copy()
            initial=conditional_q(sample,perils,kappa)[0]
            poisoned=sample.copy()
            for col in poisoned:
                if col in ['T0','reserve'] or col.startswith(('n_','y_')):poisoned[col]=-1e30
            assert np.array_equal(initial,conditional_q(poisoned,perils,kappa)[0])
            common=sample.copy()
            for p in perils:common['f_'+p]*=7.
            assert np.allclose(initial,conditional_q(common,perils,kappa)[0],rtol=1e-14)
            commonq=sample.copy()
            for p in perils:commonq['q_'+p]=.6
            assert np.allclose(conditional_q(commonq,perils,kappa)[0],.6,atol=1e-14)
            constant=sample.copy()
            for p in perils:constant['f_'+p]=c0['mixture'][p];constant['s_'+p]=1.
            flat=conditional_q(constant,perils,{p:1. for p in perils})[0]
            assert np.allclose(flat,sample.e_cost_scope.to_numpy()/sample.exposure.to_numpy(),rtol=2e-13,atol=1e-14)
            zero=sample.copy();zero.loc[zero.index[0],'q_'+perils[0]]=0.
            assert np.isfinite(conditional_q(zero,perils,kappa)[0]).all()
            for field,badvalue in [('f_'+perils[0],0.),('s_'+perils[0],-1.),('q_'+perils[0],1.5),('q_'+perils[0],-.1)]:
                bad=sample.copy();bad.loc[bad.index[0],field]=badvalue
                try:conditional_q(bad,perils,kappa)
                except AssertionError:pass
                else:raise AssertionError('Invalid diagnostic input accepted')
        path=OUT/f'held_completion_{line}_fold{held}.parquet';record.to_parquet(path,index=False)
        outputs.append({'path':w.rel(path),'sha256':w.sha(path),'rows':len(record)})
        checks.append({'line':line,'held':held,'C0_and_kappa_group_membership_exact':True,
            'global_C0_mixture_parity':True,'logsumexp_equivalence':True,'cost_reserve_count_payload_invariant':True,
            'scaling_and_common_completion_identities':True,'invalid_inputs_rejected':True})
    assert sum(v['rows'] for v in outputs)==109296
    assert all(w.sha(ROOT/p)==v for p,v in plan['sources'].items())
    report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'completion_profile_diagnostic_complete_no_price_test',
        'plan_sha256':w.sha(PLAN),'rows':109296,'results':results,'numeric_controls':checks,'outputs':outputs,
        'material_cells':len([v for v in results if v['materiality_screen']]),'total_cells':len(results),
        'budget_actual':plan['budget'],'limits':plan['limits'],'repair':plan['repair'],'2024_open':True,'B00_all_alternatives_preserved':True,
        'adopted_new_observation_link':False,'predictive_improvement_tested':False,'goal_achieved':False}
    dump(OUT/'report.json',report)
    pd.DataFrame(results).to_json(OUT/'cells.json',orient='records',indent=2)
    worst=sorted(results,key=lambda a:a['fraction_factor_difference_gt_1_05'],reverse=True)[:12]
    print(json.dumps({'complete':True,'new_fits':0,'new_scores':0,'material_cells':report['material_cells'],'total_cells':report['total_cells'],'largest_fraction_cells':worst},ensure_ascii=True))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['register','run']);a=p.parse_args()
    {'register':register,'run':run}[a.mode]()
