"""Mismas cribas2023 para candidatos nuevos; sin productores ni modelos."""
import hashlib
import numpy as np,pandas as pd
from .modelos_robustos2023 import KEY,metrics


def evaluate(old,new,ids,fit_calls,reference_id='W2-B20'):
    mids=['W2-B00','W2-B20',reference_id]+ids
    parts={mid:frame.sort_values(KEY).reset_index(drop=True) for mid,frame in pd.concat([old,new]).groupby('model_id') if mid in mids}
    first=parts[reference_id];gcodes,groups=pd.factorize(first.group_id,sort=True);g=len(groups)
    for mid,p in parts.items():
        assert len(p)==50094 and p.year.eq(2023).all() and p[KEY].equals(first[KEY])
        for c in ['T0','fold','group_id','exposure','e_cost_mix_1.0']:assert np.array_equal(first[c].to_numpy(),p[c].to_numpy()),c
    n=np.bincount(gcodes,minlength=g);sy=np.bincount(gcodes,weights=first.T0,minlength=g);sr=np.bincount(gcodes,weights=np.sqrt(first.T0),minlength=g)
    losses={mid:np.bincount(gcodes,weights=p.unit_deviance,minlength=g) for mid,p in parts.items()}
    fullnull=metrics(first)['null_deviance_sum'];summaries=[];segments=[];sens=[]
    for mid,p in parts.items():
        summaries.append({'model_id':mid,**metrics(p)})
        labels={'line':p.line.astype(str),'fold':p.fold.astype(str),'business':np.where(p.x_new_business.eq(1),'new','renewal'),
                'line_business':p.line.astype(str)+'_'+np.where(p.x_new_business.eq(1),'new','renewal')}
        for dim,lab in labels.items():
            for name,cell in p.assign(label=lab).groupby('label',observed=True):segments.append({'model_id':mid,'dimension':dim,'label':str(name),**metrics(cell)})
        for y,e in [('T1_reserve075','e_cost_mix_0.75'),('T1_reserve125','e_cost_mix_1.25'),('T0','e_cost_mix_tail0.05'),('T0','e_cost_mix_tail0.1')]:
            sens.append({'model_id':mid,'target':y,'effective_exposure':e,**metrics(p.assign(stress=p.annual_rate*p[e]),prediction='stress',target=y)})
    rng=np.random.default_rng(2026102501);boot={mid:[] for mid in ids};digest=hashlib.sha256()
    for start in range(0,2000,32):
        draw=rng.integers(0,g,size=(min(32,2000-start),g));digest.update(draw.tobytes())
        null=8*(np.sqrt(n[draw].sum(axis=1)*sy[draw].sum(axis=1))-sr[draw].sum(axis=1))
        for mid in ids:boot[mid].extend(((losses[reference_id][draw].sum(axis=1)-losses[mid][draw].sum(axis=1))/null).tolist())
    pairs=[];gates=[]
    for mid in ids:
        adv=losses[reference_id]-losses[mid];keep=np.ones(g,bool);removed=max(5,int(np.ceil(.001*g)));keep[np.argsort(-adv,kind='stable')[:removed]]=False
        null=8*(np.sqrt(n[keep].sum()*sy[keep].sum())-sr[keep].sum());after=float(adv[keep].sum()/null)
        q=np.quantile(boot[mid],[.0041666666667,.9958333333333]);delta=float(adv.sum()/fullnull)
        fd=[];hd=[]
        for dim in ['fold','line_business']:
            for cell in [x for x in segments if x['model_id']==mid and x['dimension']==dim]:
                b=next(x for x in segments if x['model_id']==reference_id and x['dimension']==dim and x['label']==cell['label'])
                gain=(b['deviance_sum']-cell['deviance_sum'])/fullnull
                if dim=='fold':fd.append(gain)
                else:hd.append({'segment':cell['label'],'delta_over_full_null':gain})
        positive=sum(x>0 for x in fd)
        pairs.append({'candidate':mid,'reference':reference_id,'delta_D2':delta,'exploratory_interval':q.tolist(),
           'removed_favorable_groups':removed,'delta_after_removal':after,'positive_folds':positive,'segment_deltas_over_full_null':hd,'adaptive_search_disclosed':True})
        checks={'material_gain':delta>=.005,'lower_bound':bool(q[0]>.0005),'four_folds':positive>=4,
                'segment_harm':min(x['delta_over_full_null'] for x in hd)>=-.0005,'not_few_groups':after>=.0005}
        gates.append({'model_id':mid,'checks':checks,'all_pass':all(checks.values()),'formal_promotion':False})
    return {'summaries':summaries,'segments':segments,'pairs':pairs,'gates':gates,'sensitivity':sens,
       'bootstrap_draws_sha256':digest.hexdigest(),'new_price_fits':fit_calls,'new_C0_fits':0,
       '2024_closed':True,'B00_preserved':True,'promotion':False,'public_score_used_for_parameters':False,'new_submissions':0}
