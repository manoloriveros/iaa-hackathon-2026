"""Verifica solo concentración/AD nuevas: diccionarios, fsum y desviación general."""
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal
import argparse,ast,hashlib,importlib.util,json,math,subprocess,sys
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pyarrow.parquet as pq
from sklearn.metrics import mean_tweedie_deviance
KEY=['market','line','row_id'];AD='x_accidental_damage_cover';E='e_cost_mix_1.0'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()


def verify(run):
    run=run.resolve();p=read(run/'plan_snapshot.json');checks=[]
    def check(name,ok):checks.append({'name':name,'pass':bool(ok)});assert ok,name
    def close(a,b):return math.isclose(float(a),float(b),rel_tol=1e-10,abs_tol=1e-7)
    for x in p['frozen_sources']:check('Frozen '+x['path'],sha(ROOT/x['path'])==x['sha256'])
    f=pq.read_table(ROOT/p['row_attribution'],filters=[('reference','=','W2-B19')]).to_pylist()
    reason=pq.read_table(ROOT/p['selection_reasons']).to_pylist();ids={r['group_id'] for r in reason}
    case={rank:next(r['group_id'] for r in reason if r['reason']=='OOF_top5_adverse_buildings' and r['rank']==rank) for rank in [1,2]}
    primary=case[1];fire=[r for r in f if r['group_id']==primary and r['line']=='buildings'];check('Fixed fire unique',len(fire)==1)
    key=tuple(fire[0][k] for k in KEY);isrow=lambda r:tuple(r[k] for k in KEY)==key
    selected=lambda r:r['group_id'] in ids
    scope={'global':f,'selected12':[r for r in f if selected(r)],'fire_row':fire,'fire_full_component':[r for r in f if r['group_id']==primary],
           'global_without_fire_row':[r for r in f if not isrow(r)],'global_without_fire_component':[r for r in f if r['group_id']!=primary],
           'selected_without_fire_row':[r for r in f if selected(r) and not isrow(r)],'selected_without_fire_component':[r for r in f if selected(r) and r['group_id']!=primary]}
    out=read(run/'concentration_scopes.json');stats=out['scope_statistics'];sums={}
    for name,rows in scope.items():
        g={}
        for r in rows:g.setdefault(r['group_id'],[]).append(r['stored_gain'])
        gains={key:math.fsum(v) for key,v in g.items()}
        actual={'net_gain':math.fsum(r['stored_gain'] for r in rows),'T0':math.fsum(r['T0'] for r in rows),
                'mu19_total':math.fsum(r['muref'] for r in rows),'mu20_total':math.fsum(r['mu20'] for r in rows),
                'gross_row_positive_gain':math.fsum(r['stored_gain'] for r in rows if r['stored_gain']>0),
                'gross_row_negative_gain_abs':-math.fsum(r['stored_gain'] for r in rows if r['stored_gain']<0),
                'gross_group_positive_gain':math.fsum(v for v in gains.values() if v>0),
                'gross_group_negative_gain_abs':-math.fsum(v for v in gains.values() if v<0)}
        for field,value in actual.items():check('Independent fsum '+name+field,close(stats[name][field],value))
        check('Independent scope sizes '+name,stats[name]['rows']==len(rows) and stats[name]['groups']==len(gains))
        check('Independent signed group counts '+name,stats[name]['positive_groups']==sum(v>0 for v in gains.values()) and stats[name]['negative_groups']==sum(v<0 for v in gains.values()))
        sums[name]=actual
    for name in ['global_without_fire_row','global_without_fire_component']:
        rows=scope[name];y=[r['T0'] for r in rows];m19=[r['muref'] for r in rows];m20=[r['mu20'] for r in rows]
        null=mean_tweedie_deviance(y,[math.fsum(y)/len(y)]*len(y),power=1.5)*len(y)
        delta=(mean_tweedie_deviance(y,m19,power=1.5)-mean_tweedie_deviance(y,m20,power=1.5))*len(y)/null
        check('General deviance exclusion null '+name,close(null,stats[name]['null_deviance']))
        check('General deviance exclusion delta '+name,math.isclose(delta,stats[name]['derived_delta_D2'],rel_tol=1e-9,abs_tol=1e-11))
        check('Positive null cannot reverse signedgain '+name,(delta>0)==(sums[name]['net_gain']>0))
    check('Single-row D2 deliberately undefined',stats['fire_row']['derived_delta_D2'] is None and stats['fire_row']['null_deviance']==0)
    definitions={'fire_row_of_selected_net':('fire_row','selected12','net_gain'),'fire_row_of_global_net':('fire_row','global','net_gain'),
                 'fire_row_of_global_gross_positive_rows':('fire_row','global','gross_row_positive_gain'),
                 'fire_component_of_selected_net':('fire_full_component','selected12','net_gain'),'fire_component_of_global_net':('fire_full_component','global','net_gain'),
                 'fire_component_of_global_gross_positive_groups':('fire_full_component','global','gross_group_positive_gain'),
                 'fire_component_of_selected_gross_positive_groups':('fire_full_component','selected12','gross_group_positive_gain')}
    for label,(numerator,denom,field) in definitions.items():
        expected=float(Decimal(str(sums[numerator]['net_gain']))/Decimal(str(sums[denom][field])))
        check('Explicit denominator by Decimal '+label,close(out['shares_with_explicit_denominators'][label],expected))
    # A different general formula is used only for the fixed fire's stored two terms.
    r=fire[0];power=1.5
    def dev(y,mu):return 2*(y**(2-power)/((1-power)*(2-power))-y*mu**(1-power)/(1-power)+mu**(2-power)/(2-power))
    check('Fixed fire stored gain by general formula',close(r['stored_gain'],dev(r['T0'],r['muref'])-dev(r['T0'],r['mu20'])))
    check('Fixed fire two-term identity',close(r['stored_gain'],r['outcome_term']+r['prediction_term']))
    claim=pq.read_table(ROOT/p['claims_2023'],filters=[('line','=','buildings')]).to_pylist()
    rowcells=pq.read_table(run/'AD_period_composition_by_fold.parquet').to_pylist()
    claimcells=pq.read_table(run/'AD_peril_composition_by_fold.parquet').to_pylist()
    membership=pq.read_table(run/'fixed_fire_training_membership.parquet').to_pylist()
    fixed={}
    for fold,path in enumerate(p['building_frames']):
        rows=pq.read_table(ROOT/path,columns=KEY+['year','fold','group_id','T0','exposure',E,'x_new_business',AD]).to_pylist();mapping={tuple(r[k] for k in KEY):r for r in rows}
        def label(r):
            value=r[AD]
            if value is None or (isinstance(value,float) and math.isnan(value)):return 'missing'
            assert value in [0,1];return 'yes' if value==1 else 'no'
        for role in ['fit','heldout']:
            cellrows=[r for r in rows if (r['fold']!=fold if role=='fit' else r['fold']==fold)]
            actualclaims={}
            for c in claim:
                period=mapping[tuple(c[k] for k in KEY)]
                if not (c['fold']!=fold if role=='fit' else c['fold']==fold):continue
                ck=(label(period),'new' if period['x_new_business']==1 else 'renewal',c['peril'])
                v=actualclaims.setdefault(ck,{'claims':0,'T0_cents':0,'open_claims':0,'fixed_two_fire_cents':0})
                v['claims']+=1;v['T0_cents']+=c['T0_cents'];v['open_claims']+=int(c['status']=='open')
                if c['group_id'] in case.values():v['fixed_two_fire_cents']+=c['T0_cents']
            for outrow in [r for r in rowcells if r['fold_view']==fold and r['role']==role]:
                chosen=[r for r in cellrows if label(r)==outrow['AD_group'] and ('new' if r['x_new_business']==1 else 'renewal')==outrow['business']]
                check('Period cell rows/positive '+str(fold)+role+outrow['AD_group']+outrow['business'],outrow['rows']==len(chosen) and outrow['positive_rows']==sum(r['T0']>0 for r in chosen))
                cents=sum(int((Decimal(str(r['T0']))*100).quantize(Decimal('1'))) for r in chosen)
                check('Period cell exact cents '+str(fold)+role+outrow['AD_group']+outrow['business'],outrow['T0_cents']==cents)
                for field,sourcefield in [('nominal_exposure','exposure'),('effective_C0_exposure',E)]:check('Period denominator fsum '+str(fold)+role+field,close(outrow[field],math.fsum(r[sourcefield] for r in chosen)))
            target=[r for r in claimcells if r['fold_view']==fold and r['role']==role]
            check('Peril cell keys exact '+str(fold)+role,set(actualclaims)=={(r['AD_group'],r['business'],r['peril']) for r in target})
            for r in target:
                z=actualclaims[(r['AD_group'],r['business'],r['peril'])]
                for field in ['claims','T0_cents','open_claims','fixed_two_fire_cents']:check('Independent peril cell '+str(fold)+role+field,z[field]==r[field])
        for name,gid in [('primary',case[1]),('secondary',case[2])]:
            selected=[r for r in rows if r['group_id']==gid];v=[r for r in membership if r['fold_view']==fold and r['fixed_group_label']==name];check('Fixed fire membership source exact '+str(fold)+name,len(v)==1 and v[0]['present_in_fit']==all(r['fold']!=fold for r in selected) and v[0]['validation_fold']==selected[0]['fold'])
    check('Allrows four fit/oneheldout views',sum(r['rows'] for r in rowcells if r['role']=='fit')==12580*4 and sum(r['rows'] for r in rowcells if r['role']=='heldout')==12580)
    oldlocal=pq.read_table(ROOT/p['B19_local_influence'],filters=[('line','=','buildings'),('group_id','in',list(case.values()))]).to_pylist()
    actual=pq.read_table(run/'existing_B19_local_influence_fixed_fires.parquet').to_pylist();check('Only existing8localB19 values reused',len(oldlocal)==len(actual)==8)
    for r in actual:
        z=next(x for x in oldlocal if x['fold']==r['fold'] and x['group_id']==r['group_id'])
        check('Existing B19 approximate influence unchanged',all(r[field]==z[field] for field in ['local_delete_delta_coverage_beta','current_coverage_beta_raw','group_leverage_trace']))
        check('No heldout training influence manufactured',r['fold']!=r['group_validation_fold'])
    src=pq.read_table(ROOT/p['coefficients']).to_pylist();coef=pq.read_table(run/'AD_coefficient_by_fold.parquet').to_pylist()
    for r in coef:
        z=next(x for x in src if x['model_id']==r['model_id'] and x['line']=='buildings' and x['fold']==r['fold'] and x['feature']==AD)
        check('Original AD coefficient exact',r['beta_raw']==z['beta_raw'])
        check('Original AD ratio by math.exp',close(r['rate_ratio_yes_no'],math.exp(r['beta_raw'])))
    spec=importlib.util.spec_from_file_location('fireADguard',ROOT/p['code']);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    frame=pq.read_table(ROOT/p['row_attribution'],filters=[('reference','=','W2-B19')]).to_pandas()
    for name in ['year','missing_key','duplicate','negative_cost','empty']:
        z=frame.copy()
        if name=='year':z.loc[0,'year']=2024
        if name=='missing_key':z.loc[0,'row_id']=None
        if name=='duplicate':z.loc[1,KEY]=z.loc[0,KEY].to_numpy()
        if name=='negative_cost':z.loc[0,'T0']=-1
        if name=='empty':z=z.iloc[:0]
        caught=False
        try:module.guard(z)
        except ValueError:caught=True
        check('Invalid scope rejected '+name,caught)
    base=pq.read_table(ROOT/p['building_frames'][0],columns=[AD]).to_pandas();base.loc[0,AD]=2;caught=False
    try:module.ad_labels(base)
    except ValueError:caught=True
    check('Nonbinary AD rejected',caught);check('Zero net fraction not invented',module.ratio(1,0) is None)
    tree=ast.parse((ROOT/p['code']).read_text(encoding='utf-8'));check('No training/prediction/model imports',not any(isinstance(n,(ast.Import,ast.ImportFrom)) and any('sklearn' in a.name or 'joblib' in a.name for a in n.names) for n in ast.walk(tree)) and not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ['fit','fit_transform','predict','predict_proba'] for n in ast.walk(tree)))
    folder=run/'adversaries';folder.mkdir();poison=frame.copy();poison.loc[0,'year']=2024;file=folder/'wrong_year_attribution.parquet';poison.to_parquet(file,index=False)
    invalid=dict(p,id=p['id']+'-ADVERSE-YEAR',row_attribution=rel(file));invalid['frozen_sources']=[x for x in p['frozen_sources'] if x['path']!=p['row_attribution']]+[{'path':rel(file),'sha256':sha(file)}]
    pp=folder/'plan_wrong_year.json';pp.write_text(json.dumps(invalid,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');before=set(run.parent.glob('incendio_AD_b20_*'))
    proc=subprocess.run([sys.executable,str(ROOT/p['code']),'--plan',str(pp)],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    (folder/'stdout.txt').write_text(proc.stdout,encoding='utf-8');(folder/'stderr.txt').write_text(proc.stderr,encoding='utf-8')
    failures=[x for x in set(run.parent.glob('incendio_AD_b20_*'))-before if (x/'plan_snapshot.json').exists() and read(x/'plan_snapshot.json')['id']==invalid['id']]
    check('Actual CLI wrongyear fails before analysis tables',proc.returncode!=0 and 'Non2023 or empty scope' in proc.stderr and len(failures)==1 and not (failures[0]/'concentration_scopes.json').exists())
    failures[0].joinpath('expected_adversary_failure.json').write_text(json.dumps({'expected':True,'reason':'Synthetic year in saved2023 source; originals intact','verification':rel(run/'verification.json'),'successful_fit_calls':0},indent=2)+'\n',encoding='utf-8')
    receipt={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'passed':sum(r['pass'] for r in checks),'failed':sum(not r['pass'] for r in checks),'checks':checks,
             'expected_failure_runs':[rel(failures[0])],'successful_fit_calls':0,'model_loads':0,'new_price_predictions':0,'new_bootstrap':0,
             'scope':'New fixedfire concentration, two declared evaluation exclusions and AD composition only. No prior fullsuite or bootstrap repetition. Own review, not professional independent validation.'}
    with (run/'verification.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({k:receipt[k] for k in ['passed','failed','successful_fit_calls','model_loads','expected_failure_runs']},ensure_ascii=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);verify(Path(parser.parse_args().run))
