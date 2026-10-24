"""Replay, recetas y oráculo de pérdidas v2, sin importar productores de precios."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,math,re,sys,uuid
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
spec=importlib.util.spec_from_file_location('checker_dev2_oracle',REPO/'herramientas/verificar_desarrollo2023_semana2.py')
c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
np,pd,pq=c.np,c.pd,c.pq;KEY=c.KEY


def predict(bundle,frame):
    assert frame.year.eq(2023).all() and not frame.is_test.any()
    if bundle['family']!='LGBMBoosterPrefix':return c.predict(bundle,frame)
    x=frame[bundle['columns']].copy()
    for col,levels in bundle['categories'].items():x[col]=pd.Categorical(x[col].astype(str),categories=levels)
    return bundle['booster'].predict(x)


def leaf_values(node):
    if 'leaf_index' in node:return {node['leaf_index']:node['leaf_value']}
    return dict(leaf_values(node['left_child']),**{}) | leaf_values(node['right_child'])


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);args=ap.parse_args()
    run=Path(args.run).resolve();run.relative_to(REPO/'privado/semana2/desarrollo2023')
    report=c.read(run/'report.json');plan=c.read(run/'plan_snapshot.json');parent=ROOT/plan['parent_run']
    ready=c.read(run/'readiness_snapshot.json');block_contract=c.read(ROOT/ready['availability_contract'])['blocks']
    checks=[];gradient=[]
    def check(name,condition,detail=None):checks.append({'name':name,'pass':bool(condition),'detail':detail})
    close=lambda a,b:np.allclose(a,b,rtol=2e-11,atol=1e-8,equal_nan=True)
    for item in c.read(run/'manifest.json')['files']:check('Artifact '+item['path'],c.sha(run/item['path'])==item['sha256'])
    for item in c.read(run/'frozen_sources_before_fit.json')['files']:check('Frozen source '+item['path'],c.sha(ROOT/item['path'])==item['sha256'])
    check('Plan checksum',c.sha(run/'plan_snapshot.json')==report['plan_sha256'])
    check('Code checksum',c.sha(run/'code_snapshot.py')==report['code_sha256'])
    prereg=re.search(r'^## Codex \| COD-S2-20261023-010 \| ([^|]+) \|',(run/'forum_before_training.md').read_text(encoding='utf-8'),re.M)
    check('Preregistered before all v2 fits',prereg is not None and datetime.fromisoformat(prereg[1].strip())<datetime.fromisoformat(report['started_utc']))
    check('20 actual fits and declared reuse',report['new_estimator_fits']==20 and report['GLM_bundle_reuses']==10 and report['prefix_exports']==15)
    check('All nodes complete',report['nodes_completed']==45 and report['nodes_failed']==0)
    check('No 2024/test prices or scores',report['scope_2024']=={'price_fit_rows':0,'predictions':0,'scores':0,'confirmation_open':False} and report['test_predictions']==0)
    check('Reference retained/no promotion',report['reference_retained']=='W2-B00' and not report['promotion'] and not report['final_confirmation_roster_frozen'])
    selection=c.read(REPO/'registro/semana2_seleccion_actual.json');check('2024 ledger remains unopened',not (ROOT/selection['ledger_workspace_relative']).exists())
    for cls in [c.TweedieRegressor,c.SimpleImputer,c.StandardScaler,c.OneHotEncoder,c.ColumnTransformer,c.Pipeline,c.lgb.LGBMRegressor,c.lgb.LGBMModel]:
        cls.fit=c.forbid_fit
        if hasattr(cls,'fit_transform'):cls.fit_transform=c.forbid_fit
    oof=pq.read_table(run/'oof_2023.parquet').to_pandas();old=pq.read_table(parent/'oof_2023.parquet').to_pandas()
    ids=['W2-B00','W2-B01','W2-B02','W2-B03','W2-B04','W2-B05'];recipes={x['id']:x for x in plan['models']}
    check('Only 2023 unique model rows',oof.year.eq(2023).all() and not oof.duplicated(['model_id',*KEY]).any())
    original=old.sort_values(['model_id',*KEY]).reset_index(drop=True)
    check('Original comparators exactly unchanged',oof.loc[oof.model_id.isin(ids[:3])].reset_index(drop=True).equals(original))
    check('Original OOF checksum',c.sha(parent/'oof_2023.parquet')==plan['parent_oof_sha256'])
    first=old.loc[old.model_id.eq('W2-B00')].sort_values(KEY).reset_index(drop=True)
    ordered={}
    for mid in ids:
        part=oof.loc[oof.model_id.eq(mid)].sort_values(KEY).reset_index(drop=True);ordered[mid]=part
        check('All original keys '+mid,part[KEY].equals(first[KEY]) and len(part)==50094)
        for field in ['year','group_id','fold','exposure','T0','reserve','T1_reserve075','T1_reserve125','e_cost_mix_1.0']:
            check('Common '+mid+' '+field,part[field].equals(first[field]))
        check('Positive finite rates '+mid,np.isfinite(part.annual_rate).all() and part.annual_rate.gt(0).all())
        check('Single offset '+mid,np.array_equal(part.prediction,part.annual_rate*part['e_cost_mix_1.0']))
        check('Separate unit deviance '+mid,close(part.unit_deviance,c.dev(part.T0,part.prediction)))
        point=next(x for x in report['summary'] if x['model_id']==mid)
        check('Global D2 '+mid,close(point['D2'],c.d2_tweedie_score(part.T0,part.prediction,power=1.5)))
    train_nodes=[]
    for line in ['motor','buildings','contents']:
        data=pq.read_table(run/f'inputs_2023/{line}.parquet').to_pandas();block=block_contract[line]
        check('Input same frozen 2023 '+line,c.sha(run/f'inputs_2023/{line}.parquet')==c.sha(parent/f'inputs_2023/{line}.parquet') and data.year.eq(2023).all() and not data.is_test.any())
        for fold in range(5):
            linkpath=run/f'links_2023/{line}_fold{fold}.parquet'
            links=pq.read_table(linkpath).to_pandas();offsets=[col for col in links if col.startswith('e_cost_')]
            check('Link unchanged '+line+str(fold),c.sha(linkpath)==c.sha(parent/f'links_2023/{line}_fold{fold}.parquet'))
            frame=data.merge(links[KEY+offsets],on=KEY,validate='one_to_one');fit=frame.loc[frame.fold.ne(fold)];valid=frame.loc[frame.fold.eq(fold)].sort_values(KEY).reset_index(drop=True)
            for col in ['group_id','customer_id','address_id']:check('Disjoint '+line+str(fold)+col,not set(fit[col])&set(valid[col]))
            for mid in ids[3:]:
                node=f'{mid}_{line}_fold{fold}';folder=run/'models'/node;bundle=c.joblib.load(folder/'bundle.joblib');receipt=c.read(folder/'receipt.json')
                check('Exact whitelist '+node,bundle['columns']==block['all']==receipt['features'])
                part=ordered[mid].loc[ordered[mid].line.eq(line)&ordered[mid].fold.eq(fold)].reset_index(drop=True)
                check('Validation keys '+node,part[KEY].equals(valid[KEY]))
                for col in offsets:check('Offset '+node+col,np.array_equal(part[col],valid[col]))
                with c.threadpool_limits(limits=2):r=predict(bundle,valid);tr=predict(bundle,fit)
                check('Blocked-fit replay exact '+node,np.array_equal(r,part.annual_rate))
                check('Rows in receipt '+node,receipt['train_rows']==len(fit) and receipt['validation_rows']==len(valid))
                if mid=='W2-B03':
                    if line!='buildings':
                        src=parent/'models'/f'W2-B01_{line}_fold{fold}'/'bundle.joblib'
                        check('B03 unchanged other-line model '+node,c.sha(folder/'bundle.joblib')==c.sha(src))
                        oldrate=ordered['W2-B01'].loc[ordered['W2-B01'].line.eq(line)&ordered['W2-B01'].fold.eq(fold),'annual_rate']
                        check('B03 unchanged other-line rate '+node,np.array_equal(r,oldrate))
                    else:
                        expected=recipes[mid]['params'];actual=bundle['estimator'].get_params()
                        check('Only stronger ridge parameters '+node,all(actual.get(k)==v for k,v in expected.items()))
                    transform=bundle['transformer'];raw=fit[block['numeric']].to_numpy(float)
                    median=np.array([np.nanmedian(raw[:,j]) if np.isfinite(raw[:,j]).any() else 0 for j in range(raw.shape[1])]);numeric=transform.named_transformers_['numeric']
                    check('Training medians '+node,close(median,numeric['median'].statistics_))
                    filled=np.where(np.isnan(raw),median,raw)
                    check('Training scaler '+node,close(numeric['scale'].mean_,filled.mean(axis=0)) and close(numeric['scale'].var_,filled.var(axis=0)))
                    categories=transform.named_transformers_['categorical'].categories_
                    check('Training OHE '+node,all(np.array_equal(categories[j],np.sort(fit[col].unique())) for j,col in enumerate(block['categorical'])))
                    with c.threadpool_limits(limits=2):
                        matrix=transform.transform(fit[block['all']]);e=fit['e_cost_mix_1.0'].to_numpy();g=np.sqrt(e)*(tr-fit.T0.to_numpy()/e)/np.sqrt(tr)/np.sqrt(e).sum()
                        grad=np.asarray(matrix.T@g).ravel()+bundle['estimator'].alpha*bundle['estimator'].coef_;norm=float(max(abs(g.sum()),np.abs(grad).max()))
                    gradient.append({'node':node,'norm':norm});check('GLM objective stationary '+node,norm<1e-4,norm)
                elif mid=='W2-B04':
                    parent_bundle=c.joblib.load(parent/'models'/f'W2-B02_{line}_fold{fold}'/'bundle.joblib')
                    parent_trees=parent_bundle['estimator'].booster_.dump_model(num_iteration=25)['tree_info'];trees=bundle['booster'].dump_model()['tree_info']
                    check('Exactly first 25 trees '+node,len(trees)==25 and trees==parent_trees)
                    check('Prefix parent categories '+node,bundle['categories']==parent_bundle['categories'])
                    x=valid[block['all']].copy()
                    for col,levels in bundle['categories'].items():x[col]=pd.Categorical(x[col].astype(str),categories=levels)
                    with c.threadpool_limits(limits=2):leaf=bundle['booster'].predict(x,pred_leaf=True).astype(int)
                    lograte=np.zeros(len(valid))
                    for j,tree in enumerate(trees):
                        vals=leaf_values(tree['tree_structure']);lograte+=np.array([vals[int(z)] for z in leaf[:,j]])
                    check('Oracle sum of 25 tree leaf values '+node,close(np.exp(lograte),r))
                else:
                    params=bundle['estimator'].get_params();expected=recipes[mid]['params'];trees=bundle['estimator'].booster_.dump_model()['tree_info']
                    check('Shallow frozen parameters '+node,all(params.get(k)==v for k,v in expected.items()))
                    check('At most 80 stump trees '+node,0<len(trees)<=80 and all(t['num_leaves']<=2 for t in trees))
                if mid in ['W2-B04','W2-B05']:
                    check('Training native categories '+node,all(levels==sorted(fit[col].astype(str).unique().tolist()) for col,levels in bundle['categories'].items()))
                train_nodes.append({'model_id':mid,'line':line,'fold':fold,'deviance_sum':float(c.dev(fit.T0,tr*fit['e_cost_mix_1.0'].to_numpy()).sum()),'predicted_total':float((tr*fit['e_cost_mix_1.0'].to_numpy()).sum())})
    for node in c.read(run/'diagnostics/training_nodes.json'):
        actual=next(x for x in train_nodes if all(x[k]==node[k] for k in ['model_id','line','fold']))
        check('Training loss and level '+str([node[k] for k in ['model_id','line','fold']]),close([node['deviance_sum'],node['predicted_total']],[actual['deviance_sum'],actual['predicted_total']]))
    for item in c.read(run/'diagnostics/segments.json'):
        part=ordered[item['model_id']]
        if item['segment']=='line':part=part.loc[part.line.eq(item['label'])]
        elif item['segment']=='fold':part=part.loc[part.fold.eq(int(item['label']))]
        else:part=part.loc[part.x_new_business.eq(1) if item['label']=='new_business' else part.x_new_business.ne(1)]
        check('Segment '+str((item['model_id'],item['segment'],item['label'])),close(item['D2'],c.d2_tweedie_score(part.T0,part.prediction,power=1.5)))
    scenarios={'base':('T0','e_cost_mix_1.0'),'reserve075':('T1_reserve075','e_cost_mix_0.75'),'reserve125':('T1_reserve125','e_cost_mix_1.25'),'late_cost05':('T0','e_cost_mix_tail0.05'),'late_cost10':('T0','e_cost_mix_tail0.1')}
    for item in c.read(run/'diagnostics/observation_sensitivity.json'):
        part=ordered[item['model_id']];ycol,ecol=scenarios[item['scenario']]
        check('Sensitivity '+item['model_id']+item['scenario'],close(item['D2'],c.d2_tweedie_score(part[ycol],part.annual_rate*part[ecol],power=1.5)))
    groups,codes=np.unique(first.group_id,return_inverse=True);g=len(groups)
    n=np.bincount(codes).astype(float);sy=np.bincount(codes,weights=first.T0);sr=np.bincount(codes,weights=np.sqrt(first.T0))
    losses=np.array([np.bincount(codes,weights=c.dev(ordered[mid].T0,ordered[mid].prediction)) for mid in ids]).T
    pairs=c.read(run/'diagnostics/pairs.json');boot=pq.read_table(run/'diagnostics/bootstrap_2023.parquet').to_pandas()
    config=plan['diagnostics']['development_uncertainty'];rng=np.random.default_rng(config['seed']);digest=hashlib.sha256()
    values={(p['candidate'],p['reference']):[] for p in pairs['pairs']}
    check('All fifteen pairs',len(values)==15 and len(boot)==30000)
    for start in range(0,config['replicates'],32):
        draw=rng.integers(0,g,size=(min(32,config['replicates']-start),g),dtype=np.int64);digest.update(draw.tobytes())
        denominator=8*(np.sqrt(n[draw].sum(axis=1)*sy[draw].sum(axis=1))-sr[draw].sum(axis=1));ls=losses[draw].sum(axis=1)
        for key in values:values[key].extend(((ls[:,ids.index(key[1])]-ls[:,ids.index(key[0])])/denominator).tolist())
    check('Shared draw checksum',digest.hexdigest()==pairs['draws_sha256'])
    check('Same exploratory draws as v1',pairs['draws_sha256']==c.read(parent/'diagnostics/pairs.json')['draws_sha256'])
    for pair in pairs['pairs']:
        key=(pair['candidate'],pair['reference']);dist=values[key];saved=boot.loc[boot.candidate.eq(key[0])&boot.reference.eq(key[1])].sort_values('replicate')
        check('Replicate values '+str(key),len(saved)==2000 and close(saved.delta_D2,dist))
        check('Interval '+str(key),close([pair['exploratory_lower95'],pair['exploratory_upper95']],np.quantile(dist,[.025,.975])))
        advantage=losses[:,ids.index(key[1])]-losses[:,ids.index(key[0])];den=8*(np.sqrt(n.sum()*sy.sum())-sr.sum())
        check('Point '+str(key),close(pair['delta_D2'],advantage.sum()/den))
        count=min(g-1,max(5,math.ceil(.001*g)));keep=np.ones(g,dtype=bool);keep[np.argsort(-advantage,kind='stable')[:count]]=False
        den_keep=8*(np.sqrt(n[keep].sum()*sy[keep].sum())-sr[keep].sum())
        check('Influence '+str(key),count==pair['removed_favorable_groups'] and close(pair['delta_after_removal'],advantage[keep].sum()/den_keep))
    directory=run/'verifications';directory.mkdir(exist_ok=True);path=directory/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]+'.json')
    result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'source_sha256':c.sha(Path(__file__)),'run':str(run.relative_to(ROOT)),'checks':checks,
       'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'GLM_gradients':gradient,'fit_calls':0,
       'professional_independent_validation':False,'price_2024_predictions_or_scores':0}
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'verification':str(path.relative_to(ROOT)),'passed':result['passed'],'failed':result['failed'],'failures':[x for x in checks if not x['pass']]},ensure_ascii=True))
    return 0 if result['failed']==0 else 2


if __name__=='__main__':raise SystemExit(main())
