"""Diagnóstico descriptivo de calendario/truncamiento. No ajusta ni puntúa precios."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,uuid
ROOT=Path(__file__).resolve().parents[4];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

KEY=['market','line','row_id'];LINES=['motor','buildings','contents']
CUT=pd.Timestamp('2024-12-31');THRESHOLDS=[0,30,90,180,365,540,730]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()

def dump(p,obj):
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False,default=lambda x:x.item() if hasattr(x,'item') else str(x))+'\n',encoding='utf-8')

def require(ok,msg):
    if not bool(ok):raise ValueError(msg)

def frame_guard(f):
    require(not f.empty,'Empty frame')
    require(f.year.eq(2023).all() and ~f.is_test.any(),'Only policy-year2023 non-test')
    require(not f.duplicated(KEY).any(),'Duplicate period')
    require(f.x_new_business.isin([0.,1.]).all(),'Business scope')
    require(f.fold.isin(range(5)).all(),'Fold scope')
    start=pd.to_datetime(f.period_start);end=pd.to_datetime(f.period_end)
    require(start.dt.year.eq(2023).all(),'Year/start mismatch')
    require((end>=start).all() and (end<=CUT).all(),'Period beyond observation cutoff')
    require(np.isfinite(f.exposure).all() and f.exposure.gt(0).all(),'Invalid exposure')

def histogram(f):
    """Daily maturity mass, inclusive dates; mass unit is nominal exposure."""
    require(not f.empty,'Empty histogram scope')
    a=(CUT-pd.to_datetime(f.period_start)).dt.days.to_numpy(dtype=int)
    z=(CUT-pd.to_datetime(f.period_end)).dt.days.to_numpy(dtype=int)
    require((a>=z).all() and (z>=0).all(),'Invalid maturity interval')
    days=a-z+1;weight=f.exposure.to_numpy()/days
    delta=np.zeros(int(a.max())+2);counts=np.zeros_like(delta)
    np.add.at(delta,z,weight);np.add.at(delta,a+1,-weight)
    np.add.at(counts,z,1);np.add.at(counts,a+1,-1)
    mass=np.cumsum(delta)[:-1];covered=np.cumsum(counts)[:-1]
    require((mass>=-1e-10).all(),'Negative daily mass')
    mass=np.maximum(mass,0.)
    require(np.isclose(mass.sum(),f.exposure.sum(),rtol=1e-11,atol=1e-10),'Histogram exposure reconciliation')
    require(np.isclose(covered.sum(),days.sum()),'Covered-day reconciliation')
    return mass,covered

def evaluate_curve(model,kind,ages):
    support=np.asarray(model['delay_days']);curve=np.asarray(model['count_cdf'] if kind=='count' else model['cost_cdf']['1.0'])
    require(len(support)>0 and (np.diff(support)>0).all(),'Curve support order')
    require(np.isfinite(curve).all() and (np.diff(curve)>=-1e-12).all() and (curve>=0).all() and (curve<=1+1e-12).all(),'Invalid CDF')
    positions=np.searchsorted(support,ages,side='right')-1
    return np.where(positions>=0,curve[np.maximum(positions,0)],0.)

def claim_guard(claims,frame,fold):
    require(not claims.claim_id.duplicated().any(),'Duplicate claim')
    require(claims.year.eq(2023).all() and claims.fold.ne(fold).all(),'Heldout/year claim')
    require(claims.x_new_business.isin([0.,1.]).all(),'Claim business')
    require((claims.delay>=0).all() and (claims.age>=claims.delay).all(),'Impossible delay/truncation')
    require(((pd.to_datetime(claims.report_date)-pd.to_datetime(claims.loss_date)).dt.days==claims.delay).all(),'Delay mismatch')
    require(((CUT-pd.to_datetime(claims.loss_date)).dt.days==claims.age).all(),'Followup mismatch')
    require((claims.T0_cents>=0).all() and np.isfinite(claims.severity_probability_weight).all() and claims.severity_probability_weight.gt(0).all(),'Invalid cost/weight')
    joined=claims.merge(frame[KEY+['period_start','period_end','fold','group_id','x_new_business']],on=KEY,how='left',suffixes=('','_period'),validate='many_to_one',indicator=True)
    require(joined['_merge'].eq('both').all(),'Claim missing period')
    require((joined.fold==joined.fold_period).all() and (joined.group_id==joined.group_id_period).all() and (joined.x_new_business==joined.x_new_business_period).all(),'Claim/period metadata mismatch')
    require((pd.to_datetime(joined.loss_date)>=pd.to_datetime(joined.period_start)).all() and (pd.to_datetime(joined.loss_date)<=pd.to_datetime(joined.period_end)).all(),'Loss outside assigned period')

def cell_stats(claims):
    costs=claims.T0_cents.to_numpy(dtype=float);weights=claims.severity_probability_weight.to_numpy()
    positive=costs>0;mass=weights[positive];wm=costs*weights
    return {'claims':len(claims),'positive_claims':int(positive.sum()),'groups':int(claims.group_id.nunique()),
        'net_cents':int(claims.T0_cents.sum()),'delay_min':int(claims.delay.min()) if len(claims) else None,
        'delay_max':int(claims.delay.max()) if len(claims) else None,'followup_min':int(claims.age.min()) if len(claims) else None,
        'followup_max':int(claims.age.max()) if len(claims) else None,
        'observed_delay_median':float(claims.delay.median()) if len(claims) else None,
        'positive_weight_ESS':float(mass.sum()**2/(mass@mass)) if len(mass) else None,
        'weighted_cost_total_cents':float(wm.sum()),'max_weighted_cost_share':float(wm.max()/wm.sum()) if wm.sum()>0 else None}

def main():
    planpath=Path(sys.argv[1]).resolve();p=read(planpath);require(p['code_sha256']==sha(Path(__file__)),'Frozen code changed')
    for source in p['frozen_sources']:require(sha(ROOT/source['path'])==source['sha256'],'Frozen source '+source['path'])
    base=ROOT/p['period_input_run'];mix=ROOT/p['mixture_run'];obs=ROOT/p['observation_run']
    out=REPO/'privado/semana2/desarrollo2023'/('soporte_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);out.mkdir(exist_ok=False)
    dump(out/'plan_snapshot.json',p);(out/'code_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (out/'inputs_2023').mkdir();histrows=[];calendar=[];cells=[];support=[];contrasts=[];checks=[];frames={}
    def check(name,ok):checks.append({'name':name,'pass':bool(ok)})
    meta=KEY+['policy_id','customer_id','address_id','period_start','period_end','year','is_test','exposure','x_new_business','fold','group_id']
    for line in LINES:
        frame=pq.read_table(base/f'inputs_2023/{line}.parquet',columns=meta).to_pandas();frame_guard(frame);frames[line]=frame
        pq.write_table(pa.Table.from_pandas(frame,preserve_index=False),out/f'inputs_2023/{line}.parquet')
        for fold in range(5):
            fit=frame[frame.fold.ne(fold)].copy();held=frame[frame.fold.eq(fold)]
            check('Groups disjoint '+line+str(fold),set(fit.group_id).isdisjoint(held.group_id))
            claims=pq.read_table(mix/f'inputs_2023/{line}_fold{fold}_fitclaims.parquet').to_pandas();claim_guard(claims,frame,fold)
            models={key.split('|',1)[1]:v for key,v in read(obs/f'exclude_fold{fold}/reporting_models.json').items() if key.startswith(line+'|')}
            perils=sorted(models);cols=KEY+['qN_'+x for x in perils]+['qC_1.0_'+x for x in perils]
            link=pq.read_table(obs/f'exclude_fold{fold}/observation_link_{line}.parquet',columns=cols,filters=[('year','=',2023),('is_test','=',False)]).to_pandas()
            joined=fit.merge(link,on=KEY,how='left',validate='one_to_one');check('Curves match periods '+line+str(fold),len(joined)==len(fit) and joined.filter(regex=r'^q[NC]_').notna().all().all())
            masses={}
            for business in [0,1]:
                g=fit[fit.x_new_business.eq(business)];cg=claims[claims.x_new_business.eq(business)];mass,covered=histogram(g);masses[business]=mass
                ages=np.arange(len(mass));total=float(g.exposure.sum())
                histrows.extend({'line':line,'fold':fold,'business':business,'age':int(age),'exposure_mass':float(m),'covered_days':int(round(d))} for age,m,d in zip(ages,mass,covered))
                calendar.append({'line':line,'fold':fold,'business':business,'periods':len(g),'groups':int(g.group_id.nunique()),'exposure':total,'covered_days':int(covered.sum()),
                    'min_maturity':int((CUT-pd.to_datetime(g.period_end)).dt.days.min()),'max_maturity':int((CUT-pd.to_datetime(g.period_start)).dt.days.max()),
                    'claims':len(cg),'loss_calendar_years':sorted(int(y) for y in pd.to_datetime(cg.loss_date).dt.year.unique())})
                for peril in perils:
                    cc=cg[cg.peril.eq(peril)];model=models[peril];ident={'line':line,'fold':fold,'business':business,'peril':peril}
                    cell={**ident,**cell_stats(cc),'pooled_max_delay':model['max_delay'],'pooled_claims':model['n']}
                    gq=joined[joined.x_new_business.eq(business)]
                    for kind,col in [('count','qN_'+peril),('cost','qC_1.0_'+peril)]:
                        exact=float(mass@evaluate_curve(model,kind,ages));native=float((gq.exposure*gq[col]).sum())
                        cell[kind+'_weighted_completion']=exact/total
                        check('Daily curve integral '+line+str(fold)+str(business)+peril+kind,np.isclose(exact,native,rtol=1e-11,atol=1e-9))
                    cells.append(cell)
                    for threshold_index,threshold in enumerate(THRESHOLDS+[int(model['max_delay'])]):
                        # Last point is marked separately even if it equals a fixed threshold.
                        late=cc.delay.gt(threshold);risk=cc.delay.le(threshold)&cc.age.ge(threshold)
                        at=cc.delay.eq(threshold);sumcost=int(cc.T0_cents.sum());weighted=cc.T0_cents*cc.severity_probability_weight
                        support.append({**ident,'threshold':threshold,'pooled_endpoint':threshold_index==len(THRESHOLDS),
                            'period_exposure':total,'mature_exposure':float(mass[threshold:].sum()),'mature_fraction':float(mass[threshold:].sum()/total),
                            'observed_claims':len(cc),'followup_at_least_threshold':int(cc.age.ge(threshold).sum()),'reverse_risk_set':int(risk.sum()),
                            'events_at_threshold':int(at.sum()),'observed_reports_after_threshold':int(late.sum()),
                            'observed_net_after_threshold_cents':int(cc.loc[late,'T0_cents'].sum()),
                            'observed_net_tail_share':float(cc.loc[late,'T0_cents'].sum()/sumcost) if sumcost else None,
                            'weighted_cost_tail_share':float(weighted[late].sum()/weighted.sum()) if weighted.sum()>0 else None})
            length=max(len(x) for x in masses.values());pm=[np.pad(masses[b]/masses[b].sum(),(0,length-len(masses[b]))) for b in [0,1]]
            contrasts.append({'line':line,'fold':fold,'calendar_maturity_TV':float(abs(pm[1]-pm[0]).sum()/2),'calendar_maturity_KS':float(abs(np.cumsum(pm[1])-np.cumsum(pm[0])).max())})
    combined=pd.concat(list(frames.values()),ignore_index=True);check('All2023 periods',len(combined)==50094 and combined.group_id.nunique()==30869)
    for name,rows in [('maturity_histograms',histrows),('calendar_profile',calendar),('peril_business_cells',cells),('delay_support',support),('calendar_contrasts',contrasts)]:
        pq.write_table(pa.Table.from_pylist(rows),out/(name+'.parquet'))
    result={'author':'Codex','scope':'New descriptive calendar/reporting-support audit only; no pricing fits/predictions/scores, no new timing curves or bootstrap',
        'id':p['id'],'run':rel(out),'completed_utc':datetime.now(timezone.utc).isoformat(),'period_rows':len(combined),'groups':int(combined.group_id.nunique()),
        'cells':len(cells),'support_rows':len(support),'calendar_cells':len(calendar),'checks':checks,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),
        'price_fits':0,'price_constants':0,'curve_fits':0,'new_scores':0,'bootstrap':0,'scope_2024':{'own_policy_rows':0,'ledger_read':False,'external_score_header_exposure_recorded':True},
        'reference':'W2-B00','all_alternatives_preserved':True,'professional_independent_validation':False}
    dump(out/'report.json',result)
    dump(out/'manifest.json',{'files':[{'path':q.relative_to(out).as_posix(),'sha256':sha(q),'bytes':q.stat().st_size} for q in sorted(out.rglob('*')) if q.is_file()]})
    require(result['failed']==0,'Producer controls failed; retain run')
    print(json.dumps({'run':rel(out),'passed':result['passed'],'failed':result['failed'],'cells':len(cells),'no_fit_or_score':True}))

if __name__=='__main__':main()
