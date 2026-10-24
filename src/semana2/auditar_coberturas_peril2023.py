"""Coberturas y denominadores por peril: diagnóstico, sin ajustes ni precios."""
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
COVER_COLS={'motor':['cover_type'],'buildings':['accidental_damage_cover'],'contents':['accidental_damage_cover','bicycle_cover']}
PERILS={'motor':['bodily_injury','glass_hail','own_damage','theft','third_party_prop'],'buildings':['accidental_damage','escape_of_water','fire','flood','storm','subsidence'],'contents':['accidental_damage','escape_of_water','flood','theft']}
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()

def require(ok,msg):
    if not bool(ok):raise ValueError(msg)

def dump(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False,default=lambda x:x.item() if hasattr(x,'item') else str(x))+'\n',encoding='utf-8')

def frame_guard(f,line):
    require(f.year.eq(2023).all() and not f.is_test.any(),'Only policy-year2023 non-test')
    require(not f.empty and f.line.eq(line).all() and not f.duplicated(KEY).any(),'Period keys/line')
    require(f.x_new_business.isin([0.,1.]).all() and f.fold.isin(range(5)).all(),'Business/fold')
    require(np.isfinite(f.exposure).all() and f.exposure.gt(0).all(),'Exposure must be positive')
    require(pd.to_datetime(f.period_start).dt.year.eq(2023).all(),'Start/year mismatch')
    for col in COVER_COLS[line]:
        require(f[col].notna().all(),'Missing coverage '+col)
        if col=='cover_type':require(f[col].isin(['comprehensive','third_party_fire_theft','third_party_only']).all(),'Unknown motor cover')
        else:require(f[col].map(lambda x:isinstance(x,(bool,np.bool_))).all(),'Coverage must be boolean '+col)

def candidate_mask(frame,line,peril):
    require(peril in PERILS[line],'Unknown peril')
    if line=='motor':
        if peril in ['own_damage','glass_hail']:return frame.cover_type.eq('comprehensive').to_numpy()
        if peril=='theft':return frame.cover_type.isin(['comprehensive','third_party_fire_theft']).to_numpy()
    elif peril=='accidental_damage':return frame.accidental_damage_cover.to_numpy(dtype=bool)
    return np.ones(len(frame),dtype=bool)

def claim_guard(c,frame,fold=None):
    require(c.claim_id.is_unique and c.year.eq(2023).all(),'Claim duplicate/year')
    if fold is not None:require(c.fold.ne(fold).all(),'Heldout claim')
    require((c.T0_cents>=0).all() and c.included_in_T0.all(),'Canonical nonnegative cost cohort')
    check=c.merge(frame[KEY+['policy_id','group_id','fold','year','period_start','period_end']],on=KEY,how='left',validate='many_to_one',suffixes=('','_period'),indicator=True)
    require(check['_merge'].eq('both').all(),'Missing claim period')
    for col in ['policy_id','group_id','fold','year']:require(check[col].eq(check[col+'_period']).all(),'Claim metadata '+col)
    require((pd.to_datetime(check.loss_date)>=pd.to_datetime(check.period_start)).all() and (pd.to_datetime(check.loss_date)<=pd.to_datetime(check.period_end)).all(),'Loss outside assigned period')

def denominators(exposure,qn,qc,mask):
    e=np.asarray(exposure,float);n=np.asarray(qn,float);c=np.asarray(qc,float);m=np.asarray(mask)
    require(e.shape==n.shape==c.shape==m.shape and m.dtype==bool,'Denominator dimensions/mask')
    require(np.isfinite(e).all() and (e>0).all() and np.isfinite(n).all() and np.isfinite(c).all(),'Nonfinite exposure/curve')
    require((n>=0).all() and (n<=1+1e-10).all() and (c>=0).all() and (c<=1+1e-10).all(),'Invalid count/cost completion')
    full=float(np.dot(e,n));selected=float(np.dot(e[m],n[m]));outside=float(np.dot(e[~m],n[~m]))
    require(full>0 and abs(full-selected-outside)<=1e-8,'Denominator partition')
    return {'nominal_all':float(e.sum()),'nominal_candidate':float(e[m].sum()),'count_all':full,'count_candidate':selected,'count_excluded':outside,
        'cost_all':float(np.dot(e,c)),'cost_candidate':float(np.dot(e[m],c[m])),
        'count_retained_fraction':selected/full,'inverse_denominator_factor_not_a_fitted_rate':full/selected if selected>0 else None,
        'candidate_denominator_zero':selected==0}

