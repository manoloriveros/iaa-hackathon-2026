"""Concentración en incendio fijado y composición de AD; ninguna llamada a modelos."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,sys,uuid
REPO=Path(__file__).resolve().parents[2];ROOT=REPO.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
KEY=['market','line','row_id'];E='e_cost_mix_1.0';AD='x_accidental_damage_cover'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()


def dump(path,obj):
    with path.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False,default=lambda v:v.item() if hasattr(v,'item') else str(v));f.write('\n')


def require(ok,msg):
    if not bool(ok):raise ValueError(msg)


def guard(f):
    require(len(f)>0 and f.year.eq(2023).all(),'Non2023 or empty scope')
    require(f[KEY].notna().all().all() and not f.duplicated(KEY).any(),'Missing/duplicate keys')
    if 'T0' in f:require(np.isfinite(f.T0).all() and f.T0.ge(0).all(),'Invalid observed cost')


def ratio(a,b):return float(a/b) if abs(b)>1e-12 else None


def summarize(f):
    g=f.groupby('group_id',sort=True).stored_gain.sum()
    n=len(f);y=float(f.T0.sum());root=float(np.sqrt(f.T0).sum());null=float(8*(np.sqrt(n*y)-root))
    gain=float(f.stored_gain.sum())
    return {'rows':n,'groups':len(g),'T0':y,'mu19_total':float(f.muref.sum()),'mu20_total':float(f.mu20.sum()),
            'net_gain':gain,'gross_row_positive_gain':float(f.loc[f.stored_gain.gt(0),'stored_gain'].sum()),
            'gross_row_negative_gain_abs':float(-f.loc[f.stored_gain.lt(0),'stored_gain'].sum()),
            'positive_groups':int(g.gt(0).sum()),'negative_groups':int(g.lt(0).sum()),
            'gross_group_positive_gain':float(g[g.gt(0)].sum()),'gross_group_negative_gain_abs':float(-g[g.lt(0)].sum()),
            'null_deviance':null,'derived_delta_D2':gain/null if n>0 and null>1e-12 else None}


def ad_labels(frame):
    require((frame[AD].isin([0,1])|frame[AD].isna()).all(),'Nonbinary AD flag')
    return np.where(frame[AD].isna(),'missing',np.where(frame[AD].eq(1),'yes','no'))


def main(planpath):
    p=read(planpath);run=REPO/'privado/semana2/desarrollo2023'/('incendio_AD_b20_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);run.mkdir()
    (run/'plan_snapshot.json').write_bytes(planpath.read_bytes());(run/'code_snapshot.py').write_bytes(Path(__file__).read_bytes());checks=[]
    def check(name,ok):checks.append({'name':name,'pass':bool(ok)});require(ok,name)
    try:
        for x in p['frozen_sources']:check('Frozen source '+x['path'],sha(ROOT/x['path'])==x['sha256'])
        forum=(ROOT/'Hackaton/Semana 2/Foro/FORO.md').read_bytes();check('Prior forum comment',forum.count(('<!-- aporte:'+p['forum_prior']+' -->').encode())==1)
        f=pq.read_table(ROOT/p['row_attribution'],filters=[('reference','=','W2-B19')]).to_pandas().sort_values(KEY).reset_index(drop=True)
        guard(f);check('Full B20/B19 saved row scope',len(f)==50094 and set(f.reference)=={'W2-B19'})
        check('Saved positive finite prices',np.isfinite(f[['mu20','muref']]).all().all() and f[['mu20','muref']].gt(0).all().all())
        check('Saved gain definition',np.allclose(f.gain,f.stored_gain,rtol=1e-11,atol=1e-8))
        reasons=pq.read_table(ROOT/p['selection_reasons']).to_pandas();selected_ids=set(reasons.group_id)
        primary=reasons.loc[reasons.reason.eq('OOF_top5_adverse_buildings')&reasons['rank'].eq(1),'group_id'].iloc[0]
        secondary=reasons.loc[reasons.reason.eq('OOF_top5_adverse_buildings')&reasons['rank'].eq(2),'group_id'].iloc[0]
        fire=f[f.group_id.eq(primary)&f.line.eq('buildings')].copy();check('Fixed primary fire is one building row',len(fire)==1)
        firekey=fire[KEY].iloc[0].to_dict();isrow=np.logical_and.reduce([f[k].eq(v) for k,v in firekey.items()]);isgroup=f.group_id.eq(primary);isselected=f.group_id.isin(selected_ids)
        scopes={'global':f,'selected12':f[isselected],'fire_row':f[isrow],'fire_full_component':f[isgroup],
                'global_without_fire_row':f[~isrow],'global_without_fire_component':f[~isgroup],
                'selected_without_fire_row':f[isselected&~isrow],'selected_without_fire_component':f[isselected&~isgroup]}
        stats={name:summarize(cell) for name,cell in scopes.items()}
        check('Fixed original cohort preserved',stats['selected12']['rows']==20 and stats['selected12']['groups']==12)
        for name,cell in scopes.items():
            z=stats[name];check('Signed gain conservation '+name,np.isclose(z['net_gain'],z['gross_row_positive_gain']-z['gross_row_negative_gain_abs'],rtol=1e-10,atol=1e-7))
        rowgain=stats['fire_row']['net_gain'];groupgain=stats['fire_full_component']['net_gain']
        shares={'fire_row_of_selected_net':ratio(rowgain,stats['selected12']['net_gain']),
                'fire_row_of_global_net':ratio(rowgain,stats['global']['net_gain']),
                'fire_row_of_global_gross_positive_rows':ratio(rowgain,stats['global']['gross_row_positive_gain']),
                'fire_component_of_selected_net':ratio(groupgain,stats['selected12']['net_gain']),
                'fire_component_of_global_net':ratio(groupgain,stats['global']['net_gain']),
                'fire_component_of_global_gross_positive_groups':ratio(groupgain,stats['global']['gross_group_positive_gain']),
                'fire_component_of_selected_gross_positive_groups':ratio(groupgain,stats['selected12']['gross_group_positive_gain'])}
        dump(run/'concentration_scopes.json',{'scope_statistics':stats,'shares_with_explicit_denominators':shares,
            'fixed_fire':{'private_key':firekey,'private_group':primary,'secondary_private_group':secondary,'validation_fold':int(fire.fold.iloc[0]),
                          'T0':float(fire.T0.iloc[0]),'outcome_term':float(fire.outcome_term.iloc[0]),'prediction_term':float(fire.prediction_term.iloc[0]),
                          'saved_gain':rowgain,'mu19':float(fire.muref.iloc[0]),'mu20':float(fire.mu20.iloc[0])},
            'evaluation_exclusions_only_no_record_removed':True,'no_new_model_or_bootstrap':True})
        for name,cell in scopes.items():
            if name in ['fire_row','fire_full_component','selected12']:cell.to_parquet(run/(name+'_existing_rows.parquet'),index=False)
        coef=pq.read_table(ROOT/p['coefficients']).to_pandas();coef=coef[coef.line.eq('buildings')&coef.feature.eq(AD)&coef.level.eq('unit')]
        check('Ten fixed AD coefficient rows',len(coef)==10 and set(coef.model_id)=={'W2-B19','W2-B20'})
        coef['rate_ratio_yes_no']=np.exp(coef.beta_raw);coef.to_parquet(run/'AD_coefficient_by_fold.parquet',index=False)
        base=None;rowcells=[];claimcells=[];membership=[]
        claims=pq.read_table(ROOT/p['claims_2023'],filters=[('line','=','buildings')]).to_pandas()
        check('Building canonical claims2023 accepted',claims.year.eq(2023).all() and claims.included_in_T0.all() and claims.claim_id.is_unique)
        columns=KEY+['year','fold','group_id','T0','exposure',E,'x_new_business',AD]
        for fold,path in enumerate(p['building_frames']):
            frame=pq.read_table(ROOT/path,columns=columns).to_pandas().sort_values(KEY).reset_index(drop=True);guard(frame)
            check('Building fixed12580 rows '+str(fold),len(frame)==12580)
            frame['AD_group']=ad_labels(frame);frame['business']=np.where(frame.x_new_business.eq(1),'new','renewal')
            frame['T0_cents']=np.rint(frame.T0*100).astype('int64')
            check('Building T0 exact cents '+str(fold),np.max(np.abs(frame.T0*100-frame.T0_cents))<1e-5)
            if base is None:base=frame.copy()
            else:
                for col in KEY+['group_id','fold','T0_cents',AD,'business']:check('Same building metadata '+col+str(fold),frame[col].equals(base[col]))
            mapped=claims[KEY+['claim_id','peril','status','T0_cents','fold','group_id']].merge(frame[KEY+['AD_group','business']],on=KEY,how='left',validate='many_to_one')
            check('All building claims mapped '+str(fold),mapped.AD_group.notna().all())
            for role,mask in [('fit',frame.fold.ne(fold)),('heldout',frame.fold.eq(fold))]:
                period=frame[mask];claim=mapped[mapped.fold.ne(fold) if role=='fit' else mapped.fold.eq(fold)]
                check('Peril numerator complete '+str(fold)+role,int(claim.T0_cents.sum())==int(period.T0_cents.sum()))
                for ad in ['no','yes','missing']:
                    for business in ['new','renewal']:
                        z=period[period.AD_group.eq(ad)&period.business.eq(business)]
                        rowcells.append({'fold_view':fold,'role':role,'AD_group':ad,'business':business,'rows':len(z),'positive_rows':int(z.T0_cents.gt(0).sum()),
                                         'T0_cents':int(z.T0_cents.sum()),'nominal_exposure':float(z.exposure.sum()),'effective_C0_exposure':float(z[E].sum()),
                                         'primary_fire_rows':int(z.group_id.eq(primary).sum()),'secondary_fire_rows':int(z.group_id.eq(secondary).sum())})
                for keys,z in claim.groupby(['AD_group','business','peril'],sort=True):
                    claimcells.append({'fold_view':fold,'role':role,'AD_group':keys[0],'business':keys[1],'peril':keys[2],
                                       'claims':len(z),'T0_cents':int(z.T0_cents.sum()),'open_claims':int(z.status.eq('open').sum()),
                                       'fixed_two_fire_cents':int(z.loc[z.group_id.isin([primary,secondary]),'T0_cents'].sum())})
            for label,gid in [('primary',primary),('secondary',secondary)]:
                z=frame[frame.group_id.eq(gid)]
                membership.append({'fold_view':fold,'fixed_group_label':label,'validation_fold':int(z.fold.iloc[0]),'present_in_fit':bool(z.fold.ne(fold).all()),
                                   'rows':len(z),'T0_cents':int(z.T0_cents.sum()),'AD_groups':sorted(z.AD_group.unique().tolist())})
        pd.DataFrame(rowcells).to_parquet(run/'AD_period_composition_by_fold.parquet',index=False)
        pd.DataFrame(claimcells).to_parquet(run/'AD_peril_composition_by_fold.parquet',index=False)
        pd.DataFrame(membership).to_parquet(run/'fixed_fire_training_membership.parquet',index=False)
        local=pq.read_table(ROOT/p['B19_local_influence'],filters=[('line','=','buildings'),('group_id','in',[primary,secondary])]).to_pandas()
        check('Existing B19 local influence excludes heldout',local['fold'].ne(local.group_validation_fold).all())
        check('Each fixedfire appears four B19 training views',len(local)==8 and local.groupby('group_id')['fold'].nunique().eq(4).all())
        local['fixed_group_label']=np.where(local.group_id.eq(primary),'primary','secondary');local.to_parquet(run/'existing_B19_local_influence_fixed_fires.parquet',index=False)
        dump(run/'report.json',{'id':p['id'],'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'run':rel(run),'passed':len(checks),'failed':0,'checks':checks,
            'successful_fit_calls':0,'model_loads':0,'new_price_predictions':0,'new_bootstrap':0,'new_candidate_recipes':0,'only_saved2023_artifacts':True,
            'reference':'W2-B00','all_alternatives_preserved':True,'ledger_read':False,'professional_independent_validation':False})
        files=[x for x in run.iterdir() if x.is_file()];dump(run/'manifest.json',{'files':[{'path':rel(x),'sha256':sha(x),'bytes':x.stat().st_size} for x in sorted(files)]})
        print(json.dumps({'run':rel(run),'passed':len(checks),'failed':0,'successful_fit_calls':0,'model_loads':0,'scope_summaries':{k:stats[k] for k in ['global','fire_row','fire_full_component','global_without_fire_component']},'shares':shares},ensure_ascii=True))
        return run
    except Exception as exc:
        dump(run/'failure.json',{'error':str(exc),'run':rel(run),'checks':checks,'successful_fit_calls':0,'model_loads':0,'new_price_predictions':0});raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--plan',required=True);main(Path(parser.parse_args().plan).resolve())
