"""Otra cuenta de exposición y siniestros por cobertura; adversos focales."""
from pathlib import Path
from datetime import datetime,timezone
import json,math,hashlib,sys,importlib.util,subprocess
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
KEY=['market','line','row_id']

def eligible(row,line,peril):
    # Separate literal implementation, no imported producer/mask table.
    if line=='motor' and peril in ('own_damage','glass_hail'):return row['cover_type']=='comprehensive'
    if line=='motor' and peril=='theft':return row['cover_type']!='third_party_only'
    if line!='motor' and peril=='accidental_damage':return bool(row['accidental_damage_cover'])
    return True

def main():
    run=Path(sys.argv[1]).resolve();run.relative_to(REPO/'privado/semana2/desarrollo2023');p=read(run/'plan_snapshot.json')
    base=ROOT/p['period_input_run'];obs=ROOT/p['observation_run'];mix=ROOT/p['mixture_run'];checks=[]
    def check(n,x):checks.append({'name':n,'pass':bool(x)})
    def close(a,b):return math.isclose(float(a),float(b),rel_tol=1e-11,abs_tol=1e-8)
    for source in p['frozen_sources']:check('Source '+source['path'],sha(ROOT/source['path'])==source['sha256'])
    den=pq.read_table(run/'denominators_and_numerators.parquet').to_pylist();cat=pq.read_table(run/'coverage_categories.parquet').to_pylist();full=read(run/'full_cohort_candidate_conflicts.json')
    sourceclaims=pq.read_table(mix/'inputs_2023/claims_2023.parquet').to_pylist();frames={};claims={};perils={}
    for line in ['motor','buildings','contents']:
        columns=['cover_type'] if line=='motor' else ['accidental_damage_cover']+(['bicycle_cover'] if line=='contents' else [])
        raw=pq.read_table(base/f'inputs_2023/raw_{line}.parquet',columns=['row_id']+columns).to_pylist();raw={x['row_id']:x for x in raw}
        meta=KEY+['policy_id','customer_id','address_id','group_id','fold','year','is_test','period_start','period_end','exposure','x_new_business']
        rows=pq.read_table(base/f'inputs_2023/{line}.parquet',columns=meta).to_pylist()
        joined=[dict(x,**{col:raw[x['row_id']][col] for col in columns}) for x in rows];frames[line]=joined
        saved=pq.read_table(run/f'inputs_2023/{line}.parquet').to_pylist()
        check('Source coverage/meta exact '+line,joined==saved)
        byid={x['row_id']:x for x in joined}
        claims[line]=[dict(x,**{col:raw[x['row_id']][col] for col in columns}) for x in sourceclaims if x['line']==line]
        check('Claim copies exact '+line,claims[line]==pq.read_table(run/f'inputs_2023/claims_{line}.parquet').to_pylist())
        perils[line]=sorted({x['peril'] for x in claims[line]})
        for fold in range(5):
            fit=[x for x in joined if x['fold']!=fold];held=[x for x in joined if x['fold']==fold]
            check('Group/customer/address disjoint '+line+str(fold),all({x[k] for x in fit}.isdisjoint(x[k] for x in held) for k in ['customer_id','address_id','group_id']))
            cols=KEY+['qN_'+x for x in perils[line]]+['qC_1.0_'+x for x in perils[line]]
            curves=pq.read_table(obs/f'exclude_fold{fold}/observation_link_{line}.parquet',columns=cols,filters=[('year','=',2023),('is_test','=',False)]).to_pylist();q={x['row_id']:x for x in curves}
            check('Unique curve keys '+line+str(fold),len(q)==len(joined)==len(curves))
            for cell in [x for x in den if x['line']==line and x['fold']==fold]:
                business=cell['business'];peril=cell['peril'];g=[x for x in fit if int(x['x_new_business'])==business];covered=[x for x in g if eligible(x,line,peril)];excluded=[x for x in g if not eligible(x,line,peril)]
                observed=[x for x in claims[line] if x['fold']!=fold and int(x['x_new_business'])==business and x['peril']==peril];outside=[x for x in observed if not eligible(x,line,peril)];inside=[x for x in observed if eligible(x,line,peril)]
                norm=math.fsum(x['exposure']*q[x['row_id']]['qN_'+peril] for x in g)
                selected=math.fsum(x['exposure']*q[x['row_id']]['qN_'+peril] for x in covered)
                calculated={'nominal_all':math.fsum(x['exposure'] for x in g),'nominal_candidate':math.fsum(x['exposure'] for x in covered),
                    'count_all':norm,'count_candidate':selected,'count_excluded':math.fsum(x['exposure']*q[x['row_id']]['qN_'+peril] for x in excluded),
                    'cost_all':math.fsum(x['exposure']*q[x['row_id']]['qC_1.0_'+peril] for x in g),'cost_candidate':math.fsum(x['exposure']*q[x['row_id']]['qC_1.0_'+peril] for x in covered),
                    'count_retained_fraction':selected/norm}
                ident=line+str(fold)+str(business)+peril
                for key,value in calculated.items():check('fsum '+ident+key,close(cell[key],value))
                check('Not a fitted frequency factor '+ident,cell['inverse_denominator_factor_not_a_fitted_rate'] is None if selected==0 else close(cell['inverse_denominator_factor_not_a_fitted_rate'],norm/selected))
                check('Claim partition '+ident,cell['observed_claims']==len(observed) and cell['candidate_claims']==len(inside) and cell['outside_claims']==len(outside) and cell['outside_positive_claims']==sum(x['T0_cents']>0 for x in outside))
                check('Cost cents retained '+ident,cell['outside_net_cents']==sum(x['T0_cents'] for x in outside) and cell['all_net_cents']==sum(x['T0_cents'] for x in observed) and cell['candidate_net_cents']==sum(x['T0_cents'] for x in inside))
                check('Compatibility flags '+ident,cell['numerator_matches_candidate_all_claims']==(len(outside)==0) and cell['numerator_matches_candidate_positive_costs']==not_any_positive(outside))
                for category in [x for x in cat if x['line']==line and x['fold']==fold and x['business']==business and x['peril']==peril]:
                    field=category['coverage_field'];value=category['coverage_value'];cg=[x for x in g if str(x[field])==value];cl=[x for x in observed if str(x[field])==value]
                    check('Category '+ident+field+value,category['periods']==len(cg) and category['claims']==len(cl) and category['positive_claims']==sum(x['T0_cents']>0 for x in cl) and category['net_cents']==sum(x['T0_cents'] for x in cl)
                        and close(category['nominal_exposure'],math.fsum(x['exposure'] for x in cg)) and close(category['count_effective_exposure'],math.fsum(x['exposure']*q[x['row_id']]['qN_'+peril] for x in cg)) and close(category['cost_effective_exposure'],math.fsum(x['exposure']*q[x['row_id']]['qC_1.0_'+peril] for x in cg)))
        for record in [x for x in full if x['line']==line]:
            selected=[x for x in claims[line] if x['peril']==record['peril'] and eligible(x,line,x['peril'])==(record['position']=='inside_candidate')]
            statuses={name:sum(x['status']==name for x in selected) for name in {x['status'] for x in selected}}
            positive={name:sum(x['status']==name and x['T0_cents']>0 for x in selected) for name in {x['status'] for x in selected if x['T0_cents']>0}}
            check('Full cohort apparent mismatch '+line+record['peril']+record['position'],record['claims']==len(selected) and record['positive_claims']==sum(x['T0_cents']>0 for x in selected) and record['net_cents']==sum(x['T0_cents'] for x in selected) and record['statuses']==statuses and record['positive_statuses']==positive)
    check('Canonical target unchanged',len(sourceclaims)==4567 and sum(x['T0_cents'] for x in sourceclaims)==1529710384)
    check('Expected diagnostic grids',len(den)==150 and len(cat)==430 and len(full)==30)
    # New guards and algebra only; independent counts above do not import the producer.
    spec=importlib.util.spec_from_file_location('coverage_guard_fixtures',ROOT/p['code']);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    def reject(n,fn):
        try:fn()
        except ValueError:check(n,True)
        else:check(n,False)
    f=pd.DataFrame(frames['motor']);c=pd.DataFrame(claims['motor'])
    for label,col,value in [('year','year',2024),('test','is_test',True),('unknown','cover_type','unknown'),('missing','cover_type',None),('exposure','exposure',-1.),('business','x_new_business',2.)]:
        bad=f.head(1).copy();bad[col]=value;reject('Period guard '+label,lambda bad=bad:m.frame_guard(bad,'motor'))
    reject('Duplicate period',lambda:m.frame_guard(pd.concat([f.head(1),f.head(1)],ignore_index=True),'motor'))
    bad=c[c.fold.ne(0)].head(1).copy();bad['fold']=0;reject('Heldout claim rejected',lambda:m.claim_guard(bad,f,0))
    bad=c.head(1).copy();bad['row_id']='missing_fixture';reject('Missing claim period rejected',lambda:m.claim_guard(bad,f))
    reject('Unknown peril rejected',lambda:m.candidate_mask(f,'motor','unknown_peril'))
    home=pd.DataFrame(frames['contents']).head(1).copy();home['accidental_damage_cover']=0;reject('Numeric false not silent boolean',lambda:m.frame_guard(home,'contents'))
    # Pure technical fixtures: masks affect denominators, never an extra pricing multiplier.
    e=np.array([.25,.75]);qn=np.array([.5,1.]);qc=np.array([.2,.8])
    allone=m.denominators(e,qn,qc,np.array([True,True]));check('Allones identity',allone['count_all']==allone['count_candidate'] and allone['count_retained_fraction']==1 and allone['inverse_denominator_factor_not_a_fitted_rate']==1)
    split=m.denominators(e,qn,qc,np.array([True,False]));check('Complement additive',close(split['count_all'],split['count_candidate']+split['count_excluded']) and close(split['cost_candidate'],.05))
    zero=m.denominators(e,qn,qc,np.array([False,False]));check('Zero denominator explicit, no infinite factor',zero['candidate_denominator_zero'] and zero['inverse_denominator_factor_not_a_fitted_rate'] is None)
    reject('Mask dimensions rejected',lambda:m.denominators(e,qn,qc,np.array([True])))
    reject('NaN CDF rejected',lambda:m.denominators(e,np.array([float('nan'),1.]),qc,np.array([True,True])))
    zero_bike=pd.DataFrame(frames['contents']).head(3).copy();zero_bike['bicycle_cover']=False
    check('Bicycle false never removes all theft',m.candidate_mask(zero_bike,'contents','theft').all())
    # Two full-command negative cases preserve expected failure artifacts, with synthetic labels only.
    adversary=run/'adversaries';adversary.mkdir(exist_ok=False);failure_runs=[]
    for label,message in [('year','Only policy-year2023 non-test'),('missing','Missing coverage cover_type')]:
        fixture=adversary/label;(fixture/'inputs_2023').mkdir(parents=True)
        bad=f.head(2).copy()
        if label=='year':bad['year']=2024
        else:bad['cover_type']=None
        periodfile=fixture/'inputs_2023/motor.parquet';rawfile=fixture/'inputs_2023/raw_motor.parquet'
        pq.write_table(pa.Table.from_pandas(bad.drop(columns=['cover_type']),preserve_index=False),periodfile)
        pq.write_table(pa.Table.from_pandas(bad[['row_id','cover_type']],preserve_index=False),rawfile)
        negative=dict(p,period_input_run=rel(fixture),frozen_sources=[{'path':rel(x),'sha256':sha(x)} for x in [periodfile,rawfile]])
        negativepath=fixture/'plan.json';negativepath.write_text(json.dumps(negative),encoding='utf-8')
        before=set(run.parent.glob('coberturas_*'));proc=subprocess.run([sys.executable,str(ROOT/p['code']),str(negativepath)],capture_output=True,text=True)
        created=sorted(set(run.parent.glob('coberturas_*'))-before);failure_runs.extend(rel(x) for x in created)
        (fixture/'stderr.txt').write_text(proc.stderr,encoding='utf-8')
        check('Native command rejects '+label,proc.returncode!=0 and message in proc.stderr and len(created)==1 and not (created[0]/'report.json').exists())
    result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,
        'expected_failure_runs':failure_runs,'scope':'New independent Python dictionary joins/math.fsum counts and exposure; producer imported only for focal guard/algebra fixtures. Real native negative flows retained. No new fits/scores/bootstrap.',
        'professional_independent_validation':False}
    (run/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':result['passed'],'failed':result['failed'],'expected_failure_runs':len(failure_runs)}))
    if result['failed']:print(json.dumps([x for x in checks if not x['pass']]));return 1
    return 0

def not_any_positive(rows):return not any(x['T0_cents']>0 for x in rows)

if __name__=='__main__':raise SystemExit(main())