def main():
    path=Path(sys.argv[1]).resolve();p=read(path)
    require(p['code_sha256']==sha(Path(__file__)),'Frozen code changed')
    for x in p['frozen_sources']:require(sha(ROOT/x['path'])==x['sha256'],'Frozen source '+x['path'])
    forum=(ROOT/'Hackaton/Semana 2/Foro/FORO.md').read_bytes()
    require(forum.count(('<!-- aporte:'+p['forum_prior']+' -->').encode())==1,'Preregister in forum before audit')
    base=ROOT/p['period_input_run'];mix=ROOT/p['mixture_run'];obs=ROOT/p['observation_run']
    out=REPO/'privado/semana2/desarrollo2023'/('coberturas_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);out.mkdir(exist_ok=False);(out/'inputs_2023').mkdir()
    dump(out/'plan_snapshot.json',p);(out/'code_snapshot.py').write_bytes(Path(__file__).read_bytes())
    claims=pq.read_table(mix/'inputs_2023/claims_2023.parquet').to_pandas()
    frames={};numerator=[];categories=[];conflicts=[];checks=[]
    def check(name,value):checks.append({'name':name,'pass':bool(value)})
    for line in LINES:
        cols=KEY+['policy_id','customer_id','address_id','group_id','fold','year','is_test','period_start','period_end','exposure','x_new_business']
        f=pq.read_table(base/f'inputs_2023/{line}.parquet',columns=cols).to_pandas()
        raw=pq.read_table(base/f'inputs_2023/raw_{line}.parquet',columns=['row_id']+COVER_COLS[line]).to_pandas()
        require(raw.row_id.is_unique and set(raw.row_id)==set(f.row_id),'Raw coverage keys')
        f=f.merge(raw,on='row_id',how='left',validate='one_to_one');frame_guard(f,line);frames[line]=f
        pq.write_table(pa.Table.from_pandas(f,preserve_index=False),out/f'inputs_2023/{line}.parquet')
        lc=claims[claims.line.eq(line)].copy();claim_guard(lc,f)
        lc=lc.merge(f[KEY+COVER_COLS[line]],on=KEY,how='left',validate='many_to_one');pq.write_table(pa.Table.from_pandas(lc,preserve_index=False),out/f'inputs_2023/claims_{line}.parquet')
        # Full-cohort view is descriptive only; training views below never use heldout claims.
        for peril in PERILS[line]:
            cc=lc[lc.peril.eq(peril)];mask=candidate_mask(cc,line,peril)
            for outside,label in [(True,'outside_candidate'),(False,'inside_candidate')]:
                g=cc[~mask if outside else mask]
                conflicts.append({'line':line,'peril':peril,'position':label,'claims':len(g),'positive_claims':int(g.T0_cents.gt(0).sum()),'zero_cost_claims':int(g.T0_cents.eq(0).sum()),
                    'net_cents':int(g.T0_cents.sum()),'statuses':g.groupby('status').size().to_dict(),'positive_statuses':g[g.T0_cents.gt(0)].groupby('status').size().to_dict(),
                    'rule_changed':not candidate_mask(f,line,peril).all()})
        for fold in range(5):
            fit=f[f.fold.ne(fold)].copy();held=f[f.fold.eq(fold)]
            check('No customer/address/group overlap '+line+str(fold),all(set(fit[col]).isdisjoint(held[col]) for col in ['customer_id','address_id','group_id']))
            c=lc[lc.fold.ne(fold)].copy();claim_guard(c,f,fold)
            qcols=KEY+['qN_'+x for x in PERILS[line]]+['qC_1.0_'+x for x in PERILS[line]]
            curve=pq.read_table(obs/f'exclude_fold{fold}/observation_link_{line}.parquet',columns=qcols,filters=[('year','=',2023),('is_test','=',False)]).to_pandas()
            fit=fit.merge(curve,on=KEY,how='left',validate='one_to_one');require(fit[qcols[3:]].notna().all().all(),'Missing curve key')
            for business in [0,1]:
                g=fit[fit.x_new_business.eq(business)];cg=c[c.x_new_business.eq(business)]
                for peril in PERILS[line]:
                    mask=candidate_mask(g,line,peril);cc=cg[cg.peril.eq(peril)];cm=candidate_mask(cc,line,peril);outside=cc[~cm]
                    den=denominators(g.exposure,g['qN_'+peril],g['qC_1.0_'+peril],mask)
                    check('Candidate partition '+line+str(fold)+str(business)+peril,np.isclose(den['count_all'],den['count_candidate']+den['count_excluded'],rtol=1e-12,atol=1e-10))
                    numerator.append({'line':line,'fold':fold,'business':business,'peril':peril,'fit_periods':len(g),'candidate_periods':int(mask.sum()),
                        'observed_claims':len(cc),'candidate_claims':int(cm.sum()),'outside_claims':len(outside),'outside_positive_claims':int(outside.T0_cents.gt(0).sum()),
                        'outside_net_cents':int(outside.T0_cents.sum()),'all_net_cents':int(cc.T0_cents.sum()),'candidate_net_cents':int(cc.loc[cm,'T0_cents'].sum()),
                        'numerator_matches_candidate_all_claims':bool(cm.all()),'numerator_matches_candidate_positive_costs':not outside.T0_cents.gt(0).any(),**den})
                    for col in COVER_COLS[line]:
                        for value in sorted(f[col].unique(),key=str):
                            fg=g[g[col].eq(value)];cf=cc[cc[col].eq(value)]
                            categories.append({'line':line,'fold':fold,'business':business,'peril':peril,'coverage_field':col,'coverage_value':str(value),
                                'periods':len(fg),'nominal_exposure':float(fg.exposure.sum()),'count_effective_exposure':float((fg.exposure*fg['qN_'+peril]).sum()),
                                'cost_effective_exposure':float((fg.exposure*fg['qC_1.0_'+peril]).sum()),'claims':len(cf),'positive_claims':int(cf.T0_cents.gt(0).sum()),'net_cents':int(cf.T0_cents.sum())})
    allf=pd.concat(list(frames.values()),ignore_index=True);check('Full2023scope',len(allf)==50094 and allf.group_id.nunique()==30869 and not allf.duplicated(KEY).any())
    check('Canonical claim/net total preserved',len(claims)==4567 and claims.T0_cents.sum()==1529710384)
    for name,rows in [('denominators_and_numerators',numerator),('coverage_categories',categories)]:pq.write_table(pa.Table.from_pylist(rows),out/(name+'.parquet'))
    dump(out/'full_cohort_candidate_conflicts.json',conflicts)
    result={'id':p['id'],'author':'Codex','run':rel(out),'completed_utc':datetime.now(timezone.utc).isoformat(),'scope':'Only policy-year2023 and ownfold claims/curves; candidate-mask diagnostic, no adoption or inferred contract. Bicycle is category only, never a theft mask.',
        'rows':len(allf),'groups':int(allf.group_id.nunique()),'claims':len(claims),'denominator_cells':len(numerator),'category_cells':len(categories),
        'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,
        'new_price_fits':0,'new_price_constants':0,'new_curves':0,'new_scores':0,'new_bootstrap':0,'reference':'W2-B00','all_alternatives_preserved':True,
        'external2024_subject_exposure_previously_disclosed':True,'ledger_read':False,'external2024_artifacts_read':False,'professional_independent_validation':False}
    dump(out/'report.json',result)
    dump(out/'manifest.json',{'files':[{'path':x.relative_to(out).as_posix(),'sha256':sha(x),'bytes':x.stat().st_size} for x in sorted(out.rglob('*')) if x.is_file()]})
    require(result['failed']==0,'Audit failed; retain run')
    print(json.dumps({'run':rel(out),'passed':result['passed'],'failed':result['failed'],'denominator_cells':len(numerator),'no_new_fits_scores':True}))

if __name__=='__main__':main()
