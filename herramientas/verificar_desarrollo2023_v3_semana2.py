"""Oráculo separado del ancla y mezcla; replay sin ajustar estimadores base."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,math,re,sys,uuid
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
spec=importlib.util.spec_from_file_location('v3_independent_math',REPO/'herramientas/verificar_desarrollo2023_semana2.py')
c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
np,pd,pq=c.np,c.pd,c.pq;KEY=c.KEY
FIT_ATTEMPTS=0
def no_fit(*args,**kwargs):
    global FIT_ATTEMPTS
    FIT_ATTEMPTS+=1
    raise AssertionError('fit bloqueado durante comprobación')
def predict(bundle,frame):
    assert frame.year.eq(2023).all() and not frame.is_test.any()
    raw=c.predict(bundle['parent'],frame);w=bundle['shape_weight']
    return (1-w)*bundle['reference_rate']+w*bundle['scale']*raw


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);args=ap.parse_args()
    run=Path(args.run).resolve();run.relative_to(REPO/'privado/semana2/desarrollo2023')
    report=c.read(run/'report.json');plan=c.read(run/'plan_snapshot.json');parent=ROOT/plan['parent_run'];refdir=ROOT/plan['reference_model_run']
    checks=[]
    def check(name,value,detail=None):checks.append({'name':name,'pass':bool(value),'detail':detail})
    close=lambda a,b:np.allclose(a,b,rtol=2e-11,atol=1e-8,equal_nan=True)
    for item in c.read(run/'manifest.json')['files']:check('Artifact '+item['path'],c.sha(run/item['path'])==item['sha256'])
    for item in c.read(run/'frozen_sources_before_fit.json')['files']:check('Source '+item['path'],c.sha(ROOT/item['path'])==item['sha256'])
    check('Plan/code frozen',c.sha(run/'plan_snapshot.json')==report['plan_sha256'] and c.sha(run/'code_snapshot.py')==report['code_sha256'])
    header=re.search(r'^## Codex \| COD-S2-20261023-012 \| ([^|]+) \|',(run/'forum_before_training.md').read_text(encoding='utf-8'),re.M)
    check('Preregistration before factors',header is not None and datetime.fromisoformat(header[1].strip())<datetime.fromisoformat(report['started_utc']))
    check('No base fitting; 30 factors/60 adapters',report['new_base_estimator_fits']==0 and report['base_estimator_fit_attempts']==0 and report['training_level_factors']==30 and report['adapter_bundles']==60)
    check('2024/test closed',report['scope_2024']=={'price_fit_rows':0,'predictions':0,'scores':0,'confirmation_open':False} and report['test_predictions']==0)
    selector=c.read(REPO/'registro/semana2_seleccion_actual.json');check('No 2024 ledger',not (ROOT/selector['ledger_workspace_relative']).exists())
    check('B00/no promotion/no final roster',report['reference_retained']=='W2-B00' and not report['promotion'] and not report['final_confirmation_roster_frozen'])
    for cls in [c.TweedieRegressor,c.SimpleImputer,c.StandardScaler,c.OneHotEncoder,c.ColumnTransformer,c.Pipeline,c.lgb.LGBMRegressor,c.lgb.LGBMModel]:
        cls.fit=no_fit
        if hasattr(cls,'fit_transform'):cls.fit_transform=no_fit
    old=pq.read_table(parent/'oof_2023.parquet').to_pandas();oof=pq.read_table(run/'oof_2023.parquet').to_pandas()
    ids=plan['comparators_reused_without_refit']+[x['id'] for x in plan['models']];recipes={x['id']:x for x in plan['models']}
    check('Only 2023 unique keys',oof.year.eq(2023).all() and not oof.duplicated(['model_id',*KEY]).any())
    check('Six comparator tables unchanged',oof.loc[oof.model_id.isin(ids[:6])].reset_index(drop=True).equals(old.sort_values(['model_id',*KEY]).reset_index(drop=True)))
    first=old.loc[old.model_id.eq('W2-B00')].sort_values(KEY).reset_index(drop=True);ordered={}
    for mid in ids:
        part=oof.loc[oof.model_id.eq(mid)].sort_values(KEY).reset_index(drop=True);ordered[mid]=part
        check('Complete original keys '+mid,part[KEY].equals(first[KEY]) and len(part)==50094)
        for col in ['year','group_id','fold','exposure','T0','reserve','T1_reserve075','T1_reserve125','e_cost_mix_1.0']:check('Common '+mid+col,part[col].equals(first[col]))
        check('Positive rates '+mid,np.isfinite(part.annual_rate).all() and part.annual_rate.gt(0).all())
        check('Single offset '+mid,np.array_equal(part.prediction,part.annual_rate*part['e_cost_mix_1.0']))
        check('Unit deviance '+mid,close(part.unit_deviance,c.dev(part.T0,part.prediction)))
        point=next(x for x in report['summary'] if x['model_id']==mid)
        check('Global D2 '+mid,close(point['D2'],c.d2_tweedie_score(part.T0,part.prediction,power=1.5)))
    factor_records={};training=[]
    ready=c.read(run/'readiness_snapshot.json');blocks=c.read(ROOT/ready['availability_contract'])['blocks']
    for line in ['motor','buildings','contents']:
        path=run/f'inputs_2023/{line}.parquet';data=pq.read_table(path).to_pandas();block=blocks[line]
        check('Same 2023 input '+line,c.sha(path)==c.sha(parent/f'inputs_2023/{line}.parquet') and data.year.eq(2023).all() and not data.is_test.any())
        for fold in range(5):
            linkpath=run/f'links_2023/{line}_fold{fold}.parquet';links=pq.read_table(linkpath).to_pandas();offsets=[x for x in links if x.startswith('e_cost_')]
            check('Frozen C0 '+line+str(fold),c.sha(linkpath)==c.sha(parent/f'links_2023/{line}_fold{fold}.parquet'))
            frame=data.merge(links[KEY+offsets],on=KEY,validate='one_to_one');fit=frame.loc[frame.fold.ne(fold)];valid=frame.loc[frame.fold.eq(fold)].sort_values(KEY).reset_index(drop=True)
            for col in ['group_id','customer_id','address_id']:check('Disjoint '+line+str(fold)+col,not set(fit[col])&set(valid[col]))
            fitrows=run/f'fit_rows/{line}_fold{fold}.parquet'
            check('Untrimmed saved roles '+line+str(fold),c.sha(fitrows)==c.sha(parent/f'fit_rows/{line}_fold{fold}.parquet'))
            refpath=refdir/'models'/f'W2-B00_{line}_fold{fold}'/'bundle.joblib';ref=c.joblib.load(refpath);e=fit['e_cost_mix_1.0'].to_numpy()
            optimal=math.fsum((fit.T0/np.sqrt(e)).tolist())/math.fsum(np.sqrt(e).tolist())
            check('B00 anchor from same training '+line+str(fold),close(ref['rate'],optimal))
            for pid in ['W2-B03','W2-B05']:
                sourcepath=parent/'models'/f'{pid}_{line}_fold{fold}'/'bundle.joblib';base=c.joblib.load(sourcepath)
                # Independently predict using only features and metadata, no responses/reserve labels.
                no_labels=fit.drop(columns=['T0','reserve','T1_reserve075','T1_reserve125'])
                with c.threadpool_limits(limits=2):rfit=c.predict(base,no_labels);rvalid=c.predict(base,valid)
                denominator=math.fsum((e*rfit).tolist());numerator=ref['rate']*math.fsum(e.tolist());scale=numerator/denominator
                entry=c.read(run/'factors'/f'{pid}_{line}_fold{fold}.json');factor_records[pid,line,fold]=entry
                check('Training-only scale '+str((pid,line,fold)),close(entry['scale'],scale) and entry['fit_rows']==len(fit) and not entry['factor_fit_uses_heldout_rows'])
                check('Factor source hashes '+str((pid,line,fold)),entry['parent_sha256']==c.sha(sourcepath) and entry['reference_sha256']==c.sha(refpath))
                for mid,specification in recipes.items():
                    if specification['parent_model']!=pid:continue
                    node=f'{mid}_{line}_fold{fold}';folder=run/'models'/node;bundle=c.joblib.load(folder/'bundle.joblib');receipt=c.read(folder/'receipt.json');w=specification['shape_weight']
                    check('Formula parameters '+node,bundle['family']=='AnchoredRate' and bundle['shape_weight']==w and close(bundle['scale'],scale) and bundle['reference_rate']==ref['rate'])
                    check('Exact whitelist '+node,bundle['columns']==block['all']==bundle['parent']['columns']==receipt['features'])
                    check('Parent params unchanged '+node,bundle['parent']['estimator'].get_params()==base['estimator'].get_params())
                    if pid=='W2-B03':
                        check('Parent GLM coefficients unchanged '+node,np.array_equal(bundle['parent']['estimator'].coef_,base['estimator'].coef_) and bundle['parent']['estimator'].intercept_==base['estimator'].intercept_)
                    else:check('Parent booster unchanged '+node,bundle['parent']['estimator'].booster_.model_to_string()==base['estimator'].booster_.model_to_string())
                    part=ordered[mid].loc[ordered[mid].line.eq(line)&ordered[mid].fold.eq(fold)].reset_index(drop=True)
                    check('Held-out keys '+node,part[KEY].equals(valid[KEY]))
                    for col in offsets:check('C0/scenario offset '+node+col,np.array_equal(part[col],valid[col]))
                    expected=(1-w)*ref['rate']+w*scale*rvalid
                    check('Independent formula '+node,close(part.annual_rate,expected))
                    with c.threadpool_limits(limits=2):actual=predict(bundle,valid);train_r=predict(bundle,fit)
                    check('Blocked-fit replay exact '+node,np.array_equal(actual,part.annual_rate))
                    check('Unchanged embedded parent predictions '+node,close(actual,(1-w)*ref['rate']+w*bundle['scale']*rvalid))
                    train_total=math.fsum((e*train_r).tolist())
                    check('Exact training aggregate anchor '+node,close(train_total,numerator) and close(receipt['fit_predicted_total'],numerator))
                    if w==.5:check('Half anchored-rate deviation '+node,close(actual-ref['rate'],.5*(scale*rvalid-ref['rate'])))
                    check('Rate ordering within scope '+node,(np.diff(actual[np.argsort(rvalid,kind='stable')])>=-1e-10).all())
                    training.append({'model_id':mid,'line':line,'fold':fold,'deviance_sum':float(c.dev(fit.T0,e*train_r).sum()),'fit_predicted_total':train_total})
    check('Exactly 30 distinct factors',len(factor_records)==30 and len(list((run/'factors').glob('*.json')))==30)
    for item in c.read(run/'diagnostics/training_nodes.json'):
        actual=next(x for x in training if all(x[k]==item[k] for k in ['model_id','line','fold']))
        check('Training node '+str((item['model_id'],item['line'],item['fold'])),close([item['deviance_sum'],item['fit_predicted_total']],[actual['deviance_sum'],actual['fit_predicted_total']]))
    for item in c.read(run/'diagnostics/segments.json'):
        part=ordered[item['model_id']]
        if item['segment']=='line':part=part.loc[part.line.eq(item['label'])]
        elif item['segment']=='fold':part=part.loc[part.fold.eq(int(item['label']))]
        else:part=part.loc[part.x_new_business.eq(1) if item['label']=='new_business' else part.x_new_business.ne(1)]
        check('Segment '+str((item['model_id'],item['segment'],item['label'])),close(item['D2'],c.d2_tweedie_score(part.T0,part.prediction,power=1.5)))
    scenarios={'base':('T0','e_cost_mix_1.0'),'reserve075':('T1_reserve075','e_cost_mix_0.75'),'reserve125':('T1_reserve125','e_cost_mix_1.25'),'late_cost05':('T0','e_cost_mix_tail0.05'),'late_cost10':('T0','e_cost_mix_tail0.1')}
    for item in c.read(run/'diagnostics/observation_sensitivity.json'):
        part=ordered[item['model_id']];ycol,ecol=scenarios[item['scenario']]
        check('Fixed adapter sensitivity '+item['model_id']+item['scenario'],close(item['D2'],c.d2_tweedie_score(part[ycol],part.annual_rate*part[ecol],power=1.5)))
    groups,codes=np.unique(first.group_id,return_inverse=True);g=len(groups);n=np.bincount(codes).astype(float)
    sy=np.bincount(codes,weights=first.T0);sr=np.bincount(codes,weights=np.sqrt(first.T0));losses=np.array([np.bincount(codes,weights=c.dev(ordered[mid].T0,ordered[mid].prediction)) for mid in ids]).T
    for item in c.read(run/'diagnostics/frozen_parent_influence.json'):
        parent_advantage=losses[:,0]-losses[:,ids.index(item['parent_model'])];excluded=np.argsort(-parent_advantage,kind='stable')[:31]
        keep=np.ones(g,dtype=bool);keep[excluded]=False;den=8*(np.sqrt(n[keep].sum()*sy[keep].sum())-sr[keep].sum())
        delta=(losses[keep,0]-losses[keep,ids.index(item['model_id'])]).sum()/den
        check('Frozen parent influence '+item['model_id'],close(item['delta_D2_after_frozen_parent_removal'],delta))
    pairs=c.read(run/'diagnostics/pairs.json');boot=pq.read_table(run/'diagnostics/bootstrap_2023.parquet').to_pandas()
    config=plan['diagnostics']['development_uncertainty'];rng=np.random.default_rng(config['seed']);digest=hashlib.sha256();distributions={(p['candidate'],p['reference']):[] for p in pairs['pairs']}
    check('45 pairs and 90000 replicates',len(distributions)==45 and len(boot)==90000)
    for start in range(0,config['replicates'],32):
        draw=rng.integers(0,g,size=(min(32,config['replicates']-start),g),dtype=np.int64);digest.update(draw.tobytes())
        denominator=8*(np.sqrt(n[draw].sum(axis=1)*sy[draw].sum(axis=1))-sr[draw].sum(axis=1));ls=losses[draw].sum(axis=1)
        for pair in distributions:distributions[pair].extend(((ls[:,ids.index(pair[1])]-ls[:,ids.index(pair[0])])/denominator).tolist())
    check('Same shared exploratory draws',digest.hexdigest()==pairs['draws_sha256']==c.read(parent/'diagnostics/pairs.json')['draws_sha256'])
    for p in pairs['pairs']:
        key=(p['candidate'],p['reference']);samples=distributions[key];saved=boot.loc[boot.candidate.eq(key[0])&boot.reference.eq(key[1])].sort_values('replicate')
        check('Bootstrap values '+str(key),len(saved)==2000 and close(saved.delta_D2,samples))
        check('Exploratory interval '+str(key),close([p['exploratory_lower95'],p['exploratory_upper95']],np.quantile(samples,[.025,.975])))
        advantage=losses[:,ids.index(key[1])]-losses[:,ids.index(key[0])];den=8*(np.sqrt(n.sum()*sy.sum())-sr.sum())
        check('Pair point '+str(key),close(p['delta_D2'],advantage.sum()/den))
        count=min(g-1,max(5,math.ceil(.001*g)));keep=np.ones(g,dtype=bool);keep[np.argsort(-advantage,kind='stable')[:count]]=False
        reduced=8*(np.sqrt(n[keep].sum()*sy[keep].sum())-sr[keep].sum())
        check('Own top31 influence '+str(key),close(p['delta_after_removal'],advantage[keep].sum()/reduced))
    check('No attempted base fit in checker',FIT_ATTEMPTS==0)
    directory=run/'verifications';directory.mkdir(exist_ok=True);path=directory/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]+'.json')
    result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'source_sha256':c.sha(Path(__file__)),'run':str(run.relative_to(ROOT)),
      'checks':checks,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'base_fit_attempts':FIT_ATTEMPTS,
      'professional_independent_validation':False,'price_2024_predictions_or_scores':0}
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'verification':str(path.relative_to(ROOT)),'passed':result['passed'],'failed':result['failed'],'failures':[x for x in checks if not x['pass']]},ensure_ascii=True))
    return 0 if not result['failed'] else 2


if __name__=='__main__':raise SystemExit(main())
