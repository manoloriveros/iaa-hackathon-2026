"""Otra cuenta de soporte diario y casos adversos; sin ajustes o scores."""
from pathlib import Path
from datetime import date,datetime,timezone
from bisect import bisect_right
import json,hashlib,sys,math,importlib.util,subprocess
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
KEY=['market','line','row_id'];CUT=date(2024,12,31);D=[0,30,90,180,365,540,730]

def main():
    run=Path(sys.argv[1]).resolve();run.relative_to(REPO/'privado/semana2/desarrollo2023')
    plan=read(run/'plan_snapshot.json');base=ROOT/plan['period_input_run'];mix=ROOT/plan['mixture_run'];obs=ROOT/plan['observation_run']
    checks=[]
    def check(name,value):checks.append({'name':name,'pass':bool(value)})
    def close(a,b):return math.isclose(float(a),float(b),rel_tol=1e-10,abs_tol=1e-8)
    hist=pq.read_table(run/'maturity_histograms.parquet').to_pandas();cells=pq.read_table(run/'peril_business_cells.parquet').to_pandas();supp=pq.read_table(run/'delay_support.parquet').to_pandas();contr=pq.read_table(run/'calendar_contrasts.parquet').to_pandas();cal=pq.read_table(run/'calendar_profile.parquet').to_pandas()
    for src in plan['frozen_sources']:check('Frozen source '+src['path'],sha(ROOT/src['path'])==src['sha256'])
    frames={};fitclaims={}
    # Direct daily addition, built ONCE by held fold, then training totals by subtraction.
    # This does not use the producer's interval-difference/cumulative algorithm.
    for line in ['motor','buildings','contents']:
        frame=pq.read_table(run/f'inputs_2023/{line}.parquet').to_pandas();frames[line]=frame
        direct=np.zeros((5,2,731));days=np.zeros_like(direct)
        for row in frame.itertuples(index=False):
            first=(CUT-row.period_start.date()).days;last=(CUT-row.period_end.date()).days
            direct[row.fold,int(row.x_new_business),last:first+1]+=row.exposure/(first-last+1)
            days[row.fold,int(row.x_new_business),last:first+1]+=1
        total=direct.sum(axis=0);daytotal=days.sum(axis=0)
        for fold in range(5):
            claims=pq.read_table(mix/f'inputs_2023/{line}_fold{fold}_fitclaims.parquet').to_pandas();fitclaims[line,fold]=claims
            claimrows=list(claims.itertuples(index=False));models={k.split('|',1)[1]:v for k,v in read(obs/f'exclude_fold{fold}/reporting_models.json').items() if k.startswith(line+'|')}
            hm={}
            for business in [0,1]:
                mass=total[business]-direct[fold,business];covered=daytotal[business]-days[fold,business];hm[business]=mass
                actual=hist[(hist.line==line)&(hist.fold==fold)&(hist.business==business)].sort_values('age')
                check('Explicit daily exposure '+line+str(fold)+str(business),np.allclose(np.pad(actual.exposure_mass.to_numpy(),(0,731-len(actual))),mass,rtol=1e-10,atol=1e-10))
                check('Explicit covered days '+line+str(fold)+str(business),np.array_equal(np.pad(actual.covered_days.to_numpy(),(0,731-len(actual))),covered))
                c=cal[(cal.line==line)&(cal.fold==fold)&(cal.business==business)].iloc[0]
                check('Calendar totals '+line+str(fold)+str(business),close(c.exposure,mass.sum()) and c.covered_days==int(covered.sum()))
                for peril,model in models.items():
                    rows=[x for x in claimrows if int(x.x_new_business)==business and x.peril==peril]
                    cs=cells[(cells.line==line)&(cells.fold==fold)&(cells.business==business)&(cells.peril==peril)].iloc[0]
                    cents=[int(x.T0_cents) for x in rows];weights=[float(x.severity_probability_weight) for x in rows]
                    positive=[w for x,w in zip(rows,weights) if x.T0_cents>0];weighted=[w*y for w,y in zip(weights,cents)]
                    check('Cell observed count/cost '+line+str(fold)+str(business)+peril,cs.claims==len(rows) and cs.positive_claims==sum(x>0 for x in cents) and cs.groups==len({x.group_id for x in rows}) and cs.net_cents==sum(cents))
                    check('Cell weighted mass '+line+str(fold)+str(business)+peril,close(cs.weighted_cost_total_cents,math.fsum(weighted)))
                    if positive:
                        ess=math.fsum(positive)**2/math.fsum(w*w for w in positive)
                        check('Cell positive ESS '+line+str(fold)+str(business)+peril,close(cs.positive_weight_ESS,ess))
                    else:check('No fabricated empty ESS '+line+str(fold)+str(business)+peril,pd.isna(cs.positive_weight_ESS))
                    for kind,curve in [('count',model['count_cdf']),('cost',model['cost_cdf']['1.0'])]:
                        values=[]
                        for age,value in enumerate(mass):
                            at=bisect_right(model['delay_days'],age)-1;values.append(value*(curve[at] if at>=0 else 0.))
                        check('Step curve via bisect '+line+str(fold)+str(business)+peril+kind,close(cs[kind+'_weighted_completion'],math.fsum(values)/math.fsum(mass)))
                    ss=supp[(supp.line==line)&(supp.fold==fold)&(supp.business==business)&(supp.peril==peril)]
                    check('All fixed points and endpoint '+line+str(fold)+str(business)+peril,len(ss)==8 and sorted(ss[~ss.pooled_endpoint].threshold.tolist())==D and ss[ss.pooled_endpoint].threshold.tolist()==[model['max_delay']])
                    for point in ss.itertuples(index=False):
                        t=int(point.threshold);risk=sum(x.delay<=t<=x.age for x in rows);after=[x for x in rows if x.delay>t]
                        check('Threshold counts '+line+str(fold)+str(business)+peril+str(t)+str(point.pooled_endpoint),point.reverse_risk_set==risk and point.followup_at_least_threshold==sum(x.age>=t for x in rows) and point.events_at_threshold==sum(x.delay==t for x in rows) and point.observed_reports_after_threshold==len(after) and point.observed_net_after_threshold_cents==sum(x.T0_cents for x in after))
                        check('Threshold calendar mass '+line+str(fold)+str(business)+peril+str(t)+str(point.pooled_endpoint),close(point.mature_exposure,math.fsum(mass[t:])) and close(point.mature_fraction,math.fsum(mass[t:])/math.fsum(mass)))
            norm=[hm[b]/hm[b].sum() for b in [0,1]]
            cr=contr[(contr.line==line)&(contr.fold==fold)].iloc[0]
            check('Calendar distances '+line+str(fold),close(cr.calendar_maturity_TV,sum(abs(a-b) for a,b in zip(*norm))/2) and close(cr.calendar_maturity_KS,max(abs(a-b) for a,b in zip(np.cumsum(norm[0]),np.cumsum(norm[1])))))
            for peril,model in models.items():
                points=supp[(supp.line==line)&(supp.fold==fold)&(supp.peril==peril)&supp.pooled_endpoint]
                check('Business endpoint risk reconciles pooled '+line+str(fold)+peril,points.reverse_risk_set.sum()==model['risk_set'][-1] and points.events_at_threshold.sum()==model['events'][-1])
    # Import producer only for new guards/adversaries; independent calculations above never call it.
    spec=importlib.util.spec_from_file_location('calendar_adversaries',ROOT/plan['code']);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    def reject(name,fn):
        try:fn()
        except ValueError:check(name,True)
        else:check(name,False)
    frame=frames['motor'].copy();m.frame_guard(frame)
    for name,col,val in [('year','year',2024),('test','is_test',True),('business','x_new_business',2.),('fold','fold',5),('negativeexposure','exposure',-1.),('futureend','period_end',pd.Timestamp('2025-01-01'))]:
        bad=frame.head(1).copy();bad[col]=val;reject('Frame guard '+name,lambda bad=bad:m.frame_guard(bad))
    reject('Duplicate period',lambda:m.frame_guard(pd.concat([frame.head(1),frame.head(1)],ignore_index=True)))
    one=frame.head(1).copy();one['period_start']=pd.Timestamp('2023-12-31');one['period_end']=pd.Timestamp('2023-12-31');one['exposure']=1/365
    mass,covered=m.histogram(one);check('One-day inclusive boundary',close(mass.sum(),1/365) and covered.sum()==1 and close(mass[366],1/365))
    # Direct full-year inclusive denominator, including leap-day2024 in a2023-start contract.
    one['period_start']=pd.Timestamp('2023-07-01');one['period_end']=pd.Timestamp('2024-06-30');one['exposure']=1.
    mass,covered=m.histogram(one);check('Leap-day boundary',covered.sum()==366 and close(mass.sum(),1.))
    claims=fitclaims['motor',0].head(1).copy()
    for name,col,val in [('heldout','fold',0),('year','year',2024),('weight','severity_probability_weight',0.),('negative_delay','delay',-1),('missing_period','row_id','missing_fixture')]:
        bad=claims.copy();bad[col]=val;reject('Claim guard '+name,lambda bad=bad:m.claim_guard(bad,frame,0))
    reject('Duplicate claim',lambda:m.claim_guard(pd.concat([claims,claims],ignore_index=True),frame,0))
    # Poisoned synthetic metadata goes through the real command, retaining its expected failure run.
    adversary=run/'adversaries';adversary.mkdir(exist_ok=False);fixturebase=adversary/'year_poison';(fixturebase/'inputs_2023').mkdir(parents=True)
    poisoned=frame.head(2).copy();poisoned['year']=2024;pq.write_table(pa.Table.from_pandas(poisoned,preserve_index=False),fixturebase/'inputs_2023/motor.parquet')
    negativeplan=dict(plan,period_input_run=rel(fixturebase),frozen_sources=[{'path':rel(fixturebase/'inputs_2023/motor.parquet'),'sha256':sha(fixturebase/'inputs_2023/motor.parquet')}])
    negativepath=adversary/'plan_year_poison.json';negativepath.write_text(json.dumps(negativeplan),encoding='utf-8')
    before=set(run.parent.glob('soporte_*'));proc=subprocess.run([sys.executable,str(ROOT/plan['code']),str(negativepath)],capture_output=True,text=True)
    failedruns=sorted(set(run.parent.glob('soporte_*'))-before)
    (adversary/'year_poison_stderr.txt').write_text(proc.stderr,encoding='utf-8')
    check('Real command rejects2024 metadata before any score',proc.returncode!=0 and 'Only policy-year2023 non-test' in proc.stderr and len(failedruns)==1 and not (failedruns[0]/'report.json').exists())
    # Safe inventory is exercised as a real command as well as with title/body canaries.
    safe=REPO/'herramientas/leer_foro_semana2_seguro.py';s=importlib.util.spec_from_file_location('safe_forum',safe);reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
    sample='## Claude | CLA-S2-20261024-006 | 2026-10-24T00:57:11+00:00 | CONFIRMACION_SECRETA\nCUERPO_SECRETO\n'
    inv=reader.inventory(sample);encoded=json.dumps(inv)
    check('Title/body canaries absent',len(inv)==1 and 'CONFIRMACION_SECRETA' not in encoded and 'CUERPO_SECRETO' not in encoded and set(inv[0])=={'author','id','utc'})
    check('Malformed header omitted',reader.inventory('## Un encabezado incompleto CONFIRMACION_SECRETA\n')==[])
    cli=subprocess.run([sys.executable,str(safe),'10'],capture_output=True,text=True,check=True);inventory=json.loads(cli.stdout)
    check('Real safe inventory schema',all(set(x)=={'author','id','utc'} for x in inventory) and len(inventory)>0)
    allframe=pd.concat(list(frames.values()),ignore_index=True)
    check('2023scope keys exact',len(allframe)==50094 and allframe.year.eq(2023).all() and not allframe.is_test.any() and not allframe.duplicated(KEY).any() and allframe.group_id.nunique()==30869)
    result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,
        'scope':'New calendar/support audit only, independent direct daily addition and Python/bisect counts; producer imported only for focal guard fixtures. Real CLI year-poison failure retained. No model fits/scores/bootstrap.',
        'expected_failure_runs':[rel(x) for x in failedruns],'safe_inventory_output':inventory,'professional_independent_validation':False}
    (run/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':result['passed'],'failed':result['failed'],'expected_failed_native_runs':len(failedruns),'safe_reader_checked':True}))
    if result['failed']:print(json.dumps([x for x in checks if not x['pass']]));return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
