"""Descomposición de nivel e influencia desde OOF congelado; ningún ajuste."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,sys,uuid
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
spec=importlib.util.spec_from_file_location('level_review_checker',REPO/'herramientas/verificar_desarrollo2023_semana2.py')
c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
np,pd,pq=c.np,c.pd,c.pq
ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);args=ap.parse_args()
run=Path(args.run).resolve();run.relative_to(REPO/'privado/semana2/desarrollo2023')
oof=pq.read_table(run/'oof_2023.parquet').to_pandas();assert oof.year.eq(2023).all()
first=oof.loc[oof.model_id.eq('W2-B00')].sort_values(c.KEY).reset_index(drop=True)
groups,codes=np.unique(first.group_id,return_inverse=True);g=len(groups)
n=np.bincount(codes).astype(float);y=np.bincount(codes,weights=first.T0);syroot=np.bincount(codes,weights=np.sqrt(first.T0))
positive=np.bincount(codes,weights=first.T0.gt(0));exposure=np.bincount(codes,weights=first.exposure)
null=8*(np.sqrt(n.sum()*y.sum())-syroot.sum());reference_loss=np.bincount(codes,weights=first.unit_deviance)
out=run.parent/('revision_nivel_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);out.mkdir()
level=[];influence=[];selections={};all_groups=[]
for mid in ['W2-B03','W2-B05']:
    part=oof.loc[oof.model_id.eq(mid)].sort_values(c.KEY).reset_index(drop=True);assert part[c.KEY].equals(first[c.KEY])
    for dimension,labels in [('global',np.repeat('all',len(part))),('line',part.line),('fold',part.fold),('business',np.where(part.x_new_business.eq(1),'new_business','renewal'))]:
        tmp=part.assign(segment=labels)
        for label,sub in tmp.groupby('segment',observed=True):
            positions=sub.index;ref=first.loc[positions];actual=float(sub.T0.sum());pred=float(sub.prediction.sum());refpred=float(ref.prediction.sum())
            level.append({'model_id':mid,'dimension':dimension,'segment':str(label),'rows':len(sub),
              'observed_total':actual,'predicted_total':pred,'reference_predicted_total':refpred,
              'actual_over_expected':actual/pred,'predicted_over_reference':pred/refpred,
              'observed_shortfall_CU':actual-pred,'difference_from_reference_CU':pred-refpred})
    loss=np.bincount(codes,weights=part.unit_deviance);advantage=reference_loss-loss
    ranking=np.argsort(-advantage,kind='stable');count=min(g-1,max(5,int(np.ceil(.001*g))))
    chosen=ranking[:count];selections[mid]=set(groups[chosen].tolist());keep=np.ones(g,dtype=bool);keep[chosen]=False
    restnull=8*(np.sqrt(n[keep].sum()*y[keep].sum())-syroot[keep].sum())
    flips=np.where(np.cumsum(advantage[ranking])>=advantage.sum())[0]
    record={'model_id':mid,'groups':g,'delta_D2':float(advantage.sum()/null),'favorable_groups_removed':count,
      'removed_advantage_over_net_advantage':float(advantage[chosen].sum()/advantage.sum()),
      'removed_observed_cost_share':float(y[chosen].sum()/y.sum()),'removed_exposure_share':float(exposure[chosen].sum()/exposure.sum()),
      'removed_rows':int(n[chosen].sum()),'removed_positive_rows':int(positive[chosen].sum()),
      'minimum_favorable_groups_for_sign_flip':int(flips[0]+1) if len(flips) else None,
      'delta_after_removal':float(advantage[keep].sum()/restnull),
      'largest_favorable_group_share_of_net_gain':float(advantage.max()/advantage.sum()),
      'largest_adverse_group_delta':float(advantage.min()/null)}
    influence.append(record)
    table=pd.DataFrame({'model_id':mid,'group_id':groups,'rows':n,'exposure':exposure,'observed':y,
        'positive_rows':positive,'advantage':advantage,'reference_loss':reference_loss,'model_loss':loss})
    table['favorable_rank']=np.argsort(ranking)+1;all_groups.append(table)
pd.concat(all_groups,ignore_index=True).to_parquet(out/'group_influence.parquet',index=False)
result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'source_run':str(run.relative_to(ROOT)),'parent_oof_sha256':c.sha(run/'oof_2023.parquet'),
  'source_sha256':c.sha(Path(__file__)),'level':level,'influence':influence,
  'favorable_groups_overlap':len(selections['W2-B03']&selections['W2-B05']),
  'fit_calls':0,'new_calibration_factors':0,'year':2023,'confirmation_2024_open':False,
  'limitations':['Aggregate differences concern observed T0, not true ultimate calibration',
    'Evaluation-group removal keeps all fitted models fixed; not a refitting jackknife or a data-cleaning rule',
    'Training-set level normalization has not been tried in this review; future recipe must be preregistered',
    'B00 itself depends on training claims; anchoring does not remove all sensitivity to large losses']}
(out/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(out/'code_snapshot.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps({'review':str(out.relative_to(ROOT)),'global_level':[x for x in level if x['dimension']=='global'],
                 'line_level':[x for x in level if x['dimension']=='line'],'influence':influence,
                 'favorable_groups_overlap':result['favorable_groups_overlap']},ensure_ascii=True))
