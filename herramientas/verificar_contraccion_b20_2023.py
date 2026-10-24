"""Cotejo focal de coeficientes y grupos: fsum y diseño manual, sin ajuste."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,importlib.util,json,math,subprocess,sys
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import joblib

KEY=['market','line','row_id'];E='e_cost_mix_1.0'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()


def verify(run):
    run=run.resolve();p=read(run/'plan_snapshot.json');checks=[]
    def check(name,ok):checks.append({'name':name,'pass':bool(ok)});assert ok,name
    def close(a,b):return math.isclose(float(a),float(b),rel_tol=1e-10,abs_tol=1e-9)
    for x in p['frozen_sources']:check('Source '+x['path'],sha(ROOT/x['path'])==x['sha256'])
    rows=pq.read_table(run/'fixed_period_comparison_2023.parquet').to_pylist()
    saved=pq.read_table(ROOT/p['fixed_periods'],columns=KEY+['group_id']).to_pylist()
    check('Fixed20keys preserved',{tuple(r[k] for k in KEY) for r in rows}=={tuple(r[k] for k in KEY) for r in saved} and len(rows)==20)
    groupout=pq.read_table(run/'fixed_group_comparison_2023.parquet').to_pylist()
    groupdict={}
    for r in rows:groupdict.setdefault((r['group_id'],r['line'],r['fold']),[]).append(r)
    for out in groupout:
        cell=groupdict[(out['group_id'],out['line'],out['fold'])]
        for target,source in [('T0','T0'),('B19_prediction','B19_prediction'),('B20_prediction','B20_prediction'),('saved_deviance_gain_B20','saved_deviance_gain_B20')]:
            check('Fixed group fsum '+target,close(out[target],math.fsum(r[source] for r in cell)))
        check('Fixed group level ratio',close(out['prediction_ratio_B20_B19'],math.fsum(r['B20_prediction'] for r in cell)/math.fsum(r['B19_prediction'] for r in cell)))
    # The full existing OOF is used for level totals only, no score/bootstrap/regroup ranking.
    old=pq.read_table(ROOT/p['b19_oof'],filters=[('model_id','=','W2-B19')]).to_pandas().sort_values(KEY).reset_index(drop=True)
    new=pq.read_table(ROOT/p['b20_oof']).to_pandas().sort_values(KEY).reset_index(drop=True)
    keyset={tuple(r[k] for k in KEY) for r in rows}
    reason=pq.read_table(ROOT/p['selection_reasons']).to_pylist()
    top5={scope:{r['group_id'] for r in reason if r['reason']=='OOF_top5_adverse_'+scope} for scope in ['buildings','motor_new']}
    records=list(zip(old.to_dict('records'),new.to_dict('records')))
    for out in read(run/'level_diagnostics_2023.json'):
        dim,label=out['dimension'],out['label']
        def member(r):
            if dim=='global':return True
            if dim=='fixed_union':return tuple(r[k] for k in KEY) in keyset
            if dim=='line':return r['line']==label
            if dim=='fold':return str(r['fold'])==label
            if dim=='business':return ('new' if r['x_new_business']==1 else 'renewal')==label
            if dim=='line_business':return r['line']+'_'+('new' if r['x_new_business']==1 else 'renewal')==label
            if dim=='fixed_OOF_top5':return r['group_id'] in top5[label] and r['line']==('motor' if label=='motor_new' else 'buildings')
            raise ValueError(dim)
        cell=[(a,b) for a,b in records if member(a)]
        check('Level row count '+dim+label,len(cell)==out['rows'])
        for target,which,field in [('observed_T0',0,'T0'),('B19_observed_bridge_total',0,'prediction'),('B20_observed_bridge_total',1,'prediction')]:
            check('Level fsum '+target+dim+label,close(out[target],math.fsum(pair[which][field] for pair in cell)))
        for which,mid in [(0,'B19'),(1,'B20')]:check('Nominal fsum '+mid+dim+label,close(out[mid+'_nominal_total'],math.fsum(pair[which]['exposure']*pair[which]['annual_rate'] for pair in cell)))
        check('Saved gain fsum '+dim+label,close(out['saved_deviance_gain_B20'],math.fsum(a['unit_deviance']-b['unit_deviance'] for a,b in cell)))
    attribution=read(run/'fixed_gain_attribution.json');gain=math.fsum(r['saved_deviance_gain_B20'] for r in rows)
    check('Fixed attribution from same20 saved losses',close(attribution['fixed_group_saved_gain'],gain))
    check('Net remainder conservation',close(attribution['fixed_group_saved_gain']+attribution['remaining_group_saved_gain'],attribution['saved_global_deviance_gain_B20']))
    normout={(r['line'],r['fold']):r for r in pq.read_table(run/'standardized_coefficient_norms.parquet').to_pylist()}
    coefs=pq.read_table(run/'coefficients_original_scale.parquet').to_pylist()
    decomposition={tuple(r[k] for k in KEY):r for r in pq.read_table(run/'fixed_period_logratio_decomposition.parquet').to_pylist()}
    rowmap={tuple(r[k] for k in KEY):r for r in rows}
    for line in ['motor','buildings','contents']:
        for fold in range(5):
            bundles=[joblib.load(ROOT/p['b19_run']/f'models/W2-B19_{line}_fold{fold}/bundle.joblib'),joblib.load(ROOT/p['b20_run']/f'models/{line}_fold{fold}/bundle.joblib')]
            betas=[list(b['estimator'].coef_) for b in bundles]
            for j,mid in enumerate(['B19','B20']):check('Independent joint norm '+mid+line+str(fold),close(normout[(line,fold)][mid+'_std_L2'],math.sqrt(math.fsum(float(v)**2 for v in betas[j]))))
            count=sum(abs(float(b))>abs(float(a))+1e-10 for a,b in zip(*betas))
            check('Coordinate exceptions counted '+line+str(fold),count==normout[(line,fold)]['absolute_coordinates_larger'])
            for j,b in enumerate(bundles):
                native=b['estimator'];tr=b['transformer'];numeric=tr.transformers_[0][2];scale=tr.named_transformers_['numeric']['scale']
                recordscoef=[r for r in coefs if r['model_id']==('W2-B19' if j==0 else 'W2-B20') and r['line']==line and r['fold']==fold]
                cmap={(r['feature'],r['level']):r['beta_raw'] for r in recordscoef}
                expected_intercept=float(native.intercept_)-math.fsum(float(native.coef_[k])*float(scale.mean_[k])/float(scale.scale_[k]) for k in range(len(numeric)))
                check('Raw intercept centering '+line+str(fold)+str(j),close(cmap[('intercept','baseline')],expected_intercept))
                for k,col in enumerate(numeric):check('Raw slope '+col+line+str(fold)+str(j),close(cmap[(col,'unit')],float(native.coef_[k])/float(scale.scale_[k])))
            keys=[key for key,r in rowmap.items() if r['line']==line and r['fold']==fold]
            if not keys:continue
            frame=pq.read_table(ROOT/p['b19_run']/f'inputs_2023/{line}_fold{fold}.parquet',filters=[('row_id','in',[k[2] for k in keys])]).to_pylist()
            for r in frame:
                key=tuple(r[k] for k in KEY);out=decomposition[key];native_log=[];termsets=[]
                for j,b in enumerate(bundles):
                    tr=b['transformer'];num=tr.transformers_[0][2];cat=tr.transformers_[1][2];pipe=tr.named_transformers_['numeric'];enc=tr.named_transformers_['categorical'];beta=b['estimator'].coef_
                    terms={'intercept':float(b['estimator'].intercept_),'coverage':0.,'newbusiness':0.,'other_main_effects':0.}
                    rawterms=[];rc={(c['feature'],c['level']):c['beta_raw'] for c in coefs if c['model_id']==('W2-B19' if j==0 else 'W2-B20') and c['line']==line and c['fold']==fold}
                    rawterms.append(rc[('intercept','baseline')])
                    for k,col in enumerate(num):
                        x=r[col];x=float(pipe['median'].statistics_[k]) if x is None or pd.isna(x) else float(x)
                        label='newbusiness' if col=='x_new_business' else 'coverage' if col=='x_accidental_damage_cover' else 'other_main_effects'
                        terms[label]+=((x-float(pipe['scale'].mean_[k]))/float(pipe['scale'].scale_[k]))*float(beta[k])
                        rawterms.append(x*rc[(col,'unit')])
                    offset=len(num)
                    for k,col in enumerate(cat):
                        levels=list(enc.categories_[k]);drop=int(enc.drop_idx_[k]);value=str(r[col]);reference=str(levels[drop])
                        for h,level in enumerate(levels):
                            if h==drop:continue
                            if value==str(level):
                                terms['coverage' if col=='x_cover_type' else 'other_main_effects']+=float(beta[offset])
                            offset+=1
                        if (col,value) in rc:rawterms.append(rc[(col,value)])
                        else:check('Unknown category ignored as declared',enc.handle_unknown=='ignore')
                    linear=math.fsum(rawterms);native_log.append(linear);termsets.append(terms)
                    expected=rowmap[key][('B19' if j==0 else 'B20')+'_annual_rate']
                    check('Manual rawscale rate '+line+str(fold)+str(j),close(math.exp(linear),expected))
                for term in ['intercept','coverage','newbusiness','other_main_effects']:
                    check('Reused log term verified manually '+term,close(out['delta_'+term],termsets[1][term]-termsets[0][term]))
                check('Manual total logratio',close(out['delta_log_rate'],native_log[1]-native_log[0]))
                check('Existing observed ratio no C0 change',close(out['existing_prediction_ratio_B20_B19'],math.exp(native_log[1]-native_log[0])))
    spec=importlib.util.spec_from_file_location('b20diag_guard',ROOT/p['code']);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    for name in ['year','duplicate','missing_key','nonpositive_C0','changed_target']:
        f=new.copy()
        if name=='year':f.loc[0,'year']=2024
        if name=='duplicate':f.loc[1,KEY]=f.loc[0,KEY].to_numpy()
        if name=='missing_key':f.loc[0,'row_id']=None
        if name=='nonpositive_C0':f.loc[0,E]=0
        if name=='changed_target':f.loc[0,'T0']+=1
        caught=False
        try:module.pair_guard(f,old)
        except ValueError:caught=True
        check('Adverse guard '+name,caught)
    mismatch=copy.deepcopy(bundles[0]);mismatch['columns']=list(reversed(mismatch['columns']));caught=False
    try:module.transforms_equal(mismatch,bundles[1])
    except ValueError:caught=True
    check('Adverse transform incompatibility',caught)
    module.block_fit();blocked=0
    for cls in [module.TweedieRegressor,module.SimpleImputer,module.StandardScaler,module.OneHotEncoder,module.ColumnTransformer,module.Pipeline]:
        try:cls.fit(None,None)
        except RuntimeError:blocked+=1
    check('All six fit entrypoints blocked',blocked==6)
    folder=run/'adversaries';folder.mkdir()
    poisoned=new.copy();poisoned.loc[0,E]+=0.001;path=folder/'poisoned_C0_oof_2023.parquet';poisoned.to_parquet(path,index=False)
    invalid=dict(p,id=p['id']+'-ADVERSE-C0',b20_oof=rel(path));invalid['frozen_sources']=[x for x in p['frozen_sources'] if x['path']!=p['b20_oof']]+[{'path':rel(path),'sha256':sha(path)}]
    pp=folder/'plan_poisoned_C0.json';pp.write_text(json.dumps(invalid,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    before=set(run.parent.glob('contraccion_b20_*'))
    proc=subprocess.run([sys.executable,str(ROOT/p['code']),'--plan',str(pp)],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    (folder/'stdout.txt').write_text(proc.stdout,encoding='utf-8');(folder/'stderr.txt').write_text(proc.stderr,encoding='utf-8')
    failures=[x for x in set(run.parent.glob('contraccion_b20_*'))-before if (x/'plan_snapshot.json').exists() and read(x/'plan_snapshot.json')['id']==invalid['id']]
    check('Actual CLI incompatible C0 rejected before coefficient/model work',proc.returncode!=0 and 'Pair changed '+E in proc.stderr and len(failures)==1 and not (failures[0]/'standardized_coefficient_norms.parquet').exists())
    failures[0].joinpath('expected_adversary_failure.json').write_text(json.dumps({'expected':True,'reason':'Synthetic C0 mismatch, original sources unchanged','verification':rel(run/'verification.json'),'successful_fit_calls':0},indent=2)+'\n',encoding='utf-8')
    receipt={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,'expected_failure_runs':[rel(failures[0])],'blocked_adverse_fit_calls':blocked,'successful_fit_calls':0,'new_bootstrap':0,'professional_independent_validation':False,'scope':'Own focal rawscale/manual-term and fsum verification; prior542/48 or concurrent global/31group suites not repeated.'}
    with (run/'verification.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({k:receipt[k] for k in ['passed','failed','successful_fit_calls','expected_failure_runs']}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);verify(Path(parser.parse_args().run))
